# LAUNCH_BLOCKER_ACTION_PACKET_20260626.md

## 用途

这份行动包只处理当前上线目标总审计的红项，不代表 App 已可提交。红项来源以 `Backend/proof/launch-objective-audit.json` 和 `Backend/proof/app-store-evidence.json` 为准。

当前 `launch-objective-audit.json` 仍有 6 个必需红项：

1. `weChatConfigurationGreen`
2. `ios265PhysicalDeviceAvailabilityReady`
3. `testFlightRegressionPlanReadyButNotEvidence`
4. `realDeviceRegressionEvidenceReady`
5. `appStoreManualEvidenceReady`
6. `productionReadinessGreen`

## 本机测试规则

本机测试只使用 iOS 26.5。

- iOS 26.5 simulator 可用于构建、安装启动烟测和截图候选验证。
- iOS 26.5 TestFlight 或 iOS 26.5 Xcode 签名真机包可用于真机回归。
- iOS 27.0 不能作为本项目本机测试环境。
- 模拟器不能替代真机证据。

## 红项行动表

| 红项 | 当前含义 | 必须补齐的动作 | 通过后看哪个 proof |
| --- | --- | --- | --- |
| `weChatConfigurationGreen` | iOS Release 包和服务端微信 provider 都还没有真实微信开放平台配置 | 在微信开放平台创建/确认移动应用，配置 Bundle ID `com.mewpow.xiaonaiping`、真实 AppID、AppSecret、URL Scheme、Universal Link；把脱敏截图归档到 `08-wechat-open-platform` | `ios-release-readiness.json`、`ios-app-bundle.json`、`auth-providers.json` |
| `ios265PhysicalDeviceAvailabilityReady` | `ios265-device-availability.json` 未能证明本机可读到 iOS 26.5 `physical iPhone` | 连接 iOS 26.5 真机，确保 `devicectl` 可读取设备列表且设备可用；iOS 27 和模拟器不能替代 | `ios265-device-availability.json` |
| `testFlightRegressionPlanReadyButNotEvidence` | TestFlight 回归计划齐，但 `ios265-device-availability.json` 未能证明本机可读到 iOS 26.5 `physical iPhone` | 连接 iOS 26.5 真机，确保 `devicectl` 可读取设备列表，再复跑 iOS 26.5 真机可用性和 TestFlight 回归计划检查 | `ios265-device-availability.json`、`testflight-regression-plan.json` |
| `realDeviceRegressionEvidenceReady` | 只有清单预检，没有真实 iOS 26.5 TestFlight / 签名真机执行结果 | 复制 `12-real-device-regression.template.md` 为 `12-real-device-regression.md`，用 TestFlight 或 Xcode 签名真机包跑完 RD-01 到 RD-24，全部状态写为“通过” | `app-store-evidence.json` |
| `appStoreManualEvidenceReady` | App Store Connect、备案、签名归档、TestFlight、短信、微信、OBS 策略截图还没有归档 | 按下面文件清单补齐真实截图、PDF 或 JSON 证据 | `app-store-evidence.json` |
| `productionReadinessGreen` | 生产总闸门被微信配置、iOS 包体微信配置、认证 provider 和人工证据牵连为红 | 先完成微信、真机回归和人工证据，再复跑总闸门 | `production-readiness.json` |

`production-readiness.json` 还会检查 `deploymentProofCurrent` 和 `storageBackendProofCurrent`。提交前必须刷新当天部署 proof 和当天 OBS/存储 proof；旧日期 proof 只能用于定位问题，不能让生产总闸门变绿。

当天部署 proof 优先使用 `XNP_DEPLOY_HOST=... Backend/deploy/deploy-huawei-baota.sh` 在服务器端刷新；该脚本会在真实私有 env 下运行 `collect_deployment_proof.py`，生成不含 secret 的证明；当天 OBS/存储 proof 使用 `verify_storage_backend.py` 生成，证明照片上传、下载、删除和账号删除清理路径仍可用。

`production-readiness.json` 也会因为 `testFlightRegressionPlanProofPassed` 变红。`ios265-device-availability.json` 必须能由 `devicectl` 读到 iOS 26.5 `physical iPhone`；`devicectl` 超时、无 physical iPhone、iOS 27 真机或模拟器都不能替代该证据，也不能让 TestFlight 回归计划 proof 变绿。

## 外部证据文件清单

把证据放在 `Docs/08_Release/AppStoreEvidence/`。不要保存密码、token、AK/SK、完整手机号、验证码、恢复密钥或真实宝宝照片。

