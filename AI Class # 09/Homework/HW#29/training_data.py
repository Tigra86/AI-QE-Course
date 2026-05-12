# =====================================================
# AI TRAINING DATA â€” INTENT CLASSIFICATION
# =====================================================

from collections import defaultdict
import math

# -----------------------------
# 1. CONFIG
# -----------------------------

CONFIDENCE_THRESHOLD = 0.70         # 70%

# -----------------------------
# 2. TRAINING DATA
# -----------------------------

def load_training_data(path: str):
    data = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            label, text = line.split("|", 1)
            data.append((text.strip(), label.strip()))
    return data

training_data = load_training_data("training_data.txt")

# -----------------------------
# 3. TRAINING PHASE
# -----------------------------

word_counts = defaultdict(lambda: defaultdict(int))
label_counts = defaultdict(int)
vocabulary = set()

for text, label in training_data:
    label_counts[label] += 1
    words = text.lower().split()
    for word in words:
        word_counts[label][word] += 1
        vocabulary.add(word)

# -----------------------------
# 4. SOFTMAX
# -----------------------------
def softmax(scores: dict) -> dict:
    max_score = max(scores.values())
    exp_scores = {
        label: math.exp(score - max_score)
        for label, score in scores.items()
    }
    total = sum(exp_scores.values())
    return {label: value / total for label, value in exp_scores.items()}

# -----------------------------
# 5. PREDICTION WITH CONFIDENCE
# -----------------------------
def predict(text):
    words = text.lower().split()
    scores = {}

    for label in label_counts:
        score = math.log(label_counts[label] / sum(label_counts.values()))

        for word in words:
            word_freq = word_counts[label][word] + 1
            total_words = sum(word_counts[label].values()) + len(vocabulary)
            score += math.log(word_freq / total_words)

        scores[label] = score

    probabilities = softmax(scores)
    best_label = max(probabilities, key=probabilities.get)
    confidence = probabilities[best_label]

    decision = (
        best_label
        if confidence >= CONFIDENCE_THRESHOLD
        else "ESCALATE_TO_HUMAN"
    )

    return decision, best_label, confidence, probabilities

# -----------------------------
# 6. TESTS
# -----------------------------

def load_tests(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return [line.strip() for line in f if line.strip()]

tests = load_tests("tests.txt")

# -----------------------------

for text in tests:
    decision, label, confidence, probs = predict(text)

    print(f"Question: '{text}'")
    print(f"Predicted label: {label}")
    print(f"Confidence: {confidence:.2%}")
    print(f"Decision: {decision}")

    print("Probabilities:")
    for l, p in probs.items():
        print(f"  {l}: {p:.2%}")

    print("-" * 60)
    