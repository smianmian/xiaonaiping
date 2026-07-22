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


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_production_refresh_packet() -> dict:
    return json.loads(
        (SCRIPT.parents[2] / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json").read_text(
            encoding="utf-8",
        ),
    )


def write_proofs(root: Path) -> None:
    write_json(
        root / "Backend/proof/launch-objective-audit.json",
        {
            "ready": False,
            "failedRequiredChecks": [
                "weChatConfigurationGreen",
                "ios265PhysicalDeviceAvailabilityReady",
                "testFlightRegressionPlanReadyButNotEvidence",
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
                "ageRatingResult",
                "signedArchive",
                "testFlight",
                "appleDeveloperAccountAccess",
                "smsProvider",
                "wechatOpenPlatform",
                "wechatUniversalLinkAasa",
                "huaweiObsPolicy",
                "finalScreenshots",
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
                    "evidence": "/repo/Backend/proof/xcodebuild-release-ios265-20260629.log",
                },
                "deviceBuildLogSucceeded": {
                    "passed": True,
                    "evidence": "/repo/Backend/proof/xcodebuild-release-ios265-20260629-device-current.log",
                },
            },
        },
    )
    write_json(
        root / "Backend/proof/production-readiness.json",
        {
            "ready": False,
            "failedRequiredChecks": [
                "deploymentProofCurrent",
                "storageBackendProofCurrent",
                "testFlightRegressionPlanProofPassed",
            ],
        },
    )
    write_json(
        root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json",
        valid_production_refresh_packet(),
    )
    write_text(
        root / "Backend/proof/auth-provider-targeted-tests-20260630.log",
        """
test_invalid_signature_is_rejected (Backend.tests.test_aliyun_sms_adapter.AliyunSMSAdapterTest) ... ok
test_deployment_proof_can_pass_offline_provider_gate (Backend.tests.test_auth_provider_verification.AuthProviderVerificationTest) ... ok
test_live_check_accepts_production_rejection_of_debug_wechat_code (Backend.tests.test_auth_provider_verification.AuthProviderVerificationTest) ... ok
test_sample_wechat_app_id_fails_provider_gate (Backend.tests.test_auth_provider_verification.AuthProviderVerificationTest) ... ok

----------------------------------------------------------------------
Ran 8 tests in 1.902s

OK
""".lstrip(),
    )


