# 小奶瓶 App Store Connect 填表版

日期：2026-07-03

状态：可用于准备 App Store Connect 草稿，不可直接提交审核。正式提交仍需 `Backend/proof/production-readiness.json` 为 `ready: true`，并补齐微信开放平台、签名归档、TestFlight、中国大陆 APP 备案和人工证据。

素材机器校验：`Backend/proof/app-store-connect-materials.json`，当前 `passed=true`。

版本页、发布方式、出口合规、IDFA 和内容权利填写见 `Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260703.md`。

结构化草稿总览见 `Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260703.json`，该 JSON 只用于核对草稿字段，不代表可提交审核。

人工填写当天执行包见 `Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260703.json`，该包只约束填写顺序、停机条件、页面证据和复跑命令，不代表 App Store Connect 已填写或可提交审核。

最终人工粘贴、同轮 build / 证据截图核对见 `Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260703.md`。

## App 信息

| 字段 | 填写内容 |
| --- | --- |
| App 名称 | 小奶瓶 |
| Bundle ID | `com.mewpow.xiaonaiping` |
| SKU | `xiaonaiping-ios-1` |
| 副标题 | 温柔记录宝宝每一天 |
| 主类别 | 生活 |
| 第二类别 | 留空，推荐不要选择健康健美，降低被误判为医疗/健康建议 App 的风险 |
| 价格 | 免费 |
| 首发地区 | Specific Countries or Regions -> China mainland |
| 第二批地区 | Hong Kong |
| 版权 | `© 2026 深圳市闪现生活科技有限公司` |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` |
| 技术支持 URL | `https://api.mewpow.com/xiaonaiping/support` |
| 用户协议 URL | `https://api.mewpow.com/xiaonaiping/terms` |

## 字段预算

关键词按 UTF-8 bytes 计算；其他字段按 App Store Connect 字符数口径复核。人工粘贴前如果改字，一个字段改完必须重跑 `check_app_store_connect_materials.py`。

| 字段 | 限制 | 当前 | 余量 |
| --- | --- | --- | --- |
| App 名称 | 30 字符 | 3 字符 | 剩余 27 字符 |
| 副标题 | 30 字符 | 9 字符 | 剩余 21 字符 |
| 关键词 | 100 UTF-8 bytes | 73 bytes | 剩余 27 bytes |
| 宣传文本 | 170 字符 | 31 字符 | 剩余 139 字符 |
| 描述 | 4000 字符 | 488 字符 | 剩余 3512 字符 |
| 新版本说明 | 4000 字符 | 58 字符 | 剩余 3942 字符 |
| 审核备注 | 4000 字符 | 887 字符 | 剩余 3113 字符 |

## 关键词

App Store Connect 关键词按 UTF-8 bytes 控制，当前版本保持在 100 bytes 内：

```text
宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册
```

## 宣传文本

```text
用低负担的方式记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片。
```

## 描述

```text
小奶瓶是一款为新手父母和照护者设计的宝宝成长记录 App。你可以快速记录喂养、睡眠、排便、身高体重、疫苗提醒和成长瞬间，也可以把宝宝照片整理在私密时间线里。

数据默认本地优先保存。开启账号与同步后，用户可使用恢复密钥登录私有账号，并将记录和主动加入 App 的照片原图同步到账号空间，便于换机恢复。

主要功能：

- 宝宝档案：记录昵称、生日、性别和成长信息。
- 日常记录：快速记录喂养、睡眠、排便和备注。
- 喝奶提醒：手动设置下一次喝奶提醒或固定间隔；新增喂养后可按 5 分钟一档顺延下一次提醒。
- 成长回看：整理身高、体重和月度变化。
- 疫苗提醒：提供中国大陆和香港模板切换，用于记录和提醒。
- 照片时间线：整理用户主动加入 App 的宝宝照片。
- 账号与同步：使用恢复密钥登录账号，支持云端同步恢复和账号删除。

喝奶提醒仅按你设置的固定间隔和手动顺延重新安排；小奶瓶不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。

小奶瓶不提供医疗诊断、治疗建议或专业疫苗建议。疫苗模板仅用于记录和提醒，实际接种安排请以医生和当地官方信息为准。
```

## 新版本说明

```text
第一版：宝宝档案、日常记录、喝奶提醒与手动顺延、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。
```

## 年龄分级建议

- 不选择 Kids 类目。
- 预期年龄分级：4+，以 App Store Connect 问卷自动计算结果为准。
- 目标用户为父母和照护者，不面向儿童直接使用。
- 不含公开 UGC、社交匹配、成人内容、赌博、广告追踪、购买或订阅。
- 疫苗和成长记录只作为记录与提醒工具，不作为医疗建议。
- 如果问卷涉及医疗/健康信息，如实选择存在健康相关记录，但说明不提供诊断、治疗、疾病预测或专业接种建议。
- 不接入 HealthKit、传感器、医院系统或第三方健康数据源；不提供压力评估、心理健康判断或压力提醒。

## App Privacy 填写来源

