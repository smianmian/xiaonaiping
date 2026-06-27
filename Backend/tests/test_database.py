from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.database import DatabaseConfigurationError, DatabaseSettings, connect_database, ensure_schema
from api.server import upsert_backup, upsert_phone_code, upsert_photo


class FakeCursor:
    def __init__(self, statements: list[tuple[str, tuple]]) -> None:
        self.statements = statements

    def execute(self, statement: str, parameters: tuple = ()) -> None:
        self.statements.append((statement, parameters))


class FakeConnection:
    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []
        self.committed = False
        self.closed = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.statements)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class DatabaseTest(unittest.TestCase):
    def test_sqlite_schema_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "xiaonaiping.sqlite3"
            with connect_database(DatabaseSettings(backend="sqlite", sqlite_path=path)) as db:
                ensure_schema(db)
                tables = {
                    row["name"]
                    for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
                }
            self.assertIn("accounts", tables)
            self.assertIn("deletion_audit", tables)

    def test_mysql_requires_complete_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaises(DatabaseConfigurationError):
                connect_database(DatabaseSettings(backend="mysql", sqlite_path=Path(tempdir) / "unused"))

    def test_mysql_schema_uses_mysql_placeholders_and_commits(self) -> None:
        fake_connection = FakeConnection()
        fake_module = SimpleNamespace(
            cursors=SimpleNamespace(DictCursor=object()),
            connect=lambda **kwargs: fake_connection,
        )
        settings = DatabaseSettings(
            backend="mysql",
            sqlite_path=Path("/unused"),
            mysql_host="rds.internal",
            mysql_user="xiaonaiping",
            mysql_password="secret",
            mysql_database="xiaonaiping",
        )
        with patch.dict(sys.modules, {"pymysql": fake_module}):
            with connect_database(settings) as db:
                db.execute("SELECT ? AS value", ("ok",))
                ensure_schema(db)

        self.assertEqual(fake_connection.statements[0], ("SELECT %s AS value", ("ok",)))
        self.assertTrue(any("ENGINE=InnoDB" in statement for statement, _ in fake_connection.statements))
        self.assertTrue(fake_connection.committed)
        self.assertTrue(fake_connection.closed)

    def test_mysql_upserts_use_mysql_syntax(self) -> None:
        fake_connection = FakeConnection()
        from api.database import DatabaseConnection

        db = DatabaseConnection("mysql", fake_connection)
        upsert_phone_code(db, "phone", "code", "now", 123)
        upsert_backup(db, "account", b"{}", "now")
        upsert_photo(db, "account", "photo", "image/jpeg", 10, "digest", "now")

        statements = [statement for statement, _ in fake_connection.statements]
        self.assertEqual(len(statements), 3)
        self.assertTrue(all("ON DUPLICATE KEY UPDATE" in statement for statement in statements))
        self.assertTrue(all("?" not in statement for statement in statements))


if __name__ == "__main__":
    unittest.main()
