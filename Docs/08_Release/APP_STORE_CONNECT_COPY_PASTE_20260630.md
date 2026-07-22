# 小奶瓶 App Store Connect 可复制字段包

日期：2026-06-30

状态：用于在 App Store Connect 创建草稿和逐项粘贴字段；不可直接提交审核。提交前必须确认 `Backend/proof/production-readiness.json` 为 `ready=true`，并补齐 App Store 人工证据、D-U-N-S 后 Apple Developer 组织注册、签名归档、TestFlight、微信开放平台、短信服务商、OBS、备案和 iOS 26.5 真机回归证据。

源文件：`Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260630.md`

App Review Information 私密字段另见：`Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260630.md`

App Privacy 逐项答案表另见：`Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260630.md`

版本页和发布设置另见：`Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md`

结构化草稿总览另见：`Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260630.json`

人工填写当天执行包另见：`Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260630.json`

最终人工粘贴和同轮证据核对另见：`Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260630.md`

## App 信息

```text
App 名称：小奶瓶
Bundle ID：com.mewpow.xiaonaiping
SKU：xiaonaiping-ios-1
副标题：温柔记录宝宝每一天
主类别：生活
第二类别：留空
价格：免费
首发地区：Specific Countries or Regions -> China mainland
第二批地区：Hong Kong
版权：© 2026 深圳市闪现生活科技有限公司
隐私政策 URL：https://api.mewpow.com/xiaonaiping/privacy
技术支持 URL：https://api.mewpow.com/xiaonaiping/support
用户协议 URL：https://api.mewpow.com/xiaonaiping/terms
```

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

## 年龄分级填写口径

```text
逐项答案表：Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md

不选择 Kids 类目。预期年龄分级为 4+，以 App Store Connect 问卷自动计算结果为准。

目标用户是父母和照护者，不面向儿童直接使用。不含公开 UGC、社交匹配、成人内容、赌博、广告追踪、购买或订阅。

如果问卷涉及医疗或健康信息，如实说明 App 存在用户主动输入的喂养、睡眠、成长和疫苗提醒记录，但不提供诊断、治疗、疾病预测、专业接种建议、健康建议、压力评估、心理健康判断或压力提醒。

App 不接入 HealthKit、传感器、医院系统或第三方健康数据源。
```

## 隐私标签来源

```text
最终填写以 Docs/08_Release/APP_STORE_PRIVACY_LABEL.json 为准。
逐项填写以 Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260630.md 为人工核对表。

收集并关联身份：Identifiers、Contact Info、User Content、Photos or Videos、Health and Fitness、Usage Data。
收集但不关联身份：Diagnostics。
用于追踪：否。
第三方广告：否。
第三方分析 SDK：否。
```

## 审核备注

```text
小奶瓶用于父母或照护者记录宝宝成长。第一版免费，无 IAP，无广告，无第三方分析 SDK，不提供医疗诊断、治疗建议或专业疫苗建议，不是医疗器械，也不作为医疗器械使用。

数据默认本地优先保存。用户可以在“资料 -> 账号与同步”中使用恢复密钥登录并主动同步。同步会上传宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。App Review 测试请使用 App Review Information 中提供的恢复密钥测试账号；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充。

账号删除路径为：“资料 -> 账号与同步 -> 删除云端账号与同步”。该操作会删除账号、云端 JSON 同步和云端照片原图。本机资料默认保留，用户可以另行清空本地记录或删除宝宝档案。

疫苗模板仅用于记录和提醒，App 内文案不构成医疗建议。实际接种安排请以医生和当地官方信息为准。

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。

审核测试登录请优先使用 App Review Information 中提供的恢复密钥测试账号。手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充；正式提交包不提供、不依赖 debug code。
```

## 提交前不可跳过

```text
App Review Information 的联系人、恢复密钥和测试凭证只能填在 App Store Connect 私密字段；不要写入公开文案、截图或仓库。
Version Release 选择手动发布；不要在备案、TestFlight、iOS 26.5 真机回归和 App Store 人工证据完成前自动发布。
D-U-N-S 交付后必须回 Apple Developer 继续 Organization enrollment，并确认 Team ID、证书、Archive 和 TestFlight。
真实微信开放平台 AppID / AppSecret / wx... URL Scheme / Universal Link 后台绑定必须完成。
短信服务商截图和真实实发验证必须归档。
OBS 私有访问、加密、生命周期和删除验证必须归档。
iOS 26.5 TestFlight 或 Xcode 签名真机包回归必须完成，模拟器和 iOS 27 不能替代。
```
