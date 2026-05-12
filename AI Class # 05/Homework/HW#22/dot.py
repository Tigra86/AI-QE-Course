from sentence_transformers import SentenceTransformer
import numpy as np

def dot_product_similarity(a, b):
    return float(np.dot(a, b))

model = SentenceTransformer("multi-qa-MiniLM-L6-dot-v1")                          # 384 dimensions Not Normalized
# model = SentenceTransformer("sentence-transformers/multi-qa-mpnet-base-dot-v1")   # 768 dimensions Not Normalized
# model = SentenceTransformer("sentence-transformers/all-roberta-large-v1")         # 1024 dimensions Normalized
# model = SentenceTransformer("sentence-transformers/gtr-t5-xl")                    # 2048 dimensions Normalized
# model = SentenceTransformer("sentence-transformers/gtr-t5-xxl")                   # 4096 dimensions Normalized

def dot_semantic_similarity(text1, text2):
    emb1 = model.encode(text1, normalize_embeddings=False)
    emb2 = model.encode(text2, normalize_embeddings=False)
    sim = dot_product_similarity(emb1, emb2)
    return sim

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

print("Dot-Product semantic similarity")

for a, b in pairs:
    print(f"{a} ↔ {b} = {dot_semantic_similarity(a, b):.3f}")
