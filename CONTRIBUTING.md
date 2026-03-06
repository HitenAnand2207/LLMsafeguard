# Contributing to Sovereign-LLM-Guard

First off — thank you for wanting to contribute.

This is an open-source project and we welcome all contributions.

By participating in this project, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Ways to Contribute

### 1. Add a new PII detector
Edit `backend/detectors/pii_detector.py` and add a new pattern to `PII_PATTERNS`:

```python
{
    "type": "PAN_CARD",                          # Your type name
    "pattern": r'\b[A-Z]{5}\d{4}[A-Z]\b',       # Your regex
    "replacement": "[PAN_REDACTED]",             # Replacement text
    "severity": "HIGH"                           # CRITICAL / HIGH / MEDIUM / LOW
}
```

### 2. Add a new injection detection rule
Edit `backend/detectors/injection_detector.py` and add to `INJECTION_RULES`:

```python
{
    "category": "YOUR_CATEGORY",
    "patterns": [
        r"your pattern here",
    ],
    "severity": "HIGH",
    "description": "What this detects"
}
```

### 3. Add a new LLM provider
Create `backend/providers/your_provider.py`:

```python
async def call_your_provider(messages, model, temperature, max_tokens):
    # Call the API
    # Return OpenAI-compatible response format
    ...
```

Then add it to `backend/proxy/router.py`.

---

## Setup for Development

```bash
git clone https://github.com/YOUR_USERNAME/sovereign-llm-guard
cd sovereign-llm-guard/backend
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY
python main.py
```

If you are on Windows PowerShell, use:

```bash
Copy-Item .env.example .env
```

---

## Code Standards

- Python: Follow PEP8, add docstrings to all functions
- Use type hints everywhere
- Write clear commit messages: `feat: add PAN card detection`
- One PR per feature

---

## Branch Naming

Use one of these prefixes:

- `feature/<short-name>`
- `bugfix/<short-name>`
- `docs/<short-name>`
- `chore/<short-name>`

Examples:

- `feature/add-passport-pii`
- `bugfix/fix-ssn-regex`

---

## Commit Message Format

```
feat: add PAN card PII detection
fix: correct SSN regex false positives
docs: update API reference
refactor: clean up injection detector
```

---

## Reporting Issues

Before opening an issue, please check if it already exists.

When you report a bug, include:

- what you were trying to do
- what happened (include the error message if any)
- steps to reproduce
- your environment (OS, Python version, Node version if relevant)

## Suggesting Features

If you have an idea, open an issue describing:

- the problem you are trying to solve
- who it helps (and how often)
- a simple example of how you want it to work

## Pull Request Process

- Keep PRs focused (one change per PR).
- Add or update tests if your change affects behavior.
- Update docs if you changed setup, config, or API behavior.
- Make sure the project runs locally before requesting review.

## First Contribution Guide

If you are new to open source, start with a small change:

- Add a new PII pattern (one regex and a test case)
- Add an injection rule for a common pattern you have seen
- Improve error messages or documentation

Good first issues should be labeled `good first issue` (once this repo is on GitHub).

Thank you for helping make AI systems safer.
