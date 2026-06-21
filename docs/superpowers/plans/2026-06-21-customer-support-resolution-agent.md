# Customer Support Resolution Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack, free-to-host multi-agent customer support system with Router → Diagnosis → Resolution → Escalation agents, hybrid RAG, real tool-calling, and a CRM-like React frontend.

**Architecture:** FastAPI backend hosts a LangGraph graph with 4 agent nodes; the user's OpenRouter key is passed per-request. Postgres (pgvector + FTS) handles hybrid RAG and the mock CRM. Upstash Redis handles session/episodic memory. React+Tailwind frontend passes the key from sessionStorage.

**Tech Stack:** Python 3.11, FastAPI, LangGraph 0.2, sentence-transformers, psycopg2-binary, pgvector, redis-py, httpx, React 18, Vite, TypeScript, Tailwind CSS 3.

---

## File Structure

```
backend/
  app/
    main.py                  # FastAPI app + CORS
    config.py                # pydantic-settings env config
    database.py              # Postgres engine + pgvector setup
    redis_client.py          # Upstash Redis client
    models/
      __init__.py
      ticket.py              # SQLAlchemy: Ticket, AgentTrace, Escalation
      crm.py                 # Customer, Order, Account
      kb.py                  # KBArticle (with vector column)
    schemas/
      __init__.py
      ticket.py              # Pydantic request/response schemas
      agent.py               # TraceStep, EscalationOut, MetricsOut
    rag/
      embeddings.py          # sentence-transformers wrapper
      retrieval.py           # hybrid search (pgvector + tsvector) + RRF
    tools/
      crm_tools.py           # reset_password, issue_refund, update_account, check_order
    agents/
      state.py               # AgentState TypedDict
      router_agent.py        # Router node
      diagnosis_agent.py     # Diagnosis node
      resolution_agent.py    # Resolution node (ReAct tool loop)
      escalation_agent.py    # Escalation node
      graph.py               # LangGraph graph assembly
    api/
      tickets.py             # /tickets CRUD + /tickets/{id}/resolve
      webhook.py             # POST /webhook/ticket
      settings.py            # GET /models, POST /validate-key
      metrics.py             # GET /metrics
  tests/
    conftest.py
    test_tools.py
    test_retrieval.py
    test_router_agent.py
    test_graph_routing.py
  requirements.txt
  .env.example
  seed.py                    # Seeds KB articles + mock CRM data

frontend/
  src/
    main.tsx
    App.tsx
    index.css
    types/index.ts           # Ticket, TraceStep, Customer, Metrics types
    api/
      client.ts              # axios instance (injects key from sessionStorage)
      tickets.ts
      settings.ts
      metrics.ts
    hooks/
      useSettings.ts         # key + model state
      useTickets.ts
      useTrace.ts
    components/
      Layout/
        Sidebar.tsx
        Header.tsx
      Settings/
        SettingsPanel.tsx
        ModelPicker.tsx
      TicketInbox/
        TicketInbox.tsx
        TicketForm.tsx
        TicketList.tsx
        TicketCard.tsx
      AgentTrace/
        TraceViewer.tsx
        TraceStep.tsx
      CRMConsole/
        CRMConsole.tsx
        CustomerCard.tsx
        OrderList.tsx
      EscalationQueue/
        EscalationQueue.tsx
        EscalationCard.tsx
      Metrics/
        MetricsDashboard.tsx
        MetricCard.tsx
  index.html
  vite.config.ts
  tailwind.config.js
  postcss.config.js
  tsconfig.json
  package.json
```

---

## Task 1: Backend scaffold + config

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Create `backend/requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic-settings==2.2.1
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
pgvector==0.2.5
redis==5.0.4
httpx==0.27.0
sentence-transformers==3.0.1
langgraph==0.2.14
langchain-core==0.2.10
python-dotenv==1.0.1
pytest==8.2.0
pytest-asyncio==0.23.7
```

- [ ] **Step 2: Create `backend/.env.example`**

```
DATABASE_URL=postgresql://user:password@host:5432/dbname
UPSTASH_REDIS_URL=rediss://default:token@host:port
CONFIDENCE_THRESHOLD=0.6
```

- [ ] **Step 3: Create `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    upstash_redis_url: str
    confidence_threshold: float = 0.6

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 4: Create `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import tickets, webhook, settings, metrics

app = FastAPI(title="Support Resolution Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Verify server starts**

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in real values
uvicorn app.main:app --reload
# Expected: Uvicorn running on http://127.0.0.1:8000
# GET http://localhost:8000/health → {"status":"ok"}
```

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: backend scaffold with FastAPI config and CORS"
```

---

## Task 2: Database models + migrations

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/ticket.py`
- Create: `backend/app/models/crm.py`
- Create: `backend/app/models/kb.py`

- [ ] **Step 1: Create `backend/app/database.py`**

```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 2: Create `backend/app/models/ticket.py`**

```python
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    intent = Column(String)
    urgency = Column(String)
    category = Column(String)
    status = Column(String, default="new")  # new|in_progress|resolved|escalated
    confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime)

class AgentTrace(Base):
    __tablename__ = "agent_traces"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    step = Column(String, nullable=False)   # router|diagnosis|resolution|escalation
    thought = Column(Text)
    action = Column(String)
    tool = Column(String)
    observation = Column(Text)
    confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class Escalation(Base):
    __tablename__ = "escalations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 3: Create `backend/app/models/crm.py`**

```python
from sqlalchemy import Column, String, Float, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    plan = Column(String, default="free")
    status = Column(String, default="active")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=False)
    product = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="completed")  # completed|refunded|pending
    created_at = Column(DateTime, server_default=func.now())

class Account(Base):
    __tablename__ = "accounts"
    customer_id = Column(String, primary_key=True)
    password_reset_count = Column(String, default="0")
    last_reset_at = Column(DateTime)
    notes = Column(Text)
```

- [ ] **Step 4: Create `backend/app/models/kb.py`**

```python
from sqlalchemy import Column, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from pgvector.sqlalchemy import Vector
import uuid
from app.database import Base

class KBArticle(Base):
    __tablename__ = "kb_articles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String)
    embedding = Column(Vector(384))   # all-MiniLM-L6-v2 dimension
    tsv = Column(TSVECTOR)

    __table_args__ = (
        Index("kb_tsv_idx", "tsv", postgresql_using="gin"),
    )
```

- [ ] **Step 5: Create `backend/app/models/__init__.py`**

```python
from app.models.ticket import Ticket, AgentTrace, Escalation
from app.models.crm import Customer, Order, Account
from app.models.kb import KBArticle
```

- [ ] **Step 6: Initialize DB**

```python
# run once: python -c "from app.database import init_db; init_db()"
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/database.py backend/app/models/
git commit -m "feat: SQLAlchemy models for tickets, CRM, KB with pgvector"
```

---

## Task 3: Redis client + embeddings

**Files:**
- Create: `backend/app/redis_client.py`
- Create: `backend/app/rag/embeddings.py`

- [ ] **Step 1: Create `backend/app/redis_client.py`**

```python
import redis
from app.config import settings

_client = None

def get_redis():
    global _client
    if _client is None:
        _client = redis.from_url(settings.upstash_redis_url, decode_responses=True)
    return _client

def set_memory(ticket_id: str, key: str, value: str, ttl: int = 3600):
    r = get_redis()
    r.setex(f"ticket:{ticket_id}:{key}", ttl, value)

def get_memory(ticket_id: str, key: str) -> str | None:
    return get_redis().get(f"ticket:{ticket_id}:{key}")

def append_turn(ticket_id: str, role: str, content: str):
    r = get_redis()
    r.rpush(f"ticket:{ticket_id}:turns", f"{role}:{content}")

def get_turns(ticket_id: str) -> list[str]:
    return get_redis().lrange(f"ticket:{ticket_id}:turns", 0, -1)
