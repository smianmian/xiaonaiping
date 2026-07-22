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
        ("RD-03", "记录喂养", "首页今日摘要和最近记录更新；已有固定喝奶间隔时，顺延滚轮提供不顺延、+5、+10、+15、+20、+25、+30 分钟，保存后下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算", "待测"),
        ("RD-04", "记录睡眠", "睡眠记录可保存、可回看", "待测"),
        ("RD-05", "记录排便", "排便记录可保存、可回看", "待测"),
        ("RD-06", "成长记录", "身高体重可保存，成长页可见", "待测"),
        ("RD-07", "疫苗模板切换", "中国大陆 / 香港模板可切换；文案不构成医疗建议", "待测"),
        ("RD-08", "相册权限拒绝", "拒绝权限后 App 不崩溃", "待测"),
        ("RD-09", "相册权限允许", "可主动加入照片；不自动扫描系统相册", "待测"),
        ("RD-10", "恢复密钥账号登录", "可用测试恢复密钥连接账号", "待测"),
        ("RD-11", "云同步", "同步成功", "待测"),
        ("RD-12", "云恢复", "清空/换装后可恢复测试数据", "待测"),
        ("RD-13", "手机号登录", "真实验证码可发送、可校验、频控正常", "待真实短信配置"),
        ("RD-14", "微信登录", "可拉起微信授权并回到 App", "待微信开放平台配置"),
        ("RD-15", "删除云端账号与同步", "云端同步、照片对象、账号失效", "待测"),
        ("RD-16", "断网保存", "本地记录可保存；云操作给出失败状态", "待测"),
        ("RD-17", "通知权限", "允许后可创建下一次喝奶提醒；拒绝后有可理解状态和系统设置入口；关闭提醒会移除 pending notification", "待测"),
        ("RD-18", "Apple Watch 镜像通知", "iPhone 本地通知可按系统设置镜像到 Apple Watch", "待测"),
        ("RD-19", "隐私政策/用户协议/支持 URL", "App Store Connect URL 可打开，无 404", "待测"),
        ("RD-20", "崩溃/日志脱敏", "不输出宝宝内容、照片对象 key、手机号明文", "待测"),
        ("RD-21", "Release 包体自检", "ios-app-bundle.json 不含内部文档、本地地址、debug 文案或 API key 标记", "当前通过；微信配置仍阻断"),
        ("RD-22", "灵动岛喝奶提醒开关", "开关打开后仅在保存喝奶闹钟时展示下一次喝奶时间、固定间隔和手动顺延后的提醒时间；顺延只改变下一次提醒时间、不新增持久化字段；关闭后结束 Live Activity", "待测"),
        ("RD-23", "锁屏/桌面小组件", "锁屏通知栈不遮挡；锁屏小组件和桌面小组件只读展示本机今日摘要，不展示照片原图、备注、token 或云端对象 key", "待测"),
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
            "| RD-11 云同步 | `RealDevice/RD-11-cloud-sync.png` |",
            "| RD-12 云恢复 | `RealDevice/RD-12-cloud-restore.png` |",
            "| RD-13 手机号登录 | `RealDevice/RD-13-phone-login.png` |",
            "| RD-14 微信登录 | `RealDevice/RD-14-wechat-login.png` |",
            "| RD-15 删除云端账号与同步 | `RealDevice/RD-15-account-delete.png` |",
            "| RD-16 断网保存 | `RealDevice/RD-16-offline-save.png` |",
            "| RD-17 通知权限允许 | `RealDevice/RD-17-notification-allowed.png` |",
            "| RD-17 通知权限拒绝 | `RealDevice/RD-17-notification-denied.png` |",
            "| RD-18 Apple Watch 镜像通知 | `RealDevice/RD-18-watch-mirror.png` |",
            "| RD-19 隐私政策/用户协议/支持 URL | `RealDevice/RD-19-public-urls.png` |",
            "| RD-20 崩溃/日志脱敏 | `RealDevice/RD-20-diagnostics-redaction.png` |",
            "| RD-21 Release 包体自检 | `RealDevice/RD-21-release-bundle.png` |",
            "| RD-22 灵动岛紧凑态 | `RealDevice/RD-22-dynamic-island-compact.png` |",
            "| RD-22 灵动岛展开态 | `RealDevice/RD-22-dynamic-island-expanded.png` |",
            "| RD-23 锁屏通知栈 | `RealDevice/RD-23-lock-screen-notification-stack.png` |",
            "| RD-23 锁屏小组件 | `RealDevice/RD-23-lock-screen-widget-summary.png` |",
            "| RD-23 桌面小组件 | `RealDevice/RD-23-home-widget-summary.png` |",
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

1. 登录路径：打开 App -> 设置 -> 账号与同步 -> 恢复密钥登录。
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

## 同一 build 身份锁

`12-real-device-regression.md` 里的 App 版本和 Build 号必须同时对齐 `05-signed-archive.png`、`06-testflight.png`、`AppStoreConnect/ASC-07-build-testflight-link.png` 和 `APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md`。版本号和 build 号必须一致，证据只能来自同一 TestFlight build 或 Xcode 签名真机包，不能混用不同 build。

如果任一截图、表格或 App Store Connect 选中 build 对不上，先重新归档、上传或重跑真机回归；随后复跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_testflight_regression_plan.py` 和 `check_app_store_evidence.py --allow-incomplete`，再更新本表。

### 当前本机真机可用性

| 设备 | 系统 | 状态 | 本轮处理 |
|---|---|---|---|
| 蓝蓝 / iPhone 16 Pro Max | iOS 26.5 | unavailable | 符合版本但当前不可用，未测试 |
| 面面 / iPhone 16 Plus | iOS 27.0 | available (paired) | 不符合本项目 iOS 26.5 本机测试规则，未测试 |

机器证据：`Backend/proof/ios265-device-availability.json`。

## 上线当天执行顺序

同一天同一轮执行时，先完成外部和包体前置证明，再跑真机回归；不能先跑真机回归再补服务商证据。

1. 确认 `ios265-device-availability.json` 证明可用 physical iPhone 为 iOS 26.5。
2. 归档 `05-signed-archive.png` 和 `06-testflight.png`。
3. 完成 `verify_auth_providers.py --send-test-sms --require-sms-live-send`，并归档 `07-sms-provider.png`。
4. 归档 `08-wechat-open-platform.png` 和 `09-obs-policy.png`。
5. 复跑 `check_production_readiness.py`，确认 production proof 变绿或把红项写入阻断清单。
6. 使用同一 TestFlight build 或 Xcode 签名真机包填写 `12-real-device-regression.md`。
7. 先跑 `RD-11-cloud-sync.png`、`RD-12-cloud-restore.png`、`RD-13-phone-login.png`、`RD-14-wechat-login.png`、`RD-15-account-delete.png`。
8. 再跑 `RD-22-dynamic-island-compact.png`、`RD-22-dynamic-island-expanded.png`、`RD-23-lock-screen-notification-stack.png`、`RD-23-lock-screen-widget-summary.png`、`RD-23-home-widget-summary.png`。

## 本机 iOS 26.5 烟测证据

| 启动 | 通过，输出 `com.mewpow.xiaonaiping: 15975` |
| 注意 | 该证据只证明本机 iOS 26.5 安装启动，不替代 TestFlight / 签名真机回归 |

## 必测用例

| 编号 | 用例 | 期望 | 结果 |
|---|---|---|---|
{table}

## 重点采集清单

以下证据必须来自 iOS 26.5 TestFlight 或 Xcode 签名真机包；模拟器、iOS 27、模板截图、空白图或口头结论不能替代。

| 场景 | 必拍内容 | 建议证据 |
|---|---|---|
| 灵动岛紧凑态 | 头像/进度环完整；每项必须使用独立证据文件 | `RealDevice/RD-22-dynamic-island-compact.png` |
| 灵动岛展开态 | 下一次喝奶时间和固定间隔可读；顺延选项来自不顺延、+5、+10、+15、+20、+25、+30 分钟；每项必须使用独立证据文件 | `RealDevice/RD-22-dynamic-island-expanded.png` |
| 锁屏通知栈 | 不遮挡提醒卡片；每项必须使用独立证据文件 | `RealDevice/RD-23-lock-screen-notification-stack.png` |
| 锁屏小组件 | accessoryCircular / accessoryRectangular / accessoryInline 锁屏小组件可读；每项必须使用独立证据文件 | `RealDevice/RD-23-lock-screen-widget-summary.png` |
| 桌面小组件 | 只读展示本机今日摘要；每项必须使用独立证据文件 | `RealDevice/RD-23-home-widget-summary.png` |
| 恢复密钥登录 | 不展示密钥全文 | `RealDevice/RD-10-recovery-login.png` |
| 手机号登录 | 遮挡完整手机号和验证码 | `RealDevice/RD-13-phone-login.png` |
| 微信登录 | 不使用 debug code | `RealDevice/RD-14-wechat-login.png` |
| 账号删除 | 账号失效和云端删除 | `RealDevice/RD-15-account-delete.png` |
| 通知权限允许 | 可创建下一次喝奶提醒；每项必须使用独立证据文件 | `RealDevice/RD-17-notification-allowed.png` |
| 通知权限拒绝 | 有系统设置入口；每项必须使用独立证据文件 | `RealDevice/RD-17-notification-denied.png` |

## 通知权限双路径重置锁

RD-17 必须分别验证允许和拒绝两条路径。由于 iOS 通知授权状态会保留，拍 `RD-17-notification-allowed.png` 和 `RD-17-notification-denied.png` 前，必须先把 App 回到干净通知授权状态：删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包，或在系统设置中重置小奶瓶通知授权并确认首次弹窗会重新出现。不能在已经允许通知的安装状态下拍拒绝路径，也不能在已经拒绝通知的安装状态下拍允许路径。

| RD-17 路径 | 前置状态 | 必须观察 | 证据 |
|---|---|---|---|
| 通知权限允许 | 干净通知授权状态，首次弹窗可见 | 点击允许后可创建下一次喝奶提醒，并能看到 pending reminder 生效 | `RealDevice/RD-17-notification-allowed.png` |
| 通知权限拒绝 | 重新回到干净通知授权状态，首次弹窗可见 | 点击拒绝后有可理解状态和系统设置入口，不崩溃，不继续假装已创建提醒 | `RealDevice/RD-17-notification-denied.png` |

两张证据必须来自同一 App 版本 / Build 的独立安装或独立重置回合；不能复用同一次授权状态、不能复用同一张截图、不能用系统设置页单独替代 App 内状态。

## 证据索引与脱敏复核

所有截图/录屏必须来自同一 TestFlight build 或 Xcode 签名真机包，文件大小不低于 10KB，并逐项确认是独立证据、已脱敏。

| 证据 | 来源 build | 文件大小 | 独立证据 | 脱敏复核 |
|---|---|---|---|---|
| `RealDevice/00-overview.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片已遮挡或未出现 |
| `RealDevice/RD-10-recovery-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥全文、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-13-phone-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 完整手机号和验证码已遮挡，不展示 token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-14-wechat-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示 AppSecret、debug code、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-15-account-delete.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-17-notification-allowed.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-17-notification-denied.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-22-dynamic-island-compact.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-22-dynamic-island-expanded.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-lock-screen-notification-stack.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-lock-screen-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-home-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |

## 失败复测与阻断清单

任一 RD 失败时，不要覆盖失败证据；先保留失败截图或录屏，再用同一 iOS 26.5 TestFlight build 或 Xcode 签名真机包复测。失败仍存在时，不得提交 App Store Connect 审核，并把阻断写入 `RELEASE_CHECKLIST.md`、`LAUNCH_GATE_RERUN_20260626.md`、`production-readiness.json` 和 `launch-objective-audit.json` 的当前结论。

| 失败 RD | 失败现象 | 失败证据 | 复测证据 | 复测结果 | 阻断结论 |
|---|---|---|---|---|---|
| RD-13 手机号登录 | 真实短信服务商验证码未收到、校验失败或完整手机号/验证码入镜 | RealDevice/RD-13-phone-login-fail.png | RealDevice/RD-13-phone-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-14 微信登录 | 微信开放平台授权未拉起、未回到 App、AppSecret / debug code 入镜 | RealDevice/RD-14-wechat-login-fail.png | RealDevice/RD-14-wechat-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-17 通知权限 | 允许或拒绝路径不可理解，或拒绝后仍假装已创建提醒 | RealDevice/RD-17-notification-fail.png | RealDevice/RD-17-notification-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-22 灵动岛 | 紧凑态裁剪、压到岛中心，或展开态提醒时间/固定间隔/顺延结果不可读 | RealDevice/RD-22-dynamic-island-fail.png | RealDevice/RD-22-dynamic-island-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-23 锁屏/小组件 | 锁屏通知栈遮挡，或锁屏/桌面小组件裁剪、展示隐私照片、备注、token、对象存储 key | RealDevice/RD-23-widget-fail.png | RealDevice/RD-23-widget-retest.png | 待填 | 未通过前不得提交 App Store Connect |

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

## 同一 build 身份锁

本文件的 App 版本和 Build 号必须同时对齐 `05-signed-archive.png`、`06-testflight.png`、`AppStoreConnect/ASC-07-build-testflight-link.png` 和 `APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md`。版本号和 build 号必须一致，证据只能来自同一 TestFlight build 或 Xcode 签名真机包，不能混用不同 build。

如果任一截图、表格或 App Store Connect 选中 build 对不上，先重新归档、上传或重跑真机回归；随后复跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_testflight_regression_plan.py` 和 `check_app_store_evidence.py --allow-incomplete`，再更新 `12-real-device-regression.md`。

