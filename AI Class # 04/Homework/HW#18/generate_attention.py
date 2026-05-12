# ================================================================
# ATTENTION ENGINE
# ================================================================

import os
import re
import json
import hashlib
import numpy as np

# ================================================================
# TOKENIZATION
# ================================================================
def tokenize_sentence(sentence: str) -> list[str]:
    return re.findall(r"[A-Za-z]+", sentence.lower())

# ================================================================
# STOPWORDS / TEMPORAL WORDS
# ================================================================
STOPWORDS = {
    "the","a","an","and","or","but","if","while","this","that","to","in",
    "on","for","with","is","was","are","were","of","at","by","it","as",
    "be","from","has","had","have","not","will","would","can","could",
    "do","does","did","so","than","then","too","very","just","after","before"
}

TEMPORAL_WORDS = {
    "yesterday", "today", "tomorrow",
    "early", "late",
    "daily", "weekly", "monthly", "yearly",
    "recently", "currently", "formerly"
}

# ================================================================
# HASH-BASED WORD EMBEDDINGS (DETERMINISTIC)
# ================================================================
EMBED_DIM = 64

def word_embedding(word: str) -> np.ndarray:
    h = hashlib.sha256(word.encode("utf-8")).digest()
    vec = np.frombuffer(h, dtype=np.uint8)[:EMBED_DIM].astype(np.float64)
    vec -= vec.mean()
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec

# ================================================================
# MATH UTILITIES
# ================================================================
def dot(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

def softmax(xs: list[float]) -> np.ndarray:
    xs = np.array(xs, dtype=np.float64)
    e = np.exp(xs - xs.max())
    return e / e.sum()

# ================================================================
# FOCUS WORD HEURISTIC
# ================================================================
ADJECTIVE_SUFFIXES = ("ing", "ed", "ous", "ful", "able", "ive", "al", "y")

def detect_focus_word(words: list[str]) -> str:
    candidates = [w for w in words if w not in STOPWORDS and w not in TEMPORAL_WORDS]
    if not candidates:
        return words[0]

    adjectives = [w for w in candidates if w.endswith(ADJECTIVE_SUFFIXES)]
    if adjectives:
        return adjectives[-1]  # predicate adjectives often occur late

    verbs = [w for w in candidates if w.endswith(("ed", "ing"))]
    if verbs:
        return verbs[-1]

    return max(candidates, key=len)

# ================================================================
# HELPERS
# ================================================================
def find_subject_idx(words: list[str], focus_idx: int) -> int | None:
    """Nearest content word to the left of focus (excluding stopwords/temporal)."""
    for i in range(focus_idx - 1, -1, -1):
        if words[i] not in STOPWORDS and words[i] not in TEMPORAL_WORDS:
            return i
    return None

def cap_and_redistribute(att: np.ndarray, cap_idx: int, cap: float, eligible_idxs: list[int]) -> np.ndarray:
    """Cap att[cap_idx] to cap and redistribute excess proportionally to eligible_idxs."""
    if att[cap_idx] <= cap:
        return att

    excess = float(att[cap_idx] - cap)
    att[cap_idx] = cap

    if not eligible_idxs:
        return att / float(att.sum())

    s = float(sum(att[i] for i in eligible_idxs))
    if s <= 0:
        share = excess / len(eligible_idxs)
        for i in eligible_idxs:
            att[i] += share
        return att / float(att.sum())

    for i in eligible_idxs:
        att[i] += excess * (float(att[i]) / s)

    return att

# ================================================================
# ATTENTION COMPUTATION
# ================================================================
def compute_attention(sentence: str) -> dict | None:
    words = tokenize_sentence(sentence)
    if not words:
        return None

    focus_word = detect_focus_word(words)
    focus_idx = words.index(focus_word)

    focus_vec = word_embedding(focus_word)
    similarities = [dot(focus_vec, word_embedding(w)) for w in words]

    # -------------------------------
    # Pre-softmax penalties
    # -------------------------------
    penalized = []
    for w, s in zip(words, similarities):
        if w == focus_word:
            s *= 0.25          # self-penalty
        if w in STOPWORDS:
            s *= 0.35          # stopword penalty
        penalized.append(s)

    # -------------------------------
    # Bias: predicate adjective → subject
    # -------------------------------
    if focus_word.endswith(ADJECTIVE_SUFFIXES):
        subj = find_subject_idx(words, focus_idx)
        if subj is not None:
            penalized[subj] *= 3.0    # strong subject boost

    # -------------------------------
    # Softmax
    # -------------------------------
    attention = softmax(penalized)

    # -------------------------------
    # Cap focus (cannot dominate)
    # -------------------------------
    attention = cap_and_redistribute(
        att=attention,
        cap_idx=focus_idx,
        cap=0.15,
        eligible_idxs=[i for i in range(len(words)) if i != focus_idx]
    )

    # -------------------------------
    # Cap stopwords (cannot dominate)
    # -------------------------------
    for i, w in enumerate(words):
        if w in STOPWORDS:
            attention = cap_and_redistribute(
                att=attention,
                cap_idx=i,
                cap=0.08,
                eligible_idxs=[j for j in range(len(words)) if j != i and words[j] not in STOPWORDS]
            )

    # -------------------------------
    # FINAL HARD RULE: subject MUST be primary attention target
    # (apply after all caps/redistribution)
    # -------------------------------
    if focus_word.endswith(ADJECTIVE_SUFFIXES):
        subj = find_subject_idx(words, focus_idx)
        if subj is not None:
            max_idx = int(attention.argmax())
            if max_idx != subj:
                attention[subj], attention[max_idx] = attention[max_idx], attention[subj]

    # Final renormalization (defensive)
    attention = attention / float(attention.sum())

    return {
        "sentence": sentence,
        "focus_word": focus_word,
        "raw_scores": {w: round(float(s), 4) for w, s in zip(words, penalized)},
        "softmax_attention_weights": {w: round(float(a), 4) for w, a in zip(words, attention)},
        "softmax_sum": round(float(attention.sum()), 6),
    }

# ================================================================
# MAIN PROCESSOR
# ================================================================
def process_sentences(input_file: str) -> None:
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"{input_file} not found.")

    with open(input_file, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    os.makedirs("attention_outputs", exist_ok=True)

    for i, sentence in enumerate(sentences, 1):
        result = compute_attention(sentence)
        if not result:
            continue

        path = f"attention_outputs/attention_{i}.json"
        with open(path, "w", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, indent=4)

        print(f"[OK] {path} → focus = {result['focus_word']}")

# ================================================================
# ENTRY POINT
# ================================================================
if __name__ == "__main__":
    process_sentences("sentences.txt")