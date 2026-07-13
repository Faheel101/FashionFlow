"""Database connection and session management for the source system.

Provides a SQLite engine, session factory, and context manager for
safe database operations with automatic commit/rollback.

Usage::

    from source_system.database.connection import get_engine, get_session

    engine = get_engine()

    with get_session() as session:
        customers = session.query(Customer).all()
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from source_system.database.models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(db_path: str = "data/fashionflow.db") -> Engine:
    """Create or return the SQLite engine.

    Args:
        db_path: Path to the SQLite database file, relative to project root.

    Returns:
        SQLAlchemy Engine connected to the SQLite database.
    """
    global _engine

    if _engine is not None:
        return _engine

    # Ensure the data directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(
        f"sqlite:///{db_file}",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Enable foreign key enforcement for SQLite
    @event.listens_for(_engine, "connect")
    def _enable_foreign_keys(dbapi_conn, connection_record):  # noqa: ANN001
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return _engine


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Create or return the session factory.

    Args:
        engine: SQLAlchemy Engine. If None, uses the default engine.

    Returns:
        Configured sessionmaker instance.
    """
    global _session_factory

    if _session_factory is not None:
        return _session_factory

    if engine is None:
        engine = get_engine()

    _session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _session_factory


@contextmanager
def get_session(engine: Engine | None = None) -> Generator[Session, None, None]:
    """Provide a transactional session scope.

    Commits on success, rolls back on exception, always closes.

    Args:
        engine: Optional SQLAlchemy Engine override.

    Yields:
        SQLAlchemy Session.
    """
    factory = get_session_factory(engine)
    session = factory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(db_path: str = "data/fashionflow.db") -> Engine:
    """Initialize the database — create all tables.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        The initialized SQLAlchemy Engine.
    """
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def reset_engine() -> None:
    """Reset the cached engine and session factory. Useful for tests."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