## 上线当天执行顺序

同一天同一轮执行时，先完成外部和包体前置证明，再跑真机回归；不能先跑真机回归再补服务商证据。

1. 确认 `ios265-device-availability.json` 证明可用 physical iPhone 为 iOS 26.5。
2. 归档 `05-signed-archive.png` 和 `06-testflight.png`。
3. 完成 `verify_auth_providers.py --send-test-sms --require-sms-live-send`，并归档 `07-sms-provider.png`。
4. 归档 `08-wechat-open-platform.png` 和 `09-obs-policy.png`。
5. 复跑 `check_production_readiness.py`，确认 production proof 变绿或把红项写入阻断清单。
6. 使用同一 TestFlight build 或 Xcode 签名真机包填写 `12-real-device-regression.md`。
7. 先跑 `RD-11-cloud-sync.png`、`RD-12-cloud-restore.png`、`RD-13-phone-login.png`、`RD-14-wechat-login.png`、`RD-15-account-delete.png`。
8. 再跑 `RD-22-dynamic-island-compact.png`、`RD-22-dynamic-island-expanded.png`、`RD-23-lock-screen-notification-stack.png`、`RD-23-lock-screen-widget-summary.png`、`RD-23-home-widget-summary.png`。

## 必填勾选

- [ ] iOS 26.5
- [ ] 微信登录
- [ ] 账号删除
- [ ] 通知权限
- [ ] 通知权限允许后可创建下一次喝奶提醒
- [ ] 通知权限拒绝后有可理解状态和系统设置入口
- [ ] 通知权限允许独立截图
- [ ] 通知权限拒绝独立截图
- [ ] 灵动岛喝奶提醒开关
- [ ] 灵动岛紧凑态独立截图
- [ ] 灵动岛展开态独立截图
- [ ] 灵动岛展开态展示手动顺延后的提醒时间
- [ ] 喂养顺延滚轮只提供不顺延和 +5、+10、+15、+20、+25、+30 分钟
- [ ] 下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算
- [ ] 锁屏通知栈上下相邻通知不遮挡提醒卡片
- [ ] 锁屏/桌面小组件
- [ ] 锁屏通知栈独立截图
- [ ] 锁屏小组件独立截图
- [ ] 桌面小组件独立截图
- [ ] 锁屏小组件内容不裁剪不展示隐私照片
- [ ] 桌面小组件内容不裁剪不展示隐私照片
- [ ] 审核边界文案

## 重点采集清单

> 每项必须填写实际观察结论和证据文件。证据必须来自 iOS 26.5 TestFlight 或 Xcode 签名真机包；模拟器、iOS 27、模板截图、空白图或口头结论不能替代。每项必须使用独立证据文件。

| 场景 | 实际观察结论 | 证据 |
|---|---|---|
| 灵动岛紧凑态 |  | RealDevice/RD-22-dynamic-island-compact.png |
| 灵动岛展开态 | 必须确认下一次喝奶时间、固定间隔、手动顺延后的提醒时间都可读；顺延选项来自不顺延、+5、+10、+15、+20、+25、+30 分钟；文案不构成喂养建议 | RealDevice/RD-22-dynamic-island-expanded.png |
| 锁屏通知栈 |  | RealDevice/RD-23-lock-screen-notification-stack.png |
| 锁屏小组件 | 必须确认 accessoryCircular / accessoryRectangular / accessoryInline 至少一种锁屏小组件可读、无裁剪、不展示隐私照片、备注、token 或对象存储 key | RealDevice/RD-23-lock-screen-widget-summary.png |
| 桌面小组件 |  | RealDevice/RD-23-home-widget-summary.png |
| 恢复密钥登录 |  | RealDevice/RD-10-recovery-login.png |
| 手机号登录 |  | RealDevice/RD-13-phone-login.png |
| 微信登录 |  | RealDevice/RD-14-wechat-login.png |
| 账号删除 |  | RealDevice/RD-15-account-delete.png |
| 通知权限允许 |  | RealDevice/RD-17-notification-allowed.png |
| 通知权限拒绝 |  | RealDevice/RD-17-notification-denied.png |

## 通知权限双路径重置锁

RD-17 必须分别验证允许和拒绝两条路径。由于 iOS 通知授权状态会保留，拍 `RD-17-notification-allowed.png` 和 `RD-17-notification-denied.png` 前，必须先把 App 回到干净通知授权状态：删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包，或在系统设置中重置小奶瓶通知授权并确认首次弹窗会重新出现。不能在已经允许通知的安装状态下拍拒绝路径，也不能在已经拒绝通知的安装状态下拍允许路径。

| RD-17 路径 | 前置状态 | 必须观察 | 证据 |
|---|---|---|---|
| 通知权限允许 | 干净通知授权状态，首次弹窗可见 | 点击允许后可创建下一次喝奶提醒，并能看到 pending reminder 生效 | `RealDevice/RD-17-notification-allowed.png` |
| 通知权限拒绝 | 重新回到干净通知授权状态，首次弹窗可见 | 点击拒绝后有可理解状态和系统设置入口，不崩溃，不继续假装已创建提醒 | `RealDevice/RD-17-notification-denied.png` |

两张证据必须来自同一 App 版本 / Build 的独立安装或独立重置回合；不能复用同一次授权状态、不能复用同一张截图、不能用系统设置页单独替代 App 内状态。

## 证据索引与脱敏复核

每个核心证据文件都要填来源 build、文件大小、是否独立证据和脱敏复核。所有截图/录屏必须来自同一 TestFlight build 或 Xcode 签名真机包；文件大小不低于 10KB；不得复用总览图替代独立截图。

| 证据 | 来源 build | 文件大小 | 独立证据 | 脱敏复核 |
|---|---|---|---|---|
| `RealDevice/00-overview.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片已遮挡或未出现 |
| `RealDevice/RD-10-recovery-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥全文、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-13-phone-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 完整手机号和验证码已遮挡，不展示 token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-14-wechat-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示 AppSecret、debug code、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-15-account-delete.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-17-notification-allowed.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-17-notification-denied.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-22-dynamic-island-compact.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-22-dynamic-island-expanded.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-lock-screen-notification-stack.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-lock-screen-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-home-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |

## 失败复测与阻断清单

任一 RD 失败时，不要覆盖失败证据；先保留失败截图或录屏，再用同一 iOS 26.5 TestFlight build 或 Xcode 签名真机包复测。失败仍存在时，不得提交 App Store Connect 审核，并把阻断写入 `RELEASE_CHECKLIST.md`、`LAUNCH_GATE_RERUN_20260626.md`、`production-readiness.json` 和 `launch-objective-audit.json` 的当前结论。

| 失败 RD | 失败现象 | 失败证据 | 复测证据 | 复测结果 | 阻断结论 |
|---|---|---|---|---|---|
| RD-13 手机号登录 | 真实短信服务商验证码未收到、校验失败或完整手机号/验证码入镜 | RealDevice/RD-13-phone-login-fail.png | RealDevice/RD-13-phone-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-14 微信登录 | 微信开放平台授权未拉起、未回到 App、AppSecret / debug code 入镜 | RealDevice/RD-14-wechat-login-fail.png | RealDevice/RD-14-wechat-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-17 通知权限 | 允许或拒绝路径不可理解，或拒绝后仍假装已创建提醒 | RealDevice/RD-17-notification-fail.png | RealDevice/RD-17-notification-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-22 灵动岛 | 紧凑态裁剪、压到岛中心，或展开态提醒时间/固定间隔/顺延结果不可读 | RealDevice/RD-22-dynamic-island-fail.png | RealDevice/RD-22-dynamic-island-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-23 锁屏/小组件 | 锁屏通知栈遮挡，或锁屏/桌面小组件裁剪、展示隐私照片、备注、token、对象存储 key | RealDevice/RD-23-widget-fail.png | RealDevice/RD-23-widget-retest.png | 待填 | 未通过前不得提交 App Store Connect |

## RD-01 到 RD-24 结果

> 最终提交前每一行都必须改成“通过”，并填写截图或录屏证据路径。安装方式只能填写 `TestFlight` 或 `Xcode 签名真机包` 其中一个，不要保留斜杠选项。

