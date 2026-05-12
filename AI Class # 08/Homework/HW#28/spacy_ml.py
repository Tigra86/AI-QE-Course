
"""
Install:
  pip install spacy
  python -m spacy download en_core_web_sm
  python -m spacy download ru_core_news_sm
"""

import argparse
import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Dict, Optional

import spacy

# ============================================================
# CONFIGURATION
# ============================================================

SEVERITY: Dict[str, str] = {
    "EMPTY": "FAIL",
    "MATH::SENTENCE": "FAIL",

    "NO::SUBJECT": "WARN",
    "NO::VERB": "WARN",
    "NO::PREDICATE": "FAIL",

    "FRAGMENT::EN": "FAIL",
    "FRAGMENT::RU": "WARN",

    "LEN::TOO_SHORT": "WARN",
    "LEN::TOO_LONG": "WARN",
    "LEN::EXTREME_LONG": "FAIL",

    "PUNCT::NO_TERMINAL": "WARN",
}

MIN_LEN = 3
MAX_LEN = 40
EXTREME_LEN = 80
TERMINAL_PUNCT = (".", "!", "?")

Finding = Tuple[str, str]  # (rule, details)

# ============================================================
# NLP MODELS (loaded once)
# ============================================================

NLP_MODELS = {
    "en": spacy.load("en_core_web_sm"),
    "ru": spacy.load("ru_core_news_sm"),
}

# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("spacy_sentence_validator")

def setup_logging(log_path: Optional[str], verbose: bool) -> None:
    logger.setLevel(logging.INFO)

    handlers: List[logging.Handler] = []

    if log_path:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        handlers.append(fh)

    if verbose:
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        handlers.append(sh)

    # Avoid duplicate handlers if re-run in notebook contexts
    logger.handlers = []
    for h in handlers:
        logger.addHandler(h)

# ============================================================
# LANGUAGE DETECTION (deterministic heuristic for EN/RU)
# ============================================================

_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
_LATIN_RE = re.compile(r"[A-Za-z]")

def detect_lang_heuristic(text: str) -> str:
    t = text.strip()
    if not t:
        return "en"

    cyr = len(_CYRILLIC_RE.findall(t))
    lat = len(_LATIN_RE.findall(t))

    if cyr == 0 and lat == 0:
        logger.info("lang=auto decision=en (low-signal text) text=%r", t[:80])
        return "en"

    if cyr > lat:
        return "ru"
    return "en"

# ============================================================
# RUSSIAN-SPECIFIC DETECTORS
# ============================================================

def ru_has_verb(doc) -> bool:
    return any(t.pos_ == "VERB" for t in doc)

def ru_has_subject(doc) -> bool:
    return any(t.dep_ in ("nsubj", "nsubjpass") for t in doc)

def ru_has_predicate(doc) -> bool:
    # 1) verb predicate
    if ru_has_verb(doc):
        return True

    # 2) nominal predicate as ROOT (zero-copula)
    for t in doc:
        if t.dep_ == "ROOT" and t.pos_ in ("NOUN", "ADJ", "PROPN"):
            return True

    # 3) category of state as ROOT (e.g., "Холодно.")
    if any(t.dep_ == "ROOT" and t.pos_ == "ADV" for t in doc):
        return True

    return False

# ============================================================
# VALIDATION
# ============================================================

