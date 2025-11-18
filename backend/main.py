from typing import Union, List, Dict
import json
import os
import logging
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import re
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from e2b import Sandbox
from services.sandbox import SandboxManager
from services.parser import extract_artifact
from prompts import get_messages_for_llm

# Configure logging - ERRORS ONLY
logging.basicConfig(
    level=logging.ERROR,
    format='[ERROR] %(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ExecuteRequest(BaseModel):
    session_id: str
    actions: List[Dict]

class TerminalRequest(BaseModel):
    session_id: str
    command: str

class PromptRequest(BaseModel):
    prompt: str
    conversation_history: list = []

app = FastAPI()
sandbox_manager = SandboxManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class PromptRequest(BaseModel):
    prompt: str
    conversation_history: list = []
    model_provider: str = "gpt"  # "gpt" or "claude"

@app.post("/api/generate")
async def generate_code(request: PromptRequest):
    """Main endpoint for code generation - returns full response with artifact"""
    try:
        messages = get_messages_for_llm(request.prompt, request.conversation_history)
        
        # Choose provider based on request
        if request.model_provider == "claude":
            # Convert OpenAI format to Anthropic format
            system_message = next((m["content"] for m in messages if m["role"] == "system"), "")
            anthropic_messages = [m for m in messages if m["role"] != "system"]
            
            response = await anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16384,
                temperature=1,
                system=system_message,
                messages=anthropic_messages
            )
            content = response.content[0].text
        else:
            # GPT (default)
            response = await openai_client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages,
                temperature=1,
                max_tokens=16384,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            content = response.choices[0].message.content
        
        # Extract artifact if present
        artifact = extract_artifact(content) if content else None
        
        return {
            'content': content,
            'artifact': artifact if artifact else None
        }
    except Exception as e:
        logger.error(f"Generate endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/execute")
