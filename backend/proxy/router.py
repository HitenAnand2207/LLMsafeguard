"""
Proxy Router — intercepts requests, runs detection, forwards safe prompts to Groq
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import time
import uuid

from detectors.pii_detector import detect_and_redact_pii
from detectors.injection_detector import detect_injection
from detectors.confidential_detector import detect_confidential
from providers.groq_provider import call_groq
from proxy.logs import log_store

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = "llama-3.3-70b-versatile"
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    block_on_injection: Optional[bool] = True  # block prompt injections (default: on)
    block_on_confidential: Optional[bool] = (
        False  # block confidential content (default: warn only)
    )


class SimplePromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = "llama-3.3-70b-versatile"


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    OpenAI-compatible endpoint. Drop-in replacement.
    Intercepts, sanitizes, then forwards to Groq.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Process each message
    sanitized_messages = []
    pii_detected = False
    pii_types_found = []
    injection_detected = False
    injection_reason = ""
    confidential_detected = False
    confidential_types_found = []
    blocked = False
    block_reason = ""

    for msg in request.messages:
        if msg.role == "user":
            # Step 1: Detect and redact PII
            sanitized_content, pii_results = detect_and_redact_pii(msg.content)
            if pii_results:
                pii_detected = True
                pii_types_found.extend([r["type"] for r in pii_results])

            # Step 2: Detect prompt injection
            injection_result = detect_injection(sanitized_content)
            if injection_result["detected"]:
                injection_detected = True
                injection_reason = injection_result["reason"]
                if request.block_on_injection:
                    blocked = True
                    block_reason = "injection"

            # Step 3: Detect confidential / proprietary content
            sanitized_content, confidential_results = detect_confidential(
                sanitized_content
            )
            if confidential_results:
                confidential_detected = True
                confidential_types_found.extend(
                    [r["type"] for r in confidential_results]
                )
                if request.block_on_confidential and not blocked:
                    blocked = True
                    block_reason = "confidential"

            sanitized_messages.append({"role": msg.role, "content": sanitized_content})
        else:
            sanitized_messages.append({"role": msg.role, "content": msg.content})

    # Extract only user messages for the log (skip system prompt)
    user_original = [m.dict() for m in request.messages if m.role == "user"]
    user_sanitized = [m for m in sanitized_messages if m["role"] == "user"]

    # Log the request
    log_entry = {
        "id": request_id,
        "timestamp": time.time(),
        "original_messages": user_original,
        "sanitized_messages": user_sanitized,
        "pii_detected": pii_detected,
        "pii_types": list(set(pii_types_found)),
        "injection_detected": injection_detected,
        "injection_reason": injection_reason,
        "confidential_detected": confidential_detected,
        "confidential_types": list(set(confidential_types_found)),
        "blocked": blocked,
        "block_reason": block_reason,
        "model": request.model,
    }
    log_store.append(log_entry)

    # Block if injection or confidential content triggered a block
    if blocked:
        if block_reason == "confidential":
            block_detail = f"Confidential content detected: {', '.join(set(confidential_types_found))}"
            block_message = "Confidential or proprietary content detected"
        else:
            block_detail = injection_reason
            block_message = "Prompt injection attempt detected"

        return JSONResponse(
            status_code=403,
            content={
                "error": "Request blocked by Sovereign-LLM-Guard",
                "reason": block_message,
                "details": block_detail,
                "request_id": request_id,
            },
        )

    # Forward to Groq
    try:
        groq_response = await call_groq(
            messages=sanitized_messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        log_store[-1]["status"] = "success"
        return groq_response
    except Exception as e:
        log_store[-1]["status"] = "error"
        log_store[-1]["error"] = str(e)
        raise HTTPException(status_code=502, detail=f"LLM provider error: {str(e)}")


@router.post("/guard/inspect")
async def inspect_only(request: SimplePromptRequest):
    """
    Inspect a prompt WITHOUT forwarding to LLM.
    Logs every call so the dashboard captures PII and injection stats
    regardless of whether the caller is a demo app or a production client.
    """
    request_id = str(uuid.uuid4())[:8]

    sanitized, pii_results = detect_and_redact_pii(request.prompt)
    injection = detect_injection(sanitized)
    sanitized, confidential_results = detect_confidential(sanitized)

    blocked = injection["detected"]  # inspect always treats injection as blocked

    log_store.append(
        {
            "id": request_id,
            "timestamp": time.time(),
            "original_messages": [{"role": "user", "content": request.prompt}],
            "sanitized_messages": [{"role": "user", "content": sanitized}],
            "pii_detected": len(pii_results) > 0,
            "pii_types": list({r["type"] for r in pii_results}),
            "injection_detected": injection["detected"],
            "injection_reason": injection.get("reason", ""),
            "confidential_detected": len(confidential_results) > 0,
            "confidential_types": list({r["type"] for r in confidential_results}),
            "blocked": blocked,
            "block_reason": "injection" if blocked else "",
            "model": request.model,
            "status": "inspect",
        }
    )

    return {
        "request_id": request_id,
        "original": request.prompt,
        "sanitized": sanitized,
        "pii_detected": len(pii_results) > 0,
        "pii_findings": pii_results,
        "injection_detected": injection["detected"],
        "injection_details": injection,
        "confidential_detected": len(confidential_results) > 0,
        "confidential_findings": confidential_results,
        "safe_to_send": not injection["detected"],
    }
