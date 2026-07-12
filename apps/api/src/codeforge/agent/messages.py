from __future__ import annotations

import json
from typing import Any, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

APP_ROOT = "/home/user"


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def _json_safe(content: Any) -> Any:
    if isinstance(content, str):
        return content
    try:
        json.dumps(content)
        return content
    except TypeError:
        return str(content)


def _serialize_tool_calls(tool_calls: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tc in tool_calls or []:
        if isinstance(tc, dict):
            out.append({
                "id": tc.get("id", ""),
                "name": tc.get("name", ""),
                "args": tc.get("args", {}),
            })
        else:
            out.append({
                "id": getattr(tc, "id", ""),
                "name": getattr(tc, "name", ""),
                "args": getattr(tc, "args", {}),
            })
    return out


def _summarize_tool_output(output: Any, name: str = "") -> str:
    text = output
    if isinstance(output, dict):
        text = output.get("output", output)
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                text = str(parsed.get("output", text))
        except json.JSONDecodeError:
            pass
    else:
        text = str(text)
    cap = 500 if name in ("read_file", "run_command", "check_project", "get_dev_server_logs") else 200
    return text if len(text) <= cap else text[:cap] + "…"


def _tool_result_error(output: Any) -> bool:
    if isinstance(output, dict):
        return bool(output.get("isError", False))
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
            return bool(parsed.get("isError", False)) if isinstance(parsed, dict) else False
        except json.JSONDecodeError:
            return False
    return False


def rows_to_ui_messages(rows: list[Any]) -> list[dict[str, Any]]:
    """Merge stored assistant + tool rows into one UI turn with interleaved blocks."""
    ui: list[dict[str, Any]] = []
    i = 0

    while i < len(rows):
        row = rows[i]
        role = row.role if hasattr(row, "role") else row["role"]

        if role == "user":
            content = row.content if hasattr(row, "content") else row["content"]
            created_at = row.created_at if hasattr(row, "created_at") else row["created_at"]
            ui.append({
                "id": row.id if hasattr(row, "id") else row["id"],
                "role": "user",
                "content": str(content),
                "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
            })
            i += 1
            continue

        blocks: list[dict[str, Any]] = []
        pending_tools: dict[str, int] = {}
        first_id = row.id if hasattr(row, "id") else row["id"]
        first_at = row.created_at if hasattr(row, "created_at") else row["created_at"]

        while i < len(rows):
            cur = rows[i]
            cur_role = cur.role if hasattr(cur, "role") else cur["role"]
            if cur_role == "user":
                break

            cur_content = cur.content if hasattr(cur, "content") else cur["content"]

            if cur_role == "assistant":
                if isinstance(cur_content, dict) and cur_content.get("_internal") == "tool_calls":
                    text = str(cur_content.get("text") or "")
                    if text.strip():
                        blocks.append({"type": "text", "content": text})
                    for tc in cur_content.get("tool_calls", []):
                        tid = str(tc.get("id") or "")
                        step = {
                            "id": tid or f"tool-{len(blocks)}",
                            "name": tc.get("name", ""),
                            "input": tc.get("args", {}),
                            "status": "done",
                        }
                        blocks.append({"type": "tool", "step": step})
                        if tid:
                            pending_tools[tid] = len(blocks) - 1
                elif isinstance(cur_content, str) and cur_content.strip():
                    blocks.append({"type": "text", "content": cur_content})

            elif cur_role == "tool" and isinstance(cur_content, dict):
                tid = str(cur_content.get("tool_call_id") or "")
                raw = cur_content.get("output", "")
                idx = pending_tools.get(tid)
                if idx is not None:
                    step = blocks[idx]["step"]
                    name = step.get("name", "")
                    is_error = _tool_result_error(raw)
                    step["output"] = _summarize_tool_output(raw, name)
                    step["isError"] = is_error
                    step["status"] = "error" if is_error else "done"

            i += 1

        if blocks:
            created = first_at.isoformat() if hasattr(first_at, "isoformat") else str(first_at)
            ui.append({
                "id": first_id,
                "role": "assistant",
                "content": "",
                "blocks": blocks,
                "created_at": created,
            })

    return ui


def is_display_message(role: str, content: Any) -> bool:
    """Messages safe to show in the chat UI."""
    if role == "tool":
        return False
    if role == "user" and isinstance(content, list):
        return not any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        )
    if role == "assistant" and isinstance(content, dict):
        return content.get("_internal") != "tool_calls"
    return role in ("user", "assistant")


def display_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict) and content.get("_internal") == "tool_calls":
        return str(content.get("text") or "")
    return ""


def history_to_messages(rows: list[dict[str, Any]]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for row in rows:
        role, content = row["role"], row["content"]
        if role == "user":
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        messages.append(ToolMessage(
                            content=block.get("content", ""),
                            tool_call_id=block.get("tool_use_id", ""),
                        ))
                    else:
                        messages.append(HumanMessage(content=str(block)))
            else:
                messages.append(HumanMessage(content=str(content)))
        elif role == "assistant":
            if isinstance(content, dict) and content.get("_internal") == "tool_calls":
                messages.append(AIMessage(
                    content=content.get("text", ""),
                    tool_calls=content.get("tool_calls", []),
                ))
            elif isinstance(content, str):
                messages.append(AIMessage(content=content))
            else:
                messages.append(AIMessage(content=_extract_text(content) or str(content)))
        elif role == "tool":
            if isinstance(content, dict):
                messages.append(ToolMessage(
                    content=str(content.get("output", "")),
                    tool_call_id=content.get("tool_call_id", ""),
                ))
            else:
                messages.append(ToolMessage(content=str(content), tool_call_id=""))
    return messages


def messages_to_rows(messages: List[BaseMessage]) -> List[dict[str, Any]]:
    rows: List[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            rows.append({"role": "user", "content": _json_safe(m.content)})
        elif isinstance(m, AIMessage):
            if m.tool_calls:
                rows.append({
                    "role": "assistant",
                    "content": {
                        "_internal": "tool_calls",
                        "text": _extract_text(m.content),
                        "tool_calls": _serialize_tool_calls(m.tool_calls),
                    },
                })
            else:
                text = _extract_text(m.content)
                if text.strip():
                    rows.append({"role": "assistant", "content": text})
        elif isinstance(m, ToolMessage):
            rows.append({
                "role": "tool",
                "content": {
                    "output": _json_safe(m.content),
                    "tool_call_id": m.tool_call_id or "",
                },
            })
    return rows
