# Automatic Customer Support Resolution Agent

A multi-agent customer support system that auto-resolves 80%+ of tickets using
Router → Diagnosis → Resolution → Escalation agents with hybrid RAG and real tool-calling.

## Tech Stack (Free Build)

| Layer | Free Build | Production Equivalent |
|---|---|---|
| Agent Orchestration | LangGraph | LangGraph |
| LLM | OpenRouter (user key) | GPT-4o / Claude 3.5 Sonnet |
| Vector Search | pgvector (Postgres) | Pinecone |
| Keyword Search | Postgres FTS (tsvector) | Elasticsearch (BM25) |
| CRM Integration | Mock tools (Postgres) | Salesforce / Zendesk API |
| API Layer | FastAPI | FastAPI |
| Session/Memory | Upstash Redis | Redis |
| Database | Supabase / Neon (Postgres) | PostgreSQL (RDS) |
| Monitoring | In-app metrics dashboard | Grafana |
| Compute | Render / HF Spaces | AWS Lambda |
| Frontend | Vercel | Vercel / CloudFront |

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
source venv/bin/activate           # macOS/Linux
pip install -r requirements.txt
cp .env.example .env               # fill DATABASE_URL and UPSTASH_REDIS_URL
python -c "from app.database import init_db; init_db()"
python seed.py
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

Open http://localhost:5173 → Settings → enter your OpenRouter API key → validate → pick a model.

## Production Swap Guide

### Pinecone (replaces pgvector)
1. Create a Pinecone index with dimension=384, metric=cosine
2. Replace `app/rag/retrieval.py` dense search with Pinecone `index.query(vector=..., top_k=10)`
3. Set `PINECONE_API_KEY` and `PINECONE_INDEX` env vars

### Elasticsearch (replaces Postgres FTS)
1. Deploy Elastic Cloud or self-host OpenSearch
2. Create index with BM25 similarity for `body` field
3. Replace the `tsvector` query in `retrieval.py` with `es.search(query={"match": {"body": query}})`
4. RRF fusion logic stays unchanged

### Salesforce / Zendesk (replaces mock tools)
1. Add `simple-salesforce` or `pyzendesk` to requirements
2. Replace function bodies in `app/tools/crm_tools.py` with real API calls
3. `TOOL_DEFINITIONS` and `TOOL_REGISTRY` stay the same — no agent changes needed

### Grafana (replaces in-app metrics)
1. Add a Prometheus metrics endpoint via `prometheus-fastapi-instrumentator`
2. Point Grafana at the Prometheus scrape URL
3. Import the included dashboard template (docs/grafana-dashboard.json)

## Architecture

```
Ticket → Router Agent (intent/urgency/category)
       → Diagnosis Agent (hybrid RAG: pgvector + FTS)
       → Resolution Agent (ReAct tool loop: reset_password | issue_refund | update_account | check_order)
       → [confidence < 0.6] → Escalation Agent (human handoff summary)
```

## Concepts Implemented

- ReAct agent loop (Thought → Action → Observation)
- Hybrid search: dense (pgvector cosine) + keyword (BM25/FTS) fused with RRF
- LLM function-calling / tool use
- Episodic memory (Redis turn history) + semantic memory (past tickets in pgvector)
- Confidence-threshold HITL escalation
- LLM intent classification (structured JSON output)
- Conversation summarization for escalation handoff
