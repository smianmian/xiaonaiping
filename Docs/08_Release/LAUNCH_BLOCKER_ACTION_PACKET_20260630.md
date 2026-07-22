# LAUNCH_BLOCKER_ACTION_PACKET_20260630.md

## 用途

这是 2026-06-30 小奶瓶提交阻塞行动包。它不代表 App 已可提交，只把当前红项、外部平台动作、iOS 26.5 证据边界和复跑命令钉住。

当前 `launch-objective-audit.json` 仍有 7 个必需红项：

1. `ios265PhysicalDeviceAvailabilityReady`
2. `weChatConfigurationGreen`
3. `appStoreAssetsReady`
4. `testFlightRegressionPlanReadyButNotEvidence`
5. `realDeviceRegressionEvidenceReady`
6. `appStoreManualEvidenceReady`
7. `productionReadinessGreen`

## 最短下一步顺序

本地材料不要再继续扩模板。后续只按下面顺序推进；没有拿到对应真实证据时，不要把任何 plan、template、current proof 或模拟器结果当成完成。

1. 先恢复 iOS 26.5 物理真机可用性：`devicectl` 必须读到可用的 iOS 26.5 physical iPhone。这个动作解锁 TestFlight / 签名真机回归，但不替代 RD 证据。
2. D-U-N-S 交付后立刻回 Apple Developer 继续 Organization enrollment：只在 Apple 官方页面填写完整 D-U-N-S；仓库里只保存脱敏截图或 PDF。拿到 Team ID 后再核对 Bundle ID、App Groups、Associated Domains、AASA Team prefix、证书和 profiles。
3. Team ID / 证书 / profiles 就绪后再做 Archive 和 TestFlight：主 App `com.mewpow.xiaonaiping` 与 Widget `com.mewpow.xiaonaiping.widgets` 都必须使用 App Store Distribution profile。Archive 成功后还要等 TestFlight build processed/testable。
4. 微信、短信、OBS、备案/隐私证据可以并行采集：微信必须是真实开放平台移动应用和 server-only AppSecret；短信必须有真实实发 proof；OBS 必须证明私有访问、加密、生命周期和删除；备案不能写占位号。
5. App Store Connect 只做草稿回填和截图归档，不点击 Submit for Review：ASC-01 到 ASC-08、隐私标签、年龄分级、审核信息、公司账号和大陆可售都必须用真实页面证据。
6. 最后用同一个 iOS 26.5 TestFlight 或 Xcode 签名真机 build 完成 `12-real-device-regression.md`、`REAL-DEVICE-CAPTURE-RESULT.json` 和 `10-final-screenshots/UPLOAD_PROVENANCE.json`，再复跑 App Store evidence、production readiness 和 launch objective audit。

## 本机测试规则

本机测试只使用 iOS 26.5。

- iOS 26.5 simulator 可用于构建、安装启动烟测和截图候选验证。
- iOS 26.5 TestFlight 或 iOS 26.5 Xcode 签名真机包可用于真机回归。
- iOS 27.0 不能作为本项目本机测试环境。
- 模拟器不能替代真机证据。
- `devicectl` 必须能读到 iOS 26.5 physical iPhone，才能让 `ios265-device-availability.json` 和 `testFlightRegressionPlanProofPassed` 进入可执行状态；它仍不能替代最终真机证据。

## iOS 26.5 设备恢复动作

当前第一优先级是让 `蓝蓝` 这台 iOS 26.5 physical iPhone 从 `unavailable` 变成 `available (paired)`。可用的 `面面` 是 iOS 27.0，不能作为本项目本机证据。

1. 打开 `蓝蓝` 屏幕并解锁，确认系统版本仍是 iOS 26.5，不升级到 iOS 27。
2. 用 USB 直连当前 Mac；如果弹出“信任此电脑”，点信任并输入锁屏密码。
3. 确认 `设置 -> 隐私与安全性 -> 开发者模式` 已开启；如需重启，重启后再次解锁并确认信任。
4. 如仍显示 unavailable，拔插 USB、关闭再打开 Wi-Fi 配对，或在 Xcode Devices and Simulators 里重新配对；不要改用 iOS 27 设备继续真机回归。
5. 设备显示 available 后立即复跑：

```bash
python3 Backend/scripts/check_ios265_device_availability.py --output Backend/proof/ios265-device-availability.json
python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
```

