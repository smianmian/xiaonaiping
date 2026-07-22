from __future__ import annotations

import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_ios_release_readiness.py"
VALID_WECHAT_APP_ID = "wxa4f19c3e802b7d65"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_plist(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        plistlib.dump(value, file)


def write_minimal_ios_repo(root: Path, configured_wechat: bool) -> None:
    wechat_app_id = VALID_WECHAT_APP_ID if configured_wechat else ""
    wechat_scheme = wechat_app_id if configured_wechat else ""
    wechat_link = "https://xiaonaiping.example.test/wechat/" if configured_wechat else ""
    write(
        root / "App/iOS/project.yml",
        f"""
targets:
  XiaoNaiPing:
    resources:
      - path: XiaoNaiPing/PrivacyInfo.xcprivacy
    settings:
      configs:
        Release:
          XNP_API_BASE_URL: "https://api.xiaonaiping.test"
          XNP_WECHAT_APP_ID: "{wechat_app_id}"
          XNP_WECHAT_URL_SCHEME: "{wechat_scheme}"
          XNP_WECHAT_UNIVERSAL_LINK: "{wechat_link}"
""".lstrip(),
    )

    plist = {
        "XNPAPIBaseURL": "$(XNP_API_BASE_URL)",
        "XNPWeChatAppID": "$(XNP_WECHAT_APP_ID)",
        "XNPWeChatURLScheme": "$(XNP_WECHAT_URL_SCHEME)",
        "XNPWeChatUniversalLink": "$(XNP_WECHAT_UNIVERSAL_LINK)",
        "LSApplicationQueriesSchemes": ["weixin", "weixinULAPI"],
        "NSCameraUsageDescription": "camera",
        "NSPhotoLibraryUsageDescription": "photos",
    }
    if configured_wechat:
        plist["CFBundleURLTypes"] = [
            {"CFBundleURLSchemes": [wechat_scheme]},
        ]
    else:
        plist["CFBundleURLTypes"] = [
            {"CFBundleURLSchemes": ["$(XNP_WECHAT_URL_SCHEME)"]},
        ]
    write_plist(root / "App/iOS/XiaoNaiPing/Info.plist", plist)
    write_plist(
        root / "App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy",
        {
            "NSPrivacyAccessedAPITypes": [],
            "NSPrivacyTracking": False,
            "NSPrivacyTrackingDomains": [],
            "NSPrivacyCollectedDataTypes": [
                {
                    "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeUserID",
                    "NSPrivacyCollectedDataTypeLinked": True,
                    "NSPrivacyCollectedDataTypeTracking": False,
                    "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
                },
                {
                    "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypePhoneNumber",
                    "NSPrivacyCollectedDataTypeLinked": True,
                    "NSPrivacyCollectedDataTypeTracking": False,
                    "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
                },
                {
                    "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeOtherUserContent",
                    "NSPrivacyCollectedDataTypeLinked": True,
                    "NSPrivacyCollectedDataTypeTracking": False,
                    "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
                },
                {
                    "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypePhotosorVideos",
                    "NSPrivacyCollectedDataTypeLinked": True,
                    "NSPrivacyCollectedDataTypeTracking": False,
                    "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
                },
                {
                    "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeHealth",
                    "NSPrivacyCollectedDataTypeLinked": True,
                    "NSPrivacyCollectedDataTypeTracking": False,
                    "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
                },
                {
                    "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeCrashData",
                    "NSPrivacyCollectedDataTypeLinked": False,
                    "NSPrivacyCollectedDataTypeTracking": False,
                    "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
                },
                {
                    "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypePerformanceData",
                    "NSPrivacyCollectedDataTypeLinked": False,
                    "NSPrivacyCollectedDataTypeTracking": False,
                    "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAnalytics"],
                },
            ],
        },
    )
    write(
        root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        json.dumps(
            {
                "dataCategories": [
                    {"category": "Identifiers", "collected": True},
                    {"category": "Contact Info", "collected": True},
                    {"category": "User Content", "collected": True},
                    {"category": "Photos or Videos", "collected": True},
                    {"category": "Health and Fitness", "collected": True},
                    {"category": "Diagnostics", "collected": True},
                ]
            }
        ),
    )

    sdk_marker = "WechatOpenSDK" if configured_wechat else ""
    write(
        root / "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj",
        f"""
{{
	objects = {{
		AAAA1111 /* Release */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				DEVELOPMENT_TEAM = L2TYJNDTJK;
				INFOPLIST_FILE = XiaoNaiPingWidgets/Info.plist;
				PRODUCT_BUNDLE_IDENTIFIER = com.mewpow.xiaonaiping.widgets;
			}};
			name = Release;
		}};
		ABCD1234 /* Release */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				DEVELOPMENT_TEAM = L2TYJNDTJK;
				INFOPLIST_FILE = XiaoNaiPing/Info.plist;
				PRODUCT_BUNDLE_IDENTIFIER = com.mewpow.xiaonaiping;
			}};
			name = Release;
		}};
		ABCD1235 /* PrivacyInfo.xcprivacy in Resources */ = {{isa = PBXBuildFile; fileRef = ABCD1236 /* PrivacyInfo.xcprivacy */; }};
		1724BE8C448FDB748B006CE9 /* Project object */ = {{
			knownRegions = (
				Base,
				"zh-Hans",
				"zh-Hant-HK",
			);
		}};
		/* {sdk_marker} */
	}};
}}
""".lstrip(),
    )
    write(root / "App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/Localizable.strings", '"微信登录" = "微信登入";\n')
    write(root / "App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/InfoPlist.strings", '"CFBundleDisplayName" = "小奶瓶";\n')
    cloud_sync_client_config = """\
struct CloudSyncConfiguration {
    static var isWeChatLoginConfigured: Bool {
%s
    }
}
""".lstrip() % (
        "        #if canImport(WechatOpenSDK)\n        return true\n        #else\n        return false\n        #endif"
        if configured_wechat
        else "        return false"
    )
    write(
        root / "App/iOS/XiaoNaiPing/Services/CloudSyncAPIClient.swift",
        cloud_sync_client_config,
    )
    write(
        root / "App/iOS/XiaoNaiPing/Services/CloudSyncController.swift",
        """
final class CloudSyncController {
    func loginWithWeChat() async {
        #if DEBUG
        _ = "debug_wechat_ios"
        #else
        let code = try await WeChatLoginService.shared.requestAuthorizationCode()
        _ = try await client.loginWithWeChat(code: code)
        #endif
    }
}
""".lstrip(),
    )
    wechat_service_source = (
        """
final class WeChatLoginService {
    static let shared = WeChatLoginService()

    func requestAuthorizationCode() async throws -> String {
        #if canImport(WechatOpenSDK)
        _ = WXApi.registerApp
        _ = SendAuthReq()
        return "code"
        #else
        throw NSError(domain: "wechat", code: 1)
        #endif
    }

    func handleOpenURL() {
        #if canImport(WechatOpenSDK)
        _ = WXApi.handleOpen
        #endif
    }

    func handleUniversalLink() {
        #if canImport(WechatOpenSDK)
        _ = WXApi.handleOpenUniversalLink
        #endif
    }
}
"""
        if configured_wechat
        else """
final class WeChatLoginService {
    static let shared = WeChatLoginService()

    func requestAuthorizationCode() async throws -> String {
        throw NSError(domain: "wechat", code: 1)
    }

    func handleOpenURL() {}

    func handleUniversalLink() {}
}
"""
    )
    write(root / "App/iOS/XiaoNaiPing/Services/WeChatLoginService.swift", wechat_service_source)
    write(
        root / "App/iOS/XiaoNaiPing/Views/ProfileView.swift",
        """
Button("微信登录") {}
    .disabled(cloudSync.isWorking || !cloudSync.isWeChatLoginConfigured)
""".lstrip(),
    )


class IOSReleaseReadinessTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/ios-release-readiness.json"
        completed = subprocess.run(
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
        self.assertIn("iOS release readiness", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_unconfigured_wechat_client_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_ios_repo(root, configured_wechat=False)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("weChatReleaseBuildSettingsConfigured", report["failedRequiredChecks"])
            self.assertIn("weChatOpenSDKLinked", report["failedRequiredChecks"])
            self.assertIn("weChatRuntimeRequiresOpenSDK", report["failedRequiredChecks"])
            self.assertTrue(report["checks"]["weChatURLTypeConfigured"]["passed"])
            self.assertIn("weChatAuthorizationBridgePresent", report["failedRequiredChecks"])
            self.assertTrue(report["checks"]["releaseWeChatDebugCodeBlocked"]["passed"])
            self.assertTrue(report["checks"]["releaseWeChatButtonGated"]["passed"])

    def test_configured_wechat_client_can_pass_offline_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_ios_repo(root, configured_wechat=True)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_debug_wechat_marker_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_ios_repo(root, configured_wechat=True)
            controller = root / "App/iOS/XiaoNaiPing/Services/CloudSyncController.swift"
            controller.write_text(
                controller.read_text(encoding="utf-8").replace(
                    '        #if DEBUG\n        _ = "debug_wechat_ios"\n        #else\n',
                    '        #if DEBUG\n        #else\n',
                ),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertTrue(report["checks"]["releaseWeChatDebugCodeBlocked"]["passed"])
            self.assertIn("absent", report["checks"]["releaseWeChatDebugCodeBlocked"]["evidence"])

    def test_dry_run_wechat_values_do_not_pass_release_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_ios_repo(root, configured_wechat=True)
            project_yml = root / "App/iOS/project.yml"
            project_yml.write_text(
                project_yml.read_text(encoding="utf-8").replace(
                    VALID_WECHAT_APP_ID,
                    "wxclientdryrun123456",
                ),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("weChatReleaseBuildSettingsConfigured", report["failedRequiredChecks"])
            evidence = report["checks"]["weChatReleaseBuildSettingsConfigured"]["evidence"]
            self.assertIn("XNP_WECHAT_APP_ID=real wx app id", evidence)
            self.assertIn("XNP_WECHAT_URL_SCHEME=real wx scheme", evidence)

    def test_sample_wechat_values_do_not_pass_release_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_ios_repo(root, configured_wechat=True)
            project_yml = root / "App/iOS/project.yml"
            project_yml.write_text(
                project_yml.read_text(encoding="utf-8").replace(
                    VALID_WECHAT_APP_ID,
                    "wx1234567890abcdef",
                ),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("weChatReleaseBuildSettingsConfigured", report["failedRequiredChecks"])
            evidence = report["checks"]["weChatReleaseBuildSettingsConfigured"]["evidence"]
            self.assertIn("XNP_WECHAT_APP_ID=real wx app id", evidence)
            self.assertIn("XNP_WECHAT_URL_SCHEME=real wx scheme", evidence)

    def test_privacy_manifest_extra_type_without_label_category_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_ios_repo(root, configured_wechat=True)
            privacy_manifest_path = root / "App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy"
            with privacy_manifest_path.open("rb") as file:
                manifest = plistlib.load(file)
            manifest["NSPrivacyCollectedDataTypes"].append(
                {
                    "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeProductInteraction",
                    "NSPrivacyCollectedDataTypeLinked": True,
                    "NSPrivacyCollectedDataTypeTracking": False,
                    "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAnalytics"],
                }
            )
            write_plist(privacy_manifest_path, manifest)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyManifestMatchesPrivacyLabel", report["failedRequiredChecks"])
            self.assertIn(
                "manifest data types missing from privacy label: NSPrivacyCollectedDataTypeProductInteraction",
                report["checks"]["privacyManifestMatchesPrivacyLabel"]["evidence"],
            )


if __name__ == "__main__":
    unittest.main()
