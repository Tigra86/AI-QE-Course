# python -m spacy download en_core_web_sm

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["DISABLE_TQDM"] = "1"

import configparser
import contextlib
import html
import io
import json
import numpy as np
import spacy
import sys
import time

from collections import Counter
from datetime import datetime
from pathlib import Path

from transformers import logging as transformers_logging
from huggingface_hub.utils import logging as hf_logging
from sentence_transformers import SentenceTransformer

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

EMBED_MODEL         = config.get("API", "EMBED_MODEL")
SEMANTIC_THRESHOLD  = config.getfloat("API", "SIMILARITY_THRESHOLD")

MIN_TOKENS_WARN     = config.getint("RULES", "MIN_TOKENS_WARN")
MAX_TOKENS_WARN     = config.getint("RULES", "MAX_TOKENS_WARN")
MAX_TOKENS_FAIL     = config.getint("RULES", "MAX_TOKENS_FAIL")

STATIC_CSS          = config.get("API", "STATIC_CSS")
STATIC_JS_SEN       = config.get("API", "STATIC_JS_SEN")

MATH_SYMBOLS        = set("=+-*/^()")

TEMPLATE_HTML       = BASE_DIR / "templates" / "sentence_report.html"
DEFAULT_INPUT       = Path(config.get("API", "SENTENCE_INPUT"))
DEFAULT_HTML        = Path(config.get("API", "SEN_HTML_REPORT"))

SEVERITY = {
    "EMPTY": "FAIL",
    "MATH::SENTENCE": "FAIL",
    "NO::SUBJECT": "WARN",
    "NO::PREDICATE": "FAIL",
    "NO::VERB": "WARN",
    "LEN::TOO_SHORT": "WARN",
    "LEN::TOO_LONG": "WARN",
    "LEN::EXTREME_LONG": "FAIL",
    "PUNCT::NO_TERMINAL": "WARN",
}

FINDING_EXPLANATION = {
    "PUNCT::NO_TERMINAL": "No terminal punctuation / Нет знака препинания",
    "NO::SUBJECT": "No Subject / Нет подлежащего",
    "NO::VERB": "No Verb / Нет глагола",
    "NO::PREDICATE": "No Predicate / Нет сказуемого",
    "LEN::TOO_SHORT": "Sentence too short / Слишком короткое",
    "LEN::TOO_LONG": "Sentence too long / Слишком длинное",
    "LEN::EXTREME_LONG": "Sentence extremely long / Чрезвычайно длинное",
    "MATH::SENTENCE": "Looks like a math expression / Похоже на формулу",
    "Semantic Mismatch": "Semantic similarity below threshold",
    "Empty Answer": "No meaningful content returned",
    "OK": "OK",
    "WARN": "WARN",
    "FAIL": "FAIL",
}

# ============================================================
# NLP
# ============================================================

try:
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
except OSError:
    raise RuntimeError("spaCy model 'en_core_web_sm' not installed. Run: python -m spacy download en_core_web_sm")

# ============================================================
# UTILITIES
# ============================================================

def esc(s: str) -> str:
    return html.escape(s or "", quote=True)

def semantic_similarity(expected, actual, embedder):
    if not expected.strip() or not actual.strip():
        return 0.0
    emb = embedder.encode([expected, actual], normalize_embeddings=True)
    return float(np.dot(emb[0], emb[1]))

def is_math_sentence(text: str, threshold=0.20) -> bool:
    math_count = sum(c in MATH_SYMBOLS for c in text)
    return (math_count / max(len(text), 1)) >= threshold

def worst_status(findings):
    if any(SEVERITY.get(f) == "FAIL" for f in findings):
        return "FAIL"
    if any(SEVERITY.get(f) == "WARN" for f in findings):
        return "WARN"
    return "OK"

def primary_reason_key(final_status: str,
                       structural_skipped: bool,
                       similarity: float,
                       findings: list[str]) -> str:

    if final_status == "OK":
        return "OK"

    if structural_skipped:
        return "Semantic Mismatch" if similarity < SEMANTIC_THRESHOLD else "Empty Answer"

    PRIORITY = [
        "NO::PREDICATE",
        "MATH::SENTENCE",
        "LEN::EXTREME_LONG",
        "NO::SUBJECT",
        "NO::VERB",
        "LEN::TOO_LONG",
        "LEN::TOO_SHORT",
        "PUNCT::NO_TERMINAL",
    ]

    for p in PRIORITY:
        if p in findings:
            return p

    return findings[0] if findings else final_status

def pill_kind(reason_key: str) -> str:
    if reason_key in ("Semantic Mismatch", "Empty Answer"):
        return "sem"
    if reason_key.startswith("NO::PREDICATE"):
        return "pred"
    if reason_key.startswith("NO::SUBJECT"):
        return "subj"
    if reason_key.startswith("NO::VERB"):
        return "verb"
    if reason_key.startswith("LEN::"):
        return "len"
    if reason_key.startswith("PUNCT::"):
        return "punct"
    if reason_key.startswith("MATH::"):
        return "math"
    return "sem"

