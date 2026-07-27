from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_app_store_connect_evidence_materials.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_fill_sheet() -> str:
    return """
# 小奶瓶 App Store Connect 填表版

| 字段 | 填写内容 |
| --- | --- |
| App 名称 | 小奶瓶 |
| Bundle ID | `com.mewpow.xiaonaiping` |
| 首发地区 | Specific Countries or Regions -> China mainland |
| 第二批地区 | Hong Kong |
| 版权 | `© 2026 深圳市闪现生活科技有限公司` |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` |
| 技术支持 URL | `https://api.mewpow.com/xiaonaiping/support` |

以 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` 为最终源文件。

Identifiers, Contact Info, User Content, Photos or Videos, Health and Fitness, Usage Data, Diagnostics。
是否追踪：否。不接入 HealthKit，不提供压力评估。
""".lstrip()


def valid_packet() -> str:
    return """
# APP_STORE_SUBMISSION_PACKET.md

## Pre-Submit Commands

```bash
python3 Backend/scripts/check_app_store_connect_materials.py
python3 Backend/scripts/check_app_store_connect_evidence_materials.py
python3 Backend/scripts/check_app_store_evidence.py
```
""".lstrip()


def valid_runbook() -> str:
    return """
# CHINA_MAINLAND_APP_STORE_RUNBOOK.md

1. `01-company-account.png`：深圳市闪现生活科技有限公司主体截图。
2. `02-mainland-availability.png`：只选择中国大陆可售地区截图。
4. `04-privacy-label.png`：App Store Connect 隐私标签截图。
""".lstrip()


def valid_readme() -> str:
    return """
# AppStoreEvidence

| 文件名 | 证明什么 | 脱敏要求 | 当前状态 |
| --- | --- | --- | --- |
| `01-company-account.png` | App Store Connect 主体为深圳市闪现生活科技有限公司 | 遮邮箱、电话、付款信息 | 未完成 |
| `02-mainland-availability.png` | 只选择 China mainland 首发 | 不展示无关账号信息 | 未完成 |
| `04-privacy-label.png` | App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写 | 不展示账号隐私信息 | 未完成 |
""".lstrip()


def valid_capture_guide(date: str = "20260704") -> str:
    return """
# CAPTURE_GUIDE.md

| 文件 | 必须能证明 | 保留字段 | 必须遮挡 |
|---|---|---|---|
| `01-company-account.png` | App Store Connect 账号主体为深圳市闪现生活科技有限公司，且 D-U-N-S 后 Apple Developer Organization / Team ID 已确认 | 团队/法律主体名称、账号页标题、Apple Developer Organization、Team ID | 邮箱、电话、付款信息、D-U-N-S 编码完整值 |
| `02-mainland-availability.png` | 首发只选 China mainland / 中国大陆 | App 名称、可售地区选择状态 | 无关账号信息 |
| `04-privacy-label.png` | App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写 | 已采集类别、未追踪、用途 | 账号邮箱 |
| `17-age-rating-result.png` 或 `.pdf` | App Store Connect 年龄分级结果已按答案表完成 | 年龄分级结果、关键问答项、与 `APP_STORE_AGE_RATING_ANSWERS_{date}.md` 一致 | Apple ID 邮箱、电话、付款信息 |
""".lstrip().format(date=date)


def valid_asc_execution_sheet() -> str:
    return """
# 小奶瓶 App Store Connect 回填截图现场执行单

| 文件 | 页面 | 必须看见 | 必须隐藏 | 通过口径 |
| --- | --- | --- | --- | --- |
| `ASC-04-app-privacy.png` | App Privacy | Tracking=No、隐私标签数据类别、与 `APP_STORE_PRIVACY_LABEL.json` 一致 | Apple ID 邮箱、账号私密信息 | 不声明追踪 |
| `ASC-05-age-rating.png` | Age Rating | Age Rating、Kids Category 未选择、疫苗记录/提醒相关回答、Regulated Medical Device 回答 | Apple ID 邮箱、完整手机号、付款信息 | 疫苗模板仅用于记录和提醒 |
| `ASC-06-review-information.png` | App Review Information | Sign-in required、审核备注、联系人字段已填、短信服务商、微信开放平台、恢复密钥测试说明 | 验证码、完整手机号、恢复密钥、AppSecret、Apple ID 邮箱 | 私密字段脱敏后入库 |
| `ASC-PRIVACY-AGE-REVIEW-RESULT.json` | ASC-04/05/06 结果复核 | `status: captured-live-privacy-age-review`、ASC-04/05/06、`04-privacy-label`、`17-age-rating-result`、`11-test-account-redacted`、answer-sheet matching、post-result gates | 恢复密钥、验证码、完整手机号、Apple ID 邮箱、联系人完整电话、AppSecret、短信密钥、微信密钥、OBS AK/SK、付款/税务信息、完整 D-U-N-S 编码 | 先从 `ASC-PRIVACY-AGE-REVIEW-RESULT.template.json` 复制；模板不是证据，不能替代隐私标签、年龄分级结果、审核账号、production readiness 或 iOS 26.5 真机 proof |
""".lstrip()


