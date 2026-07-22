#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ACTION_PACKET = "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
IOS_265_BUILD_PROOF = "Backend/proof/ios-265-build.json"
PRODUCTION_PROOF_REFRESH_PACKET = "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json"
AUTH_PROVIDER_TARGETED_TEST_LOG = "Backend/proof/auth-provider-targeted-tests-20260630.log"

EVIDENCE_FILENAMES = {
    "companyAccount": ["01-company-account"],
    "mainlandAvailability": ["02-mainland-availability"],
    "mainlandFiling": ["03-app-filing"],
    "privacyLabel": ["04-privacy-label"],
    "ageRatingResult": ["17-age-rating-result"],
    "signedArchive": ["05-signed-archive"],
    "testFlight": ["06-testflight"],
    "appleDeveloperAccountAccess": ["AppleDeveloper/16-account-roles-access", "appleDeveloperAccountAccess"],
    "smsProvider": ["07-sms-provider"],
    "wechatOpenPlatform": ["08-wechat-open-platform"],
    "wechatUniversalLinkAasa": ["08b-wechat-universal-link-aasa", "wechatUniversalLinkAasa"],
    "huaweiObsPolicy": ["09-obs-policy"],
    "finalScreenshots": ["10-final-screenshots/UPLOAD_PROVENANCE.json", "finalScreenshotsUploadProvenancePresent"],
    "realDeviceRegression": ["12-real-device-regression.md"],
}

IOS_265_MARKERS = (
    "本机测试只使用 iOS 26.5",
    "iOS 27.0",
    "不能替代真机证据",
)

WECHAT_MARKERS = (
    "wx + 16 hex",
    "URL Scheme equal to AppID",
    "Universal Link",
    "AppSecret",
    "com.mewpow.xiaonaiping",
    "08-wechat-open-platform",
)

RERUN_COMMAND_MARKERS = (
    "Backend/scripts/run_launch_readiness.sh",
    "check_launch_objective_audit.py --allow-incomplete",
    "check_app_store_evidence.py --allow-incomplete",
)

REAL_DEVICE_MARKERS = (
    "TestFlight",
    "Xcode 签名真机包",
    "12-real-device-regression.md",
    "RD-01",
    "RD-24",
)

PRODUCTION_FRESHNESS_MARKERS = {
    "deploymentProofCurrent": (
        "deploymentProofCurrent",
        "当天部署 proof",
        "XNP_DEPLOY_HOST",
        "deploy-huawei-baota.sh",
        "collect_deployment_proof.py",
        "PRODUCTION_PROOF_REFRESH_PACKET_20260629.json",
    ),
    "storageBackendProofCurrent": (
        "storageBackendProofCurrent",
        "当天 OBS/存储 proof",
        "verify_storage_backend.py",
        "PRODUCTION_PROOF_REFRESH_PACKET_20260629.json",
    ),
}

TESTFLIGHT_REGRESSION_PREREQUISITE_MARKERS = {
    "testFlightRegressionPlanProofPassed": (
        "testFlightRegressionPlanProofPassed",
        "ios265-device-availability.json",
        "devicectl",
        "physical iPhone",
        "iOS 26.5",
        "不能替代",
    ),
}

AUTH_PROVIDER_TARGETED_PACKET_MARKERS = (
    "Backend/proof/auth-provider-targeted-tests-20260629.log",
    "8 个 targeted tests 通过",
    "短信 webhook adapter",
    "签名校验",
    "auth provider 配置门禁",
    "debug 微信拒绝路径",
)
AUTH_PROVIDER_TARGETED_LOG_MARKERS = (
    "Backend.tests.test_aliyun_sms_adapter.AliyunSMSAdapterTest",
    "Backend.tests.test_auth_provider_verification.AuthProviderVerificationTest",
    "test_invalid_signature_is_rejected",
    "test_deployment_proof_can_pass_offline_provider_gate",
    "test_live_check_accepts_production_rejection_of_debug_wechat_code",
    "test_sample_wechat_app_id_fails_provider_gate",
    "Ran 8 tests",
    "OK",
)
STALE_AUTH_PROVIDER_TARGETED_MARKERS = (
    "auth-provider-targeted-tests-20260628.log",
)

