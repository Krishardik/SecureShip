from fastapi.testclient import TestClient


def test_security_headers_are_present(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert (
        response.headers["Permissions-Policy"]
        == "camera=(), microphone=(), geolocation=()"
    )
    assert response.headers["Cache-Control"] == "no-store"


def test_security_headers_are_applied_to_authenticated_routes(
    client: TestClient,
):
    response = client.get("/projects/999999")

    assert response.status_code == 401

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"
