from rapidfuzz import fuzz

def rapidfuzz_similarity(text1, text2):
    return fuzz.token_sort_ratio(text1, text2) / 100.0

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
    print(f"{a} ↔ {b} = {rapidfuzz_similarity(a, b):.3f}")
    