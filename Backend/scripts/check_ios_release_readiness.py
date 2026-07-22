#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
import os
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
REQUIRED_PRIVACY_KEYS = {
    "NSCameraUsageDescription": "camera/photo capture",
    "NSPhotoLibraryUsageDescription": "photo import",
}

PRIVACY_LABEL_TO_MANIFEST_TYPES = {
    "Identifiers": {"NSPrivacyCollectedDataTypeUserID"},
    "Contact Info": {"NSPrivacyCollectedDataTypePhoneNumber"},
    "User Content": {"NSPrivacyCollectedDataTypeOtherUserContent"},
    "Photos or Videos": {"NSPrivacyCollectedDataTypePhotosorVideos"},
    "Health and Fitness": {"NSPrivacyCollectedDataTypeHealth"},
    "Usage Data": {"NSPrivacyCollectedDataTypeProductInteraction"},
    "Diagnostics": {"NSPrivacyCollectedDataTypeCrashData", "NSPrivacyCollectedDataTypePerformanceData"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_plist(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            data = plistlib.load(file)
    except (FileNotFoundError, plistlib.InvalidFileException, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def clean_build_value(value: str) -> str:
    return value.strip().strip('"').strip("'")


def resolve_build_value(value: str) -> str:
    value = clean_build_value(value)
    if value.startswith("$(") and value.endswith(")"):
        env_key = value[2:-1]
        return os.environ.get(env_key, "").strip()
    return value


def is_placeholder_url(value: str) -> bool:
    lower = value.lower()
    return any(host in lower for host in PLACEHOLDER_HOSTS)


def parse_release_build_settings(project_yml: Path) -> dict[str, str]:
    text = read_text(project_yml)
    settings: dict[str, str] = {}
    in_release = False
    release_indent = 0

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if re.fullmatch(r"Release:\s*", stripped):
            in_release = True
            release_indent = indent
            continue
        if in_release and indent <= release_indent:
            break
        if not in_release:
            continue
        match = re.match(r"([A-Za-z0-9_]+):\s*(.*)$", stripped)
        if match:
            settings[match.group(1)] = clean_build_value(match.group(2))
    return settings


def release_target_build_settings(pbxproj: Path) -> dict[str, str]:
    text = read_text(pbxproj)
    candidates: list[dict[str, str]] = []
    for marker in re.finditer(r"\n\t\t[A-F0-9]+ /\* Release \*/ = \{", text):
        block_end = text.find("\n\t\t};", marker.start())
        if block_end < 0:
            continue
        block = text[marker.start():block_end]
        if "PRODUCT_BUNDLE_IDENTIFIER" not in block:
            continue
        settings: dict[str, str] = {}
        for match in re.finditer(r"\n\t\t\t\t([A-Za-z0-9_]+)\s*=\s*([^;]+);", block):
            settings[match.group(1)] = clean_build_value(match.group(2))
        if settings.get("PRODUCT_BUNDLE_IDENTIFIER") == "com.mewpow.xiaonaiping":
            return settings
        if settings.get("INFOPLIST_FILE") == "XiaoNaiPing/Info.plist":
            return settings
        candidates.append(settings)
    return candidates[0] if candidates else {}


def nonempty(value: str) -> bool:
    value = value.strip()
    return bool(value) and "$(" not in value


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


def url_types_include_wechat(plist: dict[str, Any]) -> bool:
    url_types = plist.get("CFBundleURLTypes")
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


def url_types_include_wechat_build_setting(plist: dict[str, Any]) -> bool:
    url_types = plist.get("CFBundleURLTypes")
    if not isinstance(url_types, list):
        return False
    for item in url_types:
        if not isinstance(item, dict):
            continue
        schemes = item.get("CFBundleURLSchemes")
        if not isinstance(schemes, list):
            continue
        for scheme in schemes:
            if scheme == "$(XNP_WECHAT_URL_SCHEME)" or (isinstance(scheme, str) and scheme.startswith("wx")):
                return True
    return False


def swift_markers_only_inside_debug(path: Path, markers: list[str]) -> tuple[bool, str]:
    text = read_text(path)
    if not text:
        return False, f"missing {path}"

    debug_stack: list[bool] = []
    failures: list[str] = []
    seen: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#if DEBUG"):
            debug_stack.append(True)
        elif stripped.startswith("#else") and debug_stack:
            debug_stack[-1] = False
        elif stripped.startswith("#endif") and debug_stack:
            debug_stack.pop()

        for marker in markers:
            if marker in line:
                seen.append(f"{marker}@{line_number}")
                if not any(debug_stack):
                    failures.append(f"{marker}@{line_number}")

    if failures:
        return False, "markers outside DEBUG: " + ", ".join(failures)
    if not seen:
        return False, "expected debug markers not found"
    return True, "debug markers guarded: " + ", ".join(seen)


def privacy_manifest_collected_types(manifest: dict[str, Any]) -> set[str]:
    entries = manifest.get("NSPrivacyCollectedDataTypes")
    if not isinstance(entries, list):
        return set()
    collected: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        value = entry.get("NSPrivacyCollectedDataType")
        if isinstance(value, str):
            collected.add(value)
    return collected


def privacy_manifest_tracking_failures(manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if manifest.get("NSPrivacyTracking") is not False:
        failures.append("NSPrivacyTracking must be false")
    tracking_domains = manifest.get("NSPrivacyTrackingDomains")
    if not isinstance(tracking_domains, list) or tracking_domains:
        failures.append("NSPrivacyTrackingDomains must be an empty array")
    entries = manifest.get("NSPrivacyCollectedDataTypes")
    if not isinstance(entries, list):
        failures.append("NSPrivacyCollectedDataTypes must be an array")
        return failures
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("collected data entry is not a dictionary")
            continue
        data_type = str(entry.get("NSPrivacyCollectedDataType", "<missing>"))
        if entry.get("NSPrivacyCollectedDataTypeTracking") is not False:
            failures.append(f"{data_type} tracking must be false")
        purposes = entry.get("NSPrivacyCollectedDataTypePurposes")
        if not isinstance(purposes, list) or not purposes:
            failures.append(f"{data_type} purposes are missing")
    return failures


def privacy_label_required_manifest_types(label: dict[str, Any]) -> set[str]:
    required: set[str] = set()
    categories = label.get("dataCategories")
    if not isinstance(categories, list):
        return required
    for category in categories:
        if not isinstance(category, dict) or category.get("collected") is not True:
            continue
        name = category.get("category")
        if isinstance(name, str):
            required.update(PRIVACY_LABEL_TO_MANIFEST_TYPES.get(name, set()))
    return required


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


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    report = Report()

    project_yml = root / "App/iOS/project.yml"
    pbxproj = root / "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj"
    info_plist = root / "App/iOS/XiaoNaiPing/Info.plist"
    profile_view = root / "App/iOS/XiaoNaiPing/Views/ProfileView.swift"
    sync_controller = root / "App/iOS/XiaoNaiPing/Services/CloudSyncController.swift"
    sync_client = root / "App/iOS/XiaoNaiPing/Services/CloudSyncAPIClient.swift"
    wechat_service = root / "App/iOS/XiaoNaiPing/Services/WeChatLoginService.swift"
    privacy_manifest = root / "App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy"
    privacy_label = root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json"

    release_yml_settings = parse_release_build_settings(project_yml)
    release_pbx_settings = release_target_build_settings(pbxproj)
    plist = read_plist(info_plist)
    privacy_manifest_data = read_plist(privacy_manifest)
    privacy_label_data = read_json(privacy_label)
    pbx_text = read_text(pbxproj)
    client_text = read_text(sync_client)
    controller_text = read_text(sync_controller)
    profile_text = read_text(profile_view)
    wechat_service_text = read_text(wechat_service)
    wechat_shim_text = read_text(root / "App/iOS/XiaoNaiPing/Services/WechatOpenSDKShim.swift")
    project_yml_text = read_text(project_yml)

    release_url = resolve_build_value(release_yml_settings.get("XNP_API_BASE_URL", ""))
    report.add(
        "releaseApiBaseURLConfigured",
        release_url.startswith("https://") and not is_placeholder_url(release_url),
        f"XNP_API_BASE_URL={release_url or '<empty>'}",
    )
    report.add(
        "infoPlistUsesReleaseAPIBuildSetting",
        plist.get("XNPAPIBaseURL") == "$(XNP_API_BASE_URL)",
        f"XNPAPIBaseURL={plist.get('XNPAPIBaseURL', '<missing>')}",
    )

    bundle_id = release_pbx_settings.get("PRODUCT_BUNDLE_IDENTIFIER", "")
    development_team = release_pbx_settings.get("DEVELOPMENT_TEAM", "")
    report.add(
        "bundleIdentifierConfigured",
        bundle_id == "com.mewpow.xiaonaiping",
        f"PRODUCT_BUNDLE_IDENTIFIER={bundle_id or '<empty>'}",
    )
    report.add(
        "developerTeamConfigured",
        bool(development_team),
        f"DEVELOPMENT_TEAM={development_team or '<empty>'}",
    )

    zh_hant_hk_files = [
        root / "App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/Localizable.strings",
        root / "App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/InfoPlist.strings",
    ]
    missing_localization = [str(path.relative_to(root)) for path in zh_hant_hk_files if not path.exists()]
    report.add(
        "zhHantHKResourcesPresent",
        not missing_localization,
        "missing: " + ", ".join(missing_localization) if missing_localization else "zh-Hant-HK strings and InfoPlist strings exist",
    )
    report.add(
        "zhHantHKKnownRegionConfigured",
        '"zh-Hant-HK"' in pbx_text,
        "project knownRegions includes zh-Hant-HK" if '"zh-Hant-HK"' in pbx_text else "project knownRegions missing zh-Hant-HK",
    )

    missing_privacy = [
        key for key in REQUIRED_PRIVACY_KEYS
        if not isinstance(plist.get(key), str) or not plist.get(key, "").strip()
    ]
    report.add(
        "privacyUsageDescriptionsPresent",
        not missing_privacy,
        "missing: " + ", ".join(missing_privacy) if missing_privacy else "camera and photo usage descriptions exist",
    )

    report.add(
        "privacyManifestPresent",
        bool(privacy_manifest_data),
        "App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy is valid plist" if privacy_manifest_data else "missing or invalid PrivacyInfo.xcprivacy",
    )
    report.add(
        "privacyManifestIncludedInResources",
        "PrivacyInfo.xcprivacy in Resources" in pbx_text and "PrivacyInfo.xcprivacy" in project_yml_text,
        "PrivacyInfo.xcprivacy is listed in project.yml and Xcode Resources"
        if "PrivacyInfo.xcprivacy in Resources" in pbx_text and "PrivacyInfo.xcprivacy" in project_yml_text
        else "PrivacyInfo.xcprivacy is not included in both project.yml and Xcode Resources",
    )
    accessed_api_types = privacy_manifest_data.get("NSPrivacyAccessedAPITypes")
    report.add(
        "privacyManifestAccessedAPITypesDeclared",
        isinstance(accessed_api_types, list),
        "NSPrivacyAccessedAPITypes is declared as an array"
        if isinstance(accessed_api_types, list)
        else "NSPrivacyAccessedAPITypes is missing or not an array",
    )
    tracking_failures = privacy_manifest_tracking_failures(privacy_manifest_data)
    report.add(
        "privacyManifestTrackingDisabled",
        not tracking_failures,
        "; ".join(tracking_failures) if tracking_failures else "tracking disabled in manifest and all collected data entries",
    )
    collected_types = privacy_manifest_collected_types(privacy_manifest_data)
    required_types = privacy_label_required_manifest_types(privacy_label_data)
    missing_manifest_types = sorted(required_types - collected_types)
    extra_manifest_types = sorted(collected_types - required_types)
    privacy_alignment_failures = []
    if missing_manifest_types:
        privacy_alignment_failures.append("missing manifest data types: " + ", ".join(missing_manifest_types))
    if extra_manifest_types:
        privacy_alignment_failures.append("manifest data types missing from privacy label: " + ", ".join(extra_manifest_types))
    report.add(
        "privacyManifestMatchesPrivacyLabel",
        not privacy_alignment_failures and bool(required_types),
        "; ".join(privacy_alignment_failures)
        if privacy_alignment_failures
        else "manifest collected data types match App Store privacy label categories"
        if required_types
        else "privacy label categories missing or unreadable",
    )

    wechat_build_values = {
        key: resolve_build_value(release_yml_settings.get(key, ""))
        for key in ["XNP_WECHAT_APP_ID", "XNP_WECHAT_URL_SCHEME", "XNP_WECHAT_UNIVERSAL_LINK"]
    }
    wechat_build_missing = [key for key, value in wechat_build_values.items() if not nonempty(value)]
    wechat_app_id = wechat_build_values["XNP_WECHAT_APP_ID"]
    wechat_scheme = wechat_build_values["XNP_WECHAT_URL_SCHEME"]
    if wechat_app_id and not is_real_wechat_app_id(wechat_app_id):
        wechat_build_missing.append("XNP_WECHAT_APP_ID=real wx app id")
    universal_link = wechat_build_values["XNP_WECHAT_UNIVERSAL_LINK"]
    if universal_link and (not universal_link.startswith("https://") or is_placeholder_url(universal_link)):
        wechat_build_missing.append("XNP_WECHAT_UNIVERSAL_LINK=https")
    if wechat_scheme and not is_real_wechat_app_id(wechat_scheme):
        wechat_build_missing.append("XNP_WECHAT_URL_SCHEME=real wx scheme")
    if wechat_app_id and wechat_scheme and wechat_app_id != wechat_scheme:
        wechat_build_missing.append("XNP_WECHAT_URL_SCHEME must equal XNP_WECHAT_APP_ID")
    report.add(
        "weChatReleaseBuildSettingsConfigured",
        not wechat_build_missing,
        "missing or invalid: " + ", ".join(wechat_build_missing) if wechat_build_missing else "WeChat release build settings are configured",
    )

    plist_wechat_keys = {
        "XNPWeChatAppID": "$(XNP_WECHAT_APP_ID)",
        "XNPWeChatURLScheme": "$(XNP_WECHAT_URL_SCHEME)",
        "XNPWeChatUniversalLink": "$(XNP_WECHAT_UNIVERSAL_LINK)",
    }
    bad_plist_keys = [
        key for key, expected in plist_wechat_keys.items()
        if plist.get(key) != expected
    ]
    report.add(
        "weChatInfoPlistBuildSettingsPresent",
        not bad_plist_keys,
        "missing or wrong: " + ", ".join(bad_plist_keys) if bad_plist_keys else "WeChat Info.plist build settings are present",
    )

    query_schemes = set(plist.get("LSApplicationQueriesSchemes") or [])
    missing_queries = sorted(REQUIRED_WECHAT_QUERY_SCHEMES - query_schemes)
    report.add(
        "weChatQuerySchemesConfigured",
        not missing_queries,
        "missing: " + ", ".join(missing_queries) if missing_queries else "LSApplicationQueriesSchemes includes weixin and weixinULAPI",
    )
    report.add(
        "weChatURLTypeConfigured",
        url_types_include_wechat_build_setting(plist),
        "CFBundleURLTypes is wired to XNP_WECHAT_URL_SCHEME"
        if url_types_include_wechat_build_setting(plist) and not url_types_include_wechat(plist)
        else "CFBundleURLTypes contains non-placeholder wx scheme"
        if url_types_include_wechat(plist)
        else "missing WeChat URL scheme or XNP_WECHAT_URL_SCHEME build setting in CFBundleURLTypes",
    )
    report.add(
        "weChatOpenSDKLinked",
        "WechatOpenSDK" in pbx_text
        or "WXApi" in pbx_text
        or "WXApi" in wechat_service_text
        or "WXApi" in wechat_shim_text,
        "Xcode project or source references WechatOpenSDK/WXApi"
        if "WechatOpenSDK" in pbx_text
        or "WXApi" in pbx_text
        or "WXApi" in wechat_service_text
        or "WXApi" in wechat_shim_text
        else "project and sources do not reference WechatOpenSDK/WXApi",
    )
    report.add(
        "weChatRuntimeRequiresOpenSDK",
        ("#if canImport(WechatOpenSDK)" in wechat_service_text
         and "#if !canImport(WechatOpenSDK)" in wechat_service_text)
        or "#if canImport(WechatOpenSDK)" in wechat_service_text,
        "WeChat service accepts native SDK or local fallback shim path",
    )
    wechat_bridge_markers = {
        "WXApi.registerApp": wechat_service_text,
        "SendAuthReq": wechat_service_text,
        "WXApi.handleOpen": wechat_service_text,
        "WXApi.handleOpenUniversalLink": wechat_service_text,
        "client.loginWithWeChat(code: code)": controller_text,
    }
    missing_bridge_markers = [
        marker for marker, text in wechat_bridge_markers.items()
        if marker not in text
    ]
    report.add(
        "weChatAuthorizationBridgePresent",
        not missing_bridge_markers,
        "missing: " + ", ".join(missing_bridge_markers)
        if missing_bridge_markers
        else "WeChat service registers OpenSDK, sends auth request, handles URL callbacks, and exchanges returned code with backend",
    )
    debug_guarded, debug_evidence = swift_markers_only_inside_debug(sync_controller, ["debug_wechat_ios"])
    if debug_evidence == "expected debug markers not found":
        debug_guarded = True
        debug_evidence = "debug_wechat_ios is absent from source"
    report.add("releaseWeChatDebugCodeBlocked", debug_guarded, debug_evidence)
    report.add(
        "releaseWeChatButtonGated",
        "!cloudSync.isWeChatLoginConfigured" in profile_text,
        "Profile WeChat button is disabled until native WeChat config is present",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output", default="Backend/proof/ios-release-readiness.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"iOS release readiness passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"iOS release readiness incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
