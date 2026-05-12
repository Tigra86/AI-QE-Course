import configparser
import glob
import hashlib
import html
import joblib
import json
import math
import numpy as np
import platform
import sklearn
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# LOGGING HELPERS
# ============================================================

def fmt_path(p: str | Path) -> str:
    p = Path(p).resolve()

    try:
        return str(p.relative_to(BASE_DIR)).replace("\\", "/")
    except ValueError:
        pass

    try:
        return str(p.relative_to(Path.cwd().resolve())).replace("\\", "/")
    except ValueError:
        pass

    return p.name


def log_info(message: str):
    print(f"[INFO] {message}")


def log_section(title: str):
    print(f"\n=== {title} ===")

# ============================================================
# QA / CI GUARDRAILS
# ============================================================

MIN_ACCEPTABLE_ACCURACY = 0.65
MIN_SAMPLES_PER_CLASS_WARNING = 5

FAIL_ON_COLLAPSE = True
FAIL_ON_DEAD_INTENT = False

# ============================================================
# DATA LOADING
# ============================================================

def load_dataset(path: str):
    texts, labels = [], []
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            texts.append(obj["text"])
            labels.append(obj["label"])
    return texts, labels

def load_all_datasets(pattern=None):
    if pattern is None:
        pattern = str(BASE_DIR / "datasets" / "*.jsonl")

    all_texts, all_labels = [], []
    files = sorted(glob.glob(pattern))

    if not files:
        log_info("No dataset files found.")
        return all_texts, all_labels, files

    for file in files:
        t, l = load_dataset(file)
        all_texts.extend(t)
        all_labels.extend(l)

        log_info(
            f"Loaded dataset: {fmt_path(file):<50} | samples={len(t)}"
        )

    log_info(f"Total samples loaded: {len(all_texts)}")
    log_info(f"Total dataset files: {len(files)}")

    return all_texts, all_labels, files

def load_rules(folder=None):
    if folder is None:
        folder = str(BASE_DIR / "rules" / "*.json")

    rules = {}
    files = sorted(glob.glob(folder))

    if not files:
        log_info("No rule files found.")
        return rules

    for file in files:
        with open(file, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        for intent, groups in data.items():
            rules.setdefault(intent, {}).update(groups)

        log_info(f"Loaded rule file: {fmt_path(file)}")

    log_info(f"Total rule files loaded: {len(files)}")

    return rules

def load_fallback(path=None):
    if path is None:
        path = BASE_DIR / "config" / "fallback_messages.json"
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "other": [
                "I'm not sure what you mean — could you rephrase?",
                "Sorry, I didn’t understand — try asking in a different way."
            ]
        }

def load_intent_thresholds(config: configparser.ConfigParser):
    if not config.has_section("INTENT_THRESHOLDS"):
        raise ValueError("Missing [INTENT_THRESHOLDS] section in system.config")
    return {k: config.getfloat("INTENT_THRESHOLDS", k) for k in config["INTENT_THRESHOLDS"]}


def file_fingerprint(paths: list[str]) -> str:
    h = hashlib.md5()
    for p in sorted(paths):
        h.update(p.encode("utf-8"))
        h.update(b"\0")
        fp = Path(p)
        if fp.exists():
            h.update(fp.read_bytes())
        h.update(b"\0\0")
    return h.hexdigest()

def maybe_load_previous_pack(path="model.pkl"):
    p = Path(path)
    if not p.exists():
        return None
    try:
        obj = joblib.load(p)
        if isinstance(obj, dict) and "dataset_hash" in obj:
            return obj
    except Exception:
        return None
    return None

def load_fuzzy_threshold(config):
    if config.has_section("FUZZY"):
        return config.getint("FUZZY", "threshold", fallback=70)
    return 70

def load_collapse_thresholds(config: configparser.ConfigParser):
    if not config.has_section("QA_COLLAPSE"):
        return 0.85, 0.35

    dom = config.getfloat("QA_COLLAPSE", "dominance_threshold", fallback=0.85)
    ent = config.getfloat("QA_COLLAPSE", "entropy_floor", fallback=0.35)

    if not (0.0 < dom <= 1.0):
        raise ValueError("dominance_threshold must be in (0,1]")

    if not (0.0 <= ent <= 1.0):
        raise ValueError("entropy_floor must be in [0,1]")

    return dom, ent

# ============================================================
# ANALYTICS
# ============================================================