只有 `eligibleIOS265PhysicalIphoneAvailable` 通过后，才进入 TestFlight / Xcode 签名真机包回归采集；这一步仍不替代 `12-real-device-regression.md` 或 `REAL-DEVICE-CAPTURE-RESULT.json`。

## 当前阻塞动作表

| 红项 | 当前含义 | 必须补齐的动作 | 通过后看哪个 proof |
| --- | --- | --- | --- |
| `ios265PhysicalDeviceAvailabilityReady` | `ios265-device-availability.json` 未能证明本机可读到可用的 iOS 26.5 `physical iPhone` | 连接 iOS 26.5 真机，确保 `devicectl` 可读取设备列表且设备可用；iOS 27 和模拟器不能替代 | `ios265-device-availability.json` |
| `weChatConfigurationGreen` | iOS Release 包和服务端微信 provider 都还没有真实微信开放平台配置 | 在微信开放平台创建/确认移动应用，配置 Bundle ID `com.mewpow.xiaonaiping`、真实 AppID、AppSecret、URL Scheme、Universal Link；把脱敏截图归档到 `08-wechat-open-platform` 和 `08b-wechat-universal-link-aasa` | `ios-release-readiness.json`、`ios-app-bundle.json`、`auth-providers.json` |
| `appStoreAssetsReady` | App Store assets proof 还没有证明最终截图上传包可提交 | 用 iOS 26.5 TestFlight 或签名真机包复核最终截图，补齐 `10-final-screenshots/UPLOAD_PROVENANCE.json` 和 App Store Connect 版本页截图 | `app-store-assets.json` |
| `testFlightRegressionPlanReadyButNotEvidence` | TestFlight 回归计划齐，但 `ios265-device-availability.json` 未能证明本机可读到 iOS 26.5 `physical iPhone` | 连接 iOS 26.5 真机，确保 `devicectl` 可读取设备列表，再复跑 iOS 26.5 真机可用性和 TestFlight 回归计划检查 | `ios265-device-availability.json`、`testflight-regression-plan.json` |
| `realDeviceRegressionEvidenceReady` | 只有清单预检，没有真实 iOS 26.5 TestFlight / 签名真机执行结果 | 复制 `12-real-device-regression.template.md` 为 `12-real-device-regression.md`，用 TestFlight 或 Xcode 签名真机包跑完 RD-01 到 RD-24，全部状态写为“通过” | `app-store-evidence.json` |
| `appStoreManualEvidenceReady` | App Store Connect、备案、签名归档、TestFlight、短信、微信、OBS 策略截图还没有归档 | 按下面文件清单补齐真实截图、PDF 或 JSON 证据 | `app-store-evidence.json` |
| `productionReadinessGreen` | 生产总闸门被私密 env、MySQL、短信/微信 provider、`/internal` 阻断、命名空间、iOS Release 包、TestFlight 计划、App Store assets、auth providers 和人工证据牵连为红 | 先完成真实生产 env / DB / admin / internal / namespace、微信、短信实发、iOS Release 包、真机回归、截图 provenance 和人工证据，再复跑总闸门 | `production-readiness.json` |

## 生产 proof 刷新

`production-readiness.json` 当前红项包含 `productionSecretConfigured`、`productionDataDirConfigured`、`mysqlDatabaseSelected`、`mysqlDatabaseEnvPresent`、`phoneLoginProviderConfigured`、`wechatLoginProviderConfigured`、`privateOperationsDashboardConfigured`、`publicInternalDashboardBlocked`、`xiaonaipingProductionNamespaceConfigured`、`iosReleaseReadinessProofPassed`、`iosAppBundleProofPassed`、`testFlightRegressionPlanProofPassed`、`appStoreAssetsProofPassed` 和 `authProvidersProofPassed`。

结构化刷新执行包见 `Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json`；它不是部署证据，不是 production readiness，也不能作为提交许可。它只用于锁定同一天同一轮 current proof、稳定 alias 同步条件、停止条件、脱敏规则和复跑 gate。

- 私密 env 必须来自服务器 `/srv/xiaonaiping/private/xiaonaiping-api.env`，不要创建假的本地 env 文件。
- `XNP_SECRET_KEY`、`XNP_DATA_DIR`、`xiaonaiping_prod` 和 `xiaonaiping_app` 必须在真实生产环境里证明。
- `/internal` 和运维面板必须由生产访问路径证明不可公开访问。
- 当天部署 proof 和 OBS/存储 proof 只能用于生产 proof 链，不能替代 App Store 人工截图或 iOS 26.5 真机证据。
- 旧日期部署 proof 或存储 proof 只能用于定位问题，不能让生产总闸门变绿。
- 当前 `production-readiness.json` 仍有 `deploymentProofCurrent` 和 `storageBackendProofCurrent` freshness blocker；正式提交前必须用 `collect_deployment_proof.py` 刷新同轮部署 proof，并用 `verify_storage_backend.py` 刷新当天 OBS/存储 proof，不能复用旧 `huawei-baota-deploy` 或 `storage-backend` JSON 让闸门变绿。

