from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """
    Verify that the root endpoint works correctly.
    This test checks two things:
    1. The API returns HTTP 200.
    2. The response contains the expected message.
    """

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SecureShip is running"}
