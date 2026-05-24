import os
from pathlib import Path

# Enforce Project Root to prevent leakage into System32
PROJECT_ROOT = Path("C:/Users/mattm/Documents/cms-python-assessment")

def resolve_path(target_path):
    """Ensures paths are always relative to the Project Root."""
    path = Path(target_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path

def list_directory(dir_path="."):
    """Lists files and directories in the given path."""
    try:
        abs_path = resolve_path(dir_path)
        items = os.listdir(abs_path)
        return {"status": "success", "items": items, "cwd": str(abs_path)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def read_file(file_path):
    """Reads the content of a file."""
    try:
        abs_path = resolve_path(file_path)
        if not abs_path.exists():
            return {"status": "error", "message": f"File not found at {abs_path}"}
        content = abs_path.read_text(encoding='utf-8')
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def write_file(file_path, content):
    """Writes or overwrites a file with the given content."""
    try:
        abs_path = resolve_path(file_path)
        # Security: Prevent writing outside project root
        if PROJECT_ROOT not in abs_path.parents and abs_path != PROJECT_ROOT:
             return {"status": "error", "message": "Security Violation: Cannot write outside PROJECT_ROOT"}
             
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding='utf-8')
        return {"status": "success", "message": f"File {file_path} written successfully to {abs_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def web_search(query):
    """Searches the web for the given query using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        # Improve query to avoid noise
        refined_query = f"{query} CMS.gov Medicare 2024" if "medicare" in query.lower() else query
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(refined_query, max_results=8)]
            if not results:
                # Fallback to broader search
                results = [r for r in ddgs.text(query, max_results=5)]
            return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_command(command):
    """Executes a shell command and returns the output."""
    import subprocess
    try:
        # Enforce execution in Project Root
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, cwd=str(PROJECT_ROOT))
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_python(code):
    """Executes Python code in a sandbox and returns results or tracebacks."""
    import subprocess
    import tempfile
    import os
    
    # Create a temporary file in Project Root
    temp_dir = PROJECT_ROOT / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=str(temp_dir)) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        # Enforce execution in Project Root
        result = subprocess.run(['python', temp_path], capture_output=True, text=True, timeout=30, cwd=str(PROJECT_ROOT))
        return {
            "status": "success" if result.returncode == 0 else "failure",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def reassign_task(task_id, new_assignee, reason):
    """Reassigns a task to a different specialist (programmer, researcher, designer, reviewer)."""
    import sqlite3
    DB_PATH = os.path.expanduser("~/.hermes/kanban.db")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE tasks SET assignee = ?, body = body || ? WHERE id = ?", 
                     (new_assignee, f"\n\n[REASSIGNED to {new_assignee}] Reason: {reason}", task_id))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Task {task_id} reassigned to {new_assignee}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Define tools for OpenAI format
JARVIS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists files and directories in a specific folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {"type": "string", "description": "The path to list. Defaults to current directory."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "The path to the file to read."}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes or updates a local file with new content. Paths are relative to PROJECT_ROOT.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "The path to the file to write."},
                    "content": {"type": "string", "description": "The full content to write to the file."}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Searches the internet for real-time information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to research."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Executes a shell command. Execution is forced inside PROJECT_ROOT.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to execute."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Executes raw Python code and returns the output. Use this to test code before writing it to a file. Executes in PROJECT_ROOT.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The Python code to execute."}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reassign_task",
            "description": "Hand off this task to another specialist. Use 'reviewer' to request a peer review of your work.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The ID of the task to reassign."},
                    "new_assignee": {"type": "string", "enum": ["programmer", "researcher", "designer", "reviewer"], "description": "The specialist to hand off to."},
                    "reason": {"type": "string", "description": "Why you are reassigning the task."}
                },
                "required": ["task_id", "new_assignee", "reason"]
            }
        }
    }
]

def execute_tool(name, arguments):
    """Executes a tool by name with provided arguments."""
    if name == "list_directory":
        return list_directory(**arguments)
    elif name == "read_file":
        return read_file(**arguments)
    elif name == "write_file":
        return write_file(**arguments)
    elif name == "web_search":
        return web_search(**arguments)
    elif name == "run_command":
        return run_command(**arguments)
    elif name == "run_python":
        return run_python(**arguments)
    elif name == "reassign_task":
        return reassign_task(**arguments)
    else:
        return {"status": "error", "message": f"Unknown tool: {name}"}
