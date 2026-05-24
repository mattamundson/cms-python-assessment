import sqlite3
import os
import time
import json
import uuid
from pathlib import Path
from brain import JarvisBrain

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))
brain = JarvisBrain()

def calculate_cost(usage, model="gpt-4o"):
    """Calculates estimated cost based on usage object."""
    INPUT_PRICE = 5.00
    OUTPUT_PRICE = 15.00
    if hasattr(usage, 'prompt_tokens'): # OpenAI
        in_tokens = usage.prompt_tokens
        out_tokens = usage.completion_tokens
    elif hasattr(usage, 'input_tokens'): # Anthropic
        in_tokens = usage.input_tokens
        out_tokens = usage.output_tokens
    else:
        return 0.0, 0
    cost = (in_tokens * (INPUT_PRICE / 1_000_000)) + (out_tokens * (OUTPUT_PRICE / 1_000_000))
    return cost, (in_tokens + out_tokens)

def process_triage_task(task_id):
    """Processes a single task from triage to todo using LLM decomposition."""
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
    body = task['body'] or ""
    assignee = task['assignee']

    print(f"[*] Chief Orchestrator planning Task #{task_id}: {title}")

    system_prompt = (
        "You are the Chief Orchestrator of the Jarvis Swarm. "
        "Your goal is to take a high-level task and decompose it into 2-4 actionable sub-tasks. "
        "Each sub-task must be assigned to one of these profiles: programmer, researcher, designer. "
        "Output ONLY a JSON list of objects with 'title', 'body', and 'assignee' fields."
    )
    
    prompt = f"Decompose this task: {title}\nDetails: {body}"
    
    try:
        response, usage = brain.reason(prompt, system_prompt)
        cost, tokens = calculate_cost(usage)
        
        # Strip potential markdown formatting from JSON
        clean_response = response.replace('```json', '').replace('```', '').strip()
        sub_tasks = json.loads(clean_response)

        for i, st in enumerate(sub_tasks):
            sub_id = f"{task_id}-sub-{i}-{str(uuid.uuid4())[:4]}"
            conn.execute("""
                INSERT OR REPLACE INTO tasks (id, title, body, status, assignee)
                VALUES (?, ?, ?, 'todo', ?)
            """, (sub_id, st['title'], st['body'], st['assignee']))

            conn.execute("""
                INSERT OR REPLACE INTO task_links (parent_id, child_id)
                VALUES (?, ?)
            """, (task_id, sub_id))

        # Move parent to todo and record telemetry
        conn.execute("UPDATE tasks SET status = 'todo', tokens = ?, cost = ? WHERE id = ?", (tokens, cost, task_id))
        print(f"    [✓] Decomposed into {len(sub_tasks)} sub-tasks (${cost:.4f}).")
        
    except Exception as e:
        print(f"    [Error] Planning failed: {e}")
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
    
    cursor = conn.execute("SELECT id FROM tasks WHERE status = 'triage' LIMIT 5")
    triaged_ids = [row['id'] for row in cursor.fetchall()]
    conn.close()
    
    if not triaged_ids:
        print("No tasks in Triage.")
        return

    print(f"Processing {len(triaged_ids)} tasks from Triage...")
    for tid in triaged_ids:
        process_triage_task(tid)

    print("Triage cycle complete.")

if __name__ == "__main__":
    print("🚀 Starting REAL Planning Agent (Chief Orchestrator - Telemetry Enabled)...")
    while True:
        process_triage()
        print("Sleeping for 30 minutes...")
        time.sleep(1800)
