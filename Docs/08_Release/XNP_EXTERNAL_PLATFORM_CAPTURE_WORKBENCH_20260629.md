# 小奶瓶外部平台现场采集工作台

日期：2026-06-29

结论：这份工作台用于现场采集微信开放平台、短信服务商、OBS、备案、隐私标签和生产 proof。它不是提交许可，也不代表这些外部平台已经配置完成；只有小奶瓶自己的 `provider-evidence-materials.json`、`mainland-filing-materials.json`、`signed-archive-testflight-materials.json`、`app-store-evidence.json`、`production-readiness.json`、`launch-objective-audit.json` 和 iOS 26.5 真机回归均通过后，才允许进入 App Store Connect 提交审核。

来源文件：

- `Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260629.json`
- `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260629.md`
- `Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260629.md`
- `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json`
- `Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md`
- `Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260629.md`
- `Backend/proof/production-readiness-20260629T-current.json`
- `Backend/proof/provider-evidence-materials.json`
- `Backend/proof/mainland-filing-materials.json`
- `Backend/proof/signed-archive-testflight-materials.json`

## 1. 文件落点

所有人工证据只允许进入：

`Docs/08_Release/AppStoreEvidence/`

现场完成后再复制结构化结果模板，不要直接改模板本体：

- 从 `Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json` 复制到 `Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.json`。
- 只有真实完成微信开放平台、Universal Link/AASA、短信服务商、真实实发、OBS、备案、隐私标签和生产 proof 采集后，结果文件才允许填写 `status: captured-live-external-platforms`。
- 结果文件必须记录 `canSubmitAtCapture`、`redactionReviewed`、小奶瓶 required proof 组、各平台截图路径、复跑 proof 和真机联动状态；它只是同轮证据索引，不能替代截图/PDF、真实短信实发、生产 proof、真机回归或小奶瓶 proof 组。

## 1.1 同轮一致性和哈希清单

从模板复制出的 `EXTERNAL-PLATFORM-CAPTURE-RESULT.json` 必须填写 `sameRoundEvidenceManifest`，并至少记录：

- `captureRoundId`，例如 `xnp-external-platforms-2026-06-29`。
- `SHA-256` / `sha256` 哈希：每个最终证据文件、短信实发 proof、微信配置 proof、AASA proof、OBS proof 和生产 proof 都必须有哈希。
- `Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260629.json`
- `Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260629.json`
- `Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260629.json`
- `Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260629.json`
- `Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260629.json`
- `Backend/proof/auth-providers-sms-live-20260629T-current.json`
- `Backend/proof/wechat-client-configuration-20260629T-current.json`
- `Backend/proof/universal-links-20260629T-current.json`
- `Backend/proof/storage-backend-20260629T-current.json`
- `Backend/proof/production-readiness-20260629T-current.json`

只有采集时间、文件日期、SHA-256 和复跑 proof 都属于同一轮采集，才能把 `allDependenciesCurrentAndPassed` 改为 true。不能跨天拼接，不能把 2026-06-27 的截图、微信临时图、短信旧发送记录、旧 OBS proof 或旧生产 proof 混入 2026-06-29 结果文件。

允许的外部平台文件名：

- `07-sms-provider.png` 或 `.pdf`
- `08-wechat-open-platform.png` 或 `.pdf`
- `08b-wechat-universal-link-aasa.png` 或 `.pdf`
- `09-obs-policy.png` 或 `.pdf`
- `03-app-filing.png` 或 `.pdf`
- `04-privacy-label.png`
- `12-real-device-regression.md`

不接受桌面、下载目录、微信临时目录、聊天截图原图、外部绝对路径或未脱敏原图作为最终证据。

## 2. 微信开放平台现场采集

采集前先打开：`Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json`

目标文件：`Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png`

页面范围：

1. 微信开放平台移动应用详情页。
2. AppID 区域。
3. App 名称、应用图标和开发者主体/运营主体区域。
4. Bundle ID 区域。
5. URL Scheme 区域。
6. Universal Link 区域。
7. 移动应用审核/配置状态。

必须可见：

- AppID，格式为 `wx + 16 hex`。
- App 名称：小奶瓶。
- 应用图标为小奶瓶正式图标或 App Store Connect 同一图标。
- 若页面展示开发者主体/运营主体，必须对应深圳市闪现生活科技有限公司或与 App Store Connect 主体一致。
- Bundle ID：`com.mewpow.xiaonaiping`。
- URL Scheme equal to AppID。
- Universal Link：`https://api.mewpow.com/xiaonaiping/wechat/`。
- 移动应用审核/配置状态必须为 `审核通过 / 已上线 / 可用于微信登录`，不能是 `待审核`、`未通过`、`开发中`、`资料未完善` 或同类未完成状态。
- 以上 AppID、Bundle ID、URL Scheme、Universal Link、App 名称、图标和审核通过状态必须属于同一移动应用，不能拼接不同 App 的截图。

