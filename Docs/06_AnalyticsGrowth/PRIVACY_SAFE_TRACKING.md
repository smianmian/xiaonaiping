# PRIVACY_SAFE_TRACKING.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：隐私安全指标策略已批准
- 日期：2026-06-24
- 当前结论：第一版允许自有后端第一方行为埋点；默认不接入第三方分析 SDK、广告 SDK、归因 SDK 或热力图 SDK

## 已确认事实

1. 产品处理儿童、照片、成长记录、疫苗等高敏感家庭数据。
2. 第一版需要账号、备份恢复和照片原图云备份。
3. 后续正规商业化需要留存、转化和核心功能采用率。
4. 已实现第一方 `POST /v1/analytics/events`，只接受白名单事件和枚举属性。
5. 崩溃上报继续使用 Apple 原生渠道。

## 可采集的指标

| 指标 | 是否可采集 | 方式 |
|---|---:|---|
| App 打开趋势 | 是 | `app_opened`，不带设备指纹 |
| 引导完成率 | 是 | `onboarding_completed`，不带宝宝档案 |
| 登录方式完成率 | 是 | `login_completed`，只带 `authProvider` 枚举 |
| 账号创建率 | 是 | `account_created`，只带登录方式枚举 |
| 云备份成功率 | 是 | `cloud_backup_completed`，不带备份内容 |
| 云恢复成功率 | 是 | `cloud_restore_completed`，不带恢复内容 |
| 记录功能采用率 | 是 | `record_created`，只带 `recordType` 枚举 |
| 照片功能采用率 | 是 | `photo_added`，不带照片、文件名或对象 key |
| 提醒采用率 | 是 | `reminder_enabled`，只带提醒类别 |
| 未来付费漏斗 | 可预留 | `paywall_viewed`, `purchase_started`, `purchase_completed`，不上价格、订单号或支付凭证 |

## 禁止采集

1. 宝宝昵称、真实姓名、出生日期、性别。
2. 照片、照片文件名、照片 EXIF、对象 key。
3. 喂养量、睡眠时长、排便内容、身高体重数值。
4. 疫苗名称、接种日期、备注内容。
5. 手机号、微信 openid/unionid、恢复密钥、session token。
6. 联系人、定位、剪贴板、广告标识、设备指纹。
7. IP、User-Agent 或可用于跨站追踪的客户端标识。

## 技术边界

1. 客户端只在已有登录会话时上报，事件失败不得影响记录、登录、备份或恢复。
2. 服务端用 `XNP_SECRET_KEY` 对账号 ID 做 HMAC，埋点表不保存原始 `account_id`。
3. 服务端不接受自由文本属性，不接受未知字段。
4. 管理后台只展示聚合计数、活跃账号哈希数和 Top 事件。
5. 默认留存 180 天，最长 365 天。
6. 用户删除云端账号时同步删除其埋点事件。

## 合规动作

1. 隐私政策必须披露第一方产品使用数据用于产品分析和服务改进。
2. App Store Privacy Label 必须增加 Usage Data / Product Interaction，目的为 Analytics，不用于 Tracking。
3. `SDK_DATA_INVENTORY.md` 必须保持“无第三方分析 SDK”且列出自有后端第一方埋点。
4. 每次新增事件必须更新 `EVENT_TAXONOMY.md`、测试和远端验证证据。
5. 若未来接入 IAP，只能在 App Store 规则内记录漏斗事件，不上传订单号、支付凭证或价格歧视字段。

## 当前结论

可以上线第一方合规埋点基础设施，用于聚合运营分析和后续商业化漏斗准备；仍不允许第三方分析、广告、归因、画像或内容分析。
