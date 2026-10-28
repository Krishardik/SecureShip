"""Regression tests for cross-user project access and IDOR prevention."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Project, User
from app.services.token import create_access_token


def create_user(db_session: Session, email: str) -> User:
    user = User(
        email=email,
        password_hash="not-used-in-this-test",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_project(
    db_session: Session,
    owner: User,
    name: str,
) -> Project:
    project = Project(name=name, owner_id=owner.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def test_user_cannot_read_another_users_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "idor-owner-read@example.com")
    other_user = create_user(db_session, "idor-other-read@example.com")
    project = create_project(db_session, owner, "Private Project")

    response = client.get(
        f"/projects/{project.id}",
        headers=auth_headers(other_user),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_user_cannot_modify_another_users_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "idor-owner-update@example.com")
    other_user = create_user(db_session, "idor-other-update@example.com")
    project = create_project(db_session, owner, "Original Project")

    response = client.patch(
        f"/projects/{project.id}",
        json={"name": "Unauthorized Change"},
        headers=auth_headers(other_user),
    )

    assert response.status_code == 404
    db_session.refresh(project)
    assert project.name == "Original Project"
    assert project.owner_id == owner.id


def test_user_cannot_delete_another_users_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "idor-owner-delete@example.com")
    other_user = create_user(db_session, "idor-other-delete@example.com")
    project = create_project(db_session, owner, "Protected Project")
    project_id = project.id

    response = client.delete(
        f"/projects/{project_id}",
        headers=auth_headers(other_user),
    )

    assert response.status_code == 404

    remaining_project = db_session.get(Project, project_id)
    assert remaining_project is not None
    assert remaining_project.name == "Protected Project"
    assert remaining_project.owner_id == owner.id