PRODUCTION_REFRESH_DOC_MARKERS = (
    "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260629.json",
    "不是部署证据",
    "不是 production readiness",
    "不能作为提交许可",
)
PRODUCTION_REFRESH_PACKET_SCALARS = {
    "artifactType": "production-proof-refresh-packet",
    "status": "refresh-plan-not-evidence",
    "date": "2026-06-29",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
    "baseUrl": "https://api.mewpow.com/xiaonaiping",
}
PRODUCTION_REFRESH_PACKET_SOURCE_FILES = {
    "launchBlockerActionPacket": "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260629.md",
    "externalPlatformHandoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260629.md",
    "productionConfigExample": "Backend/deploy/production-config.example",
    "runLaunchReadiness": "Backend/scripts/run_launch_readiness.sh",
    "collectDeploymentProof": "Backend/scripts/collect_deployment_proof.py",
    "verifyRemoteApi": "Backend/scripts/verify_remote_api.py",
    "verifyStorageBackend": "Backend/scripts/verify_storage_backend.py",
    "verifyAuthProviders": "Backend/scripts/verify_auth_providers.py",
    "checkAppStoreEvidence": "Backend/scripts/check_app_store_evidence.py",
    "checkProductionReadiness": "Backend/scripts/check_production_readiness.py",
    "checkLaunchObjectiveAudit": "Backend/scripts/check_launch_objective_audit.py",
}
PRODUCTION_REFRESH_PACKET_TARGET_PROOFS = {
    "deploymentProofCurrent": "Backend/proof/huawei-baota-deploy-20260629T-current.json",
    "remoteApiCurrent": "Backend/proof/remote-api-20260629T-current.json",
    "storageBackendCurrent": "Backend/proof/storage-backend-20260629T-current.json",
    "authProvidersConfigCurrent": "Backend/proof/auth-providers-20260629T-current.json",
    "authProvidersSmsLiveCurrent": "Backend/proof/auth-providers-sms-live-20260629T-current.json",
    "wechatClientConfigurationCurrent": "Backend/proof/wechat-client-configuration-20260630T-current.json",
    "iosReleaseReadinessCurrent": "Backend/proof/ios-release-readiness-20260629T-current-ios265.json",
    "iosAppBundleCurrent": "Backend/proof/ios-app-bundle-20260629T-current-ios265.json",
    "appStoreEvidenceCurrent": "Backend/proof/app-store-evidence-20260629T-current.json",
    "productionReadinessCurrent": "Backend/proof/production-readiness-20260629T-current.json",
    "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
    "stableDeploymentAlias": "Backend/proof/huawei-baota-deploy.json",
    "stableRemoteApiAlias": "Backend/proof/remote-api.json",
    "stableStorageAlias": "Backend/proof/storage-backend.json",
    "stableAuthProvidersAlias": "Backend/proof/auth-providers.json",
    "stableWechatClientConfigurationAlias": "Backend/proof/wechat-client-configuration.json",
    "stableIosReleaseReadinessAlias": "Backend/proof/ios-release-readiness.json",
    "stableIosAppBundleAlias": "Backend/proof/ios-app-bundle.json",
    "stableAppStoreEvidenceAlias": "Backend/proof/app-store-evidence.json",
    "stableProductionReadinessAlias": "Backend/proof/production-readiness.json",
}
PRODUCTION_REFRESH_PACKET_SEPARATION_MARKERS = (
    "this packet is not deployment proof",
    "this packet is not production readiness",
    "do not copy old 20260628T-current proof into 20260629T-current proof",
    "stable aliases sync only after same-round current proofs pass",
    "do not use simulator evidence as iOS 26.5 real-device proof",
    "do not use provider templates",
    "Submit for Review",
)
PRODUCTION_REFRESH_PACKET_SEQUENCE_IDS = (
    "confirmPrivateProductionEnv",
    "refreshDeploymentProof",
    "refreshRemoteApiProof",
    "refreshStorageProof",
    "refreshAuthProviderConfigProof",
    "refreshWechatClientConfigurationProof",
    "refreshIosReleaseReadinessProof",
    "refreshIosAppBundleProof",
    "refreshSmsLiveSendProof",
    "refreshAppStoreEvidenceProof",
    "refreshProductionReadinessCurrent",
    "syncStableAliasesAfterGreen",
    "refreshLaunchObjectiveAudit",
)
PRODUCTION_REFRESH_PACKET_SEQUENCE_MARKERS = (
    "/srv/xiaonaiping/private/xiaonaiping-api.env",
    "XNP_SECRET_KEY",
    "XNP_DATA_DIR",
    "xiaonaiping_prod",
    "XNP_DEPLOY_HOST=root@YOUR_SERVER Backend/deploy/deploy-huawei-baota.sh",
    "collect_deployment_proof.py",
    "verify_remote_api.py",
    "verify_storage_backend.py",
    "verify_auth_providers.py --live-check",
    "check_wechat_client_configuration.py",
    "check_ios_release_readiness.py",
    "check_ios_app_bundle.py",
    "--send-test-sms",
    "check_app_store_evidence.py --allow-incomplete",
    "check_production_readiness.py",
    "auth-providers-sms-live-20260629T-current.json",
    "cp Backend/proof/huawei-baota-deploy-20260629T-current.json Backend/proof/huawei-baota-deploy.json",
    "cp Backend/proof/remote-api-20260629T-current.json Backend/proof/remote-api.json",
    "cp Backend/proof/storage-backend-20260629T-current.json Backend/proof/storage-backend.json",
    "cp Backend/proof/auth-providers-sms-live-20260629T-current.json Backend/proof/auth-providers.json",
    "cp Backend/proof/wechat-client-configuration-20260630T-current.json Backend/proof/wechat-client-configuration.json",
    "cp Backend/proof/ios-release-readiness-20260629T-current-ios265.json Backend/proof/ios-release-readiness.json",
    "cp Backend/proof/ios-app-bundle-20260629T-current-ios265.json Backend/proof/ios-app-bundle.json",
    "cp Backend/proof/app-store-evidence-20260629T-current.json Backend/proof/app-store-evidence.json",
    "cp Backend/proof/production-readiness-20260629T-current.json Backend/proof/production-readiness.json",
    "check_launch_objective_audit.py --allow-incomplete",
)
PRODUCTION_REFRESH_PACKET_STOP_CONDITIONS = {
    "noDeployHost": ("XNP_DEPLOY_HOST", "wrong server"),
    "missingPrivateEnv": ("/srv/xiaonaiping/private/xiaonaiping-api.env", "do not create fake local env files"),
    "productionSecretOrDatabaseMissing": ("XNP_SECRET_KEY", "XNP_DATA_DIR", "xiaonaiping_prod", "xiaonaiping_app"),
    "obsProofMissingOrStale": ("Huawei OBS", "storage-backend-20260629T-current.json", "account deletion cleanup"),
    "smsLiveSendProofMissing": ("auth-providers-sms-live-20260629T-current.json", "Do not sync auth-providers.json"),
    "wechatProviderMissing": ("WeChat provider", "real wx AppID/AppSecret"),
    "appStoreEvidenceIncomplete": ("app-store-evidence-20260629T-current.json", "ready=true"),
    "ios265EvidenceMissing": ("iOS 26.5", "Do not use iOS 27, simulator"),
    "productionReadinessStillRed": ("production-readiness-20260629T-current.json", "ready=true"),
}
PRODUCTION_REFRESH_PACKET_POST_GATES = (
    "check_provider_evidence_materials.py",
    "check_app_store_submission_packet.py",
    "check_launch_blocker_action_packet.py",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
)
PRODUCTION_REFRESH_PACKET_COMPLETION_MARKERS = (
    "refresh-plan-not-evidence",
    "not submission permission",
    "same-day production proof refresh workflow",
    "stable aliases are synced from the same-round current proofs",
    "production-readiness.json ready=true",
    "app-store-evidence.json ready=true",
    "launch-objective-audit.json ready=true",
)
PRODUCTION_REFRESH_PACKET_FORBIDDEN_SECRET_MARKERS = (
    "sk-",
    "Bearer ",
    "debug_wechat_",
    "XNP_REVIEW_RECOVERY_KEY=",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def date_parts(date_value: str) -> tuple[str, str, str]:
    current = datetime.fromisoformat(date_value).date()
    return current.isoformat(), current.strftime("%Y%m%d"), (current - timedelta(days=1)).strftime("%Y%m%d")


def dated_text(value: str, date_value: str) -> str:
    iso, compact, previous_compact = date_parts(date_value)
    previous_iso = (datetime.fromisoformat(date_value).date() - timedelta(days=1)).isoformat()
    return (
        value
        .replace("2026-06-28", "__PREVIOUS_ISO_DATE__")
        .replace("20260628", "__PREVIOUS_COMPACT_DATE__")
        .replace("2026-06-29", "__CURRENT_ISO_DATE__")
        .replace("20260629", "__CURRENT_COMPACT_DATE__")
        .replace("__PREVIOUS_ISO_DATE__", previous_iso)
        .replace("__PREVIOUS_COMPACT_DATE__", previous_compact)
        .replace("__CURRENT_ISO_DATE__", iso)
        .replace("__CURRENT_COMPACT_DATE__", compact)
    )


def dated_markers(markers: list[str] | tuple[str, ...], date_value: str) -> list[str]:
    return [dated_text(marker, date_value) for marker in markers]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def input_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def latest_action_packet(root: Path) -> Path:
    packet_dir = root / "Docs/08_Release"
    packets = sorted(packet_dir.glob("LAUNCH_BLOCKER_ACTION_PACKET_*.md"))
    if packets:
        return packets[-1]
    return root / ACTION_PACKET


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def as_searchable_text(value: Any) -> str:
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return "\n".join(as_searchable_text(item) for item in value)
    return str(value or "")


def list_value(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def nested_check_evidence(data: dict[str, Any], name: str) -> str:
    checks = data.get("checks", {})
    if not isinstance(checks, dict):
        return ""
    check = checks.get(name, {})
    if not isinstance(check, dict):
        return ""
    evidence = check.get("evidence", "")
    return str(evidence) if evidence else ""


def ios265_build_log_markers(data: dict[str, Any]) -> list[str]:
    markers: list[str] = []
    for check_name in ("simulatorBuildLogSucceeded", "deviceBuildLogSucceeded"):
        evidence = nested_check_evidence(data, check_name)
        if evidence:
            markers.append(Path(evidence).name)
    return markers


def contains_all(text: str, markers: list[str] | tuple[str, ...]) -> tuple[bool, list[str]]:
    lower = text.lower()
    missing = [marker for marker in markers if marker.lower() not in lower]
    return not missing, missing


def production_refresh_packet_failures(packet: dict[str, Any], date_value: str) -> list[str]:
    if not packet:
        return ["production proof refresh packet invalid or missing"]

    failures: list[str] = []
    for key, expected in PRODUCTION_REFRESH_PACKET_SCALARS.items():
        dated_expected = dated_text(expected, date_value)
        if packet.get(key) != dated_expected:
            failures.append(f"{key} must be {dated_expected}")

    if packet.get("canSubmitFromThisPacket") is not False:
        failures.append("canSubmitFromThisPacket must be false")

    source_files = packet.get("sourceFiles")
    if not isinstance(source_files, dict):
        failures.append("sourceFiles must be an object")
    else:
        for key, expected in PRODUCTION_REFRESH_PACKET_SOURCE_FILES.items():
            dated_expected = dated_text(expected, date_value)
            if source_files.get(key) != dated_expected:
                failures.append(f"sourceFiles.{key} must be {dated_expected}")

    target_proofs = packet.get("targetProofFiles")
    if not isinstance(target_proofs, dict):
        failures.append("targetProofFiles must be an object")
    else:
        for key, expected in PRODUCTION_REFRESH_PACKET_TARGET_PROOFS.items():
            dated_expected = dated_text(expected, date_value)
            if target_proofs.get(key) != dated_expected:
                failures.append(f"targetProofFiles.{key} must be {dated_expected}")

    separation_text = as_searchable_text(packet.get("separationRules"))
    for marker in dated_markers(PRODUCTION_REFRESH_PACKET_SEPARATION_MARKERS, date_value):
        if marker not in separation_text:
            failures.append(f"separationRules missing {marker}")

    sequence = packet.get("refreshSequence")
    if not isinstance(sequence, list):
        failures.append("refreshSequence must be a list")
    else:
        sequence_ids = [
            item.get("step")
            for item in sequence
            if isinstance(item, dict)
        ]
        if tuple(sequence_ids) != PRODUCTION_REFRESH_PACKET_SEQUENCE_IDS:
            failures.append("refreshSequence order must be " + " -> ".join(PRODUCTION_REFRESH_PACKET_SEQUENCE_IDS))
        sequence_text = as_searchable_text(sequence)
        for marker in dated_markers(PRODUCTION_REFRESH_PACKET_SEQUENCE_MARKERS, date_value):
            if marker not in sequence_text:
                failures.append(f"refreshSequence missing {marker}")

    stop_conditions = packet.get("stopConditions")
    if not isinstance(stop_conditions, list):
        failures.append("stopConditions must be a list")
    else:
        by_id = {
            item.get("id"): item
            for item in stop_conditions
            if isinstance(item, dict)
        }
        for stop_id, markers in PRODUCTION_REFRESH_PACKET_STOP_CONDITIONS.items():
            item = by_id.get(stop_id)
            if not item:
                failures.append(f"stopConditions missing {stop_id}")
                continue
            item_text = as_searchable_text(item)
            for marker in dated_markers(markers, date_value):
                if marker not in item_text:
                    failures.append(f"stopConditions.{stop_id} missing {marker}")

    post_gate_text = as_searchable_text(packet.get("postRefreshGates"))
    for marker in PRODUCTION_REFRESH_PACKET_POST_GATES:
        if marker not in post_gate_text:
            failures.append(f"postRefreshGates missing {marker}")

    completion_rule = str(packet.get("completionRule", ""))
    for marker in PRODUCTION_REFRESH_PACKET_COMPLETION_MARKERS:
        if marker not in completion_rule:
            failures.append(f"completionRule missing {marker}")

    packet_text = as_searchable_text(packet)
    secret_hits = [marker for marker in PRODUCTION_REFRESH_PACKET_FORBIDDEN_SECRET_MARKERS if marker in packet_text]
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, details: dict[str, Any] | None = None) -> None:
        check: dict[str, Any] = {
            "passed": passed,
            "evidence": evidence,
        }
        if details:
            check.update(details)
        self.checks[name] = check

    def to_dict(
        self,
        started_at: str,
        completed_at: str,
        packet_path: Path,
        failed_objective_checks: list[str],
        missing_evidence: list[str],
    ) -> dict[str, Any]:
        failed = [name for name, check in self.checks.items() if check["passed"] is not True]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "passed": not failed,
            "failedRequiredChecks": failed,
            "actionPacket": str(packet_path),
            "launchObjectiveFailedChecks": failed_objective_checks,
            "missingEvidence": missing_evidence,
            "checks": self.checks,
        }


