# SQLite Execution Project

## Overview
This project automates the execution of SQL scripts against an SQLite database and generates structured reports.

## Files
* **sqlite.py**: The Python script used to run SQL commands and generate reports [cite: 2].
* **input.sql**: The SQL file containing table definitions (DDL) and data insertion (DML) for 'customer' and 'credit_card' tables [cite: 3].
* **my.db**: The SQLite database file where the data is stored [cite: 4].
* **report.html**: The formatted execution report showing successful statements, row counts, and query results [cite: 1].
* ** output/20260513_175700.txt**: A text file generated automatically in the `output/` directory. This file is contains unformatted execution logs [cite: 2].

## Execution Details
When running the script with the following command:
`python sqlite.py -d my.db -s input.sql -r report.html`

The system generates two types of output [cite: 2]:
1. **Primary Report**: A formatted HTML file (`report.html`) containing detailed results [cite: 1, 2].
2. **Raw Log**: A text file generated automatically in the `output/` directory [cite: 2]. This file is **timestamped** (e.g., `YYYYMMDD_HHMMSS.txt`) and contains unformatted execution logs [cite: 2].

## Summary of Results
The latest run processed 12 statements with 100% success [cite: 1]:
* Tables Created: `customer`, `credit_card` [cite: 1, 3]
* Data Inserted: 1 customer record and 2 credit card records [cite: 1, 3]
* Final Operation: A JOIN query retrieving customer names alongside their card details [cite: 1, 3]
