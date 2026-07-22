#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def proof_bool(data: dict[str, Any]) -> bool:
    if "passed" in data:
        return data.get("passed") is True
    if "ready" in data:
        return data.get("ready") is True
    return False


def check_passed(data: dict[str, Any], name: str) -> bool:
    checks = data.get("checks", {})
    if not isinstance(checks, dict):
        return False
    check = checks.get(name, {})
    return isinstance(check, dict) and check.get("passed") is True


def failed_detail(data: dict[str, Any]) -> str:
    failed = data.get("failedRequiredChecks")
    if failed:
        return "failedRequiredChecks=" + ", ".join(str(item) for item in failed)
    missing = data.get("missingEvidence")
    if missing:
        return "missingEvidence=" + ", ".join(str(item) for item in missing)
    if "passed" in data:
        return f"passed={data.get('passed')}"
    if "ready" in data:
        return f"ready={data.get('ready')}"
    return "proof missing or unreadable"


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "ready": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    report = Report()

    production = read_json(root / args.production_readiness)
    ios_265 = read_json(root / args.ios_265_build)
    ios265_device_availability = read_json(root / args.ios265_device_availability)
    ios_release = read_json(root / args.ios_release)
    ios_bundle = read_json(root / args.ios_app_bundle)
    auth = read_json(root / args.auth_providers)
    app_store_assets = read_json(root / args.app_store_assets)
    privacy_materials = read_json(root / args.app_store_connect_materials)
    app_store_connect_evidence_materials = read_json(root / args.app_store_connect_evidence_materials)
    submission = read_json(root / args.app_store_submission_packet)
    launch_day_rollover = read_json(root / args.launch_day_rollover)
    launch_operator_workbench = read_json(root / args.launch_operator_workbench)
    mainland_filing_materials = read_json(root / args.mainland_filing_materials)
    signed_archive_testflight_materials = read_json(root / args.signed_archive_testflight_materials)
    provider_evidence_materials = read_json(root / args.provider_evidence_materials)
    testflight = read_json(root / args.testflight_precheck)
    testflight_plan = read_json(root / args.testflight_regression_plan)
    app_store_evidence = read_json(root / args.app_store_evidence)
    review_notes = read_json(root / args.review_notes)
    remote_api = read_json(root / args.remote_api)
    public_pages = read_json(root / args.public_pages)
    legal_drafts = read_json(root / args.legal_drafts)
    diagnostics = read_json(root / args.diagnostics_redaction)
    universal_links = read_json(root / args.universal_links)
    wechat_client_configuration = read_json(root / args.wechat_client_configuration)
    storage = read_json(root / args.storage_backend)

    ios_265_ok = proof_bool(ios_265)
    report.add(
        "ios265BuildGreen",
        ios_265_ok,
        "iOS 26.5 simulator/device build proof passed" if ios_265_ok else failed_detail(ios_265),
    )

    ios265_device_availability_ok = proof_bool(ios265_device_availability)
    report.add(
        "ios265PhysicalDeviceAvailabilityReady",
        ios265_device_availability_ok,
        "iOS 26.5 physical-device availability proof passed"
        if ios265_device_availability_ok
        else failed_detail(ios265_device_availability),
    )

    bundle_id_ok = (
        check_passed(ios_265, "simulatorBundleIdentifierMatches")
        and check_passed(ios_265, "deviceBundleIdentifierMatches")
        and check_passed(ios_bundle, "bundleIdentifierMatches")
    )
    report.add(
        "bundleIdentifierGreen",
        bundle_id_ok,
        "Bundle ID matches com.mewpow.xiaonaiping in iOS 26.5 and built app proofs"
        if bundle_id_ok
        else "Bundle ID checks are missing or failed",
    )

    wechat_ok = (
        check_passed(ios_release, "weChatReleaseBuildSettingsConfigured")
        and check_passed(ios_bundle, "weChatNativeConfigPresent")
        and check_passed(ios_bundle, "weChatURLTypePresent")
        and proof_bool(auth)
    )
    report.add(
        "weChatConfigurationGreen",
        wechat_ok,
        "WeChat release build settings, URL type, bundle config, and auth provider are ready"
        if wechat_ok
        else "; ".join(
            detail
            for detail in [
                "ios-release: " + failed_detail(ios_release),
                "ios-app-bundle: " + failed_detail(ios_bundle),
                "auth-providers: " + failed_detail(auth),
            ]
        ),
    )

    wechat_client_handoff_ok = proof_bool(wechat_client_configuration)
    report.add(
        "weChatClientConfigurationHandoffReady",
        wechat_client_handoff_ok,
        "WeChat client configuration handoff covers iOS 26.5 validation, Info.plist slots, build settings, and secret boundaries"
        if wechat_client_handoff_ok
        else failed_detail(wechat_client_configuration),
    )

    privacy_ok = (
        check_passed(ios_release, "privacyManifestPresent")
        and check_passed(ios_release, "privacyManifestTrackingDisabled")
        and check_passed(ios_release, "privacyManifestMatchesPrivacyLabel")
        and check_passed(ios_265, "simulatorPrivacyManifestBundled")
        and check_passed(ios_265, "devicePrivacyManifestBundled")
        and check_passed(ios_265, "simulatorPrivacyManifestTrackingDisabled")
        and check_passed(ios_265, "devicePrivacyManifestTrackingDisabled")
        and check_passed(ios_265, "simulatorPrivacyManifestDataTypesAligned")
        and check_passed(ios_265, "devicePrivacyManifestDataTypesAligned")
    )
    report.add(
        "privacyManifestGreen",
        privacy_ok,
        "PrivacyInfo.xcprivacy is bundled, non-tracking, and aligned with the App Store privacy label"
        if privacy_ok
        else "Privacy manifest checks are missing or failed",
    )

    backend_proofs_ok = all(
        proof_bool(proof)
        for proof in [remote_api, storage, diagnostics, public_pages, legal_drafts, universal_links]
    )
    report.add(
        "backendProofsGreen",
        backend_proofs_ok,
        "remote API, storage, diagnostics, public pages, legal drafts, and universal links proofs passed"
        if backend_proofs_ok
        else "; ".join(
            [
                "remote-api: " + failed_detail(remote_api),
                "storage: " + failed_detail(storage),
                "diagnostics: " + failed_detail(diagnostics),
                "public-pages: " + failed_detail(public_pages),
                "legal-drafts: " + failed_detail(legal_drafts),
                "universal-links: " + failed_detail(universal_links),
            ]
        ),
    )

    app_store_materials_ok = proof_bool(privacy_materials)
    report.add(
        "appStoreConnectMaterialsReady",
        app_store_materials_ok,
        "App name, subtitle, description, keywords, category, age rating, URLs, privacy label, and screenshot copy passed"
        if app_store_materials_ok
        else failed_detail(privacy_materials),
    )

    app_store_connect_evidence_materials_ok = proof_bool(app_store_connect_evidence_materials)
    report.add(
        "appStoreConnectEvidenceMaterialsReady",
        app_store_connect_evidence_materials_ok,
        "company account, mainland availability, and App Privacy evidence material checklist is internally complete and does not claim real evidence before files exist"
        if app_store_connect_evidence_materials_ok
        else failed_detail(app_store_connect_evidence_materials),
    )

    launch_day_rollover_ok = proof_bool(launch_day_rollover)
    report.add(
        "launchDayRolloverReady",
        launch_day_rollover_ok,
        "current launch-day rollover proof separates reusable draft copy from same-day evidence refresh"
        if launch_day_rollover_ok
        else failed_detail(launch_day_rollover),
    )

    launch_operator_workbench_ok = proof_bool(launch_operator_workbench)
    report.add(
        "launchOperatorWorkbenchReady",
        launch_operator_workbench_ok,
        "current operator workbench covers App Store Connect draft fields, D-U-N-S actions, TestFlight/iOS 26.5 capture templates, and external platform next actions"
        if launch_operator_workbench_ok
        else failed_detail(launch_operator_workbench),
    )

    app_store_assets_ok = proof_bool(app_store_assets)
    report.add(
        "appStoreAssetsReady",
        app_store_assets_ok,
        "1024 icon and final screenshot count, upload order, sizes, non-blank pixel content, and iOS 26.5 screenshot provenance passed"
        if app_store_assets_ok
        else failed_detail(app_store_assets),
    )

    review_notes_ok = proof_bool(review_notes) and proof_bool(submission)
    report.add(
        "reviewNotesAndSubmissionBoundariesReady",
        review_notes_ok,
        "Review notes and submission packet cover Live Activity/widget data source and non-medical boundaries"
        if review_notes_ok
        else "review-notes: " + failed_detail(review_notes) + "; submission: " + failed_detail(submission),
    )

    mainland_filing_materials_ok = proof_bool(mainland_filing_materials)
    report.add(
        "mainlandFilingMaterialsReady",
        mainland_filing_materials_ok,
        "mainland App filing/ICP material checklist is internally complete and aligned with evidence filenames"
        if mainland_filing_materials_ok
        else failed_detail(mainland_filing_materials),
    )

    signed_archive_testflight_materials_ok = proof_bool(signed_archive_testflight_materials)
    report.add(
        "signedArchiveTestFlightMaterialsReady",
        signed_archive_testflight_materials_ok,
        "signed archive and TestFlight material checklist is internally complete and separates local proof from real upload evidence"
        if signed_archive_testflight_materials_ok
        else failed_detail(signed_archive_testflight_materials),
    )

    provider_evidence_materials_ok = proof_bool(provider_evidence_materials)
    report.add(
        "providerEvidenceMaterialsReady",
        provider_evidence_materials_ok,
        "SMS, WeChat Open Platform, and Huawei OBS evidence material checklist is internally complete and does not claim real evidence before files exist"
        if provider_evidence_materials_ok
        else failed_detail(provider_evidence_materials),
    )

    testflight_client_ok = proof_bool(testflight)
    report.add(
        "testFlightClientPrecheckReady",
        testflight_client_ok,
        "Widget, Live Activity, Dynamic Island, notifications, App Group, and boundary checks passed"
        if testflight_client_ok
        else failed_detail(testflight),
    )

    review_test_account_ok = check_passed(app_store_evidence, "reviewTestAccount") and check_passed(
        testflight_plan, "reviewAccountRedactedProofPresent"
    )
    report.add(
        "reviewTestAccountEvidenceReady",
        review_test_account_ok,
        "redacted App Review test account proof is present, verified, sync-seeded, and secret-free"
        if review_test_account_ok
        else "review test account redacted proof is missing or failed",
    )

    testflight_plan_ok = proof_bool(testflight_plan) and check_passed(testflight_plan, "realDeviceEvidenceGateSeparated")
    report.add(
        "testFlightRegressionPlanReadyButNotEvidence",
        testflight_plan_ok,
        "Regression plan passed and explicitly separates plan proof from real-device evidence"
        if testflight_plan_ok
        else failed_detail(testflight_plan),
    )

    real_device_evidence_ready = (
        isinstance(app_store_evidence.get("checks", {}), dict)
        and check_passed(app_store_evidence, "realDeviceRegression")
    )
    report.add(
        "realDeviceRegressionEvidenceReady",
        real_device_evidence_ready,
        "iOS 26.5 TestFlight/signed-device regression evidence is present"
        if real_device_evidence_ready
        else "realDeviceRegression missing from App Store evidence",
    )

    manual_evidence_ok = proof_bool(app_store_evidence)
    report.add(
        "appStoreManualEvidenceReady",
        manual_evidence_ok,
        "all App Store manual evidence is present" if manual_evidence_ok else failed_detail(app_store_evidence),
    )

    production_ready = production.get("ready") is True
    report.add(
        "productionReadinessGreen",
        production_ready,
        "production readiness is green" if production_ready else failed_detail(production),
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--production-readiness", default="Backend/proof/production-readiness.json")
    parser.add_argument("--ios-265-build", default="Backend/proof/ios-265-build.json")
    parser.add_argument("--ios265-device-availability", default="Backend/proof/ios265-device-availability.json")
    parser.add_argument("--ios-release", default="Backend/proof/ios-release-readiness.json")
    parser.add_argument("--ios-app-bundle", default="Backend/proof/ios-app-bundle.json")
    parser.add_argument("--auth-providers", default="Backend/proof/auth-providers.json")
    parser.add_argument("--app-store-assets", default="Backend/proof/app-store-assets.json")
    parser.add_argument("--app-store-connect-materials", default="Backend/proof/app-store-connect-materials.json")
    parser.add_argument("--app-store-connect-evidence-materials", default="Backend/proof/app-store-connect-evidence-materials.json")
    parser.add_argument("--app-store-submission-packet", default="Backend/proof/app-store-submission-packet.json")
    parser.add_argument("--launch-day-rollover", default="Backend/proof/launch-day-rollover.json")
    parser.add_argument("--launch-operator-workbench", default="Backend/proof/launch-operator-workbench.json")
    parser.add_argument("--mainland-filing-materials", default="Backend/proof/mainland-filing-materials.json")
    parser.add_argument("--signed-archive-testflight-materials", default="Backend/proof/signed-archive-testflight-materials.json")
    parser.add_argument("--provider-evidence-materials", default="Backend/proof/provider-evidence-materials.json")
    parser.add_argument("--testflight-precheck", default="Backend/proof/testflight-precheck.json")
    parser.add_argument("--testflight-regression-plan", default="Backend/proof/testflight-regression-plan.json")
    parser.add_argument("--app-store-evidence", default="Backend/proof/app-store-evidence.json")
    parser.add_argument("--review-notes", default="Backend/proof/review-notes.json")
    parser.add_argument("--remote-api", default="Backend/proof/remote-api.json")
    parser.add_argument("--public-pages", default="Backend/proof/public-pages.json")
    parser.add_argument("--legal-drafts", default="Backend/proof/legal-drafts.json")
    parser.add_argument("--diagnostics-redaction", default="Backend/proof/diagnostics-redaction.json")
    parser.add_argument("--universal-links", default="Backend/proof/universal-links.json")
    parser.add_argument("--wechat-client-configuration", default="Backend/proof/wechat-client-configuration.json")
    parser.add_argument("--storage-backend", default="Backend/proof/storage-backend.json")
    parser.add_argument("--output", default="Backend/proof/launch-objective-audit.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["ready"]:
        print(f"launch objective audit passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"launch objective audit incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
