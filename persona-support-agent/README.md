# Persona-Adaptive Customer Support Agent

An AI-powered customer support agent that detects a customer's communication **persona**
(Technical Expert, Frustrated User, Business Executive), retrieves grounded answers from a
knowledge base using **RAG**, adapts its tone accordingly, and **escalates to a human agent**
with a structured handoff summary when needed.

This project uses **Google Gemini**, which has a generous **free API tier** (no credit card
required for moderate usage) — get a free key at https://aistudio.google.com/apikey.

- **Frontend**: React + Vite
- **Backend**: Python + FastAPI
- **Database**: MongoDB (stores knowledge-base chunks + embeddings, conversation history, escalations)
- **LLM**: Google Gemini (`gemini-2.5-flash`, free tier)
- **Embeddings**: Google Gemini (`text-embedding-001`, free tier)

---

### Deploy:
Backend: https://aniladsparkxbackend.onrender.com/health
Backend-docs: https://aniladsparkxbackend.onrender.com/docs

frontend: https://aniladsparkx.vercel.app

## 1. Project Overview

The agent classifies every incoming message into one of three personas, retrieves the most
relevant chunks from a knowledge base of support articles via cosine-similarity vector search,
generates a response in a persona-appropriate tone using **only** the retrieved content, and
escalates to a human when retrieval confidence is low, the topic is sensitive (billing/legal),
or the user remains frustrated across multiple turns.

## 2. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React | 18.3.x |
| Frontend | Vite | 5.3.x |
| Frontend | Axios | 1.7.x |
| Backend | Python | 3.11+ |
| Backend | FastAPI | 0.110+ |
| Backend | Uvicorn | 0.29+ |
| Database | MongoDB | 6.x / Atlas |
| Database driver | PyMongo | 4.6+ |
| LLM | Google Gemini `gemini-2.5-flash` (free tier) | via `google-genai` SDK |
| Embeddings | Google Gemini `text-embedding-001` (free tier) | via `google-genai` SDK |
| Chunking | `langchain-text-splitters` `RecursiveCharacterTextSplitter` | 0.3+ |
| PDF parsing | `pypdf` | 4.2+ |
| Vector math | `numpy` (cosine similarity) | 1.26+ |

## 3. Architecture Diagram

```
                        ┌───────────────────────┐
                        │      User Query        │
                        │   (React Chat UI)      │
                        └───────────┬────────────┘
                                    │ POST /chat
                                    ▼
                        ┌───────────────────────┐
                        │   Persona Detection     │
                        │  (Gemini structured     │
                        │   JSON classification,   │
                        │   rule-based fallback)   │
                        └───────────┬────────────┘
                                    │ persona label
                                    ▼
                        ┌───────────────────────┐
                        │   RAG Retrieval         │
                        │  Embed query → cosine   │
                        │  similarity search over  │
                        │  MongoDB chunk store     │
                        └───────────┬────────────┘
                                    │ top-k chunks + scores
                                    ▼
                        ┌───────────────────────┐
                        │   Escalation Check      │
                        │  - low confidence?      │
                        │  - sensitive topic?     │
                        │  - repeated frustration? │
                        └──────┬─────────┬────────┘
                  no escalation│         │escalation needed
                               ▼         ▼
                ┌─────────────────┐  ┌─────────────────────┐
                │ Adaptive Response │  │  Human Handoff       │
                │ Generation (LLM,  │  │  Summary (JSON):      │
                │ grounded strictly │  │  persona, issue,      │
                │ in retrieved text)│  │  history, sources,    │
                └─────────┬─────────┘  │  attempted steps,     │
                          │            │  recommendation       │
                          ▼            └──────────┬───────────┘
                ┌─────────────────────────────────▼───────────┐
                │     Response returned to React chat UI       │
                │  (persona badge, sources, escalation status) │
                └───────────────────────────────────────────────┘
                          │
                          ▼
                ┌─────────────────────────┐
                │   MongoDB: conversation   │
                │   history + escalations   │
                │   persisted for audit      │
                └─────────────────────────┘
```

## 4. Persona Detection Strategy

- **Classification method**: A single Gemini chat call (`response_mime_type=application/json`)
  with a system prompt that defines the three personas and their linguistic signals, returning
  `{"persona", "confidence", "reasoning"}`.
- **Prompt design**: The system prompt explicitly lists the vocabulary/tone signals for each
  persona (technical jargon & API/log mentions → Technical Expert; emotional/urgent language →
  Frustrated User; business-impact/timeline/SLA language → Business Executive) and forces strict
  JSON output to avoid free-text parsing issues.
- **Rules used / fallback**: If the LLM call fails or returns invalid JSON, `classifier.py` falls
  back to a deterministic keyword-scoring heuristic (`_rule_based_fallback`) so the system never
  crashes and always degrades gracefully, defaulting to "Business Executive" (the safest, most
  neutral tone) when no signal is detected.

## 5. RAG Pipeline Design

- **Document ingestion**: `.txt`/`.md` files are read directly; `.pdf` files are parsed page-by-page
  with `pypdf` so page numbers can be preserved as metadata.
- **Chunking strategy**: `RecursiveCharacterTextSplitter` with `chunk_size=500`, `chunk_overlap=50`
  (configurable via `.env`). This splits on paragraph → sentence → word boundaries first, falling
  back to character splits, to keep chunks semantically coherent while preserving context across
  boundaries via overlap.
- **Embedding model**: Google Gemini `text-embedding-004` (768-dim, free tier).
- **Vector storage choice**: Rather than a separate vector database process, embeddings are stored
  as arrays directly inside **MongoDB** documents (one document per chunk, with `source`, `page`,
  `section`, `text`, and `embedding` fields). This keeps the whole system on a single database
  (MongoDB, as required) without needing to run/operate FAISS/Chroma/Qdrant alongside it.
