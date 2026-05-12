import os
import json
import re
import random

import joblib
from rapidfuzz import fuzz
# -----------------------------
# Load model pack
# -----------------------------
PACK = joblib.load("model.pkl")

vectorizer        = PACK["vectorizer"]
model             = PACK["model"]
rules             = PACK["rules"]
thresholds        = PACK["intent_thresholds"]
fallback_messages = PACK["fallback_messages"]
fuzzy_threshold   = PACK["fuzzy_threshold"]
model_version     = PACK.get("model_version", "unknown")

# -----------------------------
AUTO_SPECS_FILE = os.path.join("rules", "auto_product_specs.json")
AUTO_COMP_FILE  = os.path.join("rules", "auto_product_comparisons.json")

auto_specs = {}
auto_comparisons = {}


def _load_auto_file(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("product_specs", {})
    except Exception as e:
        print(f"[AUTO-LOAD ERROR] {path}: {e}")
        return {}


def load_auto_rules():
    global auto_specs, auto_comparisons

    specs = _load_auto_file(AUTO_SPECS_FILE)
    auto_specs = specs

    comps = _load_auto_file(AUTO_COMP_FILE)
    auto_comparisons = comps

    if "product_specs" not in rules:
        rules["product_specs"] = {}

    rules["product_specs"].update(specs)
    rules["product_specs"].update(comps)

    print(f"[AUTO-LOAD] Loaded {len(specs)} auto specs, {len(comps)} auto comparisons.")


def _persist_auto(path, mapping):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"product_specs": mapping}, f, ensure_ascii=False, indent=2)
        print(f"[AUTO-SAVE] {path} updated ({len(mapping)} entries).")
    except Exception as e:
        print(f"[AUTO-SAVE ERROR] {path}: {e}")


def persist_auto_specs():
    _persist_auto(AUTO_SPECS_FILE, auto_specs)


def persist_auto_comparisons():
    _persist_auto(AUTO_COMP_FILE, auto_comparisons)


def store_product_specs_rule(product: str):
    key = product.lower().strip()
    if not key:
        return

    if key not in auto_specs:
        placeholder = f"Specifications placeholder for {key}. Add real details later."
        auto_specs[key] = [placeholder]
        # keep main rules in sync
        if "product_specs" not in rules:
            rules["product_specs"] = {}
        rules["product_specs"][key] = auto_specs[key]
        persist_auto_specs()
        print(f"[AUTO-LEARN] specs: {key}")


def store_comparison_rule(a: str, b: str):
    a = a.lower().strip()
    b = b.lower().strip()
    if not a or not b:
        return
    key = f"{a} vs {b}"

    if key not in auto_comparisons:
        placeholder = f"Placeholder comparison for {a} vs {b}. Add real details later."
        auto_comparisons[key] = [placeholder]
        # keep main rules in sync
        if "product_specs" not in rules:
            rules["product_specs"] = {}
        rules["product_specs"][key] = auto_comparisons[key]
        persist_auto_comparisons()
        print(f"[AUTO-LEARN] comparison: {key}")
load_auto_rules()
# -----------------------------
def detect_comparison_pairs(text: str):
    t = text.lower()

    patterns = [
        r"compare\s+(.+?)\s+and\s+(.+)",
        r"compare\s+(.+?)\s+to\s+(.+)",
        r"(.+?)\s+vs\.?\s+(.+)",
        r"(.+?)\s+vs\s+(.+)",
        r"(.+?)\s+and\s+(.+)",
        r"(.+?)\s+or\s+(.+)",
        r"(.+?)\s+compared\s+to\s+(.+)",
    ]

    for p in patterns:
        m = re.search(p, t)
        if m:
            a = m.group(1).strip()
            b = m.group(2).strip()
            return a, b

    return None, None

def generate_dynamic_comparison(a: str, b: str) -> str:
    templates = [
        f"Here is a general comparison between {a} and {b}: consider price, performance, design, and durability.",
        f"Comparing {a} to {b}: evaluate display quality, battery life, sensors, and long-term reliability.",
        f"{a} vs {b}: key differences usually involve features, performance metrics, and ecosystem or usage context."
    ]
    return random.choice(templates)
# -----------------------------
def fuzzy_match(text, keyword, threshold):
    score = fuzz.partial_ratio(text.lower(), keyword.lower())
    return score >= threshold, score

