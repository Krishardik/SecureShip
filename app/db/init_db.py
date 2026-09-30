from app.db.base import Base
from app.db.session import engine
from app.models import Project, User


def init_db() -> None:
    _ = Project, User
    Base.metadata.create_all(bind=engine)
