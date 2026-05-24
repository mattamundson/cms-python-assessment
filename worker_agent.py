import sqlite3
import os
import time
import json
import random
from pathlib import Path
from brain import JarvisBrain
from tools import JARVIS_TOOLS, execute_tool

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

        # REAL EXECUTION PHASE (WITH HANDS)
        print(f"    [Brain] Executing task with tool access: {title}...")
        system_prompt = (
            f"You are the {assignee.capitalize()} Agent in the Jarvis Swarm. "
            f"You have access to file system tools. Use them to investigate or complete the task if needed. "
            f"If you write code, provide it in the final summary."
        )
        
        prompt = f"Task: {title}\nDetails: {body}"
        
        try:
            # Step 1: Initial call to brain with tools
            message = brain.reason_with_tools(prompt, JARVIS_TOOLS, system_prompt)
            
            execution_log = []
            
            # Step 2: Handle potential tool calls
            while message.tool_calls:
                for tool_call in message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    print(f"    [Tool] Executing {name}({args})...")
                    result = execute_tool(name, args)
                    execution_log.append(f"Tool Call: {name}({args}) -> {result}")
                    
                    # Note: In a production loop, we'd feed this back to the LLM. 
                    # For this phase, we'll execute once and summarize to keep it simple but functional.
                
                # After executing tools, we'll ask the brain for a final summary
                summary_prompt = f"{prompt}\n\nExecution Log:\n" + "\n".join(execution_log) + "\n\nPlease provide a final report on what you did."
                result = brain.reason(summary_prompt, system_prompt)
                break # Exit loop for now
            else:
                # No tools called, just reasoning
                result = message.content

            # Update the task body with the brain's output and log
            log_str = "\n".join(execution_log)
            new_body = f"{body}\n\n--- AGENT EXECUTION ---\n{result}\n\n--- TOOL LOG ---\n{log_str}"
            conn.execute("UPDATE tasks SET body = ?, status = 'done' WHERE id = ?", (new_body, task_id))
            print(f"[✓] {assignee.upper()} completed Task #{task_id}")
            
        except Exception as e:
            print(f"    [Error] Execution failed: {e}")
            conn.execute("UPDATE tasks SET status = 'todo' WHERE id = ?", (task_id,))
        
        conn.commit()

    conn.close()

if __name__ == "__main__":
    print("🚀 Starting REAL Worker Agent (Doer Mode - Tool Access Enabled)...")
    while True:
        process_tasks()
        print("Waiting for next task cycle (60s)...")
        time.sleep(60)