def validate_sentence(text: str, lang: str) -> List[Finding]:
    findings: List[Finding] = []
    text = text.strip()

    if not text:
        return [("EMPTY", "")]

    if re.fullmatch(r"[\d\s\W]+", text):
        findings.append(("MATH::SENTENCE", ""))

    doc = NLP_MODELS[lang](text)

    # LENGTH (token count ignoring punctuation)
    token_count = len([t for t in doc if not t.is_punct])
    if token_count > EXTREME_LEN:
        findings.append(("LEN::EXTREME_LONG", f"tokens={token_count}, extreme={EXTREME_LEN}"))
    elif token_count > MAX_LEN:
        findings.append(("LEN::TOO_LONG", f"tokens={token_count}, max={MAX_LEN}"))
    elif token_count < MIN_LEN:
        findings.append(("LEN::TOO_SHORT", f"tokens={token_count}, min={MIN_LEN}"))

    if lang == "en":
        has_verb = any(t.pos_ == "VERB" for t in doc)
        has_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in doc)
        has_predicate = any(
            t.pos_ == "VERB" and "Fin" in t.morph.get("VerbForm", [])
            for t in doc
        )

        if not has_verb:
            findings.append(("NO::VERB", "en-no-verb"))
            findings.append(("FRAGMENT::EN", "en-fragment-no-verb"))

        if not has_subject:
            findings.append(("NO::SUBJECT", "en-no-subject"))

        if not has_predicate:
            findings.append(("NO::PREDICATE", "en-no-predicate"))

    elif lang == "ru":
        has_verb = ru_has_verb(doc)
        has_subject = ru_has_subject(doc)
        has_predicate = ru_has_predicate(doc)

        if not has_verb:
            findings.append(("NO::VERB", "Нет глагола"))

        if not has_subject:
            findings.append(("NO::SUBJECT", "Нет подлежащего"))

        if not has_predicate:
            findings.append(("NO::PREDICATE", "Нет сказуемого"))
            findings.append(("FRAGMENT::RU", "Неполное предложение"))

    if text[-1] not in TERMINAL_PUNCT:
        findings.append(("PUNCT::NO_TERMINAL", "Отсутствует знак препинания"))

    return findings

def severity_level(findings: List[Finding]) -> str:
    rules = [rule for rule, _ in findings]
    if any(SEVERITY.get(r) == "FAIL" for r in rules):
        return "FAIL"
    if any(SEVERITY.get(r) == "WARN" for r in rules):
        return "WARN"
    return "PASS"

# ============================================================
# RESULT MODEL
# ============================================================

@dataclass
class RowResult:
    line_no: int
    lang: str
    text: str
    level: str
    findings: List[Finding]

# ============================================================
# HTML REPORT
# ============================================================

