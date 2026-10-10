from fastapi.testclient import TestClient


def test_cors_allows_configured_origin(client: TestClient):
    response = client.get(
        "/",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_does_not_allow_unconfigured_origin(client: TestClient):
    response = client.get(
        "/",
        headers={"Origin": "https://untrusted.example"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_allows_configured_origin(client: TestClient):
    response = client.options(
        "/users/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_untrusted_host_is_rejected(client: TestClient):
    response = client.get(
        "/",
        headers={"Host": "untrusted.example"},
    )

    assert response.status_code == 400
