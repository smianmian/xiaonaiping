from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_testflight_regression_plan.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def complete_plan() -> str:
    rows = [
        ("RD-01", "冷启动进入首页", "不崩溃，首页可见", "待测"),
        ("RD-02", "创建宝宝档案", "本地保存成功", "待测"),
        ("RD-03", "记录喂养", "首页今日摘要和最近记录更新", "待测"),
        ("RD-04", "记录睡眠", "睡眠记录可保存、可回看", "待测"),
        ("RD-05", "记录排便", "排便记录可保存、可回看", "待测"),
        ("RD-06", "成长记录", "身高体重可保存，成长页可见", "待测"),
        ("RD-07", "疫苗模板切换", "中国大陆 / 香港模板可切换；文案不构成医疗建议", "待测"),
        ("RD-08", "相册权限拒绝", "拒绝权限后 App 不崩溃", "待测"),
        ("RD-09", "相册权限允许", "可主动加入照片；不自动扫描系统相册", "待测"),
        ("RD-10", "恢复密钥账号登录", "可用测试恢复密钥连接账号", "待测"),
        ("RD-11", "云备份", "备份成功", "待测"),
        ("RD-12", "云恢复", "清空/换装后可恢复测试数据", "待测"),
        ("RD-13", "手机号登录", "真实验证码可发送、可校验、频控正常", "待真实短信配置"),
        ("RD-14", "微信登录", "可拉起微信授权并回到 App", "待微信开放平台配置"),
        ("RD-15", "删除云端账号与备份", "云端备份、照片对象、账号失效", "待测"),
        ("RD-16", "断网保存", "本地记录可保存；云操作给出失败状态", "待测"),
        ("RD-17", "通知权限", "喂养提醒权限请求、提醒创建、关闭均正常", "待测"),
        ("RD-18", "Apple Watch 镜像通知", "iPhone 本地通知可按系统设置镜像到 Apple Watch", "待测"),
        ("RD-19", "隐私政策/用户协议/支持 URL", "App Store Connect URL 可打开，无 404", "待测"),
        ("RD-20", "崩溃/日志脱敏", "不输出宝宝内容、照片对象 key、手机号明文", "待测"),
        ("RD-21", "Release 包体自检", "ios-app-bundle.json 不含内部文档、本地地址、debug 文案或 API key 标记", "当前通过；微信配置仍阻断"),
        ("RD-22", "灵动岛喝奶提醒开关", "开关打开后仅在保存喝奶闹钟时展示下一次喝奶时间和固定间隔；关闭后结束 Live Activity", "待测"),
        ("RD-23", "锁屏/桌面小组件", "只读展示本机今日摘要，不展示照片原图、备注、token 或云端对象 key", "待测"),
        ("RD-24", "审核边界文案", "App 内和审核说明明确灵动岛/Live Activity/小组件只是状态展示，不暗示 HealthKit、传感器、健康建议、压力评估、压力提醒、心理健康判断、医疗诊断或喂养建议", "待测"),
    ]
    table = "\n".join(f"| {case_id} | {name} | {expected} | {result} |" for case_id, name, expected, result in rows)
    evidence_paths = "\n".join(
        [
            "| 环境总览 | `RealDevice/00-overview.png` |",
            "| RD-01 冷启动进入首页 | `RealDevice/RD-01-cold-start.png` |",
            "| RD-02 创建宝宝档案 | `RealDevice/RD-02-baby-profile.png` |",
            "| RD-03 记录喂养 | `RealDevice/RD-03-feeding-record.png` |",
            "| RD-04 记录睡眠 | `RealDevice/RD-04-sleep-record.png` |",
            "| RD-05 记录排便 | `RealDevice/RD-05-diaper-record.png` |",
            "| RD-06 成长记录 | `RealDevice/RD-06-growth-record.png` |",
            "| RD-07 疫苗模板切换 | `RealDevice/RD-07-vaccine-template.png` |",
            "| RD-08 相册权限拒绝 | `RealDevice/RD-08-photo-denied.png` |",
            "| RD-09 相册权限允许 | `RealDevice/RD-09-photo-allowed.png` |",
            "| RD-10 恢复密钥账号登录 | `RealDevice/RD-10-recovery-login.png` |",
            "| RD-11 云备份 | `RealDevice/RD-11-cloud-backup.png` |",
            "| RD-12 云恢复 | `RealDevice/RD-12-cloud-restore.png` |",
            "| RD-13 手机号登录 | `RealDevice/RD-13-phone-login.png` |",
            "| RD-14 微信登录 | `RealDevice/RD-14-wechat-login.png` |",
            "| RD-15 删除云端账号与备份 | `RealDevice/RD-15-account-delete.png` |",
            "| RD-16 断网保存 | `RealDevice/RD-16-offline-save.png` |",
            "| RD-17 通知权限 | `RealDevice/RD-17-notification-permission.png` |",
            "| RD-18 Apple Watch 镜像通知 | `RealDevice/RD-18-watch-mirror.png` |",
            "| RD-19 隐私政策/用户协议/支持 URL | `RealDevice/RD-19-public-urls.png` |",
            "| RD-20 崩溃/日志脱敏 | `RealDevice/RD-20-diagnostics-redaction.png` |",
            "| RD-21 Release 包体自检 | `RealDevice/RD-21-release-bundle.png` |",
            "| RD-22 灵动岛喝奶提醒开关 | `RealDevice/RD-22-live-activity-switch.png` |",
            "| RD-23 锁屏/桌面小组件 | `RealDevice/RD-23-widget-summary.png` |",
            "| RD-24 审核边界文案 | `RealDevice/RD-24-review-boundary.png` |",
        ]
    )
    return f"""
# TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md

## 文档状态

- 当前结论：恢复密钥测试账号已创建；iOS 26.5 本机模拟器安装启动烟测通过；TestFlight 真机回归尚未完成。

## 测试账号

| 项目 | 状态 |
|---|---|
| 恢复密钥测试账号 | 已创建 |
| 恢复密钥 | 只保存在本机 `.env.xnp-review-account`，不得提交到仓库 |

### App Store Connect 填写方式

1. 登录路径：打开 App -> 设置 -> 账号与备份 -> 恢复密钥登录。
2. 恢复密钥：读取本机 `.env.xnp-review-account` 中的 `XNP_REVIEW_RECOVERY_KEY`。

### 审核时不得使用

1. 不使用 debug code、工程内部账号、真实宝宝照片或真实家庭数据。
2. 不使用未配置完成的微信登录替代恢复密钥审核路径。

## 真机回归环境

| 项目 | 填写 |
|---|---|
| 设备 | 待填，当前本机模拟器只使用 iPhone 17 Pro / iOS 26.5 |
| iOS 版本 | iOS 26.5；本机测试不得改用旧 runtime |
| 安装方式 | TestFlight / Xcode 签名真机包 |
| 网络 | Wi-Fi + 蜂窝网络各一轮 |
| Apple ID 地区 | 中国大陆 |
| 证据文件 | `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md` |

### 当前本机真机可用性

| 设备 | 系统 | 状态 | 本轮处理 |
|---|---|---|---|
| 蓝蓝 / iPhone 16 Pro Max | iOS 26.5 | unavailable | 符合版本但当前不可用，未测试 |
| 面面 / iPhone 16 Plus | iOS 27.0 | available (paired) | 不符合本项目 iOS 26.5 本机测试规则，未测试 |

## 本机 iOS 26.5 烟测证据

| 启动 | 通过，输出 `com.mewpow.xiaonaiping: 15975` |
| 注意 | 该证据只证明本机 iOS 26.5 安装启动，不替代 TestFlight / 签名真机回归 |

## 必测用例

| 编号 | 用例 | 期望 | 结果 |
|---|---|---|---|
{table}

## 通过标准

1. RD-01 到 RD-12、RD-15 到 RD-24 必须通过。
2. RD-13 和 RD-14 必须在真实短信和微信配置完成后通过；不能用 debug code 代替。
3. 每轮真机回归必须附截图或录屏证据。

## 建议证据文件名

| 证据 | 建议路径 |
|---|---|
{evidence_paths}
""".lstrip()


