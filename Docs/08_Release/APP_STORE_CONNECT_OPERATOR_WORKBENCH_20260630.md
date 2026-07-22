# 小奶瓶 App Store Connect 上线操作台

日期：2026-06-30

状态：operator-workbench-not-evidence。本文用于今天继续整理 App Store Connect 草稿、D-U-N-S 后动作、真机/TestFlight 采集和外部平台材料；不是 App Store Connect 已填写证据，不是生产就绪证明，也不是 Submit for Review 许可。

同日日期边界：`Docs/08_Release/LAUNCH_DAY_ROLLOVER_20260630.json`

跨项目可复用材料边界：`Docs/08_Release/CROSS_APP_REUSABLE_EVIDENCE_PACKET_20260630.json`

生产/隐私证据入库工作台：`Docs/08_Release/XNP_PRODUCTION_PRIVACY_EVIDENCE_WORKBENCH_20260630.md`

生产 proof 当日刷新计划：`Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json`。该包是 `refresh-plan-not-evidence`，用于按顺序刷新同日 deployment、remote API、storage、auth provider、SMS live-send、WeChat client、iOS 26.5 Release readiness / app bundle、App Store evidence、production readiness 和 launch objective proof；不是 deployment proof、不是 production readiness，也不是提交许可。稳定 alias 只能在同一轮 current proof 全绿后同步，不能从旧 `20260627T-current` / `20260629T-current` proof、模拟器证据、provider template 或红色 current proof 复制。

生产 proof 当前刷新状态：`Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260630.json`。当前状态是 `current-proof-status-not-submit-permission` 且 `stableAliasSyncAllowed=false`；含义是 current proof files are incomplete or failed; do not sync stable aliases。该状态文件只用于记录缺口、失败项和下一步，不允许把 `Backend/proof/production-readiness.json`、`Backend/proof/app-store-evidence.json`、`Backend/proof/auth-providers.json`、`Backend/proof/storage-backend.json`、`Backend/proof/ios-release-readiness.json` 或 `Backend/proof/ios-app-bundle.json` 提前替换为未通过的 current proof。

微信 Release 配置执行包：`Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json`。该包是 `release-configuration-packet-not-evidence`，用于拿到真实微信开放平台 AppID 后核对同一个 `wx...` AppID、URL Scheme、Universal Link、Apple Developer Team ID、AASA、服务端私有 AppSecret、iOS 26.5 Release proof 和 RD-14 真机微信登录边界；不是 AppSecret 容器，也不是提交许可。

短信真实实发执行包：`Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260630.json`。该包是 `live-send-packet-not-evidence`，用于上线当天按顺序核对 `07-sms-provider.png` 或 PDF、`auth-providers-20260630T-current.json`、`auth-providers-sms-live-20260630T-current.json` 和稳定 alias 同步；测试手机号只能来自私有环境变量 `XNP_SMS_TEST_PHONE`，不能写进命令行、日志、截图、JSON proof 或仓库。仅 `verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE` 生成的 sms-live proof 可用于同步 `auth-providers.json`，普通 `--live-check` 不替代真实短信实发。

OBS 存储证据执行包：`Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260630.json`。该包是 `storage-proof-packet-not-evidence`，用于上线当天按顺序核对 `09-obs-policy.png` 或 PDF、`storage-backend-20260630T-current.json`、`production-readiness-20260630T-current.json` 和稳定 alias 同步；OBS 控制台截图不能替代 storage proof，storage proof 也不能单独替代 production readiness。必须证明私有 bucket 或 prefix、生产区域、私有访问策略、加密、生命周期、删除策略、账号删除清理和无公开对象访问，且不能记录 AK/SK、临时签名 URL、完整 object key 或真实宝宝照片。

备案 / ICP / 公安联网备案执行包：`Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260630.json`。该包是 `execution-packet-not-evidence`，用于上线当天按顺序核对公司主体、大陆可售、`03-app-filing.pdf` / `03-app-filing.png`、公安联网备案、隐私标签、年龄分级、RD-19 公开 URL 真机证据、`mainland-filing-materials.json`、App Store evidence 和 production readiness；不能替代真实备案回执或适用判断。拿到真实备案号前，不得在公开页、App UI、审核备注或 App Store Connect 里写占位备案号；拿到真实号后才更新 public pages / App 内展示 / Review Notes 并复跑备案、公开页、审核备注、App Store evidence、production readiness 和 launch objective gates。