## 外部证据文件清单

把证据放在 `Docs/08_Release/AppStoreEvidence/`。不要保存密码、token、AK/SK、完整手机号、验证码、恢复密钥或真实宝宝照片。

| 文件 | 证明什么 | 当前动作 |
| --- | --- | --- |
| `01-company-account.png` 或 `.pdf` / `.json` | App Store Connect 主体为深圳市闪现生活科技有限公司 | 登录 App Store Connect 后截图主体页，遮邮箱、电话、付款信息 |
| `02-mainland-availability.png` 或 `.pdf` / `.json` | 中国大陆首发可售地区选择 | 截图可售地区，只展示 China mainland 相关配置 |
| `03-app-filing.pdf` 或 `.png` | 中国大陆 APP 备案或适用判断 | 归档备案号/备案提交/适用判断证据，遮个人证件细节 |
| `04-privacy-label.png` 或 `.json` | App Privacy 按 `APP_STORE_PRIVACY_LABEL.json` 填写 | 截图或导出 App Store Connect 隐私标签 |
| `17-age-rating-result.png` 或 `.pdf` / `.json` | 年龄分级结果页 | 截图年龄分级结果，避免暴露个人账号信息 |
| `05-signed-archive.png` 或 `.pdf` / `.json` | App Store Distribution Archive 成功 | 截图 Xcode Organizer，可见 bundle id、版本、build 和 archive 成功 |
| `06-testflight.png` 或 `.pdf` / `.json` | TestFlight 构建已处理完成并可测试 | 截图构建号、处理完成状态和测试状态 |
| `AppleDeveloper/16-account-roles-access.png` 或 `.pdf` / `.json` | `appleDeveloperAccountAccess`，当前 Apple ID 有 Certificates、App 管理、构建上传、TestFlight 和提交审核权限 | 截图 Roles and Access / Certificates 权限页，遮 Apple ID 邮箱、电话和付款信息 |
| `07-sms-provider.png` 或 `.pdf` / `.json` | 真实短信签名、模板和验证码发送成功 | 截图短信服务商签名/模板/发送成功，手机号中段打码，隐藏密钥 |
| `08-wechat-open-platform.png` 或 `.pdf` / `.json` | 微信开放平台移动应用配置 | 截图 AppID、Bundle ID、URL Scheme / Universal Link；隐藏 AppSecret |
| `08b-wechat-universal-link-aasa.png` 或 `.pdf` / `.json` | `wechatUniversalLinkAasa`，AASA、Team ID、Associated Domains 和微信 Universal Link 同轮核对 | 截图 AASA endpoint、Team ID、Bundle ID、`applinks:api.mewpow.com`、`/xiaonaiping/wechat/`、`XNPWeChatUniversalLink`；隐藏 AppSecret、Apple ID 邮箱、完整手机号、验证码和 token |
| `09-obs-policy.png` 或 `.pdf` / `.json` | 华为 OBS bucket、生命周期、加密、删除策略 | 截图 bucket、生命周期、加密、删除策略，隐藏 AK/SK 和完整对象路径 |
| `10-final-screenshots/UPLOAD_PROVENANCE.json` | `finalScreenshots` 和 `finalScreenshotsUploadProvenancePresent`，最终 App Store 截图上传来源 | 用 iOS 26.5 TestFlight 或 Xcode 签名真机包复核五张 iPhone 6.9 截图，JSON 写明 `final-app-store-upload`、`iPhone 6.9" display`、iOS 26.5、安装来源、版本/build 和 finalFiles；不能使用 Debug simulator 候选 provenance |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归结果 | 跑完 RD-01 到 RD-24，证据截图/录屏路径脱敏填写 |

`10-final-screenshots/` 当前已有候选截图，但正式提交前必须用 TestFlight or signed-device final screenshots 复核一遍并补齐 `UPLOAD_PROVENANCE.json`，不要展示真实宝宝照片、完整手机号、恢复密钥、token 或 debug code。

## 微信配置动作