def complete_template() -> str:
    return """
# 12-real-device-regression.md Template

> 复制本文件为 `12-real-device-regression.md` 后再填写，并删除本模板提示。不要把恢复密钥、验证码、完整手机号、token、真实宝宝照片或对象存储 key 写进来。
> 本项目真机回归只接受 iOS 26.5；iOS 27.0 不能作为本项目真机回归证据。

## 环境

- 设备：
- iOS：26.5
- 安装方式：TestFlight
- App 版本：
- Build：
- 网络：Wi-Fi / 蜂窝网络
- 证据截图/录屏：RealDevice/00-overview.png

## 必填勾选

- [ ] iOS 26.5
- [ ] 微信登录
- [ ] 账号删除
- [ ] 灵动岛喝奶提醒开关
- [ ] 锁屏/桌面小组件
- [ ] 审核边界文案

## RD-01 到 RD-24 结果

> 最终提交前每一行都必须改成“通过”，并填写截图或录屏证据路径。安装方式只能填写 `TestFlight` 或 `Xcode 签名真机包` 其中一个，不要保留斜杠选项。

| 编号 | 结果 | 证据/备注 |
|---|---|---|
| RD-01 冷启动进入首页 | 待测 | RealDevice/RD-01-cold-start.png |
| RD-02 创建宝宝档案 | 待测 | RealDevice/RD-02-baby-profile.png |
| RD-03 记录喂养 | 待测 | RealDevice/RD-03-feeding-record.png |
| RD-04 记录睡眠 | 待测 | RealDevice/RD-04-sleep-record.png |
| RD-05 记录排便 | 待测 | RealDevice/RD-05-diaper-record.png |
| RD-06 成长记录 | 待测 | RealDevice/RD-06-growth-record.png |
| RD-07 疫苗模板切换 | 待测 | RealDevice/RD-07-vaccine-template.png |
| RD-08 相册权限拒绝 | 待测 | RealDevice/RD-08-photo-denied.png |
| RD-09 相册权限允许 | 待测 | RealDevice/RD-09-photo-allowed.png |
| RD-10 恢复密钥账号登录 | 待测 | RealDevice/RD-10-recovery-login.png |
| RD-11 云备份 | 待测 | RealDevice/RD-11-cloud-backup.png |
| RD-12 云恢复 | 待测 | RealDevice/RD-12-cloud-restore.png |
| RD-13 手机号登录 | 待真实短信配置 | RealDevice/RD-13-phone-login.png |
| RD-14 微信登录 | 待微信开放平台配置 | RealDevice/RD-14-wechat-login.png |
| RD-15 删除云端账号与备份 | 待测 | RealDevice/RD-15-account-delete.png |
| RD-16 断网保存 | 待测 | RealDevice/RD-16-offline-save.png |
| RD-17 通知权限 | 待测 | RealDevice/RD-17-notification-permission.png |
| RD-18 Apple Watch 镜像通知 | 待测 | RealDevice/RD-18-watch-mirror.png |
| RD-19 隐私政策/用户协议/支持 URL | 待测 | RealDevice/RD-19-public-urls.png |
| RD-20 崩溃/日志脱敏 | 待测 | RealDevice/RD-20-diagnostics-redaction.png |
| RD-21 Release 包体自检 | 待测 | RealDevice/RD-21-release-bundle.png |
| RD-22 灵动岛喝奶提醒开关 | 待测 | RealDevice/RD-22-live-activity-switch.png |
| RD-23 锁屏/桌面小组件 | 待测 | RealDevice/RD-23-widget-summary.png |
| RD-24 审核边界文案 | 待测 | RealDevice/RD-24-review-boundary.png |

## 审核边界确认

- [ ] Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔。
- [ ] 小组件只读展示本机今日摘要。
- [ ] 状态展示只反映用户主动记录的数据。
- [ ] 不生成健康建议、压力提醒、喂养建议或医疗判断。
- [ ] 不接入 HealthKit。
- [ ] 不提供压力评估。
""".lstrip()


