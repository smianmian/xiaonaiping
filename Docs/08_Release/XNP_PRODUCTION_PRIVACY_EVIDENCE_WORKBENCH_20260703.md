# 小奶瓶生产与隐私证据入库工作台

日期：2026-07-03

结论：这份工作台只用于整理生产 proof、隐私 URL、备案/隐私标签、OBS 和账号删除证据的同轮入库规则。它不是提交许可，也不代表生产环境、备案、微信、短信、OBS、TestFlight 或 Apple Developer 组织账号已经完成；只有小奶瓶自己的 App Store evidence、production readiness、launch objective audit、TestFlight regression、provider、filing 和 signed archive/TestFlight proof 全部 ready/passed 后，才允许进入 App Store Connect 提交审核。

来源文件：

- `Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_20260703.md`
- `Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json`
- `Docs/08_Release/MAINLAND_FILING_MATERIALS.md`
- `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json`
- `Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md`
- `Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260703.json`
- `Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260703.json`
- `Backend/proof/production-readiness-20260703T-current.json`
- `Backend/proof/public-pages.json`
- `Backend/proof/provider-evidence-materials.json`
- `Backend/proof/mainland-filing-materials.json`
- `Backend/proof/signed-archive-testflight-materials.json`

## 1. 生产 proof 入库范围

生产 proof 必须同时覆盖下面这些文件，不能只靠其中一个 JSON 或一张后台截图放行：

- `Backend/proof/huawei-baota-deploy-20260703T-current.json`
- `Backend/proof/remote-api-20260703T-current.json`
- `Backend/proof/storage-backend-20260703T-current.json`
- `Backend/proof/auth-providers-20260703T-current.json`
- `Backend/proof/ios-app-bundle-20260703T-current-ios265.json`
- `Backend/proof/app-store-evidence-20260703T-current.json`
- `Backend/proof/production-readiness-20260703T-current.json`

稳定 alias 只有在同日 current proof 通过后才能同步：

- `Backend/proof/huawei-baota-deploy.json`
- `Backend/proof/remote-api.json`
- `Backend/proof/storage-backend.json`
- `Backend/proof/auth-providers.json`
- `Backend/proof/ios-app-bundle.json`
- `Backend/proof/app-store-evidence.json`
- `Backend/proof/production-readiness.json`

当前生产 proof 状态快照：`Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260703.json`。该文件由 `python3 Backend/scripts/check_production_proof_refresh_status.py --date 2026-07-03 --allow-incomplete --output Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260703.json` 按当前本机 proof 文件状态生成，状态为 `current-proof-status-not-submit-permission`，当前 `stableAliasSyncAllowed=false`；`deploymentProofCurrent` 已存在但仍记录 OBS、短信和微信生产配置 blocker，`production-readiness-20260703T-current.json` 仍要求补当天 `/internal` 阻断证明，`missingProofs` 仅剩 `authProvidersSmsLiveCurrent`，`failedProofs` 包含 deployment proof blockers、auth provider、App Store evidence、production readiness、launch objective audit 和相关 stable alias；`secretScanFailures=0`。结论保持：current proof files are incomplete or failed; do not sync stable aliases。

## 1.0 外部平台结构化结果模板联动

生产 proof、隐私/备案和外部平台截图不能分散保存后靠人工口头对应。外部平台采集完成后，必须先从 `Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json` 复制生成 `EXTERNAL-PLATFORM-CAPTURE-RESULT.json`，再把状态填为 `captured-live-external-platforms`。

该结果文件必须保留：

- `sameRoundEvidenceManifest`：同一轮 `captureRoundId`、采集日期、`sha256`、`captureResultSha256`、依赖 proof 链接和同轮判断。
- `evidenceFileChecks`：每个截图或 proof 的 `fileSizeBytes`、`sha256`、`redactionChecked`、`sameRoundAsCapture`、`sourceIsAllowedEvidenceRoot`。
- `minimumFileSizeBytes=10240`，低于 10KB 的截图或 PDF 不入库。
- 允许入库目录只能是 `Docs/08_Release/AppStoreEvidence/`；失败材料只能进入 `Docs/08_Release/AppStoreEvidence/failed/`。
- 结果模板必须覆盖 `smsProvider`、`smsLiveSend`、`wechatOpenPlatform`、`wechatUniversalLinkAasa`、`huaweiObs`、`mainlandFiling`、`privacyLabel`。
- 必须交叉引用当天 `Backend/proof/auth-providers-sms-live-20260703T-current.json`、`Backend/proof/wechat-client-configuration-20260703T-current.json`、`Backend/proof/storage-backend-20260703T-current.json` 和 `Backend/proof/production-readiness-20260703T-current.json`。

