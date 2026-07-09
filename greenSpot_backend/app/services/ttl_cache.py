"""간단한 프로세스 내 TTL 캐시 (외부 API 응답 공용)."""
from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

# key -> (expires_at, value)
_STORE: Dict[str, Tuple[float, Any]] = {}


def cache_get(key: str) -> Optional[Any]:
    item = _STORE.get(key)
    if item is None:
        return None
    expires_at, value = item
    if time.monotonic() > expires_at:
        _STORE.pop(key, None)
        return None
    return value


def cache_set(key: str, value: Any, ttl_sec: float = 600.0) -> None:
    _STORE[key] = (time.monotonic() + max(1.0, ttl_sec), value)


def cache_clear() -> None:
    _STORE.clear()
