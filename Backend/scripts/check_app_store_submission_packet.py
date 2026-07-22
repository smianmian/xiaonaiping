#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OFFICIAL_APPLE_URLS = {
    "appReviewGuidelines": "https://developer.apple.com/app-store/review/guidelines/",
    "appPrivacyOverview": "https://developer.apple.com/help/app-store-connect/manage-app-privacy/overview-of-app-privacy-details/",
    "privacyNutritionLabels": "https://developer.apple.com/app-store/app-privacy-details/",
    "screenshotSpecifications": "https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications",
    "ageRating": "https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating",
    "regulatedMedicalDevice": "https://developer.apple.com/help/app-store-connect/manage-app-information/declare-regulated-medical-device-status",
}

REVIEW_BOUNDARY_MARKERS = {
    "liveActivityBoundary": ("灵动岛", "Live Activity", "下一次喝奶提醒"),
    "widgetBoundary": ("小组件", "今日摘要"),
    "statusDisplayBoundary": ("状态展示",),
    "manualFeedingReminderDeferral": (
        "手动顺延下一次提醒",
        "5 分钟一档",
        "不顺延",
        "+5",
        "+10",
        "+15",
        "+20",
        "+25",
        "+30 分钟",
    ),
    "feedingReminderDeferralCalculation": ("本顿结束时间 + 固定间隔 + 顺延分钟", "本顿发生时间"),
    "feedingReminderDeferralPersistenceBoundary": ("顺延只改变下一次提醒时间", "不新增持久化字段"),
    "noAutomaticFeedingInference": ("不根据奶量、月龄、传感器或健康数据自动推算喂养时间",),
    "userEnteredDataSource": ("用户在 App 内输入", "本机记录"),
    "noHealthPressureFeedingAdvice": ("不生成健康建议、压力提醒、喂养建议",),
    "noHealthKit": ("不接入 HealthKit",),
    "noPressureOrDiagnosis": ("不提供压力评估", "医疗诊断"),
    "noDebugCode": ("debug code",),
}

DO_NOT_SUBMIT_MARKERS = {
    "noRealFamilyData": ("real baby photos", "real phone numbers", "recovery keys", "tokens"),
    "noDebugOrLocal": ("debug login codes", "127.0.0.1", "localhost"),
    "noMedicalClaims": ("medical diagnosis", "doctor replacement"),
    "noUnfinishedWeChat": ("WeChat login before Open Platform proof",),
    "noSensorClaims": ("HealthKit", "stress detection", "medical interpretation"),
}

PRIVACY_SOURCE_MARKERS = (
    "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
    "Docs/07_PrivacySecurity/SDK_DATA_INVENTORY.md",
    "Docs/07_PrivacySecurity/PRIVACY_REVIEW.md",
    "App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy",
)

PRE_SUBMIT_COMMAND_MARKERS = (
    "run_launch_readiness.sh",
    "--ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260629-stable.log",
    "--ios-device-log Backend/proof/xcodebuild-release-ios265-20260629-device-current.log",
    "check_ios_265_build_proof.py",
    "check_ios_app_bundle.py",
    "check_testflight_precheck.py",
    "check_testflight_regression_plan.py",
    "check_wechat_client_configuration.py",
    "check_app_store_evidence.py",
    "check_app_store_connect_evidence_materials.py",
    "check_mainland_filing_materials.py",
    "check_signed_archive_testflight_materials.py",
    "check_provider_evidence_materials.py",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
    "check_launch_blocker_action_packet.py",
)

EXPORT_COMPLIANCE_MARKERS = (
    "standard system/network encryption",
    "does not implement custom cryptography",
    "VPN",
    "DRM",
    "end-to-end encrypted messaging",
)

