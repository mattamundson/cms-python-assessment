import sqlite3
import os
import secrets
from fastapi import FastAPI, HTTPException, Depends, status, Body
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from pathlib import Path

class TaskCreate(BaseModel):
    title: str
    body: str = ""
    assignee: str = "programmer"

app = FastAPI(title="Jarvis Live Dashboard")
security = HTTPBasic()

# Mount outputs for charts
app.mount("/outputs", StaticFiles(directory="C:/Users/mattm/Documents/cms-python-assessment/outputs"), name="outputs")

DB_PATH = Path(os.path.expanduser("~/.hermes/kanban.db"))

# Simple Auth - Defaults for the demo
ADMIN_USER = os.getenv("DASHBOARD_USER", "amo")
ADMIN_PASS = os.getenv("DASHBOARD_PASS", "jarvis2026")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USER)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/tasks")
def list_tasks(username: str = Depends(authenticate)):
    if not DB_PATH.exists():
        return {"tasks": [], "links": []}
    conn = get_db()
    cursor = conn.execute("SELECT * FROM tasks WHERE status != 'archived' ORDER BY created_at DESC")
    tasks = [dict(row) for row in cursor.fetchall()]
    
    cursor = conn.execute("SELECT * FROM task_links")
    links = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {"tasks": tasks, "links": links}

@app.post("/api/tasks")
def create_task(task: TaskCreate, username: str = Depends(authenticate)):
    import uuid
    conn = get_db()
    task_id = str(uuid.uuid4())[:8]
    conn.execute("""
        INSERT INTO tasks (id, title, body, status, assignee)
        VALUES (?, ?, ?, 'triage', ?)
    """, (task_id, task.title, task.body, task.assignee))
    conn.commit()
    conn.close()
    return {"status": "success", "task_id": task_id}

@app.get("/api/reports")
def list_reports(username: str = Depends(authenticate)):
    reports_dir = Path("C:/Users/mattm/Documents/cms-python-assessment/reports")
    if not reports_dir.exists():
        return {"reports": []}
    reports = [f.name for f in reports_dir.glob("*.md")]
    return {"reports": reports}

@app.get("/api/stats")
def get_stats(username: str = Depends(authenticate)):
    if not DB_PATH.exists():
        return {"status_counts": {}, "assignee_counts": {}, "total_tokens": 0, "total_cost": 0.0}
    conn = get_db()
    
    cursor = conn.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
    
    cursor = conn.execute("SELECT assignee, COUNT(*) as count FROM tasks GROUP BY assignee")
    assignee_counts = {row['assignee']: row['count'] for row in cursor.fetchall()}

    cursor = conn.execute("SELECT SUM(tokens) as total_tokens, SUM(cost) as total_cost FROM tasks")
    row = cursor.fetchone()
    total_tokens = row['total_tokens'] or 0
    total_cost = row['total_cost'] or 0.0
    
    conn.close()
    return {
        "status_counts": status_counts, 
        "assignee_counts": assignee_counts,
        "total_tokens": total_tokens,
        "total_cost": total_cost
    }

@app.post("/api/tasks/{task_id}/triage")
def trigger_triage(task_id: str, username: str = Depends(authenticate)):
    from triage_agent import process_triage_task
    success = process_triage_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or not in triage")
    return {"status": "success", "message": f"Task {task_id} triaged"}

