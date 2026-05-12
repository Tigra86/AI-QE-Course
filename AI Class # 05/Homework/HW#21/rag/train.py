import glob
import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

def load_dataset(path):
    texts = []
    labels = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            texts.append(obj["text"])
            labels.append(obj["label"])
    return texts, labels


def load_all_datasets(pattern="datasets/*.jsonl"):
    all_texts = []
    all_labels = []
    for file in glob.glob(pattern):
        t, l = load_dataset(file)
        all_texts.extend(t)
        all_labels.extend(l)
        print(f"Loaded dataset: {file}  ({len(t)} samples)")
    return all_texts, all_labels

def load_rules(folder="rules/*.json"):
    rules = {}
    for file in glob.glob(folder):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Merge into top-level dict
        for intent, groups in data.items():
            if intent not in rules:
                rules[intent] = {}
            rules[intent].update(groups)

        print(f"Loaded rule file: {file}")
    return rules

def load_fallback(path="fallback_messages.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            fb = json.load(f)
        print("Loaded fallback_messages.json")
        return fb
    except FileNotFoundError:
        print("fallback_messages.json NOT FOUND - using defaults.")
        return {
            "other": [
                "I'm not sure what you mean - could you rephrase?",
                "Sorry, I didnâ€™t understand - try asking in a different way."
            ]
        }

def main():

    print("=== LOADING DATASETS ===")
    texts, labels = load_all_datasets("datasets/*.jsonl")
    print(f"Total training samples: {len(texts)}")

    print("\n=== LOADING RULE FILES ===")
    rules = load_rules("rules/*.json")

    print("\n=== LOADING FALLBACK MESSAGES ===")
    fallback_messages = load_fallback("fallback_messages.json")

    print("\n=== VECTORIZE TEXTS ===")
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)

    print("\n=== TRAIN MODEL ===")
    model = LogisticRegression(max_iter=500)
    model.fit(X, labels)

    intent_thresholds = {
        "product_specs": 0.45,
        "technical_how_to": 0.45,
        "local_information": 0.45,
        "other": 0.20
    }

    PACK = {
        "vectorizer": vectorizer,
        "model": model,
        "rules": rules,
        "fallback_messages": fallback_messages,
        "intent_thresholds": intent_thresholds,
        "fuzzy_threshold": 70,
        "training_metadata": {
            "total_samples": len(texts),
            "unique_labels": list(set(labels))
        },
        "model_version": "1.0.0"
    }

    print("\n=== SAVING MODEL PACK ===")
    joblib.dump(PACK, "model.pkl")
    print("Saved to model.pkl")


if __name__ == "__main__":
    main()