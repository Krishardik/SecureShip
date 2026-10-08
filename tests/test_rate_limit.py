from app.core.rate_limit import LoginRateLimiter


def test_rate_limiter_allows_attempts_below_limit():
    limiter = LoginRateLimiter(
        max_attempts=3,
        window_seconds=60,
    )

    assert limiter.is_blocked("192.0.2.1") is False

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is False


def test_rate_limiter_blocks_after_max_attempts():
    limiter = LoginRateLimiter(
        max_attempts=3,
        window_seconds=60,
    )

    for _ in range(3):
        limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is True


def test_rate_limiter_tracks_clients_independently():
    limiter = LoginRateLimiter(
        max_attempts=2,
        window_seconds=60,
    )

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is True
    assert limiter.is_blocked("192.0.2.2") is False


def test_rate_limiter_reset_allows_login_again():
    limiter = LoginRateLimiter(
        max_attempts=2,
        window_seconds=60,
    )

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is True

    limiter.reset("192.0.2.1")

    assert limiter.is_blocked("192.0.2.1") is False


def test_rate_limiter_clear_removes_all_records():
    limiter = LoginRateLimiter(
        max_attempts=1,
        window_seconds=60,
    )

    limiter.record_failure("192.0.2.1")
    limiter.record_failure("192.0.2.2")

    assert limiter.is_blocked("192.0.2.1") is True
    assert limiter.is_blocked("192.0.2.2") is True

    limiter.clear()

    assert limiter.is_blocked("192.0.2.1") is False
    assert limiter.is_blocked("192.0.2.2") is False