# ============================================================
# SENTENCE FRAGMENT MERGE
# ============================================================

def merge_sentence_fragments(sentences):
    merged = []
    i = 0
    while i < len(sentences):
        cur = sentences[i]
        if i + 1 < len(sentences):
            nxt = sentences[i + 1]
            cur_doc = nlp(cur)
            has_root = any(t.dep_ == "ROOT" and t.pos_ in ("VERB", "AUX") for t in cur_doc)
            if not has_root and nxt and nxt[0].isupper():
                merged.append(cur.rstrip() + " " + nxt.lstrip())
                i += 2
                continue
        merged.append(cur)
        i += 1
    return merged

# ============================================================
# SENTENCE VALIDATION
# ============================================================

def validate_sentence(doc):
    findings = []

    text = doc.text

    if is_math_sentence(text):
        return ["MATH::SENTENCE"]

    tokens = [t for t in doc if not t.is_space]
    token_count = len(tokens)

    if token_count <= MIN_TOKENS_WARN:
        findings.append("LEN::TOO_SHORT")
    elif token_count > MAX_TOKENS_FAIL:
        findings.append("LEN::EXTREME_LONG")
    elif token_count > MAX_TOKENS_WARN:
        findings.append("LEN::TOO_LONG")

    if not text.rstrip().endswith((".", "?", "!")):
        findings.append("PUNCT::NO_TERMINAL")

    has_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in tokens)
    has_verb = any(t.pos_ in ("VERB", "AUX") for t in tokens)
    has_predicate = any(t.dep_ == "ROOT" and t.pos_ in ("VERB", "AUX") for t in tokens)

    if not has_predicate:
        findings.append("NO::PREDICATE")
    if not has_subject:
        findings.append("NO::SUBJECT")
    if not has_verb:
        findings.append("NO::VERB")

    return findings

# ============================================================
# HTML REPORT RENDERING
# ============================================================

def render_reason_pills(final_status: str, reasons_all: list[str]) -> str:
    if final_status == "OK":
        return ""

    status_cls = final_status.lower()

    pills = []
    for r in reasons_all:
        if r in ("OK", "WARN", "FAIL"):
            continue

        title = FINDING_EXPLANATION.get(r, r)
        pills.append(
            f"<span class='pill {status_cls} {pill_kind(r)}' "
            f"title='{esc(title)}'>{esc(r)}</span>"
        )

    return " ".join(pills)

def write_html_report(rows, summary, output_html):
    blocks_html = ""

    ids = [r.get("id", "") for r in rows]
    sims = [round(float(r.get("similarity", 0.0)) * 100.0, 2) for r in rows]

    for r in rows:
        status = r["final"]
        reasons_all = r.get("reasons_all", [])
        reasons_csv = ",".join(reasons_all)

        label = render_reason_pills(status, reasons_all)

        blocks_html += f"""
    <details class="result" data-status="{esc(status)}"
        data-reason="{esc(r['reason_key'])}"
        data-reasons="{esc(reasons_csv)}"
        data-id="{esc(r['id'])}"
        data-question="{esc(r['question'])}">

    <summary>
        <span class="col id">{esc(r['id'])}</span>
        <span class="col question">{esc(r['question'])}</span>
        <span class="col sim">{r['similarity']*100:.2f}%</span>
        <span class="col status status-{status.lower()}">{status}</span>
        <span class="col reasons">{render_reason_pills(status, reasons_all)}</span>
    </summary>

    <div class="details">
        <b>Expected:</b>
            <pre>{esc(r['expected'])}</pre>
        <hr/>
        <b>Actual:</b>
        <pre>{esc(r['actual'])}</pre>
"""

        if r["structural_skipped"]:
            blocks_html += "    <div class='small'><i>Sentence checks skipped</i></div>\n  </div>\n</details>\n"
            continue

        blocks_html += """
    <table class="sent-table">
        <thead>
            <tr>
                <th>#</th><th>Status</th><th>Tokens</th>
                <th>Sentence</th><th>Findings</th>
            </tr>
        </thead>
    <tbody>
"""

        for s in r["sentences"]:
            if s["findings"]:
                findings_html = "<br>".join(
                    f"{esc(f)} — {esc(FINDING_EXPLANATION.get(f,''))}" for f in s["findings"]
                )
            else:
                findings_html = "None"

            blocks_html += f"""
            <tr>
                <td>{s['index']}</td>
                <td class="cell-status {esc(s['status'])}">{esc(s['status'])}</td>
                <td>{s['tokens']}</td>
                <td>{esc(s['sentence'])}</td>
                <td>{findings_html}</td>
            </tr>
"""
        blocks_html += """
      </tbody>
    </table>
  </div>
</details>
"""

    if not TEMPLATE_HTML.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_HTML}")

    template = TEMPLATE_HTML.read_text(encoding="utf-8-sig")


    html = (
        template
        .replace("{{TOTAL}}", str(summary["items_total"]))
        .replace("{{PASSED}}", str(summary["items_ok"]))
        .replace("{{WARNED}}", str(summary["items_warn"]))
        .replace("{{FAILED}}", str(summary["items_fail"]))
        .replace("{{OK_COUNT}}", str(summary["items_ok"]))
        .replace("{{WARN_COUNT}}", str(summary["items_warn"]))
        .replace("{{FAIL_COUNT}}", str(summary["items_fail"]))
        .replace("{{IDS_JSON}}", json.dumps(ids))
        .replace("{{SIMS_JSON}}", json.dumps(sims))
        .replace("{{TABLES}}", blocks_html)
        .replace("{{CSS_PATH}}", STATIC_CSS)
        .replace("{{JS_PATH}}", STATIC_JS_SEN)
        .replace("{{TIMESTAMP}}", summary["generated"])
        .replace("{{THRESHOLD}}", str(int(SEMANTIC_THRESHOLD * 100)))
    )

    Path(output_html).write_text(html, encoding="utf-8-sig")

