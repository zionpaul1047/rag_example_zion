import sqlite3
from pathlib import Path
from app.core.settings import settings

db_path = Path(settings.APP_SQLITE_PATH)
print("DB_PATH:", db_path.resolve())
print("exists:", db_path.exists())

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row["name"] for row in cur.fetchall()]
print("tables:", tables)

for table in tables:
    print(f"\n--- {table} ---")

    cur.execute(f"PRAGMA table_info({table})")
    print("[columns]")
    for col in cur.fetchall():
        print(dict(col))

    print("[sample rows]")
    try:
        cur.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cur.fetchall()
        for row in rows:
            print(dict(row))
    except Exception as e:
        print("select error:", e)

conn.close()