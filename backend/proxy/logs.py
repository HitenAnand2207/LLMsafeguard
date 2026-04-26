# Shared in-memory log store
# In production, swap this for PostgreSQL or MongoDB

import os
from threading import Lock
from typing import Any, Dict, List


LOG_STORE_MAX = int(os.getenv("LOG_STORE_MAX", "1000"))
log_store: List[Dict[str, Any]] = []
_log_lock = Lock()


def append_log(entry: Dict[str, Any]) -> None:
    """Append a log entry and keep only the newest LOG_STORE_MAX entries."""
    with _log_lock:
        log_store.append(entry)
        overflow = len(log_store) - LOG_STORE_MAX
        if overflow > 0:
            del log_store[:overflow]


def update_latest_log(updates: Dict[str, Any]) -> None:
    """Update the most recent log entry in a thread-safe way."""
    with _log_lock:
        if not log_store:
            return
        log_store[-1].update(updates)


def get_logs(*, limit: int = 100, offset: int = 0, newest_first: bool = True) -> Dict[str, Any]:
    """Return a paginated snapshot of logs."""
    safe_limit = max(1, min(limit, LOG_STORE_MAX))
    safe_offset = max(0, offset)

    with _log_lock:
        snapshot = list(log_store)

    if newest_first:
        snapshot = list(reversed(snapshot))

    page = snapshot[safe_offset : safe_offset + safe_limit]
    return {
        "total": len(snapshot),
        "offset": safe_offset,
        "limit": safe_limit,
        "logs": page,
    }


def clear_logs() -> int:
    """Clear all logs and return the number of removed entries."""
    with _log_lock:
        removed = len(log_store)
        log_store.clear()
    return removed


def get_log_snapshot() -> List[Dict[str, Any]]:
    """Return a thread-safe full copy of logs for aggregate calculations."""
    with _log_lock:
        return list(log_store)
