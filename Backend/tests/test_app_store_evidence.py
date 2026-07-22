from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_app_store_evidence.py"
CHECKER_SPEC = importlib.util.spec_from_file_location("check_app_store_evidence", SCRIPT)
CHECKER = importlib.util.module_from_spec(CHECKER_SPEC)
assert CHECKER_SPEC.loader is not None
CHECKER_SPEC.loader.exec_module(CHECKER)
EXPECTED_SCREENSHOTS = [
    "01-home-iphone16pro.png",
    "02-record-iphone16pro.png",
    "03-growth-iphone16pro.png",
    "04-profile-iphone16pro.png",
    "05-profile-sync-iphone16pro.png",
]
REAL_DEVICE_EVIDENCE_PATHS = {
    "RD-01": "RealDevice/RD-01-cold-start.png",
    "RD-02": "RealDevice/RD-02-baby-profile.png",
    "RD-03": "RealDevice/RD-03-feeding-record.png",
    "RD-04": "RealDevice/RD-04-sleep-record.png",
    "RD-05": "RealDevice/RD-05-diaper-record.png",
    "RD-06": "RealDevice/RD-06-growth-record.png",
    "RD-07": "RealDevice/RD-07-vaccine-template.png",
    "RD-08": "RealDevice/RD-08-photo-denied.png",
    "RD-09": "RealDevice/RD-09-photo-allowed.png",
    "RD-10": "RealDevice/RD-10-recovery-login.png",
    "RD-11": "RealDevice/RD-11-cloud-sync.png",
    "RD-12": "RealDevice/RD-12-cloud-restore.png",
    "RD-13": "RealDevice/RD-13-phone-login.png",
    "RD-14": "RealDevice/RD-14-wechat-login.png",
    "RD-15": "RealDevice/RD-15-account-delete.png",
    "RD-16": "RealDevice/RD-16-offline-save.png",
    "RD-17": "RealDevice/RD-17-notification-allowed.png",
    "RD-18": "RealDevice/RD-18-watch-mirror.png",
    "RD-19": "RealDevice/RD-19-public-urls.png",
    "RD-20": "RealDevice/RD-20-diagnostics-redaction.png",
    "RD-21": "RealDevice/RD-21-release-bundle.png",
    "RD-22": "RealDevice/RD-22-dynamic-island-compact.png",
    "RD-23": "RealDevice/RD-23-lock-screen-notification-stack.png",
    "RD-24": "RealDevice/RD-24-review-boundary.png",
}
FOCUSED_REAL_DEVICE_EVIDENCE_PATHS = {
    "recoveryLogin": "RealDevice/RD-10-recovery-login.png",
    "phoneLogin": "RealDevice/RD-13-phone-login.png",
    "wechatLogin": "RealDevice/RD-14-wechat-login.png",
    "accountDelete": "RealDevice/RD-15-account-delete.png",
    "notificationAllowed": "RealDevice/RD-17-notification-allowed.png",
    "notificationDenied": "RealDevice/RD-17-notification-denied.png",
    "dynamicIslandCompact": "RealDevice/RD-22-dynamic-island-compact.png",
    "dynamicIslandExpanded": "RealDevice/RD-22-dynamic-island-expanded.png",
    "lockScreenNotificationStack": "RealDevice/RD-23-lock-screen-notification-stack.png",
    "lockScreenWidgetSummary": "RealDevice/RD-23-lock-screen-widget-summary.png",
    "homeWidgetSummary": "RealDevice/RD-23-home-widget-summary.png",
}


