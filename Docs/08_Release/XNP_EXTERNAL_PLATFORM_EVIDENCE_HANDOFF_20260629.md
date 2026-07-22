# 小奶瓶外部平台证据交接包

日期：2026-06-29

用途：把小奶瓶当前还能推进的微信开放平台、短信服务商、OBS、备案、隐私和生产 proof 补齐路径固定下来。本文件不代表已经可提交，也不包含 AppSecret、短信密钥、OBS AK/SK、验证码、恢复密钥或完整手机号。

## 当前结论

小奶瓶当前提交红项集中在：

- `xnp.ios.wechatNativeConfig`
- `xnp.ios.wechatUrlScheme`
- `xnp.auth.smsProvider`
- `xnp.auth.wechatProvider`
- `xnp.production.ready`
- `xnp.manualEvidence.ready`
- `xnp.testflightManualEvidence`

短信服务商材料和采集模板已经准备好，但 2026-06-29T-current 的 auth provider proof 仍未通过：`deploymentProofReadable`、`smsProviderConfigured`、`wechatProviderConfigured`。短信 provider 服务器 proof 只能证明后端配置存在；只有当天部署 proof 可读、生产短信 webhook 私有环境变量齐、`07-sms-provider` 服务商截图存在、真实 `--send-test-sms --require-sms-live-send` proof 通过，才能把短信链路写成闭环。微信 provider 和 iOS 微信包体配置仍需要真实微信开放平台移动应用。

## 1. 微信开放平台证据

采集模板：`Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json`。模板只用于核对字段和脱敏，不是证据，不能改名成 `08-wechat-open-platform.*`。

证据文件：`Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png` 或 `.pdf`

必须可见：

1. 微信开放平台移动应用 AppID，格式为 `wx + 16 hex`。
2. App 名称：小奶瓶；应用图标为小奶瓶正式图标或 App Store Connect 同一图标。
3. 若页面展示开发者主体/运营主体，必须对应深圳市闪现生活科技有限公司或与 App Store Connect 主体一致。
4. Bundle ID：`com.mewpow.xiaonaiping`。
5. URL Scheme equal to AppID。
6. Universal Link：`https://api.mewpow.com/xiaonaiping/wechat/`。
7. 移动应用审核/配置状态必须为 `审核通过 / 已上线 / 可用于微信登录`，不能是 `待审核`、`未通过`、`开发中`、`资料未完善` 或同类未完成状态。
8. 以上 AppID、Bundle ID、URL Scheme、Universal Link、App 名称、图标和审核通过状态必须属于同一移动应用，不能拼接不同 App 的截图。

必须隐藏：

- AppSecret
- 管理员手机号完整值
- 微信后台账号信息
- token / 密钥 / 验证码

服务端只在私有环境配置：

- `XNP_WECHAT_APP_ID`
- `XNP_WECHAT_APP_SECRET`

iOS Release 包只注入：

- `XNPWeChatAppID`
- `XNPWeChatURLScheme`
- `CFBundleURLTypes`
- `XNPWeChatUniversalLink`

### 微信 Universal Link / AASA 证据

证据文件：

- `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` 或 `.pdf`
- `Backend/proof/universal-links-20260629T-current.json`
- `Backend/proof/wechat-client-configuration-20260629T-current.json`

必须可见：

1. Apple 新组织 Team ID 获批后，AASA 中的 App ID 使用 `新 Team ID.com.mewpow.xiaonaiping`，不能继续使用旧 Team ID。
2. `https://api.mewpow.com/.well-known/apple-app-site-association` 可访问，返回 `application/json` 或 Apple 可接受的 JSON 内容。
3. AASA 覆盖 `applinks`，路径或 components 覆盖 `/xiaonaiping/wechat/`。
4. Xcode / Apple Developer Associated Domains 包含 `applinks:api.mewpow.com`。
5. 微信开放平台后台 Universal Link 与 iOS Release 包中的 `XNPWeChatUniversalLink` 完全一致。
6. 真机微信登录回调从微信回到 `com.mewpow.xiaonaiping`，不是只停留在微信授权页。

