import stanza
import csv
import re

stanza.download("ru")
nlp = stanza.Pipeline("ru")

MATH_SYMBOLS = set("=+-*/^()")

def is_math_sentence(text):
    # if ~20% of characters are mathematical
    math_count = sum(ch in MATH_SYMBOLS for ch in text)
    ratio = math_count / max(1, len(text))
    return ratio >= 0.20

def analyze_sentence(sentence):
    text = sentence.text

    found_subj = False
    found_root = False
    found_verb = False

    math_sentence = is_math_sentence(text)

    for w in sentence.words:
        if w.deprel in ("nsubj", "nsubj:pass"):
            found_subj = True
        if w.deprel == "root":
            found_root = True
        if w.upos == "VERB":
            found_verb = True

    errors = []

    if math_sentence:
        errors.append("MATH::SENTENCE")
        return False, errors
    if not found_subj:
        errors.append("NO::SUBJECT")
    if not found_root:
        errors.append("NO::PREDICATE")
    if not found_verb:
        errors.append("NO::VERB")

    is_ok = len(errors) == 0
    return is_ok, errors

def analyze_file(input_file, output_csv="errors_ru.csv"):
    results = []

    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for text in lines:
        doc = nlp(text)
        for sent in doc.sentences:
            ok, errors = analyze_sentence(sent)
            results.append({
                "sentence": sent.text,
                "status": "OK" if ok else "BAD",
                "errors": "; ".join(errors) if errors else ""
            })

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["sentence", "status", "errors"])
        writer.writeheader()
        writer.writerows(results)

    return results

results = analyze_file("sentences_ru.txt")

for r in results:
    print(f"{r['sentence']} â†’ {r['status']} ({r['errors']})")