可复用文案源：

- `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260630.md`
- `Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260630.md`
- `Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260630.json`
- `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json`
- `Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260630.md`
- `Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md`
- `Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260630.md`
- `Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md`
- `Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260630.json`
- `Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_20260630.json`

今天必须重采或当日复核的证据：App Store Connect 页面截图、Apple Developer / D-U-N-S 后状态、签名 Archive、TestFlight、最终截图上传 provenance、微信开放平台、短信服务商、OBS、备案/隐私、iOS 26.5 真机回归和生产 proof。20260630 材料可以作为填表源，不能当作 20260630 现场证据。

## 跨项目复用边界

一根呆毛 / Emotion Isle 项目里的公司级材料只允许作为 D-U-N-S、Apple Developer Organization 和历史 cross-app 状态的参考来源，不直接证明小奶瓶已经完成上线证据，也不能作为小奶瓶 Submit for Review 许可。

| 可参考来源 | 允许用途 | 小奶瓶仍必须重采 |
| --- | --- | --- |
| `/Users/smianmian/Emotion Isle/output/cross-app-submission-readiness-20260629-current.json` | 只作为最新可见历史跨项目状态参考；20260630 current 源文件不存在，不能当作今天证据；无论 `canSubmit` 值如何，都不能替代小奶瓶 proof 组 | App Store Connect 页面、App Store evidence、production readiness、launch objective audit、TestFlight regression、provider、filing、signed archive |
| `/Users/smianmian/Emotion Isle/output/duns-post-delivery-apple-developer-runbook-20260629-current.json` | 只作为最新可见历史 D-U-N-S / Apple Developer 顺序参考；20260630 current 源文件不存在，不能当作今天证据 | `AppleDeveloper/13-organization-team-id.png`、`14-bundle-id-capabilities.png`、`15-distribution-certificate-profile.png`、`16-account-roles-access.png` |
| `/Users/smianmian/Emotion Isle/output/AppStoreEvidence/16-duns-delivery.png or .pdf` | 公司级 D-U-N-S 交付参考，必须隐藏完整 D-U-N-S 编码、Apple ID 邮箱和完整手机号；源路径不能直接作为小奶瓶目标证据 | 先复制或重采到 `Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png or .pdf`；仍需 XiaoNaiPing Archive、TestFlight、微信开放平台、短信服务商、OBS、APP 备案 |
| `/Users/smianmian/Emotion Isle/output/AppStoreEvidence/17-apple-org-enrollment-continued.png or .pdf` | 公司级 Apple Organization 继续注册参考；源路径不能直接作为小奶瓶目标证据 | 先复制或重采到 `Docs/08_Release/AppStoreEvidence/AppleDeveloper/17-apple-org-enrollment-continued.png or .pdf`；仍需 `com.mewpow.xiaonaiping` Bundle ID、`group.com.mewpow.xiaonaiping` App Group、`applinks:api.mewpow.com` Associated Domains、XiaoNaiPing TestFlight build |

复用规则：

- 只有主体仍为深圳市闪现生活科技有限公司时，才允许引用跨项目公司级材料。
- `/Users/smianmian/Emotion Isle/output/cross-app-submission-readiness-20260630-current.json` 和 `/Users/smianmian/Emotion Isle/output/duns-post-delivery-apple-developer-runbook-20260630-current.json` 当前不存在；不要按不存在路径找材料，也不要把 20260629 历史参考当成 20260630 同日证据。
- 不能把一根呆毛 / Emotion Isle 的 App Store Connect 页面、Archive、TestFlight、截图、真机回归、短信、微信、OBS、生产 namespace 或备案证据当作小奶瓶证据。
- 如果 Apple Team ID 不等于 `L2TYJNDTJK`，先同步小奶瓶 project signing、ExportOptions、AASA Team prefix 和微信 Universal Link，再 Archive / TestFlight。
- 任何复制到小奶瓶证据目录的公司级材料，都必须记录来源路径、文件大小、sha256、采集日期和脱敏结论。
- 这个复用包是 `reuse-plan-not-evidence`，不能让 `app-store-evidence.json`、`production-readiness.json` 或 `launch-objective-audit.json` 变绿。

## App Store Connect 草稿字段

