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
PBXPROJ = "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj"
INFO_PLIST = "App/iOS/XiaoNaiPing/Info.plist"
ENTITLEMENTS = "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements"
APP_ENTRY = "App/iOS/XiaoNaiPing/XiaoNaiPingApp.swift"
WECHAT_SERVICE = "App/iOS/XiaoNaiPing/Services/WeChatLoginService.swift"
AASA = "Backend/static/apple-app-site-association"
DOC_MARKERS = (
    "日期：2026-06-30",
    "wx + 16 hex",
    "XNP_WECHAT_APP_ID",
    "XNP_WECHAT_URL_SCHEME",
    "XNP_WECHAT_UNIVERSAL_LINK",
    "XNP_WECHAT_APP_SECRET",
    "服务端",
    "不能写进 iOS 工程",
    "08-wechat-open-platform",
    "## 微信开放平台后台字段清单",
    "移动应用名称",
    "小奶瓶",
    "iOS Bundle ID",
    "com.mewpow.xiaonaiping",
    "URL Scheme",
    "equal to AppID",
    "Universal Link",
    "https://api.mewpow.com/xiaonaiping/wechat/",
    "AppSecret",
    "只写入服务端私有 env",
    "必须遮挡",
    "审核/配置状态",
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
    "check_wechat_client_configuration.py",
    "verify_auth_providers.py",
    "check_launch_objective_audit.py",
)
CURRENT_WECHAT_PROOF_MARKERS = (
    "wechat-release-env-validation-20260630T-current.json",
    "ios-release-readiness-20260630T-current-ios265.json",
    "ios-app-bundle-20260630T-current-ios265.json",
    "wechat-client-configuration-20260630T-current.json",
    "huawei-baota-deploy-20260630T-current.json",
    "auth-providers-20260630T-current.json",
    "--allow-incomplete",
    "同步稳定 alias",
    "`ios-release-readiness.json`",
    "`ios-app-bundle.json`",
    "`wechat-client-configuration.json`",
    "`auth-providers.json`",
    "不要把旧部署 proof 或旧 auth provider proof 当成真实微信配置完成证据",
)
CLIENT_PRECONFIGURATION_MATRIX_MARKERS = (
    "## 客户端配置预注入矩阵",
    "能先做",
    "必须等外部真值",
    "`XNP_WECHAT_APP_ID`",
    "`XNP_WECHAT_URL_SCHEME`",
    "`XNP_WECHAT_UNIVERSAL_LINK`",
    "`XNP_ASSOCIATED_DOMAIN`",
    "`XNP_WECHAT_APP_SECRET`",
    "`Backend/static/apple-app-site-association`",
    "`App/iOS/project.yml`",
    "`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`",
    "`App/iOS/XiaoNaiPing/Info.plist`",
    "`App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements`",
    "真实 AppID",
    "URL Scheme equal to AppID",
    "Apple Developer Team ID",
    "AppSecret 只进服务端私有 env",
    "check_ios_release_readiness.py",
    "check_ios_app_bundle.py",
    "verify_auth_providers.py",
    "不能为了过 gate 写入假的 `wxclientdryrun...`",
)
VALUE_PROPAGATION_MATRIX_MARKERS = (
    "## 真实值传播核对矩阵",
    "同一个微信开放平台移动应用",
    "同一个 Apple Developer 组织 Team",
    "真实微信 AppID",
    "微信开放平台移动应用，格式 `wx + 16 hex`",
    "`XNP_WECHAT_APP_ID`",
    "`XNP_WECHAT_URL_SCHEME`",
    "`XNPWeChatAppID`",
    "`XNPWeChatURLScheme`",
    "`CFBundleURLTypes`",
    "`wechat-release-env-validation-20260630T-current.json`",
    "`ios-app-bundle-20260630T-current-ios265.json`",
    "URL Scheme",
    "与 AppID 不一致的 scheme",
    "Universal Link",
    "`08b-wechat-universal-link-aasa.png`",
    "`universal-links-20260630T-current.json`",
    "Apple Developer Team ID",
    "旧 Team ID 当作新组织 proof",
    "AppSecret",
    "仅服务器私有 env `XNP_WECHAT_APP_SECRET`",
    "写入 iOS 工程、Info.plist、截图、JSON、仓库文档或命令行历史",
    "真机微信登录",
    "RD-14 微信登录录屏",
    "模拟器、iOS 27、debug code 或未签名包",
)
STALE_WECHAT_PROOF_MARKERS = (
    "huawei-baota-deploy-20260625T080412Z.json",
    "huawei-baota-deploy-20260628T-current.json",
    "--output Backend/proof/auth-providers.json",
    "--output Backend/proof/ios-app-bundle.json",
    "--output Backend/proof/ios-release-readiness.json",
    "--output Backend/proof/wechat-client-configuration.json",
)

