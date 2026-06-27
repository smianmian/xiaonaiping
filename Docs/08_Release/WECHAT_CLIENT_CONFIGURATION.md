# WECHAT_CLIENT_CONFIGURATION.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 日期：2026-06-25
- 用途：微信登录 iOS 客户端配置交接
- 当前结论：客户端桥接、Info.plist 槽位、URL Scheme 槽位、Associated Domains 和按钮禁用态已具备；不能提交审核的原因是还没有微信开放平台移动应用发下来的真实 `wx...` AppID / URL Scheme，以及服务端 AppSecret 证据。本机验证只使用 iOS 26.5；iOS 27.0 不能作为本项目本机测试环境。

## 客户端配置是什么

App Store Release 包里的微信客户端配置由三部分组成：

1. 微信开放平台移动应用 AppID：格式为 `wx + 16 hex`，写入 `XNP_WECHAT_APP_ID`。
2. iOS URL Scheme：通常和 AppID 一致，格式为 `wx + 16 hex`，写入 `XNP_WECHAT_URL_SCHEME`，并进入 `CFBundleURLTypes`。
3. Universal Link：当前候选为 `https://api.mewpow.com/xiaonaiping/wechat/`，写入 `XNP_WECHAT_UNIVERSAL_LINK`，并要求微信开放平台后台绑定同一域名路径。

服务端还必须配置 `XNP_WECHAT_APP_SECRET`。这个不是客户端值，不能写进 iOS 工程或仓库。

## 已经先做完的客户端部分

| 项目 | 状态 |
|---|---|
| `Info.plist` 中 `XNPWeChatAppID` / `XNPWeChatURLScheme` / `XNPWeChatUniversalLink` | 已接 build setting |
| `CFBundleURLTypes` | 已接 `$(XNP_WECHAT_URL_SCHEME)` |
| `LSApplicationQueriesSchemes` | 已包含 `weixin`、`weixinULAPI` |
| Associated Domains | 已接 `$(XNP_ASSOCIATED_DOMAIN)`，当前为 `applinks:api.mewpow.com` |
| Release entitlements | 已接 `$(XNP_ASSOCIATED_DOMAIN)`，`check_wechat_client_configuration.py` 会直接检查 |
| Universal Link / AASA 预检 | 已通过 `Backend/proof/universal-links.json` |
| 微信授权桥 | `WeChatLoginService` 已处理注册、授权请求、URL 回调、Universal Link 回调和 code 交给后端 |
| 未配置时按钮状态 | Release 包禁用微信登录按钮，不提供假成功路径 |
| 包体预检 | `check_ios_app_bundle.py` 会检查 built app 内的真实微信值，并拒绝 dry-run / debug / test / placeholder 这类假值 |

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
  --output-json Backend/proof/wechat-release-env-validation.json

source /tmp/xnp-wechat-release.env

xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -sdk iphonesimulator26.5 -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -derivedDataPath /tmp/XiaoNaiPing-WeChatClient-ReleaseSim-26_5 CODE_SIGNING_ALLOWED=NO -quiet build

xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -sdk iphoneos26.5 -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-WeChatClient-ReleaseDevice-26_5 CODE_SIGNING_ALLOWED=NO -quiet build

python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness.json

python3 Backend/scripts/check_ios_app_bundle.py --app /tmp/XiaoNaiPing-WeChatClient-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json

python3 Backend/scripts/verify_auth_providers.py --deployment-proof Backend/proof/huawei-baota-deploy-20260625T080412Z.json --base-url https://api.mewpow.com/xiaonaiping --live-check --output Backend/proof/auth-providers.json

python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
```

如果还没有签名证书，可以继续用 `CODE_SIGNING_ALLOWED=NO` 做包体预检；真机微信登录回归必须使用签名包或 TestFlight。

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

归档到 `Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png` 或同名 PDF：

1. 微信开放平台移动应用 AppID。
2. iOS Bundle ID：`com.mewpow.xiaonaiping`。
3. iOS URL Scheme：真实 `wx...`。
4. Universal Link：`https://api.mewpow.com/xiaonaiping/wechat/`，或最终专属域名路径。
5. 移动应用审核/配置状态。

## 通过标准

1. `Backend/proof/ios-release-readiness.json` 的 `passed=true`。
2. `Backend/proof/ios-app-bundle.json` 的 `passed=true`。
3. `Backend/proof/auth-providers.json` 的 `passed=true`，并证明生产 API 拒绝 `debug_wechat_*`。
4. 真机或 TestFlight 能拉起微信授权，授权后回到小奶瓶并完成私有备份账号登录。
