#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SECRET_ENV_NAMES = {
    "XNP_SECRET_KEY",
    "XNP_ADMIN_TOKEN",
    "XNP_MYSQL_PASSWORD",
    "HUAWEI_OBS_ACCESS_KEY_ID",
    "HUAWEI_OBS_SECRET_ACCESS_KEY",
    "HUAWEI_OBS_SECURITY_TOKEN",
    "XNP_SMS_SECRET",
    "XNP_WECHAT_APP_SECRET",
}

EXPECTED_ENV_NAMES = [
    "XNP_DEPLOYMENT_TARGET",
    "XNP_HOST",
    "XNP_PORT",
    "XNP_DATA_DIR",
    "XNP_SECRET_KEY",
    "XNP_ADMIN_TOKEN",
    "XNP_AUTH_DEBUG_MODE",
    "XNP_DATABASE_BACKEND",
    "XNP_MYSQL_HOST",
    "XNP_MYSQL_PORT",
    "XNP_MYSQL_USER",
    "XNP_MYSQL_PASSWORD",
    "XNP_MYSQL_DATABASE",
    "XNP_MYSQL_SSL_CA",
    "XNP_STORAGE_BACKEND",
    "HUAWEI_OBS_ACCESS_KEY_ID",
    "HUAWEI_OBS_SECRET_ACCESS_KEY",
    "HUAWEI_OBS_SECURITY_TOKEN",
    "HUAWEI_OBS_ENDPOINT",
    "HUAWEI_OBS_BUCKET",
    "HUAWEI_OBS_PREFIX",
    "XNP_SMS_PROVIDER",
    "XNP_SMS_WEBHOOK_URL",
    "XNP_SMS_SECRET",
    "XNP_SMS_TEMPLATE_ID",
    "XNP_WECHAT_APP_ID",
    "XNP_WECHAT_APP_SECRET",
]

PUBLIC_ENV_NAMES = {
    "XNP_DEPLOYMENT_TARGET",
    "XNP_AUTH_DEBUG_MODE",
    "XNP_DATABASE_BACKEND",
    "XNP_STORAGE_BACKEND",
    "XNP_SMS_PROVIDER",
    "XNP_MYSQL_USER",
    "XNP_MYSQL_DATABASE",
    "HUAWEI_OBS_PREFIX",
}

PLACEHOLDER_MARKERS = ("replace", "example", "changeme", "todo", "your_", "YOUR_")
FORBIDDEN_SHARED_MARKERS = ("emotion", "emotion-isle", "emotion_isle", "ydm", "daimao", "一根呆毛", "情绪")
WECHAT_APP_ID_RE = re.compile(r"^wx[a-f0-9]{16}$")
WECHAT_SAMPLE_APP_ID_BODIES = {
    "0123456789abcdef",
    "1234567890abcdef",
    "abcdef1234567890",
    "fedcba9876543210",
}
LOCAL_SMS_WEBHOOK_HOSTS = {"127.0.0.1", "localhost", "::1"}
LOCAL_SMS_ADAPTER_PORT = 8791
LOCAL_SMS_ADAPTER_PATH = "/send"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def clean_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = clean_env_value(value)
    return values


def merge_env(env_file_values: dict[str, str], include_process_env: bool) -> dict[str, str]:
    values = dict(env_file_values)
    if include_process_env:
        for name in EXPECTED_ENV_NAMES:
            if name in os.environ:
                values[name] = os.environ[name]
    return values


def is_placeholder(value: str) -> bool:
    lower = value.lower()
    return any(marker.lower() in lower for marker in PLACEHOLDER_MARKERS)


def configured_wechat_app_id(value: str) -> bool:
    value = value.strip()
    if not value or is_placeholder(value) or not WECHAT_APP_ID_RE.fullmatch(value):
        return False
    body = value[2:].lower()
    return body not in WECHAT_SAMPLE_APP_ID_BODIES and len(set(body)) > 1


def configured_sms_webhook_url(value: str) -> bool:
    value = value.strip()
    if not value or is_placeholder(value):
        return False
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme == "http"
        and host in LOCAL_SMS_WEBHOOK_HOSTS
        and parsed.port == LOCAL_SMS_ADAPTER_PORT
        and parsed.path == LOCAL_SMS_ADAPTER_PATH
    ):
        return True
    return (
        parsed.scheme == "https"
        and bool(host)
        and host not in LOCAL_SMS_WEBHOOK_HOSTS
        and "example" not in host
    )


