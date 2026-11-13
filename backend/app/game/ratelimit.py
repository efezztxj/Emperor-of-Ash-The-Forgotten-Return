"""Süreç içi, tek düğümlü basit hız sınırı (maliyet koruması).

Üretimde Redis veya gateway seviyesinde yapılır; burada amaç sadece
kaçak bir döngünün faturayı uçurmasını engellemek.
"""

from __future__ import annotations

import time
from collections import deque
from threading import Lock


class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self.limit = per_minute
        self._hits: deque[float] = deque()
        self._lock = Lock()

    def allow(self) -> bool:
        if self.limit <= 0:
            return True
        now = time.monotonic()
        with self._lock:
            while self._hits and now - self._hits[0] > 60:
                self._hits.popleft()
            if len(self._hits) >= self.limit:
                return False
            self._hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
