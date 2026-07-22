# 小奶瓶 App Store Privacy 逐项答案表

日期：2026-07-04

状态：用于 App Store Connect 的 App Privacy 填写。机器源文件仍是 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json`；本表把 JSON 翻译成可人工逐项核对的页面答案。提交前必须与实际 App 行为、隐私政策、SDK 清单、Privacy Manifest 和生产 proof 重新核对。

## 官方核对入口

1. App privacy details：https://developer.apple.com/app-store/app-privacy-details/
2. Manage app privacy：https://developer.apple.com/help/app-store-connect/manage-app-privacy/overview-of-app-privacy-details/

## 全局答案

| App Store Connect 问题 | 当前答案 | 依据 |
|---|---|---|
| Data Used to Track You | No | 第一版无第三方广告、无第三方分析 SDK、不使用广告标识或跨 App / 网站追踪 |
| Tracking Domains | None | `PrivacyInfo.xcprivacy` 中 tracking disabled，tracking domains 为空 |
| Third-Party Advertising | No | 第一版无广告 |
| Third-Party Analytics | No | 第一版只使用自有后端第一方白名单事件 |
| Kids Category | No | 面向父母和照护者，不面向儿童直接使用 |
| Privacy Policy URL | `https://api.mewpow.com/xiaonaiping/privacy` | 与 App Store Connect 填表版和公开页面一致 |

## Data Linked to You

| 数据类别 | 收集 | 关联身份 | 用于追踪 | 用途 | 项目内数据 |
|---|---|---|---|---|---|
| Identifiers | Yes | Yes | No | App Functionality | 账号 ID、session token、微信 openid/unionid hash |
| Contact Info | Yes | Yes | No | App Functionality | 手机号验证码登录；真实短信服务商和区域提交前复核 |
| User Content | Yes | Yes | No | App Functionality | 宝宝档案、备注、喂养、睡眠、排便、成长、疫苗提醒、照片元数据 |
| Photos or Videos | Yes | Yes | No | App Functionality | 用户主动加入 App 的照片原图，仅用于私有账号同步 |
| Health and Fitness | Yes | Yes | No | App Functionality | 用户主动输入的喂养、睡眠、成长、疫苗提醒记录 |
| Usage Data | Yes | Yes | No | Analytics | 第一方产品交互事件，例如账号创建、登录、同步、恢复、记录类型和提醒类型 |

## Data Not Linked to You

| 数据类别 | 收集 | 关联身份 | 用于追踪 | 用途 | 项目内数据 |
|---|---|---|---|---|---|
| Diagnostics | Yes | No | No | App Functionality, Analytics | Apple crash reports、设备和 OS 诊断；最终 payload 仍需 TestFlight / App Store Connect 真实样本复核 |

## Not Collected

当前不收集以下类别：

1. Location
2. Contacts
3. Search History
4. Browsing History
5. Purchases
6. Financial Info
7. Sensitive Info for tracking
8. Advertising Data

## Health and Fitness 边界

App Store Connect 中如果按 Health and Fitness 填写，必须保持以下解释口径：

1. 数据来自用户主动输入的宝宝照护记录。
2. 不接入 HealthKit、传感器、医院系统或第三方健康数据源。
3. 不做 stress detection、medical interpretation、health advice、pressure reminders、feeding advice 或 medical diagnosis。
4. 疫苗模板只用于记录和提醒，不提供专业疫苗建议。
5. 灵动岛、锁屏 Live Activity 和小组件只做 status display only，不生成健康建议、压力提醒、喂养建议或医疗判断。
6. 喝奶提醒的手动顺延只改变下一次提醒时间，不根据奶量、月龄、传感器或健康数据自动推算喂养时间。

## Usage Data 边界

第一方产品交互事件只允许白名单枚举，不包含：

1. baby content
2. photos
3. photo keys
4. phone numbers
5. WeChat identifiers
6. location
7. advertising ID
8. device fingerprint

## 提交前重检

1. 若新增 SDK、广告、第三方分析、IAP、分享、社区、AI 建议、HealthKit、传感器、医院数据、崩溃上报方案或账号方式，必须重做本表和 `APP_STORE_PRIVACY_LABEL.json`。
2. 提交前复跑 `check_ios_release_readiness.py`，确认 `PrivacyInfo.xcprivacy` 与 App Store Privacy label 不漏不多。
3. 提交前复跑 `check_diagnostics_redaction.py`，确认诊断和日志不含宝宝内容、照片对象 key、手机号明文或 token。
4. 提交前归档 `Docs/08_Release/AppStoreEvidence/04-privacy-label.png`，证明 App Store Connect 已按本表填写；截图需遮账号邮箱。