必须遮挡：

- AppSecret。
- 管理员账号。
- 完整手机号。
- 邮箱完整值。
- 一次性验证码。
- token。

采集后立刻复跑：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/check_wechat_client_configuration.py \
  --output Backend/proof/wechat-client-configuration-20260629T-current.json
python3 Backend/scripts/verify_auth_providers.py \
  --live-check \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260629T-current.json \
  --output Backend/proof/auth-providers-20260629T-current.json \
  --allow-incomplete
```

通过口径：后台截图、iOS Release 包、服务端 provider 三边一致，且微信开放平台移动应用已经审核通过或已上线。如果状态是待审核、未通过、开发中、资料未完善，`xnp.auth.wechatProvider` 继续保持 blocker。不能只截图微信后台就声称微信登录可用。

## 3. Universal Link / AASA 现场采集

目标文件：`Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png`

页面范围：

1. Apple Developer Associated Domains。
2. AASA URL 浏览器响应。
3. 微信开放平台 Universal Link 输入框。
4. iOS Release 包 proof 摘要。

必须可见：

- 新 Team ID + `com.mewpow.xiaonaiping`。
- `applinks:api.mewpow.com`。
- `https://api.mewpow.com/.well-known/apple-app-site-association`。
- `/xiaonaiping/wechat/`。
- `application/json` 或 Apple 可接受的 JSON 内容。
- 微信开放平台 Universal Link 与 Release 包 `XNPWeChatUniversalLink` 一致。

必须遮挡：

- Apple ID 邮箱。
- 完整手机号。
- AppSecret。
- token。
- 私钥。
- 证书密码。

采集后立刻复跑：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/check_universal_links.py \
  --output Backend/proof/universal-links-20260629T-current.json
python3 Backend/scripts/check_ios_app_bundle.py \
  --app /path/to/XiaoNaiPing.app \
  --output Backend/proof/ios-app-bundle-20260629T-current-ios265.json
```

通过口径：必须拿到 Apple 新组织 Team ID 后再做最终验收；旧 Team ID 只能作为过渡记录，不能作为提交证据。

## 4. 短信服务商现场采集

采集前先打开：`Docs/08_Release/AppStoreEvidence/_templates/sms-provider-evidence.template.json`

目标文件：`Docs/08_Release/AppStoreEvidence/07-sms-provider.png`

页面范围：

1. 服务商控制台签名页。
2. 验证码模板页。
3. 发送记录页。
4. 真实实发验证结果。

必须可见：

- 短信服务商名称。
- 短信签名。
- 验证码模板，必须能证明只用于账号登录/验证。
- 模板审核状态和发送区域。
- 发送成功记录。
- 真实实发验证。
- 手机号中段打码后的收信号码。
- 模板内容不含营销、不含医疗、不含育儿建议，不写健康建议、喂养建议、医疗诊断、治疗建议或专业疫苗建议。

必须遮挡：

- `XNP_SMS_SECRET`。
- webhook secret。
- AccessKey。
- SecretKey。
- 完整手机号。
- 验证码明文。
- token。

采集后立刻复跑：

`XNP_SMS_TEST_PHONE` 只放在本地私密 shell 或私有 env 文件中；不要 echo，不要把完整手机号写入命令历史、日志、截图、proof、提交说明或仓库文档。

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/verify_auth_providers.py \
  --live-check \
  --send-test-sms \
  --require-sms-live-send \
  --phone-env XNP_SMS_TEST_PHONE \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260629T-current.json \
  --output Backend/proof/auth-providers-sms-live-20260629T-current.json \
  --allow-incomplete
```

通过口径：短信 provider 服务器 proof 只能证明后端配置存在，不能替代服务商截图和真实短信实发。真实实发 proof 必须单独保存为 `Backend/proof/auth-providers-sms-live-20260629T-current.json`，并且只有它和 `Backend/proof/auth-providers-20260629T-current.json` 都通过后，才能把 sms-live proof 同步到稳定 alias `Backend/proof/auth-providers.json`。

## 5. OBS / 对象存储现场采集

采集前先打开：`Docs/08_Release/AppStoreEvidence/_templates/obs-policy-evidence.template.json`

目标文件：`Docs/08_Release/AppStoreEvidence/09-obs-policy.png`

页面范围：

1. 华为云 OBS bucket 或小奶瓶专用 prefix。
2. 私有访问策略。
3. 服务端上传、下载、删除路径 proof。
4. 加密、生命周期或删除策略。
5. 账号删除清理对象存储数据的验证结果。

必须可见：

- 华为云 OBS。
- bucket 或专用 prefix。
- 私有访问策略。
- 上传、下载、删除能力。
- 账号删除会清理宝宝照片和对象存储数据。
- `storageBackendProofCurrent` 相关 proof 摘要。

