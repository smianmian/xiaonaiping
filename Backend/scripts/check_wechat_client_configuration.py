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
WECHAT_RELEASE_PACKET = "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json"

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
WECHAT_RELEASE_PACKET_DOC_MARKERS = (
    "## 真实微信 Release 配置执行包",
    "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json",
    "不是证据",
    "不是 AppSecret 容器",
    "不能作为提交许可",
    "真实 `wx + 16 hex` AppID",
    "URL Scheme equal to AppID",
    "Apple Developer Team ID",
    "prepare_wechat_release_env.py",
    "iOS 26.5",
    "ios-release-readiness-20260630T-current-ios265.json",
    "ios-app-bundle-20260630T-current-ios265.json",
    "wechat-client-configuration-20260630T-current.json",
    "auth-providers-20260630T-current.json",
    "RD-14 iOS 26.5 TestFlight / 签名真机微信登录",
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
WECHAT_RELEASE_PACKET_MARKERS = (
    "wechat-release-configuration-packet",
    "release-configuration-packet-not-evidence",
    "2026-06-30",
    "XiaoNaiPing",
    "小奶瓶",
    "com.mewpow.xiaonaiping",
    "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md",
    "Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
    "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "Backend/static/apple-app-site-association",
    "realWechatAppId",
    "wx + 16 lowercase hex characters",
    "XNP_WECHAT_APP_ID",
    "XNP_WECHAT_URL_SCHEME",
    "CFBundleURLTypes",
    "08-wechat-open-platform.png",
    "wxclientdryrun123456",
    "debug",
    "placeholder",
    "wechatAppSecret",
    "server private env only",
    "mustNotAppearIn",
    "iOS project",
    "screenshots",
    "JSON evidence",
    "appleDeveloperTeamId",
    "ExportOptions teamID",
    "AASA appID/appIDs prefix",
    "08b-wechat-universal-link-aasa.png",
    "wechatUniversalLink",
    "https://api.mewpow.com/xiaonaiping/wechat/",
    "Associated Domains applinks:api.mewpow.com",
    "valuePropagationMatrix",
    "evidenceDependencyMatrix",
    "sameRealWechatAppId",
    "sameUniversalLinkAndAasa",
    "serverOnlyAppSecret",
    "ios265SignedWechatLogin",
    "doesNotProve",
    "requiredBeforeStableAliasSync",
    "initialStatus",
    "XNPWeChatAppID",
    "XNPWeChatURLScheme",
    "targetEvidenceFiles",
    "evidenceFileChecks",
    "fileSizeBytes",
    "sha256",
    "FILL_AFTER_CAPTURE",
    "sameRoundAsWechatReleaseConfiguration",
    "sourceIsAllowedEvidenceRoot",
    "realEvidenceNotTemplate",
    "secretValuesNotRecorded",
    "AppleDeveloper/13-organization-team-id.png",
    "RD-14-wechat-login.png",
    "universal-links-20260630T-current.json",
    "RD-14 WeChat login recording",
    "backend login success",
    "WeChat console screenshot only",
    "confirmTeamId",
    "syncTeamIdIfNeeded",
    "prepareWechatReleaseEnv",
    "prepare_wechat_release_env.py",
    "wechat-release-env-validation-20260630T-current.json",
    "-sdk iphonesimulator26.5",
    "-sdk iphoneos26.5",
    "ios-release-readiness-20260630T-current-ios265.json",
    "ios-app-bundle-20260630T-current-ios265.json",
    "wechat-client-configuration-20260630T-current.json",
    "auth-providers-20260630T-current.json",
    "08-wechat-open-platform.png",
    "08b-wechat-universal-link-aasa.png",
    "syncStableAliases",
    "Release app bundle contains real wx URL Scheme and native WeChat config",
    "iOS 26.5 TestFlight or signed real-device WeChat login succeeds from WeChat back to XiaoNaiPing",
    "ios-release-readiness.json",
    "ios-app-bundle.json",
    "wechat-client-configuration.json",
    "auth-providers.json",
    "check_provider_evidence_materials.py",
    "check_app_store_evidence.py --allow-incomplete",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
    "RD-14 iOS 26.5 TestFlight or signed real-device login passes",
    "production-readiness.json plus launch-objective-audit.json are ready=true",
)
WECHAT_RELEASE_PACKET_SCALARS = {
    "artifactType": "wechat-release-configuration-packet",
    "status": "release-configuration-packet-not-evidence",
    "date": "2026-06-30",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
    "bundleId": "com.mewpow.xiaonaiping",
}
WECHAT_RELEASE_PACKET_SOURCE_FILES = {
    "wechatClientConfiguration": "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md",
    "wechatOpenPlatformEvidenceTemplate": "Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json",
    "externalPlatformHandoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
    "appleDeveloperDunsHandoff": "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "aasa": "Backend/static/apple-app-site-association",
    "iosReleaseReadinessProof": "Backend/proof/ios-release-readiness-20260630T-current-ios265.json",
    "iosAppBundleProof": "Backend/proof/ios-app-bundle-20260630T-current-ios265.json",
    "wechatClientConfigurationProof": "Backend/proof/wechat-client-configuration-20260630T-current.json",
    "authProvidersProof": "Backend/proof/auth-providers-20260630T-current.json",
}
WECHAT_RELEASE_PACKET_TARGET_EVIDENCE_FILES = {
    "wechatOpenPlatform": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png or .pdf",
    "wechatUniversalLinkAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png or .pdf",
    "appleDeveloperTeamId": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png or .pdf",
    "wechatReleaseEnvValidationProof": "Backend/proof/wechat-release-env-validation-20260630T-current.json",
    "iosReleaseReadinessProof": "Backend/proof/ios-release-readiness-20260630T-current-ios265.json",
    "iosAppBundleProof": "Backend/proof/ios-app-bundle-20260630T-current-ios265.json",
    "wechatClientConfigurationProof": "Backend/proof/wechat-client-configuration-20260630T-current.json",
    "authProvidersProof": "Backend/proof/auth-providers-20260630T-current.json",
    "realDeviceWechatLogin": "Docs/08_Release/AppStoreEvidence/RealDevice/RD-14-wechat-login.png or .mp4",
    "realDeviceRegression": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
}
WECHAT_RELEASE_PACKET_EVIDENCE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsWechatReleaseConfiguration", False),
    ("sourceIsAllowedEvidenceRoot", False),
    ("realEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
WECHAT_RELEASE_PACKET_DEPENDENCY_MATRIX_FIELDS = (
    "artifactId",
    "target",
    "proves",
    "doesNotProve",
    "requiredBeforeStableAliasSync",
    "initialStatus",
)
WECHAT_RELEASE_PACKET_DEPENDENCY_MATRIX = (
    {
        "artifactId": "wechatOpenPlatform",
        "target": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png or .pdf",
        "proves": [
            "WeChat mobile app AppID, Bundle ID, URL Scheme, Universal Link, and approval or active configuration status",
            "AppSecret is redacted and server-only",
        ],
        "doesNotProve": [
            "Apple Developer Team ID",
            "AASA and Associated Domains alignment",
            "Release bundle contains the real wx URL Scheme",
            "server auth provider proof",
            "RD-14 iOS 26.5 WeChat login",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "wechatUniversalLinkAasa",
        "target": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png or .pdf",
        "proves": [
            "AASA endpoint, Associated Domains, Team ID, Bundle ID, and WeChat Universal Link alignment",
            "AASA Team ID matches Apple Developer organization Team ID",
        ],
        "doesNotProve": [
            "WeChat Open Platform mobile app approval",
            "server AppSecret configuration",
            "Release bundle contains the real wx URL Scheme",
            "RD-14 iOS 26.5 WeChat login",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "appleDeveloperTeamId",
        "target": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png or .pdf",
        "proves": [
            "D-U-N-S post-enrollment Apple Developer organization Team ID",
            "Team ID authority for signing, AASA appID/appIDs, and Associated Domains",
        ],
        "doesNotProve": [
            "WeChat Open Platform mobile app approval",
            "App Store Distribution certificate/profile permission",
            "Release archive or TestFlight processing",
            "RD-14 iOS 26.5 WeChat login",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "wechatReleaseEnvValidationProof",
        "target": "Backend/proof/wechat-release-env-validation-20260630T-current.json",
        "proves": [
            "real WeChat AppID format and URL Scheme equality are validated before Release build",
            "local ignored env is prepared without storing AppSecret",
        ],
        "doesNotProve": [
            "WeChat Open Platform screenshot evidence",
            "server AppSecret configured",
            "Release bundle inspection",
            "RD-14 iOS 26.5 WeChat login",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "iosReleaseReadinessProof",
        "target": "Backend/proof/ios-release-readiness-20260630T-current-ios265.json",
        "proves": [
            "iOS Release build settings include real WeChat AppID, URL Scheme, Universal Link, Associated Domains, and required frameworks",
            "proof was generated for iOS 26.5",
        ],
        "doesNotProve": [
            "exported app bundle contains the real URL Scheme",
            "server AppSecret configured",
            "RD-14 iOS 26.5 WeChat login",
            "App Store submission readiness",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "iosAppBundleProof",
        "target": "Backend/proof/ios-app-bundle-20260630T-current-ios265.json",
        "proves": [
            "Release app bundle contains real wx URL Scheme and native WeChat config",
            "Bundle ID remains com.mewpow.xiaonaiping",
        ],
        "doesNotProve": [
            "server AppSecret configured",
            "WeChat Open Platform approval",
            "TestFlight processed build",
            "RD-14 iOS 26.5 WeChat login",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "wechatClientConfigurationProof",
        "target": "Backend/proof/wechat-client-configuration-20260630T-current.json",
        "proves": [
            "client WeChat handoff, AASA shape, Universal Link, and documentation gates are current",
        ],
        "doesNotProve": [
            "real wx AppID has been injected into Release build",
            "server auth provider proof",
            "RD-14 iOS 26.5 WeChat login",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "authProvidersProof",
        "target": "Backend/proof/auth-providers-20260630T-current.json",
        "proves": [
            "production auth provider proof verifies WeChat provider configuration with secrets redacted",
            "debug code is rejected",
        ],
        "doesNotProve": [
            "iOS bundle contains the real wx URL Scheme",
            "WeChat Open Platform screenshot evidence",
            "RD-14 iOS 26.5 WeChat login",
            "App Store submission readiness",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "realDeviceWechatLogin",
        "target": "Docs/08_Release/AppStoreEvidence/RealDevice/RD-14-wechat-login.png or .mp4",
        "proves": [
            "iOS 26.5 TestFlight or signed real-device WeChat login succeeds from WeChat back to XiaoNaiPing",
            "same build uses configured WeChat Open Platform values",
        ],
        "doesNotProve": [
            "App Store Connect manual evidence",
            "production-readiness.json ready=true",
            "launch-objective-audit.json ready=true",
            "all real-device regression cases",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
    {
        "artifactId": "realDeviceRegression",
        "target": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
        "proves": [
            "RD-14 is included in the full iOS 26.5 real-device regression evidence set",
            "login, account deletion, notification permission, Live Activity, lock screen, and widgets are reviewed in the same regression round",
        ],
        "doesNotProve": [
            "WeChat Open Platform credentials by itself",
            "server AppSecret by itself",
            "production-readiness.json ready=true",
            "App Store submission readiness",
        ],
        "requiredBeforeStableAliasSync": True,
        "initialStatus": "pending",
    },
)
WECHAT_RELEASE_PACKET_REQUIRED_EXTERNAL_INPUT_IDS = (
    "realWechatAppId",
    "wechatAppSecret",
    "appleDeveloperTeamId",
    "wechatUniversalLink",
)
WECHAT_RELEASE_PACKET_VALUE_PROPAGATION_IDS = (
    "sameRealWechatAppId",
    "sameUniversalLinkAndAasa",
    "serverOnlyAppSecret",
    "ios265SignedWechatLogin",
)
WECHAT_RELEASE_PACKET_EXECUTION_STEPS = (
    "confirmTeamId",
    "syncTeamIdIfNeeded",
    "prepareWechatReleaseEnv",
    "buildReleaseSimIos265",
    "buildReleaseDeviceIos265",
    "refreshClientProofs",
    "refreshServerAuthProof",
    "captureExternalEvidence",
    "syncStableAliases",
)
WECHAT_RELEASE_PACKET_POST_GATES = (
    "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260630T-current.json",
    "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
    "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260630T-current.json",
    "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
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


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, list[str]]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, missing


def has_placeholder_secret_assignment(text: str) -> bool:
    return bool(re.search(r"XNP_WECHAT_APP_SECRET\s*=", text))


def as_searchable_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def wechat_release_packet_structure_failures(packet: dict[str, Any]) -> list[str]:
    if not packet:
        return ["WeChat release configuration packet invalid or missing"]

    failures: list[str] = []
    for key, expected in WECHAT_RELEASE_PACKET_SCALARS.items():
        if packet.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    source_files = packet.get("sourceFiles")
    if not isinstance(source_files, dict):
        failures.append("sourceFiles must be an object")
    else:
        if tuple(source_files) != tuple(WECHAT_RELEASE_PACKET_SOURCE_FILES):
            failures.append(
                "sourceFiles order must be "
                + " -> ".join(WECHAT_RELEASE_PACKET_SOURCE_FILES)
            )
        for key, expected in WECHAT_RELEASE_PACKET_SOURCE_FILES.items():
            if source_files.get(key) != expected:
                failures.append(f"sourceFiles.{key} must be {expected}")

    target_files = packet.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        failures.append("targetEvidenceFiles must be an object")
    else:
        if tuple(target_files) != tuple(WECHAT_RELEASE_PACKET_TARGET_EVIDENCE_FILES):
            failures.append(
                "targetEvidenceFiles order must be "
                + " -> ".join(WECHAT_RELEASE_PACKET_TARGET_EVIDENCE_FILES)
            )
        for key, expected in WECHAT_RELEASE_PACKET_TARGET_EVIDENCE_FILES.items():
            if target_files.get(key) != expected:
                failures.append(f"targetEvidenceFiles.{key} must be {expected}")

    evidence_checks = packet.get("evidenceFileChecks")
    if not isinstance(evidence_checks, list):
        failures.append("evidenceFileChecks must be a list")
    else:
        seen: set[str] = set()
        by_artifact: dict[str, dict[str, Any]] = {}
        for item in evidence_checks:
            if not isinstance(item, dict):
                failures.append("evidenceFileChecks entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in seen:
                failures.append(f"evidenceFileChecks duplicate {artifact_id}")
                continue
            seen.add(artifact_id)
            by_artifact[artifact_id] = item
        expected_ids = tuple(WECHAT_RELEASE_PACKET_TARGET_EVIDENCE_FILES)
        if tuple(by_artifact) != expected_ids:
            failures.append("evidenceFileChecks order must be " + " -> ".join(expected_ids))
        for artifact_id, expected_target in WECHAT_RELEASE_PACKET_TARGET_EVIDENCE_FILES.items():
            check = by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != expected_target:
                failures.append(f"evidenceFileChecks.{artifact_id}.target must be {expected_target}")
            for field, expected in WECHAT_RELEASE_PACKET_EVIDENCE_FILE_CHECK_FIELDS:
                if check.get(field) != expected:
                    failures.append(f"evidenceFileChecks.{artifact_id}.{field} must be {expected!r}")

    dependency_matrix = packet.get("evidenceDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("evidenceDependencyMatrix must be a list")
    else:
        seen_dependency_ids: set[str] = set()
        dependency_by_artifact: dict[str, dict[str, Any]] = {}
        for item in dependency_matrix:
            if not isinstance(item, dict):
                failures.append("evidenceDependencyMatrix entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceDependencyMatrix entry missing artifactId")
                continue
            if artifact_id in seen_dependency_ids:
                failures.append(f"evidenceDependencyMatrix duplicate {artifact_id}")
                continue
            seen_dependency_ids.add(artifact_id)
            dependency_by_artifact[artifact_id] = item

        expected_dependency_ids = tuple(item["artifactId"] for item in WECHAT_RELEASE_PACKET_DEPENDENCY_MATRIX)
        if tuple(dependency_by_artifact) != expected_dependency_ids:
            failures.append("evidenceDependencyMatrix order must match WeChat release evidence workflow")

        for expected in WECHAT_RELEASE_PACKET_DEPENDENCY_MATRIX:
            artifact_id = expected["artifactId"]
            item = dependency_by_artifact.get(artifact_id)
            if not isinstance(item, dict):
                failures.append(f"evidenceDependencyMatrix.{artifact_id} missing object")
                continue
            if tuple(item) != WECHAT_RELEASE_PACKET_DEPENDENCY_MATRIX_FIELDS:
                failures.append(
                    f"evidenceDependencyMatrix.{artifact_id} keys must be "
                    + ", ".join(WECHAT_RELEASE_PACKET_DEPENDENCY_MATRIX_FIELDS)
                )
            for field in WECHAT_RELEASE_PACKET_DEPENDENCY_MATRIX_FIELDS:
                if item.get(field) == expected[field]:
                    continue
                expected_value = expected[field]
                if isinstance(expected_value, list):
                    expected_text = ", ".join(expected_value)
                elif isinstance(expected_value, bool):
                    expected_text = str(expected_value)
                else:
                    expected_text = str(expected_value)
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.{field} must be {expected_text}")

    required_inputs = packet.get("requiredExternalInputs")
    if not isinstance(required_inputs, list):
        failures.append("requiredExternalInputs must be a list")
    else:
        input_ids = tuple(item.get("id") for item in required_inputs if isinstance(item, dict))
        if input_ids != WECHAT_RELEASE_PACKET_REQUIRED_EXTERNAL_INPUT_IDS:
            failures.append(
                "requiredExternalInputs order must be "
                + " -> ".join(WECHAT_RELEASE_PACKET_REQUIRED_EXTERNAL_INPUT_IDS)
            )

    value_matrix = packet.get("valuePropagationMatrix")
    if not isinstance(value_matrix, list):
        failures.append("valuePropagationMatrix must be a list")
    else:
        value_ids = tuple(item.get("id") for item in value_matrix if isinstance(item, dict))
        if value_ids != WECHAT_RELEASE_PACKET_VALUE_PROPAGATION_IDS:
            failures.append(
                "valuePropagationMatrix order must be "
                + " -> ".join(WECHAT_RELEASE_PACKET_VALUE_PROPAGATION_IDS)
            )

    execution_order = packet.get("executionOrder")
    if not isinstance(execution_order, list):
        failures.append("executionOrder must be a list")
    else:
        steps = tuple(item.get("step") for item in execution_order if isinstance(item, dict))
        if steps != WECHAT_RELEASE_PACKET_EXECUTION_STEPS:
            failures.append(
                "executionOrder order must be "
                + " -> ".join(WECHAT_RELEASE_PACKET_EXECUTION_STEPS)
            )

    post_gates = packet.get("postExecutionGates")
    if not isinstance(post_gates, list):
        failures.append("postExecutionGates must be a list")
    elif tuple(post_gates) != WECHAT_RELEASE_PACKET_POST_GATES:
        failures.append(
            "postExecutionGates order must be "
            + " -> ".join(WECHAT_RELEASE_PACKET_POST_GATES)
        )

    return failures


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
    release_packet_path = root / args.wechat_release_packet

    doc = read_text(doc_path)
    project = read_text(project_path)
    pbxproj = read_text(pbxproj_path)
    plist = read_text(plist_path)
    entitlements = read_text(entitlements_path)
    app_entry = read_text(app_entry_path)
    wechat_service = read_text(wechat_service_path)
    aasa = read_text(aasa_path)
    release_packet = read_json(release_packet_path)
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

    release_packet_doc_ok, missing_release_packet_doc_markers = contains_all(doc, WECHAT_RELEASE_PACKET_DOC_MARKERS)
    report.add(
        "wechatReleaseConfigurationPacketReferenced",
        release_packet_doc_ok,
        "document points to the structured real WeChat Release configuration packet and states it is not evidence or submission permission",
        {"missingMarkers": missing_release_packet_doc_markers} if missing_release_packet_doc_markers else None,
    )

    value_matrix_ok, missing_value_matrix_markers = contains_all(doc, VALUE_PROPAGATION_MATRIX_MARKERS)
    report.add(
        "wechatValuePropagationMatrixPresent",
        value_matrix_ok,
        "document maps the same real WeChat AppID, URL Scheme, Universal Link, Team ID, server-only AppSecret, and iOS 26.5 signed-device login proof across all required destinations",
        {"missingMarkers": missing_value_matrix_markers} if missing_value_matrix_markers else None,
    )

    report.add(
        "wechatReleaseConfigurationPacketPresent",
        bool(release_packet),
        str(release_packet_path) if release_packet else "missing WeChat Release configuration packet",
    )
    release_packet_text = as_searchable_json(release_packet)
    release_packet_ok, missing_release_packet_markers = contains_all(
        release_packet_text,
        WECHAT_RELEASE_PACKET_MARKERS,
    )
    release_packet_structure_failures = wechat_release_packet_structure_failures(release_packet)
    release_packet_has_secret_assignment = has_placeholder_secret_assignment(release_packet_text)
    release_packet_details: dict[str, Any] = {}
    if missing_release_packet_markers:
        release_packet_details["missingMarkers"] = missing_release_packet_markers
    if release_packet_structure_failures:
        release_packet_details["structureFailures"] = release_packet_structure_failures
    if release_packet_has_secret_assignment:
        release_packet_details["secretAssignment"] = True
    report.add(
        "wechatReleaseConfigurationPacketValid",
        bool(release_packet) and release_packet_ok and not release_packet_structure_failures and not release_packet_has_secret_assignment,
        "structured packet covers real wx AppID, URL Scheme, server-only AppSecret boundary, Team ID/AASA sync, iOS 26.5 Release validation, provider proof, external evidence, stable aliases, and RD-14 completion boundary",
        release_packet_details if release_packet_details else None,
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
    parser.add_argument("--wechat-release-packet", default=WECHAT_RELEASE_PACKET)
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
