# -------------------------------------------------
# Alignment
# -------------------------------------------------

BLOCKED_KEYWORDS = {"hack", "exploit", "illegal", "bypass", "crack", "trojan", "phishing"}
DISALLOWED_RULES = {"any": ["weapon", "gun", "bomb", "explosive"]}

REFUSAL_MESSAGE = "This request is not allowed."
RESTRICTED_MESSAGE = "That topic is restricted."

# -------------------------------------------------
# ML inference
# -------------------------------------------------
def fake_ml_inference(text: str):
    text_l = text.lower()

    if "spec" in text_l:
        return "product_specs", 0.91
    if "how to" in text_l:
        return "technical_how_to", 0.88
    if "where" in text_l:
        return "local_information", 0.83
    return "other", 0.65

# -------------------------------------------------
# Alignment layer
# -------------------------------------------------
def apply_alignment(question, ml_intent, probability):
    q = question.lower()

    # Hard block
    for word in BLOCKED_KEYWORDS:
        if word in q:
            return {
                "final_intent": "blocked",
                "answer": REFUSAL_MESSAGE,
                "reason": "policy_block",
            }

    # Global restricted
    for word in DISALLOWED_RULES.get("any", []):
        if word in q:
            return {
                "final_intent": "restricted",
                "answer": RESTRICTED_MESSAGE,
                "reason": "policy_restricted",
            }

    # Allowed
    return {
        "final_intent": ml_intent,
        "answer": f"Allowed response for intent: {ml_intent}",
        "reason": "allowed",
    }

# -------------------------------------------------
# Run demo
# -------------------------------------------------
def run_demo(input_file="alligment_input.txt"):
    print("\n=== Inference Results (Alignment) ===\n")
    with open(input_file, encoding="utf-8-sig") as f:
        for line in f:
            sentence = line.strip()
            if not sentence:
                continue

            ml_intent, prob = fake_ml_inference(sentence)
            aligned = apply_alignment(sentence, ml_intent, prob)

            print(f"Input: {sentence}")
            print(f"ML Intent: {ml_intent} (p={prob:.2f})")
            print(f"Final Intent: {aligned['final_intent']}")
            print(f"Answer: {aligned['answer']}")
            print(f"Reason: {aligned['reason']}")
            print("-" * 50)


if __name__ == "__main__":
    run_demo()