#!/usr/bin/env python3
from __future__ import annotations
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import sys
import time
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
import urllib.error
import urllib.request

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.database import DatabaseConnection, connect_database, ensure_schema, settings_from_environment
from api.storage import ObjectStorage, build_object_storage


STATIC_ROUTES = {
    "/privacy": ("privacy.html", "text/html; charset=utf-8"),
    "/terms": ("terms.html", "text/html; charset=utf-8"),
    "/support": ("support.html", "text/html; charset=utf-8"),
    "/support-assets/app-icon-108.png": ("support-assets/app-icon-108.png", "image/png"),
    "/support-assets/operation-flow.jpg": ("support-assets/operation-flow.jpg", "image/jpeg"),
    "/support-assets/screenshot-home.jpg": ("support-assets/screenshot-home.jpg", "image/jpeg"),
    "/support-assets/screenshot-record.jpg": ("support-assets/screenshot-record.jpg", "image/jpeg"),
    "/support-assets/screenshot-sync.jpg": ("support-assets/screenshot-sync.jpg", "image/jpeg"),
    "/apple-app-site-association": ("apple-app-site-association", "application/json; charset=utf-8"),
    "/.well-known/apple-app-site-association": ("apple-app-site-association", "application/json; charset=utf-8"),
    "/internal/dashboard": ("dashboard.html", "text/html; charset=utf-8"),
}
MAX_SYNC_BYTES = 5 * 1024 * 1024
MAX_PHOTO_BYTES = 20 * 1024 * 1024
MAX_ANALYTICS_BYTES = 64 * 1024
MAX_ANALYTICS_EVENTS = 50
SESSION_TTL_SECONDS = 60 * 60 * 24 * 30
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
SAFE_ANALYTICS_EVENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")
PHONE_RE = re.compile(r"^\+[1-9][0-9]{7,15}$")
PHONE_CODE_TTL_SECONDS = 10 * 60
SMS_PROVIDER_WEBHOOK = "webhook"
WECHAT_DEBUG_PREFIX = "debug_wechat_"
WECHAT_SUBJECT_RE = re.compile(r"^[A-Za-z0-9_-]{4,128}$")
DEFAULT_WECHAT_ACCESS_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
DEFAULT_ANALYTICS_RETENTION_DAYS = 180
ANALYTICS_EVENT_NAMES = {
    "app_opened",
    "onboarding_completed",
    "account_created",
    "login_completed",
    "cloud_sync_enabled",
    "cloud_sync_completed",
    "cloud_restore_completed",
    "photo_added",
    "record_created",
    "reminder_enabled",
    "paywall_viewed",
    "purchase_started",
    "purchase_completed",
}
ANALYTICS_PROPERTY_VALUES = {
    "screen": {"home", "record", "profile", "album", "growth", "sync", "onboarding", "paywall"},
    "source": {"app_launch", "onboarding", "profile", "record", "album", "growth", "sync", "restore", "system"},
    "recordType": {"feeding", "sleep", "diaper", "growth", "milestone", "vaccine", "photo"},
    "reminderType": {"feeding", "vaccine"},
    "authProvider": {"recovery_key", "phone", "wechat"},
    "result": {"success", "failure", "cancelled"},
    "feature": {"cloud_sync", "cloud_restore", "photo_sync", "account", "reminder", "commercial"},
    "productTier": {"free", "premium"},
    "platform": {"ios"},
}
ANALYTICS_FORBIDDEN_PROPERTY_FRAGMENTS = (
    "baby",
    "birth",
    "name",
    "note",
    "content",
    "photo",
    "image",
    "file",
    "object",
    "key",
    "token",
    "recovery",
    "phone",
    "openid",
    "unionid",
    "location",
    "address",
    "latitude",
    "longitude",
    "height",
    "weight",
    "amount",
    "duration",
    "vaccine",
)


@dataclass(frozen=True)
class ServerConfig:
    data_dir: Path
    secret_key: str
    object_storage: ObjectStorage | None = None
    auth_debug_mode: bool = False
    sms_provider: str = ""
    sms_secret: str = ""
    sms_webhook_url: str = ""
    sms_template_id: str = ""
    app_review_phone_number: str = ""
    app_review_phone_code: str = ""
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_access_token_url: str = DEFAULT_WECHAT_ACCESS_TOKEN_URL
    admin_token: str = ""

    def storage(self) -> ObjectStorage:
        return self.object_storage or build_object_storage(self.data_dir)


