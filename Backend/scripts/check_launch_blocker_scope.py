#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_PRODUCTION_BLOCKERS = {
    "productionSecretConfigured",
    "productionDataDirConfigured",
    "mysqlDatabaseSelected",
    "mysqlDatabaseEnvPresent",
    "huaweiObsSelected",
    "huaweiObsEnvPresent",
    "phoneLoginProviderConfigured",
    "wechatLoginProviderConfigured",
    "privateOperationsDashboardConfigured",
    "xiaonaipingProductionNamespaceConfigured",
    "storageBackendProofPassed",
    "iosReleaseReadinessProofPassed",
    "iosAppBundleProofPassed",
    "authProvidersProofPassed",
    "appStoreManualEvidenceReady",
}

EXPECTED_APP_STORE_EVIDENCE_GAPS = {
    "companyAccount",
    "mainlandAvailability",
    "mainlandFiling",
    "privacyLabel",
    "signedArchive",
    "testFlight",
    "smsProvider",
    "wechatOpenPlatform",
    "huaweiObsPolicy",
    "realDeviceRegression",
}

EXPECTED_AUTH_PROVIDER_BLOCKERS = {"smsProviderConfigured", "wechatProviderConfigured"}
EXPECTED_IOS_RELEASE_BLOCKERS = {"weChatReleaseBuildSettingsConfigured"}
EXPECTED_IOS_APP_BUNDLE_BLOCKERS = {"weChatNativeConfigPresent", "weChatURLTypePresent"}


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


def list_value(data: dict[str, Any], key: str) -> set[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value}


def compare(actual: set[str], expected: set[str]) -> dict[str, Any]:
    unexpected = sorted(actual - expected)
    absent_expected = sorted(expected - actual)
    return {
        "actual": sorted(actual),
        "expected": sorted(expected),
        "unexpected": unexpected,
        "absentExpected": absent_expected,
        "scopeClean": not unexpected,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    started_at = utc_now()

    production = read_json(root / args.production_proof)
    app_store_evidence = read_json(root / args.app_store_evidence)
    auth_providers = read_json(root / args.auth_providers_proof)
    ios_release = read_json(root / args.ios_release_proof)
    ios_bundle = read_json(root / args.ios_app_bundle_proof)

    comparisons = {
        "productionReadiness": compare(
            list_value(production, "failedRequiredChecks"),
            EXPECTED_PRODUCTION_BLOCKERS,
        ),
        "appStoreEvidence": compare(
            list_value(app_store_evidence, "missingEvidence"),
            EXPECTED_APP_STORE_EVIDENCE_GAPS,
        ),
        "authProviders": compare(
            list_value(auth_providers, "failedRequiredChecks"),
            EXPECTED_AUTH_PROVIDER_BLOCKERS,
        ),
        "iosReleaseReadiness": compare(
            list_value(ios_release, "failedRequiredChecks"),
            EXPECTED_IOS_RELEASE_BLOCKERS,
        ),
        "iosAppBundle": compare(
            list_value(ios_bundle, "failedRequiredChecks"),
            EXPECTED_IOS_APP_BUNDLE_BLOCKERS,
        ),
    }

    unexpected = {
        name: comparison["unexpected"]
        for name, comparison in comparisons.items()
        if comparison["unexpected"]
    }

    return {
        "startedAt": started_at,
        "completedAt": utc_now(),
        "passed": not unexpected,
        "unexpectedBlockers": unexpected,
        "comparisons": comparisons,
        "knownBlockerMeaning": {
            "productionEnv": "Private production env, MySQL, OBS, dashboard, and namespace values are not proven in this local current proof.",
            "sms": "SMS webhook provider private env is not loaded in the current proof, and provider screenshot evidence is not archived.",
            "wechat": "WeChat Open Platform AppID/AppSecret and real wx URL Scheme are not configured.",
            "appStoreManualEvidence": "App Store Connect screenshots, filing, signed archive, TestFlight, providers, OBS policy, and real-device regression are not archived.",
            "notSubmissionReady": "This proof only says remaining blockers are known; it does not make the app submission-ready.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--production-proof", default="Backend/proof/production-readiness.json")
    parser.add_argument("--app-store-evidence", default="Backend/proof/app-store-evidence.json")
    parser.add_argument("--auth-providers-proof", default="Backend/proof/auth-providers.json")
    parser.add_argument("--ios-release-proof", default="Backend/proof/ios-release-readiness.json")
    parser.add_argument("--ios-app-bundle-proof", default="Backend/proof/ios-app-bundle.json")
    parser.add_argument("--output", default="Backend/proof/launch-blocker-scope.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"launch blocker scope passed: {output_path}")
        return

    print(f"launch blocker scope has unexpected blockers: {output_path}", file=sys.stderr)
    print(json.dumps(result["unexpectedBlockers"], ensure_ascii=False, sort_keys=True), file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