AGE_AND_MEDICAL_DEVICE_MARKERS = (
    "4+",
    "Do not select Kids",
    "Regulated Medical Device",
    "No",
    "not a medical device",
    "does not provide diagnosis",
    "does not provide treatment",
    "does not predict disease",
    "HealthKit",
    "sensors",
    "stress",
)
RELEASE_BUNDLE_IOS265_MARKERS = (
    "Backend/proof/ios-265-build.json",
    "Backend/proof/ios-app-bundle.json",
    "iOS 26.5",
    "iphonesimulator26.5",
    "iphoneos26.5",
    "com.mewpow.xiaonaiping",
    "PrivacyInfo.xcprivacy",
    "XNPAPIBaseURL=https://api.mewpow.com/xiaonaiping",
    "WeChat AppID",
    "`wx...` URL Scheme",
)
CURRENT_GATE_STATUS_MARKERS = (
    "Backend/proof/app-store-connect-materials.json",
    "Backend/proof/app-store-evidence.json",
    "Backend/proof/production-readiness.json",
    "Backend/proof/launch-objective-audit.json",
    "Backend/proof/testflight-regression-plan.json",
    "Backend/proof/provider-evidence-materials.json",
    "Backend/proof/mainland-filing-materials.json",
    "Backend/proof/signed-archive-testflight-materials.json",
    "Backend/proof/auth-providers.json",
    "Backend/proof/ios-app-bundle.json",
    "productionSecretConfigured",
    "productionDataDirConfigured",
    "mysqlDatabaseSelected",
    "mysqlDatabaseEnvPresent",
    "phoneLoginProviderConfigured",
    "wechatLoginProviderConfigured",
    "privateOperationsDashboardConfigured",
    "publicInternalDashboardBlocked",
    "xiaonaipingProductionNamespaceConfigured",
    "testFlightRegressionPlanProofPassed",
    "appStoreAssetsProofPassed",
    "authProvidersProofPassed",
    "weChatNativeConfigPresent",
    "weChatURLTypePresent",
    "XiaoNaiPing submit permission",
    "not ready",
    "iOS 26.5 real-device evidence",
)
CURRENT_SUBMISSION_PACKET_MARKERS = (
    "Date: 2026-06-30",
    "## Current 2026-06-30 Gate Status",
    "XiaoNaiPing submit permission",
    "Backend/proof/provider-evidence-materials.json",
    "Backend/proof/mainland-filing-materials.json",
    "Backend/proof/signed-archive-testflight-materials.json",
    "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260630.md",
    "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260630.md",
    "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260630.md",
    "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md",
)
FORBIDDEN_SUBMISSION_PACKET_MARKERS = (
    "Cross-app submission guard",
    "cross-app-submission-readiness",
    "check-cross-app-submit-ready",
    "canSubmit=true",
    "canSubmit=false",
)
STALE_SUBMISSION_PACKET_MARKERS = (
    "Current 2026-06-29 Gate Status",
    "APP_STORE_EVIDENCE_CHECKLIST_20260629.md",
    "APP_STORE_CONNECT_COPY_PASTE_20260629.md",
    "APP_STORE_CONNECT_FILL_SHEET_20260629.md",
    "APP_STORE_AGE_RATING_ANSWERS_20260629.md",
    "Current 2026-06-28 Gate Status",
    "cross-app-submission-readiness-20260628-current.json",
    "APP_STORE_EVIDENCE_CHECKLIST_20260628.md",
    "APP_STORE_CONNECT_COPY_PASTE_20260628.md",
    "APP_STORE_CONNECT_FILL_SHEET_20260628.md",
    "APP_STORE_AGE_RATING_ANSWERS_20260628.md",
)
MANUAL_EVIDENCE_CHECKLIST_MARKERS = (
    "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260630.md",
    "manualEvidenceChecklist",
    "RD-01",
    "RD-24",
    "iOS 26.5",
    "Live Activity",
    "小组件",
    "不生成健康建议、压力提醒、喂养建议或医疗判断",
)
CURRENT_RELEASE_BUNDLE_MARKERS = (
    "Backend/proof/xcodebuild-release-ios265-20260629-stable.log",
    "Backend/proof/xcodebuild-release-ios265-20260629-device-current.log",
    "Backend/proof/ios-app-bundle.json",
    "weChatNativeConfigPresent",
    "weChatURLTypePresent",
)
STALE_RELEASE_BUNDLE_MARKERS = (
    "xcodebuild-debug-ios265-20260629.log",
    "xcodebuild-release-ios265-20260629.log",
    "xcodebuild-debug-ios265-20260628.log",
    "xcodebuild-release-ios265-20260628.log",
    "xcodebuild-release-ios265-20260628-device-current.log",
    "xcodebuild-release-ios265-20260629-sim-current.log",
    "XiaoNaiPing-BundleReuse-Release",
    "iphoneos18.5",
    "iphonesimulator18.5",
    "DTSDKName=iphoneos18.5",
    "OS=18.5",
)

AGE_RATING_ANSWERS_MARKERS = (
    "日期：2026-06-30",
    "set-an-app-age-rating",
    "declare-regulated-medical-device-status",
    "Kids Category",
    "父母和照护者",
    "不面向儿童直接使用",
    "4+",
    "App Store Connect 问卷自动计算结果为准",
    "Age Categories and Override",
    "Not Applicable",
    "Made for Kids",
    "公开 UGC",
    "社交",
    "聊天",
    "无 IAP",
    "无广告",
    "无第三方分析 SDK",
    "无赌博",
    "无成人内容",
    "Health-related records",
    "不接入 HealthKit",
    "传感器",
    "医院系统",
    "手动顺延下一次提醒",
    "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
    "Regulated Medical Device",
    "No",
    "not a medical device",
    "does not provide diagnosis",
    "does not provide diagnosis, prevention, monitoring, treatment",
    "FDA",
    "CE mark",
    "UKCA",
    "提交前重检项",
)

