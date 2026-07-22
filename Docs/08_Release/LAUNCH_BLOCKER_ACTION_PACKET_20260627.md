# LAUNCH_BLOCKER_ACTION_PACKET_20260627.md

## 用途

这是 2026-06-27 跨项目提交守卫使用的小奶瓶阻塞行动包摘要。它不代表小奶瓶已可提交，只把当前红项和补齐边界钉住。

## 当前阻塞

- 上线目标红项仍为 `weChatConfigurationGreen`、`ios265PhysicalDeviceAvailabilityReady`、`testFlightRegressionPlanReadyButNotEvidence`、`realDeviceRegressionEvidenceReady`、`appStoreManualEvidenceReady`、`productionReadinessGreen`。
- `production-readiness.json` 当前还会检查 `deploymentProofCurrent` 和 `storageBackendProofCurrent`：提交前必须刷新当天部署 proof 和当天 OBS/存储 proof，不能继续沿用旧日期 proof。
- `production-readiness.json` 当前还会因为 `testFlightRegressionPlanProofPassed` 变红：`ios265-device-availability.json` 必须能由 `devicectl` 读到 iOS 26.5 `physical iPhone`，否则 TestFlight 回归计划只能算“计划齐”，不能算“证据齐”。
- 微信开放平台真实配置未齐：需要 `XNP_WECHAT_APP_ID`、`XNP_WECHAT_APP_SECRET`、iOS `XNPWeChatAppID`、`XNPWeChatURLScheme`、`CFBundleURLTypes` 和 Universal Link 一致。
- 短信工程链路已有当前 proof：`Backend/proof/auth-provider-targeted-tests-20260627.log` 覆盖短信 webhook adapter、签名校验、auth provider 配置门禁和 debug 微信拒绝路径。
- 短信上线仍缺人工材料：必须补短信服务商签名、模板、发送成功记录和真实实发验证截图，手机号中段打码，密钥不截图。
- App Store 人工证据仍缺公司主体、仅 China mainland 可售、APP 备案、隐私标签、签名归档、TestFlight、短信服务商、微信开放平台、OBS 策略和 iOS 26.5 真机回归。
- 当天部署 proof 优先使用 `XNP_DEPLOY_HOST=... Backend/deploy/deploy-huawei-baota.sh` 在服务器端刷新；该脚本会在真实私有 env 下运行 `collect_deployment_proof.py`，生成不含 secret 的证明；当天 OBS/存储 proof 使用 `verify_storage_backend.py` 生成，证明照片上传、下载、删除和账号删除清理路径仍可用。

## 不可替代边界

- 本机测试只使用 iOS 26.5。
- iOS 27.0 不能作为本项目本机测试环境。
- 模拟器不能替代真机证据。
- `XNP_SMS_PROVIDER=webhook`、`XNP_SMS_SECRET`、`XNP_SMS_WEBHOOK_URL` 只能证明服务端短信 provider 配置存在，不替代短信服务商截图和真实实发。
- `XNP_WECHAT_APP_ID` 和 `XNP_WECHAT_APP_SECRET` 必须来自微信开放平台真实移动应用；`XNP_WECHAT_APP_SECRET` 不得写入仓库、截图或聊天。
- iOS 27、模拟器启动日志、空截图、模板文档、debug code、placeholder `wx...` 都不能替代 iOS 26.5 TestFlight 或 Xcode 签名真机回归证据。
- 旧日期的部署 proof 或存储 proof 不能替代 `deploymentProofCurrent` / `storageBackendProofCurrent`；当天部署 proof、当天 OBS/存储 proof 必须在提交前刷新。
- `devicectl` 超时、无 physical iPhone、iOS 27 真机、模拟器都不能替代 `ios265-device-availability.json` 里的 iOS 26.5 真机可用性证据，也不能替代 `testFlightRegressionPlanProofPassed`。
- `ios265PhysicalDeviceAvailabilityReady` 只有在 `ios265-device-availability.json` 证明 iOS 26.5 physical iPhone 可读且可用时才算通过。

真机回归只能二选一：

1. `TestFlight`
2. `Xcode 签名真机包`

## 证据目录

所有人工证据放在 `Docs/08_Release/AppStoreEvidence/`。`12-real-device-regression.md` 的 RD-01 到 RD-24 必须全部为“通过”，且证据/备注指向该目录内真实存在、非空的脱敏截图、录屏或 PDF。

必须补齐的证据文件名：

- `01-company-account`
- `02-mainland-availability`
- `03-app-filing`
- `04-privacy-label`
- `17-age-rating-result`
- `05-signed-archive`
- `06-testflight`
- `07-sms-provider`
- `08-wechat-open-platform`
- `09-obs-policy`
- `12-real-device-regression.md`

## 微信配置细则

微信不能用 dry-run、debug、test、placeholder 或假 `wx...` 值替代。

1. AppID 格式必须是 `wx + 16 hex`。
2. URL Scheme equal to AppID。
3. Bundle ID 必须绑定 `com.mewpow.xiaonaiping`。
4. Universal Link 必须绑定到 `https://api.mewpow.com/xiaonaiping/wechat/` 对应的微信开放平台后台配置。
5. AppSecret 只配置在服务端私有 env，不能写入仓库、截图或聊天。
6. `08-wechat-open-platform` 证据截图必须能看出 AppID、Bundle ID、URL Scheme 和 Universal Link，且 AppSecret 已隐藏。

## 复跑命令

统一 gate：

```bash
Backend/scripts/run_launch_readiness.sh \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260625T080412Z.json \
  --storage-proof Backend/proof/storage-backend-20260625T080039Z.json \
  --app-path /private/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260627-sim-current.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260627-device-current.log \
  --base-url https://api.mewpow.com/xiaonaiping
```

聚焦检查：

```bash
XNP_DEPLOY_HOST=root@YOUR_SERVER Backend/deploy/deploy-huawei-baota.sh
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json
python3 Backend/scripts/check_launch_blocker_action_packet.py --allow-incomplete --output Backend/proof/launch-blocker-action-packet.json
```
