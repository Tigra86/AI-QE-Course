import json
import re
import argparse
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
# =================================================
# DEFAULT CONFIG (overridable via CLI)
# =================================================
MODEL_NAME = "all-MiniLM-L6-v2" # all-mpnet-base-v2 all-MiniLM-L6-v2

RESPONSE_SIMILARITY_THRESHOLD = 0.92
RESPONSE_LENGTH_DELTA_RATIO  = 0.30

BASELINE_FILE = "responses-gpt-4o-mini.json"
CURRENT_FILE  = "responses-gpt-5.2.json"

JSON_REPORT_PATH = "response_drift_report.json"
HTML_REPORT_PATH = "response_drift_report.html"
# =================================================
# MODEL
# =================================================
model = SentenceTransformer(MODEL_NAME)
# =================================================
# UTILITIES
# =================================================
def local_time_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %I:%M %p")
# =================================================
# CLI
# =================================================
def parse_args():
    parser = argparse.ArgumentParser(description="LLM Response Drift Detection")

    parser.add_argument("--baseline", default=BASELINE_FILE)
    parser.add_argument("--current", default=CURRENT_FILE)

    parser.add_argument("--similarity-threshold", type=float,
                        default=RESPONSE_SIMILARITY_THRESHOLD)
    parser.add_argument("--length-delta", type=float,
                        default=RESPONSE_LENGTH_DELTA_RATIO)

    parser.add_argument("--json-out", default=JSON_REPORT_PATH)
    parser.add_argument("--html-out", default=HTML_REPORT_PATH)

    parser.add_argument(
        "--ignore-punctuation",
        action="store_true",
        help="Ignore punctuation differences"
    )

    return parser.parse_args()
# =================================================
# LOAD RESPONSES
# =================================================
def load_response_file(path: str) -> Tuple[Dict[str, dict], dict]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if isinstance(data, dict) and "results" in data:
        items = data["results"]
        meta = {
            "model": data.get("model", "unknown"),
            "timestamp": data.get("timestamp", "unknown")
        }
    elif isinstance(data, list):
        items = data
        meta = {"model": "unknown", "timestamp": "unknown"}
    else:
        raise ValueError(f"Unsupported response file format: {path}")

    return {item["id"]: item for item in items}, meta
# =================================================
# EMBEDDING / SIMILARITY
# =================================================
def embed(text: str) -> np.ndarray:
    return model.encode(text, normalize_embeddings=True)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
# =================================================
# TEXT NORMALIZATION
# =================================================
def normalize_text(text: str, ignore_punctuation: bool) -> str:
    if not text:
        return ""

    text = re.sub(r'(\*\*|\*|__|_)', '', text)

    if ignore_punctuation:
        text = re.sub(r'[^\w\s]', '', text)

    return re.sub(r'\s+', ' ', text).strip()
# =================================================
# SENTENCE DIFF
# =================================================
def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    return re.split(r'(?<=[.!?])\s+', text.strip())

def diff_sentences(base: str, curr: str) -> List[dict]:
    base_s = split_sentences(base)
    curr_s = split_sentences(curr)

    matcher = SequenceMatcher(None, base_s, curr_s)
    diffs = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        elif tag == "delete":
            for s in base_s[i1:i2]:
                diffs.append({"base": s, "current": ""})

        elif tag == "insert":
            for s in curr_s[j1:j2]:
                diffs.append({"base": "", "current": s})

        elif tag == "replace":
            for i in range(max(i2 - i1, j2 - j1)):
                diffs.append({
                    "base": base_s[i1 + i] if i1 + i < i2 else "",
                    "current": curr_s[j1 + i] if j1 + i < j2 else ""
                })

    return diffs
# =================================================
# DRIFT DETECTION
# =================================================
def detect_response_drift(
    baseline: Dict[str, dict],
    current: Dict[str, dict],
    ignore_punctuation: bool
) -> List[dict]:

    results = []

    for pid, base_item in baseline.items():
        base_resp = normalize_text(base_item.get("prompt_output", ""), ignore_punctuation)

        if pid not in current:
            results.append({
                "id": pid,
                "name": base_item.get("name"),
                "status": "MISSING_RESPONSE",
                "similarity": None,
                "length_delta": None,
                "diff": []
            })
            continue

        curr_resp = normalize_text(current[pid].get("prompt_output", ""), ignore_punctuation)

        if base_resp == curr_resp:
            results.append({
                "id": pid,
                "name": base_item.get("name"),
                "status": "OK",
                "similarity": 1.0,
                "length_delta": 0.0,
                "diff": []
            })
            continue

        sim = cosine_similarity(embed(base_resp), embed(curr_resp))

        base_len = len(base_resp.split())
        curr_len = len(curr_resp.split())
        length_delta = abs(curr_len - base_len) / max(base_len, 1)

        if sim < RESPONSE_SIMILARITY_THRESHOLD:
            status = "SEMANTIC_DRIFT"
        elif length_delta > RESPONSE_LENGTH_DELTA_RATIO:
            status = "STRUCTURAL_DRIFT"
        else:
            status = "MINOR_VARIATION"

        results.append({
            "id": pid,
            "name": base_item.get("name"),
            "status": status,
            "similarity": round(sim, 4),
            "length_delta": round(length_delta, 3),
            "diff": diff_sentences(base_resp, curr_resp)
        })

    return results
