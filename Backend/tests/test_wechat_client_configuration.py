from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_wechat_client_configuration.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_doc() -> str:
    return """
# WECHAT_CLIENT_CONFIGURATION.md

日期：2026-06-30

AppID format is wx + 16 hex. Client values are XNP_WECHAT_APP_ID,
XNP_WECHAT_URL_SCHEME, and XNP_WECHAT_UNIVERSAL_LINK. XNP_WECHAT_APP_SECRET
只配置在服务端，不能写进 iOS 工程。Evidence goes to 08-wechat-open-platform.

## 微信开放平台后台字段清单

| 微信开放平台字段 | 小奶瓶填写口径 | 证据要求 |
|---|---|---|
| 移动应用名称 | 小奶瓶 | 截图保留应用名称和审核/配置状态 |
| iOS Bundle ID | `com.mewpow.xiaonaiping` | 必须和 Release 包 Bundle ID 一致 |
| AppID | 真实 `wx + 16 hex` | 可在 `08-wechat-open-platform.png` 展示 |
| URL Scheme | equal to AppID | 必须和 `XNP_WECHAT_URL_SCHEME` 一致 |
| Universal Link | `https://api.mewpow.com/xiaonaiping/wechat/` | 必须和 `XNP_WECHAT_UNIVERSAL_LINK` 一致 |
| AppSecret | 只写入服务端私有 env `XNP_WECHAT_APP_SECRET` | 必须遮挡，不写入 iOS 工程、截图或仓库 |

本机验证只使用 iOS 26.5。iOS 27.0 不能作为本机测试环境。

```bash
xcodebuild -sdk iphonesimulator26.5
xcodebuild -sdk iphoneos26.5
python3 Backend/scripts/check_ios_release_readiness.py
python3 Backend/scripts/check_ios_app_bundle.py
python3 Backend/scripts/check_wechat_client_configuration.py
python3 Backend/scripts/prepare_wechat_release_env.py
python3 Backend/scripts/verify_auth_providers.py
python3 Backend/scripts/check_launch_objective_audit.py
python3 Backend/scripts/prepare_wechat_release_env.py --output-json Backend/proof/wechat-release-env-validation-20260630T-current.json
python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260630T-current-ios265.json
python3 Backend/scripts/check_ios_app_bundle.py --output Backend/proof/ios-app-bundle-20260630T-current-ios265.json
python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260630T-current.json
python3 Backend/scripts/verify_auth_providers.py --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --output Backend/proof/auth-providers-20260630T-current.json --allow-incomplete
```

同轮 `20260630T-current` proof 全部变绿后，再同步稳定 alias：`ios-release-readiness.json`、`ios-app-bundle.json`、`wechat-client-configuration.json` 和 `auth-providers.json`；不要把旧部署 proof 或旧 auth provider proof 当成真实微信配置完成证据。

## 客户端配置预注入矩阵

| 配置项 | 能先做 | 必须等外部真值 | 落点 | 复跑 gate |
|---|---|---|---|---|
| `XNP_WECHAT_APP_ID` | 预留 build setting、Info.plist key 和注入命令 | 微信开放平台真实 AppID，格式 `wx + 16 hex` | `App/iOS/project.yml`、`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`、`App/iOS/XiaoNaiPing/Info.plist` | `check_ios_release_readiness.py`、`check_ios_app_bundle.py` |
| `XNP_WECHAT_URL_SCHEME` | 预留 `CFBundleURLTypes` 槽位 | URL Scheme equal to AppID | `App/iOS/XiaoNaiPing/Info.plist` | `check_ios_app_bundle.py` |
| `XNP_WECHAT_UNIVERSAL_LINK` | 预留当前候选路径 | 微信开放平台后台绑定同一路径，且与 AASA 响应一致 | `App/iOS/project.yml`、微信开放平台后台 | `check_wechat_client_configuration.py`、`check_ios_app_bundle.py` |
| `XNP_ASSOCIATED_DOMAIN` | 预留 `applinks:api.mewpow.com` entitlement | Apple Developer Team ID 和 Associated Domains 在当前组织下生效 | `App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements`、Apple Developer 后台 | `check_ios_release_readiness.py`、`check_wechat_client_configuration.py` |
| AASA `appID` / `appIDs` | 先保留当前 Team ID + Bundle ID 结构 | Apple Developer Team ID 若漂移，必须同轮改 AASA、工程签名和 ExportOptions | `Backend/static/apple-app-site-association` | `check_wechat_client_configuration.py`、`check_ios_app_bundle.py` |
| `XNP_WECHAT_APP_SECRET` | 只写清楚服务端 env 名称和脱敏规则 | AppSecret 只进服务端私有 env，不进 iOS 工程、截图或仓库 | 服务器私有 env | `verify_auth_providers.py` |

当前能本地先完成的已经是上表里的槽位、回调、AASA 结构和 gate；剩下的真实 AppID、URL Scheme equal to AppID、Apple Developer Team ID 和服务端 AppSecret 必须来自外部后台。不能为了过 gate 写入假的 `wxclientdryrun...`、debug、test、placeholder 或不属于微信开放平台移动应用的 `wx...`。

## 真实值传播核对矩阵

拿到微信开放平台真实值后，按下面矩阵逐项核对。每一行必须来自同一个微信开放平台移动应用和同一个 Apple Developer 组织 Team。

| 值 | 权威来源 | 必须同步到 | 通过证据 | 禁止替代 |
|---|---|---|---|---|
| 真实微信 AppID | 微信开放平台移动应用，格式 `wx + 16 hex` | `XNP_WECHAT_APP_ID`、`XNP_WECHAT_URL_SCHEME`、`XNPWeChatAppID`、`XNPWeChatURLScheme`、`CFBundleURLTypes`、`08-wechat-open-platform.png` | `wechat-release-env-validation-20260630T-current.json`、`ios-app-bundle-20260630T-current-ios265.json`、`08-wechat-open-platform.png` | `wxclientdryrun123456`、debug、test、placeholder、其他 App 的 `wx...` |
| URL Scheme | 微信开放平台同一移动应用 | `XNP_WECHAT_URL_SCHEME`、`CFBundleURLTypes`、Release 包 URL Types | `ios-app-bundle-20260630T-current-ios265.json` 和真机微信回调录屏 | 与 AppID 不一致的 scheme |
| Universal Link | 微信开放平台 Universal Link 输入框和 AASA | `XNP_WECHAT_UNIVERSAL_LINK`、`XNPWeChatUniversalLink`、`Backend/static/apple-app-site-association`、Associated Domains | `08b-wechat-universal-link-aasa.png`、`universal-links-20260630T-current.json`、`wechat-client-configuration-20260630T-current.json` | 只截图微信后台、不验证 AASA 或 Associated Domains |
| Apple Developer Team ID | D-U-N-S 后 Apple Developer Organization 页面 | Xcode signing、ExportOptions、AASA `appID` / `appIDs`、Associated Domains 截图 | `08b-wechat-universal-link-aasa.png`、`ios-release-readiness-20260630T-current-ios265.json` | 旧 Team ID 当作新组织 proof |
| AppSecret | 微信开放平台同一移动应用 | 仅服务器私有 env `XNP_WECHAT_APP_SECRET` | `auth-providers-20260630T-current.json` 只能显示已配置且已脱敏 | 写入 iOS 工程、Info.plist、截图、JSON、仓库文档或命令行历史 |
| 真机微信登录 | iOS 26.5 TestFlight 或签名真机包 | RD-14 微信登录录屏、`12-real-device-regression.md` | 微信授权拉起、回到 `com.mewpow.xiaonaiping`、后端完成登录 | 模拟器、iOS 27、debug code 或未签名包 |

## 真实微信 Release 配置执行包

结构化执行包见 `Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json`。该 JSON 只用于拿到真实微信开放平台 AppID 后按顺序执行，不是证据、不是 AppSecret 容器，也不能作为提交许可。

1. 外部输入必须来自微信开放平台移动应用和 D-U-N-S 后 Apple Developer 组织页：真实 `wx + 16 hex` AppID、URL Scheme equal to AppID、服务端私有 `XNP_WECHAT_APP_SECRET`、Apple Developer Team ID、Universal Link。
2. 用 `prepare_wechat_release_env.py` 生成本机 ignored env 和脱敏 validation proof。
3. 只用 iOS 26.5 跑 Release simulator / device bundle 预检，然后刷新 `ios-release-readiness-20260630T-current-ios265.json`、`ios-app-bundle-20260630T-current-ios265.json`、`wechat-client-configuration-20260630T-current.json`。
4. 服务端只在私有 env 配置 `XNP_WECHAT_APP_SECRET`，随后刷新 `auth-providers-20260630T-current.json`。
5. 只有 RD-14 iOS 26.5 TestFlight / 签名真机微信登录通过后，才允许同步稳定 alias。
""".lstrip()


