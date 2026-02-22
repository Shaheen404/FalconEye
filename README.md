# 🦅 FalconEye

**High-performance, RAG-enhanced OSINT Agentic Tool**

FalconEye is a web-based, multi-agent system that automates reconnaissance, data correlation, and social-engineering simulation. It uses CrewAI agents backed by Claude LLMs, a Pinecone-powered RAG pipeline, and a real-time streaming React dashboard.

---

## 📂 Project Structure

```
FalconEye/
├── backend/
│   ├── main.py                  # FastAPI entry-point
│   ├── requirements.txt         # Python dependencies
│   ├── routes/
│   │   └── crew_routes.py       # API endpoints (SSE streaming)
│   ├── services/
│   │   ├── crew.py              # CrewAI agentic engine
│   │   └── safety_filter.py     # Blocks .gov/.edu/.mil queries
│   ├── memory/
│   │   ├── embeddings.py        # Sentence-transformer embeddings
│   │   ├── pinecone_store.py    # Pinecone vector store
│   │   └── rag_pipeline.py      # Chunk → embed → store → retrieve
│   └── tests/
│       ├── test_safety_filter.py
│       └── test_routes.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       └── components/
│           ├── SearchForm.jsx    # Target input form
│           ├── LogTerminal.jsx   # Live SSE agent log viewer
│           └── FinalReport.jsx   # Markdown report renderer
├── .env.example                  # Environment variable template
├── .gitignore
└── README.md
```

---

## ⚙️ Technical Stack

| Layer | Technology |
|---|---|
| **LLM** | Claude (Anthropic) via CrewAI |
| **Backend** | Python 3.12+ / FastAPI (async) |
| **Agents** | CrewAI (hierarchical process) |
| **Vector DB** | Pinecone (serverless) |
| **Frontend** | React 19 / Vite / Tailwind CSS / Framer Motion |
| **Real-time** | Server-Sent Events (SSE) |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** — [python.org](https://www.python.org/downloads/)
- **Node.js 20+** — [nodejs.org](https://nodejs.org/)
- **Git** — [git-scm.com](https://git-scm.com/)

### 1. Clone the repository

```bash
git clone https://github.com/Shaheen404/FalconEye.git
cd FalconEye
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/) |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev/) |
| `PINECONE_API_KEY` | [pinecone.io](https://www.pinecone.io/) |

### 3. Backend setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Run the API server
uvicorn backend.main:app --reload --port 8000
```

The API is now available at **http://localhost:8000**. Verify with:

```bash
curl http://localhost:8000/api/health
# → {"status":"ok"}
```

### 4. Frontend setup

Open a **second terminal**:

```bash
cd frontend
npm install
npm run dev
```

The dashboard is now available at **http://localhost:5173**.

### 5. Run both servers simultaneously (shortcut)

You can use two terminal tabs, or a process manager like `concurrently`:

```bash
# Terminal 1 — Backend
source .venv/bin/activate && uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

---

## 🧪 Running Tests

```bash
# From project root, with venv activated
pytest backend/tests/ -v
```

---

## 🛡️ Safety Filter

FalconEye includes a built-in `SafetyFilter` that **blocks any search query targeting sensitive domains** (`.gov`, `.edu`, `.mil`). This filter is enforced at both the API route level and inside the agent tools.

---

## 📡 API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | App info |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/crew/stream` | Launch a crew run with SSE streaming |

### `POST /api/crew/stream`

**Request body:**

```json
{
  "target": "acme-corp.com",
  "pinecone_index": "falconeye"
}
```

**Response:** Server-Sent Events stream with JSON payloads:

```
data: {"run_id":"...","type":"start","message":"Crew launched."}
data: {"run_id":"...","type":"log","message":"Agent is analyzing..."}
data: {"run_id":"...","type":"result","message":"# Final Report\n..."}
data: {"run_id":"...","type":"done"}
```

---

## 📝 License

This project is for educational and authorised security-testing purposes only. Always obtain proper authorisation before performing reconnaissance on any target.
