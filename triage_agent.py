import sqlite3
import os
import time
from pathlib import Path

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))

def process_triage():
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Fetch triaged tasks
    cursor = conn.execute("SELECT * FROM tasks WHERE status = 'triage'")
    triaged_tasks = cursor.fetchall()
    
    if not triaged_tasks:
        print("No tasks in Triage.")
        conn.close()
        return

    print(f"Processing {len(triaged_tasks)} tasks from Triage...")

    for task in triaged_tasks:
        task_id = task['id']
        title = task['title']
        assignee = task['assignee']

        print(f"[*] Processing Task #{task_id}: {title}")

        # 2. Simulate decomposition
        # In a real scenario, this would involve LLM reasoning.
        # Here we simulate creating a specific "Implementation" sub-task.
        sub_task_id = f"{task_id}-impl"
        sub_task_title = f"[IMPL] {title}"
        sub_task_body = f"Decomposed implementation step for: {title}"
        
        # Insert sub-task
        conn.execute("""
            INSERT OR REPLACE INTO tasks (id, title, body, status, assignee)
            VALUES (?, ?, ?, 'todo', ?)
        """, (sub_task_id, sub_task_title, sub_task_body, assignee))

        # Create link
        conn.execute("""
            INSERT OR REPLACE INTO task_links (parent_id, child_id)
            VALUES (?, ?)
        """, (task_id, sub_task_id))

        # 3. Move parent to todo
        conn.execute("UPDATE tasks SET status = 'todo' WHERE id = ?", (task_id,))

    conn.commit()
    print("Triage processing complete.")
    conn.close()

if __name__ == "__main__":
    while True:
        process_triage()
        print("Sleeping for 30 seconds...")
        time.sleep(30)
