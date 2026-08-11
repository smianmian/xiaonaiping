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

from api.database import (
    DatabaseConfigurationError,
    DatabaseSettings,
    connect_database,
    ensure_deletion_audit_sync_deleted_column,
    ensure_schema,
)
from api.server import upsert_sync, upsert_phone_code, upsert_photo


class FakeCursor:
    def __init__(self, statements: list[tuple[str, tuple]]) -> None:
        self.statements = statements

    def execute(self, statement: str, parameters: tuple = ()) -> None:
        self.statements.append((statement, parameters))

    def fetchone(self):
        return None


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
                account_columns = [row["name"] for row in db.execute("PRAGMA table_info(accounts)").fetchall()]
                phone_code_columns = {
                    row["name"] for row in db.execute("PRAGMA table_info(phone_login_codes)").fetchall()
                }
            self.assertIn("accounts", tables)
            self.assertIn("deletion_audit", tables)
            self.assertEqual(account_columns, ["account_id", "created_at", "deleted_at"])
            self.assertTrue(
                {"request_window_started_at", "last_requested_at", "request_count", "failed_attempts", "locked_until"}
                <= phone_code_columns
            )

    def test_sqlite_schema_migrates_legacy_deletion_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "xiaonaiping.sqlite3"
            with connect_database(DatabaseSettings(backend="sqlite", sqlite_path=path)) as db:
                db.execute(
                    """
                    CREATE TABLE deletion_audit (
                        audit_id TEXT PRIMARY KEY,
                        account_id TEXT NOT NULL,
                        deleted_at TEXT NOT NULL,
                        photo_count INTEGER NOT NULL
                    )
                    """
                )
                ensure_schema(db)
                columns = {row["name"] for row in db.execute("PRAGMA table_info(deletion_audit)").fetchall()}

            self.assertIn("sync_deleted", columns)

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
        upsert_sync(db, "account", b"{}", "now")
        upsert_photo(db, "account", "photo", "image/jpeg", 10, "digest", "now")

        statements = [statement for statement, _ in fake_connection.statements]
        upsert_statements = [statement for statement in statements if "INSERT INTO" in statement]
        self.assertEqual(len(upsert_statements), 3)
        self.assertTrue(all("ON DUPLICATE KEY UPDATE" in statement for statement in upsert_statements))
        self.assertTrue(all("?" not in statement for statement in statements))

    def test_upsert_sync_archives_previous_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "xiaonaiping.sqlite3"
            with connect_database(DatabaseSettings(backend="sqlite", sqlite_path=path)) as db:
                ensure_schema(db)
                db.execute(
                    "INSERT INTO accounts(account_id, created_at) VALUES (?, ?)",
                    ("account", "t0"),
                )

                upsert_sync(db, "account", b'{"v":1}', "t1")
                upsert_sync(db, "account", b'{"v":2}', "t2")
                # 相同 payload 不应产生重复归档
                upsert_sync(db, "account", b'{"v":2}', "t3")

                current = db.execute(
                    "SELECT payload FROM syncs WHERE account_id = ?", ("account",)
                ).fetchone()
                versions = db.execute(
                    "SELECT version, payload, updated_at FROM sync_versions WHERE account_id = ? ORDER BY version",
                    ("account",),
                ).fetchall()

            self.assertEqual(bytes(current["payload"]), b'{"v":2}')
            self.assertEqual(len(versions), 1)
            self.assertEqual(bytes(versions[0]["payload"]), b'{"v":1}')
            self.assertEqual(versions[0]["updated_at"], "t1")

    def test_mysql_legacy_backup_deleted_column_gets_a_default(self) -> None:
        class LegacyAuditDatabase:
            dialect = "mysql"

            def __init__(self) -> None:
                self.statements: list[str] = []

            def execute(self, statement: str):
                self.statements.append(statement)
                has_backup_deleted = "backup_deleted" in statement
                return SimpleNamespace(fetchone=lambda: {"present": 1} if has_backup_deleted else None)

        db = LegacyAuditDatabase()
        ensure_deletion_audit_sync_deleted_column(db)

        self.assertTrue(any("ADD COLUMN sync_deleted" in statement for statement in db.statements))
        self.assertTrue(any("MODIFY backup_deleted" in statement for statement in db.statements))


if __name__ == "__main__":
    unittest.main()
