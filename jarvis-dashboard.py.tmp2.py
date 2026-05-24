import sqlite3
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path

app = FastAPI(title="Jarvis Live Dashboard")

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/tasks")
def list_tasks():
    if not DB_PATH.exists():
        return {"tasks": [], "links": []}
    conn = get_db()
    cursor = conn.execute("SELECT * FROM tasks WHERE status != 'archived' ORDER BY created_at DESC")
    tasks = [dict(row) for row in cursor.fetchall()]
    
    cursor = conn.execute("SELECT * FROM task_links")
    links = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {"tasks": tasks, "links": links}

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #09090b; color: #fafafa; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .status-column { background-color: #18181b; border-radius: 8px; padding: 12px; min-height: 80vh; position: relative; }
        .task-card { background-color: #27272a; border: 1px solid #3f3f46; border-radius: 6px; padding: 12px; margin-bottom: 12px; transition: all 0.2s; cursor: pointer; position: relative; z-index: 10; }
        .task-card:hover { border-color: #71717a; transform: scale(1.02); box-shadow: 0 4px 20px -5px rgba(0,0,0,0.5); }
        .badge { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }
        .badge-programmer { background-color: #1e3a8a; color: #bfdbfe; }
        .badge-researcher { background-color: #312e81; color: #c7d2fe; }
        .badge-designer { background-color: #581c87; color: #e9d5ff; }
        svg#swarm-lines { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5; }
    </style>
</head>
<body class="p-8">
    <header class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-2xl font-bold tracking-tight text-blue-500">⚕️ Jarvis Live Dashboard</h1>
            <p class="text-zinc-400">Real-time Hermes Swarm & Kanban</p>
        </div>
        <div id="last-update" class="text-xs text-zinc-500 font-mono uppercase">Updating...</div>
    </header>

    <div class="relative">
        <svg id="swarm-lines"></svg>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10">
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
    </div>

    <script>
        async function fetchTasks() {
            try {
                const res = await fetch('/api/tasks');
                const data = await res.json();
                renderTasks(data.tasks);
                setTimeout(() => renderLinks(data.links), 100);
                document.getElementById('last-update').innerText = 'Sync OK: ' + new Date().toLocaleTimeString();
            } catch (e) {
                console.error('Fetch failed', e);
            }
        }

        function renderTasks(tasks) {
            const cols = {
                triage: document.getElementById('col-triage'),
                todo: document.getElementById('col-todo'),
                in_progress: document.getElementById('col-in_progress'),
                done: document.getElementById('col-done')
            };

            Object.values(cols).forEach(c => c.innerHTML = '');

            tasks.forEach(task => {
                const col = cols[task.status] || cols.todo;
                const card = document.createElement('div');
                card.className = 'task-card';
                card.id = `task-${task.id}`;
                card.innerHTML = `
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-xs text-zinc-500 font-mono">#\${task.id}</span>
                        <span class="badge badge-\${task.assignee}">\${task.assignee}</span>
                    </div>
                    <h3 class="text-sm font-medium mb-1">\${task.title}</h3>
                    <p class="text-xs text-zinc-400 line-clamp-2">\${task.body || ''}</p>
                `;
                col.appendChild(card);
            });
        }

        function renderLinks(links) {
            const svg = document.getElementById('swarm-lines');
            const board = document.querySelector('.grid');
            if (!board) return;
            const boardRect = board.getBoundingClientRect();
            svg.setAttribute('width', boardRect.width);
            svg.setAttribute('height', boardRect.height);
            svg.innerHTML = '';
            
            links.forEach(link => {
                const parent = document.getElementById(`task-\${link.parent_id}`);
                const child = document.getElementById(`task-\${link.child_id}`);
                
                if (parent && child) {
                    const pRect = parent.getBoundingClientRect();
                    const cRect = child.getBoundingClientRect();
                    
                    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                    line.setAttribute("x1", pRect.right - boardRect.left);
                    line.setAttribute("y1", pRect.top + pRect.height/2 - boardRect.top);
                    line.setAttribute("x2", cRect.left - boardRect.left);
                    line.setAttribute("y2", cRect.top + cRect.height/2 - boardRect.top);
                    line.setAttribute("stroke", "#3b82f6");
                    line.setAttribute("stroke-width", "2");
                    line.setAttribute("stroke-dasharray", "4");
                    line.setAttribute("opacity", "0.6");
                    svg.appendChild(line);
                }
            });
        }

        window.addEventListener('resize', fetchTasks);
        setInterval(fetchTasks, 5000);
        fetchTasks();
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)
