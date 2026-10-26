import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.api_rate_limit import (
    project_creation_api_limiter,
    rate_limit_dependency,
)
from app.db.session import get_db
from app.models import Project, User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

security_logger = logging.getLogger("secureship.security")

router = APIRouter(prefix="/projects", tags=["projects"])


def get_owned_project(
    project_id: int,
    user_id: int,
    db: Session,
) -> Project:
    """Return a project only when it belongs to the authenticated user."""
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == user_id,
        )
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.post(
    "",
    response_model=ProjectResponse,
    dependencies=[Depends(rate_limit_dependency(project_creation_api_limiter))],
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    new_project = Project(
        name=project.name,
        owner_id=current_user.id,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    security_logger.info(
        "Project created",
        extra={
            "event": "project.created",
            "user_id": current_user.id,
            "project_id": new_project.id,
        },
    )

    return new_project


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    return get_owned_project(project_id, current_user.id, db)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    project = get_owned_project(project_id, current_user.id, db)
    project.name = project_update.name

    db.commit()
    db.refresh(project)

    security_logger.info(
        "Project updated",
        extra={
            "event": "project.updated",
            "user_id": current_user.id,
            "project_id": project.id,
        },
    )

    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    project = get_owned_project(project_id, current_user.id, db)
    deleted_project_id = project.id

    db.delete(project)
    db.commit()

    security_logger.info(
        "Project deleted",
        extra={
            "event": "project.deleted",
            "user_id": current_user.id,
            "project_id": deleted_project_id,
        },
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
