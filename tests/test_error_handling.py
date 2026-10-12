from fastapi.testclient import TestClient


def test_unknown_route_returns_controlled_404(client: TestClient):
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_method_not_allowed_returns_405(client: TestClient):
    response = client.put("/users/login")

    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


def test_validation_error_does_not_expose_internal_details(
    client: TestClient,
):
    response = client.post(
        "/users/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert "detail" in body
    assert "Traceback" not in response.text
    assert "password_hash" not in response.text


def test_unknown_project_returns_generic_not_found(
    client: TestClient,
):
    response = client.get("/projects/999999")

    # Authentication is required before project lookup.
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
