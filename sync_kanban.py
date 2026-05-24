import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))
BACKLOG_PATH = Path(os.path.expanduser("~/.hermes/upgrade/backlog.jsonl"))

def init_db(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT,
        body TEXT,
        status TEXT,
        assignee TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS task_links (
        parent_id TEXT,
        child_id TEXT,
        PRIMARY KEY (parent_id, child_id)
    )
    """)
    conn.commit()

def sync():
    if not BACKLOG_PATH.exists():
        print(f"Error: {BACKLOG_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    with open(BACKLOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                task_id = item.get('bookmark_id')
                title = item.get('title')
                body = item.get('rationale')
                status = item.get('apply_status', 'todo')
                
                # Map apply_status to kanban columns
                if status == 'applied':
                    status = 'done'
                elif status == 'pending':
                    status = 'todo'
                elif status == 'failed':
                    status = 'triage'
                
                # Assignee - random for demo or based on type
                assignee = 'programmer'
                if 'research' in title.lower():
                    assignee = 'researcher'
                elif 'design' in title.lower():
                    assignee = 'designer'

                conn.execute("""
                INSERT OR REPLACE INTO tasks (id, title, body, status, assignee)
                VALUES (?, ?, ?, ?, ?)
                """, (task_id, title, body, status, assignee))
            except Exception as e:
                print(f"Error processing line: {e}")

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    print(f"Successfully synced {count} tasks to {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    sync()
