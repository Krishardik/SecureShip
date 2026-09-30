from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """
    Verify that the root endpoint works correctly.
    This test checks two things:
    1. The API returns HTTP 200.
    2. The response contains the expected message.
    """

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SecureShip is running"}


def test_create_project(client: TestClient):
    response = client.post(
        "/projects",
        json={"name": "SecureShip"},
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "SecureShip"
    assert isinstance(data["id"], int)


def test_create_project_rejects_empty_name(client: TestClient):
    response = client.post(
        "/projects",
        json={"name": ""},
    )

    assert response.status_code == 422


def test_create_project_rejects_name_over_100_characters(client: TestClient):
    response = client.post(
        "/projects",
        json={"name": "A" * 101},
    )

    assert response.status_code == 422
