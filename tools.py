import os
from pathlib import Path

def list_directory(dir_path="."):
    """Lists files and directories in the given path."""
    try:
        items = os.listdir(dir_path)
        return {"status": "success", "items": items}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def read_file(file_path):
    """Reads the content of a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": "File not found"}
        content = path.read_text(encoding='utf-8')
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def write_file(file_path, content):
    """Writes or overwrites a file with the given content."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return {"status": "success", "message": f"File {file_path} written successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def web_search(query):
    """Searches the web for the given query using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_command(command):
    """Executes a shell command and returns the output."""
    import subprocess
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
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
    
    # Create a temporary file for the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = subprocess.run(['python', temp_path], capture_output=True, text=True, timeout=30)
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
            "description": "Writes or updates a local file with new content.",
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
            "description": "Executes a shell command (e.g., 'python script.py').",
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
            "description": "Executes raw Python code and returns the output. Use this to test code before writing it to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The Python code to execute."}
                },
                "required": ["code"]
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
    else:
        return {"status": "error", "message": f"Unknown tool: {name}"}
