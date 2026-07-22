# App Review 拒审点交叉检查 - 2026-07-08

## 来源

- 参考 App: 一根呆毛
- 来源记录: `/Users/smianmian/Emotion Isle/output/app-review-rejection-fix-20260708.md`
- Apple Review date: July 07, 2026
- 一根呆毛被拒 build: 1.0 (2)

## 一根呆毛本次拒审点

1. `4.2.3(i) Design - Minimum Functionality`
   - 审核认为登录前需要先安装微信。

2. `5.1.1(iv) Legal - Privacy - Data Collection and Storage`
   - HealthKit 权限预说明页使用类似“立即授权”的引导按钮。
   - 系统权限弹窗前提供“以后再说”这类关闭/延后入口。

3. `2.1(a) Performance - App Completeness`
   - 审核员登录时看到错误提示。
   - 最直接同源风险是未安装微信时仍显示微信入口并报错。

## 小奶瓶检查结论

### 命中并已修复: 微信登录入口

小奶瓶已有手机号登录、恢复密钥登录和微信登录。之前的风险是: 只要微信 AppID / URL Scheme / Universal Link 配置存在，UI 就会显示微信登录入口；如果审核设备没有安装微信，可能重现一根呆毛的 `4.2.3(i)` 和 `2.1(a)` 风险。

本次修复:

- `WeChatLoginService.isNativeLoginAvailable` 在运行时确认微信 SDK 可用、微信已安装且支持授权 API。
- `CloudSyncController.isWeChatLoginConfigured` 改为只在原生微信授权可用或 Debug fallback 可用时为 true。
- 启动登录页和资料页仅在微信授权可用时显示微信登录入口。
- 未安装或不可用时不再提示用户安装微信，改为引导使用恢复密钥或手机号登录。

### 未命中: HealthKit 权限预提示

小奶瓶没有接入 HealthKit；App 代码中未发现 `HealthKit` / `HKHealth` 实现，也没有一根呆毛本次被拒的 HealthKit 预授权流程。

### 登录完整性缓解

未安装微信的审核设备上，微信入口不会显示；审核员仍可使用手机号或恢复密钥路径登录。这样避免把“必须安装微信”变成登录前置条件。

## 修改文件

- `App/iOS/XiaoNaiPing/Services/WeChatLoginService.swift`
- `App/iOS/XiaoNaiPing/Services/WechatOpenSDKShim.swift`
- `App/iOS/XiaoNaiPing/Services/CloudSyncController.swift`
- `App/iOS/XiaoNaiPing/Views/RootTabView.swift`
- `App/iOS/XiaoNaiPing/Views/ProfileView.swift`

## 验证

- `rg "未能拉起微信授权|设备已安装微信|您的设备未安装微信|微信账号一键登录|立即授权|以后再说|HealthKit|HKHealth" App/iOS/XiaoNaiPing App/iOS/XiaoNaiPingShared App/iOS/XiaoNaiPingWidgets -S`: 无命中。
- `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -derivedDataPath output/DerivedData/AppReviewCrosscheck-20260708 CODE_SIGNING_ALLOWED=NO build`: `BUILD SUCCEEDED`。

## 提交前提醒

当前修改只在本地生效。若 Apple 当前审核中的 build 已经上传，审核端不会自动看到本地修复。需要用户确认后，才能重新归档、上传新 build、在 App Store Connect 选择新 build，并重新提交审核。