只把 `07-sms-provider.png`、`08-wechat-open-platform.png`、`08b-wechat-universal-link-aasa.png`、`09-obs-policy.png`、`03-app-filing.png`、`04-privacy-label.png` 或 `17-age-rating-result.png` 复制到目录，不填写 `EXTERNAL-PLATFORM-CAPTURE-RESULT.json` 的同轮清单和逐文件哈希，不算生产/隐私 proof 完成。

## 1.1 生产 proof 字段回填表

这张表用于补生产 proof 时逐项对照。所有真实密钥、完整手机号、数据库密码、AK/SK、AppSecret 和验证码只进服务器环境或平台后台，不写进仓库、截图正文或 Markdown。

| 阻断项 | 需要的 proof | 通过标准 | 入库边界 |
| --- | --- | --- | --- |
| `productionSecretConfigured` | 当天部署 proof 和 secret 扫描结果 | 生产密钥已在服务器环境存在，仓库 secret 扫描为 0 | 不展示密钥值，只展示检查结果 |
| `productionDataDirConfigured` | 部署 proof、数据目录权限 proof | 生产数据目录存在、权限正确、不是本机临时目录 | 不展示私有绝对路径中的敏感用户名 |
| `mysqlDatabaseSelected` / `mysqlDatabaseEnvPresent` | MySQL 连接 proof 和环境变量存在性 proof | 生产使用 MySQL，不是 sqlite、mock 或本地测试库 | 不展示数据库密码、连接串和 root 账号 |
| `phoneLoginProviderConfigured` | `auth-providers-20260703T-current.json`、短信服务商截图、真实实发 proof | webhook provider、服务商模板、发送成功和 iOS 26.5 登录回归都通过 | 不展示完整手机号、验证码或 `XNP_SMS_SECRET` |
| `wechatLoginProviderConfigured` | 微信开放平台截图、服务端 provider proof、iOS bundle proof、真机登录 proof | AppID/AppSecret、URL Scheme、Universal Link、AASA 和真机回跳同轮一致 | 不展示 AppSecret、管理员账号或 token |
| `privateOperationsDashboardConfigured` | 生产后台访问控制 proof | 私有运维入口受控且不暴露给公网用户 | 不上传后台敏感数据截图 |
| `publicInternalDashboardBlocked` | `/internal`、admin/debug 公开阻断 proof | 公开网络访问被 403/404/登录保护拦截 | 不把可访问截图当通过 |
| `xiaonaipingProductionNamespaceConfigured` | 公开 URL、API 路由、部署 proof | 所有生产路径归属 `/xiaonaiping` namespace | 不混用一根呆毛或旧 namespace |
| `iosReleaseReadinessProofPassed` / `iosAppBundleProofPassed` | iOS 26.5 Release 包体 proof | Bundle ID、API URL、隐私清单、微信配置和无 debug endpoint 均通过 | 模拟器包不替代签名包或 TestFlight |
| `testFlightRegressionPlanProofPassed` / `appStoreAssetsProofPassed` | TestFlight 计划、最终截图 provenance、真机 RD 记录 | iOS 26.5 TestFlight 或签名真机证据齐全 | iOS 27、旧图和聊天转发图不能入库 |
| `authProvidersProofPassed` | 短信和微信 provider proof | 短信、微信两条链路都通过 live check | 任一 provider 未通过时不能同步 stable alias |

字段补齐后先更新 current proof，再由脚本决定是否允许同步稳定 alias；不要手工把 `stableAliasSyncAllowed` 改成 true。

## 2. 同轮证据规则