- **Retrieval strategy**: At query time, the query is embedded once, then **cosine similarity**
  (via `numpy`) is computed against every stored chunk's embedding in Python; the top-k
  (`TOP_K=3` by default) highest-scoring chunks are returned with their similarity score, which
  doubles as the retrieval-confidence signal used by the escalation logic.
- **Metadata**: Each chunk stores `source` (filename) and either `page` (for PDFs) or `section`
  (chunk index, for txt/md), satisfying the source+location metadata requirement.

## 6. Escalation Logic

Escalation triggers (all configurable in `app/config.py` / `.env`):

1. **No relevant information found** — zero chunks retrieved.
2. **Low retrieval confidence** — best cosine similarity score `< RETRIEVAL_CONFIDENCE_THRESHOLD`
   (default `0.45`).
3. **Sensitive topics** — message contains a keyword from `SENSITIVE_KEYWORDS`
   (e.g. `refund`, `chargeback`, `legal`, `dispute`, `duplicate charge`).
4. **Repeated frustration** — the user has been classified as `Frustrated User` for
   `MAX_FRUSTRATED_TURNS_BEFORE_ESCALATION` (default `2`) consecutive turns.

When any trigger fires, `escalator.build_handoff_summary()` assembles a structured JSON document
(persona, issue, full conversation history, documents used, attempted steps, escalation reasons,
and a recommendation) which is stored in MongoDB (`escalations` collection) and returned to the UI.

## 7. Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MongoDB running locally (`mongodb://localhost:27017`) or a MongoDB Atlas connection string
- A free Google Gemini API key from https://aistudio.google.com/apikey

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit .env and add your GEMINI_API_KEY / MONGO_URI

uvicorn app.main:app --reload --port 8000
```

On first startup, the backend automatically ingests every document in `app/data/` into MongoDB
(skips re-ingestion if chunks already exist). You can force re-ingestion any time via:

```bash
curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json" -d '{"force": true}'
```

#### CLI chatbot (minimum required UI)

```bash
cd backend
python cli.py
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # defaults to http://localhost:8000, edit if backend is elsewhere
npm run dev
```

Open the printed local URL (default `http://localhost:5173`).

## 8. Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | **Required.** Free key from https://aistudio.google.com/apikey | — |
| `CHAT_MODEL` | Gemini chat model | `gemini-2.5-flash` |
| `EMBEDDING_MODEL` | Gemini embedding model | `text-embedding-001` |
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Database name | `persona_support_agent` |
| `CHUNK_SIZE` | Characters per chunk | `500` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `TOP_K` | Chunks retrieved per query | `3` |
| `RETRIEVAL_CONFIDENCE_THRESHOLD` | Min cosine score before escalation | `0.45` |
| `MAX_FRUSTRATED_TURNS_BEFORE_ESCALATION` | Consecutive frustrated turns before escalation | `2` |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |

## 9. Example Queries

1. `"Our production API key stopped working with a 401 Unauthorized. Can you check the logs?"`
   → **Technical Expert**, grounded in `api_authentication_troubleshooting.md`.
2. `"I've tried everything and nothing works, this is so frustrating!!"`
   → **Frustrated User**, empathetic tone, troubleshooting steps.
3. `"What's the business impact and resolution timeline for this outage?"`
   → **Business Executive**, concise, SLA-grounded answer from `sla_response_times.md`.
4. `"My billing statement has duplicate charges, I want a refund immediately!"`
   → **Escalated** (sensitive billing keyword) with a full handoff summary.
5. `"How do I clear my browser cache, the page won't load?"`
   → Grounded answer from `browser_cache_clearing.md`.

## 10. Known Limitations & Future Improvements

- Cosine similarity is computed by scanning all chunks in Python rather than using an indexed
  vector database (FAISS/Qdrant/Pinecone); this is fine for the current knowledge-base size but
  would need a real vector index (e.g. MongoDB Atlas Vector Search) at larger scale.
- Gemini's free tier has rate limits (requests per minute/day); under heavy testing you may hit
  `429` errors — wait a minute and retry, or reduce request volume. Swapping in a different
  provider (OpenAI, Claude, Ollama) is a drop-in change in `llm_client.py` if needed.
- Persona detection and escalation decisions are made independently per turn; there is no
  long-term user/sentiment memory beyond the current session's stored history.
- No authentication/authorization on the API endpoints — add this before any production exposure.
- The handoff summary's "recommendation" field uses simple keyword heuristics rather than an LLM
  call; this keeps escalation deterministic and cheap, but could be made more nuanced with an
  additional LLM summarization step.
- No automated test suite is included; manual testing via the CLI/UI and the example queries above
  is the current verification method.

## 11. Project Structure

```
persona-support-agent/
├── backend/
│   ├── app/
│   │   ├── data/                  # knowledge base (10+ docs incl. 1 PDF)
│   │   ├── main.py                # FastAPI app & routes
│   │   ├── config.py              # settings & escalation thresholds
│   │   ├── db.py                  # MongoDB connection/collections
│   │   ├── llm_client.py          # Gemini chat + embedding wrapper
│   │   ├── classifier.py          # persona detection
│   │   ├── rag_pipeline.py        # ingestion, chunking, retrieval
│   │   ├── generator.py           # persona-adaptive response generation
│   │   └── escalator.py           # escalation logic + handoff summary
│   ├── cli.py                     # CLI chatbot
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # chat UI (persona badge, sources, escalation)
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
└── README.md
```
