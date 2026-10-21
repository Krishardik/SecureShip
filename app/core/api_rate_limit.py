import math
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from app.core.config import settings


@dataclass
class RequestRecord:
    count: int
    window_started_at: float


class ApiRateLimiter:
    """Thread-safe, in-memory fixed-window limiter for API operations."""

    def __init__(
        self,
        max_requests: int,
        window_seconds: int = 60,
        clock: Callable[[], float] = time.monotonic,
    ):
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")

        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")

        self.max_requests = max_requests
        self.window_seconds = float(window_seconds)
        self._clock = clock
        self._records: dict[str, RequestRecord] = {}
        self._last_cleanup_at = clock()
        self._lock = threading.Lock()

    def _is_expired(self, record: RequestRecord, now: float) -> bool:
        return now - record.window_started_at >= self.window_seconds

    def _cleanup_expired(self, now: float) -> None:
        # Avoid scanning every client record on every request.
        if now - self._last_cleanup_at < self.window_seconds:
            return

        expired_keys = [
            key
            for key, record in self._records.items()
            if self._is_expired(record, now)
        ]

        for key in expired_keys:
            self._records.pop(key, None)

        self._last_cleanup_at = now

    def check(self, key: str) -> int | None:
        """Return Retry-After seconds when blocked, otherwise allow the request."""
        with self._lock:
            now = self._clock()
            self._cleanup_expired(now)

            record = self._records.get(key)

            if record is None or self._is_expired(record, now):
                self._records[key] = RequestRecord(
                    count=1,
                    window_started_at=now,
                )
                return None

            if record.count >= self.max_requests:
                remaining = self.window_seconds - (now - record.window_started_at)
                return max(1, math.ceil(remaining))

            record.count += 1
            return None

    def clear(self) -> None:
        """Clear records; useful for isolated tests."""
        with self._lock:
            self._records.clear()
            self._last_cleanup_at = self._clock()


registration_api_limiter = ApiRateLimiter(
    max_requests=settings.registration_rate_limit_max_requests,
    window_seconds=settings.api_rate_limit_window_seconds,
)

project_creation_api_limiter = ApiRateLimiter(
    max_requests=settings.project_creation_rate_limit_max_requests,
    window_seconds=settings.api_rate_limit_window_seconds,
)


def rate_limit_dependency(limiter: ApiRateLimiter):
    """Create a FastAPI dependency for a specific API rate limiter."""

    def enforce_rate_limit(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        retry_after = limiter.check(client_ip)

        if retry_after is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return enforce_rate_limit
