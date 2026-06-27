from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_review_notes.py"


GOOD_NOTES = """
小奶瓶用于父母或照护者记录宝宝成长。第一版免费，无 IAP，无广告，无第三方分析 SDK，不提供医疗诊断、治疗建议或专业疫苗建议，不是医疗器械。

数据默认本地优先保存。用户可以在“资料 -> 账号与备份”中使用恢复密钥、手机号或微信登录并主动备份。备份会上传宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。手机号和微信登录仅用于账号识别和恢复。

账号删除路径为：“资料 -> 账号与备份 -> 删除云端账号与备份”。该操作会删除账号、云端 JSON 备份和云端照片原图。

疫苗模板仅用于记录和提醒，App 内文案不构成医疗建议。

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。

审核测试登录需使用生产测试手机号和微信测试号；正式提交包不得提供或依赖 debug code。
""".strip()


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_notes(root: Path, complete: bool) -> None:
    notes = GOOD_NOTES if complete else "第一版免费，无广告。"
    write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", f"# Packet\n\n## Review Notes\n\n{notes}\n\n## Next\n")
    write(root / "Docs/08_Release/APP_STORE_METADATA.md", f"# Metadata\n\n## 审核说明草案\n\n{notes}\n\n## Next\n")


class ReviewNotesTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "review-notes.json"
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

    def test_complete_review_notes_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_notes(root, complete=True)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertFalse(report["containsSecrets"])

    def test_incomplete_review_notes_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_notes(root, complete=False)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("submissionReviewNotesOriginalPhotos", report["failedRequiredChecks"])
            self.assertIn("submissionReviewNotesDeletionPath", report["failedRequiredChecks"])
            self.assertIn("submissionReviewNotesNoDebugCode", report["failedRequiredChecks"])

    def test_review_notes_require_status_display_and_advice_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            weak_notes = GOOD_NOTES.replace(
                "这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。",
                "",
            )
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", f"# Packet\n\n## Review Notes\n\n{weak_notes}\n\n## Next\n")
            write(root / "Docs/08_Release/APP_STORE_METADATA.md", f"# Metadata\n\n## 审核说明草案\n\n{GOOD_NOTES}\n\n## Next\n")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("submissionReviewNotesStatusDisplayBoundary", report["failedRequiredChecks"])
            self.assertIn("submissionReviewNotesNoHealthPressureFeedingAdvice", report["failedRequiredChecks"])

    def test_review_notes_reject_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            secret_notes = GOOD_NOTES + "\nXNP_REVIEW_RECOVERY_KEY=secret\nBearer abc.def_123\n13800138000\n"
            write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", f"# Packet\n\n## Review Notes\n\n{secret_notes}\n\n## Next\n")
            write(root / "Docs/08_Release/APP_STORE_METADATA.md", f"# Metadata\n\n## 审核说明草案\n\n{GOOD_NOTES}\n\n## Next\n")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertTrue(report["containsSecrets"])
            self.assertIn("reviewNotesDoNotExposeSecrets", report["failedRequiredChecks"])
            evidence = report["checks"]["reviewNotesDoNotExposeSecrets"]["evidence"]
            self.assertIn("recoveryKeyAssignment", evidence)
            self.assertIn("bearerToken", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)


if __name__ == "__main__":
    unittest.main()