def render_html_report(results: List[RowResult], input_file: str, html_path: str) -> None:
    total = len(results)
    pass_n = sum(1 for r in results if r.level == "PASS")
    warn_n = sum(1 for r in results if r.level == "WARN")
    fail_n = sum(1 for r in results if r.level == "FAIL")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    rows_html = []
    for r in results:
        findings_html = ""
        if r.findings:
            items = []
            for rule, detail in r.findings:
                sev = SEVERITY.get(rule, "WARN")
                suffix = f" [{esc(detail)}]" if detail else ""
                items.append(f"<li><code>{esc(rule)}</code> <span class='sev sev-{sev.lower()}'>{sev}</span>{suffix}</li>")
            findings_html = "<ul class='findings'>" + "".join(items) + "</ul>"
        else:
            findings_html = "<span class='muted'>None</span>"

        rows_html.append(
            f"""
            <tr class="row-{r.level.lower()}">
              <td>{r.line_no}</td>
              <td><code>{esc(r.lang)}</code></td>
              <td><span class="badge badge-{r.level.lower()}">{r.level}</span></td>
              <td class="sentence">{esc(r.text) if r.text else '<span class="muted">&lt;EMPTY&gt;</span>'}</td>
              <td>{findings_html}</td>
            </tr>
            """
        )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Sentence Validator Report</title>
  <style>
    :root {{
      --bg: #ffffff;
      --text: #111;
      --muted: #666;
      --border: #e5e5e5;
      --pass: #1a7f37;
      --warn: #b54708;
      --fail: #b42318;
      --chip: #f2f4f7;
    }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      margin: 24px;
      background: var(--bg);
      color: var(--text);
    }}
    .header {{
      display: flex;
      gap: 16px;
      align-items: baseline;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }}
    .title {{
      font-size: 20px;
      font-weight: 700;
    }}
    .meta {{
      color: var(--muted);
      font-size: 13px;
    }}
    .summary {{
      display: flex;
      gap: 10px;
      margin: 14px 0 18px 0;
      flex-wrap: wrap;
    }}
    .chip {{
      background: var(--chip);
      border: 1px solid var(--border);
      padding: 8px 10px;
      border-radius: 999px;
      font-size: 13px;
    }}
    .chip b {{ margin-right: 6px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid var(--border);
      padding: 10px 12px;
      vertical-align: top;
      font-size: 13px;
    }}
    th {{
      text-align: left;
      background: #fafafa;
      font-weight: 700;
    }}
    tr:last-child td {{ border-bottom: none; }}
    .badge {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 12px;
      border: 1px solid var(--border);
      background: #fff;
    }}
    .badge-pass {{ color: var(--pass); }}
    .badge-warn {{ color: var(--warn); }}
    .badge-fail {{ color: var(--fail); }}
    .sev {{
      display: inline-block;
      padding: 2px 6px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      margin-left: 6px;
      border: 1px solid var(--border);
      background: #fff;
    }}
    .sev-pass {{ color: var(--pass); }}
    .sev-warn {{ color: var(--warn); }}
    .sev-fail {{ color: var(--fail); }}
    .sentence {{
      word-break: break-word;
      white-space: pre-wrap;
    }}
    .findings {{
      margin: 0;
      padding-left: 18px;
    }}
    .muted {{ color: var(--muted); }}
    .row-pass {{ background: #fbfffb; }}
    .row-warn {{ background: #fffdf7; }}
    .row-fail {{ background: #fff7f7; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">Sentence Validator Report</div>
    <div class="meta">Generated: {esc(now)} | Input: {esc(input_file)}</div>
  </div>

  <div class="summary">
    <div class="chip"><b>Total</b> {total}</div>
    <div class="chip"><b>PASS</b> {pass_n}</div>
    <div class="chip"><b>WARN</b> {warn_n}</div>
    <div class="chip"><b>FAIL</b> {fail_n}</div>
    <div class="chip"><b>Thresholds</b> MIN={MIN_LEN}, MAX={MAX_LEN}, EXTREME={EXTREME_LEN}</div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width:70px;">Line</th>
        <th style="width:70px;">Lang</th>
        <th style="width:80px;">Level</th>
        <th>Sentence</th>
        <th style="width:360px;">Findings</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8-sig") as f:
        f.write(html_doc)

# ============================================================
# MAIN
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Multilingual syntactic validator (EN/RU) with HTML + logging")
    parser.add_argument("input", help="Input text file (one sentence per line)")
    parser.add_argument("-l", "--lang", choices=["en", "ru", "auto"], default="en",
                        help="Language: en | ru | auto (default: en)")
    parser.add_argument("--html", dest="html_path", default=None,
                        help="Write an HTML report to this path (e.g., report.html)")
    parser.add_argument("--log", dest="log_path", default=None,
                        help="Write logs to this file (e.g., validator.log)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Also log to console")

    args = parser.parse_args()

    setup_logging(args.log_path, args.verbose)
    logger.info("start input=%s lang=%s html=%s log=%s", args.input, args.lang, args.html_path, args.log_path)

    results: List[RowResult] = []

    with open(args.input, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.rstrip("\n")
            s = raw.strip()

            if args.lang == "auto":
                detected = detect_lang_heuristic(s)
                logger.info("line=%d lang=auto detected=%s text=%r", line_no, detected, s[:120])
                lang = detected
            else:
                lang = args.lang

            findings = validate_sentence(raw, lang=lang)
            level = severity_level(findings)

            results.append(RowResult(
                line_no=line_no,
                lang=lang,
                text=s,
                level=level,
                findings=findings
            ))

            # Console-style output (always)
            sentence_out = s if s else "<EMPTY>"
            print(f"[{level}] Line {line_no} ({lang}): {sentence_out}")
            for rule, detail in findings:
                sev = SEVERITY.get(rule, "WARN")
                suffix = f" [{detail}]" if detail else ""
                print(f"  - {rule} ({sev}){suffix}")
            print()

    if args.html_path:
        render_html_report(results, input_file=args.input, html_path=args.html_path)
        logger.info("html_report_written path=%s", args.html_path)

    # Summary log
    pass_n = sum(1 for r in results if r.level == "PASS")
    warn_n = sum(1 for r in results if r.level == "WARN")
    fail_n = sum(1 for r in results if r.level == "FAIL")
    logger.info("done total=%d pass=%d warn=%d fail=%d", len(results), pass_n, warn_n, fail_n)

if __name__ == "__main__":
    main()