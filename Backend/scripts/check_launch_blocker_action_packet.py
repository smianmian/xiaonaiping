#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTION_PACKET = "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260626.md"
IOS_265_BUILD_PROOF = "Backend/proof/ios-265-build.json"

EVIDENCE_FILENAMES = {
    "companyAccount": ["01-company-account"],
    "mainlandAvailability": ["02-mainland-availability"],
    "mainlandFiling": ["03-app-filing"],
    "privacyLabel": ["04-privacy-label"],
    "signedArchive": ["05-signed-archive"],
    "testFlight": ["06-testflight"],
    "smsProvider": ["07-sms-provider"],
    "wechatOpenPlatform": ["08-wechat-open-platform"],
    "huaweiObsPolicy": ["09-obs-policy"],
    "finalScreenshots": ["10-final-screenshots"],
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
    packet_path = latest_action_packet(root) if not args.packet else input_path(root, args.packet)
    objective_path = input_path(root, args.launch_objective_audit)
    app_store_evidence_path = input_path(root, args.app_store_evidence)
    ios265_build_path = input_path(root, args.ios_265_build_proof)

    packet = read_text(packet_path)
    objective = read_json(objective_path)
    app_store_evidence = read_json(app_store_evidence_path)
    ios265_build = read_json(ios265_build_path)
    failed_objective_checks = list_value(objective, "failedRequiredChecks")
    missing_evidence = list_value(app_store_evidence, "missingEvidence")
    build_log_markers = ios265_build_log_markers(ios265_build)

    report = Report()
    report.add(
        "actionPacketPresent",
        bool(packet),
        str(packet_path) if packet else "missing action packet",
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

    return report.to_dict(started_at, utc_now(), packet_path, failed_objective_checks, missing_evidence)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--packet", default="")
    parser.add_argument("--launch-objective-audit", default="Backend/proof/launch-objective-audit.json")
    parser.add_argument("--app-store-evidence", default="Backend/proof/app-store-evidence.json")
    parser.add_argument("--ios-265-build-proof", default=IOS_265_BUILD_PROOF)
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
