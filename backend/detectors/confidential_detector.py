"""
Confidential Content Detector — Detects proprietary and sensitive business content

Two-pass approach:
  1. REDACT structured tokens  — patent numbers, crypto keys, JWTs, TLS certs.
     These have safe placeholders so redacting doesn't destroy the prompt's intent.
  2. FLAG contextual markers   — NDA language, M&A content, document classification,
     financial insider info, proprietary source code headers.
     Redacting these would break the prompt — instead we surface them in the audit log
     so engineers know what slipped through, and admins can decide to block.
"""

import re
from typing import Tuple, List, Dict


# ─── Pass 1: Structured tokens — safe to redact ───────────────────────────────

REDACTABLE_PATTERNS = [
    {
        "type": "PATENT_NUMBER",
        # Covers US, EP, WO (PCT), CN, JP grant/application numbers
        "pattern": r"\b(US\s*\d{7,8}\s*[A-Z]\d?|EP\s*\d{7}\s*[A-Z]\d?|WO\s*\d{4}\s*/\s*\d{6}|CN\s*\d{9,12}[A-Z]?|JP\s*\d{7,11}[A-Z]?)\b",
        "replacement": "[PATENT_REDACTED]",
        "severity": "HIGH",
    },
    {
        "type": "PRIVATE_KEY",
        # PEM-encoded private keys in any form
        "pattern": r"-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----[\s\S]+?-----END\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----",
        "replacement": "[PRIVATE_KEY_REDACTED]",
        "severity": "CRITICAL",
    },
    {
        "type": "TLS_CERTIFICATE",
        "pattern": r"-----BEGIN\s+CERTIFICATE-----[\s\S]+?-----END\s+CERTIFICATE-----",
        "replacement": "[CERTIFICATE_REDACTED]",
        "severity": "HIGH",
    },
    {
        "type": "JWT_TOKEN",
        # Three base64url segments separated by dots — classic JWT shape
        "pattern": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
        "replacement": "[JWT_REDACTED]",
        "severity": "CRITICAL",
    },
]


# ─── Pass 2: Contextual markers — flag but do NOT redact ─────────────────────
#
# Why not redact?  "Our acquisition target is Acme Corp" → "[REDACTED] is Acme Corp"
# is useless to the engineer AND still leaks the company name.
# Better to flag the whole message so a human reviews whether it should have been sent.

CONFIDENTIAL_MARKERS = [
    {
        "type": "DOCUMENT_CLASSIFICATION",
        "patterns": [
            r"\b(strictly\s+confidential|confidential\s+and\s+proprietary|internal\s+use\s+only)\b",
            r"\b(not\s+for\s+distribution|do\s+not\s+distribute|company\s+confidential)\b",
            r"\b(trade\s+secret|proprietary\s+information)\b",
        ],
        "severity": "HIGH",
        "description": "Document bears a confidential or proprietary classification header",
    },
    {
        "type": "NDA_RESTRICTED",
        "patterns": [
            r"\bunder\s+(?:an?\s+)?NDA\b",
            r"\bsubject\s+to\s+(?:an?\s+)?NDA\b",
            r"\bnon[\-\s]disclosure\s+agreement\b",
            r"\bbound\s+by\s+(?:an?\s+)?NDA\b",
        ],
        "severity": "HIGH",
        "description": "Content explicitly marked as NDA-restricted",
    },
    {
        "type": "FINANCIAL_RESTRICTED",
        "patterns": [
            r"\bmaterial\s+non[\-\s]public\s+information\b",
            r"\bMNPI\b",
            r"\binside(?:r)?\s+information\b",
            r"\bpre[\-\s]?IPO\b",
            r"\bundisclosed\s+financials?\b",
        ],
        "severity": "CRITICAL",
        "description": "Financially restricted or insider information",
    },
    {
        "type": "MA_STRATEGY",
        "patterns": [
            r"\bacquisition\s+target\b",
            r"\bmerger\s+(?:candidate|target|plan)\b",
            r"\bhostile\s+takeover\b",
            r"\bletter\s+of\s+intent\b",
            r"\bterm\s+sheet\b",
            r"\bdue\s+diligence\s+(?:report|findings|notes)\b",
        ],
        "severity": "CRITICAL",
        "description": "Mergers and acquisitions — highly sensitive pre-announcement content",
    },
    {
        "type": "SOURCE_CODE_IP",
        "patterns": [
            r"(?i)proprietary\s+(?:algorithm|implementation|codebase|logic)",
            r"(?i)copyright\b.{0,60}\ball\s+rights\s+reserved\b.{0,80}\bdo\s+not\s+(?:copy|distribute|share|reproduce)\b",
        ],
        "severity": "HIGH",
        "description": "Source code explicitly marked as proprietary IP",
    },
]


# ─── Public API ───────────────────────────────────────────────────────────────


def detect_confidential(text: str) -> Tuple[str, List[Dict]]:
    """
    Runs both passes and returns the sanitized text plus all findings.

    Each finding carries:
        type       — what was found
        action     — "REDACTED" | "FLAGGED"
        severity   — CRITICAL / HIGH / MEDIUM
        original   — the matched text  (only for REDACTED findings)
        description — human-readable explanation (only for FLAGGED findings)
    """
    sanitized = text
    findings: List[Dict] = []

    # Pass 1 — redact structured tokens
    for rule in REDACTABLE_PATTERNS:
        matches = list(
            re.finditer(rule["pattern"], sanitized, re.IGNORECASE | re.DOTALL)
        )
        for match in matches:
            findings.append(
                {
                    "type": rule["type"],
                    "action": "REDACTED",
                    "original": match.group()[:80],  # truncate long keys in logs
                    "severity": rule["severity"],
                }
            )
        if matches:
            sanitized = re.sub(
                rule["pattern"],
                rule["replacement"],
                sanitized,
                flags=re.IGNORECASE | re.DOTALL,
            )

    # Pass 2 — flag contextual markers
    text_lower = sanitized.lower()
    for rule in CONFIDENTIAL_MARKERS:
        for pattern in rule["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                findings.append(
                    {
                        "type": rule["type"],
                        "action": "FLAGGED",
                        "severity": rule["severity"],
                        "description": rule["description"],
                    }
                )
                break  # one finding per marker type is enough

    return sanitized, findings
