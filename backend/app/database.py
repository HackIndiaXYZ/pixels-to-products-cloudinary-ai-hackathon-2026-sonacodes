"""SQLAlchemy engine and session. SQLite by default; URL is configurable."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _sqlalchemy_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return database_url


def _make_engine(database_url: str):
    if database_url.startswith("sqlite"):
        _ensure_sqlite_directory(database_url)
        connect_args = {"check_same_thread": False}
        kwargs: dict = {"connect_args": connect_args}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
        sqlite_engine = create_engine(database_url, **kwargs)

        @event.listens_for(sqlite_engine, "connect")
        def _enable_sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return sqlite_engine
    return create_engine(_sqlalchemy_database_url(database_url), pool_pre_ping=True)


def _ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///") or database_url.endswith(":memory:"):
        return
    raw_path = database_url.removeprefix("sqlite:///")
    if not raw_path or raw_path == ":memory:":
        return
    Path(raw_path).parent.mkdir(parents=True, exist_ok=True)


settings = get_settings()
engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        inspector = inspect(connection)
        columns = {column["name"] for column in inspector.get_columns("clothing_items")}
        migrations = {
            "user_id": "ALTER TABLE clothing_items ADD COLUMN user_id INTEGER REFERENCES users(id)",
            "material": "ALTER TABLE clothing_items ADD COLUMN material VARCHAR(80)",
            "texture": "ALTER TABLE clothing_items ADD COLUMN texture VARCHAR(80)",
            "sleeve_type": "ALTER TABLE clothing_items ADD COLUMN sleeve_type VARCHAR(80)",
            "neckline": "ALTER TABLE clothing_items ADD COLUMN neckline VARCHAR(80)",
            "fit": "ALTER TABLE clothing_items ADD COLUMN fit VARCHAR(80)",
            "length": "ALTER TABLE clothing_items ADD COLUMN length VARCHAR(80)",
            "formality": "ALTER TABLE clothing_items ADD COLUMN formality VARCHAR(80)",
            "ai_description": "ALTER TABLE clothing_items ADD COLUMN ai_description TEXT",
            "ai_tags": "ALTER TABLE clothing_items ADD COLUMN ai_tags TEXT",
            "recognition_confidence": "ALTER TABLE clothing_items ADD COLUMN recognition_confidence FLOAT",
            "recognition_provider": "ALTER TABLE clothing_items ADD COLUMN recognition_provider VARCHAR(40)",
            "recognition_status": "ALTER TABLE clothing_items ADD COLUMN recognition_status VARCHAR(40)",
        }
        for name, sql in migrations.items():
            if name not in columns:
                connection.execute(text(sql))
        connection.execute(
            text("CREATE INDEX IF NOT EXISTS ix_clothing_items_user_id ON clothing_items (user_id)")
        )
