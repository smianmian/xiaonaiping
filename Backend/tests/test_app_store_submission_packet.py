from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_app_store_submission_packet.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_packet() -> str:
    return """
# APP_STORE_SUBMISSION_PACKET.md

## Official Apple Checkpoints

1. App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
2. App privacy details: https://developer.apple.com/help/app-store-connect/manage-app-privacy/overview-of-app-privacy-details/
3. Privacy nutrition label fields: https://developer.apple.com/app-store/app-privacy-details/
4. Screenshot specifications: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications
5. Age rating: https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating
6. Regulated medical device declaration: https://developer.apple.com/help/app-store-connect/manage-app-information/declare-regulated-medical-device-status

## App Information

| Field | Value |
|---|---|
| Bundle ID | `com.mewpow.xiaonaiping` |
| App name | 小奶瓶 |
| Category | Lifestyle |
| Price | Free |
| Regions | China mainland first |
| WeChat login | WeChat authorization |

## Review Notes

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒。桌面/锁屏小组件只读展示今日摘要。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit，不提供压力评估或医疗诊断。正式提交包不得依赖 debug code。

## Do Not Submit Or Screenshot

Do not include real baby photos, real phone numbers, recovery keys, tokens, debug login codes, 127.0.0.1, localhost, medical diagnosis, doctor replacement, WeChat login before Open Platform proof, HealthKit, stress detection, or medical interpretation.

## Privacy Label Fill Source

1. Docs/08_Release/APP_STORE_PRIVACY_LABEL.json
2. Docs/07_PrivacySecurity/SDK_DATA_INVENTORY.md
3. Docs/07_PrivacySecurity/PRIVACY_REVIEW.md
4. App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy

## Export Compliance

Uses standard system/network encryption only and does not implement custom cryptography, VPN, DRM, or end-to-end encrypted messaging.

## Age Rating And Medical Device Answers

Expected age rating is 4+. Do not select Kids. Regulated Medical Device: No. 小奶瓶 is not a medical device, does not provide diagnosis, does not provide treatment, and does not predict disease. It does not use HealthKit, sensors, hospital records, stress detection, or medical interpretation.

## Release Bundle Verification

Use Backend/proof/ios-265-build.json and Backend/proof/ios-app-bundle.json. Current iOS 26.5 proof covers iphonesimulator26.5, iphoneos26.5, Bundle ID com.mewpow.xiaonaiping, XNPAPIBaseURL=https://api.mewpow.com/xiaonaiping, and PrivacyInfo.xcprivacy. The app-bundle proof is still blocked until real WeChat AppID and `wx...` URL Scheme are configured.

Current proof files: Backend/proof/xcodebuild-debug-ios265-20260627.log, Backend/proof/xcodebuild-release-ios265-20260627.log, Backend/proof/ios-app-bundle-20260627T-current-ios265.json. Active iOS bundle blockers remain weChatNativeConfigPresent and weChatURLTypePresent.

## Current 2026-06-27 Gate Status

Current submit gate uses Backend/proof/app-store-connect-materials-20260627-current.json, Backend/proof/app-store-evidence-20260627T-current.json, Backend/proof/production-readiness-20260627T-current.json, Backend/proof/auth-providers-20260627T-current.json, and Backend/proof/ios-app-bundle-20260627T-current-ios265.json. The current cross-app result is canSubmit=false. Active blockers include wechatProviderConfigured, weChatNativeConfigPresent, weChatURLTypePresent, and appStoreManualEvidenceReady.

## Screenshot Status

Final screenshots require TestFlight or signed-device final screenshots. No real baby photos. Copy review for medical and privacy claims.

## Manual Evidence Checklist

Use Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260627.md and the manualEvidenceChecklist gate before submission. The checklist must cover RD-01 through RD-24 on iOS 26.5, including Live Activity, 小组件, and the review boundary phrase 不生成健康建议、压力提醒、喂养建议或医疗判断.

## Pre-Submit Commands

```bash
Backend/scripts/run_launch_readiness.sh
python3 Backend/scripts/check_ios_265_build_proof.py
python3 Backend/scripts/check_ios_app_bundle.py
python3 Backend/scripts/check_testflight_precheck.py
python3 Backend/scripts/check_testflight_regression_plan.py
python3 Backend/scripts/check_wechat_client_configuration.py
python3 Backend/scripts/check_app_store_connect_evidence_materials.py
python3 Backend/scripts/check_app_store_evidence.py
python3 Backend/scripts/check_mainland_filing_materials.py
python3 Backend/scripts/check_signed_archive_testflight_materials.py
python3 Backend/scripts/check_provider_evidence_materials.py
python3 Backend/scripts/check_production_readiness.py
python3 Backend/scripts/check_launch_objective_audit.py
python3 Backend/scripts/check_launch_blocker_action_packet.py
```
""".lstrip()


class AppStoreSubmissionPacketTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/app-store-submission-packet.json"
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

    def test_valid_submission_packet_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", valid_packet())

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_official_urls_and_boundaries_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = valid_packet()
            packet = packet.replace("https://developer.apple.com/app-store/review/guidelines/", "")
            packet = packet.replace("不接入 HealthKit", "")
            packet = packet.replace("check_testflight_precheck.py", "")
            packet = packet.replace("does not implement custom cryptography", "")
            packet = packet.replace("Regulated Medical Device: No.", "")
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("officialAppleCheckpointsPresent", report["failedRequiredChecks"])
            self.assertIn("noHealthKit", report["failedRequiredChecks"])
            self.assertIn("preSubmitCommandsComplete", report["failedRequiredChecks"])
            self.assertIn("exportComplianceAnswerPresent", report["failedRequiredChecks"])
            self.assertIn("ageRatingAndMedicalDeviceAnswersPresent", report["failedRequiredChecks"])

    def test_review_notes_require_status_and_advice_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = valid_packet().replace(
                "这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。",
                "",
            )
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("statusDisplayBoundary", report["failedRequiredChecks"])
            self.assertIn("noHealthPressureFeedingAdvice", report["failedRequiredChecks"])

    def test_release_bundle_verification_requires_ios265_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = valid_packet()
            packet = packet.replace("Backend/proof/ios-265-build.json", "")
            packet = packet.replace("iphonesimulator26.5", "iphonesimulator18.5")
            packet = packet.replace("iphoneos26.5", "iphoneos18.5")
            packet = packet.replace(
                "Use  and Backend/proof/ios-app-bundle.json.",
                "Current package scan result from `/tmp/XiaoNaiPing-BundleReuse-Release/Build/Products/Release-iphoneos/XiaoNaiPing.app`.",
            )
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("releaseBundleVerificationUsesIOS265Proofs", report["failedRequiredChecks"])
            evidence = report["checks"]["releaseBundleVerificationUsesIOS265Proofs"]["evidence"]
            self.assertIn("Backend/proof/ios-265-build.json", evidence)
            self.assertIn("XiaoNaiPing-BundleReuse-Release", evidence)

    def test_submission_packet_rejects_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = valid_packet() + "\nXNP_REVIEW_RECOVERY_KEY=secret\nBearer abc.def_123\n13800138000\n"
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("submissionPacketDoesNotExposeSecrets", report["failedRequiredChecks"])
            evidence = report["checks"]["submissionPacketDoesNotExposeSecrets"]["evidence"]
            self.assertIn("recoveryKeyAssignment", evidence)
            self.assertIn("bearerToken", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)


if __name__ == "__main__":
    unittest.main()
