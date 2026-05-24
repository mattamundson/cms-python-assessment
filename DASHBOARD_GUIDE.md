# Jarvis Live Dashboard - User Guide

## Overview
The Jarvis Live Dashboard is a real-time Kanban board for managing your Hermes Agent's upgrades and tasks. It synchronizes with your `backlog.jsonl` and provides a visual interface for tracking progress.

## Access
- **Local:** [http://localhost:9000](http://localhost:9000)
- **Public (via ngrok):** [https://perioecic-piper-postsigmoid.ngrok-free.dev](https://perioecic-piper-postsigmoid.ngrok-free.dev)

## Authentication
- **User:** `amo`
- **Password:** `jarvis2026`
*(Note: These can be changed via environment variables `DASHBOARD_USER` and `DASHBOARD_PASS`.)*

## Key Features
1. **Kanban View:** Tasks are categorized into Triage, Todo, In Progress, and Done.
2. **Assignee Badges:** See which profile (Programmer, Researcher, Designer) is assigned to each task.
3. **Real-time Sync:** The dashboard auto-refreshes every 5 seconds.
4. **Swarm Connections:** Visualizes relationships between parent and child tasks.

## Maintenance
To sync the latest tasks from the backlog, run:
```bash
python sync_kanban.py
```

## Troubleshooting
If the dashboard is empty:
1. Ensure `kanban.db` exists in `~/.hermes/`.
2. Run the `sync_kanban.py` script.
3. Check the dashboard logs for database connection errors.
