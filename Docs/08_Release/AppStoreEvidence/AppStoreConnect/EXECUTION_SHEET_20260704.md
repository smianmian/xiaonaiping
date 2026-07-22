# 小奶瓶 App Store Connect 回填截图现场执行单

日期：2026-07-04

状态：现场拍摄和填表用，不是已完成证据。只有小奶瓶提交 proof 组全部 `ready=true` / `passed=true` 后，才允许把这些截图作为提交前核对材料。

源文件：

- `../../APP_STORE_CONNECT_FILL_SHEET_20260704.md`
- `../../APP_STORE_CONNECT_COPY_PASTE_20260704.md`
- `../../APP_STORE_SUBMISSION_PACKET.md`
- `../../APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260704.md`
- `../../../../Backend/proof/app-store-evidence.json`
- `../../../../Backend/proof/production-readiness.json`
- `../../../../Backend/proof/launch-objective-audit.json`
- `../../../../Backend/proof/testflight-regression-plan.json`
- `../../../../Backend/proof/provider-evidence-materials.json`
- `../../../../Backend/proof/mainland-filing-materials.json`
- `../../../../Backend/proof/signed-archive-testflight-materials.json`

保存目录：`Docs/08_Release/AppStoreEvidence/AppStoreConnect/`

## 现场规则

- 每张截图都必须来自 App Store Connect 真实页面，不能用 Markdown、草稿表格、历史截图或模拟图替代。
- 截图只证明页面值已经回填，不替代真实公司主体、备案、签名、TestFlight、final screenshot provenance、短信服务商、微信开放平台、OBS、iOS 26.5 真机回归、灵动岛/锁屏/小组件视觉 proof。
- 完整手机号、验证码、恢复密钥、AppSecret、D-U-N-S 编码完整值、Apple ID 邮箱、付款信息、税务信息、测试员邮箱、token、证书私钥都必须遮挡。
- App Review Information 可以填写恢复密钥测试账号、短信服务商和微信开放平台说明，但截图入库前必须脱敏。
- final screenshot provenance 未完成前，不能把候选截图当最终上传证据；最终必须有 `10-final-screenshots/UPLOAD_PROVENANCE.json`，且证明 iOS 26.5、TestFlight 或 Xcode 签名真机包、同一版本/build。

## 截图清单

| 文件 | 页面 | 必须看见 | 必须隐藏 | 通过口径 |
| --- | --- | --- | --- | --- |
| `ASC-01-app-information.png` | App Information | App 名称、小奶瓶、Bundle ID、SKU、主类别、版权、隐私政策 URL、技术支持 URL、用户协议 URL | Apple ID 邮箱、完整手机号、付款信息、D-U-N-S 编码完整值 | 字段和 `APP_STORE_CONNECT_COPY_PASTE_20260704.md` 一致 |
| `ASC-02-version-information.png` | Version Information | Version、选中 build、描述、关键词、新版本说明、截图上传顺序 | 测试员邮箱、Apple ID 邮箱、验证码 | 不把短信、微信、生产云同步写成未证实可用 |
| `ASC-03-pricing-availability-release.png` | Pricing and Availability / Version Release | Free、China mainland、手动发布 | 付款信息、税务信息、无关账号资料 | 未完成备案、TestFlight 和真机 proof 前不自动发布 |
| `ASC-04-app-privacy.png` | App Privacy | Tracking=No、隐私标签数据类别、与 `APP_STORE_PRIVACY_LABEL.json` 一致 | Apple ID 邮箱、账号私密信息 | 不声明追踪，不暴露账号私密信息 |
| `ASC-05-age-rating.png` | Age Rating | Age Rating、Kids Category 未选择、疫苗记录/提醒相关回答、Regulated Medical Device 回答 | Apple ID 邮箱、完整手机号、付款信息 | 疫苗模板仅用于记录和提醒，不提供专业疫苗建议 |
| `ASC-06-review-information.png` | App Review Information | Sign-in required、审核备注、联系人字段已填、短信服务商、微信开放平台、恢复密钥测试说明 | 验证码、完整手机号、恢复密钥、AppSecret、Apple ID 邮箱 | 私密字段脱敏后入库 |
| `ASC-07-build-testflight-link.png` | Build / TestFlight | 选中 build、TestFlight 构建状态、版本和 build 与真机回归一致 | 测试员邮箱、Apple ID 邮箱、内部备注 | 不用未处理完成的 build 当提交证据 |
| `ASC-08-submit-review-precheck.png` | Submit for Review precheck | 无未处理警告、字段与提交包一致、小奶瓶提交 proof 组全部 ready/passed | 验证码、完整手机号、AppSecret、证书私钥、Apple ID 邮箱 | 只有小奶瓶提交 proof 组通过后才保留最终提交前截图 |
| `ASC-PRIVACY-AGE-REVIEW-RESULT.json` | ASC-04/05/06 结果复核 | `status: captured-live-privacy-age-review`、ASC-04/05/06、`04-privacy-label`、`17-age-rating-result`、`11-test-account-redacted`、answer-sheet matching、post-result gates | 恢复密钥、验证码、完整手机号、Apple ID 邮箱、联系人完整电话、AppSecret、短信密钥、微信密钥、OBS AK/SK、付款/税务信息、完整 D-U-N-S 编码 | 先从 `ASC-PRIVACY-AGE-REVIEW-RESULT.template.json` 复制；模板不是证据，不能替代隐私标签、年龄分级结果、审核账号、production readiness 或 iOS 26.5 真机 proof |
| `ASC-BACKFILL-RESULT.json` | 现场回填结果 | `status: captured-live-backfill`、`fieldEntryChecks` 逐项确认 App 名称/副标题/描述/关键词/分类/年龄分级/隐私政策 URL/技术支持 URL/用户协议 URL/审核备注、`canSubmitAtCapture`、`screenshotFiles`、`redactionReviewed`、小奶瓶 `app-store-evidence` / `production-readiness` / `launch-objective-audit` / `testflight-regression-plan` / `provider-evidence-materials` / `mainland-filing-materials` / `signed-archive-testflight-materials` proof | 完整手机号、验证码、恢复密钥、AppSecret、短信密钥、微信密钥、OBS AK/SK、证书私钥、Apple ID 邮箱、付款信息、完整 D-U-N-S 编码 | 先从 `ASC-BACKFILL-RESULT.template.json` 复制；模板不是证据，结果文件也不替代小奶瓶 proof 组 |

