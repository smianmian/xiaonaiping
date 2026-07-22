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
    "reviewNotesFree": ("第一版免费",),
    "reviewNotesNoIAP": ("无 IAP", "无内购"),
    "reviewNotesNoAds": ("无广告",),
    "reviewNotesNoThirdPartyAnalytics": ("无第三方分析 SDK",),
    "reviewNotesNoMedicalAdvice": ("不提供医疗诊断", "不构成医疗建议"),
    "reviewNotesNoMedicalDevice": ("不是医疗器械", "不作为医疗器械"),
    "reviewNotesLocalFirst": ("本地优先",),
    "reviewNotesAccountMethods": ("恢复密钥", "手机号", "微信"),
    "reviewNotesPrivateSync": ("主动同步", "私有同步"),
    "reviewNotesOriginalPhotos": ("照片原图",),
    "reviewNotesDeletionPath": ("资料 -> 账号与同步 -> 删除云端账号与同步",),
    "reviewNotesVaccineBoundary": ("疫苗模板仅用于记录和提醒",),
    "reviewNotesLiveActivityBoundary": ("灵动岛", "锁屏", "Live Activity"),
    "reviewNotesWidgetBoundary": ("小组件", "Widget"),
    "reviewNotesStatusDisplayBoundary": ("状态展示",),
    "reviewNotesManualFeedingReminderDeferral": ("手动顺延下一次提醒",),
    "reviewNotesFeedingReminderDeferralGranularity": ("5 分钟一档",),
    "reviewNotesFeedingReminderDeferralOptions": ("+5、+10、+15、+20、+25、+30 分钟", "0-30 分钟"),
    "reviewNotesFeedingReminderDeferralCalculation": ("本顿结束时间 + 固定间隔 + 顺延分钟",),
    "reviewNotesFeedingReminderNoDurationFallback": ("本顿发生时间",),
    "reviewNotesFeedingReminderNoPersistentField": ("不新增持久化字段",),
    "reviewNotesNoAutomaticFeedingInference": ("不根据奶量、月龄、传感器或健康数据自动推算喂养时间",),
    "reviewNotesUserEnteredDataSource": ("用户在 App 内输入", "本机记录", "用户主动记录"),
    "reviewNotesNoHealthKitOrPressure": ("不接入 HealthKit", "不提供压力评估", "无压力"),
    "reviewNotesNoHealthPressureFeedingAdvice": ("不生成健康建议、压力提醒、喂养建议",),
    "reviewNotesNoDebugCode": ("不得提供或依赖 debug code", "不允许使用 debug code"),
}

FORBIDDEN_SECRET_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
    "placeholderFilingNumber": re.compile(r"ICP备0{4,}号?|ICP备待|待备案号|占位备案号|示例备案号|placeholder filing", re.IGNORECASE),
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
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str, contains_secrets: bool) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "containsSecrets": contains_secrets,
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def add_section_checks(report: Report, prefix: str, source: str, text: str) -> None:
    report.add(
        prefix + "Present",
        bool(text),
        f"{source} Review Notes section present" if text else f"{source} missing Review Notes section",
    )
    for name, markers in REQUIRED_MARKERS.items():
        passed = any(marker in text for marker in markers)
        report.add(
            prefix + name[0].upper() + name[1:],
            passed,
            f"{source} contains one of: " + ", ".join(markers)
            if passed
            else f"{source} missing one of: " + ", ".join(markers),
        )


def forbidden_secret_hits(sections: dict[str, str]) -> list[str]:
    hits: list[str] = []
    for source, text in sections.items():
        for name, pattern in FORBIDDEN_SECRET_PATTERNS.items():
            if pattern.search(text):
                hits.append(f"{source}:{name}")
    return sorted(hits)


def build_report(root: Path) -> dict[str, Any]:
    started_at = utc_now()
    report = Report()

    submission = read_text(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md")
    metadata = read_text(root / "Docs/08_Release/APP_STORE_METADATA.md")
    submission_notes = extract_section(submission, "Review Notes")
    metadata_notes = extract_section(metadata, "审核说明草案")

    add_section_checks(report, "submission", "APP_STORE_SUBMISSION_PACKET.md", submission_notes)
    add_section_checks(report, "metadata", "APP_STORE_METADATA.md", metadata_notes)
    secret_hits = forbidden_secret_hits(
        {
            "APP_STORE_SUBMISSION_PACKET.md": submission_notes,
            "APP_STORE_METADATA.md": metadata_notes,
        }
    )
    report.add(
        "reviewNotesDoNotExposeSecrets",
        not secret_hits,
        "found: " + ", ".join(secret_hits) if secret_hits else "review notes do not expose recovery keys, tokens, debug codes, API keys, or complete phone numbers",
    )

    return report.to_dict(started_at, utc_now(), contains_secrets=bool(secret_hits))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output", default=str(repo_root() / "Backend/proof/review-notes.json"))
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(Path(args.repo_root).resolve())
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"review notes proof passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"review notes proof incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