def confusion_matrix_heatmap_table(cm: np.ndarray, classes: list[str]) -> str:

    cm = np.asarray(cm, dtype=float)
    vmax = float(cm.max()) if cm.size and cm.max() > 0 else 1.0

    header = "".join(f"<th class='mono'>{html.escape(c)}</th>" for c in classes)

    rows = []
    for i, row in enumerate(cm):
        cells = []
        for v in row:
            t = float(v) / vmax
            bg = f"rgba(37, 99, 235, {0.08 + 0.65 * t})"  # base + scaled alpha
            fg = "#fff" if t > 0.55 else "#111"
            cells.append(
                f"<td style='background:{bg};color:{fg};text-align:center;font-weight:600'>{int(v)}</td>"
            )
        rows.append(f"<tr><th class='mono'>{html.escape(classes[i])}</th>{''.join(cells)}</tr>")

    return f"""
    <table>
      <tr><th>True \\ Pred</th>{header}</tr>
      {''.join(rows)}
    </table>
    """

def detect_dead_intents(classes: list[str], y_train: list[str], y_pred: list[str]):
    train_set = set(y_train)
    pred_counts = Counter(y_pred)
    dead_pred = [c for c in classes if pred_counts.get(c, 0) == 0]  # never predicted
    unseen_in_train = [c for c in classes if c not in train_set]    # should not happen
    return pred_counts, dead_pred, unseen_in_train

def detect_class_collapse(pred_counts, classes, total, dominance_threshold, entropy_floor):

    if total <= 0:
        return {
            "collapsed": False,
            "dominant_class": None,
            "dominant_ratio": 0.0,
            "entropy_bits": 0.0,
            "norm_entropy": 0.0,
            "k_predicted": 0,
        }

    dominant_class, dominant_n = pred_counts.most_common(1)[0]
    dominant_ratio = dominant_n / total

    probs = np.array(
        [pred_counts.get(c, 0) / total for c in classes],
        dtype=float
    )

    entropy = float(-(probs * np.log2(probs + 1e-12)).sum())

    k = len(classes)
    max_entropy = math.log2(k) if k > 1 else 1.0
    norm_entropy = float(entropy / max_entropy)

    collapsed = (dominant_ratio >= dominance_threshold or norm_entropy < entropy_floor)

    return {
        "collapsed": bool(collapsed),
        "dominant_class": dominant_class,
        "dominant_ratio": float(dominant_ratio),
        "entropy_bits": float(entropy),
        "norm_entropy": float(norm_entropy),
        "k_predicted": int(len(pred_counts)),
        "dominance_threshold": dominance_threshold,
        "entropy_floor": entropy_floor,
    }

def calibration_report(probs: np.ndarray, y_true: list[str], classes: list[str], n_bins: int = 10):

    y_true = np.asarray(y_true)
    probs = np.asarray(probs, dtype=float)

    pred_idx = probs.argmax(axis=1)
    conf = probs.max(axis=1)
    pred_label = np.array([classes[i] for i in pred_idx], dtype=object)
    correct = (pred_label == y_true)

    # bins over confidence
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    bins = []

    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        # include hi in last bin
        if b == n_bins - 1:
            mask = (conf >= lo) & (conf <= hi)
        else:
            mask = (conf >= lo) & (conf < hi)

        n = int(mask.sum())
        if n == 0:
            bins.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": 0, "acc": None, "avg_conf": None})
            continue

        bin_acc = float(correct[mask].mean())
        bin_conf = float(conf[mask].mean())
        w = n / len(conf)
        ece += w * abs(bin_acc - bin_conf)

        bins.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": n, "acc": bin_acc, "avg_conf": bin_conf})

    return float(ece), bins

def calibration_bins_table(ece: float, bins: list[dict]) -> str:
    rows = []
    for b in bins:
        if b["n"] == 0:
            rows.append(f"<tr><td class='mono'>{b['bin']}</td><td>0</td><td>-</td><td>-</td></tr>")
        else:
            rows.append(
                "<tr>"
                f"<td class='mono'>{b['bin']}</td>"
                f"<td>{b['n']}</td>"
                f"<td>{b['acc']:.3f}</td>"
                f"<td>{b['avg_conf']:.3f}</td>"
                "</tr>"
            )
    return f"""
    <div class="note">
      <b>Expected Calibration Error (ECE):</b> <span class="mono">{ece:.4f}</span><br/>
      Uses max-confidence binning (multiclass).
    </div>
    <table>
      <tr><th>Confidence Bin</th><th>N</th><th>Accuracy</th><th>Avg Confidence</th></tr>
      {''.join(rows)}
    </table>
    """