class AuthProviderError(Exception):
    def __init__(self, status: HTTPStatus, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def utc_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")


def analytics_retention_days() -> int:
    try:
        days = int(os.environ.get("XNP_ANALYTICS_RETENTION_DAYS", str(DEFAULT_ANALYTICS_RETENTION_DAYS)))
    except ValueError:
        return DEFAULT_ANALYTICS_RETENTION_DAYS
    if days < 1:
        return DEFAULT_ANALYTICS_RETENTION_DAYS
    return min(days, 365)


def internal_client_allowed(client_ip: str, forwarded_for: str = "") -> bool:
    candidate = (forwarded_for.split(",", 1)[0] if forwarded_for else client_ip).strip()
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return address.is_loopback or address.is_private


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def unb64url(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def json_dumps_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def recovery_hash(secret_key: str, recovery_key: str) -> str:
    return hmac.new(secret_key.encode("utf-8"), recovery_key.encode("utf-8"), hashlib.sha256).hexdigest()


def subject_hash(secret_key: str, provider: str, subject: str) -> str:
    value = f"{provider}:{subject}"
    return hmac.new(secret_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def sign(secret_key: str, value: bytes) -> str:
    return hmac.new(secret_key.encode("utf-8"), value, hashlib.sha256).hexdigest()


def make_session_token(secret_key: str, account_id: str) -> str:
    now = int(time.time())
    payload = {"sub": account_id, "iat": now, "exp": now + SESSION_TTL_SECONDS}
    encoded = b64url(json_dumps_bytes(payload))
    return f"{encoded}.{sign(secret_key, encoded.encode('ascii'))}"


def verify_session_token(secret_key: str, token: str) -> str | None:
    try:
        encoded, signature = token.split(".", 1)
    except ValueError:
        return None

    expected = sign(secret_key, encoded.encode("ascii"))
    if not hmac.compare_digest(expected, signature):
        return None

    try:
        payload = json.loads(unb64url(encoded))
    except (ValueError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    account_id = payload.get("sub")
    if not isinstance(account_id, str):
        return None
    return account_id


def normalize_phone_number(value: str) -> str | None:
    normalized = re.sub(r"[\s-]", "", value)
    if not PHONE_RE.fullmatch(normalized):
        return None
    return normalized


def make_phone_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def send_phone_code(config: ServerConfig, phone_number: str, code: str) -> None:
    provider = config.sms_provider.strip().lower()
    if provider != SMS_PROVIDER_WEBHOOK:
        raise AuthProviderError(HTTPStatus.NOT_IMPLEMENTED, "sms_provider_missing", "生产短信服务尚未配置。")
    if not config.sms_secret or not config.sms_webhook_url:
        raise AuthProviderError(HTTPStatus.NOT_IMPLEMENTED, "sms_provider_missing", "生产短信服务缺少 webhook URL 或签名密钥。")

    body = {
        "phoneNumber": phone_number,
        "code": code,
        "ttlSeconds": PHONE_CODE_TTL_SECONDS,
        "purpose": "login",
    }
    if config.sms_template_id:
        body["templateId"] = config.sms_template_id
    payload = json_dumps_bytes(body)
    signature = hmac.new(config.sms_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    request = urllib.request.Request(
        config.sms_webhook_url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-XNP-Signature": signature,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status >= 300:
                raise AuthProviderError(HTTPStatus.BAD_GATEWAY, "sms_provider_failed", "短信服务发送失败。")
    except urllib.error.HTTPError as error:
        raise AuthProviderError(HTTPStatus.BAD_GATEWAY, "sms_provider_failed", f"短信服务发送失败：HTTP {error.code}。") from error
    except urllib.error.URLError as error:
        raise AuthProviderError(HTTPStatus.BAD_GATEWAY, "sms_provider_failed", f"短信服务不可用：{error.reason}。") from error


def exchange_wechat_code(config: ServerConfig, code: str) -> str:
    if not config.wechat_app_id or not config.wechat_app_secret:
        raise AuthProviderError(HTTPStatus.NOT_IMPLEMENTED, "wechat_provider_missing", "生产微信登录服务尚未配置。")

    query = urlencode(
        {
            "appid": config.wechat_app_id,
            "secret": config.wechat_app_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
    )
    separator = "&" if "?" in config.wechat_access_token_url else "?"
    url = config.wechat_access_token_url + separator + query
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        raise AuthProviderError(HTTPStatus.BAD_GATEWAY, "wechat_provider_failed", f"微信登录服务失败：HTTP {error.code}。") from error
    except urllib.error.URLError as error:
        raise AuthProviderError(HTTPStatus.BAD_GATEWAY, "wechat_provider_failed", f"微信登录服务不可用：{error.reason}。") from error

    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AuthProviderError(HTTPStatus.BAD_GATEWAY, "wechat_provider_failed", "微信登录服务返回内容无法识别。") from error

    errcode = data.get("errcode")
    if errcode not in (None, 0):
        raise AuthProviderError(HTTPStatus.UNAUTHORIZED, "invalid_wechat_code", "微信授权 code 无效或已过期。")

    subject = data.get("unionid") or data.get("openid")
    if not isinstance(subject, str) or not WECHAT_SUBJECT_RE.fullmatch(subject):
        raise AuthProviderError(HTTPStatus.BAD_GATEWAY, "wechat_provider_failed", "微信登录服务缺少可用账号标识。")
    return subject


def create_account_with_recovery(db: DatabaseConnection, config: ServerConfig) -> dict[str, str]:
    account_id = str(uuid.uuid4())
    recovery_key = "xnp_" + secrets.token_urlsafe(24)
    created_at = utc_now()
    db.execute(
        "INSERT INTO accounts(account_id, recovery_hash, created_at) VALUES (?, ?, ?)",
        (account_id, recovery_hash(config.secret_key, recovery_key), created_at),
    )
    return {
        "accountId": account_id,
        "recoveryKey": recovery_key,
        "createdAt": created_at,
    }


def app_review_phone_code(config: ServerConfig, phone_number: str) -> str | None:
    review_phone_number = normalize_phone_number(config.app_review_phone_number)
    review_code = config.app_review_phone_code.strip()
    if review_phone_number != phone_number or not re.fullmatch(r"^[0-9]{6}$", review_code):
        return None
    return review_code


def identity_session(db: DatabaseConnection, config: ServerConfig, provider: str, subject: str) -> dict[str, Any]:
    hashed = subject_hash(config.secret_key, provider, subject)
    row = db.execute(
        """
        SELECT accounts.account_id, accounts.created_at
        FROM account_identities
        JOIN accounts ON accounts.account_id = account_identities.account_id
        WHERE account_identities.provider = ?
          AND account_identities.subject_hash = ?
          AND accounts.deleted_at IS NULL
        """,
        (provider, hashed),
    ).fetchone()

    if row is None:
        db.execute(
            "DELETE FROM account_identities WHERE provider = ? AND subject_hash = ?",
            (provider, hashed),
        )
        created = create_account_with_recovery(db, config)
        account_id = created["accountId"]
        created_at = created["createdAt"]
        db.execute(
            "INSERT INTO account_identities(provider, subject_hash, account_id, created_at) VALUES (?, ?, ?, ?)",
            (provider, hashed, account_id, utc_now()),
        )
    else:
        account_id = row["account_id"]
        created_at = row["created_at"]

    response = {
        "accountId": account_id,
        "sessionToken": make_session_token(config.secret_key, account_id),
        "createdAt": created_at,
        "authProvider": provider,
    }
    return response


def connect(config: ServerConfig) -> DatabaseConnection:
    return connect_database(settings_from_environment(config.data_dir))


def upsert_phone_code(
    db: DatabaseConnection,
    phone_digest: str,
    code_digest: str,
    created_at: str,
    expires_at: int,
) -> None:
    if db.dialect == "mysql":
        db.execute(
            """
            INSERT INTO phone_login_codes(phone_hash, code_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                code_hash = VALUES(code_hash),
                created_at = VALUES(created_at),
                expires_at = VALUES(expires_at)
            """,
            (phone_digest, code_digest, created_at, expires_at),
        )
        return
    db.execute(
        """
        INSERT INTO phone_login_codes(phone_hash, code_hash, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(phone_hash) DO UPDATE SET
            code_hash = excluded.code_hash,
            created_at = excluded.created_at,
            expires_at = excluded.expires_at
        """,
        (phone_digest, code_digest, created_at, expires_at),
    )


# 覆盖前保留的历史版本数：客户端 bug 用坏数据覆盖唯一副本时，这是最后的救援手段。
SYNC_VERSIONS_TO_KEEP = 30

# ---- 家人共享（多看护人逐条增量同步）----
# 与整包 blob 备份并存：blob 是单账号灾备，family_records 是家庭内
# 按记录 LWW（updated_at_ms 新者胜）的协作通道，seq 游标增量拉取。
FAMILY_INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
FAMILY_INVITE_CODE_LENGTH = 6
FAMILY_MAX_MEMBERS = 6
FAMILY_RECORD_TYPES = {"baby", "feeding", "water", "sleep", "diaper", "growth", "vaccine", "milestone", "health"}
FAMILY_BATCH_LIMIT = 500
FAMILY_RECORD_PAYLOAD_LIMIT = 64 * 1024
FAMILY_PULL_LIMIT = 500


def generate_family_invite_code() -> str:
    return "".join(secrets.choice(FAMILY_INVITE_CODE_ALPHABET) for _ in range(FAMILY_INVITE_CODE_LENGTH))


def new_family_invite_code(db: DatabaseConnection) -> str:
    for _ in range(8):
        invite_code = generate_family_invite_code()
        if db.execute("SELECT 1 FROM families WHERE invite_code = ?", (invite_code,)).fetchone() is None:
            return invite_code
    raise RuntimeError("unable to generate unique family invite code")


def family_membership(db: DatabaseConnection, account_id: str):
    return db.execute(
        """
        SELECT m.family_id AS family_id, m.role AS role,
               f.invite_code AS invite_code, f.owner_account_id AS owner_account_id
        FROM family_members m
        JOIN families f ON f.family_id = m.family_id
        WHERE m.account_id = ?
        """,
        (account_id,),
    ).fetchone()


def family_member_count(db: DatabaseConnection, family_id: str) -> int:
    row = db.execute(
        "SELECT COUNT(*) AS member_count FROM family_members WHERE family_id = ?",
        (family_id,),
    ).fetchone()
    return int(row["member_count"])


def family_membership_response(db: DatabaseConnection, membership) -> dict:
    family = {
        "familyId": membership["family_id"],
        "role": membership["role"],
        "inviteCode": membership["invite_code"],
        "memberCount": family_member_count(db, membership["family_id"]),
    }
    if membership["role"] == "owner":
        rows = db.execute(
            """
            SELECT account_id, role, created_at FROM family_members
            WHERE family_id = ?
            ORDER BY CASE WHEN role = 'owner' THEN 0 ELSE 1 END, created_at ASC
            """,
            (membership["family_id"],),
        ).fetchall()
        family["members"] = [
            {"accountId": row["account_id"], "role": row["role"], "joinedAt": row["created_at"]}
            for row in rows
        ]
    return {"family": family}


def remove_family_membership(db: DatabaseConnection, membership, account_id: str) -> None:
    """删除成员资格；创建者离开时转移给最早加入的剩余成员。"""
    family_id = membership["family_id"]
    remaining = db.execute(
        """
        SELECT account_id FROM family_members
        WHERE family_id = ? AND account_id != ?
        ORDER BY created_at ASC, account_id ASC
        """,
        (family_id, account_id),
    ).fetchall()
    if not remaining:
        db.execute("DELETE FROM family_records WHERE family_id = ?", (family_id,))
        db.execute("DELETE FROM family_members WHERE family_id = ?", (family_id,))
        db.execute("DELETE FROM families WHERE family_id = ?", (family_id,))
        return
    if membership["role"] == "owner":
        successor_id = remaining[0]["account_id"]
        db.execute("UPDATE families SET owner_account_id = ? WHERE family_id = ?", (successor_id, family_id))
        db.execute("UPDATE family_members SET role = 'owner' WHERE family_id = ? AND account_id = ?", (family_id, successor_id))
    db.execute("DELETE FROM family_members WHERE family_id = ? AND account_id = ?", (family_id, account_id))


def upsert_family_record(
    db: DatabaseConnection,
    family_id: str,
    author_account_id: str,
    record_type: str,
    record_id: str,
    payload: bytes,
    updated_at_ms: int,
    deleted_at_ms: int | None,
) -> bool:
    """LWW：仅当来件不早于已存版本时替换；替换用删+插拿新 seq。返回是否接受。"""
    row = db.execute(
        """
        SELECT updated_at_ms FROM family_records
        WHERE family_id = ? AND record_type = ? AND record_id = ?
        """,
        (family_id, record_type, record_id),
    ).fetchone()
    if row is not None and int(row["updated_at_ms"]) > updated_at_ms:
        return False
    if row is not None:
        db.execute(
            "DELETE FROM family_records WHERE family_id = ? AND record_type = ? AND record_id = ?",
            (family_id, record_type, record_id),
        )
    db.execute(
        """
        INSERT INTO family_records(
            family_id, record_type, record_id, payload, updated_at_ms, deleted_at_ms, author_account_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (family_id, record_type, record_id, payload, updated_at_ms, deleted_at_ms, author_account_id),
    )
    return True


def archive_sync_version(db: DatabaseConnection, account_id: str, new_payload: bytes, archived_at: str) -> None:
    row = db.execute(
        "SELECT payload, updated_at FROM syncs WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    if row is None:
        return
    previous_payload = bytes(row["payload"])
    if previous_payload == new_payload:
        return
    version_row = db.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 AS next_version FROM sync_versions WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    next_version = int(version_row["next_version"])
    db.execute(
        """
        INSERT INTO sync_versions(account_id, version, payload, updated_at, archived_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (account_id, next_version, previous_payload, row["updated_at"], archived_at),
    )
    db.execute(
        "DELETE FROM sync_versions WHERE account_id = ? AND version <= ?",
        (account_id, next_version - SYNC_VERSIONS_TO_KEEP),
    )


def upsert_sync(db: DatabaseConnection, account_id: str, payload: bytes, updated_at: str) -> None:
    archive_sync_version(db, account_id, payload, updated_at)
    if db.dialect == "mysql":
        db.execute(
            """
            INSERT INTO syncs(account_id, payload, updated_at) VALUES (?, ?, ?)
            ON DUPLICATE KEY UPDATE payload = VALUES(payload), updated_at = VALUES(updated_at)
            """,
            (account_id, payload, updated_at),
        )
        return
    db.execute(
        """
        INSERT INTO syncs(account_id, payload, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(account_id) DO UPDATE SET payload = excluded.payload, updated_at = excluded.updated_at
        """,
        (account_id, payload, updated_at),
    )


def upsert_photo(
    db: DatabaseConnection,
    account_id: str,
    photo_id: str,
    content_type: str,
    size_bytes: int,
    digest: str,
    updated_at: str,
) -> None:
    parameters = (account_id, photo_id, content_type, size_bytes, digest, updated_at)
    if db.dialect == "mysql":
        db.execute(
            """
            INSERT INTO photos(account_id, photo_id, content_type, size_bytes, sha256, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                content_type = VALUES(content_type),
                size_bytes = VALUES(size_bytes),
                sha256 = VALUES(sha256),
                updated_at = VALUES(updated_at)
            """,
            parameters,
        )
        return
    db.execute(
        """
        INSERT INTO photos(account_id, photo_id, content_type, size_bytes, sha256, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(account_id, photo_id) DO UPDATE SET
            content_type = excluded.content_type,
            size_bytes = excluded.size_bytes,
            sha256 = excluded.sha256,
            updated_at = excluded.updated_at
        """,
        parameters,
    )


def insert_analytics_event(
    db: DatabaseConnection,
    event_id: str,
    account_hash: str,
    event_name: str,
    occurred_at: str,
    received_at: str,
    properties_json: str,
) -> None:
    parameters = (event_id, account_hash, event_name, occurred_at, received_at, properties_json)
    if db.dialect == "mysql":
        db.execute(
            """
            INSERT IGNORE INTO analytics_events(
                event_id, account_hash, event_name, occurred_at, received_at, properties_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            parameters,
        )
        return
    db.execute(
        """
        INSERT OR IGNORE INTO analytics_events(
            event_id, account_hash, event_name, occurred_at, received_at, properties_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        parameters,
    )


class XiaoNaiPingHandler(BaseHTTPRequestHandler):
    server_version = "XiaoNaiPingAPI/1.0"
    config: ServerConfig

    @staticmethod
    def redacted_log_path(raw_path: str) -> str:
        path = urlparse(raw_path).path
        if path.startswith("/v1/photos/"):
            return "/v1/photos/<redacted>"
        return path

    def log_message(self, format: str, *args: Any) -> None:
        path = self.redacted_log_path(self.path)
        status = args[1] if len(args) > 1 else ""
        print(f"{self.address_string()} {self.command} {path} {status}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/healthz":
            self.write_json({"status": "ok", "time": utc_now()})
            return
        if path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if path in STATIC_ROUTES:
            self.handle_static(path)
            return
        if path == "/internal/metrics":
            self.handle_internal_metrics()
            return

        account_id = self.require_account()
        if account_id is None:
            return

        if path == "/v1/account":
            self.handle_get_account(account_id)
        elif path == "/v1/sync":
            self.handle_get_sync(account_id)
        elif path == "/v1/family":
            self.handle_get_family(account_id)
        elif path == "/v1/family/records":
            self.handle_get_family_records(account_id)
        elif path == "/v1/photos":
            self.handle_list_photos(account_id)
        elif path.startswith("/v1/photos/"):
            self.handle_get_photo(account_id, path.removeprefix("/v1/photos/"))
        else:
            self.write_error(HTTPStatus.NOT_FOUND, "not_found", "接口不存在。")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/v1/accounts":
            self.handle_create_account()
        elif path == "/v1/sessions/recover":
            self.handle_recover_session()
        elif path == "/v1/auth/phone/request-code":
            self.handle_phone_request_code()
        elif path == "/v1/auth/phone/verify":
            self.handle_phone_verify()
        elif path == "/v1/auth/wechat/login":
            self.handle_wechat_login()
        elif path == "/v1/analytics/events":
            account_id = self.require_account()
            if account_id is not None:
                self.handle_post_analytics_events(account_id)
        elif path == "/v1/family":
            account_id = self.require_account()
            if account_id is not None:
                self.handle_create_family(account_id)
        elif path == "/v1/family/join":
            account_id = self.require_account()
            if account_id is not None:
                self.handle_join_family(account_id)
        elif path == "/v1/family/invite/rotate":
            account_id = self.require_account()
            if account_id is not None:
                self.handle_rotate_family_invite(account_id)
        else:
            self.write_error(HTTPStatus.NOT_FOUND, "not_found", "接口不存在。")

    def do_PUT(self) -> None:
        account_id = self.require_account()
        if account_id is None:
            return

        path = urlparse(self.path).path
        if path == "/v1/sync":
            self.handle_put_sync(account_id)
        elif path == "/v1/family/records":
            self.handle_put_family_records(account_id)
        elif path.startswith("/v1/photos/"):
            self.handle_put_photo(account_id, path.removeprefix("/v1/photos/"))
        else:
            self.write_error(HTTPStatus.NOT_FOUND, "not_found", "接口不存在。")

    def do_DELETE(self) -> None:
        account_id = self.require_account()
        if account_id is None:
            return

        path = urlparse(self.path).path
        if path == "/v1/account":
            self.handle_delete_account(account_id)
        elif path == "/v1/family":
            self.handle_leave_family(account_id)
        elif path.startswith("/v1/family/members/"):
            self.handle_remove_family_member(account_id, path.removeprefix("/v1/family/members/"))
        elif path.startswith("/v1/photos/"):
            self.handle_delete_photo(account_id, path.removeprefix("/v1/photos/"))
        else:
            self.write_error(HTTPStatus.NOT_FOUND, "not_found", "接口不存在。")

    def handle_create_account(self) -> None:
        with connect(self.config) as db:
            created = create_account_with_recovery(db, self.config)
            db.commit()

        self.write_json(
            {
                "accountId": created["accountId"],
                "sessionToken": make_session_token(self.config.secret_key, created["accountId"]),
                "recoveryKey": created["recoveryKey"],
                "createdAt": created["createdAt"],
                "authProvider": "recovery_key",
            },
            status=HTTPStatus.CREATED,
        )

    def handle_recover_session(self) -> None:
        body = self.read_json(MAX_SYNC_BYTES)
        if not isinstance(body, dict):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_json", "请求体必须是 JSON 对象。")
            return

        recovery_key = body.get("recoveryKey")
        if not isinstance(recovery_key, str) or not recovery_key:
            self.write_error(HTTPStatus.BAD_REQUEST, "missing_recovery_key", "缺少恢复密钥。")
            return

        key_hash = recovery_hash(self.config.secret_key, recovery_key)
        with connect(self.config) as db:
            row = db.execute(
                "SELECT account_id, created_at FROM accounts WHERE recovery_hash = ? AND deleted_at IS NULL",
                (key_hash,),
            ).fetchone()

        if row is None:
            self.write_error(HTTPStatus.UNAUTHORIZED, "invalid_recovery_key", "恢复密钥无效或账号已删除。")
            return

        self.write_json(
            {
                "accountId": row["account_id"],
                "sessionToken": make_session_token(self.config.secret_key, row["account_id"]),
                "createdAt": row["created_at"],
                "authProvider": "recovery_key",
            }
        )

    def handle_phone_request_code(self) -> None:
        body = self.read_json(MAX_SYNC_BYTES)
        if not isinstance(body, dict):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_json", "请求体必须是 JSON 对象。")
            return
        raw_phone = body.get("phoneNumber")
        if not isinstance(raw_phone, str):
            self.write_error(HTTPStatus.BAD_REQUEST, "missing_phone_number", "缺少手机号。")
            return
        phone_number = normalize_phone_number(raw_phone)
        if phone_number is None:
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_phone_number", "手机号必须使用 E.164 格式，例如 +85251234567。")
            return
        review_code = app_review_phone_code(self.config, phone_number)
        code = review_code or make_phone_code()
        if not self.config.auth_debug_mode and review_code is None:
            try:
                send_phone_code(self.config, phone_number, code)
            except AuthProviderError as error:
                self.write_error(error.status, error.code, error.message)
                return

        now = int(time.time())
        phone_digest = subject_hash(self.config.secret_key, "phone", phone_number)
        code_digest = subject_hash(self.config.secret_key, "phone_code", f"{phone_number}:{code}")
        with connect(self.config) as db:
            upsert_phone_code(db, phone_digest, code_digest, utc_now(), now + PHONE_CODE_TTL_SECONDS)
            db.commit()

        response = {"sent": True, "expiresInSeconds": PHONE_CODE_TTL_SECONDS}
        if self.config.auth_debug_mode:
            response["debugCode"] = code
        self.write_json(response)

    def handle_phone_verify(self) -> None:
        body = self.read_json(MAX_SYNC_BYTES)
        if not isinstance(body, dict):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_json", "请求体必须是 JSON 对象。")
            return
        phone_number = normalize_phone_number(body.get("phoneNumber", "") if isinstance(body.get("phoneNumber"), str) else "")
        code = body.get("code")
        if phone_number is None:
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_phone_number", "手机号必须使用 E.164 格式。")
            return
        if not isinstance(code, str) or not re.fullmatch(r"^[0-9]{6}$", code):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_phone_code", "验证码必须是 6 位数字。")
            return

        phone_digest = subject_hash(self.config.secret_key, "phone", phone_number)
        code_digest = subject_hash(self.config.secret_key, "phone_code", f"{phone_number}:{code}")
        with connect(self.config) as db:
            row = db.execute(
                "SELECT code_hash, expires_at FROM phone_login_codes WHERE phone_hash = ?",
                (phone_digest,),
            ).fetchone()
            if row is None or row["expires_at"] < int(time.time()) or not hmac.compare_digest(row["code_hash"], code_digest):
                self.write_error(HTTPStatus.UNAUTHORIZED, "invalid_phone_code", "验证码无效或已过期。")
                return
            db.execute("DELETE FROM phone_login_codes WHERE phone_hash = ?", (phone_digest,))
            response = identity_session(db, self.config, "phone", phone_number)
            db.commit()
        self.write_json(response)

    def handle_wechat_login(self) -> None:
        body = self.read_json(MAX_SYNC_BYTES)
        if not isinstance(body, dict):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_json", "请求体必须是 JSON 对象。")
            return
        code = body.get("code")
        if not isinstance(code, str) or not code:
            self.write_error(HTTPStatus.BAD_REQUEST, "missing_wechat_code", "缺少微信授权 code。")
            return
        if self.config.auth_debug_mode and code.startswith(WECHAT_DEBUG_PREFIX):
            subject = code.removeprefix(WECHAT_DEBUG_PREFIX)
            if not WECHAT_SUBJECT_RE.fullmatch(subject):
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid_wechat_subject", "微信调试标识不合法。")
                return
        else:
            try:
                subject = exchange_wechat_code(self.config, code)
            except AuthProviderError as error:
                self.write_error(error.status, error.code, error.message)
                return

        with connect(self.config) as db:
            response = identity_session(db, self.config, "wechat", subject)
            db.commit()
        self.write_json(response)

    def handle_get_account(self, account_id: str) -> None:
        with connect(self.config) as db:
            row = db.execute(
                "SELECT account_id, created_at FROM accounts WHERE account_id = ? AND deleted_at IS NULL",
                (account_id,),
            ).fetchone()
        if row is None:
            self.write_error(HTTPStatus.UNAUTHORIZED, "account_deleted", "账号不存在或已删除。")
            return
        self.write_json({"accountId": row["account_id"], "createdAt": row["created_at"]})

    def handle_get_family(self, account_id: str) -> None:
        with connect(self.config) as db:
            membership = family_membership(db, account_id)
            if membership is None:
                self.write_json({"family": None})
                return
            response = family_membership_response(db, membership)
        self.write_json(response)

    def handle_create_family(self, account_id: str) -> None:
        with connect(self.config) as db:
            existing = family_membership(db, account_id)
            if existing is not None:
                # 幂等：已在家庭里则直接返回现有信息。
                response = family_membership_response(db, existing)
                self.write_json(response)
                return

            family_id = str(uuid.uuid4())
            invite_code = new_family_invite_code(db)

            now = utc_now()
            db.execute(
                "INSERT INTO families(family_id, owner_account_id, invite_code, created_at) VALUES (?, ?, ?, ?)",
                (family_id, account_id, invite_code, now),
            )
            db.execute(
                "INSERT INTO family_members(family_id, account_id, role, created_at) VALUES (?, ?, ?, ?)",
                (family_id, account_id, "owner", now),
            )
            db.commit()

        self.write_json(
            {"family": {"familyId": family_id, "role": "owner", "inviteCode": invite_code, "memberCount": 1}},
            status=HTTPStatus.CREATED,
        )

    def handle_join_family(self, account_id: str) -> None:
        body = self.read_json(MAX_SYNC_BYTES)
        if not isinstance(body, dict):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_json", "请求体必须是 JSON 对象。")
            return
        invite_code = body.get("inviteCode")
        if not isinstance(invite_code, str):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_invite_code", "邀请码格式不正确。")
            return
        invite_code = invite_code.strip().upper()
        if not re.fullmatch(r"^[A-Z0-9]{4,16}$", invite_code):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_invite_code", "邀请码格式不正确。")
            return

        with connect(self.config) as db:
            family_row = db.execute(
                "SELECT family_id FROM families WHERE invite_code = ?",
                (invite_code,),
            ).fetchone()
            if family_row is None:
                self.write_error(HTTPStatus.NOT_FOUND, "invite_code_not_found", "邀请码不存在或已失效。")
                return
            family_id = family_row["family_id"]

            existing = family_membership(db, account_id)
            if existing is not None:
                if existing["family_id"] == family_id:
                    response = family_membership_response(db, existing)
                    self.write_json(response)
                    return
                self.write_error(HTTPStatus.CONFLICT, "already_in_family", "当前账号已在另一个家庭中。")
                return

            if family_member_count(db, family_id) >= FAMILY_MAX_MEMBERS:
                self.write_error(HTTPStatus.CONFLICT, "family_full", "这个家庭的成员数已达上限。")
                return

            db.execute(
                "INSERT INTO family_members(family_id, account_id, role, created_at) VALUES (?, ?, ?, ?)",
                (family_id, account_id, "member", utc_now()),
            )
            membership = family_membership(db, account_id)
            response = family_membership_response(db, membership)
            db.commit()
        self.write_json(response, status=HTTPStatus.CREATED)

    def handle_rotate_family_invite(self, account_id: str) -> None:
        with connect(self.config) as db:
            membership = family_membership(db, account_id)
            if membership is None:
                self.write_error(HTTPStatus.FORBIDDEN, "not_in_family", "还没有加入家庭。")
                return
            if membership["role"] != "owner":
                self.write_error(HTTPStatus.FORBIDDEN, "not_family_owner", "只有创建者可以更换邀请码。")
                return
            invite_code = new_family_invite_code(db)
            db.execute("UPDATE families SET invite_code = ? WHERE family_id = ?", (invite_code, membership["family_id"]))
            membership = family_membership(db, account_id)
            response = family_membership_response(db, membership)
            db.commit()
        self.write_json(response)

    def handle_leave_family(self, account_id: str) -> None:
        with connect(self.config) as db:
            membership = family_membership(db, account_id)
            if membership is None:
                self.write_error(HTTPStatus.NOT_FOUND, "family_not_found", "当前账号没有加入家庭。")
                return
            remove_family_membership(db, membership, account_id)
            db.commit()
        self.write_json({"left": True})

    def handle_remove_family_member(self, account_id: str, member_account_id: str) -> None:
        if not self.is_safe_id(member_account_id):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_member_id", "成员 ID 不合法。")
            return
        with connect(self.config) as db:
            membership = family_membership(db, account_id)
            if membership is None:
                self.write_error(HTTPStatus.FORBIDDEN, "not_in_family", "还没有加入家庭。")
                return
            if membership["role"] != "owner":
                self.write_error(HTTPStatus.FORBIDDEN, "not_family_owner", "只有创建者可以移除成员。")
                return
            if member_account_id == account_id:
                self.write_error(HTTPStatus.BAD_REQUEST, "cannot_remove_owner", "创建者请使用退出家庭。")
                return
            target = db.execute(
                "SELECT 1 FROM family_members WHERE family_id = ? AND account_id = ?",
                (membership["family_id"], member_account_id),
            ).fetchone()
            if target is None:
                self.write_error(HTTPStatus.NOT_FOUND, "family_member_not_found", "成员不存在或已离开。")
                return
            db.execute(
                "DELETE FROM family_members WHERE family_id = ? AND account_id = ?",
                (membership["family_id"], member_account_id),
            )
            db.commit()
        self.write_json({"removedAccountId": member_account_id, "removed": True})

    def handle_put_family_records(self, account_id: str) -> None:
        body = self.read_json(MAX_SYNC_BYTES)
        if not isinstance(body, dict) or not isinstance(body.get("records"), list):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_records", "请求体必须包含 records 数组。")
            return
        records = body["records"]
        if len(records) > FAMILY_BATCH_LIMIT:
            self.write_error(HTTPStatus.BAD_REQUEST, "batch_too_large", f"单批最多 {FAMILY_BATCH_LIMIT} 条。")
            return

        parsed = []
        for item in records:
            if not isinstance(item, dict):
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid_records", "记录必须是 JSON 对象。")
                return
            record_type = item.get("recordType")
            record_id = item.get("recordId")
            payload = item.get("payload")
            updated_at_ms = item.get("updatedAtMs")
            deleted_at_ms = item.get("deletedAtMs")
            if record_type not in FAMILY_RECORD_TYPES:
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid_record_type", "不支持的记录类型。")
                return
            if not isinstance(record_id, str) or not self.is_safe_id(record_id):
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid_record_id", "记录 ID 不合法。")
                return
            if not isinstance(payload, str) or len(payload.encode("utf-8")) > FAMILY_RECORD_PAYLOAD_LIMIT:
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid_record_payload", "记录 payload 缺失或过大。")
                return
            if not isinstance(updated_at_ms, int) or updated_at_ms <= 0:
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid_record_updated_at", "updatedAtMs 必须是正整数毫秒。")
                return
            if deleted_at_ms is not None and (not isinstance(deleted_at_ms, int) or deleted_at_ms <= 0):
                self.write_error(HTTPStatus.BAD_REQUEST, "invalid_record_deleted_at", "deletedAtMs 必须是正整数毫秒。")
                return
            parsed.append((record_type, record_id, payload.encode("utf-8"), updated_at_ms, deleted_at_ms))

        with connect(self.config) as db:
            membership = family_membership(db, account_id)
            if membership is None:
                self.write_error(HTTPStatus.FORBIDDEN, "not_in_family", "还没有加入家庭。")
                return
            family_id = membership["family_id"]
            accepted = 0
            stale = 0
            for record_type, record_id, payload, updated_at_ms, deleted_at_ms in parsed:
                if upsert_family_record(
                    db, family_id, account_id, record_type, record_id, payload, updated_at_ms, deleted_at_ms
                ):
                    accepted += 1
                else:
                    stale += 1
            cursor_row = db.execute(
                "SELECT COALESCE(MAX(seq), 0) AS cursor_seq FROM family_records WHERE family_id = ?",
                (family_id,),
            ).fetchone()
            db.commit()

        self.write_json({"accepted": accepted, "staleSkipped": stale, "cursor": int(cursor_row["cursor_seq"])})

    def handle_get_family_records(self, account_id: str) -> None:
        query = parse_qs(urlparse(self.path).query)
        since_raw = (query.get("since") or ["0"])[0]
        try:
            since = int(since_raw)
        except ValueError:
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_cursor", "since 游标必须是整数。")
            return

        with connect(self.config) as db:
            membership = family_membership(db, account_id)
            if membership is None:
                self.write_error(HTTPStatus.FORBIDDEN, "not_in_family", "还没有加入家庭。")
                return
            rows = db.execute(
                """
                SELECT seq, record_type, record_id, payload, updated_at_ms, deleted_at_ms, author_account_id
                FROM family_records
                WHERE family_id = ? AND seq > ?
                ORDER BY seq ASC
                LIMIT ?
                """,
                (membership["family_id"], since, FAMILY_PULL_LIMIT),
            ).fetchall()

        changes = []
        cursor = since
        for row in rows:
            cursor = int(row["seq"])
            changes.append(
                {
                    "recordType": row["record_type"],
                    "recordId": row["record_id"],
                    "payload": bytes(row["payload"]).decode("utf-8"),
                    "updatedAtMs": int(row["updated_at_ms"]),
                    "deletedAtMs": int(row["deleted_at_ms"]) if row["deleted_at_ms"] is not None else None,
                    "mine": row["author_account_id"] == account_id,
                }
            )
        self.write_json({"records": changes, "cursor": cursor, "hasMore": len(rows) == FAMILY_PULL_LIMIT})

    def handle_put_sync(self, account_id: str) -> None:
        payload = self.read_body(MAX_SYNC_BYTES)
        try:
            json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_sync", "同步必须是 UTF-8 JSON。")
            return

        now = utc_now()
        with connect(self.config) as db:
            upsert_sync(db, account_id, payload, now)
            db.commit()

        self.write_json({"updatedAt": now, "sizeBytes": len(payload)})

    def handle_get_sync(self, account_id: str) -> None:
        with connect(self.config) as db:
            row = db.execute(
                "SELECT payload, updated_at FROM syncs WHERE account_id = ?",
                (account_id,),
            ).fetchone()
        if row is None:
            self.write_error(HTTPStatus.NOT_FOUND, "sync_not_found", "还没有云端同步。")
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("X-XNP-Updated-At", row["updated_at"])
        self.send_header("Content-Length", str(len(row["payload"])))
        self.end_headers()
        self.wfile.write(row["payload"])

    def handle_put_photo(self, account_id: str, photo_id: str) -> None:
        if not self.is_safe_id(photo_id):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_photo_id", "照片 ID 不合法。")
            return

        content_type = self.headers.get("Content-Type") or "application/octet-stream"
        if content_type.split(";")[0].strip().lower() not in {"image/jpeg", "image/png", "application/octet-stream"}:
            self.write_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "unsupported_photo_type", "只允许上传 JPEG 或 PNG。")
            return

        payload = self.read_body(MAX_PHOTO_BYTES)
        digest = hashlib.sha256(payload).hexdigest()
        self.config.storage().put_photo(account_id, photo_id, payload, content_type)

        now = utc_now()
        with connect(self.config) as db:
            upsert_photo(db, account_id, photo_id, content_type, len(payload), digest, now)
            db.commit()

        self.write_json(
            {
                "photoId": photo_id,
                "updatedAt": now,
                "sizeBytes": len(payload),
                "sha256": digest,
            }
        )

    def handle_list_photos(self, account_id: str) -> None:
        with connect(self.config) as db:
            rows = db.execute(
                """
                SELECT photo_id, content_type, size_bytes, sha256, updated_at
                FROM photos
                WHERE account_id = ?
                ORDER BY updated_at DESC
                """,
                (account_id,),
            ).fetchall()

        self.write_json(
            {
                "photos": [
                    {
                        "photoId": row["photo_id"],
                        "contentType": row["content_type"],
                        "sizeBytes": row["size_bytes"],
                        "sha256": row["sha256"],
                        "updatedAt": row["updated_at"],
                    }
                    for row in rows
                ]
            }
        )

    def handle_get_photo(self, account_id: str, photo_id: str) -> None:
        if not self.is_safe_id(photo_id):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_photo_id", "照片 ID 不合法。")
            return

        with connect(self.config) as db:
            row = db.execute(
                "SELECT content_type, size_bytes FROM photos WHERE account_id = ? AND photo_id = ?",
                (account_id, photo_id),
            ).fetchone()

        if row is None:
            self.write_error(HTTPStatus.NOT_FOUND, "photo_not_found", "照片不存在或已删除。")
            return
        payload = self.config.storage().get_photo(account_id, photo_id)
        if payload is None:
            self.write_error(HTTPStatus.NOT_FOUND, "photo_not_found", "照片不存在或已删除。")
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", row["content_type"])
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_delete_photo(self, account_id: str, photo_id: str) -> None:
        if not self.is_safe_id(photo_id):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_photo_id", "照片 ID 不合法。")
            return

        self.config.storage().delete_photo(account_id, photo_id)
        with connect(self.config) as db:
            db.execute("DELETE FROM photos WHERE account_id = ? AND photo_id = ?", (account_id, photo_id))
            db.commit()
        self.write_json({"photoId": photo_id, "deleted": True})

    def handle_post_analytics_events(self, account_id: str) -> None:
        body = self.read_json(MAX_ANALYTICS_BYTES)
        if not isinstance(body, dict):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_json", "请求体必须是 JSON 对象。")
            return

        events = body.get("events")
        if not isinstance(events, list):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_events", "缺少事件数组。")
            return
        if len(events) > MAX_ANALYTICS_EVENTS:
            self.write_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "too_many_events", "单次最多提交 50 条事件。")
            return

        account_digest = subject_hash(self.config.secret_key, "analytics_account", account_id)
        received_at = utc_now()
        accepted = 0
        dropped = 0
        retention_days = analytics_retention_days()

        with connect(self.config) as db:
            db.execute("DELETE FROM analytics_events WHERE received_at < ?", (utc_days_ago(retention_days),))
            for event in events:
                normalized = self.normalize_analytics_event(event, received_at)
                if normalized is None:
                    dropped += 1
                    continue
                insert_analytics_event(
                    db,
                    normalized["event_id"],
                    account_digest,
                    normalized["event_name"],
                    normalized["occurred_at"],
                    received_at,
                    normalized["properties_json"],
                )
                accepted += 1
            db.commit()

        self.write_json(
            {
                "accepted": accepted,
                "dropped": dropped,
                "retentionDays": retention_days,
                "storage": "first_party_aggregate_only",
            }
        )

    def handle_static(self, path: str) -> None:
        if path == "/internal/dashboard" and not self.internal_dashboard_allowed():
            self.write_error(HTTPStatus.NOT_FOUND, "not_found", "接口不存在。")
            return
        file_name, content_type = STATIC_ROUTES[path]
        static_path = Path(__file__).resolve().parents[1] / "static" / file_name
        if not static_path.exists():
            self.write_error(HTTPStatus.NOT_FOUND, "static_not_found", "页面不存在。")
            return
        payload = static_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        cache_control = "no-store" if path == "/internal/dashboard" else "public, max-age=300"
        self.send_header("Cache-Control", cache_control)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def internal_dashboard_allowed(self) -> bool:
        forwarded_for = self.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            client_ip = self.client_address[0] if self.client_address else ""
            return internal_client_allowed(client_ip, forwarded_for)
        if self.config.auth_debug_mode:
            return True
        client_ip = self.client_address[0] if self.client_address else ""
        return internal_client_allowed(client_ip)

    def handle_internal_metrics(self) -> None:
        if not self.config.admin_token:
            self.write_error(HTTPStatus.NOT_FOUND, "not_found", "接口不存在。")
            return
        authorization = self.headers.get("Authorization") or ""
        supplied_token = authorization.removeprefix("Bearer ").strip() if authorization.startswith("Bearer ") else ""
        if not supplied_token or not hmac.compare_digest(supplied_token, self.config.admin_token):
            self.write_error(HTTPStatus.UNAUTHORIZED, "invalid_admin_token", "管理员令牌无效。")
            return

        with connect(self.config) as db:
            active_accounts = db.execute(
                "SELECT COUNT(*) AS count FROM accounts WHERE deleted_at IS NULL"
            ).fetchone()["count"]
            deleted_accounts = db.execute(
                "SELECT COUNT(*) AS count FROM accounts WHERE deleted_at IS NOT NULL"
            ).fetchone()["count"]
            total_accounts = db.execute("SELECT COUNT(*) AS count FROM accounts").fetchone()["count"]
            accounts_last_day = db.execute(
                "SELECT COUNT(*) AS count FROM accounts WHERE created_at >= ?",
                (utc_days_ago(1),),
            ).fetchone()["count"]
            accounts_last_week = db.execute(
                "SELECT COUNT(*) AS count FROM accounts WHERE created_at >= ?",
                (utc_days_ago(7),),
            ).fetchone()["count"]
            accounts_with_sync = db.execute("SELECT COUNT(*) AS count FROM syncs").fetchone()["count"]
            sync_totals = db.execute(
                "SELECT COALESCE(SUM(LENGTH(payload)), 0) AS bytes, MAX(updated_at) AS latest FROM syncs"
            ).fetchone()
            photo_totals = db.execute(
                "SELECT COUNT(*) AS count, COALESCE(SUM(size_bytes), 0) AS bytes, MAX(updated_at) AS latest FROM photos"
            ).fetchone()
            identity_rows = db.execute(
                "SELECT provider, COUNT(*) AS count FROM account_identities GROUP BY provider ORDER BY provider"
            ).fetchall()
            pending_phone_codes = db.execute(
                "SELECT COUNT(*) AS count FROM phone_login_codes WHERE expires_at >= ?",
                (int(time.time()),),
            ).fetchone()["count"]
            deletion_totals = db.execute(
                """
                SELECT COUNT(*) AS count,
                       COALESCE(SUM(photo_count), 0) AS photo_count,
                       MAX(deleted_at) AS latest
                FROM deletion_audit
                """
            ).fetchone()
            analytics_events_last_day = db.execute(
                "SELECT COUNT(*) AS count FROM analytics_events WHERE received_at >= ?",
                (utc_days_ago(1),),
            ).fetchone()["count"]
            analytics_events_last_week = db.execute(
                "SELECT COUNT(*) AS count FROM analytics_events WHERE received_at >= ?",
                (utc_days_ago(7),),
            ).fetchone()["count"]
            analytics_actors_last_day = db.execute(
                "SELECT COUNT(DISTINCT account_hash) AS count FROM analytics_events WHERE received_at >= ?",
                (utc_days_ago(1),),
            ).fetchone()["count"]
            analytics_actors_last_week = db.execute(
                "SELECT COUNT(DISTINCT account_hash) AS count FROM analytics_events WHERE received_at >= ?",
                (utc_days_ago(7),),
            ).fetchone()["count"]
            top_analytics_events = db.execute(
                """
                SELECT event_name, COUNT(*) AS count
                FROM analytics_events
                WHERE received_at >= ?
                GROUP BY event_name
                ORDER BY count DESC, event_name ASC
                LIMIT 8
                """,
                (utc_days_ago(7),),
            ).fetchall()

            # 30 天日粒度序列：仪表盘趋势图的数据源。
            # 时间戳是 ISO 字符串，SUBSTR(…,1,10) 即 UTC 日期，SQLite/MySQL 通用。
            series_window_start = utc_days_ago(29)
            new_accounts_daily = db.execute(
                """
                SELECT SUBSTR(created_at, 1, 10) AS day, COUNT(*) AS count
                FROM accounts
                WHERE created_at >= ?
                GROUP BY SUBSTR(created_at, 1, 10)
                ORDER BY day
                """,
                (series_window_start,),
            ).fetchall()
            analytics_daily = db.execute(
                """
                SELECT SUBSTR(received_at, 1, 10) AS day,
                       COUNT(*) AS events,
                       COUNT(DISTINCT account_hash) AS actors
                FROM analytics_events
                WHERE received_at >= ?
                GROUP BY SUBSTR(received_at, 1, 10)
                ORDER BY day
                """,
                (series_window_start,),
            ).fetchall()
            sync_activity_daily = db.execute(
                """
                SELECT SUBSTR(archived_at, 1, 10) AS day,
                       COUNT(*) AS count,
                       COUNT(DISTINCT account_id) AS accounts
                FROM sync_versions
                WHERE archived_at >= ?
                GROUP BY SUBSTR(archived_at, 1, 10)
                ORDER BY day
                """,
                (series_window_start,),
            ).fetchall()
            photo_uploads_daily = db.execute(
                """
                SELECT SUBSTR(updated_at, 1, 10) AS day, COUNT(*) AS count
                FROM photos
                WHERE updated_at >= ?
                GROUP BY SUBSTR(updated_at, 1, 10)
                ORDER BY day
                """,
                (series_window_start,),
            ).fetchall()
            family_totals = db.execute("SELECT COUNT(*) AS count FROM families").fetchone()["count"]
            family_member_totals = db.execute("SELECT COUNT(*) AS count FROM family_members").fetchone()["count"]
            multi_member_families = db.execute(
                """
                SELECT COUNT(*) AS count FROM (
                    SELECT family_id FROM family_members GROUP BY family_id HAVING COUNT(*) >= 2
                ) AS multi
                """
            ).fetchone()["count"]

        self.write_json(
            {
                "generatedAt": utc_now(),
                "databaseBackend": settings_from_environment(self.config.data_dir).backend,
                "storageBackend": os.environ.get("XNP_STORAGE_BACKEND", "disk"),
                "totalAccounts": int(total_accounts),
                "activeAccounts": int(active_accounts),
                "deletedAccounts": int(deleted_accounts),
                "newAccountsLast24h": int(accounts_last_day),
                "newAccountsLast7d": int(accounts_last_week),
                "accountsWithSync": int(accounts_with_sync),
                "syncBytes": int(sync_totals["bytes"] or 0),
                "latestSyncAt": sync_totals["latest"],
                "photoObjects": int(photo_totals["count"]),
                "photoBytes": int(photo_totals["bytes"]),
                "latestPhotoAt": photo_totals["latest"],
                "pendingPhoneCodes": int(pending_phone_codes),
                "authIdentities": {row["provider"]: int(row["count"]) for row in identity_rows},
                "deletionAudit": {
                    "deletedAccounts": int(deletion_totals["count"]),
                    "deletedPhotoObjects": int(deletion_totals["photo_count"] or 0),
                    "latestDeletedAt": deletion_totals["latest"],
                },
                "analytics": {
                    "retentionDays": analytics_retention_days(),
                    "eventsLast24h": int(analytics_events_last_day),
                    "eventsLast7d": int(analytics_events_last_week),
                    "actorsLast24h": int(analytics_actors_last_day),
                    "actorsLast7d": int(analytics_actors_last_week),
                    "topEventsLast7d": [
                        {"eventName": row["event_name"], "count": int(row["count"])}
                        for row in top_analytics_events
                    ],
                },
                "family": {
                    "families": int(family_totals),
                    "members": int(family_member_totals),
                    "familiesWithPartner": int(multi_member_families),
                },
                "series": {
                    "windowDays": 30,
                    "newAccountsDaily": [
                        {"day": row["day"], "count": int(row["count"])} for row in new_accounts_daily
                    ],
                    "analyticsDaily": [
                        {"day": row["day"], "events": int(row["events"]), "actors": int(row["actors"])}
                        for row in analytics_daily
                    ],
                    "syncActivityDaily": [
                        {"day": row["day"], "count": int(row["count"]), "accounts": int(row["accounts"])}
                        for row in sync_activity_daily
                    ],
                    "photoUploadsDaily": [
                        {"day": row["day"], "count": int(row["count"])} for row in photo_uploads_daily
                    ],
                },
            }
        )

    def handle_delete_account(self, account_id: str) -> None:
        with connect(self.config) as db:
            photo_count = db.execute("SELECT COUNT(*) AS count FROM photos WHERE account_id = ?", (account_id,)).fetchone()[
                "count"
            ]
            had_sync = db.execute("SELECT 1 FROM syncs WHERE account_id = ?", (account_id,)).fetchone() is not None
            analytics_digest = subject_hash(self.config.secret_key, "analytics_account", account_id)
            analytics_count = db.execute(
                "SELECT COUNT(*) AS count FROM analytics_events WHERE account_hash = ?",
                (analytics_digest,),
            ).fetchone()["count"]
            membership = family_membership(db, account_id)
            now = utc_now()
            if membership is not None:
                remove_family_membership(db, membership, account_id)
            db.execute("DELETE FROM syncs WHERE account_id = ?", (account_id,))
            db.execute("DELETE FROM photos WHERE account_id = ?", (account_id,))
            db.execute("DELETE FROM account_identities WHERE account_id = ?", (account_id,))
            db.execute("DELETE FROM analytics_events WHERE account_hash = ?", (analytics_digest,))
            db.execute("UPDATE accounts SET deleted_at = ? WHERE account_id = ?", (now, account_id))
            db.execute(
                """
                INSERT INTO deletion_audit(audit_id, account_id, deleted_at, sync_deleted, photo_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), account_id, now, int(had_sync), int(photo_count)),
            )
            db.commit()

        self.config.storage().delete_account(account_id)

        self.write_json(
            {
                "accountId": account_id,
                "deletedAt": now,
                "syncDeleted": had_sync,
                "photoCountDeleted": photo_count,
                "analyticsEventsDeleted": int(analytics_count),
            }
        )

    @staticmethod
    def normalize_analytics_event(event: Any, default_occurred_at: str) -> dict[str, str] | None:
        if not isinstance(event, dict):
            return None

        event_id = event.get("eventId")
        event_name = event.get("name")
        occurred_at = event.get("occurredAt", default_occurred_at)
        raw_properties = event.get("properties", {})

        if not isinstance(event_id, str) or SAFE_ANALYTICS_EVENT_ID_RE.fullmatch(event_id) is None:
            return None
        if not isinstance(event_name, str) or event_name not in ANALYTICS_EVENT_NAMES:
            return None
        if not isinstance(occurred_at, str) or len(occurred_at) > 40 or not re.fullmatch(r"^[0-9T:+\-.Z]{10,40}$", occurred_at):
            return None
        if raw_properties is None:
            raw_properties = {}
        if not isinstance(raw_properties, dict) or len(raw_properties) > 8:
            return None

        properties: dict[str, str] = {}
        for key, value in raw_properties.items():
            if not isinstance(key, str) or not isinstance(value, str):
                return None
            normalized_key = re.sub(r"[^a-z0-9]", "", key.lower())
            if any(fragment in normalized_key for fragment in ANALYTICS_FORBIDDEN_PROPERTY_FRAGMENTS):
                return None
            allowed_values = ANALYTICS_PROPERTY_VALUES.get(key)
            if allowed_values is None or value not in allowed_values:
                return None
            properties[key] = value

        return {
            "event_id": event_id,
            "event_name": event_name,
            "occurred_at": occurred_at,
            "properties_json": json.dumps(properties, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        }

    def require_account(self) -> str | None:
        authorization = self.headers.get("Authorization") or ""
        if not authorization.startswith("Bearer "):
            self.write_error(HTTPStatus.UNAUTHORIZED, "missing_token", "缺少登录令牌。")
            return None

        token = authorization.removeprefix("Bearer ").strip()
        account_id = verify_session_token(self.config.secret_key, token)
        if account_id is None:
            self.write_error(HTTPStatus.UNAUTHORIZED, "invalid_token", "登录令牌无效或已过期。")
            return None

        with connect(self.config) as db:
            row = db.execute(
                "SELECT account_id FROM accounts WHERE account_id = ? AND deleted_at IS NULL",
                (account_id,),
            ).fetchone()

        if row is None:
            self.write_error(HTTPStatus.UNAUTHORIZED, "account_deleted", "账号不存在或已删除。")
            return None
        return account_id

    def read_json(self, max_bytes: int) -> Any:
        payload = self.read_body(max_bytes)
        if not payload:
            return {}
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def read_body(self, max_bytes: int) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > max_bytes:
            self.write_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "body_too_large", "请求体过大。")
            raise ConnectionAbortedError("request body too large")
        return self.rfile.read(length)

    def write_json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json_dumps_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def write_error(self, status: HTTPStatus, code: str, message: str) -> None:
        self.write_json({"error": {"code": code, "message": message}}, status=status)

    @staticmethod
    def is_safe_id(value: str) -> bool:
        return SAFE_ID_RE.match(value) is not None


def create_http_server(host: str, port: int, config: ServerConfig) -> ThreadingHTTPServer:
    class ConfiguredHandler(XiaoNaiPingHandler):
        pass

    effective_config = config if config.object_storage is not None else replace(
        config,
        object_storage=build_object_storage(config.data_dir),
    )
    ConfiguredHandler.config = effective_config
    with connect(effective_config) as db:
        ensure_schema(db)
    return ThreadingHTTPServer((host, port), ConfiguredHandler)


def main() -> None:
    data_dir = Path(os.environ.get("XNP_DATA_DIR", ".xnp-data")).resolve()
    secret_key = os.environ.get("XNP_SECRET_KEY", "local-dev-change-me")
    host = os.environ.get("XNP_HOST", "127.0.0.1")
    port = int(os.environ.get("XNP_PORT", "8787"))
    auth_debug_mode = os.environ.get("XNP_AUTH_DEBUG_MODE", "").strip() == "1"
    server = create_http_server(
        host,
        port,
        ServerConfig(
            data_dir=data_dir,
            secret_key=secret_key,
            auth_debug_mode=auth_debug_mode,
            sms_provider=os.environ.get("XNP_SMS_PROVIDER", ""),
            sms_secret=os.environ.get("XNP_SMS_SECRET", ""),
            sms_webhook_url=os.environ.get("XNP_SMS_WEBHOOK_URL", ""),
            sms_template_id=os.environ.get("XNP_SMS_TEMPLATE_ID", ""),
            app_review_phone_number=os.environ.get("XNP_APP_REVIEW_PHONE_NUMBER", ""),
            app_review_phone_code=os.environ.get("XNP_APP_REVIEW_PHONE_CODE", ""),
            wechat_app_id=os.environ.get("XNP_WECHAT_APP_ID", ""),
            wechat_app_secret=os.environ.get("XNP_WECHAT_APP_SECRET", ""),
            wechat_access_token_url=os.environ.get("XNP_WECHAT_ACCESS_TOKEN_URL", DEFAULT_WECHAT_ACCESS_TOKEN_URL),
            admin_token=os.environ.get("XNP_ADMIN_TOKEN", ""),
        ),
    )
    print(f"XiaoNaiPing API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