PROJECT_MARKERS = (
    "WechatOpenSDK:",
    "product: WechatOpenSDK",
    "WebKit.framework",
    "XNP_WECHAT_APP_ID: \"wxe919f9e41822223c\"",
    "XNP_WECHAT_URL_SCHEME: \"wxe919f9e41822223c\"",
    "XNP_WECHAT_UNIVERSAL_LINK: \"https://api.mewpow.com/xiaonaiping/wechat/\"",
    "XNP_ASSOCIATED_DOMAIN: \"applinks:api.mewpow.com\"",
)

PBXPROJ_MARKERS = (
    "WechatOpenSDK in Frameworks",
    "WebKit.framework in Frameworks",
    "PRODUCT_BUNDLE_IDENTIFIER = com.mewpow.xiaonaiping;",
    "CODE_SIGN_ENTITLEMENTS = XiaoNaiPing/XiaoNaiPing.entitlements;",
    "XNP_WECHAT_APP_ID = wxe919f9e41822223c;",
    "XNP_WECHAT_URL_SCHEME = wxe919f9e41822223c;",
    "XNP_WECHAT_UNIVERSAL_LINK = \"https://api.mewpow.com/xiaonaiping/wechat/\";",
    "XNP_ASSOCIATED_DOMAIN = \"applinks:api.mewpow.com\";",
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

APP_ENTRY_MARKERS = (
    ".onOpenURL",
    "WeChatLoginService.shared.handleOpenURL",
    ".onContinueUserActivity(NSUserActivityTypeBrowsingWeb)",
    "WeChatLoginService.shared.handleUniversalLink",
)

WECHAT_SERVICE_MARKERS = (
    "import WechatOpenSDK",
    "WXApi.registerApp(appID, universalLink: universalLink.absoluteString)",
    "request.scope = \"snsapi_userinfo\"",
    "WXApi.send(request)",
    "WXApi.handleOpen(url, delegate: self)",
    "WXApi.handleOpenUniversalLink(userActivity, delegate: self)",
    "response.state == expectedState",
    "response.code",
)

AASA_MARKERS = (
    "\"appID\": \"L2TYJNDTJK.com.mewpow.xiaonaiping\"",
    "\"/wechat/*\"",
    "\"/xiaonaiping/wechat/*\"",
    "\"appIDs\"",
    "\"components\"",
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
    pbxproj_path = root / args.pbxproj
    plist_path = root / args.info_plist
    entitlements_path = root / args.entitlements
    app_entry_path = root / args.app_entry
    wechat_service_path = root / args.wechat_service
    aasa_path = root / args.aasa

    doc = read_text(doc_path)
    project = read_text(project_path)
    pbxproj = read_text(pbxproj_path)
    plist = read_text(plist_path)
    entitlements = read_text(entitlements_path)
    app_entry = read_text(app_entry_path)
    wechat_service = read_text(wechat_service_path)
    aasa = read_text(aasa_path)
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
    current_wechat_proof_ok, missing_current_wechat_proof_markers = contains_all(doc, CURRENT_WECHAT_PROOF_MARKERS)
    stale_wechat_proof_markers = [marker for marker in STALE_WECHAT_PROOF_MARKERS if marker in doc]
    proof_details: dict[str, Any] = {}
    if missing_current_wechat_proof_markers:
        proof_details["missingMarkers"] = missing_current_wechat_proof_markers
    if stale_wechat_proof_markers:
        proof_details["staleMarkers"] = stale_wechat_proof_markers
    report.add(
        "wechatValidationUsesCurrentProofChain",
        current_wechat_proof_ok and not stale_wechat_proof_markers,
        "document regenerates WeChat validation, iOS release readiness, app bundle, WeChat client configuration, and auth provider proof as 20260630T-current before syncing stable aliases",
        proof_details if proof_details else None,
    )

    preconfig_ok, missing_preconfig_markers = contains_all(doc, CLIENT_PRECONFIGURATION_MATRIX_MARKERS)
    report.add(
        "clientPreconfigurationMatrixPresent",
        preconfig_ok,
        "document separates local client slots that can be prepared from external WeChat/Apple values that must not be faked",
        {"missingMarkers": missing_preconfig_markers} if missing_preconfig_markers else None,
    )

    value_matrix_ok, missing_value_matrix_markers = contains_all(doc, VALUE_PROPAGATION_MATRIX_MARKERS)
    report.add(
        "wechatValuePropagationMatrixPresent",
        value_matrix_ok,
        "document maps the same real WeChat AppID, URL Scheme, Universal Link, Team ID, server-only AppSecret, and iOS 26.5 signed-device login proof across all required destinations",
        {"missingMarkers": missing_value_matrix_markers} if missing_value_matrix_markers else None,
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

    pbxproj_ok, missing_pbxproj_markers = contains_all(pbxproj, PBXPROJ_MARKERS)
    report.add(
        "xcodeProjectReleaseBuildSettingsWired",
        pbxproj_ok,
        "Xcode project Release target wires Bundle ID, entitlements, WeChat build settings, and Associated Domain",
        {"missingMarkers": missing_pbxproj_markers} if missing_pbxproj_markers else None,
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

    app_entry_ok, missing_app_entry_markers = contains_all(app_entry, APP_ENTRY_MARKERS)
    report.add(
        "appEntryHandlesWeChatCallbacks",
        app_entry_ok,
        "SwiftUI app entry routes URL scheme and Universal Link callbacks to WeChatLoginService",
        {"missingMarkers": missing_app_entry_markers} if missing_app_entry_markers else None,
    )

    wechat_service_ok, missing_wechat_service_markers = contains_all(wechat_service, WECHAT_SERVICE_MARKERS)
    report.add(
        "wechatServiceUsesNativeSdkAuthFlow",
        wechat_service_ok,
        "WeChat login service registers the native SDK, sends snsapi_userinfo auth request, handles callbacks, and validates state/code",
        {"missingMarkers": missing_wechat_service_markers} if missing_wechat_service_markers else None,
    )

    aasa_ok, missing_aasa_markers = contains_all(aasa, AASA_MARKERS)
    report.add(
        "aasaCoversWeChatUniversalLinkPaths",
        aasa_ok,
        "AASA covers the current Team ID / Bundle ID and both dedicated and transitional WeChat callback paths",
        {"missingMarkers": missing_aasa_markers} if missing_aasa_markers else None,
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--doc", default=DOC_PATH)
    parser.add_argument("--project-yml", default=PROJECT_YML)
    parser.add_argument("--pbxproj", default=PBXPROJ)
    parser.add_argument("--info-plist", default=INFO_PLIST)
    parser.add_argument("--entitlements", default=ENTITLEMENTS)
    parser.add_argument("--app-entry", default=APP_ENTRY)
    parser.add_argument("--wechat-service", default=WECHAT_SERVICE)
    parser.add_argument("--aasa", default=AASA)
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
