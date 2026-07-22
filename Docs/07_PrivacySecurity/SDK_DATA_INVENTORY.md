# SDK_DATA_INVENTORY.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：SDK 与数据清单实现更新
- 日期：2026-06-14
- 当前结论：第一版已采用恢复密钥账号、自有 API 云同步，并新增手机号登录、阿里云短信 webhook adapter、微信登录和第一方合规埋点；服务端已支持短信 webhook、微信 code exchange 和白名单行为事件，iOS 微信 OpenSDK 依赖已接入，真实微信 AppID / URL Scheme / Universal Link 后台绑定 / AppSecret、阿里云短信签名/模板/RAM 密钥和区域仍需上线前确认；仍默认不接入第三方分析/广告 SDK

## 已确认事实

1. 第一版只做 iOS 原生 App。
2. 第一版不做广告和商业化。
3. 第一版需要账号、同步恢复和照片原图云同步。
4. 产品涉及儿童、照片、家庭和成长记录。
5. 崩溃上报进入第一版。
6. 崩溃上报使用 Apple 原生渠道。
7. 第一方合规埋点通过自有后端完成，不接入第三方分析 SDK。

## 合理推断

1. 优先使用 Apple 原生框架。
2. 账号当前采用恢复密钥、手机号和微信登录组合；暂不接入 Sign in with Apple。
3. 云端照片原图通过自有 API 上传，不建议客户端直连云厂商 SDK。
4. 崩溃上报使用 Apple 原生 App Store Connect / TestFlight 崩溃报告；不接入第三方崩溃 SDK。
5. 合规埋点只应记录白名单行为枚举，不记录宝宝内容、照片、手机号、微信标识或定位。

## 待我确认的问题

1. 付费 Apple Developer 账号开通时间。
2. TestFlight / App Store Connect 真实崩溃样本脱敏归档方式。
3. 生产服务器和对象存储区域。

## 不进入第一版的功能

1. 广告 SDK。
2. 归因 SDK。
3. 第三方分析 SDK。
4. 热力图 SDK。
5. 第三方云相册 SDK。

## SDK 表

| SDK / Framework | 用途 | 收集数据 | 是否追踪 | 是否含广告 | 是否发往境外 | 结论 |
|---|---|---|---|---|---|---|
| SwiftUI | UI | 无 | 否 | 否 | 否 | 可用 |
| SwiftData/Core Data | 本地存储 | 本地业务数据 | 否 | 否 | 否 | 待技术选择 |
| PhotosUI | 用户主动选照片 | 用户选择的照片 | 否 | 否 | 否 | 可用，需权限说明 |
| UserNotifications | 本地提醒 | 通知授权状态 | 否 | 否 | 否 | 可用，需触发时说明 |
| AuthenticationServices | Sign in with Apple | Apple 用户标识，如未来采用 | 否 | 否 | 取决于 Apple 服务 | 当前不接入 |
| Keychain | token 存储 | 登录凭证 | 否 | 否 | 否 | 已接入 |
| 自有后端 API | 同步恢复、照片上传 | 账号、记录、照片原图 | 否 | 否 | 取决于服务器区域 | 已接入 |
| 自有后端合规埋点 | 聚合产品分析 | HMAC 账号哈希、事件名、时间、白名单枚举属性 | 否 | 否 | 取决于服务器区域 | 已接入；无第三方 SDK |
| 短信服务商 SDK/API | 手机号验证码 | 手机号、验证码发送状态 | 否 | 否 | 待服务商和区域确认 | 已新增阿里云 Dysmsapi webhook adapter；正式签名、模板、RAM 密钥待私有配置，`auth-providers` 会阻断未配置后端 |
| 微信 OpenSDK / 微信开放平台 | 微信登录 | 微信授权 code、openid/unionid | 否 | 否 | 取决于微信服务 | 服务端支持 code exchange；iOS OpenSDK 依赖和授权桥已接入，真实微信 AppID / URL Scheme / Universal Link 后台绑定 / AppSecret 待私有配置，`auth-providers` 和 `ios-release-readiness` 会分别阻断未配置后端和客户端 |
| 对象存储 SDK | 对象存储 | 照片原图 | 否 | 否 | 取决于区域 | 默认不直接接入客户端，优先自有 API |
| Apple crash reports | 崩溃上报 | 崩溃诊断、设备/系统信息 | 否 | 否 | 取决于 Apple 服务 | 第一版使用；代码层 proof 见 `diagnostics-redaction` |
| 第三方崩溃 SDK | 崩溃上报 | 崩溃诊断、设备/系统信息 | 否 | 否 | 待定 | 第一版禁用；`diagnostics-redaction` 会阻断常见第三方 crash/analytics SDK 标记 |
| 第三方分析 SDK | 埋点 | 可能收集设备和行为 | 待定 | 待定 | 待定 | 第一版禁用，已由自有后端白名单埋点替代 |
| 广告 SDK | 广告 | 设备/追踪数据 | 是 | 是 | 待定 | 禁用 |

## iOS Privacy Manifest

1. 当前文件：`App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy`。
2. 当前声明：不使用 tracking，tracking domains 为空。
3. 当前覆盖：`UserID`、`PhoneNumber`、`OtherUserContent`、`PhotosorVideos`、`Health`、`ProductInteraction`、`CrashData`、`PerformanceData`。
4. 当前 required-reason API：`NSPrivacyAccessedAPITypes` 为空数组；如后续引入 UserDefaults、文件时间戳、磁盘空间、系统启动时间或键盘状态相关 required-reason API，必须先更新该文件和 `Backend/scripts/check_ios_release_readiness.py`。

## 数据类型表

| 数据 | 用途 | 是否必要 | 是否敏感 | 是否上传 | 是否用于分析 | 删除方式 |
|---|---|---:|---:|---|---:|---|
| 账号标识 | 登录和恢复 | 是 | 是 | 是 | 否 | 删除账号 |
| 手机号 | 手机号登录 | 是，如启用手机号登录 | 是 | 是 | 否 | 删除账号 |
| 微信账号标识 | 微信登录 | 是，如启用微信登录 | 是 | 是 | 否 | 删除账号 |
| 宝宝昵称 | 档案展示 | 是 | 是 | 是 | 否 | 删除档案/账号 |
| 出生日期 | 年龄/纪念日 | 是 | 是 | 是 | 否 | 删除档案/账号 |
| 宝宝照片原图 | 时间线和同步 | 是 | 是 | 是 | 否 | 删除照片/账号 |
| 喂养/睡眠/排便 | 日常记录 | 是 | 是 | 是 | 否 | 删除记录/账号 |
| 喝奶闹钟 | 本机提醒 | 否 | 是 | 否 | 否 | 取消闹钟/删除档案 |
| 身高体重 | 成长记录 | 是 | 是 | 是 | 否 | 删除记录/账号 |
| 疫苗提醒 | 提醒 | 是 | 是 | 是 | 否 | 删除提醒/账号 |
| 第一方行为事件 | 聚合产品分析 | 否 | 否，需白名单 | 是 | 是 | 删除账号 |
| 崩溃诊断 | 稳定性修复 | 是 | 否，需脱敏 | 是 | 否 | 按服务保留周期 |

## 禁止事项

1. 不得为了“以后可能有用”采集数据。
2. 不得采集宝宝照片、儿童敏感信息作为分析事件。
3. 不得让 SDK 暗中采集设备信息、剪贴板、定位、通讯录、相册。
4. 不得接入不明来源 SDK。
5. 不得将照片原图传给分析、广告、AI 训练或第三方云相册。
6. 崩溃日志不得包含宝宝内容、照片对象 key、记录明细、token 或密钥。
