# python performance_report.py --in performance_results.json --out performance_report.html

import argparse
import json
import os
from datetime import datetime

# ================= LOAD HISTORY =================

def load_history(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("performance_results.json must be a JSON array")

    data.sort(key=lambda x: x.get("timestamp", ""))
    return data


# ================= FORMAT HELPERS =================

PRECISION = 2

def fmt(v):
    if isinstance(v, (int, float)):
        return f"{v:.{PRECISION}f}"
    return "—"


def fmt_int(v):
    if isinstance(v, (int, float)):
        return str(int(v))
    return "—"

def fmt_ts(ts):
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts

# ================= BUILD REPORT =================

def build_report(history, in_path, out_path):

    if not history:
        raise ValueError("No runs found.")

    latest = history[-1]
    total_metrics = latest.get("metrics", {}).get("total", {})

    # ----------- Build Series Per Step -----------

    steps = ["llm_step1", "tool", "llm_step2", "total"]
    series = {}

    for step in steps:
        x, avg, p95, threshold = [], [], [], None

        for r in history:
            ts = r.get("timestamp")
            m = r.get("metrics", {}).get(step, {})
            if not m:
                continue

            x.append(ts)
            avg.append(m.get("average"))
            p95.append(m.get("p95"))
            threshold = m.get("sla_threshold")

        series[step] = {
            "x": x,
            "avg": avg,
            "p95": p95,
            "threshold": threshold
        }

    # ----------- Run History Table -----------

    rows = ""
    for r in reversed(history):
        ts = fmt_ts(r.get("timestamp", "—"))
        q = r.get("question", "—")
        runs = r.get("runs", "—")
        m_total = r.get("metrics", {}).get("total", {})

        rows += f"""
        <tr>
          <td>{ts}</td>
          <td>{q}</td>
          <td>{runs}</td>
          <td>{fmt(m_total.get("average"))}</td>
          <td>{fmt(m_total.get("p95"))}</td>
          <td>{fmt(m_total.get("p99"))}</td>
          <td>{fmt(m_total.get("std_dev"))}</td>
          <td>{fmt(m_total.get("error_rate_pct"))}%</td>
          <td>{fmt(m_total.get("sla_pass_rate_pct"))}%</td>
        </tr>
        """

    # ----------- HTML -----------

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AI Performance Test Report</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>

<style>
body {{
  margin:0;
  background:linear-gradient(135deg,#0f172a,#020617);
  color:white;
  font-family:system-ui;
  padding:30px;
}}

.summary-card {{
  background:rgba(255,255,255,0.06);
  padding:20px;
  border-radius:14px;
  margin-bottom:30px;
}}

.metrics-table {{
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;   /* KEY FIX */
}}

.metrics-table th,
.metrics-table td {{
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}}

/* Column widths */
.metrics-table th:nth-child(1),
.metrics-table td:nth-child(1) {{
  width: 220px;  /* Metric */
}}

.metrics-table th:nth-child(2),
.metrics-table td:nth-child(2) {{
  width: 140px;  /* Value */
  text-align: right;
}}

.metrics-table th:nth-child(3),
.metrics-table td:nth-child(3) {{
  width: auto;   /* Description expands */
}}

.charts {{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:25px;
  margin-bottom:40px;
}}

.chart-box {{
  background:rgba(255,255,255,0.05);
  border-radius:14px;
  padding:10px;
}}

/* ================= TABLE ================= */

table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}}

thead th {{
  text-align: left;
  font-weight: 600;
  opacity: 0.75;
  padding: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.15);
}}

tbody td {{
  padding: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}}

/* Numeric columns */
th:nth-child(n+3),
td:nth-child(n+3) {{
  text-align: left;
}}

/* Timestamp column */
th:nth-child(1),
td:nth-child(1) {{
  width: 240px;
  white-space: nowrap;
}}

/* Question column */
th:nth-child(2),
td:nth-child(2) {{
  width: 420px;
  white-space: normal;
}}

footer {{
  margin-top:25px;
  font-size:14px;
  opacity:0.5;
}}


</style>
</head>
<body>

