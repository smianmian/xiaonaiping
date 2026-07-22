#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_MARKERS = {
    "privacyCurrentDate": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "日期：2026-06-24"),
    "privacyCompanyEntity": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "深圳市闪现生活科技有限公司"),
    "privacyMainlandFirst": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "第一版计划先上中国大陆 App Store"),
    "privacyHongKongSecond": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "香港为第二批"),
    "privacyAccountMethods": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "恢复密钥、手机号和微信登录"),
    "privacyStatusDisplayBoundary": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示"),
    "privacyManualReminderDeferral": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "提醒顺延由你手动选择"),
    "privacyReminderDeferralGranularity": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "5 分钟一档"),
    "privacyReminderDeferralOptions": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "+5、+10、+15、+20、+25、+30 分钟"),
    "privacyReminderDeferralCalculation": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "本顿结束时间 + 固定间隔 + 顺延分钟"),
    "privacyReminderNoDurationFallback": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "本顿发生时间"),
    "privacyReminderNoPersistentField": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "不新增持久化字段"),
    "privacyNoAutomaticFeedingInference": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "不根据奶量、月龄、传感器或健康数据自动推算喂养时间"),
    "privacyUserEnteredStatusSource": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "这些状态展示只反映用户主动记录的数据"),
    "privacyNoHealthPressureFeedingAdvice": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "privacyNoHealthKitOrSensors": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "不接入 HealthKit、传感器、医院系统或第三方健康数据源"),
    "termsCurrentDate": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "日期：2026-06-24"),
    "termsCompanyEntity": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "深圳市闪现生活科技有限公司"),
    "termsAccountMethods": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "恢复密钥、手机号验证码和微信授权登录"),
    "termsSyncOriginalPhotos": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "用户主动加入 App 的照片原图"),
    "termsDeletion": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "删除云端账号与同步"),
    "termsMedicalBoundary": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "不提供诊断、治疗、预测、处方或专业疫苗建议"),
    "termsStatusDisplayBoundary": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示"),
    "termsManualReminderDeferral": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "提醒顺延由你手动选择"),
    "termsReminderDeferralGranularity": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "5 分钟一档"),
    "termsReminderDeferralOptions": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "+5、+10、+15、+20、+25、+30 分钟"),
    "termsReminderDeferralCalculation": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "本顿结束时间 + 固定间隔 + 顺延分钟"),
    "termsReminderNoDurationFallback": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "本顿发生时间"),
    "termsReminderNoPersistentField": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "不新增持久化字段"),
    "termsNoAutomaticFeedingInference": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "不根据奶量、月龄、传感器或健康数据自动推算喂养时间"),
    "termsUserEnteredStatusSource": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "这些状态展示只反映用户主动记录的数据"),
    "termsNoHealthPressureFeedingAdvice": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "termsNoHealthKitOrSensors": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "不接入 HealthKit、传感器、医院系统或第三方健康数据源"),
    "publicationHandoffCurrentDate": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "日期：2026-06-29"),
    "publicationHandoffPrivacyURL": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "https://api.mewpow.com/xiaonaiping/privacy"),
    "publicationHandoffTermsURL": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "https://api.mewpow.com/xiaonaiping/terms"),
    "publicationHandoffSupportURL": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "https://api.mewpow.com/xiaonaiping/support"),
    "publicationHandoffCompanyEntity": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "深圳市闪现生活科技有限公司"),
    "publicationHandoffPrivacyEmail": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "隐私联系邮箱"),
    "publicationHandoffSupportEmail": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "支持邮箱"),
    "publicationHandoffServiceProviders": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "短信服务商、微信开放平台、Apple TestFlight / App Store Connect、华为云 OBS"),
    "publicationHandoffDeletionSLA": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "删除 SLA"),
    "publicationHandoffFilingNumber": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "拿到真实 App 备案 / ICP 编号后再更新"),
    "publicationHandoffNoPlaceholders": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "不得写占位邮箱、测试邮箱、个人邮箱或未确认的隐私联系邮箱"),
    "publicationHandoffNoPretendEvidence": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "不得声称短信服务商、微信开放平台、OBS、备案、TestFlight 或 App Store Connect 人工证据已完成"),
    "publicationHandoffNoMedicalClaims": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "不得把小奶瓶描述为医疗器械、诊断工具、治疗工具、健康建议工具、压力评估工具或自动喂养建议工具"),
    "publicationHandoffRecheckCommands": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "check_public_pages.py"),
    "publicationHandoffUrlConsistencyChecklist": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "## 公开 URL 一致性清单"),
    "publicationHandoffUrlConsistencyFillSheet": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "APP_STORE_CONNECT_FILL_SHEET_20260629.md"),
    "publicationHandoffUrlConsistencyCopyPaste": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "APP_STORE_CONNECT_COPY_PASTE_20260629.md"),
    "publicationHandoffUrlConsistencyMetadata": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "APP_STORE_METADATA.md"),
    "publicationHandoffUrlConsistencyPrivacyLabel": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "APP_STORE_PRIVACY_LABEL.json"),
    "publicationHandoffUrlConsistencyPrivacyAnswers": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "APP_STORE_PRIVACY_ANSWERS_20260629.md"),
    "publicationHandoffUrlConsistencyVersionSettings": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md"),
    "publicationHandoffUrlConsistencyFiling": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "MAINLAND_FILING_MATERIALS.md"),
    "publicationHandoffUrlConsistencyExternalHandoff": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260629.md"),
    "publicationHandoffUrlConsistencySubmissionPacket": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "APP_STORE_SUBMISSION_PACKET.md"),
    "publicationHandoffUrlConsistencyStaticPages": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "Backend/static/privacy.html"),
    "publicationHandoffUrlConsistencyTermsStaticPage": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "Backend/static/terms.html"),
    "publicationHandoffUrlConsistencySupportStaticPage": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "Backend/static/support.html"),
    "publicationHandoffUrlConsistencyEvidence": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "RealDevice/RD-19-public-urls.png"),
    "publicationHandoffUrlConsistencyNoPartialUpdate": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "不要只改一处 URL"),
    "publicationHandoffUrlConsistencyRecheckAppStore": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "check_app_store_connect_materials.py"),
}

