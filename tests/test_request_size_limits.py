"""Regression tests for request body size limits."""

from fastapi.testclient import TestClient

MAX_BODY_BYTES = 1_048_576


def test_oversized_request_body_is_rejected(client: TestClient):
    oversized_body = b"x" * (MAX_BODY_BYTES + 1)

    response = client.request(
        "POST",
        "/projects",
        content=oversized_body,
        headers={"Content-Type": "application/octet-stream"},
    )

    assert response.status_code == 413


def test_normal_health_request_is_not_rejected(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
