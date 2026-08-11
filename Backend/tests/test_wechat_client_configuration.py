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

""".lstrip()


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