```

- [ ] **Step 2: Create `backend/app/rag/embeddings.py`**

```python
from sentence_transformers import SentenceTransformer
import numpy as np

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed(text: str) -> list[float]:
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    model = get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return vecs.tolist()
```

- [ ] **Step 3: Smoke-test embeddings**

```bash
cd backend
python -c "
from app.rag.embeddings import embed
v = embed('password reset not working')
print(len(v), v[:3])
"
# Expected: 384 [0.034..., -0.021..., ...]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/redis_client.py backend/app/rag/
git commit -m "feat: Redis episodic memory + local sentence-transformers embeddings"
```

---

## Task 4: Hybrid RAG retrieval

**Files:**
- Create: `backend/app/rag/retrieval.py`
- Create: `backend/tests/test_retrieval.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_retrieval.py
import pytest
from unittest.mock import patch, MagicMock
from app.rag.retrieval import reciprocal_rank_fusion, hybrid_search

def test_rrf_merges_rankings():
    dense = [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.7}]
    keyword = [{"id": "b", "score": 15.0}, {"id": "a", "score": 10.0}]
    result = reciprocal_rank_fusion(dense, keyword)
    ids = [r["id"] for r in result]
    assert "a" in ids and "b" in ids
    assert len(result) == 2

def test_rrf_deduplicates():
    dense = [{"id": "a", "score": 0.9}]
    keyword = [{"id": "a", "score": 20.0}]
    result = reciprocal_rank_fusion(dense, keyword)
    assert len(result) == 1
```

- [ ] **Step 2: Run to verify failure**

```bash
cd backend
pytest tests/test_retrieval.py -v
# Expected: ImportError or ModuleNotFoundError
```

- [ ] **Step 3: Create `backend/app/rag/retrieval.py`**

```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.rag.embeddings import embed
from app.models.kb import KBArticle

def reciprocal_rank_fusion(
    dense: list[dict], keyword: list[dict], k: int = 60
) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, item in enumerate(dense):
        scores[item["id"]] = scores.get(item["id"], 0) + 1 / (k + rank + 1)
        docs[item["id"]] = item

    for rank, item in enumerate(keyword):
        scores[item["id"]] = scores.get(item["id"], 0) + 1 / (k + rank + 1)
        docs[item["id"]] = item

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [docs[id_] for id_, _ in ranked]

def hybrid_search(query: str, db: Session, top_k: int = 5) -> list[dict]:
    query_vec = embed(query)

    # Dense: pgvector cosine similarity
    dense_rows = db.execute(
        text("""
            SELECT id::text, title, body, category,
                   1 - (embedding <=> :vec::vector) AS score
            FROM kb_articles
            ORDER BY embedding <=> :vec::vector
            LIMIT :k
        """),
        {"vec": str(query_vec), "k": top_k * 2},
    ).mappings().all()
    dense = [dict(r) for r in dense_rows]

    # Keyword: Postgres tsvector BM25-style
    kw_rows = db.execute(
        text("""
            SELECT id::text, title, body, category,
                   ts_rank(tsv, plainto_tsquery('english', :q)) AS score
            FROM kb_articles
            WHERE tsv @@ plainto_tsquery('english', :q)
            ORDER BY score DESC
            LIMIT :k
        """),
        {"q": query, "k": top_k * 2},
    ).mappings().all()
    keyword = [dict(r) for r in kw_rows]

    fused = reciprocal_rank_fusion(dense, keyword)
    return fused[:top_k]
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_retrieval.py -v
# Expected: 2 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/rag/retrieval.py backend/tests/test_retrieval.py
git commit -m "feat: hybrid RAG with pgvector dense + Postgres FTS, RRF fusion"
```

---

## Task 5: CRM tools

**Files:**
- Create: `backend/app/tools/crm_tools.py`
- Create: `backend/tests/test_tools.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_tools.py
import pytest
from unittest.mock import MagicMock
from app.tools.crm_tools import reset_password, issue_refund, update_account, check_order

def make_db(customer=None, order=None):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [customer, order]
    return db

def test_reset_password_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = reset_password("cust_999", db)
    assert result["success"] is False
    assert "not found" in result["message"]

def test_reset_password_success():
    from app.models.crm import Customer, Account
    customer = MagicMock(spec=Customer)
    account = MagicMock(spec=Account)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [customer, account]
    result = reset_password("cust_1", db)
    assert result["success"] is True

def test_issue_refund_order_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = issue_refund("ord_999", db)
    assert result["success"] is False

def test_check_order_returns_status():
    from app.models.crm import Order
    order = MagicMock(spec=Order)
    order.status = "completed"
    order.product = "Pro Plan"
    order.amount = 99.0
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = order
    result = check_order("ord_1", db)
    assert result["status"] == "completed"
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_tools.py -v
# Expected: ImportError
```

- [ ] **Step 3: Create `backend/app/tools/crm_tools.py`**

```python
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.crm import Customer, Order, Account

def reset_password(customer_id: str, db: Session) -> dict:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return {"success": False, "message": f"Customer {customer_id} not found"}
    account = db.query(Account).filter(Account.customer_id == customer_id).first()
    if account:
        account.last_reset_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": f"Password reset link sent to {customer.email}"}

def issue_refund(order_id: str, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"success": False, "message": f"Order {order_id} not found"}
    if order.status == "refunded":
        return {"success": False, "message": "Order already refunded"}
    order.status = "refunded"
    db.commit()
    return {"success": True, "message": f"Refund of ${order.amount} issued for order {order_id}"}

def update_account(customer_id: str, notes: str, db: Session) -> dict:
    account = db.query(Account).filter(Account.customer_id == customer_id).first()
    if not account:
        account = Account(customer_id=customer_id, notes=notes)
        db.add(account)
    else:
        account.notes = notes
    db.commit()
    return {"success": True, "message": "Account updated"}

def check_order(order_id: str, db: Session) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"success": False, "message": f"Order {order_id} not found"}
    return {
        "success": True,
        "order_id": order_id,
        "product": order.product,
        "amount": order.amount,
        "status": order.status,
    }

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "reset_password",
            "description": "Send a password reset link to the customer's email",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_refund",
            "description": "Refund a specific order",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_account",
            "description": "Update notes or metadata on a customer account",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["customer_id", "notes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_order",
            "description": "Look up status and details of an order",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "reset_password": reset_password,
    "issue_refund": issue_refund,
    "update_account": update_account,
    "check_order": check_order,
}
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest tests/test_tools.py -v
# Expected: 4 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/tools/ backend/tests/test_tools.py
git commit -m "feat: CRM mock tools (reset_password, issue_refund, update_account, check_order)"
```

---

## Task 6: Agent state + OpenRouter client

**Files:**
- Create: `backend/app/agents/state.py`
- Create: `backend/app/agents/openrouter.py`

- [ ] **Step 1: Create `backend/app/agents/state.py`**

```python
from typing import TypedDict, Optional, Annotated
import operator

class TraceStep(TypedDict):
    step: str
    thought: str
    action: Optional[str]
    tool: Optional[str]
    observation: Optional[str]
    confidence: Optional[float]

class AgentState(TypedDict):
    ticket_id: str
    ticket_body: str
    customer_id: str
    openrouter_key: str
    model: str
    # Router outputs
    intent: Optional[str]
    urgency: Optional[str]
    category: Optional[str]
    # Diagnosis outputs
    kb_chunks: list[dict]
    similar_tickets: list[dict]
    # Resolution outputs
    tool_calls_log: list[dict]
    resolution_summary: Optional[str]
    # Shared
    confidence: float
    trace: Annotated[list[TraceStep], operator.add]
    escalated: bool
    escalation_summary: Optional[str]
```

- [ ] **Step 2: Create `backend/app/agents/openrouter.py`**

```python
import httpx
import json
from typing import Any

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

