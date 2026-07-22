#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


EXPECTED_REUSABLE_DRAFT_SOURCES = {
    "appStoreConnectCopy": {
        "App 名称",
        "副标题",
        "描述",
        "关键词",
        "分类",
        "年龄分级",
        "隐私政策 URL",
        "技术支持 URL",
        "审核备注",
    },
    "legalPublicUrls": {"privacy", "terms", "support"},
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_today() -> str:
    return datetime.now().astimezone().date().isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def compact_date(value: str) -> str:
    return value.replace("-", "")


def previous_day(value: str) -> str:
    return (datetime.strptime(value, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()


def default_packet_for(today: str) -> str:
    return f"Docs/08_Release/LAUNCH_DAY_ROLLOVER_{compact_date(today)}.json"


def expected_scalars(today: str) -> dict[str, Any]:
    return {
        "artifactType": "launch-day-rollover-packet",
        "status": "rollover-plan-not-evidence",
        "date": today,
        "previousEvidenceDate": previous_day(today),
        "project": "XiaoNaiPing",
        "appName": "小奶瓶",
    }


def expected_source_files(today: str) -> dict[str, str]:
    previous = compact_date(previous_day(today))
    return {
        "appStoreConnectFillSheet": f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{previous}.md",
        "appStoreConnectDraft": f"Docs/08_Release/APP_STORE_CONNECT_DRAFT_{previous}.json",
        "appStoreEvidenceChecklist": f"Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_{previous}.md",
        "productionProofRefreshPacket": f"Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_{previous}.json",
        "externalPlatformCapturePacket": f"Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_{previous}.json",
        "realDeviceFocusedCapturePacket": f"Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_{previous}.json",
        "finalScreenshotUploadPacket": f"Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_{previous}.json",
        "dunsPostDeliveryActions": "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
    }


def expected_current_day_execution_packets(today: str) -> dict[str, str]:
    current = compact_date(today)
    return {
        "appStoreConnectFieldFreeze": f"Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_{current}.json",
        "appStoreConnectSubmitReviewPreflight": f"Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_{current}.json",
        "appStoreManualEvidencePacket": f"Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_{current}.json",
        "appReviewTestAccountPacket": f"Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_{current}.json",
        "productionProofRefreshPacket": f"Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_{current}.json",
        "productionPrivacyEvidenceWorkbench": f"Docs/08_Release/XNP_PRODUCTION_PRIVACY_EVIDENCE_WORKBENCH_{current}.md",
        "externalPlatformCapturePacket": f"Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_{current}.json",
        "smsProviderLiveSendPacket": f"Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_{current}.json",
        "wechatReleaseConfigurationPacket": f"Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_{current}.json",
        "obsStorageProofPacket": f"Docs/08_Release/OBS_STORAGE_PROOF_PACKET_{current}.json",
        "mainlandFilingExecutionPacket": f"Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_{current}.json",
        "realDeviceFocusedCapturePacket": f"Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_{current}.json",
        "realDeviceCapturePreflightPacket": f"Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_{current}.json",
        "finalScreenshotUploadPacket": f"Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_{current}.json",
        "dunsPostDeliveryActions": "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
    }


def expected_same_day_refresh(today: str) -> dict[str, tuple[str, str, tuple[str, ...]]]:
    current = compact_date(today)
    previous = previous_day(today)
    previous_compact = compact_date(previous)
    return {
        "appStoreConnectPageEvidence": (
            "Docs/08_Release/AppStoreEvidence/AppStoreConnect/",
            "Backend/proof/app-store-connect-evidence-materials.json",
            (previous,),
        ),
        "appStoreManualEvidence": (
            "Docs/08_Release/AppStoreEvidence/",
            f"Backend/proof/app-store-evidence-{current}T-current.json",
            (previous,),
        ),
        "productionCurrentProofs": (
            f"Backend/proof/*-{current}T-current.json",
            f"Backend/proof/production-readiness-{current}T-current.json",
            (f"{previous_compact}T-current", previous),
        ),
        "providerEvidence": (
            "Docs/08_Release/AppStoreEvidence/07-sms-provider.png; "
            "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png; "
            "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png; "
            "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
            "Backend/proof/provider-evidence-materials.json",
            (previous,),
        ),
        "signedArchiveTestFlight": (
            "Docs/08_Release/AppStoreEvidence/05-signed-archive.png; "
            "Docs/08_Release/AppStoreEvidence/06-testflight.png; "
            "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-07-build-testflight-link.png",
            "Backend/proof/signed-archive-testflight-materials.json",
            (previous,),
        ),
        "finalScreenshotUploadProvenance": (
            "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
            "Backend/proof/app-store-assets.json",
            ("Debug simulator candidate provenance", f"{previous} candidate-only provenance"),
        ),
        "ios265RealDeviceRegression": (
            "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
            "Backend/proof/testflight-regression-plan.json",
            ("iOS 27", "simulator-only proof", previous),
        ),
        "dunsStatusPoll": (
            "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.json",
            "Backend/proof/signed-archive-testflight-materials.json",
            (previous,),
        ),
    }


def rollover_rule_markers(today: str) -> tuple[str, ...]:
    previous = previous_day(today)
    return (
        f"Do not copy {compact_date(previous)}T-current proof into any {compact_date(today)}T-current proof.",
        f"Stable aliases may sync only after {today} same-round current proofs pass.",
        f"captured or re-verified on {today}",
        "UPLOAD_PROVENANCE.json must come from iOS 26.5 TestFlight or Xcode signed physical-device build.",
        "local evidence only counts on iOS 26.5.",
        "live Apple portals after the D-U-N-S status changes.",
        "not Submit for Review permission.",
    )


def post_command_markers(today: str) -> tuple[str, ...]:
    current = compact_date(today)
    return (
        "python3 Backend/scripts/check_launch_day_rollover.py --output Backend/proof/launch-day-rollover.json",
        "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
        "python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
        f"python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date {today} --output Backend/proof/app-store-evidence-{current}T-current.json",
        "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json",
        "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
    )


def completion_rule_markers(today: str) -> tuple[str, ...]:
    return (
        "rollover-plan-not-evidence",
        "not submission permission",
        f"{today} submission requires same-day App Store manual evidence",
        "production current proofs",
        "provider evidence",
        "signed Archive/TestFlight evidence",
        "final screenshot UPLOAD_PROVENANCE.json",
        "iOS 26.5 real-device regression",
        "launch-objective-audit.json ready=true",
    )


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


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
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def check_scalars(packet: dict[str, Any], today: str) -> list[str]:
    return [
        f"{key}: expected {expected!r}, got {packet.get(key)!r}"
        for key, expected in expected_scalars(today).items()
        if packet.get(key) != expected
    ]


def check_packet_date_is_today(packet: dict[str, Any], today: str) -> list[str]:
    packet_date = packet.get("date")
    if packet_date == today:
        return []
    return [f"packet date {packet_date!r} is stale for today {today!r}"]


def check_source_files(root: Path, packet: dict[str, Any], today: str) -> list[str]:
    source_files = packet.get("sourceFiles", {})
    if not isinstance(source_files, dict):
        return ["sourceFiles must be an object"]

    failures: list[str] = []
    for key, expected in expected_source_files(today).items():
        actual = source_files.get(key)
        if actual != expected:
            failures.append(f"{key}: expected {expected}, got {actual!r}")
            continue
        if not (root / expected).is_file():
            failures.append(f"{key}: missing file {expected}")
    return failures


def check_current_day_execution_packets(root: Path, packet: dict[str, Any], today: str) -> list[str]:
    packets = packet.get("currentDayExecutionPackets", {})
    if not isinstance(packets, dict):
        return ["currentDayExecutionPackets must be an object"]

    failures: list[str] = []
    expected_packets = expected_current_day_execution_packets(today)
    if tuple(packets) != tuple(expected_packets):
        failures.append(
            "currentDayExecutionPackets order must be "
            + " -> ".join(expected_packets)
        )
    current = compact_date(today)
    previous = compact_date(previous_day(today))
    for key, expected in expected_packets.items():
        actual = packets.get(key)
        if actual != expected:
            failures.append(f"{key}: expected {expected}, got {actual!r}")
            continue
        if key != "dunsPostDeliveryActions" and current not in expected:
            failures.append(f"{key}: expected packet must be pinned to {current}")
        if previous in str(actual):
            failures.append(f"{key}: current-day execution packet must not point to {previous}")
        if not (root / expected).is_file():
            failures.append(f"{key}: missing file {expected}")
    return failures


def check_reusable_sources(packet: dict[str, Any], today: str) -> list[str]:
    sources = packet.get("reusableDraftSources", [])
    if not isinstance(sources, list):
        return ["reusableDraftSources must be a list"]

    by_id = {item.get("id"): item for item in sources if isinstance(item, dict)}
    failures: list[str] = []
    for source_id, expected_fields in EXPECTED_REUSABLE_DRAFT_SOURCES.items():
        item = by_id.get(source_id)
        if not isinstance(item, dict):
            failures.append(f"{source_id}: missing")
            continue
        fields = item.get("fields", [])
        if not isinstance(fields, list):
            failures.append(f"{source_id}: fields must be a list")
            continue
        missing_fields = sorted(expected_fields - set(str(field) for field in fields))
        if missing_fields:
            failures.append(f"{source_id}: missing fields {', '.join(missing_fields)}")
        if item.get("notEvidence") is not True:
            failures.append(f"{source_id}: notEvidence must be true")
        boundary = str(item.get("reuseBoundary", ""))
        if today not in boundary or "pass" not in boundary:
            failures.append(f"{source_id}: reuseBoundary must require {today} checks to pass")
    return failures


def check_same_day_refresh(packet: dict[str, Any], today: str) -> list[str]:
    refresh_items = packet.get("sameDayEvidenceRefresh", [])
    if not isinstance(refresh_items, list):
        return ["sameDayEvidenceRefresh must be a list"]

    by_id = {item.get("id"): item for item in refresh_items if isinstance(item, dict)}
    failures: list[str] = []
    for item_id, (target, gate, previous_markers) in expected_same_day_refresh(today).items():
        item = by_id.get(item_id)
        if not isinstance(item, dict):
            failures.append(f"{item_id}: missing")
            continue
        if item.get("target") != target:
            failures.append(f"{item_id}: target expected {target}, got {item.get('target')!r}")
        if item.get("requiredGate") != gate:
            failures.append(f"{item_id}: requiredGate expected {gate}, got {item.get('requiredGate')!r}")
        if item.get("mustRefreshOnOrAfter") != today:
            failures.append(f"{item_id}: mustRefreshOnOrAfter must be {today}")
        previous = item.get("previousDateNotAllowed", [])
        if not isinstance(previous, list):
            failures.append(f"{item_id}: previousDateNotAllowed must be a list")
            continue
        missing_previous = [marker for marker in previous_markers if marker not in previous]
        if missing_previous:
            failures.append(f"{item_id}: missing previousDateNotAllowed {', '.join(missing_previous)}")
    return failures


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    packet_path = root / (args.packet or default_packet_for(args.today))
    packet = read_json(packet_path)
    report = Report()

    report.add(
        "rolloverPacketPresent",
        bool(packet),
        str(packet_path.relative_to(root)) if packet else f"missing or invalid JSON: {packet_path.relative_to(root)}",
    )

    scalar_failures = check_scalars(packet, args.today)
    report.add(
        "rolloverPacketScalarsValid",
        not scalar_failures,
        f"date/status/project/app identity are pinned to {args.today}"
        if not scalar_failures
        else "failures: " + "; ".join(scalar_failures),
    )

    date_failures = check_packet_date_is_today(packet, args.today)
    report.add(
        "rolloverPacketDateIsToday",
        not date_failures,
        f"packet date matches current launch date {args.today}"
        if not date_failures
        else "failures: " + "; ".join(date_failures),
    )

    source_failures = check_source_files(root, packet, args.today)
    report.add(
        "rolloverSourceFilesPinned",
        not source_failures,
        f"all reusable {previous_day(args.today)} source material files are explicitly pinned and present"
        if not source_failures
        else "failures: " + "; ".join(source_failures),
    )

    current_packet_failures = check_current_day_execution_packets(root, packet, args.today)
    report.add(
        "currentDayExecutionPacketsPinned",
        not current_packet_failures,
        f"{args.today} execution packets are pinned for App Store Connect, external providers, real-device capture, final screenshots, filing, production refresh, and D-U-N-S actions"
        if not current_packet_failures
        else "failures: " + "; ".join(current_packet_failures),
    )

    reusable_failures = check_reusable_sources(packet, args.today)
    report.add(
        "reusableDraftSourcesBounded",
        not reusable_failures,
        f"copy/public URL reuse is bounded by current {args.today} checks and marked not evidence"
        if not reusable_failures
        else "failures: " + "; ".join(reusable_failures),
    )

    refresh_failures = check_same_day_refresh(packet, args.today)
    report.add(
        "sameDayEvidenceRefreshRequired",
        not refresh_failures,
        "same-day refresh is required for App Store pages, production proofs, providers, signed Archive/TestFlight, screenshots, iOS 26.5 real-device regression, and D-U-N-S polling"
        if not refresh_failures
        else "failures: " + "; ".join(refresh_failures),
    )

    rules = "\n".join(str(item) for item in packet.get("rolloverRules", []) if isinstance(item, str))
    missing_rules = missing_markers(rules, rollover_rule_markers(args.today))
    report.add(
        "rolloverRulesBlockStaleEvidence",
        not missing_rules,
        "rules block stale 20260628 current proof copies, simulator-only screenshot evidence, non-iOS 26.5 real-device evidence, and submission claims"
        if not missing_rules
        else "missing: " + ", ".join(missing_rules),
    )

    commands = "\n".join(str(item) for item in packet.get("postRolloverCommands", []) if isinstance(item, str))
    missing_commands = missing_markers(commands, post_command_markers(args.today))
    report.add(
        "postRolloverCommandsPresent",
        not missing_commands,
        "post-rollover commands rerun the local material, evidence, production, and launch audit gates"
        if not missing_commands
        else "missing: " + ", ".join(missing_commands),
    )

    completion_rule = str(packet.get("completionRule", ""))
    missing_completion = missing_markers(completion_rule, completion_rule_markers(args.today))
    report.add(
        "completionRuleBlocksSubmission",
        not missing_completion,
        "completion rule says this packet is not submission permission and requires same-day evidence plus launch objective audit ready=true"
        if not missing_completion
        else "missing: " + ", ".join(missing_completion),
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--packet")
    parser.add_argument("--output", default="Backend/proof/launch-day-rollover.json")
    parser.add_argument("--today", default=local_today())
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"launch day rollover passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"launch day rollover incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
