import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database_bootstrap import (
    initialise_runtime_database,
    runtime_database_path,
)


class DatabaseBootstrapTests(unittest.TestCase):
    def test_copies_seed_once_without_modifying_or_replacing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            seed_path = directory / "seed.db"
            runtime_path = directory / "runtime" / "app.db"
            seed_path.write_bytes(b"immutable seed")

            self.assertTrue(initialise_runtime_database(seed_path, runtime_path))
            self.assertEqual(runtime_path.read_bytes(), b"immutable seed")
            self.assertEqual(seed_path.read_bytes(), b"immutable seed")

            runtime_path.write_bytes(b"runtime data")
            self.assertFalse(initialise_runtime_database(seed_path, runtime_path))
            self.assertEqual(runtime_path.read_bytes(), b"runtime data")
            self.assertEqual(seed_path.read_bytes(), b"immutable seed")

    def test_replaces_an_empty_database_created_before_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            seed_path = directory / "seed.db"
            runtime_path = directory / "runtime" / "app.db"
            seed_path.write_bytes(b"immutable seed")
            runtime_path.parent.mkdir()
            runtime_path.touch()

            self.assertTrue(initialise_runtime_database(seed_path, runtime_path))
            self.assertEqual(runtime_path.read_bytes(), b"immutable seed")

    def test_repairs_an_empty_failed_initial_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            seed_path = directory / "seed.db"
            runtime_path = directory / "runtime.db"
            seed_path.write_bytes(b"immutable seed")
            with sqlite3.connect(runtime_path) as connection:
                connection.execute("CREATE TABLE alembic_version (version_num TEXT)")
                connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")

            self.assertTrue(initialise_runtime_database(seed_path, runtime_path))
            self.assertEqual(runtime_path.read_bytes(), b"immutable seed")

    def test_preserves_a_failed_database_that_contains_a_user(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            seed_path = directory / "seed.db"
            runtime_path = directory / "runtime.db"
            seed_path.write_bytes(b"immutable seed")
            with sqlite3.connect(runtime_path) as connection:
                connection.execute("CREATE TABLE alembic_version (version_num TEXT)")
                connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
                connection.execute("INSERT INTO users (id) VALUES (1)")

            self.assertFalse(initialise_runtime_database(seed_path, runtime_path))
            with sqlite3.connect(runtime_path) as connection:
                self.assertEqual(connection.execute("SELECT id FROM users").fetchall(), [(1,)])

    def test_rejects_the_seed_as_the_runtime_database(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "app.db"
            database_path.write_bytes(b"database")

            with self.assertRaises(ValueError):
                initialise_runtime_database(database_path, database_path)

    def test_extracts_an_absolute_sqlite_database_path(self) -> None:
        self.assertEqual(
            runtime_database_path("sqlite+aiosqlite:////app/runtime/app.db"),
            Path("/app/runtime/app.db"),
        )


if __name__ == "__main__":
    unittest.main()