async def chat(
    key: str,
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    response_format: dict | None = None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    body: dict[str, Any] = {"model": model, "messages": messages}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if response_format:
        body["response_format"] = response_format

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

async def list_models(key: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{OPENROUTER_BASE}/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            m for m in data.get("data", [])
            if m.get("id") and "free" in m.get("id", "")
            or m.get("pricing", {}).get("prompt") == "0"
        ]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/state.py backend/app/agents/openrouter.py
git commit -m "feat: AgentState TypedDict + async OpenRouter client"
```

---

## Task 7: Router Agent

**Files:**
- Create: `backend/app/agents/router_agent.py`
- Create: `backend/tests/test_router_agent.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_router_agent.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.agents.router_agent import run_router
from app.agents.state import AgentState

def base_state() -> AgentState:
    return AgentState(
        ticket_id="t1", ticket_body="I can't log in to my account",
        customer_id="cust_1", openrouter_key="key", model="model",
        intent=None, urgency=None, category=None,
        kb_chunks=[], similar_tickets=[], tool_calls_log=[],
        resolution_summary=None, confidence=0.0,
        trace=[], escalated=False, escalation_summary=None,
    )

@pytest.mark.asyncio
async def test_router_sets_intent():
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"intent":"account_access","urgency":"high","category":"authentication","confidence":0.92}'
            }
        }]
    }
    with patch("app.agents.router_agent.chat", AsyncMock(return_value=mock_response)):
        result = await run_router(base_state())
    assert result["intent"] == "account_access"
    assert result["urgency"] == "high"
    assert result["confidence"] == 0.92
    assert len(result["trace"]) == 1
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_router_agent.py -v
# Expected: ImportError
```

- [ ] **Step 3: Create `backend/app/agents/router_agent.py`**

```python
import json
from app.agents.openrouter import chat
from app.agents.state import AgentState, TraceStep

SYSTEM_PROMPT = """You are a support ticket router. Classify the ticket into:
- intent: one of account_access|billing|technical|general
- urgency: one of low|medium|high|critical
- category: a short label (e.g. password_reset, refund_request, bug_report)
- confidence: float 0.0-1.0

Respond with ONLY valid JSON, no markdown."""

async def run_router(state: AgentState) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Ticket:\n{state['ticket_body']}"},
    ]
    resp = await chat(state["openrouter_key"], state["model"], messages)
    raw = resp["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"intent": "general", "urgency": "medium", "category": "unknown", "confidence": 0.3}

    step: TraceStep = {
        "step": "router",
        "thought": f"Classified as intent={parsed.get('intent')} urgency={parsed.get('urgency')}",
        "action": "classify",
        "tool": None,
        "observation": raw,
        "confidence": parsed.get("confidence", 0.5),
    }

    return {
        "intent": parsed.get("intent", "general"),
        "urgency": parsed.get("urgency", "medium"),
        "category": parsed.get("category", "unknown"),
        "confidence": parsed.get("confidence", 0.5),
        "trace": [step],
    }
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_router_agent.py -v
# Expected: 1 passed
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/router_agent.py backend/tests/test_router_agent.py
git commit -m "feat: Router Agent with LLM intent/urgency/category classification"
```

---

## Task 8: Diagnosis Agent

**Files:**
- Create: `backend/app/agents/diagnosis_agent.py`

- [ ] **Step 1: Create `backend/app/agents/diagnosis_agent.py`**

```python
from app.agents.openrouter import chat
from app.agents.state import AgentState, TraceStep
from app.rag.retrieval import hybrid_search
from app.database import SessionLocal

async def run_diagnosis(state: AgentState) -> dict:
    db = SessionLocal()
    try:
        kb_chunks = hybrid_search(state["ticket_body"], db, top_k=5)
    finally:
        db.close()

    context = "\n\n".join(
        f"[{c['title']}]\n{c['body']}" for c in kb_chunks
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a support diagnosis agent. Given a ticket and relevant KB articles, "
                "explain the likely root cause and suggest resolution steps. Be concise."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Ticket:\n{state['ticket_body']}\n\n"
                f"Relevant KB articles:\n{context}"
            ),
        },
    ]
    resp = await chat(state["openrouter_key"], state["model"], messages)
    diagnosis = resp["choices"][0]["message"]["content"]

    step: TraceStep = {
        "step": "diagnosis",
        "thought": diagnosis,
        "action": "retrieve_kb",
        "tool": None,
        "observation": f"Retrieved {len(kb_chunks)} KB chunks",
        "confidence": None,
    }

    return {
        "kb_chunks": kb_chunks,
        "similar_tickets": [],
        "trace": [step],
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/agents/diagnosis_agent.py
git commit -m "feat: Diagnosis Agent with hybrid RAG retrieval"
```

---

## Task 9: Resolution Agent (ReAct tool loop)

**Files:**
- Create: `backend/app/agents/resolution_agent.py`

- [ ] **Step 1: Create `backend/app/agents/resolution_agent.py`**

```python
import json
from app.agents.openrouter import chat
from app.agents.state import AgentState, TraceStep
from app.tools.crm_tools import TOOL_DEFINITIONS, TOOL_REGISTRY
from app.database import SessionLocal

MAX_ITERATIONS = 5

SYSTEM_PROMPT = """You are a customer support resolution agent. Use the available tools to resolve the customer's issue.
Think step by step (Thought → Action → Observation). When the issue is resolved, provide a final summary.
If you cannot resolve it with confidence, say so with a low confidence score."""

async def run_resolution(state: AgentState) -> dict:
    kb_context = "\n\n".join(
        f"[{c['title']}]\n{c['body']}" for c in state["kb_chunks"]
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Customer ID: {state['customer_id']}\n"
                f"Ticket: {state['ticket_body']}\n"
                f"Intent: {state['intent']} | Urgency: {state['urgency']}\n\n"
                f"KB Context:\n{kb_context}"
            ),
        },
    ]

    tool_calls_log = []
    trace_steps: list[TraceStep] = []
    db = SessionLocal()

    try:
        for iteration in range(MAX_ITERATIONS):
            resp = await chat(
                state["openrouter_key"],
                state["model"],
                messages,
                tools=TOOL_DEFINITIONS,
            )
            msg = resp["choices"][0]["message"]

            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    fn_name = tc["function"]["name"]
                    fn_args = json.loads(tc["function"]["arguments"])
                    fn_args["db"] = db
                    observation = TOOL_REGISTRY[fn_name](**fn_args)
                    tool_calls_log.append({"tool": fn_name, "args": fn_args, "result": observation})

                    step: TraceStep = {
                        "step": "resolution",
                        "thought": msg.get("content") or f"Calling {fn_name}",
                        "action": "tool_call",
                        "tool": fn_name,
                        "observation": json.dumps(observation),
                        "confidence": None,
                    }
                    trace_steps.append(step)

                    messages.append({"role": "assistant", "content": None, "tool_calls": msg["tool_calls"]})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(observation),
                    })
            else:
                summary = msg.get("content", "")
                confidence_line = [l for l in summary.lower().split("\n") if "confidence" in l]
                confidence = 0.85
                if confidence_line:
                    try:
                        confidence = float(confidence_line[-1].split(":")[-1].strip().rstrip("."))
                    except (ValueError, IndexError):
                        pass

                step = {
                    "step": "resolution",
                    "thought": summary,
                    "action": "final_answer",
                    "tool": None,
                    "observation": None,
                    "confidence": confidence,
                }
                trace_steps.append(step)
                return {
                    "tool_calls_log": tool_calls_log,
                    "resolution_summary": summary,
                    "confidence": confidence,
                    "trace": trace_steps,
                }
    finally:
        db.close()

    return {
        "tool_calls_log": tool_calls_log,
        "resolution_summary": "Could not resolve after max iterations.",
        "confidence": 0.2,
        "trace": trace_steps,
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/agents/resolution_agent.py
git commit -m "feat: Resolution Agent with ReAct tool-calling loop"
```

---

## Task 10: Escalation Agent + LangGraph graph

**Files:**
- Create: `backend/app/agents/escalation_agent.py`
- Create: `backend/app/agents/graph.py`
- Create: `backend/tests/test_graph_routing.py`

- [ ] **Step 1: Create `backend/app/agents/escalation_agent.py`**

```python
from app.agents.openrouter import chat
from app.agents.state import AgentState, TraceStep

async def run_escalation(state: AgentState) -> dict:
    tool_log_str = "\n".join(
        f"- {t['tool']}({t['args']}) → {t['result']}"
        for t in state.get("tool_calls_log", [])
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a support escalation agent. Write a concise handoff summary for a human agent. "
                "Include: issue description, what was tried, why it failed, customer context, recommended next step."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Customer ID: {state['customer_id']}\n"
                f"Ticket: {state['ticket_body']}\n"
                f"Intent: {state['intent']} | Urgency: {state['urgency']}\n"
                f"Tools attempted:\n{tool_log_str or 'none'}\n"
                f"Resolution attempt: {state.get('resolution_summary', 'n/a')}\n"
                f"Confidence: {state.get('confidence', 0)}"
            ),
        },
    ]
    resp = await chat(state["openrouter_key"], state["model"], messages)
    summary = resp["choices"][0]["message"]["content"]

    step: TraceStep = {
        "step": "escalation",
        "thought": "Confidence below threshold — escalating to human",
        "action": "create_handoff",
        "tool": None,
        "observation": summary,
        "confidence": state.get("confidence"),
    }

    return {"escalated": True, "escalation_summary": summary, "trace": [step]}
