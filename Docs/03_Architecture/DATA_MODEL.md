# DATA_MODEL.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：数据模型初版
- 日期：2026-05-28
- 实现状态：未实现；本文只定义模型和约束

## 已确认事实

1. 第一版只做 iOS 原生 App。
2. 数据本地优先。
3. 第一版需要账号。
4. 第一版需要备份恢复。
5. 服务器需要存储宝宝照片原图。
6. 首发地区为香港和美国。
7. 照片可以复制进 App 私有空间。
8. 数据包含儿童、照片、健康/成长、疫苗、家庭记录，均属于高敏感数据。
9. 疫苗提醒模板覆盖国内 + 香港。
10. 崩溃上报进入第一版。
11. 崩溃上报使用 Apple 原生渠道。

## 合理推断

1. 本地存储优先使用 SwiftData 或 Core Data，最终选择需在实现计划中确认。
2. 所有业务对象都应带本地 UUID、创建时间、更新时间、删除状态和同步状态。
3. 第一版单人记录，冲突处理可以保持简单。
4. 月度成长报告优先作为聚合视图生成，不必先保存成独立重数据。

## 待我确认的问题

1. 是否支持多个宝宝档案。
2. 删除是立即硬删除，还是服务器保留短期可恢复窗口。
3. 是否上传照片缩略图。
4. Apple 原生崩溃上报脱敏验证方式。

## 不进入第一版的功能

1. 家庭成员权限模型。
2. 多人协作冲突模型。
3. 社交分享数据模型。
4. 电商、广告、订阅数据模型。

## 通用字段

所有可持久化对象默认包含：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | UUID/String | 本地唯一 ID；如果同步到服务器，也作为客户端对象 ID |
| babyId | UUID/String | 所属宝宝档案 ID，BabyProfile 自身除外 |
| createdAt | Date | 本地创建时间 |
| updatedAt | Date | 本地最后更新时间 |
| deletedAt | Date? | 软删除时间；是否最终硬删除见删除策略 |
| syncStatus | Enum | notSynced / pending / synced / failed / localOnly |
| serverId | String? | 后端对象 ID，只有启用服务器存储后存在 |

## 数据对象

| 对象 | 说明 | 是否敏感 | 是否同步 | 是否可删除 |
|---|---|---|---|---|
| Account | 用户账号身份 | 是 | 是 | 是 |
| BabyProfile | 宝宝档案 | 是 | 是 | 是 |
| FeedingRecord | 喂养记录 | 是 | 是 | 是 |
| SleepRecord | 睡眠记录 | 是 | 是 | 是 |
| DiaperRecord | 排便记录 | 是 | 是 | 是 |
| GrowthMeasurement | 身高体重记录 | 是 | 是 | 是 |
| BabyPhoto | App 内照片资产、元数据和云端原图关系 | 高敏感 | 是，含原图 | 是 |
| VaccineReminder | 疫苗提醒 | 高敏感 | 是 | 是 |
| VaccineTemplate | 国内/香港疫苗模板 | 是 | 可随 App 或服务端配置 | 可更新 |
| CrashReportPolicy | Apple 原生崩溃上报策略 | 否 | 通过 Apple 原生渠道 | 可调整 |
| Milestone | 纪念日 | 是 | 不需要同步；可由生日计算 | 随档案删除 |
| MonthlyReport | 月度报告聚合结果 | 是 | 默认不同步；由本地数据生成 | 可重新生成 |
| AppPrivacySetting | 隐私和同步偏好 | 是 | 默认本地；必要时同步最小状态 | 是 |

### Account

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 本地账号记录 ID |
| provider | Enum | 是 | currentDevAccount / signInWithApple / email，正式上架前需确认 |
| providerUserId | String | 是 | 第三方或自有账号用户 ID |
| createdAt | Date | 是 | 创建时间 |
| deletedAt | Date? | 否 | 删除时间 |

## 字段定义

### BabyProfile

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 宝宝档案 ID |
| nickname | String | 是 | 宝宝昵称；不强制真实姓名 |
| birthDate | Date | 是 | 出生日期，用于纪念日和年龄计算 |
| sex | Enum? | 否 | female / male / unspecified |
| avatarPhotoId | UUID/String? | 否 | 头像照片 ID |
| notes | String? | 否 | 备注 |

### FeedingRecord

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 记录 ID |
| babyId | UUID/String | 是 | 所属宝宝 |
| occurredAt | Date | 是 | 喂养时间，默认当前时间 |
| type | Enum | 是 | breast / bottle / formula / solidFood |
| amountMl | Decimal? | 否 | 瓶喂/配方奶数量 |
| durationMinutes | Int? | 否 | 母乳或喂养时长 |
| note | String? | 否 | 备注 |

