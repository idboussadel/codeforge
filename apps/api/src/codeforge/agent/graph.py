from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from codeforge.agent.cache import extract_turn_usage, merge_usage
from codeforge.agent.llm import create_llm
from codeforge.agent.messages import history_to_messages
from codeforge.agent.prompt import SYSTEM_PROMPT
from codeforge.agent.tools import build_tools
from codeforge.sandbox import E2BSandbox, normalize_path

AgentEvent = dict[str, Any]
Emit = Callable[[AgentEvent], None]

# ponytail: LangGraph requires recursion_limit; 500 is high enough for any real build
RECURSION_LIMIT = 500


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def _tool_output(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    if hasattr(raw, "content"):
        c = raw.content
        return c if isinstance(c, str) else json.dumps(c, default=str)
    try:
        return json.dumps(raw, default=str)
    except TypeError:
        return str(raw)


def _summarize_tool_output(output: str, name: str) -> str:
    try:
        parsed = json.loads(output)
        text = str(parsed.get("output", output))
    except json.JSONDecodeError:
        text = output
    cap = 500 if name in ("read_file", "run_command", "check_project", "get_dev_server_logs") else 200
    return text if len(text) <= cap else text[:cap] + "…"


def _last_ai_text(messages: list[BaseMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            text = _extract_text(m.content)
            if text.strip():
                return text
    return ""


async def run_agent(
    sandbox: E2BSandbox,
    history: list[dict[str, Any]],
    user_message: str,
    emit: Emit,
) -> tuple[list[BaseMessage], dict[str, int]]:
    llm = create_llm()
    tools = build_tools(sandbox)
    agent = create_react_agent(
        llm,
        tools,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
    )

    input_messages = history_to_messages(history) + [HumanMessage(content=user_message)]
    usage = {"input": 0, "output": 0, "cacheRead": 0, "cacheMiss": 0}
    pending: dict[str, dict[str, Any]] = {}
    final_messages = input_messages
    streamed_text = ""

    async for event in agent.astream_events(
        {"messages": input_messages},
        version="v2",
        config={"recursion_limit": RECURSION_LIMIT},
    ):
        kind = event.get("event")

        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            text = _extract_text(getattr(chunk, "content", ""))
            if text:
                streamed_text += text
                emit({"type": "text", "delta": text})

        elif kind == "on_tool_start":
            run_id = event.get("run_id", "")
            name = event.get("name", "unknown")
            inp = event.get("data", {}).get("input", {})
            pending[run_id] = {"name": name, "input": inp}
            emit({"type": "tool_start", "id": run_id, "name": name, "input": inp})

        elif kind == "on_tool_end":
            run_id = event.get("run_id", "")
            raw = event.get("data", {}).get("output", "")
            output = _tool_output(raw)

            is_error = False
            preview_url = None
            changed_paths: list[str] = []
            try:
                parsed = json.loads(output)
                is_error = parsed.get("isError", False)
                preview_url = parsed.get("previewUrl")
                changed_paths = parsed.get("changedPaths", [])
            except json.JSONDecodeError:
                pass

            meta = pending.pop(run_id, {})
            if not changed_paths and meta.get("name") in ("write_file", "edit_file"):
                path = meta.get("input", {}).get("path")
                if path:
                    changed_paths = [path]

            emit({
                "type": "tool_end",
                "id": run_id,
                "output": _summarize_tool_output(output, meta.get("name", "")),
                "isError": is_error,
            })
            if changed_paths:
                emit({"type": "files_changed", "paths": [normalize_path(p) for p in changed_paths]})
            if preview_url:
                emit({"type": "preview", "url": preview_url})

        elif kind == "on_chat_model_end":
            output = event.get("data", {}).get("output")
            if output:
                usage = merge_usage(usage, extract_turn_usage(output))

        elif kind == "on_chain_end" and event.get("name") == "LangGraph":
            out = event.get("data", {}).get("output", {})
            if out and "messages" in out:
                final_messages = out["messages"]
                tail = _last_ai_text(final_messages)
                if tail and tail not in streamed_text:
                    emit({"type": "text", "delta": tail})

    emit({"type": "done", "usage": usage})
    return final_messages, usage
