from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import tickets, webhook, settings, metrics
from app.database import init_db

app = FastAPI(title="Support Resolution Agent")

@app.on_event("startup")
def startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev/demo only — set ALLOWED_ORIGINS env var for production
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