必须遮挡：

- AK/SK。
- SecretKey。
- 临时签名 URL。
- 完整对象 key。
- 真实宝宝照片。
- 内部私有路径。

采集后立刻复跑：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/verify_storage_backend.py \
  --output Backend/proof/storage-backend-20260629T-current.json
```

通过口径：必须证明账号删除链路会清理对应云端对象，不能只证明 bucket 存在。

## 6. 备案、隐私标签和 URL 现场采集

采集前先打开：`Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json`

目标文件：

- `Docs/08_Release/AppStoreEvidence/03-app-filing.png` 或 `.pdf`
- `Docs/08_Release/AppStoreEvidence/04-privacy-label.png`
- `Docs/08_Release/AppStoreEvidence/01-company-account.png`
- `Docs/08_Release/AppStoreEvidence/02-mainland-availability.png`

必须可见：

- 主体：深圳市闪现生活科技有限公司。
- App 名称：小奶瓶。
- 可售地区：China mainland / 中国大陆。
- APP 备案号或适用判断证据。
- App Privacy 与 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` 一致。
- Tracking 为否。
- 隐私政策 URL：`https://api.mewpow.com/xiaonaiping/privacy`。
- 用户协议 URL：`https://api.mewpow.com/xiaonaiping/terms`。
- 技术支持 URL：`https://api.mewpow.com/xiaonaiping/support`。

必须遮挡：

- Apple ID 邮箱。
- 完整手机号。
- 付款信息。
- 证件细节。
- D-U-N-S 完整值。
- 验证码。

通过口径：小奶瓶不接入 HealthKit、传感器、医院系统或第三方健康数据源；不提供压力评估、心理健康判断、健康建议、喂养建议、医疗诊断、治疗建议或专业疫苗建议。

换句话说，小奶瓶不提供医疗诊断。

## 6.1 现场字段采集表

现场截图时按这张表逐项核对。截图可以证明页面状态，但只有截图、live check、iOS 26.5 真机或 TestFlight 回归，以及小奶瓶 App Store evidence / production readiness / launch objective audit / provider / filing / signed archive gates 全部通过后，才算提交链路闭环。

| 平台 | 必须看到 | 写入结果文件 | 缺失时结论 |
| --- | --- | --- | --- |
| 微信开放平台 | AppID 格式、App 名称、正式图标、主体、Bundle ID、URL Scheme、Universal Link、审核通过状态 | `wechatOpenPlatform.status`、`wechatOpenPlatform.evidencePath`、`wechatOpenPlatform.redactionChecked` | 继续阻断 `xnp.auth.wechatProvider` |
| Universal Link / AASA | 新 Team ID、`com.mewpow.xiaonaiping`、`applinks:api.mewpow.com`、AASA URL、`/xiaonaiping/wechat/` | `wechatUniversalLinkAasa.status`、`wechatUniversalLinkAasa.teamIdRedacted`、`wechatUniversalLinkAasa.sameRoundAsIosBundle` | 不能把微信登录写成可用 |
| 短信服务商 | 服务商名称、短信签名、验证码模板、模板审核状态、发送成功记录、真实实发验证 | `smsProvider.status`、`smsLiveSend.status`、`smsLiveSend.proofPath` | 只能说服务商或实发未闭环 |
| OBS / 对象存储 | 华为云 OBS、bucket 或 prefix、私有访问策略、上传/下载/删除、账号删除清理结果 | `huaweiObs.status`、`huaweiObs.storageProofPath`、`huaweiObs.accountDeletionCleanup` | 不能把云同步/照片清理写成完成 |
| 备案 / 隐私标签 | 主体、App 名称、中国大陆可售、备案号或适用判断、App Privacy、Tracking=No | `mainlandFiling.status`、`privacyLabel.status`、`privacyLabel.sameAsJsonSource` | 不能在 App Store Connect 或审核备注里写已完成 |
| 生产 proof | deployment、remote API、storage、auth providers、iOS bundle、App Store evidence、production readiness | `productionProofs.status`、`productionProofs.failedProofs`、`productionProofs.canSyncStableAlias` | 不能同步 stable alias，不能提交 |

所有 `status` 只能填真实状态，例如 `captured-live`、`blocked-missing-secret`、`blocked-pending-review`、`blocked-failed-live-check`、`blocked-needs-ios265-regression`。不要用 `done` 或 `ready` 掩盖缺失项。

## 7. 外部平台 proof 入库闸门

`07-sms-provider.*`、`08-wechat-open-platform.*`、`08b-wechat-universal-link-aasa.*`、`09-obs-policy.*`、`03-app-filing.*` 和 `04-privacy-label.png` 只有通过入库闸门后才能作为最终人工证据。

