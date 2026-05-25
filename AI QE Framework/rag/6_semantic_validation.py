# ============================================================
# Semantic Evaluation Pipeline
# ============================================================

import configparser
import json
import numpy as np
import requests
import statistics
import time
import os
import html

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import logging as transformers_logging
from huggingface_hub.utils import logging as hf_logging

# ============================================================
# ENV CLEANUP
# ============================================================

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

transformers_logging.set_verbosity_error()
transformers_logging.disable_progress_bar()
hf_logging.set_verbosity_error()

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "system.config"

if not CONFIG_FILE.exists():
    raise FileNotFoundError("Missing config/system.config")

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

API_URL         = config.get("API", "API_URL")
OUTPUT_FILE     = config.get("API", "S_OUTPUT_FILE")
HTML_REPORT     = config.get("API", "S_HTML_REPORT")
PASS_THRESHOLD  = config.getfloat("API", "SIMILARITY_THRESHOLD", fallback=0.80)
REQUEST_TIMEOUT = config.getint("API", "REQUEST_TIMEOUT", fallback=30)
EMBED_MODEL     = config.get("API", "EMBED_MODEL")
TEMPERATURE     = float(config.get("INFERENCE", "TEMPERATURE"))

EVAL_DIR        = Path("eval")
TEMPLATE_HTML   = Path("templates/semantic_report.html")
STATIC_CSS      = config.get("API", "STATIC_CSS")
STATIC_JS       = config.get("API", "STATIC_JS")

embedder        = SentenceTransformer(EMBED_MODEL)

# ============================================================
# UTILITIES
# ============================================================

def local_time_str():
    return datetime.now().strftime("%Y-%m-%d %I:%M %p")

def normalize(text):
    return " ".join(text.lower().strip().split()) if text else ""

def semantic_similarity(a, b):
    if not a or not b:
        return 0.0

    if normalize(a) == normalize(b):
        return 1.0

    emb = embedder.encode([a, b], normalize_embeddings=True)
    return float(np.dot(emb[0], emb[1]))

def is_effectively_empty(text):
    if not text:
        return True
    return text.strip().lower() in {"", ".", "-", "n/a", "na"}

def expresses_unknown(text):
    if not text:
        return False
    t = text.lower()
    return any(p in t for p in [
        "not specified",
        "not provided",
        "not available",
        "unknown",
        "no information"
    ])

def esc(text):
    return html.escape(text or "")

# ============================================================
# FAIL REASON LOGIC
# ============================================================

def fail_reason(expected, actual, sim):

    e = normalize(expected)
    a = normalize(actual)

    # Correct negative inference
    if not e and expresses_unknown(actual):
        return None
    if e == a:
        return None
    if is_effectively_empty(actual):
        return "Empty Answer"
    if ("not specified" in e or "unknown" in e) and a != e:
        return "Overreach"
    if sim < 0.50:
        return "Hallucination"
    if sim < PASS_THRESHOLD:
        return "Semantic Mismatch"
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
            headers={"Content-Type": "application/json"}
        )
        r.raise_for_status()
        return r.json().get("answer", "").strip()
    except Exception as e:
        print(f"[API ERROR] {e}")
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
        raise RuntimeError("No eval files found")

    return rows

# ============================================================
# MAIN
# ============================================================

def run():
    start_time = time.time()
    rows = load_eval_files()
    results = []

    for r in rows:
        actual = call_api(r["question"])
        sim = semantic_similarity(r["expected_answer"], actual)
        reason = fail_reason(r["expected_answer"], actual, sim)
        status = "PASS" if reason is None else "FAIL"

        results.append({
            **r,
            "actual": actual,
            "similarity": sim,
            "reason": reason,
            "status": status
        })

    write_json(results)
    write_html_report(results)

    print("\n========= DONE =========")
    print(f"JSON -> {OUTPUT_FILE}")
    print(f"HTML -> {HTML_REPORT}")
    print(f"Runtime: {time.time() - start_time:.2f}s")

# ============================================================
# JSON OUTPUT
# ============================================================

def write_json(results):
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed

    avg_sim = statistics.mean(r["similarity"] for r in results) if total else 0

    payload = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "accuracy": round((passed / total) * 100, 2) if total else 0,
            "avg_similarity": round(avg_sim, 4)
        },
        "results": [
            {
                "id": r["id"],
                "question": r["question"],
                "expected": r["expected_answer"],
                "actual": r["actual"],
                "similarity": round(r["similarity"], 4),
                "status": r["status"],
                "reason": r["reason"],
                "source_file": r["_source"]
            }
            for r in results
        ]
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

# ============================================================
# HTML REPORT
# ============================================================

def sort_by_id_numeric(item):
    """Sort function to handle IDs like Q101, Q001, etc. numerically by number only"""
    id_str = item["id"]
    # Extract just the number part, ignoring prefix
    if len(id_str) > 1 and id_str[0].isalpha():
        try:
            number = int(id_str[1:])
            return number
        except ValueError:
            return 999999  # fallback for non-standard IDs (put at end)
    return 999999

def write_html_report(results):
    # Sort results by ID numerically
    results_sorted = sorted(results, key=sort_by_id_numeric)

    grouped = defaultdict(list)
    for r in results_sorted:
        grouped[r["_source"]].append(r)

    total = len(results_sorted)
    passed = sum(1 for r in results_sorted if r["status"] == "PASS")
    failed = total - passed

    ids  = [r["id"] for r in results_sorted]
    sims = [round(r["similarity"] * 100, 2) for r in results_sorted]

    blocks_html = ""

    for src, items in grouped.items():
        blocks_html += f"<div class='file-section'><h2>{src}</h2>"

        for r in items:
            reason = r["reason"] or "PASS"
            label = "PASS" if r["status"] == "PASS" else f"FAIL – {reason}"

            blocks_html += f"""
<details class="result"
    data-status="{esc(r['status'])}"
    data-reason="{esc(reason)}"
    data-id="{esc(r['id'])}"
    data-question="{esc(r['question'])}">

<summary>
    <span class="col id">{esc(r['id'])}</span>
    <span class="col question">{esc(r['question'])}</span>
    <span class="col sim">{round(r['similarity']*100,2)}%</span>
    <span class="col status">{esc(label)}</span>
</summary>

<div class="details">
    <b>Expected:</b>
    <pre>{esc(r['expected_answer'])}</pre>
    <hr/>
    <b>Actual:</b>
    <pre>{esc(r['actual'])}</pre>
</div>
</details>
"""

        blocks_html += "</div>"

    html_template = TEMPLATE_HTML.read_text(encoding="utf-8-sig")

    html_output = (
        html_template
        .replace("{{TOTAL}}", str(total))
        .replace("{{PASSED}}", str(passed))
        .replace("{{FAILED}}", str(failed))
        .replace("{{TABLES}}", blocks_html)
        .replace("{{CSS_PATH}}", STATIC_CSS)
        .replace("{{JS_PATH}}", STATIC_JS)
        .replace("{{TIMESTAMP}}", local_time_str())
        .replace("{{THRESHOLD}}", str(int(PASS_THRESHOLD * 100)))
    )

    html_output = html_output.replace(
        "</head>",
        f"""
    <script>
        const PASS_COUNT = {passed};
        const FAIL_COUNT = {failed};
        const IDS = {json.dumps(ids)};
        const SIMS = {json.dumps(sims)};
    </script>
</head>
"""
    )

    Path(HTML_REPORT).write_text(html_output, encoding="utf-8-sig")

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run()
