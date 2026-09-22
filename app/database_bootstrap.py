import os
import shutil
import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

from sqlalchemy.engine import make_url

from app.config import settings

BOOTSTRAP_MIGRATION_TABLES = frozenset({"alembic_version", "users"})


def runtime_database_path(database_url: str) -> Path:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database:
        raise ValueError("DATABASE_URL must identify a file-backed SQLite database")
    if url.database == ":memory:":
        raise ValueError("The runtime database cannot be an in-memory SQLite database")
    return Path(url.database).resolve()


def _runtime_database_can_be_reinitialised(runtime_path: Path) -> bool:
    """Return whether the database contains no mutable application data."""
    try:
        if runtime_path.stat().st_size == 0:
            return True

        database_uri = f"{runtime_path.as_uri()}?mode=ro"
        with sqlite3.connect(database_uri, uri=True) as connection:
            table_names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = ?",
                    ("table",),
                )
            }
            if not table_names:
                return True
            if not table_names.issubset(BOOTSTRAP_MIGRATION_TABLES):
                return False
            if "users" not in table_names:
                return True
            return connection.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None
    except (FileNotFoundError, sqlite3.DatabaseError):
        return not runtime_path.exists()


def initialise_runtime_database(seed_path: Path, runtime_path: Path) -> bool:
    seed_path = seed_path.resolve()
    runtime_path = runtime_path.resolve()

    if seed_path == runtime_path:
        raise ValueError("The seed and runtime database paths must be different")
    if runtime_path.exists() and not _runtime_database_can_be_reinitialised(runtime_path):
        return False
    if not seed_path.is_file():
        raise FileNotFoundError(f"Seed database not found: {seed_path}")

    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            dir=runtime_path.parent,
            prefix=f".{runtime_path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        shutil.copyfile(seed_path, temporary_path)
        os.replace(temporary_path, runtime_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return True


def main() -> None:
    initialise_runtime_database(
        settings.seed_database_path,
        runtime_database_path(settings.database_url),
    )


if __name__ == "__main__":
    main()
