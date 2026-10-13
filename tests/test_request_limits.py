from fastapi.testclient import TestClient

from app.core.request_limits import RequestSizeLimitMiddleware


def test_request_size_limit_rejects_non_positive_limit():
    async def dummy_app(scope, receive, send):
        return None

    try:
        RequestSizeLimitMiddleware(dummy_app, max_body_bytes=0)
    except ValueError as exc:
        assert str(exc) == "max_body_bytes must be positive"
    else:
        raise AssertionError("Expected non-positive limit to be rejected")


def test_oversized_request_is_rejected(client: TestClient):
    response = client.post(
        "/users/register",
        content=b"x" * (1_048_576 + 1),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}


def test_invalid_content_length_is_rejected(client: TestClient):
    response = client.post(
        "/users/register",
        content=b'{"email":"body@example.com","password":"StrongPassword123!"}',
        headers={
            "Content-Type": "application/json",
            "Content-Length": "-1",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Content-Length header"}