| 文件 | 证明什么 | 当前动作 |
| --- | --- | --- |
| `01-company-account.png` 或 `.pdf` / `.json` | App Store Connect 主体为深圳市闪现生活科技有限公司 | 登录 App Store Connect 后截图主体页，遮邮箱、电话、付款信息 |
| `02-mainland-availability.png` 或 `.pdf` / `.json` | 中国大陆首发可售地区选择 | 截图可售地区，只展示 China mainland 相关配置 |
| `03-app-filing.pdf` 或 `.png` | 中国大陆 APP 备案或适用判断 | 归档备案号/备案提交/适用判断证据，遮个人证件细节 |
| `04-privacy-label.png` 或 `.json` | App Privacy 按 `APP_STORE_PRIVACY_LABEL.json` 填写 | 截图或导出 App Store Connect 隐私标签 |
| `05-signed-archive.png` 或 `.pdf` / `.json` | App Store Distribution Archive 成功 | 截图 Xcode Organizer，可见 bundle id、版本、build 和 archive 成功 |
| `06-testflight.png` 或 `.pdf` / `.json` | TestFlight 构建已处理完成并可测试 | 截图构建号、处理完成状态和测试状态 |
| `07-sms-provider.png` 或 `.pdf` / `.json` | 真实短信签名、模板和验证码发送成功 | 截图服务商签名/模板/发送成功，手机号中段打码，隐藏密钥 |
| `08-wechat-open-platform.png` 或 `.pdf` / `.json` | 微信开放平台移动应用配置 | 截图 AppID、Bundle ID、URL Scheme / Universal Link；隐藏 AppSecret |
| `09-obs-policy.png` 或 `.pdf` / `.json` | 华为 OBS bucket、生命周期、加密、删除策略 | 截图 bucket、生命周期、加密、删除策略，隐藏 AK/SK 和完整对象路径 |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归结果 | 跑完 RD-01 到 RD-24，证据截图/录屏路径脱敏填写 |

`10-final-screenshots/` 当前已有候选截图，但正式提交前仍建议用 TestFlight or signed-device final screenshots 复核一遍，不要展示真实宝宝照片、完整手机号、恢复密钥、token 或 debug code。

## 微信配置动作

微信不能用 dry-run、debug、test、placeholder 或假 `wx...` 值替代。需要外部后台真实值：

1. AppID 格式必须是 `wx + 16 hex`。
2. URL Scheme equal to AppID。
3. Bundle ID 必须绑定 `com.mewpow.xiaonaiping`。
4. Universal Link 必须绑定到 `https://api.mewpow.com/xiaonaiping/wechat/` 对应的微信开放平台后台配置。
5. AppSecret 只配置在服务端私有 env，不能写入仓库、截图或聊天。
6. `08-wechat-open-platform` 证据截图必须能看出 AppID、Bundle ID、URL Scheme 和 Universal Link，且 AppSecret 已隐藏。

拿到真实值后，重新构建 Release 包并复跑 iOS 26.5 gate。不能为了过 gate 写入假的 `wxclientdryrun...`。

## 短信与 auth 工程证据

已完成：

- `Backend/proof/auth-provider-targeted-tests-20260626.log`：`Backend.tests.test_aliyun_sms_adapter` 和 `Backend.tests.test_auth_provider_verification` 共 7 个测试通过，覆盖阿里云短信 webhook adapter、签名校验、auth provider 配置门禁和 debug 微信拒绝路径。
- `Backend/proof/auth-providers-20260626T-current.json` 已用服务器 deployment proof 证明 `XNP_SMS_PROVIDER=webhook`、`XNP_SMS_SECRET` 和 `XNP_SMS_WEBHOOK_URL` 配置存在；当前 auth provider 红项只剩微信。

仍不能替代：

- 真实阿里云短信签名、模板、RAM 密钥、短信服务商发送成功截图和最终真实实发测试。
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

本机无生产 env 时使用最近一次服务器 proof：

```bash
Backend/scripts/run_launch_readiness.sh \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260625T080412Z.json \
  --storage-proof Backend/proof/storage-backend-20260625T080039Z.json \
  --app-path /private/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260627-sim-current.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260627-device-current.log \
  --base-url https://api.mewpow.com/xiaonaiping
```

补完部分证据后可先跑聚焦检查：

```bash
XNP_DEPLOY_HOST=root@YOUR_SERVER Backend/deploy/deploy-huawei-baota.sh
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json
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
