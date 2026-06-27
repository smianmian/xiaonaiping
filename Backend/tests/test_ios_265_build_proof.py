from __future__ import annotations

import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_ios_265_build_proof.py"
PRIVACY_DATA_TYPES = [
    "NSPrivacyCollectedDataTypeUserID",
    "NSPrivacyCollectedDataTypePhoneNumber",
    "NSPrivacyCollectedDataTypeOtherUserContent",
    "NSPrivacyCollectedDataTypePhotosorVideos",
    "NSPrivacyCollectedDataTypeHealth",
    "NSPrivacyCollectedDataTypeProductInteraction",
    "NSPrivacyCollectedDataTypeCrashData",
    "NSPrivacyCollectedDataTypePerformanceData",
]


def write_plist(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        plistlib.dump(value, file)


def privacy_manifest(data_types: list[str] | None = None, tracking: bool = False) -> dict:
    return {
        "NSPrivacyAccessedAPITypes": [],
        "NSPrivacyTracking": tracking,
        "NSPrivacyTrackingDomains": ["tracker.example"] if tracking else [],
        "NSPrivacyCollectedDataTypes": [
            {
                "NSPrivacyCollectedDataType": data_type,
                "NSPrivacyCollectedDataTypeLinked": data_type
                not in {
                    "NSPrivacyCollectedDataTypeCrashData",
                    "NSPrivacyCollectedDataTypePerformanceData",
                },
                "NSPrivacyCollectedDataTypeTracking": False,
                "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
            }
            for data_type in (data_types or PRIVACY_DATA_TYPES)
        ],
    }


def write_app(root: Path, name: str, sdk: str, complete: bool = True) -> Path:
    app = root / name
    app.mkdir(parents=True)
    write_plist(
        app / "Info.plist",
        {
            "CFBundleIdentifier": "com.mewpow.xiaonaiping" if complete else "com.example.bad",
            "DTPlatformVersion": "26.5" if complete else "18.5",
            "DTSDKName": sdk if complete else sdk.replace("26.5", "18.5"),
            "XNPAPIBaseURL": "https://api.mewpow.com/xiaonaiping",
            "NSSupportsLiveActivities": True,
        },
    )
    if complete:
        write_plist(app / "PrivacyInfo.xcprivacy", privacy_manifest())
        (app / "PlugIns/XiaoNaiPingWidgets.appex").mkdir(parents=True)
    return app


class IOS265BuildProofTest(unittest.TestCase):
    def run_checker(self, root: Path, simulator_app: Path, device_app: Path, simulator_log: Path) -> dict:
        output = root / "Backend/proof/ios-265-build.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(root),
                "--simulator-app",
                str(simulator_app),
                "--device-app",
                str(device_app),
                "--simulator-log",
                str(simulator_log),
                "--output",
                str(output),
                "--allow-incomplete",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("iOS 26.5 build proof", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_complete_ios_265_artifacts_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            simulator_app = write_app(root, "sim/XiaoNaiPing.app", "iphonesimulator26.5")
            device_app = write_app(root, "device/XiaoNaiPing.app", "iphoneos26.5")
            simulator_log = root / "Backend/proof/xcodebuild-release-ios265.log"
            simulator_log.parent.mkdir(parents=True)
            simulator_log.write_text("iphonesimulator26.5\n** BUILD SUCCEEDED **\n", encoding="utf-8")

            report = self.run_checker(root, simulator_app, device_app, simulator_log)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_old_runtime_and_missing_bundle_assets_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            simulator_app = write_app(root, "sim/XiaoNaiPing.app", "iphonesimulator26.5", complete=False)
            device_app = write_app(root, "device/XiaoNaiPing.app", "iphoneos26.5", complete=False)
            simulator_log = root / "Backend/proof/xcodebuild-release-ios265.log"
            simulator_log.parent.mkdir(parents=True)
            simulator_log.write_text("iphonesimulator18.5\n** BUILD SUCCEEDED **\n", encoding="utf-8")

            report = self.run_checker(root, simulator_app, device_app, simulator_log)

            self.assertFalse(report["passed"])
            self.assertIn("simulatorBuiltWithIOS265", report["failedRequiredChecks"])
            self.assertIn("deviceBuiltWithIOS265", report["failedRequiredChecks"])
            self.assertIn("simulatorBundleIdentifierMatches", report["failedRequiredChecks"])
            self.assertIn("devicePrivacyManifestBundled", report["failedRequiredChecks"])
            self.assertIn("simulatorBuildLogSucceeded", report["failedRequiredChecks"])
            self.assertIn("simulatorBuildLogIOS265Only", report["failedRequiredChecks"])

    def test_successful_log_with_mixed_sdk_markers_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            simulator_app = write_app(root, "sim/XiaoNaiPing.app", "iphonesimulator26.5")
            device_app = write_app(root, "device/XiaoNaiPing.app", "iphoneos26.5")
            simulator_log = root / "Backend/proof/xcodebuild-release-ios265.log"
            simulator_log.parent.mkdir(parents=True)
            simulator_log.write_text(
                "iphonesimulator26.5\n"
                "iphonesimulator18.5\n"
                "destination OS=27.0\n"
                "** BUILD SUCCEEDED **\n",
                encoding="utf-8",
            )

            report = self.run_checker(root, simulator_app, device_app, simulator_log)

            self.assertFalse(report["passed"])
            self.assertNotIn("simulatorBuildLogSucceeded", report["failedRequiredChecks"])
            self.assertIn("simulatorBuildLogIOS265Only", report["failedRequiredChecks"])

    def test_privacy_manifest_tracking_and_data_type_mismatch_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            simulator_app = write_app(root, "sim/XiaoNaiPing.app", "iphonesimulator26.5")
            device_app = write_app(root, "device/XiaoNaiPing.app", "iphoneos26.5")
            write_plist(
                simulator_app / "PrivacyInfo.xcprivacy",
                privacy_manifest(data_types=["NSPrivacyCollectedDataTypeUserID"], tracking=True),
            )
            simulator_log = root / "Backend/proof/xcodebuild-release-ios265.log"
            simulator_log.parent.mkdir(parents=True)
            simulator_log.write_text("iphonesimulator26.5\n** BUILD SUCCEEDED **\n", encoding="utf-8")

            report = self.run_checker(root, simulator_app, device_app, simulator_log)

            self.assertFalse(report["passed"])
            self.assertIn("simulatorPrivacyManifestTrackingDisabled", report["failedRequiredChecks"])
            self.assertIn("simulatorPrivacyManifestDataTypesAligned", report["failedRequiredChecks"])
            self.assertNotIn("devicePrivacyManifestDataTypesAligned", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
