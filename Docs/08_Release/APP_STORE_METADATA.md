# APP_STORE_METADATA.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：中国大陆 App Store 元数据草案补齐
- 日期：2026-06-18
- 公司主体：深圳市闪现生活科技有限公司

## 已确认事实

1. 项目暂名：小奶瓶 / 宝宝成长记录。
2. 第一版免费。
3. 第一版不做医疗诊断。
4. 产品面向父母/照护者，不面向儿童直接使用。
5. 当前首发地区改为中国大陆，香港第二批。
6. 第一版需要账号、备份恢复和照片原图云备份。
7. 疫苗模板覆盖中国大陆 + 香港，并可在 App 内切换模板地区。
8. 崩溃上报进入第一版。
9. App 内语言跟随 iOS 系统；已加入 `zh-Hant-HK` 繁体中文香港资源，不做 App 内语言切换器。

## 合理推断

1. 元数据应该强调记录、回看、纪念册感，不应暗示医疗能力。
2. 截图应展示本地优先和隐私可信任，但不暴露真实宝宝照片。
3. 中国大陆使用简体中文主版本；香港第二批使用繁中版本。
4. 疫苗提醒文案必须避免医疗建议。

## 待我确认的问题

1. App Store 最终名称是否为“小奶瓶”。
2. 副标题。
3. 类别。
4. 中国大陆简体中文元数据和审核截图是否已最终校对。
5. 香港第二批繁中 App 内高频文案是否已人工校对。
6. 付费 Apple Developer 账号开通时间。
7. 隐私政策正式托管 URL。
8. Support URL。
9. API 正式域名。

## 不进入第一版的功能

1. 订阅文案。
2. 医疗疗效宣传。
3. AI 诊断宣传。
4. 社区宣传。

## 元数据草案原则

1. 不使用真实宝宝照片作为公开素材，除非有明确授权。
2. 不写“健康诊断”“疫苗建议”“医学判断”。
3. 不承诺治疗、预测或专业医疗效果。
4. 强调私密、温柔、低负担、本地优先、可备份恢复。
5. 清楚说明照片原图备份是用户账号下的私有备份。
6. 疫苗提醒只表达为记录和提醒工具，不表达为接种建议或医疗判断。

## Review Notes 要点

1. App 用于父母记录宝宝成长。
2. 第一版免费，无 IAP。
3. 不提供医疗诊断。
4. 数据本地优先，同时支持账号备份恢复。
5. 账号支持恢复密钥、手机号和微信登录，不采集邮箱。
6. 生产提交前必须配置真实短信服务和微信开放平台。
7. 用户主动加入 App 的宝宝照片原图会用于私有云备份。
8. 审核可在资料页 -> 账号与备份中创建账号并备份。
9. 删除路径：资料页 -> 账号与备份 -> 删除云端账号与备份。
10. 说明崩溃上报只用于稳定性修复，不包含宝宝内容。

## App Store 填写草案，简体中文

| 字段 | 草案 |
|---|---|
| App 名称 | 小奶瓶 |
| 副标题 | 温柔记录宝宝每一天 |
| Bundle ID | `com.mewpow.xiaonaiping` |
| 分类 | 生活；第二分类留空，避免被误判为医疗/健康建议 App |
| 年龄分级 | 面向父母和照护者，不面向儿童直接使用；不含社交、UGC 或成人内容 |
| 关键词 | 宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册 |
| 宣传文本 | 用低负担的方式记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片。 |
| 描述 | 小奶瓶是一款为新手父母和照护者设计的宝宝成长记录 App。你可以快速记录喂养、睡眠、排便、身高体重、疫苗提醒和成长瞬间，也可以把宝宝照片整理在私密时间线里。数据默认本地优先保存；开启账号与备份后，可通过恢复密钥、手机号或微信登录私有账号，并将记录和主动加入 App 的照片原图备份到账号空间，便于换机恢复。小奶瓶不提供医疗诊断或治疗建议，疫苗模板仅用于记录和提醒，实际接种安排请以医生和当地官方信息为准。 |
| 新版本说明 | 第一版：宝宝档案、日常记录、成长记录、疫苗提醒、照片时间线、手机号/微信/恢复密钥账号备份恢复和云端账号删除。 |

## App Store 填寫草案，繁體中文（香港）

| 欄位 | 草案 |
|---|---|
| App 名稱 | 小奶瓶 |
| 副標題 | 溫柔記錄寶寶每一天 |
| Bundle ID | `com.mewpow.xiaonaiping` |
| 分類 | 生活；第二分類留空，避免被誤判為醫療/健康建議 App |
| 年齡分級 | 面向父母和照護者，不面向兒童直接使用；不含社交、UGC 或成人內容 |
| 關鍵字 | 寶寶記錄,育兒,餵奶,睡眠,尿布,成長記錄,疫苗提醒,相簿 |
| 宣傳文字 | 用低負擔的方式記錄餵養、睡眠、排便、成長、疫苗提醒和珍貴照片。 |
| 描述 | 小奶瓶是一款為新手父母和照護者設計的寶寶成長記錄 App。你可以快速記錄餵養、睡眠、排便、身高體重、疫苗提醒和成長瞬間，也可以把寶寶照片整理在私密時間線裡。資料預設本機優先保存；開啟帳號與備份後，可透過恢復密鑰、手機號碼或微信登入私有帳號，並將記錄和主動加入 App 的照片原圖備份到帳號空間，方便換機恢復。小奶瓶不提供醫療診斷或治療建議，疫苗模板僅用於記錄和提醒，實際接種安排請以醫生和當地官方資訊為準。 |
| 新版本說明 | 第一版：寶寶檔案、日常記錄、成長記錄、疫苗提醒、照片時間線、手機號碼/微信/恢復密鑰帳號備份恢復和雲端帳號刪除。 |

