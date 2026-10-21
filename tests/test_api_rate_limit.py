from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.api_rate_limit import (
    ApiRateLimiter,
    project_creation_api_limiter,
    registration_api_limiter,
)
from app.models import User
from app.services.token import create_access_token


def test_api_rate_limiter_allows_requests_up_to_limit():
    limiter = ApiRateLimiter(max_requests=2, window_seconds=60)

    assert limiter.check("192.0.2.1") is None
    assert limiter.check("192.0.2.1") is None

    assert limiter.check("192.0.2.1") == 60


def test_api_rate_limiter_tracks_clients_independently():
    limiter = ApiRateLimiter(max_requests=1, window_seconds=60)

    assert limiter.check("192.0.2.1") is None
    assert limiter.check("192.0.2.1") == 60
    assert limiter.check("192.0.2.2") is None


def test_api_rate_limiter_allows_requests_after_window_expires():
    now = [100.0]
    limiter = ApiRateLimiter(
        max_requests=1,
        window_seconds=10,
        clock=lambda: now[0],
    )

    assert limiter.check("192.0.2.1") is None
    assert limiter.check("192.0.2.1") == 10

    now[0] += 10

    assert limiter.check("192.0.2.1") is None


def test_api_rate_limiter_clear_resets_records():
    limiter = ApiRateLimiter(max_requests=1, window_seconds=60)

    assert limiter.check("192.0.2.1") is None
    assert limiter.check("192.0.2.1") == 60

    limiter.clear()

    assert limiter.check("192.0.2.1") is None


def test_registration_endpoint_returns_429_after_limit(
    client: TestClient,
    monkeypatch,
):
    registration_api_limiter.clear()
    monkeypatch.setattr(registration_api_limiter, "max_requests", 1)

    first_response = client.post(
        "/users/register",
        json={
            "email": "first@example.com",
            "password": "StrongPassword123!",
        },
    )
    second_response = client.post(
        "/users/register",
        json={
            "email": "second@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 429
    assert second_response.json() == {
        "detail": "Too many requests. Try again later.",
    }
    assert second_response.headers["Retry-After"] == "60"


def test_project_creation_endpoint_returns_429_after_limit(
    client: TestClient,
    db_session: Session,
    monkeypatch,
):
    project_creation_api_limiter.clear()
    monkeypatch.setattr(project_creation_api_limiter, "max_requests", 1)

    user = User(
        email="api-limit-project@example.com",
        password_hash="not-used-in-this-test",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    first_response = client.post(
        "/projects",
        json={"name": "First project"},
        headers=headers,
    )
    second_response = client.post(
        "/projects",
        json={"name": "Second project"},
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 429
    assert second_response.json() == {
        "detail": "Too many requests. Try again later.",
    }
    assert second_response.headers["Retry-After"] == "60"
