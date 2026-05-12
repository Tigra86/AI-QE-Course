# ============================================================
# python 2_generate_assets.py
# python 2_generate_assets.py --source qa.json
# python 2_generate_assets.py --source data/
# ============================================================

import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict, Counter

# ============================================================
# CLI CONFIG
# ============================================================

parser = argparse.ArgumentParser(
    description="Generate training, eval, and rules datasets (flat files, multi-answer)"
)

parser.add_argument(
    "--source",
    "-s",
    default="data/",
    help="Path to source QA JSON file or directory (default: data/)"
)

parser.add_argument(
    "--out",
    default=".",
    help="Base output directory (default: current directory)"
)

parser.add_argument(
    "--recursive",
    action="store_true",
    help="Recursively scan subdirectories for JSON files"
)

args = parser.parse_args()

SOURCE_PATH = Path(args.source)
BASE_DIR    = Path(args.out)

# Auto-enable recursive if directory
if SOURCE_PATH.is_dir():
    args.recursive = True

DATASET_DIR = BASE_DIR / "datasets"
RULES_DIR   = BASE_DIR / "rules"
EVAL_DIR    = BASE_DIR / "eval"

DATASET_DIR.mkdir(parents=True, exist_ok=True)
RULES_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# UTILITIES
# ============================================================

def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())

def slugify(text: str) -> str:
    return normalize(text).replace(" ", "_")

def infer_tags(category: str, question: str, answers: list[str]):
    tags = set()
    q = question.lower()

    for a in answers:
        a_lower = a.lower()
        if "not specified" in a_lower or "unknown" in a_lower:
            tags.add("unknown")
        if "not supported" in a_lower or "does not" in a_lower:
            tags.add("negative")

    if q.startswith(("what", "which", "does", "is", "are")):
        tags.add("fact")

    return sorted(tags)

def collect_sources(path: Path, recursive: bool):
    if path.is_file():
        return [path]
    if path.is_dir():
        pattern = "**/*.json" if recursive else "*.json"
        return sorted(path.glob(pattern))
    raise ValueError(f"Invalid source path: {path}")

def extract_answers(q: dict):
    if "expected_answers" in q:
        answers = q["expected_answers"]
    elif "expected_answer" in q:
        answers = [q["expected_answer"]]
    else:
        raise ValueError(f"Question {q.get('id')} missing expected answer(s)")

    if not isinstance(answers, list):
        raise ValueError(f"expected_answers must be list in {q.get('id')}")

    return sorted({a.strip() for a in answers if a.strip()})

# ============================================================
# COLLECT SOURCES
# ============================================================

sources = collect_sources(SOURCE_PATH, args.recursive)

if not sources:
    raise ValueError(f"No JSON files found in: {SOURCE_PATH}")

print(f"Discovered {len(sources)} source file(s)")

# ============================================================
# AGGREGATION STRUCTURE
# ============================================================

aggregate = defaultdict(lambda: {
    "train": [],
    "eval": [],
    "rules": defaultdict(list),
    "ids": set()
})

intent_counter = Counter()

REQUIRED_FIELDS = {"id", "category", "question"}

# ============================================================
# PROCESS FILES
# ============================================================

for src in sources:

    with open(src, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    meta      = data.get("metadata", {})
    questions = data.get("questions", [])

    if not isinstance(questions, list):
        raise ValueError(f"{src}: 'questions' must be list")

    product_slug = slugify(meta.get("product", "unknown_product"))
    domain_slug  = slugify(meta.get("domain", "product_specs"))
    prefix = f"{product_slug}_{domain_slug}"

    seen_questions = set()

    for q in questions:

        missing = REQUIRED_FIELDS - q.keys()
        if missing:
            raise ValueError(f"{src}: missing fields {missing}")

        qid      = q["id"]
        question = q["question"].strip()
        category = q["category"]
        answers  = extract_answers(q)

        # ID collision detection
        if qid in aggregate[prefix]["ids"]:
            raise ValueError(f"Duplicate ID detected: {qid}")
        aggregate[prefix]["ids"].add(qid)

        # Deduplicate normalized questions
        norm_q = normalize(question)
        if norm_q in seen_questions:
            continue
        seen_questions.add(norm_q)

        # TRAIN
        aggregate[prefix]["train"].append({
            "text": question,
            "label": domain_slug
        })

        # EVAL
        for ans in answers:
            aggregate[prefix]["eval"].append({
                "id": qid,
                "category": category,
                "intent": domain_slug,
                "question": question,
                "expected_answer": ans,
                "tags": infer_tags(category, question, answers),
                "regex": ".*"
            })

        # RULES
        aggregate[prefix]["rules"][norm_q].extend(answers)

        intent_counter[domain_slug] += 1

# ============================================================
# WRITE OUTPUT FILES
# ============================================================

for prefix, bundle in aggregate.items():

    TRAIN_FILE = DATASET_DIR / f"{prefix}.jsonl"
    EVAL_FILE  = EVAL_DIR    / f"{prefix}_eval.jsonl"
    RULE_FILE  = RULES_DIR   / f"{prefix}.json"

    # Deduplicate rules
    for k in bundle["rules"]:
        bundle["rules"][k] = sorted(set(bundle["rules"][k]))

    # Deterministic ordering
    bundle["train"].sort(key=lambda x: x["text"])
    bundle["eval"].sort(key=lambda x: (x["id"], x["expected_answer"]))

    with open(TRAIN_FILE, "w", encoding="utf-8-sig") as f:
        for row in bundle["train"]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with open(EVAL_FILE, "w", encoding="utf-8-sig") as f:
        for row in bundle["eval"]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with open(RULE_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(
            {prefix.split("_", 1)[1]: dict(bundle["rules"])},
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"\n{prefix}")
    print(f" - datasets/{prefix}.jsonl")
    print(f" - eval/{prefix}_eval.jsonl")
    print(f" - rules/{prefix}.json")

# ============================================================
# SUMMARY
# ============================================================

print("\nIntent Distribution:")
for intent, count in intent_counter.items():
    print(f" - {intent}: {count}")

print("\nAll datasets generated successfully.")
sys.exit(0)