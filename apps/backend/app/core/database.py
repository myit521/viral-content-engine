from __future__ import annotations

import logging
import os
import tempfile
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DEFAULT_DB_PATH = Path(tempfile.gettempdir()) / "viral-content-engine" / "app_v3.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")
logger = logging.getLogger(__name__)
logger.info("Using DATABASE_URL: %s", DATABASE_URL)

if DATABASE_URL.startswith("sqlite:///"):
    if DATABASE_URL.startswith("sqlite:////"):
        db_path = Path(DATABASE_URL.replace("sqlite:///", "", 1))
    else:
        db_path = Path(DATABASE_URL.replace("sqlite:///", "", 1))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connect_args: dict[str, object] = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import orm  # noqa: F401

    # Keep metadata bootstrap for local/dev convenience.
    # Schema evolution should be managed by Alembic migrations.
    Base.metadata.create_all(bind=engine)
