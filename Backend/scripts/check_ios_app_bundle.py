#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLACEHOLDER_HOSTS = (
    "api.example.com",
    "example.com",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
)

REQUIRED_WECHAT_QUERY_SCHEMES = {"weixin", "weixinULAPI"}
WECHAT_PLACEHOLDER_MARKERS = (
    "placeholder",
    "example",
    "your",
    "replace",
    "changeme",
    "todo",
    "debug",
    "dryrun",
    "test",
)
WECHAT_SAMPLE_APP_ID_BODIES = {
    "0123456789abcdef",
    "1234567890abcdef",
    "abcdef1234567890",
    "fedcba9876543210",
}
REQUIRED_PRIVACY_TYPES = {
    "NSPrivacyCollectedDataTypeUserID",
    "NSPrivacyCollectedDataTypePhoneNumber",
    "NSPrivacyCollectedDataTypeOtherUserContent",
    "NSPrivacyCollectedDataTypePhotosorVideos",
    "NSPrivacyCollectedDataTypeHealth",
    "NSPrivacyCollectedDataTypeProductInteraction",
    "NSPrivacyCollectedDataTypeCrashData",
    "NSPrivacyCollectedDataTypePerformanceData",
}
DISALLOWED_BUNDLE_SUFFIXES = {
    ".backup",
    ".bak",
    ".env",
    ".htm",
    ".html",
    ".markdown",
    ".md",
}
DISALLOWED_BUNDLE_NAMES = {
    ".env",
    "README",
    "Secrets.plist",
}
TEXT_RESOURCE_SUFFIXES = {
    ".json",
    ".plist",
    ".strings",
    ".txt",
    ".xcprivacy",
}
FORBIDDEN_TEXT_MARKERS = {
    "127.0.0.1",
    "localhost",
    "api.openai.com",
    "api.deepseek.com",
    "generativelanguage.googleapis.com",
    "debug_wechat_",
    "sk-",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_plist(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            data = plistlib.load(file)
    except (FileNotFoundError, plistlib.InvalidFileException, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def is_placeholder_url(value: str) -> bool:
    lower = value.lower()
    return any(host in lower for host in PLACEHOLDER_HOSTS)


def is_real_wechat_app_id(value: str) -> bool:
    value = value.strip()
    lower = value.lower()
    if any(marker in lower for marker in WECHAT_PLACEHOLDER_MARKERS):
        return False
    if re.fullmatch(r"wx[0-9a-fA-F]{16}", value) is None:
        return False

    body = lower[2:]
    if body in WECHAT_SAMPLE_APP_ID_BODIES:
        return False
    if body == body[0] * len(body):
        return False
    return True


def collected_privacy_types(manifest: dict[str, Any]) -> set[str]:
    entries = manifest.get("NSPrivacyCollectedDataTypes")
    if not isinstance(entries, list):
        return set()
    result: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        data_type = entry.get("NSPrivacyCollectedDataType")
        if isinstance(data_type, str):
            result.add(data_type)
    return result


def privacy_tracking_failures(manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if manifest.get("NSPrivacyTracking") is not False:
        failures.append("NSPrivacyTracking must be false")
    tracking_domains = manifest.get("NSPrivacyTrackingDomains")
    if not isinstance(tracking_domains, list) or tracking_domains:
        failures.append("NSPrivacyTrackingDomains must be an empty array")
    for entry in manifest.get("NSPrivacyCollectedDataTypes", []):
        if not isinstance(entry, dict):
            failures.append("collected data entry is not a dictionary")
            continue
        data_type = str(entry.get("NSPrivacyCollectedDataType", "<missing>"))
        if entry.get("NSPrivacyCollectedDataTypeTracking") is not False:
            failures.append(f"{data_type} tracking must be false")
    return failures


def app_binary_contains(app_path: Path, info: dict[str, Any], marker: bytes) -> tuple[bool, str]:
    executable = info.get("CFBundleExecutable")
    if not isinstance(executable, str) or not executable:
        return False, "CFBundleExecutable is missing"
    executable_path = app_path / executable
    try:
        data = executable_path.read_bytes()
    except OSError as error:
        return False, f"cannot read executable: {error}"
    return marker in data, f"{marker.decode('utf-8', errors='replace')} {'found' if marker in data else 'not found'} in {executable}"


def bundle_url_types_include_wechat(info: dict[str, Any]) -> bool:
    url_types = info.get("CFBundleURLTypes")
    if not isinstance(url_types, list):
        return False
    for item in url_types:
        if not isinstance(item, dict):
            continue
        schemes = item.get("CFBundleURLSchemes")
        if not isinstance(schemes, list):
            continue
        for scheme in schemes:
            if isinstance(scheme, str) and is_real_wechat_app_id(scheme):
                return True
    return False


def disallowed_bundle_files(app_path: Path) -> list[str]:
    result: list[str] = []
    for path in app_path.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        suffix = path.suffix.lower()
        if name in DISALLOWED_BUNDLE_NAMES or suffix in DISALLOWED_BUNDLE_SUFFIXES:
            result.append(str(path.relative_to(app_path)))
    return sorted(result)


def text_resource_marker_hits(app_path: Path) -> list[str]:
    hits: list[str] = []
    for path in app_path.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_RESOURCE_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in text:
                hits.append(f"{path.relative_to(app_path)} contains {marker}")
    return sorted(hits)


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str, app_path: Path) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "appPath": str(app_path),
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    app_path = Path(args.app).resolve()
    info_path = app_path / "Info.plist"
    privacy_path = app_path / "PrivacyInfo.xcprivacy"
    info = read_plist(info_path)
    privacy = read_plist(privacy_path)
    report = Report()

    report.add("appBundleExists", app_path.is_dir(), str(app_path))
    report.add("infoPlistPresent", bool(info), str(info_path) if info else f"missing or invalid {info_path}")

    bundle_id = str(info.get("CFBundleIdentifier", ""))
    report.add(
        "bundleIdentifierMatches",
        bundle_id == args.expected_bundle_id,
        f"CFBundleIdentifier={bundle_id or '<missing>'}",
    )

    api_url = str(info.get("XNPAPIBaseURL", "")).strip()
    report.add(
        "releaseApiBaseURLMatches",
        api_url == args.expected_api_url,
        f"XNPAPIBaseURL={api_url or '<missing>'}",
    )
    report.add(
        "releaseApiBaseURLUsesHTTPS",
        api_url.startswith("https://") and not is_placeholder_url(api_url),
        api_url or "<missing>",
    )

    query_schemes = set(info.get("LSApplicationQueriesSchemes") or [])
    missing_queries = sorted(REQUIRED_WECHAT_QUERY_SCHEMES - query_schemes)
    report.add(
        "weChatQuerySchemesPresent",
        not missing_queries,
        "missing: " + ", ".join(missing_queries) if missing_queries else "weixin and weixinULAPI present",
    )

    wechat_values = {
        "XNPWeChatAppID": str(info.get("XNPWeChatAppID", "")).strip(),
        "XNPWeChatURLScheme": str(info.get("XNPWeChatURLScheme", "")).strip(),
        "XNPWeChatUniversalLink": str(info.get("XNPWeChatUniversalLink", "")).strip(),
    }
    missing_wechat_values = [name for name, value in wechat_values.items() if not value or "$(" in value]
    wechat_app_id = wechat_values["XNPWeChatAppID"]
    wechat_scheme = wechat_values["XNPWeChatURLScheme"]
    if wechat_app_id and not is_real_wechat_app_id(wechat_app_id):
        missing_wechat_values.append("XNPWeChatAppID=real wx app id")
    universal_link = wechat_values["XNPWeChatUniversalLink"]
    if universal_link and (not universal_link.startswith("https://") or is_placeholder_url(universal_link)):
        missing_wechat_values.append("XNPWeChatUniversalLink=https")
    if wechat_scheme and not is_real_wechat_app_id(wechat_scheme):
        missing_wechat_values.append("XNPWeChatURLScheme=real wx scheme")
    if wechat_app_id and wechat_scheme and wechat_app_id != wechat_scheme:
        missing_wechat_values.append("XNPWeChatURLScheme must equal XNPWeChatAppID")
    report.add(
        "weChatNativeConfigPresent",
        not missing_wechat_values,
        "missing or invalid: " + ", ".join(missing_wechat_values) if missing_wechat_values else "WeChat native config present in built app",
    )
    report.add(
        "weChatURLTypePresent",
        bundle_url_types_include_wechat(info),
        "CFBundleURLTypes includes a non-placeholder wx scheme" if bundle_url_types_include_wechat(info) else "missing non-placeholder wx URL scheme in CFBundleURLTypes",
    )

    debug_found, debug_evidence = app_binary_contains(app_path, info, b"debug_wechat_ios")
    report.add("debugWeChatCodeAbsent", not debug_found, debug_evidence)

    internal_docs = disallowed_bundle_files(app_path)
    report.add(
        "releaseBundleInternalDocsAbsent",
        not internal_docs,
        "found: " + ", ".join(internal_docs) if internal_docs else "no README/Markdown/HTML/env files found in app bundle",
    )
    text_marker_hits = text_resource_marker_hits(app_path)
    report.add(
        "releaseBundleForbiddenTextMarkersAbsent",
        not text_marker_hits,
        "found: " + "; ".join(text_marker_hits) if text_marker_hits else "no local/debug/API-key markers found in text resources",
    )

    zh_hant_hk_dir = app_path / "zh-Hant-HK.lproj"
    report.add(
        "zhHantHKLocalizationBundled",
        (zh_hant_hk_dir / "Localizable.strings").exists() and (zh_hant_hk_dir / "InfoPlist.strings").exists(),
        str(zh_hant_hk_dir),
    )

    report.add(
        "privacyManifestBundled",
        bool(privacy),
        str(privacy_path) if privacy else f"missing or invalid {privacy_path}",
    )
    tracking_failures = privacy_tracking_failures(privacy)
    report.add(
        "privacyManifestTrackingDisabled",
        not tracking_failures,
        "; ".join(tracking_failures) if tracking_failures else "tracking disabled in bundled PrivacyInfo.xcprivacy",
    )
    missing_privacy_types = sorted(REQUIRED_PRIVACY_TYPES - collected_privacy_types(privacy))
    report.add(
        "privacyManifestCollectedTypesComplete",
        not missing_privacy_types,
        "missing: " + ", ".join(missing_privacy_types) if missing_privacy_types else "bundled privacy manifest contains required collected data types",
    )

    return report.to_dict(started_at, utc_now(), app_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--expected-api-url", default="https://api.mewpow.com/xiaonaiping")
    parser.add_argument("--expected-bundle-id", default="com.mewpow.xiaonaiping")
    parser.add_argument("--output", default="Backend/proof/ios-app-bundle.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"iOS app bundle readiness passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"iOS app bundle readiness incomplete: {output_path}")
    print(f"failed required checks: {failed}")
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
