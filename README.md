# 🧪 ML Sandbox

An AI-powered code execution sandbox that autonomously debugs and improves Python/ML scripts. Give it a goal and some starter code — the AI agent iterates in a secure Docker sandbox until the objective is met.

## ✨ How It Works

```
You provide:  Goal + Baseline Code + Dataset (optional) + Requirements (optional)
                                    ↓
                          ┌─────────────────┐
                          │   Ingest State   │  Build Docker image with deps
                          └────────┬────────┘
                                   ↓
                          ┌─────────────────┐
                     ┌───→│  Execute Code    │  Run script in Docker sandbox
                     │    └────────┬────────┘
                     │             ↓
                     │    ┌─────────────────┐
                     │    │  Evaluate Code   │  AI analyzes output vs goal
                     │    └────────┬────────┘
                     │             ↓
                     │       ┌───────────┐
                     │       │  Success?  │──── Yes ──→ ✅ Done
                     │       └─────┬─────┘
                     │             │ No
                     │             ↓
                     │    ┌─────────────────┐
                     └────│  Modify Code    │  AI rewrites the script
                          └─────────────────┘
                        (up to 5 iterations)
```

The agent uses **Gemini 2.5 Flash** for reasoning and code generation, **LangGraph** for the state machine, and **Docker** for secure sandboxed execution.

## 🏗️ Architecture

```
ML Sandbox/
├── backend/                    # FastAPI + LangGraph agent
│   ├── main.py                 # WebSocket & upload endpoints
│   ├── agent.py                # LangGraph state machine (4 nodes)
│   ├── sand_box.py             # Docker container management
│   ├── pyproject.toml          # Python dependencies (uv)
│   └── .env                    # GEMINI_API_KEY
│
└── frontend/                   # React + Vite + Tailwind v4
    └── src/
        ├── App.jsx             # Main UI (workspace + telemetry)
        ├── index.css           # Tailwind v4 entry
        └── main.jsx            # React entry point
```

| Layer | Tech |
|-------|------|
| **Frontend** | React 18, Vite, Tailwind CSS v4, Lucide Icons |
| **Backend** | FastAPI, WebSocket (async streaming), LangGraph |
| **AI** | Gemini 2.5 Flash via LangChain |
| **Sandbox** | Docker containers (`python:3.10-slim`) |
| **Package Manager** | uv (backend), npm (frontend) |

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Docker** (running — `docker ps` should work)
- **uv** ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Gemini API Key** ([get one](https://aistudio.google.com/apikey))

### 1. Clone the repo

```bash
git clone https://github.com/AdiTyaPal0710/ML-SandBox.git
cd ML-SandBox
```

### 2. Backend setup

```bash
cd backend

# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env

# Install dependencies and start the server
uv sync
uv run uvicorn main:app --reload
```

The backend runs at `http://localhost:8000`.

### 3. Frontend setup

```bash
cd frontend

npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

### 4. Pull the Docker base image (first time only)

```bash
docker pull python:3.10-slim
```

## 📖 Usage

1. **Set an objective** — Describe what you want the agent to achieve
2. **Provide baseline code** — Paste Python code or upload a `.py` file
3. **Upload a dataset** *(optional)* — `.csv` or `.json` files, available at `/data/filename` inside the container
4. **Upload requirements** *(optional)* — A `requirements.txt` file; dependencies get baked into a custom Docker image once, then reused across iterations
5. **Click "Deploy Agent"** — Watch the agent iterate in real-time via the Live Telemetry panel

### Controls

| Button | Action |
|--------|--------|
| **Deploy Agent** | Start the AI agent loop |
| **Stop Agent** | Abort a running agent (preserves logs for review) |
| **Reset** | Clear the workspace to start fresh |
| **Clear All** | Wipe everything after a completed run |

## 🔒 Security

- **Sandboxed execution** — All user code runs inside Docker containers with memory limits (512MB) and CPU constraints (1 core)
- **Container timeout** — Containers are killed after 120 seconds
- **Read-only data** — Datasets are mounted as read-only inside the container
- **Upload validation** — Filename sanitization prevents path traversal attacks, extension allowlist (`.csv`, `.json`), 50MB file size cap
- **Ephemeral containers** — Containers are removed after each execution

## ⚙️ Key Design Decisions

- **Image caching** — When a `requirements.txt` is provided, a custom Docker image is built once with dependencies pre-installed (`docker build`), then reused for all iterations. This avoids re-running `pip install` on every iteration.
- **Async streaming** — The backend uses `graph.astream()` with `async for` to push node-by-node updates to the frontend via WebSocket in real-time.
- **Failsafe cap** — The agent stops after 5 iterations to prevent runaway API costs.
- **Structured output** — The evaluator uses Pydantic-based structured output to guarantee valid status decisions (`success`, `needs_improvement`, `needs_debugging`).

## 🧰 Backend Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | HTTP & WebSocket server |
| `uvicorn` | ASGI server |
| `langgraph` | Agent state machine |
| `langchain-google-genai` | Gemini LLM integration |
| `docker` | Docker SDK for Python |
| `pydantic` | Structured output schemas |
| `python-dotenv` | Environment variable loading |
| `python-multipart` | File upload handling |

## 📄 License

This project is open source. Feel free to use and modify.