def has_xiaonaiping_namespace(value: str) -> bool:
    lower = value.lower()
    return "xiaonaiping" in lower or "xnp" in lower


def contains_forbidden_shared_marker(value: str) -> bool:
    lower = value.lower()
    return any(marker.lower() in lower for marker in FORBIDDEN_SHARED_MARKERS)


def env_status(values: dict[str, str]) -> dict[str, Any]:
    set_names: list[str] = []
    empty_names: list[str] = []
    placeholder_names: list[str] = []
    for name in EXPECTED_ENV_NAMES:
        value = values.get(name, "")
        if value and not is_placeholder(value):
            set_names.append(name)
        elif value and is_placeholder(value):
            placeholder_names.append(name)
        else:
            empty_names.append(name)
    return {
        "verifiedAt": utc_now(),
        "doesNotExposeValues": True,
        "set": sorted(set_names),
        "empty": sorted(empty_names),
        "placeholder": sorted(placeholder_names),
        "secretValuesRedacted": sorted(name for name in EXPECTED_ENV_NAMES if name in SECRET_ENV_NAMES),
    }


def public_env_values(values: dict[str, str]) -> dict[str, str]:
    return {
        name: values.get(name, "")
        for name in sorted(PUBLIC_ENV_NAMES)
        if values.get(name, "") and not is_placeholder(values.get(name, ""))
    }


def provider_checks(values: dict[str, str]) -> dict[str, bool]:
    auth_debug = values.get("XNP_AUTH_DEBUG_MODE", "").strip()
    storage_backend = values.get("XNP_STORAGE_BACKEND", "").strip().lower()
    obs_bucket = values.get("HUAWEI_OBS_BUCKET", "").strip()
    obs_prefix = values.get("HUAWEI_OBS_PREFIX", "").strip()
    sms_provider = values.get("XNP_SMS_PROVIDER", "").strip().lower()
    return {
        "authDebugModeDisabled": auth_debug in {"", "0", "false"},
        "storageBackendIsHuaweiOBS": storage_backend == "huawei_obs",
        "obsBucketHasXiaoNaiPingNamespace": bool(obs_bucket and has_xiaonaiping_namespace(obs_bucket)),
        "obsPrefixHasXiaoNaiPingNamespace": bool(obs_prefix and has_xiaonaiping_namespace(obs_prefix)),
        "smsProviderIsWebhook": sms_provider == "webhook",
        "smsWebhookURLConfigured": configured_sms_webhook_url(values.get("XNP_SMS_WEBHOOK_URL", "")),
        "wechatAppIDConfigured": configured_wechat_app_id(values.get("XNP_WECHAT_APP_ID", "")),
        "wechatAppSecretConfigured": bool(values.get("XNP_WECHAT_APP_SECRET", "").strip() and not is_placeholder(values.get("XNP_WECHAT_APP_SECRET", ""))),
    }


def isolation(values: dict[str, str], args: argparse.Namespace) -> dict[str, Any]:
    checked_values = [
        values.get("XNP_DATA_DIR", ""),
        values.get("XNP_MYSQL_USER", ""),
        values.get("XNP_MYSQL_DATABASE", ""),
        values.get("HUAWEI_OBS_BUCKET", ""),
        values.get("HUAWEI_OBS_PREFIX", ""),
    ]
    return {
        "linuxUser": args.linux_user,
        "systemdService": args.systemd_service,
        "mysqlDatabase": values.get("XNP_MYSQL_DATABASE", ""),
        "mysqlUser": values.get("XNP_MYSQL_USER", ""),
        "reusedEmotionAppDatabase": contains_forbidden_shared_marker(values.get("XNP_MYSQL_DATABASE", "")),
        "reusedEmotionAppService": contains_forbidden_shared_marker(args.systemd_service),
        "reusedEmotionAppDirectory": contains_forbidden_shared_marker(args.deploy_root),
        "sharedNamespaceMarkersFound": any(contains_forbidden_shared_marker(value) for value in checked_values),
    }


