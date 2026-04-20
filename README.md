# Multi-Agent Customer Support System

An AI-powered customer support stack that uses **multiple agents** to understand, route, and resolve user queries with **LLMs, RAG (FAISS), and a Next.js chat UI**.

---

## Overview

- **Triage Agent** — classifies intent and confidence  
- **Technical Agent** — product / technical issues  
- **Billing Agent** — payments and subscriptions  
- **Retrieval Agent (RAG)** — answers from `data/docs/` via FAISS  
- **Escalation Agent** — human handoff when confidence is low  

Orchestration uses **LangGraph** (`backend/graph/workflow.py`). Optional **MongoDB** stores chat history when `MONGODB_URI` is set.

---

## Architecture

```
User (Next.js)
     ↓
FastAPI (/api/chat)
     ↓
LangGraph: Triage → Technical | Billing | RAG | Escalation
     ↓
Gemini or OpenAI (chat + embeddings)
```

---

## Tech stack

| Layer    | Choice                                      |
| -------- | ------------------------------------------- |
| API      | FastAPI                                     |
| Agents   | LangChain + LangGraph                       |
| RAG      | FAISS + Gemini or OpenAI embeddings         |
| UI       | Next.js 14, Tailwind                        |
| History  | MongoDB (optional)                          |

---

## Project layout

```
.
├── backend/           # FastAPI app (run uvicorn from here)
│   ├── main.py
│   ├── agents/
│   ├── graph/
│   ├── services/
│   └── routes/
├── frontend/          # Next.js chat UI
├── data/
│   ├── docs/          # Markdown/txt for RAG
│   └── embeddings/    # Built FAISS index (gitignored)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Environment

Copy `.env.example` to `.env` at the repo root (or export variables). Use **one** provider (or set `LLM_PROVIDER` if both keys exist):

**Gemini (recommended if you have a Google AI key):**

```env
GEMINI_API_KEY=your_key
# optional: LLM_PROVIDER=gemini
# optional: GEMINI_CHAT_MODEL=gemini-2.0-flash
# optional: GEMINI_EMBEDDING_MODEL=models/text-embedding-004
```

**OpenAI:**

```env
OPENAI_API_KEY=sk-...
```

If `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is set and `LLM_PROVIDER` is not `openai`, the app uses **Gemini** for all agents and RAG embeddings.

Optional:

```env
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
TRIAGE_CONFIDENCE_THRESHOLD=0.55
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=multi_agent_support
CORS_ORIGINS=http://localhost:3000
```

### 2. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

On first start, the app builds a FAISS index from `data/docs/` under `data/embeddings/`.

### 3. Frontend

```bash
cd frontend
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if API is not localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## API

- `POST /api/chat` — body: `{ "message": "...", "session_id": "<optional uuid>" }`  
- `POST /api/session` — returns a new `session_id`  
- `GET /health` — health check  

---

## Example queries

| Query                     | Typical route |
| ------------------------- | ------------- |
| App not loading           | Technical     |
| Refund my payment         | Billing       |
| What is your pricing?     | RAG           |
| Ambiguous / low confidence| Escalation    |

---

## Deployment notes

- **Frontend:** Vercel (set `NEXT_PUBLIC_API_URL` to your API URL).  
- **Backend:** Render / Railway / any host that can run Python + persistent disk or rebuild index on boot.  
- Ensure CORS `CORS_ORIGINS` includes your frontend origin.

---

## Author

**Aravindhan S**

- GitHub: [aravind123465](https://github.com/aravind123465)  
- LinkedIn: [aravindhan](https://linkedin.com/in/aravindhan)  

---

## License

MIT License
# multi-agents-Ai
