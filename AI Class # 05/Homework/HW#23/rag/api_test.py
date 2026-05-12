import csv
import json
import requests
import re
from rapidfuzz import fuzz
from difflib import HtmlDiff
import statistics

API_URL = "http://127.0.0.1:5000/api/predict"

INPUT_FILE = "api_test.csv"
OUTPUT_FILE = "api_output.csv"
HTML_REPORT = "api_report.html"

SIMILARITY_THRESHOLD = 70
# -----------------------------------------
# Helpers
# -----------------------------------------
def normalize(text):
    if not text:
        return ""
    text = text.replace("\\n", "\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()

def call_api(question: str):
    try:
        r = requests.post(API_URL, json={"input": question}, timeout=10)
        r.raise_for_status()
        return r.json().get("answer", "")
    except Exception as e:
        return f"[ERROR: {e}]"

def make_diff(expected: str, actual: str):
    """HTML red/green diff"""
    diff = HtmlDiff(wrapcolumn=60)
    html = diff.make_table(
        expected.splitlines(),
        actual.splitlines(),
        fromdesc="Expected",
        todesc="Actual",
        context=True,
        numlines=2,
    )
    return html
# -----------------------------------------
# Main Test Runner
# -----------------------------------------
def run_test_suite():
    results = []

    print("\n=== Running API Batch Test ===\n")

    with open(INPUT_FILE, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            q_id = row.get("id")
            question = row.get("question", "")
            expected = row.get("expected_answer", "")

            actual = call_api(question)

            # Normalize for similarity
            sim = fuzz.ratio(normalize(expected), normalize(actual))

            status = "PASS" if sim >= SIMILARITY_THRESHOLD else "FAIL"

            print(f"ID {q_id}: {status} ({sim:.1f}%)")

            diff_html = make_diff(expected, actual)

            results.append({
                "id": q_id,
                "question": question,
                "expected": expected,
                "actual": actual,
                "similarity": sim,
                "status": status,
                "diff_html": diff_html
            })

    write_csv(results)
    write_html_report(results)

    print("\n=== Done! Results saved to api_output.csv and api_report.html ===\n")
# -----------------------------------------
# Write CSV Output
# -----------------------------------------
def write_csv(results):
    with open(OUTPUT_FILE, "w", newline='', encoding="utf-8-sig") as f:
        fieldnames = ["id", "question", "expected", "actual", "similarity", "status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for r in results:
            writer.writerow({
                "id": r["id"],
                "question": r["question"],
                "expected": r["expected"],
                "actual": r["actual"],
                "similarity": f"{r['similarity']:.2f}",
                "status": r["status"]
            })
# -----------------------------------------
# HTML Report
# -----------------------------------------
def write_html_report(results):
    total = len(results)
    passed = len([r for r in results if r["status"] == "PASS"])
    failed = total - passed
    accuracy = (passed / total * 100) if total > 0 else 0
    avg_similarity = statistics.mean([r["similarity"] for r in results]) if total > 0 else 0

    # Prepare data for charts
    ids = [r["id"] for r in results]
    sims = [r["similarity"] for r in results]

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>API Test Report</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ padding: 8px 12px; border: 1px solid #ddd; vertical-align: top; }}
            th {{ background-color: #f4f4f4; }}
            .PASS {{ background-color: #d4edda; }}
            .FAIL {{ background-color: #f8d7da; }}
            pre {{ white-space: pre-wrap; }}

            .charts-container {{
                display: flex;
                gap: 20px;
                margin-top: 20px;
            }}
            .chart-box {{
                width: 320px;
                height: 220px;
            }}
        </style>
    </head>

    <body>
        <h1>API Test Report</h1>

        <h2>Summary</h2>
        <ul>
            <li><b>Total tests:</b> {total}</li>
            <li><b>Passed:</b> {passed}</li>
            <li><b>Failed:</b> {failed}</li>
            <li><b>Accuracy:</b> {accuracy:.2f}%</li>
            <li><b>Average similarity:</b> {avg_similarity:.2f}%</li>
        </ul>

        <div class="charts-container">
            <div class="chart-box">
                <canvas id="passFailChart"></canvas>
            </div>
            <div class="chart-box">
                <canvas id="similarityChart"></canvas>
            </div>
        </div>

        <script>
            new Chart(document.getElementById('passFailChart'), {{
                type: 'pie',
                data: {{
                    labels: ['PASS', 'FAIL'],
                    datasets: [{{
                        data: [{passed}, {failed}],
                        backgroundColor: ['#28a745', '#dc3545']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});

            new Chart(document.getElementById('similarityChart'), {{
                type: 'bar',
                data: {{
                    labels: {ids},
                    datasets: [{{
                        label: 'Similarity %',
                        data: {sims},
                        backgroundColor: '#007bff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ beginAtZero: true }}
                    }}
                }}
            }});
        </script>

        <h2>Detailed Results</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Question</th>

                <th>Expected</th>
                <th>Actual</th>

                <th>Similarity</th>
                <th>Status</th>
            </tr>
    """

    for r in results:
        html += f"""
            <tr class="{r['status']}">
                <td>{r['id']}</td>
                <td>{r['question']}</td>


                <td><pre>{r['expected']}</pre></td>
                <td><pre>{r['actual']}</pre></td>

                <td>{r['similarity']:.2f}%</td>
                <td><b>{r['status']}</b></td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    with open(HTML_REPORT, "w", encoding="utf-8-sig") as f:
        f.write(html)
# -----------------------------------------
# Execute
# -----------------------------------------
if __name__ == "__main__":
    run_test_suite()