def remaining_blockers(values: dict[str, str], checks: dict[str, bool]) -> list[str]:
    blockers: list[str] = []
    required_env = env_status(values)
    if required_env["placeholder"]:
        blockers.append("production private env still contains placeholder values: " + ", ".join(required_env["placeholder"]))
    if not checks["storageBackendIsHuaweiOBS"]:
        blockers.append("Huawei OBS storage backend is not selected")
    if not checks["obsBucketHasXiaoNaiPingNamespace"]:
        blockers.append("Huawei OBS bucket is missing or does not contain xiaonaiping/xnp namespace")
    if not checks["smsProviderIsWebhook"] or not checks["smsWebhookURLConfigured"]:
        blockers.append("production SMS webhook provider is not fully configured")
    if not checks["wechatAppIDConfigured"] or not checks["wechatAppSecretConfigured"]:
        blockers.append("WeChat Open Platform AppID/AppSecret are not fully configured")
    return blockers


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    env_file_values = parse_env_file(Path(args.env_file)) if args.env_file else {}
    values = merge_env(env_file_values, args.include_process_env)
    checks = provider_checks(values)
    now = utc_now()
    deploy_root = args.deploy_root
    return {
        "startedAt": now,
        "completedAt": now,
        "verifiedAt": now,
        "target": values.get("XNP_DEPLOYMENT_TARGET", args.target),
        "containsSecrets": False,
        "source": {
            "envFile": args.env_file,
            "processEnvIncluded": args.include_process_env,
        },
        "remotePaths": {
            "deployRoot": deploy_root,
            "current": args.current_path,
            "privateEnv": args.env_file,
            "dataDir": values.get("XNP_DATA_DIR", ""),
        },
        "privateEnvStatus": env_status(values),
        "isolation": isolation(values, args),
        "runtime": {
            "pythonVenv": args.python_venv,
            "serviceActive": args.service_active,
            "bindAddress": values.get("XNP_HOST", ""),
            "port": int(values["XNP_PORT"]) if values.get("XNP_PORT", "").isdigit() else values.get("XNP_PORT", ""),
            "databaseBackend": values.get("XNP_DATABASE_BACKEND", ""),
            "storageBackend": values.get("XNP_STORAGE_BACKEND", ""),
        },
        "publicEnvValues": public_env_values(values),
        "providerChecks": checks,
        "publicRoute": {
            "baseUrl": args.base_url,
            "dedicatedSubdomainConfigured": args.dedicated_subdomain,
            "usesIsolatedBackendService": not contains_forbidden_shared_marker(args.systemd_service),
            "publicInternalPathsBlocked": args.public_internal_blocked,
            "blockedPaths": ["/xiaonaiping/internal", "/xiaonaiping/internal/"] if args.public_internal_blocked else [],
        },
        "remainingProductionBlockers": remaining_blockers(values, checks),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default="/srv/xiaonaiping/private/xiaonaiping-api.env")
    parser.add_argument("--allow-missing-env-file", action="store_true")
    parser.add_argument("--include-process-env", action="store_true")
    parser.add_argument("--target", default="huawei_baota")
    parser.add_argument("--deploy-root", default="/srv/xiaonaiping")
    parser.add_argument("--current-path", default="/srv/xiaonaiping/current")
    parser.add_argument("--python-venv", default="/srv/xiaonaiping/current/Backend/.venv")
    parser.add_argument("--linux-user", default="xiaonaiping")
    parser.add_argument("--systemd-service", default="xiaonaiping-api.service")
    parser.add_argument("--base-url", default="https://api.mewpow.com/xiaonaiping")
    parser.add_argument("--service-active", action="store_true")
    parser.add_argument("--dedicated-subdomain", action="store_true")
    parser.add_argument("--public-internal-blocked", action="store_true")
    parser.add_argument("--output", default=str(repo_root() / "Backend/proof/huawei-baota-deploy.json"))
    args = parser.parse_args()

    env_file = Path(args.env_file)
    if args.env_file and not env_file.exists() and not args.include_process_env and not args.allow_missing_env_file:
        raise SystemExit(f"env file not found: {env_file}")

    report = build_report(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"deployment proof written without secrets: {output}")
    if report["remainingProductionBlockers"]:
        print("remaining blockers: " + "; ".join(report["remainingProductionBlockers"]))


if __name__ == "__main__":
    main()