## App Store Draft, English

| Field | Draft |
|---|---|
| App Name | Xiao Nai Ping |
| Subtitle | Gentle baby daily log |
| Bundle ID | `com.mewpow.xiaonaiping` |
| Category | Lifestyle; leave the secondary category blank |
| Keywords | baby tracker,parenting,feeding,sleep,diaper,growth,vaccine,album |
| Promotional Text | A calm way to record feeding, sleep, diapers, growth, reminders, and baby moments. |
| Description | Xiao Nai Ping is a gentle baby journal for parents and caregivers. Record feeding, sleep, diapers, height, weight, vaccine reminders, and memorable photos in a low-pressure daily flow. Your data is local-first. When you sign in with a recovery key, phone number, or WeChat and turn on backup, your baby records and photos that you add to the app can be backed up privately for device recovery. Xiao Nai Ping does not provide medical diagnosis, treatment advice, or professional vaccine guidance. Vaccine templates are only for record keeping and reminders; please follow your doctor and local public health guidance. |
| What’s New | First release: baby profile, daily logs, growth records, vaccine reminders, photo timeline, phone/WeChat/recovery-key backup and restore, and cloud account deletion. |

## URL 草案

当前公网过渡 API 路径：

| URL | 草案 |
|---|---|
| Privacy Policy URL | `https://api.mewpow.com/xiaonaiping/privacy` |
| Terms URL | `https://api.mewpow.com/xiaonaiping/terms` |
| Support URL | `https://api.mewpow.com/xiaonaiping/support` |

后端已提供匿名访问页面：`/privacy`、`/terms`、`/support`。

## App Store Privacy Label 草案

| 数据类别 | 是否采集 | 用途 | 与用户身份关联 | 追踪 |
|---|---:|---|---:|---:|
| Identifiers | 是 | 账号、备份恢复 | 是 | 否 |
| Contact Info | 是 | 手机号登录验证码 | 是 | 否 |
| User Content | 是 | 记录、备注、照片元数据、照片原图备份 | 是 | 否 |
| Photos or Videos | 是 | 用户主动加入 App 的宝宝照片原图备份 | 是 | 否 |
| Health and Fitness | 是 | 喂养、睡眠、成长、疫苗提醒记录 | 是 | 否 |
| Usage Data | 是 | 第一方产品交互事件，用于聚合分析 | 是 | 否 |
| Diagnostics | 是 | Apple 原生崩溃诊断 | 否，需最终验证 | 否 |
| Location | 否 | 不使用 | 否 | 否 |
| Contacts | 否 | 不使用 | 否 | 否 |
| Purchases | 否 | 第一版免费无 IAP | 否 | 否 |

## 审核说明草案

小奶瓶用于父母或照护者记录宝宝成长。第一版免费，无 IAP，无广告，无第三方分析 SDK，不提供医疗诊断、治疗建议或专业疫苗建议，不是医疗器械，也不作为医疗器械使用。产品交互分析只使用自有后端第一方白名单事件，不采集宝宝内容、照片、照片 key、手机号、微信标识、定位、广告标识或设备指纹。

数据默认本地优先保存。用户可以在“资料 -> 账号与备份”中使用恢复密钥、手机号或微信登录并主动备份。备份会上传宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。手机号和微信登录仅用于账号识别和恢复。

账号删除路径为：“资料 -> 账号与备份 -> 删除云端账号与备份”。该操作会删除账号、云端 JSON 备份和云端照片原图，本机资料默认保留，用户可以另行清空本地记录或删除宝宝档案。

疫苗模板仅用于记录和提醒，App 内文案不构成医疗建议。

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。

审核测试登录请优先使用 App Review Information 中提供的恢复密钥测试账号。手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充；正式提交包不得提供或依赖 debug code。

## 中国大陆首批提交设置

| 项目 | 设置 |
|---|---|
| Availability | Specific Countries or Regions -> China mainland |
| Primary localization | Simplified Chinese |
| Secondary localization | Traditional Chinese (Hong Kong) for the second launch batch |
| Price | Free |
| Category recommendation | Lifestyle |
| Not selected | Hong Kong, United States, and all other regions for the first submission |

注：中国大陆提交前必须完成适用备案、生产后端和 App Store Connect 合规信息。已安装用户在 App 内不按所在地封锁功能，可切换中国大陆 / 香港疫苗提醒模板。
