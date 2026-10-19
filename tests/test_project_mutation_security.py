from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Project, User
from app.services.token import create_access_token


def create_user(db_session: Session, email: str) -> User:
    """Create an active user for project mutation tests."""
    user = User(
        email=email,
        password_hash="not-used-in-these-tests",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_project(
    db_session: Session,
    owner_id: int,
    name: str = "Test Project",
) -> Project:
    """Create a project owned by the specified user."""
    project = Project(name=name, owner_id=owner_id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def test_owner_can_update_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "owner@example.com")
    project = create_project(db_session, owner.id)

    response = client.patch(
        f"/projects/{project.id}",
        json={"name": "Updated Project"},
        headers=auth_headers(owner),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project"
    assert response.json()["owner_id"] == owner.id


def test_other_user_cannot_update_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "owner@example.com")
    other_user = create_user(db_session, "other@example.com")
    project = create_project(db_session, owner.id)

    response = client.patch(
        f"/projects/{project.id}",
        json={"name": "Unauthorized Change"},
        headers=auth_headers(other_user),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}

    db_session.refresh(project)
    assert project.name == "Test Project"


def test_update_rejects_client_supplied_owner_id(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "owner@example.com")
    other_user = create_user(db_session, "other@example.com")
    project = create_project(db_session, owner.id)

    response = client.patch(
        f"/projects/{project.id}",
        json={
            "name": "Attempted Ownership Change",
            "owner_id": other_user.id,
        },
        headers=auth_headers(owner),
    )

    assert response.status_code == 422

    db_session.refresh(project)
    assert project.name == "Test Project"
    assert project.owner_id == owner.id


def test_owner_can_delete_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "owner@example.com")
    project = create_project(db_session, owner.id)

    response = client.delete(
        f"/projects/{project.id}",
        headers=auth_headers(owner),
    )

    assert response.status_code == 204
    assert db_session.get(Project, project.id) is None


def test_other_user_cannot_delete_project(
    client: TestClient,
    db_session: Session,
):
    owner = create_user(db_session, "owner@example.com")
    other_user = create_user(db_session, "other@example.com")
    project = create_project(db_session, owner.id)

    response = client.delete(
        f"/projects/{project.id}",
        headers=auth_headers(other_user),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    assert db_session.get(Project, project.id) is not None


def test_update_nonexistent_project_returns_404(
    client: TestClient,
    db_session: Session,
):
    user = create_user(db_session, "user@example.com")

    response = client.patch(
        "/projects/999999",
        json={"name": "Missing Project"},
        headers=auth_headers(user),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


def test_delete_nonexistent_project_returns_404(
    client: TestClient,
    db_session: Session,
):
    user = create_user(db_session, "user@example.com")

    response = client.delete(
        "/projects/999999",
        headers=auth_headers(user),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
