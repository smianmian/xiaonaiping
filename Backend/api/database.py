from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DatabaseConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class DatabaseSettings:
    backend: str
    sqlite_path: Path
    mysql_host: str = ""
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = ""
    mysql_ssl_ca: str = ""


class DatabaseConnection:
    def __init__(self, dialect: str, raw_connection: Any) -> None:
        self.dialect = dialect
        self.raw_connection = raw_connection

    def execute(self, statement: str, parameters: tuple[Any, ...] = ()):
        if self.dialect == "mysql":
            statement = statement.replace("?", "%s")
        cursor = self.raw_connection.cursor()
        cursor.execute(statement, parameters)
        return cursor

    def executescript(self, script: str) -> None:
        if self.dialect != "sqlite":
            raise RuntimeError("executescript is only available for SQLite")
        self.raw_connection.executescript(script)

    def commit(self) -> None:
        self.raw_connection.commit()

    def rollback(self) -> None:
        self.raw_connection.rollback()

    def close(self) -> None:
        self.raw_connection.close()

    def __enter__(self) -> "DatabaseConnection":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None:
            self.rollback()
        self.close()


def settings_from_environment(data_dir: Path) -> DatabaseSettings:
    backend = os.environ.get("XNP_DATABASE_BACKEND", "sqlite").strip().lower()
    try:
        mysql_port = int(os.environ.get("XNP_MYSQL_PORT", "3306"))
    except ValueError as error:
        raise DatabaseConfigurationError("XNP_MYSQL_PORT 必须是整数。") from error

    return DatabaseSettings(
        backend=backend,
        sqlite_path=data_dir / "xiaonaiping.sqlite3",
        mysql_host=os.environ.get("XNP_MYSQL_HOST", "").strip(),
        mysql_port=mysql_port,
        mysql_user=os.environ.get("XNP_MYSQL_USER", "").strip(),
        mysql_password=os.environ.get("XNP_MYSQL_PASSWORD", ""),
        mysql_database=os.environ.get("XNP_MYSQL_DATABASE", "").strip(),
        mysql_ssl_ca=os.environ.get("XNP_MYSQL_SSL_CA", "").strip(),
    )


def connect_database(settings: DatabaseSettings) -> DatabaseConnection:
    if settings.backend == "sqlite":
        settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(settings.sqlite_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return DatabaseConnection("sqlite", connection)

    if settings.backend != "mysql":
        raise DatabaseConfigurationError(f"不支持的数据库后端：{settings.backend}")

    missing = [
        name
        for name, value in {
            "XNP_MYSQL_HOST": settings.mysql_host,
            "XNP_MYSQL_USER": settings.mysql_user,
            "XNP_MYSQL_PASSWORD": settings.mysql_password,
            "XNP_MYSQL_DATABASE": settings.mysql_database,
        }.items()
        if not value
    ]
    if missing:
        raise DatabaseConfigurationError("缺少 MySQL 配置：" + ", ".join(missing))

    try:
        import pymysql
    except ImportError as error:
        raise DatabaseConfigurationError("缺少 PyMySQL，请安装 Backend/requirements-production.txt。") from error

    ssl = {"ca": settings.mysql_ssl_ca} if settings.mysql_ssl_ca else None
    connection = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
        ssl=ssl,
    )
    return DatabaseConnection("mysql", connection)


