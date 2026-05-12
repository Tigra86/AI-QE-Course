from ufal.udpipe import Model, Pipeline
import csv
import re

MODEL_RU = "ru.udpipe"
MODEL_EN = "en.udpipe"
MODEL_UK = "uk.udpipe"

INPUT_FILE = "sentences.txt"
OUTPUT_CSV = "errors.csv"

def load_udpipe_model(path):
    model = Model.load(path)
    if not model:
        raise RuntimeError(f"Cannot load UDPipe model: {path}")
    return model

ru_model = load_udpipe_model(MODEL_RU)
en_model = load_udpipe_model(MODEL_EN)
uk_model = load_udpipe_model(MODEL_UK)

ru_nlp = Pipeline(ru_model, "tokenize", "tag", "parse", "conllu")
en_nlp = Pipeline(en_model, "tokenize", "tag", "parse", "conllu")
uk_nlp = Pipeline(uk_model, "tokenize", "tag", "parse", "conllu")

def detect_language(text):
    if re.search(r"[А-Яа-яЁёЇїІіЄєҐґ]", text):
        if re.search(r"[ЇїІіЄєҐґ]", text):
            return "uk"
        else:
            return "ru"
    return "en"

MATH_SYMBOLS = set("+-=*/^()[]{}")

def is_math_sentence(text):
    math_count = sum(ch in MATH_SYMBOLS for ch in text)
    ratio = math_count / max(1, len(text))
    return ratio >= 0.20

def parse_conllu(conllu_text):
    sentences = []
    current = []

    for line in conllu_text.splitlines():
        line = line.strip()
        if not line:
            if current:
                sentences.append(current)
                current = []
            continue

        if line.startswith("#"):
            continue

        cols = line.split("\t")
        if len(cols) != 10:
            continue

        tid = cols[0]
        if "-" in tid or "." in tid:
            continue

        try:
            tid_int = int(tid)
        except ValueError:
            continue

        token = {
            "id": tid_int,
            "form": cols[1],
            "lemma": cols[2],
            "upos": cols[3],
            "head": int(cols[6]) if cols[6].isdigit() else 0,
            "deprel": cols[7]
        }
        current.append(token)

    if current:
        sentences.append(current)
    return sentences

def analyze_tokens(tokens, original_text):
    found_subj = False
    found_root = False
    found_verb = False

    math_sentence = is_math_sentence(original_text)

    for tok in tokens:
        if tok["deprel"] in ("nsubj", "nsubj:pass"):
            found_subj = True
        if tok["deprel"] == "root":
            found_root = True
        if tok["upos"] == "VERB":
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

    return len(errors) == 0, errors

def analyze_file(input_file, output_csv):
    results = []

    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    PIPELINES = {
        "ru": ru_nlp,
        "uk": uk_nlp,
        "en": en_nlp,
    }

    for line in lines:
        lang = detect_language(line)

        nlp = PIPELINES[lang]
        processed = nlp.process(line)
        parsed_sentences = parse_conllu(processed)

        for tokens in parsed_sentences:
            text = " ".join(tok["form"] for tok in tokens)
            ok, errors = analyze_tokens(tokens, text)

            results.append({
                "sentence": text,
                "language": lang,
                "status": "OK" if ok else "BAD",
                "errors": "; ".join(errors) if errors else ""
            })

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["sentence", "language", "status", "errors"])
        writer.writeheader()
        writer.writerows(results)

    return results

res = analyze_file(INPUT_FILE, OUTPUT_CSV)

for r in res:
    print(f"[{r['language']}] {r['sentence']} → {r['status']} ({r['errors']})")