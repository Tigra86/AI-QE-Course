# python sqlite.py -d my.db -s input.sql -r report.html
# python sqlite.py --db my.db --sql input.sql --report report.txt

import argparse
import html
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Execute SQL from file against SQLite and generate a report.")
    parser.add_argument("-d", "--db", required=True, help="Path to SQLite database file (created if it does not exist)")
    parser.add_argument("-s", "--sql", required=True, help="Path to input SQL file")
    parser.add_argument("-r", "--report", required=True, help="Report output file name/path (.html or .txt)")
    return parser.parse_args()

def read_sql_file(sql_path: Path) -> str:
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    return sql_path.read_text(encoding="utf-8")

def split_sql_statements(sql_text: str) -> list[str]:
    statements = []
    current = []

    in_single_quote = False
    in_double_quote = False

    for ch in sql_text:
        if ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote

        if ch == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(ch)

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements

def format_rows_as_text(columns, rows):
    lines = []

    if columns:
        lines.append(" | ".join(columns))
        lines.append("-" * (len(" | ".join(columns))))

    if rows:
        for row in rows:
            lines.append(" | ".join("" if v is None else str(v) for v in row))
    else:
        lines.append("[No rows returned]")
    return "\n".join(lines)

def execute_statements(db_path: Path, statements: list[str]):
    results = []
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        for i, statement in enumerate(statements, start=1):
            entry = {
                "index": i,
                "sql": statement,
                "success": True,
                "rowcount": 0,
                "columns": [],
                "rows": [],
                "message": ""
            }

            try:
                cursor.execute(statement)

                if cursor.description is not None:
                    entry["columns"] = [col[0] for col in cursor.description]
                    entry["rows"] = cursor.fetchall()
                    entry["rowcount"] = len(entry["rows"])
                    entry["message"] = "SELECT executed successfully"
                else:
                    conn.commit()
                    entry["rowcount"] = cursor.rowcount
                    entry["message"] = "Statement executed successfully"

            except Exception as e:
                conn.rollback()
                entry["success"] = False
                entry["message"] = str(e)
            results.append(entry)
    finally:
        conn.close()
    return results

