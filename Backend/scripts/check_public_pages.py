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
    "privacyPageGlobalLaunch": ("privacy.html", "已在 App Store 按全球同步上线策略正式发布"),
    "privacyPageFilingCompleted": ("privacy.html", "小奶瓶 APP 备案已完成"),
    "privacyPageFilingNumber": ("privacy.html", "粤ICP备2025379333号"),
    "privacyPageCompanyEntity": ("privacy.html", "深圳市闪现生活科技有限公司"),
    "privacyPagePhoneAndWeChatLogin": ("privacy.html", "手机号验证码或微信授权"),
    "privacyPageStatusDisplayBoundary": ("privacy.html", "灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示"),
    "privacyPageManualReminderDeferral": ("privacy.html", "你可以手动顺延下一次喝奶提醒"),
    "privacyPageReminderDeferralGranularity": ("privacy.html", "5 分钟一档"),
    "privacyPageReminderDeferralOptions": ("privacy.html", "+5、+10、+15、+20、+25、+30 分钟"),
    "privacyPageReminderDeferralCalculation": ("privacy.html", "本顿结束时间 + 固定间隔 + 顺延分钟"),
    "privacyPageReminderNoDurationFallback": ("privacy.html", "本顿发生时间"),
    "privacyPageReminderNoPersistentField": ("privacy.html", "不新增持久化字段"),
    "privacyPageNoAutomaticFeedingInference": ("privacy.html", "不根据奶量、月龄、传感器或健康数据自动推算喂养时间"),
    "privacyPageNoHealthPressureFeedingAdvice": ("privacy.html", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "privacyPageNoHealthKitOrSensors": ("privacy.html", "不接入 HealthKit、传感器、医院系统或第三方健康数据源"),
    "privacyPageAccountDeletionPath": ("privacy.html", "资料 -> 账号与同步 -> 删除云端账号与同步"),
    "termsPagePhoneAndWeChatLogin": ("terms.html", "手机号验证码和微信授权登录"),
    "termsPageCompanyEntity": ("terms.html", "深圳市闪现生活科技有限公司"),
    "termsPageStatusDisplayBoundary": ("terms.html", "灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示"),
    "termsPageManualReminderDeferral": ("terms.html", "你可以手动顺延下一次喝奶提醒"),
    "termsPageReminderDeferralGranularity": ("terms.html", "5 分钟一档"),
    "termsPageReminderDeferralOptions": ("terms.html", "+5、+10、+15、+20、+25、+30 分钟"),
    "termsPageReminderDeferralCalculation": ("terms.html", "本顿结束时间 + 固定间隔 + 顺延分钟"),
    "termsPageReminderNoDurationFallback": ("terms.html", "本顿发生时间"),
    "termsPageReminderNoPersistentField": ("terms.html", "不新增持久化字段"),
    "termsPageNoAutomaticFeedingInference": ("terms.html", "不根据奶量、月龄、传感器或健康数据自动推算喂养时间"),
    "termsPageNoHealthPressureFeedingAdvice": ("terms.html", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "termsPageNoHealthKitOrSensors": ("terms.html", "不接入 HealthKit、传感器、医院系统或第三方健康数据源"),
    "termsPageAccountDeletionPath": ("terms.html", "资料 -> 账号与同步 -> 删除云端账号与同步"),
    "supportPagePhoneAndWeChatSync": ("support.html", "手机号验证码或微信授权登录"),
    "supportPageCompanyEntity": ("support.html", "深圳市闪现生活科技有限公司"),
    "supportPageOfficialWebsiteTitle": ("support.html", "小奶瓶 - 宝宝成长记录 App 官方网站"),
    "supportPageHomepage": ("support.html", "首页"),
    "supportPageProductShowcase": ("support.html", "产品展示"),
    "supportPageAppScreenshots": ("support.html", "应用截图"),
    "supportPageAppIntroduction": ("support.html", "应用介绍"),
    "supportPageBusinessFlow": ("support.html", "业务流程"),
    "supportPageOperationFlowImage": ("support.html", "应用运行流程图"),
    "supportPageDownloadStatus": ("support.html", "应用下载与上架状态"),
    "supportPageAppIconAsset": ("support.html", "support-assets/app-icon-108.png"),
    "supportPageFavicon": ("support.html", 'rel="icon"'),
    "supportPageHomeScreenshotAsset": ("support.html", "support-assets/screenshot-home.jpg"),
    "supportPageRecordScreenshotAsset": ("support.html", "support-assets/screenshot-record.jpg"),
    "supportPageOperationFlowAsset": ("support.html", "support-assets/operation-flow.jpg"),
    "supportPageCopyrightOwner": ("support.html", "版权所有者：深圳市闪现生活科技有限公司"),
    "supportPageContactEmail": ("support.html", "support@mewpow.com"),
    "supportPageWebsiteFilingInfo": ("support.html", "网站备案信息"),
    "supportPageFilingCompleted": ("support.html", "小奶瓶 APP 备案已完成"),
    "supportPageFilingNumber": ("support.html", "粤ICP备2025379333号"),
    "supportPageStatusDisplayBoundary": ("support.html", "灵动岛、锁屏 Live Activity 和小组件只做状态展示"),
    "supportPageManualReminderDeferral": ("support.html", "手动顺延下一次喝奶提醒"),
    "supportPageReminderDeferralGranularity": ("support.html", "5 分钟一档"),
    "supportPageReminderDeferralOptions": ("support.html", "+5、+10、+15、+20、+25、+30 分钟"),
    "supportPageReminderDeferralCalculation": ("support.html", "本顿结束时间 + 固定间隔 + 顺延分钟"),
    "supportPageReminderNoDurationFallback": ("support.html", "本顿发生时间"),
    "supportPageReminderNoPersistentField": ("support.html", "不新增持久化字段"),
    "supportPageNoAutomaticFeedingInference": ("support.html", "不根据奶量、月龄、传感器或健康数据自动推算喂养时间"),
    "supportPageNoHealthPressureFeedingAdvice": ("support.html", "不生成健康建议、压力提醒、喂养建议或医疗判断"),
    "supportPageAccountDeletionPath": ("support.html", "资料 -> 账号与同步 -> 删除云端账号与同步"),
}

PUBLIC_URL_MARKERS = {
    "privacyPagePrivacyURL": ("privacy.html", "https://api.mewpow.com/xiaonaiping/privacy"),
    "privacyPageTermsURL": ("privacy.html", "https://api.mewpow.com/xiaonaiping/terms"),
    "privacyPageSupportURL": ("privacy.html", "https://api.mewpow.com/xiaonaiping/support"),
    "termsPagePrivacyURL": ("terms.html", "https://api.mewpow.com/xiaonaiping/privacy"),
    "termsPageTermsURL": ("terms.html", "https://api.mewpow.com/xiaonaiping/terms"),
    "termsPageSupportURL": ("terms.html", "https://api.mewpow.com/xiaonaiping/support"),
    "supportPagePrivacyURL": ("support.html", "https://api.mewpow.com/xiaonaiping/privacy"),
    "supportPageTermsURL": ("support.html", "https://api.mewpow.com/xiaonaiping/terms"),
    "supportPageSupportURL": ("support.html", "https://api.mewpow.com/xiaonaiping/support"),
}

FORBIDDEN_PATTERNS = {
    "privacyOutdatedHongKongUsFirst": ("privacy.html", r"首发香港和美国|首發香港和美國"),
    "privacyOutdatedMainlandExcluded": ("privacy.html", r"不选择中国大陆|不選擇中國大陸|不含中国大陆|不含中國大陸"),
    "privacyOutdatedPhasedLaunch": ("privacy.html", r"先在中国大陆.*香港为第二批|香港为第二批|分批上线|分阶段上线"),
    "privacyNoPlaceholderFilingNumber": ("privacy.html", r"ICP备0{4,}号?|ICP备待|待备案号|占位备案号|示例备案号|placeholder filing"),
    "termsNoPlaceholderFilingNumber": ("terms.html", r"ICP备0{4,}号?|ICP备待|待备案号|占位备案号|示例备案号|placeholder filing"),
    "supportOutdatedRecoveryOnly": ("support.html", r"中创建账号并同步|中創建帳號並同步"),
    "supportNoPlaceholderFilingNumber": ("support.html", r"ICP备0{4,}号?|ICP备待|待备案号|占位备案号|示例备案号|placeholder filing"),
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

    for check_name, (page, marker) in PUBLIC_URL_MARKERS.items():
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
