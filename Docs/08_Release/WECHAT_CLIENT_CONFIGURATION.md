# WECHAT_CLIENT_CONFIGURATION.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 日期：2026-06-30
- 用途：微信登录 iOS 客户端配置交接
- 当前结论：客户端桥接、Info.plist 槽位、URL Scheme 槽位、Associated Domains 和按钮禁用态已具备；不能提交审核的原因是还没有微信开放平台移动应用发下来的真实 `wx...` AppID / URL Scheme，以及服务端 AppSecret 证据。本机验证只使用 iOS 26.5；iOS 27.0 不能作为本项目本机测试环境。

## 客户端配置是什么

App Store Release 包里的微信客户端配置由三部分组成：

1. 微信开放平台移动应用 AppID：格式为 `wx + 16 hex`，写入 `XNP_WECHAT_APP_ID`。
2. iOS URL Scheme：通常和 AppID 一致，格式为 `wx + 16 hex`，写入 `XNP_WECHAT_URL_SCHEME`，并进入 `CFBundleURLTypes`。
3. Universal Link：当前候选为 `https://api.mewpow.com/xiaonaiping/wechat/`，写入 `XNP_WECHAT_UNIVERSAL_LINK`，并要求微信开放平台后台绑定同一域名路径。

服务端还必须配置 `XNP_WECHAT_APP_SECRET`。这个不是客户端值，不能写进 iOS 工程或仓库。

## 微信开放平台后台字段清单

拿到微信开放平台移动应用后，后台字段按下面口径填写和截图归档；不要把 AppSecret、管理员手机号完整值、后台账号、token 或验证码写进仓库。

| 微信开放平台字段 | 小奶瓶填写口径 | 证据要求 |
|---|---|---|
| 移动应用名称 | 小奶瓶 | 截图保留应用名称和审核/配置状态 |
| iOS Bundle ID | `com.mewpow.xiaonaiping` | 必须和 Release 包 Bundle ID 一致 |
| AppID | 真实 `wx + 16 hex` | 可在 `08-wechat-open-platform.png` 展示 |
| URL Scheme | equal to AppID | 必须和 `XNP_WECHAT_URL_SCHEME` 一致 |
| Universal Link | `https://api.mewpow.com/xiaonaiping/wechat/` | 必须和 `XNP_WECHAT_UNIVERSAL_LINK` 一致，并依赖 AASA proof |
| AppSecret | 只写入服务端私有 env `XNP_WECHAT_APP_SECRET` | 必须遮挡，不写入 iOS 工程、截图或仓库 |
| 采集规则 | `Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md` | 只用于截图前核对字段和脱敏，不是证据 |
| 证据文件 | `Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png` 或 `.pdf` | 保留 AppID、Bundle ID、URL Scheme、Universal Link、审核/配置状态 |

## 已经先做完的客户端部分

| 项目 | 状态 |
|---|---|
| `Info.plist` 中 `XNPWeChatAppID` / `XNPWeChatURLScheme` / `XNPWeChatUniversalLink` | 已接 build setting |
| `CFBundleURLTypes` | 已接 `$(XNP_WECHAT_URL_SCHEME)` |
| `LSApplicationQueriesSchemes` | 已包含 `weixin`、`weixinULAPI` |
| WechatOpenSDK / WebKit.framework | `project.yml` 和 `XiaoNaiPing.xcodeproj/project.pbxproj` 均已接入，避免真 SDK 授权路径缺框架 |
| Xcode Release build settings | `project.yml` 和 `XiaoNaiPing.xcodeproj/project.pbxproj` 均已接 `XNP_WECHAT_*` 和 `XNP_ASSOCIATED_DOMAIN` |
| Associated Domains | 已接 `$(XNP_ASSOCIATED_DOMAIN)`，当前为 `applinks:api.mewpow.com` |
| Release entitlements | 已接 `$(XNP_ASSOCIATED_DOMAIN)`，`check_wechat_client_configuration.py` 会直接检查 |
| Universal Link / AASA 预检 | 已通过 `Backend/proof/universal-links.json`；本地 AASA 覆盖 `/wechat/*` 和 `/xiaonaiping/wechat/*` |
| App URL / Universal Link 回调入口 | `XiaoNaiPingApp.swift` 已把 `.onOpenURL` 和 `.onContinueUserActivity(NSUserActivityTypeBrowsingWeb)` 转交给 `WeChatLoginService` |
| 微信授权桥 | `WeChatLoginService` 已处理注册、授权请求、URL 回调、Universal Link 回调和 code 交给后端 |
| 未配置时按钮状态 | Release 包禁用微信登录按钮，不提供假成功路径 |
| 包体预检 | `check_ios_app_bundle.py` 会检查 built app 内的真实微信值，并拒绝 dry-run / debug / test / placeholder 这类假值 |

