from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str = "New session"
    message: Optional[str] = Field(default=None, min_length=1)


class CreateSessionResponse(BaseModel):
    id: str
    title: str
    sandbox_id: Optional[str] = None


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: str


class ListSessionsResponse(BaseModel):
    sessions: List[SessionSummary] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class TerminalRequest(BaseModel):
    command: str = Field(min_length=1)


class SessionMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str = ""
    blocks: Optional[List[dict[str, Any]]] = None
    created_at: str


class GetSessionResponse(BaseModel):
    id: str
    title: str
    sandbox_id: Optional[str]
    sandbox_state: Literal["running", "paused", "dead"]
    messages: List[SessionMessage]
    preview_url: Optional[str] = None
    needs_run: bool = False
    agent_running: bool = False


class ToolResult(BaseModel):
    output: str
    is_error: bool = False
    changed_paths: List[str] = Field(default_factory=list)
    preview_url: Optional[str] = None


class ListFilesResponse(BaseModel):
    paths: List[str] = Field(default_factory=list)


class PreviewResponse(BaseModel):
    preview_url: Optional[str] = None
    status: Literal["ready", "started", "no_sandbox", "error"]
    output: Optional[str] = None
