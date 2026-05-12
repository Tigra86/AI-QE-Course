# ============================================================
# python 1_validate_data.py data/capitals.json
# python 1_validate_data.py data/
# ============================================================

import json
import sys
from pathlib import Path
from collections import Counter

REQUIRED_METADATA_KEYS = {
    "product",
    "domain",
    "version",
    "total_questions",
}

REQUIRED_QUESTION_BASE_KEYS = {
    "id",
    "category",
    "question",
    "tags",
}

ALLOWED_DOMAINS = {
    "local_information",
    "product_specs",
    "technical_how_to",
    "other",
}

def fail(msg: str):
    raise ValueError(msg)

def warn(msg: str):
    print(f"[WARN] {msg}")

def normalize_expected_answers(q: dict, qid: str) -> list[str]:

    has_single = "expected_answer" in q
    has_multi  = "expected_answers" in q

    if has_single and has_multi:
        fail(f"Question {qid}: use either expected_answer or expected_answers, not both")

    if not has_single and not has_multi:
        fail(f"Question {qid}: missing expected_answer(s)")

    if has_single:
        ans = q["expected_answer"]
        if not isinstance(ans, str) or not ans.strip():
            fail(f"Question {qid}: expected_answer must be a non-empty string")
        return [ans.strip()]

    answers = q["expected_answers"]
    if not isinstance(answers, list) or not answers:
        fail(f"Question {qid}: expected_answers must be a non-empty list")

    if not all(isinstance(a, str) and a.strip() for a in answers):
        fail(f"Question {qid}: expected_answers must contain non-empty strings")

    return [a.strip() for a in answers]

def validate_file(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"Invalid JSON: {e}")

    if "metadata" not in data:
        fail("Missing 'metadata' section")
    if "questions" not in data:
        fail("Missing 'questions' section")

    metadata  = data["metadata"]
    questions = data["questions"]

    if not isinstance(questions, list) or not questions:
        fail("'questions' must be a non-empty list")

    missing_meta = REQUIRED_METADATA_KEYS - metadata.keys()
    if missing_meta:
        fail(f"Metadata missing keys: {sorted(missing_meta)}")

    domain = metadata["domain"]
    if not isinstance(domain, str) or domain not in ALLOWED_DOMAINS:
        fail(
            f"Invalid metadata.domain '{domain}'. "
            f"Allowed: {sorted(ALLOWED_DOMAINS)}"
        )

    if not isinstance(metadata["total_questions"], int):
        fail("'metadata.total_questions' must be an integer")

    if metadata["total_questions"] != len(questions):
        fail(
            f"metadata.total_questions={metadata['total_questions']} "
            f"but found {len(questions)} questions"
        )

    ids = []
    for idx, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            fail(f"Question #{idx} is not an object")

        qid = q.get("id", f"#{idx}")

        missing = REQUIRED_QUESTION_BASE_KEYS - q.keys()
        if missing:
            fail(f"Question {qid}: missing keys {sorted(missing)}")

        if not isinstance(q["id"], str) or not q["id"].strip():
            fail(f"Question #{idx}: id must be a non-empty string")

        if not isinstance(q["question"], str) or not q["question"].strip():
            fail(f"Question {qid}: question must be a non-empty string")

        answers = normalize_expected_answers(q, qid)

        dup = [a for a, c in Counter(answers).items() if c > 1]
        if dup:
            warn(f"{path.name} / {qid}: duplicate expected answers {dup}")

        tags = q["tags"]
        if not isinstance(tags, list) or not tags:
            fail(f"Question {qid}: tags must be a non-empty list")

        if not all(isinstance(t, str) and t.strip() for t in tags):
            fail(f"Question {qid}: tags must contain non-empty strings")

        ids.append(q["id"])

    dup_ids = [i for i, c in Counter(ids).items() if c > 1]
    if dup_ids:
        fail(f"Duplicate question IDs found: {dup_ids}")

def validate_path(path_str: str) -> bool:
    path = Path(path_str)

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(path.glob("*.json"))
        if not files:
            print(f"[WARN] No JSON files found in {path}")
            return True
    else:
        print(f"[FAIL] Path not found: {path}")
        return False

    all_ok = True
    for file in files:
        try:
            validate_file(file)
            print(f"[OK]   {file}")
        except Exception as e:
            print(f"[FAIL] {file}: {e}")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python 1_validate_data.py data/capitals.json")
        print("Usage: python 1_validate_data.py data/")
        sys.exit(2)

    success = validate_path(sys.argv[1])
    sys.exit(0 if success else 1)
    