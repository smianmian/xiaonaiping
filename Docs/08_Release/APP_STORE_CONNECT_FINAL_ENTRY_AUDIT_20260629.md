# 小奶瓶 App Store Connect 终填审计表

日期：2026-06-29

状态：用于 App Store Connect 草稿最后一次人工粘贴和截图前核对。本文只记录字段、证据路径和复跑命令，不写入恢复密钥、验证码、AppSecret、D-U-N-S 编码完整值、证书私钥、Apple ID 邮箱、完整手机号或测试员邮箱。

结构化人工填写执行包：`Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260629.json`。该包状态为 `entry-session-plan-not-evidence`，只约束 App Store Connect 填写顺序、页面证据路径、停机条件、脱敏项和复跑命令；不是 App Store Connect 人工证据，不能作为提交许可。

结构化提交前预检包：`Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260629.json`。该包状态为 `preflight-plan-not-evidence`，只约束 ASC-08 Submit for Review 页面、必须变绿的 proof、红灯证据、脱敏项和复跑命令；不是 App Store Connect 人工证据，不能作为提交许可。

## 同一天同一轮环境

| 项 | 填写或检查口径 |
| --- | --- |
| App 版本 | `1.0`，与 `APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md` 一致 |
| Build 号 | App Store Connect 选中的 build 与 `06-testflight.png`、`12-real-device-regression.md` 一致 |
| 安装来源 | TestFlight 或 Xcode 签名真机包，不能用模拟器或 iOS 27 截图替代 |
| Apple Developer 主体 | D-U-N-S 交付后完成 Apple Developer Organization enrollment |
| Team ID | 从 Apple Developer 后台确认；如不同于 `L2TYJNDTJK`，先同步工程、AASA、证书和描述文件 |

## 终填字段核对

| App Store Connect 字段 | 本轮填写值或源文件 | 人工证据 |
| --- | --- | --- |
| App 名称 | 小奶瓶 | `01-company-account.png` |
| 副标题 | 温柔记录宝宝每一天 | `APP_STORE_CONNECT_COPY_PASTE_20260629.md` |
| Bundle ID | `com.mewpow.xiaonaiping` | `AppleDeveloper/14-bundle-id-capabilities.png` |
| SKU | `xiaonaiping-ios-1` | App Store Connect App 信息页截图 |
| 主类别：生活 | `APP_STORE_CONNECT_FILL_SHEET_20260629.md` | App 信息页截图 |
| 第二类别：留空 | `APP_STORE_CONNECT_FILL_SHEET_20260629.md` | App 信息页截图 |
| 价格/地区 | Free；Specific Countries or Regions -> China mainland | `02-mainland-availability.png` |
| 隐私政策 URL | https://api.mewpow.com/xiaonaiping/privacy | 公开 URL 可访问证明；`04-privacy-label.png` |
| 技术支持 URL | https://api.mewpow.com/xiaonaiping/support | 公开 URL 可访问证明 |
| 用户协议 URL | https://api.mewpow.com/xiaonaiping/terms | 公开 URL 可访问证明 |
| 关键词 | `宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册` | `APP_STORE_CONNECT_COPY_PASTE_20260629.md` |
| 描述 | 从 `APP_STORE_CONNECT_COPY_PASTE_20260629.md` 粘贴 | 字段粘贴后人工复核 |
| 新版本说明 | 从 `APP_STORE_CONNECT_COPY_PASTE_20260629.md` 粘贴 | 字段粘贴后人工复核 |
| 审核备注 | 从 `APP_STORE_CONNECT_COPY_PASTE_20260629.md` 的审核备注粘贴 | App Review Notes 截图或导出 |
| Sign-In Information | 从 `APP_STORE_REVIEW_INFORMATION_20260629.md` 填入私密字段 | `11-test-account-redacted.json` |
| App Privacy | 以 `APP_STORE_PRIVACY_ANSWERS_20260629.md` 和 `APP_STORE_PRIVACY_LABEL.json` 逐项填写 | `04-privacy-label.png` |
| 年龄分级 | 按 `APP_STORE_AGE_RATING_ANSWERS_20260629.md` 填写；不选择 Kids 类目 | `17-age-rating-result.png` 或 `17-age-rating-result.pdf` |
| 版本发布设置 | `APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md`；手动发布，Phased release off | Version 信息页截图 |
| 截图 | `10-final-screenshots/` 上传 5 张最终图 | `10-final-screenshots/` 和 App Store Connect 截图页 |

