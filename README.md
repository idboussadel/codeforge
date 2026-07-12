<div align="center">

<img width="120" alt="CodeForge" src="apps/web/public/logo1.png" />

# CodeForge

**Describe an app. Watch an agent build it — live.**

[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct-1C3C3C?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![E2B](https://img.shields.io/badge/E2B-Sandbox-000?style=flat-square)](https://e2b.dev/)

</div>

---

CodeForge is an AI coding workbench. You describe what you want in natural language; a LangGraph agent plans, writes files, runs commands, and verifies the result inside an isolated E2B sandbox — while you follow every step in a Cursor-style interface.

No code generation in chat bubbles. Real files. Real terminal. Real preview.

## Features

- **ReAct agent** — LangGraph loop with tools: read/write/edit files, shell, lint, dev server
- **Live workspace** — file tree, Monaco editor, sandbox console, iframe preview
- **Transparent runs** — interleaved markdown + collapsible tool steps, persisted across reloads
- **Session history** — SQLite-backed conversations; resume or branch from any session
- **E2B sandboxes** — cloud-isolated environments with Next.js preview on port 3000
- **Server-owned state** — agent survives tab refresh; no fragile client-side session hacks

## Stack

| Layer | Tech |
|-------|------|
| Web | Next.js 16, React 19, Tailwind 4, shadcn/ui, Monaco |
| API | FastAPI, SQLAlchemy + SQLite, SSE streaming |
| Agent | LangGraph, DeepSeek (`langchain-deepseek`) |
| Runtime | E2B code interpreter sandboxes |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  apps/web          Landing + chat UI + preview panel        │
└────────────────────────────┬────────────────────────────────┘
                             │ REST + SSE
┌────────────────────────────▼────────────────────────────────┐
│  apps/api          FastAPI routes + agent runtime           │
│    ├── LangGraph ReAct agent (tools → E2BSandbox)         │
│    ├── SQLite (sessions, messages)                        │
│    └── SSE stream (text, tools, preview, files_changed)     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│  E2B Sandbox       /home/user/<project>                     │
│    Next.js dev server → preview URL (0.0.0.0:3000)        │
└─────────────────────────────────────────────────────────────┘
```

**Request flow**

1. User creates a session with an initial prompt → stored in SQLite.
2. `POST /api/sessions/:id/run` starts the agent via SSE.
3. Agent uses sandbox tools; UI streams text and tool events in real time.
4. On completion, assistant + tool rows are saved; reload restores full history.
5. Demo tab calls `GET /preview` to ensure the dev server is up.

## Quick start

**Prerequisites:** Node 20+, Python 3.9+, [pnpm](https://pnpm.io/), [E2B](https://e2b.dev/) and [DeepSeek](https://platform.deepseek.com/) API keys.

```bash
git clone <repo-url> codeforge && cd codeforge
make setup        # install deps + copy .env.example → .env
```

Add your keys to `.env`:

```env
DEEPSEEK_API_KEY=...
E2B_API_KEY=...
```

```bash
make dev          # web → :3000  |  api → :8000
```

Open [http://localhost:3000](http://localhost:3000), describe an app, and follow the agent in the workspace.

## Environment

| Variable | Description |
|----------|-------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `E2B_API_KEY` | E2B sandbox API key |
| `E2B_TEMPLATE` | Sandbox template (default: `code-interpreter-v1`) |
| `MODEL` | LLM model (default: `deepseek-chat`) |
| `CORS_ORIGIN` | Allowed web origin (default: `http://localhost:3000`) |
| `NEXT_PUBLIC_API_URL` | API base URL for the web app |

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/sessions` | List sessions |
| `POST` | `/api/sessions` | Create session (+ optional first message) |
| `GET` | `/api/sessions/:id` | Session state + UI messages (with tool blocks) |
| `POST` | `/api/sessions/:id/run` | Resume agent on last user message (SSE) |
| `POST` | `/api/sessions/:id/messages` | New user turn (SSE) |
| `POST` | `/api/sessions/:id/abort` | Stop running agent |
| `GET` | `/api/sessions/:id/files` | Project file tree from sandbox |
| `GET` | `/api/sessions/:id/files/:path` | Read file content |
| `GET` | `/api/sessions/:id/preview` | Ensure dev server; return preview URL |
| `POST` | `/api/sessions/:id/terminal` | Run shell command in sandbox |

SSE events: `status`, `text`, `tool_start`, `tool_end`, `preview`, `files_changed`, `done`, `error`.

## Project structure

```
codeforge/
├── apps/
│   ├── web/                 Next.js frontend
│   │   ├── app/             Landing + /chat/[id]
│   │   ├── components/      Chat, preview, terminal, sidebar
│   │   └── lib/             API client, chat blocks, types
│   └── api/                 FastAPI backend
│       └── src/codeforge/
│           ├── agent/       LangGraph graph, tools, prompts
│           ├── agent_runtime.py
│           ├── sandbox.py   E2B integration
│           ├── db.py        SQLite models
│           └── main.py      Routes
├── data/                    SQLite database (created at runtime)
├── .env.example
├── Makefile
└── package.json             pnpm + turbo monorepo
```

## Development

```bash
make dev          # web + api
make web          # frontend only
make api          # backend only
make lint         # eslint
make typecheck    # tsc
```

Agent self-check:

```bash
cd apps/api/src && PYTHONPATH=. ../venv/bin/python -m codeforge.agent.self_check
```
