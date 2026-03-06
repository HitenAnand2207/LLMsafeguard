"""
Prompt Injection Detector — Detects attempts to hijack LLM behavior
Categories: Direct injection, Jailbreak, Data exfiltration, Role confusion
"""

import re
from typing import Dict, List

# ─── Injection Signatures ─────────────────────────────────────────────────────

INJECTION_RULES = [
    # Direct instruction override
    {
        "category": "INSTRUCTION_OVERRIDE",
        "patterns": [
            r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?",
            r"disregard\s+(your\s+)?(previous|prior|above|earlier)\s+instructions?",
            r"forget\s+(everything|all)\s+(you\s+)?(were\s+)?(told|instructed|trained)",
            r"forget\s+everything\s+and\s+(write|respond|answer|act|do|say)",
            r"override\s+(your\s+)?(previous|prior)?\s*(instructions?|rules?|guidelines?)",
            r"do not\s+follow\s+your\s+(previous\s+)?instructions?",
            r"(write|respond|answer|act)\s+(only\s+)?according\s+to\s+(me|my\s+(instructions?|rules?|wishes?))",
        ],
        "severity": "CRITICAL",
        "description": "Attempts to override system instructions",
    },
    # System prompt extraction
    {
        "category": "SYSTEM_PROMPT_LEAK",
        "patterns": [
            r"reveal\s+(your\s+)?(system\s+prompt|instructions?|guidelines?)",
            r"show\s+me\s+(your\s+)?(system\s+prompt|hidden\s+instructions?)",
            r"what\s+(are\s+)?(your\s+)?(system\s+)?(instructions?|prompt|guidelines?)",
            r"print\s+(your\s+)?system\s+prompt",
            r"repeat\s+(your\s+)?(original\s+)?instructions?\s+(back\s+to\s+me)?",
            r"output\s+(your\s+)?(initial\s+)?prompt",
        ],
        "severity": "HIGH",
        "description": "Attempts to extract system prompt",
    },
    # Role/persona hijacking
    {
        "category": "ROLE_HIJACK",
        "patterns": [
            r"you\s+are\s+now\s+(a\s+)?(DAN|jailbreak|hacker|unrestricted)",
            r"pretend\s+(you\s+)?(are|have\s+no)\s+(restrictions?|guidelines?|rules?)",
            r"act\s+as\s+(if\s+you\s+(have\s+no|are\s+without)\s+(rules?|restrictions?|guidelines?))",
            r"you\s+(must|should)\s+(now\s+)?(ignore|forget)\s+(your\s+)?(training|restrictions?|guidelines?)",
            r"(jailbreak|DAN|unrestricted\s+mode|developer\s+mode|god\s+mode)",
            r"from\s+now\s+on\s+you\s+(will|must|should)\s+not\s+(follow|obey)",
            # Broader forget/no restrictions patterns
            r"forget\s+(your\s+)?(guidelines?|rules?|restrictions?|training|instructions?|limits?)",
            r"you\s+have\s+no\s+(restrictions?|guidelines?|rules?|limits?|boundaries)",
            r"(no\s+restrictions?|no\s+guidelines?|no\s+rules?|no\s+limits?|no\s+boundaries)",
            r"(remove|drop|disable|bypass|override)\s+(your\s+)?(restrictions?|guidelines?|rules?|limits?|filters?)",
            r"you\s+(can|are\s+allowed\s+to|must|should)\s+(now\s+)?(do\s+anything|say\s+anything|answer\s+anything)",
            r"(free\s+yourself|liberate\s+yourself)\s+from\s+(your\s+)?(restrictions?|guidelines?|rules?)",
            r"(act|behave|respond)\s+(as\s+if\s+you\s+(have\s+no|are\s+without|don.t\s+have)\s+(restrictions?|rules?|guidelines?))",
        ],
        "severity": "CRITICAL",
        "description": "Attempts to hijack LLM role or persona",
    },
    # Data exfiltration
    {
        "category": "DATA_EXFILTRATION",
        "patterns": [
            r"send\s+(me|the\s+user)?\s*(all\s+)?(database\s+)?(passwords?|credentials?|secrets?)",
            r"exfiltrate\s+(data|information|credentials?)",
            r"extract\s+(and\s+send)?\s*(all\s+)?(user\s+)?(data|information|passwords?)",
            r"dump\s+(the\s+)?(database|all\s+data|user\s+data)",
            # Credential fishing
            r"tell\s+me\s+(the\s+)?(admin|root|master|super)\s+(password|credentials?|key|secret)",
            r"what\s+is\s+(the\s+)?(admin|root|master)\s+(password|key|secret)",
            r"give\s+me\s+(the\s+)?(admin|root|system|master)\s+(password|access|credentials?)",
        ],
        "severity": "CRITICAL",
        "description": "Attempts to extract or exfiltrate data",
    },
    # Indirect/encoded injection
    {
        "category": "ENCODED_INJECTION",
        "patterns": [
            r"base64\s+decode\s+.*\s+and\s+execute",
            r"eval\s*\(.*\)",
            r"exec\s*\(.*\)",
            r"<\s*script[^>]*>",
            r"\{\{.*\}\}",  # template injection
        ],
        "severity": "HIGH",
        "description": "Encoded or indirect injection attempt",
    },
    # Manipulation tactics
    {
        "category": "MANIPULATION",
        "patterns": [
            r"(my\s+)?(boss|manager|ceo|anthropic|openai)\s+(said|told|authorized|approved)\s+(you\s+)?(to|can)",
            r"you\s+(have\s+)?(special|admin|root|sudo)\s+(access|permissions?|privileges?)",
            r"this\s+is\s+a\s+(test|simulation|hypothetical)\s+so\s+(you\s+can|rules\s+don.t\s+apply)",
        ],
        "severity": "MEDIUM",
        "description": "Social engineering / authority manipulation",
    },
]


def detect_injection(text: str) -> Dict:
    """
    Scans text for prompt injection patterns.

    Returns:
        {
            "detected": bool,
            "reason": str,
            "findings": list,
            "highest_severity": str
        }
    """
    findings = []
    text_lower = text.lower()

    for rule in INJECTION_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                findings.append(
                    {
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "pattern_matched": pattern,
                    }
                )
                break  # one match per rule category is enough

    if not findings:
        return {
            "detected": False,
            "reason": "",
            "findings": [],
            "highest_severity": "NONE",
        }

    # Determine highest severity
    severity_rank = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
    highest = max(findings, key=lambda x: severity_rank.get(x["severity"], 0))

    categories = list(set([f["category"] for f in findings]))
    reason = f"Detected: {', '.join(categories)}"

    return {
        "detected": True,
        "reason": reason,
        "findings": findings,
        "highest_severity": highest["severity"],
    }
