# pip install flask flask_cors rapidfuzz joblib rapidfuzz scikit-learn sentence_transformers spacy

import os
import json
import re
import random
import joblib
import logging
import configparser
from flask import render_template
from flask import Flask, request, jsonify
from flask_cors import CORS
from rapidfuzz import fuzz
from pathlib import Path
from datetime import datetime, timezone
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
BASE_DIR = Path(__file__).resolve().parent

# -------------------------------------------------------------------

app = Flask(
    __name__,
    template_folder=BASE_DIR / "templates",
    static_folder=BASE_DIR / "static"
)
CORS(app)

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    return jsonify({
        "error": str(e),
        "type": type(e).__name__,
        "traceback": traceback.format_exc()
    }), 500

# -------------------------------------------------------------------

CONFIG_FILE = BASE_DIR / "config" / "system.config"

if not CONFIG_FILE.exists():
    raise FileNotFoundError(f"Missing config file: {CONFIG_FILE}")

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# -------------------------------------------------------------------

model_path = BASE_DIR / config.get("UI", "MODEL", fallback="model.pkl")
PACK = joblib.load(model_path)

DEFAULT_TEMPERATURE = config.getfloat("INFERENCE","TEMPERATURE",fallback=0.0)

vectorizer        = PACK["vectorizer"]
model             = PACK["model"]
rules             = PACK["rules"]
thresholds        = PACK["intent_thresholds"]
fallback_messages = PACK["fallback_messages"]
fuzzy_threshold   = PACK.get("fuzzy_threshold", 70)
model_version     = PACK.get("model_version", "1.0.0")

MODEL_CLASSES = getattr(model, "classes_", [])

# -------------------------------------------------------------------
# ALIGNMENT CONFIG
# -------------------------------------------------------------------

BLOCKED_KEYWORDS = [
    k.strip().lower()
    for k in config.get("ALIGNMENT", "BLOCKED_KEYWORDS", fallback="").split(",")
    if k.strip()
]

try:
    DISALLOWED_RULES = json.loads(
        config.get("ALIGNMENT", "DISALLOWED_RULES", fallback="{}")
    )
except Exception:
    DISALLOWED_RULES = {}

REFUSAL_MESSAGE = config.get(
    "ALIGNMENT", "REFUSAL_MESSAGE",
    fallback="I can't help with that request."
)

RESTRICTED_MESSAGE = config.get(
    "ALIGNMENT", "RESTRICTED_MESSAGE",
    fallback="That topic is restricted."
)

# -------------------------------------------------------------------

RULES_DIR = "rules"
AUTO_SPECS_FILE   = os.path.join(RULES_DIR, "auto_product_specs.json")
AUTO_COMP_FILE    = os.path.join(RULES_DIR, "auto_product_comparisons.json")
MANUAL_RULES_FILE = os.path.join(RULES_DIR, "manual_rules.json")

os.makedirs(RULES_DIR, exist_ok=True)

auto_specs = {}
auto_comparisons = {}

# -------------------------------------------------------------------

def apply_alignment(question: str, result: dict) -> dict:

    q = (question or "").lower()

    for word in BLOCKED_KEYWORDS:
        if re.search(rf"\b{re.escape(word)}\b", q):
            return {
                **result,
                "answer": REFUSAL_MESSAGE,
                "final_intent": "blocked",
                "reason": f"global_blocked_keyword:{word}",
            }

    restricted_any = set()
    if isinstance(DISALLOWED_RULES, dict):
        for _, words in DISALLOWED_RULES.items():
            if isinstance(words, list):
                restricted_any.update(w.strip().lower() for w in words if isinstance(w, str) and w.strip())

    for word in restricted_any:
        if word in q:
            return {
                **result,
                "answer": RESTRICTED_MESSAGE,
                "final_intent": "restricted",
                "reason": f"global_restricted_keyword:{word}",
            }

    return result

# -------------------------------------------------------------------

def _load_auto_file(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return data.get("product_specs", {})
    except Exception:
        return {}

def _persist_auto(path, mapping):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"product_specs": mapping}, f, ensure_ascii=False, indent=2)

def load_auto_rules():
    global auto_specs, auto_comparisons
    auto_specs = _load_auto_file(AUTO_SPECS_FILE)
    auto_comparisons = _load_auto_file(AUTO_COMP_FILE)

    rules.setdefault("product_specs", {})
    rules["product_specs"].update(auto_specs)
    rules["product_specs"].update(auto_comparisons)

def store_product_specs_rule(product):
    key = product.lower().strip()
    if key and key not in auto_specs:
        auto_specs[key] = [f"Specifications placeholder for {key}. Add real details later."]
        rules["product_specs"][key] = auto_specs[key]
        _persist_auto(AUTO_SPECS_FILE, auto_specs)

def store_comparison_rule(a, b):
    key = f"{a} vs {b}"
    if key not in auto_comparisons:
        auto_comparisons[key] = [f"Placeholder comparison for {a} vs {b}. Add real details later."]
        rules["product_specs"][key] = auto_comparisons[key]
        _persist_auto(AUTO_COMP_FILE, auto_comparisons)

