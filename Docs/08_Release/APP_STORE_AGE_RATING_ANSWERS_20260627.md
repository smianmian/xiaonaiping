# 小奶瓶 App Store 年龄分级与医疗器械答案表

日期：2026-06-27

状态：用于 App Store Connect 年龄分级问卷、Kids 类目选择和受监管医疗器械声明的填表依据；不可替代 App Store Connect 最终自动计算结果。提交前如功能、地区、隐私标签、审核备注或医疗/健康相关文案变化，必须重新复核。

## 官方核对入口

1. App Store Connect 年龄分级：https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating
2. 受监管医疗器械声明：https://developer.apple.com/help/app-store-connect/manage-app-information/declare-regulated-medical-device-status
3. Kids Category 审核指南：https://developer.apple.com/app-store/review/guidelines/#kids-category

## 产品事实边界

1. 小奶瓶面向父母和照护者，不面向儿童直接使用。
2. 第一版免费，无 IAP、订阅、广告、第三方广告 SDK 或第三方分析 SDK。
3. 第一版没有公开 UGC、社区、聊天、社交匹配、公开分享、用户搜索、私信或陌生人互动。
4. 第一版没有赌博、抽奖、真钱交易、loot box、成人内容、暴力内容、恐怖内容、烟酒毒品内容或粗俗语言；填表口径为无成人内容。
5. 第一版不接入 HealthKit、传感器、医院系统或第三方健康数据源。
6. 用户可以主动记录喂养、睡眠、排便、身高体重、疫苗提醒、里程碑、备注和照片。
7. 疫苗模板仅用于记录和提醒，不提供专业疫苗建议。
8. 保存新喂养时，用户可以手动顺延下一次提醒；小奶瓶不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。

## App Store Connect 年龄分级问卷口径

| 项目 | 填写口径 |
|---|---|
| 预期年龄分级 | 预期为 `4+`，最终以 App Store Connect 问卷自动计算结果为准 |
| Age Categories and Override | 选择 `Not Applicable`，不主动提高分级，除非 App Store Connect 计算结果、EULA 或法务复核要求更高分级 |
| Made for Kids / Kids Category | 不选择；小奶瓶不是为儿童直接使用设计的 App，元数据也不得写成儿童直接使用 |
| Web access | 无内置开放网页浏览器；仅使用隐私政策、用户协议、支持页等固定 HTTPS 页面 |
| User-generated public content | 无公开 UGC、公开评论、社区、陌生人内容浏览或公开发布 |
| Messaging / chat | 无聊天、私信、陌生人互动或社交匹配 |
| Purchases | 无 IAP、订阅、付费会员或真钱交易 |
| Advertising / tracking | 无广告、无第三方广告 SDK、无第三方分析 SDK、不用于追踪 |
| Gambling / contests | 无赌博、抽奖、竞赛、loot box 或真钱奖励 |
| Mature or objectionable content | 无成人、暴力、恐怖、烟酒毒品、粗俗语言等内容 |
| Health-related records | 如问卷或审核备注涉及健康相关内容，如实说明存在用户主动输入的宝宝照护记录，但它们只用于记录和提醒 |
| Medical advice | 不提供诊断、治疗、疾病预测、健康建议、压力评估、心理健康判断、专业疫苗建议或喂养建议 |

## 受监管医疗器械声明口径

| 项目 | 填写口径 |
|---|---|
| Regulated Medical Device | `No` |
| 解释 | 小奶瓶 is not a medical device. It does not provide diagnosis, prevention, monitoring, treatment, disease prediction, physiological-condition measurement, or professional medical advice. |
| 外部监管状态 | 无 FDA cleared / approved、无 FDA medical device database registration、无 CE mark、无 UKCA mark、无 EU MDR / MDD self-certification、无 UK medical-device self-certification |
| 硬件/传感器 | 不连接医疗器械硬件，不使用设备传感器生成健康测量 |
| 数据来源 | 数据来自用户主动输入或主动加入 App 的本机记录和照片，不来自 HealthKit、传感器、医院系统或第三方健康数据源 |

## 提交前重检项

1. 如新增 IAP、广告、社区、公开分享、聊天、网页浏览、AI 建议、健康评分、压力提醒、自动喂养推算、传感器、HealthKit、医院数据或第三方 SDK，必须重做年龄分级问卷口径。
2. 如 App Store Connect 最终计算结果不是 `4+`，以 App Store Connect 结果为准，并同步 `APP_STORE_METADATA.md`、`APP_STORE_SUBMISSION_PACKET.md`、`APP_STORE_CONNECT_COPY_PASTE_20260627.md` 和 Review Notes。
3. 如选择 Kids Category，必须先重新评估儿童隐私、外链、广告、分析、家长门和后续版本约束；当前第一版口径是不选择。
4. 如任何地区被要求补充医疗器械声明材料，必须停止提交并复核产品功能、法务意见和 Apple 受监管医疗器械入口。
