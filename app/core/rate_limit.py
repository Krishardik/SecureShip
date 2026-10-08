from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class AttemptRecord:
    count: int
    window_started_at: datetime


class LoginRateLimiter:
    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 60,
    ):
        self.max_attempts = max_attempts
        self.window = timedelta(seconds=window_seconds)
        self._attempts: dict[str, AttemptRecord] = {}

    def is_blocked(self, key: str) -> bool:
        record = self._attempts.get(key)

        if record is None:
            return False

        now = datetime.now(timezone.utc)

        if now - record.window_started_at >= self.window:
            self._attempts.pop(key, None)
            return False

        return record.count >= self.max_attempts

    def record_failure(self, key: str) -> None:
        now = datetime.now(timezone.utc)
        record = self._attempts.get(key)

        if record is None or now - record.window_started_at >= self.window:
            self._attempts[key] = AttemptRecord(
                count=1,
                window_started_at=now,
            )
            return

        record.count += 1

    def reset(self, key: str) -> None:
        self._attempts.pop(key, None)

    def clear(self) -> None:
        self._attempts.clear()


login_rate_limiter = LoginRateLimiter()