所有生产与隐私证据必须来自同一天、同一环境、同一 App、同一 Bundle ID、同一 base URL：

- 日期：2026-07-03。
- App：小奶瓶。
- Bundle ID：`com.mewpow.xiaonaiping`。
- Base URL：`https://api.mewpow.com/xiaonaiping`。
- 运行环境：华为云中国大陆生产环境。
- 对象存储：华为云 OBS。
- 真机证据：iOS 26.5 TestFlight 或 iOS 26.5 签名真机包。

不能把 iOS 27、模拟器、旧日期 proof、占位截图、聊天截图、微信临时目录素材、桌面/下载目录文件、空 JSON、手写说明、模板文件或本地 mock 当作生产 proof。

## 3. 隐私 URL 和公开页证据

必须证明以下 URL 可公开访问、使用 HTTPS、返回正式页面、归属 `xiaonaiping` namespace，且不暴露内部后台或 debug 文案：

- 隐私政策 URL：`https://api.mewpow.com/xiaonaiping/privacy`
- 用户协议 URL：`https://api.mewpow.com/xiaonaiping/terms`
- 技术支持 URL：`https://api.mewpow.com/xiaonaiping/support`

页面必须覆盖：

- 主体：深圳市闪现生活科技有限公司。
- App 名称：小奶瓶。
- 联系方式或支持入口。
- 账号删除、数据导出或数据删除说明。
- 不接入 HealthKit、传感器、医院系统或第三方健康数据源。
- 不提供压力评估、心理健康判断、健康建议、喂养建议、医疗诊断、治疗建议或专业疫苗建议。
- 不写 localhost、staging、internal、admin、debug、placeholder、待补充或测试文案。

复跑命令：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/check_public_pages.py \
  --base-url https://api.mewpow.com/xiaonaiping \
  --output Backend/proof/public-pages-20260703T-current.json
python3 Backend/scripts/check_legal_drafts.py \
  --output Backend/proof/legal-drafts-20260703T-current.json
```

## 4. 备案和隐私标签证据

目标文件：

- `Docs/08_Release/AppStoreEvidence/03-app-filing.png` 或 `.pdf`
- `Docs/08_Release/AppStoreEvidence/04-privacy-label.png` 或 `.pdf`
- `Docs/08_Release/AppStoreEvidence/17-age-rating-result.png` 或 `.pdf`

必须可见：

- 主体：深圳市闪现生活科技有限公司。
- App 名称：小奶瓶。
- China mainland / 中国大陆可售地区。
- APP 备案号、提交状态或适用判断证据。
- App Privacy 与 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` 一致。
- Tracking 为否。
- 年龄分级结果与 `Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260703.md` 一致。

必须遮挡：

- Apple ID 邮箱。
- 完整手机号。
- 证件细节。
- D-U-N-S 完整值。
- 验证码。
- 付款信息。

复跑命令：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/check_mainland_filing_materials.py \
  --output Backend/proof/mainland-filing-materials-20260703T-current.json
python3 Backend/scripts/check_app_store_connect_evidence_materials.py \
  --output Backend/proof/app-store-connect-evidence-materials-20260703-current.json
```

备案通过前不在公开页、App 内、审核备注或 App Store Connect 里写占位备案号。拿到备案号后再更新公开页和 App 内关于页，并重新跑公开页、审核备注、生产 readiness。

## 5. OBS 和账号删除证据

目标文件：

- `Docs/08_Release/AppStoreEvidence/09-obs-policy.png` 或 `.pdf`
- `Backend/proof/storage-backend-20260703T-current.json`

必须可见：

- 华为云 OBS。
- bucket 或小奶瓶专用 prefix。
- 私有访问策略。
- 加密、生命周期或删除策略。
- 上传、下载、删除 proof。
- 账号删除后宝宝照片和对象存储对象被清理。
- 只展示脱敏 bucket/prefix，不展示完整对象 key。

必须遮挡：

- AK/SK。
- SecretKey。
- 临时签名 URL。
- 完整对象 key。
- 真实宝宝照片。
- 内部私有路径。

复跑命令：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/verify_storage_backend.py \
  --output Backend/proof/storage-backend-20260703T-current.json
```

