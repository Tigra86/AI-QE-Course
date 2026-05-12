import openai
import numpy as np
import csv
import re
import os

# ==========================
# CONFIG
# ==========================

openai.api_key      = os.environ.get('OPENAI_API_KEY')
MODEL_GENERATION    = "gpt-4.1"    # gpt-4.1 or gpt-3.5-turbo
MODEL_EMBEDDING     = "text-embedding-3-small"

TESTS_CSV           = "ai_tests.csv"
OUTPUT_CSV          = "ai_results.csv"

SIMILARITY_THRESHOLD_FACT      = 0.85
SIMILARITY_THRESHOLD_NONEXIST  = 0.75

# ==========================
# LOAD TEST CASES
# ==========================

def load_tests(path):
    tests = []

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")

        normalized_fieldnames = [col.strip().lower() for col in reader.fieldnames]
        print("Detected normalized columns:", normalized_fieldnames)

        for row in reader:
            clean = {k.strip().lower(): v.strip() for k, v in row.items()}

            tests.append({
                "id": int(clean.get("id")),
                "mode": clean.get("mode"),
                "prompt": clean.get("prompt"),
                "ground_truth": clean.get("ground_truth")
            })

    return tests

# ==========================
# EMBEDDINGS + SIMILARITY
# ==========================

def get_embedding(text: str) -> np.ndarray:
    resp = openai.embeddings.create(
        model=MODEL_EMBEDDING,
        input=text
    )
    return np.array(resp.data[0].embedding, dtype=float)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def contains_any(text: str, keywords) -> bool:
    text_low = text.lower()
    return any(k in text_low for k in keywords)

# ==========================
# RULE-BASED CHECKS
# ==========================

DENIAL_KEYWORDS = [
    "There is no country or region",
    "so it does not have a capital city",
    "does not exist",
    "is not real",
    "not a real",
    "no such",
    "fictional",
    "imaginary",
    "cannot find any information",
    "i could not find any information",
    "unknown",
]

WRONG_CONFIDENT_PHRASES_FOR_NONEXIST = [
    "the capital is",
    "the capital city is",
    "is located in",
    "is a country in",
]


def rule_check_nonexistent(model_output: str) -> dict:
    out = model_output.lower()
    has_denial = contains_any(out, DENIAL_KEYWORDS)
    has_confident_real = contains_any(out, WRONG_CONFIDENT_PHRASES_FOR_NONEXIST)

    return {
        "has_denial": has_denial,
        "has_confident_real": has_confident_real
    }


def rule_check_factual(model_output: str) -> dict:
    out = model_output.lower()
    has_denial = contains_any(out, DENIAL_KEYWORDS)
    return {"has_denial": has_denial}


# ==========================
# MAIN HYBRID TEST
# ==========================

def run_hybrid_test(test: dict) -> dict:
    test_id      = test["id"]
    prompt       = test["prompt"]
    ground_truth = test["ground_truth"]
    mode         = test["mode"]

    print(f"\nTest {test_id} | Mode: {mode}")
    print(f"  Prompt: {prompt}")

    # 01. Ask GPT
    completion = openai.chat.completions.create(
        model=MODEL_GENERATION,
        messages=[{"role": "user", "content": prompt}]
    )
    model_output = completion.choices[0].message.content.strip()
    print(f"   Model output: {model_output}")

    # 02. Embeddings
    emb_output = get_embedding(model_output)
    emb_truth  = get_embedding(ground_truth)

    similarity = cosine_similarity(emb_output, emb_truth)
    print(f"   Cosine similarity: {similarity:.3f}")

    # 03. Rule checks
    rule_fail = False
    rules_detail = {}

    if mode == "nonexistent":
        rules_detail = rule_check_nonexistent(model_output)
        if not rules_detail["has_denial"] or rules_detail["has_confident_real"]:
            rule_fail = True
        sim_threshold = SIMILARITY_THRESHOLD_NONEXIST

    elif mode == "factual":
        rules_detail = rule_check_factual(model_output)
        if rules_detail["has_denial"]:
            rule_fail = True
        sim_threshold = SIMILARITY_THRESHOLD_FACT

    else:
        sim_threshold = SIMILARITY_THRESHOLD_FACT

    similarity_fail = similarity < sim_threshold
    hallucination = rule_fail or similarity_fail

    print(f"   Rule fail:       {rule_fail}")
    print(f"   Similarity fail: {similarity_fail}")
    print(f"   HALLUCINATION?   {hallucination}")

    return {
        "id": test_id,
        "mode": mode,
        "prompt": prompt,
        "ground_truth": ground_truth,
        "model_output": model_output,
        "similarity": similarity,
        "similarity_threshold": sim_threshold,
        "rule_fail": rule_fail,
        "similarity_fail": similarity_fail,
        "hallucination": hallucination,
        "rules_detail": rules_detail,
    }


# ==========================
# MAIN ENTRY POINT
# ==========================

def main():
    if not os.path.exists(TESTS_CSV):
        raise FileNotFoundError(f"Test file not found: {TESTS_CSV}")

    tests = load_tests(TESTS_CSV)
    results = []

    for t in tests:
        results.append(run_hybrid_test(t))

    # OUTPUT CSV WITH SEMICOLON SEPARATOR
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id", "mode", "prompt", "ground_truth", "model_output",
                "similarity", "similarity_threshold",
                "rule_fail", "similarity_fail", "hallucination", "rules_detail"
            ]
        )
        writer.writeheader()

        for r in results:
            row = r.copy()
            row["rules_detail"] = str(r["rules_detail"])
            writer.writerow(row)

    print(f"\nDone! Results saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()