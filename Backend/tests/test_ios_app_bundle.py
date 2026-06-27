from __future__ import annotations

import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_ios_app_bundle.py"
VALID_WECHAT_APP_ID = "wxa4f19c3e802b7d65"


def write_plist(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        plistlib.dump(value, file)


def write_app(root: Path, complete: bool) -> Path:
    app = root / "XiaoNaiPing.app"
    app.mkdir(parents=True)
    executable = app / "XiaoNaiPing"
    executable.write_bytes(b"release-binary" if complete else b"release-binary debug_wechat_ios")
    info = {
        "CFBundleExecutable": "XiaoNaiPing",
        "CFBundleIdentifier": "com.mewpow.xiaonaiping",
        "XNPAPIBaseURL": "https://api.mewpow.com/xiaonaiping",
        "LSApplicationQueriesSchemes": ["weixin", "weixinULAPI"],
        "XNPWeChatAppID": VALID_WECHAT_APP_ID if complete else "",
        "XNPWeChatURLScheme": VALID_WECHAT_APP_ID if complete else "",
        "XNPWeChatUniversalLink": "https://xiaonaiping.example.test/wechat/" if complete else "",
    }
    if complete:
        info["CFBundleURLTypes"] = [
            {"CFBundleURLSchemes": [VALID_WECHAT_APP_ID]},
        ]
    write_plist(app / "Info.plist", info)
    if not complete:
        (app / "README.md").write_text("internal release note\n", encoding="utf-8")
        (app / "LocalConfig.txt").write_text("base=http://127.0.0.1:8787\n", encoding="utf-8")

    l10n = app / "zh-Hant-HK.lproj"
    l10n.mkdir()
    (l10n / "Localizable.strings").write_text('"微信登录" = "微信登入";\n', encoding="utf-8")
    (l10n / "InfoPlist.strings").write_text('"CFBundleDisplayName" = "小奶瓶";\n', encoding="utf-8")

    if complete:
        write_plist(
            app / "PrivacyInfo.xcprivacy",
            {
                "NSPrivacyAccessedAPITypes": [],
                "NSPrivacyTracking": False,
                "NSPrivacyTrackingDomains": [],
                "NSPrivacyCollectedDataTypes": [
                    {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeUserID", "NSPrivacyCollectedDataTypeTracking": False},
                    {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypePhoneNumber", "NSPrivacyCollectedDataTypeTracking": False},
                    {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeOtherUserContent", "NSPrivacyCollectedDataTypeTracking": False},
                    {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypePhotosorVideos", "NSPrivacyCollectedDataTypeTracking": False},
                    {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeHealth", "NSPrivacyCollectedDataTypeTracking": False},
                    {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeProductInteraction", "NSPrivacyCollectedDataTypeTracking": False},
                    {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeCrashData", "NSPrivacyCollectedDataTypeTracking": False},
                    {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypePerformanceData", "NSPrivacyCollectedDataTypeTracking": False},
                ],
            },
        )
    return app


class IOSAppBundleTest(unittest.TestCase):
    def run_checker(self, app: Path) -> dict:
        output = app.parent / "ios-app-bundle.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--app",
                str(app),
                "--output",
                str(output),
                "--allow-incomplete",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("iOS app bundle readiness", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_complete_release_app_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            app = write_app(Path(tempdir), complete=True)

            report = self.run_checker(app)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_debug_marker_and_missing_wechat_config_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            app = write_app(Path(tempdir), complete=False)

            report = self.run_checker(app)

            self.assertFalse(report["passed"])
            self.assertIn("debugWeChatCodeAbsent", report["failedRequiredChecks"])
            self.assertIn("weChatNativeConfigPresent", report["failedRequiredChecks"])
            self.assertIn("weChatURLTypePresent", report["failedRequiredChecks"])
            self.assertIn("releaseBundleInternalDocsAbsent", report["failedRequiredChecks"])
            self.assertIn("releaseBundleForbiddenTextMarkersAbsent", report["failedRequiredChecks"])
            self.assertIn("privacyManifestBundled", report["failedRequiredChecks"])

    def test_dry_run_wechat_values_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            app = write_app(Path(tempdir), complete=True)
            info_path = app / "Info.plist"
            with info_path.open("rb") as file:
                info = plistlib.load(file)
            info["XNPWeChatAppID"] = "wxclientdryrun123456"
            info["XNPWeChatURLScheme"] = "wxclientdryrun123456"
            info["CFBundleURLTypes"] = [
                {"CFBundleURLSchemes": ["wxclientdryrun123456"]},
            ]
            write_plist(info_path, info)

            report = self.run_checker(app)

            self.assertFalse(report["passed"])
            self.assertIn("weChatNativeConfigPresent", report["failedRequiredChecks"])
            self.assertIn("weChatURLTypePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["weChatNativeConfigPresent"]["evidence"]
            self.assertIn("XNPWeChatAppID=real wx app id", evidence)
            self.assertIn("XNPWeChatURLScheme=real wx scheme", evidence)

    def test_sample_wechat_values_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            app = write_app(Path(tempdir), complete=True)
            info_path = app / "Info.plist"
            with info_path.open("rb") as file:
                info = plistlib.load(file)
            info["XNPWeChatAppID"] = "wx1234567890abcdef"
            info["XNPWeChatURLScheme"] = "wx1234567890abcdef"
            info["CFBundleURLTypes"] = [
                {"CFBundleURLSchemes": ["wx1234567890abcdef"]},
            ]
            write_plist(info_path, info)

            report = self.run_checker(app)

            self.assertFalse(report["passed"])
            self.assertIn("weChatNativeConfigPresent", report["failedRequiredChecks"])
            self.assertIn("weChatURLTypePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["weChatNativeConfigPresent"]["evidence"]
            self.assertIn("XNPWeChatAppID=real wx app id", evidence)
            self.assertIn("XNPWeChatURLScheme=real wx scheme", evidence)

    def test_product_interaction_privacy_type_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            app = write_app(Path(tempdir), complete=True)
            privacy_path = app / "PrivacyInfo.xcprivacy"
            with privacy_path.open("rb") as file:
                privacy = plistlib.load(file)
            privacy["NSPrivacyCollectedDataTypes"] = [
                entry
                for entry in privacy["NSPrivacyCollectedDataTypes"]
                if entry.get("NSPrivacyCollectedDataType") != "NSPrivacyCollectedDataTypeProductInteraction"
            ]
            write_plist(privacy_path, privacy)

            report = self.run_checker(app)

            self.assertFalse(report["passed"])
            self.assertIn("privacyManifestCollectedTypesComplete", report["failedRequiredChecks"])
            evidence = report["checks"]["privacyManifestCollectedTypesComplete"]["evidence"]
            self.assertIn("NSPrivacyCollectedDataTypeProductInteraction", evidence)


if __name__ == "__main__":
    unittest.main()
