"""
Sovereign-LLM-Guard — Privacy Layer for LLM APIs
Main FastAPI application entry point
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
from dotenv import load_dotenv
from proxy.router import router as proxy_router
from proxy.logs import log_store

# Load .env at startup — this makes GROQ_API_KEY available everywhere
load_dotenv()



app = FastAPI(
    title="Sovereign-LLM-Guard",
    description="Open-source privacy proxy for LLM APIs — PII redaction & prompt injection detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Allow frontend dashboard to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy_router)


@app.get("/")
async def root():
    return {
        "service": "Sovereign-LLM-Guard",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/logs")
async def get_logs():
    """Return all intercepted prompt logs for the dashboard"""
    return {"logs": log_store}


@app.get("/stats")
async def get_stats():
    """Return statistics about intercepted prompts"""
    total = len(log_store)
    redacted = sum(1 for l in log_store if l.get("pii_detected"))
    injections = sum(1 for l in log_store if l.get("injection_detected"))
    blocked = sum(1 for l in log_store if l.get("blocked"))
    return {
        "total_requests": total,
        "pii_redactions": redacted,
        "injection_attempts": injections,
        "blocked_requests": blocked,
        "safe_requests": total - blocked
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)