@app.get("/", response_class=HTMLResponse)
def index(username: str = Depends(authenticate)):
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
        .hidden { display: none; }
        .tree-node { position: relative; margin-left: 2rem; border-left: 2px solid #3f3f46; padding-left: 1.5rem; }
        .tree-card { background-color: #18181b; border: 1px solid #27272a; border-radius: 6px; padding: 8px; margin-bottom: 8px; max-width: 400px; }
    </style>
</head>
<body class="p-8">
    <header class="flex justify-between items-center mb-8">
        <div class="flex items-center gap-6">
            <div>
                <h1 class="text-2xl font-bold tracking-tight text-blue-500">⚕️ Jarvis Live Dashboard</h1>
                <p class="text-zinc-400 text-xs">Real-time Hermes Swarm & Kanban</p>
            </div>
            <div class="flex gap-2">
                <input type="text" id="quick-add-input" placeholder="Quick add task..." class="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 text-sm focus:outline-none focus:border-blue-500 w-96 shadow-inner">
                <button onclick="quickAddTask()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-xs font-bold uppercase transition-all shadow-lg active:scale-95">Add</button>
            </div>
        </div>
        <div class="flex flex-col items-end">
            <div id="last-update" class="text-xs text-zinc-500 font-mono uppercase">Updating...</div>
            <div class="text-[10px] text-zinc-600 font-mono mt-1 tracking-widest">SECURE ACCESS: ON</div>
        </div>
    </header>

    <nav class="flex gap-6 mb-8 border-b border-zinc-800 pb-4">
        <button onclick="showView('kanban')" class="text-sm font-medium hover:text-blue-500 transition-colors" id="btn-kanban">Kanban Board</button>
        <button onclick="showView('tree')" class="text-sm font-medium hover:text-blue-500 transition-colors text-zinc-500" id="btn-tree">Swarm Tree View</button>
        <button onclick="showView('analytics')" class="text-sm font-medium hover:text-blue-500 transition-colors text-zinc-500" id="btn-analytics">Analytics & CMS</button>
    </nav>

    <!-- Kanban View -->
    <div id="view-kanban">
        <div class="flex gap-4 mb-6">
            <input type="text" id="search-input" placeholder="Search tasks..." class="bg-zinc-800 border border-zinc-700 rounded px-3 py-1 text-sm focus:outline-none focus:border-blue-500 w-64">
            <select id="assignee-filter" class="bg-zinc-800 border border-zinc-700 rounded px-3 py-1 text-sm focus:outline-none focus:border-blue-500">
                <option value="all">All Assignees</option>
                <option value="programmer">Programmer</option>
                <option value="researcher">Researcher</option>
                <option value="designer">Designer</option>
            </select>
        </div>

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
    </div>

    <!-- Tree View -->
    <div id="view-tree" class="hidden">
        <div id="tree-container" class="space-y-8">
            <!-- Tree will be rendered here -->
        </div>
    </div>

    <!-- Analytics View -->
    <div id="view-analytics" class="hidden">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="space-y-8">
                <div class="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                    <h2 class="text-lg font-bold mb-4">Swarm Statistics</h2>
                    <div id="stats-container" class="space-y-4">
                        <!-- Stats will be rendered here -->
                    </div>
                </div>
                <div class="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                    <h2 class="text-lg font-bold mb-4">⚕️ Executive Reports</h2>
                    <div id="reports-container" class="space-y-2">
                        <!-- Reports will be rendered here -->
                    </div>
                    <p class="text-[10px] text-zinc-500 mt-4 italic">Reports autonomously generated by the Swarm.</p>
                </div>
            </div>
            <div class="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <h2 class="text-lg font-bold mb-4">CMS Medicare Analysis</h2>
                <img src="/outputs/markup_distribution.png" alt="Markup Distribution" class="rounded border border-zinc-800">
                <p class="text-xs text-zinc-500 mt-2 italic">Source: outputs/markup_distribution.png</p>
            </div>
        </div>
    </div>

    <script>
        let currentTasks = [];
        let currentLinks = [];
        let currentView = 'kanban';

        function showView(view) {
            currentView = view;
            document.getElementById('view-kanban').classList.toggle('hidden', view !== 'kanban');
            document.getElementById('view-tree').classList.toggle('hidden', view !== 'tree');
            document.getElementById('view-analytics').classList.toggle('hidden', view !== 'analytics');
            
            document.getElementById('btn-kanban').classList.toggle('text-blue-500', view === 'kanban');
            document.getElementById('btn-kanban').classList.toggle('text-zinc-500', view !== 'kanban');
            document.getElementById('btn-tree').classList.toggle('text-blue-500', view === 'tree');
            document.getElementById('btn-tree').classList.toggle('text-zinc-500', view !== 'tree');
            document.getElementById('btn-analytics').classList.toggle('text-blue-500', view === 'analytics');
            document.getElementById('btn-analytics').classList.toggle('text-zinc-500', view !== 'analytics');

            if (view === 'analytics') { fetchStats(); fetchReports(); }
            if (view === 'tree') renderTree();
        }

        async function fetchReports() {
            try {
                const res = await fetch('/api/reports');
                const data = await res.json();
                renderReports(data.reports);
            } catch (e) { console.error('Reports fetch failed', e); }
        }

        function renderReports(reports) {
            const container = document.getElementById('reports-container');
            if (reports.length === 0) {
                container.innerHTML = '<div class="text-xs text-zinc-600">No reports generated yet.</div>';
                return;
            }
            let html = '';
            reports.forEach(report => {
                html += `
                    <div class="flex justify-between items-center p-2 bg-zinc-800 rounded hover:bg-zinc-700 transition-colors cursor-pointer group">
                        <span class="text-sm font-medium text-zinc-300">📄 ${report}</span>
                        <span class="text-[10px] text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity font-bold uppercase">View</span>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        async function quickAddTask() {
            const input = document.getElementById('quick-add-input');
            const title = input.value.trim();
            if (!title) return;

            try {
                const res = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: title, body: "Quick-added from dashboard", assignee: "programmer" })
                });
                if (res.ok) {
                    input.value = '';
                    fetchTasks();
                    showNotification('Goal captured to Triage');
                }
            } catch (e) { console.error('Add failed', e); }
        }

        document.getElementById('quick-add-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') quickAddTask();
        });

        async function triageTask(taskId) {
            try {
                const res = await fetch(`/api/tasks/${taskId}/triage`, { method: 'POST' });
                if (res.ok) {
                    fetchTasks();
                    showNotification('Task triaged successfully');
                }
            } catch (e) {
                console.error('Triage failed', e);
            }
        }

        function showNotification(msg) {
            const toast = document.createElement('div');
            toast.className = 'fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow-lg z-50 text-sm font-medium transition-opacity';
            toast.innerText = msg;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 500);
            }, 3000);
        }

        async function fetchTasks() {
            try {
                const res = await fetch('/api/tasks');
                if (res.status === 401) { window.location.reload(); return; }
                const data = await res.json();
                currentTasks = data.tasks;
                currentLinks = data.links;
                if (currentView === 'kanban') applyFiltersAndRender();
                if (currentView === 'tree') renderTree();
                document.getElementById('last-update').innerText = 'Sync OK: ' + new Date().toLocaleTimeString();
            } catch (e) {
                console.error('Fetch failed', e);
            }
        }

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                renderStats(stats);
            } catch (e) {
                console.error('Stats fetch failed', e);
            }
        }

        function renderStats(stats) {
            const container = document.getElementById('stats-container');
            let html = '<div class="grid grid-cols-1 gap-6">';
            
            html += '<div class="grid grid-cols-2 gap-4">';
            html += '<div><h3 class="text-sm font-semibold text-zinc-500 uppercase mb-2">By Status</h3>';
            for (const [status, count] of Object.entries(stats.status_counts)) {
                html += `<div class="flex justify-between text-sm py-1 border-b border-zinc-800"><span>${status}</span><span class="font-mono text-blue-500">${count}</span></div>`;
            }
            html += '</div>';

            html += '<div><h3 class="text-sm font-semibold text-zinc-500 uppercase mb-2">By Assignee</h3>';
            for (const [assignee, count] of Object.entries(stats.assignee_counts)) {
                html += `<div class="flex justify-between text-sm py-1 border-b border-zinc-800"><span>${assignee}</span><span class="font-mono text-blue-500">${count}</span></div>`;
            }
            html += '</div></div>';

            html += '<div class="bg-zinc-800/50 p-4 rounded border border-zinc-700">';
            html += '<h3 class="text-sm font-semibold text-zinc-400 uppercase mb-3">Operational Costs</h3>';
            html += `<div class="flex justify-between items-center mb-2"><span>Total Tokens Consumed</span><span class="font-mono text-lg text-blue-400">${stats.total_tokens.toLocaleString()}</span></div>`;
            html += `<div class="flex justify-between items-center"><span>Total Swarm Cost (USD)</span><span class="font-mono text-lg text-green-500">$${stats.total_cost.toFixed(4)}</span></div>`;
            html += '</div>';
            
            html += '</div>';
            
            container.innerHTML = html;
        }

        function renderTree() {
            const container = document.getElementById('tree-container');
            container.innerHTML = '';
            
            // Find root tasks (no parents)
            const childrenIds = new Set(currentLinks.map(l => l.child_id));
            const roots = currentTasks.filter(t => !childrenIds.has(t.id));

            roots.forEach(root => {
                const rootEl = document.createElement('div');
                rootEl.innerHTML = buildTreeNode(root);
                container.appendChild(rootEl);
            });
        }

        function buildTreeNode(task) {
            const children = currentLinks.filter(l => l.parent_id === task.id).map(l => currentTasks.find(t => t.id === l.child_id)).filter(t => t);
            
            let html = `
                <div class="mb-4">
                    <div class="tree-card border-l-4 border-l-blue-500 shadow-lg">
                        <div class="flex justify-between mb-1">
                            <span class="text-[10px] text-zinc-500 font-mono">#${task.id}</span>
                            <span class="badge badge-${task.assignee}">${task.assignee}</span>
                        </div>
                        <div class="text-sm font-bold text-zinc-200">${task.title}</div>
                        <div class="text-[10px] text-zinc-500 mt-1 uppercase font-bold tracking-tighter">${task.status}</div>
                    </div>
            `;

            if (children.length > 0) {
                html += '<div class="tree-node">';
                children.forEach(child => {
                    html += buildTreeNode(child);
                });
                html += '</div>';
            }

            html += '</div>';
            return html;
        }

        function applyFiltersAndRender() {
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            const assigneeFilter = document.getElementById('assignee-filter').value;

            const filteredTasks = currentTasks.filter(task => {
                const matchesSearch = task.title.toLowerCase().includes(searchTerm) || (task.body && task.body.toLowerCase().includes(searchTerm));
                const matchesAssignee = assigneeFilter === 'all' || task.assignee === assigneeFilter;
                return matchesSearch && matchesAssignee;
            });

            renderTasks(filteredTasks);
            setTimeout(() => renderLinks(currentLinks), 100);
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
                
                let actions = '';
                if (task.status === 'triage') {
                    actions = `<button onclick="event.stopPropagation(); triageTask('${task.id}')" class="mt-3 text-[10px] bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded transition-colors uppercase font-bold">Manual Triage</button>`;
                }

                card.innerHTML = `
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-xs text-zinc-500 font-mono">#${task.id}</span>
                        <span class="badge badge-${task.assignee}">${task.assignee}</span>
                    </div>
                    <h3 class="text-sm font-medium mb-1">${task.title}</h3>
                    <p class="text-xs text-zinc-400 line-clamp-2">${task.body || ''}</p>
                    ${actions}
                `;
                col.appendChild(card);
            });
        }

        function renderLinks(links) {
            const svg = document.getElementById('swarm-lines');
            const board = document.querySelector('.grid');
            if (!board || currentView !== 'kanban') return;
            const boardRect = board.getBoundingClientRect();
            svg.setAttribute('width', boardRect.width);
            svg.setAttribute('height', boardRect.height);
            svg.innerHTML = '';
            
            links.forEach(link => {
                const parent = document.getElementById(`task-${link.parent_id}`);
                const child = document.getElementById(`task-${link.child_id}`);
                
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

        document.getElementById('search-input').addEventListener('input', applyFiltersAndRender);
        document.getElementById('assignee-filter').addEventListener('change', applyFiltersAndRender);

        window.addEventListener('resize', applyFiltersAndRender);
        setInterval(fetchTasks, 5000);
        fetchTasks();
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)