# =================================================
# REPORTING
# =================================================
def write_json_report(results: List[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"generated_at": local_time_str(), "results": results},
            f, indent=2, ensure_ascii=False
        )

def render_diff(diff: List[dict], baseline_meta: dict, current_meta: dict) -> str:
    if not diff:
        return "<i>No differences</i>"

    rows = ""
    for d in diff:
        rows += f"""
        <tr>
            <td class="baseline"><pre>{d['base']}</pre></td>
            <td class="current"><pre>{d['current']}</pre></td>
        </tr>
        """

    return f"""
    <table class="diff-table">
        <tr>
            <th>Baseline [{baseline_meta['model']} / {baseline_meta['timestamp']}]</th>
            <th>Current [{current_meta['model']} / {current_meta['timestamp']}]</th>
        </tr>
        {rows}
    </table>
    """

def write_html_report(results, baseline_meta, current_meta, path):
    STATUS_COLORS = {
        "OK": "#d4edda",
        "MINOR_VARIATION": "#fff3cd",
        "SEMANTIC_DRIFT": "#f8d7da",
        "STRUCTURAL_DRIFT": "#fde2e2",
        "MISSING_RESPONSE": "#e2e3e5"
    }

    rows = ""
    for r in results:
        rows += f"""
        <tr style="background:{STATUS_COLORS[r['status']]}">
            <td>{r['id']}</td>
            <td>{r['name']}</td>
            <td><b>{r['status']}</b></td>
            <td>{r['similarity'] if r['similarity'] is not None else "-"}</td>
            <td>{r['length_delta'] if r['length_delta'] is not None else "-"}</td>
        </tr>
        <tr class="diff-row">
            <td colspan="5">
                <details>
                    <summary>View Response Diff</summary>
                    <div class="diff-overlay">
                        {render_diff(r["diff"], baseline_meta, current_meta)}
                    </div>
                </details>
            </td>
        </tr>
        """

    html = f"""
        <html>
        <head>
        <style>
        body            {{font-family: Arial, Helvetica, sans-serif;font-size: 16px;}}
        table           {{width: 100%;border-collapse: collapse;table-layout: fixed;}}
        th, td          {{border: 1px solid #fff;padding: 8px;vertical-align: top;}}
        th              {{background: #f2f2f2; font-weight: bold;}}
        .diff-row       {{height: 0;}}
        .diff-overlay   {{max-height: 360px;overflow: auto;border: 1px solid #ccc;background: #fff;}}
        .diff-table     {{width: 100%;table-layout: fixed;}}
        .baseline       {{background: #fff5f5;width: 50%;}}
        .current        {{background: #f5fff5;width: 50%;}}
        pre             {{font-family: Arial, Helvetica, sans-serif;font-size: 16px;margin: 0;white-space: pre-wrap;word-break: break-word;}}
        summary         {{cursor: pointer;font-weight: bold;}}
        </style>
        </head>
        <body>

        <h2>Response Drift Report</h2>
        <b>Generated:</b> {local_time_str()}<br />
        <b>Similarity Threshold:</b> {RESPONSE_SIMILARITY_THRESHOLD}<br />
        <b>Length Delta Threshold:</b> {RESPONSE_LENGTH_DELTA_RATIO} ({int(RESPONSE_LENGTH_DELTA_RATIO * 100)}%)<br />
        <b>Baseline:</b> {baseline_meta['model']} / {baseline_meta['timestamp']}<br />
        <b>Current:</b> {current_meta['model']} / {current_meta['timestamp']}<br />

        <h3>Status Legend</h3>
        <ul>
            <li><b>OK</b> - Response is identical to baseline</li>
            <li><b>MINOR_VARIATION</b> - Small wording changes, meaning preserved</li>
            <li><b>SEMANTIC_DRIFT</b> - Meaning has changed</li>
            <li><b>STRUCTURAL_DRIFT</b> - Significant change in length or format</li>
            <li><b>MISSING_RESPONSE</b> - Response missing in current run</li>
        </ul>

        <table>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Status</th>
            <th>Similarity</th>
            <th>Length</th>
        </tr>
        {rows}
        </table>

        </body>
        </html>
        """

    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(html)
# =================================================
# MAIN
# =================================================
if __name__ == "__main__":
    args = parse_args()

    RESPONSE_SIMILARITY_THRESHOLD = args.similarity_threshold
    RESPONSE_LENGTH_DELTA_RATIO   = args.length_delta

    baseline, baseline_meta = load_response_file(args.baseline)
    current,  current_meta  = load_response_file(args.current)

    results = detect_response_drift(
        baseline,
        current,
        ignore_punctuation=args.ignore_punctuation
    )

    write_json_report(results, args.json_out)
    write_html_report(results, baseline_meta, current_meta, args.html_out)

    print("Response drift reports generated:")
    print(f" - {args.json_out}")
    print(f" - {args.html_out}")