| 字段 | 今天填写值或口径 | 来源 |
| --- | --- | --- |
| App 名称 | 小奶瓶 | `APP_STORE_CONNECT_FILL_SHEET_20260630.md` |
| Bundle ID | `com.mewpow.xiaonaiping` | App Store Connect / Apple Developer |
| SKU | `xiaonaiping-ios-1` | `APP_STORE_CONNECT_FILL_SHEET_20260630.md` |
| 副标题 | 温柔记录宝宝每一天 | `APP_STORE_CONNECT_COPY_PASTE_20260630.md` |
| 主类别 | 生活 | `APP_STORE_CONNECT_FILL_SHEET_20260630.md` |
| 第二类别 | 留空，不选择健康健美 | `APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260630.md` |
| 首发地区 | Specific Countries or Regions -> China mainland | `APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md` |
| 价格 | 免费 | `APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md` |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` | `APP_STORE_PRIVACY_LABEL.json` / `Backend/static/privacy.html` |
| 技术支持 URL | `https://api.mewpow.com/xiaonaiping/support` | `APP_STORE_PRIVACY_LABEL.json` / `Backend/static/support.html` |
| 用户协议 URL | `https://api.mewpow.com/xiaonaiping/terms` | `Backend/static/terms.html` |
| 关键词 | `宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册` | 73 UTF-8 bytes，低于 100 bytes |
| 年龄分级 | 预期 4+，不选择 Kids Category，Regulated Medical Device 为 No | `APP_STORE_AGE_RATING_ANSWERS_20260630.md` |
| App Privacy | 不追踪；无第三方广告；无第三方分析 SDK；Identifiers、Contact Info、User Content、Photos or Videos、Health and Fitness、Usage Data、Diagnostics 按 privacy label 填写 | `APP_STORE_PRIVACY_LABEL.json` |
| 审核备注 | 使用下方审核备注口径，不写恢复密钥、不写验证码、不写完整手机号、不写 AppSecret | `APP_STORE_REVIEW_INFORMATION_20260630.md` |

描述可粘贴文本：

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

新版本说明：

```text
第一版：宝宝档案、日常记录、喝奶提醒、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。
```

审核备注可粘贴文本：

```text
小奶瓶用于父母或照护者记录宝宝成长。第一版免费，无 IAP，无广告，无第三方分析 SDK，不提供医疗诊断、治疗建议或专业疫苗建议，不是医疗器械，也不作为医疗器械使用。

数据默认本地优先保存。用户可以在“资料 -> 账号与同步”中使用恢复密钥登录并主动同步。同步会上传宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。App Review 测试请使用 App Review Information 中提供的恢复密钥测试账号；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充。

账号删除路径为：“资料 -> 账号与同步 -> 删除云端账号与同步”。该操作会删除账号、云端 JSON 同步和云端照片原图。本机资料默认保留，用户可以另行清空本地记录或删除宝宝档案。

疫苗模板仅用于记录和提醒，App 内文案不构成医疗建议。实际接种安排请以医生和当地官方信息为准。

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。

审核测试登录请优先使用 App Review Information 中提供的恢复密钥测试账号。手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充；正式提交包不提供、不依赖 debug code。
```

回填 App Store Connect 前先核对 `Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260630.json`。该包是 `field-freeze-plan-not-evidence`，只冻结 App 名称、副标题、描述、关键词、分类、年龄分级、隐私政策 URL、技术支持 URL、用户协议 URL 和审核备注的源文件、预算、复制顺序和字段锁；不得现场改字后只改 App Store Connect 页面，任一字段改字必须回写源文件并重跑 post-freeze gates。该包不是 App Store Connect live evidence，也不是提交许可。

正式填写页面时核对 `Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260630.json`。该包是 `entry-session-plan-not-evidence`，用于按顺序填 App Information、Pricing / Availability / Release、Version Information、App Privacy、Age Rating、Review Information、Build/TestFlight 和 Submit Review precheck，并归档 ASC-01 到 ASC-08 同 session 页面证据、脱敏项、停机条件和 post-entry gates；不是 App Store Connect 人工证据，不能作为提交许可。

最后一次人工粘贴和截图前核对 `Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260630.md`。该审计表只用于锁定同一天同一轮环境、App 名称/副标题/描述/关键词/分类/年龄分级/隐私政策 URL/技术支持 URL/用户协议 URL/审核备注、字段源文件一致性、字段预算、外部证据索引、最终截图来源、ASC-01 到 ASC-08 页面证据、Submit for Review 总守卫和禁写项；不得只改 App Store Connect 页面而不回写源文件，不得把 debug code、placeholder `wx...`、模拟器截图或 iOS 27 真机截图当作提交证据，也不能在 `production-readiness.json` 或 `launch-objective-audit.json` 仍为红色时声称完成。

