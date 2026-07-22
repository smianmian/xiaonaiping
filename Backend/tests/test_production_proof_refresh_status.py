from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_production_proof_refresh_status.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: dict) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def packet() -> dict:
    return {
        "artifactType": "production-proof-refresh-packet",
        "status": "refresh-plan-not-evidence",
        "date": "2026-06-29",
        "project": "XiaoNaiPing",
        "appName": "小奶瓶",
        "baseUrl": "https://api.mewpow.com/xiaonaiping",
        "targetProofFiles": {
            "deploymentProofCurrent": "Backend/proof/huawei-baota-deploy-20260629T-current.json",
            "authProvidersSmsLiveCurrent": "Backend/proof/auth-providers-sms-live-20260629T-current.json",
            "wechatClientConfigurationCurrent": "Backend/proof/wechat-client-configuration-20260629-current.json",
            "iosReleaseReadinessCurrent": "Backend/proof/ios-release-readiness-20260629T-current-ios265.json",
            "iosAppBundleCurrent": "Backend/proof/ios-app-bundle-20260629T-current-ios265.json",
            "productionReadinessCurrent": "Backend/proof/production-readiness-20260629T-current.json",
            "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
            "stableProductionReadinessAlias": "Backend/proof/production-readiness.json",
        },
    }


def deployment_proof() -> dict:
    return {
        "startedAt": "2026-06-28T17:18:34+00:00",
        "completedAt": "2026-06-28T17:18:34+00:00",
        "containsSecrets": False,
        "privateEnvStatus": {"doesNotExposeValues": True},
        "remainingProductionBlockers": [
            "production SMS webhook provider is not fully configured",
            "WeChat Open Platform AppID/AppSecret are not fully configured",
        ],
    }


def ready_proof() -> dict:
    return {
        "startedAt": "2026-06-29T01:00:00+08:00",
        "completedAt": "2026-06-29T01:00:00+08:00",
        "passed": True,
        "checks": {"ok": {"passed": True, "required": True}},
    }


def incomplete_readiness() -> dict:
    return {
        "startedAt": "2026-06-28T17:20:00+00:00",
        "completedAt": "2026-06-28T17:20:00+00:00",
        "ready": False,
        "failedRequiredChecks": [
            "productionSecretConfigured",
            "authProvidersProofPassed",
            "iosReleaseReadinessProofPassed",
            "iosAppBundleProofPassed",
        ],
        "checks": {},
    }


