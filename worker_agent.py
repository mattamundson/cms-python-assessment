import sqlite3
import os
import time
import json
import random
from pathlib import Path
from brain import JarvisBrain
from tools import JARVIS_TOOLS, execute_tool, PROJECT_ROOT
from memory import index_task_experience, retrieve_related_experiences

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

def process_tasks():
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Pick the highest priority task first
    cursor = conn.execute("SELECT * FROM tasks WHERE status = 'todo' ORDER BY priority DESC, created_at ASC LIMIT 1")
    task = cursor.fetchone()
    
    if task:
        task_id = task['id']
        assignee = task['assignee']
        title = task['title']
        body = task['body']

        print(f"[*] {assignee.upper()} picking up Task #{task_id}: {title}")
        conn.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task_id,))
        conn.commit()

        print(f"    [Brain] Executing task in multi-turn mode: {title}...")
        
        # Phase 7: Retrieve Related Experiences (RAG)
        past_experiences = []
        try:
            past_experiences = retrieve_related_experiences(title)
            print(f"    [Memory] Retrieved {len(past_experiences)} related experiences.")
        except Exception as e:
            print(f"    [Memory Error] Failed to retrieve: {e}")
            
        context_str = "\n\nPAST EXPERIENCES (Use these if relevant):\n" + "\n---\n".join(past_experiences) if past_experiences else ""

        system_msg = f"""You are the {assignee.capitalize()} Agent in the Jarvis Swarm. 
        Your HOME BASE (PROJECT_ROOT) is: {PROJECT_ROOT}
        Always use relative paths for files. 
        MISSION: {title} 
        DETAILS: {body} 
        {context_str}"""

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"Please complete this task: {title}"}
        ]
        
        total_tokens = 0
        total_cost = 0.0
        execution_log = []
        final_result = "No result generated."
        
        try:
            # Multi-turn tool execution loop (Max 12 turns for complex logic)
            for turn in range(12):
                provider, msg, usage = brain.chat_with_tools(messages, JARVIS_TOOLS)
                
                c, t = calculate_cost(usage)
                total_cost += c
                total_tokens += t
                
                # Append assistant message
                messages.append({"role": "assistant", "content": msg.content})
                
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        print(f"    [Tool] Turn {turn+1} ({provider}): {name}({args})...")
                        result = execute_tool(name, args)
                        execution_log.append(f"Turn {turn+1} - {name}: {result}")
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": name,
                            "content": json.dumps(result)
                        })
                else:
                    # Final answer received
                    final_result = msg.content
                    break
            else:
                final_result = "Reached maximum execution turns (12). Task might be incomplete."

            # Phase 7: Index the successful experience
            try:
                index_task_experience(task_id, title, final_result)
            except Exception as e:
                print(f"    [Memory Error] Failed to index: {e}")

            log_str = "\n".join(execution_log)
            new_body = f"{body}\n\n--- AGENT EXECUTION ---\n{final_result}\n\n--- TOOL LOG ---\n{log_str}"
            conn.execute("UPDATE tasks SET body = ?, status = 'done', tokens = ?, cost = ? WHERE id = ?", 
                         (new_body, total_tokens, total_cost, task_id))
            print(f"[✓] {assignee.upper()} completed Task #{task_id} (${total_cost:.4f})")
            
        except Exception as e:
            print(f"    [Error] Execution failed: {e}")
            conn.execute("UPDATE tasks SET status = 'todo' WHERE id = ?", (task_id,))
        
        conn.commit()

    conn.close()

if __name__ == "__main__":
    print("🚀 Starting REAL Worker Agent (Autonomous Doer - Multi-Turn & Fallback Enabled)...")
    while True:
        process_tasks()
        time.sleep(30)