`check_wechat_client_configuration.py` 会直接检查 WechatOpenSDK / WebKit.framework、`Info.plist`、Associated Domains entitlement、`XiaoNaiPingApp.swift` 回调入口、`WeChatLoginService` 的 `WXApi.registerApp` / `send` / state-code 校验，以及 AASA 中的当前 Team ID / Bundle ID / 微信回调路径。这个 gate 只证明客户端槽位和回调链路具备，不代表微信开放平台后台、AppSecret 或真机授权已完成。

## 客户端配置预注入矩阵

这部分可以先做，但只能先做“槽位”和“复跑链路”，不能用假值把 Release gate 改绿。

| 配置项 | 能先做 | 必须等外部真值 | 落点 | 复跑 gate |
|---|---|---|---|---|
| `XNP_WECHAT_APP_ID` | 预留 build setting、Info.plist key 和注入命令 | 微信开放平台真实 AppID，格式 `wx + 16 hex` | `App/iOS/project.yml`、`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`、`App/iOS/XiaoNaiPing/Info.plist` | `check_ios_release_readiness.py`、`check_ios_app_bundle.py` |
| `XNP_WECHAT_URL_SCHEME` | 预留 `CFBundleURLTypes` 槽位 | URL Scheme equal to AppID | `App/iOS/XiaoNaiPing/Info.plist` | `check_ios_app_bundle.py` |
| `XNP_WECHAT_UNIVERSAL_LINK` | 预留当前候选路径 `https://api.mewpow.com/xiaonaiping/wechat/` | 微信开放平台后台绑定同一路径，且与 AASA 响应一致 | `App/iOS/project.yml`、微信开放平台后台 | `check_wechat_client_configuration.py`、`check_ios_app_bundle.py` |
| `XNP_ASSOCIATED_DOMAIN` | 预留 `applinks:api.mewpow.com` entitlement | Apple Developer Team ID 和 Associated Domains 在当前组织下生效 | `App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements`、Apple Developer 后台 | `check_ios_release_readiness.py`、`check_wechat_client_configuration.py` |
| AASA `appID` / `appIDs` | 先保留当前 Team ID + Bundle ID 结构和 `/wechat/*`、`/xiaonaiping/wechat/*` 路径 | Apple Developer Team ID 若漂移，必须同轮改 AASA、工程签名和 ExportOptions | `Backend/static/apple-app-site-association` | `check_wechat_client_configuration.py`、`check_ios_app_bundle.py` |
| `XNP_WECHAT_APP_SECRET` | 只写清楚服务端 env 名称和脱敏规则 | AppSecret 只进服务端私有 env，不进 iOS 工程、截图或仓库 | 服务器私有 env | `verify_auth_providers.py` |

当前能本地先完成的已经是上表里的槽位、回调、AASA 结构和 gate；剩下的真实 AppID、URL Scheme equal to AppID、Apple Developer Team ID 和服务端 AppSecret 必须来自外部后台。不能为了过 gate 写入假的 `wxclientdryrun...`、debug、test、placeholder 或不属于微信开放平台移动应用的 `wx...`。

## 真实值传播核对矩阵

拿到微信开放平台真实值后，按下面矩阵逐项核对。每一行必须来自同一个微信开放平台移动应用和同一个 Apple Developer 组织 Team；不能把截图、env、Release 包和真机回归里的值拼接自不同 App 或不同 Team。

