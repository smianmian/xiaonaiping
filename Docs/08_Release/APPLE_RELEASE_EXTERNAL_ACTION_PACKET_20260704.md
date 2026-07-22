# 小奶瓶 Apple 发布外部动作包

日期：2026-07-04

状态：外部后台执行清单，不是发布完成证据。执行任何会创建 Apple 记录、证书、profile、App Store Connect App、上传构建或提交审核的动作前，都必须由操作者在 Apple 页面上确认。

## 当前 live 阻断

| 位置 | 当前证据 | 结论 |
| --- | --- | --- |
| Apple Developer Identifiers | `Backend/proof/apple-developer-identifiers-live-missing-xnp-bundle-20260704.json` | 当前团队为 `Shenzhen Flash Life Technology Co., Ltd - L2TYJNDTJK`，但没有 `com.mewpow.xiaonaiping` 或 `com.mewpow.xiaonaiping.widgets` |
| App Store Connect Apps | `Backend/proof/app-store-connect-apps-live-missing-xnp-20260704.json` | App 列表只有一根呆毛，小奶瓶 App 记录不存在 |
| Xcode Archive | `Backend/proof/xcodebuild-archive-appstore-20260704-l2tyjndtjk.log` | 缺少主 App 和 widget 的 provisioning profiles，不能 Archive |

## Apple Developer 要创建/确认的项目

| 项 | 值 |
| --- | --- |
| Team | `Shenzhen Flash Life Technology Co., Ltd - L2TYJNDTJK` |
| 主 App Bundle ID | `com.mewpow.xiaonaiping` |
| Widget Bundle ID | `com.mewpow.xiaonaiping.widgets` |
| App Group | `group.com.mewpow.xiaonaiping.shared` |
| Associated Domain | `applinks:api.mewpow.com` |
| AASA appID 前缀 | `L2TYJNDTJK.com.mewpow.xiaonaiping` |
| Universal Link | `https://api.mewpow.com/xiaonaiping/wechat/` |

主 App 必须启用 App Groups 和 Associated Domains。Widget 必须启用同一个 App Group。不得启用 HealthKit、iCloud、Push Notifications 或其他工程未声明的 capability。

## App Store Connect 要创建的 App

| 字段 | 值 |
| --- | --- |
| 平台 | iOS |
| App 名称 | 小奶瓶 |
| Primary language | Simplified Chinese / 简体中文 |
| Bundle ID | `com.mewpow.xiaonaiping` |
| SKU | `xiaonaiping-ios-1` |
| 用户访问权限 | Full Access，除非 Account Holder 指定更窄权限 |

创建 App 后，按 `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260704.md` 和 `Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260704.md` 填写字段。不要在 App Store Connect 页面临时改文案；改字必须先回写源文件并重跑材料 gate。

## 证据归档

| 完成动作 | 必须归档 |
| --- | --- |
| Team / Membership / 组织主体确认 | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png` |
| Bundle ID / App Group / Associated Domains | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png` |
| App Store Distribution certificate / profiles | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png` |
| 当前 Apple ID 权限 | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png` |
| AASA / Associated Domains / Universal Link 同轮核对 | `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` |
| Archive 成功 | `Docs/08_Release/AppStoreEvidence/05-signed-archive.png` |
| TestFlight 构建处理完成并可测试 | `Docs/08_Release/AppStoreEvidence/06-testflight.png` |
| iOS 26.5 真机回归 | `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md` |

截图必须遮挡 Apple ID 邮箱、联系人完整电话、付款信息、证书私钥、profile 下载链接、App Store Connect API key、验证码、AppSecret、token 和完整手机号。

## 执行后复跑命令

```bash
python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links-20260704T-apple-live.json
. /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260704T-apple-live.json
. /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-apple-live.json
python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials-20260704T-apple-live.json
. /tmp/xnp-wechat-release.env && xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive XNP_WECHAT_APP_ID="$XNP_WECHAT_APP_ID" XNP_WECHAT_URL_SCHEME="$XNP_WECHAT_URL_SCHEME" XNP_WECHAT_UNIVERSAL_LINK="$XNP_WECHAT_UNIVERSAL_LINK" archive
xcodebuild -exportArchive -archivePath /tmp/XiaoNaiPing-CN.xcarchive -exportPath /tmp/XiaoNaiPing-CN-AppStoreConnect -exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist -allowProvisioningUpdates
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-07-04 --output Backend/proof/app-store-evidence-20260704T-apple-live.json
python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260704T-apple-live.json
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit-20260704T-apple-live.json
```

## 停机条件

- `com.mewpow.xiaonaiping` 或 `com.mewpow.xiaonaiping.widgets` 不属于 `L2TYJNDTJK`：停止 Archive。
- App Group 不包含 `group.com.mewpow.xiaonaiping.shared`：停止 Archive。
- Associated Domains 不包含 `applinks:api.mewpow.com`：停止微信 Universal Link / TestFlight。
- 当前 Apple ID 缺少 Certificates, Identifiers & Profiles、App 管理、构建上传、TestFlight 管理或提交审核权限：停止证书、上传和提交。
- TestFlight 未处理完成或不可测试：停止 iOS 26.5 真机回归。
- 没有 iOS 26.5 真机：不要用 iOS 27、模拟器或其他设备替代。