人工证据采集前核对 `Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260630.json`。该包是 `manual-evidence-plan-not-evidence`，用于统一锁定 01 公司账号、02 大陆可售、03 备案、04 隐私标签、17 年龄分级、05 Archive、06 TestFlight、Apple Developer 权限、07 短信服务商、08 微信开放平台、08b AASA、09 OBS、ASC-01 到 ASC-08、最终截图 `UPLOAD_PROVENANCE.json` 和 `12-real-device-regression.md` 的目标文件、同轮采集、真实证据非模板、脱敏和 post-capture gates；不是截图/PDF/脱敏 JSON/TestFlight/签名归档/生产 proof/iOS 26.5 真机回归本身，也不是提交许可。

最终截图上传 provenance 填写前核对 `Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.template.json`。该模板只能在最终截图来自同一个 iOS 26.5 TestFlight 或 Xcode 签名真机 build，并且 `05-signed-archive.png`、`06-testflight.png`、ASC-07 build、ASC-02 截图顺序和 `12-real-device-regression.md` 同轮归档后复制为 `UPLOAD_PROVENANCE.json`；必须逐张填写 `fileSizeBytes`、`sha256`、`redactionChecked`、`matchesFinalUploadOrder` 和 `secretValuesNotRecorded`。Debug simulator candidate 截图不能作为最终 App Store 上传证据。

隐私标签、年龄分级和审核信息现场结果前核对 `Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-PRIVACY-AGE-REVIEW-RESULT.template.json`。该模板是 `template-not-evidence` / `privacy-age-review-result-template-not-evidence`，只能在真实 App Store Connect 会话完成 ASC-04、ASC-05、ASC-06、`04-privacy-label`、`17-age-rating-result` 和 `11-test-account-redacted` 同轮归档后复制为 `ASC-PRIVACY-AGE-REVIEW-RESULT.json`。结果索引必须逐项填写隐私标签、年龄分级和审核账号证据的 `fileSizeBytes`、`sha256`、`sameSessionAsAscBackfill`、`sourceMatchesAnswerSheet`、`redactionChecked`、`secretValuesNotRecorded`，并确认 Tracking 为 No、Regulated Medical Device 为 No、恢复密钥只进入 App Store Connect private Sign-In Information 字段。该模板不能替代隐私标签证据、年龄分级结果证据、App Store evidence、production readiness、launch objective audit、TestFlight、provider、备案、最终截图或 iOS 26.5 真机 proof，也不能作为提交许可。

现场回填 App Store Connect 后复制 `Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-BACKFILL-RESULT.template.json` 为 `ASC-BACKFILL-RESULT.json`，逐项填写 App 名称、副标题、描述、关键词、分类、年龄分级、隐私政策 URL、技术支持 URL、用户协议 URL 和审核备注的 `sourceMatchesFieldFreeze`、`pageValueVisibleOrConfirmed`、`sameSessionAsBackfill`、`copyPastedWithoutAscOnlyEdit`、`lengthOrChoiceLimitChecked`、`redactionChecked`。同时给 ASC-01 到 ASC-08 截图补 `fileSizeBytes`、`sha256`、`sameSessionAsBackfill`、`sourceIsAppStoreConnectEvidenceRoot`、`fieldFreezeConfirmed`、`secretValuesNotRecorded`。该结果索引不是提交许可，`canSubmitAtCapture` 仍必须等待 App Store evidence、production readiness、launch objective audit 和 TestFlight regression plan 全绿。

填写 App Review Information 前核对 `Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260630.json`：App Review 测试使用恢复密钥测试账号，私密恢复密钥只允许从本机 `.env.xnp-review-account:XNP_REVIEW_RECOVERY_KEY` 复制到 App Store Connect 的 private Sign-In Information 字段，不写入 Markdown、JSON proof、截图、录屏、日志或 App Store metadata。`11-test-account-redacted.json` 只能保存脱敏账号证据；RD-10/RD-13/RD-14/RD-15 必须来自同一个 iOS 26.5 TestFlight 或 Xcode 签名真机 build，且分别证明恢复密钥登录、真实短信、微信登录和账号删除。手机号和微信测试账号在真实短信服务商、微信开放平台和 RD-13/RD-14 证据完成前保持 pending；该 packet 不是提交许可。