| 值 | 权威来源 | 必须同步到 | 通过证据 | 禁止替代 |
|---|---|---|---|---|
| 真实微信 AppID | 微信开放平台移动应用，格式 `wx + 16 hex` | `XNP_WECHAT_APP_ID`、`XNP_WECHAT_URL_SCHEME`、`XNPWeChatAppID`、`XNPWeChatURLScheme`、`CFBundleURLTypes`、`08-wechat-open-platform.png` | 当轮新生成的 Release 包体证据和 `08-wechat-open-platform.png` | `wxclientdryrun123456`、debug、test、placeholder、其他 App 的 `wx...` |
| URL Scheme | 微信开放平台同一移动应用 | `XNP_WECHAT_URL_SCHEME`、`CFBundleURLTypes`、Release 包 URL Types | 当轮新生成的 Release 包体证据和真机微信回调录屏 | 与 AppID 不一致的 scheme |
| Universal Link | 微信开放平台 Universal Link 输入框和 AASA | `XNP_WECHAT_UNIVERSAL_LINK`、`XNPWeChatUniversalLink`、`Backend/static/apple-app-site-association`、Associated Domains | `08b-wechat-universal-link-aasa.png` 和当轮新生成的 Universal Link / 微信客户端证据 | 只截图微信后台、不验证 AASA 或 Associated Domains |
| Apple Developer Team ID | D-U-N-S 后 Apple Developer Organization 页面 | Xcode signing、ExportOptions、AASA `appID` / `appIDs`、Associated Domains 截图 | `08b-wechat-universal-link-aasa.png` 和当轮新生成的 iOS Release 证据 | 旧 Team ID 当作新组织 proof |
| AppSecret | 微信开放平台同一移动应用 | 仅服务器私有 env `XNP_WECHAT_APP_SECRET` | 当轮新生成的认证服务商证据只能显示已配置且已脱敏 | 写入 iOS 工程、Info.plist、截图、JSON、仓库文档或命令行历史 |
| 真机微信登录 | iOS 26.5 TestFlight 或签名真机包 | RD-14 微信登录录屏、`12-real-device-regression.md` | 微信授权拉起、回到 `com.mewpow.xiaonaiping`、后端完成登录 | 微信后台截图、模拟器、iOS 27、debug code 或未签名包 |

这个矩阵不替代微信开放平台截图、服务端私有 env、签名包或真机回归。它只用于防止真实值到手后漏配某一层。

## 真实微信 Release 配置执行包

旧日期结构化执行包已移除。拿到真实微信开放平台 AppID 后，直接按本节顺序执行；本文不是证据、不是 AppSecret 容器，也不能作为提交许可。

执行包固定了下面几件事：

1. 外部输入必须来自微信开放平台移动应用和 D-U-N-S 后 Apple Developer 组织页：真实 `wx + 16 hex` AppID、URL Scheme equal to AppID、服务端私有 `XNP_WECHAT_APP_SECRET`、Apple Developer Team ID、Universal Link。
2. 先确认 Team ID；如果不是 `L2TYJNDTJK`，同轮更新工程签名、ExportOptions、AASA `appID` / `appIDs`、Associated Domains 和 `08b-wechat-universal-link-aasa.png`。
3. 用 `prepare_wechat_release_env.py` 生成本机 ignored env 和脱敏 validation proof；不要把真实 AppID 以外的假 `wx...`、debug、test、placeholder 写进 Release。
4. 只用 iOS 26.5 跑 Release simulator / device bundle 预检，然后重新生成当轮 iOS Release、包体和微信客户端证据。
5. 服务端只在私有 env 配置 `XNP_WECHAT_APP_SECRET`，随后用 `verify_auth_providers.py --live-check` 重新生成当轮认证服务商证据，证明微信 provider 配置和 debug code 拒绝；proof 中不得出现 AppSecret。
6. 只有同轮 current proof 全绿、`08-wechat-open-platform.png`、`08b-wechat-universal-link-aasa.png` 和 RD-14 iOS 26.5 TestFlight / 签名真机微信登录通过后，才允许同步稳定 alias。

## 不能先假的原因

不能把占位的 `wx123...` 或 `wxclientdryrun...` 写进 Release 配置让检查变绿。当前 `check_ios_release_readiness.py` 和 `check_ios_app_bundle.py` 已明确拒绝 dry-run / debug / test / placeholder 这类假值；它们只接受形如 `wx` + 16 位十六进制字符的 AppID / URL Scheme，并要求两者一致。

原因：

1. `wx...` 必须来自微信开放平台移动应用，并与 Bundle ID `com.mewpow.xiaonaiping` 绑定。
2. URL Scheme 和 Universal Link 必须和微信后台一致，否则真机会拉不起微信或回不到 App。
3. 服务端 `AppSecret` 必须和同一个 AppID 配套，否则 `/v1/auth/wechat/login` 无法用 code 换 openid/unionid。
4. 假配置会让审核包出现不可复现的登录路径，属于上线风险。

## 拿到真实值后的本地验证命令

不要把真实值提交到仓库。只在本机 shell 或 CI secret 里注入。下面的 `<...>` 必须替换为微信开放平台移动应用后台发下来的真实值，直接复制占位值不会通过 Release gate：