def top_tfidf_features_per_intent(model: LogisticRegression, vectorizer: TfidfVectorizer, top_k: int = 15):

    feat_names = np.array(vectorizer.get_feature_names_out())
    coefs = model.coef_
    classes = list(model.classes_)

    out = {}
    for i, c in enumerate(classes):
        w = coefs[i]
        top_idx = np.argsort(w)[-top_k:][::-1]
        out[c] = [{"term": str(feat_names[j]), "weight": float(w[j])} for j in top_idx]
    return out

def top_features_table(top_feats: dict) -> str:
    sections = []
    for intent in sorted(top_feats.keys()):
        items = top_feats[intent]
        rows = "".join(
            f"<tr><td class='mono'>{html.escape(it['term'])}</td><td class='mono'>{it['weight']:.4f}</td></tr>"
            for it in items
        )
        sections.append(f"""
        <h3 class="mono">{html.escape(intent)}</h3>
        <table>
          <tr><th>Term</th><th>Weight</th></tr>
          {rows}
        </table>
        """)
    return "".join(sections)

def drift_section(prev_pack: dict | None, dataset_hash: str, config_hash: str,
                  label_counts: Counter, vectorizer_params: dict, model_params: dict) -> str:

    if not prev_pack:
        return """
        <div class="note">
          <b>Drift comparison:</b> No previous model.pkl found. Baseline established.
        </div>
        """

    prev_dataset = prev_pack.get("dataset_hash")
    prev_config = prev_pack.get("config_hash")
    prev_labels = prev_pack.get("training_metadata", {}).get("label_distribution", {})
    prev_vec = prev_pack.get("vectorizer_params", {})
    prev_model = prev_pack.get("model_params", {})

    dataset_changed = (prev_dataset != dataset_hash)
    config_changed = (prev_config != config_hash)
    labels_changed = (dict(label_counts) != prev_labels)
    vec_changed = (prev_vec != vectorizer_params)
    model_changed = (prev_model != model_params)

    def flag(changed: bool) -> str:
        return "<span class='bad'>CHANGED</span>" if changed else "<span class='ok'>UNCHANGED</span>"

    return f"""
    <h2>Training Drift</h2>
    <table>
      <tr><th>Dataset Hash</th><td class="mono">{prev_dataset}</td><td class="mono">{dataset_hash}</td><td>{flag(dataset_changed)}</td></tr>
      <tr><th>Config Hash</th><td class="mono">{prev_config}</td><td class="mono">{config_hash}</td><td>{flag(config_changed)}</td></tr>
      <tr><th>Label Distribution</th><td class="mono wrap">{prev_labels}</td><td class="mono wrap">{dict(label_counts)}</td><td>{flag(labels_changed)}</td></tr>
      <tr><th>Vectorizer Params</th><td class="mono wrap">{prev_vec}</td><td class="mono wrap">{vectorizer_params}</td><td>{flag(vec_changed)}</td></tr>
      <tr><th>Model Params</th><td class="mono wrap">{prev_model}</td><td class="mono wrap">{model_params}</td><td>{flag(model_changed)}</td></tr>
    </table>
    """
# ============================================================
# TRAINING REPORT
# ============================================================

