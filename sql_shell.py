import sqlite3
import os
import glob

print("=" * 40)
print("  SQLite Interactive Shell (Python)")
print("=" * 40)

# Find all .db files in the current directory
db_files = glob.glob("*.db")

if not db_files:
    print("\nNo .db files found in current directory.")
    exit()

print("\nAvailable databases:")
for i, f in enumerate(db_files, 1):
    print(f"  [{i}] {f}")

choice = input("\nSelect database number: ")
try:
    db_path = db_files[int(choice) - 1]
except (ValueError, IndexError):
    print("Invalid choice.")
    exit()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
print(f"\nConnected to: {db_path}")

# Show tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Tables: {[t[0] for t in tables]}\n")

# Show schema
for t in tables:
    schema = conn.execute(f"SELECT sql FROM sqlite_master WHERE name='{t[0]}'").fetchone()
    print(schema[0])
    count = conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    print(f"  -> {count} row(s)\n")

print("Type SQL queries below. Type 'exit' to quit.\n")

while True:
    try:
        query = input("sql> ").strip()
    except (EOFError, KeyboardInterrupt):
        break

    if not query:
        continue
    if query.lower() in ('exit', 'quit', '.quit'):
        break

    try:
        cursor = conn.execute(query)
        if query.upper().startswith("SELECT"):
            rows = cursor.fetchall()
            if rows:
                # Print column headers
                cols = [desc[0] for desc in cursor.description]
                print(" | ".join(cols))
                print("-" * (len(" | ".join(cols))))
                for row in rows:
                    print(" | ".join(str(v) for v in row))
                print(f"({len(rows)} row(s))")
            else:
                print("(0 rows)")
        else:
            conn.commit()
            print(f"OK. {conn.total_changes} row(s) affected.")
    except Exception as e:
        print(f"Error: {e}")

    print()

conn.close()
print("Bye!")
