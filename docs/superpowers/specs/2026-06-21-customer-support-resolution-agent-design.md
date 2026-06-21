# Design: Automatic Customer Support Resolution Agent

**Date:** 2026-06-21
**Status:** Approved

## 1. Goal & Scope

A free-to-host, full-stack demo of a **4-agent customer-support system**. Users bring
their own OpenRouter API key (entered in the UI), submit/ingest support tickets, and watch
them flow through **Router → Diagnosis → Resolution → Escalation** with real LLM reasoning,
real hybrid RAG, and real (mock-backed) tool calls.

Every production-grade concept from the problem statement is implemented honestly; the only
substitutions are free equivalents, each documented in the README as a "swap for production"
note:

| Production (spec) | Free build | README note |
| --- | --- | --- |
| Pinecone | pgvector (in Postgres) | yes |
| Elasticsearch (BM25) | Postgres full-text search (`tsvector`) | yes |
| Salesforce / Zendesk | Mock tools backed by our Postgres "CRM" | yes |
| Grafana | In-app metrics dashboard | yes |
| Auth/SSO | None (single workspace) | yes |

Non-goals: real auth, real third-party CRM, multi-tenant scaling, fine-tuning pipeline
(documented as future work only).

## 2. Architecture

```
┌─────────────── Frontend (React + Tailwind, Vercel) ───────────────┐
│  Settings (OpenRouter key + model picker)                          │
│  Ticket Inbox  │  Agent Trace Viewer  │  CRM-like Console          │
│  Metrics Dashboard  │  Human Escalation Queue                      │
└───────────────────────────┬───────────────────────────────────────┘
                            │ REST (key passed per-request)
┌───────────────────────────▼─────── Backend (FastAPI, Render/HF) ──┐
│  LangGraph Orchestrator (ReAct loop, 4 agent nodes)                │
│  ├─ Router Agent      → LLM intent/urgency/category classification │
│  ├─ Diagnosis Agent   → Hybrid RAG (pgvector + Postgres FTS)       │
│  ├─ Resolution Agent  → Tool/function calling                      │
│  └─ Escalation Agent  → Conversation summarization + HITL handoff  │
│  Embeddings: local sentence-transformers (all-MiniLM-L6-v2)        │
│  Tools: reset_password, issue_refund, update_account, ...          │
└──────┬───────────────────────┬───────────────────────┬────────────┘
       │                       │                       │
   Postgres+pgvector       Upstash Redis          OpenRouter API
   (Supabase/Neon)         (session/memory)       (user's key)
```

## 3. Components

### Frontend (React + Tailwind)

- **Settings panel** — password-masked OpenRouter key (stored in `sessionStorage` only,
  never persisted to our DB), live model dropdown populated from OpenRouter `/models`,
  "Validate key" button, optional separate classify/resolve model selection.
- **Ticket Inbox** — new-ticket submission form + list of tickets with status badges
  (new / in-progress / resolved / escalated).
- **Agent Trace Viewer** — step-by-step ReAct trace per ticket: each agent's thought,
  tool calls, retrieved KB chunks, confidence score. Centerpiece of the demo.
- **CRM-like Console** — customer record, orders, account actions; shows what the
  Resolution Agent reads/writes.
- **Escalation Queue** — escalated tickets with the auto-generated context summary for a
  human agent.
- **Metrics Dashboard** — auto-resolution rate, escalation rate, avg latency, ticket
  volume (replaces Grafana).

### Backend (FastAPI + LangGraph)

- **LangGraph graph** with 4 agent nodes + a confidence-gated conditional edge to
  Escalation (the HITL threshold).
- **Router Agent** — LLM classifies intent / urgency / category via structured output.
- **Diagnosis Agent** — hybrid retrieval: dense (pgvector cosine) + keyword (Postgres
  `tsvector` ranking), score-fused, returns top-K KB chunks + similar past tickets
  (semantic memory).
- **Resolution Agent** — function-calling loop; tools execute real reads/writes against
  our Postgres "CRM" tables.
- **Escalation Agent** — summarizes the conversation + trace into a handoff packet, writes
  to the human queue.
- **Memory** — episodic (conversation turns in Redis/Postgres) + semantic (past tickets in
  pgvector).
- **Embeddings** — local sentence-transformers (`all-MiniLM-L6-v2`), no API cost; RAG works
  before any key is entered.

## 4. Data Model (Postgres)

- `tickets` (id, customer_id, subject, body, intent, urgency, category, status, confidence,
  created_at, resolved_at)
- `customers`, `orders`, `accounts` — the mock "CRM" the tools act on
- `kb_articles` (id, title, body, embedding `vector`, tsv `tsvector`) — hybrid search source
- `agent_traces` (ticket_id, step, agent, thought, action, tool, observation, confidence)
- `escalations` (ticket_id, summary, created_at)
- Metrics derived via aggregate queries (no separate table initially)

## 5. Key Flows

1. **Ingest** — UI form or `POST /webhook/ticket` → row in `tickets`.
2. **Run** — `POST /tickets/{id}/resolve` (carries the user's OpenRouter key + model
   selection in the request) kicks off the LangGraph run; backend returns/streams the trace.
3. **HITL gate** — if final confidence < threshold (configurable, default 0.6), route to the
   Escalation Agent instead of auto-resolving.
4. **Resolve** — tool calls mutate Postgres CRM tables; ticket marked resolved.
5. **Metrics** — dashboard queries aggregate counts/latency.

## 6. Error Handling

- Missing/invalid key → clear UI error, no run starts.
- Free-model tool-calling failure → retry once, then surface "model may not support
  tool-calling, try another" (ties to the model picker).
- OpenRouter rate-limit/timeouts → backend returns a structured error; UI shows it inline on
  the trace.
- Tool failure (e.g., refund on a nonexistent order) → agent observes the error and can
  re-plan or escalate.

## 7. Testing

- **Backend:** pytest for each tool, the hybrid-search ranking/fusion, the Router classifier
  (stubbed LLM), and the confidence-gate routing. LLM calls mocked in unit tests; one
  optional live smoke test.
- **Frontend:** component tests for Settings (key masking, model fetch) and the trace viewer
  rendering.

## 8. Free-Tier Hosting Summary

Frontend → Vercel · Backend → Render / Hugging Face Spaces · DB → Supabase / Neon (pgvector)
· Cache → Upstash Redis · LLM → user's OpenRouter key · Embeddings → local sentence-transformers.

## 9. README Production Notes

Document the production swaps: **pgvector → Pinecone**, **Postgres FTS → Elasticsearch**,
**mock tools → Salesforce/Zendesk**, **in-app metrics → Grafana**, **no-auth → SSO/auth**,
plus the future fine-tuning/feedback-loop pipeline.
