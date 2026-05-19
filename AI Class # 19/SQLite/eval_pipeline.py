# python eval_pipeline.py --db eval_pipeline.db init
# python eval_pipeline.py --db eval_pipeline.db load --source jsons
# python eval_pipeline.py --db eval_pipeline.db run --model gpt-5.2
# python eval_pipeline.py --db eval_pipeline.db report --run-id c8e6c018-97f0-47ea-9a83-34b7df9f8b3b

import argparse
import json
import re
import sqlite3
import uuid
from datetime import datetime
from datetime import UTC 
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ============================================================

def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_cases (
        id TEXT PRIMARY KEY,
        category TEXT,
        intent TEXT,
        question TEXT NOT NULL,
        expected_answer TEXT,
        tags TEXT,
        regex TEXT,
        source_file TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eval_runs (
        run_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        model_name TEXT,
        total_tests INTEGER,
        passed_tests INTEGER,
        failed_tests INTEGER,
        avg_score REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eval_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        test_id TEXT NOT NULL,
        question TEXT NOT NULL,
        expected_answer TEXT,
        actual_answer TEXT,
        exact_match INTEGER,
        regex_match INTEGER,
        contains_expected INTEGER,
        score REAL,
        passed INTEGER,
        error_message TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES eval_runs(run_id)
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_cases_category ON test_cases(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_cases_intent ON test_cases(intent)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eval_results_run_id ON eval_results(run_id)")

    conn.commit()

# ============================================================

def load_json_folder(conn: sqlite3.Connection, folder_path: str) -> None:
    cursor = conn.cursor()
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    loaded = 0

    for file_path in sorted(folder.glob("*.json")):
        with file_path.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)

        test_id = str(data.get("id", "")).strip()
        if not test_id:
            raise ValueError(f"Missing 'id' in {file_path.name}")

        tags = data.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        cursor.execute("""
        INSERT OR REPLACE INTO test_cases (
            id, category, intent, question, expected_answer, tags, regex, source_file
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id,
            data.get("category"),
            data.get("intent"),
            data.get("question"),
            data.get("expected_answer"),
            json.dumps(tags, ensure_ascii=False),
            data.get("regex", ".*"),
            file_path.name
        ))

        loaded += 1

    conn.commit()
    print(f"[OK] Loaded {loaded} test case(s) from {folder_path}")

# ============================================================

def ask_model(question: str, model_name: str = "gpt-5.4") -> str:
    from openai import OpenAI

    client = OpenAI()

    try:
        response = client.responses.create(
            model=model_name,
            input=question
        )
        return response.output_text or ""
    except Exception as e:
        raise RuntimeError(f"Model call failed: {e}") from e

# ============================================================

def normalize_text(text: str) -> str:
    if text is None:
        return ""
    return " ".join(text.strip().lower().split())


def safe_regex_match(pattern: str, actual: str) -> Tuple[int, str]:
    try:
        matched = bool(re.search(pattern, actual or "", re.IGNORECASE | re.DOTALL))
        return int(matched), ""
    except re.error as e:
        return 0, f"Invalid regex: {e}"


def evaluate_one(expected: str, regex_pattern: str, actual: str) -> Dict[str, Any]:
    expected_norm = normalize_text(expected)
    actual_norm = normalize_text(actual)

    exact_match = int(expected_norm != "" and expected_norm == actual_norm)
    contains_expected = int(expected_norm != "" and expected_norm in actual_norm)

    regex_match, regex_error = safe_regex_match(regex_pattern or ".*", actual or "")

    score = 0.0
    if exact_match:
        score = 1.0
    elif regex_match:
        score = 0.8
    elif contains_expected:
        score = 0.6
    else:
        score = 0.0

    passed = int(
        exact_match == 1
        or regex_match == 1
        or contains_expected == 1
    )

    return {
        "exact_match": exact_match,
        "regex_match": regex_match,
        "contains_expected": contains_expected,
        "score": score,
        "passed": passed,
        "error_message": regex_error,
    }

# ============================================================

def fetch_test_cases(
    conn: sqlite3.Connection,
    category: str | None = None,
    intent: str | None = None
) -> List[sqlite3.Row]:
    cursor = conn.cursor()

    query = "SELECT * FROM test_cases WHERE 1=1"
    params: List[Any] = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if intent:
        query += " AND intent = ?"
        params.append(intent)

    query += " ORDER BY id"

    cursor.execute(query, params)
    return cursor.fetchall()


def run_evaluation(
    conn: sqlite3.Connection,
    model_name: str,
    category: str | None = None,
    intent: str | None = None
) -> str:
    test_cases = fetch_test_cases(conn, category=category, intent=intent)
    if not test_cases:
        raise ValueError("No test cases found for the selected filters.")

    run_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()
    cursor = conn.cursor()

    total = 0
    passed = 0
    total_score = 0.0

    for row in test_cases:
        total += 1
        question = row["question"]
        expected_answer = row["expected_answer"] or ""
        regex_pattern = row["regex"] or ".*"

        actual_answer = ""
        error_message = ""

        try:
            actual_answer = ask_model(question, model_name=model_name)
            eval_result = evaluate_one(expected_answer, regex_pattern, actual_answer)
            error_message = eval_result["error_message"]
        except Exception as e:
            eval_result = {
                "exact_match": 0,
                "regex_match": 0,
                "contains_expected": 0,
                "score": 0.0,
                "passed": 0,
                "error_message": str(e),
            }

        passed += eval_result["passed"]
        total_score += eval_result["score"]

        cursor.execute("""
        INSERT INTO eval_results (
            run_id, test_id, question, expected_answer, actual_answer,
            exact_match, regex_match, contains_expected, score, passed,
            error_message, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            row["id"],
            question,
            expected_answer,
            actual_answer,
            eval_result["exact_match"],
            eval_result["regex_match"],
            eval_result["contains_expected"],
            eval_result["score"],
            eval_result["passed"],
            error_message,
            created_at
        ))

    failed = total - passed
    avg_score = round(total_score / total, 4) if total else 0.0

    cursor.execute("""
    INSERT INTO eval_runs (
        run_id, created_at, model_name, total_tests, passed_tests, failed_tests, avg_score
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        created_at,
        model_name,
        total,
        passed,
        failed,
        avg_score
    ))

    conn.commit()
    return run_id

# ============================================================

def print_run_summary(conn: sqlite3.Connection, run_id: str) -> None:
    cursor = conn.cursor()

    cursor.execute("""
    SELECT run_id, created_at, model_name, total_tests, passed_tests, failed_tests, avg_score
    FROM eval_runs
    WHERE run_id = ?
    """, (run_id,))
    run = cursor.fetchone()

    if not run:
        print(f"[ERROR] Run not found: {run_id}")
        return

    print("\n=== EVALUATION SUMMARY ===")
    print(f"Run ID       : {run['run_id']}")
    print(f"Created At   : {run['created_at']}")
    print(f"Model        : {run['model_name']}")
    print(f"Total Tests  : {run['total_tests']}")
    print(f"Passed       : {run['passed_tests']}")
    print(f"Failed       : {run['failed_tests']}")
    print(f"Average Score: {run['avg_score']:.4f}")

    cursor.execute("""
    SELECT test_id, passed, score, exact_match, regex_match, contains_expected, error_message
    FROM eval_results
    WHERE run_id = ?
    ORDER BY test_id
    """, (run_id,))
    rows = cursor.fetchall()

    print("\n=== PER-TEST RESULTS ===")
    for row in rows:
        status = "PASS" if row["passed"] else "FAIL"
        print(
            f"{row['test_id']}: {status} | "
            f"score={row['score']:.2f} | "
            f"exact={row['exact_match']} | "
            f"regex={row['regex_match']} | "
            f"contains={row['contains_expected']}"
        )
        if row["error_message"]:
            print(f"  error: {row['error_message']}")


def print_failed_cases(conn: sqlite3.Connection, run_id: str) -> None:
    cursor = conn.cursor()
    cursor.execute("""
    SELECT test_id, question, expected_answer, actual_answer, score, error_message
    FROM eval_results
    WHERE run_id = ? AND passed = 0
    ORDER BY test_id
    """, (run_id,))
    rows = cursor.fetchall()

    if not rows:
        print("\nNo failed cases.")
        return

    print("\n=== FAILED CASES ===")
    for row in rows:
        print(f"\n[{row['test_id']}] score={row['score']:.2f}")
        print(f"Q: {row['question']}")
        print(f"Expected: {row['expected_answer']}")
        print(f"Actual  : {row['actual_answer']}")
        if row["error_message"]:
            print(f"Error   : {row['error_message']}")

# ============================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SQLite + Python evaluation pipeline")

    parser.add_argument("--db", default="eval_pipeline.db", help="SQLite database path")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize database")

    load_parser = subparsers.add_parser("load", help="Load JSON test files into SQLite")
    load_parser.add_argument("--source", required=True, help="Folder containing .json files")

    run_parser = subparsers.add_parser("run", help="Run evaluation")
    run_parser.add_argument("--model", default="gpt-5.4", help="Model name label")
    run_parser.add_argument("--category", help="Optional category filter")
    run_parser.add_argument("--intent", help="Optional intent filter")

    report_parser = subparsers.add_parser("report", help="Show report for a run")
    report_parser.add_argument("--run-id", required=True, help="Evaluation run ID")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    conn = get_connection(args.db)

    try:
        if args.command == "init":
            init_db(conn)
            print(f"[OK] Database initialized: {args.db}")

        elif args.command == "load":
            init_db(conn)
            load_json_folder(conn, args.source)

        elif args.command == "run":
            init_db(conn)
            run_id = run_evaluation(
                conn,
                model_name=args.model,
                category=args.category,
                intent=args.intent
            )
            print(f"[OK] Evaluation complete. Run ID: {run_id}")
            print_run_summary(conn, run_id)
            print_failed_cases(conn, run_id)

        elif args.command == "report":
            print_run_summary(conn, args.run_id)
            print_failed_cases(conn, args.run_id)

        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
