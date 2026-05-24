import sqlite3
import os
import json
import time
from pathlib import Path
from brain import JarvisBrain

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))
brain = JarvisBrain()

def evaluate_and_prioritize():
    """
    Scans the 'todo' list and re-ranks tasks based on estimated ROI and urgency.
    """
    if not DB_PATH.exists():
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get all tasks in 'todo'
    cursor = conn.execute("SELECT * FROM tasks WHERE status = 'todo'")
    tasks = cursor.fetchall()
    
    if not tasks:
        conn.close()
        return

    print(f"[*] ROI Evaluation Agent scanning {len(tasks)} tasks...")
    
    task_list_str = ""
    for t in tasks:
        task_list_str += f"- ID: {t['id']} | Title: {t['title']} | Body: {t['body'][:100]}...\n"

    prompt = f"""
    You are the Strategic ROI Evaluation Agent. Your goal is to rank the following tasks by their projected value to the project and urgency.
    
    TASKS TO EVALUATE:
    {task_list_str}
    
    For each task, provide:
    1. A Priority Score (1-10, where 10 is highest ROI).
    2. A brief ROI Analysis (why this task matters).
    
    Return your response as a JSON object:
    {{
        "evaluations": [
            {{ "id": "task_id", "priority": 10, "analysis": "High impact because..." }},
            ...
        ]
    }}
    """
    
    try:
        response_text, _ = brain.reason(prompt, system_prompt="You are a strategic business analyst.")
        # Clean potential markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        
        data = json.loads(response_text)
        
        for eval in data.get('evaluations', []):
            task_id = eval['id']
            priority = eval['priority']
            analysis = eval['analysis']
            
            conn.execute("UPDATE tasks SET priority = ?, roi_analysis = ? WHERE id = ?", 
                         (priority, analysis, task_id))
            print(f"    [ROI] Task #{task_id} -> Priority {priority}")
            
        conn.commit()
        print("[✓] Strategic re-prioritization complete.")
        
    except Exception as e:
        print(f"    [Error] ROI Evaluation failed: {e}")
        
    conn.close()

if __name__ == "__main__":
    while True:
        evaluate_and_prioritize()
        time.sleep(300) # Re-evaluate every 5 minutes
