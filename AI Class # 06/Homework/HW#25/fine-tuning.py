import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# --------------------------------------
# 1. Pretraining texts (NO labels)
# --------------------------------------

pretrain_texts = [
    "Hello world",
    "What is artificial intelligence",
    "The iPhone has a battery",
    "How to reset a device",
]

pretrain_labels = ["other"] * len(pretrain_texts)

# --------------------------------------
# 2. Fine-tuning data (YOUR NEW DATASET)
# --------------------------------------

finetune_data = [
    # --- Category: technical_how_to ---
    ("how to reset garmin fenix", "technical_how_to"),
    ("factory reset instructions for fenix 7", "technical_how_to"),
    ("how to update firmware on speedcoach", "technical_how_to"),
    ("steps to calibrate garmin compass", "technical_how_to"),
    ("garmin watch not syncing fix", "technical_how_to"),
    ("fix bluetooth issues on android", "technical_how_to"),
    ("how to pair garmin heart rate monitor", "technical_how_to"),
    ("how to update tesla software", "technical_how_to"),
    ("troubleshoot iphone wifi connection", "technical_how_to"),
    ("guide to installing latest os", "technical_how_to"),
    ("how to clean carbon paddle shaft", "technical_how_to"),
    ("improving paddling cadence techniques", "technical_how_to"),

    # --- Category: product_specs ---
    ("garmin fenix 8 pro specs", "product_specs"),
    ("garmin fenix 8 pro weight and dimensions", "product_specs"),
    ("apple watch ultra battery life", "product_specs"),
    ("iphone 17 camera specifications", "product_specs"),
    ("iphone 17 screen resolution", "product_specs"),
    ("tesla model y range and top speed", "product_specs"),
    ("tesla model 3 battery capacity kwh", "product_specs"),
    ("macbook pro m3 chip technical details", "product_specs"),
    ("samsung galaxy s24 ultra sensor size", "product_specs"),
    ("sony a7v megapixels and iso range", "product_specs"),
    ("bmw m850i engine specs", "product_specs"),
    ("carbon fiber paddle weight", "product_specs"),

    # --- Category: local_information ---
    ("best fishing spots near alameda", "local_information"),
    ("where to fish in san francisco bay", "local_information"),
    ("parking near half moon bay harbor", "local_information"),
    ("best kayaking launch spots in oakland", "local_information"),
    ("is mont blanc open this season", "local_information"),
    ("weather in chamonix today", "local_information"),
    ("tides near san mateo bridge", "local_information"),
    ("boat ramp locations near sausalito", "local_information"),
    ("where can i kayak in lake tahoe", "local_information"),
    ("current temperature in san francisco", "local_information"),

    # --- Category: other ---
    ("hello", "other"),
    ("how are you doing today", "other"),
    ("tell me a joke", "other"),
    ("explain the theory of relativity", "other"),
    ("who won the world series", "other"),
    ("what is the meaning of life", "other"),
    ("how does machine learning work", "other"),
    ("who invented the internet", "other")
]

# --------------------------------------
# 3. Combine datasets (THIS IS FINE-TUNING)
# --------------------------------------

X_text = pretrain_texts + [t for t, _ in finetune_data]
y_labels = pretrain_labels + [y for _, y in finetune_data]

# --------------------------------------
# 4. Model pipeline
# --------------------------------------

model = Pipeline([
    ("vectorizer", TfidfVectorizer(
        ngram_range=(1, 2),
        lowercase=True
    )),
    ("classifier", LogisticRegression(
        max_iter=300,
        class_weight="balanced"
    ))
])

# --------------------------------------
# 5. Train
# --------------------------------------

model.fit(X_text, y_labels)

# --------------------------------------
# 6. Load test queries from file
# --------------------------------------

def load_queries(path="fine-tuning_input.txt"):
    with open(path, encoding="utf-8-sig") as f:
        return [line.strip() for line in f if line.strip()]

test_queries = load_queries()

# --------------------------------------
# 7. Inference (NO alignment)
# --------------------------------------

print("\n=== Inference Results (Fine-Tuning) ===\n")

for q in test_queries:
    probs = model.predict_proba([q])[0]
    classes = model.classes_
    prediction = model.predict([q])[0]

    print(f"Input: {q}")
    print(f"Prediction: {prediction}")
    print("Probabilities:")
    for c, p in zip(classes, probs):
        print(f"  {c}: {p:.3f}")
    print("-" * 40)