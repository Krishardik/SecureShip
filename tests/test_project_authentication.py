"""Regression tests for authentication on project endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models import Project, User


@pytest.fixture
def existing_project(db_session):
    """Create a project so endpoint tests exercise existing resources."""
    user = User(
        email="auth-check@example.com",
        password_hash="not-used-in-this-test",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    project = Project(name="Protected Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    return project


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/projects/1", None),
        ("PATCH", "/projects/1", {"name": "Changed"}),
        ("DELETE", "/projects/1", None),
    ],
)
def test_project_endpoints_require_authentication(
    client: TestClient,
    method: str,
    path: str,
    payload: dict | None,
):
    """Requests without a bearer token must not access project endpoints."""
    response = client.request(method, path, json=payload)

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("method", "payload"),
    [
        ("GET", None),
        ("PATCH", {"name": "Changed"}),
        ("DELETE", None),
    ],
)
def test_existing_project_endpoints_reject_missing_credentials(
    client: TestClient,
    existing_project: Project,
    method: str,
    payload: dict | None,
):
    """Existing project IDs must not bypass authentication."""
    response = client.request(
        method,
        f"/projects/{existing_project.id}",
        json=payload,
    )

    assert response.status_code == 401
