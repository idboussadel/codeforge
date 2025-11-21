<div align="center">
<img width="500" alt="logo1" src="https://github.com/user-attachments/assets/1032ded3-5f44-4c8b-8b51-8eebd0c2f9a7" />

[![Next.js](https://img.shields.io/badge/Next.js-16.0-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

**An AI-powered full-stack development platform that transforms natural language into production-ready web applications**

</div>
<video src="https://github.com/user-attachments/assets/43aeee16-cda1-4480-82e2-ad6c22b7917c" controls></video>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**CodeForge** is a sophisticated AI-powered development platform that enables developers to generate complete, production-ready web applications through natural language prompts ( its like a [Bolt](https://bolt.com) clone ). Leveraging state-of-the-art language models (GPT-4o and Claude Sonnet 4), CodeForge intelligently creates React/Next.js applications with proper component architecture, styling, and functionality.

### What Makes CodeForge Different?

- **Production-Ready Code**: Generates complete applications using shadcn/ui components and Tailwind CSS
- **Real-Time Preview**: Instant visual feedback with live code execution in isolated sandboxes
- **Multi-Model Support**: Choose between OpenAI GPT-4o and Anthropic Claude Sonnet 4
- **Conversational Development**: Iterative refinement through natural conversation
- **Smart Architecture**: Intelligent file structuring, component composition, and dependency management
- **E2B Sandbox Integration**: Safe, isolated code execution environment with full Node.js support

E2B sandboxes example :
<img width="1919" height="898" alt="image" src="https://github.com/user-attachments/assets/2a4d36a4-b527-4b76-a434-9aefe96d5e74" />

---

## Features

### Core Capabilities

- **Instant App Generation**: Transform ideas into complete web applications in seconds
- **Natural Language Interface**: Describe what you want in plain English
- **Framework-Aware**: Understands Next.js, React, and modern web development patterns
- **Beautiful UI by Default**: Automatically integrates shadcn/ui components with polished designs
- **Responsive Design**: Mobile-first, accessible interfaces out of the box
- **Live Code Editing**: Real-time code preview and execution
- **Session Management**: Persistent conversations with context retention
- **Interactive Terminal**: Execute shell commands within the sandbox environment

### Developer Experience

- **Automatic Dependency Management**: Smart package.json generation with required dependencies
- **Intelligent Code Parsing**: Extracts and organizes generated artifacts
- **Multi-Provider Support**: Switch between GPT-4o and Claude Sonnet 4 on the fly
- **Streaming Responses**: Real-time AI response streaming for better UX
- **Error Handling**: Comprehensive error boundaries and graceful degradation
- **Hot Reload**: Instant feedback during development

---

## Tech Stack

### Frontend

| Technology                   | Version | Purpose                         |
| ---------------------------- | ------- | ------------------------------- |
| **Next.js**                  | 16.0.3  | React framework with App Router |
| **React**                    | 19.2.0  | UI library                      |
| **TypeScript**               | 5.x     | Type safety                     |
| **Tailwind CSS**             | 4.x     | Utility-first styling           |
| **shadcn/ui**                | Latest  | High-quality component library  |
| **Radix UI**                 | Latest  | Accessible primitives           |
| **Lucide React**             | 0.553.0 | Icon library                    |
| **React Markdown**           | 10.1.0  | Markdown rendering              |
| **React Syntax Highlighter** | 16.1.0  | Code syntax highlighting        |

### Backend

| Technology        | Version | Purpose                        |
| ----------------- | ------- | ------------------------------ |
| **FastAPI**       | 0.100+  | Modern Python web framework    |
| **Python**        | 3.9+    | Runtime environment            |
| **OpenAI API**    | Latest  | GPT-4o language model          |
| **Anthropic API** | Latest  | Claude Sonnet 4 language model |
| **E2B**           | Latest  | Code execution sandboxes       |
| **Pydantic**      | Latest  | Data validation                |
| **python-dotenv** | Latest  | Environment management         |

---

## Architecture

CodeForge follows a modern, scalable architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                       │
│                    (Next.js + React)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Application                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Chat Panel   │  │Preview Panel │  │  Terminal    │       │
│  │  Component   │  │  Component   │  │  Component   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   API        │  │   Prompts    │  │  Services    │       │
│  │  Endpoints   │  │   Engine     │  │   Layer      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────┬────────────────────┬────────────────────┬──────────────┘
     │                    │                    │
     ▼                    ▼                    ▼
┌─────────┐         ┌─────────┐         ┌──────────┐
│ OpenAI  │         │Anthropic│         │   E2B    │
│   API   │         │   API   │         │ Sandbox  │
└─────────┘         └─────────┘         └──────────┘
```

### Key Components

1. **Frontend (Next.js)**

   - **Chat Panel**: User interaction, prompt input, model selection
   - **Preview Panel**: Live iframe preview of generated applications
   - **Terminal**: Interactive shell for sandbox commands
   - **State Management**: Session-based storage with React hooks

2. **Backend (FastAPI)**

   - **API Layer**: RESTful endpoints for code generation and execution
   - **Prompt Engine**: Advanced prompt engineering for optimal AI responses
   - **Parser Service**: Extracts and organizes generated artifacts
   - **Sandbox Manager**: E2B sandbox lifecycle management

3. **External Services**
   - **OpenAI GPT-4o**: Primary language model for code generation
   - **Anthropic Claude Sonnet 4**: Alternative model with extended context
   - **E2B Sandboxes**: Isolated execution environments with Node.js support

---

## Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18.0.0 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.9 or higher) - [Download](https://python.org/)
- **npm** or **yarn** - Comes with Node.js
- **Git** - [Download](https://git-scm.com/)

### API Keys Required

You'll need API keys from the following services:

1. **OpenAI API Key** - [Get it here](https://platform.openai.com/api-keys)
2. **Anthropic API Key** - [Get it here](https://console.anthropic.com/)
3. **E2B API Key** - [Get it here](https://e2b.dev/)

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/idboussadel/codeforge.git
cd codeforge
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Or create manually

# Edit .env and add your API keys
```

**Backend `.env` file:**

```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
E2B_API_KEY=your_e2b_api_key_here
```

#### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install
# or
yarn install

# Create .env.local file (if needed for frontend-specific vars)
cp .env.example .env.local  # Optional
```

---

## Configuration

### Backend Configuration

**File: `backend/.env`**

```env
# Required API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
E2B_API_KEY=...

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8000

# Optional: Logging Level
LOG_LEVEL=ERROR  # ERROR, INFO, DEBUG
```

### Frontend Configuration

**File: `frontend/.env.local`** (Optional)

```env
# API Base URL (default: http://localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics, etc.
```

### CORS Configuration

The backend is configured to allow requests from `http://localhost:3000` by default. To modify:

**File: `backend/main.py`**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Modify this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Usage

### Starting the Application

#### 1. Start the Backend Server

```bash
cd backend

# Activate virtual environment if not already active
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

#### 2. Start the Frontend Development Server

```bash
cd frontend

# Start Next.js dev server
npm run dev
# or
yarn dev
```

The frontend will be available at `http://localhost:3000`

### Using CodeForge

1. **Open your browser** and navigate to `http://localhost:3000`

2. **Enter a prompt** describing what you want to build:

   ```
   Create a modern landing page for a SaaS product with a hero section,
   feature cards, pricing table, and contact form. Use gradients and
   animations.
   ```

3. **Select your AI model**:

   - **GPT-4o**: Faster, great for most use cases
   - **Claude Sonnet 4**: Larger context window, better for complex apps

4. **Watch the magic happen**:

   - AI generates complete code with all necessary files
   - Preview updates in real-time as code is created
   - Interact with the generated application immediately

5. **Iterate and refine**:

   ```
   Add a dark mode toggle and make the pricing cards more vibrant
   ```

6. **Execute terminal commands** (if needed):
   - Use the terminal panel to run npm commands
   - Install additional packages
   - Check build outputs

---

## API Reference

### POST `/api/generate`

Generate code from a natural language prompt.

**Request Body:**

```json
{
  "prompt": "Create a todo app with React",
  "conversation_history": [],
  "model_provider": "gpt"
}
```

**Response:**

```json
{
  "content": "Full AI response with markdown and artifacts",
  "artifact": {
    "id": "unique-artifact-id",
    "title": "Todo Application",
    "type": "nextjs",
    "actions": [
      {
        "type": "file",
        "path": "package.json",
        "content": "..."
      }
    ]
  }
}
```

### POST `/api/stream`

Stream code generation responses in real-time.

**Request Body:**

```json
{
  "prompt": "Build a weather dashboard",
  "conversation_history": [],
  "model_provider": "claude"
}
```

**Response:** Server-Sent Events (SSE) stream

### POST `/api/execute`

Execute artifact actions in an E2B sandbox.

**Request Body:**

```json
{
  "session_id": "unique-session-id",
  "actions": [
    {
      "type": "file",
      "path": "app/page.tsx",
      "content": "export default function Page() { ... }"
    }
  ]
}
```

### POST `/api/terminal`

Execute shell commands in the sandbox.

**Request Body:**

```json
{
  "session_id": "unique-session-id",
  "command": "npm install axios"
}
```

---

## Project Structure

```
codeforge/
├── backend/                    # FastAPI backend
│   ├── main.py                # Main API application
│   ├── prompts.py             # Prompt engineering templates
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables (not in git)
│   └── services/              # Business logic services
│       ├── parser.py          # Artifact extraction & parsing
│       └── sandbox.py         # E2B sandbox management
│
├── frontend/                  # Next.js frontend
│   ├── app/                   # Next.js App Router
│   │   ├── page.tsx           # Landing page
│   │   ├── layout.tsx         # Root layout
│   │   ├── globals.css        # Global styles
│   │   └── chat/              # Chat interface
│   │       └── [id]/
│   │           └── page.tsx   # Dynamic chat page
│   │
│   ├── components/            # React components
│   │   ├── chat-panel.tsx     # Chat interface component
│   │   ├── preview-panel.tsx  # Code preview component
│   │   ├── terminal.tsx       # Terminal component
│   │   └── ui/                # shadcn/ui components
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── input.tsx
│   │       └── ...
│   │
│   ├── lib/                   # Utilities & types
│   │   ├── api.ts             # API client functions
│   │   ├── types.ts           # TypeScript type definitions
│   │   └── utils.ts           # Utility functions
│   │
│   ├── public/                # Static assets
│   ├── package.json           # Node dependencies
│   ├── tsconfig.json          # TypeScript config
│   ├── tailwind.config.ts     # Tailwind configuration
│   └── next.config.ts         # Next.js configuration
│
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

---

## Development

### Backend Development

#### Installing New Python Packages

```bash
cd backend
pip install package-name
pip freeze > requirements.txt
```

#### Running Tests

```bash
cd backend
pytest
```

#### Code Formatting

```bash
# Install black (code formatter)
pip install black

# Format code
black .
```

### Frontend Development

#### Installing New NPM Packages

```bash
cd frontend
npm install package-name
# or
yarn add package-name
```

#### Type Checking

```bash
npm run type-check
# or
npx tsc --noEmit
```

#### Linting

```bash
npm run lint
```

#### Building for Production

```bash
npm run build
npm run start  # Run production build
```

### Adding shadcn/ui Components

While CodeForge generates shadcn/ui components programmatically, you can add them manually:

```bash
cd frontend
npx shadcn@latest add button
npx shadcn@latest add card
# etc.
```

---

## Deployment

### Backend Deployment (FastAPI)

#### Option 1: Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t codeforge-backend .
docker run -p 8000:8000 --env-file backend/.env codeforge-backend
```

#### Option 2: Cloud Platforms

- **Railway**: Connect GitHub repo, set environment variables
- **Render**: Deploy as Web Service, add environment variables
- **Google Cloud Run**: Deploy container with Cloud Build
- **AWS Lambda**: Use Mangum adapter for serverless deployment

### Frontend Deployment (Next.js)

#### Option 1: Vercel (Recommended)

```bash
cd frontend
npm install -g vercel
vercel
```

#### Option 2: Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

CMD ["npm", "start"]
```

#### Option 3: Static Export (if applicable)

```bash
npm run build
# Deploy the 'out' directory to any static host
```

### Environment Variables in Production

**Backend:**

- Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `E2B_API_KEY` in your hosting platform
- Update CORS origins in `main.py` to match your frontend URL

**Frontend:**

- Set `NEXT_PUBLIC_API_URL` to your backend URL
- Ensure API endpoint URLs are correctly configured

---

## Troubleshooting

### Common Issues

#### Issue: Backend won't start

```bash
Error: No module named 'fastapi'
```

**Solution:**

```bash
cd backend
pip install -r requirements.txt
```

#### Issue: Frontend API calls fail

```bash
Error: CORS policy blocked
```

**Solution:** Update `backend/main.py` CORS settings:

```python
allow_origins=["http://localhost:3000", "your-frontend-url"]
```

#### Issue: E2B sandbox timeout

```bash
Error: Sandbox creation timeout
```

**Solution:**

- Check your E2B API key is valid
- Verify E2B account has available credits
- Check network connectivity

#### Issue: Module not found in generated code

**Solution:** The sandbox needs to install dependencies:

- Use the terminal panel to run `npm install`
- CodeForge automatically runs this in most cases

#### Issue: Preview not loading

**Solution:**

- Check browser console for errors
- Verify the sandbox URL is accessible
- Try refreshing the preview panel

### Getting Help

- **GitHub Issues**: [Open an issue](https://github.com/idboussadel/codeforge/issues)
- **Documentation**: Check this README thoroughly
- **Logs**: Check backend terminal for detailed error messages

---

## Contributing

We welcome contributions! Here's how you can help:

### How to Contribute

1. **Fork the repository**

   ```bash
   git clone https://github.com/yourusername/codeforge.git
   ```

2. **Create a feature branch**

   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**

   - Write clean, documented code
   - Follow existing code style
   - Add tests if applicable

4. **Commit your changes**

   ```bash
   git commit -m "Add amazing feature"
   ```

5. **Push to your fork**

   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open a Pull Request**

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python, ESLint config for TypeScript
- **Commits**: Use clear, descriptive commit messages
- **Documentation**: Update README if you change functionality
- **Testing**: Ensure existing tests pass, add tests for new features

### Areas for Contribution

- Bug fixes
- New features (AI models, UI improvements)
- Documentation improvements
- UI/UX enhancements
- Test coverage
- Internationalization

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **OpenAI** - For the powerful GPT-4o model
- **Anthropic** - For Claude Sonnet 4
- **E2B** - For secure sandbox environments
- **Vercel** - For Next.js and deployment platform
- **shadcn** - For the beautiful UI component library
- **FastAPI** - For the modern Python web framework

---

## Contact

**Project Maintainer**: [@idboussadel](https://github.com/idboussadel)

**Project Link**: [https://github.com/idboussadel/codeforge](https://github.com/idboussadel/codeforge)

---

<div align="center">

**Made with love by developers, for developers**

Star this repo if you find it helpful!

</div>
