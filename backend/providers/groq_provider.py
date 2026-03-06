"""
Groq Provider — Forwards sanitized prompts to Groq's LLM API
Groq supports: llama-3.3-70b-versatile, llama3-70b-8192, mixtral-8x7b-32768, gemma-7b-it
"""

import httpx
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load .env file — must happen before reading env vars
load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def call_groq(
    messages: List[Dict],
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> Dict:
    """
    Forward sanitized messages to Groq and return response.
    Groq's API is OpenAI-compatible so the format is identical.
    """
    # Read key fresh every call so .env changes take effect without restart
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set. "
            "Add it to backend/.env — get a free key at https://console.groq.com"
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(GROQ_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()