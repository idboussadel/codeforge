from typing import List, Dict
import os
from dotenv import load_dotenv
from e2b import Sandbox

# Load environment variables
load_dotenv()

# Set E2B API key globally
os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY", "")

class SandboxManager:
    def __init__(self):
        self.sandboxes = {}
        self.templates = {}  # Track templates per session
        self.working_dirs = {}  # Track working directory per session
    
    def get_sandbox(self, session_id: str):
        """Get existing sandbox by session ID"""
        return self.sandboxes.get(session_id)
    
    def get_working_dir(self, session_id: str) -> str:
        """Get current working directory for session"""
        return self.working_dirs.get(session_id, "/home/user")
    
    def set_working_dir(self, session_id: str, path: str):
        """Set current working directory for session"""
        self.working_dirs[session_id] = path
    
    async def create_sandbox(self, session_id: str):
        """Create new E2B sandbox with code-interpreter template"""
        sandbox = Sandbox.create(
            template="code-interpreter-v1",  # Use code-interpreter-v1 template for Node.js support
            timeout=3600  # 1 hour timeout
        )
        self.sandboxes[session_id] = sandbox
        self.working_dirs[session_id] = "/home/user"
        return sandbox
    
    async def execute_actions(self, session_id: str, actions: List[Dict]):
        """Execute artifact actions in sandbox"""
        sandbox = self.sandboxes.get(session_id)
        if not sandbox:
            sandbox = await self.create_sandbox(session_id)
        
        results = []
        
        for action in actions:
            if action['type'] == 'file':
                # Write file to sandbox using files API
                sandbox.files.write(
                    action['filePath'],
                    action['content']
                )
                results.append({'type': 'file', 'path': action['filePath'], 'status': 'created'})
            
            elif action['type'] == 'shell':
                # Check if it's a background command (like npm run dev)
                is_background = 'npm run dev' in action['command'] or 'npm start' in action['command']
                
                if is_background:
                    # Start process in background
                    process = sandbox.commands.run(
                        action['command'],
                        background=True
                    )
                    results.append({
                        'type': 'shell', 
                        'command': action['command'], 
                        'status': 'started',
                        'background': True,
                        'pid': process.pid if hasattr(process, 'pid') else None
                    })
                else:
                    # Execute synchronously
                    try:
                        process = sandbox.commands.run(
                            action['command'],
                            timeout=300  # 5 minute timeout
                        )
                        results.append({
                            'type': 'shell', 
                            'command': action['command'], 
                            'status': 'completed',
                            'stdout': process.stdout,
                            'stderr': process.stderr,
                            'exit_code': process.exit_code
                        })
                    except Exception as cmd_error:
                        # If command fails, capture error but continue
                        results.append({
                            'type': 'shell',
                            'command': action['command'],
                            'status': 'failed',
                            'error': str(cmd_error),
                            'exit_code': 1
                        })
        
        return results
    
    async def get_preview_url(self, session_id: str):
        """Get preview URL for Next.js app"""
        sandbox = self.sandboxes.get(session_id)
        if sandbox:
            # Get the URL for port 3000 (Next.js default)
            return f"https://{sandbox.get_host(3000)}"
        return None
    
    async def get_logs(self, session_id: str, file_path: str = None):
        """Get logs from sandbox - either from a file or command output"""
        sandbox = self.sandboxes.get(session_id)
        if not sandbox:
            return {"error": "Sandbox not found"}
        
        # If file_path is provided, read that file
        if file_path:
            try:
                content = sandbox.files.read(file_path)
                return {"logs": content, "source": file_path}
            except Exception as e:
                return {"error": str(e)}
        
        # Otherwise, try to read common log locations
        log_files = [
            "/home/user/.npm/_logs",  # npm logs directory
            "/home/user/netflix-clone/.next/trace",  # Next.js trace logs
        ]
        
        logs = {}
        for log_path in log_files:
            try:
                # List files in log directory
                result = sandbox.commands.run(f"ls -la {log_path}")
                logs[log_path] = {
                    "listing": result.stdout,
                    "error": result.stderr
                }
            except Exception as e:
                logs[log_path] = {"error": str(e)}
        
        return logs
    
    async def check_port(self, session_id: str, port: int = 3000):
        """Check if a port is listening"""
        sandbox = self.sandboxes.get(session_id)
        if not sandbox:
            return {"error": "Sandbox not found"}
        
        # Check if port is listening
        result = sandbox.commands.run(f"netstat -tuln | grep :{port} || echo 'Port {port} not listening'")
        
        return {
            "port": port,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "is_listening": f":{port}" in result.stdout
        }
    
    async def get_process_list(self, session_id: str):
        """Get list of running processes"""
        sandbox = self.sandboxes.get(session_id)
        if not sandbox:
            return {"error": "Sandbox not found"}
        
        result = sandbox.commands.run("ps aux")
        
        return {
            "processes": result.stdout,
            "error": result.stderr
        }