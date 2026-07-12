from __future__ import annotations

import json
from typing import Any, List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from codeforge.sandbox import E2BSandbox


class WriteFileArgs(BaseModel):
    path: str = Field(description="Path relative to /home/user, e.g. netflix-clone/src/app/page.tsx")
    content: str


class EditFileArgs(BaseModel):
    path: str
    old_str: str = Field(description="Exact text to replace (must be unique)")
    new_str: str


class ReadFileArgs(BaseModel):
    path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class ListFilesArgs(BaseModel):
    path: str = "."


class RunCommandArgs(BaseModel):
    command: str
    timeout_s: int = 120


class DevLogsArgs(BaseModel):
    lines: int = 50


class EmptyArgs(BaseModel):
    pass


def _dump(result) -> str:
    return json.dumps({
        "output": result.output,
        "isError": result.is_error,
        "previewUrl": result.preview_url,
        "changedPaths": result.changed_paths,
    })


def build_tools(sandbox: E2BSandbox) -> List[StructuredTool]:
    async def write_file(path: str, content: str) -> str:
        return _dump(await sandbox.write_file(path, content))

    async def edit_file(path: str, old_str: str, new_str: str) -> str:
        return _dump(await sandbox.edit_file(path, old_str, new_str))

    async def read_file(path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        return _dump(await sandbox.read_file(path, start_line, end_line))

    async def list_files(path: str = ".") -> str:
        return _dump(await sandbox.list_files(path))

    async def run_command(command: str, timeout_s: int = 120) -> str:
        return _dump(await sandbox.run_command(command, timeout_s))

    async def start_dev_server() -> str:
        return _dump(await sandbox.start_dev_server())

    async def get_dev_server_logs(lines: int = 50) -> str:
        return _dump(await sandbox.get_dev_server_logs(lines))

    async def check_project() -> str:
        return _dump(await sandbox.check_project())

    return [
        StructuredTool.from_function(
            coroutine=write_file, name="write_file",
            description="Create or overwrite a NEW file. For existing files use edit_file.",
            args_schema=WriteFileArgs,
        ),
        StructuredTool.from_function(
            coroutine=edit_file, name="edit_file",
            description="Replace exact string in existing file. old_str must match exactly once.",
            args_schema=EditFileArgs,
        ),
        StructuredTool.from_function(
            coroutine=read_file, name="read_file",
            description="Read file contents with optional line range.",
            args_schema=ReadFileArgs,
        ),
        StructuredTool.from_function(
            coroutine=list_files, name="list_files",
            description="List project files (depth-limited, node_modules excluded).",
            args_schema=ListFilesArgs,
        ),
        StructuredTool.from_function(
            coroutine=run_command, name="run_command",
            description="Run shell in /home/user (pass cd into project first). Do NOT use for file writes. shadcn: use `-y` not `--force`.",
            args_schema=RunCommandArgs,
        ),
        StructuredTool.from_function(
            coroutine=start_dev_server, name="start_dev_server",
            description="Start dev server on 0.0.0.0:3000 in the detected project dir. Returns preview URL when port is live (max 90s).",
            args_schema=EmptyArgs,
        ),
        StructuredTool.from_function(
            coroutine=get_dev_server_logs, name="get_dev_server_logs",
            description="Tail dev-server output for runtime/HMR errors.",
            args_schema=DevLogsArgs,
        ),
        StructuredTool.from_function(
            coroutine=check_project, name="check_project",
            description="Run tsc --noEmit and eslint. Use before declaring done.",
            args_schema=EmptyArgs,
        ),
    ]