async def execute_in_sandbox(request: ExecuteRequest):
    """Execute actions in E2B sandbox with streaming progress"""
    async def generate_progress():
        try:
            sandbox = sandbox_manager.sandboxes.get(request.session_id)
            if not sandbox:
                sandbox = await sandbox_manager.create_sandbox(request.session_id)
            
            for i, action in enumerate(request.actions):
                # Send progress update for this action
                yield f"data: {json.dumps({'type': 'progress', 'action_index': i, 'action': action, 'status': 'executing'})}\n\n"
                
                if action['type'] == 'file':
                    # Write file
                    sandbox.files.write(action['filePath'], action['content'])
                    result = {'type': 'file', 'path': action['filePath'], 'status': 'created'}
                    
                elif action['type'] == 'shell':
                    is_background = 'npm run dev' in action['command'] or 'npm start' in action['command']
                    
                    # Set working directory if not already set
                    working_dir = '/home/user'
                    
                    if is_background:
                        # Start in background - use the command as-is since package.json has hostname
                        try:
                            bg_command = action['command']
                            
                            # Only add hostname if it's NOT already in the command and NOT already in package.json dev script
                            # Since we now generate package.json with --hostname, don't add it again
                            
                            process = sandbox.commands.run(bg_command, background=True, cwd=working_dir, timeout=0)
                            
                            # Wait for Next.js to start (takes about 2-3 seconds)
                            await asyncio.sleep(3)
                            
                            result = {
                                'type': 'shell',
                                'command': action['command'],
                                'status': 'started',
                                'background': True
                            }
                        except Exception as bg_error:
                            # Background command failed to start
                            error_str = str(bg_error)
                            logger.error(f"Background command failed: {error_str}")
                            
                            # Check if it's a network binding error
                            if 'getaddrinfo' in error_str or 'EADDRNOTAVAIL' in error_str:
                                result = {
                                    'type': 'shell',
                                    'command': action['command'],
                                    'status': 'failed',
                                    'error': 'Network binding error - ensure Next.js is configured with --hostname 0.0.0.0',
                                }
                            else:
                                result = {
                                    'type': 'shell',
                                    'command': action['command'],
                                    'status': 'failed',
                                    'error': error_str,
                                }
                            
                            # Send completion and continue (don't wait for port)
                            yield f"data: {json.dumps({'type': 'progress', 'action_index': i, 'status': 'completed', 'result': result})}\n\n"
                            continue
                        
                        # Wait for port 3000 to be ready
                        yield f"data: {json.dumps({'type': 'progress', 'action_index': i, 'status': 'waiting_for_server'})}\n\n"
                        
                        max_wait = 60
                        port_ready = False
                        last_error = None
                        
                        for wait_i in range(max_wait):
                            await asyncio.sleep(2)
                            try:
                                # Check if port is listening
                                check = sandbox.commands.run(
                                    f"netstat -tuln 2>/dev/null | grep ':3000' || ss -tuln 2>/dev/null | grep ':3000' || echo 'not listening'",
                                    timeout=5
                                )
                                
                                if '3000' in check.stdout and 'not listening' not in check.stdout:
                                    # Port is open, try to curl it
                                    curl_check = sandbox.commands.run(
                                        f"curl -s http://localhost:3000 > /dev/null 2>&1 && echo 'ready' || echo 'not ready'",
                                        timeout=5
                                    )
                                    if 'ready' in curl_check.stdout:
                                        port_ready = True
                                        result['ready'] = True
                                        result['wait_time'] = wait_i + 1
                                        break
                                else:
                                    # Check if process is still running
                                    proc_check = sandbox.commands.run(
                                        f"ps aux | grep -v grep | grep 'next dev' || echo 'not running'",
                                        timeout=5
                                    )
                                    if 'not running' in proc_check.stdout:
                                        last_error = "Next.js dev server process not running"
                                        break
                            except Exception as e:
                                last_error = str(e)
                                pass
                        
                        if not port_ready:
                            result['ready'] = False
                            result['status'] = 'timeout'
                            if last_error:
                                result['error'] = last_error
                            
                            # Try to get logs from the dev server to debug
                            try:
                                log_check = sandbox.commands.run(
                                    "ps aux | grep -v grep | grep node | head -5",
                                    timeout=5
                                )
                                result['debug_info'] = log_check.stdout if log_check.stdout else 'No process info'
                            except:
                                pass
                    else:
                        # Execute synchronously (npm install, etc)
                        try:
                            # For npm install, optimize for speed
                            actual_command = action['command']
                            if 'npm install' in actual_command:
                                # Add flags for faster, more reliable installation
                                if '--legacy-peer-deps' not in actual_command:
                                    actual_command = actual_command.replace('npm install', 
                                        'npm install --legacy-peer-deps --no-audit --no-fund --prefer-offline --loglevel=error')
                            
                            # Increase timeout for npm install (600s = 10min), shorter for other commands
                            cmd_timeout = 600 if 'npm install' in actual_command else 120
                            process = sandbox.commands.run(actual_command, timeout=cmd_timeout, cwd=working_dir)
                            result = {
                                'type': 'shell',
                                'command': action['command'],
                                'status': 'completed',
                                'exit_code': process.exit_code,
                                'stdout': process.stdout[-1000:] if len(process.stdout) > 1000 else process.stdout,
                            }
                        except Exception as cmd_error:
                            # E2B throws exception for non-zero exit codes
                            # npm warnings/deprecations cause exit code -1 but aren't real errors
                            error_msg = str(cmd_error)
                            
                            # For npm install, ALWAYS check if node_modules exists first
                            if 'npm install' in action['command']:
                                try:
                                    check_modules = sandbox.commands.run('test -d node_modules && ls node_modules | wc -l', cwd=working_dir, timeout=10)
                                    module_count = int(check_modules.stdout.strip())
                                    
                                    if module_count > 0:
                                        # Dependencies were installed successfully despite error
                                        result = {
                                            'type': 'shell',
                                            'command': action['command'],
                                            'status': 'completed',
                                            'warning': 'npm install completed with warnings (dependencies installed)',
                                        }
                                        # Send completion and continue
                                        yield f"data: {json.dumps({'type': 'progress', 'action_index': i, 'status': 'completed', 'result': result})}\n\n"
                                        continue
                                except:
                                    pass
                            
                            # Check if it's just npm warnings or successful completion with warnings
                            if any(indicator in error_msg.lower() for indicator in ['exit code -1', 'npm warn', 'deprecated', 'exited with code -1']):
                                # Verify node_modules was created successfully
                                try:
                                    check_modules = sandbox.commands.run('ls -la node_modules 2>/dev/null | wc -l', cwd=working_dir)
                                    modules_exist = int(check_modules.stdout.strip()) > 2  # More than just . and ..
                                    
                                    if modules_exist:
                                        result = {
                                            'type': 'shell',
                                            'command': action['command'],
                                            'status': 'completed',
                                            'warning': 'Completed with npm warnings (safe to ignore)',
                                        }
                                    else:
                                        raise cmd_error
                                except:
                                    # If we can't verify, but it's exit -1, assume success
                                    result = {
                                        'type': 'shell',
                                        'command': action['command'],
                                        'status': 'completed',
                                        'warning': 'Completed with warnings',
                                    }
                            elif 'timeout' in error_msg.lower() or 'deadline exceeded' in error_msg.lower():
                                # Timeout - check if dependencies were installed anyway
                                try:
                                    check_modules = sandbox.commands.run('ls -la node_modules 2>/dev/null | wc -l', cwd=working_dir)
                                    modules_exist = int(check_modules.stdout.strip()) > 2
                                    
                                    if modules_exist:
                                        result = {
                                            'type': 'shell',
                                            'command': action['command'],
                                            'status': 'completed',
                                            'warning': 'Installation timed out but dependencies appear to be installed',
                                        }
                                    else:
                                        result = {
                                            'type': 'shell',
                                            'command': action['command'],
                                            'status': 'failed',
                                            'error': 'Installation timeout - dependencies not fully installed',
                                        }
                                except:
                                    result = {
                                        'type': 'shell',
                                        'command': action['command'],
                                        'status': 'failed',
                                        'error': 'Installation timeout',
                                    }
                            else:
                                # Real error - command failed
                                result = {
                                    'type': 'shell',
                                    'command': action['command'],
                                    'status': 'failed',
                                    'error': error_msg,
                                }
                
                # Send completion for this action
                yield f"data: {json.dumps({'type': 'progress', 'action_index': i, 'status': 'completed', 'result': result})}\n\n"
            
            # Get preview URL
            preview_url = await sandbox_manager.get_preview_url(request.session_id)
            
            # Send final completion
            yield f"data: {json.dumps({'type': 'complete', 'preview_url': preview_url})}\n\n"
            
        except Exception as e:
            logger.error(f"Execute streaming error: {str(e)}")
            logger.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate_progress(), media_type="text/event-stream")