def write_raw_output(output_dir: Path, timestamp: str, results: list[dict]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_file = output_dir / f"{timestamp}.txt"

    lines = []
    lines.append(f"Execution Timestamp: {timestamp}")
    lines.append("=" * 80)

    for result in results:
        lines.append(f"Statement #{result['index']}")
        lines.append(f"SQL: {result['sql']}")
        lines.append(f"Success: {result['success']}")
        lines.append(f"Message: {result['message']}")
        lines.append(f"Row count: {result['rowcount']}")

        if result["success"] and result["columns"]:
            lines.append("Result:")
            lines.append(format_rows_as_text(result["columns"], result["rows"]))

        lines.append("-" * 80)

    raw_file.write_text("\n".join(lines), encoding="utf-8")
    return raw_file

def build_txt_report(timestamp: str, db_path: Path, sql_path: Path, raw_output_path: Path, results: list[dict]) -> str:
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    lines = []
    lines.append("SQLITE EXECUTION REPORT")
    lines.append("=" * 80)
    lines.append(f"Timestamp     : {timestamp}")
    lines.append(f"Database      : {db_path}")
    lines.append(f"SQL file      : {sql_path}")
    lines.append(f"Raw output    : {raw_output_path}")
    lines.append(f"Statements    : {len(results)}")
    lines.append(f"Successful    : {success_count}")
    lines.append(f"Failed        : {fail_count}")
    lines.append("")

    for result in results:
        lines.append(f"[Statement #{result['index']}]")
        lines.append(f"SQL      : {result['sql']}")
        lines.append(f"Status   : {'PASS' if result['success'] else 'FAIL'}")
        lines.append(f"Message  : {result['message']}")
        lines.append(f"Row count: {result['rowcount']}")

        if result["success"] and result["columns"]:
            lines.append("Rows:")
            lines.append(format_rows_as_text(result["columns"], result["rows"]))

        lines.append("")

    return "\n".join(lines)

def build_html_report(timestamp: str, db_path: Path, sql_path: Path, raw_output_path: Path, results: list[dict]) -> str:
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "  <title>SQLite Report</title>",
        "  <style>",
        "    body { font-family: Arial, sans-serif; margin: 24px; color: #222; }",
        "    h1, h2 { margin-bottom: 8px; }",
        "    .summary { margin-bottom: 24px; padding: 12px; background: #f6f6f6; border-radius: 8px; }",
        "    .stmt { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px; }",
        "    .pass { color: green; font-weight: bold; }",
        "    .fail { color: red; font-weight: bold; }",
        "    pre { background: #fafafa; padding: 12px; border-radius: 6px; overflow-x: auto; }",
        "    table { border-collapse: collapse; width: 100%; margin-top: 10px; }",
        "    th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }",
        "    th { background: #efefef; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h1>SQLite Execution Report</h1>",
        "  <div class='summary'>",
        f"    <p><strong>Timestamp:</strong> {html.escape(timestamp)}</p>",
        f"    <p><strong>Database:</strong> {html.escape(str(db_path))}</p>",
        f"    <p><strong>SQL file:</strong> {html.escape(str(sql_path))}</p>",
        f"    <p><strong>Raw output:</strong> {html.escape(str(raw_output_path))}</p>",
        f"    <p><strong>Statements:</strong> {len(results)}</p>",
        f"    <p><strong>Successful:</strong> {success_count}</p>",
        f"    <p><strong>Failed:</strong> {fail_count}</p>",
        "  </div>"
    ]

    for result in results:
        status_class = "pass" if result["success"] else "fail"
        status_text = "PASS" if result["success"] else "FAIL"

        html_parts.extend([
            "  <div class='stmt'>",
            f"    <h2>Statement #{result['index']}</h2>",
            f"    <p><strong>Status:</strong> <span class='{status_class}'>{status_text}</span></p>",
            f"    <p><strong>Message:</strong> {html.escape(result['message'])}</p>",
            f"    <p><strong>Row count:</strong> {result['rowcount']}</p>",
            "     <p><strong>SQL:</strong></p>",
            f"    <pre>{html.escape(result['sql'])}</pre>",
        ])

        if result["success"] and result["columns"]:
            html_parts.append("<table>")
            html_parts.append("<tr>")
            for col in result["columns"]:
                html_parts.append(f"<th>{html.escape(str(col))}</th>")
            html_parts.append("</tr>")

            if result["rows"]:
                for row in result["rows"]:
                    html_parts.append("<tr>")
                    for value in row:
                        html_parts.append(f"<td>{html.escape('' if value is None else str(value))}</td>")
                    html_parts.append("</tr>")
            else:
                html_parts.append("<tr><td colspan='100%'>No rows returned</td></tr>")

            html_parts.append("</table>")

        html_parts.append("</div>")

    html_parts.extend([
        "</body>",
        "</html>"
    ])

    return "\n".join(html_parts)

def write_report(report_path: Path, content: str):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")

def main():
    args = parse_args()

    db_path = Path(args.db)
    sql_path = Path(args.sql)
    report_path = Path(args.report)

    output_dir = Path("output")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        sql_text = read_sql_file(sql_path)
        statements = split_sql_statements(sql_text)

        if not statements:
            raise ValueError("No SQL statements found in the input file.")

        results = execute_statements(db_path, statements)
        raw_output_path = write_raw_output(output_dir, timestamp, results)

        ext = report_path.suffix.lower()
        if ext == ".html":
            report_content = build_html_report(timestamp2, db_path, sql_path, raw_output_path, results)
        elif ext == ".txt":
            report_content = build_txt_report(timestamp2, db_path, sql_path, raw_output_path, results)
        else:
            raise ValueError("Report file must end with .html or .txt")

        write_report(report_path, report_content)

        print("Done.")
        print(f"Database   : {db_path}")
        print(f"SQL input  : {sql_path}")
        print(f"Raw output : {raw_output_path}")
        print(f"Report     : {report_path}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
    