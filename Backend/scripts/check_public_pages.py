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
    "privacyPageMainlandFirst": ("privacy.html", "第一版计划先在中国大陆 App Store 提交"),
    "privacyPageHongKongSecond": ("privacy.html", "香港为第二批"),
    "privacyPageCompanyEntity": ("privacy.html", "深圳市闪现生活科技有限公司"),
    "privacyPagePhoneAndWeChatLogin": ("privacy.html", "手机号验证码或微信授权"),
    "privacyPageStatusDisplayBoundary": ("privacy.html", "灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示"),
    "privacyPageNoHealthPressureFeedingAdvice": ("privacy.html", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "privacyPageNoHealthKitOrSensors": ("privacy.html", "不接入 HealthKit、传感器、医院系统或第三方健康数据源"),
    "termsPagePhoneAndWeChatLogin": ("terms.html", "恢复密钥、手机号验证码和微信授权登录"),
    "termsPageCompanyEntity": ("terms.html", "深圳市闪现生活科技有限公司"),
    "termsPageStatusDisplayBoundary": ("terms.html", "灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示"),
    "termsPageNoHealthPressureFeedingAdvice": ("terms.html", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "termsPageNoHealthKitOrSensors": ("terms.html", "不接入 HealthKit、传感器、医院系统或第三方健康数据源"),
    "supportPagePhoneAndWeChatBackup": ("support.html", "恢复密钥、手机号或微信登录"),
    "supportPageCompanyEntity": ("support.html", "深圳市闪现生活科技有限公司"),
    "supportPageStatusDisplayBoundary": ("support.html", "灵动岛、锁屏 Live Activity 和小组件只做状态展示"),
    "supportPageNoHealthPressureFeedingAdvice": ("support.html", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
}

FORBIDDEN_PATTERNS = {
    "privacyOutdatedHongKongUsFirst": ("privacy.html", r"首发香港和美国|首發香港和美國"),
    "privacyOutdatedMainlandExcluded": ("privacy.html", r"不选择中国大陆|不選擇中國大陸|不含中国大陆|不含中國大陸"),
    "termsOutdatedRecoveryOnly": ("terms.html", r"账号采用恢复密钥方式|帳號採用恢復密鑰方式"),
    "supportOutdatedRecoveryOnly": ("support.html", r"中创建账号并备份|中創建帳號並備份"),
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
    static_root = root / "Backend/static"
    report = Report()
    pages = {
        name: read_text(static_root / name)
        for name in ("privacy.html", "terms.html", "support.html")
    }

    for check_name, (page, marker) in REQUIRED_MARKERS.items():
        passed = marker in pages.get(page, "")
        report.add(
            check_name,
            passed,
            f"{page} contains {marker}" if passed else f"{page} missing {marker}",
        )

    for check_name, (page, pattern) in FORBIDDEN_PATTERNS.items():
        matched = re.search(pattern, pages.get(page, "")) is not None
        report.add(
            check_name,
            not matched,
            f"{page} has no outdated marker"
            if not matched
            else f"{page} contains outdated marker matching {pattern}",
        )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output", default=str(repo_root() / "Backend/proof/public-pages.json"))
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(Path(args.repo_root).resolve())
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"public pages proof passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"public pages proof incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
