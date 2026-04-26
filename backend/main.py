"""
Sovereign-LLM-Guard — Privacy Layer for LLM APIs
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import os
import sys
from dotenv import load_dotenv
from proxy.router import router as proxy_router
from proxy.logs import clear_logs, get_logs, get_log_snapshot

# Load .env at startup — this makes GROQ_API_KEY available everywhere
load_dotenv()

REQUIRED_PYTHON = (3, 10)
if sys.version_info[:2] != REQUIRED_PYTHON:
    raise RuntimeError(
        "Sovereign-LLM-Guard requires Python 3.10. "
        f"Detected: {sys.version_info.major}.{sys.version_info.minor}."
    )


def _parse_origins(raw_origins: str) -> list[str]:
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["http://localhost:3000", "http://127.0.0.1:3000"]


APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
CORS_ALLOWED_ORIGINS = _parse_origins(
    os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    )
)
ALLOW_CREDENTIALS = "*" not in CORS_ALLOWED_ORIGINS



app = FastAPI(
    title="Sovereign-LLM-Guard",
    description="Open-source privacy proxy for LLM APIs — PII redaction & prompt injection detection",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Allow frontend dashboard to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy_router)


@app.get("/")
async def root():
    return {
        "service": "Sovereign-LLM-Guard",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "groq_api_key_configured": bool(os.getenv("GROQ_API_KEY")),
    }


@app.get("/logs")
async def list_logs(limit: int = 100, offset: int = 0):
    """Return paginated intercepted prompt logs for the dashboard."""
    return get_logs(limit=limit, offset=offset, newest_first=True)


@app.delete("/logs")
async def delete_logs():
    """Clear all in-memory logs."""
    removed = clear_logs()
    return {"deleted": removed}


@app.get("/stats")
async def get_stats():
    """Return statistics about intercepted prompts"""
    snapshot = get_log_snapshot()
    total = len(snapshot)
    redacted = sum(1 for l in snapshot if l.get("pii_detected"))
    injections = sum(1 for l in snapshot if l.get("injection_detected"))
    blocked = sum(1 for l in snapshot if l.get("blocked"))
    return {
        "total_requests": total,
        "pii_redactions": redacted,
        "injection_attempts": injections,
        "blocked_requests": blocked,
        "safe_requests": total - blocked
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)