def required_evidence_markers(missing_evidence: list[str]) -> list[str]:
    markers: list[str] = []
    for name in missing_evidence:
        markers.extend(EVIDENCE_FILENAMES.get(name, [name]))
    return markers


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    _, compact_date, previous_compact_date = date_parts(args.date)
    packet_path = latest_action_packet(root) if not args.packet else input_path(root, args.packet)
    objective_path = input_path(root, args.launch_objective_audit)
    app_store_evidence_path = input_path(root, args.app_store_evidence)
    ios265_build_path = input_path(root, args.ios_265_build_proof)
    production_readiness_path = input_path(root, args.production_readiness)
    production_refresh_packet_path = input_path(
        root,
        args.production_refresh_packet
        or f"Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_{compact_date}.json",
    )
    auth_provider_targeted_log_path = input_path(
        root,
        args.auth_provider_targeted_test_log
        or f"Backend/proof/auth-provider-targeted-tests-{compact_date}.log",
    )

    packet = read_text(packet_path)
    objective = read_json(objective_path)
    app_store_evidence = read_json(app_store_evidence_path)
    ios265_build = read_json(ios265_build_path)
    production_readiness = read_json(production_readiness_path)
    production_refresh_packet = read_json(production_refresh_packet_path)
    auth_provider_targeted_log = read_text(auth_provider_targeted_log_path)
    failed_objective_checks = list_value(objective, "failedRequiredChecks")
    missing_evidence = list_value(app_store_evidence, "missingEvidence")
    production_failed_checks = list_value(production_readiness, "failedRequiredChecks")
    build_log_markers = ios265_build_log_markers(ios265_build)

    report = Report()
    report.add(
        "actionPacketPresent",
        bool(packet),
        str(packet_path) if packet else "missing action packet",
    )
    expected_packet_name = f"LAUNCH_BLOCKER_ACTION_PACKET_{compact_date}.md"
    report.add(
        "actionPacketDateMatches",
        packet_path.name == expected_packet_name,
        f"action packet must be {expected_packet_name}",
        {"actual": packet_path.name, "expected": expected_packet_name}
        if packet_path.name != expected_packet_name
        else None,
    )
    report.add(
        "launchObjectiveAuditReadable",
        bool(objective),
        str(objective_path) if objective else "missing or unreadable launch objective audit proof",
    )
    report.add(
        "appStoreEvidenceReadable",
        bool(app_store_evidence),
        str(app_store_evidence_path) if app_store_evidence else "missing or unreadable App Store evidence proof",
    )
    report.add(
        "ios265BuildProofReadable",
        bool(ios265_build),
        str(ios265_build_path) if ios265_build else "missing or unreadable iOS 26.5 build proof",
    )
    report.add(
        "productionReadinessReadable",
        bool(production_readiness),
        str(production_readiness_path) if production_readiness else "missing or unreadable production readiness proof",
    )
    report.add(
        "productionProofRefreshPacketPresent",
        bool(production_refresh_packet),
        str(production_refresh_packet_path)
        if production_refresh_packet
        else "missing production proof refresh packet",
    )

    objective_ok, missing_objective_markers = contains_all(packet, failed_objective_checks)
    report.add(
        "failedLaunchObjectiveChecksCovered",
        objective_ok,
        "all current failed launch objective checks are named",
        {"missingMarkers": missing_objective_markers} if missing_objective_markers else None,
    )

    evidence_markers = required_evidence_markers(missing_evidence)
    evidence_ok, missing_evidence_markers = contains_all(packet, evidence_markers)
    report.add(
        "missingEvidenceFilenamesCovered",
        evidence_ok,
        "all current missing App Store evidence filenames are named",
        {"missingMarkers": missing_evidence_markers} if missing_evidence_markers else None,
    )

    ios_ok, missing_ios_markers = contains_all(packet, IOS_265_MARKERS)
    report.add(
        "ios265OnlyRuleCovered",
        ios_ok,
        "local testing is constrained to iOS 26.5 and non-evidence devices are called out",
        {"missingMarkers": missing_ios_markers} if missing_ios_markers else None,
    )

    wechat_ok, missing_wechat_markers = contains_all(packet, WECHAT_MARKERS)
    report.add(
        "wechatExternalConfigActionsCovered",
        wechat_ok,
        "WeChat AppID/AppSecret/URL Scheme/Universal Link evidence actions are explicit",
        {"missingMarkers": missing_wechat_markers} if missing_wechat_markers else None,
    )

    rerun_ok, missing_rerun_markers = contains_all(packet, RERUN_COMMAND_MARKERS)
    report.add(
        "rerunCommandsCovered",
        rerun_ok,
        "unified gate and focused blocker commands are listed",
        {"missingMarkers": missing_rerun_markers} if missing_rerun_markers else None,
    )

    build_logs_ok, missing_build_log_markers = contains_all(packet, build_log_markers)
    report.add(
        "rerunCommandsUseCurrentIOS265BuildLogs",
        bool(build_log_markers) and build_logs_ok,
        "rerun command references current iOS 26.5 simulator/device build proof logs",
        {"missingMarkers": missing_build_log_markers} if missing_build_log_markers else None,
    )

    real_device_ok, missing_real_device_markers = contains_all(packet, REAL_DEVICE_MARKERS)
    report.add(
        "realDeviceEvidenceBoundaryCovered",
        real_device_ok,
        "real TestFlight or signed-device regression evidence boundary is explicit",
        {"missingMarkers": missing_real_device_markers} if missing_real_device_markers else None,
    )

    active_freshness_markers: list[str] = []
    for check_name, markers in PRODUCTION_FRESHNESS_MARKERS.items():
        if check_name in production_failed_checks:
            active_freshness_markers.extend(dated_markers(markers, args.date))
    freshness_ok, missing_freshness_markers = contains_all(packet, active_freshness_markers)
    report.add(
        "productionFreshnessBlockersCovered",
        freshness_ok,
        "current deployment/storage proof refresh blockers are called out",
        {"missingMarkers": missing_freshness_markers} if missing_freshness_markers else None,
    )

    production_refresh_doc_ok, missing_production_refresh_doc_markers = contains_all(
        packet,
        dated_markers(PRODUCTION_REFRESH_DOC_MARKERS, args.date),
    )
    report.add(
        "productionProofRefreshPacketReferenced",
        production_refresh_doc_ok,
        "launch blocker action packet references the structured production proof refresh packet and its no-evidence boundary",
        {"missingMarkers": missing_production_refresh_doc_markers} if missing_production_refresh_doc_markers else None,
    )

    production_refresh_failures = production_refresh_packet_failures(production_refresh_packet, args.date)
    report.add(
        "productionProofRefreshPacketValid",
        not production_refresh_failures,
        "production proof refresh packet locks current proof outputs, refresh order, stable alias sync, stop conditions, post gates, and no-submission boundary",
        {"failures": production_refresh_failures} if production_refresh_failures else None,
    )

    targeted_packet_ok, missing_targeted_packet_markers = contains_all(
        packet,
        dated_markers(AUTH_PROVIDER_TARGETED_PACKET_MARKERS, args.date),
    )
    stale_targeted_packet_markers = list(
        dict.fromkeys(
            marker
            for marker in (
                *STALE_AUTH_PROVIDER_TARGETED_MARKERS,
                f"auth-provider-targeted-tests-{previous_compact_date}.log",
            )
            if marker in packet
        )
    )
    report.add(
        "authProviderTargetedTestLogCurrent",
        bool(auth_provider_targeted_log)
        and targeted_packet_ok
        and not stale_targeted_packet_markers,
        "launch blocker action packet references the current auth-provider targeted test log",
        {
            **({"missingMarkers": missing_targeted_packet_markers} if missing_targeted_packet_markers else {}),
            **({"staleMarkers": stale_targeted_packet_markers} if stale_targeted_packet_markers else {}),
            **({"log": str(auth_provider_targeted_log_path)} if not auth_provider_targeted_log else {}),
        }
        if missing_targeted_packet_markers or stale_targeted_packet_markers or not auth_provider_targeted_log
        else None,
    )

    targeted_log_ok, missing_targeted_log_markers = contains_all(
        auth_provider_targeted_log,
        AUTH_PROVIDER_TARGETED_LOG_MARKERS,
    )
    report.add(
        "authProviderTargetedTestLogPassed",
        bool(auth_provider_targeted_log) and targeted_log_ok,
        "auth-provider targeted log proves Aliyun SMS adapter and auth provider verification tests passed",
        {"missingMarkers": missing_targeted_log_markers}
        if missing_targeted_log_markers
        else None,
    )

    active_testflight_prerequisite_markers: list[str] = []
    for check_name, markers in TESTFLIGHT_REGRESSION_PREREQUISITE_MARKERS.items():
        if check_name in production_failed_checks:
            active_testflight_prerequisite_markers.extend(markers)
    testflight_prerequisite_ok, missing_testflight_prerequisite_markers = contains_all(
        packet,
        active_testflight_prerequisite_markers,
    )
    report.add(
        "testflightRegressionPrerequisiteBlockersCovered",
        testflight_prerequisite_ok,
        "iOS 26.5 physical-device availability blocker is called out",
        {"missingMarkers": missing_testflight_prerequisite_markers} if missing_testflight_prerequisite_markers else None,
    )

    return report.to_dict(started_at, utc_now(), packet_path, failed_objective_checks, missing_evidence)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--packet", default="")
    parser.add_argument("--launch-objective-audit", default="Backend/proof/launch-objective-audit.json")
    parser.add_argument("--app-store-evidence", default="Backend/proof/app-store-evidence.json")
    parser.add_argument("--ios-265-build-proof", default=IOS_265_BUILD_PROOF)
    parser.add_argument("--production-readiness", default="Backend/proof/production-readiness.json")
    parser.add_argument("--production-refresh-packet", default="")
    parser.add_argument("--auth-provider-targeted-test-log", default="")
    parser.add_argument("--date", default="2026-06-30")
    parser.add_argument("--output", default="Backend/proof/launch-blocker-action-packet.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = input_path(Path(args.repo_root).resolve(), args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"launch blocker action packet passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"launch blocker action packet incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
