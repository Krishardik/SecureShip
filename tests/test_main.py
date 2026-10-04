import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import User
from app.services.token import create_access_token


def create_test_user(db_session: Session) -> User:
    user = User(
        email="project-user@example.com",
        password_hash=hash_password("StrongPassword123!"),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_root_endpoint(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "SecureShip is running"}


def test_create_project_requires_authentication(
    client: TestClient,
):
    response = client.post(
        "/projects",
        json={"name": "SecureShip"},
    )

    assert response.status_code == 401


def test_create_project(client: TestClient, db_session: Session):
    user = create_test_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/projects",
        json={"name": "SecureShip"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "SecureShip"
    assert isinstance(data["id"], int)


def test_create_project_rejects_empty_name(
    client: TestClient,
    db_session: Session,
):
    user = create_test_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/projects",
        json={"name": ""},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_create_project_rejects_name_over_100_characters(
    client: TestClient,
    db_session: Session,
):
    user = create_test_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/projects",
        json={"name": "A" * 101},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_create_project_rejects_malformed_token(
    client: TestClient,
):
    response = client.post(
        "/projects",
        json={"name": "SecureShip"},
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired token",
    }


def test_create_project_rejects_token_with_wrong_signature(
    client: TestClient,
    db_session: Session,
):
    user = create_test_user(db_session)

    token = jwt.encode(
        {
            "sub": str(user.id),
        },
        "different-secret-key-32-bytes-long",
        algorithm=settings.jwt_algorithm,
    )

    response = client.post(
        "/projects",
        json={"name": "SecureShip"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired token",
    }


def test_create_project_rejects_expired_token(
    client: TestClient,
    db_session: Session,
):
    user = create_test_user(db_session)

    token = jwt.encode(
        {
            "sub": str(user.id),
            "exp": 1,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.post(
        "/projects",
        json={"name": "SecureShip"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired token",
    }


def test_create_project_rejects_inactive_user(
    client: TestClient,
    db_session: Session,
):
    user = create_test_user(db_session)

    user.is_active = False
    db_session.commit()

    token = create_access_token(user.id)

    response = client.post(
        "/projects",
        json={"name": "SecureShip"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Inactive user",
    }


def test_project_owner_can_get_project(
    client: TestClient,
    db_session: Session,
):
    user = create_test_user(db_session)
    token = create_access_token(user.id)

    create_response = client.post(
        "/projects",
        json={"name": "Owned Project"},
        headers={"Authorization": f"Bearer {token}"},
    )

    project_id = create_response.json()["id"]

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == project_id
    assert data["name"] == "Owned Project"
    assert data["owner_id"] == user.id


def test_get_project_requires_authentication(
    client: TestClient,
    db_session: Session,
):
    user = create_test_user(db_session)
    token = create_access_token(user.id)

    create_response = client.post(
        "/projects",
        json={"name": "Private Project"},
        headers={"Authorization": f"Bearer {token}"},
    )

    project_id = create_response.json()["id"]

    response = client.get(f"/projects/{project_id}")

    assert response.status_code == 401


def test_user_cannot_get_another_users_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_test_user(db_session)

    owner_token = create_access_token(owner.id)

    create_response = client.post(
        "/projects",
        json={"name": "Private Project"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    project_id = create_response.json()["id"]

    another_user = User(
        email="another-user@example.com",
        password_hash=hash_password("AnotherStrongPassword123!"),
    )

    db_session.add(another_user)
    db_session.commit()
    db_session.refresh(another_user)

    another_user_token = create_access_token(another_user.id)

    response = client.get(
        f"/projects/{project_id}",
        headers={"Authorization": f"Bearer {another_user_token}"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have access to this project",
    }


def test_get_project_returns_404_for_unknown_project(
    client: TestClient,
    db_session: Session,
):
    user = create_test_user(db_session)
    token = create_access_token(user.id)

    response = client.get(
        "/projects/99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Project not found",
    }
