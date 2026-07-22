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

Date: 2026-06-30

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

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒。桌面/锁屏小组件只读展示今日摘要。用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit，不提供压力评估或医疗诊断。正式提交包不得依赖 debug code。

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

Dedicated answer sheet: Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md. Expected age rating is 4+. Do not select Kids. Final answer is subject to App Store Connect 问卷自动计算结果为准. Regulated Medical Device: No. 小奶瓶 is not a medical device, does not provide diagnosis, does not provide treatment, and does not predict disease. It does not use HealthKit, sensors, hospital records, stress detection, or medical interpretation.

## Release Bundle Verification

Use Backend/proof/ios-265-build.json and Backend/proof/ios-app-bundle.json. Current iOS 26.5 proof covers iphonesimulator26.5, iphoneos26.5, Bundle ID com.mewpow.xiaonaiping, XNPAPIBaseURL=https://api.mewpow.com/xiaonaiping, and PrivacyInfo.xcprivacy. The app-bundle proof is still blocked until real WeChat AppID and `wx...` URL Scheme are configured.

Current proof files: Backend/proof/xcodebuild-release-ios265-20260629-stable.log, Backend/proof/xcodebuild-release-ios265-20260629-device-current.log, Backend/proof/ios-app-bundle.json. Active iOS bundle blockers remain weChatNativeConfigPresent and weChatURLTypePresent.

## Current 2026-06-30 Gate Status

Current submit gate uses XiaoNaiPing submit permission from Backend/proof/app-store-connect-materials.json, Backend/proof/app-store-evidence.json, Backend/proof/production-readiness.json, Backend/proof/launch-objective-audit.json, Backend/proof/testflight-regression-plan.json, Backend/proof/provider-evidence-materials.json, Backend/proof/mainland-filing-materials.json, Backend/proof/signed-archive-testflight-materials.json, Backend/proof/auth-providers.json, and Backend/proof/ios-app-bundle.json. Current status is not ready until XiaoNaiPing App Store evidence, production readiness, launch objective audit, TestFlight regression, provider evidence, mainland filing, signed Archive/TestFlight materials, and iOS 26.5 real-device evidence are ready/passed. Active blockers include productionSecretConfigured, productionDataDirConfigured, mysqlDatabaseSelected, mysqlDatabaseEnvPresent, phoneLoginProviderConfigured, wechatLoginProviderConfigured, privateOperationsDashboardConfigured, publicInternalDashboardBlocked, xiaonaipingProductionNamespaceConfigured, testFlightRegressionPlanProofPassed, appStoreAssetsProofPassed, authProvidersProofPassed, weChatNativeConfigPresent, weChatURLTypePresent, and iOS 26.5 real-device evidence.

## Screenshot Status

Final screenshots require TestFlight or signed-device final screenshots. No real baby photos. Copy review for medical and privacy claims.

## Manual Evidence Checklist

Use Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260630.md and the manualEvidenceChecklist gate before submission. The checklist must cover RD-01 through RD-24 on iOS 26.5, including Live Activity, 小组件, and the review boundary phrase 不生成健康建议、压力提醒、喂养建议或医疗判断.

Copy-paste field packet for App Store Connect draft creation: Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260630.md. It mirrors Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260630.md and keeps the same no-submit boundary.

## Pre-Submit Commands