# ============================================================
# PIPELINE
# ============================================================

def run(input_json: str, output_html: str):
    start_time = time.time()

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        embedder = SentenceTransformer(EMBED_MODEL, device="cpu", trust_remote_code=False)
    
    with open(input_json, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if "results" not in data or not isinstance(data["results"], list):
        raise ValueError("Invalid semantic_output.json format: missing 'results' list")

    rows = []
    exit_fail = False
    finding_counter = Counter()

    for r in data["results"]:

        qid = r.get("id", "")
        question = r.get("question", "")
        expected = r.get("expected", "")
        actual = r.get("actual", "")

        similarity = semantic_similarity(expected, actual, embedder)

        if not actual.strip():
            final_status = "FAIL"
            rkey = primary_reason_key("FAIL", True, similarity, [])

            rows.append({
                "id": qid,
                "question": question,
                "expected": expected,
                "actual": "",
                "similarity": similarity,
                "final": final_status,
                "reason_key": rkey,
                "reasons_all": [rkey],
                "structural_skipped": True,
                "sentences": []
            })
            exit_fail = True
            continue

        if similarity < SEMANTIC_THRESHOLD:
            final_status = "FAIL"
            rkey = primary_reason_key("FAIL", True, similarity, [])

            rows.append({
                "id": qid,
                "question": question,
                "expected": expected,
                "actual": actual,
                "similarity": similarity,
                "final": final_status,
                "reason_key": rkey,
                "reasons_all": [rkey],
                "structural_skipped": True,
                "sentences": []
            })
            exit_fail = True
            continue

        doc_full = nlp(actual)
        sentence_spans = list(doc_full.sents)

        sentence_results = []
        item_findings = []

        for i, sent in enumerate(sentence_spans, 1):

            tokens = [t for t in sent if not t.is_space]
            token_count = len(tokens)

            findings = validate_sentence(sent)
            status = worst_status(findings)

            item_findings.extend(findings)

            for fnd in findings:
                finding_counter[fnd] += 1

            sentence_results.append({
                "index": i,
                "status": status,
                "tokens": token_count,
                "sentence": sent.text,
                "findings": findings
            })


        final_status = worst_status(item_findings)
        rkey = primary_reason_key(final_status, False, similarity, item_findings)


        if final_status != "OK":
            reasons_all = sorted(
                set(item_findings),
                key=lambda x: (SEVERITY.get(x) != "FAIL", x)
            )
        else:
            reasons_all = []

        if final_status == "FAIL":
            exit_fail = True

        rows.append({
            "id": qid,
            "question": question,
            "expected": expected,
            "actual": actual,
            "similarity": similarity,
            "final": final_status,
            "reason_key": rkey,
            "reasons_all": reasons_all,
            "structural_skipped": False,
            "sentences": sentence_results
        })

    summary = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items_total": len(rows),
        "items_ok": sum(1 for r in rows if r["final"] == "OK"),
        "items_warn": sum(1 for r in rows if r["final"] == "WARN"),
        "items_fail": sum(1 for r in rows if r["final"] == "FAIL"),
        "finding_counts": dict(finding_counter),
    }

    write_html_report(rows, summary, output_html)

    print("\n========= DONE =========")
    print(f"HTML -> {output_html}\n")

    print(f"Runtime: {time.time() - start_time:.2f}s")

    sys.exit(1 if exit_fail else 0)

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) == 1:
        input_path = DEFAULT_INPUT
        output_path = DEFAULT_HTML

    elif len(sys.argv) == 2:
        input_path = Path(sys.argv[1])
        output_path = input_path.with_name("sentence_validation_report.html")

    elif len(sys.argv) == 3:
        input_path = Path(sys.argv[1])
        output_path = Path(sys.argv[2])

    else:
        print("Usage:")
        print("  python 8_sentence_validation.py")
        print("  python 8_sentence_validation.py <input.json>")
        print("  python 8_sentence_validation.py <input.json> <output.html>")
        sys.exit(2)

    if output_path.suffix.lower() != ".html":
        output_path = output_path.with_suffix(".html")

    run(str(input_path), str(output_path))
