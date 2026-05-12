from sentence_transformers import SentenceTransformer
import numpy as np

def euclidean_distance(a, b):
    return np.linalg.norm(a - b)

model = SentenceTransformer("multi-qa-MiniLM-L6-dot-v1")                          # 384 dimensions Not Normalized
# model = SentenceTransformer("sentence-transformers/multi-qa-mpnet-base-dot-v1")   # 768 dimensions Not Normalized
# model = SentenceTransformer("sentence-transformers/all-roberta-large-v1")         # 1024 dimensions Normalized
# model = SentenceTransformer("sentence-transformers/gtr-t5-xl")                    # 2048 dimensions Normalized
# model = SentenceTransformer("sentence-transformers/gtr-t5-xxl")                   # 4096 dimensions Normalized

def semantic_distance(text1, text2):
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)
    dist = euclidean_distance(emb1, emb2)
    return dist

pairs = [
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

print("Semantic/Euclidean Distance")

for a, b in pairs:
    print(f"{a} ↔ {b} = {semantic_distance(a, b):.3f}")
