"""
Simple in-memory rate limiter (per user_id).
For multi-instance deployments swap the deque-based store with Redis.
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Optional


class RateLimiter:
    """Sliding-window rate limiter."""

    def __init__(self, max_calls: int = 5, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        # user_id -> deque of timestamps
        self._calls: dict[int, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def is_allowed(self, user_id: int) -> tuple[bool, Optional[float]]:
        """
        Returns (allowed, retry_after_seconds).
        retry_after is None when allowed.
        """
        async with self._lock:
            now = time.monotonic()
            window_start = now - self.period
            q = self._calls[user_id]

            # Evict old timestamps
            while q and q[0] < window_start:
                q.popleft()

            if len(q) >= self.max_calls:
                # Oldest call is q[0]; user can retry after it expires
                retry_after = self.period - (now - q[0])
                return False, max(retry_after, 0.0)

            q.append(now)
            return True, None

    async def remaining(self, user_id: int) -> int:
        async with self._lock:
            now = time.monotonic()
            window_start = now - self.period
            q = self._calls[user_id]
            while q and q[0] < window_start:
                q.popleft()
            return max(0, self.max_calls - len(q))
