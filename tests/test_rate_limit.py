import pytest

from app.core.rate_limit import LoginRateLimiter


def test_rate_limiter_allows_attempts_below_limit():
    limiter = LoginRateLimiter(max_attempts=3, window_seconds=60)

    assert limiter.is_blocked("192.0.2.1") is False

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is False


def test_rate_limiter_blocks_after_max_attempts():
    limiter = LoginRateLimiter(max_attempts=3, window_seconds=60)

    for _ in range(3):
        limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is True


def test_rate_limiter_tracks_clients_independently():
    limiter = LoginRateLimiter(max_attempts=2, window_seconds=60)

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is True
    assert limiter.is_blocked("192.0.2.2") is False


def test_rate_limiter_reset_allows_login_again():
    limiter = LoginRateLimiter(max_attempts=2, window_seconds=60)

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is True

    limiter.reset("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is False


def test_rate_limiter_clear_removes_all_records():
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=60)

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.2")

    assert limiter.is_blocked("192.0.2.1") is True
    assert limiter.is_blocked("192.0.2.2") is True

    limiter.clear()

    assert limiter.is_blocked("192.0.2.1") is False
    assert limiter.is_blocked("192.0.2.2") is False


def test_rate_limiter_allows_attempts_after_window_expires():
    now = [100.0]
    limiter = LoginRateLimiter(
        max_attempts=2,
        window_seconds=60,
        clock=lambda: now[0],
    )

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is True

    now[0] += 60

    assert limiter.is_blocked("192.0.2.1") is False


def test_expired_window_starts_a_new_attempt_count():
    now = [100.0]
    limiter = LoginRateLimiter(
        max_attempts=3,
        window_seconds=60,
        clock=lambda: now[0],
    )

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.1")

    now[0] += 60
    limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is False


def test_rate_limiter_periodically_removes_expired_records():
    now = [100.0]
    limiter = LoginRateLimiter(
        max_attempts=2,
        window_seconds=10,
        cleanup_interval_seconds=5,
        clock=lambda: now[0],
    )

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.2")

    assert len(limiter._attempts) == 2

    now[0] += 10

    # Trigger cleanup with another client operation.
    limiter.record_failure("192.0.2.3")

    assert "192.0.2.1" not in limiter._attempts
    assert "192.0.2.2" not in limiter._attempts
    assert "192.0.2.3" in limiter._attempts


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_attempts": 0}, "max_attempts"),
        ({"window_seconds": 0}, "window_seconds"),
        ({"cleanup_interval_seconds": 0}, "cleanup_interval_seconds"),
    ],
)
def test_rate_limiter_rejects_invalid_configuration(kwargs, message):
    with pytest.raises(ValueError, match=message):
        LoginRateLimiter(**kwargs)
