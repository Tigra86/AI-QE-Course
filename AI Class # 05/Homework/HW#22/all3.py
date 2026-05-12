from sentence_transformers import SentenceTransformer
import numpy as np
from tabulate import tabulate

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def euclidean_distance(a, b):
    return np.linalg.norm(a - b)

def true_dot_product(a, b):
    return np.dot(a, b)

MODELS = {"384 dimensions":    "multi-qa-MiniLM-L6-dot-v1"}                          # 384 dimensions Not Normalized
# MODELS = {"768 dimensions":    "sentence-transformers/multi-qa-mpnet-base-dot-v1"}   # 768 dimensions Not Normalized
# MODELS = {"1024 dimensions":   "sentence-transformers/all-roberta-large-v1"}         # 1024 dimensions Normalized
# MODELS = {"2048 dimensions":   "sentence-transformers/gtr-t5-xl"}                    # 2048 dimensions Normalized
# MODELS = {"4096 dimensions":   "sentence-transformers/gtr-t5-xxl"}                   # 4096 dimensions Normalized

# ======================================

PAIRS = [
    ("apple", "apple"),
    ("fuzzy wuzzy", "wuzzy fuzzy"),
    ("Python", "Pytho"),
    ("color", "colour"),
    ("night", "knight"),
    ("apple", "pear"),
    ("kitten", "sitting"),
    ("programming", "gramming"),
    ("machine learning", "AI"),
    ("football", "electricity"),
]

# ======================================

def compare(model, text1, text2):

    # Raw, unnormalized embeddings
    r1, r2 = model.encode([text1, text2], normalize_embeddings=False)

    # Normalized vectors (for cosine)
    n1 = r1 / np.linalg.norm(r1)
    n2 = r2 / np.linalg.norm(r2)

    cosine = cosine_similarity(n1, n2)     # semantic angle
    dot    = true_dot_product(r1, r2)      # magnitude × alignment
    dist   = euclidean_distance(r1, r2)    # geometric distance

    return cosine, dot, dist

for model_name, model_id in MODELS.items():
    print("\n" + "="*80)
    print(f"MODEL: {model_name}   ({model_id})")
    print("="*80)

    model = SentenceTransformer(model_id)

    table = []
    headers = ["Pair", "Cosine", "Dot-Product", "Euclidean"]

    for a, b in PAIRS:
        cosine, dot, dist = compare(model, a, b)
        table.append([
            f"{a} ↔ {b}",
            f"{cosine:.3f}",
            f"{dot:.3f}",
            f"{dist:.3f}",
        ])

    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
