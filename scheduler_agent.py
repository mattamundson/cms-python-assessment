import sqlite3
import os
import time
import uuid
from pathlib import Path

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))

def schedule_cms_audit():
    """Adds a recurring CMS Audit task to the Triage column."""
    if not DB_PATH.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    task_id = f"audit-{str(uuid.uuid4())[:8]}"
    title = "REC: Automated CMS Medicare Audit & Regulatory Report"
    body = (
        "Goal: Perform a full end-to-end Medicare audit.\n"
        "1. Run 'python generate_data.py' to refresh practice data.\n"
        "2. Run 'python cms_analysis.py' to identify billing outliers.\n"
        "3. Research '2024 CMS Medicare Part B markup regulations' online for context.\n"
        "4. Compile a final Executive Summary as a new file 'reports/audit_report.md'."
    )
    
    conn.execute("""
        INSERT INTO tasks (id, title, body, status, assignee)
        VALUES (?, ?, ?, 'triage', 'programmer')
    """, (task_id, title, body))
    
    conn.commit()
    conn.close()
    print(f"[Scheduled] Added CMS Audit task: {task_id}")

if __name__ == "__main__":
    print("🚀 Starting Jarvis Scheduler (Autonomous Goal Generator)...")
    # For the demo, we'll schedule one immediately, then every 4 hours.
    while True:
        schedule_cms_audit()
        print("Next audit cycle in 4 hours...")
        time.sleep(14400) # 4 hours
