#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLACEHOLDER_MARKERS = ("replace", "example", "changeme", "todo", "your_", "YOUR_")
PHONE_RE = re.compile(r"^\+[1-9][0-9]{7,15}$")
WECHAT_APP_ID_RE = re.compile(r"^wx[a-f0-9]{16}$")
WECHAT_SAMPLE_APP_ID_BODIES = {
    "0123456789abcdef",
    "1234567890abcdef",
    "abcdef1234567890",
    "fedcba9876543210",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def is_placeholder(value: str) -> bool:
    lower = value.lower()
    return any(marker.lower() in lower for marker in PLACEHOLDER_MARKERS)


def configured_value(value: str) -> bool:
    return bool(value.strip()) and not is_placeholder(value)


def configured_wechat_app_id(value: str) -> bool:
    value = value.strip()
    if not value or is_placeholder(value) or not WECHAT_APP_ID_RE.fullmatch(value):
        return False
    body = value[2:].lower()
    return body not in WECHAT_SAMPLE_APP_ID_BODIES and len(set(body)) > 1


def deployment_private_set(deployment_proof: dict[str, Any]) -> set[str]:
    status = deployment_proof.get("privateEnvStatus", {})
    if not isinstance(status, dict):
        return set()
    values = status.get("set", [])
    return {str(value) for value in values} if isinstance(values, list) else set()


def deployment_public_env(deployment_proof: dict[str, Any]) -> dict[str, str]:
    values = deployment_proof.get("publicEnvValues", {})
    if not isinstance(values, dict):
        return {}
    return {str(key): str(value) for key, value in values.items()}


def deployment_provider_checks(deployment_proof: dict[str, Any]) -> dict[str, bool]:
    values = deployment_proof.get("providerChecks", {})
    if not isinstance(values, dict):
        return {}
    return {str(key): value is True for key, value in values.items()}


def env_or_proof_configured(
    name: str,
    private_set: set[str],
    public_env: dict[str, str],
    provider_checks: dict[str, bool],
    provider_check_name: str = "",
) -> bool:
    value = os.environ.get(name, "").strip()
    if configured_value(value):
        return True
    if configured_value(public_env.get(name, "")):
        return True
    if name in private_set:
        return True
    if provider_check_name and provider_checks.get(provider_check_name) is True:
        return True
    return False


def env_or_proof_wechat_app_id_configured(
    public_env: dict[str, str],
    provider_checks: dict[str, bool],
) -> bool:
    value = os.environ.get("XNP_WECHAT_APP_ID", "").strip()
    if value:
        return configured_wechat_app_id(value)
    public_value = public_env.get("XNP_WECHAT_APP_ID", "")
    if public_value:
        return configured_wechat_app_id(public_value)
    return provider_checks.get("wechatAppIDConfigured") is True


def request_json(base_url: str, method: str, path: str, body: Any = None) -> tuple[int, dict[str, Any] | bytes]:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = urllib.request.Request(base_url.rstrip("/") + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type", "")
            if content_type.startswith("application/json"):
                return response.status, json.loads(payload.decode("utf-8"))
            return response.status, payload
    except urllib.error.HTTPError as error:
        payload = error.read()
        content_type = error.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            try:
                return error.code, json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError:
                return error.code, payload
        return error.code, payload


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str, base_url: str) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "containsSecrets": False,
            "apiBaseUrl": base_url,
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    deployment_proof = read_json(Path(args.deployment_proof))
    private_set = deployment_private_set(deployment_proof)
    public_env = deployment_public_env(deployment_proof)
    provider_checks = deployment_provider_checks(deployment_proof)
    route = deployment_proof.get("publicRoute", {}) if isinstance(deployment_proof.get("publicRoute", {}), dict) else {}
    base_url = args.base_url or os.environ.get("XNP_API_BASE_URL", "") or str(route.get("baseUrl", ""))

    report = Report()
    report.add(
        "deploymentProofReadable",
        bool(deployment_proof),
        args.deployment_proof if deployment_proof else f"missing or invalid: {args.deployment_proof}",
    )

    auth_debug = os.environ.get("XNP_AUTH_DEBUG_MODE", "").strip() or public_env.get("XNP_AUTH_DEBUG_MODE", "").strip()
    auth_debug_disabled = auth_debug in {"", "0", "false", "False"} or provider_checks.get("authDebugModeDisabled") is True
    report.add(
        "authDebugModeDisabled",
        auth_debug_disabled,
        "deployment proof reports authDebugModeDisabled=true"
        if provider_checks.get("authDebugModeDisabled") is True
        else f"XNP_AUTH_DEBUG_MODE={auth_debug or '<empty>'}",
    )

    sms_provider = os.environ.get("XNP_SMS_PROVIDER", "").strip() or public_env.get("XNP_SMS_PROVIDER", "").strip()
    sms_provider_is_webhook = sms_provider == "webhook" or provider_checks.get("smsProviderIsWebhook") is True
    sms_secret_configured = env_or_proof_configured("XNP_SMS_SECRET", private_set, public_env, provider_checks)
    sms_webhook_configured = env_or_proof_configured(
        "XNP_SMS_WEBHOOK_URL",
        private_set,
        public_env,
        provider_checks,
        "smsWebhookURLConfigured",
    )
    sms_missing = []
    if not sms_provider_is_webhook:
        sms_missing.append("XNP_SMS_PROVIDER=webhook")
    if not sms_secret_configured:
        sms_missing.append("XNP_SMS_SECRET")
    if not sms_webhook_configured:
        sms_missing.append("XNP_SMS_WEBHOOK_URL")
    report.add(
        "smsProviderConfigured",
        not sms_missing,
        "SMS webhook provider is configured" if not sms_missing else "missing: " + ", ".join(sms_missing),
    )

    wechat_id_configured = env_or_proof_wechat_app_id_configured(public_env, provider_checks)
    wechat_secret_configured = env_or_proof_configured(
        "XNP_WECHAT_APP_SECRET",
        private_set,
        public_env,
        provider_checks,
        "wechatAppSecretConfigured",
    )
    report.add(
        "wechatProviderConfigured",
        wechat_id_configured and wechat_secret_configured,
        "WeChat Open Platform AppID/AppSecret are configured"
        if wechat_id_configured and wechat_secret_configured
        else "missing valid XNP_WECHAT_APP_ID (wx + 16 hex) or XNP_WECHAT_APP_SECRET",
    )

    if args.live_check:
        if not base_url:
            report.add("wechatDebugLoginRejected", False, "missing --base-url or deployment publicRoute.baseUrl")
        elif not base_url.startswith("https://") and not args.allow_insecure_http:
            report.add("wechatDebugLoginRejected", False, f"live auth check requires https:// base URL: {base_url}")
        else:
            try:
                status, payload = request_json(base_url, "POST", "/v1/auth/wechat/login", {"code": "debug_wechat_auth_probe"})
                accepted_debug = status < 300 and isinstance(payload, dict) and bool(payload.get("sessionToken"))
                report.add(
                    "wechatDebugLoginRejected",
                    not accepted_debug,
                    f"/v1/auth/wechat/login rejected debug code with HTTP {status}"
                    if not accepted_debug
                    else "/v1/auth/wechat/login accepted debug_wechat_auth_probe",
                )
            except urllib.error.URLError as error:
                report.add("wechatDebugLoginRejected", False, f"live auth check failed: {error}")
    else:
        report.add("wechatDebugLoginRejected", False, "skipped; pass --live-check to probe public API", required=False)

    if args.require_sms_live_send or args.send_test_sms:
        if not args.send_test_sms:
            report.add("smsLiveSendVerified", False, "missing --send-test-sms", required=True)
        elif not args.phone or not PHONE_RE.fullmatch(args.phone):
            report.add("smsLiveSendVerified", False, "missing valid --phone in E.164 format", required=True)
        elif not base_url:
            report.add("smsLiveSendVerified", False, "missing --base-url or deployment publicRoute.baseUrl", required=True)
        elif not base_url.startswith("https://") and not args.allow_insecure_http:
            report.add("smsLiveSendVerified", False, f"live SMS check requires https:// base URL: {base_url}", required=True)
        else:
            try:
                status, payload = request_json(base_url, "POST", "/v1/auth/phone/request-code", {"phoneNumber": args.phone})
                debug_code_returned = isinstance(payload, dict) and "debugCode" in payload
                sent = status < 300 and isinstance(payload, dict) and payload.get("sent") is True and not debug_code_returned
                report.add(
                    "smsLiveSendVerified",
                    sent,
                    f"/v1/auth/phone/request-code returned HTTP {status} without debugCode"
                    if sent
                    else f"/v1/auth/phone/request-code returned HTTP {status}"
                    + (" with debugCode" if debug_code_returned else ""),
                    required=True,
                )
            except urllib.error.URLError as error:
                report.add("smsLiveSendVerified", False, f"live SMS check failed: {error}", required=True)
    else:
        report.add(
            "smsLiveSendVerified",
            False,
            "skipped to avoid sending real SMS; pass --send-test-sms --phone +... for final carrier test",
            required=False,
        )

    return report.to_dict(started_at, utc_now(), base_url)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment-proof", default=str(repo_root() / "Backend/proof/huawei-baota-deploy-20260620.json"))
    parser.add_argument("--base-url", default="")
    parser.add_argument("--live-check", action="store_true")
    parser.add_argument("--allow-insecure-http", action="store_true")
    parser.add_argument("--send-test-sms", action="store_true")
    parser.add_argument("--require-sms-live-send", action="store_true")
    parser.add_argument("--phone", default="")
    parser.add_argument("--output", default=str(repo_root() / "Backend/proof/auth-providers.json"))
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"auth provider verification passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"auth provider verification incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
