from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from codeforge import db
from codeforge.agent.graph import run_agent
from codeforge.agent.messages import history_to_messages, messages_to_rows
from codeforge.config import settings
from codeforge.db import SessionLocal
from codeforge.sandbox import E2BSandbox

active_tasks: Dict[str, asyncio.Task] = {}
KEEPALIVE_S = 15


def message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content)


def needs_run(messages: list) -> bool:
    return bool(messages) and messages[-1].role == "user"


def is_agent_running(session_id: str) -> bool:
    task = active_tasks.get(session_id)
    return task is not None and not task.done()


def abort_run(session_id: str) -> None:
    task = active_tasks.pop(session_id, None)
    if task and not task.done():
        task.cancel()


async def _sse_response(
    session_id: str,
    user_content: str,
    history: list[dict[str, Any]],
    sandbox_id: Optional[str],
    *,
    save_user_message: bool,
) -> StreamingResponse:
    if is_agent_running(session_id):
        raise HTTPException(409, "Agent already running for this session")

    queue: asyncio.Queue[Optional[dict]] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit(event: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, event)

    async def agent_task() -> None:
        try:
            if save_user_message:
                async with SessionLocal() as s:
                    await db.add_message(s, session_id, "user", user_content)

            emit({"type": "status", "message": "Connecting sandbox..."})

            async with SessionLocal() as db_session:
                async def on_created(sid: str) -> None:
                    await db.update_sandbox_id(db_session, session_id, sid)

                sbx, _ = await E2BSandbox.connect_or_create(
                    sandbox_id, settings.e2b_template, on_created,
                )

            emit({"type": "status", "message": "Agent is thinking..."})

            final_messages, _ = await run_agent(sbx, history, user_content, emit)

            prior = len(history_to_messages(history)) + 1
            for row in messages_to_rows(final_messages[prior:]):
                async with SessionLocal() as s:
                    await db.add_message(s, session_id, row["role"], row["content"])

        except asyncio.CancelledError:
            emit({"type": "error", "message": "Agent aborted"})
        except Exception as e:
            emit({"type": "error", "message": str(e)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)
            active_tasks.pop(session_id, None)

    task = asyncio.create_task(agent_task())
    active_tasks[session_id] = task

    async def event_stream() -> AsyncIterator[bytes]:
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_S)
                except asyncio.TimeoutError:
                    if task.done():
                        break
                    yield b": keepalive\n\n"
                    continue
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n".encode()
        except asyncio.CancelledError:
            # ponytail: browser disconnected — agent keeps running in background
            pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def start_run(session_id: str) -> StreamingResponse:
    async with SessionLocal() as session:
        row = await db.get_session(session, session_id)
        if not row:
            raise HTTPException(404, "Session not found")
        msgs = await db.list_messages(session, session_id)

    if not msgs:
        raise HTTPException(400, "No messages to run")
    if msgs[-1].role != "user":
        raise HTTPException(400, "Nothing to run — waiting for user message")

    user_content = message_content(msgs[-1].content)
    history = [{"role": m.role, "content": m.content} for m in msgs[:-1]]

    return await _sse_response(
        session_id, user_content, history, row.sandbox_id, save_user_message=False,
    )


async def start_message(session_id: str, content: str) -> StreamingResponse:
    async with SessionLocal() as session:
        row = await db.get_session(session, session_id)
        if not row:
            raise HTTPException(404, "Session not found")
        msgs = await db.list_messages(session, session_id)

    history = [{"role": m.role, "content": m.content} for m in msgs]
    return await _sse_response(
        session_id, content, history, row.sandbox_id, save_user_message=True,
    )