| 编号 | 结果 | 证据/备注 |
|---|---|---|
| RD-01 冷启动进入首页 | 待测 | RealDevice/RD-01-cold-start.png |
| RD-02 创建宝宝档案 | 待测 | RealDevice/RD-02-baby-profile.png |
| RD-03 记录喂养 | 待测 | RealDevice/RD-03-feeding-record.png；需验证已有固定喝奶间隔时，顺延滚轮只提供不顺延、+5、+10、+15、+20、+25、+30 分钟 |
| RD-04 记录睡眠 | 待测 | RealDevice/RD-04-sleep-record.png |
| RD-05 记录排便 | 待测 | RealDevice/RD-05-diaper-record.png |
| RD-06 成长记录 | 待测 | RealDevice/RD-06-growth-record.png |
| RD-07 疫苗模板切换 | 待测 | RealDevice/RD-07-vaccine-template.png |
| RD-08 相册权限拒绝 | 待测 | RealDevice/RD-08-photo-denied.png |
| RD-09 相册权限允许 | 待测 | RealDevice/RD-09-photo-allowed.png |
| RD-10 恢复密钥账号登录 | 待测 | RealDevice/RD-10-recovery-login.png |
| RD-11 云同步 | 待测 | RealDevice/RD-11-cloud-sync.png |
| RD-12 云恢复 | 待测 | RealDevice/RD-12-cloud-restore.png |
| RD-13 手机号登录 | 待真实短信配置 | RealDevice/RD-13-phone-login.png |
| RD-14 微信登录 | 待微信开放平台配置 | RealDevice/RD-14-wechat-login.png |
| RD-15 删除云端账号与同步 | 待测 | RealDevice/RD-15-account-delete.png |
| RD-16 断网保存 | 待测 | RealDevice/RD-16-offline-save.png |
| RD-17 通知权限 | 待测 | RealDevice/RD-17-notification-allowed.png；RealDevice/RD-17-notification-denied.png |
| RD-18 Apple Watch 镜像通知 | 待测 | RealDevice/RD-18-watch-mirror.png |
| RD-19 隐私政策/用户协议/支持 URL | 待测 | RealDevice/RD-19-public-urls.png |
| RD-20 崩溃/日志脱敏 | 待测 | RealDevice/RD-20-diagnostics-redaction.png |
| RD-21 Release 包体自检 | 待测 | RealDevice/RD-21-release-bundle.png |
| RD-22 灵动岛喝奶提醒开关 | 待测 | RealDevice/RD-22-dynamic-island-compact.png；RealDevice/RD-22-dynamic-island-expanded.png |
| RD-23 锁屏/桌面小组件 | 待测 | RealDevice/RD-23-lock-screen-notification-stack.png；RealDevice/RD-23-lock-screen-widget-summary.png；RealDevice/RD-23-home-widget-summary.png |
| RD-24 审核边界文案 | 待测 | RealDevice/RD-24-review-boundary.png |

## 审核边界确认

- [ ] Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔。
- [ ] 手动顺延只改变下一次提醒时间，不新增持久化字段，不根据奶量、月龄、传感器或健康数据自动推算。
- [ ] 下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。
- [ ] 小组件只读展示本机今日摘要。
- [ ] 状态展示只反映用户主动记录的数据。
- [ ] 不生成健康建议、压力提醒、喂养建议或医疗判断。
- [ ] 不接入 HealthKit。
- [ ] 不提供压力评估。
""".lstrip()


def complete_execution_sheet() -> str:
    return """
# 小奶瓶真机证据现场执行单

日期：2026-06-30

状态：现场拍摄和填表用，不是已完成证据。正式提交仍以 `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md`、`Backend/proof/testflight-regression-plan.json` 和 `Backend/proof/app-store-evidence-20260630T-current.json` 为准。

## 0. 硬门槛

- 只接受 iOS 26.5。
- 构建来源只能是 `TestFlight` 或 `Xcode 签名真机包`。
- RD 编号、用例名称和目标文件必须与 `Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`、`Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md` 保持一致。
- 每个证据文件不低于 10KB。
- 不能写桌面、下载目录、微信临时目录或绝对路径。
- 不保存恢复密钥、token、对象 key、真实宝宝照片或未授权家庭资料。

## 1. 开始前

| 项 | 填写 |
| --- | --- |
| 设备 |  |
| iOS | 26.5 |
| 安装方式 | TestFlight / Xcode 签名真机包 |
| App 版本 / Build 号 |  |
| 网络 | Wi-Fi / 蜂窝网络 |
| 测试时间 |  |
| 前置 build 证据 | `05-signed-archive.png`、`06-testflight.png` |

## 同一 build 身份锁

现场填写的 App 版本和 Build 号必须同时对齐 `05-signed-archive.png`、`06-testflight.png`、`AppStoreConnect/ASC-07-build-testflight-link.png`、`APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md` 和 `12-real-device-regression.md`。版本号和 build 号必须一致，证据只能来自同一 TestFlight build 或 Xcode 签名真机包，不能混用不同 build。