def valid_privacy_label() -> dict:
    return {
        "app": {
            "name": "小奶瓶",
            "bundleId": "com.mewpow.xiaonaiping",
            "usesTracking": False,
            "containsThirdPartyAdvertising": False,
            "containsThirdPartyAnalytics": False,
        },
        "privacyPolicyUrl": "https://api.mewpow.com/xiaonaiping/privacy",
        "supportUrl": "https://api.mewpow.com/xiaonaiping/support",
        "dataCategories": [
            {"category": "Identifiers", "collected": True, "usedForTracking": False, "purposes": ["App Functionality"]},
            {"category": "Contact Info", "collected": True, "usedForTracking": False, "purposes": ["App Functionality"]},
            {"category": "User Content", "collected": True, "usedForTracking": False, "purposes": ["App Functionality"]},
            {"category": "Photos or Videos", "collected": True, "usedForTracking": False, "purposes": ["App Functionality"]},
            {"category": "Health and Fitness", "collected": True, "usedForTracking": False, "purposes": ["App Functionality"]},
            {"category": "Usage Data", "collected": True, "usedForTracking": False, "purposes": ["Analytics"]},
            {"category": "Diagnostics", "collected": True, "usedForTracking": False, "purposes": ["App Functionality", "Analytics"]},
        ],
    }


def write_valid_docs(root: Path) -> None:
    write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260704.md", valid_fill_sheet())
    write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", valid_packet())
    write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook())
    write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_readme())
    write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide())
    write(
        root / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/EXECUTION_SHEET_20260704.md",
        valid_asc_execution_sheet(),
    )
    write(root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json", json.dumps(valid_privacy_label(), ensure_ascii=False))


class AppStoreConnectEvidenceMaterialsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/app-store-connect-evidence-materials.json"
        completed = subprocess.run(
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
        self.assertIn("App Store Connect evidence materials", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_materials_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_latest_dated_fill_sheet_is_used_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260628.md", "stale draft")

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(
                report["checks"]["fillSheetPresent"]["evidence"],
                "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260704.md",
            )
            self.assertTrue(report["checks"]["fillSheetUsesExpectedMaterialDate"]["passed"])

    def test_outdated_latest_fill_sheet_date_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            (root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260704.md").unlink()
            write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260628.md", valid_fill_sheet())
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide("20260628"))

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("fillSheetUsesExpectedMaterialDate", report["failedRequiredChecks"])
            self.assertIn("expected=20260704", report["checks"]["fillSheetUsesExpectedMaterialDate"]["evidence"])

    def test_missing_capture_and_privacy_label_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide().replace("04-privacy-label.png", "04-privacy.png").replace("未追踪、用途", "用途"))
            write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_readme().replace("04-privacy-label.png", "04-privacy.png"))
            write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook().replace("04-privacy-label.png", "04-privacy.png"))
            broken = valid_privacy_label()
            broken["app"]["usesTracking"] = True
            write(root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json", json.dumps(broken, ensure_ascii=False))

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectEvidenceFilenamesPresent", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectEvidenceRedactionCovered", report["failedRequiredChecks"])
            self.assertIn("privacyLabelJsonMatchesEvidenceChecklist", report["failedRequiredChecks"])

    def test_company_account_capture_must_include_duns_team_id_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                valid_capture_guide()
                .replace("，且 D-U-N-S 后 Apple Developer Organization / Team ID 已确认", "")
                .replace("、Apple Developer Organization、Team ID", "")
                .replace("、D-U-N-S 编码完整值", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectEvidenceRedactionCovered", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectEvidenceRedactionCovered"]["evidence"]
            self.assertIn("D-U-N-S 后 Apple Developer Organization / Team ID 已确认", evidence)
            self.assertIn("D-U-N-S 编码完整值", evidence)

    def test_asc_execution_sheet_must_cover_privacy_age_review_result(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/EXECUTION_SHEET_20260704.md",
                valid_asc_execution_sheet()
                .replace("ASC-PRIVACY-AGE-REVIEW-RESULT.template.json", "")
                .replace("17-age-rating-result", "")
                .replace("post-result gates", "")
                .replace("不能替代隐私标签、年龄分级结果、审核账号、production readiness 或 iOS 26.5 真机 proof", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ascPrivacyAgeReviewExecutionSheetCovered", report["failedRequiredChecks"])
            evidence = report["checks"]["ascPrivacyAgeReviewExecutionSheetCovered"]["evidence"]
            self.assertIn("ASC-PRIVACY-AGE-REVIEW-RESULT.template.json", evidence)
            self.assertIn("17-age-rating-result", evidence)
            self.assertIn("post-result gates", evidence)
            self.assertIn(
                "不能替代隐私标签、年龄分级结果、审核账号、production readiness 或 iOS 26.5 真机 proof",
                evidence,
            )

    def test_capture_guide_must_use_current_age_rating_answer_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide("20260629"))

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("captureGuideUsesCurrentAgeRatingAnswerSheet", report["failedRequiredChecks"])
            evidence = report["checks"]["captureGuideUsesCurrentAgeRatingAnswerSheet"]["evidence"]
            self.assertIn("APP_STORE_AGE_RATING_ANSWERS_20260704.md", evidence)
            self.assertIn("APP_STORE_AGE_RATING_ANSWERS_20260629.md", evidence)

    def test_completion_claim_without_archived_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
                valid_packet() + "\n公司主体证据已完成。隐私标签证据已完成。\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("doesNotPretendAppStoreConnectEvidenceCompleteBeforeFiles", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