def valid_evidence_dependency_matrix() -> list[dict]:
    return [
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
    ]


def valid_wechat_release_packet() -> dict:
    return {
        "artifactType": "wechat-release-configuration-packet",
        "status": "release-configuration-packet-not-evidence",
        "date": "2026-06-30",
        "project": "XiaoNaiPing",
        "appName": "小奶瓶",
        "bundleId": "com.mewpow.xiaonaiping",
        "sourceFiles": {
            "wechatClientConfiguration": "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md",
            "wechatOpenPlatformEvidenceTemplate": "Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json",
            "externalPlatformHandoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
            "appleDeveloperDunsHandoff": "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
            "aasa": "Backend/static/apple-app-site-association",
            "iosReleaseReadinessProof": "Backend/proof/ios-release-readiness-20260630T-current-ios265.json",
            "iosAppBundleProof": "Backend/proof/ios-app-bundle-20260630T-current-ios265.json",
            "wechatClientConfigurationProof": "Backend/proof/wechat-client-configuration-20260630T-current.json",
            "authProvidersProof": "Backend/proof/auth-providers-20260630T-current.json",
        },
        "targetEvidenceFiles": {
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
        },
        "evidenceFileChecks": [
            {
                "artifactId": "wechatOpenPlatform",
                "target": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png or .pdf",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "wechatUniversalLinkAasa",
                "target": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png or .pdf",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "appleDeveloperTeamId",
                "target": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png or .pdf",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "wechatReleaseEnvValidationProof",
                "target": "Backend/proof/wechat-release-env-validation-20260630T-current.json",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "iosReleaseReadinessProof",
                "target": "Backend/proof/ios-release-readiness-20260630T-current-ios265.json",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "iosAppBundleProof",
                "target": "Backend/proof/ios-app-bundle-20260630T-current-ios265.json",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "wechatClientConfigurationProof",
                "target": "Backend/proof/wechat-client-configuration-20260630T-current.json",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "authProvidersProof",
                "target": "Backend/proof/auth-providers-20260630T-current.json",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "realDeviceWechatLogin",
                "target": "Docs/08_Release/AppStoreEvidence/RealDevice/RD-14-wechat-login.png or .mp4",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
            {
                "artifactId": "realDeviceRegression",
                "target": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsWechatReleaseConfiguration": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            },
        ],
        "evidenceDependencyMatrix": valid_evidence_dependency_matrix(),
        "requiredExternalInputs": [
            {
                "id": "realWechatAppId",
                "format": "wx + 16 lowercase hex characters",
                "mustMatch": ["XNP_WECHAT_APP_ID", "XNP_WECHAT_URL_SCHEME", "CFBundleURLTypes", "08-wechat-open-platform.png"],
                "forbiddenValues": ["wxclientdryrun123456", "debug", "test", "placeholder"],
            },
            {
                "id": "wechatAppSecret",
                "storage": "server private env only",
                "mustNotAppearIn": ["iOS project", "screenshots", "JSON evidence"],
            },
            {
                "id": "appleDeveloperTeamId",
                "mustMatch": ["ExportOptions teamID", "AASA appID/appIDs prefix", "08b-wechat-universal-link-aasa.png"],
            },
            {
                "id": "wechatUniversalLink",
                "value": "https://api.mewpow.com/xiaonaiping/wechat/",
                "mustMatch": ["Associated Domains applinks:api.mewpow.com"],
            },
        ],
        "valuePropagationMatrix": [
            {
                "id": "sameRealWechatAppId",
                "authority": "WeChat Open Platform mobile app",
                "valueFormat": "wx + 16 lowercase hex characters",
                "mustMatch": [
                    "XNP_WECHAT_APP_ID",
                    "XNP_WECHAT_URL_SCHEME",
                    "XNPWeChatAppID",
                    "XNPWeChatURLScheme",
                    "CFBundleURLTypes",
                    "08-wechat-open-platform.png",
                    "wechat-release-env-validation-20260630T-current.json",
                    "ios-app-bundle-20260630T-current-ios265.json",
                ],
                "mustNotUse": ["wxclientdryrun123456", "debug", "test", "placeholder"],
            },
            {
                "id": "sameUniversalLinkAndAasa",
                "authority": "WeChat Open Platform Universal Link plus Apple AASA",
                "value": "https://api.mewpow.com/xiaonaiping/wechat/",
                "mustMatch": [
                    "XNP_WECHAT_UNIVERSAL_LINK",
                    "XNPWeChatUniversalLink",
                    "Backend/static/apple-app-site-association",
                    "Associated Domains applinks:api.mewpow.com",
                    "08b-wechat-universal-link-aasa.png",
                    "universal-links-20260630T-current.json",
                    "wechat-client-configuration-20260630T-current.json",
                ],
                "mustNotUse": ["WeChat console screenshot without AASA proof"],
            },
            {
                "id": "serverOnlyAppSecret",
                "authority": "WeChat Open Platform mobile app",
                "mustMatch": [
                    "server private env XNP_WECHAT_APP_SECRET",
                    "auth-providers-20260630T-current.json redacted configured status",
                ],
                "mustNotAppearIn": ["iOS project", "Info.plist", "xcodeproj", "screenshots", "JSON evidence"],
            },
            {
                "id": "ios265SignedWechatLogin",
                "authority": "iOS 26.5 TestFlight or signed real-device build",
                "mustMatch": ["RD-14 WeChat login recording", "12-real-device-regression.md", "backend login success"],
                "mustNotUse": ["simulator", "iOS 27", "debug code", "WeChat console screenshot only"],
            },
        ],
        "executionOrder": [
            {"step": "confirmTeamId"},
            {"step": "syncTeamIdIfNeeded"},
            {
                "step": "prepareWechatReleaseEnv",
                "command": "python3 Backend/scripts/prepare_wechat_release_env.py --output-json Backend/proof/wechat-release-env-validation-20260630T-current.json",
            },
            {"step": "buildReleaseSimIos265", "command": "xcodebuild -sdk iphonesimulator26.5"},
            {"step": "buildReleaseDeviceIos265", "command": "xcodebuild -sdk iphoneos26.5"},
            {
                "step": "refreshClientProofs",
                "commands": [
                    "python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260630T-current-ios265.json",
                    "python3 Backend/scripts/check_ios_app_bundle.py --output Backend/proof/ios-app-bundle-20260630T-current-ios265.json",
                    "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260630T-current.json",
                ],
            },
            {
                "step": "refreshServerAuthProof",
                "command": "python3 Backend/scripts/verify_auth_providers.py --output Backend/proof/auth-providers-20260630T-current.json",
            },
            {
                "step": "captureExternalEvidence",
                "evidence": ["08-wechat-open-platform.png", "08b-wechat-universal-link-aasa.png"],
            },
            {
                "step": "syncStableAliases",
                "copyTargets": [
                    "ios-release-readiness.json",
                    "ios-app-bundle.json",
                    "wechat-client-configuration.json",
                    "auth-providers.json",
                ],
            },
        ],
        "postExecutionGates": [
            "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260630T-current.json",
            "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
            "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
            "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260630T-current.json",
            "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
        ],
        "completionRule": "RD-14 iOS 26.5 TestFlight or signed real-device login passes and production-readiness.json plus launch-objective-audit.json are ready=true.",
    }


def valid_project_yml() -> str:
    return """
packages:
  WechatOpenSDK:
    url: https://github.com/yanyin1986/WechatOpenSDK.git
targets:
  XiaoNaiPing:
    dependencies:
      - package: WechatOpenSDK
        product: WechatOpenSDK
      - sdk: WebKit.framework
settings:
  configs:
    Release:
      XNP_WECHAT_APP_ID: "wxe919f9e41822223c"
      XNP_WECHAT_URL_SCHEME: "wxe919f9e41822223c"
      XNP_WECHAT_UNIVERSAL_LINK: "https://api.mewpow.com/xiaonaiping/wechat/"
      XNP_ASSOCIATED_DOMAIN: "applinks:api.mewpow.com"
""".lstrip()


def valid_info_plist() -> str:
    return """
<plist>
<dict>
  <key>CFBundleURLTypes</key>
  <array>
    <dict>
      <key>CFBundleURLSchemes</key>
      <array>
        <string>$(XNP_WECHAT_URL_SCHEME)</string>
      </array>
    </dict>
  </array>
  <key>LSApplicationQueriesSchemes</key>
  <array>
    <string>weixin</string>
    <string>weixinULAPI</string>
  </array>
  <key>XNPWeChatAppID</key>
  <string>$(XNP_WECHAT_APP_ID)</string>
  <key>XNPWeChatURLScheme</key>
  <string>$(XNP_WECHAT_URL_SCHEME)</string>
  <key>XNPWeChatUniversalLink</key>
  <string>$(XNP_WECHAT_UNIVERSAL_LINK)</string>
</dict>
</plist>
    """.lstrip()


def valid_pbxproj() -> str:
    return """
{
  DB060DB3B7880529CFE1888B /* WechatOpenSDK in Frameworks */ = {};
  6D1866E7072EC8D5D8A08D98 /* WebKit.framework in Frameworks */ = {};
  buildSettings = {
    PRODUCT_BUNDLE_IDENTIFIER = com.mewpow.xiaonaiping;
    CODE_SIGN_ENTITLEMENTS = XiaoNaiPing/XiaoNaiPing.entitlements;
    XNP_ASSOCIATED_DOMAIN = "applinks:api.mewpow.com";
    XNP_WECHAT_APP_ID = wxe919f9e41822223c;
    XNP_WECHAT_UNIVERSAL_LINK = "https://api.mewpow.com/xiaonaiping/wechat/";
    XNP_WECHAT_URL_SCHEME = wxe919f9e41822223c;
  };
}
""".lstrip()


def valid_app_entry() -> str:
    return """
import SwiftUI

@main
struct XiaoNaiPingApp: App {
    var body: some Scene {
        WindowGroup {
            RootTabView()
                .onOpenURL { url in
                    _ = WeChatLoginService.shared.handleOpenURL(url)
                }
                .onContinueUserActivity(NSUserActivityTypeBrowsingWeb) { userActivity in
                    _ = WeChatLoginService.shared.handleUniversalLink(userActivity)
                }
        }
    }
}
""".lstrip()


def valid_wechat_service() -> str:
    return """
import Foundation
#if canImport(WechatOpenSDK)
import WechatOpenSDK
#endif

final class WeChatLoginService {
    func requestAuthorizationCode() {
        guard WXApi.registerApp(appID, universalLink: universalLink.absoluteString) else { return }
        let request = SendAuthReq()
        request.scope = "snsapi_userinfo"
        WXApi.send(request) { _ in }
    }

    func handleOpenURL(_ url: URL) -> Bool {
        WXApi.handleOpen(url, delegate: self)
    }

    func handleUniversalLink(_ userActivity: NSUserActivity) -> Bool {
        WXApi.handleOpenUniversalLink(userActivity, delegate: self)
    }

    func handle(response: SendAuthResp) {
        guard response.state == expectedState else { return }
        guard let code = response.code else { return }
        _ = code
    }
}
""".lstrip()


def valid_aasa() -> str:
    return """
{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appID": "L2TYJNDTJK.com.mewpow.xiaonaiping",
        "paths": [
          "/wechat/*",
          "/xiaonaiping/wechat/*"
        ],
        "appIDs": [
          "L2TYJNDTJK.com.mewpow.xiaonaiping"
        ],
        "components": [
          { "/": "/wechat/*" },
          { "/": "/xiaonaiping/wechat/*" }
        ]
      }
    ]
  }
}
""".lstrip()


def valid_entitlements() -> str:
    return """
<plist>
<dict>
  <key>com.apple.developer.associated-domains</key>
  <array>
    <string>$(XNP_ASSOCIATED_DOMAIN)</string>
  </array>
</dict>
</plist>
""".lstrip()


def write_valid_inputs(root: Path, doc: str | None = None) -> None:
    write(root / "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md", doc if doc is not None else valid_doc())
    write(
        root / "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json",
        json.dumps(valid_wechat_release_packet(), ensure_ascii=False),
    )
    write(root / "App/iOS/project.yml", valid_project_yml())
    write(root / "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj", valid_pbxproj())
    write(root / "App/iOS/XiaoNaiPing/Info.plist", valid_info_plist())
    write(root / "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements", valid_entitlements())
    write(root / "App/iOS/XiaoNaiPing/XiaoNaiPingApp.swift", valid_app_entry())
    write(root / "App/iOS/XiaoNaiPing/Services/WeChatLoginService.swift", valid_wechat_service())
    write(root / "Backend/static/apple-app-site-association", valid_aasa())


class WeChatClientConfigurationTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/wechat-client-configuration.json"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(root),
                "--output",
                str(output),
                "--allow-incomplete",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(output.read_text(encoding="utf-8"))

    def test_complete_configuration_handoff_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])
            self.assertTrue(report["checks"]["wechatValuePropagationMatrixPresent"]["passed"])

    def test_missing_ios_265_commands_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc().replace("-sdk iphoneos26.5", "-sdk iphoneos")
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ios265ValidationCommandsPresent", report["failedRequiredChecks"])
            self.assertEqual(report["checks"]["ios265ValidationCommandsPresent"]["missingMarkers"], ["-sdk iphoneos26.5"])

    def test_app_secret_assignment_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc() + "\nexport XNP_WECHAT_APP_SECRET=secret\n"
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("docDoesNotAssignAppSecret", report["failedRequiredChecks"])

    def test_missing_auth_provider_validation_command_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc().replace("verify_auth_providers.py", "verify_auth_provider.py")
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("proofRegenerationCommandsPresent", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["proofRegenerationCommandsPresent"]["missingMarkers"],
                ["verify_auth_providers.py"],
            )

    def test_client_preconfiguration_matrix_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc().replace("## 客户端配置预注入矩阵", "## 客户端配置说明")
            doc = doc.replace("能先做", "已预留")
            doc = doc.replace("必须等外部真值", "待补")
            doc = doc.replace("不能为了过 gate 写入假的 `wxclientdryrun...`、debug、test、placeholder 或不属于微信开放平台移动应用的 `wx...`。", "")
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("clientPreconfigurationMatrixPresent", report["failedRequiredChecks"])
            missing = report["checks"]["clientPreconfigurationMatrixPresent"]["missingMarkers"]
            self.assertIn("## 客户端配置预注入矩阵", missing)
            self.assertIn("能先做", missing)
            self.assertIn("必须等外部真值", missing)

    def test_wechat_validation_must_use_current_proof_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = (
                valid_doc()
                .replace("日期：2026-06-30", "日期：2026-06-28")
                .replace("wechat-release-env-validation-20260630T-current.json", "wechat-release-env-validation.json")
                .replace("ios-release-readiness-20260630T-current-ios265.json", "ios-release-readiness.json")
                .replace("ios-app-bundle-20260630T-current-ios265.json", "ios-app-bundle.json")
                .replace("wechat-client-configuration-20260630T-current.json", "wechat-client-configuration.json")
                .replace("huawei-baota-deploy-20260630T-current.json", "huawei-baota-deploy-20260625T080412Z.json")
                .replace("auth-providers-20260630T-current.json", "auth-providers.json")
                .replace(" --allow-incomplete", "")
                .replace("同轮 `20260630T-current` proof 全部变绿后，再", "同轮 proof 全部变绿后，再")
                .replace("不要把旧部署 proof 或旧 auth provider proof 当成真实微信配置完成证据。", "")
            )
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("handoffDocumentCoversRequiredValues", report["failedRequiredChecks"])
            self.assertIn("wechatValidationUsesCurrentProofChain", report["failedRequiredChecks"])
            check = report["checks"]["wechatValidationUsesCurrentProofChain"]
            self.assertIn("wechat-release-env-validation-20260630T-current.json", check["missingMarkers"])
            self.assertIn("huawei-baota-deploy-20260630T-current.json", check["missingMarkers"])
            self.assertIn("huawei-baota-deploy-20260625T080412Z.json", check["staleMarkers"])
            self.assertIn("--output Backend/proof/auth-providers.json", check["staleMarkers"])

    def test_wechat_release_configuration_packet_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            packet = valid_wechat_release_packet()
            packet["status"] = "evidence"
            packet["requiredExternalInputs"] = [
                item for item in packet["requiredExternalInputs"] if item["id"] != "appleDeveloperTeamId"
            ]
            packet["completionRule"] = "WeChat configuration is complete."
            write(
                root / "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("wechatReleaseConfigurationPacketValid", report["failedRequiredChecks"])
            missing = report["checks"]["wechatReleaseConfigurationPacketValid"]["missingMarkers"]
            self.assertIn("release-configuration-packet-not-evidence", missing)
            self.assertIn("RD-14 iOS 26.5 TestFlight or signed real-device login passes", missing)
            structure_failures = report["checks"]["wechatReleaseConfigurationPacketValid"]["structureFailures"]
            self.assertTrue(
                any("requiredExternalInputs order must be" in failure for failure in structure_failures)
            )

    def test_wechat_release_configuration_packet_rejects_reordered_or_extra_items(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            packet = valid_wechat_release_packet()
            packet["sourceFiles"]["extraTemplate"] = "Docs/08_Release/template-only.md"
            packet["requiredExternalInputs"].append(packet["requiredExternalInputs"].pop(0))
            packet["valuePropagationMatrix"].append(packet["valuePropagationMatrix"].pop(0))
            packet["executionOrder"].append(packet["executionOrder"].pop(0))
            packet["postExecutionGates"].append(packet["postExecutionGates"].pop(0))
            write(
                root / "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("wechatReleaseConfigurationPacketValid", report["failedRequiredChecks"])
            structure_failures = report["checks"]["wechatReleaseConfigurationPacketValid"]["structureFailures"]
            self.assertTrue(any("sourceFiles order must be" in failure for failure in structure_failures))
            self.assertTrue(any("requiredExternalInputs order must be" in failure for failure in structure_failures))
            self.assertTrue(any("valuePropagationMatrix order must be" in failure for failure in structure_failures))
            self.assertTrue(any("executionOrder order must be" in failure for failure in structure_failures))
            self.assertTrue(any("postExecutionGates order must be" in failure for failure in structure_failures))

    def test_wechat_release_configuration_packet_requires_evidence_file_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            packet = valid_wechat_release_packet()
            packet["targetEvidenceFiles"].pop("wechatUniversalLinkAasa")
            packet["evidenceFileChecks"] = [
                item for item in packet["evidenceFileChecks"] if item["artifactId"] != "wechatOpenPlatform"
            ]
            packet["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/08b-wrong.png"
            packet["evidenceFileChecks"][0]["sha256"] = "already-filled"
            packet["evidenceFileChecks"][0]["sameRoundAsWechatReleaseConfiguration"] = True
            packet["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            write(
                root / "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("wechatReleaseConfigurationPacketValid", report["failedRequiredChecks"])
            structure_failures = report["checks"]["wechatReleaseConfigurationPacketValid"]["structureFailures"]
            self.assertIn(
                "targetEvidenceFiles.wechatUniversalLinkAasa must be "
                "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png or .pdf",
                structure_failures,
            )
            self.assertIn(
                "evidenceFileChecks.wechatOpenPlatform missing object",
                structure_failures,
            )
            self.assertIn(
                "evidenceFileChecks.wechatUniversalLinkAasa.target must be "
                "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png or .pdf",
                structure_failures,
            )
            self.assertIn(
                "evidenceFileChecks.wechatUniversalLinkAasa.sha256 must be 'FILL_AFTER_CAPTURE'",
                structure_failures,
            )
            self.assertIn(
                "evidenceFileChecks.wechatUniversalLinkAasa.sameRoundAsWechatReleaseConfiguration must be False",
                structure_failures,
            )
            self.assertIn(
                "evidenceFileChecks.wechatUniversalLinkAasa.secretValuesNotRecorded must be False",
                structure_failures,
            )

    def test_wechat_release_configuration_packet_requires_dependency_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            packet = valid_wechat_release_packet()
            packet["evidenceDependencyMatrix"] = [
                item for item in packet["evidenceDependencyMatrix"] if item["artifactId"] != "wechatUniversalLinkAasa"
            ]
            for item in packet["evidenceDependencyMatrix"]:
                if item["artifactId"] == "wechatReleaseEnvValidationProof":
                    item["proves"] = ["env exists"]
                if item["artifactId"] == "authProvidersProof":
                    item["requiredBeforeStableAliasSync"] = False
                    item["initialStatus"] = "captured"
            write(
                root / "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("wechatReleaseConfigurationPacketValid", report["failedRequiredChecks"])
            structure_failures = report["checks"]["wechatReleaseConfigurationPacketValid"]["structureFailures"]
            self.assertIn(
                "evidenceDependencyMatrix order must match WeChat release evidence workflow",
                structure_failures,
            )
            self.assertIn(
                "evidenceDependencyMatrix.wechatUniversalLinkAasa missing object",
                structure_failures,
            )
            self.assertIn(
                "evidenceDependencyMatrix.wechatReleaseEnvValidationProof.proves must be "
                "real WeChat AppID format and URL Scheme equality are validated before Release build, "
                "local ignored env is prepared without storing AppSecret",
                structure_failures,
            )
            self.assertIn(
                "evidenceDependencyMatrix.authProvidersProof.requiredBeforeStableAliasSync must be True",
                structure_failures,
            )
            self.assertIn(
                "evidenceDependencyMatrix.authProvidersProof.initialStatus must be pending",
                structure_failures,
            )

    def test_value_propagation_matrix_is_required_in_document(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc().replace("## 真实值传播核对矩阵", "## 真实值说明")
            doc = doc.replace("同一个微信开放平台移动应用", "同一个后台")
            doc = doc.replace("RD-14 微信登录录屏", "微信登录截图")
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("wechatValuePropagationMatrixPresent", report["failedRequiredChecks"])
            missing = report["checks"]["wechatValuePropagationMatrixPresent"]["missingMarkers"]
            self.assertIn("## 真实值传播核对矩阵", missing)
            self.assertIn("同一个微信开放平台移动应用", missing)
            self.assertIn("RD-14 微信登录录屏", missing)

    def test_value_propagation_matrix_is_required_in_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            packet = valid_wechat_release_packet()
            packet.pop("valuePropagationMatrix")
            write(
                root / "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("wechatReleaseConfigurationPacketValid", report["failedRequiredChecks"])
            missing = report["checks"]["wechatReleaseConfigurationPacketValid"]["missingMarkers"]
            self.assertIn("valuePropagationMatrix", missing)
            self.assertIn("sameRealWechatAppId", missing)

    def test_open_platform_field_sheet_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc().replace("## 微信开放平台后台字段清单", "## 微信后台").replace("equal to AppID", "")
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("handoffDocumentCoversRequiredValues", report["failedRequiredChecks"])
            missing = report["checks"]["handoffDocumentCoversRequiredValues"]["missingMarkers"]
            self.assertIn("## 微信开放平台后台字段清单", missing)
            self.assertIn("equal to AppID", missing)

    def test_missing_associated_domains_entitlement_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            write(root / "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements", "<plist><dict></dict></plist>\n")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("associatedDomainsEntitlementWired", report["failedRequiredChecks"])

    def test_missing_xcode_project_release_wechat_slots_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            write(
                root / "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj",
                valid_pbxproj().replace("XNP_WECHAT_URL_SCHEME = wxe919f9e41822223c;\n", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("xcodeProjectReleaseBuildSettingsWired", report["failedRequiredChecks"])
            self.assertIn(
                "XNP_WECHAT_URL_SCHEME = wxe919f9e41822223c;",
                report["checks"]["xcodeProjectReleaseBuildSettingsWired"]["missingMarkers"],
            )

    def test_missing_app_callback_entry_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            write(
                root / "App/iOS/XiaoNaiPing/XiaoNaiPingApp.swift",
                valid_app_entry().replace(".onContinueUserActivity(NSUserActivityTypeBrowsingWeb)", ".task"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appEntryHandlesWeChatCallbacks", report["failedRequiredChecks"])
            self.assertIn(
                ".onContinueUserActivity(NSUserActivityTypeBrowsingWeb)",
                report["checks"]["appEntryHandlesWeChatCallbacks"]["missingMarkers"],
            )

    def test_missing_aasa_wechat_callback_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            write(
                root / "Backend/static/apple-app-site-association",
                valid_aasa().replace('"/xiaonaiping/wechat/*"', '"/other/*"'),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("aasaCoversWeChatUniversalLinkPaths", report["failedRequiredChecks"])
            self.assertIn(
                '"/xiaonaiping/wechat/*"',
                report["checks"]["aasaCoversWeChatUniversalLinkPaths"]["missingMarkers"],
            )


if __name__ == "__main__":
    unittest.main()