@app.post("/api/execute-simple")
async def execute_in_sandbox_simple(request: ExecuteRequest):
    """Execute actions in E2B sandbox (non-streaming, for compatibility)"""
    try:
        results = await sandbox_manager.execute_actions(
            request.session_id,
            request.actions
        )
        preview_url = await sandbox_manager.get_preview_url(request.session_id)
        
        return {
            'results': results,
            'preview_url': preview_url
        }
    except Exception as e:
        logger.error(f"Execute endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sandbox/{session_id}/logs")
async def get_sandbox_logs(session_id: str, file_path: str = None):
    """Get logs from sandbox"""
    try:
        logs = await sandbox_manager.get_logs(session_id, file_path)
        return logs
    except Exception as e:
        logger.error(f"Logs endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sandbox/{session_id}/port/{port}")
async def check_sandbox_port(session_id: str, port: int):
    """Check if port is listening in sandbox"""
    try:
        status = await sandbox_manager.check_port(session_id, port)
        return status
    except Exception as e:
        logger.error(f"Port check endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sandbox/{session_id}/processes")
async def get_sandbox_processes(session_id: str):
    """Get running processes in sandbox"""
    try:
        processes = await sandbox_manager.get_process_list(session_id)
        return processes
    except Exception as e:
        logger.error(f"Processes endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/terminal")
async def execute_terminal_command(request: TerminalRequest):
    """Execute a terminal command in the sandbox"""
    try:
        sandbox = sandbox_manager.get_sandbox(request.session_id)
        if not sandbox:
            raise HTTPException(status_code=404, detail="Sandbox not found")
        
        command = request.command.strip()
        
        # Get current working directory
        cwd = sandbox_manager.get_working_dir(request.session_id)
        
        # Handle cd command specially
        if command.startswith('cd '):
            target_dir = command[3:].strip()
            
            # Handle relative and absolute paths
            if target_dir.startswith('/'):
                new_dir = target_dir
            elif target_dir == '..':
                # Go up one directory
                new_dir = '/'.join(cwd.rstrip('/').split('/')[:-1]) or '/'
            elif target_dir == '~':
                new_dir = '/home/user'
            else:
                # Relative path
                new_dir = f"{cwd.rstrip('/')}/{target_dir}"
            
            # Verify directory exists
            check_result = sandbox.commands.run(f"test -d {new_dir} && echo 'exists'", cwd=cwd)
            
            if 'exists' in check_result.stdout:
                sandbox_manager.set_working_dir(request.session_id, new_dir)
                return {
                    'stdout': '',
                    'stderr': '',
                    'exit_code': 0,
                    'cwd': new_dir
                }
            else:
                return {
                    'stdout': '',
                    'stderr': f"cd: {target_dir}: No such file or directory",
                    'exit_code': 1,
                    'cwd': cwd
                }
        
        # Check if it's a background command
        is_background = 'npm run dev' in command or 'npm start' in command
        
        if is_background:
            # Start in background
            process = sandbox.commands.run(command, cwd=cwd, background=True)
            return {
                'stdout': f"Started background process (PID: {process.pid})",
                'stderr': '',
                'exit_code': 0,
                'cwd': cwd
            }
        else:
            # Execute command with current working directory
            result = sandbox.commands.run(command, cwd=cwd)
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.exit_code,
                'cwd': cwd
            }
    except Exception as e:
        logger.error(f"Terminal endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

