"""
PII Detector — Detects and redacts Personally Identifiable Information
Supports: Email, Phone, SSN, Credit Card, Aadhaar, API Keys, IP addresses, Names patterns
"""

import re
from typing import Tuple, List, Dict

# ─── PII Patterns ────────────────────────────────────────────────────────────

PII_PATTERNS = [
    {
        "type": "EMAIL",
        "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "replacement": "[EMAIL_REDACTED]",
        "severity": "HIGH"
    },
    {
        "type": "PHONE_NUMBER",
        "pattern": r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
        "replacement": "[PHONE_REDACTED]",
        "severity": "HIGH"
    },
    {
        "type": "SSN",
        "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
        "replacement": "[SSN_REDACTED]",
        "severity": "CRITICAL"
    },
    {
        "type": "CREDIT_CARD",
        "pattern": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        "replacement": "[CREDIT_CARD_REDACTED]",
        "severity": "CRITICAL"
    },
    {
        "type": "AADHAAR",
        "pattern": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
        "replacement": "[AADHAAR_REDACTED]",
        "severity": "CRITICAL"
    },
    {
        "type": "API_KEY",
        "pattern": r'\b(sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z-_]{35}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|gsk_[a-zA-Z0-9]{52})\b',
        "replacement": "[API_KEY_REDACTED]",
        "severity": "CRITICAL"
    },
    {
        "type": "IP_ADDRESS",
        "pattern": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        "replacement": "[IP_REDACTED]",
        "severity": "MEDIUM"
    },
    {
        "type": "DATE_OF_BIRTH",
        "pattern": r'\b(DOB|date of birth|born on)[:\s]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        "replacement": "[DOB_REDACTED]",
        "severity": "HIGH"
    },
    {
        "type": "PASSPORT",
        "pattern": r'\b[A-Z]{1,2}\d{6,9}\b',
        "replacement": "[PASSPORT_REDACTED]",
        "severity": "CRITICAL"
    },
    {
        "type": "BANK_ACCOUNT",
        "pattern": r'\b\d{9,18}\b(?=.*\b(account|IFSC|bank)\b)',
        "replacement": "[BANK_ACCOUNT_REDACTED]",
        "severity": "CRITICAL"
    },
    {
        "type": "PASSWORD",
        "pattern": r'(?i)(password|passwd|pwd)\s*[=:]\s*\S+',
        "replacement": "[PASSWORD_REDACTED]",
        "severity": "CRITICAL"
    },
]


def detect_and_redact_pii(text: str) -> Tuple[str, List[Dict]]:
    """
    Scans text for PII, redacts it, and returns results.

    Returns:
        (sanitized_text, list_of_findings)
    """
    sanitized = text
    findings = []

    for rule in PII_PATTERNS:
        matches = list(re.finditer(rule["pattern"], sanitized, re.IGNORECASE))
        for match in matches:
            findings.append({
                "type": rule["type"],
                "original": match.group(),
                "start": match.start(),
                "end": match.end(),
                "severity": rule["severity"]
            })

        # Replace in text
        sanitized = re.sub(
            rule["pattern"],
            rule["replacement"],
            sanitized,
            flags=re.IGNORECASE
        )

    return sanitized, findings


def get_pii_summary(findings: List[Dict]) -> Dict:
    """Return a summary of PII types found"""
    summary = {}
    for f in findings:
        t = f["type"]
        summary[t] = summary.get(t, 0) + 1
    return summary
