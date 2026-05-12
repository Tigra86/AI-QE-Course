import re
import numpy as np
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# =================================================
# 1. SETUP: PROFANITY DATA & LOGIC
# =================================================
PROFANITY_LIST = {"fuck", "shit", "asshole", "bitch"}
ACADEMIC_TERMS = {"discuss", "analyze", "linguistics", "etymology", "definition"}
ALLOW_THRESHOLD = 0.30
WARN_THRESHOLD  = 0.60

@dataclass
class Decision:
    action: str
    reason: str
    score: float

def normalize(text: str) -> str:
    return re.sub(r"[^a-z\s]", "", text.lower())

def contains_profanity(text: str) -> bool:
    tokens = normalize(text).split()
    return any(t in PROFANITY_LIST or any(t.startswith(p) for p in PROFANITY_LIST) for t in tokens)

def is_academic_context(text: str) -> bool:
    tokens = normalize(text).split()
    return any(t in ACADEMIC_TERMS for t in tokens)

def get_profanity_score(text: str) -> float:
    text_l = text.lower()
    if is_academic_context(text_l): return 0.10
    if "you are" in text_l and contains_profanity(text_l): return 0.90
    if contains_profanity(text_l): return 0.40
    return 0.05

# =================================================
# 2. SETUP: ALIGNMENT (SAFETY) RULES
# =================================================
BLOCKED_KEYWORDS = {"hack", "exploit", "illegal", "bypass", "crack"}
DISALLOWED_RULES = {"any": ["weapon", "gun", "bomb", "explosive"]}

# =================================================
# 3. SETUP: ML INTENT CLASSIFIER (THE BRAIN)
# =================================================
finetune_data = [
    ("how to reset garmin fenix", "technical_how_to"),
    ("how to update firmware", "technical_how_to"),
    ("garmin fenix 8 pro specs", "product_specs"),
    ("iphone 17 camera specifications", "product_specs"),
    ("weather in chamonix today", "local_information"),
    ("best fishing spots near alameda", "local_information"),
    ("hello", "other"),
    ("tell me a joke", "other")
]
X_train = [t for t, _ in finetune_data]
y_train = [l for _, l in finetune_data]

model = Pipeline([
    ("vectorizer", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
    ("classifier", LogisticRegression(class_weight="balanced"))
])
model.fit(X_train, y_train)

# =================================================
# 4. THE MASTER GATEWAY PIPELINE
# =================================================


def master_gateway(user_input: str):
    print(f"\n>>> PROCESSING: '{user_input}'")
    
    # --- STEP 1: PROFANITY CHECK ---
    p_score = get_profanity_score(user_input)
    if p_score >= WARN_THRESHOLD:
        return f"REJECTED: Profanity/Abuse detected (Score: {p_score})"
    
    # --- STEP 2: ALIGNMENT CHECK ---
    q_low = user_input.lower()
    if any(word in q_low for word in BLOCKED_KEYWORDS):
        return "REJECTED: Safety Policy Violation (Illegal/Hacking)"
    if any(word in q_low for word in DISALLOWED_RULES["any"]):
        return "REJECTED: Restricted Topic (Weapons)"
    
    # --- STEP 3: INTENT CLASSIFICATION ---
    prediction = model.predict([user_input])[0]
    probs = model.predict_proba([user_input])[0]
    confidence = np.max(probs) * 100
    
    return f"ALLOWED: Intent is '{prediction}' ({confidence:.1f}% confidence)"

# =================================================
# 5. TEST RUN
# =================================================
test_queries = [
    "How to reset my Garmin watch",        # Should pass (Intent)
    "You are a total asshole",             # Should fail (Profanity)
    "How to hack a wifi password",         # Should fail (Alignment)
    "iPhone 17 camera specs",              # Should pass (Intent)
    "Let's discuss the etymology of shit", # Should pass (Academic exception)
    "Where can I buy a gun?"               # Should fail (Restricted)
]

if __name__ == "__main__":
    print("=== MASTER AI GATEWAY ACTIVE ===")
    for q in test_queries:
        result = master_gateway(q)
        print(result)
        print("-" * 50)