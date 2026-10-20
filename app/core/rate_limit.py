import threading
import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class AttemptRecord:
    count: int
    window_started_at: float


class LoginRateLimiter:
    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 60,
        cleanup_interval_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        if cleanup_interval_seconds <= 0:
            raise ValueError("cleanup_interval_seconds must be positive")

        self.max_attempts = max_attempts
        self.window_seconds = float(window_seconds)
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._clock = clock

        self._attempts: dict[str, AttemptRecord] = {}
        self._last_cleanup_at = clock()
        self._lock = threading.Lock()

    def _is_expired(self, record: AttemptRecord, now: float) -> bool:
        return now - record.window_started_at >= self.window_seconds

    def _cleanup_expired(self, now: float) -> None:
        """Remove expired client records periodically to limit stale state."""
        if now - self._last_cleanup_at < self.cleanup_interval_seconds:
            return

        expired_keys = [
            key
            for key, record in self._attempts.items()
            if self._is_expired(record, now)
        ]

        for key in expired_keys:
            self._attempts.pop(key, None)

        self._last_cleanup_at = now

    def is_blocked(self, key: str) -> bool:
        with self._lock:
            now = self._clock()
            self._cleanup_expired(now)

            record = self._attempts.get(key)

            if record is None:
                return False

            if self._is_expired(record, now):
                self._attempts.pop(key, None)
                return False

            return record.count >= self.max_attempts

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            self._cleanup_expired(now)

            record = self._attempts.get(key)

            if record is None or self._is_expired(record, now):
                self._attempts[key] = AttemptRecord(
                    count=1,
                    window_started_at=now,
                )
                return

            record.count += 1

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()
            self._last_cleanup_at = self._clock()


login_rate_limiter = LoginRateLimiter()
