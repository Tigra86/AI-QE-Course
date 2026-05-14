import argparse
import html
import sqlite3
import sys
import re
from datetime import datetime
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Run SQL queries against a SQLite database and generate a report.")
    parser.add_argument("-d", "--db", required=True, help="Path to the SQLite database file.")
    parser.add_argument("-s", "--sql", required=True, help="Name of the SQL file (searched for in the 'inputs' folder).")
    parser.add_argument("-r", "--report", required=True, help="Name of the report file (saved in the 'reports' folder).")
    return parser.parse_args()

def read_sql_file(file_path):
    with open(file_path, "r") as f:
        return f.read()

def split_sql_statements(sql_text):
    statements = []
    current_statement = []
    for line in sql_text.splitlines():
        line = line.strip()
        if not line or line.startswith("--"):
            continue
        current_statement.append(line)
        if line.endswith(";"):
            statements.append(" ".join(current_statement))
            current_statement = []
    return statements

def execute_statements(db_path, statements):
    results = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for sql in statements:
        try:
            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                results.append({"sql": sql, "status": "SUCCESS", "data": rows, "columns": columns})
            else:
                conn.commit()
                results.append({"sql": sql, "status": "SUCCESS", "data": None, "columns": None})
        except Exception as e:
            results.append({"sql": sql, "status": "ERROR", "message": str(e)})
    conn.close()
    return results

def write_raw_output(output_dir, filename_prefix, results):
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_output_path = output_dir / f"{filename_prefix}.txt"
    with open(raw_output_path, "w") as f:
        for res in results:
            f.write(f"SQL: {res['sql']}\n")
            f.write(f"STATUS: {res['status']}\n")
            if res["status"] == "SUCCESS" and res["data"] is not None:
                f.write(f"ROWS: {len(res['data'])}\n")
            elif res["status"] == "ERROR":
                f.write(f"ERROR: {res['message']}\n")
            f.write("-" * 40 + "\n")
    return raw_output_path

def build_html_report(timestamp, db_path, sql_path, raw_path, results):
    html_content = f"<html><head><title>SQL Report</title><style>table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #ddd; padding: 8px; }} th {{ background-color: #f2 f2 f2; }} .error {{ color: red; }}</style></head><body>"
    html_content += f"<h1>SQL Execution Report</h1>"
    html_content += f"<p>Executed at: {timestamp}</p>"
    html_content += f"<p>Database: {db_path}</p>"
    html_content += f"<p>SQL File: {sql_path}</p>"
    html_content += f"<p>Raw Log: {raw_path}</p>"
    
    for res in results:
        html_content += f"<h3>Query:</h3><code>{html.escape(res['sql'])}</code>"
        if res["status"] == "SUCCESS":
            html_content += f"<p style='color: green;'>Status: SUCCESS</p>"
            if res["data"]:
                html_content += "<table><tr>"
                for col in res["columns"]:
                    html_content += f"<th>{html.escape(str(col))}</th>"
                html_content += "</tr>"
                for row in res["data"]:
                    html_content += "<tr>"
                    for val in row:
                        html_content += f"<td>{html.escape(str(val))}</td>"
                    html_content += "</tr>"
                html_content += "</table>"
        else:
            html_content += f"<p class='error'>Status: ERROR - {html.escape(res['message'])}</p>"
        html_content += "<hr>"
    html_content += "</body></html>"
    return html_content

def main():
    args = parse_args()
    
    # Plural Folder Logic
    inputs_dir = Path("inputs")
    sql_path = inputs_dir / Path(args.sql).name
    
    if not sql_path.exists():
        print(f"Error: SQL file '{sql_path}' not found.")
        sys.exit(1)

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / Path(args.report).name

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_display = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        sql_text = read_sql_file(sql_path)
        statements = split_sql_statements(sql_text)
        results = execute_statements(Path(args.db), statements)
        
        raw_output_path = write_raw_output(outputs_dir, f"{sql_path.stem}_{timestamp}", results)
        
        report_content = build_html_report(timestamp_display, args.db, sql_path, raw_output_path, results)
        
        with open(report_path, "w") as f:
            f.write(report_content)

        print(f"Success! Report saved to: {report_path}")
    except Exception as e:
        print(f"Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()