#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://api.mewpow.com/xiaonaiping"
STATUS_ARTIFACT_TYPE = "production-proof-refresh-status"
STATUS_VALUE = "current-proof-status-not-submit-permission"

SECRET_PATTERNS = {
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    "openaiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "accessKey": re.compile(r"AKIA[0-9A-Z]{12,}"),
    "wechatSecretAssignment": re.compile(r"XNP_WECHAT_APP_SECRET\s*[:=]\s*[^\s\",}]+"),
    "smsSecretAssignment": re.compile(r"XNP_SMS_SECRET\s*[:=]\s*[^\s\",}]+"),
    "obsSecretAssignment": re.compile(r"HUAWEI_OBS_SECRET_ACCESS_KEY\s*[:=]\s*[^\s\",}]+"),
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*[:=]\s*[^\s\",}]+"),
    "chinaPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_date() -> str:
    return datetime.now().astimezone().date().isoformat()


def path_date(date: str) -> str:
    return date.replace("-", "")


def default_packet_path(date: str) -> Path:
    return Path(f"Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_{path_date(date)}.json")


def default_output_path(date: str) -> Path:
    return Path(f"Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_{path_date(date)}.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def timestamp_matches_date(value: Any, expected_date: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False

    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return value.startswith(expected_date)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return expected_date in {
        parsed.astimezone().date().isoformat(),
        parsed.astimezone(timezone.utc).date().isoformat(),
    }


def current_date_stamped(target: str, data: dict[str, Any] | None, expected_date: str, exists: bool) -> bool:
    if not exists:
        return False
    if path_date(expected_date) in target or expected_date in target:
        return True
    if not data:
        return False
    return any(
        timestamp_matches_date(data.get(key), expected_date)
        for key in ("startedAt", "completedAt", "checkedAt", "verifiedAt", "date")
    )


def proof_passed_or_ready(data: dict[str, Any] | None) -> bool:
    if not data:
        return False
    if any(data.get(key) is True for key in ("passed", "ready", "canSubmit")):
        return True

    # collect_deployment_proof.py intentionally records redacted environment shape
    # rather than a top-level "passed" flag. Treat that as readable proof, while
    # keeping remainingProductionBlockers in failedRequiredChecks.
    return data.get("containsSecrets") is False and isinstance(data.get("privateEnvStatus"), dict)


def failed_required_checks(data: dict[str, Any] | None) -> list[str]:
    if not data:
        return []

    for key in ("failedRequiredChecks", "missingEvidence", "remainingProductionBlockers"):
        value = data.get(key)
        if isinstance(value, list):
            return [str(item) for item in value]

    checks = data.get("checks")
    if isinstance(checks, dict):
        return [
            str(name)
            for name, check in checks.items()
            if isinstance(check, dict) and check.get("required") is True and check.get("passed") is not True
        ]
    return []


def secret_hits(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def real_proof_not_template(data: dict[str, Any] | None, exists: bool) -> bool:
    if not exists or not data:
        return False
    status = str(data.get("status", "")).lower()
    return "template" not in status and "not-evidence" not in status


def status_by_artifact(statuses: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("artifactId")): item for item in statuses}


def has_failed(statuses_by_id: dict[str, dict[str, Any]], artifact_id: str, check_name: str) -> bool:
    return check_name in statuses_by_id.get(artifact_id, {}).get("failedRequiredChecks", [])


def missing_or_failed(statuses_by_id: dict[str, dict[str, Any]], artifact_id: str) -> bool:
    item = statuses_by_id.get(artifact_id, {})
    return item.get("exists") is not True or item.get("passedOrReadyVerified") is not True or bool(item.get("failedRequiredChecks"))


def build_current_blocker_closure(statuses: list[dict[str, Any]], expected_date: str) -> list[dict[str, Any]]:
    items = status_by_artifact(statuses)
    dated = expected_date.replace("-", "")
    closure: list[dict[str, Any]] = []

    def dated_text(value: str) -> str:
        return value.replace("20260629", dated).replace("2026-06-29", expected_date)

    def dated_list(values: list[str]) -> list[str]:
        return [dated_text(value) for value in values]

    def add(
        blocker_id: str,
        title: str,
        source_proofs: list[str],
        required_private_values: list[str],
        required_evidence: list[str],
        rerun_commands: list[str],
        can_progress_without_duns: bool = True,
        blocks_submit: bool = True,
    ) -> None:
        closure.append(
            {
                "id": blocker_id,
                "title": title,
                "canProgressWithoutDuns": can_progress_without_duns,
                "blocksSubmit": blocks_submit,
                "sourceProofs": dated_list(source_proofs),
                "requiredPrivateValues": required_private_values,
                "requiredEvidence": dated_list(required_evidence),
                "rerunCommands": dated_list(rerun_commands),
                "mustNotRecord": [
                    "secret values",
                    "complete phone numbers",
                    "verification codes",
                    "AppSecret",
                    "SMS secret",
                    "OBS AK/SK",
                    "database password",
                    "tokens",
                    "recovery keys",
                ],
            }
        )

    if has_failed(items, "productionReadinessCurrent", "productionSecretConfigured"):
        add(
            "xnp.production.secret",
            "Configure the XiaoNaiPing production app secret in the private server env",
            ["Backend/proof/production-readiness-20260629T-current.json"],
            ["XNP_SECRET_KEY"],
            ["Backend/proof/huawei-baota-deploy-20260629T-current.json with containsSecrets=false"],
            [
                f"python3 Backend/scripts/collect_deployment_proof.py --output Backend/proof/huawei-baota-deploy-{dated}T-current.json",
                f"python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-{dated}T-current.json",
            ],
        )

    if (
        has_failed(items, "productionReadinessCurrent", "productionDataDirConfigured")
        or has_failed(items, "productionReadinessCurrent", "xiaonaipingProductionNamespaceConfigured")
    ):
        add(
            "xnp.production.namespace",
            "Set XiaoNaiPing-specific data namespace, separated from Emotion Isle",
            ["Backend/proof/production-readiness-20260629T-current.json"],
            ["XNP_DATA_DIR containing xiaonaiping or xnp namespace"],
            ["Deployment proof showing the redacted namespace shape, not the full private path"],
            [
                f"python3 Backend/scripts/collect_deployment_proof.py --output Backend/proof/huawei-baota-deploy-{dated}T-current.json",
                f"python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-{dated}T-current.json",
            ],
        )

    if (
        has_failed(items, "productionReadinessCurrent", "mysqlDatabaseSelected")
        or has_failed(items, "productionReadinessCurrent", "mysqlDatabaseEnvPresent")
    ):
        add(
            "xnp.production.mysql",
            "Select MySQL and configure an isolated XiaoNaiPing production database",
            ["Backend/proof/production-readiness-20260629T-current.json"],
            [
                "XNP_DATABASE_BACKEND=mysql",
                "XNP_MYSQL_HOST",
                "XNP_MYSQL_USER containing xiaonaiping or xnp namespace",
                "XNP_MYSQL_PASSWORD",
                "XNP_MYSQL_DATABASE containing xiaonaiping or xnp namespace",
            ],
            ["Deployment proof showing database backend and redacted namespace, not credentials"],
            [
                f"python3 Backend/scripts/collect_deployment_proof.py --output Backend/proof/huawei-baota-deploy-{dated}T-current.json",
                f"python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-{dated}T-current.json",
            ],
        )

    if has_failed(items, "productionReadinessCurrent", "privateOperationsDashboardConfigured"):
        add(
            "xnp.production.admin-dashboard",
            "Configure the private operations dashboard token and keep public internal routes blocked",
            ["Backend/proof/production-readiness-20260629T-current.json"],
            ["XNP_ADMIN_TOKEN"],
            ["Deployment proof showing admin protection configured without exposing token"],
            [
                f"python3 Backend/scripts/collect_deployment_proof.py --output Backend/proof/huawei-baota-deploy-{dated}T-current.json",
                f"python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-{dated}T-current.json",
            ],
        )

    if has_failed(items, "productionReadinessCurrent", "publicInternalDashboardBlocked"):
        add(
            "xnp.production.internal-block",
            "Prove public /internal routes are blocked in production",
            ["Backend/proof/production-readiness-20260629T-current.json"],
            [],
            ["Deployment or HTTP proof showing public /internal is not exposed"],
            [
                f"python3 Backend/scripts/collect_deployment_proof.py --output Backend/proof/huawei-baota-deploy-{dated}T-current.json",
                f"python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-{dated}T-current.json",
            ],
        )

    if (
        has_failed(items, "authProvidersConfigCurrent", "smsProviderConfigured")
        or has_failed(items, "productionReadinessCurrent", "phoneLoginProviderConfigured")
    ):
        add(
            "xnp.auth.sms-provider",
            "Configure SMS webhook provider and capture provider console proof",
            [
                "Backend/proof/auth-providers-20260629T-current.json",
                "Backend/proof/production-readiness-20260629T-current.json",
            ],
            ["XNP_SMS_PROVIDER=webhook", "XNP_SMS_SECRET", "XNP_SMS_WEBHOOK_URL"],
            [
                "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
                "SMS provider name, signature, template, approved status, and masked send result",
            ],
            [
                f"python3 Backend/scripts/verify_auth_providers.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/auth-providers-{dated}T-current.json",
                f"python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-{dated}T-current.json",
            ],
        )

    if missing_or_failed(items, "authProvidersSmsLiveCurrent"):
        add(
            "xnp.auth.sms-live-send",
            "Run one real SMS live-send proof after provider config is in place",
            ["Backend/proof/auth-providers-sms-live-20260629T-current.json"],
            ["A masked test phone number supplied only at execution time"],
            [
                "Backend/proof/auth-providers-sms-live-20260629T-current.json",
                "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260629.json filled with redacted result metadata",
            ],
            [
                f"python3 Backend/scripts/verify_auth_providers.py --send-test-sms --phone-env XNP_SMS_TEST_PHONE --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/auth-providers-sms-live-{dated}T-current.json",
            ],
        )

    if (
        has_failed(items, "authProvidersConfigCurrent", "wechatProviderConfigured")
        or has_failed(items, "productionReadinessCurrent", "wechatLoginProviderConfigured")
    ):
        add(
            "xnp.auth.wechat-provider",
            "Configure WeChat Open Platform server credentials without storing AppSecret in proof",
            [
                "Backend/proof/auth-providers-20260629T-current.json",
                "Backend/proof/production-readiness-20260629T-current.json",
            ],
            ["XNP_WECHAT_APP_ID=wx + 16 lowercase hex", "XNP_WECHAT_APP_SECRET"],
            [
                "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
                "WeChat Open Platform mobile app status with AppSecret fully hidden",
            ],
            [
                f"python3 Backend/scripts/verify_auth_providers.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/auth-providers-{dated}T-current.json",
                f"python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-{dated}T-current.json",
            ],
        )

    if (
        has_failed(items, "productionReadinessCurrent", "iosReleaseReadinessProofPassed")
        or has_failed(items, "productionReadinessCurrent", "iosAppBundleProofPassed")
    ):
        add(
            "xnp.ios.wechat-client",
            "Build the iOS Release bundle with the same WeChat AppID, URL Scheme, and Universal Link",
            [
                "Backend/proof/ios-app-bundle-20260629T-current-ios265.json",
                "Backend/proof/production-readiness-20260629T-current.json",
            ],
            [
                "XNP_WECHAT_APP_ID=wx + 16 lowercase hex",
                "XNP_WECHAT_URL_SCHEME equal to XNP_WECHAT_APP_ID",
                "XNP_WECHAT_UNIVERSAL_LINK on api.mewpow.com",
            ],
            [
                "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
                "Release app bundle proof showing Info.plist XNPWeChatAppID and CFBundleURLTypes are non-placeholder",
            ],
            [
                f"python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-{dated}T-current.json",
                "python3 Backend/scripts/check_ios_app_bundle.py "
                "--app /tmp/XiaoNaiPing-WeChatClient-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app "
                f"--output Backend/proof/ios-app-bundle-{dated}T-current-ios265.json",
                ". /tmp/xnp-wechat-release.env && "
                f"python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-{dated}T-current-ios265.json",
            ],
        )

    if has_failed(items, "productionReadinessCurrent", "appStoreAssetsProofPassed"):
        add(
            "xnp.appstore.final-screenshots",
            "Replace Debug simulator screenshot candidates with final upload provenance",
            [
                "Backend/proof/app-store-assets.json",
                "Backend/proof/app-store-evidence-20260629T-current.json",
            ],
            [],
            [
                "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                "Final screenshots from the same iOS 26.5 TestFlight build or Xcode signed-device build",
            ],
            [
                f"python3 Backend/scripts/check_app_store_assets.py --allow-incomplete --output Backend/proof/app-store-assets.json",
                f"python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence-{dated}T-current.json",
            ],
            can_progress_without_duns=False,
        )

    if has_failed(items, "productionReadinessCurrent", "testFlightRegressionPlanProofPassed"):
        add(
            "xnp.real-device-regression",
            "Complete iOS 26.5 real-device or TestFlight regression evidence",
            ["Backend/proof/production-readiness-20260629T-current.json"],
            [],
            [
                "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
                "Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.json",
            ],
            [
                f"python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan-{dated}T-current.json",
                f"python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence-{dated}T-current.json",
            ],
            can_progress_without_duns=False,
        )

    if has_failed(items, "productionReadinessCurrent", "authProvidersProofPassed"):
        add(
            "xnp.production.auth-proof-chain",
            "Refresh production readiness only after SMS and WeChat auth provider proofs are green",
            ["Backend/proof/production-readiness-20260629T-current.json"],
            [],
            ["Backend/proof/auth-providers-20260629T-current.json with failedRequiredChecks=[]"],
            [
                f"python3 Backend/scripts/verify_auth_providers.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/auth-providers-{dated}T-current.json",
                f"python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-{dated}T-current.json",
            ],
        )

    if has_failed(items, "appStoreEvidenceCurrent", "huaweiObsPolicy"):
        add(
            "xnp.external.obs-policy",
            "Capture Huawei OBS policy proof for private storage and account deletion boundary",
            ["Backend/proof/app-store-evidence-20260629T-current.json"],
            [],
            ["Docs/08_Release/AppStoreEvidence/09-obs-policy.png"],
            [
                f"python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence-{dated}T-current.json",
            ],
        )

    return closure


def build_status(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    expected_date = args.date
    packet_path = root / args.packet
    packet = read_json(packet_path)
    if not packet:
        raise SystemExit(f"invalid production proof refresh packet: {packet_path}")

    target_proofs = packet.get("targetProofFiles")
    if not isinstance(target_proofs, dict) or not target_proofs:
        raise SystemExit(f"production proof refresh packet has no targetProofFiles: {packet_path}")

    statuses: list[dict[str, Any]] = []
    missing: list[str] = []
    failed: list[dict[str, Any]] = []
    secret_failures: list[dict[str, Any]] = []

    for artifact_id, target in target_proofs.items():
        target_text = str(target)
        path = root / target_text
        exists = path.is_file()
        parsed = read_json(path) if exists else None
        hits = secret_hits(path) if exists else []
        failed_checks = failed_required_checks(parsed)
        passed_or_ready = proof_passed_or_ready(parsed)
        stable_alias = str(artifact_id).startswith("stable")

        status = {
            "artifactId": artifact_id,
            "target": target_text,
            "exists": exists,
            "fileSizeBytes": path.stat().st_size if exists else 0,
            "sha256": sha256_file(path) if exists else None,
            "jsonParsed": parsed is not None,
            "currentDateStamped": current_date_stamped(target_text, parsed, expected_date, exists),
            "passedOrReadyVerified": passed_or_ready,
            "failedRequiredChecks": failed_checks,
            "realProofNotTemplate": real_proof_not_template(parsed, exists),
            "secretValuesNotRecorded": not hits,
            "secretScanHits": hits,
            "stableAliasSyncedOnlyAfterGreen": False,
            "syncBlockedReason": "stable alias remains blocked until same-round current proofs are all green"
            if stable_alias
            else "",
        }
        statuses.append(status)

        if not exists:
            missing.append(str(artifact_id))
        elif (not passed_or_ready) or failed_checks:
            failed.append({"artifactId": artifact_id, "failedRequiredChecks": failed_checks})
        if hits:
            secret_failures.append({"artifactId": artifact_id, "secretScanHits": hits})

    all_current_required_green = all(
        item["exists"]
        and item["jsonParsed"]
        and item["currentDateStamped"]
        and item["passedOrReadyVerified"]
        and not item["failedRequiredChecks"]
        and item["secretValuesNotRecorded"]
        for item in statuses
        if not str(item["artifactId"]).startswith("stable")
    )

    current_blocker_closure = build_current_blocker_closure(statuses, expected_date)

    return {
        "artifactType": STATUS_ARTIFACT_TYPE,
        "status": STATUS_VALUE,
        "date": expected_date,
        "checkedAt": utc_now(),
        "project": packet.get("project", "XiaoNaiPing"),
        "appName": packet.get("appName", "小奶瓶"),
        "xnpRoot": str(root),
        "baseUrl": packet.get("baseUrl", DEFAULT_BASE_URL),
        "sourcePlan": str(args.packet),
        "canSubmitFromThisStatus": False,
        "stableAliasSyncAllowed": bool(all_current_required_green),
        "stableAliasSyncReason": "all same-round current proofs are green; stable aliases may be synced"
        if all_current_required_green
        else "current proof files are incomplete or failed; do not sync stable aliases",
        "proofFileStatuses": statuses,
        "summary": {
            "totalProofFiles": len(statuses),
            "existingProofFiles": sum(1 for item in statuses if item["exists"]),
            "missingProofFiles": len(missing),
            "failedProofFiles": len(failed),
            "secretScanFailures": len(secret_failures),
            "deploymentProofCurrentExists": any(
                item["artifactId"] == "deploymentProofCurrent" and item["exists"] for item in statuses
            ),
            "authProvidersSmsLiveCurrentExists": any(
                item["artifactId"] == "authProvidersSmsLiveCurrent" and item["exists"] for item in statuses
            ),
            "stableAliasesBlocked": not all_current_required_green,
        },
        "missingProofs": missing,
        "failedProofs": failed,
        "secretScanFailures": secret_failures,
        "currentBlockerClosure": current_blocker_closure,
        "nextActions": [
            "Do not sync stable aliases until every same-round current proof is green.",
            "Configure production private env, MySQL, Huawei OBS, SMS live send, and WeChat AppSecret without recording secret values in proof files.",
            "Capture App Store Connect, Apple Developer, SMS, WeChat, OBS, filing, final screenshots, and iOS 26.5 real-device evidence before Submit for Review.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--date", default=default_date())
    parser.add_argument("--packet")
    parser.add_argument("--output")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    args.packet = args.packet or str(default_packet_path(args.date))
    args.output = args.output or str(default_output_path(args.date))

    status = build_status(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if status["stableAliasSyncAllowed"]:
        print(f"production proof refresh status passed: {output_path}")
        return

    missing = ", ".join(status["missingProofs"]) or "<none>"
    failed = ", ".join(item["artifactId"] for item in status["failedProofs"]) or "<none>"
    print(f"production proof refresh status incomplete: {output_path}", file=sys.stderr)
    print(f"missing proofs: {missing}", file=sys.stderr)
    print(f"failed proofs: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