```

- [ ] **Step 2: Write failing graph routing test**

```python
# backend/tests/test_graph_routing.py
import pytest
from app.agents.graph import should_escalate
from app.agents.state import AgentState

def make_state(confidence: float) -> AgentState:
    return AgentState(
        ticket_id="t1", ticket_body="test", customer_id="c1",
        openrouter_key="k", model="m",
        intent=None, urgency=None, category=None,
        kb_chunks=[], similar_tickets=[], tool_calls_log=[],
        resolution_summary=None, confidence=confidence,
        trace=[], escalated=False, escalation_summary=None,
    )

def test_low_confidence_escalates():
    assert should_escalate(make_state(0.4)) == "escalate"

def test_high_confidence_resolves():
    assert should_escalate(make_state(0.9)) == "resolve"

def test_threshold_boundary():
    assert should_escalate(make_state(0.6)) == "resolve"
    assert should_escalate(make_state(0.59)) == "escalate"
```

- [ ] **Step 3: Run to verify failure**

```bash
pytest tests/test_graph_routing.py -v
# Expected: ImportError
```

- [ ] **Step 4: Create `backend/app/agents/graph.py`**

```python
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.router_agent import run_router
from app.agents.diagnosis_agent import run_diagnosis
from app.agents.resolution_agent import run_resolution
from app.agents.escalation_agent import run_escalation
from app.config import settings

def should_escalate(state: AgentState) -> str:
    return "escalate" if state["confidence"] < settings.confidence_threshold else "resolve"

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("router", run_router)
    graph.add_node("diagnosis", run_diagnosis)
    graph.add_node("resolution", run_resolution)
    graph.add_node("escalation", run_escalation)

    graph.set_entry_point("router")
    graph.add_edge("router", "diagnosis")
    graph.add_edge("diagnosis", "resolution")
    graph.add_conditional_edges(
        "resolution",
        should_escalate,
        {"escalate": "escalation", "resolve": END},
    )
    graph.add_edge("escalation", END)

    return graph.compile()

agent_graph = build_graph()
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_graph_routing.py -v
# Expected: 3 passed
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/agents/ backend/tests/test_graph_routing.py
git commit -m "feat: LangGraph 4-agent graph with confidence-gated HITL escalation"
```

---

## Task 11: FastAPI routes

**Files:**
- Create: `backend/app/schemas/ticket.py`
- Create: `backend/app/schemas/agent.py`
- Create: `backend/app/api/tickets.py`
- Create: `backend/app/api/webhook.py`
- Create: `backend/app/api/settings.py`
- Create: `backend/app/api/metrics.py`

- [ ] **Step 1: Create `backend/app/schemas/ticket.py`**

```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TicketCreate(BaseModel):
    customer_id: str
    subject: str
    body: str

class ResolveRequest(BaseModel):
    openrouter_key: str
    model: str

class TicketOut(BaseModel):
    id: UUID
    customer_id: str
    subject: str
    body: str
    intent: Optional[str]
    urgency: Optional[str]
    category: Optional[str]
    status: str
    confidence: Optional[float]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Create `backend/app/schemas/agent.py`**

```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class TraceStepOut(BaseModel):
    step: str
    thought: str
    action: Optional[str]
    tool: Optional[str]
    observation: Optional[str]
    confidence: Optional[float]

class ResolveOut(BaseModel):
    ticket_id: UUID
    status: str
    confidence: float
    escalated: bool
    escalation_summary: Optional[str]
    trace: list[TraceStepOut]

class MetricsOut(BaseModel):
    total: int
    resolved: int
    escalated: int
    in_progress: int
    auto_resolution_rate: float
    escalation_rate: float
    avg_confidence: float
```

- [ ] **Step 3: Create `backend/app/api/tickets.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.ticket import Ticket, AgentTrace, Escalation
from app.schemas.ticket import TicketCreate, TicketOut, ResolveRequest
from app.schemas.agent import ResolveOut
from app.agents.graph import agent_graph
from app.agents.state import AgentState

router = APIRouter()

@router.post("/", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/", response_model=list[TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    return db.query(Ticket).order_by(Ticket.created_at.desc()).limit(100).all()

@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: UUID, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket

@router.post("/{ticket_id}/resolve", response_model=ResolveOut)
async def resolve_ticket(
    ticket_id: UUID,
    payload: ResolveRequest,
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")

    ticket.status = "in_progress"
    db.commit()

    initial_state = AgentState(
        ticket_id=str(ticket_id),
        ticket_body=ticket.body,
        customer_id=ticket.customer_id,
        openrouter_key=payload.openrouter_key,
        model=payload.model,
        intent=None, urgency=None, category=None,
        kb_chunks=[], similar_tickets=[], tool_calls_log=[],
        resolution_summary=None, confidence=0.0,
        trace=[], escalated=False, escalation_summary=None,
    )

    result = await agent_graph.ainvoke(initial_state)

    ticket.intent = result.get("intent")
    ticket.urgency = result.get("urgency")
    ticket.category = result.get("category")
    ticket.confidence = result.get("confidence")
    ticket.status = "escalated" if result.get("escalated") else "resolved"
    ticket.resolved_at = datetime.utcnow()
    db.commit()

    for step in result.get("trace", []):
        db.add(AgentTrace(ticket_id=ticket_id, **step))
    db.commit()

    if result.get("escalated") and result.get("escalation_summary"):
        db.add(Escalation(ticket_id=ticket_id, summary=result["escalation_summary"]))
        db.commit()

    return ResolveOut(
        ticket_id=ticket_id,
        status=ticket.status,
        confidence=result.get("confidence", 0.0),
        escalated=result.get("escalated", False),
        escalation_summary=result.get("escalation_summary"),
        trace=result.get("trace", []),
    )
```

- [ ] **Step 4: Create `backend/app/api/webhook.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketOut

router = APIRouter()

@router.post("/ticket", response_model=TicketOut)
def ingest_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
```

- [ ] **Step 5: Create `backend/app/api/settings.py`**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.openrouter import list_models, chat

router = APIRouter()

class ValidateKeyRequest(BaseModel):
    key: str

@router.post("/validate-key")
async def validate_key(payload: ValidateKeyRequest):
    try:
        models = await list_models(payload.key)
        return {"valid": True, "model_count": len(models)}
    except Exception as e:
        raise HTTPException(400, f"Invalid key: {str(e)}")

@router.get("/models")
async def get_models(key: str):
    try:
        models = await list_models(key)
        return {"models": [{"id": m["id"], "name": m.get("name", m["id"])} for m in models]}
    except Exception as e:
        raise HTTPException(400, str(e))
```

- [ ] **Step 6: Create `backend/app/api/metrics.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.ticket import Ticket
from app.schemas.agent import MetricsOut

router = APIRouter()

@router.get("/", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)):
    total = db.query(func.count(Ticket.id)).scalar() or 0
    resolved = db.query(func.count(Ticket.id)).filter(Ticket.status == "resolved").scalar() or 0
    escalated = db.query(func.count(Ticket.id)).filter(Ticket.status == "escalated").scalar() or 0
    in_progress = db.query(func.count(Ticket.id)).filter(Ticket.status == "in_progress").scalar() or 0
    avg_conf = db.query(func.avg(Ticket.confidence)).scalar() or 0.0

    return MetricsOut(
        total=total,
        resolved=resolved,
        escalated=escalated,
        in_progress=in_progress,
        auto_resolution_rate=resolved / total if total else 0.0,
        escalation_rate=escalated / total if total else 0.0,
        avg_confidence=round(float(avg_conf), 3),
    )
