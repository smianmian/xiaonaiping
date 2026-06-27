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
    "privacyUserEnteredStatusSource": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "这些状态展示只反映用户主动记录的数据"),
    "privacyNoHealthPressureFeedingAdvice": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "privacyNoHealthKitOrSensors": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", "不接入 HealthKit、传感器、医院系统或第三方健康数据源"),
    "termsCurrentDate": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "日期：2026-06-24"),
    "termsCompanyEntity": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "深圳市闪现生活科技有限公司"),
    "termsAccountMethods": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "恢复密钥、手机号验证码和微信授权登录"),
    "termsBackupOriginalPhotos": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "用户主动加入 App 的照片原图"),
    "termsDeletion": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "删除云端账号与备份"),
    "termsMedicalBoundary": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "不提供诊断、治疗、预测、处方或专业疫苗建议"),
    "termsStatusDisplayBoundary": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示"),
    "termsUserEnteredStatusSource": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "这些状态展示只反映用户主动记录的数据"),
    "termsNoHealthPressureFeedingAdvice": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "termsNoHealthKitOrSensors": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", "不接入 HealthKit、传感器、医院系统或第三方健康数据源"),
}

FORBIDDEN_PATTERNS = {
    "privacyOutdatedHongKongUsFirst": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", r"首发香港和美国|首發香港和美國"),
    "privacyOutdatedMainlandExcluded": ("Docs/08_Release/PRIVACY_POLICY_DRAFT.md", r"不选择中国大陆|不選擇中國大陸|不含中国大陆|不含中國大陸"),
    "termsOutdatedRecoveryOnly": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", r"账号采用恢复密钥方式|帳號採用恢復密鑰方式"),
    "termsMissingCompanyEntityPlaceholder": ("Docs/08_Release/TERMS_OF_USE_DRAFT.md", r"开发者或公司主体|開發者或公司主體"),
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
