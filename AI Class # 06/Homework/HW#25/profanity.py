# -------------------------------------------------
# Profanity
# -------------------------------------------------

import re
from dataclasses import dataclass

PROFANITY_LIST = {
    "fuck", "shit", "asshole", "bitch"
}

ACADEMIC_TERMS = {
    "discuss", "discussion", "analyze", "analysis",
    "linguistics", "morphology", "syntax", "semantics",
    "term", "usage", "definition", "etymology",
    "academic", "scholarly", "literature"
}


ALLOW_THRESHOLD = 0.30
WARN_THRESHOLD  = 0.60

# --------------------------------------------
# Utilities
# --------------------------------------------

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    return text

def contains_profanity(text: str) -> bool:
    tokens = normalize(text).split()
    return any(
        t in PROFANITY_LIST or
        any(t.startswith(p) for p in PROFANITY_LIST)
        for t in tokens
    )

def is_academic_context(text: str) -> bool:
    tokens = normalize(text).split()
    return any(t in ACADEMIC_TERMS for t in tokens)

# --------------------------------------------
# Intrinsic Alignment Simulation (What the model "intends")
# --------------------------------------------

def intrinsic_alignment_score(text: str) -> float:
    text_l = text.lower()

    # Academic / descriptive use
    if is_academic_context(text_l):
        return 0.10

    # Directed abuse
    if "you are" in text_l and contains_profanity(text_l):
        return 0.90

    # Expressive profanity
    if contains_profanity(text_l):
        return 0.40

    return 0.05

# --------------------------------------------
# Extrinsic Alignment (Policy Enforcement)
# --------------------------------------------

@dataclass
class Decision:
    action: str
    reason: str
    alignment_score: float

def policy_engine(text: str) -> Decision:
    score = intrinsic_alignment_score(text)
    profanity = contains_profanity(text)

    if score >= WARN_THRESHOLD:
        return Decision(
            action="BLOCK",
            reason="Abusive or harassing profanity",
            alignment_score=score
        )

    if profanity and score >= ALLOW_THRESHOLD:
        return Decision(
            action="WARN",
            reason="Profanity detected; allowed but discouraged",
            alignment_score=score
        )

    return Decision(
        action="ALLOW",
        reason="Aligned with acceptable use",
        alignment_score=score
    )

# -------------------------------------------------
def run_profanity(input_file="profanity_input.txt"):
    print("\n=== Inference Results (Profanity) ===\n")
    with open(input_file, encoding="utf-8-sig") as f:
        for line in f:
            sentence = line.strip()
            if not sentence:
                continue

            decision = policy_engine(sentence)
            print("-" * 60)
            print(f"INPUT:   {sentence}")
            print(f"ACTION:  {decision.action}")
            print(f"REASON:  {decision.reason}")
            print(f"SCORE:   {decision.alignment_score:.2f}")


if __name__ == "__main__":
    run_profanity()