def complete_packet_text() -> str:
    return """
# Launch Blocker Action Packet

Current objective checks: weChatConfigurationGreen, ios265PhysicalDeviceAvailabilityReady,
testFlightRegressionPlanReadyButNotEvidence, realDeviceRegressionEvidenceReady,
appStoreManualEvidenceReady, productionReadinessGreen.

Files: 01-company-account, 02-mainland-availability, 03-app-filing, 04-privacy-label,
17-age-rating-result, 05-signed-archive, 06-testflight, 07-sms-provider,
08-wechat-open-platform, 08b-wechat-universal-link-aasa, wechatUniversalLinkAasa,
AppleDeveloper/16-account-roles-access, appleDeveloperAccountAccess, 09-obs-policy,
10-final-screenshots/UPLOAD_PROVENANCE.json,
finalScreenshotsUploadProvenancePresent, 12-real-device-regression.md.

本机测试只使用 iOS 26.5。iOS 27.0 不能作为本机测试环境，模拟器不能替代真机证据。

WeChat needs wx + 16 hex. URL Scheme equal to AppID. Universal Link is bound in
Open Platform. AppSecret stays server side. Bundle ID is com.mewpow.xiaonaiping.
Evidence goes to 08-wechat-open-platform.

Real device evidence must be TestFlight or Xcode 签名真机包 in
12-real-device-regression.md, covering RD-01 through RD-24.

Final screenshots require 10-final-screenshots/UPLOAD_PROVENANCE.json and
finalScreenshotsUploadProvenancePresent before app-store-assets.json can pass.

Production freshness blockers: deploymentProofCurrent requires 当天部署 proof
from XNP_DEPLOY_HOST and Backend/deploy/deploy-huawei-baota.sh, then collect_deployment_proof.py.
storageBackendProofCurrent requires 当天 OBS/存储 proof
from verify_storage_backend.py.
Structured refresh packet: Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json.
It is 不是部署证据, 不是 production readiness, and 不能作为提交许可.

TestFlight regression prerequisite: testFlightRegressionPlanProofPassed needs
ios265-device-availability.json from devicectl showing physical iPhone on iOS 26.5.
iOS 27.0 or simulator evidence 不能替代 this prerequisite.

Commands:
Backend/scripts/run_launch_readiness.sh
--ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260629.log
--ios-device-log Backend/proof/xcodebuild-release-ios265-20260629-device-current.log
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete

Auth provider targeted proof:
Backend/proof/auth-provider-targeted-tests-20260630.log
8 个 targeted tests 通过, covering 短信 webhook adapter, 签名校验,
auth provider 配置门禁, and debug 微信拒绝路径.
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
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(complete_packet_text(), encoding="utf-8")

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_stale_action_packet_date_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260629.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(complete_packet_text(), encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("actionPacketDateMatches", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["actionPacketDateMatches"]["expected"],
                "LAUNCH_BLOCKER_ACTION_PACKET_20260630.md",
            )

    def test_missing_current_evidence_filename_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(complete_packet_text().replace("07-sms-provider,", ""), encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("missingEvidenceFilenamesCovered", report["failedRequiredChecks"])
            self.assertEqual(report["checks"]["missingEvidenceFilenamesCovered"]["missingMarkers"], ["07-sms-provider"])

    def test_missing_wechat_universal_link_aasa_evidence_filename_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(
                complete_packet_text()
                .replace("08b-wechat-universal-link-aasa, ", "")
                .replace("wechatUniversalLinkAasa,\n", ""),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("missingEvidenceFilenamesCovered", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["missingEvidenceFilenamesCovered"]["missingMarkers"],
                ["08b-wechat-universal-link-aasa", "wechatUniversalLinkAasa"],
            )

    def test_missing_final_screenshot_upload_provenance_marker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(
                complete_packet_text()
                .replace("10-final-screenshots/UPLOAD_PROVENANCE.json", "10-final-screenshots/PROVENANCE.json")
                .replace("finalScreenshotsUploadProvenancePresent", "finalScreenshotsIOS265ProvenancePresent"),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("missingEvidenceFilenamesCovered", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["missingEvidenceFilenamesCovered"]["missingMarkers"],
                ["10-final-screenshots/UPLOAD_PROVENANCE.json", "finalScreenshotsUploadProvenancePresent"],
            )

    def test_missing_current_ios265_build_logs_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(
                complete_packet_text()
                .replace("xcodebuild-release-ios265-20260629.log", "xcodebuild-release-ios265-20260626.log")
                .replace("xcodebuild-release-ios265-20260629-device-current.log", "xcodebuild-release-ios265-20260626-device-current.log"),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("rerunCommandsUseCurrentIOS265BuildLogs", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["rerunCommandsUseCurrentIOS265BuildLogs"]["missingMarkers"],
                [
                    "xcodebuild-release-ios265-20260629.log",
                    "xcodebuild-release-ios265-20260629-device-current.log",
                ],
            )

    def test_stale_auth_provider_targeted_log_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(
                complete_packet_text().replace(
                    "auth-provider-targeted-tests-20260630.log",
                    "auth-provider-targeted-tests-20260629.log",
                ),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("authProviderTargetedTestLogCurrent", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["authProviderTargetedTestLogCurrent"]["staleMarkers"],
                ["auth-provider-targeted-tests-20260629.log"],
            )

    def test_missing_auth_provider_targeted_log_content_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            write_text(root / "Backend/proof/auth-provider-targeted-tests-20260630.log", "Ran 7 tests\nFAILED\n")
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(complete_packet_text(), encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("authProviderTargetedTestLogPassed", report["failedRequiredChecks"])
            missing = report["checks"]["authProviderTargetedTestLogPassed"]["missingMarkers"]
            self.assertIn("Ran 8 tests", missing)
            self.assertIn("OK", missing)

    def test_missing_production_freshness_actions_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(
                complete_packet_text()
                .replace(
                    "deploymentProofCurrent requires 当天部署 proof\n"
                    "from XNP_DEPLOY_HOST and Backend/deploy/deploy-huawei-baota.sh, then collect_deployment_proof.py.\n",
                    "",
                )
                .replace("storageBackendProofCurrent requires 当天 OBS/存储 proof\nfrom verify_storage_backend.py.\n", ""),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionFreshnessBlockersCovered", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["productionFreshnessBlockersCovered"]["missingMarkers"],
                [
                    "deploymentProofCurrent",
                    "当天部署 proof",
                    "XNP_DEPLOY_HOST",
                    "deploy-huawei-baota.sh",
                    "collect_deployment_proof.py",
                    "storageBackendProofCurrent",
                    "当天 OBS/存储 proof",
                    "verify_storage_backend.py",
                ],
            )

    def test_missing_testflight_prerequisite_actions_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(
                complete_packet_text().replace(
                    "TestFlight regression prerequisite: testFlightRegressionPlanProofPassed needs\n"
                    "ios265-device-availability.json from devicectl showing physical iPhone on iOS 26.5.\n"
                    "iOS 27.0 or simulator evidence 不能替代 this prerequisite.\n\n",
                    "",
                ),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("testflightRegressionPrerequisiteBlockersCovered", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["testflightRegressionPrerequisiteBlockersCovered"]["missingMarkers"],
                [
                    "testFlightRegressionPlanProofPassed",
                    "ios265-device-availability.json",
                    "devicectl",
                    "physical iPhone",
                ],
            )

    def test_bad_production_refresh_packet_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(complete_packet_text(), encoding="utf-8")
            bad_refresh_packet = valid_production_refresh_packet()
            bad_refresh_packet.pop("canSubmitFromThisPacket")
            bad_refresh_packet["targetProofFiles"].pop("productionReadinessCurrent")
            bad_refresh_packet["refreshSequence"] = [
                item
                for item in bad_refresh_packet["refreshSequence"]
                if item["step"] != "syncStableAliasesAfterGreen"
            ]
            bad_refresh_packet["stopConditions"] = [
                item
                for item in bad_refresh_packet["stopConditions"]
                if item["id"] != "productionReadinessStillRed"
            ]
            bad_refresh_packet["completionRule"] = bad_refresh_packet["completionRule"].replace(
                "not submission permission",
                "",
            )
            write_json(
                root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json",
                bad_refresh_packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionProofRefreshPacketValid", report["failedRequiredChecks"])
            failures = "\n".join(report["checks"]["productionProofRefreshPacketValid"]["failures"])
            self.assertIn("canSubmitFromThisPacket must be false", failures)
            self.assertIn("targetProofFiles.productionReadinessCurrent", failures)
            self.assertIn("refreshSequence order must be", failures)
            self.assertIn("stopConditions missing productionReadinessStillRed", failures)
            self.assertIn("completionRule missing not submission permission", failures)

    def test_production_refresh_packet_uses_real_secret_key_name(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_proofs(root)
            packet = root / "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260630.md"
            packet.parent.mkdir(parents=True, exist_ok=True)
            packet.write_text(complete_packet_text(), encoding="utf-8")
            stale_refresh_packet = valid_production_refresh_packet()
            stale_refresh_packet["refreshSequence"][0]["requires"] = [
                item.replace("XNP_SECRET_KEY", "XNP_PRODUCTION_SECRET")
                for item in stale_refresh_packet["refreshSequence"][0]["requires"]
            ]
            stale_refresh_packet["refreshSequence"][0]["redaction"] = stale_refresh_packet["refreshSequence"][0][
                "redaction"
            ].replace("XNP_SECRET_KEY", "XNP_PRODUCTION_SECRET")
            stale_refresh_packet["stopConditions"] = [
                {
                    **item,
                    "condition": item["condition"].replace("XNP_SECRET_KEY", "XNP_PRODUCTION_SECRET"),
                }
                if item["id"] == "productionSecretOrDatabaseMissing"
                else item
                for item in stale_refresh_packet["stopConditions"]
            ]
            write_json(
                root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json",
                stale_refresh_packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionProofRefreshPacketValid", report["failedRequiredChecks"])
            failures = "\n".join(report["checks"]["productionProofRefreshPacketValid"]["failures"])
            self.assertIn("refreshSequence missing XNP_SECRET_KEY", failures)
            self.assertIn("stopConditions.productionSecretOrDatabaseMissing missing XNP_SECRET_KEY", failures)


if __name__ == "__main__":
    unittest.main()
