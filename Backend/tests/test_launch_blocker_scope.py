from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_launch_blocker_scope.py"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def write_known_blockers(root: Path, extra_production_blockers: list[str] | None = None) -> None:
    production_blockers = [
        "deploymentProofCurrent",
        "productionSecretConfigured",
        "productionDataDirConfigured",
        "mysqlDatabaseSelected",
        "mysqlDatabaseEnvPresent",
        "huaweiObsSelected",
        "huaweiObsEnvPresent",
        "phoneLoginProviderConfigured",
        "wechatLoginProviderConfigured",
        "privateOperationsDashboardConfigured",
        "publicInternalDashboardBlocked",
        "xiaonaipingProductionNamespaceConfigured",
        "storageBackendProofPassed",
        "storageBackendProofCurrent",
        "iosReleaseReadinessProofPassed",
        "iosAppBundleProofPassed",
        "testFlightRegressionPlanProofPassed",
        "appStoreAssetsProofPassed",
        "authProvidersProofPassed",
        "appStoreManualEvidenceReady",
    ]
    production_blockers.extend(extra_production_blockers or [])
    write_json(root / "Backend/proof/production-readiness.json", {"failedRequiredChecks": production_blockers})
    write_json(
        root / "Backend/proof/app-store-evidence.json",
        {
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
            ]
        },
    )
    write_json(root / "Backend/proof/auth-providers.json", {"failedRequiredChecks": ["smsProviderConfigured", "wechatProviderConfigured"]})
    write_json(root / "Backend/proof/ios-release-readiness.json", {"failedRequiredChecks": ["weChatReleaseBuildSettingsConfigured"]})
    write_json(root / "Backend/proof/ios-app-bundle.json", {"failedRequiredChecks": ["weChatNativeConfigPresent", "weChatURLTypePresent"]})


class LaunchBlockerScopeTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/launch-blocker-scope.json"
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

    def test_known_blockers_pass_scope_check(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_known_blockers(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["unexpectedBlockers"], {})

    def test_unexpected_production_blocker_fails_scope_check(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_known_blockers(root, ["unexpectedNewGate"])

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertEqual(
                report["unexpectedBlockers"],
                {"productionReadiness": ["unexpectedNewGate"]},
            )


if __name__ == "__main__":
    unittest.main()
