from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_public_pages.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_pages(root: Path, current: bool) -> None:
    if current:
        write(
            root / "Backend/static/privacy.html",
            "第一版计划先在中国大陆 App Store 提交。香港为第二批。账号登录可能使用恢复密钥、手机号验证码或微信授权。深圳市闪现生活科技有限公司。灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。不接入 HealthKit、传感器、医院系统或第三方健康数据源。",
        )
        write(
            root / "Backend/static/terms.html",
            "第一版账号支持恢复密钥、手机号验证码和微信授权登录。深圳市闪现生活科技有限公司。灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。不接入 HealthKit、传感器、医院系统或第三方健康数据源。",
        )
        write(
            root / "Backend/static/support.html",
            "通过恢复密钥、手机号或微信登录后备份。深圳市闪现生活科技有限公司。灵动岛、锁屏 Live Activity 和小组件只做状态展示，不生成健康建议、压力提醒、喂养建议或医疗判断。",
        )
        return

    write(
        root / "Backend/static/privacy.html",
        "第一版计划首发香港和美国，不选择中国大陆。账号登录可能使用恢复密钥。",
    )
    write(root / "Backend/static/terms.html", "第一版账号采用恢复密钥方式。")
    write(root / "Backend/static/support.html", "在 App 的资料中创建账号并备份。")


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


if __name__ == "__main__":
    unittest.main()
