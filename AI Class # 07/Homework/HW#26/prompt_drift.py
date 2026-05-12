import json
import re
import numpy as np
from datetime import datetime
from typing import Dict, List
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
# =================================================
# CONFIG
# =================================================
MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.90

BASELINE_FILE = "prompts_baseline.json"
CURRENT_FILE  = "prompts.json"

JSON_REPORT_PATH = "prompt_drift_report.json"
HTML_REPORT_PATH = "prompt_drift_report.html"
# =================================================
# MODEL
# =================================================
model = SentenceTransformer(MODEL_NAME)
# =================================================
# UTILITIES
# =================================================
def local_time_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %I:%M %p")

def load_prompts(path: str) -> Dict[str, dict]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def embed(text: str) -> np.ndarray:
    return model.encode(text, normalize_embeddings=True)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
# =================================================
# SENTENCE DIFF ENGINE
# =================================================
def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    return re.split(r'(?<=[.!?])\s+', text.strip())

def diff_sentences(base_text: str, curr_text: str) -> List[dict]:
    base_sents = split_sentences(base_text)
    curr_sents = split_sentences(curr_text)

    matcher = SequenceMatcher(None, base_sents, curr_sents)
    diffs = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        elif tag == "delete":
            for s in base_sents[i1:i2]:
                diffs.append({
                    "type": "removed",
                    "base": s,
                    "current": ""
                })

        elif tag == "insert":
            for s in curr_sents[j1:j2]:
                diffs.append({
                    "type": "added",
                    "base": "",
                    "current": s
                })

        elif tag == "replace":
            base_block = base_sents[i1:i2]
            curr_block = curr_sents[j1:j2]
            max_len = max(len(base_block), len(curr_block))

            for i in range(max_len):
                diffs.append({
                    "type": "modified",
                    "base": base_block[i] if i < len(base_block) else "",
                    "current": curr_block[i] if i < len(curr_block) else ""
                })

    return diffs
# =================================================
# PROMPT DRIFT DETECTION
# =================================================
def detect_prompt_drift(
    baseline: Dict[str, dict],
    current: Dict[str, dict]
) -> List[dict]:

    results = []

    for name, base_prompt in baseline.items():
        base_id = base_prompt["id"]
        base_text = base_prompt["text"]

        if name not in current:
            results.append({
                "prompt_name": name,
                "id": base_id,
                "status": "MISSING",
                "similarity": None,
                "diff": []
            })
            continue

        curr_text = current[name]["text"]

        if base_text == curr_text:
            results.append({
                "prompt_name": name,
                "id": base_id,
                "status": "OK",
                "similarity": 1.0,
                "diff": []
            })
            continue

        sim = cosine_similarity(embed(base_text), embed(curr_text))
        status = "DRIFT" if sim < SIMILARITY_THRESHOLD else "MINOR_CHANGE"

        results.append({
            "prompt_name": name,
            "id": base_id,
            "status": status,
            "similarity": round(sim, 4),
            "diff": diff_sentences(base_text, curr_text)
        })

    return results
# =================================================
# JSON REPORT
# =================================================
def write_json_report(results: List[dict]) -> None:
    report = {
        "generated_at": local_time_str(),
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "summary": {
            "total": len(results),
            "ok": sum(r["status"] == "OK" for r in results),
            "minor_change": sum(r["status"] == "MINOR_CHANGE" for r in results),
            "drift": sum(r["status"] == "DRIFT" for r in results),
            "missing": sum(r["status"] == "MISSING" for r in results)
        },
        "results": results
    }

    with open(JSON_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
# =================================================
# HTML REPORT (CONSISTENT UX)
# =================================================
def render_diff(diff: List[dict]) -> str:
    if not diff:
        return "<i>No differences</i>"

    rows = ""

    for d in diff:
        rows += f"""
        <tr>
            <td class="baseline">
                <pre>{d['base']}</pre>
            </td>
            <td class="current">
                <pre>{d['current']}</pre>
            </td>
        </tr>
        """

    return f"""
    <table class="diff-table">
        <tr>
            <th>Baseline Prompt</th>
            <th>Current Prompt</th>
        </tr>
        {rows}
    </table>
    """

def write_html_report(results: List[dict]) -> None:
    STATUS_CLASS = {
        "OK": "ok",
        "MINOR_CHANGE": "minor",
        "DRIFT": "drift",
        "MISSING": "missing"
    }

    rows = ""

    for r in results:
        similarity = f"{r['similarity']:.3f}" if r["similarity"] is not None else "â€”"

        rows += f"""
        <tr class="{STATUS_CLASS[r['status']]}">
            <td>{r['id']}</td>
            <td>{r['prompt_name']}</td>
            <td><b>{r['status']}</b></td>
            <td>{similarity}</td>
        </tr>
        <tr>
            <td colspan="4">
                <details>
                    <summary>View Prompt Diff</summary>
                    {render_diff(r["diff"])}
                </details>
            </td>
        </tr>
        """

    html = f"""
    <html>
    <head>
        <title>Prompt Drift Report</title>
        <style>
            body                {{font-family: Arial, sans-serif;padding: 20px;}}
            table               {{width: 100%;border-collapse: collapse;margin-top: 16px;}}
            th, td              {{border: 1px solid #fff;padding: 8px;vertical-align: top;}}
            th                  {{background-color: #f2f2f2;}}
            .ok                 {{ background: #d4edda; }}
            .minor              {{ background: #fff3cd; }}
            .drift              {{ background: #f8d7da; }}
            .missing            {{ background: #e2e3e5; }}
            .diff-table         {{width: 100%;margin-top: 10px;border-collapse: collapse;}}
            .diff-table th      {{background: #eaeaea;}}
            .baseline           {{background: #fff5f5;width: 50%;}}
            .current            {{background: #f5fff5;width: 50%;}}
            pre                 {{white-space: pre-wrap;font-family: monospace;margin: 0;}}
            details summary     {{cursor: pointer;font-weight: bold;margin: 6px 0;}}
        </style>
    </head>
    <body>

        <h2>Prompt Drift Report</h2>

        <b>Generated:</b> {local_time_str()}<br />
        <b>Similarity Threshold:</b> {SIMILARITY_THRESHOLD}

        <h3>Status Legend</h3>
        <ul>
            <li><b>OK</b> - Prompt identical to baseline</li>
            <li><b>MINOR_CHANGE</b> - Small wording change, intent preserved</li>
            <li><b>DRIFT</b> - Semantic meaning changed</li>
            <li><b>MISSING</b> - Prompt missing in current set</li>
        </ul>

        <table>
            <tr>
                <th>ID</th>
                <th>Prompt Name</th>
                <th>Status</th>
                <th>Similarity</th>
            </tr>
            {rows}
        </table>

    </body>
    </html>
    """

    with open(HTML_REPORT_PATH, "w", encoding="utf-8-sig") as f:
        f.write(html)
# =================================================
# MAIN
# =================================================
if __name__ == "__main__":
    baseline = load_prompts(BASELINE_FILE)
    current  = load_prompts(CURRENT_FILE)

    results = detect_prompt_drift(baseline, current)

    write_json_report(results)
    write_html_report(results)

    print("Prompt drift reports generated:")
    print(f" - {JSON_REPORT_PATH}")
    print(f" - {HTML_REPORT_PATH}")