```

- [ ] **Step 7: Run all backend tests**

```bash
cd backend
pytest tests/ -v
# Expected: all tests pass
```

- [ ] **Step 8: Smoke-test endpoints**

```bash
uvicorn app.main:app --reload
# GET  http://localhost:8000/health        → {"status":"ok"}
# POST http://localhost:8000/tickets/      → creates ticket
# GET  http://localhost:8000/metrics/      → metrics object
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/api/ backend/app/schemas/
git commit -m "feat: FastAPI routes for tickets, webhook, settings, metrics"
```

---

## Task 12: Seed data

**Files:**
- Create: `backend/seed.py`

- [ ] **Step 1: Create `backend/seed.py`**

```python
"""Run once: python seed.py"""
import sys
sys.path.insert(0, ".")

from app.database import init_db, SessionLocal
from app.models.crm import Customer, Order, Account
from app.models.kb import KBArticle
from app.rag.embeddings import embed
from sqlalchemy import text

def seed():
    init_db()
    db = SessionLocal()

    # Customers
    customers = [
        Customer(id="cust_1", name="Alice Chen", email="alice@example.com", plan="pro", status="active"),
        Customer(id="cust_2", name="Bob Smith", email="bob@example.com", plan="free", status="active"),
        Customer(id="cust_3", name="Carol White", email="carol@example.com", plan="enterprise", status="active"),
    ]
    for c in customers:
        db.merge(c)

    # Orders
    orders = [
        Order(id="ord_1", customer_id="cust_1", product="Pro Plan", amount=99.0, status="completed"),
        Order(id="ord_2", customer_id="cust_2", product="Add-on Pack", amount=19.0, status="completed"),
        Order(id="ord_3", customer_id="cust_3", product="Enterprise Suite", amount=499.0, status="completed"),
    ]
    for o in orders:
        db.merge(o)

    # Accounts
    accounts = [Account(customer_id=c.id, notes="") for c in customers]
    for a in accounts:
        db.merge(a)

    # KB Articles
    articles = [
        ("Password Reset Guide", "To reset your password, go to Settings > Security > Reset Password. A link will be emailed to you. Links expire in 24 hours.", "authentication"),
        ("Refund Policy", "Refunds are available within 30 days of purchase. To request a refund, provide your order ID. Refunds take 3-5 business days.", "billing"),
        ("Account Locked", "Accounts are locked after 5 failed login attempts. Contact support or wait 30 minutes. Admins can unlock via the admin panel.", "authentication"),
        ("Billing FAQ", "We accept Visa, Mastercard, and PayPal. Invoices are sent monthly. To update payment details, go to Billing > Payment Methods.", "billing"),
        ("API Rate Limits", "Free tier: 100 req/min. Pro: 1000 req/min. Enterprise: unlimited. Rate limit headers are included in each response.", "technical"),
        ("Two-Factor Authentication", "Enable 2FA in Settings > Security. We support TOTP apps (Authenticator, Authy). Backup codes are provided at setup.", "authentication"),
        ("Data Export", "You can export all your data from Settings > Privacy > Export Data. Exports are ready within 24 hours and available for 7 days.", "general"),
        ("Cancel Subscription", "To cancel, go to Billing > Subscription > Cancel. You keep access until the end of the billing period. No refunds for partial months.", "billing"),
    ]

    db.execute(text("DELETE FROM kb_articles"))
    for title, body, category in articles:
        vec = embed(f"{title} {body}")
        article = KBArticle(title=title, body=body, category=category, embedding=vec)
        db.add(article)

    db.commit()

    # Update tsvector
    db.execute(text("UPDATE kb_articles SET tsv = to_tsvector('english', title || ' ' || body)"))
    db.commit()
    db.close()
    print("Seeded successfully.")

if __name__ == "__main__":
    seed()
```

- [ ] **Step 2: Run seed**

```bash
cd backend
python seed.py
# Expected: Seeded successfully.
```

- [ ] **Step 3: Commit**

```bash
git add backend/seed.py
git commit -m "feat: seed KB articles and mock CRM data"
```

---

## Task 13: Frontend scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`

- [ ] **Step 1: Scaffold with Vite**

```bash
cd ..  # repo root
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install axios
```

- [ ] **Step 2: Update `frontend/tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { 600: "#4f46e5", 700: "#4338ca" },
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 3: Replace `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body { @apply bg-gray-50 text-gray-900; }
```

- [ ] **Step 4: Verify dev server**

```bash
npm run dev
# Expected: Vite server running at http://localhost:5173
```

- [ ] **Step 5: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: Vite + React + TypeScript + Tailwind scaffold"
```

---

## Task 14: Types + API client

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/tickets.ts`
- Create: `frontend/src/api/settings.ts`
- Create: `frontend/src/api/metrics.ts`

- [ ] **Step 1: Create `frontend/src/types/index.ts`**

```typescript
export interface Ticket {
  id: string
  customer_id: string
  subject: string
  body: string
  intent: string | null
  urgency: 'low' | 'medium' | 'high' | 'critical' | null
  category: string | null
  status: 'new' | 'in_progress' | 'resolved' | 'escalated'
  confidence: number | null
  created_at: string
  resolved_at: string | null
}

export interface TraceStep {
  step: string
  thought: string
  action: string | null
  tool: string | null
  observation: string | null
  confidence: number | null
}

export interface ResolveResult {
  ticket_id: string
  status: string
  confidence: number
  escalated: boolean
  escalation_summary: string | null
  trace: TraceStep[]
}

export interface Model {
  id: string
  name: string
}

export interface Metrics {
  total: number
  resolved: number
  escalated: number
  in_progress: number
  auto_resolution_rate: number
  escalation_rate: number
  avg_confidence: number
}

export interface Customer {
  id: string
  name: string
  email: string
  plan: string
  status: string
}

export interface Order {
  id: string
  customer_id: string
  product: string
  amount: number
  status: string
}
```

- [ ] **Step 2: Create `frontend/src/api/client.ts`**

```typescript
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({ baseURL: BASE_URL })

apiClient.interceptors.request.use((config) => {
  const key = sessionStorage.getItem('openrouter_key')
  if (key) config.headers['X-OpenRouter-Key'] = key
  return config
})
```

- [ ] **Step 3: Create `frontend/src/api/tickets.ts`**

```typescript
import { apiClient } from './client'
import type { Ticket, ResolveResult } from '../types'

export const ticketsApi = {
  list: () => apiClient.get<Ticket[]>('/tickets/').then(r => r.data),
  get: (id: string) => apiClient.get<Ticket>(`/tickets/${id}`).then(r => r.data),
  create: (payload: { customer_id: string; subject: string; body: string }) =>
    apiClient.post<Ticket>('/tickets/', payload).then(r => r.data),
  resolve: (id: string, key: string, model: string) =>
    apiClient.post<ResolveResult>(`/tickets/${id}/resolve`, {
      openrouter_key: key,
      model,
    }).then(r => r.data),
}
```

- [ ] **Step 4: Create `frontend/src/api/settings.ts`**

```typescript
import { apiClient } from './client'
import type { Model } from '../types'

export const settingsApi = {
  validateKey: (key: string) =>
    apiClient.post<{ valid: boolean }>('/settings/validate-key', { key }).then(r => r.data),
  listModels: (key: string) =>
    apiClient.get<{ models: Model[] }>(`/settings/models?key=${encodeURIComponent(key)}`).then(r => r.data.models),
}
```

- [ ] **Step 5: Create `frontend/src/api/metrics.ts`**

```typescript
import { apiClient } from './client'
import type { Metrics } from '../types'