## 终填字段源文件一致性锁

App Store Connect 页面值不能成为唯一来源。人工粘贴时只允许从下表源文件复制；如果页面值和源文件不一致，先修正 App Store Connect 或源文件，再重跑 `check_app_store_connect_materials.py` 和 `check_app_store_submission_packet.py`，不提交审核。

| 字段 | 唯一来源 | 回填证据 |
| --- | --- | --- |
| App 名称 / 副标题 / 主类别 / 第二类别 | `APP_STORE_CONNECT_FILL_SHEET_20260629.md`、`APP_STORE_CONNECT_COPY_PASTE_20260629.md` | `AppStoreConnect/ASC-01-app-information.png` |
| 关键词 / 描述 / 审核备注 | `APP_STORE_CONNECT_FILL_SHEET_20260629.md`、`APP_STORE_CONNECT_COPY_PASTE_20260629.md` | `AppStoreConnect/ASC-02-version-information.png`、`AppStoreConnect/ASC-06-review-information.png` |
| 年龄分级 | `APP_STORE_AGE_RATING_ANSWERS_20260629.md` | `AppStoreConnect/ASC-05-age-rating.png`、`17-age-rating-result.png` 或 `.pdf` |
| 隐私政策 URL / 技术支持 URL / 用户协议 URL | `APP_STORE_CONNECT_FILL_SHEET_20260629.md`、`APP_STORE_PRIVACY_LABEL.json`、`Backend/static/privacy.html`、`Backend/static/support.html`、`Backend/static/terms.html` | `AppStoreConnect/ASC-01-app-information.png`、公开 URL proof |
| App Privacy | `APP_STORE_PRIVACY_ANSWERS_20260629.md`、`APP_STORE_PRIVACY_LABEL.json` | `AppStoreConnect/ASC-04-app-privacy.png`、`04-privacy-label.png` |
| Sign-In Information | `APP_STORE_REVIEW_INFORMATION_20260629.md`、`11-test-account-redacted.json` | `AppStoreConnect/ASC-06-review-information.png` |
| 版本发布设置 | `APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md` | `AppStoreConnect/ASC-03-pricing-availability-release.png`、`AppStoreConnect/ASC-07-build-testflight-link.png` |
| 截图上传顺序 | `SCREENSHOT_PLAN.md`、`APP_STORE_EVIDENCE_CHECKLIST_20260629.md`、`10-final-screenshots/PROVENANCE.json` | `AppStoreConnect/ASC-02-version-information.png` |

- [ ] 不得只改 App Store Connect 页面而不回写源文件。
- [ ] 任一字段改字后，先同步填表版、可复制字段包、终填审计表和对应答案表，再重跑材料 gate。
- [ ] 回填截图只证明页面已经填入，不替代源文件、外部后台证据、TestFlight 或真机回归。

## 字段预算

关键词按 UTF-8 bytes 计算；其他字段按 App Store Connect 字符数口径复核。人工粘贴前如果改字，一个字段改完必须重跑 `check_app_store_connect_materials.py`。

| 字段 | 限制 | 当前 | 余量 |
| --- | --- | --- | --- |
| App 名称 | 30 字符 | 3 字符 | 剩余 27 字符 |
| 副标题 | 30 字符 | 9 字符 | 剩余 21 字符 |
| 关键词 | 100 UTF-8 bytes | 73 bytes | 剩余 27 bytes |
| 宣传文本 | 170 字符 | 31 字符 | 剩余 139 字符 |
| 描述 | 4000 字符 | 488 字符 | 剩余 3512 字符 |
| 新版本说明 | 4000 字符 | 53 字符 | 剩余 3947 字符 |
| 审核备注 | 4000 字符 | 887 字符 | 剩余 3113 字符 |

## 小奶瓶审核口径边界