<h1>AI Performance Test Report</h1>
<div>
Latest run: {fmt_ts(latest.get("timestamp"))} • Runs: {latest.get("runs")} <br /><br />
</div>

<div class="summary-card">
<h2>Latest Metrics (TOTAL)</h2>

<table class="metrics-table">
<tr><th>Metric</th><th>Value</th><th>Description</th></tr>

<tr><td>Total Runs</td><td>{fmt_int(total_metrics.get("total_runs"))}</td><td>Total executions in this batch.</td></tr>
<tr><td>Average</td><td>{fmt(total_metrics.get("average"))}s</td><td>Mean latency across runs.</td></tr>
<tr><td>P50 (Median)</td><td>{fmt(total_metrics.get("p50"))}s</td><td>50% of runs faster than this.</td></tr>
<tr><td>P95</td><td>{fmt(total_metrics.get("p95"))}s</td><td>Tail latency indicator.</td></tr>
<tr><td>P99</td><td>{fmt(total_metrics.get("p99"))}s</td><td>Extreme worst-case latency.</td></tr>
<tr><td>Trimmed Mean (5%)</td><td>{fmt(total_metrics.get("trimmed_mean_5"))}s</td><td>Average excluding outliers.</td></tr>
<tr><td>Min</td><td>{fmt(total_metrics.get("min"))}s</td><td>Fastest run.</td></tr>
<tr><td>Max</td><td>{fmt(total_metrics.get("max"))}s</td><td>Slowest run.</td></tr>
<tr><td>Std Dev</td><td>{fmt(total_metrics.get("std_dev"))}s</td><td>Latency stability indicator.</td></tr>
<tr><td>Error Rate (%)</td><td>{fmt(total_metrics.get("error_rate_pct"))}%</td><td>Failed runs percentage.</td></tr>
<tr><td>SLA Pass Rate (%)</td><td>{fmt(total_metrics.get("sla_pass_rate_pct"))}%</td><td>Runs meeting SLA.</td></tr>
<tr><td>SLA Threshold</td><td>{fmt(total_metrics.get("sla_threshold"))}s</td><td>Maximum allowed latency.</td></tr>

</table>
</div>

<div class="charts">
  <div class="chart-box"><div id="c1"></div></div>
  <div class="chart-box"><div id="c2"></div></div>
  <div class="chart-box"><div id="c3"></div></div>
  <div class="chart-box"><div id="c4"></div></div>
</div>

<h2>Run History</h2>

<table>
  <thead>
    <tr>
      <th>Timestamp</th>
      <th>Question</th>
      <th>Runs</th>
      <th>Avg</th>
      <th>p95</th>
      <th>p99</th>
      <th>Std Dev</th>
      <th>Error %</th>
      <th>SLA %</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>

<footer>
Generated from {os.path.abspath(in_path)}
</footer>

<script>
const SERIES = {json.dumps(series)};

function render(div, step, title){{
  const s = SERIES[step];

  Plotly.newPlot(div, [
    {{x:s.x,y:s.avg,mode:"lines+markers",name:"Average"}},
    {{x:s.x,y:s.p95,mode:"lines+markers",name:"p95"}}
  ], {{
    title:title,
    paper_bgcolor:"rgba(0,0,0,0)",
    plot_bgcolor:"rgba(0,0,0,0)",
    font:{{color:"white"}},
    hovermode:"x unified",
    shapes:s.threshold ? [{{
      type:"line",
      x0:s.x[0],
      x1:s.x[s.x.length-1],
      y0:s.threshold,
      y1:s.threshold,
      line:{{dash:"dash"}}
    }}] : []
  }}, {{responsive:true}});
}}

render("c1","llm_step1","LLM Step 1 — Latency Trend");
render("c2","tool","Tool — Latency Trend");
render("c3","llm_step2","LLM Step 2 — Latency Trend");
render("c4","total","Total — Latency Trend");
</script>

</body>
</html>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


# ================= MAIN =================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", default="performance_results.json")
    parser.add_argument("--out", dest="out_path", default="performance_report.html")
    args = parser.parse_args()

    history = load_history(args.in_path)
    build_report(history, args.in_path, args.out_path)

    print("Report generated:", args.out_path)


if __name__ == "__main__":
    main()
