import sqlite3

conn = sqlite3.connect("aa.db")
cursor = conn.cursor()

cursor.execute("SELECT name, completed FROM students")
rows = cursor.fetchall()

print("----------------")
print(rows)
print("----------------")

for name, completed in rows:

    print(f"01. Completed: Must not be NULL: {name}")
    assert completed is not None, f"{name}: completed is NULL"

    print(f"02. Completed: Must be integer: {name}")
    assert isinstance(completed, int), f"{name}: completed is not int"

    print(f"03. Completed: Must be non-negative: {name}")
    assert completed >= 0, f"{name}: negative completed value"

    print(f"04. Completed: Must not be suspicious magic values: {name}")
    assert completed != -5, f"{name}: invalid sentinel value -5"
    assert completed != 999999, f"{name}: unrealistic large value"

    print(f"05. Completed: Must not exceed logical upper bound: {name}")
    TOTAL_ASSIGNMENTS = 50
    assert completed <= TOTAL_ASSIGNMENTS, (
        f"{name}: completed exceeds total assignments ({completed})"
    )

    print(f"06. Completed: Sanity range check: {name}")
    assert 0 <= completed <= 1000, (
        f"{name}: completed outside sanity bounds"
    )

print("Data quality OK.")