FORBIDDEN_PATTERNS = {
    "privacyOutdatedHongKongUsFirst": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", r"首发香港和美国|首發香港和美國"),
    "privacyOutdatedMainlandExcluded": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", r"不选择中国大陆|不選擇中國大陸|不含中国大陆|不含中國大陸"),
    "termsOutdatedRecoveryOnly": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", r"账号采用恢复密钥方式|帳號採用恢復密鑰方式"),
    "termsMissingCompanyEntityPlaceholder": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", r"开发者或公司主体|開發者或公司主體"),
    "publicationNoPlaceholderEmail": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", r"[\w.+-]+@(example|test|todo|placeholder)\."),
    "publicationNoFakeFilingNumber": ("Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", r"[\u4e00-\u9fa5]?ICP备0{6,}号?"),
}

EXPECTED_PUBLIC_URLS = {
    "privacy": "https://api.mewpow.com/xiaonaiping/privacy",
    "terms": "https://api.mewpow.com/xiaonaiping/terms",
    "support": "https://api.mewpow.com/xiaonaiping/support",
}

PUBLIC_URL_REQUIREMENTS = {
    "Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md": ("privacy", "terms", "support"),
    "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260629.md": ("privacy", "terms", "support"),
    "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260629.md": ("privacy", "terms", "support"),
    "Docs/08_Release/APP_STORE_METADATA.md": ("privacy", "terms", "support"),
    "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json": ("privacy", "support"),
    "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260629.md": ("privacy",),
    "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md": ("support",),
    "Docs/08_Release/MAINLAND_FILING_MATERIALS.md": ("privacy", "terms", "support"),
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260629.md": ("privacy", "terms", "support"),
    "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md": ("privacy", "terms", "support"),
    "Backend/static/privacy.html": ("privacy", "terms", "support"),
    "Backend/static/terms.html": ("privacy", "terms", "support"),
    "Backend/static/support.html": ("privacy", "terms", "support"),
}

JSON_PUBLIC_URL_FIELDS = {
    "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json": {
        "privacyPolicyUrl": "privacy",
        "supportUrl": "support",
    },
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


def public_url_consistency_failures(root: Path) -> list[str]:
    failures: list[str] = []

    for relative, url_keys in PUBLIC_URL_REQUIREMENTS.items():
        text = read_text(root / relative)
        if not text:
            failures.append(f"{relative} missing")
            continue

        for key in url_keys:
            expected_url = EXPECTED_PUBLIC_URLS[key]
            if expected_url not in text:
                failures.append(f"{relative} missing {expected_url}")

    for relative, fields in JSON_PUBLIC_URL_FIELDS.items():
        text = read_text(root / relative)
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            failures.append(f"{relative} invalid JSON: {exc.msg}")
            continue

        for field_name, key in fields.items():
            expected_url = EXPECTED_PUBLIC_URLS[key]
            actual = data.get(field_name)
            if actual != expected_url:
                failures.append(f"{relative} {field_name} expected {expected_url}, got {actual!r}")

    return failures


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
            "containsSecrets": False,
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(root: Path) -> dict[str, Any]:
    started_at = utc_now()
    report = Report()
    texts = {
        relative: read_text(root / relative)
        for relative, _ in list(REQUIRED_MARKERS.values()) + list(FORBIDDEN_PATTERNS.values())
    }

    for check_name, (relative, marker) in REQUIRED_MARKERS.items():
        passed = marker in texts.get(relative, "")
        report.add(
            check_name,
            passed,
            f"{relative} contains {marker}" if passed else f"{relative} missing {marker}",
        )

    for check_name, (relative, pattern) in FORBIDDEN_PATTERNS.items():
        matched = re.search(pattern, texts.get(relative, "")) is not None
        report.add(
            check_name,
            not matched,
            f"{relative} has no outdated marker"
            if not matched
            else f"{relative} contains outdated marker matching {pattern}",
        )

    public_url_failures = public_url_consistency_failures(root)
    report.add(
        "publicUrlConsistencyAcrossLaunchMaterials",
        not public_url_failures,
        "all launch materials use the expected public URLs"
        if not public_url_failures
        else "; ".join(public_url_failures),
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output", default=str(repo_root() / "Backend/proof/legal-drafts.json"))
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(Path(args.repo_root).resolve())
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"legal drafts proof passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"legal drafts proof incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
