# EVENT_TAXONOMY.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：第一方合规埋点已批准
- 日期：2026-06-24
- 当前结论：允许第一方、服务端白名单、聚合展示的行为埋点；仍禁止第三方分析 SDK、广告归因、用户画像和内容分析

## 已确认事实

1. 第一版需要真实账号、备份恢复、照片原图云备份和删除闭环。
2. 后续商业化需要知道核心路径是否跑通，但不能采集宝宝内容。
3. 当前实现使用 `POST /v1/analytics/events` 写入自有后端，不接入第三方分析 SDK。
4. 事件只保存 HMAC 后的账号哈希、事件名、时间和白名单属性。
5. 后台只展示聚合指标，不提供单用户事件明细查询。

## 已批准事件

| 事件 | 用途 | 允许属性 |
|---|---|---|
| `app_opened` | 活跃趋势 | `source`, `platform` |
| `onboarding_completed` | 新手引导完成率 | `source`, `platform` |
| `account_created` | 账号创建漏斗 | `authProvider`, `source`, `feature`, `platform` |
| `login_completed` | 登录方式漏斗 | `authProvider`, `source`, `feature`, `platform` |
| `cloud_backup_enabled` | 云备份开启率 | `source`, `feature`, `platform` |
| `cloud_backup_completed` | 备份成功路径 | `source`, `result`, `feature`, `platform` |
| `cloud_restore_completed` | 恢复成功路径 | `source`, `result`, `feature`, `platform` |
| `photo_added` | 照片功能采用率 | `recordType`, `source`, `result`, `platform` |
| `record_created` | 记录功能采用率 | `recordType`, `source`, `result`, `platform` |
| `reminder_enabled` | 提醒采用率 | `reminderType`, `source`, `result`, `platform` |
| `paywall_viewed` | 未来商业化漏斗 | `source`, `feature`, `productTier`, `platform` |
| `purchase_started` | 未来商业化漏斗 | `source`, `feature`, `productTier`, `platform` |
| `purchase_completed` | 未来商业化漏斗 | `source`, `feature`, `productTier`, `result`, `platform` |

## 属性白名单

| 属性 | 允许值 |
|---|---|
| `screen` | `home`, `record`, `profile`, `album`, `growth`, `backup`, `onboarding`, `paywall` |
| `source` | `app_launch`, `onboarding`, `profile`, `record`, `album`, `growth`, `backup`, `restore`, `system` |
| `recordType` | `feeding`, `sleep`, `diaper`, `growth`, `milestone`, `vaccine`, `photo` |
| `reminderType` | `feeding`, `vaccine` |
| `authProvider` | `recovery_key`, `phone`, `wechat` |
| `result` | `success`, `failure`, `cancelled` |
| `feature` | `cloud_backup`, `cloud_restore`, `photo_backup`, `account`, `reminder`, `commercial` |
| `productTier` | `free`, `premium` |
| `platform` | `ios` |

## 禁止采集

1. 宝宝昵称、真实姓名、出生日期、性别。
2. 照片、照片文件名、EXIF、对象 key、缩略图 URL。
3. 喂养量、睡眠时长、排便详情、身高体重数值。
4. 疫苗名称、接种日期、备注内容。
5. 手机号、微信 openid/unionid、恢复密钥、session token。
6. 定位、通讯录、广告标识、剪贴板、IP、User-Agent、设备指纹。
7. 任何能反推单个宝宝生活细节的自由文本或数值。

## 服务端门禁

1. 只接受 `Backend/api/server.py` 中的事件名白名单。
2. 只接受属性白名单和固定枚举值。
3. 出现敏感字段名或未知属性时，整条事件丢弃。
4. 单次最多 50 条事件，请求体最多 64 KB。
5. 默认留存 180 天，环境变量 `XNP_ANALYTICS_RETENTION_DAYS` 最长不得超过 365 天。
6. 删除账号时同步删除该账号 HMAC 关联的埋点事件。

## 新增事件流程

1. 先更新本文件和 `PRIVACY_SAFE_TRACKING.md`。
2. 确认不需要新增敏感属性。
3. 更新服务端白名单和测试。
4. 更新 App Store Privacy Label、隐私政策和 SDK 数据清单。
5. 部署后用 `Backend/scripts/verify_remote_api.py` 留存远端证据。
