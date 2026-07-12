"""ponytail: minimal self-check for message round-trip."""
import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from codeforge.agent.messages import history_to_messages, messages_to_rows, rows_to_ui_messages

rows = messages_to_rows([HumanMessage("hi"), AIMessage("hello")])
assert len(rows) == 2
assert rows[0]["role"] == "user"
assert rows[1]["role"] == "assistant"
assert len(history_to_messages(rows)) == 2

ui_rows = [
    {"id": "1", "role": "user", "content": "build app", "created_at": "2024-01-01"},
    {
        "id": "2",
        "role": "assistant",
        "content": {
            "_internal": "tool_calls",
            "text": "",
            "tool_calls": [{"id": "tc1", "name": "list_files", "args": {"path": "."}}],
        },
        "created_at": "2024-01-01",
    },
    {
        "id": "3",
        "role": "tool",
        "content": {
            "tool_call_id": "tc1",
            "output": json.dumps({"output": "src/app/page.tsx", "isError": False}),
        },
        "created_at": "2024-01-01",
    },
    {"id": "4", "role": "assistant", "content": "Done.", "created_at": "2024-01-01"},
]
ui = rows_to_ui_messages(ui_rows)
assert len(ui) == 2
assert ui[1]["blocks"][0]["type"] == "tool"
assert ui[1]["blocks"][0]["step"]["output"] == "src/app/page.tsx"
assert ui[1]["blocks"][1]["type"] == "text"
print("agent self-check passed")
