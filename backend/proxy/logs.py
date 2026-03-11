# Shared in-memory log store
# In production, swap this for PostgreSQL or MongoDB

import os
from typing import Dict, List


LOG_STORE_MAX = int(os.getenv("LOG_STORE_MAX", "1000"))
log_store: List[Dict] = []


def append_log(entry: Dict) -> None:
    """Append a log entry and keep only the newest LOG_STORE_MAX entries."""
    log_store.append(entry)
    overflow = len(log_store) - LOG_STORE_MAX
    if overflow > 0:
        del log_store[:overflow]
