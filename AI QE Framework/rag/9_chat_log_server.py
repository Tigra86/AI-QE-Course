import json
from pathlib import Path
from datetime import datetime
import html

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "log" / "chat_logs.jsonl"
OUTPUT_FILE = BASE_DIR / "reports" / "chat_log_viewer.html"

def load_logs(path):
    logs = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    return logs


def generate_html(logs):

    logs_json = json.dumps(logs)

def generate_html(logs):

    logs_json = json.dumps(logs)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Chat Logs Viewer</title>

<style>
body {{
    background:#0b1220;
    font-family: system-ui, -apple-system;
    color:#e6edf3;
    margin:0;
    padding:30px;
}}

h1 {{ margin-bottom:5px; }}
.sub {{ color:#8b9bb3; margin-bottom:20px; }}

.filters {{
    display:grid;
    grid-template-columns: repeat(4, 1fr);
    gap:15px;
    margin-bottom:25px;
}}

input, select {{
    padding:10px;
    border-radius:8px;
    border:1px solid #22304a;
    background:#111a2b;
    color:white;
}}

.kpis {{
    display:flex;
    gap:20px;
    margin-bottom:25px;
}}

.card {{
    background:#111a2b;
    padding:20px;
    border-radius:12px;
    min-width:150px;
}}

.card h2 {{ margin:0; font-size:28px; }}

.result {{
    background:#111a2b;
    border-radius:14px;
    margin-bottom:15px;
    overflow:hidden;
    transition:all .2s ease;
}}

.result-header {{
    padding:18px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    cursor:pointer;
}}

.result-header:hover {{
    background:#16223a;
}}

.result-details {{
    max-height:0;
    overflow:hidden;
    transition:max-height .3s ease;
    background:#0f172a;
    padding:0 18px;
}}

.result.open .result-details {{
    padding:18px;
    max-height:800px;
}}

.badge {{
    padding:6px 12px;
    border-radius:20px;
    font-size:12px;
}}

.final {{ background:#083344; color:#22d3ee; }}
.ml {{ background:#1e1b4b; color:#a5b4fc; }}
.reason {{ background:#1f2937; }}
.prob {{ background:#064e3b; color:#34d399; }}

pre {{
    background:#0b1220;
    padding:10px;
    border-radius:8px;
    overflow:auto;
    font-size:13px;
}}
</style>
</head>

<body>

<h1>Chat Logs Viewer</h1>
<div class="sub">Expandable audit dashboard for chat_logs.jsonl</div>

<div class="filters">
    <input id="search" placeholder="Search question...">
    <select id="finalFilter"><option value="ALL">Final intent</option></select>
    <select id="mlFilter"><option value="ALL">ML intent</option></select>
    <input id="minProb" type="number" step="0.01" placeholder="Min probability">
</div>

<div class="kpis">
    <div class="card"><div>Total</div><h2 id="total">0</h2></div>
    <div class="card"><div>Visible</div><h2 id="visible">0</h2></div>
    <div class="card"><div>Unique final</div><h2 id="uniqueFinal">0</h2></div>
    <div class="card"><div>Unique reasons</div><h2 id="uniqueReason">0</h2></div>
</div>

<div id="results"></div>

<script>

const DATA = {logs_json};

const resultsDiv = document.getElementById("results");
const searchInput = document.getElementById("search");
const finalFilter = document.getElementById("finalFilter");
const mlFilter = document.getElementById("mlFilter");
const minProb = document.getElementById("minProb");

function uniqueValues(key) {{
    return [...new Set(DATA.map(x => x[key]))].filter(Boolean);
}}

function populateFilters() {{
    uniqueValues("final_intent").forEach(v => {{
        finalFilter.innerHTML += `<option value="${{v}}">${{v}}</option>`;
    }});
    uniqueValues("ml_intent").forEach(v => {{
        mlFilter.innerHTML += `<option value="${{v}}">${{v}}</option>`;
    }});
}}

function render() {{

    const search = searchInput.value.toLowerCase();
    const finalVal = finalFilter.value;
    const mlVal = mlFilter.value;
    const probVal = parseFloat(minProb.value) || 0;

    const filtered = DATA.filter(row => {{
        if(search && !row.question.toLowerCase().includes(search)) return false;
        if(finalVal !== "ALL" && row.final_intent !== finalVal) return false;
        if(mlVal !== "ALL" && row.ml_intent !== mlVal) return false;
        if((row.confidence || 0) < probVal) return false;
        return true;
    }});

    document.getElementById("total").innerText = DATA.length;
    document.getElementById("visible").innerText = filtered.length;
    document.getElementById("uniqueFinal").innerText =
        new Set(filtered.map(x=>x.final_intent)).size;
    document.getElementById("uniqueReason").innerText =
        new Set(filtered.map(x=>x.reason)).size;

    resultsDiv.innerHTML = "";

    filtered.forEach((row, idx) => {{

        const container = document.createElement("div");
        container.className = "result";


        container.innerHTML = `
            <div class="result-header">
                <div>
                    <div style="font-size:13px;color:#94a3b8;">
                        ${{row.timestamp || ""}}
                    </div>
                    <div style="font-size:18px;">
                        ${{row.question}}
                    </div>
                </div>
                <div style="display:flex;gap:10px;">
                    <span class="badge final">${{row.final_intent}}</span>
                    <span class="badge ml">ml: ${{row.ml_intent}}</span>
                    <span class="badge reason">${{row.reason}}</span>
                    <span class="badge prob">
                        p=${{(row.confidence || 0).toFixed(3)}}
                    </span>
                </div>
            </div>

            <div class="result-details">
                <b>Raw JSON:</b>
                <pre>${{JSON.stringify(row, null, 2)}}</pre>
            </div>
        `;

        container.querySelector(".result-header")
            .addEventListener("click", () => {{
                container.classList.toggle("open");
            }});

        resultsDiv.appendChild(container);
    }});
}}

searchInput.addEventListener("input", render);
finalFilter.addEventListener("change", render);
mlFilter.addEventListener("change", render);
minProb.addEventListener("input", render);

populateFilters();
render();

</script>
</body>
</html>
"""

def main():
    logs = load_logs(INPUT_FILE)
    html_doc = generate_html(logs)
    OUTPUT_FILE.write_text(html_doc, encoding="utf-8-sig")
    output_path = BASE_DIR / "reports" / "chat_log_viewer.html"
    print(f"Viewer generated: {output_path.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()