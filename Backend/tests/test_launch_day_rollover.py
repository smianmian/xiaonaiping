from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_launch_day_rollover.py"


SOURCE_FILES = {
    "appStoreConnectFillSheet": "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260628.md",
    "appStoreConnectDraft": "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260628.json",
    "appStoreEvidenceChecklist": "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260628.md",
    "productionProofRefreshPacket": "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260628.json",
    "externalPlatformCapturePacket": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260628.json",
    "realDeviceFocusedCapturePacket": "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260628.json",
    "finalScreenshotUploadPacket": "Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_20260628.json",
    "dunsPostDeliveryActions": "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
}
CURRENT_DAY_EXECUTION_PACKETS = {
    "appStoreConnectFieldFreeze": "Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260629.json",
    "appStoreConnectSubmitReviewPreflight": "Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260629.json",
    "appStoreManualEvidencePacket": "Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260629.json",
    "appReviewTestAccountPacket": "Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260629.json",
    "productionProofRefreshPacket": "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260629.json",
    "productionPrivacyEvidenceWorkbench": "Docs/08_Release/XNP_PRODUCTION_PRIVACY_EVIDENCE_WORKBENCH_20260629.md",
    "externalPlatformCapturePacket": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260629.json",
    "smsProviderLiveSendPacket": "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260629.json",
    "wechatReleaseConfigurationPacket": "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260629.json",
    "obsStorageProofPacket": "Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260629.json",
    "mainlandFilingExecutionPacket": "Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260629.json",
    "realDeviceFocusedCapturePacket": "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260629.json",
    "realDeviceCapturePreflightPacket": "Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260629.json",
    "finalScreenshotUploadPacket": "Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_20260629.json",
    "dunsPostDeliveryActions": "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
}


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_packet() -> dict:
    return {
        "artifactType": "launch-day-rollover-packet",
        "status": "rollover-plan-not-evidence",
        "date": "2026-06-29",
        "previousEvidenceDate": "2026-06-28",
        "project": "XiaoNaiPing",
        "appName": "小奶瓶",
        "sourceFiles": dict(SOURCE_FILES),
        "currentDayExecutionPackets": dict(CURRENT_DAY_EXECUTION_PACKETS),
        "reusableDraftSources": [
            {
                "id": "appStoreConnectCopy",
                "fields": [
                    "App 名称",
                    "副标题",
                    "描述",
                    "关键词",
                    "分类",
                    "年龄分级",
                    "隐私政策 URL",
                    "技术支持 URL",
                    "审核备注",
                ],
                "reuseBoundary": "Draft copy may be reused on 2026-06-29 only after check_app_store_connect_materials.py and check_app_store_submission_packet.py pass in the current worktree.",
                "notEvidence": True,
            },
            {
                "id": "legalPublicUrls",
                "fields": ["privacy", "terms", "support"],
                "reuseBoundary": "Public URL text can be reused only if check_public_pages.py and check_legal_drafts.py pass and the URLs still resolve on 2026-06-29.",
                "notEvidence": True,
            },
        ],
        "sameDayEvidenceRefresh": [
            {
                "id": "appStoreConnectPageEvidence",
                "target": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/",
                "mustRefreshOnOrAfter": "2026-06-29",
                "previousDateNotAllowed": ["2026-06-28"],
                "requiredGate": "Backend/proof/app-store-connect-evidence-materials.json",
            },
            {
                "id": "appStoreManualEvidence",
                "target": "Docs/08_Release/AppStoreEvidence/",
                "mustRefreshOnOrAfter": "2026-06-29",
                "previousDateNotAllowed": ["2026-06-28"],
                "requiredGate": "Backend/proof/app-store-evidence-20260629T-current.json",
            },
            {
                "id": "productionCurrentProofs",
                "target": "Backend/proof/*-20260629T-current.json",
                "mustRefreshOnOrAfter": "2026-06-29",
                "previousDateNotAllowed": ["20260628T-current", "2026-06-28"],
                "requiredGate": "Backend/proof/production-readiness-20260629T-current.json",
            },
            {
                "id": "providerEvidence",
                "target": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png; Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png; Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png; Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
                "mustRefreshOnOrAfter": "2026-06-29",
                "previousDateNotAllowed": ["2026-06-28"],
                "requiredGate": "Backend/proof/provider-evidence-materials.json",
            },
            {
                "id": "signedArchiveTestFlight",
                "target": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png; Docs/08_Release/AppStoreEvidence/06-testflight.png; Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-07-build-testflight-link.png",
                "mustRefreshOnOrAfter": "2026-06-29",
                "previousDateNotAllowed": ["2026-06-28"],
                "requiredGate": "Backend/proof/signed-archive-testflight-materials.json",
            },
            {
                "id": "finalScreenshotUploadProvenance",
                "target": "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                "mustRefreshOnOrAfter": "2026-06-29",
                "previousDateNotAllowed": [
                    "Debug simulator candidate provenance",
                    "2026-06-28 candidate-only provenance",
                ],
                "requiredGate": "Backend/proof/app-store-assets.json",
            },
            {
                "id": "ios265RealDeviceRegression",
                "target": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
                "mustRefreshOnOrAfter": "2026-06-29",
                "previousDateNotAllowed": ["iOS 27", "simulator-only proof", "2026-06-28"],
                "requiredGate": "Backend/proof/testflight-regression-plan.json",
            },
            {
                "id": "dunsStatusPoll",
                "target": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.json",
                "mustRefreshOnOrAfter": "2026-06-29",
                "previousDateNotAllowed": ["2026-06-28"],
                "requiredGate": "Backend/proof/signed-archive-testflight-materials.json",
            },
        ],
        "rolloverRules": [
            "Do not copy 20260628T-current proof into any 20260629T-current proof.",
            "Stable aliases may sync only after 2026-06-29 same-round current proofs pass.",
            "App Store Connect draft copy may be reused, but App Store Connect page screenshots and App Review evidence must be captured or re-verified on 2026-06-29.",
            "Debug simulator screenshot candidates are not final screenshot upload evidence; UPLOAD_PROVENANCE.json must come from iOS 26.5 TestFlight or Xcode signed physical-device build.",
            "iOS 27 and simulator-only runs cannot satisfy local real-device regression evidence; local evidence only counts on iOS 26.5.",
            "D-U-N-S delivery, Apple Developer organization enrollment, Team ID, signing certificate, Archive, and TestFlight evidence must be from the live Apple portals after the D-U-N-S status changes.",
            "This rollover packet is not external platform evidence, not production readiness, and not Submit for Review permission.",
        ],
        "postRolloverCommands": [
            "python3 Backend/scripts/check_launch_day_rollover.py --output Backend/proof/launch-day-rollover.json",
            "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
            "python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
            "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-29 --output Backend/proof/app-store-evidence-20260629T-current.json",
            "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json",
            "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
        ],
        "completionRule": "rollover-plan-not-evidence; not submission permission. 2026-06-28 copy and templates may remain as draft sources, but 2026-06-29 submission requires same-day App Store manual evidence, production current proofs, provider evidence, signed Archive/TestFlight evidence, final screenshot UPLOAD_PROVENANCE.json, iOS 26.5 real-device regression, and launch-objective-audit.json ready=true.",
    }