以 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` 为最终源文件。人工逐项核对表见 `Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260703.md`。当前摘要：

| 数据类别 | 是否收集 | 是否关联身份 | 是否追踪 | 用途 |
| --- | --- | --- | --- | --- |
| Identifiers | 是 | 是 | 否 | 账号、同步恢复 |
| Contact Info | 是 | 是 | 否 | 手机号验证码登录 |
| User Content | 是 | 是 | 否 | 宝宝档案、备注、记录、照片元数据 |
| Photos or Videos | 是 | 是 | 否 | 用户主动加入 App 的宝宝照片原图同步 |
| Health and Fitness | 是 | 是 | 否 | 喂养、睡眠、成长、疫苗提醒记录 |
| Usage Data | 是 | 是 | 否 | 第一方产品交互分析 |
| Diagnostics | 是 | 否 | 否 | Apple 原生崩溃诊断和稳定性修复 |

## 截图文案

当前候选截图目录：

- `Docs/08_Release/Screenshots/`
- `Docs/08_Release/AppStoreEvidence/10-final-screenshots/`

建议上传顺序和文案：

| 序号 | 截图 | 标题 | 辅助文案 |
| --- | --- | --- | --- |
| 1 | `01-home-iphone16pro.png` | 记录宝宝今天的小变化 | 今日摘要、出生天数和常用记录入口放在一起。 |
| 2 | `02-record-iphone16pro.png` | 半夜也能低负担记录 | 喂养、睡眠、排便等常用记录少点几下完成。 |
| 3 | `03-growth-iphone16pro.png` | 一个月的成长，轻轻回看 | 身高体重和成长变化用温柔的方式整理。 |
| 4 | `04-profile-iphone16pro.png` | 设置、隐私和资料都在这里 | 管理宝宝档案、隐私设置和应用资料。 |
| 5 | `05-profile-sync-iphone16pro.png` | 主动同步，也能主动删除 | 开启账号后可同步恢复，也可删除云端账号与同步。 |

当前 5 张候选图不展示灵动岛/锁屏 Live Activity 或小组件。若后续新增第 6 张截图，建议只展示“喝奶闹钟在锁屏/灵动岛显示下一次提醒”，不得写成健康建议、喂养推荐或医疗判断。

截图禁区：

1. 不使用真实宝宝照片，除非另有明确授权。
2. 不展示真实手机号、恢复密钥、token、账号 ID、对象存储 key 或内部路径。
3. 不展示 `127.0.0.1`、debug code、internal dashboard 或工程文档。
4. 不写医疗诊断、治疗、疫苗建议、医生替代或专业健康结论。
5. 微信登录未完成开放平台配置前，不截图暗示微信登录已经可用。

## App Store Connect 截图上传矩阵

官方规格：https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/ 。App Store Connect 截图上传每个设备槽位为一到十张，格式只能使用 `.jpeg`、`.jpg`、`.png`。当前草稿先用 5 张候选图排顺序；正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图。

| 槽位 | 当前口径 | 上传/证据要求 |
| --- | --- | --- |
| iPhone 6.9" display | 官方可接受竖图尺寸包含 1260 x 2736、1290 x 2796、1320 x 2868 | 最终提交优先补这一槽位；上传后在 `AppStoreConnect/ASC-02-version-information.png` 保留截图上传顺序和选中 build |
| 当前候选图 | 当前候选为 iPhone 17 Pro Max / iPhone 6.9" display / 1320 x 2868 | 只作为 App Store Connect 文案、画面顺序和尺寸候选；不能把 Debug simulator 候选图声称为 TestFlight、签名真机或 App Store Connect 上传最终证据 |
| 候选来源 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json` | 来源必须显示 iOS 26.5、截图 seed data、生产 API URL injection，并注明不是 TestFlight 或签名真机包最终证据 |
| 最终上传来源 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json` | 必须显示 `final-app-store-upload`、`iPhone 6.9" display`、iOS 26.5、`TestFlight` 或 `Xcode 签名真机包`，并列出五张 finalFiles |
| iPad 槽位 | 工程目标为 iPhone only，`TARGETED_DEVICE_FAMILY=1` | 如果 App Store Connect 要求 iPad 截图，先复核工程 target family、Bundle ID capabilities 和 App Store Connect 平台设置，不临时上传拉伸图 |

## 审核备注可粘贴文本

```text
小奶瓶用于父母或照护者记录宝宝成长。第一版免费，无 IAP，无广告，无第三方分析 SDK，不提供医疗诊断、治疗建议或专业疫苗建议，不是医疗器械，也不作为医疗器械使用。

数据默认本地优先保存。用户可以在“资料 -> 账号与同步”中使用恢复密钥登录并主动同步。同步会上传宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。App Review 测试请使用 App Review Information 中提供的恢复密钥测试账号；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充。

账号删除路径为：“资料 -> 账号与同步 -> 删除云端账号与同步”。该操作会删除账号、云端 JSON 同步和云端照片原图。本机资料默认保留，用户可以另行清空本地记录或删除宝宝档案。

疫苗模板仅用于记录和提醒，App 内文案不构成医疗建议。实际接种安排请以医生和当地官方信息为准。

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。

审核测试登录请优先使用 App Review Information 中提供的恢复密钥测试账号。手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充；正式提交包不提供、不依赖 debug code。
```

## 审核测试账号填写说明

- App Review Information 私密字段包：`Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260703.md`。
- App Review Information 中填写恢复密钥测试账号。
- 脱敏证据文件：`Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json`。
- 真机回归与测试账号操作表：`Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`。
- 真实恢复密钥只保存在本地 ignored 文件 `.env.xnp-review-account`，只允许复制到 App Review Information 安全字段。
- 真实恢复密钥不得写入 App Store Connect 文案、审核备注、截图或仓库文档。
- 手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充。

## 当前不可提交原因

以本轮复跑证据为准：

- `Backend/proof/production-readiness.json` 当前 `ready=false`
- `Backend/proof/auth-providers.json` 当前 `passed=false`，微信 provider 未配置；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充
- `Backend/proof/ios-release-readiness.json` 当前 `passed=false`，缺真实微信 Release build setting
- `Backend/proof/ios-app-bundle.json` 当前 `passed=false`，缺真实 `wx...` URL Scheme
- `Backend/proof/app-store-evidence.json` 当前 `ready=false`，缺人工证据和 iOS 26.5 真机回归记录
