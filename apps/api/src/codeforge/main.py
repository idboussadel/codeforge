from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from codeforge import db
from codeforge.agent.messages import rows_to_ui_messages
from codeforge.agent_runtime import abort_run, is_agent_running, needs_run, start_message, start_run
from codeforge.config import REPO_ROOT, settings
from codeforge.db import SessionLocal, init_db
from codeforge.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    GetSessionResponse,
    ListFilesResponse,
    ListSessionsResponse,
    PreviewResponse,
    SendMessageRequest,
    SessionMessage,
    SessionSummary,
    TerminalRequest,
)
from codeforge.sandbox import E2BSandbox, get_terminal_cwd, terminal_prompt

os.environ["E2B_API_KEY"] = settings.e2b_api_key

_preview_locks: Dict[str, asyncio.Lock] = {}


def _preview_lock(session_id: str) -> asyncio.Lock:
    if session_id not in _preview_locks:
        _preview_locks[session_id] = asyncio.Lock()
    return _preview_locks[session_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    (REPO_ROOT / "data").mkdir(exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="CodeForge API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/api/sessions", response_model=ListSessionsResponse)
async def list_sessions():
    async with SessionLocal() as session:
        rows = await db.list_sessions(session)
        return ListSessionsResponse(
            sessions=[
                SessionSummary(
                    id=r.id,
                    title=r.title,
                    created_at=r.created_at.isoformat(),
                )
                for r in rows
            ]
        )


@app.post("/api/sessions", response_model=CreateSessionResponse)
async def create_session(body: CreateSessionRequest):
    async with SessionLocal() as session:
        row = await db.create_session(session, body.title)
        if body.message:
            await db.add_message(session, row.id, "user", body.message.strip())
        return CreateSessionResponse(id=row.id, title=row.title, sandbox_id=row.sandbox_id)


@app.get("/api/sessions/{session_id}", response_model=GetSessionResponse)
async def get_session(session_id: str):
    async with SessionLocal() as session:
        row = await db.get_session(session, session_id)
        if not row:
            raise HTTPException(404, "Session not found")

        msgs = await db.list_messages(session, session_id)
        ui_messages = rows_to_ui_messages(msgs)

        return GetSessionResponse(
            id=row.id,
            title=row.title,
            sandbox_id=row.sandbox_id,
            sandbox_state=row.sandbox_state,  # type: ignore[arg-type]
            messages=[
                SessionMessage(
                    id=m["id"],
                    role=m["role"],  # type: ignore[arg-type]
                    content=m.get("content", ""),
                    blocks=m.get("blocks"),
                    created_at=m["created_at"],
                )
                for m in ui_messages
            ],
            needs_run=needs_run(msgs),
            agent_running=is_agent_running(session_id),
        )


@app.post("/api/sessions/{session_id}/run")
async def run_session(session_id: str):
    return await start_run(session_id)


@app.post("/api/sessions/{session_id}/messages")
async def send_message(session_id: str, body: SendMessageRequest):
    return await start_message(session_id, body.content)


@app.post("/api/sessions/{session_id}/abort")
async def abort_session(session_id: str):
    abort_run(session_id)
    return {"ok": True}


@app.get("/api/sessions/{session_id}/files", response_model=ListFilesResponse)
async def list_session_files(session_id: str):
    async with SessionLocal() as session:
        row = await db.get_session(session, session_id)
        if not row or not row.sandbox_id:
            return ListFilesResponse(paths=[])

    try:
        sbx, _ = await E2BSandbox.connect_or_create(row.sandbox_id, settings.e2b_template)
        return ListFilesResponse(paths=await sbx.list_project_files())
    except Exception:
        return ListFilesResponse(paths=[])


@app.get("/api/sessions/{session_id}/files/{file_path:path}", response_class=PlainTextResponse)
async def read_file(session_id: str, file_path: str):
    async with SessionLocal() as session:
        row = await db.get_session(session, session_id)
        if not row or not row.sandbox_id:
            raise HTTPException(404, "No sandbox")

    try:
        sbx, _ = await E2BSandbox.connect_or_create(row.sandbox_id, settings.e2b_template)
        return await sbx.read_file_raw(file_path)
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.get("/api/sessions/{session_id}/preview", response_model=PreviewResponse)
async def ensure_preview(session_id: str):
    """Return live preview URL; start dev server if port 3000 is down."""
    async with SessionLocal() as session:
        row = await db.get_session(session, session_id)
        if not row or not row.sandbox_id:
            return PreviewResponse(status="no_sandbox")

    async with _preview_lock(session_id):
        try:
            sbx, _ = await E2BSandbox.connect_or_create(row.sandbox_id, settings.e2b_template)
            url = await sbx.preview_url_live()
            if url:
                return PreviewResponse(preview_url=url, status="ready")

            result = await sbx.start_dev_server()
            url = result.preview_url or await sbx.preview_url_live()
            if url:
                return PreviewResponse(preview_url=url, status="started")
            return PreviewResponse(status="error", output=result.output)
        except Exception as e:
            return PreviewResponse(status="error", output=str(e))


@app.post("/api/sessions/{session_id}/terminal")
async def terminal(session_id: str, body: TerminalRequest):
    async with SessionLocal() as session:
        row = await db.get_session(session, session_id)
        if not row or not row.sandbox_id:
            raise HTTPException(404, "No sandbox")

    sbx, _ = await E2BSandbox.connect_or_create(row.sandbox_id, settings.e2b_template)
    result = await sbx.run_terminal(session_id, body.command)
    cwd = get_terminal_cwd(session_id)
    return {
        "output": result.output,
        "isError": result.is_error,
        "cwd": terminal_prompt(cwd),
    }
