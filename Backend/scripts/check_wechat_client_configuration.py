#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DOC_PATH = "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md"
PROJECT_YML = "App/iOS/project.yml"
INFO_PLIST = "App/iOS/XiaoNaiPing/Info.plist"
ENTITLEMENTS = "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements"

DOC_MARKERS = (
    "wx + 16 hex",
    "XNP_WECHAT_APP_ID",
    "XNP_WECHAT_URL_SCHEME",
    "XNP_WECHAT_UNIVERSAL_LINK",
    "XNP_WECHAT_APP_SECRET",
    "服务端",
    "不能写进 iOS 工程",
    "08-wechat-open-platform",
)

IOS_265_COMMAND_MARKERS = (
    "本机验证只使用 iOS 26.5",
    "-sdk iphonesimulator26.5",
    "-sdk iphoneos26.5",
    "iOS 27.0 不能作为",
)

VALIDATION_COMMAND_MARKERS = (
    "prepare_wechat_release_env.py",
    "check_ios_release_readiness.py",
    "check_ios_app_bundle.py",
    "verify_auth_providers.py",
    "check_launch_objective_audit.py",
)

PROJECT_MARKERS = (
    "XNP_WECHAT_APP_ID: \"$(XNP_WECHAT_APP_ID)\"",
    "XNP_WECHAT_URL_SCHEME: \"$(XNP_WECHAT_URL_SCHEME)\"",
    "XNP_WECHAT_UNIVERSAL_LINK: \"https://api.mewpow.com/xiaonaiping/wechat/\"",
    "XNP_ASSOCIATED_DOMAIN: \"applinks:api.mewpow.com\"",
)

PLIST_MARKERS = (
    "<key>XNPWeChatAppID</key>",
    "<string>$(XNP_WECHAT_APP_ID)</string>",
    "<key>XNPWeChatURLScheme</key>",
    "<string>$(XNP_WECHAT_URL_SCHEME)</string>",
    "<key>XNPWeChatUniversalLink</key>",
    "<string>$(XNP_WECHAT_UNIVERSAL_LINK)</string>",
    "<key>CFBundleURLTypes</key>",
    "<string>weixin</string>",
    "<string>weixinULAPI</string>",
)

ENTITLEMENTS_MARKERS = (
    "<key>com.apple.developer.associated-domains</key>",
    "<string>$(XNP_ASSOCIATED_DOMAIN)</string>",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, list[str]]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, missing


def has_placeholder_secret_assignment(text: str) -> bool:
    return bool(re.search(r"XNP_WECHAT_APP_SECRET\s*=", text))


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, details: dict[str, Any] | None = None) -> None:
        check: dict[str, Any] = {
            "passed": passed,
            "required": True,
            "evidence": evidence,
        }
        if details:
            check.update(details)
        self.checks[name] = check

    def to_dict(self, started_at: str, completed_at: str) -> dict[str, Any]:
        failed = [name for name, check in self.checks.items() if check["passed"] is not True]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "passed": not failed,
            "failedRequiredChecks": failed,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    doc_path = root / args.doc
    project_path = root / args.project_yml
    plist_path = root / args.info_plist
    entitlements_path = root / args.entitlements

    doc = read_text(doc_path)
    project = read_text(project_path)
    plist = read_text(plist_path)
    entitlements = read_text(entitlements_path)
    report = Report()

    report.add("handoffDocumentPresent", bool(doc), str(doc_path) if doc else "missing WeChat client configuration document")

    doc_ok, missing_doc_markers = contains_all(doc, DOC_MARKERS)
    report.add(
        "handoffDocumentCoversRequiredValues",
        doc_ok,
        "document covers AppID, URL Scheme, Universal Link, server AppSecret, and evidence path",
        {"missingMarkers": missing_doc_markers} if missing_doc_markers else None,
    )

    ios_ok, missing_ios_markers = contains_all(doc, IOS_265_COMMAND_MARKERS)
    report.add(
        "ios265ValidationCommandsPresent",
        ios_ok,
        "document constrains local validation commands to iOS 26.5",
        {"missingMarkers": missing_ios_markers} if missing_ios_markers else None,
    )

    command_ok, missing_command_markers = contains_all(doc, VALIDATION_COMMAND_MARKERS)
    report.add(
        "proofRegenerationCommandsPresent",
        command_ok,
        "document lists focused proof regeneration commands",
        {"missingMarkers": missing_command_markers} if missing_command_markers else None,
    )

    report.add(
        "docDoesNotAssignAppSecret",
        not has_placeholder_secret_assignment(doc),
        "document explains AppSecret is server-only and does not show shell assignment",
    )

    project_ok, missing_project_markers = contains_all(project, PROJECT_MARKERS)
    report.add(
        "projectBuildSettingsWired",
        project_ok,
        "project.yml wires Release WeChat build settings and Associated Domain",
        {"missingMarkers": missing_project_markers} if missing_project_markers else None,
    )

    plist_ok, missing_plist_markers = contains_all(plist, PLIST_MARKERS)
    report.add(
        "infoPlistSlotsWired",
        plist_ok,
        "Info.plist wires WeChat keys, URL type, and query schemes",
        {"missingMarkers": missing_plist_markers} if missing_plist_markers else None,
    )

    entitlements_ok, missing_entitlements_markers = contains_all(entitlements, ENTITLEMENTS_MARKERS)
    report.add(
        "associatedDomainsEntitlementWired",
        entitlements_ok,
        "Release entitlements wire Associated Domains to XNP_ASSOCIATED_DOMAIN",
        {"missingMarkers": missing_entitlements_markers} if missing_entitlements_markers else None,
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--doc", default=DOC_PATH)
    parser.add_argument("--project-yml", default=PROJECT_YML)
    parser.add_argument("--info-plist", default=INFO_PLIST)
    parser.add_argument("--entitlements", default=ENTITLEMENTS)
    parser.add_argument("--output", default="Backend/proof/wechat-client-configuration.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"WeChat client configuration passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"WeChat client configuration incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