def fuzzy_intent_match(question, rules_dict, fuzzy_threshold=70):
    q = question.lower()
    best_intent = None
    best_keyword = None
    best_score = 0

    for intent, groups in rules_dict.items():
        for keyword in groups.keys():
            if keyword == "default":
                continue

            matched, score = fuzzy_match(q, keyword, fuzzy_threshold)
            if score > best_score:
                best_score = score
                best_keyword = keyword
                if matched:
                    best_intent = intent

    return best_intent, best_keyword, best_score
# -----------------------------
def select_keyword_answer(intent, question):
    if intent not in rules:
        return random.choice(fallback_messages.get("other", ["I'm not sure yet."]))

    groups = rules[intent]
    q = question.lower()

    for keyword, answers in groups.items():
        if keyword == "default":
            continue
        matched, _ = fuzzy_match(q, keyword, fuzzy_threshold)
        if matched:
            return random.choice(answers)

    return random.choice(groups.get("default", fallback_messages.get("other", ["I'm not sure yet."])))
# -----------------------------
def infer(question: str):
    q = question.lower().strip()

    # 1. Comparison detection
    a, b = detect_comparison_pairs(q)
    if a and b:
        key = f"{a.lower().strip()} vs {b.lower().strip()}"

        # If specific comparison rule exists, use it
        ps = rules.get("product_specs", {})
        if key in ps:
            answer = random.choice(ps[key])
            reason = f"existing_comparison_rule ({key})"
        else:
            answer = generate_dynamic_comparison(a, b)
            reason = f"auto_generated_comparison ({a} vs {b})"
            # auto-learn comparison & specs
            store_product_specs_rule(a)
            store_product_specs_rule(b)
            store_comparison_rule(a, b)

        return {
            "answer": answer,
            "final_intent": "product_specs",
            "ml_intent": "product_specs",
            "reason": reason,
            "probabilities": {c: 0.0 for c in model.classes_},
            "model_version": model_version,
            "max_probability": 1.0
        }

    spec_keywords = ["specs", "specifications", "details", "features"]
    if any(word in q for word in spec_keywords):
        cleaned = q
        for w in spec_keywords:
            cleaned = cleaned.replace(w, "")
        product = cleaned.strip()

        if product:
            ps = rules.get("product_specs", {})
            if product in ps:
                answer = random.choice(ps[product])
                reason = f"existing_specs_rule ({product})"
            else:
                answer = f"Specifications placeholder for {product}. Add real details later."
                reason = f"auto_generated_specs ({product})"
                store_product_specs_rule(product)

            return {
                "answer": answer,
                "final_intent": "product_specs",
                "ml_intent": "product_specs",
                "reason": reason,
                "probabilities": {c: 0.0 for c in model.classes_},
                "model_version": model_version,
                "max_probability": 1.0
            }

    X = vectorizer.transform([question])
    probs = model.predict_proba(X)[0]
    ml_intent = model.predict(X)[0]
    ml_prob = float(max(probs))

    override_intent, override_keyword, score = fuzzy_intent_match(
        question, rules, fuzzy_threshold
    )

    if override_intent:
        final_intent = override_intent
        reason = f"fuzzy_override ({override_keyword}, score={score:.1f})"
    else:
        required = thresholds.get(ml_intent, 0.0)
        if ml_prob >= required:
            final_intent = ml_intent
            reason = "ok"
        else:
            final_intent = "other"
            reason = "low_confidence"

    answer = select_keyword_answer(final_intent, question)

    return {
        "answer": answer,
        "final_intent": final_intent,
        "ml_intent": ml_intent,
        "reason": reason,
        "probabilities": {cls: float(p) for cls, p in zip(model.classes_, probs)},
        "model_version": model_version,
        "max_probability": ml_prob
    }
# -----------------------------
if __name__ == "__main__":
    print(f"Interactive query. Model version: {model_version}")
    while True:
        q = input("\nAsk something (or 'q' to quit): ").strip()
        if q.lower() in ("q", "quit", "exit"):
            break

        result = infer(q)
        print(f"\nIntent: {result['final_intent']}  (ML: {result['ml_intent']}, reason: {result['reason']})")
        print("Probabilities:")
        for cls, p in result["probabilities"].items():
            print(f"  {cls}: {p:.3f}")
        print("\nAnswer:", result["answer"])
        