### SleepRecord

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 记录 ID |
| babyId | UUID/String | 是 | 所属宝宝 |
| startAt | Date | 是 | 开始时间 |
| endAt | Date? | 否 | 结束时间；为空表示进行中 |
| note | String? | 否 | 备注 |

### DiaperRecord

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 记录 ID |
| babyId | UUID/String | 是 | 所属宝宝 |
| occurredAt | Date | 是 | 发生时间，默认当前时间 |
| color | Enum? | 否 | 颜色，可选 |
| texture | Enum? | 否 | 形态，可选 |
| note | String? | 否 | 备注 |

### GrowthMeasurement

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 记录 ID |
| babyId | UUID/String | 是 | 所属宝宝 |
| measuredAt | Date | 是 | 测量日期 |
| weightKg | Decimal? | 否 | 体重 |
| heightCm | Decimal? | 否 | 身高 |
| note | String? | 否 | 备注 |

规则：身高和体重至少填写一项。

### BabyPhoto

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 照片记录 ID |
| babyId | UUID/String | 是 | 所属宝宝 |
| capturedAt | Date | 是 | 照片日期，可由用户修改 |
| localFileName | String | 是 | App 私有空间内文件名 |
| thumbnailFileName | String? | 否 | 本地缩略图文件名 |
| source | Enum | 是 | camera / photoLibrary |
| note | String? | 否 | 备注 |
| serverAssetId | String? | 是 | 云端照片对象 ID |
| uploadStatus | Enum | 是 | pending / uploaded / failed / deletePending |
| remoteOriginalSizeBytes | Int? | 否 | 云端原图大小 |
| remoteThumbnailAssetId | String? | 否 | 云端缩略图对象 ID，是否上传待确认 |

规则：第一版需要上传用户主动加入 App 的照片原图；不得扫描或自动上传系统相册。

### VaccineReminder

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 提醒 ID |
| babyId | UUID/String | 是 | 所属宝宝 |
| title | String | 是 | 疫苗或事项名称 |
| dueAt | Date | 是 | 提醒日期 |
| completedAt | Date? | 否 | 完成时间 |
| note | String? | 否 | 备注 |
| source | Enum | 是 | manual / template |
| region | Enum? | 否 | mainlandChina / hongKong，用于模板来源 |

规则：模板覆盖国内 + 香港；模板只生成可编辑提醒，不提供医疗建议。

### VaccineTemplate

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| id | UUID/String | 是 | 模板 ID |
| region | Enum | 是 | mainlandChina / hongKong |
| title | String | 是 | 疫苗或事项名称 |
| suggestedAgeDays | Int? | 否 | 建议年龄天数，用于生成提醒 |
| note | String? | 否 | 非医疗建议说明 |
| sourceVersion | String | 是 | 模板版本 |

规则：模板内容需要人工审核，且文案必须避免诊断或强制建议。

### MonthlyReport

月度报告默认由本地数据实时聚合生成，不作为必须持久化对象。

| 字段 | 类型 | 说明 |
|---|---|---|
| babyId | UUID/String | 所属宝宝 |
| month | YearMonth | 报告月份 |
| feedingSummary | Object | 喂养摘要 |
| sleepSummary | Object | 睡眠摘要 |
| diaperSummary | Object | 排便摘要 |
| growthSummary | Object | 身高体重变化 |
| photoIds | [UUID/String] | 当月照片 |
| milestones | [Object] | 当月纪念日 |

## 关系定义

1. BabyProfile 1 - N FeedingRecord。
2. BabyProfile 1 - N SleepRecord。
3. BabyProfile 1 - N DiaperRecord。
4. BabyProfile 1 - N GrowthMeasurement。
5. BabyProfile 1 - N BabyPhoto。
6. BabyProfile 1 - N VaccineReminder。
7. MonthlyReport 由 BabyProfile 及当月记录聚合生成。

## 删除策略

1. 单条记录删除：本地标记 `deletedAt`，如启用服务器存储则加入删除同步队列。
2. 照片删除：删除 BabyPhoto 记录、本地原图和缩略图，并删除服务器原图和缩略图。
3. 宝宝档案删除：二次确认后删除档案及所有关联记录、本地照片和云端照片。
4. 服务器删除：必须提供用户可理解的删除结果；是否保留短期恢复窗口待确认。
5. 账号删除：删除账号、云端记录、云端照片对象和可识别备份数据。

## 迁移策略

1. 所有模型从第一版开始保留 `schemaVersion` 或等价迁移标识。
2. 只允许向后兼容增加可选字段。
3. 删除字段前必须提供迁移和备份方案。
4. 涉及服务器字段变更时，必须同步更新 `SYNC_RULES.md` 和 `PRIVACY_REVIEW.md`。

## 备份策略

1. 本地数据是第一来源。
2. 服务器存储只作为第一方账号备份/恢复能力。
3. 照片原图需要上传服务器对象存储。
4. 必须单独列出容量、压缩/原质量、加密、删除和隐私标签。
