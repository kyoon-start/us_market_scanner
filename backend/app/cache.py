"""Simple thread-safe in-memory TTL cache utilities."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class CacheItem(Generic[T]):
    """One cached value with its expiry timestamp."""

    value: T
    expires_at: float


class TTLCache(Generic[T]):
    """A small reusable in-memory TTL cache for backend hot paths."""

    def __init__(self) -> None:
        self._items: dict[object, CacheItem[T]] = {}
        self._lock = threading.Lock()

    def get(self, key: object) -> T | None:
        """Return a cached value when it is still valid."""
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            if item.expires_at < time.time():
                self._items.pop(key, None)
                return None
            return item.value

    def set(self, key: object, value: T, ttl_seconds: int) -> None:
        """Store a value with a time-to-live."""
        with self._lock:
            self._items[key] = CacheItem(
                value=value,
                expires_at=time.time() + ttl_seconds,
            )

    def delete(self, key: object) -> None:
        """Remove one key when present."""
        with self._lock:
            self._items.pop(key, None)