```bash
REAL_WECHAT_APP_ID='replace_with_real_wx_app_id_from_wechat_open_platform'

python3 Backend/scripts/prepare_wechat_release_env.py \
  --app-id "$REAL_WECHAT_APP_ID" \
  --output-env /tmp/xnp-wechat-release.env \
  --output-json Backend/proof/wechat-release-env-validation-20260630T-current.json

source /tmp/xnp-wechat-release.env

xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -sdk iphonesimulator26.5 -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -derivedDataPath /tmp/XiaoNaiPing-WeChatClient-ReleaseSim-26_5 CODE_SIGNING_ALLOWED=NO -quiet build

xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -sdk iphoneos26.5 -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-WeChatClient-ReleaseDevice-26_5 CODE_SIGNING_ALLOWED=NO -quiet build

python3 Backend/scripts/check_ios_release_readiness.py

python3 Backend/scripts/check_ios_app_bundle.py --app /tmp/XiaoNaiPing-WeChatClient-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app

python3 Backend/scripts/check_wechat_client_configuration.py

python3 Backend/scripts/verify_auth_providers.py --base-url https://api.mewpow.com/xiaonaiping --live-check --allow-incomplete

python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
```

如果还没有签名证书，可以继续用 `CODE_SIGNING_ALLOWED=NO` 做包体预检；真机微信登录回归必须使用签名包或 TestFlight。当轮新证据全部变绿后再进入提交检查；不要把旧部署 proof 或旧认证服务商 proof 当成真实微信配置完成证据。

## 已完成的本地干跑

2026-06-25 已用明显假的 `wxclientdryrun123456` 做过客户端注入干跑。该干跑只证明工程能接收 `XNP_WECHAT_*` 注入值，不是 App Store 提交证据，也不能证明微信登录可用。

2026-06-26 已收紧门禁：同样的 `wxclientdryrun123456` 在当前脚本中会失败，不能再让 `ios-release-readiness.json` 或 `ios-app-bundle.json` 变绿。

执行命令：

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-WeChatClient-DryRun CODE_SIGNING_ALLOWED=NO XNP_WECHAT_APP_ID=wxclientdryrun123456 XNP_WECHAT_URL_SCHEME=wxclientdryrun123456 XNP_WECHAT_UNIVERSAL_LINK=https://api.mewpow.com/xiaonaiping/wechat/ -quiet build

XNP_WECHAT_APP_ID=wxclientdryrun123456 XNP_WECHAT_URL_SCHEME=wxclientdryrun123456 XNP_WECHAT_UNIVERSAL_LINK=https://api.mewpow.com/xiaonaiping/wechat/ python3 Backend/scripts/check_ios_release_readiness.py --output /tmp/xnp-wechat-dryrun-ios-release-readiness.json

python3 Backend/scripts/check_ios_app_bundle.py --app /tmp/XiaoNaiPing-WeChatClient-DryRun/Build/Products/Release-iphoneos/XiaoNaiPing.app --output /tmp/xnp-wechat-dryrun-ios-app-bundle.json
```

结果：

1. Release `Info.plist` 内 `XNPWeChatAppID=wxclientdryrun123456`。
2. Release `Info.plist` 内 `XNPWeChatURLScheme=wxclientdryrun123456`。
3. Release `Info.plist` 内 `XNPWeChatUniversalLink=https://api.mewpow.com/xiaonaiping/wechat/`。
4. 旧版 `/tmp/xnp-wechat-dryrun-ios-release-readiness.json` 曾通过，仅代表当时脚本验证了 build setting 注入。
5. 旧版 `/tmp/xnp-wechat-dryrun-ios-app-bundle.json` 曾通过，仅代表当时脚本验证了包体插槽注入。

正式 proof 仍必须使用微信开放平台真实值重新生成，不能复用这个干跑结果。当前正式 proof 会继续保持红色，直到真实 AppID、URL Scheme、Universal Link 后台绑定和服务端 AppSecret 同时完成。

## App Store / 微信开放平台后台需要截图归档

截图前先按 `Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md` 核对字段和遮挡要求。真正能补齐人工证据 gate 的，必须是微信开放平台后台采集到的 `08-wechat-open-platform.png` 或同名 PDF/脱敏 JSON，且单个文件不低于 10KB。

归档到 `Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png` 或同名 PDF：

1. 微信开放平台移动应用 AppID。
2. iOS Bundle ID：`com.mewpow.xiaonaiping`。
3. iOS URL Scheme：真实 `wx...`。
4. Universal Link：`https://api.mewpow.com/xiaonaiping/wechat/`，或最终专属域名路径。
5. 移动应用审核/配置状态。

## 通过标准

1. `Backend/proof/ios-release-readiness.json` 的 `passed=true`。
2. `Backend/proof/ios-app-bundle.json` 的 `passed=true`。
3. `Backend/proof/auth-providers-20260630T-current.json` 与同步后的 `Backend/proof/auth-providers.json` 都为 `passed=true`，并证明生产 API 拒绝 `debug_wechat_*`。
4. 真机或 TestFlight 能拉起微信授权，授权后回到小奶瓶并完成私有同步账号登录。
