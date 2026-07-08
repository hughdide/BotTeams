from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
from app.core.config import settings

DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}/{settings.postgres_db}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency de FastAPI que provee y cierra la sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
