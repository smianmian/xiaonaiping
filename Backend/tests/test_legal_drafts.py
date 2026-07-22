from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_legal_drafts.py"
PRIVACY_URL = "https://api.mewpow.com/xiaonaiping/privacy"
TERMS_URL = "https://api.mewpow.com/xiaonaiping/terms"
SUPPORT_URL = "https://api.mewpow.com/xiaonaiping/support"


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
保存新喂养时，如果已设置固定喝奶间隔，提醒顺延由你手动选择：可用 5 分钟一档选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；小奶瓶不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。
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
开启账号与同步后上传用户主动加入 App 的照片原图。
用户可以删除云端账号与同步。
小奶瓶不提供诊断、治疗、预测、处方或专业疫苗建议。
灵动岛、锁屏 Live Activity 和桌面/锁屏小组件只做状态展示。
保存新喂养时，如果已设置固定喝奶间隔，提醒顺延由你手动选择：可用 5 分钟一档选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；小奶瓶不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。
这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。
不接入 HealthKit、传感器、医院系统或第三方健康数据源。
""".strip(),
        )
        write(
            root / "Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md",
            """
# 小奶瓶法务页面发布交接表

日期：2026-06-29

隐私政策 URL：https://api.mewpow.com/xiaonaiping/privacy
用户协议 URL：https://api.mewpow.com/xiaonaiping/terms
支持 URL：https://api.mewpow.com/xiaonaiping/support
公司主体：深圳市闪现生活科技有限公司。
发布前补齐隐私联系邮箱和支持邮箱。
第三方/平台服务：短信服务商、微信开放平台、Apple TestFlight / App Store Connect、华为云 OBS。
删除 SLA 需要覆盖账号删除、云端 JSON 同步删除和云端照片原图删除。
拿到真实 App 备案 / ICP 编号后再更新公开页面。

## 公开 URL 一致性清单

不要只改一处 URL。
APP_STORE_CONNECT_FILL_SHEET_20260629.md
APP_STORE_CONNECT_COPY_PASTE_20260629.md
APP_STORE_METADATA.md
APP_STORE_PRIVACY_LABEL.json
APP_STORE_PRIVACY_ANSWERS_20260629.md
APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md
MAINLAND_FILING_MATERIALS.md
XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260629.md
APP_STORE_SUBMISSION_PACKET.md
Backend/static/privacy.html
Backend/static/terms.html
Backend/static/support.html
RealDevice/RD-19-public-urls.png
check_app_store_connect_materials.py