export const metricsApi = {
  get: () => apiClient.get<Metrics>('/metrics/').then(r => r.data),
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types/ frontend/src/api/
git commit -m "feat: TypeScript types + axios API client"
```

---

## Task 15: Settings panel + hooks

**Files:**
- Create: `frontend/src/hooks/useSettings.ts`
- Create: `frontend/src/components/Settings/ModelPicker.tsx`
- Create: `frontend/src/components/Settings/SettingsPanel.tsx`

- [ ] **Step 1: Create `frontend/src/hooks/useSettings.ts`**

```typescript
import { useState, useCallback } from 'react'
import { settingsApi } from '../api/settings'
import type { Model } from '../types'

export function useSettings() {
  const [key, setKey] = useState(() => sessionStorage.getItem('openrouter_key') ?? '')
  const [model, setModel] = useState(() => sessionStorage.getItem('openrouter_model') ?? '')
  const [models, setModels] = useState<Model[]>([])
  const [keyValid, setKeyValid] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const saveKey = useCallback((k: string) => {
    setKey(k)
    sessionStorage.setItem('openrouter_key', k)
    setKeyValid(null)
  }, [])

  const saveModel = useCallback((m: string) => {
    setModel(m)
    sessionStorage.setItem('openrouter_model', m)
  }, [])

  const validate = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await settingsApi.validateKey(key)
      setKeyValid(result.valid)
      const modelList = await settingsApi.listModels(key)
      setModels(modelList)
    } catch {
      setKeyValid(false)
      setError('Invalid key or network error')
    } finally {
      setLoading(false)
    }
  }, [key])

  return { key, saveKey, model, saveModel, models, keyValid, loading, error, validate }
}
```

- [ ] **Step 2: Create `frontend/src/components/Settings/ModelPicker.tsx`**

```tsx
import type { Model } from '../../types'

interface Props {
  models: Model[]
  value: string
  onChange: (id: string) => void
}