必须隐藏：

- Apple 登录邮箱
- 完整手机号
- AppSecret
- 任何一次性验证码、token、私钥或证书密码

如果 D-U-N-S 后拿到新 Team ID，必须先更新 AASA、Associated Domains 和 Release 包，再重跑 `Backend/proof/universal-links-20260629T-current.json`、`Backend/proof/wechat-client-configuration-20260629T-current.json`、`Backend/proof/ios-app-bundle-20260629T-current-ios265.json` 和 `Backend/proof/auth-providers-20260629T-current.json`。不能只改微信开放平台后台截图。

## 2. 短信服务商证据

采集模板：`Docs/08_Release/AppStoreEvidence/_templates/sms-provider-evidence.template.json`。模板只用于核对字段和脱敏，不是证据，不能改名成 `07-sms-provider.*`。

证据文件：`Docs/08_Release/AppStoreEvidence/07-sms-provider.png` 或 `.pdf`

必须可见：

1. 短信服务商名称。
2. 短信签名。
3. 验证码模板，必须能证明只用于账号登录/验证。
4. 模板审核状态和发送区域。
5. 发送成功记录。
6. 至少一次真实实发验证，手机号中段打码。
7. 模板内容不含营销、不含医疗、不含育儿建议，不写健康建议、喂养建议、医疗诊断、治疗建议或专业疫苗建议。

必须隐藏：

- `XNP_SMS_SECRET`
- webhook secret
- AccessKey
- 完整手机号
- 验证码明文

服务器配置 proof 只能证明 provider 存在；短信服务商截图和真实实发验证必须单独归档。

## 3. OBS / 存储证据

采集模板：`Docs/08_Release/AppStoreEvidence/_templates/obs-policy-evidence.template.json`。模板只用于核对字段和脱敏，不是证据，不能改名成 `09-obs-policy.*`。

证据文件：`Docs/08_Release/AppStoreEvidence/09-obs-policy.png` 或 `.pdf`

必须可见：

1. 华为云 OBS bucket 或小奶瓶专用 prefix。
2. 私有访问策略。
3. 服务端上传、下载、删除路径。
4. 加密、生命周期或删除策略。
5. 账号删除会清理宝宝照片和对象存储数据的验证结果。

必须隐藏：

- OBS AK/SK
- 完整对象 key
- 临时签名 URL
- 宝宝真实照片

提交前必须刷新当天 storage proof，不能用旧日期 proof 替代 `storageBackendProofCurrent`。

## 4. 备案、隐私和 App Store Connect 证据

采集模板：`Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json`。模板只用于核对字段和脱敏，不是证据，不能改名成 `01-...`、`02-...`、`03-...`、`04-...` 或 `17-...`。

证据文件：

- `Docs/08_Release/AppStoreEvidence/01-company-account.png`
- `Docs/08_Release/AppStoreEvidence/02-mainland-availability.png`
- `Docs/08_Release/AppStoreEvidence/03-app-filing.png` 或 `.pdf`
- `Docs/08_Release/AppStoreEvidence/04-privacy-label.png`

必须覆盖：

1. App Store Connect 主体是深圳市闪现生活科技有限公司。
2. 首发只选择 China mainland。
3. APP 备案号或适用判断证据。
4. App Privacy 与 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` 一致。
5. 隐私政策 URL：`https://api.mewpow.com/xiaonaiping/privacy`。
6. 用户协议 URL：`https://api.mewpow.com/xiaonaiping/terms`。
7. 技术支持 URL：`https://api.mewpow.com/xiaonaiping/support`。

小奶瓶不接入 HealthKit、传感器、医院系统或第三方健康数据源；不提供压力评估、心理健康判断、健康建议、喂养建议、医疗诊断、治疗建议或专业疫苗建议。换句话说，小奶瓶不提供医疗诊断。