这些内容必须和 App Store Connect 描述、审核备注、年龄分级和截图保持一致。

- 疫苗模板仅用于记录和提醒，不提供医疗诊断、治疗建议或专业疫苗建议；实际接种安排请以医生和当地官方信息为准。
- 喝奶提醒和 Live Activity 只展示用户手动设置的下一次提醒，不根据奶量、月龄、传感器或健康数据自动推算喂养时间。
- 短信服务商、微信开放平台、OBS、APP 备案、真实短信实发、TestFlight 或 iOS 26.5 签名真机包任一未通过时，不得提交审核。
- 恢复密钥测试账号只进 App Review Information 私密字段；恢复密钥、验证码、完整手机号、AppSecret、Apple ID 邮箱和测试员邮箱不得进入仓库材料。

## 外部证据同轮索引

这些文件必须在同一天同一轮归档；没有真实文件前不得声称完成。

| 证据 | 证明内容 |
| --- | --- |
| `01-company-account.png` | App Store Connect / Apple Developer 主体、Organization、Team ID |
| `02-mainland-availability.png` | 中国大陆首发地区选择 |
| `03-app-filing.pdf` 或 `03-app-filing.png` | APP 备案、ICP 或适用判断状态 |
| `04-privacy-label.png` | App Store Privacy 逐项填写结果 |
| `05-signed-archive.png` | App Store Distribution Archive 成功 |
| `06-testflight.png` | TestFlight 构建处理完成并可测试 |
| `07-sms-provider.png` | 短信签名、模板和真实发送成功记录 |
| `08-wechat-open-platform.png` | 微信开放平台 AppID、Bundle ID、URL Scheme、Universal Link |
| `09-obs-policy.png` | OBS bucket、区域、加密、生命周期和删除验证 |
| `10-final-screenshots/` | 最终 App Store 截图 |
| `11-test-account-redacted.json` | 恢复密钥测试账号脱敏证明 |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归 |
| `17-age-rating-result` | App Store Connect 年龄分级结果 |

## App Store Connect 截图上传矩阵

官方规格：https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/ 。App Store Connect 截图上传每个设备槽位为一到十张，格式只能使用 `.jpeg`、`.jpg`、`.png`。当前 5 张候选图已固定文案顺序，但正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图。

| 槽位 | 当前口径 | 回填证据 |
| --- | --- | --- |
| iPhone 6.9" display | 官方可接受竖图尺寸包含 1260 x 2736、1290 x 2796、1320 x 2868 | `AppStoreConnect/ASC-02-version-information.png` 必须保留截图上传顺序、选中 build 和上传后的 5 张图 |
| 当前候选图 | 当前候选为 iPhone 17 Pro Max / iPhone 6.9" display / 1320 x 2868 | 只作为画面、文案和尺寸候选；不能把 Debug simulator 候选图声称为 TestFlight、签名真机或 App Store Connect 上传最终证据 |
| 候选来源 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json` | 候选来源必须说明 iOS 26.5 Debug simulator、截图 seed data、生产 API URL injection，且不替代 TestFlight 或签名真机包最终证据 |
| 最终上传来源 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json` | 必须写明 `final-app-store-upload`、`iPhone 6.9" display`、iOS 26.5、`TestFlight` 或 `Xcode 签名真机包`，并列出五张 finalFiles |
| iPad 槽位 | 工程目标为 iPhone only，`TARGETED_DEVICE_FAMILY=1` | 如果 App Store Connect 要求 iPad 截图，先复核工程 target family、Bundle ID capabilities 和 App Store Connect 平台设置，不临时上传拉伸图 |

## App Store Connect 页面回填证据索引

App Store Connect 草稿人工填写完成后，把页面截图或 PDF 放进 `Docs/08_Release/AppStoreEvidence/AppStoreConnect/`。这些文件只证明页面值已经按本表回填，不替代 `01-company-account.png`、`02-mainland-availability.png`、`04-privacy-label.png`、`05-signed-archive.png`、`06-testflight.png`、`12-real-device-regression.md` 或 `17-age-rating-result`。

