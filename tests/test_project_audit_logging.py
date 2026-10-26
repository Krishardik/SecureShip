"""Tests for audit logging of successful project mutations."""

import logging

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Project, User
from app.services.token import create_access_token


def create_user(db_session: Session) -> User:
    user = User(
        email="audit-test@example.com",
        password_hash="not-used-in-this-test",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


def audit_records(caplog):
    return [
        record
        for record in caplog.records
        if record.name == "secureship.security" and hasattr(record, "event")
    ]


def test_project_creation_is_audited(
    client: TestClient,
    db_session: Session,
    caplog,
):
    user = create_user(db_session)

    with caplog.at_level(logging.INFO, logger="secureship.security"):
        response = client.post(
            "/projects",
            json={"name": "Audit Project"},
            headers=auth_headers(user),
        )

    assert response.status_code == 201

    records = audit_records(caplog)
    record = next(r for r in records if r.event == "project.created")

    assert record.user_id == user.id
    assert record.project_id == response.json()["id"]
    assert "Authorization" not in record.getMessage()


def test_project_update_is_audited(
    client: TestClient,
    db_session: Session,
    caplog,
):
    user = create_user(db_session)
    project = Project(name="Before", owner_id=user.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    with caplog.at_level(logging.INFO, logger="secureship.security"):
        response = client.patch(
            f"/projects/{project.id}",
            json={"name": "After"},
            headers=auth_headers(user),
        )

    assert response.status_code == 200

    records = audit_records(caplog)
    record = next(r for r in records if r.event == "project.updated")

    assert record.user_id == user.id
    assert record.project_id == project.id


def test_project_deletion_is_audited(
    client: TestClient,
    db_session: Session,
    caplog,
):
    user = create_user(db_session)
    project = Project(name="To Delete", owner_id=user.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    project_id = project.id

    with caplog.at_level(logging.INFO, logger="secureship.security"):
        response = client.delete(
            f"/projects/{project_id}",
            headers=auth_headers(user),
        )

    assert response.status_code == 204

    records = audit_records(caplog)
    record = next(r for r in records if r.event == "project.deleted")

    assert record.user_id == user.id
    assert record.project_id == project_id
    assert db_session.get(Project, project_id) is None
