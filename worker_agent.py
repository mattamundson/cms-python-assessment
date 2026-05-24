import sqlite3
import os
import time
import random
from pathlib import Path
from brain import JarvisBrain

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))
brain = JarvisBrain()

def process_tasks():
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. Start tasks: Todo -> In Progress
    cursor = conn.execute("SELECT * FROM tasks WHERE status = 'todo' ORDER BY RANDOM() LIMIT 1")
    task = cursor.fetchone()
    
    if task:
        task_id = task['id']
        assignee = task['assignee']
        title = task['title']
        body = task['body']

        print(f"[*] {assignee.upper()} picking up Task #{task_id}: {title}")
        conn.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task_id,))
        conn.commit()

        # REAL REASONING PHASE
        print(f"    [Brain] Reasoning about task: {title}...")
        system_prompt = f"You are the {assignee.capitalize()} Agent in the Jarvis Swarm. " \
                        f"Your goal is to process the following task. " \
                        f"Provide a brief 'Action Plan' and if it's a coding task, provide the code."
        
        prompt = f"Task: {title}\nDetails: {body}\n\nPlease provide your response in a way that I can save to the database."
        
        try:
            result = brain.reason(prompt, system_prompt)
            # Update the task body with the brain's output
            new_body = f"{body}\n\n--- AGENT EXECUTION ---\n{result}"
            conn.execute("UPDATE tasks SET body = ?, status = 'done' WHERE id = ?", (new_body, task_id))
            print(f"[✓] {assignee.upper()} completed Task #{task_id}")
        except Exception as e:
            print(f"    [Error] Brain failed: {e}")
            conn.execute("UPDATE tasks SET status = 'todo' WHERE id = ?", (task_id,))
        
        conn.commit()

    conn.close()

if __name__ == "__main__":
    print("🚀 Starting REAL Worker Agent (Powered by OpenAI)...")
    while True:
        process_tasks()
        print("Waiting for next task cycle (60s)...")
        time.sleep(60)