def ensure_schema(db: DatabaseConnection) -> None:
    if db.dialect == "sqlite":
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                deleted_at TEXT
            );

            CREATE TABLE IF NOT EXISTS syncs (
                account_id TEXT PRIMARY KEY REFERENCES accounts(account_id) ON DELETE CASCADE,
                payload BLOB NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sync_versions (
                account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
                version INTEGER NOT NULL,
                payload BLOB NOT NULL,
                updated_at TEXT NOT NULL,
                archived_at TEXT NOT NULL,
                PRIMARY KEY (account_id, version)
            );

            CREATE TABLE IF NOT EXISTS account_identities (
                provider TEXT NOT NULL,
                subject_hash TEXT NOT NULL,
                account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                PRIMARY KEY (provider, subject_hash)
            );

            CREATE TABLE IF NOT EXISTS phone_login_codes (
                phone_hash TEXT PRIMARY KEY,
                code_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                request_window_started_at INTEGER NOT NULL,
                last_requested_at INTEGER NOT NULL,
                request_count INTEGER NOT NULL DEFAULT 1,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS photos (
                account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
                photo_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (account_id, photo_id)
            );

            CREATE TABLE IF NOT EXISTS deletion_audit (
                audit_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                deleted_at TEXT NOT NULL,
                sync_deleted INTEGER NOT NULL,
                photo_count INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analytics_events (
                event_id TEXT PRIMARY KEY,
                account_hash TEXT NOT NULL,
                event_name TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                received_at TEXT NOT NULL,
                properties_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_analytics_events_name_time
                ON analytics_events(event_name, occurred_at);
            CREATE INDEX IF NOT EXISTS idx_analytics_events_actor_time
                ON analytics_events(account_hash, occurred_at);

            CREATE TABLE IF NOT EXISTS families (
                family_id TEXT PRIMARY KEY,
                owner_account_id TEXT NOT NULL,
                invite_code TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS family_members (
                family_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (family_id, account_id)
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_family_members_account
                ON family_members(account_id);

            CREATE TABLE IF NOT EXISTS family_records (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                record_type TEXT NOT NULL,
                record_id TEXT NOT NULL,
                payload BLOB NOT NULL,
                updated_at_ms INTEGER NOT NULL,
                deleted_at_ms INTEGER NULL,
                author_account_id TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_family_records_identity
                ON family_records(family_id, record_type, record_id);
            CREATE INDEX IF NOT EXISTS idx_family_records_cursor
                ON family_records(family_id, seq);
            """
        )
        ensure_phone_login_code_security_columns(db)
        ensure_deletion_audit_sync_deleted_column(db)
        db.commit()
        return

    statements = [
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id CHAR(36) PRIMARY KEY,
            created_at VARCHAR(40) NOT NULL,
            deleted_at VARCHAR(40) NULL,
            INDEX idx_accounts_deleted_at (deleted_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS syncs (
            account_id CHAR(36) PRIMARY KEY,
            payload LONGBLOB NOT NULL,
            updated_at VARCHAR(40) NOT NULL,
            CONSTRAINT fk_syncs_account
                FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS sync_versions (
            account_id CHAR(36) NOT NULL,
            version BIGINT NOT NULL,
            payload LONGBLOB NOT NULL,
            updated_at VARCHAR(40) NOT NULL,
            archived_at VARCHAR(40) NOT NULL,
            PRIMARY KEY (account_id, version),
            CONSTRAINT fk_sync_versions_account
                FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS account_identities (
            provider VARCHAR(32) NOT NULL,
            subject_hash CHAR(64) NOT NULL,
            account_id CHAR(36) NOT NULL,
            created_at VARCHAR(40) NOT NULL,
            PRIMARY KEY (provider, subject_hash),
            INDEX idx_account_identities_account (account_id),
            CONSTRAINT fk_account_identities_account
                FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS phone_login_codes (
            phone_hash CHAR(64) PRIMARY KEY,
            code_hash CHAR(64) NOT NULL,
            created_at VARCHAR(40) NOT NULL,
            expires_at BIGINT NOT NULL,
            request_window_started_at BIGINT NOT NULL,
            last_requested_at BIGINT NOT NULL,
            request_count INT NOT NULL DEFAULT 1,
            failed_attempts INT NOT NULL DEFAULT 0,
            locked_until BIGINT NOT NULL DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS photos (
            account_id CHAR(36) NOT NULL,
            photo_id VARCHAR(80) NOT NULL,
            content_type VARCHAR(120) NOT NULL,
            size_bytes BIGINT NOT NULL,
            sha256 CHAR(64) NOT NULL,
            updated_at VARCHAR(40) NOT NULL,
            PRIMARY KEY (account_id, photo_id),
            CONSTRAINT fk_photos_account
                FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS deletion_audit (
            audit_id CHAR(36) PRIMARY KEY,
            account_id CHAR(36) NOT NULL,
            deleted_at VARCHAR(40) NOT NULL,
            sync_deleted TINYINT(1) NOT NULL,
            photo_count BIGINT NOT NULL,
            INDEX idx_deletion_audit_deleted_at (deleted_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS analytics_events (
            event_id VARCHAR(80) PRIMARY KEY,
            account_hash CHAR(64) NOT NULL,
            event_name VARCHAR(80) NOT NULL,
            occurred_at VARCHAR(40) NOT NULL,
            received_at VARCHAR(40) NOT NULL,
            properties_json TEXT NOT NULL,
            INDEX idx_analytics_events_name_time (event_name, occurred_at),
            INDEX idx_analytics_events_actor_time (account_hash, occurred_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS families (
            family_id CHAR(36) PRIMARY KEY,
            owner_account_id CHAR(36) NOT NULL,
            invite_code VARCHAR(16) NOT NULL UNIQUE,
            created_at VARCHAR(40) NOT NULL,
            CONSTRAINT fk_families_owner
                FOREIGN KEY (owner_account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS family_members (
            family_id CHAR(36) NOT NULL,
            account_id CHAR(36) NOT NULL,
            role VARCHAR(16) NOT NULL,
            created_at VARCHAR(40) NOT NULL,
            PRIMARY KEY (family_id, account_id),
            UNIQUE INDEX idx_family_members_account (account_id),
            CONSTRAINT fk_family_members_family
                FOREIGN KEY (family_id) REFERENCES families(family_id) ON DELETE CASCADE,
            CONSTRAINT fk_family_members_account
                FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS family_records (
            seq BIGINT PRIMARY KEY AUTO_INCREMENT,
            family_id CHAR(36) NOT NULL,
            record_type VARCHAR(32) NOT NULL,
            record_id VARCHAR(80) NOT NULL,
            payload MEDIUMBLOB NOT NULL,
            updated_at_ms BIGINT NOT NULL,
            deleted_at_ms BIGINT NULL,
            author_account_id CHAR(36) NOT NULL,
            UNIQUE INDEX idx_family_records_identity (family_id, record_type, record_id),
            INDEX idx_family_records_cursor (family_id, seq),
            CONSTRAINT fk_family_records_family
                FOREIGN KEY (family_id) REFERENCES families(family_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    ]
    for statement in statements:
        db.execute(statement)
    ensure_phone_login_code_security_columns(db)
    ensure_deletion_audit_sync_deleted_column(db)
    db.commit()


def insert_account(db: DatabaseConnection, account_id: str, created_at: str) -> None:
    db.execute(
        "INSERT INTO accounts(account_id, created_at) VALUES (?, ?)",
        (account_id, created_at),
    )


def ensure_phone_login_code_security_columns(db: DatabaseConnection) -> None:
    columns = {
        "request_window_started_at": ("INTEGER NOT NULL DEFAULT 0", "BIGINT NOT NULL DEFAULT 0"),
        "last_requested_at": ("INTEGER NOT NULL DEFAULT 0", "BIGINT NOT NULL DEFAULT 0"),
        "request_count": ("INTEGER NOT NULL DEFAULT 1", "INT NOT NULL DEFAULT 1"),
        "failed_attempts": ("INTEGER NOT NULL DEFAULT 0", "INT NOT NULL DEFAULT 0"),
        "locked_until": ("INTEGER NOT NULL DEFAULT 0", "BIGINT NOT NULL DEFAULT 0"),
    }
    if db.dialect == "sqlite":
        existing = {row["name"] for row in db.execute("PRAGMA table_info(phone_login_codes)").fetchall()}
        for name, (sqlite_type, _) in columns.items():
            if name not in existing:
                db.execute(f"ALTER TABLE phone_login_codes ADD COLUMN {name} {sqlite_type}")
        return

    for name, (_, mysql_type) in columns.items():
        row = db.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'phone_login_codes'
              AND column_name = ?
            """,
            (name,),
        ).fetchone()
        if row is None:
            db.execute(f"ALTER TABLE phone_login_codes ADD COLUMN {name} {mysql_type}")


def ensure_deletion_audit_sync_deleted_column(db: DatabaseConnection) -> None:
    if db.dialect == "sqlite":
        columns = {row["name"] for row in db.execute("PRAGMA table_info(deletion_audit)").fetchall()}
        if "sync_deleted" not in columns:
            db.execute("ALTER TABLE deletion_audit ADD COLUMN sync_deleted INTEGER NOT NULL DEFAULT 0")
        return

    sync_deleted_column = db.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'deletion_audit'
          AND column_name = 'sync_deleted'
        """
    ).fetchone()
    if sync_deleted_column is None:
        db.execute(
            "ALTER TABLE deletion_audit ADD COLUMN sync_deleted TINYINT(1) NOT NULL DEFAULT 0 AFTER deleted_at"
        )

    backup_deleted_column = db.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'deletion_audit'
          AND column_name = 'backup_deleted'
        """
    ).fetchone()
    if backup_deleted_column is not None:
        db.execute("ALTER TABLE deletion_audit MODIFY backup_deleted TINYINT(1) NOT NULL DEFAULT 0")
