# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.0.x   | ✅ Yes     |
| < 1.0   | ❌ No      |

---

## Reporting a Vulnerability

If you discover a security vulnerability in Sovereign-LLM-Guard, **please do not open a public GitHub issue.**

Instead, report it privately so we can fix it before it is disclosed publicly.

**How to report:**
- Open a [GitHub Security Advisory](https://github.com/HitenAnand2207/LLMsafeguard/advisories/new) (preferred)
- Or email the maintainer directly (hiten.anand10@gmail.com)

Please include:
- A description of the vulnerability
- Steps to reproduce it
- The potential impact (what an attacker could do)
- Your environment (OS, Python version, how you are running the guard)

We will acknowledge your report within **72 hours** and aim to release a fix within **14 days** for critical issues.

---

## Scope

The following are in scope for security reports:

- **Bypass of PII detection** — a pattern that should be redacted but is not
- **Bypass of prompt injection detection** — an attack that passes through undetected
- **Authentication or authorization issues** in the API
- **Dependency vulnerabilities** in `requirements.txt` or `package.json`
- **Information disclosure** via logs, error messages, or API responses
- **SSRF** via the proxy forwarding logic

The following are out of scope:

- Attacks that require direct access to the server running the guard (if they can access your server, the guard is not your first problem)
- Issues in the Groq API itself (report those to Groq)
- False positives or false negatives in detection (open a normal issue for those)

---

## Security Design Notes

This project is a **local proxy** — it is designed to run inside your network, not exposed to the public internet. A few things to keep in mind:

- **Do not expose port 8000 publicly.** The guard has no authentication by default. It is designed to sit between your internal application and the LLM provider.
- **The audit log is in-memory.** No data is written to disk or sent anywhere. Logs are lost on restart. In production, connect it to your own database (PostgreSQL support is on the roadmap).
- **GROQ_API_KEY in `.env`** — never commit your `.env` file. It is already in `.gitignore`.
- **CORS is open by default** (`allow_origins=["*"]`). Restrict this in production to your frontend's origin only.

---

## Disclosure Policy

We follow **coordinated disclosure**:

1. You report privately
2. We confirm and fix the issue
3. We release the fix
4. We credit you in the release notes (unless you prefer to stay anonymous)

Thank you for helping keep Sovereign-LLM-Guard and its users safe.