只有 bucket 截图不能证明 OBS 已完成；必须同时证明私有访问、服务端读写删除和账号删除清理链路。

## 6. 登录 provider 和真实实发证据

目标文件：

- `Docs/08_Release/AppStoreEvidence/07-sms-provider.png` 或 `.pdf`
- `Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png` 或 `.pdf`
- `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` 或 `.pdf`
- `Backend/proof/auth-providers-20260703T-current.json`

必须证明：

- 短信 provider 服务端配置通过不等于短信服务商截图通过。
- 短信必须有服务商签名、验证码模板、模板审核状态、发送成功记录和真实实发验证。
- 微信必须有同一 App 的 AppID、App 名称、小奶瓶正式图标、主体、Bundle ID、URL Scheme、Universal Link 和审核通过状态。
- 微信 AppID 必须是 `wx + 16 hex`。
- URL Scheme equal to AppID。
- Universal Link：`https://api.mewpow.com/xiaonaiping/wechat/`。
- AASA、Associated Domains、Team ID、`com.mewpow.xiaonaiping` 和微信 Universal Link 必须同轮一致。

复跑命令：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/verify_auth_providers.py \
  --live-check \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260703T-current.json \
  --output Backend/proof/auth-providers-20260703T-current.json \
  --allow-incomplete
```

缺微信 AppID/AppSecret、微信开放平台审核通过状态、真实短信实发或 iOS 26.5 真机登录证据时，不能把登录链路写成已完成。

## 6.1 私有配置执行顺序

这一段只用于现场操作，不是密钥清单。所有真实值只在服务器私有 env、平台后台或本机临时 shell 中设置；不得写进仓库、截图正文、命令输出、聊天记录或 App Store 审核备注。

1. 先在服务器私有 env 文件或平台 Secret 面板配置生产变量名：`XNP_SECRET_KEY`、`XNP_DATA_DIR`、`XNP_DATABASE_BACKEND=mysql`、`XNP_MYSQL_HOST`、`XNP_MYSQL_DATABASE`、`XNP_MYSQL_USER`、`XNP_MYSQL_PASSWORD`、`XNP_STORAGE_BACKEND=huawei_obs`、`HUAWEI_OBS_BUCKET`、`HUAWEI_OBS_PREFIX`、`HUAWEI_OBS_ENDPOINT`、`HUAWEI_OBS_ACCESS_KEY_ID`、`HUAWEI_OBS_SECRET_ACCESS_KEY`、`XNP_SMS_PROVIDER=webhook`、`XNP_SMS_WEBHOOK_URL`、`XNP_SMS_SECRET`、`XNP_WECHAT_APP_ID`、`XNP_WECHAT_APP_SECRET`、`XNP_WECHAT_URL_SCHEME`、`XNP_WECHAT_UNIVERSAL_LINK`、`XNP_ADMIN_TOKEN`。
2. 重启生产 API 后，先跑部署 proof 和公开页 proof，确认 base URL 仍是 `https://api.mewpow.com/xiaonaiping`，`/internal`、admin、debug 入口没有公开暴露。
3. 再跑 OBS proof，必须证明华为云 OBS 私有访问、上传、下载、删除和账号删除清理链路；只证明 bucket 存在不算。
4. 再跑短信 provider proof：先 `verify_auth_providers.py --live-check` 验证 provider 配置，再单独用 `--send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE` 做真实实发；`XNP_SMS_TEST_PHONE` 只能放本机临时 shell 或私有 env，不得写入文件。
5. 再跑微信 proof：服务端 `XNP_WECHAT_APP_ID` / `XNP_WECHAT_APP_SECRET`、iOS `XNPWeChatAppID`、URL Scheme、Universal Link、AASA、微信开放平台移动应用状态必须同轮一致。
6. 最后跑 iOS 26.5 Release 包检查、App Store evidence、production readiness、launch objective audit、TestFlight regression、provider evidence、mainland filing、signed archive/TestFlight materials 和 `PRODUCTION_PROOF_REFRESH_STATUS_20260703.json`。

禁止操作：

