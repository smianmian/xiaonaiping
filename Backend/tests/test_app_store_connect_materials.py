from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_app_store_connect_materials.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_fill_sheet() -> str:
    return """
# 小奶瓶 App Store Connect 填表版

状态：可用于准备 App Store Connect 草稿，不可直接提交审核。正式提交仍需 `Backend/proof/production-readiness-20260627T-current.json` 为 `ready: true`。

## App 信息

| 字段 | 填写内容 |
| --- | --- |
| App 名称 | 小奶瓶 |
| Bundle ID | `com.mewpow.xiaonaiping` |
| SKU | `xiaonaiping-ios-1` |
| 副标题 | 温柔记录宝宝每一天 |
| 主类别 | 生活 |
| 第二类别 | 留空，推荐不要选择健康健美，降低被误判为医疗/健康建议 App 的风险 |
| 价格 | 免费 |
| 首发地区 | Specific Countries or Regions -> China mainland |
| 第二批地区 | Hong Kong |
| 版权 | `© 2026 深圳市闪现生活科技有限公司` |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` |
| 技术支持 URL | `https://api.mewpow.com/xiaonaiping/support` |
| 用户协议 URL | `https://api.mewpow.com/xiaonaiping/terms` |

## 关键词

```text
宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册
```

## 宣传文本

```text
用低负担的方式记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片。
```

## 新版本说明

```text
第一版：宝宝档案、日常记录、成长记录、疫苗提醒、照片时间线、手机号/微信/恢复密钥账号备份恢复和云端账号删除。
```

## 描述

```text
小奶瓶是一款宝宝成长记录 App。数据默认本地优先保存，可通过恢复密钥、手机号或微信登录账号，并备份用户主动加入 App 的照片原图。小奶瓶不提供医疗诊断。疫苗模板仅用于记录和提醒，不构成医疗建议，不作为医疗建议，实际接种安排请以医生和当地官方信息为准，不替代医生建议。
```

## 年龄分级建议

- 不选择 Kids 类目。
- 预期年龄分级：4+。
- 目标用户为父母和照护者，不面向儿童直接使用。
- 不接入 HealthKit、传感器、医院系统或第三方健康数据源；不提供压力评估、心理健康判断或压力提醒。

## 截图文案

| 序号 | 截图 | 标题 | 辅助文案 |
| --- | --- | --- | --- |
| 1 | `01-home-iphone16pro.png` | 记录宝宝今天的小变化 | 今日摘要。 |
| 2 | `02-record-iphone16pro.png` | 半夜也能低负担记录 | 快速记录。 |
| 3 | `03-growth-iphone16pro.png` | 一个月的成长，轻轻回看 | 成长变化。 |
| 4 | `04-profile-iphone16pro.png` | 设置、隐私和资料都在这里 | 管理资料。 |
| 5 | `05-profile-backup-iphone16pro.png` | 主动备份，也能主动删除 | 备份删除。 |

当前 5 张候选图不展示灵动岛/锁屏 Live Activity 或小组件。若后续新增截图，不得写成健康建议、喂养推荐或医疗判断。

截图禁区：

1. 不使用真实宝宝照片，除非另有明确授权。
2. 不展示真实手机号、恢复密钥、token、账号 ID、对象存储 key 或内部路径。
3. 不展示 `127.0.0.1`、debug code、internal dashboard 或工程文档。
4. 不写医疗诊断、治疗、疫苗建议、医生替代或专业健康结论。
5. 微信登录未完成开放平台配置前，不截图暗示微信登录已经可用。

## 审核备注可粘贴文本

```text
灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。小奶瓶不是医疗器械。正式提交包不得依赖 debug code。
```

## 审核测试账号填写说明

- App Review Information 中填写恢复密钥测试账号。
- 脱敏证据文件：`Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json`。
- 真机回归与测试账号操作表：`Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`。
- 真实恢复密钥只保存在本地 ignored 文件 `.env.xnp-review-account`，只允许复制到 App Review Information 安全字段。
- 真实恢复密钥不得写入 App Store Connect 文案、审核备注、截图或仓库文档。
- 手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充。

## 当前不可提交原因

- `Backend/proof/production-readiness-20260627T-current.json` 当前 `ready=false`
- `Backend/proof/auth-providers-20260627T-current.json` 当前 `passed=false`，微信 provider 未配置；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充
- `Backend/proof/ios-release-readiness.json` 当前 `passed=false`，缺真实微信 Release build setting
- `Backend/proof/ios-app-bundle-20260627T-current-ios265.json` 当前 `passed=false`，缺真实 `wx...` URL Scheme
- `Backend/proof/app-store-evidence-20260627T-current.json` 当前 `ready=false`，缺人工证据和 iOS 26.5 真机回归记录
""".lstrip()


def valid_metadata() -> str:
    return """
| 字段 | 草案 |
|---|---|
| App 名称 | 小奶瓶 |
| 分类 | 生活；第二分类留空 |
| 隐私政策 | https://api.mewpow.com/xiaonaiping/privacy |
| 技术支持 | https://api.mewpow.com/xiaonaiping/support |
| 用户协议 | https://api.mewpow.com/xiaonaiping/terms |

Bundle ID: com.mewpow.xiaonaiping
""".lstrip()