不得写占位邮箱、测试邮箱、个人邮箱或未确认的隐私联系邮箱。
不得声称短信服务商、微信开放平台、OBS、备案、TestFlight 或 App Store Connect 人工证据已完成。
不得把小奶瓶描述为医疗器械、诊断工具、治疗工具、健康建议工具、压力评估工具或自动喂养建议工具。
发布当天复跑 check_public_pages.py。
""".strip(),
        )
        all_urls = f"{PRIVACY_URL}\n{TERMS_URL}\n{SUPPORT_URL}\n"
        for relative in [
            "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260629.md",
            "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260629.md",
            "Docs/08_Release/APP_STORE_METADATA.md",
            "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
            "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260629.md",
            "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
            "Backend/static/privacy.html",
            "Backend/static/terms.html",
            "Backend/static/support.html",
        ]:
            write(root / relative, all_urls)
        write(
            root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
            json.dumps(
                {
                    "privacyPolicyUrl": PRIVACY_URL,
                    "supportUrl": SUPPORT_URL,
                },
                ensure_ascii=False,
            ),
        )
        write(root / "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260629.md", f"| Privacy Policy URL | `{PRIVACY_URL}` |")
        write(root / "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md", f"| Support URL | `{SUPPORT_URL}` |")
        return

    write(
        root / "Docs/08_Release/PRIVACY_POLICY_DRAFT.md",
        "第一版计划首发香港和美国，不选择中国大陆。账号采用恢复密钥。",
    )
    write(
        root / "Docs/08_Release/TERMS_OF_USE_DRAFT.md",
        "第一版账号采用恢复密钥方式。待补开发者或公司主体。",
    )
    write(root / "Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md", "privacy@example.com\nICP备000000号")


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

    def test_legal_drafts_require_manual_deferral_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_drafts(root, current=True)
            privacy = (root / "Docs/08_Release/PRIVACY_POLICY_DRAFT.md").read_text(encoding="utf-8")
            terms = (root / "Docs/08_Release/TERMS_OF_USE_DRAFT.md").read_text(encoding="utf-8")
            for path, text in [
                (root / "Docs/08_Release/PRIVACY_POLICY_DRAFT.md", privacy),
                (root / "Docs/08_Release/TERMS_OF_USE_DRAFT.md", terms),
            ]:
                text = text.replace(
                    "保存新喂养时，如果已设置固定喝奶间隔，提醒顺延由你手动选择：可用 5 分钟一档选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；小奶瓶不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。\n",
                    "",
                )
                path.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyManualReminderDeferral", report["failedRequiredChecks"])
            self.assertIn("privacyReminderDeferralGranularity", report["failedRequiredChecks"])
            self.assertIn("privacyReminderDeferralOptions", report["failedRequiredChecks"])
            self.assertIn("privacyReminderDeferralCalculation", report["failedRequiredChecks"])
            self.assertIn("privacyReminderNoDurationFallback", report["failedRequiredChecks"])
            self.assertIn("privacyReminderNoPersistentField", report["failedRequiredChecks"])
            self.assertIn("privacyNoAutomaticFeedingInference", report["failedRequiredChecks"])
            self.assertIn("termsManualReminderDeferral", report["failedRequiredChecks"])
            self.assertIn("termsReminderDeferralGranularity", report["failedRequiredChecks"])
            self.assertIn("termsReminderDeferralOptions", report["failedRequiredChecks"])
            self.assertIn("termsReminderDeferralCalculation", report["failedRequiredChecks"])
            self.assertIn("termsReminderNoDurationFallback", report["failedRequiredChecks"])
            self.assertIn("termsReminderNoPersistentField", report["failedRequiredChecks"])
            self.assertIn("termsNoAutomaticFeedingInference", report["failedRequiredChecks"])

    def test_legal_publication_handoff_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_drafts(root, current=True)
            handoff = root / "Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md"
            text = handoff.read_text(encoding="utf-8")
            text = text.replace("隐私联系邮箱", "").replace("不得声称短信服务商、微信开放平台、OBS、备案、TestFlight 或 App Store Connect 人工证据已完成。", "")
            handoff.write_text(text + "\nprivacy@example.com\n", encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("publicationHandoffPrivacyEmail", report["failedRequiredChecks"])
            self.assertIn("publicationHandoffNoPretendEvidence", report["failedRequiredChecks"])
            self.assertIn("publicationNoPlaceholderEmail", report["failedRequiredChecks"])

    def test_legal_publication_handoff_requires_url_consistency_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_drafts(root, current=True)
            handoff = root / "Docs/08_Release/LEGAL_PUBLICATION_HANDOFF_20260629.md"
            text = handoff.read_text(encoding="utf-8")
            text = text.replace("## 公开 URL 一致性清单", "## URL")
            text = text.replace("APP_STORE_CONNECT_COPY_PASTE_20260629.md\n", "")
            text = text.replace("APP_STORE_PRIVACY_LABEL.json\n", "")
            text = text.replace("MAINLAND_FILING_MATERIALS.md\n", "")
            text = text.replace("RealDevice/RD-19-public-urls.png\n", "")
            text = text.replace("不要只改一处 URL。\n", "")
            handoff.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("publicationHandoffUrlConsistencyChecklist", report["failedRequiredChecks"])
            self.assertIn("publicationHandoffUrlConsistencyCopyPaste", report["failedRequiredChecks"])
            self.assertIn("publicationHandoffUrlConsistencyPrivacyLabel", report["failedRequiredChecks"])
            self.assertIn("publicationHandoffUrlConsistencyFiling", report["failedRequiredChecks"])
            self.assertIn("publicationHandoffUrlConsistencyEvidence", report["failedRequiredChecks"])
            self.assertIn("publicationHandoffUrlConsistencyNoPartialUpdate", report["failedRequiredChecks"])

    def test_public_url_consistency_across_launch_materials_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_drafts(root, current=True)
            copy_paste = root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260629.md"
            copy_paste.write_text(
                copy_paste.read_text(encoding="utf-8").replace(SUPPORT_URL, "https://api.example.com/support"),
                encoding="utf-8",
            )
            privacy_label = root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json"
            data = json.loads(privacy_label.read_text(encoding="utf-8"))
            data["supportUrl"] = "https://api.example.com/support"
            privacy_label.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            support_page = root / "Backend/static/support.html"
            support_page.write_text(
                support_page.read_text(encoding="utf-8").replace(TERMS_URL, ""),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("publicUrlConsistencyAcrossLaunchMaterials", report["failedRequiredChecks"])
            evidence = report["checks"]["publicUrlConsistencyAcrossLaunchMaterials"]["evidence"]
            self.assertIn("APP_STORE_CONNECT_COPY_PASTE_20260629.md", evidence)
            self.assertIn("APP_STORE_PRIVACY_LABEL.json supportUrl", evidence)
            self.assertIn("Backend/static/support.html", evidence)


if __name__ == "__main__":
    unittest.main()
