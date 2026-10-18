from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Project, User
from app.services.token import create_access_token


def create_user(db_session: Session, email: str) -> User:
    """Create an active user for project creation tests."""
    user = User(
        email=email,
        password_hash="not-used-in-these-tests",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_project_creation_assigns_authenticated_user_as_owner(
    client: TestClient,
    db_session: Session,
):
    user = create_user(db_session, "creator@example.com")
    token = create_access_token(user.id)

    response = client.post(
        "/projects",
        json={"name": "Security Test Project"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    body = response.json()
    assert body["name"] == "Security Test Project"
    assert body["owner_id"] == user.id
    assert isinstance(body["id"], int)

    project = db_session.query(Project).filter_by(id=body["id"]).first()
    assert project is not None
    assert project.owner_id == user.id


def test_project_creation_rejects_client_supplied_owner_id(
    client: TestClient,
    db_session: Session,
):
    user = create_user(db_session, "creator@example.com")
    another_user = create_user(db_session, "another@example.com")
    token = create_access_token(user.id)

    response = client.post(
        "/projects",
        json={
            "name": "Attempted Ownership Override",
            "owner_id": another_user.id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert db_session.query(Project).count() == 0


def test_project_creation_requires_authentication(client: TestClient):
    response = client.post(
        "/projects",
        json={"name": "Unauthenticated Project"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
