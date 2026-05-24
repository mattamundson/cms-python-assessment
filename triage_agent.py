import sqlite3
import os
import time
from pathlib import Path

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))

def process_triage_task(task_id):
    """Processes a single task from triage to todo."""
    if not DB_PATH.exists():
        return False

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.execute("SELECT * FROM tasks WHERE id = ? AND status = 'triage'", (task_id,))
    task = cursor.fetchone()
    
    if not task:
        conn.close()
        return False

    title = task['title']
    assignee = task['assignee']

    print(f"[*] Manually Triaging Task #{task_id}: {title}")

    # Simulate decomposition
    sub_task_id = f"{task_id}-impl"
    sub_task_title = f"[IMPL] {title}"
    sub_task_body = f"Decomposed implementation step for: {title}"
    
    conn.execute("""
        INSERT OR REPLACE INTO tasks (id, title, body, status, assignee)
        VALUES (?, ?, ?, 'todo', ?)
    """, (sub_task_id, sub_task_title, sub_task_body, assignee))

    conn.execute("""
        INSERT OR REPLACE INTO task_links (parent_id, child_id)
        VALUES (?, ?)
    """, (task_id, sub_task_id))

    conn.execute("UPDATE tasks SET status = 'todo' WHERE id = ?", (task_id,))
    
    conn.commit()
    conn.close()
    return True

def process_triage():
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Fetch triaged tasks
    cursor = conn.execute("SELECT id FROM tasks WHERE status = 'triage'")
    triaged_ids = [row['id'] for row in cursor.fetchall()]
    conn.close()
    
    if not triaged_ids:
        print("No tasks in Triage.")
        return

    print(f"Processing {len(triaged_ids)} tasks from Triage...")
    for tid in triaged_ids:
        process_triage_task(tid)

    print("Triage processing complete.")

if __name__ == "__main__":
    while True:
        process_triage()
        print("Sleeping for 30 minutes...")
        time.sleep(1800)