- 不运行会打印完整 env 的命令，例如 `env`、`printenv`、`set`、`export -p`、`cat .env`。
- 不把完整手机号、验证码、AppSecret、短信密钥、OBS AK/SK、MySQL 密码、Admin Token、对象 key、恢复密钥或真实宝宝照片放入 proof。
- 不把 `auth-providers-20260703T-current.json` 的 provider 配置通过，写成短信服务商截图、真实短信实发或 iOS 26.5 真机登录已通过。
- 不在 `production-readiness.json` 仍为 `ready=false` 时同步 stable alias。

## 7. 生产 readiness 复跑顺序

截图和 current proof 刷新后按顺序跑：

```bash
cd /Users/smianmian/Downloads/小奶瓶
python3 Backend/scripts/check_app_store_evidence.py \
  --allow-incomplete \
  --output Backend/proof/app-store-evidence-20260703T-current.json

python3 Backend/scripts/check_production_readiness.py \
  --base-url https://api.mewpow.com/xiaonaiping \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260703T-current.json \
  --remote-proof Backend/proof/remote-api-20260703T-current.json \
  --storage-proof Backend/proof/storage-backend-20260703T-current.json \
  --auth-providers-proof Backend/proof/auth-providers-20260703T-current.json \
  --ios-app-bundle-proof Backend/proof/ios-app-bundle-20260703T-current-ios265.json \
  --app-store-evidence Backend/proof/app-store-evidence-20260703T-current.json \
  --require-huawei-obs \
  --require-screenshots \
  --require-app-store-evidence \
  --live-check \
  --output Backend/proof/production-readiness-20260703T-current.json \
  --allow-incomplete
```

最后复跑小奶瓶提交前材料 gates：

```bash
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit-20260703T-current.json
python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json
python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json
python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json
python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json
```

## 8. 入库失败条件

出现以下任一情况，只能进入 `Docs/08_Release/AppStoreEvidence/failed/` 或保留在私密现场目录，不能作为可提交证据：

- production readiness 仍为 `ready=false`。
- `deploymentProofCurrent` 缺失、不是当天部署 proof，或仍记录 OBS、短信、微信、`/internal` 阻断等生产配置 blocker。
- `storageBackendProofCurrent` 缺失或不是华为云 OBS。
- `authProvidersProofPassed` 缺失或微信、短信任一真实链路未闭环。
- `iosAppBundleProofPassed` 缺失或不是 iOS 26.5 release 包。
- `appStoreManualEvidenceReady` 缺失。
- 备案/隐私标签/年龄分级截图不是 App Store Connect 当前版本。
- 文件名不是本工作台或 `CAPTURE_GUIDE.md` 指定名称。
- 未脱敏完整手机号、验证码、AppSecret、短信密钥、AK/SK、token、私钥、证书密码、数据库密码、恢复密钥或真实宝宝照片。
- 旧日期、不同主体、不同 Bundle ID、不同 base URL、不同 AppID、不同 Universal Link 或来源不明。

## 9. 禁止替代口径

- 生产 JSON 不能替代外部平台截图。
- 外部平台截图不能替代 live check。
- App Store Connect 截图不能替代生产 readiness。
- 模拟器日志不能替代 iOS 26.5 真机或 TestFlight 证据。
- 短信 provider 服务器 proof 不能替代短信服务商截图和真实实发。
- 微信开放平台截图不能替代 iOS Release 包内 URL Scheme 和 Universal Link proof。
- OBS 控制台截图不能替代账号删除后对象清理 proof。
- 备案材料清单不能替代备案通过页或适用判断证据。

## 10. 敏感字段禁止入库

仓库、截图、公开页和审核备注中不得出现：

- `XNP_WECHAT_APP_SECRET=`
- `XNP_SMS_SECRET=`
- `XNP_SMS_WEBHOOK_SECRET=`
- `AK=`
- `SK=`
- `MYSQL_PASSWORD=`
- `Bearer ey`
- `debug code:`
- 完整手机号。
- 完整身份证号。
- 完整银行卡号。
- 验证码。
- 恢复密钥。
- 真实宝宝照片。
