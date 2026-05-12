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

logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=BASE_DIR / "templates",
    static_folder=BASE_DIR / "static"
)

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    return jsonify({
        "error": str(e),
        "type": type(e).__name__,
        "traceback": traceback.format_exc()
    }), 500
# -------------------------------------------------------------------
CONFIG_FILE = Path("system.config")

if not CONFIG_FILE.exists():
    raise FileNotFoundError(f"Missing config file: {CONFIG_FILE}")

config = configparser.ConfigParser()
config.read(CONFIG_FILE)
# -------------------------------------------------------------------
MODEL = config.get("UI", "MODEL")
DEFAULT_TEMPERATURE = config.getfloat("INFERENCE","TEMPERATURE",fallback=0.0)
PACK = joblib.load(MODEL)

vectorizer        = PACK["vectorizer"]
model             = PACK["model"]
rules             = PACK["rules"]
thresholds        = PACK["intent_thresholds"]
fallback_messages = PACK["fallback_messages"]
fuzzy_threshold   = PACK["fuzzy_threshold"]
model_version     = PACK.get("model_version", "unknown")

MODEL_CLASSES = getattr(model, "classes_", [])
# -------------------------------------------------------------------
RULES_DIR = "rules"
AUTO_SPECS_FILE   = os.path.join(RULES_DIR, "auto_product_specs.json")
AUTO_COMP_FILE    = os.path.join(RULES_DIR, "auto_product_comparisons.json")
MANUAL_RULES_FILE = os.path.join(RULES_DIR, "manual_rules.json")

os.makedirs(RULES_DIR, exist_ok=True)

auto_specs = {}
auto_comparisons = {}
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
def pick_answer(answers: list[str], temperature: float = 0.0) -> str:
    """
    Temperature-based answer selection.

    temperature = 0.0 → deterministic
    temperature < 1.0 → slightly random (top answers)
    temperature >= 1.5 → fully random
    """

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
            matched, score = fuzzy_match(q, keyword)
            score -= penalty
            if matched and score > best[2]:
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
        key = f"{a} vs {b}"
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

    return jsonify({
        "input": question,
        "temperature": temperature,
        **result
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True) or {}
    q = data.get("message", "").strip()
    if not q:
        return jsonify({"error": "Empty message"}), 400

    temperature = max(0.0, float(data.get("temperature", DEFAULT_TEMPERATURE)))
    return jsonify(infer(q, temperature))

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
        "index.html",
        model_version=model_version
    )
# -------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Running at http://127.0.0.1:5000 | Model {model_version}")
    app.run(debug=True)