## 5. 生产 proof 刷新顺序

提交前按这个顺序刷新，所有 `20260629T-current` 文件都要来自同一天同一轮操作。不得写入 root 密码、SSH key、AK/SK、AppSecret、完整手机号或验证码到命令、日志、截图或仓库文档。

```bash
cd /Users/smianmian/Downloads/小奶瓶

XNP_DEPLOY_HOST=root@YOUR_SERVER Backend/deploy/deploy-huawei-baota.sh

python3 Backend/scripts/collect_deployment_proof.py \
  --env-file /srv/xiaonaiping/shared/.env.production \
  --target huawei-baota \
  --deploy-root /srv/xiaonaiping \
  --current-path /srv/xiaonaiping/current \
  --python-venv /srv/xiaonaiping/current/.venv \
  --linux-user xiaonaiping \
  --systemd-service xiaonaiping \
  --base-url https://api.mewpow.com/xiaonaiping \
  --service-active \
  --public-internal-blocked \
  --include-process-env \
  --output Backend/proof/huawei-baota-deploy-20260629T-current.json

python3 Backend/scripts/verify_remote_api.py \
  --base-url https://api.mewpow.com/xiaonaiping \
  --output Backend/proof/remote-api-20260629T-current.json

python3 Backend/scripts/verify_storage_backend.py \
  --output Backend/proof/storage-backend-20260629T-current.json

python3 Backend/scripts/verify_auth_providers.py \
  --live-check \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260629T-current.json \
  --output Backend/proof/auth-providers-20260629T-current.json \
  --allow-incomplete

# XNP_SMS_TEST_PHONE 只放在本地私密 shell 或私有 env 文件中；不要 echo，不要把完整手机号写入命令历史、日志、截图、proof、提交说明或仓库文档。
python3 Backend/scripts/verify_auth_providers.py \
  --live-check \
  --send-test-sms \
  --require-sms-live-send \
  --phone-env XNP_SMS_TEST_PHONE \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260629T-current.json \
  --output Backend/proof/auth-providers-sms-live-20260629T-current.json \
  --allow-incomplete

python3 Backend/scripts/check_wechat_client_configuration.py \
  --output Backend/proof/wechat-client-configuration-20260629T-current.json

python3 Backend/scripts/check_ios_app_bundle.py \
  --app /path/to/XiaoNaiPing.app \
  --output Backend/proof/ios-app-bundle-20260629T-current-ios265.json

python3 Backend/scripts/check_app_store_evidence.py \
  --allow-incomplete \
  --output Backend/proof/app-store-evidence-20260629T-current.json

python3 Backend/scripts/check_production_readiness.py \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260629T-current.json \
  --remote-proof Backend/proof/remote-api-20260629T-current.json \
  --storage-proof Backend/proof/storage-backend-20260629T-current.json \
  --auth-providers-proof Backend/proof/auth-providers-sms-live-20260629T-current.json \
  --ios-app-bundle-proof Backend/proof/ios-app-bundle-20260629T-current-ios265.json \
  --app-store-evidence Backend/proof/app-store-evidence-20260629T-current.json \
  --require-huawei-obs \
  --require-screenshots \
  --require-app-store-evidence \
  --live-check \
  --output Backend/proof/production-readiness-20260629T-current.json \
  --allow-incomplete

cp Backend/proof/huawei-baota-deploy-20260629T-current.json Backend/proof/huawei-baota-deploy-current.json
cp Backend/proof/huawei-baota-deploy-20260629T-current.json Backend/proof/huawei-baota-deploy.json
cp Backend/proof/remote-api-20260629T-current.json Backend/proof/remote-api.json
cp Backend/proof/storage-backend-20260629T-current.json Backend/proof/storage-backend-current.json
cp Backend/proof/storage-backend-20260629T-current.json Backend/proof/storage-backend.json
cp Backend/proof/auth-providers-sms-live-20260629T-current.json Backend/proof/auth-providers.json
cp Backend/proof/ios-app-bundle-20260629T-current-ios265.json Backend/proof/ios-app-bundle.json
cp Backend/proof/app-store-evidence-20260629T-current.json Backend/proof/app-store-evidence.json
cp Backend/proof/production-readiness-20260629T-current.json Backend/proof/production-readiness.json

Backend/scripts/run_launch_readiness.sh \
  --env-file /srv/xiaonaiping/shared/.env.production \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260629T-current.json \
  --storage-proof Backend/proof/storage-backend-20260629T-current.json \
  --auth-providers-proof Backend/proof/auth-providers-sms-live-20260629T-current.json \
  --app-path /path/to/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260629.log \
  --ios-device-log Backend/proof/xcodebuild-debug-ios265-20260629.log \
  --live-check
```

