import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import User


def create_test_user(db_session: Session) -> str:
    user = User(
        email="project-user@example.com",
        password_hash=hash_password("StrongPassword123!"),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = jwt.encode(
        {"sub": str(user.id)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token


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


def test_create_project(
    client: TestClient,
    db_session: Session,
):
    token = create_test_user(db_session)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "SecureShip"},
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "SecureShip"
    assert isinstance(data["id"], int)


def test_create_project_rejects_empty_name(
    client: TestClient,
    db_session: Session,
):
    token = create_test_user(db_session)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": ""},
    )

    assert response.status_code == 422


def test_create_project_rejects_name_over_100_characters(
    client: TestClient,
    db_session: Session,
):
    token = create_test_user(db_session)

    response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "A" * 101},
    )

    assert response.status_code == 422


def test_create_project_requires_authentication(client: TestClient):
    response = client.post(
        "/projects",
        json={"name": "SecureShip"},
    )

    assert response.status_code == 401
