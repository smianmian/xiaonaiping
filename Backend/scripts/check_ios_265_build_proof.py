#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_BUNDLE_ID = "com.mewpow.xiaonaiping"
EXPECTED_API_URL = "https://api.mewpow.com/xiaonaiping"
EXPECTED_PLATFORM_VERSION = "26.5"
EXPECTED_SIM_SDK = "iphonesimulator26.5"
EXPECTED_DEVICE_SDK = "iphoneos26.5"
EXPECTED_PRIVACY_DATA_TYPES = {
    "NSPrivacyCollectedDataTypeUserID",
    "NSPrivacyCollectedDataTypePhoneNumber",
    "NSPrivacyCollectedDataTypeOtherUserContent",
    "NSPrivacyCollectedDataTypePhotosorVideos",
    "NSPrivacyCollectedDataTypeHealth",
    "NSPrivacyCollectedDataTypeProductInteraction",
    "NSPrivacyCollectedDataTypeCrashData",
    "NSPrivacyCollectedDataTypePerformanceData",
}
SDK_MARKER_RE = re.compile(r"\biphone(?:simulator|os)([0-9]+(?:\.[0-9]+)?)\b", re.IGNORECASE)
RUNTIME_MARKER_RE = re.compile(r"\b(?:OS=|iOS[ -])([0-9]+(?:\.[0-9]+)?)\b", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_plist(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            data = plistlib.load(file)
    except (FileNotFoundError, plistlib.InvalidFileException, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def unexpected_ios_markers(text: str) -> list[str]:
    markers: set[str] = set()
    for pattern in [SDK_MARKER_RE, RUNTIME_MARKER_RE]:
        for match in pattern.finditer(text):
            if match.group(1) != EXPECTED_PLATFORM_VERSION:
                markers.add(match.group(0))
    return sorted(markers, key=str.lower)


def privacy_manifest_data_type_failures(manifest: dict[str, Any]) -> list[str]:
    entries = manifest.get("NSPrivacyCollectedDataTypes")
    if not isinstance(entries, list):
        return ["missing NSPrivacyCollectedDataTypes"]

    names: set[str] = set()
    tracking_names: list[str] = []
    missing_purpose_names: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("NSPrivacyCollectedDataType", ""))
        if name:
            names.add(name)
        if entry.get("NSPrivacyCollectedDataTypeTracking") is not False:
            tracking_names.append(name or "<unknown>")
        purposes = entry.get("NSPrivacyCollectedDataTypePurposes")
        if not isinstance(purposes, list) or not purposes:
            missing_purpose_names.append(name or "<unknown>")

    failures: list[str] = []
    missing = sorted(EXPECTED_PRIVACY_DATA_TYPES - names)
    unexpected = sorted(names - EXPECTED_PRIVACY_DATA_TYPES)
    if missing:
        failures.append("missing data types: " + ", ".join(missing))
    if unexpected:
        failures.append("unexpected data types: " + ", ".join(unexpected))
    if tracking_names:
        failures.append("tracking enabled for: " + ", ".join(sorted(tracking_names)))
    if missing_purpose_names:
        failures.append("missing purposes for: " + ", ".join(sorted(missing_purpose_names)))
    return failures


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str, simulator_app: Path, device_app: Path) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "simulatorAppPath": str(simulator_app),
            "deviceAppPath": str(device_app),
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def add_app_checks(report: Report, prefix: str, app_path: Path, expected_sdk: str) -> None:
    info = read_plist(app_path / "Info.plist")
    privacy_manifest_path = app_path / "PrivacyInfo.xcprivacy"
    privacy_manifest = read_plist(privacy_manifest_path)
    report.add(f"{prefix}AppBundleExists", app_path.is_dir(), str(app_path))
    report.add(f"{prefix}InfoPlistPresent", bool(info), str(app_path / "Info.plist") if info else "missing or invalid Info.plist")
    report.add(
        f"{prefix}BuiltWithIOS265",
        info.get("DTPlatformVersion") == EXPECTED_PLATFORM_VERSION and info.get("DTSDKName") == expected_sdk,
        f"DTPlatformVersion={info.get('DTPlatformVersion', '<missing>')}, DTSDKName={info.get('DTSDKName', '<missing>')}",
    )
    report.add(
        f"{prefix}BundleIdentifierMatches",
        info.get("CFBundleIdentifier") == EXPECTED_BUNDLE_ID,
        f"CFBundleIdentifier={info.get('CFBundleIdentifier', '<missing>')}",
    )
    report.add(
        f"{prefix}ReleaseApiBaseURLMatches",
        info.get("XNPAPIBaseURL") == EXPECTED_API_URL,
        f"XNPAPIBaseURL={info.get('XNPAPIBaseURL', '<missing>')}",
    )
    report.add(
        f"{prefix}LiveActivitiesEnabled",
        info.get("NSSupportsLiveActivities") is True,
        f"NSSupportsLiveActivities={info.get('NSSupportsLiveActivities', '<missing>')}",
    )
    report.add(
        f"{prefix}PrivacyManifestBundled",
        privacy_manifest_path.is_file(),
        str(privacy_manifest_path),
    )
    tracking_domains = privacy_manifest.get("NSPrivacyTrackingDomains")
    tracking_disabled = (
        bool(privacy_manifest)
        and privacy_manifest.get("NSPrivacyTracking") is False
        and (tracking_domains == [] or tracking_domains is None)
    )
    report.add(
        f"{prefix}PrivacyManifestTrackingDisabled",
        tracking_disabled,
        "tracking disabled and tracking domains empty"
        if tracking_disabled
        else "PrivacyInfo.xcprivacy must set NSPrivacyTracking=false and no tracking domains",
    )
    data_type_failures = privacy_manifest_data_type_failures(privacy_manifest) if privacy_manifest else ["missing or invalid PrivacyInfo.xcprivacy"]
    report.add(
        f"{prefix}PrivacyManifestDataTypesAligned",
        not data_type_failures,
        "collected data types align with App Store privacy label and every entry is non-tracking"
        if not data_type_failures
        else "; ".join(data_type_failures),
    )
    report.add(
        f"{prefix}WidgetExtensionBundled",
        (app_path / "PlugIns/XiaoNaiPingWidgets.appex").is_dir(),
        str(app_path / "PlugIns/XiaoNaiPingWidgets.appex"),
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    simulator_app = Path(args.simulator_app).resolve()
    device_app = Path(args.device_app).resolve()
    simulator_log = Path(args.simulator_log).resolve()
    device_log = Path(args.device_log).resolve() if args.device_log else None
    report = Report()

    add_app_checks(report, "simulator", simulator_app, EXPECTED_SIM_SDK)
    add_app_checks(report, "device", device_app, EXPECTED_DEVICE_SDK)

    simulator_log_text = read_text(simulator_log)
    simulator_unexpected_markers = unexpected_ios_markers(simulator_log_text)
    report.add(
        "simulatorBuildLogSucceeded",
        "BUILD SUCCEEDED" in simulator_log_text and EXPECTED_SIM_SDK in simulator_log_text,
        str(simulator_log) if simulator_log_text else "missing simulator build log",
    )
    report.add(
        "simulatorBuildLogIOS265Only",
        bool(simulator_log_text) and not simulator_unexpected_markers,
        str(simulator_log)
        if simulator_log_text and not simulator_unexpected_markers
        else "unexpected SDK/runtime markers: " + ", ".join(simulator_unexpected_markers),
    )

    if device_log:
        device_log_text = read_text(device_log)
        device_unexpected_markers = unexpected_ios_markers(device_log_text)
        report.add(
            "deviceBuildLogSucceeded",
            "BUILD SUCCEEDED" in device_log_text and EXPECTED_DEVICE_SDK in device_log_text,
            str(device_log) if device_log_text else "missing device build log",
        )
        report.add(
            "deviceBuildLogIOS265Only",
            bool(device_log_text) and not device_unexpected_markers,
            str(device_log)
            if device_log_text and not device_unexpected_markers
            else "unexpected SDK/runtime markers: " + ", ".join(device_unexpected_markers),
        )
    else:
        report.add(
            "deviceBuildLogSucceeded",
            True,
            "device app artifact Info.plist is used as current build proof; no separate log supplied",
            required=False,
        )
        report.add(
            "deviceBuildLogIOS265Only",
            True,
            "device app artifact Info.plist is used as current build proof; no separate log supplied",
            required=False,
        )

    return report.to_dict(started_at, utc_now(), simulator_app, device_app)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument(
        "--simulator-app",
        default="/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app",
    )
    parser.add_argument(
        "--device-app",
        default="/tmp/XiaoNaiPing-Gate-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app",
    )
    parser.add_argument("--simulator-log", default="Backend/proof/xcodebuild-release-ios265-20260626.log")
    parser.add_argument("--device-log", default="")
    parser.add_argument("--output", default="Backend/proof/ios-265-build.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"iOS 26.5 build proof passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"iOS 26.5 build proof incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
