"""Security and pagination tests for project listing."""

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


def test_listing_returns_only_the_authenticated_users_projects(
    client: TestClient,
    db_session: Session,
):
    first_user = create_user(db_session, "listing-first@example.com")
    second_user = create_user(db_session, "listing-second@example.com")

    create_project(db_session, first_user, "First User Project A")
    create_project(db_session, first_user, "First User Project B")
    create_project(db_session, second_user, "Second User Private Project")

    response = client.get(
        "/projects",
        headers=auth_headers(first_user),
    )

    assert response.status_code == 200
    projects = response.json()

    assert len(projects) == 2
    assert {project["name"] for project in projects} == {
        "First User Project A",
        "First User Project B",
    }
    assert all(project["name"] != "Second User Private Project" for project in projects)


def test_listing_enforces_pagination(
    client: TestClient,
    db_session: Session,
):
    user = create_user(db_session, "listing-pagination@example.com")

    create_project(db_session, user, "Pagination Project A")
    create_project(db_session, user, "Pagination Project B")
    create_project(db_session, user, "Pagination Project C")

    response = client.get(
        "/projects?limit=2&offset=1",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert [project["name"] for project in response.json()] == [
        "Pagination Project B",
        "Pagination Project C",
    ]


def test_listing_rejects_limit_above_maximum(
    client: TestClient,
    db_session: Session,
):
    user = create_user(db_session, "listing-limit@example.com")

    response = client.get(
        "/projects?limit=101",
        headers=auth_headers(user),
    )

    assert response.status_code == 422


def test_listing_rejects_invalid_pagination_values(
    client: TestClient,
    db_session: Session,
):
    user = create_user(db_session, "listing-invalid-page@example.com")

    response = client.get(
        "/projects?limit=0",
        headers=auth_headers(user),
    )
    assert response.status_code == 422

    response = client.get(
        "/projects?offset=-1",
        headers=auth_headers(user),
    )
    assert response.status_code == 422


def test_listing_requires_authentication(client: TestClient):
    response = client.get("/projects")

    assert response.status_code == 401
