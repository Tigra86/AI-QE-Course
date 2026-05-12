import csv
import os
from datetime import datetime
from statistics import mean

# ==========================
# CONFIG
# ==========================

INPUT_CSV = "ai_results.csv"
OUTPUT_HTML = "ai_results.html"
PROJECT_NAME = "Hallucination Detection"

# ==========================
# DATA MODEL
# ==========================

def load_results(csv_path):
    """Load hallucination results from CSV."""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # normalize types
            r["id"] = int(r["id"])
            r["similarity"] = float(r["similarity"])
            r["similarity_threshold"] = float(r["similarity_threshold"])
            r["rule_fail"] = r["rule_fail"].strip().lower() == "true"
            r["similarity_fail"] = r["similarity_fail"].strip().lower() == "true"
            r["hallucination"] = r["hallucination"].strip().lower() == "true"
            rows.append(r)
    return rows


def compute_metrics(rows):
    total = len(rows)
    if total == 0:
        return {}

    hallucinated = [r for r in rows if r["hallucination"]]

    modes = {}
    for r in rows:
        m = r["mode"]
        modes.setdefault(m, {"total": 0, "hallucinations": 0, "similarities": []})
        
        modes[m]["total"] += 1
        if r["hallucination"]:
            modes[m]["hallucinations"] += 1
        
        modes[m]["similarities"].append(r["similarity"])

    metrics = {
        "total_tests": total,
        "total_hallucinations": len(hallucinated),
        "hallucination_rate": len(hallucinated) / total,
        "avg_similarity_all": mean(r["similarity"] for r in rows),
        "modes": {}
    }

    for mode, agg in modes.items():
        mode_total = agg["total"]
        mode_h = agg["hallucinations"]
        metrics["modes"][mode] = {
            "total": mode_total,
            "hallucinations": mode_h,
            "hallucination_rate": mode_h / mode_total if mode_total else 0.0,
            "avg_similarity": mean(agg["similarities"]) if agg["similarities"] else 0.0
        }

    return metrics


# ==========================
# HTML GENERATION
# ==========================

def generate_html(rows, metrics):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def pct(x):
        return f"{x * 100:.1f}%" if isinstance(x, float) else "N/A"

    total = metrics["total_tests"]
    total_h = metrics["total_hallucinations"]
    rate_h = pct(metrics["hallucination_rate"])
    avg_sim = f"{metrics['avg_similarity_all']:.3f}"

    mode_rows_html = ""
    for mode, m in metrics["modes"].items():
        mode_rows_html += f"""
        <tr>
          <td>{mode}</td>
          <td>{m['total']}</td>
          <td>{m['hallucinations']}</td>
          <td>{pct(m['hallucination_rate'])}</td>
          <td>{m['avg_similarity']:.3f}</td>
        </tr>
        """

    detail_rows_html = ""
    for r in rows:
        hallu_class = "hallu-yes" if r["hallucination"] else "hallu-no"
        detail_rows_html += f"""
        <tr class="{hallu_class}">
          <td>{r["id"]}</td>
          <td>{r["mode"]}</td>
          <td>{r["prompt"]}</td>
          <td>{r["model_output"]}</td>
          <td>{r["ground_truth"]}</td>
          <td>{r["similarity"]:.3f}</td>
          <td>{r["similarity_threshold"]:.3f}</td>
          <td>{r["rule_fail"]}</td>
          <td>{r["similarity_fail"]}</td>
          <td>{r["hallucination"]}</td>
        </tr>
        """

    # Full HTML document
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{PROJECT_NAME} â€“ Report</title>
<style>
  body {{
    font-family: system-ui, sans-serif;
    background: #f5f7fb;
    margin: 0;
    padding: 0;
    color: #222;
  }}
  .container {{
    max-width: 1200px;
    margin: 30px auto;
    background: #fff;
    padding: 24px 30px 40px;
    border-radius: 12px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
  }}
  h1 {{ margin-top: 0; font-size: 26px; }}
  h2 {{ margin-top: 32px; font-size: 20px; }}
  .meta {{ font-size: 13px; color: #666; margin-bottom: 18px; }}
  .summary-cards {{
    display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 10px;
  }}
  .card {{
    flex: 1 1 200px;
    background: #f4f6ff;
    border-radius: 10px;
    padding: 14px 16px;
    border: 1px solid #e0e4ff;
  }}
  .card-title {{
    font-size: 13px;
    color: #555;
    margin-bottom: 6px;
    text-transform: uppercase;
  }}
  .card-value {{ font-size: 20px; font-weight: 600; }}
  .card-bad {{ background: #fff4f4; border-color: #ffd0d0; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
  th, td {{ border: 1px solid #e0e3ec; padding: 8px 10px; }}
  thead th {{ background: #f0f2fa; font-weight: 600; }}
  tbody tr:nth-child(even) {{ background: #fafbff; }}
  .hallu-yes {{ background: #ffecec !important; }}
  .hallu-no {{ background: #effff4 !important; }}
  .footer {{ margin-top: 24px; font-size: 11px; color: #777; text-align: right; }}
</style>
</head>
<body>
  <div class="container">
    <h1>{PROJECT_NAME}</h1>
    <div class="meta">
      Generated: {now}<br>
      Total test cases: {total}
    </div>

    <h2>Summary</h2>

    <div class="summary-cards">
      <div class="card">
        <div class="card-title">Total Tests</div>
        <div class="card-value">{total}</div>
      </div>
      <div class="card card-bad">
        <div class="card-title">Total Hallucinations</div>
        <div class="card-value">{total_h} ({rate_h})</div>
      </div>
      <div class="card">
        <div class="card-title">Average Similarity</div>
        <div class="card-value">{avg_sim}</div>
      </div>
    </div>

    <h2>Per-Mode Metrics</h2>
    <table>
      <thead>
        <tr>
          <th>Mode</th>
          <th>Total</th>
          <th>Hallucinations</th>
          <th>Rate</th>
          <th>Avg Similarity</th>
        </tr>
      </thead>
      <tbody>
        {mode_rows_html}
      </tbody>
    </table>

    <h2>Detailed Results</h2>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Mode</th>
          <th>Prompt</th>
          <th>Model Output</th>
          <th>Ground Truth</th>
          <th>Similarity</th>
          <th>Threshold</th>
          <th>Rule Fail</th>
          <th>Similarity Fail</th>
          <th>Hallucination</th>
        </tr>
      </thead>
      <tbody>
        {detail_rows_html}
      </tbody>
    </table>

    <div class="footer">Hallucination QA Report Â· Generated automatically</div>
  </div>
</body>
</html>
"""
    return html


# ==========================
# MAIN
# ==========================

def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    rows = load_results(INPUT_CSV)
    if not rows:
        raise RuntimeError("No rows loaded from CSV â€“ nothing to report.")

    metrics = compute_metrics(rows)
    html = generate_html(rows, metrics)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML report saved to: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()