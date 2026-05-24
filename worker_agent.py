import sqlite3
import os
import time
import random
from pathlib import Path

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))

def process_tasks():
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Start tasks: Todo -> In Progress
    # We pick up to 2 tasks at a time to simulate concurrent work
    cursor = conn.execute("SELECT * FROM tasks WHERE status = 'todo' ORDER BY RANDOM() LIMIT 2")
    todo_tasks = cursor.fetchall()
    
    for task in todo_tasks:
        print(f"[*] {task['assignee'].upper()} picking up Task #{task['id']}: {task['title']}")
        conn.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task['id'],))
    
    conn.commit()

    # 2. Complete tasks: In Progress -> Done
    # We simulate a "work duration" by only completing tasks that have been in progress for a bit
    # For the simulation, we'll just randomly complete one active task per cycle
    cursor = conn.execute("SELECT * FROM tasks WHERE status = 'in_progress' ORDER BY RANDOM() LIMIT 1")
    active_task = cursor.fetchone()
    
    if active_task:
        print(f"[✓] {active_task['assignee'].upper()} completed Task #{active_task['id']}")
        conn.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (active_task['id'],))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🚀 Starting Worker Agent Simulation (Flow Logic)...")
    while True:
        process_tasks()
        # Sleep for a minute to allow the UI to show the "In Progress" state clearly
        print("Workers are active. Sleeping for 60 seconds...")
        time.sleep(60)
