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