def write_valid_docs(root: Path, packet: dict | None = None) -> None:
    for relative in SOURCE_FILES.values():
        write(root / relative, "{}\n")
    for relative in CURRENT_DAY_EXECUTION_PACKETS.values():
        write(root / relative, "{}\n")
    write_json(root / "Docs/08_Release/LAUNCH_DAY_ROLLOVER_20260629.json", packet or valid_packet())


class LaunchDayRolloverTest(unittest.TestCase):
    def run_checker(
        self,
        root: Path,
        today: str = "2026-06-29",
        packet: str | None = None,
    ) -> dict:
        output = root / "Backend/proof/launch-day-rollover.json"
        command = [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(root),
                "--output",
                str(output),
                "--today",
                today,
                "--allow-incomplete",
        ]
        if packet is not None:
            command.extend(["--packet", packet])
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("launch day rollover", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_rollover_packet_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])
            self.assertIn("same-day refresh", report["checks"]["sameDayEvidenceRefreshRequired"]["evidence"])
            self.assertIn("2026-06-29", report["checks"]["rolloverPacketDateIsToday"]["evidence"])

    def test_rollover_packet_fails_after_its_launch_date(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)

            report = self.run_checker(
                root,
                today="2026-06-30",
                packet="Docs/08_Release/LAUNCH_DAY_ROLLOVER_20260629.json",
            )

            self.assertFalse(report["passed"])
            self.assertIn("rolloverPacketDateIsToday", report["failedRequiredChecks"])
            self.assertIn(
                "packet date '2026-06-29' is stale for today '2026-06-30'",
                report["checks"]["rolloverPacketDateIsToday"]["evidence"],
            )

    def test_rollover_packet_rejects_stale_or_missing_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = copy.deepcopy(valid_packet())
            packet["date"] = "2026-06-28"
            del packet["sourceFiles"]["appStoreConnectDraft"]
            packet["currentDayExecutionPackets"]["realDeviceFocusedCapturePacket"] = (
                "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260628.json"
            )
            del packet["currentDayExecutionPackets"]["finalScreenshotUploadPacket"]
            packet["reusableDraftSources"][0]["fields"].remove("审核备注")
            packet["sameDayEvidenceRefresh"][0]["target"] = "Docs/08_Release/AppStoreEvidence/"
            packet["sameDayEvidenceRefresh"][2]["previousDateNotAllowed"].remove("20260628T-current")
            packet["rolloverRules"] = [rule for rule in packet["rolloverRules"] if "20260628T-current" not in rule]
            packet["postRolloverCommands"] = [
                command for command in packet["postRolloverCommands"] if "--date 2026-06-29" not in command
            ]
            packet["completionRule"] = "ready"
            write_valid_docs(root, packet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("rolloverPacketScalarsValid", report["failedRequiredChecks"])
            self.assertIn("rolloverSourceFilesPinned", report["failedRequiredChecks"])
            self.assertIn("currentDayExecutionPacketsPinned", report["failedRequiredChecks"])
            self.assertIn("reusableDraftSourcesBounded", report["failedRequiredChecks"])
            self.assertIn("sameDayEvidenceRefreshRequired", report["failedRequiredChecks"])
            self.assertIn("rolloverRulesBlockStaleEvidence", report["failedRequiredChecks"])
            self.assertIn("postRolloverCommandsPresent", report["failedRequiredChecks"])
            self.assertIn("completionRuleBlocksSubmission", report["failedRequiredChecks"])
            self.assertIn("20260628T-current", report["checks"]["sameDayEvidenceRefreshRequired"]["evidence"])
            self.assertIn("FOCUSED_CAPTURE_PACKET_20260629.json", report["checks"]["currentDayExecutionPacketsPinned"]["evidence"])
            self.assertIn("FINAL_SCREENSHOT_UPLOAD_PACKET_20260629.json", report["checks"]["currentDayExecutionPacketsPinned"]["evidence"])
            self.assertIn("not submission permission", report["checks"]["completionRuleBlocksSubmission"]["evidence"])


if __name__ == "__main__":
    unittest.main()
