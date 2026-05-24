import sqlite3
import os
from pathlib import Path

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))

def migrate():
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        print("Adding tokens and cost columns to tasks table...")
        conn.execute("ALTER TABLE tasks ADD COLUMN tokens INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE tasks ADD COLUMN cost REAL DEFAULT 0.0")
        conn.commit()
        print("[✓] Migration complete.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("[!] Columns already exist. Skipping.")
        else:
            print(f"[X] Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
