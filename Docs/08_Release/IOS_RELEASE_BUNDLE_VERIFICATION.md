# IOS_RELEASE_BUNDLE_VERIFICATION.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 日期：2026-06-25
- 用途：App Store 提交前 iOS Release 包体自检
- 当前结论：包体内容扫描已补强，当前 Release 包没有内部说明文件、本地地址、debug 文案或 API key 标记；仍不得提交，因为微信原生 AppID 和 `wx...` URL Scheme 未完成。

## 构建命令

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-BundleReuse-Release CODE_SIGNING_ALLOWED=NO -quiet build
```

结果：构建通过。Xcode 仅输出 `IDERunDestination` scheme notice，不影响产物生成。

## 产物路径

```text
/tmp/XiaoNaiPing-BundleReuse-Release/Build/Products/Release-iphoneos/XiaoNaiPing.app
```

## Info.plist 关键值

| Key | 当前值 | 结论 |
|---|---|---|
| `CFBundleDisplayName` | 小奶瓶 | 通过 |
| `CFBundleIdentifier` | `com.mewpow.xiaonaiping` | 通过 |
| `CFBundleShortVersionString` | `1.0` | 通过 |
| `CFBundleVersion` | `1` | 通过 |
| `XNPAPIBaseURL` | `https://api.mewpow.com/xiaonaiping` | 通过 |
| `NSCameraUsageDescription` | 用户主动拍摄并保存宝宝照片 | 通过 |
| `NSPhotoLibraryUsageDescription` | 用户主动选择宝宝照片并复制到私有空间 | 通过 |
| `XNPWeChatAppID` | 空 | 阻断 |
| `XNPWeChatURLScheme` | 空 | 阻断 |
| `XNPWeChatUniversalLink` | `https://api.mewpow.com/xiaonaiping/wechat/` | 通过 |

## Privacy Manifest

`PrivacyInfo.xcprivacy` 已在 app bundle 内。当前声明：

1. `NSPrivacyTracking=false`。
2. `NSPrivacyTrackingDomains=[]`。
3. 已覆盖账号标识、手机号、用户内容、照片、健康记录、产品交互、崩溃和性能诊断类别。

## 包体内容扫描

本轮从一根呆毛发布材料复用的检查项，已固化到 `Backend/scripts/check_ios_app_bundle.py`：

1. 不允许 `README`、Markdown、HTML、env、backup、`Secrets.plist` 等内部文件进入 `.app`。
2. 不允许文本资源中出现 `127.0.0.1`、`localhost`、`debug_wechat_`、第三方模型 API 域名或 `sk-` API key 标记。
3. 继续检查 Release API URL、Privacy Manifest、繁中香港资源、debug 微信码和微信原生 URL 配置。

当前执行结果：

```bash
python3 Backend/scripts/check_ios_app_bundle.py --app /tmp/XiaoNaiPing-BundleReuse-Release/Build/Products/Release-iphoneos/XiaoNaiPing.app --allow-incomplete --output Backend/proof/ios-app-bundle.json
```

结果：未通过，失败项仅为 `weChatNativeConfigPresent`、`weChatURLTypePresent`。

已通过的关键包体项：

1. `releaseBundleInternalDocsAbsent=true`，没有 README / Markdown / HTML / env 文件。
2. `releaseBundleForbiddenTextMarkersAbsent=true`，没有本地地址、debug、第三方模型端点或 API key 标记。
3. `releaseApiBaseURLMatches=true`。
4. `privacyManifestBundled=true`。
5. `privacyManifestTrackingDisabled=true`。

## 本轮修正

之前的 Release 包曾包含 `Audio/README.md`。已修正：

1. `App/iOS/project.yml` 对 `XiaoNaiPing/Audio/README.md` 增加 source exclude。
2. `App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj` 移除 `README.md in Resources`。
3. 新 Release 包手动 `find` 扫描无输出，确认 README 不再进入 `.app`。

## 仍需补齐

1. 微信开放平台移动应用 AppID。
2. 真实 `wx...` URL Scheme。
3. App Store Distribution 签名归档。
4. TestFlight 上传后的同一套包体扫描和真机回归证据。
