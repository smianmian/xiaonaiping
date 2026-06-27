#!/usr/bin/env python3
from __future__ import annotations
import base64
import hashlib
import hmac
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
from urllib.parse import urlencode, urlparse
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
    "/apple-app-site-association": ("apple-app-site-association", "application/json; charset=utf-8"),
    "/.well-known/apple-app-site-association": ("apple-app-site-association", "application/json; charset=utf-8"),
    "/internal/dashboard": ("dashboard.html", "text/html; charset=utf-8"),
}
MAX_BACKUP_BYTES = 5 * 1024 * 1024
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
    "cloud_backup_enabled",
    "cloud_backup_completed",
    "cloud_restore_completed",
    "photo_added",
    "record_created",
    "reminder_enabled",
    "paywall_viewed",
    "purchase_started",
    "purchase_completed",
}
ANALYTICS_PROPERTY_VALUES = {
    "screen": {"home", "record", "profile", "album", "growth", "backup", "onboarding", "paywall"},
    "source": {"app_launch", "onboarding", "profile", "record", "album", "growth", "backup", "restore", "system"},
    "recordType": {"feeding", "sleep", "diaper", "growth", "milestone", "vaccine", "photo"},
    "reminderType": {"feeding", "vaccine"},
    "authProvider": {"recovery_key", "phone", "wechat"},
    "result": {"success", "failure", "cancelled"},
    "feature": {"cloud_backup", "cloud_restore", "photo_backup", "account", "reminder", "commercial"},
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

    recovery_key = None
    if row is None:
        db.execute(
            "DELETE FROM account_identities WHERE provider = ? AND subject_hash = ?",
            (provider, hashed),
        )
        created = create_account_with_recovery(db, config)
        account_id = created["accountId"]
        recovery_key = created["recoveryKey"]
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
    if recovery_key is not None:
        response["recoveryKey"] = recovery_key
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


def upsert_backup(db: DatabaseConnection, account_id: str, payload: bytes, updated_at: str) -> None:
    if db.dialect == "mysql":
        db.execute(
            """
            INSERT INTO backups(account_id, payload, updated_at) VALUES (?, ?, ?)
            ON DUPLICATE KEY UPDATE payload = VALUES(payload), updated_at = VALUES(updated_at)
            """,
            (account_id, payload, updated_at),
        )
        return
    db.execute(
        """
        INSERT INTO backups(account_id, payload, updated_at) VALUES (?, ?, ?)
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
        elif path == "/v1/backup":
            self.handle_get_backup(account_id)
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
        else:
            self.write_error(HTTPStatus.NOT_FOUND, "not_found", "接口不存在。")

    def do_PUT(self) -> None:
        account_id = self.require_account()
        if account_id is None:
            return

        path = urlparse(self.path).path
        if path == "/v1/backup":
            self.handle_put_backup(account_id)
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
        body = self.read_json(MAX_BACKUP_BYTES)
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
        body = self.read_json(MAX_BACKUP_BYTES)
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
        code = make_phone_code()
        if not self.config.auth_debug_mode:
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
        body = self.read_json(MAX_BACKUP_BYTES)
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
        body = self.read_json(MAX_BACKUP_BYTES)
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

    def handle_put_backup(self, account_id: str) -> None:
        payload = self.read_body(MAX_BACKUP_BYTES)
        try:
            json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.write_error(HTTPStatus.BAD_REQUEST, "invalid_backup", "备份必须是 UTF-8 JSON。")
            return

        now = utc_now()
        with connect(self.config) as db:
            upsert_backup(db, account_id, payload, now)
            db.commit()

        self.write_json({"updatedAt": now, "sizeBytes": len(payload)})

    def handle_get_backup(self, account_id: str) -> None:
        with connect(self.config) as db:
            row = db.execute(
                "SELECT payload, updated_at FROM backups WHERE account_id = ?",
                (account_id,),
            ).fetchone()
        if row is None:
            self.write_error(HTTPStatus.NOT_FOUND, "backup_not_found", "还没有云端备份。")
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
            accounts_with_backup = db.execute("SELECT COUNT(*) AS count FROM backups").fetchone()["count"]
            backup_totals = db.execute(
                "SELECT COALESCE(SUM(LENGTH(payload)), 0) AS bytes, MAX(updated_at) AS latest FROM backups"
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
                "accountsWithBackup": int(accounts_with_backup),
                "backupBytes": int(backup_totals["bytes"] or 0),
                "latestBackupAt": backup_totals["latest"],
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
            }
        )

    def handle_delete_account(self, account_id: str) -> None:
        with connect(self.config) as db:
            photo_count = db.execute("SELECT COUNT(*) AS count FROM photos WHERE account_id = ?", (account_id,)).fetchone()[
                "count"
            ]
            had_backup = db.execute("SELECT 1 FROM backups WHERE account_id = ?", (account_id,)).fetchone() is not None
            analytics_digest = subject_hash(self.config.secret_key, "analytics_account", account_id)
            analytics_count = db.execute(
                "SELECT COUNT(*) AS count FROM analytics_events WHERE account_hash = ?",
                (analytics_digest,),
            ).fetchone()["count"]
            now = utc_now()
            db.execute("DELETE FROM backups WHERE account_id = ?", (account_id,))
            db.execute("DELETE FROM photos WHERE account_id = ?", (account_id,))
            db.execute("DELETE FROM account_identities WHERE account_id = ?", (account_id,))
            db.execute("DELETE FROM analytics_events WHERE account_hash = ?", (analytics_digest,))
            db.execute("UPDATE accounts SET deleted_at = ? WHERE account_id = ?", (now, account_id))
            db.execute(
                """
                INSERT INTO deletion_audit(audit_id, account_id, deleted_at, backup_deleted, photo_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), account_id, now, int(had_backup), int(photo_count)),
            )
            db.commit()

        self.config.storage().delete_account(account_id)

        self.write_json(
            {
                "accountId": account_id,
                "deletedAt": now,
                "backupDeleted": had_backup,
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