def write(path: Path, value: bytes = b"x" * (12 * 1024)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def write_review_test_account(path: Path, value: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value or {
        "accountId": "review-account-1",
        "recoveryKeyStored": ".env.xnp-review-account",
        "recoveryVerified": True,
        "syncSeeded": True,
        "containsSecret": False,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manual_evidence_checklist(root: Path) -> None:
    markers = [
        "仍需补齐的人工证据",
        "真机回归必须覆盖",
        "RD 用例列表",
        "灵动岛 / 小组件 / Apple Watch 边界",
        "遮挡与脱敏规则",
        "当前不可替代项",
        "采集后必跑",
        "同轮人工证据索引模板",
        "同一天同一轮采集",
        "App 版本",
        "Build 号",
        "01-company-account.png 到 09-obs-policy.png、`08b-wechat-universal-link-aasa.png` 和 17-age-rating-result",
        "10-final-screenshots/",
        "12-real-device-regression.md",
        "每个文件已脱敏",
        "单个文件不低于 10KB",
        "App Store Connect 选中的 build 与 TestFlight / 12-real-device-regression.md 一致",
        "check_app_store_evidence.py --allow-incomplete",
        "production-readiness.json",
        "01-company-account.png",
        "02-mainland-availability.png",
        "03-app-filing.pdf",
        "03-app-filing.png",
        "04-privacy-label.png",
        "17-age-rating-result.png",
        "17-age-rating-result.pdf",
        "05-signed-archive.png",
        "06-testflight.png",
        "07-sms-provider.png",
        "08-wechat-open-platform.png",
        "08b-wechat-universal-link-aasa.png",
        "09-obs-policy.png",
        "10-final-screenshots/",
        "10-final-screenshots/UPLOAD_PROVENANCE.json",
        "final-app-store-upload",
        "iPhone 6.9",
        "TestFlight 或 Xcode 签名真机包最终截图",
        "01-home-iphone16pro.png",
        "02-record-iphone16pro.png",
        "03-growth-iphone16pro.png",
        "04-profile-iphone16pro.png",
        "05-profile-sync-iphone16pro.png",
        "11-test-account-redacted.json",
        "12-real-device-regression.md",
        "AppleDeveloper/16-account-roles-access.png",
        "证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限",
        "单个 RD 文件不低于 10KB",
        "iOS 26.5",
        "TestFlight",
        "Xcode 签名真机包",
        "灵动岛紧凑态结论",
        "灵动岛展开态结论",
        "锁屏通知栈结论",
        "锁屏小组件结论",
        "桌面小组件结论",
        "Apple Watch 只作为系统镜像通知",
        "不在 App Store 文案中承诺 Watch App",
        "RD-10、RD-13、RD-14、RD-15、RD-18、RD-22、RD-23、RD-24 不能复用总览图或同一份泛证据",
        "RD-10 恢复密钥登录必须使用独立证据文件",
        "RD-13 手机号登录必须使用独立证据文件",
        "RD-14 微信登录必须使用独立证据文件",
        "RD-15 账号删除必须使用独立证据文件",
        "RD-17 通知权限允许和拒绝必须使用独立证据文件",
        "RD-22 灵动岛紧凑态和展开态必须使用独立证据文件",
        "RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须使用独立证据文件",
        "RealDevice/RD-10-recovery-login.png",
        "RealDevice/RD-13-phone-login.png",
        "RealDevice/RD-14-wechat-login.png",
        "RealDevice/RD-15-account-delete.png",
        "RD-10 路径必须体现 recovery 或恢复",
        "RD-13 路径必须体现 phone、sms、手机号或验证码",
        "RD-14 路径必须体现 wechat 或微信",
        "RD-15 路径必须体现 account / delete 或账号 / 删除",
        "RD-17 路径必须体现 notification、permission、通知或权限",
        "RD-18 路径必须同时体现 watch 和 mirror / notification",
        "RD-22 路径必须体现 live-activity、dynamic-island、island 或灵动岛",
        "RD-22 路径必须体现 switch、toggle、开关、compact 或 expanded",
        "RD-23 代表路径必须体现 widget / 小组件或 lock-screen / 锁屏",
        "RealDevice/RD-17-notification-allowed.png",
        "RealDevice/RD-17-notification-denied.png",
        "RealDevice/RD-22-dynamic-island-compact.png",
        "RealDevice/RD-22-dynamic-island-expanded.png",
        "RealDevice/RD-23-lock-screen-notification-stack.png",
        "RealDevice/RD-23-lock-screen-widget-summary.png",
        "RealDevice/RD-23-home-widget-summary.png",
        "不生成健康建议、压力提醒、喂养建议或医疗判断",
        "不接入 HealthKit、传感器、医院系统或第三方健康数据源",
        "不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议",
        *(f"RD-{index:02d}" for index in range(1, 25)),
    ]
    path = root / "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260628.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(markers) + "\n", encoding="utf-8")


def valid_manual_evidence_packet() -> dict:
    target_files = dict(CHECKER.MANUAL_EVIDENCE_PACKET_TARGET_FILES)
    return {
        "artifactType": "app-store-manual-evidence-packet",
        "status": "manual-evidence-plan-not-evidence",
        "date": "2026-06-28",
        "project": "XiaoNaiPing",
        "appName": "小奶瓶",
        "bundleId": "com.mewpow.xiaonaiping",
        "canSubmitFromThisPacket": False,
        "sourceFiles": {
            "evidenceChecklist": "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260628.md",
            "captureGuide": "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
            "appStoreEvidenceReadme": "Docs/08_Release/AppStoreEvidence/README.md",
            "appStoreConnectExecutionSheet": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/EXECUTION_SHEET_20260628.md",
            "appStoreConnectEntrySessionPacket": "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260628.json",
            "externalPlatformCapturePacket": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260628.json",
            "finalScreenshotUploadPacket": "Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_20260628.json",
            "privacyLabel": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
            "ageRatingAnswers": "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260628.md",
            "submissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
        },
        "targetEvidenceFiles": target_files,
        "evidenceFileChecks": [
            {
                "artifactId": artifact_id,
                "target": target,
                "fileSizeBytes": "FILL_AFTER_CAPTURE",
                "sha256": "FILL_AFTER_CAPTURE",
                "redactionChecked": False,
                "sameRoundAsManualEvidencePacket": False,
                "sourceIsAllowedEvidenceRoot": False,
                "realEvidenceNotTemplate": False,
                "secretValuesNotRecorded": False,
            }
            for artifact_id, target in target_files.items()
        ],
        "evidenceDependencyMatrix": [
            {
                "artifactId": artifact_id,
                "target": target,
                "proves": CHECKER.MANUAL_EVIDENCE_PACKET_DEPENDENCY_MATRIX[artifact_id]["proves"],
                "doesNotProve": CHECKER.MANUAL_EVIDENCE_PACKET_DEPENDENCY_MATRIX[artifact_id]["doesNotProve"],
                "requiredBeforeSubmit": True,
                "initialStatus": "pending",
            }
            for artifact_id, target in target_files.items()
        ],
        "captureRules": [
            "sameDaySameRoundRequired",
            "realEvidenceOnly",
            "noTemplateAsEvidence",
            "evidenceFileChecks must record file size, SHA-256, redaction, same-round capture, allowed evidence root, real-evidence-not-template confirmation, and secret-values-not-recorded confirmation before stable proof aliases are refreshed",
            "iOS26.5OnlyForLocalProof",
            "sameBuildForTestFlightFinalScreenshotsAndRealDeviceRegression",
            "canSubmitFalseUntilProductionReadinessAndLaunchAuditReady",
            "App Store Connect 真实页面",
            "不写占位备案号",
            "不把 Debug simulator 候选截图当最终上传证据",
            "不把模板、执行包或 Markdown 当证据",
            "不声称微信、短信、OBS、TestFlight、签名归档或真机回归已完成",
        ],
        "postCaptureCommands": [
            "python3 Backend/scripts/check_app_store_assets.py --allow-incomplete --output Backend/proof/app-store-assets.json",
            "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-28 --output Backend/proof/app-store-evidence-20260628T-current.json",
            "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260628T-current.json",
            "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
        ],
        "completionRule": "manual-evidence-plan-not-evidence；not submission permission；只有 app-store-evidence.json ready=true、production-readiness.json ready=true、launch-objective-audit.json ready=true 后，才允许进入提交审核判断。",
    }


def write_manual_evidence_packet(root: Path, value: dict | None = None) -> None:
    path = root / "Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260628.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value or valid_manual_evidence_packet(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_capture_guidance(root: Path) -> None:
    guide = root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md"
    guide.parent.mkdir(parents=True, exist_ok=True)
    guide.write_text(
        "\n".join(
            [
                "# App Store Evidence Capture Guide",
                "锁屏小组件视觉结论",
                "锁屏小组件要证明 accessoryCircular / accessoryRectangular / accessoryInline",
                "RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须拆成",
                "RealDevice/RD-23-lock-screen-notification-stack.png",
                "RealDevice/RD-23-lock-screen-widget-summary.png",
                "RealDevice/RD-23-home-widget-summary.png",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    readme = root / "Docs/08_Release/AppStoreEvidence/README.md"
    readme.write_text(
        "\n".join(
            [
                "# AppStoreEvidence",
                "锁屏小组件视觉结论",
                "RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须使用独立证据文件",
                "RealDevice/RD-23-lock-screen-notification-stack.png",
                "RealDevice/RD-23-lock-screen-widget-summary.png",
                "RealDevice/RD-23-home-widget-summary.png",
                "锁屏小组件内容不裁剪不展示隐私照片",
                "Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260628.json",
                "RealDevice/FOCUSED_CAPTURE_PACKET_20260628.json",
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-28 --output Backend/proof/app-store-evidence-20260628T-current.json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_real_device_regression(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path.parent / "RealDevice/00-overview.png")
    for evidence_path in REAL_DEVICE_EVIDENCE_PATHS.values():
        write(path.parent / evidence_path)
    for evidence_path in FOCUSED_REAL_DEVICE_EVIDENCE_PATHS.values():
        write(path.parent / evidence_path)
    rows = "\n".join(
        f"| RD-{index:02d} 用例 | 通过 | {REAL_DEVICE_EVIDENCE_PATHS[f'RD-{index:02d}']} |"
        for index in range(1, 25)
    )
    path.write_text(
        "\n".join(
            [
                "- 设备：蓝蓝 / iPhone 16 Pro Max",
                "- iOS：26.5",
                "- 安装方式：TestFlight",
                "- App 版本：1.0",
                "- Build：1",
                "- 网络：Wi-Fi + 蜂窝网络",
                "- 证据截图/录屏：RealDevice/00-overview.png",
                "- 灵动岛紧凑态结论：头像和进度环未压到岛中心",
                "- 灵动岛展开态结论：文字和数字留白正常，未贴边或被吞",
                "- 锁屏通知栈结论：上下相邻通知不遮挡提醒卡片",
                "- 锁屏小组件结论：accessory 小组件内容不裁剪，不展示隐私照片",
                "- 桌面小组件结论：小尺寸和中尺寸内容不裁剪，不展示隐私照片",
                "",
                "- [x] iOS 26.5",
                "- [x] 冷启动",
                "- [x] 手机号登录",
                "- [x] 微信登录",
                "- [x] 恢复密钥登录",
                "- [x] 云同步",
                "- [x] 云恢复",
                "- [x] 账号删除",
                "- [x] 通知权限",
                "- [x] 通知权限允许独立截图",
                "- [x] 通知权限拒绝独立截图",
                "- [x] 灵动岛喝奶提醒开关",
                "- [x] 灵动岛紧凑态头像和进度环未压到岛中心",
                "- [x] 灵动岛展开态文字和数字未贴边或被吞",
                "- [x] 锁屏通知栈上下相邻通知不遮挡提醒卡片",
                "- [x] 锁屏/桌面小组件",
                "- [x] 灵动岛紧凑态独立截图",
                "- [x] 灵动岛展开态独立截图",
                "- [x] 锁屏通知栈独立截图",
                "- [x] 锁屏小组件独立截图",
                "- [x] 桌面小组件独立截图",
                "- [x] 锁屏小组件内容不裁剪不展示隐私照片",
                "- [x] 桌面小组件内容不裁剪不展示隐私照片",
                "- [x] 审核边界文案",
                "- [x] Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔",
                "- [x] 小组件只读展示本机今日摘要",
                "- [x] Apple Watch 只作为系统镜像通知，不在 App Store 文案中承诺 Watch App",
                "- [x] 状态展示只反映用户主动记录的数据",
                "- [x] 不生成健康建议、压力提醒、喂养建议或医疗判断",
                "- [x] 不接入 HealthKit、传感器、医院系统或第三方健康数据源",
                "- [x] 不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议",
                "",
                "| 场景 | 实际观察结论 | 证据 |",
                "|---|---|---|",
                "| 通知权限允许 | 可创建下一次喝奶提醒 | RealDevice/RD-17-notification-allowed.png |",
                "| 通知权限拒绝 | 有系统设置入口 | RealDevice/RD-17-notification-denied.png |",
                "| 灵动岛紧凑态 | 头像和进度环未压到岛中心 | RealDevice/RD-22-dynamic-island-compact.png |",
                "| 灵动岛展开态 | 文字和数字未贴边或被吞 | RealDevice/RD-22-dynamic-island-expanded.png |",
                "| 锁屏通知栈 | 上下相邻通知不遮挡提醒卡片 | RealDevice/RD-23-lock-screen-notification-stack.png |",
                "| 锁屏小组件 | 不裁剪且不展示隐私照片 | RealDevice/RD-23-lock-screen-widget-summary.png |",
                "| 桌面小组件 | 不裁剪且不展示隐私照片 | RealDevice/RD-23-home-widget-summary.png |",
                "| 恢复密钥登录 | 可恢复审核测试账号 | RealDevice/RD-10-recovery-login.png |",
                "| 手机号登录 | 真实验证码可发送和校验 | RealDevice/RD-13-phone-login.png |",
                "| 微信登录 | 可拉起微信授权并回到 App | RealDevice/RD-14-wechat-login.png |",
                "| 账号删除 | 云端账号与同步删除后旧 token 失效 | RealDevice/RD-15-account-delete.png |",
                "",
                "| 编号 | 结果 | 证据/备注 |",
                "|---|---|---|",
                rows,
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_app_store_assets_proof(root: Path) -> None:
    proof = {
        "passed": True,
        "checks": {
            "finalScreenshotsCount": {"passed": True},
            "finalScreenshotsExpectedUploadOrder": {"passed": True},
            "finalScreenshotsAcceptedSizes": {"passed": True},
            "finalScreenshotsIphone69SlotReady": {"passed": True},
            "finalScreenshotsNotBlank": {"passed": True},
            "finalScreenshotsNoRiskyFilenames": {"passed": True},
            "finalScreenshotsIOS265ProvenancePresent": {"passed": True},
            "finalScreenshotsUploadProvenanceTemplateValid": {"passed": True},
            "finalScreenshotsUploadProvenancePresent": {"passed": True},
        },
    }
    path = root / "Backend/proof/app-store-assets.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proof, ensure_ascii=False), encoding="utf-8")


class AppStoreEvidenceTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/app-store-evidence.json"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(root),
                "--output",
                str(output),
                "--date",
                "2026-06-28",
                "--allow-incomplete",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(output.read_text(encoding="utf-8"))

    def test_missing_evidence_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            report = self.run_checker(Path(tempdir))

            self.assertFalse(report["ready"])
            self.assertIn("companyAccount", report["missingEvidence"])
            self.assertIn("finalScreenshots", report["missingEvidence"])
            self.assertIn("reviewTestAccount", report["missingEvidence"])
            self.assertIn("ageRatingResult", report["missingEvidence"])
            self.assertIn("wechatUniversalLinkAasa", report["missingEvidence"])

    def test_manual_evidence_checklist_requires_same_round_index_template(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_manual_evidence_checklist(root)
            checklist = root / "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260628.md"
            text = checklist.read_text(encoding="utf-8")
            text = text.replace("同轮人工证据索引模板\n", "")
            text = text.replace("同一天同一轮采集\n", "")
            text = text.replace("App Store Connect 选中的 build 与 TestFlight / 12-real-device-regression.md 一致\n", "")
            checklist.write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("manualEvidenceChecklist", report["missingEvidence"])
            missing = report["checks"]["manualEvidenceChecklist"]["missingMarkers"]
            self.assertIn("同轮人工证据索引模板", missing)
            self.assertIn("同一天同一轮采集", missing)
            self.assertIn("App Store Connect 选中的 build 与 TestFlight / 12-real-device-regression.md 一致", missing)

    def test_manual_evidence_packet_locks_no_submit_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            packet = valid_manual_evidence_packet()
            packet["canSubmitFromThisPacket"] = True
            del packet["targetEvidenceFiles"]["ageRatingResult"]
            del packet["targetEvidenceFiles"]["wechatUniversalLinkAasa"]
            packet["targetEvidenceFiles"]["finalScreenshotUploadProvenance"] = "Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json"
            packet["evidenceFileChecks"] = [
                check
                for check in packet["evidenceFileChecks"]
                if check["artifactId"] != "smsProvider"
            ]
            packet["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/01-company-copy.png"
            packet["evidenceFileChecks"][0]["sha256"] = "already-filled"
            packet["evidenceFileChecks"][0]["sameRoundAsManualEvidencePacket"] = True
            packet["evidenceFileChecks"][0]["sourceIsAllowedEvidenceRoot"] = True
            packet["evidenceFileChecks"][0]["realEvidenceNotTemplate"] = True
            packet["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            packet["evidenceDependencyMatrix"] = [
                entry
                for entry in packet["evidenceDependencyMatrix"]
                if entry["artifactId"] != "wechatOpenPlatform"
            ]
            packet["evidenceDependencyMatrix"][0]["target"] = "Docs/08_Release/AppStoreEvidence/01-company-copy.png"
            packet["evidenceDependencyMatrix"][0]["proves"] = ["wrong proof"]
            packet["evidenceDependencyMatrix"][0]["doesNotProve"] = ["wrong boundary"]
            packet["evidenceDependencyMatrix"][0]["requiredBeforeSubmit"] = False
            packet["evidenceDependencyMatrix"][0]["initialStatus"] = "captured"
            packet["evidenceDependencyMatrix"][0]["extra"] = "unexpected"
            packet["captureRules"].remove("iOS26.5OnlyForLocalProof")
            packet["postCaptureCommands"] = [
                command
                for command in packet["postCaptureCommands"]
                if "check_launch_objective_audit.py" not in command
            ]
            write_manual_evidence_packet(root, packet)

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("manualEvidencePacket", report["missingEvidence"])
            packet_check = report["checks"]["manualEvidencePacket"]
            self.assertEqual(packet_check["invalidFields"]["canSubmitFromThisPacket"], True)
            self.assertIn("ageRatingResult", packet_check["missingTargetEvidenceFiles"])
            self.assertIn("wechatUniversalLinkAasa", packet_check["missingTargetEvidenceFiles"])
            self.assertEqual(
                packet_check["invalidTargetEvidenceFiles"]["finalScreenshotUploadProvenance"],
                "Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json",
            )
            self.assertIn("smsProvider", packet_check["missingEvidenceFileChecks"])
            self.assertIn("invalidEvidenceFileCheckOrder", packet_check)
            self.assertEqual(
                packet_check["invalidEvidenceFileCheckTargets"]["companyAccount"],
                "Docs/08_Release/AppStoreEvidence/01-company-copy.png",
            )
            self.assertEqual(
                packet_check["invalidEvidenceFileCheckPlaceholders"]["companyAccount"]["sha256"],
                "already-filled",
            )
            self.assertTrue(
                packet_check["invalidEvidenceFileCheckPlaceholders"]["companyAccount"]["sameRoundAsManualEvidencePacket"]
            )
            self.assertTrue(
                packet_check["invalidEvidenceFileCheckPlaceholders"]["companyAccount"]["sourceIsAllowedEvidenceRoot"]
            )
            self.assertTrue(
                packet_check["invalidEvidenceFileCheckPlaceholders"]["companyAccount"]["realEvidenceNotTemplate"]
            )
            self.assertTrue(
                packet_check["invalidEvidenceFileCheckPlaceholders"]["companyAccount"]["secretValuesNotRecorded"]
            )
            self.assertIn("wechatOpenPlatform", packet_check["missingEvidenceDependencyMatrixEntries"])
            self.assertIn("invalidEvidenceDependencyMatrixOrder", packet_check)
            self.assertIn("companyAccount", packet_check["invalidEvidenceDependencyMatrixFields"])
            self.assertEqual(
                packet_check["invalidEvidenceDependencyMatrixTargets"]["companyAccount"],
                "Docs/08_Release/AppStoreEvidence/01-company-copy.png",
            )
            self.assertEqual(packet_check["invalidEvidenceDependencyMatrixProves"]["companyAccount"], ["wrong proof"])
            self.assertEqual(
                packet_check["invalidEvidenceDependencyMatrixDoesNotProve"]["companyAccount"],
                ["wrong boundary"],
            )
            self.assertFalse(packet_check["invalidEvidenceDependencyMatrixRequiredBeforeSubmit"]["companyAccount"])
            self.assertEqual(packet_check["invalidEvidenceDependencyMatrixInitialStatus"]["companyAccount"], "captured")
            self.assertIn("iOS26.5OnlyForLocalProof", packet_check["missingMarkers"])
            self.assertIn("check_launch_objective_audit.py", packet_check["missingMarkers"])

    def test_capture_guidance_requires_lock_screen_widget_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_capture_guidance(root)
            guide = root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md"
            guide.write_text(
                guide.read_text(encoding="utf-8")
                .replace("锁屏小组件视觉结论\n", "")
                .replace("锁屏小组件要证明 accessoryCircular / accessoryRectangular / accessoryInline\n", "")
                .replace("RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须拆成\n", "")
                .replace("RealDevice/RD-23-lock-screen-widget-summary.png\n", ""),
                encoding="utf-8",
            )
            readme = root / "Docs/08_Release/AppStoreEvidence/README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                .replace("RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须使用独立证据文件\n", "")
                .replace("RealDevice/RD-23-lock-screen-widget-summary.png\n", "")
                .replace("锁屏小组件内容不裁剪不展示隐私照片\n", ""),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("captureGuidance", report["missingEvidence"])
            missing = report["checks"]["captureGuidance"]["missingMarkers"]
            self.assertIn("锁屏小组件视觉结论", missing["captureGuide"])
            self.assertIn("RealDevice/RD-23-lock-screen-widget-summary.png", missing["captureGuide"])
            self.assertIn(
                "RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须使用独立证据文件",
                missing["appStoreEvidenceReadme"],
            )

    def test_capture_guidance_requires_current_execution_packet_dates(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_capture_guidance(root)
            readme = root / "Docs/08_Release/AppStoreEvidence/README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                .replace("APP_STORE_MANUAL_EVIDENCE_PACKET_20260628.json", "APP_STORE_MANUAL_EVIDENCE_PACKET_20260627.json")
                .replace("FOCUSED_CAPTURE_PACKET_20260628.json", "FOCUSED_CAPTURE_PACKET_20260627.json")
                .replace(
                    "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-28 --output Backend/proof/app-store-evidence-20260628T-current.json",
                    "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json",
                ),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("captureGuidance", report["missingEvidence"])
            missing = report["checks"]["captureGuidance"]["missingMarkers"]["appStoreEvidenceReadme"]
            self.assertIn("Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260628.json", missing)
            self.assertIn("RealDevice/FOCUSED_CAPTURE_PACKET_20260628.json", missing)
            self.assertIn(
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-28 --output Backend/proof/app-store-evidence-20260628T-current.json",
                missing,
            )

    def test_required_evidence_files_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "17-age-rating-result.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "AppleDeveloper/16-account-roles-access.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_manual_evidence_checklist(root)
            write_manual_evidence_packet(root)
            write_capture_guidance(root)
            write_real_device_regression(evidence / "12-real-device-regression.md")

            report = self.run_checker(root)

            self.assertTrue(report["ready"])
            self.assertEqual(report["missingEvidence"], [])

    def test_placeholder_markdown_files_do_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.todo.md",
                "02-mainland-availability.todo.md",
                "03-app-filing.todo.md",
                "04-privacy-label.todo.md",
                "05-signed-archive.todo.md",
                "06-testflight.todo.md",
                "07-sms-provider.todo.md",
                "08-wechat-open-platform.todo.md",
                "09-obs-policy.todo.md",
            ]:
                write(evidence / name, b"placeholder")
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("companyAccount", report["missingEvidence"])
            self.assertIn("wechatOpenPlatform", report["missingEvidence"])
            self.assertNotIn("finalScreenshots", report["missingEvidence"])
            self.assertIn("reviewTestAccount", report["missingEvidence"])

    def test_tiny_manual_screenshot_does_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            write(evidence / "01-company-account.png", b"x" * 256)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_manual_evidence_checklist(root)
            write_real_device_regression(evidence / "12-real-device-regression.md")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("companyAccount", report["missingEvidence"])
            self.assertEqual(report["checks"]["companyAccount"]["minimumBytes"], 10 * 1024)
            self.assertEqual(
                report["checks"]["companyAccount"]["smallEvidenceFiles"],
                [{"file": "01-company-account.png", "size": 256}],
            )

    def test_text_evidence_rejects_secret_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            write(evidence / "04-privacy-label.json", b'{"apiKey":"sk-1234567890123456"}')
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("privacyLabel", report["missingEvidence"])
            self.assertEqual(
                report["checks"]["privacyLabel"]["forbiddenTextEvidenceMarkers"],
                ["04-privacy-label.json:apiKey"],
            )

    def test_final_screenshots_require_ios265_provenance_asset_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            proof_path = root / "Backend/proof/app-store-assets.json"
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            proof["checks"]["finalScreenshotsIOS265ProvenancePresent"]["passed"] = False
            proof_path.write_text(json.dumps(proof, ensure_ascii=False), encoding="utf-8")
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("finalScreenshots", report["missingEvidence"])
            self.assertIn(
                "finalScreenshotsIOS265ProvenancePresent",
                report["checks"]["finalScreenshots"]["failedAssetChecks"],
            )

    def test_real_device_regression_requires_checked_items(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            (evidence / "12-real-device-regression.md").write_text(
                "- [x] iOS 26.5\n- [ ] 微信登录\n",
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            missing = report["checks"]["realDeviceRegression"]["missingCheckedItems"]
            self.assertIn("微信登录", missing)
            self.assertIn("云同步", missing)
            self.assertIn("灵动岛喝奶提醒开关", missing)
            self.assertIn("灵动岛紧凑态头像和进度环未压到岛中心", missing)
            self.assertIn("锁屏通知栈上下相邻通知不遮挡提醒卡片", missing)
            self.assertIn("锁屏/桌面小组件", missing)
            self.assertIn("审核边界文案", missing)
            self.assertIn("missingEnvironmentFields", report["checks"]["realDeviceRegression"])
            self.assertIn("missingVisualConclusionFields", report["checks"]["realDeviceRegression"])
            self.assertIn("missingRegressionCaseIds", report["checks"]["realDeviceRegression"])

    def test_real_device_regression_requires_visual_boundary_conclusions(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")
            text = (evidence / "12-real-device-regression.md").read_text(encoding="utf-8")
            text = text.replace("- 灵动岛展开态结论：文字和数字留白正常，未贴边或被吞\n", "")
            text = text.replace("- [x] 灵动岛展开态文字和数字未贴边或被吞\n", "")
            (evidence / "12-real-device-regression.md").write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertIn("灵动岛展开态结论", real_device["missingVisualConclusionFields"])
            self.assertIn("灵动岛展开态文字和数字未贴边或被吞", real_device["missingCheckedItems"])

    def test_real_device_regression_rejects_vague_visual_conclusions(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")
            text = (evidence / "12-real-device-regression.md").read_text(encoding="utf-8")
            text = text.replace("- 灵动岛紧凑态结论：头像和进度环未压到岛中心", "- 灵动岛紧凑态结论：正常")
            text = text.replace("- 灵动岛展开态结论：文字和数字留白正常，未贴边或被吞", "- 灵动岛展开态结论：正常")
            text = text.replace("- 锁屏通知栈结论：上下相邻通知不遮挡提醒卡片", "- 锁屏通知栈结论：正常")
            text = text.replace("- 锁屏小组件结论：accessory 小组件内容不裁剪，不展示隐私照片", "- 锁屏小组件结论：正常")
            text = text.replace("- 桌面小组件结论：小尺寸和中尺寸内容不裁剪，不展示隐私照片", "- 桌面小组件结论：正常")
            (evidence / "12-real-device-regression.md").write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertEqual(
                set(real_device["invalidVisualConclusions"]),
                {"灵动岛紧凑态结论", "灵动岛展开态结论", "锁屏通知栈结论", "锁屏小组件结论", "桌面小组件结论"},
            )

    def test_real_device_regression_rejects_reused_or_generic_visual_evidence_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_manual_evidence_checklist(root)
            write_real_device_regression(evidence / "12-real-device-regression.md")
            text = (evidence / "12-real-device-regression.md").read_text(encoding="utf-8")
            text = text.replace(
                "| RD-22 用例 | 通过 | RealDevice/RD-22-dynamic-island-compact.png |",
                "| RD-22 用例 | 通过 | RealDevice/00-overview.png |",
            )
            text = text.replace(
                "| RD-23 用例 | 通过 | RealDevice/RD-23-lock-screen-notification-stack.png |",
                "| RD-23 用例 | 通过 | RealDevice/00-overview.png |",
            )
            (evidence / "12-real-device-regression.md").write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertEqual(
                real_device["invalidVisualRegressionEvidenceNames"],
                {
                    "RD-22": "RealDevice/00-overview.png",
                    "RD-23": "RealDevice/00-overview.png",
                },
            )
            self.assertEqual(real_device["duplicateVisualRegressionEvidencePaths"], ["RealDevice/00-overview.png"])
            self.assertEqual(
                real_device["reusedEnvironmentVisualRegressionEvidence"],
                {
                    "RD-22": "RealDevice/00-overview.png",
                    "RD-23": "RealDevice/00-overview.png",
                },
            )

    def test_real_device_regression_rejects_generic_login_and_account_evidence_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_manual_evidence_checklist(root)
            write_real_device_regression(evidence / "12-real-device-regression.md")
            text = (evidence / "12-real-device-regression.md").read_text(encoding="utf-8")
            text = text.replace(
                "| RD-10 用例 | 通过 | RealDevice/RD-10-recovery-login.png |",
                "| RD-10 用例 | 通过 | RealDevice/00-overview.png |",
            )
            text = text.replace(
                "| RD-13 用例 | 通过 | RealDevice/RD-13-phone-login.png |",
                "| RD-13 用例 | 通过 | RealDevice/00-overview.png |",
            )
            text = text.replace(
                "| RD-14 用例 | 通过 | RealDevice/RD-14-wechat-login.png |",
                "| RD-14 用例 | 通过 | RealDevice/00-overview.png |",
            )
            text = text.replace(
                "| RD-15 用例 | 通过 | RealDevice/RD-15-account-delete.png |",
                "| RD-15 用例 | 通过 | RealDevice/00-overview.png |",
            )
            (evidence / "12-real-device-regression.md").write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertEqual(
                real_device["invalidAuthAccountRegressionEvidenceNames"],
                {
                    "RD-10": "RealDevice/00-overview.png",
                    "RD-13": "RealDevice/00-overview.png",
                    "RD-14": "RealDevice/00-overview.png",
                    "RD-15": "RealDevice/00-overview.png",
                },
            )
            self.assertEqual(real_device["duplicateAuthAccountRegressionEvidencePaths"], ["RealDevice/00-overview.png"])
            self.assertEqual(
                real_device["reusedEnvironmentAuthAccountEvidence"],
                {
                    "RD-10": "RealDevice/00-overview.png",
                    "RD-13": "RealDevice/00-overview.png",
                    "RD-14": "RealDevice/00-overview.png",
                    "RD-15": "RealDevice/00-overview.png",
                },
            )

    def test_real_device_regression_template_does_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write(evidence / "12-real-device-regression.template.md", b"- [x] iOS 26.5\n")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertEqual(report["checks"]["realDeviceRegression"]["files"], [])

    def test_real_device_regression_rejects_copied_template_notice(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")
            text = (evidence / "12-real-device-regression.md").read_text(encoding="utf-8")
            text = "复制本文件为 `12-real-device-regression.md` 后再填写。\n" + text
            (evidence / "12-real-device-regression.md").write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertIn(
                "复制本文件为 `12-real-device-regression.md` 后再填写",
                real_device["templateMarkers"],
            )

    def test_real_device_regression_rejects_ios27_pending_and_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")
            text = (evidence / "12-real-device-regression.md").read_text(encoding="utf-8")
            text = text.replace("- iOS：26.5", "- iOS：27.0")
            text = text.replace("| RD-24 用例 | 通过 | RealDevice/RD-24-review-boundary.png |", "| RD-24 用例 | 待测 | 13800138000 |")
            text += "XNP_REVIEW_RECOVERY_KEY=secret\n"
            (evidence / "12-real-device-regression.md").write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertEqual(real_device["invalidIOSVersion"], "27.0")
            self.assertIn("待测", real_device["pendingMarkers"])
            self.assertIn("recoveryKeyAssignment", real_device["forbiddenSecretMarkers"])
            self.assertIn("mainlandPhoneNumber", real_device["forbiddenSecretMarkers"])

    def test_real_device_regression_requires_every_rd_case_to_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for index in range(1, 6):
                write(evidence / f"10-final-screenshots/iphone-{index}.png")
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")
            text = (evidence / "12-real-device-regression.md").read_text(encoding="utf-8")
            text = text.replace("| RD-23 用例 | 通过 | RealDevice/RD-23-lock-screen-notification-stack.png |", "| RD-23 用例 | 失败 | RealDevice/RD-23-lock-screen-notification-stack.png |")
            (evidence / "12-real-device-regression.md").write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertEqual(real_device["failedRegressionCaseStatuses"]["RD-23"], "失败")

    def test_real_device_regression_requires_each_rd_evidence_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")
            text = (evidence / "12-real-device-regression.md").read_text(encoding="utf-8")
            text = text.replace("| RD-05 用例 | 通过 | RealDevice/RD-05-diaper-record.png |", "| RD-05 用例 | 通过 |  |")
            text = text.replace("| RD-06 用例 | 通过 | RealDevice/RD-06-growth-record.png |", "| RD-06 用例 | 通过 | RealDevice/ |")
            (evidence / "12-real-device-regression.md").write_text(text, encoding="utf-8")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertIn("RD-05", real_device["missingRegressionEvidencePaths"])
            self.assertEqual(real_device["invalidRegressionEvidencePaths"]["RD-06"], "RealDevice/")

    def test_real_device_regression_rejects_tiny_evidence_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_manual_evidence_checklist(root)
            write_real_device_regression(evidence / "12-real-device-regression.md")
            write(evidence / "RealDevice/RD-23-lock-screen-notification-stack.png", b"x" * 256)

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            real_device = report["checks"]["realDeviceRegression"]
            self.assertIn("realDeviceRegression", report["missingEvidence"])
            self.assertEqual(
                real_device["missingRegressionEvidenceFiles"]["RD-23"],
                {
                    "path": "RealDevice/RD-23-lock-screen-notification-stack.png",
                    "exists": False,
                    "error": "evidence file is too small to be reliable",
                    "size": 256,
                    "minimumBytes": 10 * 1024,
                },
            )

    def test_final_screenshots_require_expected_upload_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for index in range(1, 6):
                write(evidence / f"10-final-screenshots/iphone-{index}.png")
            write_review_test_account(evidence / "11-test-account-redacted.json")
            write_real_device_regression(evidence / "12-real-device-regression.md")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("finalScreenshots", report["missingEvidence"])
            missing = report["checks"]["finalScreenshots"]["missingExpectedFilenames"]
            self.assertIn("01-home-iphone16pro.png", missing)

    def test_review_test_account_rejects_secret_or_unverified_values(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            evidence = root / "Docs/08_Release/AppStoreEvidence"
            for name in [
                "01-company-account.png",
                "02-mainland-availability.png",
                "03-app-filing.pdf",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "07-sms-provider.png",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.png",
                "09-obs-policy.png",
            ]:
                write(evidence / name)
            for filename in EXPECTED_SCREENSHOTS:
                write(evidence / f"10-final-screenshots/{filename}")
            write_app_store_assets_proof(root)
            write_review_test_account(
                evidence / "11-test-account-redacted.json",
                {
                    "accountId": "review-account-1",
                    "recoveryKeyStored": ".env.xnp-review-account",
                    "recoveryVerified": False,
                    "syncSeeded": True,
                    "containsSecret": True,
                    "recoveryKeySecret": "XNP_REVIEW_RECOVERY_KEY=secret",
                },
            )
            write_real_device_regression(evidence / "12-real-device-regression.md")

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertIn("reviewTestAccount", report["missingEvidence"])
            review_account = report["checks"]["reviewTestAccount"]
            self.assertFalse(review_account["recoveryVerified"])
            self.assertTrue(review_account["containsSecret"])
            self.assertIn("recoveryKeySecret", review_account["forbiddenFields"])
            self.assertIn("recoveryKeyAssignment", review_account["forbiddenSecretMarkers"])


if __name__ == "__main__":
    unittest.main()