def write_training_report(
    out_path,
    *,
    model_version,
    trained_at,
    sklearn_version,
    python_version,
    platform_info,
    vectorizer_params,
    model_params,
    dataset_hash,
    config_hash,
    intent_thresholds,
    accuracy,
    classes,
    report_dict,
    confusion,
    mistakes,
    label_counts,
    eval_mode,
    macro,
    weighted,
    pred_counts,
    dead_pred,
    collapse_info,
    ece,
    calib_bins,
    top_features,
    drift_html,
):
    css = """
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
    th, td { border: 1px solid #eee; padding: 8px; vertical-align: top; }
    th { background: #f7f7f7; }
    h2 { margin-top: 28px; }
    h3 { margin-top: 18px; }
    .mono { font-family: monospace; font-size: 14px; }
    .wrap { white-space: pre-wrap; }
    .ok { background: #e7f7ed; padding: 6px 12px; border-radius: 20px; display: inline-block; }
    .bad { background: #fde8e8; padding: 6px 12px; border-radius: 20px; display: inline-block; }
    .note { background: #fff7ed; padding: 10px; border: 1px solid #fed7aa; border-radius: 10px; margin-bottom: 16px; }
    """

    metric_rows = ""
    for c in classes:
        m = report_dict.get(c, {})
        metric_rows += f"""
        <tr>
          <td class="mono">{html.escape(c)}</td>
          <td>{m.get("precision", 0):.3f}</td>
          <td>{m.get("recall", 0):.3f}</td>
          <td>{m.get("f1-score", 0):.3f}</td>
          <td>{int(m.get("support", 0))}</td>
        </tr>
        """

    thr_rows = ""
    for k in sorted(intent_thresholds):
        thr_rows += f"<tr><td class='mono'>{html.escape(k)}</td><td>{intent_thresholds[k]:.3f}</td></tr>"

    mistake_rows = ""
    for m in mistakes:
        mistake_rows += f"""
        <tr>
          <td class="mono">{html.escape(m['true'])}</td>
          <td class="mono">{html.escape(m['pred'])}</td>
          <td>{m['prob']:.3f}</td>
          <td class="wrap">{html.escape(m['text'])}</td>
        </tr>
        """

    dist_rows = ""
    for k, v in sorted(label_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        dist_rows += f"<tr><td class='mono'>{html.escape(k)}</td><td>{v}</td></tr>"

    pred_rows = ""
    for k, v in sorted(pred_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        pred_rows += f"<tr><td class='mono'>{html.escape(k)}</td><td>{v}</td></tr>"

    acc_class = "ok" if macro.get("f1-score", 0) >= MIN_ACCEPTABLE_ACCURACY else "bad"

    eval_note = ""
    if eval_mode != "stratified_holdout":
        eval_note = f"""
        <div class="note">
          <b>Evaluation mode:</b> {html.escape(eval_mode)}<br/>
          Dataset is too small for a valid stratified holdout split, so the report is based on evaluating on the full dataset.
          Treat metrics as a pipeline sanity check, not a reliable generalization estimate.
        </div>
        """

    cm_html = confusion_matrix_heatmap_table(confusion, classes)

    dead_html = "<span class='ok'>None</span>" if not dead_pred else f"<span class='bad'>{html.escape(', '.join(dead_pred))}</span>"

    collapse_html = (
        f"<span class='bad'>YES</span> "
        f"(dominant={html.escape(collapse_info['dominant_class'])}, "
        f"ratio={collapse_info['dominant_ratio']:.3f}, "
        f"norm_entropy={collapse_info['norm_entropy']:.3f}, "
        f"thr_ratio={collapse_info['dominance_threshold']:.2f}, "
        f"thr_entropy={collapse_info['entropy_floor']:.2f})"
        if collapse_info["collapsed"]
        else
        f"<span class='ok'>NO</span> "
        f"(dominant={html.escape(collapse_info['dominant_class'])}, "
        f"ratio={collapse_info['dominant_ratio']:.3f}, "
        f"norm_entropy={collapse_info['norm_entropy']:.3f}, "
        f"thr_ratio={collapse_info['dominance_threshold']:.2f}, "
        f"thr_entropy={collapse_info['entropy_floor']:.2f})"
    )

    calib_html = calibration_bins_table(ece, calib_bins)
    top_feat_html = top_features_table(top_features)

    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <title>Intent Classifier Training Report</title>
      <style>{css}</style>
    </head>
    <body>

    <h1>Intent Classifier Training Report</h1>
    <div class="{acc_class}">Accuracy: {accuracy:.3f}</div>
    {eval_note}

    <h2>Metadata</h2>
    <table>
      <tr><th>Model Version</th><td>{html.escape(model_version)}</td></tr>
      <tr><th>Trained At (UTC)</th><td class="mono">{html.escape(trained_at)}</td></tr>
      <tr><th>sklearn Version</th><td class="mono">{html.escape(sklearn_version)}</td></tr>
      <tr><th>Dataset Hash</th><td class="mono">{dataset_hash}</td></tr>
      <tr><th>Config Hash</th><td class="mono">{config_hash}</td></tr>
    </table>

    {drift_html}

    <h2>Aggregate Metrics</h2>
    <table>
        <tr><th>Type</th><th>Precision</th><th>Recall</th><th>F1</th></tr>
        <tr>
            <td>Macro Avg</td>
            <td>{macro.get("precision",0):.3f}</td>
            <td>{macro.get("recall",0):.3f}</td>
            <td>{macro.get("f1-score",0):.3f}</td>
        </tr>
        <tr>
            <td>Weighted Avg</td>
            <td>{weighted.get("precision",0):.3f}</td>
            <td>{weighted.get("recall",0):.3f}</td>
            <td>{weighted.get("f1-score",0):.3f}</td>
        </tr>
    </table>

    <h2>Environment</h2>
    <table>
      <tr><th>Python Version</th><td class="mono">{html.escape(python_version)}</td></tr>
      <tr><th>Platform</th><td class="mono">{html.escape(platform_info)}</td></tr>
      <tr><th>Vectorizer Params</th><td class="mono wrap">{html.escape(str(vectorizer_params))}</td></tr>
      <tr><th>Model Params</th><td class="mono wrap">{html.escape(str(model_params))}</td></tr>
    </table>

    <h2>Label Distribution</h2>
    <table>
      <tr><th>Label</th><th>Count</th></tr>
      {dist_rows}
    </table>

    <h2>Prediction Distribution</h2>
    <div class="note">
      <b>Dead-intent (never predicted):</b> {dead_html}<br/>
      <b>Class collapse detected:</b> {collapse_html}
    </div>
    <table>
      <tr><th>Predicted Label</th><th>Count</th></tr>
      {pred_rows}
    </table>

    <h2>Per-Intent Metrics</h2>
    <table>
      <tr><th>Intent</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr>
      {metric_rows}
    </table>

    <h2>Confidence Calibration</h2>
    {calib_html}

    <h2>Intent Thresholds</h2>
    <table>
      <tr><th>Intent</th><th>Threshold</th></tr>
      {thr_rows}
    </table>

    <h2>Confusion Matrix (Heatmap)</h2>
    {cm_html}

    <h2>Top Misclassifications</h2>
    <table>
      <tr><th>True</th><th>Pred</th><th>Prob(pred)</th><th>Text</th></tr>
      {mistake_rows or "<tr><td colspan='4'>None</td></tr>"}
    </table>

    <h2>Top TF-IDF Features Per Intent</h2>
    {top_feat_html}

    </body>
    </html>
    """

    Path(out_path).write_text(html_doc, encoding="utf-8")

# ============================================================
# MAIN
# ============================================================

def main():
    log_section("LOADING DATASETS")
    texts, labels, dataset_files = load_all_datasets()

    if not texts:
        raise ValueError("No training data found.")

    label_counts = Counter(labels)
    print(f"Label distribution: {label_counts}")

    min_class_count = min(label_counts.values())
    if min_class_count < MIN_SAMPLES_PER_CLASS_WARNING:
        print(f"WARNING: Some intents have fewer than {MIN_SAMPLES_PER_CLASS_WARNING} samples.")

    dataset_hash = file_fingerprint(dataset_files)

    print("\n=== LOADING RULES & FALLBACK ===")
    rules = load_rules()
    fallback = load_fallback()

    num_classes = len(label_counts)
    total_samples = len(labels)

    test_ratio = 0.2
    expected_test_size = math.ceil(total_samples * test_ratio)

    if (min_class_count < 2) or (expected_test_size < num_classes):
        eval_mode = "full_dataset_eval"
        collapse_basis = "full_dataset"
        print("Dataset too small for valid stratified split. Using full dataset.")
        X_train, y_train = texts, labels
        X_test, y_test = texts, labels
    else:
        eval_mode = "stratified_holdout"
        collapse_basis = "test_split"
        X_train, X_test, y_train, y_test = train_test_split(
            texts,
            labels,
            test_size=test_ratio,
            random_state=42,
            stratify=labels
        )

    print("\n=== VECTORIZATION ===")
    vectorizer = TfidfVectorizer()
    Xv_train = vectorizer.fit_transform(X_train)
    Xv_test = vectorizer.transform(X_test)

    print("\n=== TRAIN MODEL ===")
    model = LogisticRegression(max_iter=500, class_weight="balanced", solver="lbfgs", random_state=42)
    model.fit(Xv_train, y_train)

    print("\n=== EVALUATE ===")
    y_pred = model.predict(Xv_test)
    probs = model.predict_proba(Xv_test)
    classes = list(model.classes_)

    accuracy = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred, labels=classes)

    report = classification_report(y_test, y_pred, labels=classes, output_dict=True, zero_division=0)

    pred_counts, dead_pred, unseen = detect_dead_intents(classes, y_train, y_pred)

    if unseen:
        raise RuntimeError(f"Internal error: unseen classes in model: {unseen}")

    ece, bins = calibration_report(probs, y_test, classes)
    top_features = top_tfidf_features_per_intent(model, vectorizer)

    print("\n=== LOAD CONFIG ===")
    config_path = BASE_DIR / "config" / "system.config"
    if not config_path.exists():
        raise FileNotFoundError("config/system.config not found")

    config = configparser.ConfigParser()
    config.read(config_path)

    config_hash = hashlib.md5(config_path.read_bytes()).hexdigest()

    collapse_dom_thr, collapse_ent_floor = load_collapse_thresholds(config)
    thresholds = load_intent_thresholds(config)

    missing_thr = set(classes) - set(thresholds.keys())
    if missing_thr:
        raise RuntimeError(f"Missing thresholds for trained labels: {sorted(missing_thr)}")

    fuzzy_threshold = load_fuzzy_threshold(config)

    collapse_info = detect_class_collapse(
        pred_counts,
        classes,
        total=len(y_pred),
        dominance_threshold=collapse_dom_thr,
        entropy_floor=collapse_ent_floor,
    )

    collapse_info["basis"] = collapse_basis

    MIN_SAMPLES_FOR_COLLAPSE_CHECK = 50

    if (FAIL_ON_COLLAPSE and collapse_info["collapsed"] and total_samples >= MIN_SAMPLES_FOR_COLLAPSE_CHECK):
        raise RuntimeError(f"Class collapse detected on {collapse_basis}.")

    if dead_pred:
        msg = f"Dead intents detected (never predicted): {dead_pred}"

        if FAIL_ON_DEAD_INTENT:
            raise RuntimeError(msg)
        else:
            print(f"[CI WARNING] {msg}")

    macro_f1 = report.get("macro avg", {}).get("f1-score", 0)

    if macro_f1 < MIN_ACCEPTABLE_ACCURACY:
        raise RuntimeError(f"Macro-F1 {macro_f1:.3f} below minimum threshold {MIN_ACCEPTABLE_ACCURACY}")

    trained_at = datetime.utcnow().isoformat() + "Z"

    print("\n=== DRIFT COMPARE ===")
    prev_pack = maybe_load_previous_pack(str(BASE_DIR / "model.pkl"))
    drift_html = drift_section(
        prev_pack,
        dataset_hash,
        config_hash,
        label_counts,
        vectorizer.get_params(),
        model.get_params(),
    )

    print("\n=== SAVE MODEL PACK ===")
    PACK = {
        "vectorizer": vectorizer,
        "model": model,
        "rules": rules,
        "fallback_messages": fallback,
        "intent_thresholds": thresholds,
        "fuzzy_threshold": fuzzy_threshold,
        "training_metadata": {
            "label_distribution": dict(label_counts),
            "eval_mode": eval_mode,
            "collapse_info": collapse_info,
            "dead_pred": dead_pred,
            "ece": ece,
        },
        "dataset_hash": dataset_hash,
        "config_hash": config_hash,
        "vectorizer_params": vectorizer.get_params(),
        "model_params": model.get_params(),
        "trained_at": trained_at,
    }

    joblib.dump(PACK, BASE_DIR / "model.pkl")

    print("\n=== WRITE REPORT ===")
    Path("reports").mkdir(parents=True, exist_ok=True)
    write_training_report(
        "reports/training_report.html",
        model_version="1.0.0",
        trained_at=trained_at,
        sklearn_version=sklearn.__version__,
        python_version=sys.version,
        platform_info=platform.platform(),
        vectorizer_params=vectorizer.get_params(),
        model_params=model.get_params(),
        dataset_hash=dataset_hash,
        config_hash=config_hash,
        intent_thresholds=thresholds,
        accuracy=accuracy,
        classes=classes,
        report_dict=report,
        confusion=cm,
        mistakes=[],
        label_counts=label_counts,
        eval_mode=eval_mode,
        macro=report.get("macro avg", {}),
        weighted=report.get("weighted avg", {}),
        pred_counts=pred_counts,
        dead_pred=dead_pred,
        collapse_info=collapse_info,
        ece=ece,
        calib_bins=bins,
        top_features=top_features,
        drift_html=drift_html,
    )

    print("MODEL -> model.pkl and reports/training_report.html")

if __name__ == "__main__":
    main()