AGE_RATING_PACKET_REFERENCE_MARKERS = (
    "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md",
    "Age Rating And Medical Device Answers",
    "App Store Connect 问卷自动计算结果为准",
)

FORBIDDEN_SECRET_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def contains_all(text: str, markers: tuple[str, ...]) -> bool:
    lower = text.lower()
    return all(marker.lower() in lower for marker in markers)


def forbidden_secret_hits(text: str) -> list[str]:
    return sorted(name for name, pattern in FORBIDDEN_SECRET_PATTERNS.items() if pattern.search(text))


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    packet_path = root / args.packet
    packet = read_text(packet_path)
    age_rating_answers_path = root / args.age_rating_answers
    age_rating_answers = read_text(age_rating_answers_path)
    report = Report()

    report.add("submissionPacketPresent", bool(packet), str(packet_path) if packet else "missing submission packet")
    report.add(
        "ageRatingAnswersPresent",
        bool(age_rating_answers),
        str(age_rating_answers_path) if age_rating_answers else "missing age rating answer sheet",
    )
    secret_hits = forbidden_secret_hits(packet + "\n" + age_rating_answers)
    report.add(
        "submissionPacketDoesNotExposeSecrets",
        not secret_hits,
        "found: " + ", ".join(secret_hits) if secret_hits else "submission packet and age rating answer sheet do not expose recovery keys, tokens, debug codes, API keys, or complete phone numbers",
    )
    missing_current_packet_markers = [
        marker for marker in CURRENT_SUBMISSION_PACKET_MARKERS if marker not in packet
    ]
    stale_packet_markers = [marker for marker in STALE_SUBMISSION_PACKET_MARKERS if marker in packet]
    forbidden_packet_markers = [
        marker for marker in FORBIDDEN_SUBMISSION_PACKET_MARKERS if marker in packet
    ]
    report.add(
        "submissionPacketUsesCurrentDayMaterials",
        bool(packet)
        and not missing_current_packet_markers
        and not stale_packet_markers
        and not forbidden_packet_markers,
        "missing: "
        + ", ".join(missing_current_packet_markers)
        + "; stale: "
        + ", ".join(stale_packet_markers)
        + "; forbidden: "
        + ", ".join(forbidden_packet_markers)
        if missing_current_packet_markers or stale_packet_markers or forbidden_packet_markers
        else "submission packet references 2026-06-30 current App Store, evidence, age-rating, and XiaoNaiPing submit proof materials",
    )

    missing_urls = [url for url in OFFICIAL_APPLE_URLS.values() if url not in packet]
    report.add(
        "officialAppleCheckpointsPresent",
        not missing_urls,
        "missing: " + ", ".join(missing_urls) if missing_urls else "official Apple App Review/App Privacy/screenshot/age/medical URLs present",
    )

    app_info = extract_section(packet, "App Information")
    app_info_markers = (
        "com.mewpow.xiaonaiping",
        "小奶瓶",
        "Lifestyle",
        "Free",
        "China mainland first",
        "WeChat authorization",
    )
    report.add(
        "appInformationComplete",
        contains_all(app_info, app_info_markers),
        "App Information contains bundle/name/category/price/region/login fields",
    )
    report.add(
        "appInformationAvoidsHealthFitnessCategory",
        "Health & Fitness" not in app_info and "健康健美" not in app_info,
        "App Information does not use Health & Fitness category wording",
    )

    current_gate_status = extract_section(packet, "Current 2026-06-30 Gate Status")
    missing_current_gate_markers = [
        marker for marker in CURRENT_GATE_STATUS_MARKERS if marker not in current_gate_status
    ]
    report.add(
        "currentGateStatusUsesDatedProofs",
        bool(current_gate_status) and not missing_current_gate_markers,
        "missing: " + ", ".join(missing_current_gate_markers)
        if missing_current_gate_markers
        else "current gate status uses 2026-06-30 current proof files and names active blockers",
    )

    missing_manual_checklist_markers = [
        marker for marker in MANUAL_EVIDENCE_CHECKLIST_MARKERS if marker not in packet
    ]
    report.add(
        "manualEvidenceChecklistReferenced",
        not missing_manual_checklist_markers,
        "missing: " + ", ".join(missing_manual_checklist_markers)
        if missing_manual_checklist_markers
        else "manual evidence checklist and real-device boundary are referenced",
    )

    review_notes = extract_section(packet, "Review Notes")
    report.add("reviewNotesPresent", bool(review_notes), "Review Notes section present" if review_notes else "missing Review Notes")
    for name, markers in REVIEW_BOUNDARY_MARKERS.items():
        report.add(
            name,
            contains_all(review_notes, markers),
            "Review Notes contains: " + ", ".join(markers),
        )

    do_not_submit = extract_section(packet, "Do Not Submit Or Screenshot")
    report.add("doNotSubmitSectionPresent", bool(do_not_submit), "Do Not Submit section present" if do_not_submit else "missing Do Not Submit section")
    for name, markers in DO_NOT_SUBMIT_MARKERS.items():
        report.add(
            name,
            contains_all(do_not_submit, markers),
            "Do Not Submit contains: " + ", ".join(markers),
        )

    privacy_source = extract_section(packet, "Privacy Label Fill Source")
    missing_privacy_sources = [marker for marker in PRIVACY_SOURCE_MARKERS if marker not in privacy_source]
    report.add(
        "privacyLabelSourcesComplete",
        not missing_privacy_sources,
        "missing: " + ", ".join(missing_privacy_sources) if missing_privacy_sources else "privacy label source documents are listed",
    )

    export_compliance = extract_section(packet, "Export Compliance")
    missing_export_markers = [marker for marker in EXPORT_COMPLIANCE_MARKERS if marker not in export_compliance]
    report.add(
        "exportComplianceAnswerPresent",
        not missing_export_markers,
        "missing: " + ", ".join(missing_export_markers)
        if missing_export_markers
        else "export compliance answer covers standard encryption and excludes custom crypto/VPN/DRM/E2EE messaging",
    )

    age_medical_device = extract_section(packet, "Age Rating And Medical Device Answers")
    missing_age_medical_markers = [marker for marker in AGE_AND_MEDICAL_DEVICE_MARKERS if marker not in age_medical_device]
    report.add(
        "ageRatingAndMedicalDeviceAnswersPresent",
        not missing_age_medical_markers,
        "missing: " + ", ".join(missing_age_medical_markers)
        if missing_age_medical_markers
        else "age rating and regulated medical device answers are explicit",
    )
    missing_age_answer_markers = [
        marker for marker in AGE_RATING_ANSWERS_MARKERS if marker not in age_rating_answers
    ]
    report.add(
        "ageRatingAnswerSheetComplete",
        bool(age_rating_answers) and not missing_age_answer_markers,
        "missing: " + ", ".join(missing_age_answer_markers)
        if missing_age_answer_markers
        else "dedicated age rating answer sheet covers Kids, content, medical-device, data-source, and re-check boundaries",
    )
    missing_packet_age_references = [
        marker for marker in AGE_RATING_PACKET_REFERENCE_MARKERS if marker not in packet
    ]
    report.add(
        "ageRatingAnswerSheetReferenced",
        not missing_packet_age_references,
        "missing: " + ", ".join(missing_packet_age_references)
        if missing_packet_age_references
        else "submission packet references the dedicated age rating answer sheet",
    )

    release_bundle = extract_section(packet, "Release Bundle Verification")
    missing_release_bundle_markers = [marker for marker in RELEASE_BUNDLE_IOS265_MARKERS if marker not in release_bundle]
    missing_current_release_bundle_markers = [
        marker for marker in CURRENT_RELEASE_BUNDLE_MARKERS if marker not in release_bundle
    ]
    stale_release_bundle_markers = [marker for marker in STALE_RELEASE_BUNDLE_MARKERS if marker in release_bundle]
    report.add(
        "releaseBundleVerificationUsesIOS265Proofs",
        bool(release_bundle)
        and not missing_release_bundle_markers
        and not missing_current_release_bundle_markers
        and not stale_release_bundle_markers,
        "missing: "
        + ", ".join(missing_release_bundle_markers + missing_current_release_bundle_markers)
        + "; stale: "
        + ", ".join(stale_release_bundle_markers)
        if missing_release_bundle_markers or missing_current_release_bundle_markers or stale_release_bundle_markers
        else "Release Bundle Verification points to current iOS 26.5 build and app-bundle proofs",
    )

    screenshot_status = extract_section(packet, "Screenshot Status")
    screenshot_markers = ("TestFlight or signed-device final screenshots", "No real baby photos", "medical and privacy claims")
    report.add(
        "screenshotStatusHasFinalEvidenceBoundary",
        contains_all(screenshot_status, screenshot_markers),
        "Screenshot Status contains final signed/TestFlight and privacy/medical boundaries",
    )

    pre_submit = extract_section(packet, "Pre-Submit Commands")
    missing_commands = [marker for marker in PRE_SUBMIT_COMMAND_MARKERS if marker not in pre_submit]
    report.add(
        "preSubmitCommandsComplete",
        not missing_commands,
        "missing: " + ", ".join(missing_commands) if missing_commands else "pre-submit commands include unified and component gates",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--packet", default="Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md")
    parser.add_argument("--age-rating-answers", default="Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md")
    parser.add_argument("--output", default="Backend/proof/app-store-submission-packet.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"App Store submission packet passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"App Store submission packet incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
