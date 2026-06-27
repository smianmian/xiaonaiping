from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_launch_blocker_action_packet.py"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def write_proofs(root: Path) -> None:
    write_json(
        root / "Backend/proof/launch-objective-audit.json",
        {
            "ready": False,
            "failedRequiredChecks": [
                "weChatConfigurationGreen",
                "realDeviceRegressionEvidenceReady",
                "appStoreManualEvidenceReady",
                "productionReadinessGreen",
            ],
        },
    )
    write_json(
        root / "Backend/proof/app-store-evidence.json",
        {
            "ready": False,
            "missingEvidence": [
                "companyAccount",
                "mainlandAvailability",
                "mainlandFiling",
                "privacyLabel",
                "signedArchive",
                "testFlight",
                "smsProvider",
                "wechatOpenPlatform",
                "huaweiObsPolicy",
                "realDeviceRegression",
            ],
        },
    )
    write_json(
        root / "Backend/proof/ios-265-build.json",
        {
            "passed": True,
            "checks": {
                "simulatorBuildLogSucceeded": {
                    "passed": True,
                    "evidence": "/repo/Backend/proof/xcodebuild-release-ios265-20260627-sim-current.log",
                },
                "deviceBuildLogSucceeded": {
                    "passed": True,
                    "evidence": "/repo/Backend/proof/xcodebuild-release-ios265-20260627-device-current.log",
                },
            },
        },
    )


def complete_packet_text() -> str:
    return """
# Launch Blocker Action Packet

Current objective checks: weChatConfigurationGreen, realDeviceRegressionEvidenceReady,
appStoreManualEvidenceReady, productionReadinessGreen.

Files: 01-company-account, 02-mainland-availability, 03-app-filing, 04-privacy-label,
05-signed-archive, 06-testflight, 07-sms-provider, 08-wechat-open-platform,
09-obs-policy, 12-real-device-regression.md.

本机测试只使用 iOS 26.5。iOS 27.0 不能作为本机测试环境，模拟器不能替代真机证据。

WeChat needs wx + 16 hex. URL Scheme equal to AppID. Universal Link is bound in
Open Platform. AppSecret stays server side. Bundle ID is com.mewpow.xiaonaiping.
Evidence goes to 08-wechat-open-platform.

Real device evidence must be TestFlight or Xcode 签名真机包 in
12-real-device-regression.md, covering RD-01 through RD-24.

Commands:
Backend/scripts/run_launch_readiness.sh
--ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260627-sim-current.log
--ios-device-log Backend/proof/xcodebuild-release-ios265-20260627-device-current.log
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete
"""


class LaunchBlockerActionPacketTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/launch-blocker-action-packet.json"
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

    def test_complete_action_packet_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260626.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(complete_packet_text(), encoding="utf-8")

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_current_evidence_filename_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260626.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(complete_packet_text().replace("07-sms-provider, ", ""), encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("missingEvidenceFilenamesCovered", report["failedRequiredChecks"])
            self.assertEqual(report["checks"]["missingEvidenceFilenamesCovered"]["missingMarkers"], ["07-sms-provider"])

    def test_missing_current_ios265_build_logs_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260626.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(
                complete_packet_text()
                .replace("20260627-sim-current.log", "20260626-sim-current.log")
                .replace("20260627-device-current.log", "20260626-device-current.log"),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("rerunCommandsUseCurrentIOS265BuildLogs", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["rerunCommandsUseCurrentIOS265BuildLogs"]["missingMarkers"],
                [
                    "xcodebuild-release-ios265-20260627-sim-current.log",
                    "xcodebuild-release-ios265-20260627-device-current.log",
                ],
            )


if __name__ == "__main__":
    unittest.main()
