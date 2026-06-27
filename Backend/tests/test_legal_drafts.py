from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_legal_drafts.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_drafts(root: Path, current: bool) -> None:
    if current:
        write(
            root / "Docs/08_Release/PRIVACY_POLICY_DRAFT.md",
            """
# 小奶瓶隐私政策草案

日期：2026-06-24

公司主体：深圳市闪现生活科技有限公司。
第一版计划先上中国大陆 App Store，香港为第二批。
第一版账号支持恢复密钥、手机号和微信登录。
灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。
这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。
不接入 HealthKit、传感器、医院系统或第三方健康数据源。
""".strip(),
        )
        write(
            root / "Docs/08_Release/TERMS_OF_USE_DRAFT.md",
            """
# 小奶瓶用户协议草案

日期：2026-06-24

公司主体：深圳市闪现生活科技有限公司。
第一版账号支持恢复密钥、手机号验证码和微信授权登录。
开启账号与备份后上传用户主动加入 App 的照片原图。
用户可以删除云端账号与备份。
小奶瓶不提供诊断、治疗、预测、处方或专业疫苗建议。
灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。
这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。
不接入 HealthKit、传感器、医院系统或第三方健康数据源。
""".strip(),
        )
        return

    write(
        root / "Docs/08_Release/PRIVACY_POLICY_DRAFT.md",
        "第一版计划首发香港和美国，不选择中国大陆。账号采用恢复密钥。",
    )
    write(
        root / "Docs/08_Release/TERMS_OF_USE_DRAFT.md",
        "第一版账号采用恢复密钥方式。待补开发者或公司主体。",
    )


class LegalDraftsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "legal-drafts.json"
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

    def test_current_legal_drafts_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_drafts(root, current=True)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertFalse(report["containsSecrets"])

    def test_outdated_legal_drafts_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_drafts(root, current=False)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyOutdatedHongKongUsFirst", report["failedRequiredChecks"])
            self.assertIn("privacyOutdatedMainlandExcluded", report["failedRequiredChecks"])
            self.assertIn("termsOutdatedRecoveryOnly", report["failedRequiredChecks"])
            self.assertIn("termsMissingCompanyEntityPlaceholder", report["failedRequiredChecks"])

    def test_legal_drafts_require_status_display_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_drafts(root, current=True)
            privacy = (root / "Docs/08_Release/PRIVACY_POLICY_DRAFT.md").read_text(encoding="utf-8")
            terms = (root / "Docs/08_Release/TERMS_OF_USE_DRAFT.md").read_text(encoding="utf-8")
            for path, text in [
                (root / "Docs/08_Release/PRIVACY_POLICY_DRAFT.md", privacy),
                (root / "Docs/08_Release/TERMS_OF_USE_DRAFT.md", terms),
            ]:
                text = text.replace("灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。\n", "")
                text = text.replace("这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。\n", "")
                path.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyStatusDisplayBoundary", report["failedRequiredChecks"])
            self.assertIn("privacyNoHealthPressureFeedingAdvice", report["failedRequiredChecks"])
            self.assertIn("termsStatusDisplayBoundary", report["failedRequiredChecks"])
            self.assertIn("termsNoHealthPressureFeedingAdvice", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
