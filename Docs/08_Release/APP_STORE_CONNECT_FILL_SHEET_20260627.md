# 小奶瓶 App Store Connect 填表版

日期：2026-06-27

状态：可用于准备 App Store Connect 草稿，不可直接提交审核。正式提交仍需 `Backend/proof/production-readiness-20260627T-current.json` 为 `ready: true`，并补齐微信开放平台、签名归档、TestFlight、中国大陆 APP 备案和人工证据。

素材机器校验：`Backend/proof/app-store-connect-materials-20260627-current.json`，当前 `passed=true`。

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

数据默认本地优先保存。开启账号与备份后，可通过恢复密钥、手机号或微信登录私有账号，并将记录和主动加入 App 的照片原图备份到账号空间，便于换机恢复。

主要功能：

- 宝宝档案：记录昵称、生日、性别和成长信息。
- 日常记录：快速记录喂养、睡眠、排便和备注。
- 成长回看：整理身高、体重和月度变化。
- 疫苗提醒：提供中国大陆和香港模板切换，用于记录和提醒。
- 照片时间线：整理用户主动加入 App 的宝宝照片。
- 账号与备份：支持恢复密钥、手机号、微信登录、云端备份恢复和账号删除。

小奶瓶不提供医疗诊断、治疗建议或专业疫苗建议。疫苗模板仅用于记录和提醒，实际接种安排请以医生和当地官方信息为准。
```

## 新版本说明

```text
第一版：宝宝档案、日常记录、成长记录、疫苗提醒、照片时间线、手机号/微信/恢复密钥账号备份恢复和云端账号删除。
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

以 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` 为最终源文件。当前摘要：

| 数据类别 | 是否收集 | 是否关联身份 | 是否追踪 | 用途 |
| --- | --- | --- | --- | --- |
| Identifiers | 是 | 是 | 否 | 账号、备份恢复 |
| Contact Info | 是 | 是 | 否 | 手机号验证码登录 |
| User Content | 是 | 是 | 否 | 宝宝档案、备注、记录、照片元数据 |
| Photos or Videos | 是 | 是 | 否 | 用户主动加入 App 的宝宝照片原图备份 |
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
| 5 | `05-profile-backup-iphone16pro.png` | 主动备份，也能主动删除 | 开启账号后可备份恢复，也可删除云端账号与备份。 |

当前 5 张候选图不展示灵动岛/锁屏 Live Activity 或小组件。若后续新增第 6 张截图，建议只展示“喝奶闹钟在锁屏/灵动岛显示下一次提醒”，不得写成健康建议、喂养推荐或医疗判断。

截图禁区：

1. 不使用真实宝宝照片，除非另有明确授权。
2. 不展示真实手机号、恢复密钥、token、账号 ID、对象存储 key 或内部路径。
3. 不展示 `127.0.0.1`、debug code、internal dashboard 或工程文档。
4. 不写医疗诊断、治疗、疫苗建议、医生替代或专业健康结论。
5. 微信登录未完成开放平台配置前，不截图暗示微信登录已经可用。

## 审核备注可粘贴文本

```text
小奶瓶用于父母或照护者记录宝宝成长。第一版免费，无 IAP，无广告，无第三方分析 SDK，不提供医疗诊断、治疗建议或专业疫苗建议，不是医疗器械，也不作为医疗器械使用。

数据默认本地优先保存。用户可以在“资料 -> 账号与备份”中使用恢复密钥、手机号或微信登录并主动备份。备份会上传宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。手机号和微信登录仅用于账号识别和恢复。

账号删除路径为：“资料 -> 账号与备份 -> 删除云端账号与备份”。该操作会删除账号、云端 JSON 备份和云端照片原图。本机资料默认保留，用户可以另行清空本地记录或删除宝宝档案。

疫苗模板仅用于记录和提醒，App 内文案不构成医疗建议。实际接种安排请以医生和当地官方信息为准。

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。

审核测试登录请优先使用 App Review Information 中提供的恢复密钥测试账号。手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充；正式提交包不提供、不依赖 debug code。
```

## 审核测试账号填写说明

- App Review Information 中填写恢复密钥测试账号。
- 脱敏证据文件：`Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json`。
- 真机回归与测试账号操作表：`Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`。
- 真实恢复密钥只保存在本地 ignored 文件 `.env.xnp-review-account`，只允许复制到 App Review Information 安全字段。
- 真实恢复密钥不得写入 App Store Connect 文案、审核备注、截图或仓库文档。
- 手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充。

## 当前不可提交原因

以本轮复跑证据为准：

- `Backend/proof/production-readiness-20260627T-current.json` 当前 `ready=false`
- `Backend/proof/auth-providers-20260627T-current.json` 当前 `passed=false`，微信 provider 未配置；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充
- `Backend/proof/ios-release-readiness.json` 当前 `passed=false`，缺真实微信 Release build setting
- `Backend/proof/ios-app-bundle-20260627T-current-ios265.json` 当前 `passed=false`，缺真实 `wx...` URL Scheme
- `Backend/proof/app-store-evidence-20260627T-current.json` 当前 `ready=false`，缺人工证据和 iOS 26.5 真机回归记录
