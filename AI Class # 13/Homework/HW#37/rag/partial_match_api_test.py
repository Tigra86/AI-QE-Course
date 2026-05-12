import configparser
import html as html_lib
import json
import regex
import requests
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "system.config"

if not CONFIG_FILE.exists():
    raise FileNotFoundError("Missing config/system.config")

config              = configparser.ConfigParser()
config.read(CONFIG_FILE)

API_URL             = config.get("API", "API_URL")
OUTPUT_FILE         = config.get("API", "PM_OUTPUT_FILE")
HTML_REPORT         = config.get("API", "PM_HTML_REPORT")
REQUEST_TIMEOUT     = config.getint("API", "REQUEST_TIMEOUT", fallback=30)
TEMPERATURE         = float(config.get("INFERENCE", "TEMPERATURE"))

EVAL_DIR            = BASE_DIR / "eval"
TEMPLATE_HTML       = BASE_DIR / "templates" / "partial_match_report.html"

STATIC_CSS          = config.get("API", "STATIC_CSS")
STATIC_JS           = config.get("API", "STATIC_JS")

REGEX_TIMEOUT       = 0.05
MAX_PATTERN_LENGTH  = 500

# ============================================================
# UTILITIES
# ============================================================

def local_time_str():
    return datetime.now().strftime("%Y-%m-%d %I:%M %p")

def normalize(text):
    return " ".join(text.lower().strip().split()) if text else ""

def is_effectively_empty(text):
    if not text:
        return True
    return text.strip().lower() in {"", ".", "-", "n/a", "na"}

# ============================================================
# REGEX MATCH ENGINE
# ============================================================

def regex_match(pattern, actual):

    if not isinstance(pattern, str) or not pattern.strip():
        return False, "Missing Regex"

    if len(pattern) > MAX_PATTERN_LENGTH:
        return False, "Regex Too Long"

    actual = actual or ""

    try:
        matched = bool(
            regex.search(
                pattern,
                actual,
                flags=regex.IGNORECASE,
                timeout=REGEX_TIMEOUT
            )
        )
        return matched, None

    except regex.TimeoutError:
        return False, "Regex Timeout"

    except Exception:
        return False, "Invalid Regex"

def fail_reason(actual, pattern):

    if is_effectively_empty(actual):
        return "Empty Answer"

    matched, engine_error = regex_match(pattern, actual)

    if engine_error:
        return engine_error

    if not matched:
        return "Regex Mismatch"

    return None

# ============================================================
# API CALL
# ============================================================

def call_api(question):

    try:
        r = requests.post(
            API_URL,
            json={"input": question, "temperature": TEMPERATURE},
            timeout=REQUEST_TIMEOUT,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        r.raise_for_status()
        return r.json().get("answer", "").strip()

    except Exception:
        return ""

# ============================================================
# LOAD EVAL FILES
# ============================================================

def load_eval_files():

    rows = []
    seen = set()

    for file in sorted(EVAL_DIR.glob("*.jsonl")):
        with open(file, "r", encoding="utf-8-sig") as f:
            for line in f:
                if not line.strip():
                    continue

                obj = json.loads(line)
                key = (obj.get("id"), normalize(obj.get("question")))

                if key in seen:
                    continue

                seen.add(key)
                obj["_source"] = file.name
                rows.append(obj)

    if not rows:
        raise RuntimeError("No eval files found in eval/")

    return rows

# ============================================================
# MAIN
# ============================================================

def run():

    start_time = time.time()
    rows = load_eval_files()
    results = []
    reason_counter = Counter()

    for r in rows:

        actual = call_api(r.get("question", ""))
        pattern = r.get("regex")

        reason = fail_reason(actual, pattern)
        status = "PASS" if reason is None else "FAIL"

        if reason:
            reason_counter[reason] += 1

        results.append({
            **r,
            "actual": actual,
            "status": status,
            "reason": reason
        })

    write_json(results, reason_counter)
    write_html_report(results, reason_counter)

    print("\n========= DONE =========")
    print(f"JSON -> {OUTPUT_FILE}")
    print(f"HTML -> {HTML_REPORT}")
    print(f"Runtime: {time.time() - start_time:.2f}s")

# ============================================================
# JSON OUTPUT
# ============================================================

def write_json(results, reason_counter):

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed

    payload = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "accuracy": round((passed / total) * 100, 2) if total else 0,
            "reason_distribution": dict(reason_counter)
        },
        "results": [
            {
                "id": r.get("id"),
                "question": r.get("question"),
                "actual": r.get("actual"),
                "regex": r.get("regex"),
                "status": r.get("status"),
                "reason": r.get("reason"),
                "source_file": r.get("_source")
            }
            for r in results
        ]
    }

    Path(OUTPUT_FILE).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8-sig"
    )

# ============================================================
# HTML REPORT
# ============================================================

def write_html_report(results, reason_counter):

    if not TEMPLATE_HTML.exists():
        raise FileNotFoundError("Missing templates/partial_match_report.html")

    grouped = defaultdict(list)
    for r in results:
        grouped[r["_source"]].append(r)

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed

    blocks_html = ""

    for src, items in grouped.items():

        safe_src = html_lib.escape(src)
        file_passed = sum(1 for x in items if x["status"] == "PASS")
        file_failed = len(items) - file_passed

        blocks_html += f"""
<div class="file-section">
    <h2>{safe_src}</h2>
    <div class="file-summary">
    <b>Total:</b> {len(items)} |
    <b>Pass:</b> {file_passed} |
    <b>Fail:</b> {file_failed}
</div>
"""

        for r in items:

            safe_id = html_lib.escape(r.get("id") or "")
            safe_q = html_lib.escape(r.get("question") or "")
            safe_actual = html_lib.escape(r.get("actual") or "")
            safe_regex = html_lib.escape(r.get("regex") or "")
            safe_status = html_lib.escape(r.get("status") or "")
            safe_reason = html_lib.escape(r.get("reason") or "")

            label = "PASS" if safe_status == "PASS" else f"FAIL – {safe_reason}"

            blocks_html += f"""

<details class="result" data-status="{safe_status}" data-reason="{safe_reason}" data-id="{safe_id.lower()}" data-question="{safe_q.lower()}">

    <summary>
        <span class="col id">{safe_id}</span>
        <span class="col question">{safe_q}</span>
        <span class="col status">{label}</span>
    </summary>
        <div class="details">
            <b>Actual:</b>
            <pre>{safe_actual}</pre>
            <hr/>
            <b>Regex:</b>
            <pre>{safe_regex}</pre>
        </div>
</details>
"""

        blocks_html += "</div>"

    html_template = TEMPLATE_HTML.read_text(encoding="utf-8-sig")

    html_template = (
        html_template
        .replace("{{TOTAL}}", str(total))
        .replace("{{PASSED}}", str(passed))
        .replace("{{FAILED}}", str(failed))
        .replace("{{TABLES}}", blocks_html)
        .replace("{{CSS_PATH}}", STATIC_CSS)
        .replace("{{JS_PATH}}", STATIC_JS)
        .replace("{{TIMESTAMP}}", local_time_str())
        .replace("{{THRESHOLD}}", "REGEX")
    )

    Path(HTML_REPORT).write_text(html_template, encoding="utf-8-sig")

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run()