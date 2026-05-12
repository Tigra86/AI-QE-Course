from sentence_transformers import SentenceTransformer
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

model = SentenceTransformer("multi-qa-MiniLM-L6-dot-v1")                          # 384 dimensions Not Normalized
# model = SentenceTransformer("sentence-transformers/multi-qa-mpnet-base-dot-v1")   # 768 dimensions Not Normalized
# model = SentenceTransformer("sentence-transformers/all-roberta-large-v1")         # 1024 dimensions Normalized
# model = SentenceTransformer("sentence-transformers/gtr-t5-xl")                    # 2048 dimensions Normalized
# model = SentenceTransformer("sentence-transformers/gtr-t5-xxl")                   # 4096 dimensions Normalized

def semantic_similarity(text1, text2):
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)
    sim = cosine_similarity(emb1, emb2)
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

print("Semantic/Cosine similarity")

for a, b in pairs:
    print(f"{a} ↔ {b} = {semantic_similarity(a, b):.3f}")
