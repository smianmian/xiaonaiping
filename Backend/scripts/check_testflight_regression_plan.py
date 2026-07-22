#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_CASE_IDS = {f"RD-{index:02d}" for index in range(1, 25)}
REAL_DEVICE_EXECUTION_SHEET = Path("Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md")
FOCUSED_CAPTURE_PACKET = Path("Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json")
REAL_DEVICE_CAPTURE_PREFLIGHT_PACKET = Path(
    "Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260630.json"
)
REAL_DEVICE_CAPTURE_RESULT_TEMPLATE = Path(
    "Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json"
)
DEFAULT_EXPECTED_SIM_LAUNCH_DATE = "20260630"
APP_STORE_EVIDENCE_CURRENT_PROOF = "Backend/proof/app-store-evidence-20260630T-current.json"
PRODUCTION_READINESS_CURRENT_PROOF = "Backend/proof/production-readiness-20260630T-current.json"
CHECK_APP_STORE_EVIDENCE_CURRENT = (
    "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete "
    "--date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json"
)
CHECK_PRODUCTION_READINESS_CURRENT = (
    "python3 Backend/scripts/check_production_readiness.py --allow-incomplete "
    "--output Backend/proof/production-readiness-20260630T-current.json"
)
REQUIRED_COVERAGE_MARKERS = {
    "coldStart": ("RD-01", "冷启动", "首页"),
    "babyProfile": ("RD-02", "创建宝宝档案"),
    "feedingRecord": ("RD-03", "记录喂养", "固定喝奶间隔", "顺延滚轮", "本顿结束时间 + 固定间隔 + 顺延分钟"),
    "sleepRecord": ("RD-04", "记录睡眠"),
    "diaperRecord": ("RD-05", "记录排便"),
    "growthRecord": ("RD-06", "成长记录"),
    "vaccineTemplate": ("RD-07", "疫苗模板切换", "不构成医疗建议"),
    "photoPermissionDenied": ("RD-08", "相册权限拒绝"),
    "photoPermissionAllowed": ("RD-09", "相册权限允许", "不自动扫描系统相册"),
    "recoveryKeyLogin": ("RD-10", "恢复密钥账号登录"),
    "cloudSync": ("RD-11", "云同步"),
    "cloudRestore": ("RD-12", "云恢复"),
    "phoneLogin": ("RD-13", "手机号登录"),
    "wechatLogin": ("RD-14", "微信登录"),
    "accountDeletion": ("RD-15", "删除云端账号与同步"),
    "offlineSave": ("RD-16", "断网保存"),
    "notificationPermission": ("RD-17", "通知权限"),
    "appleWatchMirror": ("RD-18", "Apple Watch"),
    "publicUrls": ("RD-19", "隐私政策/用户协议/支持 URL"),
    "diagnosticsRedaction": ("RD-20", "崩溃/日志脱敏"),
    "bundleSelfCheck": ("RD-21", "Release 包体自检"),
    "liveActivitySwitch": ("RD-22", "灵动岛喝奶提醒开关"),
    "widgets": ("RD-23", "锁屏/桌面小组件"),
    "reviewBoundary": ("RD-24", "审核边界文案"),
}
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    re.compile(r"sk-[A-Za-z0-9]{12,}"),
)
REQUIRED_TEMPLATE_MARKERS = (
    "不要把恢复密钥、验证码、完整手机号、token、真实宝宝照片或对象存储 key 写进来",
    "本项目真机回归只接受 iOS 26.5",
    "iOS 27.0 不能作为本项目真机回归证据",
    "- iOS：26.5",
    "- 安装方式：TestFlight",
    "安装方式只能填写 `TestFlight` 或 `Xcode 签名真机包` 其中一个",
    "- [ ] iOS 26.5",
    "- [ ] 微信登录",
    "- [ ] 账号删除",
    "- [ ] 通知权限",
    "- [ ] 通知权限允许后可创建下一次喝奶提醒",
    "- [ ] 通知权限拒绝后有可理解状态和系统设置入口",
    "- [ ] 通知权限允许独立截图",
    "- [ ] 通知权限拒绝独立截图",
    "- [ ] 灵动岛喝奶提醒开关",
    "- [ ] 喂养顺延滚轮只提供不顺延和 +5、+10、+15、+20、+25、+30 分钟",
    "- [ ] 下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算",
    "- [ ] 锁屏通知栈上下相邻通知不遮挡提醒卡片",
    "- [ ] 锁屏/桌面小组件",
    "- [ ] 灵动岛紧凑态独立截图",
    "- [ ] 灵动岛展开态独立截图",
    "- [ ] 灵动岛展开态展示手动顺延后的提醒时间",
    "- [ ] 锁屏通知栈独立截图",
    "- [ ] 锁屏小组件独立截图",
    "- [ ] 桌面小组件独立截图",
    "- [ ] 锁屏小组件内容不裁剪不展示隐私照片",
    "- [ ] 桌面小组件内容不裁剪不展示隐私照片",
    "- [ ] 审核边界文案",
    "RD-01",
    "RD-24",
    "最终提交前每一行都必须改成“通过”",
    "Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔",
    "手动顺延只改变下一次提醒时间",
    "不新增持久化字段",
    "不顺延、+5、+10、+15、+20、+25、+30 分钟",
    "本顿结束时间 + 固定间隔 + 顺延分钟",
    "本顿无喂养时长时按本顿发生时间",
    "小组件只读展示本机今日摘要",
    "状态展示只反映用户主动记录的数据",
    "不生成健康建议、压力提醒、喂养建议",
    "不接入 HealthKit",
    "不提供压力评估",
    "RD-17 通知权限 | 待测 | RealDevice/RD-17-notification-allowed.png；RealDevice/RD-17-notification-denied.png",
    "RD-22 灵动岛喝奶提醒开关 | 待测 | RealDevice/RD-22-dynamic-island-compact.png；RealDevice/RD-22-dynamic-island-expanded.png",
    "RD-23 锁屏/桌面小组件 | 待测 | RealDevice/RD-23-lock-screen-notification-stack.png；RealDevice/RD-23-lock-screen-widget-summary.png；RealDevice/RD-23-home-widget-summary.png",
)
REQUIRED_CAPTURE_SHOT_LIST_MARKERS = (
    "## 重点采集清单",
    "iOS 26.5 TestFlight",
    "Xcode 签名真机包",
    "模拟器、iOS 27、模板截图、空白图或口头结论不能替代",
    "灵动岛紧凑态",
    "灵动岛展开态",
    "手动顺延后的提醒时间",
    "不顺延、+5、+10、+15、+20、+25、+30 分钟",
    "本顿结束时间 + 固定间隔 + 顺延分钟",
    "本顿无喂养时长时按本顿发生时间",
    "不新增持久化字段",
    "锁屏通知栈",
    "锁屏小组件",
    "桌面小组件",
    "恢复密钥登录",
    "手机号登录",
    "微信登录",
    "账号删除",
    "通知权限允许",
    "通知权限拒绝",
    "每项必须使用独立证据文件",
    "RealDevice/RD-17-notification-allowed.png",
    "RealDevice/RD-17-notification-denied.png",
    "RealDevice/RD-22-dynamic-island-compact.png",
    "RealDevice/RD-22-dynamic-island-expanded.png",
    "RealDevice/RD-23-lock-screen-notification-stack.png",
    "RealDevice/RD-23-lock-screen-widget-summary.png",
    "RealDevice/RD-23-home-widget-summary.png",
    "RealDevice/RD-10-recovery-login.png",
    "RealDevice/RD-13-phone-login.png",
    "RealDevice/RD-14-wechat-login.png",
    "RealDevice/RD-15-account-delete.png",
)
REQUIRED_SAME_DAY_EXECUTION_ORDER_MARKERS = (
    "## 上线当天执行顺序",
    "ios265-device-availability.json",
    "05-signed-archive.png",
    "06-testflight.png",
    "verify_auth_providers.py --send-test-sms --require-sms-live-send",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "09-obs-policy.png",
    "check_production_readiness.py",
    "production proof 变绿",
    "不能先跑真机回归再补服务商证据",
    "RD-13-phone-login.png",
    "RD-14-wechat-login.png",
    "RD-11-cloud-sync.png",
    "RD-12-cloud-restore.png",
    "RD-15-account-delete.png",
    "RD-22-dynamic-island-compact.png",
    "RD-22-dynamic-island-expanded.png",
    "RD-23-lock-screen-notification-stack.png",
    "RD-23-lock-screen-widget-summary.png",
    "RD-23-home-widget-summary.png",
    "12-real-device-regression.md",
)
REQUIRED_EVIDENCE_INDEX_MARKERS = (
    "证据索引与脱敏复核",
    "同一 TestFlight build 或 Xcode 签名真机包",
    "文件大小",
    "不低于 10KB",
    "独立证据",
    "脱敏复核",
    "恢复密钥",
    "验证码",
    "完整手机号",
    "token",
    "对象存储 key",
    "真实宝宝照片",
    "12-real-device-regression.md",
)
REQUIRED_EVIDENCE_INDEX_ROWS = (
    "| `RealDevice/00-overview.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-10-recovery-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-13-phone-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-14-wechat-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-15-account-delete.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-17-notification-allowed.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-17-notification-denied.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-22-dynamic-island-compact.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-22-dynamic-island-expanded.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-23-lock-screen-notification-stack.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-23-lock-screen-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
    "| `RealDevice/RD-23-home-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 |",
)
REQUIRED_NOTIFICATION_PERMISSION_RESET_MARKERS = (
    "## 通知权限双路径重置锁",
    "RD-17 必须分别验证允许和拒绝两条路径",
    "iOS 通知授权状态会保留",
    "删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包",
    "在系统设置中重置小奶瓶通知授权并确认首次弹窗会重新出现",
    "不能在已经允许通知的安装状态下拍拒绝路径",
    "不能在已经拒绝通知的安装状态下拍允许路径",
    "通知权限允许",
    "通知权限拒绝",
    "干净通知授权状态",
    "首次弹窗可见",
    "pending reminder 生效",
    "系统设置入口",
    "同一 App 版本 / Build 的独立安装或独立重置回合",
    "不能复用同一次授权状态",
    "不能复用同一张截图",
    "不能用系统设置页单独替代 App 内状态",
    "RealDevice/RD-17-notification-allowed.png",
    "RealDevice/RD-17-notification-denied.png",
)
REQUIRED_BUILD_IDENTITY_LOCK_MARKERS = (
    "## 同一 build 身份锁",
    "`05-signed-archive.png`",
    "`06-testflight.png`",
    "`AppStoreConnect/ASC-07-build-testflight-link.png`",
    "`APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md`",
    "`12-real-device-regression.md`",
    "App 版本",
    "Build 号",
    "版本号和 build 号必须一致",
    "同一 TestFlight build 或 Xcode 签名真机包",
    "不能混用不同 build",
    "`check_ios_app_bundle.py`",
    "`check_testflight_precheck.py`",
    "`check_testflight_regression_plan.py`",
    "`check_app_store_evidence.py --allow-incomplete`",
)
REQUIRED_FAILURE_TRIAGE_MARKERS = (
    "## 失败复测与阻断清单",
    "失败 RD",
    "失败现象",
    "失败证据",
    "复测证据",
    "复测结果",
    "阻断结论",
    "不得提交 App Store Connect",
    "保留失败截图或录屏",
    "不要覆盖失败证据",
    "RELEASE_CHECKLIST.md",
    "LAUNCH_GATE_RERUN_20260626.md",
    "production-readiness.json",
    "launch-objective-audit.json",
    "RD-13",
    "RD-14",
    "真实短信服务商",
    "微信开放平台",
    "iOS 26.5",
    "TestFlight build",
    "Xcode 签名真机包",
)
REQUIRED_REAL_DEVICE_EVIDENCE_PATHS = {
    "overview": "RealDevice/00-overview.png",
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
    "RD-17-denied": "RealDevice/RD-17-notification-denied.png",
    "RD-18": "RealDevice/RD-18-watch-mirror.png",
    "RD-19": "RealDevice/RD-19-public-urls.png",
    "RD-20": "RealDevice/RD-20-diagnostics-redaction.png",
    "RD-21": "RealDevice/RD-21-release-bundle.png",
    "RD-22": "RealDevice/RD-22-dynamic-island-compact.png",
    "RD-22-expanded": "RealDevice/RD-22-dynamic-island-expanded.png",
    "RD-23": "RealDevice/RD-23-lock-screen-notification-stack.png",
    "RD-23-lock-widget": "RealDevice/RD-23-lock-screen-widget-summary.png",
    "RD-23-home-widget": "RealDevice/RD-23-home-widget-summary.png",
    "RD-24": "RealDevice/RD-24-review-boundary.png",
}
REQUIRED_EXECUTION_SHEET_MARKERS = (
    "# 小奶瓶真机证据现场执行单",
    "现场拍摄和填表用，不是已完成证据",
    "12-real-device-regression.md",
    "Backend/proof/testflight-regression-plan.json",
    "Backend/proof/app-store-evidence-20260630T-current.json",
    "只接受 iOS 26.5",
    "构建来源只能是 `TestFlight` 或 `Xcode 签名真机包`",
    "RD 编号、用例名称和目标文件必须与",
    "TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
    "12-real-device-regression.template.md",
    "每个证据文件不低于 10KB",
    "不能写桌面、下载目录、微信临时目录或绝对路径",
    "不保存恢复密钥、token、对象 key、真实宝宝照片或未授权家庭资料",
    "外部后台证据不能互相替代",
    "外部后台证据按以下文件归档，不占用 RD 编号",
    "08b-wechat-universal-link-aasa.png",
    "17-age-rating-result.png",
    "rdResults.feedingReminderDeferral",
    "check_testflight_regression_plan.py",
)
REQUIRED_EXECUTION_SHEET_RD_ROWS = {
    "RD-01": ("RD-01 冷启动进入首页", "RealDevice/RD-01-cold-start.png"),
    "RD-02": ("RD-02 创建宝宝档案", "RealDevice/RD-02-baby-profile.png"),
    "RD-03": ("RD-03 记录喂养", "RealDevice/RD-03-feeding-record.png"),
    "RD-04": ("RD-04 记录睡眠", "RealDevice/RD-04-sleep-record.png"),
    "RD-05": ("RD-05 记录排便", "RealDevice/RD-05-diaper-record.png"),
    "RD-06": ("RD-06 成长记录", "RealDevice/RD-06-growth-record.png"),
    "RD-07": ("RD-07 疫苗模板切换", "RealDevice/RD-07-vaccine-template.png"),
    "RD-08": ("RD-08 相册权限拒绝", "RealDevice/RD-08-photo-denied.png"),
    "RD-09": ("RD-09 相册权限允许", "RealDevice/RD-09-photo-allowed.png"),
    "RD-10": ("RD-10 恢复密钥账号登录", "RealDevice/RD-10-recovery-login.png"),
    "RD-11": ("RD-11 云同步", "RealDevice/RD-11-cloud-sync.png"),
    "RD-12": ("RD-12 云恢复", "RealDevice/RD-12-cloud-restore.png"),
    "RD-13": ("RD-13 手机号登录", "RealDevice/RD-13-phone-login.png"),
    "RD-14": ("RD-14 微信登录", "RealDevice/RD-14-wechat-login.png"),
    "RD-15": ("RD-15 删除云端账号与同步", "RealDevice/RD-15-account-delete.png"),
    "RD-16": ("RD-16 断网保存", "RealDevice/RD-16-offline-save.png"),
    "RD-17-allowed": ("RD-17 通知权限", "RealDevice/RD-17-notification-allowed.png"),
    "RD-17-denied": ("RD-17 通知权限", "RealDevice/RD-17-notification-denied.png"),
    "RD-18": ("RD-18 Apple Watch 镜像通知", "RealDevice/RD-18-watch-mirror.png"),
    "RD-19": ("RD-19 隐私政策/用户协议/支持 URL", "RealDevice/RD-19-public-urls.png"),
    "RD-20": ("RD-20 崩溃/日志脱敏", "RealDevice/RD-20-diagnostics-redaction.png"),
    "RD-21": ("RD-21 Release 包体自检", "RealDevice/RD-21-release-bundle.png"),
    "RD-22-compact": ("RD-22 灵动岛喝奶提醒开关", "RealDevice/RD-22-dynamic-island-compact.png"),
    "RD-22-expanded": ("RD-22 灵动岛喝奶提醒开关", "RealDevice/RD-22-dynamic-island-expanded.png"),
    "RD-23-lock": ("RD-23 锁屏/桌面小组件", "RealDevice/RD-23-lock-screen-notification-stack.png"),
    "RD-23-lock-widget": ("RD-23 锁屏/桌面小组件", "RealDevice/RD-23-lock-screen-widget-summary.png"),
    "RD-23-home-widget": ("RD-23 锁屏/桌面小组件", "RealDevice/RD-23-home-widget-summary.png"),
    "RD-24": ("RD-24 审核边界文案", "RealDevice/RD-24-review-boundary.png"),
}
REQUIRED_FOCUSED_CAPTURE_SOURCE_FILES = {
    "plan": "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
    "template": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md",
    "executionSheet": "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md",
    "preflightPacket": "Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260630.json",
    "deviceAvailabilityProof": "Backend/proof/ios265-device-availability.json",
    "appStoreEvidenceProof": APP_STORE_EVIDENCE_CURRENT_PROOF,
}
REQUIRED_FOCUSED_CAPTURE_TARGET_EVIDENCE_FILES = {
    "RD-03": "RealDevice/RD-03-feeding-record.png",
    "RD-10": "RealDevice/RD-10-recovery-login.png",
    "RD-13": "RealDevice/RD-13-phone-login.png",
    "RD-14": "RealDevice/RD-14-wechat-login.png",
    "RD-15": "RealDevice/RD-15-account-delete.png",
    "RD-17-allowed": "RealDevice/RD-17-notification-allowed.png",
    "RD-17-denied": "RealDevice/RD-17-notification-denied.png",
    "RD-22-compact": "RealDevice/RD-22-dynamic-island-compact.png",
    "RD-22-expanded": "RealDevice/RD-22-dynamic-island-expanded.png",
    "RD-23-lock": "RealDevice/RD-23-lock-screen-notification-stack.png",
    "RD-23-lock-widget": "RealDevice/RD-23-lock-screen-widget-summary.png",
    "RD-23-home-widget": "RealDevice/RD-23-home-widget-summary.png",
}
REQUIRED_FOCUSED_CAPTURE_DEPENDENCY_FIELDS = (
    "artifactId",
    "target",
    "requiredBeforeCapture",
    "mustObserve",
    "doesNotReplace",
    "blockIfMissing",
    "initialStatus",
)
REQUIRED_FOCUSED_CAPTURE_DEPENDENCY_MARKERS = {
    "RD-03": (
        "iOS 26.5 physical iPhone available",
        "same TestFlight or Xcode signed build prepared",
        "fixed feeding interval configured",
        "deferral wheel options",
        "next reminder rebase",
        "does not prove RD-22 Dynamic Island",
        "does not prove notification permission",
    ),
    "RD-10": (
        ".env.xnp-review-account",
        "redacted review account proof",
        "recovery-key login works",
        "does not prove SMS login",
        "does not prove WeChat login",
    ),
    "RD-13": (
        "SMS provider live-send proof",
        "verify_auth_providers.py --send-test-sms --require-sms-live-send",
        "real SMS code can be sent and verified",
        "does not prove recovery-key login",
        "does not prove WeChat login",
    ),
    "RD-14": (
        "WeChat Open Platform proof",
        "AASA universal link proof",
        "real WeChat release values are configured",
        "WeChat authorization opens and returns",
        "does not prove SMS login",
        "does not prove recovery-key login",
    ),
    "RD-15": (
        "RD-11 cloud sync evidence",
        "RD-12 cloud restore evidence",
        "storage backend and OBS proof are green",
        "old token is rejected",
        "cloud JSON sync deletion",
        "cloud photo-object deletion",
        "does not prove production readiness",
    ),
    "RD-17-allowed": (
        "clean notification authorization state",
        "independent allow reset round",
        "first permission prompt is visible",
        "pending reminder is effective",
        "does not prove denied path",
    ),
    "RD-17-denied": (
        "clean notification authorization state",
        "independent deny reset round",
        "first permission prompt is visible",
        "does not pretend a reminder was created",
        "does not prove allowed path",
    ),
    "RD-22-compact": (
        "RD-03 feeding deferral scenario prepared",
        "Live Activity enabled",
        "compact state is not clipped",
        "does not prove expanded Dynamic Island",
        "does not prove lock screen widget",
    ),
    "RD-22-expanded": (
        "RD-03 feeding deferral scenario prepared",
        "Live Activity enabled",
        "manual deferral value is readable",
        "no health advice or medical claim",
        "does not prove compact Dynamic Island",
        "does not prove home widget",
    ),
    "RD-23-lock": (
        "RD-17 allowed path captured",
        "next feeding reminder exists",
        "notification stack does not cover the reminder card",
        "does not prove lock screen widget",
        "does not prove home widget",
    ),
    "RD-23-lock-widget": (
        "lock screen widget configured",
        "accessory widget is readable",
        "no notes, photos, tokens, or object keys",
        "does not prove notification stack",
        "does not prove home widget",
    ),
    "RD-23-home-widget": (
        "home widget configured",
        "today summary is readable",
        "no notes, photos, tokens, or object keys",
        "does not prove lock screen widget",
        "does not prove notification stack",
    ),
}
REQUIRED_FOCUSED_CAPTURE_CASE_MARKERS = {
    "RealDevice/RD-03-feeding-record.png": (
        "RD-03",
        "记录喂养",
        "固定喝奶间隔",
        "顺延滚轮",
        "不顺延、+5、+10、+15、+20、+25、+30 分钟",
        "本顿结束时间 + 固定间隔 + 顺延分钟",
        "本顿无喂养时长时按本顿发生时间",
        "不根据奶量、月龄、传感器或健康数据自动推算",
    ),
    "RealDevice/RD-10-recovery-login.png": (
        "RD-10",
        "恢复密钥账号登录",
        "恢复密钥不入镜",
        ".env.xnp-review-account",
    ),
    "RealDevice/RD-13-phone-login.png": (
        "RD-13",
        "手机号登录",
        "真实短信服务商",
        "完整手机号",
        "验证码",
    ),
    "RealDevice/RD-14-wechat-login.png": (
        "RD-14",
        "微信登录",
        "微信开放平台",
        "debug code",
        "AppSecret",
    ),
    "RealDevice/RD-15-account-delete.png": (
        "RD-15",
        "删除云端账号与同步",
        "测试账号已完成云同步",
        "云端照片对象存在可删除 proof",
        "删除云端账号与同步入口可达",
        "确认弹窗文案清楚",
        "删除后旧 token 失效",
        "云端同步删除",
        "照片对象删除",
        "本机资料默认保留",
    ),
    "RealDevice/RD-17-notification-allowed.png": (
        "RD-17-allowed",
        "通知权限允许",
        "干净通知授权状态",
        "首次弹窗可见",
        "删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包",
        "不能复用同一次授权状态",
        "点击允许",
        "允许后可创建下一次喝奶提醒",
        "pending reminder 生效",
        "不展示系统外 debug 文案",
    ),
    "RealDevice/RD-17-notification-denied.png": (
        "RD-17-denied",
        "通知权限拒绝",
        "干净通知授权状态",
        "首次弹窗可见",
        "删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包",
        "不能复用同一次授权状态",
        "点击拒绝",
        "拒绝后有可理解状态",
        "系统设置入口可见",
        "不继续假装已创建提醒",
    ),
    "RealDevice/RD-22-dynamic-island-compact.png": (
        "RD-22-compact",
        "灵动岛紧凑态",
        "无裁剪",
        "独立证据文件",
    ),
    "RealDevice/RD-22-dynamic-island-expanded.png": (
        "RD-22-expanded",
        "灵动岛展开态",
        "手动顺延后的提醒时间",
        "不顺延、+5、+10、+15、+20、+25、+30 分钟",
        "本顿结束时间 + 固定间隔 + 顺延分钟",
        "本顿无喂养时长时按本顿发生时间",
        "不新增持久化字段",
    ),
    "RealDevice/RD-23-lock-screen-notification-stack.png": (
        "RD-23-lock",
        "锁屏通知栈",
        "不遮挡提醒卡片",
        "独立证据文件",
    ),
    "RealDevice/RD-23-lock-screen-widget-summary.png": (
        "RD-23-lock-widget",
        "锁屏小组件",
        "accessoryCircular",
        "accessoryRectangular",
        "accessoryInline",
        "只读展示本机今日摘要",
        "不展示备注",
        "不展示真实照片",
        "不展示 token",
        "不展示对象存储 key",
    ),
    "RealDevice/RD-23-home-widget-summary.png": (
        "RD-23-home-widget",
        "桌面小组件",
        "只读展示本机今日摘要",
        "不展示备注",
        "不展示真实照片",
        "不展示 token",
        "不展示对象存储 key",
    ),
}
REQUIRED_FOCUSED_CAPTURE_TARGET_FILES = tuple(REQUIRED_FOCUSED_CAPTURE_CASE_MARKERS)
REQUIRED_FOCUSED_CAPTURE_COMPLETION_MARKERS = (
    "template-only-not-evidence",
    "不替代 TestFlight / 签名真机回归",
    "不代表 RD-03/RD-10/RD-13/RD-14/RD-15/RD-17/RD-22/RD-23 已完成",
    "app-store-evidence-20260630T-current.json ready=true",
    "12-real-device-regression.md",
)
REQUIRED_FOCUSED_CAPTURE_POST_COMMANDS = (
    "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    CHECK_APP_STORE_EVIDENCE_CURRENT,
    "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
REQUIRED_FOCUSED_CAPTURE_MANIFEST_FIELDS = (
    "targetFile",
    "appVersion",
    "build",
    "installSource",
    "device",
    "ios",
    "captureStartedAt",
    "captureEndedAt",
    "fileSizeBytes",
    "sha256",
    "redactionChecked",
    "independentEvidenceFile",
    "sameBuildAs05SignedArchive",
    "sameBuildAs06TestFlight",
)
REQUIRED_FOCUSED_CAPTURE_MANIFEST_RULES = (
    "ios must equal 26.5",
    "installSource must be TestFlight or Xcode 签名真机包",
    "fileSizeBytes must be >= 10240",
    "sha256 must be recorded after capture",
    "redactionChecked must be true before copying into 12-real-device-regression.md",
    "independentEvidenceFile must be true; do not reuse overview screenshots",
    "sameBuildAs05SignedArchive and sameBuildAs06TestFlight must be true when TestFlight is used",
    "captureStartedAt and captureEndedAt must stay inside the same execution window",
)
FOCUSED_CAPTURE_PACKET_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameBuildAsFocusedCapture": False,
    "runtimeIsIos265": False,
    "sourceIsRealDeviceEvidenceRoot": False,
    "independentEvidenceFile": False,
    "realEvidenceNotTemplate": False,
    "secretValuesNotRecorded": False,
}
REAL_DEVICE_CAPTURE_TEMPLATE_REQUIRED_INSTRUCTIONS = (
    "Copy this file to REAL-DEVICE-CAPTURE-RESULT.json only after the iOS 26.5 live capture session.",
    "Set status to captured-live-real-device only after every RD screenshot or recording exists",
    "evidenceFileChecks",
    "file size",
    "SHA-256",
    "same-build confirmation",
    "iOS 26.5 runtime confirmation",
    "approved real-device evidence-root confirmation",
    "redaction review result",
    "xiaonaipingRequiredProofs",
    "postCaptureXiaoNaiPingProofReruns",
    "不能用一根呆毛 / Emotion Isle / cross-app readiness 替代",
    "Do not treat this result file as submit permission",
    "Backend/proof/app-store-evidence-20260630T-current.json ready=true",
    "Backend/proof/production-readiness-20260630T-current.json ready=true",
    "Backend/proof/launch-objective-audit.json ready=true",
    "Do not fill secrets",
)
REAL_DEVICE_CAPTURE_TEMPLATE_ALLOWED_INSTALL_SOURCES = ("TestFlight", "Xcode 签名真机包")
REAL_DEVICE_CAPTURE_TEMPLATE_FILE_CHECKS = REQUIRED_FOCUSED_CAPTURE_TARGET_EVIDENCE_FILES
REAL_DEVICE_CAPTURE_TEMPLATE_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameBuildAsResult": False,
    "runtimeIsIos265": False,
    "sourceIsRealDeviceEvidenceRoot": False,
    "secretValuesNotRecorded": False,
}
REAL_DEVICE_CAPTURE_TEMPLATE_RD_RESULT_REQUIREMENTS = {
    "feedingReminderDeferral": (
        ("status", "pending"),
        ("files", ("RealDevice/RD-03-feeding-record.png",)),
        ("fixedIntervalConfigured", False),
        ("deferralWheelOptionsVisible", False),
        ("allowedDeferralOptionsOnly", False),
        ("nextReminderRebasedFromEndOrOccurredAt", False),
        ("doesNotInferFromVolumeAgeSensorOrHealthData", False),
        ("noPersistentFieldAdded", False),
    ),
    "login.smsLogin": (
        ("status", "pending"),
        ("files", ("RealDevice/RD-13-phone-login.png",)),
        ("realSmsProviderSendVerified", False),
    ),
    "login.wechatLogin": (
        ("status", "pending"),
        ("files", ("RealDevice/RD-14-wechat-login.png",)),
        ("wechatAuthorizationOpened", False),
        ("wechatReturnedToXiaoNaiPing", False),
        ("noDebugCodePathUsed", False),
        ("appSecretNotVisible", False),
    ),
    "login.recoveryKeyLogin": (
        ("status", "pending"),
        ("files", ("RealDevice/RD-10-recovery-login.png",)),
        ("recoveryKeyLoginSucceeded", False),
        ("recoveryKeyNotVisible", False),
        ("accountSyncScreenReachable", False),
    ),
    "accountDelete": (
        ("status", "pending"),
        ("files", ("RealDevice/RD-15-account-delete.png",)),
        ("deleteEntryAndConfirmationVisible", False),
        ("oldTokenRejected", False),
        ("cloudJsonSyncDeleted", False),
        ("photoObjectsDeleted", False),
        ("localDataRetentionBoundaryVisible", False),
    ),
    "notificationPermission": (
        ("status", "pending"),
        (
            "files",
            (
                "RealDevice/RD-17-notification-allowed.png",
                "RealDevice/RD-17-notification-denied.png",
            ),
        ),
        ("allowAndDenyPathsCovered", False),
        ("cleanAuthorizationStateReset", False),
        ("allowedFirstPromptVisible", False),
        ("allowedReminderPendingAndEffective", False),
        ("deniedFirstPromptVisible", False),
        ("deniedSettingsEntryVisible", False),
        ("deniedDoesNotPretendReminderCreated", False),
    ),
    "dynamicIsland": (
        ("status", "pending"),
        (
            "files",
            (
                "RealDevice/RD-22-dynamic-island-compact.png",
                "RealDevice/RD-22-dynamic-island-expanded.png",
            ),
        ),
        ("visualQA.compactNotClipped", False),
        ("visualQA.compactNotCenteredIncorrectly", False),
        ("visualQA.expandedNextFeedingReadable", False),
        ("visualQA.expandedFixedIntervalReadable", False),
        ("visualQA.manualDeferralReadable", False),
        ("visualQA.noPersistentDeferralFieldClaimed", False),
        ("visualQA.noHealthAdviceOrMedicalClaim", False),
    ),
    "lockScreen": (
        ("status", "pending"),
        (
            "files",
            (
                "RealDevice/RD-23-lock-screen-notification-stack.png",
                "RealDevice/RD-23-lock-screen-widget-summary.png",
            ),
        ),
        ("visualQA.notificationStackDoesNotCoverCard", False),
        ("visualQA.reminderCardReadable", False),
        ("visualQA.widgetNotClipped", False),
        ("visualQA.accessoryCircularReadable", False),
        ("visualQA.accessoryRectangularReadable", False),
        ("visualQA.accessoryInlineReadable", False),
        ("visualQA.noPrivatePhotoOrObjectKey", False),
    ),
    "homeWidget": (
        ("status", "pending"),
        ("files", ("RealDevice/RD-23-home-widget-summary.png",)),
        ("visualQA.todaySummaryReadable", False),
        ("visualQA.homeWidgetNotClipped", False),
        ("visualQA.localTodaySummaryOnly", False),
        ("visualQA.noNotesPrivatePhotoTokenOrObjectKey", False),
    ),
}
REAL_DEVICE_CAPTURE_TEMPLATE_REQUIRED_PROOFS = {
    "signedArchiveTestFlightMaterials": "Backend/proof/signed-archive-testflight-materials.json",
    "testflightRegressionPlan": "Backend/proof/testflight-regression-plan.json",
    "appStoreConnectMaterials": "Backend/proof/app-store-connect-materials.json",
    "providerEvidenceMaterials": "Backend/proof/provider-evidence-materials.json",
    "mainlandFilingMaterials": "Backend/proof/mainland-filing-materials.json",
    "appStoreEvidence": APP_STORE_EVIDENCE_CURRENT_PROOF,
    "productionReadiness": PRODUCTION_READINESS_CURRENT_PROOF,
    "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
    "ios265DeviceAvailability": "Backend/proof/ios265-device-availability.json",
}
REAL_DEVICE_CAPTURE_TEMPLATE_POST_RERUNS = {
    "checkSignedArchiveTestFlightMaterials": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
    "checkTestFlightRegressionPlan": "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    "checkAppStoreConnectMaterials": "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
    "checkProviderEvidenceMaterials": "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "checkMainlandFilingMaterials": "python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "checkAppStoreEvidence": CHECK_APP_STORE_EVIDENCE_CURRENT,
    "checkProductionReadiness": CHECK_PRODUCTION_READINESS_CURRENT,
    "checkLaunchObjectiveAudit": "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
}
REAL_DEVICE_CAPTURE_TEMPLATE_SESSION_SCALARS = {
    "sessionId": "xnp-real-device-ios265-2026-06-30",
    "requiredRuntime": "iOS 26.5 physical iPhone only",
    "deviceAvailabilityProof": "Backend/proof/ios265-device-availability.json",
    "evidenceRoot": "Docs/08_Release/AppStoreEvidence/RealDevice/",
}
REAL_DEVICE_CAPTURE_TEMPLATE_SAME_BUILD_PROOFS = {
    "signedArchive": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
    "testFlight": "Docs/08_Release/AppStoreEvidence/06-testflight.png",
    "appStoreConnectBuildLink": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-07-build-testflight-link.png",
    "versionReleaseSettings": "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md",
}
REAL_DEVICE_CAPTURE_TEMPLATE_SESSION_FLAGS = (
    "sameBuildAcrossAllFocusedRdFiles",
    "sameBuildAsSignedArchive",
    "sameBuildAsTestFlight",
    "runtimeIsIos265PhysicalIphone",
    "notSimulator",
    "notIos27OrOtherRuntime",
    "allFocusedFilesUnderRealDeviceRoot",
    "allFocusedFilesHaveSha256AndSize",
    "allFocusedFilesRedacted",
)
REAL_DEVICE_CAPTURE_TEMPLATE_CAPTURE_GROUPS = {
    "login": ("RD-10", "RD-13", "RD-14"),
    "accountDelete": ("RD-15",),
    "notificationPermission": ("RD-17-allowed", "RD-17-denied"),
    "dynamicIsland": ("RD-22-compact", "RD-22-expanded"),
    "lockScreenAndWidgets": ("RD-23-lock", "RD-23-lock-widget", "RD-23-home-widget"),
}
REAL_DEVICE_CAPTURE_TEMPLATE_GROUP_REQUIREMENT_MARKERS = {
    "login": (
        "recovery-key account",
        "real SMS provider live-send proof",
        "WeChat Open Platform and AASA proof",
    ),
    "accountDelete": (
        "old token rejection",
        "cloud JSON sync deletion",
        "cloud photo-object deletion",
        "local data retention boundary",
    ),
    "notificationPermission": (
        "independent clean authorization states",
        "must not pretend a reminder was created",
    ),
    "dynamicIsland": (
        "same fixed feeding interval",
        "manual deferral result",
        "without health advice",
    ),
    "lockScreenAndWidgets": (
        "must not cover the reminder card",
        "avoid notes, real photos, tokens, and object keys",
    ),
}
REAL_DEVICE_CAPTURE_TEMPLATE_STOP_CONDITION_MARKERS = {
    "noIos265PhysicalIphone": (
        "ios265-device-availability.json",
        "iOS 26.5 physical iPhone",
        "do not start real-device capture",
    ),
    "mixedBuildEvidence": (
        "same TestFlight build",
        "Xcode signed device build",
        "recapture the whole focused set",
    ),
    "simulatorOrIos27Evidence": (
        "simulator",
        "iOS 27",
        "reject the evidence",
    ),
    "notificationResetMissing": (
        "reuse the same notification authorization state",
        "reset notification authorization",
    ),
    "externalProviderProofMissing": (
        "SMS/WeChat/AASA provider proof",
        "complete provider evidence",
    ),
}
REAL_DEVICE_CAPTURE_TEMPLATE_ARTIFACT_CAPTURE_FLAGS = {
    "initialStatus": "pending",
    "sameBuildRequired": True,
    "runtimeIsIos265Required": True,
    "independentEvidenceFileRequired": True,
}
REAL_DEVICE_CAPTURE_TEMPLATE_ARTIFACT_CAPTURE_MATRIX = {
    "RD-03": {
        "target": "RealDevice/RD-03-feeding-record.png",
        "group": "feedingReminderDeferral",
        "requiredBeforeCapture": (
            "fixed feeding interval configured",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "deferral wheel shows 不顺延",
            "+5",
            "+10",
            "+15",
            "+20",
            "+25",
            "+30",
            "next reminder uses end time plus fixed interval plus manual deferral",
            "occurredAt when duration is empty",
            "does not infer from volume, age, sensor, health data",
            "no persistent deferral field is added",
        ),
        "redaction": ("no real baby photos", "no private notes", "no tokens or object keys"),
        "failureEvidence": "RealDevice/RD-03-feeding-record-fail.png",
        "retestEvidence": "RealDevice/RD-03-feeding-record-retest.png",
    },
    "RD-10": {
        "target": "RealDevice/RD-10-recovery-login.png",
        "group": "login",
        "requiredBeforeCapture": (
            ".env.xnp-review-account redacted test account proof ready",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "recovery-key login works",
            "recovery key is not visible",
            "account and sync screen is reachable",
        ),
        "redaction": ("hide recovery key", "hide tokens", "hide complete phone number"),
        "failureEvidence": "RealDevice/RD-10-recovery-login-fail.png",
        "retestEvidence": "RealDevice/RD-10-recovery-login-retest.png",
    },
    "RD-13": {
        "target": "RealDevice/RD-13-phone-login.png",
        "group": "login",
        "requiredBeforeCapture": (
            "real SMS provider live-send proof",
            "provider evidence materials are green",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "real SMS code can be sent",
            "real SMS code can be verified",
            "rate limit or retry state is understandable",
            "no debug verification code is accepted",
        ),
        "redaction": ("hide complete phone number", "hide verification code", "hide SMS secret"),
        "failureEvidence": "RealDevice/RD-13-phone-login-fail.png",
        "retestEvidence": "RealDevice/RD-13-phone-login-retest.png",
    },
    "RD-14": {
        "target": "RealDevice/RD-14-wechat-login.png",
        "group": "login",
        "requiredBeforeCapture": (
            "WeChat Open Platform proof is green",
            "AASA universal link proof is green",
            "real WeChat release values are configured",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "WeChat authorization opens",
            "authorization returns to 小奶瓶",
            "no debug code path is used",
            "AppSecret is not visible",
        ),
        "redaction": ("hide AppSecret", "hide tokens", "hide complete phone number"),
        "failureEvidence": "RealDevice/RD-14-wechat-login-fail.png",
        "retestEvidence": "RealDevice/RD-14-wechat-login-retest.png",
    },
    "RD-15": {
        "target": "RealDevice/RD-15-account-delete.png",
        "group": "accountDelete",
        "requiredBeforeCapture": (
            "seeded sync proof ready",
            "seeded photo-object proof ready",
            "storage backend proof is green",
            "test account exists",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "delete entry and confirmation copy are visible",
            "old token is rejected after deletion",
            "cloud JSON sync is deleted",
            "cloud photo objects are deleted",
            "local data retention boundary is visible",
        ),
        "redaction": (
            "hide recovery key",
            "hide complete phone number",
            "hide tokens",
            "hide object keys",
        ),
        "failureEvidence": "RealDevice/RD-15-account-delete-fail.png",
        "retestEvidence": "RealDevice/RD-15-account-delete-retest.png",
    },
    "RD-17-allowed": {
        "target": "RealDevice/RD-17-notification-allowed.png",
        "group": "notificationPermission",
        "requiredBeforeCapture": (
            "clean notification authorization state via reinstall or reset",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "first notification permission prompt is visible",
            "Allow is tapped",
            "next feeding reminder is pending and effective",
            "settings status is understandable",
        ),
        "redaction": ("no private notes", "no tokens or object keys"),
        "failureEvidence": "RealDevice/RD-17-notification-allowed-fail.png",
        "retestEvidence": "RealDevice/RD-17-notification-allowed-retest.png",
    },
    "RD-17-denied": {
        "target": "RealDevice/RD-17-notification-denied.png",
        "group": "notificationPermission",
        "requiredBeforeCapture": (
            "clean notification authorization state via reinstall or reset",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "first notification permission prompt is visible",
            "Don't Allow is tapped",
            "system settings entry is visible",
            "does not pretend a reminder was created",
        ),
        "redaction": ("no private notes", "no tokens or object keys"),
        "failureEvidence": "RealDevice/RD-17-notification-denied-fail.png",
        "retestEvidence": "RealDevice/RD-17-notification-denied-retest.png",
    },
    "RD-22-compact": {
        "target": "RealDevice/RD-22-dynamic-island-compact.png",
        "group": "dynamicIsland",
        "requiredBeforeCapture": (
            "fixed feeding interval configured",
            "manual deferral scenario prepared",
            "Live Activity enabled",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "compact avatar or progress ring is not clipped",
            "compact state is not centered incorrectly",
            "no health advice or medical claim is shown",
        ),
        "redaction": ("no real baby photos", "no private notes", "no tokens or object keys"),
        "failureEvidence": "RealDevice/RD-22-dynamic-island-compact-fail.png",
        "retestEvidence": "RealDevice/RD-22-dynamic-island-compact-retest.png",
    },
    "RD-22-expanded": {
        "target": "RealDevice/RD-22-dynamic-island-expanded.png",
        "group": "dynamicIsland",
        "requiredBeforeCapture": (
            "fixed feeding interval configured",
            "manual deferral scenario prepared",
            "Live Activity enabled",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "next feeding time is readable",
            "fixed interval is readable",
            "manual deferral value from +5 through +30 or 不顺延 is readable",
            "no health advice or medical claim is shown",
            "no persistent deferral field is claimed",
        ),
        "redaction": ("no real baby photos", "no private notes", "no tokens or object keys"),
        "failureEvidence": "RealDevice/RD-22-dynamic-island-expanded-fail.png",
        "retestEvidence": "RealDevice/RD-22-dynamic-island-expanded-retest.png",
    },
    "RD-23-lock": {
        "target": "RealDevice/RD-23-lock-screen-notification-stack.png",
        "group": "lockScreenAndWidgets",
        "requiredBeforeCapture": (
            "notification stack scenario prepared",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "notification stack does not cover the reminder card",
            "reminder card remains readable",
            "no private notes or object keys are visible",
        ),
        "redaction": ("no real baby photos", "no private notes", "no tokens or object keys"),
        "failureEvidence": "RealDevice/RD-23-lock-screen-notification-stack-fail.png",
        "retestEvidence": "RealDevice/RD-23-lock-screen-notification-stack-retest.png",
    },
    "RD-23-lock-widget": {
        "target": "RealDevice/RD-23-lock-screen-widget-summary.png",
        "group": "lockScreenAndWidgets",
        "requiredBeforeCapture": (
            "lock screen widget configured",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "accessoryCircular is readable",
            "accessoryRectangular is readable",
            "accessoryInline is readable",
            "lock screen widget is not clipped or overflowing",
            "no notes, photos, tokens, or object keys are visible",
        ),
        "redaction": ("no real baby photos", "no private notes", "no tokens or object keys"),
        "failureEvidence": "RealDevice/RD-23-lock-screen-widget-summary-fail.png",
        "retestEvidence": "RealDevice/RD-23-lock-screen-widget-summary-retest.png",
    },
    "RD-23-home-widget": {
        "target": "RealDevice/RD-23-home-widget-summary.png",
        "group": "lockScreenAndWidgets",
        "requiredBeforeCapture": (
            "home widget configured",
            "same TestFlight or Xcode signed build prepared",
            "iOS 26.5 physical iPhone available",
        ),
        "mustObserve": (
            "today summary is readable",
            "home widget is not clipped or overflowing",
            "no notes, photos, tokens, or object keys are visible",
        ),
        "redaction": ("no real baby photos", "no private notes", "no tokens or object keys"),
        "failureEvidence": "RealDevice/RD-23-home-widget-summary-fail.png",
        "retestEvidence": "RealDevice/RD-23-home-widget-summary-retest.png",
    },
}
REQUIRED_REAL_DEVICE_PREFLIGHT_SOURCE_FILES = {
    "plan": "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
    "focusedCapturePacket": "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
    "captureResultTemplate": "Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json",
    "executionSheet": "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md",
    "deviceAvailabilityProof": "Backend/proof/ios265-device-availability.json",
    "signedArchiveTestFlightMaterialsProof": "Backend/proof/signed-archive-testflight-materials.json",
    "testFlightPrecheckProof": "Backend/proof/testflight-precheck.json",
    "providerEvidenceProof": "Backend/proof/provider-evidence-materials.json",
    "productionReadinessProof": PRODUCTION_READINESS_CURRENT_PROOF,
    "appStoreEvidenceProof": APP_STORE_EVIDENCE_CURRENT_PROOF,
    "appStoreConnectSubmitReviewPreflight": "Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260630.json",
}
REQUIRED_REAL_DEVICE_PREFLIGHT_CHECKS = {
    "ios265PhysicalDeviceAvailable": (
        "Backend/proof/ios265-device-availability.json",
        "passed=true",
        "requiredIOS=26.5",
        "eligibleIOS265PhysicalIphoneAvailable",
        "iOS 27.0 cannot be used as local evidence",
    ),
    "sameBuildInputsReady": (
        "Backend/proof/signed-archive-testflight-materials.json",
        "passed=true",
        "05-signed-archive.png",
        "06-testflight.png",
        "AppStoreConnect/ASC-07-build-testflight-link.png",
        "APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md",
        "same App version and Build number",
    ),
    "installSourceAllowed": (
        "TestFlight",
        "Xcode 签名真机包",
        "simulator",
        "iOS 27",
        "debug-only build",
        "template screenshot",
        "empty image",
        "oral conclusion",
    ),
    "notificationPermissionResetReady": (
        "RD-17-notification-allowed.png",
        "RD-17-notification-denied.png",
        "clean authorization state",
        "first permission prompt visible",
        "independent install or independent reset round",
        "do not reuse the same authorization state",
        "do not use Settings screenshot alone",
    ),
    "externalLoginProvidersReady": (
        "Backend/proof/provider-evidence-materials.json",
        "passed=true before RD-13/RD-14",
        "SMS provider live send proof",
        "WeChat Open Platform evidence",
        "wechat Universal Link AASA evidence",
        "no debug code",
    ),
    "storageAndDeletionReady": (
        PRODUCTION_READINESS_CURRENT_PROOF,
        "ready=true before RD-11/RD-12/RD-15",
        "Huawei OBS private bucket proof",
        "sync restore proof",
        "photo object deletion proof",
        "old token rejected after account deletion",
    ),
    "dynamicIslandAndWidgetPreconditionsReady": (
        "RD-22-dynamic-island-compact.png",
        "RD-22-dynamic-island-expanded.png",
        "RD-23-lock-screen-notification-stack.png",
        "RD-23-lock-screen-widget-summary.png",
        "RD-23-home-widget-summary.png",
        "fixed feeding interval configured",
        "manual deferral wheel exercised",
        "next reminder rebased from end time or occurredAt",
        "lock screen widget added",
        "home widget added",
        "no health advice or medical claim",
    ),
    "redactionAndEvidenceRootReady": (
        "Docs/08_Release/AppStoreEvidence/RealDevice/",
        "recovery key",
        "verification code",
        "complete phone number",
        "Apple ID email",
        "AppSecret",
        "token",
        "object storage key",
        "real baby photo",
        "independent evidence file for every RD item",
        "fileSizeBytes >= 10240",
        "sha256 recorded after capture",
        "sourceIsRealDeviceEvidenceRoot=true",
    ),
}
REQUIRED_REAL_DEVICE_PREFLIGHT_CHECK_IDS = tuple(REQUIRED_REAL_DEVICE_PREFLIGHT_CHECKS)
REQUIRED_REAL_DEVICE_PREFLIGHT_CAPTURE_GATE_MATRIX = {
    "session-baseline": {
        "appliesTo": (
            "all focused RD files",
            "REAL-DEVICE-CAPTURE-RESULT.json",
            "12-real-device-regression.md",
        ),
        "requiresPreflightChecks": (
            "ios265PhysicalDeviceAvailable",
            "sameBuildInputsReady",
            "installSourceAllowed",
            "redactionAndEvidenceRootReady",
        ),
        "requiredEvidenceOutputs": (
            "RealDevice/00-overview.png",
            "REAL-DEVICE-CAPTURE-RESULT.json",
            "12-real-device-regression.md",
        ),
        "stopIf": (
            "iOS 26.5 physical iPhone is not available",
            "05-signed-archive.png or 06-testflight.png is missing",
            "install source is simulator, iOS 27, debug-only build, template screenshot, empty image, or oral conclusion",
        ),
        "unlocks": (
            "copy REAL-DEVICE-CAPTURE-RESULT.template.json",
            "open EXECUTION_SHEET_20260630.md",
        ),
        "postGateReruns": (
            "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
        ),
    },
    "external-login": {
        "appliesTo": (
            "RD-13-phone-login.png",
            "RD-14-wechat-login.png",
        ),
        "requiresPreflightChecks": (
            "externalLoginProvidersReady",
            "sameBuildInputsReady",
        ),
        "requiredEvidenceOutputs": (
            "RealDevice/RD-13-phone-login.png",
            "RealDevice/RD-14-wechat-login.png",
        ),
        "stopIf": (
            "SMS provider live-send proof is missing",
            "WeChat Open Platform evidence is missing",
            "wechat Universal Link AASA evidence is missing",
        ),
        "unlocks": (
            "capture RD-13 phone login",
            "capture RD-14 WeChat login",
        ),
        "postGateReruns": (
            "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
            "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
        ),
    },
    "storage-deletion": {
        "appliesTo": (
            "RD-11-cloud-sync.png",
            "RD-12-cloud-restore.png",
            "RD-15-account-delete.png",
        ),
        "requiresPreflightChecks": (
            "storageAndDeletionReady",
            "sameBuildInputsReady",
        ),
        "requiredEvidenceOutputs": (
            "RealDevice/RD-11-cloud-sync.png",
            "RealDevice/RD-12-cloud-restore.png",
            "RealDevice/RD-15-account-delete.png",
        ),
        "stopIf": (
            "production-readiness-20260630T-current.json is not ready=true",
            "Huawei OBS private bucket proof is missing",
            "old token rejection after account deletion is missing",
        ),
        "unlocks": (
            "capture RD-11 cloud sync",
            "capture RD-12 cloud restore",
            "capture RD-15 account deletion",
        ),
        "postGateReruns": (
            CHECK_PRODUCTION_READINESS_CURRENT,
            "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
        ),
    },
    "notification-permission": {
        "appliesTo": (
            "RD-17-notification-allowed.png",
            "RD-17-notification-denied.png",
        ),
        "requiresPreflightChecks": (
            "notificationPermissionResetReady",
            "sameBuildInputsReady",
        ),
        "requiredEvidenceOutputs": (
            "RealDevice/RD-17-notification-allowed.png",
            "RealDevice/RD-17-notification-denied.png",
        ),
        "stopIf": (
            "allowed and denied paths reuse the same authorization state",
            "first permission prompt is not visible",
            "Settings screenshot is used alone",
        ),
        "unlocks": (
            "capture RD-17 allowed path",
            "reset authorization state",
            "capture RD-17 denied path",
        ),
        "postGateReruns": (
            "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
        ),
    },
    "live-activity-widgets": {
        "appliesTo": (
            "RD-22-dynamic-island-compact.png",
            "RD-22-dynamic-island-expanded.png",
            "RD-23-lock-screen-notification-stack.png",
            "RD-23-lock-screen-widget-summary.png",
            "RD-23-home-widget-summary.png",
        ),
        "requiresPreflightChecks": (
            "dynamicIslandAndWidgetPreconditionsReady",
            "notificationPermissionResetReady",
            "sameBuildInputsReady",
        ),
        "requiredEvidenceOutputs": (
            "RealDevice/RD-22-dynamic-island-compact.png",
            "RealDevice/RD-22-dynamic-island-expanded.png",
            "RealDevice/RD-23-lock-screen-notification-stack.png",
            "RealDevice/RD-23-lock-screen-widget-summary.png",
            "RealDevice/RD-23-home-widget-summary.png",
        ),
        "stopIf": (
            "fixed feeding interval is not configured",
            "manual deferral wheel is not exercised",
            "widget evidence shows private photo, note, token, or object key",
        ),
        "unlocks": (
            "capture RD-22 compact Dynamic Island",
            "capture RD-22 expanded Dynamic Island",
            "capture RD-23 lock screen and widget evidence",
        ),
        "postGateReruns": (
            "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
            CHECK_APP_STORE_EVIDENCE_CURRENT,
        ),
    },
    "finalize-regression": {
        "appliesTo": (
            "all RD-01 through RD-24 rows",
            "all focused evidenceFileChecks",
            "app-store-evidence-20260630T-current.json",
        ),
        "requiresPreflightChecks": (
            "ios265PhysicalDeviceAvailable",
            "sameBuildInputsReady",
            "externalLoginProvidersReady",
            "storageAndDeletionReady",
            "notificationPermissionResetReady",
            "dynamicIslandAndWidgetPreconditionsReady",
            "redactionAndEvidenceRootReady",
        ),
        "requiredEvidenceOutputs": (
            "REAL-DEVICE-CAPTURE-RESULT.json",
            "12-real-device-regression.md",
            APP_STORE_EVIDENCE_CURRENT_PROOF,
            "Backend/proof/launch-objective-audit.json",
        ),
        "stopIf": (
            "any focused RD file is missing SHA-256 or fileSizeBytes",
            "any focused RD file is outside RealDevice evidence root",
            "app-store-evidence-20260630T-current.json is not ready=true",
        ),
        "unlocks": (
            "mark realDeviceRegression evidence complete",
            "rerun launch objective audit",
        ),
        "postGateReruns": (
            CHECK_APP_STORE_EVIDENCE_CURRENT,
            "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
        ),
    },
}
REQUIRED_REAL_DEVICE_PREFLIGHT_CAPTURE_GATE_SCHEMA = (
    "id",
    "appliesTo",
    "requiresPreflightChecks",
    "requiredEvidenceOutputs",
    "stopIf",
    "unlocks",
    "postGateReruns",
    "initialStatus",
    "canSubmitFromGate",
)
REQUIRED_REAL_DEVICE_PREFLIGHT_DECISION_MARKERS = (
    "do-not-start-real-device-capture",
    "copy REAL-DEVICE-CAPTURE-RESULT.template.json to REAL-DEVICE-CAPTURE-RESULT.json",
    "same iOS 26.5 build",
    "file size, SHA-256, same-build, runtime, root, redaction and visualQA fields",
    "12-real-device-regression.md",
    "iOS 26.5 physical-device availability proof",
    "05-signed-archive.png",
    "06-testflight.png",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "08b-wechat-universal-link-aasa.png",
    "09-obs-policy.png",
    "REAL-DEVICE-CAPTURE-RESULT.json",
)
REQUIRED_REAL_DEVICE_PREFLIGHT_POST_COMMANDS = (
    "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    CHECK_APP_STORE_EVIDENCE_CURRENT,
    "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
REQUIRED_REAL_DEVICE_PREFLIGHT_COMPLETION_MARKERS = (
    "preflight-plan-not-evidence",
    "not iOS real-device evidence",
    "not TestFlight evidence",
    "not App Store Connect evidence",
    "not submission permission",
    "REAL-DEVICE-CAPTURE-RESULT.json",
    "12-real-device-regression.md",
    "app-store-evidence-20260630T-current.json ready=true",
    "launch-objective-audit.json ready=true",
    "不是 iOS 真机证据",
    "不能作为提交许可",
    "不能替代 TestFlight、签名归档、短信、微信、OBS、备案、最终截图或 App Store Connect 人工证据",
    "iOS 27、模拟器、模板截图、空白图或口头结论不能替代 iOS 26.5 真机证据",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def latest_sim_launch_proof(root: Path) -> Path:
    candidates = sorted((root / "Backend/proof").glob("sim-launch-ios265-*.json"))
    if candidates:
        return candidates[-1]
    return root / "Backend/proof/sim-launch-ios265-20260626.json"


def sim_launch_date_from(path: Path) -> str:
    match = re.search(r"sim-launch-ios265-(20\d{6})", path.name)
    return match.group(1) if match else ""


def nested_value(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for key in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_regression_cases(text: str) -> dict[str, dict[str, str]]:
    cases: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        case_id = cells[0]
        if re.fullmatch(r"RD-\d{2}", case_id):
            cases[case_id] = {
                "case": cells[1],
                "expected": cells[2],
                "result": cells[3],
                "line": line,
            }
    return cases


def contains_all(text: str, markers: tuple[str, ...]) -> bool:
    return all(marker in text for marker in markers)


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def execution_sheet_alignment_failures(text: str) -> list[str]:
    failures = missing_markers(text, REQUIRED_EXECUTION_SHEET_MARKERS)
    for key, (case_name, evidence_path) in REQUIRED_EXECUTION_SHEET_RD_ROWS.items():
        row_present = any(
            line.strip().startswith(f"| {case_name}") and evidence_path in line
            for line in text.splitlines()
        )
        if not row_present:
            failures.append(f"{key}: missing {case_name}, {evidence_path}")
    return failures


def evidence_index_failures(sources: tuple[tuple[str, str], ...]) -> list[str]:
    failures: list[str] = []
    for source, text in sources:
        for marker in REQUIRED_EVIDENCE_INDEX_MARKERS + REQUIRED_EVIDENCE_INDEX_ROWS:
            if marker not in text:
                failures.append(f"{source}: {marker}")
    return failures


def focused_capture_packet_failures(packet: dict[str, Any]) -> list[str]:
    if not packet:
        return ["missing focused capture packet"]

    failures: list[str] = []
    expected_scalars = {
        "artifactType": "real-device-focused-capture-packet",
        "status": "template-only-not-evidence",
        "date": "2026-06-30",
        "evidenceRoot": "Docs/08_Release/AppStoreEvidence/RealDevice/",
    }
    for key, expected in expected_scalars.items():
        if packet.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    requirements = packet.get("requirements", {})
    if not isinstance(requirements, dict):
        failures.append("requirements must be an object")
        requirements = {}
    if requirements.get("ios") != "26.5":
        failures.append("requirements.ios must be 26.5")
    build_sources = requirements.get("buildSourceOptions")
    if not isinstance(build_sources, list):
        failures.append("requirements.buildSourceOptions must be an array")
    else:
        for source in ("TestFlight", "Xcode 签名真机包"):
            if source not in build_sources:
                failures.append(f"requirements.buildSourceOptions missing {source}")
    if requirements.get("sameBuildRequired") is not True:
        failures.append("requirements.sameBuildRequired must be true")
    if requirements.get("noSimulatorEvidence") is not True:
        failures.append("requirements.noSimulatorEvidence must be true")
    min_file_bytes = requirements.get("minFileBytes")
    if not isinstance(min_file_bytes, int) or min_file_bytes < 10240:
        failures.append("requirements.minFileBytes must be at least 10240")
    if requirements.get("captureWindowRequired") is not True:
        failures.append("requirements.captureWindowRequired must be true")
    if requirements.get("independentEvidenceFileRequired") is not True:
        failures.append("requirements.independentEvidenceFileRequired must be true")

    source_files = packet.get("sourceFiles", {})
    if not isinstance(source_files, dict):
        failures.append("sourceFiles must be an object")
        source_files = {}
    for key, expected in REQUIRED_FOCUSED_CAPTURE_SOURCE_FILES.items():
        if source_files.get(key) != expected:
            failures.append(f"sourceFiles.{key} must be {expected}")

    target_evidence_files = packet.get("targetEvidenceFiles")
    if not isinstance(target_evidence_files, dict):
        failures.append("targetEvidenceFiles must be an object")
        target_evidence_files = {}
    elif tuple(target_evidence_files) != tuple(REQUIRED_FOCUSED_CAPTURE_TARGET_EVIDENCE_FILES):
        failures.append("targetEvidenceFiles order must match focused capture execution order")
    for key, expected in REQUIRED_FOCUSED_CAPTURE_TARGET_EVIDENCE_FILES.items():
        if target_evidence_files.get(key) != expected:
            failures.append(f"targetEvidenceFiles.{key} must be {expected}")

    file_checks = packet.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append("evidenceFileChecks must be a list")
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for check in file_checks:
            if not isinstance(check, dict):
                failures.append("evidenceFileChecks entries must be objects")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in checks_by_artifact:
                failures.append(f"evidenceFileChecks duplicate {artifact_id}")
            checks_by_artifact[artifact_id] = check

        if tuple(artifact_order) != tuple(REQUIRED_FOCUSED_CAPTURE_TARGET_EVIDENCE_FILES):
            failures.append("evidenceFileChecks order must match focused capture execution order")

        for artifact_id, target_marker in REQUIRED_FOCUSED_CAPTURE_TARGET_EVIDENCE_FILES.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != target_marker:
                failures.append(f"evidenceFileChecks.{artifact_id}.target must be {target_marker}")
            for key, expected in FOCUSED_CAPTURE_PACKET_FILE_CHECK_PLACEHOLDERS.items():
                if check.get(key) != expected:
                    failures.append(f"evidenceFileChecks.{artifact_id}.{key} must be {expected!r}")

    dependency_matrix = packet.get("captureDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("captureDependencyMatrix must be a list")
    else:
        dependency_by_artifact: dict[str, dict[str, Any]] = {}
        dependency_order: list[Any] = []
        for dependency in dependency_matrix:
            if not isinstance(dependency, dict):
                failures.append("captureDependencyMatrix entries must be objects")
                continue
            artifact_id = dependency.get("artifactId")
            dependency_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("captureDependencyMatrix entry missing artifactId")
                continue
            if artifact_id in dependency_by_artifact:
                failures.append(f"captureDependencyMatrix duplicate {artifact_id}")
            dependency_by_artifact[artifact_id] = dependency
            if tuple(dependency) != REQUIRED_FOCUSED_CAPTURE_DEPENDENCY_FIELDS:
                failures.append(f"captureDependencyMatrix.{artifact_id} fields must be {', '.join(REQUIRED_FOCUSED_CAPTURE_DEPENDENCY_FIELDS)}")

        if tuple(dependency_order) != tuple(REQUIRED_FOCUSED_CAPTURE_TARGET_EVIDENCE_FILES):
            failures.append("captureDependencyMatrix order must match focused capture execution order")

        for artifact_id, target_marker in REQUIRED_FOCUSED_CAPTURE_TARGET_EVIDENCE_FILES.items():
            dependency = dependency_by_artifact.get(artifact_id)
            if not isinstance(dependency, dict):
                failures.append(f"captureDependencyMatrix.{artifact_id} missing object")
                continue
            if dependency.get("target") != target_marker:
                failures.append(f"captureDependencyMatrix.{artifact_id}.target must be {target_marker}")
            if dependency.get("blockIfMissing") is not True:
                failures.append(f"captureDependencyMatrix.{artifact_id}.blockIfMissing must be true")
            if dependency.get("initialStatus") != "pending":
                failures.append(f"captureDependencyMatrix.{artifact_id}.initialStatus must be pending")
            dependency_text = json.dumps(dependency, ensure_ascii=False)
            for marker in REQUIRED_FOCUSED_CAPTURE_DEPENDENCY_MARKERS[artifact_id]:
                if marker not in dependency_text:
                    failures.append(f"captureDependencyMatrix.{artifact_id} missing {marker}")

    cases = packet.get("cases")
    if not isinstance(cases, list):
        return failures + ["cases must be an array"]

    by_target: dict[str, dict[str, Any]] = {}
    by_id: dict[str, str] = {}
    case_target_files: list[str] = []
    for item in cases:
        if not isinstance(item, dict):
            failures.append("cases entry must be an object")
            continue
        case_id = item.get("id")
        if not isinstance(case_id, str) or not case_id:
            failures.append("cases entry missing id")
        elif case_id in by_id:
            failures.append(f"cases duplicate id {case_id}")
        else:
            by_id[case_id] = str(item.get("targetFile", ""))
        target_file = item.get("targetFile")
        if not isinstance(target_file, str) or not target_file:
            failures.append("cases entry missing targetFile")
            continue
        if target_file in by_target:
            failures.append(f"cases duplicate {target_file}")
        by_target[target_file] = item
        case_target_files.append(target_file)

    if tuple(case_target_files) != REQUIRED_FOCUSED_CAPTURE_TARGET_FILES:
        failures.append("cases order must match focused capture execution order")

    for target_file, markers in REQUIRED_FOCUSED_CAPTURE_CASE_MARKERS.items():
        item = by_target.get(target_file)
        if not item:
            failures.append(f"cases missing {target_file}")
            continue
        expected_id = markers[0]
        if item.get("id") != expected_id:
            failures.append(f"{target_file} id must be {expected_id}")
        item_text = json.dumps(item, ensure_ascii=False)
        for marker in markers:
            if marker not in item_text:
                failures.append(f"{target_file} missing {marker}")

    packet_text = json.dumps(packet, ensure_ascii=False)
    for marker in REQUIRED_FOCUSED_CAPTURE_COMPLETION_MARKERS:
        if marker not in packet_text:
            failures.append(f"completion boundary missing {marker}")
    post_commands = packet.get("postCaptureCommands")
    post_command_text = json.dumps(post_commands, ensure_ascii=False)
    for command in REQUIRED_FOCUSED_CAPTURE_POST_COMMANDS:
        if command not in post_command_text:
            failures.append(f"postCaptureCommands missing {command}")

    manifest = packet.get("evidenceManifestTemplate")
    if not isinstance(manifest, dict):
        failures.append("evidenceManifestTemplate must be an object")
    else:
        if manifest.get("status") != "manifest-template-not-evidence":
            failures.append("evidenceManifestTemplate.status must be manifest-template-not-evidence")
        target_files = manifest.get("targetFiles")
        if not isinstance(target_files, list):
            failures.append("evidenceManifestTemplate.targetFiles must be an array")
            target_files = []
        target_file_set: set[str] = set()
        for target_file in target_files:
            target_file_text = str(target_file)
            if target_file_text in target_file_set:
                failures.append(f"evidenceManifestTemplate.targetFiles duplicate {target_file_text}")
            target_file_set.add(target_file_text)
        expected_target_files = tuple(REQUIRED_FOCUSED_CAPTURE_CASE_MARKERS)
        if tuple(str(target_file) for target_file in target_files) != expected_target_files:
            failures.append("evidenceManifestTemplate.targetFiles order must match focused capture cases")
        for target_file in REQUIRED_FOCUSED_CAPTURE_CASE_MARKERS:
            if target_file not in target_files:
                failures.append(f"evidenceManifestTemplate.targetFiles missing {target_file}")
        required_fields = manifest.get("requiredFields")
        if not isinstance(required_fields, list):
            failures.append("evidenceManifestTemplate.requiredFields must be an array")
            required_fields = []
        for field in REQUIRED_FOCUSED_CAPTURE_MANIFEST_FIELDS:
            if field not in required_fields:
                failures.append(f"evidenceManifestTemplate.requiredFields missing {field}")
        validation_rules = manifest.get("validationRules")
        if not isinstance(validation_rules, list):
            failures.append("evidenceManifestTemplate.validationRules must be an array")
            validation_rules = []
        for rule in REQUIRED_FOCUSED_CAPTURE_MANIFEST_RULES:
            if rule not in validation_rules:
                failures.append(f"evidenceManifestTemplate.validationRules missing {rule}")

    secret_hits = [pattern.pattern for pattern in FORBIDDEN_SECRET_PATTERNS if pattern.search(packet_text)]
    if secret_hits:
        failures.append("secret-like markers: " + ", ".join(secret_hits))
    return failures


def real_device_capture_result_template_failures(template: dict[str, Any]) -> list[str]:
    if not template:
        return ["missing real-device capture result template"]

    failures: list[str] = []
    expected_scalars: dict[str, Any] = {
        "status": "template-not-evidence",
        "app": "小奶瓶",
        "bundleId": "com.mewpow.xiaonaiping",
        "expectedRuntime": "iOS 26.5",
        "capturedBy": "佘鹏辉 / Penghui She",
        "sameBuildAsSignedArchiveAndTestFlight": False,
        "canSubmitAtCapture": False,
        "doNotTreatAsSubmitPermission": True,
        "redactionReviewed": False,
        "crossAppDoesNotReplaceXiaoNaiPingProof": True,
        "submissionReadinessProof": "Backend/proof/launch-objective-audit.json",
    }
    for key, expected in expected_scalars.items():
        if template.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    allowed_sources = template.get("allowedInstallSources")
    if tuple(allowed_sources or ()) != REAL_DEVICE_CAPTURE_TEMPLATE_ALLOWED_INSTALL_SOURCES:
        failures.append("allowedInstallSources must be TestFlight, Xcode 签名真机包")

    instruction_text = json.dumps(template.get("instructions"), ensure_ascii=False)
    for marker in REAL_DEVICE_CAPTURE_TEMPLATE_REQUIRED_INSTRUCTIONS:
        if marker not in instruction_text:
            failures.append(f"instructions missing {marker}")

    required_proofs = template.get("xiaonaipingRequiredProofs")
    if not isinstance(required_proofs, dict):
        failures.append("xiaonaipingRequiredProofs must be an object")
    else:
        if tuple(required_proofs) != tuple(REAL_DEVICE_CAPTURE_TEMPLATE_REQUIRED_PROOFS):
            failures.append("xiaonaipingRequiredProofs order must match real-device capture proof guard")
        for key, expected in REAL_DEVICE_CAPTURE_TEMPLATE_REQUIRED_PROOFS.items():
            if required_proofs.get(key) != expected:
                failures.append(f"xiaonaipingRequiredProofs.{key} must be {expected}")

    post_reruns = template.get("postCaptureXiaoNaiPingProofReruns")
    if not isinstance(post_reruns, dict):
        failures.append("postCaptureXiaoNaiPingProofReruns must be an object")
    else:
        if tuple(post_reruns) != tuple(REAL_DEVICE_CAPTURE_TEMPLATE_POST_RERUNS):
            failures.append(
                "postCaptureXiaoNaiPingProofReruns order must match real-device capture proof reruns"
            )
        for key, expected in REAL_DEVICE_CAPTURE_TEMPLATE_POST_RERUNS.items():
            if post_reruns.get(key) != expected:
                failures.append(f"postCaptureXiaoNaiPingProofReruns.{key} must be {expected}")

    session = template.get("captureSessionIntegrity")
    if not isinstance(session, dict):
        failures.append("captureSessionIntegrity must be an object")
    else:
        for key, expected in REAL_DEVICE_CAPTURE_TEMPLATE_SESSION_SCALARS.items():
            if session.get(key) != expected:
                failures.append(f"captureSessionIntegrity.{key} must be {expected}")

        same_build_proofs = session.get("sameBuildProofs")
        if not isinstance(same_build_proofs, dict):
            failures.append("captureSessionIntegrity.sameBuildProofs must be an object")
        else:
            if tuple(same_build_proofs) != tuple(REAL_DEVICE_CAPTURE_TEMPLATE_SAME_BUILD_PROOFS):
                failures.append("captureSessionIntegrity.sameBuildProofs order must match archive/TestFlight/build link proofs")
            for key, expected in REAL_DEVICE_CAPTURE_TEMPLATE_SAME_BUILD_PROOFS.items():
                if same_build_proofs.get(key) != expected:
                    failures.append(f"captureSessionIntegrity.sameBuildProofs.{key} must be {expected}")

        capture_flags = session.get("captureFlags")
        if not isinstance(capture_flags, dict):
            failures.append("captureSessionIntegrity.captureFlags must be an object")
        else:
            if tuple(capture_flags) != REAL_DEVICE_CAPTURE_TEMPLATE_SESSION_FLAGS:
                failures.append("captureSessionIntegrity.captureFlags order must match same-build/runtime/root/redaction checks")
            for flag in REAL_DEVICE_CAPTURE_TEMPLATE_SESSION_FLAGS:
                if capture_flags.get(flag) is not False:
                    failures.append(f"captureSessionIntegrity.captureFlags.{flag} must be False")

        capture_groups = session.get("captureGroups")
        if not isinstance(capture_groups, dict):
            failures.append("captureSessionIntegrity.captureGroups must be an object")
        else:
            if tuple(capture_groups) != tuple(REAL_DEVICE_CAPTURE_TEMPLATE_CAPTURE_GROUPS):
                failures.append("captureSessionIntegrity.captureGroups order must match login/account/notification/live/widget groups")
            for group, expected_ids in REAL_DEVICE_CAPTURE_TEMPLATE_CAPTURE_GROUPS.items():
                if tuple(capture_groups.get(group) or ()) != expected_ids:
                    failures.append(f"captureSessionIntegrity.captureGroups.{group} must be {', '.join(expected_ids)}")

        group_requirements = session.get("groupRequirements")
        if not isinstance(group_requirements, dict):
            failures.append("captureSessionIntegrity.groupRequirements must be an object")
        else:
            for group, markers in REAL_DEVICE_CAPTURE_TEMPLATE_GROUP_REQUIREMENT_MARKERS.items():
                lines = "\n".join(str(item) for item in group_requirements.get(group) or ())
                for marker in markers:
                    if marker not in lines:
                        failures.append(f"captureSessionIntegrity.groupRequirements.{group} missing {marker}")

        stop_conditions = session.get("stopConditions")
        if not isinstance(stop_conditions, list):
            failures.append("captureSessionIntegrity.stopConditions must be a list")
        else:
            by_id: dict[str, dict[str, Any]] = {}
            order: list[Any] = []
            for item in stop_conditions:
                if not isinstance(item, dict):
                    failures.append("captureSessionIntegrity.stopConditions entries must be objects")
                    continue
                condition_id = item.get("id")
                order.append(condition_id)
                if not isinstance(condition_id, str) or not condition_id:
                    failures.append("captureSessionIntegrity.stopConditions entry missing id")
                    continue
                if condition_id in by_id:
                    failures.append(f"captureSessionIntegrity.stopConditions duplicate {condition_id}")
                by_id[condition_id] = item
            if tuple(order) != tuple(REAL_DEVICE_CAPTURE_TEMPLATE_STOP_CONDITION_MARKERS):
                failures.append("captureSessionIntegrity.stopConditions order must match real-device capture stop conditions")
            for condition_id, markers in REAL_DEVICE_CAPTURE_TEMPLATE_STOP_CONDITION_MARKERS.items():
                item = by_id.get(condition_id)
                if not isinstance(item, dict):
                    failures.append(f"captureSessionIntegrity.stopConditions missing {condition_id}")
                    continue
                text = json.dumps(item, ensure_ascii=False)
                for marker in markers:
                    if marker not in text:
                        failures.append(f"captureSessionIntegrity.stopConditions.{condition_id} missing {marker}")

    artifact_matrix = template.get("artifactCaptureMatrix")
    if not isinstance(artifact_matrix, list):
        failures.append("artifactCaptureMatrix must be a list")
    else:
        matrix_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for row in artifact_matrix:
            if not isinstance(row, dict):
                failures.append("artifactCaptureMatrix entries must be objects")
                continue
            artifact_id = row.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("artifactCaptureMatrix entry missing artifactId")
                continue
            if artifact_id in matrix_by_artifact:
                failures.append(f"artifactCaptureMatrix duplicate {artifact_id}")
            matrix_by_artifact[artifact_id] = row

        if tuple(artifact_order) != tuple(REAL_DEVICE_CAPTURE_TEMPLATE_ARTIFACT_CAPTURE_MATRIX):
            failures.append("artifactCaptureMatrix order must match real-device focused capture workflow")

        for artifact_id, expected in REAL_DEVICE_CAPTURE_TEMPLATE_ARTIFACT_CAPTURE_MATRIX.items():
            row = matrix_by_artifact.get(artifact_id)
            if not isinstance(row, dict):
                failures.append(f"artifactCaptureMatrix missing {artifact_id}")
                continue
            for key, expected_value in REAL_DEVICE_CAPTURE_TEMPLATE_ARTIFACT_CAPTURE_FLAGS.items():
                if row.get(key) != expected_value:
                    failures.append(f"artifactCaptureMatrix.{artifact_id}.{key} must be {expected_value!r}")
            for key in ("target", "group", "failureEvidence", "retestEvidence"):
                if row.get(key) != expected[key]:
                    failures.append(f"artifactCaptureMatrix.{artifact_id}.{key} must be {expected[key]}")
            for key in ("requiredBeforeCapture", "mustObserve", "redaction"):
                text = "\n".join(str(item) for item in row.get(key) or ())
                for marker in expected[key]:
                    if marker not in text:
                        failures.append(f"artifactCaptureMatrix.{artifact_id}.{key} missing {marker}")

    file_checks = template.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append("evidenceFileChecks must be a list")
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for check in file_checks:
            if not isinstance(check, dict):
                failures.append("evidenceFileChecks entries must be objects")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in checks_by_artifact:
                failures.append(f"evidenceFileChecks duplicate {artifact_id}")
            checks_by_artifact[artifact_id] = check

        if tuple(artifact_order) != tuple(REAL_DEVICE_CAPTURE_TEMPLATE_FILE_CHECKS):
            failures.append("evidenceFileChecks order must match real-device focused capture workflow")

        for artifact_id, target_marker in REAL_DEVICE_CAPTURE_TEMPLATE_FILE_CHECKS.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"evidenceFileChecks.{artifact_id} missing object")
                continue
            if target_marker not in str(check.get("target", "")):
                failures.append(f"evidenceFileChecks.{artifact_id}.target missing {target_marker}")
            for key, expected in REAL_DEVICE_CAPTURE_TEMPLATE_FILE_CHECK_PLACEHOLDERS.items():
                if check.get(key) != expected:
                    failures.append(f"evidenceFileChecks.{artifact_id}.{key} must be {expected!r}")

    rd_results = template.get("rdResults")
    if not isinstance(rd_results, dict):
        failures.append("rdResults must be an object")
        rd_results = {}
    for section, expectations in REAL_DEVICE_CAPTURE_TEMPLATE_RD_RESULT_REQUIREMENTS.items():
        section_value = nested_value(rd_results, section)
        if not isinstance(section_value, dict):
            failures.append(f"rdResults.{section} must be an object")
            continue
        for field, expected in expectations:
            actual = nested_value(section_value, field) if "." in field else section_value.get(field)
            if isinstance(expected, tuple):
                if tuple(actual or ()) != expected:
                    failures.append(f"rdResults.{section}.{field} must be {', '.join(expected)}")
            elif actual != expected:
                failures.append(f"rdResults.{section}.{field} must be {expected}")

    template_text = json.dumps(template, ensure_ascii=False)
    forbidden_cross_app_submit_markers = (
        "/Users/smianmian/Emotion Isle/output/cross-app-submission-readiness",
        "cross-app-submission-readiness-20260630-current.json has canSubmit=true",
        "check-cross-app-submit-ready.py",
    )
    leaked_cross_app_submit_markers = [
        marker for marker in forbidden_cross_app_submit_markers if marker in template_text
    ]
    if leaked_cross_app_submit_markers:
        failures.append(
            "real-device capture result template must not depend on Emotion Isle cross-app submission readiness: "
            + ", ".join(leaked_cross_app_submit_markers)
        )
    for marker in (
        "captured-live-real-device",
        "all RD files exist",
        "evidenceFileChecks are filled with file size",
        "SHA-256",
        "same-build",
        "iOS 26.5 runtime",
        "approved root",
        "visualQA fields pass",
        "current submission readiness proof is attached",
        "crossAppDoesNotReplaceXiaoNaiPingProof is true",
        "xiaonaipingRequiredProofs are rerun",
        "postCaptureXiaoNaiPingProofReruns refresh",
    ):
        if marker not in template_text:
            failures.append(f"notes missing {marker}")

    secret_hits = [pattern.pattern for pattern in FORBIDDEN_SECRET_PATTERNS if pattern.search(template_text)]
    if secret_hits:
        failures.append("captureResultTemplate secret hits: " + ", ".join(secret_hits))
    return failures


def real_device_capture_preflight_failures(packet: dict[str, Any]) -> list[str]:
    if not packet:
        return ["missing real-device capture preflight packet"]

    failures: list[str] = []
    expected_scalars: dict[str, Any] = {
        "artifactType": "real-device-capture-preflight",
        "status": "preflight-plan-not-evidence",
        "date": "2026-06-30",
        "project": "XiaoNaiPing",
        "appName": "小奶瓶",
        "bundleId": "com.mewpow.xiaonaiping",
        "canStartCaptureFromThisPacket": False,
        "canSubmitFromThisPacket": False,
    }
    for key, expected in expected_scalars.items():
        if packet.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    source_files = packet.get("sourceFiles")
    if not isinstance(source_files, dict):
        failures.append("sourceFiles must be an object")
        source_files = {}
    for key, expected in REQUIRED_REAL_DEVICE_PREFLIGHT_SOURCE_FILES.items():
        if source_files.get(key) != expected:
            failures.append(f"sourceFiles.{key} must be {expected}")

    checks = packet.get("preflightChecks")
    if not isinstance(checks, list):
        failures.append("preflightChecks must be an array")
        checks = []
    checks_by_id: dict[str, dict[str, Any]] = {}
    check_ids: list[str] = []
    for item in checks:
        if not isinstance(item, dict):
            failures.append("preflightChecks entry must be an object")
            continue
        check_id = item.get("id")
        if not isinstance(check_id, str) or not check_id:
            failures.append("preflightChecks entry missing id")
            continue
        if check_id in checks_by_id:
            failures.append(f"preflightChecks duplicate {check_id}")
        checks_by_id[check_id] = item
        check_ids.append(check_id)
    if tuple(check_ids) != REQUIRED_REAL_DEVICE_PREFLIGHT_CHECK_IDS:
        failures.append("preflightChecks order must match real-device capture preflight order")

    for check_id, markers in REQUIRED_REAL_DEVICE_PREFLIGHT_CHECKS.items():
        item = checks_by_id.get(check_id)
        if not item:
            failures.append(f"preflightChecks missing {check_id}")
            continue
        item_text = json.dumps(item, ensure_ascii=False)
        for marker in markers:
            if marker not in item_text:
                failures.append(f"preflightChecks.{check_id} missing {marker}")

    gate_matrix = packet.get("captureGateMatrix")
    if not isinstance(gate_matrix, list):
        failures.append("captureGateMatrix must be an array")
        gate_matrix = []
    gates_by_id: dict[str, dict[str, Any]] = {}
    gate_ids: list[str] = []
    for item in gate_matrix:
        if not isinstance(item, dict):
            failures.append("captureGateMatrix entry must be an object")
            continue
        gate_id = item.get("id")
        if not isinstance(gate_id, str) or not gate_id:
            failures.append("captureGateMatrix entry missing id")
            continue
        if gate_id in gates_by_id:
            failures.append(f"captureGateMatrix duplicate {gate_id}")
        gates_by_id[gate_id] = item
        gate_ids.append(gate_id)
    if tuple(gate_ids) != tuple(REQUIRED_REAL_DEVICE_PREFLIGHT_CAPTURE_GATE_MATRIX):
        failures.append("captureGateMatrix order must match real-device capture gate order")

    for gate_id, expected in REQUIRED_REAL_DEVICE_PREFLIGHT_CAPTURE_GATE_MATRIX.items():
        item = gates_by_id.get(gate_id)
        if not isinstance(item, dict):
            failures.append(f"captureGateMatrix missing {gate_id}")
            continue
        if tuple(item) != REQUIRED_REAL_DEVICE_PREFLIGHT_CAPTURE_GATE_SCHEMA:
            failures.append(f"captureGateMatrix.{gate_id} keys must match capture gate schema")
        for key, expected_values in expected.items():
            values = item.get(key)
            if tuple(values or ()) != expected_values:
                failures.append(f"captureGateMatrix.{gate_id}.{key} must be {', '.join(expected_values)}")
        if item.get("initialStatus") != "pending":
            failures.append(f"captureGateMatrix.{gate_id}.initialStatus must be pending")
        if item.get("canSubmitFromGate") is not False:
            failures.append(f"captureGateMatrix.{gate_id}.canSubmitFromGate must be False")

    decision = packet.get("captureStartDecision")
    decision_text = json.dumps(decision, ensure_ascii=False)
    if not isinstance(decision, dict):
        failures.append("captureStartDecision must be an object")
    for marker in REQUIRED_REAL_DEVICE_PREFLIGHT_DECISION_MARKERS:
        if marker not in decision_text:
            failures.append(f"captureStartDecision missing {marker}")

    post_commands = packet.get("postPreflightCommands")
    post_command_text = json.dumps(post_commands, ensure_ascii=False)
    if not isinstance(post_commands, list):
        failures.append("postPreflightCommands must be an array")
    for command in REQUIRED_REAL_DEVICE_PREFLIGHT_POST_COMMANDS:
        if command not in post_command_text:
            failures.append(f"postPreflightCommands missing {command}")

    completion_text = json.dumps(
        [packet.get("completionRule"), packet.get("noSubmitBoundary")],
        ensure_ascii=False,
    )
    for marker in REQUIRED_REAL_DEVICE_PREFLIGHT_COMPLETION_MARKERS:
        if marker not in completion_text:
            failures.append(f"completion boundary missing {marker}")

    packet_text = json.dumps(packet, ensure_ascii=False)
    secret_hits = [pattern.pattern for pattern in FORBIDDEN_SECRET_PATTERNS if pattern.search(packet_text)]
    if secret_hits:
        failures.append("capturePreflight secret hits: " + ", ".join(secret_hits))
    return failures


def proof_failure_evidence(path: Path, data: dict[str, Any]) -> str:
    if not data:
        return f"invalid or missing {path}"
    failed = data.get("failedRequiredChecks")
    if isinstance(failed, list) and failed:
        return f"{path} failedRequiredChecks=" + ", ".join(str(item) for item in failed)
    return f"{path} passed={data.get('passed')}"


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
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    plan_path = root / args.plan
    review_account_path = root / args.review_account
    sim_launch_path = root / args.sim_launch_proof if args.sim_launch_proof else latest_sim_launch_proof(root)
    sim_launch_date = sim_launch_date_from(sim_launch_path)
    device_availability_path = root / args.device_availability_proof
    app_store_evidence_path = root / args.app_store_evidence_proof
    template_path = root / args.real_device_template
    execution_sheet_path = root / args.real_device_execution_sheet
    focused_capture_packet_path = root / args.focused_capture_packet
    real_device_capture_preflight_path = root / args.real_device_capture_preflight
    real_device_capture_result_template_path = root / args.real_device_capture_result_template
    text = read_text(plan_path)
    template = read_text(template_path)
    execution_sheet = read_text(execution_sheet_path)
    focused_capture_packet = read_json(focused_capture_packet_path)
    real_device_capture_preflight = read_json(real_device_capture_preflight_path)
    real_device_capture_result_template = read_json(real_device_capture_result_template_path)
    review_account = read_json(review_account_path)
    sim_launch = read_json(sim_launch_path)
    device_availability = read_json(device_availability_path)
    app_store_evidence = read_json(app_store_evidence_path)
    cases = extract_regression_cases(text)
    report = Report()

    report.add("regressionPlanPresent", bool(text), str(plan_path) if text else "missing regression plan")

    report.add(
        "realDeviceRegressionTemplatePresent",
        bool(template),
        str(template_path) if template else "missing real-device regression template",
    )
    report.add(
        "realDeviceExecutionSheetPresent",
        bool(execution_sheet),
        str(execution_sheet_path) if execution_sheet else "missing real-device execution sheet",
    )
    report.add(
        "focusedCapturePacketPresent",
        bool(focused_capture_packet),
        str(focused_capture_packet_path) if focused_capture_packet else "missing focused real-device capture packet",
    )
    report.add(
        "realDeviceCapturePreflightPresent",
        bool(real_device_capture_preflight),
        str(real_device_capture_preflight_path)
        if real_device_capture_preflight
        else "missing real-device capture preflight packet",
    )
    report.add(
        "realDeviceCaptureResultTemplatePresent",
        bool(real_device_capture_result_template),
        str(real_device_capture_result_template_path)
        if real_device_capture_result_template
        else "missing real-device capture result template",
    )
    template_missing = missing_markers(template, REQUIRED_TEMPLATE_MARKERS)
    report.add(
        "realDeviceRegressionTemplateStrict",
        not template_missing,
        "missing: " + ", ".join(template_missing)
        if template_missing
        else "real-device evidence template keeps iOS 26.5, exact TestFlight/signed-device install method, RD-01..RD-24, and review boundary requirements",
    )
    execution_sheet_failures = execution_sheet_alignment_failures(execution_sheet)
    report.add(
        "realDeviceExecutionSheetAlignedWithRegressionTemplate",
        bool(execution_sheet) and not execution_sheet_failures,
        "missing: " + ", ".join(execution_sheet_failures)
        if execution_sheet_failures
        else "real-device field execution sheet aligns RD-01..RD-24 names, evidence filenames, iOS 26.5 constraints, and external-evidence separation with the formal regression template",
    )
    shot_list_text = text + "\n" + template
    missing_capture_shot_list = missing_markers(shot_list_text, REQUIRED_CAPTURE_SHOT_LIST_MARKERS)
    report.add(
        "focusedEvidenceCaptureShotListPresent",
        bool(text) and bool(template) and not missing_capture_shot_list,
        "missing: " + ", ".join(missing_capture_shot_list)
        if missing_capture_shot_list
        else "focused capture shot list covers Dynamic Island manual deferral, lock screen, widgets, login, account deletion, and notification permission evidence",
    )
    missing_evidence_path_markers = [
        path
        for path in REQUIRED_REAL_DEVICE_EVIDENCE_PATHS.values()
        if path not in text or path not in template
    ]
    report.add(
        "realDeviceEvidenceFilenamePlanPresent",
        not missing_evidence_path_markers,
        "missing: " + ", ".join(missing_evidence_path_markers)
        if missing_evidence_path_markers
        else "real-device plan and template provide stable RealDevice/ evidence filenames for overview and RD-01..RD-24",
    )
    same_day_order_text = text + "\n" + template
    missing_same_day_order = missing_markers(same_day_order_text, REQUIRED_SAME_DAY_EXECUTION_ORDER_MARKERS)
    report.add(
        "sameDayRegressionExecutionOrderPresent",
        bool(text) and bool(template) and not missing_same_day_order,
        "missing: " + ", ".join(missing_same_day_order)
        if missing_same_day_order
        else "same-day TestFlight/regression execution order ties iOS 26.5 availability, archive/TestFlight, SMS/WeChat/OBS/provider proofs, production proof, and RD evidence paths together",
    )
    missing_evidence_index = evidence_index_failures(
        (
            ("plan", text),
            ("template", template),
            ("execution_sheet", execution_sheet),
        )
    )
    report.add(
        "realDeviceEvidenceIndexAndRedactionReviewPresent",
        bool(text) and bool(template) and bool(execution_sheet) and not missing_evidence_index,
        "missing: " + ", ".join(missing_evidence_index)
        if missing_evidence_index
        else "real-device plan, template, and execution sheet require an evidence index with file size, build source, independent proof, and redaction review",
    )
    missing_notification_permission_reset = [
        f"{source}: {marker}"
        for source, source_text in (
            ("plan", text),
            ("template", template),
            ("execution_sheet", execution_sheet),
        )
        for marker in REQUIRED_NOTIFICATION_PERMISSION_RESET_MARKERS
        if marker not in source_text
    ]
    report.add(
        "notificationPermissionResetLockPresent",
        bool(text) and bool(template) and bool(execution_sheet) and not missing_notification_permission_reset,
        "missing: " + ", ".join(missing_notification_permission_reset)
        if missing_notification_permission_reset
        else "notification permission allowed and denied paths require clean authorization state resets and independent same-build RD-17 evidence",
    )
    missing_build_identity_lock = [
        f"{source}: {marker}"
        for source, source_text in (
            ("plan", text),
            ("template", template),
            ("execution_sheet", execution_sheet),
        )
        for marker in REQUIRED_BUILD_IDENTITY_LOCK_MARKERS
        if marker not in source_text
    ]
    report.add(
        "realDeviceBuildIdentityLockPresent",
        bool(text) and bool(template) and bool(execution_sheet) and not missing_build_identity_lock,
        "missing: " + ", ".join(missing_build_identity_lock)
        if missing_build_identity_lock
        else "real-device plan, template, and execution sheet lock App version/build across archive, TestFlight, App Store Connect selected build, version settings, and regression evidence",
    )
    failure_triage_text = text + "\n" + template + "\n" + execution_sheet
    missing_failure_triage = missing_markers(failure_triage_text, REQUIRED_FAILURE_TRIAGE_MARKERS)
    report.add(
        "realDeviceFailureTriageTemplatePresent",
        bool(text) and bool(template) and bool(execution_sheet) and not missing_failure_triage,
        "missing: " + ", ".join(missing_failure_triage)
        if missing_failure_triage
        else "real-device plan, template, and execution sheet require failed RD triage, retest evidence, blocker logging, and no-submit boundaries",
    )
    focused_capture_packet_problems = focused_capture_packet_failures(focused_capture_packet)
    report.add(
        "focusedCapturePacketValid",
        bool(focused_capture_packet) and not focused_capture_packet_problems,
        "; ".join(focused_capture_packet_problems)
        if focused_capture_packet_problems
        else "structured focused capture packet locks RD-03/RD-10/RD-13/RD-14/RD-15/RD-17/RD-22/RD-23 target files, prerequisites, observations, redaction rules, evidence manifest fields, post-capture gates, and template-only evidence boundary",
    )
    real_device_capture_preflight_problems = real_device_capture_preflight_failures(
        real_device_capture_preflight
    )
    report.add(
        "realDeviceCapturePreflightValid",
        bool(real_device_capture_preflight) and not real_device_capture_preflight_problems,
        "; ".join(real_device_capture_preflight_problems)
        if real_device_capture_preflight_problems
        else "real-device capture preflight packet locks iOS 26.5 availability, same-build inputs, allowed install sources, notification reset, external login/storage preconditions, Dynamic Island/widget setup, redaction rules, post-preflight gates, and no-submit boundary before live capture starts",
    )
    capture_result_template_problems = real_device_capture_result_template_failures(
        real_device_capture_result_template
    )
    report.add(
        "realDeviceCaptureResultTemplateValid",
        bool(real_device_capture_result_template) and not capture_result_template_problems,
        "; ".join(capture_result_template_problems)
        if capture_result_template_problems
        else "real-device capture result template keeps live result status pending, iOS 26.5 only, TestFlight/signed-device install sources, same-build/no-submit/redaction boundaries, and RD login/account-delete/notification/Dynamic Island/widget result fields",
    )

    review_account_ok = (
        review_account.get("recoveryVerified") is True
        and review_account.get("syncSeeded") is True
        and review_account.get("containsSecret") is False
        and review_account.get("recoveryKeyStored") == ".env.xnp-review-account"
    )
    report.add(
        "reviewAccountRedactedProofPresent",
        review_account_ok,
        "redacted review account proof is verified and secret-free" if review_account_ok else f"invalid {review_account_path}",
    )

    report.add(
        "appReviewLoginInstructionsSafe",
        contains_all(text, ("恢复密钥登录", ".env.xnp-review-account", "不使用 debug code", "不使用未配置完成的微信登录替代恢复密钥审核路径")),
        "recovery-key review login path is documented and debug/unfinished WeChat substitutes are forbidden",
    )

    report.add(
        "realDeviceEnvironmentPlanPresent",
        contains_all(text, ("iOS 26.5", "TestFlight / Xcode 签名真机包", "Wi-Fi + 蜂窝网络", "中国大陆", "12-real-device-regression.md")),
        "real-device/TestFlight environment, network, region, and evidence path are present",
    )

    report.add(
        "ios265SmokeProofDateCurrent",
        sim_launch_date == args.expected_sim_launch_date,
        f"selected sim launch date {sim_launch_date or '<unknown>'}; expected {args.expected_sim_launch_date}; proof={sim_launch_path}",
    )

    sim_info = sim_launch.get("simulator", {}) if isinstance(sim_launch.get("simulator", {}), dict) else {}
    sim_app = sim_launch.get("app", {}) if isinstance(sim_launch.get("app", {}), dict) else {}
    sim_ok = (
        sim_launch.get("passed") is True
        and sim_info.get("runtime") == "iOS 26.5"
        and sim_app.get("dtPlatformVersion") == "26.5"
        and "com.mewpow.xiaonaiping:" in str(sim_launch.get("launchOutput", ""))
        and "不替代 TestFlight / 签名真机回归" in text
    )
    report.add(
        "ios265SmokeProofReferenced",
        sim_ok,
        "iOS 26.5 simulator launch proof is referenced and explicitly not treated as TestFlight evidence"
        if sim_ok
        else f"invalid or missing {sim_launch_path}",
    )
    launch_output = str(sim_launch.get("launchOutput", "")).strip()
    report.add(
        "ios265SmokeTextMatchesProof",
        bool(launch_output) and launch_output in text,
        f"launchOutput={launch_output or '<missing>'}",
    )

    device_availability_referenced = (
        device_availability.get("requiredIOS") == "26.5"
        and "Backend/proof/ios265-device-availability.json" in text
        and "当前本机真机可用性" in text
        and "不符合本项目 iOS 26.5 本机测试规则" in text
    )
    report.add(
        "ios265DeviceAvailabilityProofReferenced",
        device_availability_referenced,
        "iOS 26.5 physical-device availability proof is referenced and non-26.5 devices are excluded"
        if device_availability_referenced
        else f"invalid or missing {device_availability_path}",
    )
    device_availability_ok = device_availability.get("passed") is True
    report.add(
        "ios265PhysicalDeviceAvailable",
        device_availability_ok,
        "iOS 26.5 physical iPhone availability proof is green"
        if device_availability_ok
        else proof_failure_evidence(device_availability_path, device_availability),
    )

    missing_case_ids = sorted(REQUIRED_CASE_IDS - set(cases))
    report.add(
        "regressionCaseIdsComplete",
        not missing_case_ids,
        "missing: " + ", ".join(missing_case_ids) if missing_case_ids else "RD-01 through RD-24 are present",
    )

    missing_coverage = [
        name
        for name, markers in REQUIRED_COVERAGE_MARKERS.items()
        if not contains_all(text, markers)
    ]
    report.add(
        "regressionCoverageComplete",
        not missing_coverage,
        "missing coverage: " + ", ".join(missing_coverage) if missing_coverage else "all required real-device regression areas are covered",
    )

    rd13 = cases.get("RD-13", {}).get("line", "")
    rd14 = cases.get("RD-14", {}).get("line", "")
    report.add(
        "externalAuthCasesMarkedPending",
        "待真实短信配置" in rd13 and "待微信开放平台配置" in rd14,
        "SMS and WeChat cases are explicitly pending real providers",
    )

    report.add(
        "passCriteriaSeparateExternalAuthAndEvidence",
        contains_all(
            text,
            (
                "RD-01 到 RD-12、RD-15 到 RD-24 必须通过",
                "RD-13 和 RD-14 必须在真实短信和微信配置完成后通过",
                "不能用 debug code 代替",
                "每轮真机回归必须附截图或录屏证据",
            ),
        ),
        "pass criteria separates real-provider auth from core regression and requires evidence",
    )

    app_store_evidence_checks = app_store_evidence.get("checks", {})
    real_device_evidence = (
        app_store_evidence_checks.get("realDeviceRegression", {})
        if isinstance(app_store_evidence_checks, dict)
        else {}
    )
    real_device_evidence_ready = (
        isinstance(real_device_evidence, dict)
        and real_device_evidence.get("passed") is True
    )
    regression_pending_statement = contains_all(
        text,
        (
            "TestFlight 真机回归尚未完成",
            "不替代 TestFlight / 签名真机回归",
            "12-real-device-regression.md",
        ),
    )
    report.add(
        "realDeviceEvidenceGateSeparated",
        real_device_evidence_ready or regression_pending_statement,
        "real-device evidence is complete"
        if real_device_evidence_ready
        else "plan explicitly states TestFlight/signed-device regression is still incomplete and points to 12-real-device-regression.md"
        if regression_pending_statement
        else f"missing real-device evidence status from {plan_path} or {app_store_evidence_path}",
    )

    report.add(
        "reviewBoundaryCasesPresent",
        contains_all(
            text,
            (
                "HealthKit",
                "传感器",
                "状态展示",
                "健康建议",
                "压力评估",
                "压力提醒",
                "心理健康判断",
                "医疗诊断",
                "喂养建议",
                "不展示照片原图",
                "token",
                "云端对象 key",
            ),
        ),
        "Live Activity/widget/review boundary terms are present",
    )

    secret_hits = [pattern.pattern for pattern in FORBIDDEN_SECRET_PATTERNS if pattern.search(text)]
    report.add(
        "regressionPlanDoesNotExposeSecrets",
        not secret_hits,
        "found secret-like markers: " + ", ".join(secret_hits) if secret_hits else "no recovery key assignments, tokens, debug codes, or API-key markers found",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--plan", default="Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md")
    parser.add_argument("--review-account", default="Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json")
    parser.add_argument("--sim-launch-proof")
    parser.add_argument("--expected-sim-launch-date", default=DEFAULT_EXPECTED_SIM_LAUNCH_DATE)
    parser.add_argument("--device-availability-proof", default="Backend/proof/ios265-device-availability.json")
    parser.add_argument("--app-store-evidence-proof", default=APP_STORE_EVIDENCE_CURRENT_PROOF)
    parser.add_argument("--real-device-template", default="Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md")
    parser.add_argument("--real-device-execution-sheet", default=str(REAL_DEVICE_EXECUTION_SHEET))
    parser.add_argument("--focused-capture-packet", default=str(FOCUSED_CAPTURE_PACKET))
    parser.add_argument(
        "--real-device-capture-preflight",
        default=str(REAL_DEVICE_CAPTURE_PREFLIGHT_PACKET),
    )
    parser.add_argument(
        "--real-device-capture-result-template",
        default=str(REAL_DEVICE_CAPTURE_RESULT_TEMPLATE),
    )
    parser.add_argument("--output", default="Backend/proof/testflight-regression-plan.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"TestFlight regression plan passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"TestFlight regression plan incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