class ProductionProofRefreshStatusTest(unittest.TestCase):
    def run_checker(self, root: Path, allow_incomplete: bool = True) -> tuple[subprocess.CompletedProcess[str], dict | None]:
        output = root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260629.json"
        command = [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(root),
            "--date",
            "2026-06-29",
            "--output",
            str(output),
        ]
        if allow_incomplete:
            command.append("--allow-incomplete")
        completed = subprocess.run(command, text=True, capture_output=True)
        data = json.loads(output.read_text(encoding="utf-8")) if output.exists() else None
        return completed, data

    def write_base_context(self, root: Path) -> None:
        write_json(root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260629.json", packet())
        write_json(root / "Backend/proof/huawei-baota-deploy-20260629T-current.json", deployment_proof())
        write_json(root / "Backend/proof/production-readiness-20260629T-current.json", incomplete_readiness())
        write_json(root / "Backend/proof/launch-objective-audit.json", incomplete_readiness())
        write_json(root / "Backend/proof/production-readiness.json", incomplete_readiness())

    def test_incomplete_status_records_missing_and_failed_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.write_base_context(root)

            completed, status = self.run_checker(root)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIsNotNone(status)
            assert status is not None
            self.assertFalse(status["stableAliasSyncAllowed"])
            self.assertIn("authProvidersSmsLiveCurrent", status["missingProofs"])
            self.assertIn("wechatClientConfigurationCurrent", status["missingProofs"])
            self.assertIn("iosReleaseReadinessCurrent", status["missingProofs"])
            self.assertIn("iosAppBundleCurrent", status["missingProofs"])
            failed_ids = [item["artifactId"] for item in status["failedProofs"]]
            self.assertIn("deploymentProofCurrent", failed_ids)
            self.assertIn("productionReadinessCurrent", failed_ids)
            self.assertIn("launchObjectiveAudit", failed_ids)
            self.assertIn(
                "xnp.ios.wechat-client",
                [item["id"] for item in status["currentBlockerClosure"]],
            )
            ios_blocker = next(item for item in status["currentBlockerClosure"] if item["id"] == "xnp.ios.wechat-client")
            self.assertIn(
                "python3 Backend/scripts/check_ios_app_bundle.py "
                "--app /tmp/XiaoNaiPing-WeChatClient-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app "
                "--output Backend/proof/ios-app-bundle-20260629T-current-ios265.json",
                ios_blocker["rerunCommands"],
            )
            self.assertIn(
                ". /tmp/xnp-wechat-release.env && "
                "python3 Backend/scripts/check_ios_release_readiness.py "
                "--output Backend/proof/ios-release-readiness-20260629T-current-ios265.json",
                ios_blocker["rerunCommands"],
            )
            self.assertEqual(status["secretScanFailures"], [])
            launch_audit = next(
                item for item in status["proofFileStatuses"] if item["artifactId"] == "launchObjectiveAudit"
            )
            self.assertEqual(launch_audit["target"], "Backend/proof/launch-objective-audit.json")
            self.assertTrue(launch_audit["currentDateStamped"])
            deployment = next(
                item for item in status["proofFileStatuses"] if item["artifactId"] == "deploymentProofCurrent"
            )
            self.assertTrue(deployment["passedOrReadyVerified"])
            self.assertIn("production SMS webhook provider is not fully configured", deployment["failedRequiredChecks"])

    def test_without_allow_incomplete_returns_nonzero_for_red_status(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.write_base_context(root)

            completed, status = self.run_checker(root, allow_incomplete=False)

            self.assertEqual(completed.returncode, 1)
            self.assertIsNotNone(status)
            self.assertIn("production proof refresh status incomplete", completed.stderr)

    def test_secret_scan_blocks_status(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.write_base_context(root)
            write_json(
                root / "Backend/proof/auth-providers-sms-live-20260629T-current.json",
                {"startedAt": "2026-06-29T01:00:00+08:00", "passed": True},
            )
            with (root / "Backend/proof/auth-providers-sms-live-20260629T-current.json").open(
                "a", encoding="utf-8"
            ) as handle:
                handle.write("XNP_SMS_SECRET=should-not-be-recorded\n")

            completed, status = self.run_checker(root)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            assert status is not None
            self.assertEqual(status["secretScanFailures"][0]["artifactId"], "authProvidersSmsLiveCurrent")
            sms_status = next(
                item for item in status["proofFileStatuses"] if item["artifactId"] == "authProvidersSmsLiveCurrent"
            )
            self.assertFalse(sms_status["secretValuesNotRecorded"])
            self.assertIn("smsSecretAssignment", sms_status["secretScanHits"])

    def test_green_current_proofs_allow_stable_alias_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.write_base_context(root)
            write_json(root / "Backend/proof/huawei-baota-deploy-20260629T-current.json", ready_proof())
            write_json(root / "Backend/proof/auth-providers-sms-live-20260629T-current.json", ready_proof())
            write_json(root / "Backend/proof/wechat-client-configuration-20260629-current.json", ready_proof())
            write_json(root / "Backend/proof/ios-release-readiness-20260629T-current-ios265.json", ready_proof())
            write_json(root / "Backend/proof/ios-app-bundle-20260629T-current-ios265.json", ready_proof())
            write_json(root / "Backend/proof/production-readiness-20260629T-current.json", {"ready": True})
            write_json(root / "Backend/proof/launch-objective-audit.json", ready_proof())
            write_json(root / "Backend/proof/production-readiness.json", {"ready": True})

            completed, status = self.run_checker(root, allow_incomplete=False)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            assert status is not None
            self.assertTrue(status["stableAliasSyncAllowed"])
            self.assertEqual(status["missingProofs"], [])
            self.assertEqual(status["failedProofs"], [])


if __name__ == "__main__":
    unittest.main()