def write_complete_fixture(root: Path) -> None:
    write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", complete_plan())
    write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", complete_template())
    write_json(
        root / "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
        {
            "recoveryVerified": True,
            "backupSeeded": True,
            "containsSecret": False,
            "recoveryKeyStored": ".env.xnp-review-account",
        },
    )
    write_json(
        root / "Backend/proof/sim-launch-ios265-20260626.json",
        {
            "passed": True,
            "simulator": {"runtime": "iOS 26.5"},
            "app": {"dtPlatformVersion": "26.5"},
            "launchOutput": "com.mewpow.xiaonaiping: 15975",
        },
    )
    write_json(
        root / "Backend/proof/ios265-device-availability.json",
        {
            "passed": True,
            "requiredIOS": "26.5",
            "failedRequiredChecks": [],
            "eligibleIOS265PhysicalIphones": [],
            "availableNonIOS265PhysicalIphones": [
                {"name": "面面", "osVersion": "27.0", "available": True}
            ],
        },
    )
    write_json(
        root / "Backend/proof/app-store-evidence.json",
        {
            "ready": False,
            "missingEvidence": ["realDeviceRegression"],
            "checks": {
                "realDeviceRegression": {
                    "passed": False,
                    "files": [],
                }
            },
        },
    )


class TestFlightRegressionPlanTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/testflight-regression-plan.json"
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
        self.assertIn("TestFlight regression plan", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_complete_plan_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_cases_external_auth_and_secret_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            broken = complete_plan()
            broken = broken.replace("| RD-23 | 锁屏/桌面小组件 | 只读展示本机今日摘要，不展示照片原图、备注、token 或云端对象 key | 待测 |\n", "")
            broken = broken.replace("待真实短信配置", "待测")
            broken += "\nXNP_REVIEW_RECOVERY_KEY=secret\n"
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", broken)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("regressionCaseIdsComplete", report["failedRequiredChecks"])
            self.assertIn("externalAuthCasesMarkedPending", report["failedRequiredChecks"])
            self.assertIn("regressionPlanDoesNotExposeSecrets", report["failedRequiredChecks"])

    def test_loose_real_device_template_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            write(
                root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md",
                complete_template().replace("本项目真机回归只接受 iOS 26.5；iOS 27.0 不能作为本项目真机回归证据。", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceRegressionTemplateStrict", report["failedRequiredChecks"])

    def test_real_device_template_must_include_review_surface_checkboxes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            loose_template = complete_template()
            loose_template = loose_template.replace("- [ ] 灵动岛喝奶提醒开关\n", "")
            loose_template = loose_template.replace("- [ ] 锁屏/桌面小组件\n", "")
            loose_template = loose_template.replace("- [ ] 审核边界文案\n", "")
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", loose_template)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceRegressionTemplateStrict", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceRegressionTemplateStrict"]["evidence"]
            self.assertIn("- [ ] 灵动岛喝奶提醒开关", evidence)
            self.assertIn("- [ ] 锁屏/桌面小组件", evidence)
            self.assertIn("- [ ] 审核边界文案", evidence)

    def test_stale_ios265_launch_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            write_json(
                root / "Backend/proof/sim-launch-ios265-20260626.json",
                {
                    "passed": True,
                    "simulator": {"runtime": "iOS 26.5"},
                    "app": {"dtPlatformVersion": "26.5"},
                    "launchOutput": "com.mewpow.xiaonaiping: 92544",
                },
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ios265SmokeTextMatchesProof", report["failedRequiredChecks"])

    def test_real_device_regression_completion_must_not_be_implied(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            plan = complete_plan().replace("TestFlight 真机回归尚未完成", "TestFlight 真机回归")
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", plan)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceEvidenceGateSeparated", report["failedRequiredChecks"])

    def test_real_device_regression_evidence_can_satisfy_separation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            plan = complete_plan().replace("TestFlight 真机回归尚未完成", "TestFlight 真机回归")
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", plan)
            write_json(
                root / "Backend/proof/app-store-evidence.json",
                {
                    "ready": False,
                    "missingEvidence": ["companyAccount"],
                    "checks": {
                        "realDeviceRegression": {
                            "passed": True,
                            "files": ["Docs/08_Release/AppStoreEvidence/12-real-device-regression.md"],
                        }
                    },
                },
            )

            report = self.run_checker(root)

            self.assertTrue(report["checks"]["realDeviceEvidenceGateSeparated"]["passed"])


if __name__ == "__main__":
    unittest.main()
