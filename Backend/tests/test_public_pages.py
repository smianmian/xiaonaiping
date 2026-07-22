from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_public_pages.py"
PRIVACY_URL = "https://api.mewpow.com/xiaonaiping/privacy"
TERMS_URL = "https://api.mewpow.com/xiaonaiping/terms"
SUPPORT_URL = "https://api.mewpow.com/xiaonaiping/support"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_pages(root: Path, current: bool) -> None:
    if current:
        public_urls = f"{PRIVACY_URL} {TERMS_URL} {SUPPORT_URL}"
        write(
            root / "Backend/static/privacy.html",
            f"第一版计划先在中国大陆 App Store 提交。香港为第二批。账号登录可能使用恢复密钥、手机号验证码或微信授权。深圳市闪现生活科技有限公司。你可以手动顺延下一次喝奶提醒：可用 5 分钟一档选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；不根据奶量、月龄、传感器或健康数据自动推算喂养时间。灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。不接入 HealthKit、传感器、医院系统或第三方健康数据源。资料 -> 账号与同步 -> 删除云端账号与同步。{public_urls}",
        )
        write(
            root / "Backend/static/terms.html",
            f"第一版账号支持恢复密钥、手机号验证码和微信授权登录。深圳市闪现生活科技有限公司。你可以手动顺延下一次喝奶提醒：可用 5 分钟一档选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；不根据奶量、月龄、传感器或健康数据自动推算喂养时间。灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。不接入 HealthKit、传感器、医院系统或第三方健康数据源。资料 -> 账号与同步 -> 删除云端账号与同步。{public_urls}",
        )
        write(
            root / "Backend/static/support.html",
            f"小奶瓶 - 宝宝成长记录 App 官方网站。首页。产品展示。应用截图。应用介绍。业务流程。应用运行流程图。应用下载与上架状态。support-assets/app-icon-108.png。rel=\"icon\"。support-assets/screenshot-home.jpg。support-assets/screenshot-record.jpg。support-assets/screenshot-sync.jpg。support-assets/operation-flow.jpg。通过恢复密钥、手机号或微信登录后同步。资料 -> 账号与同步 -> 删除云端账号与同步。深圳市闪现生活科技有限公司。版权所有者：深圳市闪现生活科技有限公司。support@mewpow.com。网站备案信息。当前页面不声明已完成备案。可以手动顺延下一次喝奶提醒：可用 5 分钟一档选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；不根据奶量、月龄、传感器或健康数据自动推算喂养时间。灵动岛、锁屏 Live Activity 和小组件只做状态展示，不生成健康建议、压力提醒、喂养建议或医疗判断。{public_urls}",
        )
        return

    write(
        root / "Backend/static/privacy.html",
        "第一版计划首发香港和美国，不选择中国大陆。账号登录可能使用恢复密钥。",
    )
    write(root / "Backend/static/terms.html", "第一版账号采用恢复密钥方式。")
    write(root / "Backend/static/support.html", "在 App 的资料中创建账号并同步。")


class PublicPagesTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "public-pages.json"
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

    def test_current_public_pages_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_pages(root, current=True)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])

    def test_outdated_region_and_account_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_pages(root, current=False)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyOutdatedHongKongUsFirst", report["failedRequiredChecks"])
            self.assertIn("privacyOutdatedMainlandExcluded", report["failedRequiredChecks"])
            self.assertIn("termsOutdatedRecoveryOnly", report["failedRequiredChecks"])
            self.assertIn("supportOutdatedRecoveryOnly", report["failedRequiredChecks"])

    def test_public_pages_require_status_display_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_pages(root, current=True)
            for page in ["privacy.html", "terms.html", "support.html"]:
                path = root / "Backend/static" / page
                text = path.read_text(encoding="utf-8")
                text = text.replace("灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。", "")
                text = text.replace("灵动岛、锁屏 Live Activity 和小组件只做状态展示，", "")
                text = text.replace("不生成健康建议、压力提醒、喂养建议或医疗判断", "")
                path.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyPageStatusDisplayBoundary", report["failedRequiredChecks"])
            self.assertIn("termsPageNoHealthPressureFeedingAdvice", report["failedRequiredChecks"])
            self.assertIn("supportPageStatusDisplayBoundary", report["failedRequiredChecks"])

    def test_public_pages_require_manual_deferral_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_pages(root, current=True)
            for page in ["privacy.html", "terms.html", "support.html"]:
                path = root / "Backend/static" / page
                text = path.read_text(encoding="utf-8")
                text = text.replace("你可以手动顺延下一次喝奶提醒：可用 5 分钟一档选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。", "")
                text = text.replace("可以手动顺延下一次喝奶提醒：可用 5 分钟一档选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。", "")
                text = text.replace("保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。", "")
                text = text.replace("顺延只改变下一次提醒时间，不新增持久化字段；", "")
                text = text.replace("不根据奶量、月龄、传感器或健康数据自动推算喂养时间。", "")
                path.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyPageManualReminderDeferral", report["failedRequiredChecks"])
            self.assertIn("privacyPageReminderDeferralGranularity", report["failedRequiredChecks"])
            self.assertIn("privacyPageReminderDeferralOptions", report["failedRequiredChecks"])
            self.assertIn("privacyPageReminderDeferralCalculation", report["failedRequiredChecks"])
            self.assertIn("privacyPageReminderNoDurationFallback", report["failedRequiredChecks"])
            self.assertIn("privacyPageReminderNoPersistentField", report["failedRequiredChecks"])
            self.assertIn("termsPageNoAutomaticFeedingInference", report["failedRequiredChecks"])
            self.assertIn("supportPageManualReminderDeferral", report["failedRequiredChecks"])
            self.assertIn("supportPageReminderDeferralGranularity", report["failedRequiredChecks"])
            self.assertIn("supportPageReminderDeferralOptions", report["failedRequiredChecks"])
            self.assertIn("supportPageReminderDeferralCalculation", report["failedRequiredChecks"])
            self.assertIn("supportPageReminderNoDurationFallback", report["failedRequiredChecks"])
            self.assertIn("supportPageReminderNoPersistentField", report["failedRequiredChecks"])

    def test_public_pages_require_account_deletion_path(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_pages(root, current=True)
            for page in ["privacy.html", "terms.html", "support.html"]:
                path = root / "Backend/static" / page
                text = path.read_text(encoding="utf-8").replace("资料 -> 账号与同步 -> 删除云端账号与同步。", "")
                path.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyPageAccountDeletionPath", report["failedRequiredChecks"])
            self.assertIn("termsPageAccountDeletionPath", report["failedRequiredChecks"])
            self.assertIn("supportPageAccountDeletionPath", report["failedRequiredChecks"])

    def test_support_page_requires_official_website_review_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_pages(root, current=True)
            path = root / "Backend/static/support.html"
            text = path.read_text(encoding="utf-8")
            for marker in [
                "小奶瓶 - 宝宝成长记录 App 官方网站",
                "首页",
                "产品展示",
                "应用截图",
                "应用介绍",
                "业务流程",
                "应用运行流程图",
                "应用下载与上架状态",
                "support-assets/app-icon-108.png",
                'rel="icon"',
                "support-assets/screenshot-home.jpg",
                "support-assets/screenshot-record.jpg",
                "support-assets/screenshot-sync.jpg",
                "support-assets/operation-flow.jpg",
                "版权所有者：深圳市闪现生活科技有限公司",
                "support@mewpow.com",
                "网站备案信息",
                "当前页面不声明已完成备案",
            ]:
                text = text.replace(marker, "")
            path.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("supportPageOfficialWebsiteTitle", report["failedRequiredChecks"])
            self.assertIn("supportPageHomepage", report["failedRequiredChecks"])
            self.assertIn("supportPageProductShowcase", report["failedRequiredChecks"])
            self.assertIn("supportPageAppScreenshots", report["failedRequiredChecks"])
            self.assertIn("supportPageAppIntroduction", report["failedRequiredChecks"])
            self.assertIn("supportPageBusinessFlow", report["failedRequiredChecks"])
            self.assertIn("supportPageOperationFlowImage", report["failedRequiredChecks"])
            self.assertIn("supportPageDownloadStatus", report["failedRequiredChecks"])
            self.assertIn("supportPageAppIconAsset", report["failedRequiredChecks"])
            self.assertIn("supportPageFavicon", report["failedRequiredChecks"])
            self.assertIn("supportPageHomeScreenshotAsset", report["failedRequiredChecks"])
            self.assertIn("supportPageRecordScreenshotAsset", report["failedRequiredChecks"])
            self.assertIn("supportPageSyncScreenshotAsset", report["failedRequiredChecks"])
            self.assertIn("supportPageOperationFlowAsset", report["failedRequiredChecks"])
            self.assertIn("supportPageCopyrightOwner", report["failedRequiredChecks"])
            self.assertIn("supportPageContactEmail", report["failedRequiredChecks"])
            self.assertIn("supportPageWebsiteFilingInfo", report["failedRequiredChecks"])
            self.assertIn("supportPageNoCompletedFilingClaim", report["failedRequiredChecks"])

    def test_public_pages_require_public_url_links(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_pages(root, current=True)
            for page in ["privacy.html", "terms.html", "support.html"]:
                path = root / "Backend/static" / page
                text = path.read_text(encoding="utf-8").replace(SUPPORT_URL, "")
                path.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyPageSupportURL", report["failedRequiredChecks"])
            self.assertIn("termsPageSupportURL", report["failedRequiredChecks"])
            self.assertIn("supportPageSupportURL", report["failedRequiredChecks"])

    def test_public_pages_reject_placeholder_filing_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_pages(root, current=True)
            placeholders = {
                "privacy.html": "ICP备000000号",
                "terms.html": "ICP备待补",
                "support.html": "placeholder filing",
            }
            for page, placeholder in placeholders.items():
                path = root / "Backend/static" / page
                text = path.read_text(encoding="utf-8") + placeholder
                path.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyNoPlaceholderFilingNumber", report["failedRequiredChecks"])
            self.assertIn("termsNoPlaceholderFilingNumber", report["failedRequiredChecks"])
            self.assertIn("supportNoPlaceholderFilingNumber", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
