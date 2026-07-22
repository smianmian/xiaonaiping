from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_launch_objective_audit.py"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def proof(passed: bool = True, checks: dict | None = None, failed: list[str] | None = None) -> dict:
    return {
        "passed": passed,
        "failedRequiredChecks": [] if passed else failed or ["failedCheck"],
        "checks": checks or {},
    }


def check(value: bool = True) -> dict:
    return {"passed": value}


def write_green_proofs(root: Path) -> None:
    write_json(root / "Backend/proof/production-readiness.json", {"ready": True, "failedRequiredChecks": [], "checks": {}})
    write_json(
        root / "Backend/proof/ios-265-build.json",
        proof(
            checks={
                "simulatorBundleIdentifierMatches": check(),
                "deviceBundleIdentifierMatches": check(),
                "simulatorPrivacyManifestBundled": check(),
                "devicePrivacyManifestBundled": check(),
                "simulatorPrivacyManifestTrackingDisabled": check(),
                "devicePrivacyManifestTrackingDisabled": check(),
                "simulatorPrivacyManifestDataTypesAligned": check(),
                "devicePrivacyManifestDataTypesAligned": check(),
            }
        ),
    )
    write_json(
        root / "Backend/proof/ios-release-readiness.json",
        proof(
            checks={
                "weChatReleaseBuildSettingsConfigured": check(),
                "privacyManifestPresent": check(),
                "privacyManifestTrackingDisabled": check(),
                "privacyManifestMatchesPrivacyLabel": check(),
            }
        ),
    )
    write_json(
        root / "Backend/proof/ios-app-bundle.json",
        proof(
            checks={
                "bundleIdentifierMatches": check(),
                "weChatNativeConfigPresent": check(),
                "weChatURLTypePresent": check(),
            }
        ),
    )
    for name in [
        "auth-providers",
        "ios265-device-availability",
        "app-store-assets",
        "app-store-connect-materials",
        "app-store-connect-evidence-materials",
        "app-store-submission-packet",
        "launch-day-rollover",
        "launch-operator-workbench",
        "mainland-filing-materials",
        "signed-archive-testflight-materials",
        "provider-evidence-materials",
        "testflight-precheck",
        "review-notes",
        "remote-api",
        "public-pages",
        "legal-drafts",
        "diagnostics-redaction",
        "universal-links",
        "wechat-client-configuration",
        "storage-backend",
    ]:
        write_json(root / f"Backend/proof/{name}.json", proof())
    write_json(
        root / "Backend/proof/testflight-regression-plan.json",
        proof(checks={"realDeviceEvidenceGateSeparated": check(), "reviewAccountRedactedProofPresent": check()}),
    )
    write_json(
        root / "Backend/proof/app-store-evidence.json",
        {
            "ready": True,
            "missingEvidence": [],
            "checks": {"realDeviceRegression": check(), "reviewTestAccount": check()},
        },
    )


class LaunchObjectiveAuditTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/launch-objective-audit.json"
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
        self.assertIn("launch objective audit", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_green_objective_audit_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)

            report = self.run_checker(root)

            self.assertTrue(report["ready"])
            self.assertEqual(report["failedRequiredChecks"], [])
            self.assertIn("iOS 26.5 screenshot provenance", report["checks"]["appStoreAssetsReady"]["evidence"])

    def test_wechat_manual_evidence_and_real_device_block_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(root / "Backend/proof/production-readiness.json", {"ready": False, "failedRequiredChecks": ["wechatLoginProviderConfigured"]})
            write_json(
                root / "Backend/proof/ios-release-readiness.json",
                proof(False, checks={"weChatReleaseBuildSettingsConfigured": check(False)}, failed=["weChatReleaseBuildSettingsConfigured"]),
            )
            write_json(
                root / "Backend/proof/ios-app-bundle.json",
                proof(
                    False,
                    checks={
                        "bundleIdentifierMatches": check(),
                        "weChatNativeConfigPresent": check(False),
                        "weChatURLTypePresent": check(False),
                    },
                    failed=["weChatNativeConfigPresent", "weChatURLTypePresent"],
                ),
            )
            write_json(root / "Backend/proof/auth-providers.json", proof(False, failed=["wechatProviderConfigured"]))
            write_json(
                root / "Backend/proof/app-store-evidence.json",
                {
                    "ready": False,
                    "missingEvidence": ["wechatOpenPlatform", "realDeviceRegression"],
                    "checks": {"realDeviceRegression": check(False)},
                },
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("weChatConfigurationGreen", report["failedRequiredChecks"])
            self.assertIn("realDeviceRegressionEvidenceReady", report["failedRequiredChecks"])
            self.assertIn("appStoreManualEvidenceReady", report["failedRequiredChecks"])
            self.assertIn("productionReadinessGreen", report["failedRequiredChecks"])

    def test_app_store_assets_block_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(root / "Backend/proof/app-store-assets.json", proof(False, failed=["finalScreenshotsNotBlank"]))

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("appStoreAssetsReady", report["failedRequiredChecks"])

    def test_ios_265_privacy_manifest_content_blocks_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/ios-265-build.json",
                proof(
                    checks={
                        "simulatorBundleIdentifierMatches": check(),
                        "deviceBundleIdentifierMatches": check(),
                        "simulatorPrivacyManifestBundled": check(),
                        "devicePrivacyManifestBundled": check(),
                        "simulatorPrivacyManifestTrackingDisabled": check(False),
                        "devicePrivacyManifestTrackingDisabled": check(),
                        "simulatorPrivacyManifestDataTypesAligned": check(False),
                        "devicePrivacyManifestDataTypesAligned": check(),
                    },
                    failed=[
                        "simulatorPrivacyManifestTrackingDisabled",
                        "simulatorPrivacyManifestDataTypesAligned",
                    ],
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("privacyManifestGreen", report["failedRequiredChecks"])

    def test_ios_265_physical_device_availability_blocks_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/ios265-device-availability.json",
                proof(False, failed=["deviceListReadable", "physicalIphonesListed"]),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("ios265PhysicalDeviceAvailabilityReady", report["failedRequiredChecks"])

    def test_app_store_connect_evidence_materials_block_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(root / "Backend/proof/app-store-connect-evidence-materials.json", proof(False, failed=["privacyLabelJsonMatchesEvidenceChecklist"]))

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("appStoreConnectEvidenceMaterialsReady", report["failedRequiredChecks"])

    def test_launch_day_rollover_blocks_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/launch-day-rollover.json",
                proof(False, failed=["sameDayEvidenceRefreshRequired"]),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("launchDayRolloverReady", report["failedRequiredChecks"])
            self.assertIn("sameDayEvidenceRefreshRequired", report["checks"]["launchDayRolloverReady"]["evidence"])

    def test_launch_operator_workbench_blocks_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/launch-operator-workbench.json",
                proof(False, failed=["appStoreConnectDraftFieldsPresent"]),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("launchOperatorWorkbenchReady", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectDraftFieldsPresent", report["checks"]["launchOperatorWorkbenchReady"]["evidence"])

    def test_testflight_regression_plan_blocks_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/testflight-regression-plan.json",
                proof(False, checks={"realDeviceEvidenceGateSeparated": check(False)}, failed=["realDeviceEvidenceGateSeparated"]),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("testFlightRegressionPlanReadyButNotEvidence", report["failedRequiredChecks"])

    def test_mainland_filing_materials_block_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/mainland-filing-materials.json",
                proof(False, failed=["evidenceArchiveFilenamesMatchGate"]),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("mainlandFilingMaterialsReady", report["failedRequiredChecks"])

    def test_signed_archive_testflight_materials_block_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/signed-archive-testflight-materials.json",
                proof(False, failed=["preSubmitCommandsIncludeArchiveTestFlightGate"]),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("signedArchiveTestFlightMaterialsReady", report["failedRequiredChecks"])

    def test_provider_evidence_materials_block_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/provider-evidence-materials.json",
                proof(False, failed=["doesNotPretendProviderEvidenceCompleteBeforeFiles"]),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("providerEvidenceMaterialsReady", report["failedRequiredChecks"])

    def test_review_test_account_evidence_blocks_goal_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_green_proofs(root)
            write_json(
                root / "Backend/proof/app-store-evidence.json",
                {
                    "ready": True,
                    "missingEvidence": [],
                    "checks": {"realDeviceRegression": check(), "reviewTestAccount": check(False)},
                },
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("reviewTestAccountEvidenceReady", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