## D-U-N-S 交付后动作

| 顺序 | 动作 | 证据文件 | 停机条件 |
| --- | --- | --- | --- |
| 1 | 回 Apple Developer 继续深圳市闪现生活科技有限公司 Organization enrollment | `AppStoreEvidence/AppleDeveloper/13-organization-team-id.png` | 不把 D-U-N-S 完整编码写入仓库 |
| 2 | 确认组织 Team ID 和账号 Membership 状态 | `AppleDeveloper/13-organization-team-id.png` | Team ID 未确认前不 Archive |
| 3 | 确认当前 Apple ID 具备 Certificates, Identifiers & Profiles、App 管理、构建上传、TestFlight 管理和提交审核权限 | `AppleDeveloper/16-account-roles-access.png` | 权限不足先找 Account Holder 或管理员 |
| 4 | 核对 Bundle ID、App Groups、Associated Domains 和 `applinks:api.mewpow.com` | `AppleDeveloper/14-bundle-id-capabilities.png` | Team ID 漂移时先同步工程、AASA 和微信 Universal Link |
| 5 | 创建或选择 App Store Distribution certificate / provisioning profile | `AppleDeveloper/15-distribution-certificate-profile.png` | 不提交证书私钥、profile 文件或签名 secret |
| 6 | Archive Release build | `05-signed-archive.png` | Archive 成功不等于 TestFlight 已可测 |
| 7 | exportArchive 上传 App Store Connect / TestFlight | `06-testflight.png`、`ASC-07-build-testflight-link.png` | build 未 processed/testable 前不跑最终真机回归 |

等待 D-U-N-S 或 Apple Developer 状态刷新时，先复制 `Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json` 为 `EXTERNAL-STATUS-POLL-RESULT.json`，逐项填写 D&B Self-Service Portal、Apple Developer Enrollment、Apple Developer email 和 App Store Connect draft 的同轮状态、目标截图、`fileSizeBytes`、`sha256`、`sameRoundAsStatusPoll`、`sourceIsAppleDeveloperEvidenceRoot`、`realEvidenceNotTemplate`、`secretValuesNotRecorded`、是否可继续 Organization enrollment、Team ID 是否可用和 `postStatusPollXiaoNaiPingProofReruns`。该轮询结果只能决定继续等待、继续企业注册或进入签名工作流，不能作为提交许可，不能替代小奶瓶 Archive、TestFlight、外部平台、生产 proof、最终截图或 iOS 26.5 真机证据。

拿到 D-U-N-S 并现场处理 Apple Developer 后，复制 `Docs/08_Release/AppStoreEvidence/AppleDeveloper/DUNS-POST-DELIVERY-EXECUTION-RESULT.template.json` 为 `DUNS-POST-DELIVERY-EXECUTION-RESULT.json`，逐项填写 60 分钟内动作、D-U-N-S 交付、继续 Organization enrollment、付款/会员状态、Team context、D-U-N-S lookup 异常处理、证据文件大小、sha256、同轮、证据根、脱敏和 `secretValuesNotRecorded`。不要把完整 D-U-N-S 编码、Apple ID 邮箱、验证码、完整手机号、证书私钥、AppSecret、token 或付款信息写进仓库。

现场执行后复制 `Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json` 为 `APPLE-DEVELOPER-ORG-SIGNING-RESULT.json`，逐项填写 D-U-N-S 交付、Organization enrollment、Team ID、Bundle/capability、证书/Profile、账号权限、Team context、付款收据、AASA、Archive、TestFlight 和 iOS 26.5 回归证据的 `fileSizeBytes`、`sha256`、`sameRoundAsTeamIdOrBuild`、`sourceIsApprovedEvidenceRoot`、`redactionChecked`、`secretValuesNotRecorded`。该结果索引不是提交许可，`canSubmitAtCapture` 必须等同 build TestFlight 处理、iOS 26.5 回归和小奶瓶 proof gates 全绿后才可为 true。