| 文件名 | 必须保留 | 必须遮挡 | 回填核对 |
|---|---|---|---|
| `AppStoreConnect/ASC-01-app-information.png` | App 名称、副标题、Bundle ID、SKU、主类别生活、第二类别留空、版权、隐私政策 URL、技术支持 URL、用户协议 URL | Apple ID 邮箱、电话、付款信息、D-U-N-S 编码完整值 | 对照 `APP_STORE_CONNECT_FILL_SHEET_20260629.md` 和 `APP_STORE_CONNECT_COPY_PASTE_20260629.md` |
| `AppStoreConnect/ASC-02-version-information.png` | Version `1.0`、选中 build、描述、关键词、新版本说明、截图上传顺序 | 测试员邮箱、Apple ID 邮箱、任何恢复密钥或验证码 | 对照 `APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md`、`10-final-screenshots/` 和 `06-testflight.png` |
| `AppStoreConnect/ASC-03-pricing-availability-release.png` | Free、Specific Countries or Regions -> China mainland、手动发布、Phased release off | 付款信息、税务信息、无关地区账号资料 | 对照 `02-mainland-availability.png` 和版本发布设置表 |
| `AppStoreConnect/ASC-04-app-privacy.png` | Tracking 为 No、Data Linked to You / Data Not Linked to You、Health and Fitness / Usage Data / Diagnostics 填写结果 | Apple ID 邮箱、账号私密信息 | 对照 `APP_STORE_PRIVACY_ANSWERS_20260629.md` 和 `04-privacy-label.png` |
| `AppStoreConnect/ASC-05-age-rating.png` | 4+ 或 App Store Connect 自动计算结果、Kids Category 未选择、Regulated Medical Device 为 No | Apple ID 邮箱、电话、付款信息 | 对照 `APP_STORE_AGE_RATING_ANSWERS_20260629.md` 和 `17-age-rating-result.png` / `.pdf` |
| `AppStoreConnect/ASC-06-review-information.png` | Sign-in required、恢复密钥测试账号说明、审核备注、联系人字段已填 | 恢复密钥、验证码、完整手机号、Apple ID 邮箱、联系人完整电话 | 对照 `APP_STORE_REVIEW_INFORMATION_20260629.md` 和 `11-test-account-redacted.json` |
| `AppStoreConnect/ASC-07-build-testflight-link.png` | 选中 build、TestFlight 构建状态、版本和 build 与真机回归一致 | 测试员邮箱、Apple ID 邮箱、内部备注 | 对照 `06-testflight.png` 和 `12-real-device-regression.md` |
| `AppStoreConnect/ASC-08-submit-review-precheck.png` | Submit for Review 前页面无未处理警告；所有字段与本审计表一致 | 恢复密钥、验证码、完整手机号、AppSecret、证书私钥、Apple ID 邮箱 | 重跑 `check_app_store_connect_materials.py`、`check_app_store_evidence.py --allow-incomplete`、`check_launch_objective_audit.py --allow-incomplete` |

## Submit for Review 总守卫

点击 Submit for Review 前必须先在本机生成同一天同一轮的小奶瓶提交 proof 组。只有下面 proof 全部为真，才允许点击提交审核；任一项为红时，只能保存草稿和归档页面回填证据。