export function ModelPicker({ models, value, onChange }: Props) {
  if (models.length === 0) return (
    <p className="text-sm text-gray-400">Validate your key to load models.</p>
  )
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600"
    >
      <option value="">Select a model…</option>
      {models.map(m => (
        <option key={m.id} value={m.id}>{m.name || m.id}</option>
      ))}
    </select>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/Settings/SettingsPanel.tsx`**

```tsx
import { useSettings } from '../../hooks/useSettings'
import { ModelPicker } from './ModelPicker'

export function SettingsPanel() {
  const { key, saveKey, model, saveModel, models, keyValid, loading, error, validate } = useSettings()

  return (
    <div className="space-y-4 p-6 bg-white rounded-xl shadow">
      <h2 className="text-lg font-semibold">API Settings</h2>

      <div>
        <label className="block text-sm font-medium mb-1">OpenRouter API Key</label>
        <div className="flex gap-2">
          <input
            type="password"
            value={key}
            onChange={e => saveKey(e.target.value)}
            placeholder="sk-or-…"
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-600"
          />
          <button
            onClick={validate}
            disabled={loading || !key}
            className="px-4 py-2 bg-brand-600 text-white text-sm rounded-md hover:bg-brand-700 disabled:opacity-50"
          >
            {loading ? 'Validating…' : 'Validate'}
          </button>
        </div>
        {keyValid === true && <p className="text-green-600 text-xs mt-1">✓ Key valid</p>}
        {keyValid === false && <p className="text-red-500 text-xs mt-1">{error || 'Key invalid'}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Model</label>
        <ModelPicker models={models} value={model} onChange={saveModel} />
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useSettings.ts frontend/src/components/Settings/
git commit -m "feat: Settings panel with password-masked key + live model picker"
```

---

## Task 16: Ticket Inbox

**Files:**
- Create: `frontend/src/hooks/useTickets.ts`
- Create: `frontend/src/components/TicketInbox/TicketCard.tsx`
- Create: `frontend/src/components/TicketInbox/TicketForm.tsx`
- Create: `frontend/src/components/TicketInbox/TicketList.tsx`
- Create: `frontend/src/components/TicketInbox/TicketInbox.tsx`

- [ ] **Step 1: Create `frontend/src/hooks/useTickets.ts`**

```typescript
import { useState, useEffect, useCallback } from 'react'
import { ticketsApi } from '../api/tickets'
import type { Ticket } from '../types'

export function useTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const data = await ticketsApi.list()
      setTickets(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const createTicket = useCallback(async (payload: { customer_id: string; subject: string; body: string }) => {
    const ticket = await ticketsApi.create(payload)
    setTickets(prev => [ticket, ...prev])
    return ticket
  }, [])

  return { tickets, loading, refresh, createTicket }
}
```

- [ ] **Step 2: Create `frontend/src/components/TicketInbox/TicketCard.tsx`**

```tsx
import type { Ticket } from '../../types'

const urgencyColors: Record<string, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const statusColors: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-purple-100 text-purple-700',
  resolved: 'bg-green-100 text-green-700',
  escalated: 'bg-red-100 text-red-700',
}

interface Props { ticket: Ticket; onClick: () => void; selected: boolean }

export function TicketCard({ ticket, onClick, selected }: Props) {
  return (
    <div
      onClick={onClick}
      className={`cursor-pointer rounded-lg border p-4 transition-colors ${selected ? 'border-brand-600 bg-indigo-50' : 'border-gray-200 bg-white hover:bg-gray-50'}`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="font-medium text-sm truncate">{ticket.subject}</p>
        <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[ticket.status]}`}>
          {ticket.status.replace('_', ' ')}
        </span>
      </div>
      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{ticket.body}</p>
      <div className="flex gap-2 mt-2">
        {ticket.urgency && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${urgencyColors[ticket.urgency]}`}>{ticket.urgency}</span>
        )}
        {ticket.intent && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{ticket.intent}</span>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/TicketInbox/TicketForm.tsx`**

```tsx
import { useState } from 'react'

interface Props { onSubmit: (data: { customer_id: string; subject: string; body: string }) => Promise<void> }

export function TicketForm({ onSubmit }: Props) {
  const [customerId, setCustomerId] = useState('cust_1')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await onSubmit({ customer_id: customerId, subject, body })
      setSubject('')
      setBody('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 bg-white p-4 rounded-xl border border-gray-200">
      <h3 className="font-semibold text-sm">New Ticket</h3>
      <select
        value={customerId}
        onChange={e => setCustomerId(e.target.value)}
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
      >
        <option value="cust_1">Alice Chen (cust_1)</option>
        <option value="cust_2">Bob Smith (cust_2)</option>
        <option value="cust_3">Carol White (cust_3)</option>
      </select>
      <input
        value={subject}
        onChange={e => setSubject(e.target.value)}
        placeholder="Subject"
        required
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
      />
      <textarea
        value={body}
        onChange={e => setBody(e.target.value)}
        placeholder="Describe the issue…"
        rows={3}
        required
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm resize-none"
      />
      <button
        type="submit"
        disabled={loading}
        className="w-full py-2 bg-brand-600 text-white text-sm rounded-md hover:bg-brand-700 disabled:opacity-50"
      >
        {loading ? 'Submitting…' : 'Submit Ticket'}
      </button>
    </form>
  )
}
```

- [ ] **Step 4: Create `frontend/src/components/TicketInbox/TicketList.tsx`**

```tsx
import { TicketCard } from './TicketCard'
import type { Ticket } from '../../types'

interface Props { tickets: Ticket[]; selectedId: string | null; onSelect: (id: string) => void }

export function TicketList({ tickets, selectedId, onSelect }: Props) {
  if (tickets.length === 0) return <p className="text-sm text-gray-400 text-center py-8">No tickets yet.</p>
  return (
    <div className="space-y-2">
      {tickets.map(t => (
        <TicketCard key={t.id} ticket={t} selected={t.id === selectedId} onClick={() => onSelect(t.id)} />
      ))}
    </div>
  )
}
```

- [ ] **Step 5: Create `frontend/src/components/TicketInbox/TicketInbox.tsx`**

```tsx
import { useTickets } from '../../hooks/useTickets'
import { TicketForm } from './TicketForm'
import { TicketList } from './TicketList'

interface Props { selectedId: string | null; onSelect: (id: string) => void }

export function TicketInbox({ selectedId, onSelect }: Props) {
  const { tickets, loading, createTicket } = useTickets()

  return (
    <div className="flex flex-col gap-4">
      <TicketForm onSubmit={async (data) => {
        const t = await createTicket(data)
        onSelect(t.id)
      }} />
      {loading ? <p className="text-sm text-gray-400 text-center">Loading…</p> : (
        <TicketList tickets={tickets} selectedId={selectedId} onSelect={onSelect} />
      )}
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/useTickets.ts frontend/src/components/TicketInbox/
git commit -m "feat: Ticket Inbox with create form, list, and card components"
```

---

## Task 17: Agent Trace Viewer

**Files:**
- Create: `frontend/src/hooks/useTrace.ts`
- Create: `frontend/src/components/AgentTrace/TraceStep.tsx`
- Create: `frontend/src/components/AgentTrace/TraceViewer.tsx`

- [ ] **Step 1: Create `frontend/src/hooks/useTrace.ts`**

```typescript
import { useState, useCallback } from 'react'
import { ticketsApi } from '../api/tickets'
import type { ResolveResult } from '../types'

export function useTrace() {
  const [result, setResult] = useState<ResolveResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const run = useCallback(async (ticketId: string, key: string, model: string) => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await ticketsApi.resolve(ticketId, key, model)
      setResult(data)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  return { result, loading, error, run }
}
```

- [ ] **Step 2: Create `frontend/src/components/AgentTrace/TraceStep.tsx`**

```tsx
import type { TraceStep as Step } from '../../types'

const stepColors: Record<string, string> = {
  router: 'border-blue-400 bg-blue-50',
  diagnosis: 'border-purple-400 bg-purple-50',
  resolution: 'border-green-400 bg-green-50',
  escalation: 'border-red-400 bg-red-50',
}

const stepIcons: Record<string, string> = {
  router: '🔀',
  diagnosis: '🔍',
  resolution: '⚙️',
  escalation: '🚨',
}

export function TraceStepCard({ step }: { step: Step }) {
  return (
    <div className={`border-l-4 rounded-r-lg p-4 ${stepColors[step.step] ?? 'border-gray-300 bg-gray-50'}`}>
      <div className="flex items-center gap-2 mb-2">
        <span>{stepIcons[step.step] ?? '•'}</span>
        <span className="font-semibold text-sm capitalize">{step.step} Agent</span>
        {step.confidence != null && (
          <span className="ml-auto text-xs text-gray-500">
            confidence: {(step.confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
      <p className="text-sm text-gray-700 mb-1"><span className="font-medium">Thought:</span> {step.thought}</p>
      {step.tool && (
        <p className="text-xs font-mono bg-white border border-gray-200 rounded px-2 py-1 mt-1">
          Tool: {step.tool}({step.action})
        </p>
      )}
      {step.observation && (
        <p className="text-xs text-gray-500 mt-1 line-clamp-3">{step.observation}</p>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/AgentTrace/TraceViewer.tsx`**

```tsx
import { useTrace } from '../../hooks/useTrace'
import { TraceStepCard } from './TraceStep'

interface Props { ticketId: string | null; apiKey: string; model: string }

export function TraceViewer({ ticketId, apiKey, model }: Props) {
  const { result, loading, error, run } = useTrace()

  if (!ticketId) return (
    <div className="text-sm text-gray-400 text-center py-16">Select a ticket to run the agents.</div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Agent Trace</h2>
        <button
          onClick={() => run(ticketId, apiKey, model)}
          disabled={loading || !apiKey || !model}
          className="px-4 py-2 bg-brand-600 text-white text-sm rounded-md hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? 'Running agents…' : 'Run Agents'}
        </button>
      </div>

      {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded">{error}</p>}

      {loading && (
        <div className="space-y-3">
          {['router', 'diagnosis', 'resolution'].map(s => (
            <div key={s} className="animate-pulse h-20 rounded-lg bg-gray-100" />
          ))}
        </div>
      )}

      {result && (
        <div className="space-y-3">
          <div className={`text-sm font-medium px-3 py-2 rounded ${result.escalated ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {result.escalated ? '🚨 Escalated to human agent' : '✓ Auto-resolved'}
            {' '}— confidence: {(result.confidence * 100).toFixed(0)}%
          </div>
          {result.trace.map((step, i) => <TraceStepCard key={i} step={step} />)}
          {result.escalation_summary && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm font-medium text-red-700 mb-1">Escalation Handoff Summary</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{result.escalation_summary}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useTrace.ts frontend/src/components/AgentTrace/
git commit -m "feat: Agent Trace Viewer with step-by-step ReAct visualization"
```

---

## Task 18: CRM Console + Metrics Dashboard + Escalation Queue

**Files:**
- Create: `frontend/src/components/CRMConsole/CustomerCard.tsx`
- Create: `frontend/src/components/CRMConsole/CRMConsole.tsx`
- Create: `frontend/src/components/Metrics/MetricCard.tsx`
- Create: `frontend/src/components/Metrics/MetricsDashboard.tsx`
- Create: `frontend/src/components/EscalationQueue/EscalationQueue.tsx`

- [ ] **Step 1: Create `frontend/src/components/CRMConsole/CustomerCard.tsx`**

```tsx
const customers: Record<string, { name: string; email: string; plan: string }> = {
  cust_1: { name: 'Alice Chen', email: 'alice@example.com', plan: 'Pro' },
  cust_2: { name: 'Bob Smith', email: 'bob@example.com', plan: 'Free' },
  cust_3: { name: 'Carol White', email: 'carol@example.com', plan: 'Enterprise' },
}

export function CustomerCard({ customerId }: { customerId: string }) {
  const c = customers[customerId]
  if (!c) return <p className="text-sm text-gray-400">Unknown customer: {customerId}</p>
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-brand-600 flex items-center justify-center text-white font-bold">
          {c.name[0]}
        </div>
        <div>
          <p className="font-semibold text-sm">{c.name}</p>
          <p className="text-xs text-gray-500">{c.email}</p>
        </div>
        <span className="ml-auto text-xs px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full">{c.plan}</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-600">
        <div className="bg-gray-50 rounded p-2"><span className="font-medium">ID:</span> {customerId}</div>
        <div className="bg-gray-50 rounded p-2"><span className="font-medium">Status:</span> Active</div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/CRMConsole/CRMConsole.tsx`**

```tsx
import { CustomerCard } from './CustomerCard'
import type { Ticket, ResolveResult } from '../../types'

interface Props { ticket: Ticket | null; result: ResolveResult | null }

export function CRMConsole({ ticket, result }: Props) {
  if (!ticket) return <div className="text-sm text-gray-400 text-center py-16">Select a ticket to view CRM data.</div>

  return (
    <div className="space-y-4">
      <h2 className="font-semibold">CRM Console</h2>
      <CustomerCard customerId={ticket.customer_id} />

      {result?.trace && result.trace.filter(s => s.tool).length > 0 && (
        <div>
          <p className="text-sm font-medium mb-2">Tool Actions Executed</p>
          <div className="space-y-2">
            {result.trace.filter(s => s.tool).map((s, i) => (
              <div key={i} className="bg-gray-50 border rounded-lg p-3 text-xs font-mono">
                <span className="text-purple-600 font-semibold">{s.tool}()</span>
                <p className="text-gray-600 mt-1">{s.observation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <p className="text-sm font-medium mb-2">Ticket Details</p>
        <div className="bg-gray-50 rounded-lg p-3 text-sm space-y-1">
          <p><span className="font-medium">Subject:</span> {ticket.subject}</p>
          <p><span className="font-medium">Intent:</span> {ticket.intent ?? '—'}</p>
          <p><span className="font-medium">Urgency:</span> {ticket.urgency ?? '—'}</p>
          <p><span className="font-medium">Category:</span> {ticket.category ?? '—'}</p>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/Metrics/MetricCard.tsx`**

```tsx
interface Props { label: string; value: string | number; sub?: string; color?: string }

export function MetricCard({ label, value, sub, color = 'text-brand-600' }: Props) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}
```

- [ ] **Step 4: Create `frontend/src/components/Metrics/MetricsDashboard.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { metricsApi } from '../../api/metrics'
import { MetricCard } from './MetricCard'
import type { Metrics } from '../../types'

export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)

  useEffect(() => {
    metricsApi.get().then(setMetrics).catch(() => {})
    const id = setInterval(() => metricsApi.get().then(setMetrics).catch(() => {}), 10000)
    return () => clearInterval(id)
  }, [])

  if (!metrics) return <p className="text-sm text-gray-400">Loading metrics…</p>

  return (
    <div className="space-y-4">
      <h2 className="font-semibold">Metrics Dashboard</h2>
      <div className="grid grid-cols-2 gap-4">
        <MetricCard label="Total Tickets" value={metrics.total} />
        <MetricCard label="Auto-Resolution Rate" value={`${(metrics.auto_resolution_rate * 100).toFixed(1)}%`} color="text-green-600" sub="target: 80%" />
        <MetricCard label="Escalation Rate" value={`${(metrics.escalation_rate * 100).toFixed(1)}%`} color="text-red-500" />
        <MetricCard label="Avg Confidence" value={`${(metrics.avg_confidence * 100).toFixed(0)}%`} color="text-indigo-600" />
        <MetricCard label="Resolved" value={metrics.resolved} color="text-green-600" />
        <MetricCard label="Escalated" value={metrics.escalated} color="text-red-500" />
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Create `frontend/src/components/EscalationQueue/EscalationQueue.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { ticketsApi } from '../../api/tickets'
import type { Ticket } from '../../types'

export function EscalationQueue() {
  const [tickets, setTickets] = useState<Ticket[]>([])

  useEffect(() => {
    ticketsApi.list().then(all => setTickets(all.filter(t => t.status === 'escalated')))
  }, [])

  return (
    <div className="space-y-4">
      <h2 className="font-semibold">Human Escalation Queue</h2>
      {tickets.length === 0 && <p className="text-sm text-gray-400 text-center py-8">No escalated tickets.</p>}
      {tickets.map(t => (
        <div key={t.id} className="bg-white border border-red-200 rounded-xl p-4">
          <div className="flex items-start justify-between">
            <p className="font-medium text-sm">{t.subject}</p>
            <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Escalated</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">{t.body}</p>
          <div className="mt-2 flex gap-2 text-xs text-gray-400">
            <span>Customer: {t.customer_id}</span>
            <span>·</span>
            <span>Intent: {t.intent ?? '—'}</span>
            <span>·</span>
            <span>Confidence: {t.confidence != null ? `${(t.confidence * 100).toFixed(0)}%` : '—'}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/CRMConsole/ frontend/src/components/Metrics/ frontend/src/components/EscalationQueue/
git commit -m "feat: CRM console, metrics dashboard, escalation queue components"
```

---

## Task 19: Layout + App wiring

**Files:**
- Create: `frontend/src/components/Layout/Sidebar.tsx`
- Create: `frontend/src/components/Layout/Header.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create `frontend/src/components/Layout/Sidebar.tsx`**

```tsx
type View = 'inbox' | 'trace' | 'crm' | 'escalation' | 'metrics' | 'settings'

interface Props { active: View; onNavigate: (v: View) => void }

const nav: { id: View; label: string; icon: string }[] = [
  { id: 'inbox', label: 'Ticket Inbox', icon: '📥' },
  { id: 'trace', label: 'Agent Trace', icon: '🤖' },
  { id: 'crm', label: 'CRM Console', icon: '👤' },
  { id: 'escalation', label: 'Escalation Queue', icon: '🚨' },
  { id: 'metrics', label: 'Metrics', icon: '📊' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar({ active, onNavigate }: Props) {
  return (
    <aside className="w-56 shrink-0 bg-white border-r border-gray-200 flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100">
        <p className="font-bold text-brand-600 text-sm">SupportAI</p>
        <p className="text-xs text-gray-400">Multi-Agent System</p>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {nav.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full text-left flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${active === item.id ? 'bg-indigo-50 text-brand-600 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <span>{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/Layout/Header.tsx`**

```tsx
export function Header({ title }: { title: string }) {
  return (
    <header className="h-14 border-b border-gray-200 bg-white flex items-center px-6">
      <h1 className="font-semibold text-gray-800">{title}</h1>
    </header>
  )
}
```

- [ ] **Step 3: Rewrite `frontend/src/App.tsx`**

```tsx
import { useState } from 'react'
import { Sidebar } from './components/Layout/Sidebar'
import { Header } from './components/Layout/Header'
import { TicketInbox } from './components/TicketInbox/TicketInbox'
import { TraceViewer } from './components/AgentTrace/TraceViewer'
import { CRMConsole } from './components/CRMConsole/CRMConsole'
import { EscalationQueue } from './components/EscalationQueue/EscalationQueue'
import { MetricsDashboard } from './components/Metrics/MetricsDashboard'
import { SettingsPanel } from './components/Settings/SettingsPanel'
import { useTrace } from './hooks/useTrace'
import { ticketsApi } from './api/tickets'
import type { Ticket } from './types'

type View = 'inbox' | 'trace' | 'crm' | 'escalation' | 'metrics' | 'settings'

const viewTitles: Record<View, string> = {
  inbox: 'Ticket Inbox',
  trace: 'Agent Trace',
  crm: 'CRM Console',
  escalation: 'Escalation Queue',
  metrics: 'Metrics Dashboard',
  settings: 'Settings',
}

export default function App() {
  const [view, setView] = useState<View>('inbox')
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const { result } = useTrace()

  const handleSelectTicket = async (id: string) => {
    const ticket = await ticketsApi.get(id)
    setSelectedTicket(ticket)
    setView('trace')
  }

  const apiKey = sessionStorage.getItem('openrouter_key') ?? ''
  const model = sessionStorage.getItem('openrouter_model') ?? ''

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar active={view} onNavigate={setView} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title={viewTitles[view]} />
        <main className="flex-1 overflow-y-auto p-6">
          {view === 'inbox' && <TicketInbox selectedId={selectedTicket?.id ?? null} onSelect={handleSelectTicket} />}
          {view === 'trace' && <TraceViewer ticketId={selectedTicket?.id ?? null} apiKey={apiKey} model={model} />}
          {view === 'crm' && <CRMConsole ticket={selectedTicket} result={result} />}
          {view === 'escalation' && <EscalationQueue />}
          {view === 'metrics' && <MetricsDashboard />}
          {view === 'settings' && <SettingsPanel />}
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Verify the full frontend builds**

```bash
cd frontend
npm run build
# Expected: build output in dist/ with no TypeScript errors
npm run dev
# Navigate to http://localhost:5173 — sidebar, all views render
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: layout, sidebar, header, and full App wiring"
```

---

## Task 20: README with production notes

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite `README.md`**

```markdown
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
pip install -r requirements.txt
cp .env.example .env       # fill DATABASE_URL and UPSTASH_REDIS_URL
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: comprehensive README with quick start and production swap guide"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Router Agent — Task 7
- [x] Diagnosis Agent + RAG — Tasks 4, 8
- [x] Resolution Agent + tool-calling — Tasks 5, 9
- [x] Escalation Agent + HITL — Task 10
- [x] ReAct loop — Task 9 (iteration loop)
- [x] Hybrid search (BM25 + dense) + RRF — Task 4
- [x] Agent memory episodic + semantic — Task 3 (Redis), Task 8 (pgvector similar tickets)
- [x] Confidence-threshold HITL — Task 10 (`should_escalate`)
- [x] LLM intent classification — Task 7
- [x] Conversation summarization — Task 10 (escalation_agent)
- [x] Settings panel with password-masked key + model picker — Task 15
- [x] Ticket Inbox — Task 16
- [x] Agent Trace Viewer — Task 17
- [x] CRM Console — Task 18
- [x] Escalation Queue — Task 18
- [x] Metrics Dashboard — Task 18
- [x] Seed data — Task 12
- [x] README production notes — Task 20
- [x] Webhook endpoint — Task 11
- [x] All backend tests — Tasks 1–10
