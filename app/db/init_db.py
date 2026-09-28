from app.db.base import Base
from app.db.session import engine
from app.models import Project


def init_db() -> None:
    _ = Project
    Base.metadata.create_all(bind=engine)