提交前必须打开 `Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260629.json` 逐项核对：`app-store-evidence.json`、`production-readiness.json`、`launch-objective-audit.json`、`testflight-regression-plan.json`、`provider-evidence-materials.json`、`mainland-filing-materials.json` 和 `signed-archive-testflight-materials.json` 均需达到该包声明的 required state；`ASC-08-submit-review-precheck.png` 只能作为页面预检截图，不能替代 D-U-N-S、Archive、TestFlight、短信、微信、OBS、备案、隐私标签、最终截图或 iOS 26.5 真机回归证据。Emotion Isle / cross-app 状态只可作为历史参考，不能作为小奶瓶 Submit for Review 许可。

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json
python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json
python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json
python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json
python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json
python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json
```

- [ ] `Backend/proof/launch-objective-audit.json` 的 `ready=true`。
- [ ] `Backend/proof/production-readiness.json` 的 `ready=true`。
- [ ] `Backend/proof/app-store-evidence.json` 的 `ready=true`，且真实 App Store / 外部平台 / TestFlight / iOS 26.5 真机证据均已归档。
- [ ] `Backend/proof/testflight-regression-plan.json` 的 `passed=true`。
- [ ] `Backend/proof/provider-evidence-materials.json` 的 `passed=true`。
- [ ] `Backend/proof/mainland-filing-materials.json` 的 `passed=true`。
- [ ] `Backend/proof/signed-archive-testflight-materials.json` 的 `passed=true`。
- [ ] 如果 `ready=false`、`passed=false` 或仍有 `failedRequiredChecks` / `missingEvidence`，不点击 Submit for Review。

## 人工填写后回填验收模板

App Store Connect 草稿填完但点击 Submit for Review 之前，复制下面清单到当天私有执行记录或工单中填写。仓库只保留本模板和脱敏证据路径，不记录恢复密钥、验证码、AppSecret、D-U-N-S 编码完整值、Apple ID 邮箱、完整手机号或测试员邮箱。

- [ ] App Store Connect 页面值已逐项对照 `APP_STORE_CONNECT_FILL_SHEET_20260629.md` 和 `APP_STORE_CONNECT_COPY_PASTE_20260629.md`。
- [ ] `AppStoreConnect/ASC-01-app-information.png` 到 `AppStoreConnect/ASC-08-submit-review-precheck.png` 已按页面回填证据索引归档并脱敏。
- [ ] App 名称 / 副标题 / 描述 / 关键词 / 主类别 / 第二类别 与源文件一致。
- [ ] 隐私政策 URL / 技术支持 URL / 用户协议 URL 与源文件、公开页面和 `APP_STORE_PRIVACY_LABEL.json` 一致。
- [ ] App Privacy / 年龄分级 / 审核备注 与 `APP_STORE_PRIVACY_ANSWERS_20260629.md`、`APP_STORE_AGE_RATING_ANSWERS_20260629.md` 和 `APP_STORE_REVIEW_INFORMATION_20260629.md` 一致。
- [ ] App Store Connect 选中 build 与 `06-testflight.png`、`12-real-device-regression.md` 和 `APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md` 一致。
- [ ] 截图上传顺序与 `10-final-screenshots/`、`APP_STORE_EVIDENCE_CHECKLIST_20260629.md` 和 `SCREENSHOT_PLAN.md` 一致。
- [ ] 价格、首发地区和手动发布设置与 `APP_STORE_VERSION_RELEASE_SETTINGS_20260629.md` 和 `02-mainland-availability.png` 一致。
- [ ] `production-readiness.json`、`launch-objective-audit.json`、`app-store-evidence.json` 均为 ready=true。
- [ ] `testflight-regression-plan.json`、`provider-evidence-materials.json`、`mainland-filing-materials.json`、`signed-archive-testflight-materials.json` 均为 passed=true。
- [ ] 若任一页面值与源文件不一致，先修正 App Store Connect 或源文件，再重跑本页复跑命令；不提交审核。
- [ ] 回填记录不得写入恢复密钥、验证码、AppSecret、D-U-N-S 编码完整值、Apple ID 邮箱、完整手机号或测试员邮箱。

## 复跑命令

```bash
python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json
python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json
python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json
python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json
python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json
```

## 禁写和提交边界

1. 不得写入恢复密钥。
2. 不得写入验证码。
3. 不得写入 AppSecret。
4. 不得写入 D-U-N-S 编码完整值。
5. 不得写入证书私钥。
6. 不得写入 Apple ID 邮箱、完整手机号或测试员邮箱。
7. 不得把 debug code、placeholder `wx...`、模拟器截图或 iOS 27 真机截图当作提交证据。
8. 不得在 `production-readiness.json` 或 `launch-objective-audit.json` 仍为红色时声称完成。
9. 不得声称完成 App Store Connect 人工证据、TestFlight、签名归档、备案、短信、微信或 OBS，除非对应真实文件已归档并通过 gate。
10. 不得在小奶瓶提交 proof 组存在 `ready=false` 或 `passed=false` 时点击 Submit for Review。
