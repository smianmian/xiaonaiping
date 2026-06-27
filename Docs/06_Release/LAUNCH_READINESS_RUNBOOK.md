# Launch Readiness Runbook（可执行）

> 用于把证据更新到位并快速判断是否接近可提交。脚本本身不替代 App Store 上架流程。

## 使用目标

- 同时刷新发布/合规相关 proof 文件。
- 把阻断项集中到 `Backend/proof` 的 JSON 结果里，避免手工重复记忆命令。
- 保持敏感信息不出仓库（脚本不会打印 `--env-file` 内容）。
- 每次执行会生成带时间戳的归档文件，并同步更新对应无时间戳“最新快照”（例如 `Backend/proof/production-readiness.json`）。部署 proof 只有在传入 `--env-file` 时才刷新。

## 标配命令（推荐）

```bash
cd /Users/smianmian/Downloads/小奶瓶
Backend/scripts/run_launch_readiness.sh \
  --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
  --base-url https://api.mewpow.com/xiaonaiping \
  --app-path /tmp/XiaoNaiPing.xcarchive/Products/Applications/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260627-sim-current.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260627-device-current.log \
  --live-check
```

## 本机复核命令（无生产 env）

本机没有 `/srv/xiaonaiping/private/xiaonaiping-api.env` 时，不要刷新部署 proof，直接复用最近一次服务器采集的 proof：

```bash
cd /Users/smianmian/Downloads/小奶瓶
Backend/scripts/run_launch_readiness.sh \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260625T080412Z.json \
  --storage-proof Backend/proof/storage-backend-20260625T080039Z.json \
  --app-path /private/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260627-sim-current.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260627-device-current.log \
  --base-url https://api.mewpow.com/xiaonaiping
```

## 参数说明

- `--env-file`：生产私有 env 的路径。建议只读服务端私有文件，不要把真实密码贴到聊天或日志。
- `--deployment-proof`：本机无生产 env 时复用已有部署 proof；传入后脚本不会重新采集或覆盖 `Backend/proof/huawei-baota-deploy.json`。
- `--storage-proof`：本机无生产 env 时复用已有 OBS 存储 proof；传入后脚本不会把本机 disk 存储 proof 覆盖成最新快照。
- `--auth-providers-proof`：必要时复用已有登录 provider proof；通常不用传，脚本会从 `--deployment-proof` 派生短信/微信配置状态。
- `--base-url`：公网 API 域名，例如 `https://api.mewpow.com/xiaonaiping`（过渡路径）或小奶瓶正式子域名。
- `--app-path`：用于 `check_ios_app_bundle.py` 和 `check_testflight_precheck.py` 的 `.app` 路径；建议用 Release 包。
- `--ios-simulator-log`：iOS 26.5 Release simulator 构建日志，用于证明本轮确实重新构建过 `iphonesimulator26.5`。
- `--ios-device-log`：iOS 26.5 Release generic device 构建日志，用于证明本轮确实重新构建过 `iphoneos26.5`。
- `--live-check`：开启会调用 auth provider 的线上模式校验。
- `--skip-ios-bundle`：目前本地无 `.app` 时可跳过 bundle 检查。
- `--repo-root`：在 fork/脚本镜像场景可显式指定仓库根目录。

## 生成文件清单

脚本会刷新以下文件（并保持无时间戳快照文件）：

- `Backend/proof/production-readiness.json`
- `Backend/proof/launch-blocker-scope.json`
- `Backend/proof/launch-objective-audit.json`
- `Backend/proof/launch-blocker-action-packet.json`
- `Backend/proof/ios-release-readiness.json`
- `Backend/proof/ios-265-build.json`
- `Backend/proof/ios265-device-availability.json`
- `Backend/proof/ios-app-bundle.json`（传 `--app-path` 时）
- `Backend/proof/testflight-precheck.json`（传 `--app-path` 时）
- `Backend/proof/testflight-regression-plan.json`
- `Backend/proof/sim-launch-ios265-20260626.json`（由 iOS 26.5 本机烟测生成，总闸门会读取）
- `Backend/proof/remote-api.json`
- `Backend/proof/storage-backend.json`（只在传入 `--env-file` 时刷新；传 `--storage-proof` 时只读取）
- `Backend/proof/auth-providers.json`
- `Backend/proof/diagnostics-redaction.json`
- `Backend/proof/public-pages.json`
- `Backend/proof/review-notes.json`
- `Backend/proof/legal-drafts.json`
- `Backend/proof/universal-links.json`
- `Backend/proof/wechat-client-configuration.json`
- `Backend/proof/app-store-evidence.json`
- `Backend/proof/app-store-assets.json`
- `Backend/proof/app-store-connect-materials.json`
- `Backend/proof/app-store-submission-packet.json`
- `Backend/proof/huawei-baota-deploy-*.json`（只在传入 `--env-file` 时刷新；传 `--deployment-proof` 时只读取）

## 如何判读阻断项

- 只看脚本返回码不能替代 proof 内容。
- 日志里的 `[ok] generate ... proof` 只表示 proof 文件生成命令成功，不代表该 proof 已通过。
- 日志里的 `[proof-ok]` 才表示对应 proof 的 `passed=true` 或 `ready=true`。
- 日志里的 `[incomplete]` 表示对应 proof 已生成但仍有红项；脚本最终会返回非 0，不能作为可提交状态。
- 重点看：
  - `Backend/proof/production-readiness.json` 的 `failedRequiredChecks`
  - `Backend/proof/launch-blocker-scope.json` 的 `unexpectedBlockers`
  - `Backend/proof/launch-objective-audit.json` 的 `failedRequiredChecks`
  - `Backend/proof/launch-blocker-action-packet.json` 的 `failedRequiredChecks`
  - `Backend/proof/ios-release-readiness.json` 的 `failedRequiredChecks`
  - `Backend/proof/ios-265-build.json` 的 `failedRequiredChecks`
  - `Backend/proof/ios265-device-availability.json` 的 `eligibleIOS265PhysicalIphones`
  - `Backend/proof/testflight-precheck.json` 的 `failedRequiredChecks`
  - `Backend/proof/testflight-regression-plan.json` 的 `failedRequiredChecks`
  - `Backend/proof/app-store-connect-materials.json` 的 `failedRequiredChecks`
  - `Backend/proof/app-store-submission-packet.json` 的 `failedRequiredChecks`
  - `Backend/proof/auth-providers.json` 的 `failedRequiredChecks`
  - `Backend/proof/wechat-client-configuration.json` 的 `failedRequiredChecks`
  - `Backend/proof/app-store-evidence.json` 的 `missingEvidence`
- 当前主线阻断项仍可能包含：
  1. `huaweiObsPolicy` / OBS 文档与 bucket 命名空间证据
  2. 短信签名与签发链路证据
  3. 微信开放平台正式配置证据
  4. App Store Connect 主体/地区/归档/TestFlight/隐私标签截图

## 与地区提交策略的关系

- 中国大陆：必须先把 `production-readiness.json` 过关后再进入大陆区域提交。大陆提交后，保留 `zh-Hant-HK` 资源不需要额外打包，只要 App 内切换大陆 / 香港疫苗模板正常即可。
- 香港：同一套检查可复用。提交前再切换 App Store 可售地区与文案即可。

## 额外提示

- 目前未完成签名归档、TestFlight、APP 备案/适用联网判断时，脚本会持续标红阻断项，这属于真实提交前关键资料缺口，不是脚本问题。
