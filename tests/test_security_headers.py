"""Regression tests for HTTP security response headers."""

from fastapi.testclient import TestClient


def test_security_headers_are_present_on_api_responses(client: TestClient):
    response = client.get("/projects")

    # The endpoint requires authentication, but its error response must
    # still receive the application's security headers.
    assert response.status_code == 401

    headers = response.headers

    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "referrer-policy" in headers
    assert "content-security-policy" in headers


def test_security_headers_are_present_on_not_found_responses(
    client: TestClient,
):
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