# -------------------------------------------------------------------

def load_manual_rules():
    if not os.path.exists(MANUAL_RULES_FILE):
        return
    try:
        with open(MANUAL_RULES_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        for intent, groups in data.items():
            rules.setdefault(intent, {})
            rules[intent].update(groups)
    except Exception as e:
        print("[MANUAL LOAD ERROR]", e)

def persist_manual_rules():
    manual = {}
    for intent, groups in rules.items():
        if intent == "product_specs":
            manual[intent] = {
                k: v for k, v in groups.items()
                if k not in auto_specs and k not in auto_comparisons
            }
        else:
            manual[intent] = groups

    with open(MANUAL_RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(manual, f, ensure_ascii=False, indent=2)

load_auto_rules()
load_manual_rules()

# -------------------------------------------------------------------

log_path_from_config = config.get("UI", "LOG_FILE", fallback="log/chat_logs.jsonl")
LOG_FILE = BASE_DIR / Path(log_path_from_config)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE = str(LOG_FILE)
LOGS = []

def load_logs():
    if not os.path.exists(LOG_FILE):
        return
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                LOGS.append(json.loads(line.strip()))
        if len(LOGS) > 500:
            del LOGS[:-500]
        print(f"[LOG-LOAD] {len(LOGS)} logs")
    except Exception as e:
        print(f"[LOG ERROR] {e}")

def append_log(question, result):
    try:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "answer": result["answer"],
            "final_intent": result["final_intent"],
            "ml_intent": result["ml_intent"],
            "reason": result["reason"],
            "probabilities": result["probabilities"],
            "max_probability": result["max_probability"],
            "model_version": result["model_version"],
        }

        LOGS.append(entry)
        if len(LOGS) > 500:
            del LOGS[:-500]

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    except Exception as e:
        print(f"[LOG WRITE ERROR] {e}")

load_logs()

# -------------------------------------------------------------------

def pick_answer(answers: list[str], temperature: float = 0.0) -> str:

    if not answers:
        return ""

    temperature = max(0.0, temperature)

    if temperature == 0.0:
        return sorted(answers)[0]

    if temperature < 1.0:
        top_n = max(1, min(len(answers), 2))
        return random.choice(answers[:top_n])

    return random.choice(answers)

# -------------------------------------------------------------------

def detect_comparison_pairs(text):
    for p in [
        r"(.+?)\s+vs\.?\s+(.+)",
        r"compare\s+(.+?)\s+to\s+(.+)",
        r"compare\s+(.+?)\s+and\s+(.+)"
    ]:
        m = re.search(p, text)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    return None, None

def fuzzy_match(text, keyword):
    score = fuzz.partial_ratio(text.lower(), keyword.lower())
    return score >= fuzzy_threshold, score

def fuzzy_intent_match(q):
    best = (None, None, 0)
    for intent, groups in rules.items():
        for keyword in groups:
            if keyword == "default":
                continue
            penalty = 20 if " vs " in keyword else 0
            matched, raw_score = fuzzy_match(q, keyword)
            score = raw_score - penalty
            if matched and score >= fuzzy_threshold and score > best[2]:
                best = (intent, keyword, score)
    return best

def select_keyword_answer(intent, q, temperature):
    groups = rules.get(intent, {})
    for k, v in groups.items():
        matched, _ = fuzzy_match(q, k)
        if matched and isinstance(v, list):
            return pick_answer(v, temperature)

    return pick_answer(
        fallback_messages.get("other", ["I'm not sure yet."]),
        temperature
    )

# -------------------------------------------------------------------

def infer(question, temperature=DEFAULT_TEMPERATURE):
    q = question.lower().strip()

    for intent, groups in rules.items():
        normalized_groups = {k.lower(): v for k, v in groups.items()}
        if q in normalized_groups:
            return {
                "answer": pick_answer(normalized_groups[q], temperature),
                "final_intent": intent,
                "ml_intent": intent,
                "reason": "exact_rule_match",
                "probabilities": {c: 0.0 for c in MODEL_CLASSES},
                "model_version": model_version,
                "max_probability": 1.0,
            }

    if any(w in q for w in ("spec", "specs", "specifications", "features")):
        cleaned = re.sub(r"\b(specs?|specifications?|features)\b", "", q).strip()
        ps = rules.get("product_specs", {})

        cleaned = cleaned.lower()
        ps_normalized = {k.lower(): v for k, v in ps.items()}

        if cleaned in ps_normalized:
            return {
                "answer": pick_answer(ps_normalized[cleaned], temperature),
                "final_intent": "product_specs",
                "ml_intent": "product_specs",
                "reason": "explicit_specs_match",
                "probabilities": {c: 0.0 for c in MODEL_CLASSES},
                "model_version": model_version,
                "max_probability": 1.0,
            }

    a, b = detect_comparison_pairs(q)
    if a and b:
        key = f"{a.lower().strip()} vs {b.lower().strip()}"
        ps = rules.get("product_specs", {})
        if key in ps:
            answer = pick_answer(ps[key], temperature)
        else:
            answer = f"{a} vs {b}: comparison pending."
            store_product_specs_rule(a)
            store_product_specs_rule(b)
            store_comparison_rule(a, b)

        return {
            "answer": answer,
            "final_intent": "product_specs",
            "ml_intent": "product_specs",
            "reason": "comparison",
            "probabilities": {c: 0.0 for c in MODEL_CLASSES},
            "model_version": model_version,
            "max_probability": 1.0,
        }

    X = vectorizer.transform([question])
    probs = model.predict_proba(X)[0]
    ml_intent = model.predict(X)[0]
    ml_prob = float(max(probs))

    override, _, _ = fuzzy_intent_match(q)

    required = thresholds.get(ml_intent, 0.0)

    if override:
        final = override
        reason = "fuzzy_override"
    elif ml_prob >= required:
        final = ml_intent
        reason = "ml_confident"
    else:
        final = "other"
        reason = "low_confidence"

    return {
        "answer": select_keyword_answer(final, q, temperature),
        "final_intent": final,
        "ml_intent": ml_intent,
        "reason": reason,
        "probabilities": dict(zip(MODEL_CLASSES, map(float, probs))),
        "model_version": model_version,
        "max_probability": ml_prob,
    }

# -------------------------------------------------------------------

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}

    question = (data.get("input") or data.get("message") or "").strip()
    if not question:
        return jsonify({"error": "Missing 'input' field"}), 400

    temperature = max(0.0, float(data.get("temperature", DEFAULT_TEMPERATURE)))

    result = infer(question, temperature)
    result = apply_alignment(question, result)
    append_log(question, result) 
    return jsonify({
        "input": question,
        "temperature": temperature,
        **result
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True) or {}
    question = data.get("message", "").strip()
    if not question:
        return jsonify({"error": "Empty message"}), 400

    temperature = max(0.0, float(data.get("temperature", DEFAULT_TEMPERATURE)))
    result = infer(question, temperature)
    result = apply_alignment(question, result)
    append_log(question, result)
    return jsonify(result)

# -------------------------------------------------------------------

@app.route("/api/search_logs", methods=["POST"])
def api_search_logs():
    data = request.get_json(silent=True) or {}

    query = (data.get("query") or "").lower().strip()
    intent = data.get("intent")
    limit = int(data.get("limit", 50))

    if not query and not intent:
        return jsonify({"error": "Provide 'query' or 'intent'"}), 400

    results = []

    for log in reversed(LOGS):
        if query:
            if (
                query not in log["question"].lower()
                and query not in log["answer"].lower()
            ):
                continue

        if intent:
            if log["final_intent"] != intent:
                continue

        results.append(log)

        if len(results) >= limit:
            break

    return jsonify({
        "query": query,
        "intent": intent,
        "count": len(results),
        "results": results
    })

# -------------------------------------------------------------------

@app.route("/api/upload_rules", methods=["POST"])
def api_upload_rules():
    raw = None
    if request.is_json:
        try:
            raw = request.get_json()
        except Exception as e:
            return jsonify({"error": f"Invalid JSON body: {e}"}), 400
    elif "file" in request.files:
        try:
            content = request.files["file"].read().decode("utf-8-sig")
            raw = json.loads(content)
        except Exception as e:
            return jsonify({"error": f"Invalid JSON file: {e}"}), 400
    else:
        return jsonify({
            "error": "Provide rules either as JSON body or as multipart file"
        }), 400

    while (
        isinstance(raw, dict)
        and len(raw) == 1
        and isinstance(list(raw.values())[0], dict)
        and list(raw.keys())[0].lower() in ("rules", "intents", "data", "payload")
    ):
        raw = list(raw.values())[0]

    if not isinstance(raw, dict) or not raw:
        return jsonify({"error": "Top-level JSON must be a non-empty object"}), 400

    merged_intents = 0
    new_rules = 0
    updated_rules = 0

    for intent, groups in raw.items():
        if not isinstance(groups, dict):
            continue

        rules.setdefault(intent, {})
        merged_intents += 1

        for key, answers in groups.items():
            if key not in rules[intent]:
                new_rules += 1
            elif rules[intent][key] != answers:
                updated_rules += 1

            rules[intent][key] = answers

    persist_manual_rules()

    return jsonify({
        "success": True,
        "message": (
            f"Merged {merged_intents} intents | "
            f"New rules: {new_rules} | "
            f"Updated rules: {updated_rules}"
        ),
        "file": MANUAL_RULES_FILE
    })

@app.route("/")
def index():
    return render_template(
        "ui.html",
        model_version=model_version
    )

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "model_version": model_version
    })

# -------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Running at http://127.0.0.1:8080 | Model {model_version}")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="127.0.0.1", port=port)