```bash
Backend/scripts/run_launch_readiness.sh \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260629-stable.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260629-device-current.log
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


def valid_age_rating_answers() -> str:
    return """
# 小奶瓶 App Store 年龄分级与医疗器械答案表

日期：2026-06-30

## 官方核对入口

1. https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating
2. https://developer.apple.com/help/app-store-connect/manage-app-information/declare-regulated-medical-device-status
3. Kids Category https://developer.apple.com/app-store/review/guidelines/#kids-category

## 产品事实边界

小奶瓶面向父母和照护者，不面向儿童直接使用。第一版无 IAP、无广告、无第三方分析 SDK、无公开 UGC、无社交、无聊天、无赌博、无成人内容。不接入 HealthKit、传感器、医院系统。用户可以手动顺延下一次提醒，但不根据奶量、月龄、传感器或健康数据自动推算喂养时间。

## App Store Connect 年龄分级问卷口径

预期 4+，最终以 App Store Connect 问卷自动计算结果为准。Age Categories and Override 选择 Not Applicable，不选择 Made for Kids。Health-related records 来自用户主动输入，只用于记录和提醒。

## 受监管医疗器械声明口径

Regulated Medical Device: No. Xiao Nai Ping is not a medical device and does not provide diagnosis, prevention, monitoring, treatment, disease prediction, or professional medical advice. It has no FDA clearance, CE mark, or UKCA status.

## 提交前重检项

功能变化后必须重新复核。
""".lstrip()


def write_valid_materials(root: Path) -> None:
    write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", valid_packet())
    write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())


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
            write_valid_materials(root)

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
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())

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
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("statusDisplayBoundary", report["failedRequiredChecks"])
            self.assertIn("noHealthPressureFeedingAdvice", report["failedRequiredChecks"])

    def test_review_notes_require_exact_feeding_deferral_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = (
                valid_packet()
                .replace(
                    "可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。",
                    "可以手动选择顺延几分钟。",
                )
                .replace("下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。", "")
                .replace("顺延只改变下一次提醒时间，不新增持久化字段；", "")
                .replace("不根据奶量、月龄、传感器或健康数据自动推算喂养时间", "不自动生成喂养建议")
            )
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("manualFeedingReminderDeferral", report["failedRequiredChecks"])
            self.assertIn("feedingReminderDeferralCalculation", report["failedRequiredChecks"])
            self.assertIn("feedingReminderDeferralPersistenceBoundary", report["failedRequiredChecks"])
            self.assertIn("noAutomaticFeedingInference", report["failedRequiredChecks"])

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
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("releaseBundleVerificationUsesIOS265Proofs", report["failedRequiredChecks"])
            evidence = report["checks"]["releaseBundleVerificationUsesIOS265Proofs"]["evidence"]
            self.assertIn("Backend/proof/ios-265-build.json", evidence)
            self.assertIn("XiaoNaiPing-BundleReuse-Release", evidence)

    def test_release_bundle_verification_rejects_stale_build_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = valid_packet()
            packet = packet.replace("xcodebuild-release-ios265-20260629-stable.log", "xcodebuild-release-ios265-20260629.log")
            packet = packet.replace("xcodebuild-release-ios265-20260629-device-current.log", "xcodebuild-release-ios265-20260628-device-current.log")
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("releaseBundleVerificationUsesIOS265Proofs", report["failedRequiredChecks"])
            evidence = report["checks"]["releaseBundleVerificationUsesIOS265Proofs"]["evidence"]
            self.assertIn("xcodebuild-release-ios265-20260629.log", evidence)
            self.assertIn("xcodebuild-release-ios265-20260629-device-current.log", evidence)

    def test_pre_submit_commands_reject_wrong_current_simulator_log(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = valid_packet().replace(
                "xcodebuild-release-ios265-20260629-stable.log",
                "xcodebuild-release-ios265-20260629-sim-current.log",
            )
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("preSubmitCommandsComplete", report["failedRequiredChecks"])
            self.assertIn("releaseBundleVerificationUsesIOS265Proofs", report["failedRequiredChecks"])
            pre_submit_evidence = report["checks"]["preSubmitCommandsComplete"]["evidence"]
            self.assertIn("--ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260629-stable.log", pre_submit_evidence)
            release_evidence = report["checks"]["releaseBundleVerificationUsesIOS265Proofs"]["evidence"]
            self.assertIn("xcodebuild-release-ios265-20260629-sim-current.log", release_evidence)

    def test_submission_packet_rejects_stale_day_materials(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = (
                valid_packet()
                .replace("Date: 2026-06-30", "Date: 2026-06-28")
                .replace("Current 2026-06-30 Gate Status", "Current 2026-06-28 Gate Status")
                .replace("APP_STORE_EVIDENCE_CHECKLIST_20260630.md", "APP_STORE_EVIDENCE_CHECKLIST_20260628.md")
                .replace("APP_STORE_CONNECT_COPY_PASTE_20260630.md", "APP_STORE_CONNECT_COPY_PASTE_20260628.md")
                .replace("APP_STORE_CONNECT_FILL_SHEET_20260630.md", "APP_STORE_CONNECT_FILL_SHEET_20260628.md")
                .replace("APP_STORE_AGE_RATING_ANSWERS_20260630.md", "APP_STORE_AGE_RATING_ANSWERS_20260628.md")
            )
            packet += (
                "\n| Cross-app submission guard | "
                "`/Users/smianmian/Emotion Isle/output/cross-app-submission-readiness-20260628-current.json` "
                "| canSubmit=false | stale guard |\n"
            )
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("submissionPacketUsesCurrentDayMaterials", report["failedRequiredChecks"])
            evidence = report["checks"]["submissionPacketUsesCurrentDayMaterials"]["evidence"]
            self.assertIn("APP_STORE_CONNECT_COPY_PASTE_20260628.md", evidence)
            self.assertIn("cross-app-submission-readiness", evidence)
            self.assertIn("canSubmit=false", evidence)
            self.assertIn("APP_STORE_AGE_RATING_ANSWERS_20260628.md", evidence)

    def test_submission_packet_rejects_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = valid_packet() + "\nXNP_REVIEW_RECOVERY_KEY=secret\nBearer abc.def_123\n13800138000\n"
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", packet)
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", valid_age_rating_answers())

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("submissionPacketDoesNotExposeSecrets", report["failedRequiredChecks"])
            evidence = report["checks"]["submissionPacketDoesNotExposeSecrets"]["evidence"]
            self.assertIn("recoveryKeyAssignment", evidence)
            self.assertIn("bearerToken", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)

    def test_age_rating_answer_sheet_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", valid_packet())
            age_answers = valid_age_rating_answers().replace("Not Applicable", "").replace("FDA", "")
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md", age_answers)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ageRatingAnswerSheetComplete", report["failedRequiredChecks"])
            evidence = report["checks"]["ageRatingAnswerSheetComplete"]["evidence"]
            self.assertIn("Not Applicable", evidence)
            self.assertIn("FDA", evidence)


if __name__ == "__main__":
    unittest.main()
