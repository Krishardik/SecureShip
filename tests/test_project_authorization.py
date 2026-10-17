from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Project, User
from app.services.token import create_access_token


def create_user(db_session: Session, email: str) -> User:
    """Create an active user for authorization tests."""
    user = User(
        email=email,
        password_hash="not-used-in-these-authorization-tests",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_project_owner_can_access_their_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "owner@example.com")
    project = Project(name="Owner project", owner_id=owner.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    token = create_access_token(owner.id)
    response = client.get(
        f"/projects/{project.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == project.id
    assert response.json()["name"] == "Owner project"
    assert response.json()["owner_id"] == owner.id


def test_user_cannot_access_another_users_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "owner@example.com")
    other_user = create_user(db_session, "other@example.com")

    project = Project(name="Private project", owner_id=owner.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    token = create_access_token(other_user.id)
    response = client.get(
        f"/projects/{project.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


def test_user_cannot_access_nonexistent_project(
    client: TestClient,
    db_session: Session,
):
    user = create_user(db_session, "user@example.com")
    token = create_access_token(user.id)

    response = client.get(
        "/projects/999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
