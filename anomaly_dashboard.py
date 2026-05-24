import sqlite3
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path
import random

app = FastAPI(title="Jarvis Live Dashboard")

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/tasks")
def list_tasks(
    status_filter: str = Query(None, alias="status"),
    procedure_filter: str = Query(None, alias="procedure")
):
    if not DB_PATH.exists():
        return []
    conn = get_db()
    query = "SELECT * FROM tasks WHERE status != 'archived'"
    params = []

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    # For now, procedure is a dummy field, so filtering it will be based on the dummy data after fetching
    # If it were a real DB field, it would be added to the query here.

    query += " ORDER BY created_at DESC"
    cursor = conn.execute(query, params)
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Add dummy anomaly data, confidence scores, and procedure for demonstration and then filter
    procedures_list = ["Medical Procedure A", "Surgical Procedure B", "Diagnostic Procedure C"]
    filtered_tasks = []
    for task in tasks:
        task["procedure"] = random.choice(procedures_list)
        task["anomaly_score"] = round(random.uniform(0, 1), 2)
        task["confidence_score"] = round(random.uniform(0.5, 1), 2)

        if procedure_filter and task["procedure"] != procedure_filter:
            continue
        filtered_tasks.append(task)

    return filtered_tasks

@app.get("/", response_class=HTMLResponse)
def index():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #09090b; color: #fafafa; font-family: 'Inter', sans-serif; }
        .status-column { background-color: #18181b; border-radius: 8px; padding: 12px; min-height: 80vh; }
        .task-card { background-color: #27272a; border: 1px solid #3f3f46; border-radius: 6px; padding: 12px; margin-bottom: 12px; transition: transform 0.1s; cursor: pointer; }
        .task-card:hover { border-color: #71717a; transform: translateY(-2px); }
        .badge { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }
        .badge-programmer { background-color: #1e3a8a; color: #bfdbfe; }
        .badge-researcher { background-color: #312e81; color: #c7d2fe; }
        .badge-designer { background-color: #581c87; color: #e9d5ff; }
        .badge-ready { color: #4ade80; }
        .badge-blocked { color: #f87171; }
        .badge-done { color: #94a3b8; }
        .score-badge { font-size: 9px; padding: 1px 5px; border-radius: 3px; margin-left: 4px; }
        .anomaly-high { background-color: #fca5a5; color: #b91c1c; } /* Red for high anomaly */
        .anomaly-medium { background-color: #fcd34d; color: #9a3412; } /* Orange for medium anomaly */
        .anomaly-low { background-color: #a7f3d0; color: #065f46; } /* Green for low anomaly */
        .confidence-high { background-color: #d1fae5; color: #065f46; } /* Green for high confidence */
        .confidence-low { background-color: #fee2e2; color: #991b1b; } /* Red for low confidence */
    </style>
</head>
<body class="p-8">
    <header class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-2xl font-bold tracking-tight">⚙️ Jarvis Live Dashboard</h1>
            <p class="text-zinc-400">Real-time Hermes Kanban Status</p>
        </div>
        <div class="flex items-center space-x-4">
            <div id="filter-controls" class="flex items-center space-x-4">
                <select id="status-filter" class="bg-zinc-700 text-white text-sm rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">All States</option>
                    <option value="triage">Triage</option>
                    <option value="todo">Todo</option>
                    <option value="in_progress">In Progress</option>
                    <option value="done">Done</option>
                </select>
                <select id="procedure-filter" class="bg-zinc-700 text-white text-sm rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">All Procedures</option>
                    <option value="Medical Procedure A">Medical Procedure A</option>
                    <option value="Surgical Procedure B">Surgical Procedure B</option>
                    <option value="Diagnostic Procedure C">Diagnostic Procedure C</option>
                </select>
            </div>
            <div id="last-update" class="text-xs text-zinc-500">Updating...</div>
        </div>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div>
            <h2 class="text-sm font-semibold mb-4 text-zinc-500 uppercase tracking-wider">Triage</h2>
            <div id="col-triage" class="status-column"></div>
        </div>
        <div>
            <h2 class="text-sm font-semibold mb-4 text-zinc-500 uppercase tracking-wider">Todo</h2>
            <div id="col-todo" class="status-column"></div>
        </div>
        <div>
            <h2 class="text-sm font-semibold mb-4 text-zinc-500 uppercase tracking-wider">In Progress</h2>
            <div id="col-in_progress" class="status-column"></div>
        </div>
        <div>
            <h2 class="text-sm font-semibold mb-4 text-zinc-500 uppercase tracking-wider">Done</h2>
            <div id="col-done" class="status-column"></div>
        </div>
    </div>

    <script>
        const statusFilter = document.getElementById('status-filter');
        const procedureFilter = document.getElementById('procedure-filter');

        statusFilter.addEventListener('change', fetchTasks);
        procedureFilter.addEventListener('change', fetchTasks);

        async function fetchTasks() {
            try {
                const selectedStatus = statusFilter.value;
                const selectedProcedure = procedureFilter.value;

                let url = '/api/tasks';
                const params = new URLSearchParams();
                if (selectedStatus) {
                    params.append('status', selectedStatus);
                }
                if (selectedProcedure) {
                    params.append('procedure', selectedProcedure);
                }
                if (params.toString()) {
                    url += '?' + params.toString();
                }

                const res = await fetch(url);
                const tasks = await res.json();
                renderTasks(tasks, selectedStatus);
                document.getElementById('last-update').innerText = 'Last updated: ' + new Date().toLocaleTimeString();
            } catch (e) {
                console.error('Fetch failed', e);
            }
        }

        function getAnomalyBadgeClass(score) {
            if (score > 0.75) return 'anomaly-high';
            if (score > 0.4) return 'anomaly-medium';
            return 'anomaly-low';
        }

        function getConfidenceBadgeClass(score) {
            if (score > 0.75) return 'confidence-high';
            return 'confidence-low';
        }

        function renderTasks(tasks, selectedStatus) {
            const cols = {
                triage: document.getElementById('col-triage'),
                todo: document.getElementById('col-todo'),
                in_progress: document.getElementById('col-in_progress'),
                done: document.getElementById('col-done')
            };

            // Clear all columns
            Object.values(cols).forEach(c => c.innerHTML = '');

            tasks.forEach(task => {
                const col = cols[task.status] || cols.todo;
                if (selectedStatus && task.status !== selectedStatus) {
                    // If a specific status is filtered, only show tasks for that status in its column
                    // or if 'All States' is selected, display tasks in their respective columns
                    // This logic ensures that if 'All States' is selected, all tasks show up in their columns.
                    // If a specific status is selected, say 'todo', then only 'todo' tasks are fetched
                    // and rendered, and they should still appear in the 'todo' column.
                }

                const card = document.createElement('div');
                card.className = 'task-card';
                card.innerHTML = `
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-xs text-zinc-500 font-mono">#${task.id}</span>
                        <span class="badge badge-${task.assignee}">${task.assignee}</span>
                    </div>
                    <h3 class="text-sm font-medium mb-1">${task.title}</h3>
                    <p class="text-xs text-zinc-400 line-clamp-2">${task.body || ''}</p>
                    <div class="flex items-center text-xs mt-2">
                        <span class="text-zinc-500 mr-1">Procedure:</span>
                        <span class="text-zinc-300">${task.procedure || 'N/A'}</span>
                    </div>
                    <div class="flex items-center text-xs mt-1">
                        <span class="text-zinc-500 mr-1">Anomaly:</span>
                        <span class="score-badge ${getAnomalyBadgeClass(task.anomaly_score)}">${task.anomaly_score}</span>
                        <span class="text-zinc-500 ml-3 mr-1">Confidence:</span>
                        <span class="score-badge ${getConfidenceBadgeClass(task.confidence_score)}">${task.confidence_score}</span>
                    </div>
                `;
                col.appendChild(card);
            });
        }

        setInterval(fetchTasks, 5000);
        fetchTasks();
    </script>
</body>
</html>
    '''

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)