入库前必须逐项确认：

- 原始截图或 PDF 已保留在现场私密目录，脱敏版才放入 `Docs/08_Release/AppStoreEvidence/`。
- 文件名必须使用本工作台指定名称；不能使用 `IMG_*.PNG`、微信转发图、下载目录临时图、聊天临时目录素材、拼接长图或无法证明来源的截图。
- 每个文件必须写入同日采集记录，包含采集人、采集时间、登录账号主体、页面 URL 或平台名称、对应 App、对应 Bundle ID、遮挡项和通过/失败结论。
- 微信开放平台截图必须证明同一 AppID、App 名称、正式图标、主体、Bundle ID、URL Scheme、Universal Link 和审核通过状态来自同一移动应用；若状态仍是待审核、未通过、开发中或资料未完善，只能放入 `AppStoreEvidence/failed/`。
- 短信服务商截图必须和真实实发 proof、短信签名、验证码模板、发送成功记录互相引用；只有服务端 provider proof 通过但没有真实实发截图时，只能记为后端配置已存在，不能入库为 `07-sms-provider` 完成。
- OBS 截图必须和 storage proof、私有访问策略、上传/下载/删除、账号删除清理验证互相引用；只有 bucket 截图或策略截图不能单独入库。
- APP 备案和隐私标签截图必须和 App Store Connect 草稿、隐私政策 URL、用户协议 URL、技术支持 URL 和中国大陆可售地区互相引用。
- 入库后必须复跑 `check_app_store_evidence.py`、`check_production_readiness.py`、`check_launch_objective_audit.py`、`check_provider_evidence_materials.py`、`check_mainland_filing_materials.py` 和 `check_signed_archive_testflight_materials.py`；只复制图片不算完成。

入库失败的素材保留在 `Docs/08_Release/AppStoreEvidence/failed/`，并在失败记录中写明原因：字段缺失、状态未通过、主体不一致、Bundle ID 不一致、URL Scheme 不一致、Universal Link 不一致、未脱敏、来源不明、跨天素材或真机链路未闭环。

## 8. 真机/TestFlight 现场联动

外部平台截图不是最终闭环。截图后还必须补：

- `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md`
- iOS 26.5 TestFlight。
- 手机号登录。
- 微信登录。
- 恢复密钥登录。
- 云同步。
- 云恢复。
- 账号删除。
- 通知权限。
- 灵动岛喝奶提醒开关。
- 锁屏 Live Activity。
- 桌面/锁屏小组件。

所有 RD 文件不低于 10KB。iOS 27、模拟器、placeholder、空模板、聊天截图原图和旧日期 proof 不能替代。

## 9. 最终复跑顺序

截图和 proof 刷新后，按顺序跑：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/check_app_store_evidence.py \
  --allow-incomplete \
  --date 2026-06-29 \
  --output Backend/proof/app-store-evidence-20260629T-current.json

python3 Backend/scripts/check_production_readiness.py \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260629T-current.json \
  --remote-proof Backend/proof/remote-api-20260629T-current.json \
  --storage-proof Backend/proof/storage-backend-20260629T-current.json \
  --auth-providers-proof Backend/proof/auth-providers-20260629T-current.json \
  --ios-app-bundle-proof Backend/proof/ios-app-bundle-20260629T-current-ios265.json \
  --app-store-evidence Backend/proof/app-store-evidence-20260629T-current.json \
  --require-huawei-obs \
  --require-screenshots \
  --require-app-store-evidence \
  --live-check \
  --output Backend/proof/production-readiness-20260629T-current.json \
  --allow-incomplete
```

然后同步稳定 alias：

- `Backend/proof/huawei-baota-deploy.json`
- `Backend/proof/remote-api.json`
- `Backend/proof/storage-backend.json`
- `Backend/proof/auth-providers.json`
- `Backend/proof/ios-app-bundle.json`
- `Backend/proof/app-store-evidence.json`
- `Backend/proof/production-readiness.json`

最后复跑小奶瓶提交前材料 gates：

```bash
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit-20260629T-current.json
python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json
python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json
python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json
```

## 10. 禁止项

- 不写当前可以提交审核。
- 不写微信登录已经可用，除非微信开放平台、服务端 provider、iOS Release 包和 iOS 26.5 真机回归全部通过。
- 不写短信已经可用，除非服务商截图、真实实发、服务端 proof 和真机登录都通过。
- 不写 OBS 已完成，除非 storage proof、后台截图和账号删除清理验证都通过。
- 不把短信 provider 服务器 proof 当成短信服务商截图。
- 不把后台截图当成真机登录 proof。
- 不把旧 Team ID 当成新组织 Team ID。
- 不保存完整手机号、验证码、恢复密钥、AppSecret、AK/SK、token、私钥、证书密码或真实宝宝照片。