最终必须让 `Backend/proof/huawei-baota-deploy-20260629T-current.json`、`Backend/proof/remote-api-20260629T-current.json`、`Backend/proof/storage-backend-20260629T-current.json`、`Backend/proof/auth-providers-20260629T-current.json`、`Backend/proof/auth-providers-sms-live-20260629T-current.json`、`Backend/proof/ios-app-bundle-20260629T-current-ios265.json`、`Backend/proof/app-store-evidence-20260629T-current.json` 和 `Backend/proof/production-readiness-20260629T-current.json` 都变绿。

`Backend/proof/auth-providers-20260629T-current.json` 保留配置 proof 和微信 provider 检查；`Backend/proof/auth-providers-sms-live-20260629T-current.json` 保留真实实发 proof。只有两份 auth provider proof 都通过，且 `07-sms-provider.png` / `.pdf` / `.json` 已归档后，才能把 sms-live proof 同步到稳定 alias。

同轮 current proof 变绿后，必须同步到稳定 alias，至少包括 `Backend/proof/huawei-baota-deploy.json`、`Backend/proof/remote-api.json`、`Backend/proof/storage-backend.json`、`Backend/proof/auth-providers.json`、`Backend/proof/ios-app-bundle.json`、`Backend/proof/app-store-evidence.json` 和 `Backend/proof/production-readiness.json`。其中 `Backend/proof/auth-providers.json` 必须来自 `Backend/proof/auth-providers-sms-live-20260629T-current.json`，不能来自未实发短信的配置 proof。后续 `production-readiness.json`、`launch-objective-audit.json` 和人工汇报默认读取稳定 alias；如果只生成 `20260629T-current` 文件但不同步 alias，会继续出现稳定 proof 读旧结果的误判。

如果 `production-readiness-20260629T-current.json` 仍红，优先看这些检查名：`deploymentProofCurrent`、`storageBackendProofCurrent`、`authProvidersProofPassed`、`appStoreManualEvidenceReady`。这些红项只能用当天真实 proof、真实服务商配置和人工证据归档解决，不能用旧 JSON、模拟器截图或模板文档替代。

## Current proof 日期滚动规则

`YYYYMMDDT-current` 必须以实际执行当天日期生成。今天是 2026-06-29 时，新的部署、远端 API、storage、auth providers、iOS app bundle、App Store evidence 和 production readiness 输出都应使用 `20260629T-current`；不得继续把 `20260627T-current` 当成 fresh proof。

跨日执行时按这个顺序处理：

1. 先新建当天 `YYYYMMDDT-current` proof，不要只改文件名。
2. 确认 proof 内时间戳、部署时间、storage 验证时间、auth providers 验证时间和人工证据归档时间属于同一天同一轮。
3. 当前轮 `production-readiness.json` 和 `launch-objective-audit.json` 只读取已同步的稳定 alias。
4. 如果跨日，先新建当天 current proof，再同步 alias；不要把旧日期 current 文件复制成新日期文件。
5. 同一天同一轮 proof 变绿后，再同步稳定 alias：`huawei-baota-deploy.json`、`remote-api.json`、`storage-backend.json`、`auth-providers.json`、`ios-app-bundle.json`、`app-store-evidence.json` 和 `production-readiness.json`。
6. 汇报时同时写明 `YYYYMMDDT-current` 文件名和稳定 alias 是否已同步，避免 `production-readiness.json` / `launch-objective-audit.json` 继续读取旧结果。