如果任一截图、表格或 App Store Connect 选中 build 对不上，先重新归档、上传或重跑真机回归；随后复跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_testflight_regression_plan.py` 和 `check_app_store_evidence.py --allow-incomplete`，再把结果填回正式文件。

## 2. 核心 App 流程

| RD | 目标文件 | 通过结论 |
| --- | --- | --- |
| RD-01 冷启动进入首页 | `RealDevice/RD-01-cold-start.png` | 首页首屏可见 |
| RD-02 创建宝宝档案 | `RealDevice/RD-02-baby-profile.png` | 使用虚构宝宝资料 |
| RD-03 记录喂养 | `RealDevice/RD-03-feeding-record.png` | 顺延滚轮只提供不顺延、+5、+10、+15、+20、+25、+30 分钟 |
| RD-04 记录睡眠 | `RealDevice/RD-04-sleep-record.png` | 睡眠记录可添加 |
| RD-05 记录排便 | `RealDevice/RD-05-diaper-record.png` | 尿布记录可添加 |
| RD-06 成长记录 | `RealDevice/RD-06-growth-record.png` | 身高体重记录可保存 |
| RD-07 疫苗模板切换 | `RealDevice/RD-07-vaccine-template.png` | 不构成医疗建议 |
| RD-08 相册权限拒绝 | `RealDevice/RD-08-photo-denied.png` | 拒绝后不崩溃 |
| RD-09 相册权限允许 | `RealDevice/RD-09-photo-allowed.png` | 不自动扫描系统相册 |
| RD-10 恢复密钥账号登录 | `RealDevice/RD-10-recovery-login.png` | 恢复密钥不入镜 |
| RD-11 云同步 | `RealDevice/RD-11-cloud-sync.png` | 不展示对象 key |
| RD-12 云恢复 | `RealDevice/RD-12-cloud-restore.png` | token 脱敏 |
| RD-13 手机号登录 | `RealDevice/RD-13-phone-login.png` | 完整手机号和验证码脱敏 |
| RD-14 微信登录 | `RealDevice/RD-14-wechat-login.png` | 不使用 debug code |
| RD-15 删除云端账号与同步 | `RealDevice/RD-15-account-delete.png` | 旧 token 失效 |
| RD-16 断网保存 | `RealDevice/RD-16-offline-save.png` | 本地记录可保存 |

## 3. 通知、公开 URL 和审核边界

| RD | 目标文件 | 通过结论 |
| --- | --- | --- |
| RD-17 通知权限 | `RealDevice/RD-17-notification-allowed.png`、`RealDevice/RD-17-notification-denied.png` | 允许和拒绝都独立截图 |
| RD-18 Apple Watch 镜像通知 | `RealDevice/RD-18-watch-mirror.png` | 不承诺独立 Watch App |
| RD-19 隐私政策/用户协议/支持 URL | `RealDevice/RD-19-public-urls.png` | 无 404 |
| RD-20 崩溃/日志脱敏 | `RealDevice/RD-20-diagnostics-redaction.png` | 不输出宝宝内容 |
| RD-21 Release 包体自检 | `RealDevice/RD-21-release-bundle.png` | ios-app-bundle.json 结果可见 |
| RD-22 灵动岛喝奶提醒开关 | `RealDevice/RD-22-dynamic-island-compact.png`、`RealDevice/RD-22-dynamic-island-expanded.png` | 紧凑态和展开态独立截图 |
| RD-23 锁屏/桌面小组件 | `RealDevice/RD-23-lock-screen-notification-stack.png`、`RealDevice/RD-23-lock-screen-widget-summary.png`、`RealDevice/RD-23-home-widget-summary.png` | 锁屏通知栈、锁屏小组件和桌面小组件独立截图 |
| RD-24 审核边界文案 | `RealDevice/RD-24-review-boundary.png` | 不暗示 HealthKit、传感器、健康建议、压力评估、心理健康判断、医疗诊断或喂养建议 |

## 通知权限双路径重置锁

RD-17 必须分别验证允许和拒绝两条路径。由于 iOS 通知授权状态会保留，拍 `RD-17-notification-allowed.png` 和 `RD-17-notification-denied.png` 前，必须先把 App 回到干净通知授权状态：删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包，或在系统设置中重置小奶瓶通知授权并确认首次弹窗会重新出现。不能在已经允许通知的安装状态下拍拒绝路径，也不能在已经拒绝通知的安装状态下拍允许路径。

| RD-17 路径 | 前置状态 | 必须观察 | 证据 |
|---|---|---|---|
| 通知权限允许 | 干净通知授权状态，首次弹窗可见 | 点击允许后可创建下一次喝奶提醒，并能看到 pending reminder 生效 | `RealDevice/RD-17-notification-allowed.png` |
| 通知权限拒绝 | 重新回到干净通知授权状态，首次弹窗可见 | 点击拒绝后有可理解状态和系统设置入口，不崩溃，不继续假装已创建提醒 | `RealDevice/RD-17-notification-denied.png` |

两张证据必须来自同一 App 版本 / Build 的独立安装或独立重置回合；不能复用同一次授权状态、不能复用同一张截图、不能用系统设置页单独替代 App 内状态。

## 证据索引与脱敏复核

拍完后先填这个表，再填回 `12-real-device-regression.md`。所有截图/录屏必须来自同一 TestFlight build 或 Xcode 签名真机包，文件大小不低于 10KB，并逐项确认是独立证据、已脱敏。

| 证据 | 来源 build | 文件大小 | 独立证据 | 脱敏复核 |
| --- | --- | --- | --- | --- |
| `RealDevice/00-overview.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片已遮挡或未出现 |
| `RealDevice/RD-10-recovery-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥全文、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-13-phone-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 完整手机号和验证码已遮挡，不展示 token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-14-wechat-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示 AppSecret、debug code、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-15-account-delete.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-17-notification-allowed.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-17-notification-denied.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-22-dynamic-island-compact.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-22-dynamic-island-expanded.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-lock-screen-notification-stack.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-lock-screen-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-home-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |

## 5. 失败复测与阻断清单

任一 RD 失败时，不要覆盖失败证据；先保留失败截图或录屏，再用同一 iOS 26.5 TestFlight build 或 Xcode 签名真机包复测。失败仍存在时，不得提交 App Store Connect 审核，并把阻断写入 `RELEASE_CHECKLIST.md`、`LAUNCH_GATE_RERUN_20260626.md`、`production-readiness.json` 和 `launch-objective-audit.json` 的当前结论。

| 失败 RD | 失败现象 | 失败证据 | 复测证据 | 复测结果 | 阻断结论 |
|---|---|---|---|---|---|
| RD-13 手机号登录 | 真实短信服务商验证码未收到、校验失败或完整手机号/验证码入镜 | RealDevice/RD-13-phone-login-fail.png | RealDevice/RD-13-phone-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-14 微信登录 | 微信开放平台授权未拉起、未回到 App、AppSecret / debug code 入镜 | RealDevice/RD-14-wechat-login-fail.png | RealDevice/RD-14-wechat-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-17 通知权限 | 允许或拒绝路径不可理解，或拒绝后仍假装已创建提醒 | RealDevice/RD-17-notification-fail.png | RealDevice/RD-17-notification-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-22 灵动岛 | 紧凑态裁剪、压到岛中心，或展开态提醒时间/固定间隔/顺延结果不可读 | RealDevice/RD-22-dynamic-island-fail.png | RealDevice/RD-22-dynamic-island-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-23 锁屏/小组件 | 锁屏通知栈遮挡，或锁屏/桌面小组件裁剪、展示隐私照片、备注、token、对象存储 key | RealDevice/RD-23-widget-fail.png | RealDevice/RD-23-widget-retest.png | 待填 | 未通过前不得提交 App Store Connect |

## 6. 外部后台证据不能互相替代

- 外部后台证据按以下文件归档，不占用 RD 编号：
  - `03-app-filing.png` 或 `.pdf`
  - `07-sms-provider.png`
  - `08-wechat-open-platform.png`
  - `08b-wechat-universal-link-aasa.png`
  - `09-obs-policy.png`
  - `17-age-rating-result.png` 或 `.pdf`

## 7. 填回正式文件

同时从 `RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json` 复制生成 `RealDevice/REAL-DEVICE-CAPTURE-RESULT.json`。结果文件必须填写 `status: captured-live-real-device`、`iOS 26.5`、`TestFlight` 或 `Xcode 签名真机包`、`sameBuildAsSignedArchiveAndTestFlight`、`canSubmitAtCapture`、`redactionReviewed`、`rdResults.feedingReminderDeferral`、`rdResults.login`、`rdResults.accountDelete`、`rdResults.notificationPermission`、`rdResults.dynamicIsland.visualQA`、`rdResults.lockScreen.visualQA` 和 `rdResults.homeWidget.visualQA`。模板不是证据；只要结构化结果没有填完，就不能把 RD-03、RD-22、RD-23 或任何登录/账号删除/通知权限截图当作最终提交证据。

## 8. 拍完后立刻跑

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json
python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json --allow-incomplete
python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-20260630T-current.json
```
""".lstrip()


def valid_focused_capture_dependency_matrix() -> list[dict]:
    rows = [
        (
            "RD-03",
            "RealDevice/RD-03-feeding-record.png",
            [
                "iOS 26.5 physical iPhone available",
                "same TestFlight or Xcode signed build prepared",
                "fixed feeding interval configured",
            ],
            [
                "deferral wheel options",
                "next reminder rebase",
                "does not infer from volume, age, sensor, or health data",
            ],
            [
                "does not prove RD-22 Dynamic Island",
                "does not prove notification permission",
            ],
        ),
        (
            "RD-10",
            "RealDevice/RD-10-recovery-login.png",
            [
                ".env.xnp-review-account",
                "redacted review account proof",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "recovery-key login works",
                "recovery key is not visible",
            ],
            [
                "does not prove SMS login",
                "does not prove WeChat login",
            ],
        ),
        (
            "RD-13",
            "RealDevice/RD-13-phone-login.png",
            [
                "SMS provider live-send proof",
                "verify_auth_providers.py --send-test-sms --require-sms-live-send",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "real SMS code can be sent and verified",
                "no debug verification code is accepted",
            ],
            [
                "does not prove recovery-key login",
                "does not prove WeChat login",
            ],
        ),
        (
            "RD-14",
            "RealDevice/RD-14-wechat-login.png",
            [
                "WeChat Open Platform proof",
                "AASA universal link proof",
                "real WeChat release values are configured",
            ],
            [
                "WeChat authorization opens and returns",
                "no debug code path is used",
            ],
            [
                "does not prove SMS login",
                "does not prove recovery-key login",
            ],
        ),
        (
            "RD-15",
            "RealDevice/RD-15-account-delete.png",
            [
                "RD-11 cloud sync evidence",
                "RD-12 cloud restore evidence",
                "storage backend and OBS proof are green",
            ],
            [
                "old token is rejected",
                "cloud JSON sync deletion",
                "cloud photo-object deletion",
                "local data retention boundary is visible",
            ],
            [
                "does not prove production readiness",
                "does not prove OBS console policy",
            ],
        ),
        (
            "RD-17-allowed",
            "RealDevice/RD-17-notification-allowed.png",
            [
                "clean notification authorization state",
                "independent allow reset round",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "first permission prompt is visible",
                "pending reminder is effective",
            ],
            [
                "does not prove denied path",
                "does not prove lock screen notification stack",
            ],
        ),
        (
            "RD-17-denied",
            "RealDevice/RD-17-notification-denied.png",
            [
                "clean notification authorization state",
                "independent deny reset round",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "first permission prompt is visible",
                "does not pretend a reminder was created",
            ],
            [
                "does not prove allowed path",
                "does not prove lock screen notification stack",
            ],
        ),
        (
            "RD-22-compact",
            "RealDevice/RD-22-dynamic-island-compact.png",
            [
                "RD-03 feeding deferral scenario prepared",
                "Live Activity enabled",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "compact state is not clipped",
                "no health advice or medical claim",
            ],
            [
                "does not prove expanded Dynamic Island",
                "does not prove lock screen widget",
            ],
        ),
        (
            "RD-22-expanded",
            "RealDevice/RD-22-dynamic-island-expanded.png",
            [
                "RD-03 feeding deferral scenario prepared",
                "Live Activity enabled",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "manual deferral value is readable",
                "no health advice or medical claim",
                "no persistent deferral field is claimed",
            ],
            [
                "does not prove compact Dynamic Island",
                "does not prove home widget",
            ],
        ),
        (
            "RD-23-lock",
            "RealDevice/RD-23-lock-screen-notification-stack.png",
            [
                "RD-17 allowed path captured",
                "next feeding reminder exists",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "notification stack does not cover the reminder card",
                "reminder card remains readable",
            ],
            [
                "does not prove lock screen widget",
                "does not prove home widget",
            ],
        ),
        (
            "RD-23-lock-widget",
            "RealDevice/RD-23-lock-screen-widget-summary.png",
            [
                "lock screen widget configured",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "accessory widget is readable",
                "no notes, photos, tokens, or object keys",
            ],
            [
                "does not prove notification stack",
                "does not prove home widget",
            ],
        ),
        (
            "RD-23-home-widget",
            "RealDevice/RD-23-home-widget-summary.png",
            [
                "home widget configured",
                "same TestFlight or Xcode signed build prepared",
            ],
            [
                "today summary is readable",
                "no notes, photos, tokens, or object keys",
            ],
            [
                "does not prove lock screen widget",
                "does not prove notification stack",
            ],
        ),
    ]
    return [
        {
            "artifactId": artifact_id,
            "target": target,
            "requiredBeforeCapture": required_before_capture,
            "mustObserve": must_observe,
            "doesNotReplace": does_not_replace,
            "blockIfMissing": True,
            "initialStatus": "pending",
        }
        for artifact_id, target, required_before_capture, must_observe, does_not_replace in rows
    ]


def valid_focused_capture_packet() -> dict:
    return {
        "artifactType": "real-device-focused-capture-packet",
        "status": "template-only-not-evidence",
        "date": "2026-06-30",
        "evidenceRoot": "Docs/08_Release/AppStoreEvidence/RealDevice/",
        "sourceFiles": {
            "plan": "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
            "template": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md",
            "executionSheet": "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md",
            "preflightPacket": "Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260630.json",
            "deviceAvailabilityProof": "Backend/proof/ios265-device-availability.json",
            "appStoreEvidenceProof": "Backend/proof/app-store-evidence-20260630T-current.json",
        },
        "requirements": {
            "ios": "26.5",
            "buildSourceOptions": ["TestFlight", "Xcode 签名真机包"],
            "sameBuildRequired": True,
            "noSimulatorEvidence": True,
            "minFileBytes": 10240,
            "captureWindowRequired": True,
            "independentEvidenceFileRequired": True,
        },
            "targetEvidenceFiles": {
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
            },
            "evidenceFileChecks": [
                {
                    "artifactId": "RD-03",
                    "target": "RealDevice/RD-03-feeding-record.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-10",
                    "target": "RealDevice/RD-10-recovery-login.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-13",
                    "target": "RealDevice/RD-13-phone-login.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-14",
                    "target": "RealDevice/RD-14-wechat-login.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-15",
                    "target": "RealDevice/RD-15-account-delete.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-17-allowed",
                    "target": "RealDevice/RD-17-notification-allowed.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-17-denied",
                    "target": "RealDevice/RD-17-notification-denied.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-22-compact",
                    "target": "RealDevice/RD-22-dynamic-island-compact.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-22-expanded",
                    "target": "RealDevice/RD-22-dynamic-island-expanded.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-23-lock",
                    "target": "RealDevice/RD-23-lock-screen-notification-stack.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-23-lock-widget",
                    "target": "RealDevice/RD-23-lock-screen-widget-summary.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "RD-23-home-widget",
                    "target": "RealDevice/RD-23-home-widget-summary.png",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameBuildAsFocusedCapture": False,
                    "runtimeIsIos265": False,
                    "sourceIsRealDeviceEvidenceRoot": False,
                    "independentEvidenceFile": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
            ],
            "captureDependencyMatrix": valid_focused_capture_dependency_matrix(),
            "cases": [
            {
                "id": "RD-03",
                "title": "记录喂养与提醒顺延滚轮",
                "targetFile": "RealDevice/RD-03-feeding-record.png",
                "notes": [
                    "固定喝奶间隔",
                    "顺延滚轮",
                    "不顺延、+5、+10、+15、+20、+25、+30 分钟",
                    "本顿结束时间 + 固定间隔 + 顺延分钟",
                    "本顿无喂养时长时按本顿发生时间",
                    "不根据奶量、月龄、传感器或健康数据自动推算",
                ],
            },
            {
                "id": "RD-10",
                "title": "恢复密钥账号登录",
                "targetFile": "RealDevice/RD-10-recovery-login.png",
                "notes": ["恢复密钥不入镜", ".env.xnp-review-account"],
            },
            {
                "id": "RD-13",
                "title": "手机号登录",
                "targetFile": "RealDevice/RD-13-phone-login.png",
                "notes": ["真实短信服务商", "完整手机号", "验证码"],
            },
            {
                "id": "RD-14",
                "title": "微信登录",
                "targetFile": "RealDevice/RD-14-wechat-login.png",
                "notes": ["微信开放平台", "debug code", "AppSecret"],
            },
            {
                "id": "RD-15",
                "title": "删除云端账号与同步",
                "targetFile": "RealDevice/RD-15-account-delete.png",
                "notes": [
                    "测试账号已完成云同步",
                    "云端照片对象存在可删除 proof",
                    "删除云端账号与同步入口可达",
                    "确认弹窗文案清楚",
                    "删除后旧 token 失效",
                    "云端同步删除",
                    "照片对象删除",
                    "本机资料默认保留边界清楚",
                ],
            },
            {
                "id": "RD-17-allowed",
                "title": "通知权限允许",
                "targetFile": "RealDevice/RD-17-notification-allowed.png",
                "notes": [
                    "干净通知授权状态",
                    "首次弹窗可见",
                    "删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包",
                    "不能复用同一次授权状态",
                    "点击允许",
                    "允许后可创建下一次喝奶提醒",
                    "pending reminder 生效",
                    "不展示系统外 debug 文案",
                ],
            },
            {
                "id": "RD-17-denied",
                "title": "通知权限拒绝",
                "targetFile": "RealDevice/RD-17-notification-denied.png",
                "notes": [
                    "干净通知授权状态",
                    "首次弹窗可见",
                    "删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包",
                    "不能复用同一次授权状态",
                    "点击拒绝",
                    "拒绝后有可理解状态",
                    "系统设置入口可见",
                    "不继续假装已创建提醒",
                ],
            },
            {
                "id": "RD-22-compact",
                "title": "灵动岛紧凑态",
                "targetFile": "RealDevice/RD-22-dynamic-island-compact.png",
                "notes": ["无裁剪", "独立证据文件"],
            },
            {
                "id": "RD-22-expanded",
                "title": "灵动岛展开态",
                "targetFile": "RealDevice/RD-22-dynamic-island-expanded.png",
                "notes": [
                    "手动顺延后的提醒时间",
                    "不顺延、+5、+10、+15、+20、+25、+30 分钟",
                    "本顿结束时间 + 固定间隔 + 顺延分钟",
                    "本顿无喂养时长时按本顿发生时间",
                    "不新增持久化字段",
                ],
            },
            {
                "id": "RD-23-lock",
                "title": "锁屏通知栈",
                "targetFile": "RealDevice/RD-23-lock-screen-notification-stack.png",
                "notes": ["不遮挡提醒卡片", "独立证据文件"],
            },
            {
                "id": "RD-23-lock-widget",
                "title": "锁屏小组件",
                "targetFile": "RealDevice/RD-23-lock-screen-widget-summary.png",
                "notes": [
                    "accessoryCircular",
                    "accessoryRectangular",
                    "accessoryInline",
                    "不裁剪不溢出",
                    "只读展示本机今日摘要",
                    "不展示备注",
                    "不展示真实照片",
                    "不展示 token",
                    "不展示对象存储 key",
                ],
            },
            {
                "id": "RD-23-home-widget",
                "title": "桌面小组件",
                "targetFile": "RealDevice/RD-23-home-widget-summary.png",
                "notes": [
                    "只读展示本机今日摘要",
                    "不裁剪不溢出",
                    "不展示备注",
                    "不展示真实照片",
                    "不展示 token",
                    "不展示对象存储 key",
                ],
            },
        ],
        "postCaptureCommands": [
            "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
            "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
            "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
        ],
        "evidenceManifestTemplate": {
            "status": "manifest-template-not-evidence",
            "targetFiles": [
                "RealDevice/RD-03-feeding-record.png",
                "RealDevice/RD-10-recovery-login.png",
                "RealDevice/RD-13-phone-login.png",
                "RealDevice/RD-14-wechat-login.png",
                "RealDevice/RD-15-account-delete.png",
                "RealDevice/RD-17-notification-allowed.png",
                "RealDevice/RD-17-notification-denied.png",
                "RealDevice/RD-22-dynamic-island-compact.png",
                "RealDevice/RD-22-dynamic-island-expanded.png",
                "RealDevice/RD-23-lock-screen-notification-stack.png",
                "RealDevice/RD-23-lock-screen-widget-summary.png",
                "RealDevice/RD-23-home-widget-summary.png",
            ],
            "requiredFields": [
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
            ],
            "validationRules": [
                "ios must equal 26.5",
                "installSource must be TestFlight or Xcode 签名真机包",
                "fileSizeBytes must be >= 10240",
                "sha256 must be recorded after capture",
                "redactionChecked must be true before copying into 12-real-device-regression.md",
                "independentEvidenceFile must be true; do not reuse overview screenshots",
                "sameBuildAs05SignedArchive and sameBuildAs06TestFlight must be true when TestFlight is used",
                "captureStartedAt and captureEndedAt must stay inside the same execution window",
            ],
        },
        "completionRule": "template-only-not-evidence；不替代 TestFlight / 签名真机回归；不代表 RD-03/RD-10/RD-13/RD-14/RD-15/RD-17/RD-22/RD-23 已完成。只有填回 12-real-device-regression.md 且 app-store-evidence-20260630T-current.json ready=true 后才完成。",
    }


def valid_real_device_capture_result_template() -> dict:
    template_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json"
    )
    return json.loads(template_path.read_text(encoding="utf-8"))


def valid_real_device_capture_preflight() -> dict:
    packet_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260630.json"
    )
    return json.loads(packet_path.read_text(encoding="utf-8"))


def write_complete_fixture(root: Path) -> None:
    write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", complete_plan())
    write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", complete_template())
    write(root / "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md", complete_execution_sheet())
    write_json(
        root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
        valid_focused_capture_packet(),
    )
    write_json(
        root / "Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260630.json",
        valid_real_device_capture_preflight(),
    )
    write_json(
        root / "Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json",
        valid_real_device_capture_result_template(),
    )
    write_json(
        root / "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
        {
            "recoveryVerified": True,
            "syncSeeded": True,
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
            "eligibleIOS265PhysicalIphones": [
                {"name": "lanlan", "osVersion": "26.5", "available": True}
            ],
            "availableNonIOS265PhysicalIphones": [
                {"name": "面面", "osVersion": "27.0", "available": True}
            ],
        },
    )
    write_json(
        root / "Backend/proof/app-store-evidence-20260630T-current.json",
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
    def run_checker(self, root: Path, expected_sim_launch_date: str | None = "20260626") -> dict:
        output = root / "Backend/proof/testflight-regression-plan.json"
        command = [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(root),
            "--output",
            str(output),
            "--allow-incomplete",
        ]
        if expected_sim_launch_date is not None:
            command.extend(["--expected-sim-launch-date", expected_sim_launch_date])
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("TestFlight regression plan", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_default_run_requires_current_sim_launch_date(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)

            report = self.run_checker(root, expected_sim_launch_date=None)

            self.assertFalse(report["passed"])
            self.assertIn("ios265SmokeProofDateCurrent", report["failedRequiredChecks"])
            evidence = report["checks"]["ios265SmokeProofDateCurrent"]["evidence"]
            self.assertIn("selected sim launch date 20260626", evidence)
            self.assertIn("expected 20260630", evidence)

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
            broken = broken.replace("| RD-23 | 锁屏/桌面小组件 | 锁屏通知栈不遮挡；锁屏小组件和桌面小组件只读展示本机今日摘要，不展示照片原图、备注、token 或云端对象 key | 待测 |\n", "")
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

    def test_ios265_device_availability_failure_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            write_json(
                root / "Backend/proof/ios265-device-availability.json",
                {
                    "passed": False,
                    "requiredIOS": "26.5",
                    "failedRequiredChecks": ["eligibleIOS265PhysicalIphoneAvailable"],
                    "eligibleIOS265PhysicalIphones": [],
                    "availableNonIOS265PhysicalIphones": [
                        {"name": "mianmian", "osVersion": "27.0", "available": True}
                    ],
                },
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ios265PhysicalDeviceAvailable", report["failedRequiredChecks"])
            self.assertIn(
                "eligibleIOS265PhysicalIphoneAvailable",
                report["checks"]["ios265PhysicalDeviceAvailable"]["evidence"],
            )

    def test_real_device_template_must_include_review_surface_checkboxes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            loose_template = complete_template()
            loose_template = loose_template.replace("- [ ] 通知权限允许后可创建下一次喝奶提醒\n", "")
            loose_template = loose_template.replace("- [ ] 通知权限拒绝后有可理解状态和系统设置入口\n", "")
            loose_template = loose_template.replace("- [ ] 通知权限允许独立截图\n", "")
            loose_template = loose_template.replace("- [ ] 通知权限拒绝独立截图\n", "")
            loose_template = loose_template.replace("- [ ] 灵动岛喝奶提醒开关\n", "")
            loose_template = loose_template.replace("- [ ] 灵动岛紧凑态独立截图\n", "")
            loose_template = loose_template.replace("- [ ] 灵动岛展开态独立截图\n", "")
            loose_template = loose_template.replace("- [ ] 灵动岛展开态展示手动顺延后的提醒时间\n", "")
            loose_template = loose_template.replace("- [ ] 锁屏/桌面小组件\n", "")
            loose_template = loose_template.replace("- [ ] 锁屏通知栈独立截图\n", "")
            loose_template = loose_template.replace("- [ ] 锁屏小组件独立截图\n", "")
            loose_template = loose_template.replace("- [ ] 桌面小组件独立截图\n", "")
            loose_template = loose_template.replace("- [ ] 锁屏小组件内容不裁剪不展示隐私照片\n", "")
            loose_template = loose_template.replace("- [ ] 桌面小组件内容不裁剪不展示隐私照片\n", "")
            loose_template = loose_template.replace("- [ ] 审核边界文案\n", "")
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", loose_template)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceRegressionTemplateStrict", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceRegressionTemplateStrict"]["evidence"]
            self.assertIn("- [ ] 通知权限允许后可创建下一次喝奶提醒", evidence)
            self.assertIn("- [ ] 通知权限拒绝后有可理解状态和系统设置入口", evidence)
            self.assertIn("- [ ] 通知权限允许独立截图", evidence)
            self.assertIn("- [ ] 通知权限拒绝独立截图", evidence)
            self.assertIn("- [ ] 灵动岛喝奶提醒开关", evidence)
            self.assertIn("- [ ] 灵动岛紧凑态独立截图", evidence)
            self.assertIn("- [ ] 灵动岛展开态独立截图", evidence)
            self.assertIn("- [ ] 灵动岛展开态展示手动顺延后的提醒时间", evidence)
            self.assertIn("- [ ] 锁屏/桌面小组件", evidence)
            self.assertIn("- [ ] 锁屏通知栈独立截图", evidence)
            self.assertIn("- [ ] 锁屏小组件独立截图", evidence)
            self.assertIn("- [ ] 桌面小组件独立截图", evidence)
            self.assertIn("- [ ] 锁屏小组件内容不裁剪不展示隐私照片", evidence)
            self.assertIn("- [ ] 桌面小组件内容不裁剪不展示隐私照片", evidence)
            self.assertIn("- [ ] 审核边界文案", evidence)

    def test_real_device_template_rd_summary_requires_independent_surface_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            loose_template = complete_template()
            loose_template = loose_template.replace(
                "RD-17 通知权限 | 待测 | RealDevice/RD-17-notification-allowed.png；RealDevice/RD-17-notification-denied.png",
                "RD-17 通知权限 | 待测 | RealDevice/RD-17-notification-allowed.png",
            )
            loose_template = loose_template.replace(
                "RD-22 灵动岛喝奶提醒开关 | 待测 | RealDevice/RD-22-dynamic-island-compact.png；RealDevice/RD-22-dynamic-island-expanded.png",
                "RD-22 灵动岛喝奶提醒开关 | 待测 | RealDevice/RD-22-dynamic-island-compact.png",
            )
            loose_template = loose_template.replace(
                "RD-23 锁屏/桌面小组件 | 待测 | RealDevice/RD-23-lock-screen-notification-stack.png；RealDevice/RD-23-lock-screen-widget-summary.png；RealDevice/RD-23-home-widget-summary.png",
                "RD-23 锁屏/桌面小组件 | 待测 | RealDevice/RD-23-lock-screen-notification-stack.png",
            )
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", loose_template)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceRegressionTemplateStrict", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceRegressionTemplateStrict"]["evidence"]
            self.assertIn(
                "RD-17 通知权限 | 待测 | RealDevice/RD-17-notification-allowed.png；RealDevice/RD-17-notification-denied.png",
                evidence,
            )
            self.assertIn(
                "RD-22 灵动岛喝奶提醒开关 | 待测 | RealDevice/RD-22-dynamic-island-compact.png；RealDevice/RD-22-dynamic-island-expanded.png",
                evidence,
            )
            self.assertIn(
                "RD-23 锁屏/桌面小组件 | 待测 | RealDevice/RD-23-lock-screen-notification-stack.png；RealDevice/RD-23-lock-screen-widget-summary.png；RealDevice/RD-23-home-widget-summary.png",
                evidence,
            )

    def test_focused_capture_shot_list_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            plan = complete_plan().replace("## 重点采集清单", "## 采集").replace("锁屏通知栈", "")
            template = complete_template().replace("## 重点采集清单", "## 采集").replace("锁屏通知栈", "")
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", plan)
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", template)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedEvidenceCaptureShotListPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedEvidenceCaptureShotListPresent"]["evidence"]
            self.assertIn("## 重点采集清单", evidence)
            self.assertIn("锁屏通知栈", evidence)

    def test_structured_focused_capture_packet_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_focused_capture_packet()
            packet["sourceFiles"].pop("preflightPacket")
            packet["requirements"]["ios"] = "27.0"
            packet["requirements"]["minFileBytes"] = 100
            packet["requirements"]["captureWindowRequired"] = False
            packet["requirements"]["independentEvidenceFileRequired"] = False
            packet["cases"] = [
                item
                for item in packet["cases"]
                if item["targetFile"] != "RealDevice/RD-17-notification-denied.png"
            ]
            for item in packet["cases"]:
                if item["targetFile"] == "RealDevice/RD-15-account-delete.png":
                    item["notes"] = ["删除后旧 token 失效"]
                if item["targetFile"] == "RealDevice/RD-22-dynamic-island-expanded.png":
                    item["notes"] = ["手动顺延后的提醒时间"]
            packet["postCaptureCommands"] = [
                "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json"
            ]
            packet["evidenceManifestTemplate"]["targetFiles"].remove("RealDevice/RD-23-lock-screen-widget-summary.png")
            packet["evidenceManifestTemplate"]["requiredFields"].remove("sha256")
            packet["evidenceManifestTemplate"]["validationRules"].remove("fileSizeBytes must be >= 10240")
            packet["completionRule"] = "template"
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedCapturePacketValid"]["evidence"]
            self.assertIn("sourceFiles.preflightPacket must be", evidence)
            self.assertIn("requirements.ios must be 26.5", evidence)
            self.assertIn("requirements.minFileBytes must be at least 10240", evidence)
            self.assertIn("requirements.captureWindowRequired must be true", evidence)
            self.assertIn("requirements.independentEvidenceFileRequired must be true", evidence)
            self.assertIn("cases missing RealDevice/RD-17-notification-denied.png", evidence)
            self.assertIn("RD-15-account-delete.png missing 本机资料默认保留", evidence)
            self.assertIn("RD-22-dynamic-island-expanded.png missing 不顺延、+5、+10、+15、+20、+25、+30 分钟", evidence)
            self.assertIn("evidenceManifestTemplate.targetFiles missing RealDevice/RD-23-lock-screen-widget-summary.png", evidence)
            self.assertIn("evidenceManifestTemplate.requiredFields missing sha256", evidence)
            self.assertIn("evidenceManifestTemplate.validationRules missing fileSizeBytes must be >= 10240", evidence)
            self.assertIn("completion boundary missing 不替代 TestFlight / 签名真机回归", evidence)
            self.assertIn("postCaptureCommands missing python3 Backend/scripts/check_app_store_evidence.py", evidence)

    def test_real_device_capture_preflight_packet_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_real_device_capture_preflight()
            packet["canStartCaptureFromThisPacket"] = True
            packet["canSubmitFromThisPacket"] = True
            packet["sourceFiles"]["deviceAvailabilityProof"] = "Backend/proof/ios27-device-availability.json"
            packet["preflightChecks"] = [
                item
                for item in packet["preflightChecks"]
                if item["id"] != "dynamicIslandAndWidgetPreconditionsReady"
            ]
            packet["preflightChecks"][0]["requiredState"] = "passed=false"
            packet["preflightChecks"][0]["mustSee"] = ["requiredIOS=26.5"]
            packet["preflightChecks"][3]["mustSee"] = ["clean authorization state"]
            packet["preflightChecks"][4]["mustSee"] = ["SMS provider live send proof"]
            packet["captureGateMatrix"] = [
                item for item in packet["captureGateMatrix"] if item["id"] != "finalize-regression"
            ]
            packet["captureGateMatrix"][1]["requiredEvidenceOutputs"] = [
                "RealDevice/RD-13-phone-login.png"
            ]
            packet["captureGateMatrix"][3]["canSubmitFromGate"] = True
            packet["captureGateMatrix"][4]["initialStatus"] = "captured"
            packet["captureStartDecision"]["expectedBeforeAllGreen"] = "start-capture"
            packet["captureStartDecision"]["mustNotUseAsSubstituteFor"] = []
            packet["postPreflightCommands"] = [
                command
                for command in packet["postPreflightCommands"]
                if "check_launch_objective_audit.py" not in command["command"]
            ]
            packet["completionRule"] = "done"
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceCapturePreflightValid", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceCapturePreflightValid"]["evidence"]
            self.assertIn("canStartCaptureFromThisPacket must be False", evidence)
            self.assertIn("canSubmitFromThisPacket must be False", evidence)
            self.assertIn("sourceFiles.deviceAvailabilityProof must be Backend/proof/ios265-device-availability.json", evidence)
            self.assertIn("preflightChecks order must match real-device capture preflight order", evidence)
            self.assertIn("preflightChecks missing dynamicIslandAndWidgetPreconditionsReady", evidence)
            self.assertIn("preflightChecks.ios265PhysicalDeviceAvailable missing passed=true", evidence)
            self.assertIn("preflightChecks.ios265PhysicalDeviceAvailable missing eligibleIOS265PhysicalIphoneAvailable", evidence)
            self.assertIn("preflightChecks.notificationPermissionResetReady missing first permission prompt visible", evidence)
            self.assertIn("preflightChecks.externalLoginProvidersReady missing WeChat Open Platform evidence", evidence)
            self.assertIn("captureGateMatrix order must match real-device capture gate order", evidence)
            self.assertIn("captureGateMatrix missing finalize-regression", evidence)
            self.assertIn(
                "captureGateMatrix.external-login.requiredEvidenceOutputs must be RealDevice/RD-13-phone-login.png, RealDevice/RD-14-wechat-login.png",
                evidence,
            )
            self.assertIn("captureGateMatrix.notification-permission.canSubmitFromGate must be False", evidence)
            self.assertIn("captureGateMatrix.live-activity-widgets.initialStatus must be pending", evidence)
            self.assertIn("captureStartDecision missing do-not-start-real-device-capture", evidence)
            self.assertIn("captureStartDecision missing 08-wechat-open-platform.png", evidence)
            self.assertIn("postPreflightCommands missing python3 Backend/scripts/check_launch_objective_audit.py", evidence)
            self.assertIn("completion boundary missing not submission permission", evidence)

    def test_focused_capture_packet_requires_evidence_file_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_focused_capture_packet()
            packet["evidenceFileChecks"] = [
                check for check in packet["evidenceFileChecks"] if check["artifactId"] != "RD-13"
            ]
            packet["evidenceFileChecks"][0]["target"] = "RealDevice/RD-03-wrong.png"
            packet["evidenceFileChecks"][0]["sha256"] = "already-filled"
            packet["evidenceFileChecks"][0]["sameBuildAsFocusedCapture"] = True
            packet["evidenceFileChecks"][0]["runtimeIsIos265"] = True
            packet["evidenceFileChecks"][0]["sourceIsRealDeviceEvidenceRoot"] = True
            packet["evidenceFileChecks"][0]["independentEvidenceFile"] = True
            packet["evidenceFileChecks"][0]["realEvidenceNotTemplate"] = True
            packet["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedCapturePacketValid"]["evidence"]
            self.assertIn("evidenceFileChecks order must match focused capture execution order", evidence)
            self.assertIn("evidenceFileChecks.RD-13 missing object", evidence)
            self.assertIn("evidenceFileChecks.RD-03.target must be RealDevice/RD-03-feeding-record.png", evidence)
            self.assertIn("evidenceFileChecks.RD-03.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("evidenceFileChecks.RD-03.sameBuildAsFocusedCapture must be False", evidence)
            self.assertIn("evidenceFileChecks.RD-03.runtimeIsIos265 must be False", evidence)
            self.assertIn("evidenceFileChecks.RD-03.sourceIsRealDeviceEvidenceRoot must be False", evidence)
            self.assertIn("evidenceFileChecks.RD-03.independentEvidenceFile must be False", evidence)
            self.assertIn("evidenceFileChecks.RD-03.realEvidenceNotTemplate must be False", evidence)
            self.assertIn("evidenceFileChecks.RD-03.secretValuesNotRecorded must be False", evidence)

    def test_real_device_capture_result_template_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            template = valid_real_device_capture_result_template()
            template["status"] = "captured-live-real-device"
            template["capturedBy"] = "Penghui She / 佘鹏辉"
            template["allowedInstallSources"] = ["TestFlight"]
            template["sameBuildAsSignedArchiveAndTestFlight"] = True
            template["redactionReviewed"] = True
            template["crossAppDoesNotReplaceXiaoNaiPingProof"] = False
            template[
                "submissionReadinessProof"
            ] = "/Users/smianmian/Emotion Isle/output/cross-app-submission-readiness-20260630-current.json"
            template["instructions"].append(
                "Submit is still blocked unless /Users/smianmian/Emotion Isle/output/cross-app-submission-readiness-20260630-current.json has canSubmit=true."
            )
            template["xiaonaipingRequiredProofs"].pop("productionReadiness")
            template["postCaptureXiaoNaiPingProofReruns"] = {
                "checkCrossAppSubmitReady": "python3 /Users/smianmian/Emotion Isle/scripts/check-cross-app-submit-ready.py"
            }
            template["captureSessionIntegrity"]["captureFlags"]["sameBuildAcrossAllFocusedRdFiles"] = True
            template["captureSessionIntegrity"]["captureGroups"]["login"] = ["RD-10", "RD-13"]
            template["captureSessionIntegrity"]["groupRequirements"]["dynamicIsland"] = [
                item
                for item in template["captureSessionIntegrity"]["groupRequirements"]["dynamicIsland"]
                if "manual deferral result" not in item
            ]
            template["captureSessionIntegrity"]["stopConditions"] = [
                item
                for item in template["captureSessionIntegrity"]["stopConditions"]
                if item["id"] != "notificationResetMissing"
            ]
            for row in template["artifactCaptureMatrix"]:
                if row["artifactId"] == "RD-13":
                    row["target"] = "RealDevice/RD-13-wrong.png"
                    row["sameBuildRequired"] = False
                    row["requiredBeforeCapture"] = [
                        item
                        for item in row["requiredBeforeCapture"]
                        if "real SMS provider live-send proof" not in item
                    ]
            template["artifactCaptureMatrix"] = [
                row
                for row in template["artifactCaptureMatrix"]
                if row["artifactId"] != "RD-23-home-widget"
            ]
            template["evidenceFileChecks"] = [
                check
                for check in template["evidenceFileChecks"]
                if check["artifactId"] != "RD-13"
            ]
            template["evidenceFileChecks"][0]["target"] = "RealDevice/RD-03-wrong.png"
            template["evidenceFileChecks"][0]["sha256"] = "already-filled"
            template["evidenceFileChecks"][0]["sameBuildAsResult"] = True
            template["evidenceFileChecks"][0]["runtimeIsIos265"] = True
            template["evidenceFileChecks"][0]["sourceIsRealDeviceEvidenceRoot"] = True
            template["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            del template["rdResults"]["feedingReminderDeferral"]["allowedDeferralOptionsOnly"]
            template["rdResults"]["feedingReminderDeferral"]["deferralWheelOptionsVisible"] = True
            del template["rdResults"]["login"]["wechatLogin"]["wechatReturnedToXiaoNaiPing"]
            template["rdResults"]["login"]["wechatLogin"]["noDebugCodePathUsed"] = True
            del template["rdResults"]["login"]["recoveryKeyLogin"]["recoveryKeyNotVisible"]
            template["rdResults"]["login"]["recoveryKeyLogin"]["accountSyncScreenReachable"] = True
            del template["rdResults"]["accountDelete"]["cloudJsonSyncDeleted"]
            template["rdResults"]["accountDelete"]["photoObjectsDeleted"] = True
            template["rdResults"]["accountDelete"]["deleteEntryAndConfirmationVisible"] = True
            del template["rdResults"]["notificationPermission"]["deniedDoesNotPretendReminderCreated"]
            del template["rdResults"]["notificationPermission"]["allowedReminderPendingAndEffective"]
            template["rdResults"]["notificationPermission"]["deniedSettingsEntryVisible"] = True
            del template["rdResults"]["dynamicIsland"]["visualQA"]["expandedFixedIntervalReadable"]
            template["rdResults"]["dynamicIsland"]["visualQA"]["manualDeferralReadable"] = True
            template["rdResults"]["dynamicIsland"]["visualQA"]["compactNotCenteredIncorrectly"] = True
            del template["rdResults"]["lockScreen"]["visualQA"]["accessoryRectangularReadable"]
            template["rdResults"]["lockScreen"]["visualQA"]["reminderCardReadable"] = True
            del template["rdResults"]["homeWidget"]["visualQA"]["localTodaySummaryOnly"]
            template["rdResults"]["homeWidget"]["visualQA"]["homeWidgetNotClipped"] = True
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json",
                template,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceCaptureResultTemplateValid", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceCaptureResultTemplateValid"]["evidence"]
            self.assertIn("status must be template-not-evidence", evidence)
            self.assertIn("capturedBy must be 佘鹏辉 / Penghui She", evidence)
            self.assertIn("allowedInstallSources must be TestFlight, Xcode 签名真机包", evidence)
            self.assertIn("sameBuildAsSignedArchiveAndTestFlight must be False", evidence)
            self.assertIn("redactionReviewed must be False", evidence)
            self.assertIn("crossAppDoesNotReplaceXiaoNaiPingProof must be True", evidence)
            self.assertIn(
                "submissionReadinessProof must be Backend/proof/launch-objective-audit.json",
                evidence,
            )
            self.assertIn(
                "real-device capture result template must not depend on Emotion Isle cross-app submission readiness",
                evidence,
            )
            self.assertIn(
                "xiaonaipingRequiredProofs.productionReadiness must be Backend/proof/production-readiness-20260630T-current.json",
                evidence,
            )
            self.assertIn(
                "postCaptureXiaoNaiPingProofReruns.checkProductionReadiness must be python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-20260630T-current.json",
                evidence,
            )
            self.assertIn(
                "captureSessionIntegrity.captureFlags.sameBuildAcrossAllFocusedRdFiles must be False",
                evidence,
            )
            self.assertIn(
                "captureSessionIntegrity.captureGroups.login must be RD-10, RD-13, RD-14",
                evidence,
            )
            self.assertIn(
                "captureSessionIntegrity.groupRequirements.dynamicIsland missing manual deferral result",
                evidence,
            )
            self.assertIn(
                "captureSessionIntegrity.stopConditions missing notificationResetMissing",
                evidence,
            )
            self.assertIn("artifactCaptureMatrix order must match real-device focused capture workflow", evidence)
            self.assertIn(
                "artifactCaptureMatrix.RD-13.sameBuildRequired must be True",
                evidence,
            )
            self.assertIn(
                "artifactCaptureMatrix.RD-13.target must be RealDevice/RD-13-phone-login.png",
                evidence,
            )
            self.assertIn(
                "artifactCaptureMatrix.RD-13.requiredBeforeCapture missing real SMS provider live-send proof",
                evidence,
            )
            self.assertIn("artifactCaptureMatrix missing RD-23-home-widget", evidence)
            self.assertIn("evidenceFileChecks order must match real-device focused capture workflow", evidence)
            self.assertIn("evidenceFileChecks.RD-13 missing object", evidence)
            self.assertIn(
                "evidenceFileChecks.RD-03.target missing RealDevice/RD-03-feeding-record.png",
                evidence,
            )
            self.assertIn("evidenceFileChecks.RD-03.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("evidenceFileChecks.RD-03.sameBuildAsResult must be False", evidence)
            self.assertIn("evidenceFileChecks.RD-03.runtimeIsIos265 must be False", evidence)
            self.assertIn(
                "evidenceFileChecks.RD-03.sourceIsRealDeviceEvidenceRoot must be False",
                evidence,
            )
            self.assertIn("evidenceFileChecks.RD-03.secretValuesNotRecorded must be False", evidence)
            self.assertIn(
                "rdResults.feedingReminderDeferral.allowedDeferralOptionsOnly must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.feedingReminderDeferral.deferralWheelOptionsVisible must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.login.wechatLogin.wechatReturnedToXiaoNaiPing must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.login.wechatLogin.noDebugCodePathUsed must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.login.recoveryKeyLogin.recoveryKeyNotVisible must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.login.recoveryKeyLogin.accountSyncScreenReachable must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.accountDelete.cloudJsonSyncDeleted must be False",
                evidence,
            )
            self.assertIn("rdResults.accountDelete.photoObjectsDeleted must be False", evidence)
            self.assertIn(
                "rdResults.accountDelete.deleteEntryAndConfirmationVisible must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.notificationPermission.deniedDoesNotPretendReminderCreated must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.notificationPermission.allowedReminderPendingAndEffective must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.notificationPermission.deniedSettingsEntryVisible must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.dynamicIsland.visualQA.expandedFixedIntervalReadable must be False",
                evidence,
            )
            self.assertIn("rdResults.dynamicIsland.visualQA.manualDeferralReadable must be False", evidence)
            self.assertIn(
                "rdResults.dynamicIsland.visualQA.compactNotCenteredIncorrectly must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.lockScreen.visualQA.accessoryRectangularReadable must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.lockScreen.visualQA.reminderCardReadable must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.homeWidget.visualQA.localTodaySummaryOnly must be False",
                evidence,
            )
            self.assertIn(
                "rdResults.homeWidget.visualQA.homeWidgetNotClipped must be False",
                evidence,
            )

    def test_focused_capture_packet_rejects_duplicate_case_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_focused_capture_packet()
            for item in packet["cases"]:
                if item["targetFile"] == "RealDevice/RD-23-home-widget-summary.png":
                    item["id"] = "RD-23-lock-widget"
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedCapturePacketValid"]["evidence"]
            self.assertIn("cases duplicate id RD-23-lock-widget", evidence)
            self.assertIn("RealDevice/RD-23-home-widget-summary.png id must be RD-23-home-widget", evidence)

    def test_focused_capture_packet_rejects_extra_or_reordered_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_focused_capture_packet()
            cases = packet["cases"]
            packet["cases"] = [
                cases[1],
                cases[0],
                *cases[2:],
                {
                    "id": "RD-99-extra",
                    "title": "额外截图",
                    "targetFile": "RealDevice/RD-99-extra.png",
                    "prerequisites": ["不应进入正式 focused capture packet"],
                    "requiredObservations": ["额外目标文件会打乱现场采集"],
                    "redaction": ["token"],
                },
            ]
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedCapturePacketValid"]["evidence"]
            self.assertIn("cases order must match focused capture execution order", evidence)

    def test_focused_capture_dependency_matrix_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_focused_capture_packet()
            matrix = packet["captureDependencyMatrix"]
            packet["captureDependencyMatrix"] = [
                matrix[1],
                matrix[0],
                *matrix[2:-1],
            ]
            for item in packet["captureDependencyMatrix"]:
                if item["artifactId"] == "RD-13":
                    item["requiredBeforeCapture"] = ["same TestFlight or Xcode signed build prepared"]
                if item["artifactId"] == "RD-15":
                    item["doesNotReplace"] = ["does not prove OBS console policy"]
                if item["artifactId"] == "RD-23-lock":
                    item["initialStatus"] = "captured"
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedCapturePacketValid"]["evidence"]
            self.assertIn("captureDependencyMatrix order must match focused capture execution order", evidence)
            self.assertIn("captureDependencyMatrix.RD-23-home-widget missing object", evidence)
            self.assertIn("captureDependencyMatrix.RD-13 missing SMS provider live-send proof", evidence)
            self.assertIn("captureDependencyMatrix.RD-15 missing does not prove production readiness", evidence)
            self.assertIn("captureDependencyMatrix.RD-23-lock.initialStatus must be pending", evidence)

    def test_focused_capture_notification_denied_must_not_pretend_reminder_created(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_focused_capture_packet()
            for item in packet["cases"]:
                if item["targetFile"] == "RealDevice/RD-17-notification-denied.png":
                    item["notes"] = ["干净通知授权状态", "首次弹窗可见", "系统设置入口可见"]
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedCapturePacketValid"]["evidence"]
            self.assertIn("RD-17-notification-denied.png missing 不继续假装已创建提醒", evidence)

    def test_focused_capture_packet_rejects_mismatched_target_evidence_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_focused_capture_packet()
            targets = packet["targetEvidenceFiles"]
            packet["targetEvidenceFiles"] = {
                "RD-13": targets["RD-13"],
                "RD-03": targets["RD-03"],
                "RD-10": targets["RD-10"],
                "RD-14": "RealDevice/RD-14-wechat-login-copy.png",
                "RD-15": targets["RD-15"],
                "RD-17-allowed": targets["RD-17-allowed"],
                "RD-17-denied": targets["RD-17-denied"],
                "RD-22-compact": targets["RD-22-compact"],
                "RD-22-expanded": targets["RD-22-expanded"],
                "RD-23-lock": targets["RD-23-lock"],
                "RD-23-lock-widget": targets["RD-23-lock-widget"],
                "RD-23-home-widget": targets["RD-23-home-widget"],
                "RD-99-extra": "RealDevice/RD-99-extra.png",
            }
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedCapturePacketValid"]["evidence"]
            self.assertIn("targetEvidenceFiles order must match focused capture execution order", evidence)
            self.assertIn(
                "targetEvidenceFiles.RD-14 must be RealDevice/RD-14-wechat-login.png",
                evidence,
            )

    def test_focused_capture_manifest_rejects_duplicate_or_reordered_target_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            packet = valid_focused_capture_packet()
            target_files = packet["evidenceManifestTemplate"]["targetFiles"]
            packet["evidenceManifestTemplate"]["targetFiles"] = [
                target_files[1],
                target_files[0],
                *target_files[2:],
                target_files[-1],
            ]
            write_json(
                root / "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json",
                packet,
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("focusedCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["focusedCapturePacketValid"]["evidence"]
            self.assertIn("evidenceManifestTemplate.targetFiles duplicate RealDevice/RD-23-home-widget-summary.png", evidence)
            self.assertIn("evidenceManifestTemplate.targetFiles order must match focused capture cases", evidence)

    def test_real_device_evidence_index_and_redaction_review_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            plan = complete_plan().replace("## 证据索引与脱敏复核", "## 证据").replace("文件大小", "").replace("脱敏复核", "")
            template = complete_template().replace("## 证据索引与脱敏复核", "## 证据").replace("文件大小", "").replace("脱敏复核", "")
            execution_sheet = complete_execution_sheet().replace("## 证据索引与脱敏复核", "## 证据").replace("文件大小", "").replace("脱敏复核", "")
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", plan)
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", template)
            write(root / "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md", execution_sheet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceEvidenceIndexAndRedactionReviewPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceEvidenceIndexAndRedactionReviewPresent"]["evidence"]
            self.assertIn("证据索引与脱敏复核", evidence)
            self.assertIn("文件大小", evidence)
            self.assertIn("脱敏复核", evidence)

    def test_notification_permission_paths_must_start_from_clean_authorization_state(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            plan = complete_plan().replace("## 通知权限双路径重置锁", "## 通知权限")
            template = complete_template().replace("删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包", "")
            execution_sheet = complete_execution_sheet().replace("不能复用同一次授权状态", "")
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", plan)
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", template)
            write(root / "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md", execution_sheet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("notificationPermissionResetLockPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["notificationPermissionResetLockPresent"]["evidence"]
            self.assertIn("plan: ## 通知权限双路径重置锁", evidence)
            self.assertIn("template: 删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包", evidence)
            self.assertIn("execution_sheet: 不能复用同一次授权状态", evidence)

    def test_execution_sheet_evidence_index_must_include_login_and_account_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            execution_sheet = complete_execution_sheet()
            for row in (
                "| `RealDevice/RD-10-recovery-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥全文、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |\n",
                "| `RealDevice/RD-13-phone-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 完整手机号和验证码已遮挡，不展示 token、对象存储 key、真实宝宝照片 |\n",
                "| `RealDevice/RD-14-wechat-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示 AppSecret、debug code、完整手机号、token、对象存储 key、真实宝宝照片 |\n",
                "| `RealDevice/RD-15-account-delete.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |\n",
            ):
                execution_sheet = execution_sheet.replace(row, "")
            write(root / "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md", execution_sheet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceEvidenceIndexAndRedactionReviewPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceEvidenceIndexAndRedactionReviewPresent"]["evidence"]
            self.assertIn("execution_sheet", evidence)
            self.assertIn("RealDevice/RD-10-recovery-login.png", evidence)
            self.assertIn("RealDevice/RD-13-phone-login.png", evidence)
            self.assertIn("RealDevice/RD-14-wechat-login.png", evidence)
            self.assertIn("RealDevice/RD-15-account-delete.png", evidence)

    def test_real_device_build_identity_lock_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            plan = complete_plan().replace("## 同一 build 身份锁", "## Build 身份")
            template = complete_template().replace(
                "`AppStoreConnect/ASC-07-build-testflight-link.png`",
                "`AppStoreConnect/ASC-07-build.png`",
            )
            execution_sheet = complete_execution_sheet().replace("不能混用不同 build", "不能混用不同包")
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", plan)
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", template)
            write(root / "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md", execution_sheet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceBuildIdentityLockPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceBuildIdentityLockPresent"]["evidence"]
            self.assertIn("plan: ## 同一 build 身份锁", evidence)
            self.assertIn("template: `AppStoreConnect/ASC-07-build-testflight-link.png`", evidence)
            self.assertIn("execution_sheet: 不能混用不同 build", evidence)

    def test_real_device_failure_triage_template_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            plan = (
                complete_plan()
                .replace("## 失败复测与阻断清单", "## 复测")
                .replace("失败证据", "")
                .replace("复测证据", "")
                .replace("保留失败截图或录屏", "")
                .replace("不要覆盖失败证据", "")
                .replace("RELEASE_CHECKLIST.md", "")
                .replace("不得提交 App Store Connect", "")
            )
            template = (
                complete_template()
                .replace("## 失败复测与阻断清单", "## 复测")
                .replace("失败证据", "")
                .replace("复测证据", "")
                .replace("保留失败截图或录屏", "")
                .replace("不要覆盖失败证据", "")
                .replace("RELEASE_CHECKLIST.md", "")
                .replace("不得提交 App Store Connect", "")
            )
            execution_sheet = (
                complete_execution_sheet()
                .replace("## 5. 失败复测与阻断清单", "## 5. 复测")
                .replace("失败证据", "")
                .replace("复测证据", "")
                .replace("保留失败截图或录屏", "")
                .replace("不要覆盖失败证据", "")
                .replace("RELEASE_CHECKLIST.md", "")
                .replace("不得提交 App Store Connect", "")
            )
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", plan)
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", template)
            write(root / "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md", execution_sheet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceFailureTriageTemplatePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceFailureTriageTemplatePresent"]["evidence"]
            self.assertIn("## 失败复测与阻断清单", evidence)
            self.assertIn("失败证据", evidence)
            self.assertIn("复测证据", evidence)
            self.assertIn("RELEASE_CHECKLIST.md", evidence)
            self.assertIn("不得提交 App Store Connect", evidence)

    def test_real_device_execution_sheet_must_align_rd_numbering(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            broken_sheet = complete_execution_sheet()
            broken_sheet = broken_sheet.replace(
                "| RD-02 创建宝宝档案 | `RealDevice/RD-02-baby-profile.png` | 使用虚构宝宝资料 |",
                "| RD-02 手机号登录 | `RealDevice/RD-02-phone-login.png` | 手机号和验证码脱敏 |",
            )
            broken_sheet = broken_sheet.replace(
                "| RD-13 手机号登录 | `RealDevice/RD-13-phone-login.png` | 完整手机号和验证码脱敏 |",
                "| RD-13 云恢复 | `RealDevice/RD-13-cloud-restore.png` | token 脱敏 |",
            )
            write(root / "Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md", broken_sheet)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("realDeviceExecutionSheetAlignedWithRegressionTemplate", report["failedRequiredChecks"])
            evidence = report["checks"]["realDeviceExecutionSheetAlignedWithRegressionTemplate"]["evidence"]
            self.assertIn("RD-02", evidence)
            self.assertIn("RD-02 创建宝宝档案", evidence)
            self.assertIn("RealDevice/RD-02-baby-profile.png", evidence)
            self.assertIn("RD-13", evidence)
            self.assertIn("RealDevice/RD-13-phone-login.png", evidence)

    def test_same_day_regression_execution_order_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_complete_fixture(root)
            plan = complete_plan().replace("## 上线当天执行顺序", "## 执行顺序").replace("07-sms-provider.png", "")
            template = complete_template().replace("## 上线当天执行顺序", "## 执行顺序").replace("07-sms-provider.png", "")
            write(root / "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md", plan)
            write(root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md", template)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("sameDayRegressionExecutionOrderPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["sameDayRegressionExecutionOrderPresent"]["evidence"]
            self.assertIn("## 上线当天执行顺序", evidence)
            self.assertIn("07-sms-provider.png", evidence)

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
                root / "Backend/proof/app-store-evidence-20260630T-current.json",
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