def valid_privacy_label() -> dict:
    return {
        "app": {
            "name": "小奶瓶",
            "bundleId": "com.mewpow.xiaonaiping",
            "targetsChildrenDirectly": False,
            "containsThirdPartyAdvertising": False,
            "containsThirdPartyAnalytics": False,
            "usesTracking": False,
        },
        "privacyPolicyUrl": "https://api.mewpow.com/xiaonaiping/privacy",
        "supportUrl": "https://api.mewpow.com/xiaonaiping/support",
        "dataCategories": [
            {
                "category": "Identifiers",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
            },
            {
                "category": "Contact Info",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
            },
            {
                "category": "User Content",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
            },
            {
                "category": "Photos or Videos",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
            },
            {
                "category": "Health and Fitness",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
                "notes": "User-entered baby care records only. No HealthKit, sensors, hospital records, stress detection, medical interpretation, health advice, pressure reminders, feeding advice, or medical diagnosis. Live Activity and widgets are status display only.",
            },
            {
                "category": "Usage Data",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["Analytics"],
                "notes": "No baby content, photos, phone numbers, WeChat identifiers, advertising ID, or device fingerprint.",
            },
            {
                "category": "Diagnostics",
                "collected": True,
                "linkedToUser": False,
                "usedForTracking": False,
                "purposes": ["App Functionality", "Analytics"],
            },
        ],
    }


def valid_screenshot_plan() -> str:
    return """
# SCREENSHOT_PLAN.md

## 当前截图命令

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -sdk iphonesimulator26.5 -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -derivedDataPath /tmp/XiaoNaiPing-DebugScreenshots-26_5 CODE_SIGNING_ALLOWED=NO build
SIMCTL_CHILD_XNP_API_BASE_URL=https://api.mewpow.com/xiaonaiping python3 Backend/scripts/capture_ios_screenshots.py --device IOS_26_5_SIMULATOR_UDID --app /tmp/XiaoNaiPing-DebugScreenshots-26_5/Build/Products/Debug-iphonesimulator/XiaoNaiPing.app --output-dir /tmp/xnp-debug-prod-screenshots-26_5 --tabs home record growth profile profile-backup --settle-seconds 2.5 --shutdown
```

## 仍需补齐

1. TestFlight 或签名真机包最终截图。
2. 正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图。
""".lstrip()


def write_valid_materials(root: Path) -> None:
    write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md", valid_fill_sheet())
    write(root / "Docs/08_Release/APP_STORE_METADATA.md", valid_metadata())
    write(
        root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        json.dumps(valid_privacy_label(), ensure_ascii=False),
    )
    write(root / "Docs/08_Release/SCREENSHOT_PLAN.md", valid_screenshot_plan())
    write(
        root / "App/iOS/XiaoNaiPing/Views/FeedingRecordView.swift",
        'Text("会提前5分钟提醒准备泡奶，Apple Watch 可跟随系统通知震动。")\n',
    )
    write(
        root / "App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/Localizable.strings",
        '"会提前5分钟提醒准备泡奶，Apple Watch 可跟随系统通知震动。" = "會提前5分鐘提醒準備泡奶，Apple Watch 可跟隨系統通知震動。";\n',
    )


class AppStoreConnectMaterialsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/app-store-connect-materials.json"
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
        self.assertIn("App Store Connect materials", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_materials_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_latest_dated_fill_sheet_is_used_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md", "stale draft")
            write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md", valid_fill_sheet())

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertIn(
                "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                report["checks"]["fillSheetPresent"]["evidence"],
            )

    def test_category_url_keywords_and_screenshots_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_METADATA.md",
                valid_metadata() + "\n| Category | Lifestyle or Health & Fitness; choose one before submission |\n",
            )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md",
                valid_fill_sheet()
                .replace("https://api.mewpow.com/xiaonaiping/support", "https://api.example.com/support")
                .replace("宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册", "宝宝记录," + "育儿" * 60)
                .replace("| 5 | `05-profile-backup-iphone16pro.png` | 主动备份，也能主动删除 | 备份删除。 |", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("metadataNoHealthFitnessCategoryAlternative", report["failedRequiredChecks"])
            self.assertIn("publicUrlsMatch", report["failedRequiredChecks"])
            self.assertIn("keywordsCompleteAndWithinLimit", report["failedRequiredChecks"])
            self.assertIn("screenshotCopyComplete", report["failedRequiredChecks"])

    def test_keywords_limit_counts_utf8_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md",
                valid_fill_sheet().replace(
                    "宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册",
                    "宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册,轻柔记录记录记录记录记录记录",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("keywordsCompleteAndWithinLimit", report["failedRequiredChecks"])
            evidence = report["checks"]["keywordsCompleteAndWithinLimit"]["evidence"]
            self.assertIn("bytes=", evidence)

    def test_screenshot_copy_rejects_medical_or_unavailable_login_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md",
                valid_fill_sheet()
                .replace("主动备份，也能主动删除", "微信登录成功，备份恢复")
                .replace("半夜也能低负担记录", "半夜喂养推荐")
                .replace("5. 微信登录未完成开放平台配置前，不截图暗示微信登录已经可用。\n", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("screenshotCopyAvoidsUnavailableOrMedicalClaims", report["failedRequiredChecks"])
            evidence = report["checks"]["screenshotCopyAvoidsUnavailableOrMedicalClaims"]["evidence"]
            self.assertIn("微信登录成功", evidence)
            self.assertIn("喂养推荐", evidence)
            self.assertIn("微信登录未完成开放平台配置前", evidence)

    def test_stale_current_proof_references_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md",
                valid_fill_sheet()
                .replace("Backend/proof/production-readiness-20260627T-current.json", "Backend/proof/production-readiness-20260626T-current.json")
                .replace("Backend/proof/ios-app-bundle-20260627T-current-ios265.json", "Backend/proof/ios-app-bundle-20260626T-current-ios265.json"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("blockingProofReferencesUseLatestSnapshots", report["failedRequiredChecks"])

    def test_screenshot_plan_must_use_ios265_only(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/SCREENSHOT_PLAN.md",
                valid_screenshot_plan()
                .replace("-sdk iphonesimulator26.5", "")
                .replace("OS=26.5", "OS=18.5")
                .replace("XiaoNaiPing-DebugScreenshots-26_5", "XiaoNaiPing-DebugScreenshots"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("screenshotPlanUsesIOS265Only", report["failedRequiredChecks"])
            self.assertIn("OS=18.5", report["checks"]["screenshotPlanUsesIOS265Only"]["evidence"])

    def test_in_app_companion_copy_rejects_unbounded_watch_app_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "App/iOS/XiaoNaiPing/Views/FeedingRecordView.swift",
                'Text("支持 Apple Watch App 和 watchOS 手表体验。")\n',
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("inAppCompanionCopyBounded", report["failedRequiredChecks"])
            evidence = report["checks"]["inAppCompanionCopyBounded"]["evidence"]
            self.assertIn("Watch App", evidence)
            self.assertIn("watchOS", evidence)

    def test_external_auth_submission_boundaries_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md",
                valid_fill_sheet()
                .replace("，微信 provider 未配置；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充", "")
                .replace("，缺真实微信 Release build setting", "")
                .replace("，缺真实 `wx...` URL Scheme", "")
                .replace("，缺人工证据和 iOS 26.5 真机回归记录", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalAuthSubmissionBoundaryPresent", report["failedRequiredChecks"])

    def test_review_paste_text_requires_status_and_advice_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md",
                valid_fill_sheet().replace(
                    "这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。",
                    "",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("reviewNotesPasteTextHasBoundary", report["failedRequiredChecks"])

    def test_review_account_instructions_must_be_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md",
                valid_fill_sheet()
                .replace(
                    "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
                    "Docs/08_Release/AppStoreEvidence/missing.json",
                )
                + "\nXNP_REVIEW_RECOVERY_KEY=secret\nBearer abc.def_123\n13800138000\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("reviewAccountInstructionsRedacted", report["failedRequiredChecks"])
            evidence = report["checks"]["reviewAccountInstructionsRedacted"]["evidence"]
            self.assertIn("Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json", evidence)
            self.assertIn("recoveryKeyAssignment", evidence)
            self.assertIn("bearerToken", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)

    def test_release_notes_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md",
                valid_fill_sheet().replace("、照片时间线、手机号/微信/恢复密钥账号备份恢复和云端账号删除", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("releaseNotesCompleteAndWithinLimit", report["failedRequiredChecks"])

    def test_privacy_label_app_flags_and_usage_boundaries_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            privacy_label = valid_privacy_label()
            privacy_label["app"]["containsThirdPartyAnalytics"] = True
            privacy_label["dataCategories"][5]["linkedToUser"] = False
            privacy_label["dataCategories"][5]["notes"] = "First-party product interaction only."
            privacy_label["dataCategories"].append(
                {
                    "category": "Location",
                    "collected": True,
                    "linkedToUser": True,
                    "usedForTracking": False,
                    "purposes": ["Analytics"],
                }
            )
            write(
                root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
                json.dumps(privacy_label, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyLabelMatchesAppStoreDraft", report["failedRequiredChecks"])
            evidence = report["checks"]["privacyLabelMatchesAppStoreDraft"]["evidence"]
            self.assertIn("app.containsThirdPartyAnalytics must be false", evidence)
            self.assertIn("unexpected collected categories: Location", evidence)
            self.assertIn("Usage Data.linkedToUser must be true", evidence)
            self.assertIn("Usage Data boundary missing", evidence)

    def test_privacy_label_health_boundaries_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            privacy_label = valid_privacy_label()
            privacy_label["dataCategories"][4]["notes"] = "The app is not a medical device."
            write(
                root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
                json.dumps(privacy_label, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyLabelMatchesAppStoreDraft", report["failedRequiredChecks"])
            evidence = report["checks"]["privacyLabelMatchesAppStoreDraft"]["evidence"]
            self.assertIn("Health and Fitness boundary missing", evidence)


if __name__ == "__main__":
    unittest.main()