## 外部平台证据索引与脱敏复核

上线当天把下面每一项逐条填进私有执行记录；本仓库只保存脱敏后的截图、PDF、JSON 和 proof。任一截图、proof 或 alias 缺失时，不提交 App Store Connect 审核。

| 证据 / proof | 必须保留 | 必须遮挡 | 复跑或复核命令 |
|---|---|---|---|
| `07-sms-provider.png` | 短信服务商、签名、账号登录/验证验证码模板、模板审核状态、发送区域、发送成功状态、脱敏手机号片段；模板不含营销、不含医疗、不含育儿建议 | `AccessKey`、Secret、`XNP_SMS_SECRET`、完整手机号、验证码 | `verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE` |
| `08-wechat-open-platform.png` | AppID、Bundle ID、URL Scheme、Universal Link、移动应用审核/配置状态 | `AppSecret`、管理员账号、完整手机号、验证码、token | `check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260629T-current.json` |
| `08b-wechat-universal-link-aasa.png` / `Backend/proof/universal-links-20260629T-current.json` / `Backend/proof/wechat-client-configuration-20260629T-current.json` | Team ID、Bundle ID、AASA endpoint、`applinks:api.mewpow.com`、`/xiaonaiping/wechat/`、`XNPWeChatUniversalLink` | Apple ID 邮箱、完整手机号、`AppSecret`、验证码、token | `check_universal_links.py --output Backend/proof/universal-links-20260629T-current.json`；随后重跑微信客户端配置检查 |
| `09-obs-policy.png` / `Backend/proof/storage-backend-20260629T-current.json` | OBS bucket/prefix、区域、私有访问、加密、生命周期、删除验证 | `AK/SK`、`HUAWEI_OBS_SECRET_ACCESS_KEY`、完整对象 key、真实宝宝照片、内部私有路径 | `verify_storage_backend.py --output Backend/proof/storage-backend-20260629T-current.json` |
| `Backend/proof/huawei-baota-deploy-20260629T-current.json` | 服务状态、部署路径、HTTPS base URL、internal 阻断结果、进程/环境字段是否脱敏 | root 密码、SSH key、私有 env 原文、token、恢复密钥 | `collect_deployment_proof.py --output Backend/proof/huawei-baota-deploy-20260629T-current.json` |
| `Backend/proof/remote-api-20260629T-current.json` | 生产 API HTTPS 健康检查、公开接口行为、版本/时间戳 | token、恢复密钥、验证码、完整手机号 | `verify_remote_api.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/remote-api-20260629T-current.json` |
| `Backend/proof/auth-providers-20260629T-current.json` | 手机号 provider、微信 provider、debug code 拒绝、配置 proof | `AppSecret`、`XNP_SMS_SECRET`、完整手机号、验证码、token | `verify_auth_providers.py --live-check --output Backend/proof/auth-providers-20260629T-current.json` |
| `Backend/proof/auth-providers-sms-live-20260629T-current.json` | 手机号 provider、微信 provider、debug code 拒绝、真实实发 proof 和真实短信实发结论 | `AppSecret`、`XNP_SMS_SECRET`、完整手机号、验证码、token | `verify_auth_providers.py --live-check --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE --output Backend/proof/auth-providers-sms-live-20260629T-current.json` |
| `Backend/proof/production-readiness-20260629T-current.json` | `deploymentProofCurrent`、`storageBackendProofCurrent`、`authProvidersProofPassed`、`appStoreManualEvidenceReady` 和最终 `passed` | root 密码、SSH key、`AccessKey`、`AK/SK`、`AppSecret`、完整手机号、验证码 | `check_production_readiness.py --output Backend/proof/production-readiness-20260629T-current.json` |
| `01-company-account.png` / `02-mainland-availability.png` / `03-app-filing` / `04-privacy-label.png` | 公司主体、中国大陆可售区、APP 备案或适用判断、隐私标签填写结果 | Apple ID 邮箱、电话、付款信息、证件细节、D-U-N-S 完整值 | `check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence-20260629T-current.json` |
| 稳定 alias：`Backend/proof/huawei-baota-deploy.json`、`Backend/proof/remote-api.json`、`Backend/proof/storage-backend.json`、`Backend/proof/auth-providers.json`、`Backend/proof/app-store-evidence.json`、`Backend/proof/production-readiness.json` | 必须和同轮 `20260629T-current` proof 同步 | 不保留旧红项、不混入旧日期 proof | `check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json` 后再跑提交包和总 readiness |

