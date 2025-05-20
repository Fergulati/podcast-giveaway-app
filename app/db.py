from __future__ import annotations

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except Exception as e:  # pragma: no cover - optional dependency
    create_engine = None  # type: ignore
    sessionmaker = None  # type: ignore

from .models import Base


def init_db(url: str = "sqlite:///app.db"):
    """Initialize the database and return a session factory."""
    if create_engine is None or sessionmaker is None:
        raise RuntimeError("SQLAlchemy is not available")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