微信不能用 dry-run、debug、test、placeholder 或假 `wx...` 值替代。需要外部后台真实值：

1. AppID 格式必须是 `wx + 16 hex`。
2. URL Scheme equal to AppID。
3. Bundle ID 必须绑定 `com.mewpow.xiaonaiping`。
4. Universal Link 必须绑定到 `https://api.mewpow.com/xiaonaiping/wechat/` 对应的微信开放平台后台配置。
5. `XNP_WECHAT_APP_ID` 和 `XNP_WECHAT_APP_SECRET` 必须来自微信开放平台真实移动应用。
6. AppSecret 只配置在服务端私有 env，不能写入仓库、截图或聊天。
7. `08-wechat-open-platform` 证据截图必须能看出 AppID、Bundle ID、URL Scheme 和 Universal Link，且 AppSecret 已隐藏。
8. `08b-wechat-universal-link-aasa` 证据必须同轮证明 AASA、Team ID、Associated Domains 和微信 Universal Link 对齐。

拿到真实值后，重新构建 Release 包并复跑 iOS 26.5 gate。不能为了过 gate 写入假的 `wxclientdryrun...`。

## 短信与 auth 工程证据

已完成：

- `Backend/proof/auth-provider-targeted-tests-20260630.log`：8 个 targeted tests 通过，覆盖短信 webhook adapter、签名校验、auth provider 配置门禁和 debug 微信拒绝路径。
- `Backend/proof/auth-providers-20260630T-current.json` 已用服务器 deployment proof 检查 provider 配置；当前 auth provider 红项仍以真实短信/微信 provider current proof 为准。

仍不能替代：

- 真实短信服务商签名、模板、发送成功记录、发送明细和最终真实实发验证截图。
- 微信开放平台 `XNP_WECHAT_APP_ID` / `XNP_WECHAT_APP_SECRET`、iOS `wx...` URL Scheme、人工截图和最终实测。

## 真机回归动作

真机回归只能二选一：

1. `TestFlight`
2. `Xcode 签名真机包`

必须填写 `12-real-device-regression.md`，并满足：

- 环境写明 iOS 26.5。
- 安装方式写明 `TestFlight` 或 `Xcode 签名真机包`。
- RD-01 到 RD-24 全部存在，状态全部为“通过”。
- 覆盖冷启动、手机号登录、微信登录、恢复密钥登录、云同步、云恢复、账号删除、通知权限、灵动岛、小组件和审核边界。
- 证据截图/录屏路径必须填写且脱敏。

## 复跑命令

本机无生产 env 时使用最近一次服务器 proof，但正式提交前必须刷新当天部署、OBS/存储、provider、App Store 人工证据和 iOS 26.5 真机证据：

```bash
Backend/scripts/run_launch_readiness.sh \
  --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
  --app-path /tmp/XiaoNaiPing-WeChat-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260704-wechat-sim.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260704-wechat-device.log \
  --base-url https://api.mewpow.com/xiaonaiping \
  --live-check
```

当前 `ios-265-build.json` 已刷新为 iOS 26.5 build proof：simulator build log 指向 `Backend/proof/xcodebuild-release-ios265-20260704-wechat-sim.log`，device build log 指向 `Backend/proof/xcodebuild-release-ios265-20260704-wechat-device.log`。这只证明 Release simulator / iPhoneOS artifact 使用 iOS 26.5 SDK 构建成功；不替代 App Store Distribution Archive、TestFlight 处理完成、iOS 26.5 真机回归或最终 App Store Connect 提交证据。

补完部分证据后可先跑聚焦检查：

```bash
XNP_DEPLOY_HOST=root@YOUR_SERVER Backend/deploy/deploy-huawei-baota.sh
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json
python3 Backend/scripts/check_launch_blocker_action_packet.py --allow-incomplete --output Backend/proof/launch-blocker-action-packet.json
```

## 提交判断

只有当以下 proof 全绿时，才允许进入 App Store 提交流程：

1. `Backend/proof/launch-objective-audit.json` 的 `ready=true`
2. `Backend/proof/production-readiness.json` 的 `ready=true`
3. `Backend/proof/app-store-evidence.json` 的 `ready=true`
4. `Backend/proof/ios-265-build.json` 的 `passed=true`
5. `Backend/proof/ios-release-readiness.json` 的 `passed=true`
6. `Backend/proof/ios-app-bundle.json` 的 `passed=true`
7. `Backend/proof/auth-providers.json` 的 `passed=true`
