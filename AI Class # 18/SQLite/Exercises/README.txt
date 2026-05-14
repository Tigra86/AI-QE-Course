# SQLite SQL Execution Project

This project provides an automated workflow for executing multiple SQL query files against a SQLite database and generating formatted HTML reports along with raw execution logs.

## Folder Structure
- inputs/  : Place all your .sql files here (e.g., task1_rows.sql).
- outputs/ : Contains timestamped raw text logs of every execution.
- reports/ : Contains the final formatted HTML reports for your exercises.

## How the Script Works
The 'sqlite.py' script is designed to:
1. Look into the 'inputs/' folder for the SQL file specified.
2. Execute the queries against the provided SQLite database.
3. Generate a raw log in 'outputs/' named: [sql_filename]_[timestamp].txt.
4. Generate an HTML report in 'reports/' with the name provided via the -r flag.

## Files included in this task:
- task1_rows.sql
- task2_salary.sql
- task3_revenue.sql
- task4_checkbook.sql
- task5_advanced_queries.sql
- task6_time_demo.sql
