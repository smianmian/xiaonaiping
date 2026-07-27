from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_launch_operator_workbench.py"
REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_WORKBENCH = REPO_ROOT / "Docs/08_Release/APP_STORE_CONNECT_OPERATOR_WORKBENCH_20260704.md"
SUPPORTING_FILES = (
    Path("Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json"),
    Path("Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json"),
    Path("Docs/08_Release/AppStoreEvidence/AppleDeveloper/DUNS-POST-DELIVERY-EXECUTION-RESULT.template.json"),
    Path("Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json"),
    Path("Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-BACKFILL-RESULT.template.json"),
    Path("Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260704.json"),
    Path("Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260704.json"),
    Path("Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md"),
    Path("Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json"),
    Path("Docs/08_Release/CROSS_APP_REUSABLE_EVIDENCE_PACKET_20260704.json"),
    Path("Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260704.json"),
    Path("Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_20260704.json"),
    Path("Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260704.json"),
    Path("Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json"),
    Path("Docs/08_Release/XNP_PRODUCTION_PRIVACY_EVIDENCE_WORKBENCH_20260704.md"),
    Path("Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260704.json"),
    Path("Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260704.json"),
    Path("Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260704.json"),
    Path("Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260704.json"),
    Path("Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260704.json"),
    Path("Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260704.json"),
    Path("Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260704.json"),
    Path("Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260704.json"),
    Path("Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260704.json"),
    Path("Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260704.json"),
    Path("Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260704.json"),
    Path("Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-PRIVACY-AGE-REVIEW-RESULT.template.json"),
    Path("Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260704.md"),
    Path("Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260704.md"),
    Path("Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json"),
    Path("Docs/08_Release/AppStoreEvidence/_templates/apple-developer-team-signing-evidence.template.json"),
    Path("Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json"),
    Path("Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.template.json"),
    Path("Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260704.md"),
)


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_valid_context(root: Path, workbench_text: str | None = None) -> None:
    write(
        root / "Docs/08_Release/APP_STORE_CONNECT_OPERATOR_WORKBENCH_20260704.md",
        workbench_text if workbench_text is not None else REAL_WORKBENCH.read_text(encoding="utf-8"),
    )
    for relative_path in SUPPORTING_FILES:
        write(root / relative_path, (REPO_ROOT / relative_path).read_text(encoding="utf-8"))


class LaunchOperatorWorkbenchTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/launch-operator-workbench.json"
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
        self.assertIn("launch operator workbench", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_current_workbench_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_core_sections_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            text = REAL_WORKBENCH.read_text(encoding="utf-8")
            text = text.replace("日期：2026-07-04", "日期：2026-06-28")
            text = text.replace("App 名称 | 小奶瓶", "App 名称 | 待填")
            text = text.replace("确认组织 Team ID", "确认组织")
            text = text.replace("所有本机证据只认 iOS 26.5", "所有本机证据待定")
            text = text.replace("08-wechat-open-platform.png", "08-wechat.png")
            text = text.replace("跨项目可复用材料边界", "跨项目材料")
            text = text.replace("不得点击 Submit for Review", "可以提交")
            text = text.replace("check_app_store_evidence.py --allow-incomplete --date 2026-07-04", "check_app_store_evidence.py")
            write_valid_context(root, text)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("identityAndDateBoundaryPresent", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectDraftFieldsPresent", report["failedRequiredChecks"])
            self.assertIn("dunsPostDeliveryActionsPresent", report["failedRequiredChecks"])
            self.assertIn("realDeviceTestFlightCaptureTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("externalPlatformProductionPrivacyFilingPlanPresent", report["failedRequiredChecks"])
            self.assertIn("crossAppReuseBoundaryPresent", report["failedRequiredChecks"])
            self.assertIn("submitForReviewGuardPresent", report["failedRequiredChecks"])
            self.assertIn("rerunCommandsPresent", report["failedRequiredChecks"])

    def test_internal_review_login_wording_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root)
            review_information = root / "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260704.md"
            write(
                review_information,
                review_information.read_text(encoding="utf-8").replace(
                    "App Review 测试使用恢复密钥测试账号。",
                    "当前审核主路径使用恢复密钥测试账号。",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("reviewLoginInternalWordingAbsent", report["failedRequiredChecks"])

    def test_missing_supporting_packets_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root)
            for relative_path in SUPPORTING_FILES:
                (root / relative_path).unlink()

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreReviewInformationPresent", report["failedRequiredChecks"])
            self.assertIn("dunsPostDeliveryActionPacketPresent", report["failedRequiredChecks"])
            self.assertIn("appleDeveloperExternalStatusPollTemplatePresent", report["failedRequiredChecks"])
            self.assertIn(
                "appleDeveloperDunsPostDeliveryExecutionTemplatePresent",
                report["failedRequiredChecks"],
            )
            self.assertIn("appleDeveloperOrgSigningResultTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("ascBackfillResultTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("appReviewTestAccountPacketPresent", report["failedRequiredChecks"])
            self.assertIn("focusedCapturePacketPresent", report["failedRequiredChecks"])
            self.assertIn("realDeviceRegressionTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("realDeviceCaptureResultTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("crossAppReusePacketPresent", report["failedRequiredChecks"])
            self.assertIn("submitReviewPreflightPacketPresent", report["failedRequiredChecks"])
            self.assertIn("finalScreenshotUploadPacketPresent", report["failedRequiredChecks"])
            self.assertIn("externalPlatformCapturePacketPresent", report["failedRequiredChecks"])
            self.assertIn("externalPlatformCaptureResultTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("productionPrivacyEvidenceWorkbenchPresent", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectDraftJsonPresent", report["failedRequiredChecks"])
            self.assertIn("wechatReleaseConfigurationPacketPresent", report["failedRequiredChecks"])
            self.assertIn("smsProviderLiveSendPacketPresent", report["failedRequiredChecks"])
            self.assertIn("obsStorageProofPacketPresent", report["failedRequiredChecks"])
            self.assertIn("mainlandFilingExecutionPacketPresent", report["failedRequiredChecks"])
            self.assertIn("productionProofRefreshPacketPresent", report["failedRequiredChecks"])
            self.assertIn("productionProofRefreshStatusPresent", report["failedRequiredChecks"])
            self.assertIn("realDeviceCapturePreflightPacketPresent", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectFieldFreezePacketPresent", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectEntrySessionPacketPresent", report["failedRequiredChecks"])
            self.assertIn("appStoreManualEvidencePacketPresent", report["failedRequiredChecks"])
            self.assertIn("ascPrivacyAgeReviewResultTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectFinalEntryAuditPresent", report["failedRequiredChecks"])
            self.assertIn("realDeviceExecutionSheetPresent", report["failedRequiredChecks"])
            self.assertIn("wechatOpenPlatformEvidenceTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("appleDeveloperTeamSigningTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("mainlandFilingPrivacyEvidenceTemplatePresent", report["failedRequiredChecks"])
            self.assertIn("finalScreenshotUploadProvenanceTemplatePresent", report["failedRequiredChecks"])

    def test_wechat_release_packet_requires_env_sourced_build_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root)
            path = root / "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260704.json"
            packet = json.loads(path.read_text(encoding="utf-8"))
            for step in packet["executionOrder"]:
                if step["step"] in {"buildReleaseSimIos265", "buildReleaseDeviceIos265"}:
                    step["command"] = step["command"].replace(". /tmp/xnp-wechat-release.env && ", "")
                    step["command"] = step["command"].replace(' XNP_WECHAT_APP_ID="$XNP_WECHAT_APP_ID"', "")
                    step["command"] = step["command"].replace(' XNP_WECHAT_URL_SCHEME="$XNP_WECHAT_URL_SCHEME"', "")
                    step["command"] = step["command"].replace(' XNP_WECHAT_UNIVERSAL_LINK="$XNP_WECHAT_UNIVERSAL_LINK"', "")
                if step["step"] == "refreshClientProofs":
                    step["commands"][0] = step["commands"][0].replace(". /tmp/xnp-wechat-release.env && ", "")
            write(path, json.dumps(packet, ensure_ascii=False, indent=2) + "\n")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("wechatReleaseConfigurationPacketStructured", report["failedRequiredChecks"])

    def test_production_privacy_workbench_rejects_stale_obs_env_names(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root)
            path = root / "Docs/08_Release/XNP_PRODUCTION_PRIVACY_EVIDENCE_WORKBENCH_20260704.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("HUAWEI_OBS_BUCKET", "XNP_HUAWEI_OBS_BUCKET", 1),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionPrivacyEvidenceWorkbenchCanonicalObsEnvNames", report["failedRequiredChecks"])
            evidence = report["checks"]["productionPrivacyEvidenceWorkbenchCanonicalObsEnvNames"]["evidence"]
            self.assertIn("stale XNP_HUAWEI_OBS_* env names", evidence)

    def test_broken_supporting_packet_markers_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root)
            replacements = {
                SUPPORTING_FILES[0]: ("archive-release-build", "archive-build"),
                SUPPORTING_FILES[1]: ("external-status-poll-template-not-evidence", "external-status-poll-captured"),
                SUPPORTING_FILES[2]: ("captured-live-duns-post-delivery", "captured-duns-post-delivery"),
                SUPPORTING_FILES[3]: ("captured-live-apple-developer-org", "captured-apple-developer"),
                SUPPORTING_FILES[4]: ("captured-live-backfill", "captured-backfill"),
                SUPPORTING_FILES[5]: ("review-test-account-packet-not-evidence", "review-test-account-captured"),
                SUPPORTING_FILES[6]: ("noSimulatorEvidence", "simulatorEvidenceAllowed"),
                SUPPORTING_FILES[7]: ("本项目真机回归只接受 iOS 26.5", "本项目真机回归待定"),
                SUPPORTING_FILES[8]: ("captured-live-real-device", "captured-device"),
                SUPPORTING_FILES[9]: ("must not reuse Emotion Isle provider or storage namespace proof", "may reuse provider proof"),
                SUPPORTING_FILES[10]: ("do-not-click-submit-for-review", "click-submit-for-review"),
                SUPPORTING_FILES[11]: ("UPLOAD_PROVENANCE.json is still missing", "UPLOAD_PROVENANCE.json exists"),
                SUPPORTING_FILES[12]: ("template-only-not-evidence", "external-platform-captured"),
                SUPPORTING_FILES[13]: ("captured-live-external-platforms", "captured-external-platforms"),
                SUPPORTING_FILES[14]: ("stableAliasSyncAllowed=false", "stableAliasSyncAllowed=true"),
                SUPPORTING_FILES[15]: ("draft-only-not-submission", "draft-captured"),
                SUPPORTING_FILES[16]: ("release-configuration-packet-not-evidence", "release-configuration-captured"),
                SUPPORTING_FILES[17]: ("live-send-packet-not-evidence", "live-send-captured"),
                SUPPORTING_FILES[18]: ("storage-proof-packet-not-evidence", "storage-proof-captured"),
                SUPPORTING_FILES[19]: ("execution-packet-not-evidence", "execution-packet-captured"),
                SUPPORTING_FILES[20]: ("refresh-plan-not-evidence", "refresh-plan-captured"),
                SUPPORTING_FILES[21]: (
                    "current proof files are incomplete or failed; do not sync stable aliases",
                    "current proof files are complete; sync stable aliases",
                ),
                SUPPORTING_FILES[22]: ("do-not-start-real-device-capture", "start-real-device-capture"),
                SUPPORTING_FILES[23]: ("field-freeze-plan-not-evidence", "field-freeze-captured"),
                SUPPORTING_FILES[24]: ("entry-session-plan-not-evidence", "entry-session-captured"),
                SUPPORTING_FILES[25]: ("manual-evidence-plan-not-evidence", "manual-evidence-captured"),
                SUPPORTING_FILES[26]: (
                    "privacy-age-review-result-template-not-evidence",
                    "privacy-age-review-result-captured",
                ),
                SUPPORTING_FILES[27]: (
                    "安装来源 | TestFlight 或 Xcode 签名真机包，不能用模拟器或 iOS 27 截图替代",
                    "安装来源 | Debug simulator 或 iOS 27 截图也可以替代",
                ),
                SUPPORTING_FILES[28]: ("只接受 iOS 26.5", "接受 iOS 27 或模拟器"),
                SUPPORTING_FILES[29]: ("template-only-not-evidence", "captured-wechat-open-platform"),
                SUPPORTING_FILES[30]: ("template-only-not-evidence", "captured-team-signing"),
                SUPPORTING_FILES[31]: ("template-only-not-evidence", "captured-mainland-filing-privacy"),
                SUPPORTING_FILES[32]: ("Do not use Debug simulator candidate screenshots", "Debug simulator candidate screenshots are allowed"),
            }
            for relative_path, (old, new) in replacements.items():
                path = root / relative_path
                write(path, path.read_text(encoding="utf-8").replace(old, new))

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsPostDeliveryActionPacketStructured", report["failedRequiredChecks"])
            self.assertIn("appleDeveloperExternalStatusPollTemplateStructured", report["failedRequiredChecks"])
            self.assertIn(
                "appleDeveloperDunsPostDeliveryExecutionTemplateStructured",
                report["failedRequiredChecks"],
            )
            self.assertIn("appleDeveloperOrgSigningResultTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("ascBackfillResultTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("appReviewTestAccountPacketStructured", report["failedRequiredChecks"])
            self.assertIn("focusedCapturePacketStructured", report["failedRequiredChecks"])
            self.assertIn("realDeviceRegressionTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("realDeviceCaptureResultTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("crossAppReusePacketStructured", report["failedRequiredChecks"])
            self.assertIn("submitReviewPreflightPacketStructured", report["failedRequiredChecks"])
            self.assertIn("finalScreenshotUploadPacketStructured", report["failedRequiredChecks"])
            self.assertIn("externalPlatformCapturePacketStructured", report["failedRequiredChecks"])
            self.assertIn("externalPlatformCaptureResultTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("productionPrivacyEvidenceWorkbenchStructured", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectDraftJsonStructured", report["failedRequiredChecks"])
            self.assertIn("wechatReleaseConfigurationPacketStructured", report["failedRequiredChecks"])
            self.assertIn("smsProviderLiveSendPacketStructured", report["failedRequiredChecks"])
            self.assertIn("obsStorageProofPacketStructured", report["failedRequiredChecks"])
            self.assertIn("mainlandFilingExecutionPacketStructured", report["failedRequiredChecks"])
            self.assertIn("productionProofRefreshPacketStructured", report["failedRequiredChecks"])
            self.assertIn("productionProofRefreshStatusStructured", report["failedRequiredChecks"])
            self.assertIn("realDeviceCapturePreflightPacketStructured", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectFieldFreezePacketStructured", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectEntrySessionPacketStructured", report["failedRequiredChecks"])
            self.assertIn("appStoreManualEvidencePacketStructured", report["failedRequiredChecks"])
            self.assertIn("ascPrivacyAgeReviewResultTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectFinalEntryAuditStructured", report["failedRequiredChecks"])
            self.assertIn("realDeviceExecutionSheetStructured", report["failedRequiredChecks"])
            self.assertIn("wechatOpenPlatformEvidenceTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("appleDeveloperTeamSigningTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("mainlandFilingPrivacyEvidenceTemplateStructured", report["failedRequiredChecks"])
            self.assertIn("finalScreenshotUploadProvenanceTemplateStructured", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