采集 Apple Developer Team / 签名 / Archive / TestFlight 证据前先核对 `Docs/08_Release/AppStoreEvidence/_templates/apple-developer-team-signing-evidence.template.json`。该模板是 `template-only-not-evidence`，只用于锁定 `13-organization-team-id.png`、`14-bundle-id-capabilities.png`、`15-distribution-certificate-profile.png`、`16-account-roles-access.png`、`08b-wechat-universal-link-aasa.png`、`05-signed-archive.png`、`06-testflight.png` 和 `12-real-device-regression.md` 的目标文件、同轮 Team ID / build 匹配、工程 `DEVELOPMENT_TEAM`、ExportOptions `teamID`、AASA Team prefix、App Groups、Associated Domains、App Store Distribution 证书/Profile、TestFlight 处理状态、脱敏和 post-capture gates；不能把该模板改名成截图/JSON 结果，也不能用 Development、Ad Hoc、Enterprise、模拟器、debug 或 iOS 27 证据替代。

命令口径：

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive archive
xcodebuild -exportArchive -archivePath /tmp/XiaoNaiPing-CN.xcarchive -exportPath /tmp/XiaoNaiPing-CN-AppStoreConnect -exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist -allowProvisioningUpdates
```

## 真机/TestFlight 证据模板

所有本机证据只认 iOS 26.5。安装来源只能是 TestFlight 或 Xcode 签名真机包，不能用模拟器、iOS 27、不同 build 或 Debug candidate 代替。

开拍前先核对 `Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260630.json`。该包是 `preflight-plan-not-evidence`，用于确认 iOS 26.5 物理真机可用、同一 Archive/TestFlight build、通知权限允许/拒绝双路径可重置、短信/微信/AASA、OBS/storage/account deletion、灵动岛/锁屏/小组件前置、RealDevice 证据根、脱敏和 post-capture gates；当前 `canStartCaptureFromThisPacket=false` 且 `canSubmitFromThisPacket=false`，不能替代真实 `REAL-DEVICE-CAPTURE-RESULT.json`、`12-real-device-regression.md`、App Store evidence 或 launch objective audit。

现场拍摄时打开 `Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md`。该执行单用于逐项填写设备、iOS 26.5、安装方式、版本 / Build、采集时间、同一 build 身份锁、RD-03/RD-10/RD-13/RD-14/RD-15/RD-17/RD-22/RD-23 目标文件、通知权限允许/拒绝双路径重置、失败复测与阻断、外部后台证据不可替代和拍完后回填 `12-real-device-regression.md` / `REAL-DEVICE-CAPTURE-RESULT.json` 的规则；不是已完成证据，也不是提交许可。

| ID | 场景 | 目标文件 | 必须证明 |
| --- | --- | --- | --- |
| RD-03 | 喂养记录和喝奶提醒顺延 | `RealDevice/RD-03-feeding-record.png` | 固定间隔已配置；顺延滚轮只出现不顺延、+5、+10、+15、+20、+25、+30 分钟；下一次提醒按本顿结束时间或发生时间重排；不根据奶量、月龄、传感器或健康数据推算 |
| RD-10 | 恢复密钥登录 | `RealDevice/RD-10-recovery-login.png` | 恢复密钥账号可登录；截图不展示恢复密钥全文 |
| RD-13 | 手机号登录 | `RealDevice/RD-13-phone-login.png` | 真实短信服务商验证码可发送并验证；完整手机号和验证码已遮挡 |
| RD-14 | 微信登录 | `RealDevice/RD-14-wechat-login.png` | 微信授权能拉起并回到 App；不展示 AppSecret、debug code 或完整手机号 |
| RD-15 | 账号删除 | `RealDevice/RD-15-account-delete.png` | 删除云端账号与同步后旧 token 失效，云端 JSON 同步和照片对象删除，本机资料保留边界清楚 |
| RD-17-allowed | 通知权限允许 | `RealDevice/RD-17-notification-allowed.png` | 干净通知授权状态下允许后能创建下一次喝奶提醒 |
| RD-17-denied | 通知权限拒绝 | `RealDevice/RD-17-notification-denied.png` | 重新干净授权状态下拒绝后不崩溃，不假装已创建提醒，有系统设置入口 |
| RD-22-compact | 灵动岛紧凑态 | `RealDevice/RD-22-dynamic-island-compact.png` | 无裁剪、边缘完整、未右移压到岛中心 |
| RD-22-expanded | 灵动岛展开态 | `RealDevice/RD-22-dynamic-island-expanded.png` | 下一次喝奶时间、固定间隔和手动顺延结果可读，无医疗建议 |
| RD-23-lock-stack | 锁屏通知栈 | `RealDevice/RD-23-lock-screen-notification-stack.png` | 上下相邻通知不遮挡提醒卡片 |
| RD-23-lock-widget | 锁屏小组件 | `RealDevice/RD-23-lock-screen-widget-summary.png` | accessory 小组件可读、无裁剪、无隐私照片 |
| RD-23-home-widget | 桌面小组件 | `RealDevice/RD-23-home-widget-summary.png` | 小尺寸和中尺寸今日摘要可读、无溢出、无备注/token/对象 key |

采集后复制 `Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json` 为 `REAL-DEVICE-CAPTURE-RESULT.json`，填写 `captured-live-real-device`、iOS 26.5、同一 build、redactionReviewed、fileSizeBytes、sha256 和每个 visualQA 结论。模板不是证据。

同时复制 `Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md` 为 `12-real-device-regression.md`，逐项填写 iOS 26.5、同一 TestFlight build 或 Xcode 签名真机包、RD-10/RD-13/RD-14/RD-15/RD-17/RD-22/RD-23 独立证据、RD-17 允许/拒绝双路径、RD-22 灵动岛紧凑/展开、RD-23 锁屏通知栈/锁屏小组件/桌面小组件、失败/复测证据和脱敏复核。`12-real-device-regression.md` 和 `REAL-DEVICE-CAPTURE-RESULT.json` 都不是提交许可。

## 微信、短信、生产、隐私和备案

| 模块 | 今天能继续推进的材料 | 证据文件 | 必须跑的 gate |
| --- | --- | --- | --- |
| 微信开放平台 | 确认真实 `wx...` AppID、Bundle ID、URL Scheme、Universal Link、AASA 和 Release build setting | `08-wechat-open-platform.png`、`08b-wechat-universal-link-aasa.png`、`RD-14-wechat-login.png` | `check_wechat_client_configuration.py`、`check_provider_evidence_materials.py`、`check_ios_release_readiness.py` |
| 短信服务商 | 截图短信签名、账号登录/验证模板、模板审核状态、发送区域、真实实发成功记录 | `07-sms-provider.png`、`auth-providers-sms-live-YYYYMMDDT-current.json` | `verify_auth_providers.py --send-test-sms --require-sms-live-send`、`check_provider_evidence_materials.py` |
| OBS | 私有 bucket/prefix、区域、加密、生命周期、删除策略和删除验证 | `09-obs-policy.png`、`storage-backend-YYYYMMDDT-current.json` | `verify_storage_backend.py`、`check_production_readiness.py --require-huawei-obs` |
| 生产 proof | 同日刷新 deploy、remote-api、storage、auth-providers、app-store-evidence、production-readiness 稳定 alias | `Backend/proof/*-20260630T-current.json` 和稳定 alias | `run_launch_readiness.sh`、`check_launch_objective_audit.py --allow-incomplete` |
| 隐私标签 | App Store Privacy 页面按 `APP_STORE_PRIVACY_LABEL.json` 回填并截图 | `04-privacy-label.png`、`ASC-04-app-privacy.png` | `check_app_store_connect_evidence_materials.py`、`check_app_store_evidence.py --allow-incomplete --date 2026-06-30` |
| ICP / App 备案 | 归档备案号、APP 备案状态或适用判断，不写占位备案号 | `03-app-filing.pdf` 或 `03-app-filing.png` | `check_mainland_filing_materials.py`、`check_app_store_evidence.py --allow-incomplete --date 2026-06-30` |

备案、隐私标签和年龄分级证据采集前先核对 `Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json`。该模板是 `template-only-not-evidence`，只用于锁定 `01-company-account.png`、`02-mainland-availability.png`、`03-app-filing.png` / `.pdf`、`04-privacy-label.png`、`17-age-rating-result.png` / `.pdf` 的目标证据、公司主体、China mainland 首发、备案号/进度/适用判断、隐私政策/用户协议/技术支持 URL、App Store privacy label source、No tracking、非医疗边界、脱敏和 post-capture gates；不能把该模板改名成截图/结果 JSON，不能在真实证据归档前声称 App Store evidence 完成。

微信开放平台采集前先核对 `Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json`。该模板是 `template-only-not-evidence`，只用于锁定 `08-wechat-open-platform.png` 和 `08b-wechat-universal-link-aasa.png` 的目标证据、真实 `wx + 16 lowercase hex` AppID、URL Scheme 等于 AppID、Universal Link `https://api.mewpow.com/xiaonaiping/wechat/`、移动应用配置状态、服务端私有 `XNP_WECHAT_APP_SECRET`、脱敏和 post-capture gates；不能把该模板改名成截图/PDF/结果证据，也不能把 AppSecret 写入 iOS 工程、截图、JSON evidence 或仓库。

采集前先核对 `Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260630.json`，逐项确认微信开放平台、微信 AASA、短信服务商、OBS、备案/隐私标签和 production readiness current proof 的目标文件、`fileSizeBytes`、`sha256`、同轮采集、证据根、脱敏和 `secretValuesNotRecorded` 占位。该采集包只是现场清单，不是截图/PDF/实发 proof；不能把 provider 配置 proof 当短信实发 proof，也不能把后台截图当 iOS 26.5 真机证据。

外部平台采集完成后复制 `Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json` 为 `EXTERNAL-PLATFORM-CAPTURE-RESULT.json`，状态只允许在真实截图、PDF、短信实发 proof 和同轮 production proof 都归档后改为 `captured-live-external-platforms`。结果索引必须逐项填写 `smsProviderConsole`、`wechatOpenPlatform`、`wechatUniversalLinkAasa`、`smsLiveSendProof`、`huaweiObsPolicy`、`mainlandFiling`、`privacyLabel`、`ageRatingResult` 的 `fileSizeBytes`、`sha256`、`sameRoundAsCapture`、`sourceIsAllowedEvidenceRoot`、`redactionChecked`、`secretValuesNotRecorded`，并保留 `sameRoundEvidenceManifest`、`postCaptureRerunCommands`、`checkTestFlightRegressionPlan`、`checkSignedArchiveTestFlightMaterials` 和 cross-app 历史参考不可替代边界。该结果索引不是提交许可，不能替代 App Store evidence、production readiness、launch objective audit、TestFlight regression、最终截图或 iOS 26.5 真机证据。

## Submit for Review 停机线

只允许保存草稿和采集页面证据；不得点击 Submit for Review，除非以下全部为真：

- `Backend/proof/launch-day-rollover.json` passed=true。
- `Backend/proof/app-store-connect-materials.json` passed=true。
- `Backend/proof/app-store-submission-packet.json` passed=true。
- `Backend/proof/app-store-assets.json` passed=true。
- `Backend/proof/app-store-evidence-20260630T-current.json` ready=true，并同步到 `Backend/proof/app-store-evidence.json`。
- `Backend/proof/production-readiness-20260630T-current.json` ready=true，并同步到 `Backend/proof/production-readiness.json`。
- `Backend/proof/launch-objective-audit.json` ready=true。
- `Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260630.json` 已核对，且 `ASC-08-submit-review-precheck.png` 只作为 Submit for Review 前页面截图，不替代任何 green proof。
- `Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_20260630.json` 已核对，且 `UPLOAD_PROVENANCE.json` 证明最终截图来自同一个 iOS 26.5 TestFlight 或 Xcode 签名真机 build。
- `10-final-screenshots/UPLOAD_PROVENANCE.json` 证明 iOS 26.5、TestFlight 或 Xcode 签名真机包、同一版本/build。
- `12-real-device-regression.md` 和 `REAL-DEVICE-CAPTURE-RESULT.json` 证明 iOS 26.5 TestFlight 或签名真机包回归通过。
- D-U-N-S 后 Apple Developer Organization、Team ID、证书、Archive、TestFlight、微信、短信、OBS、备案和隐私证据均已归档并脱敏。

## 复跑命令

```bash
python3 Backend/scripts/check_launch_operator_workbench.py --output Backend/proof/launch-operator-workbench.json
python3 Backend/scripts/check_launch_day_rollover.py --output Backend/proof/launch-day-rollover.json
python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json
python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json
python3 Backend/scripts/check_app_store_assets.py --allow-incomplete --output Backend/proof/app-store-assets.json
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
```

## 禁写项

不得在本文、截图、proof 或仓库中写入恢复密钥、验证码、完整手机号、Apple ID 邮箱、付款信息、D-U-N-S 完整编码、证书私钥、provisioning profile 文件、AppSecret、短信 secret、OBS AK/SK、token、对象存储 key 或真实宝宝照片。