## 字段冻结

完成回填截图后进入字段冻结，并填写 `ASC-BACKFILL-RESULT.json` 的 `fieldEntryChecks`。不得静默改字段。若现场修改描述、关键词、新版本说明、截图顺序、隐私标签、年龄分级、审核备注、选中 build、价格/可售地区，必须写变更原因，补拍对应 ASC 截图，更新 `ASC-BACKFILL-RESULT.json`，并重跑 `check_app_store_connect_materials.py`、`check_app_store_connect_evidence_materials.py`、`check_app_store_submission_packet.py`、`check_app_store_evidence.py --allow-incomplete`、`check_testflight_regression_plan.py --allow-incomplete`、`check_provider_evidence_materials.py`、`check_mainland_filing_materials.py`、`check_signed_archive_testflight_materials.py`、`check_production_readiness.py --allow-incomplete`、`check_launch_objective_audit.py --allow-incomplete`。小奶瓶 proof 组仍红时，不得作为提交许可；Emotion Isle / cross-app 状态只能作为历史参考，不能授权小奶瓶 Submit for Review。

## 小奶瓶审核边界

- 目标用户是父母和照护者。
- 疫苗模板仅用于记录和提醒，实际接种安排以医生和当地官方信息为准。
- 不生成健康建议、压力提醒、喂养建议或医疗判断。
- 灵动岛/锁屏 Live Activity 只显示用户设置的下一次喝奶提醒。
- 桌面/锁屏小组件只读展示今日摘要。
- 不接入 HealthKit、传感器、医院系统或第三方健康数据源。
- 微信开放平台、短信服务商、OBS、APP 备案、真实短信实发、iOS 26.5 真机回归任一未通过时，不能提交审核。
- AppSecret、短信密钥、微信密钥、恢复密钥和完整手机号只能进入 Apple 后台私密字段或本地脱敏截图，不能进仓库。

## 现场完成记录

| 项 | 状态 | 备注 |
| --- | --- | --- |
| ASC-01 | 待拍摄 |  |
| ASC-02 | 待拍摄 |  |
| ASC-03 | 待拍摄 |  |
| ASC-04 | 待拍摄 |  |
| ASC-05 | 待拍摄 |  |
| ASC-06 | 待拍摄 |  |
| ASC-07 | 待拍摄 |  |
| ASC-08 | 待拍摄 |  |
| ASC-PRIVACY-AGE-REVIEW-RESULT | 待填写 | 从 `ASC-PRIVACY-AGE-REVIEW-RESULT.template.json` 复制，ASC-04/05/06 与隐私标签、年龄分级结果、审核账号脱敏证据齐全后再改为 `captured-live-privacy-age-review` |
| ASC-BACKFILL-RESULT | 待填写 | 从 `ASC-BACKFILL-RESULT.template.json` 复制，截图齐全且脱敏复核后再改为 `captured-live-backfill` |