## 外部平台上线当天执行记录模板

复制下面清单到当天的私有执行记录或工单中填写；所有项必须来自同一天同一轮操作。不要写入 root 密码、SSH key、AK/SK、AppSecret、完整手机号、验证码、恢复密钥、token、证书私钥或真实宝宝照片。

- [ ] 08-wechat-open-platform.png 已归档。
- [ ] 08b-wechat-universal-link-aasa.png 已归档。
- [ ] 微信 AppID、URL Scheme、Universal Link 已与 Release 包和服务端 env 对齐。
- [ ] AASA、Associated Domains、Release 包和微信开放平台 Universal Link 已同轮核对。
- [ ] auth-providers-20260629T-current.json 已证明微信 provider。
- [ ] auth-providers-sms-live-20260629T-current.json 已证明真实短信实发。
- [ ] 07-sms-provider.png 已归档。
- [ ] verify_auth_providers.py --send-test-sms --require-sms-live-send 已完成真实实发验证。
- [ ] 09-obs-policy.png 已归档。
- [ ] storage-backend-20260629T-current.json 已通过。
- [ ] 01-company-account.png、02-mainland-availability.png、03-app-filing、04-privacy-label 已归档。
- [ ] production-readiness-20260629T-current.json 已变绿。
- [ ] 已同步稳定 alias，且 auth-providers.json 来自 auth-providers-sms-live-20260629T-current.json。
- [ ] 未记录 root 密码、SSH key、AK/SK、AppSecret、完整手机号、验证码、恢复密钥或 token。
- [ ] 如果任一项未通过，不提交 App Store Connect 审核。

## 6. 真机 / TestFlight 证据

证据文件：`Docs/08_Release/AppStoreEvidence/12-real-device-regression.md`

必须是 iOS 26.5 签名真机包或 iOS 26.5 TestFlight。必须覆盖：

- 冷启动
- 手机号登录
- 微信登录
- 恢复密钥登录
- 云同步
- 云恢复
- 账号删除
- 通知权限
- 灵动岛喝奶提醒开关
- 锁屏 Live Activity
- 桌面/锁屏小组件

RD-01 到 RD-24 必须全部为“通过”，证据/备注必须指向 `Docs/08_Release/AppStoreEvidence/` 内真实存在且不低于 10KB 的脱敏截图、录屏或 PDF。iOS 27、模拟器、模板文档、空截图、debug code、placeholder `wx...` 都不能替代。

## 7. 提交前判断

只有小奶瓶自己的 `provider-evidence-materials.json`、`mainland-filing-materials.json`、`signed-archive-testflight-materials.json`、`app-store-evidence.json`、`production-readiness.json`、`launch-objective-audit.json` 和 iOS 26.5 真机回归全部 ready/passed，才允许进入 App Store Connect 提交审核。任何单个文档、截图、旧 proof 或跨项目 `canSubmit` 值都不能单独代表可提交。
