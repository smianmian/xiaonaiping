# Apple Developer D-U-N-S Handoff

日期：2026-07-04

状态：D-U-N-S 编码交付后的执行清单。本文只准备动作和证据边界，不写入 D-U-N-S 编码、联系人电话、Apple ID 邮箱、付款信息、证书私钥或描述文件私密内容。

## 目标

D-U-N-S 交付后，立刻回到 Apple Developer 继续深圳市闪现生活科技有限公司的组织注册。注册完成后，确认 Apple Developer 组织 Team ID、证书、Identifiers、Profiles、Archive 和 TestFlight 证据链路。

当前工程已把 Development Team 写为 `L2TYJNDTJK`，但这只证明本机 Xcode 工程有签名 Team 槽位；企业注册完成后必须在 Apple Developer 后台重新确认组织 Team ID。如果 Apple Developer 显示的组织 Team ID 不是 `L2TYJNDTJK`，必须同步更新 `App/iOS/project.yml`、`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`、`Backend/static/apple-app-site-association`、AASA 中的 `appID` / `appIDs`，并重新归档 `08b-wechat-universal-link-aasa.png`，然后重跑 `Backend/scripts/check_universal_links.py`、`Backend/scripts/check_wechat_client_configuration.py` 和 `Backend/scripts/check_ios_release_readiness.py`。

## 企业主体一致性锁

D-U-N-S 交付后，Apple Developer Organization enrollment、App Store Connect 公司账号、App Store metadata、备案材料和公开法律页必须统一为深圳市闪现生活科技有限公司。不能用个人账号或其他公司主体完成证书、Archive、TestFlight 或 Submit for Review。

| 核对位置 | 必须一致的主体字段 | 证据或复跑 |
| --- | --- | --- |
| Apple Developer 组织页 | 深圳市闪现生活科技有限公司、Organization / Membership 状态、Team ID | `AppleDeveloper/13-organization-team-id.png`、人工核对当前 Organization / Team ID |
| App Store Connect 公司主体 | 深圳市闪现生活科技有限公司 | `Docs/08_Release/AppStoreEvidence/01-company-account.png`、人工核对当前 App Store Connect 主体 |
| App Store metadata | `Docs/08_Release/APP_STORE_METADATA.md` 的公司主体、Copyright 和提交阻断说明 | `check_review_notes.py` |
| 中国大陆备案材料 | `Docs/08_Release/MAINLAND_FILING_MATERIALS.md` 的公司主体 / 主办单位 | 人工核对当前备案材料与 `03-app-filing.*` |
| 公开法律页 | `Backend/static/privacy.html`、`Backend/static/terms.html`、`Backend/static/support.html` 的开发者主体 | `check_public_pages.py` |

主体不一致时不得继续 Archive / TestFlight / Submit for Review；先修正主体材料、重新归档 `01-company-account.png` 和 `AppleDeveloper/13-organization-team-id.png`，人工复核备案与 App Store Connect 主体，再重跑 `check_public_pages.py`、`check_review_notes.py` 和 `check_production_readiness.py`。

## Apple Developer 联系人姓名锁

Apple Developer Organization enrollment、D&B 补充信息和后续 Apple 联系人资料里的联系人姓名必须使用证件姓名：佘鹏辉 / Penghui She。不能使用余鹏辉，不能使用 Penghui Yu；如果 Apple 或 D&B 页面出现旧错名，先更正联系人姓名再继续提交或缴费。

## D-U-N-S 到手后的动作

旧结构化执行包与旧 proof 索引已移除。现场必须直接按本节顺序核对 Organization enrollment、Team ID、账号权限、证书/Profile、Archive、TestFlight 和 iOS 26.5 真机回归；每一步只记录真实证据，直到按现行认证方案重新生成的 App Store、生产就绪和上线总审计证据同轮全绿。

1. 打开 Apple Developer，继续 Organization enrollment。
2. 主体选择深圳市闪现生活科技有限公司。
3. 填入 D-U-N-S 编码，只在 Apple 页面填写，不提交到仓库。
4. 完成 Apple 的主体、联系人和付款校验。
5. 记录 Apple Developer 后台显示的组织 Team ID；不要把 Apple ID 邮箱、联系人完整电话或付款信息写进仓库。
6. 进入 Apple Developer / App Store Connect 角色与权限页，确认当前 Apple ID 有 Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限，并归档 `Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png`。
7. 进入 Certificates, Identifiers & Profiles。
8. 确认 Bundle ID `com.mewpow.xiaonaiping` 归属该组织 Team。
9. 确认 App Groups 包含 `group.com.mewpow.xiaonaiping.shared`。
10. 确认 Associated Domains 能用于 `applinks:api.mewpow.com`。
11. 确认 App Store Distribution signing 可用，并创建或下载 App Store Distribution certificate / provisioning profile。
12. 在 Xcode 登录该 Apple Developer 账号，选择组织 Team。
13. 注入真实微信 Release 值：`XNP_WECHAT_APP_ID`、`XNP_WECHAT_URL_SCHEME`、`XNP_WECHAT_UNIVERSAL_LINK`。
14. 如果 Team ID 漂移，确认 AASA 中 App ID 已使用 `新 Team ID.com.mewpow.xiaonaiping`，Associated Domains 仍包含 `applinks:api.mewpow.com`，微信开放平台 Universal Link 与 Release 包 `XNPWeChatUniversalLink` 一致，并重新归档 `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png`。
15. 执行 App Store Distribution Archive。
16. 使用 `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` 执行 `xcodebuild -exportArchive`，ExportOptions 必须是 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`、`distributionBundleIdentifier=com.mewpow.xiaonaiping`、`manageAppVersionAndBuildNumber=false`、`testFlightInternalTestingOnly=false`、`uploadSymbols=true`。当前工程/模板值仍为 `L2TYJNDTJK`；只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用。
17. Archive / export / upload 成功后，用同一导出 `.app` 重新跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_wechat_client_configuration.py` 和 `check_production_readiness.py`。
18. 等待 App Store Connect / TestFlight 构建处理完成。
19. 归档 `Docs/08_Release/AppStoreEvidence/05-signed-archive.png` 和 `Docs/08_Release/AppStoreEvidence/06-testflight.png`。

## Apple Developer / App Store Connect 权限锁

拿到 Team ID 后，先确认当前 Apple ID 的权限，再配证书、Archive、上传 TestFlight 或点 Submit for Review。必须归档 `AppleDeveloper/16-account-roles-access.png`：保留当前 Apple ID 所属团队、角色列表、Certificates, Identifiers & Profiles 访问状态、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限；遮挡 Apple ID 邮箱、联系人完整电话、付款信息和无关成员。不能只用 Team ID 截图替代权限截图。

现场必须逐项确认证书/Profile、App 管理、构建上传、TestFlight 管理、提交审核和 Account Holder / Admin 补权限路径；任一项未确认时，不得继续证书、Archive、TestFlight 或 Submit for Review。

如果当前账号缺少 App Store Distribution certificate / provisioning profile 创建权限、App 管理权限、构建上传权限、TestFlight 管理权限或提交审核权限，不得继续 Archive / TestFlight / Submit for Review；先让 Account Holder 或管理员补权限、重新归档账号权限截图，再用同一导出 `.app` 重跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py` 和 `check_production_readiness.py --allow-incomplete`。

## Team ID 漂移同步矩阵

Apple Developer 显示的组织 Team ID 是最终口径。若新 Team ID 不是 `L2TYJNDTJK`，不要只改 Xcode；必须按下面矩阵同轮同步、取证、复跑。

| 位置 | 必须同步的字段 | 证据 | 复跑 gate |
| --- | --- | --- | --- |
| `App/iOS/project.yml` | `DEVELOPMENT_TEAM`；Release 仍使用真实 `XNP_WECHAT_APP_ID` / `XNP_WECHAT_URL_SCHEME` / `XNP_WECHAT_UNIVERSAL_LINK` | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png` | `check_ios_release_readiness.py`、`check_ios_app_bundle.py` |
| `App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj` | `DEVELOPMENT_TEAM` | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png` | `check_ios_release_readiness.py`、`check_ios_app_bundle.py` |
| `Backend/static/apple-app-site-association` | `appID` / `appIDs` 使用新 Team ID，例如 `新 Team ID.com.mewpow.xiaonaiping` | `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` | `check_universal_links.py`、`check_wechat_client_configuration.py` |
| `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` | `teamID` | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png` | `check_ios_release_readiness.py`、导出后运行 `check_ios_app_bundle.py` |
| `Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md` | `XNPWeChatUniversalLink`、Associated Domains 和微信开放平台 Universal Link 同轮一致 | `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` | `check_wechat_client_configuration.py` |
| `Docs/08_Release/APP_STORE_METADATA.md` | 当前公司主体、账号认证、同步和提交阻断口径 | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png` | `check_review_notes.py`、`check_ios_release_readiness.py` |
| `Docs/08_Release/REGIONAL_LAUNCH_STRATEGY.md` | 全球首发策略中的 Team ID、Archive / TestFlight 与地区合规前置项 | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png` | `check_review_notes.py`、`check_production_readiness.py` |

## Team ID 预导出一致性锁

Apple Developer 后台 Team ID 是最终值。执行 `xcodebuild -exportArchive` 前，必须把下面口径逐项核对为同一个 Team ID；只要任一项不一致，不得执行 `xcodebuild -exportArchive`。直到这些 Team ID 口径一致，才允许继续导出和上传。

| 核对项 | 必须一致的字段 | 证据或 proof |
| --- | --- | --- |
| Apple Developer 组织页 | 页面显示的组织 Team ID | `AppleDeveloper/13-organization-team-id.png` |
| XcodeGen 工程源 | `App/iOS/project.yml` 的 `DEVELOPMENT_TEAM` | `Backend/proof/ios-release-readiness.json` |
| Xcode 工程文件 | `App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj` 的 `DEVELOPMENT_TEAM` | `Backend/proof/ios-release-readiness.json` |
| ExportOptions | `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` 的 `teamID` | `AppleDeveloper/15-distribution-certificate-profile.png` |
| AASA | `Backend/static/apple-app-site-association` 的 `appID` / `appIDs` Team 前缀 | `08b-wechat-universal-link-aasa.png`、`Backend/proof/universal-links.json` |
| 微信客户端配置 | Associated Domains、`XNPWeChatUniversalLink` 和 AASA Team ID | 按现行配置重新生成的微信客户端证据 |
| 导出前包体检查 | Release app bundle 中的 Team / Associated Domains / 微信值 | `Backend/proof/ios-app-bundle.json` |

如果 ExportOptions 仍是 `L2TYJNDTJK` 但 Apple 页面显示新 Team ID，先更新 ExportOptions `teamID`、工程签名、AASA 和微信 Universal Link 证据，再重新生成 Archive / TestFlight。不要用旧 Team ID 的 Archive 或 TestFlight 证据补交。

## 证据要求

| 证据 | 保留字段 | 必须遮挡 |
| --- | --- | --- |
| Apple Developer 组织页 | 公司主体、Team ID、Membership 状态 | Apple ID 邮箱、联系人完整电话、付款信息 |
| Bundle ID / Identifier 页 | `com.mewpow.xiaonaiping`、App Groups、Associated Domains | 无关 App、人员信息 |
| App Store Distribution 证书 / Profile | 类型、Bundle ID、Team ID、有效状态 | 证书私钥、下载链接、个人邮箱 |
| 微信 Universal Link / AASA 同轮核对 | AASA endpoint、`新 Team ID.com.mewpow.xiaonaiping`、Associated Domains、`applinks:api.mewpow.com`、`XNPWeChatUniversalLink`、微信开放平台 Universal Link | Apple ID 邮箱、完整手机号、AppSecret、验证码、token |
| Archive 成功 | `com.mewpow.xiaonaiping`、版本、build、Archive succeeded / uploaded | Apple ID 邮箱 |
| ExportOptions / 上传参数 | `XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` 使用 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`、`distributionBundleIdentifier=com.mewpow.xiaonaiping`、`testFlightInternalTestingOnly=false`；当前工程/模板值仍为 `L2TYJNDTJK`，只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用 | App Store Connect API key、Apple ID 邮箱、验证码、provisioning profile、证书私钥、导出的 `.ipa` |
| TestFlight 处理完成 | 版本、build、处理完成或可测试状态 | 测试员邮箱 |

## Apple Developer 页面证据索引与脱敏复核

D-U-N-S 交付后，按下面顺序把 Apple Developer / Xcode / App Store Connect 页面证据归档到 `Docs/08_Release/AppStoreEvidence/`。这些文件只证明 Apple Developer 组织注册、签名能力、Archive 和 TestFlight 链路，不替代微信开放平台、短信服务商、OBS、备案或 iOS 26.5 真机回归证据。

| 文件名 | 必须保留 | 必须遮挡 | 复跑或复核命令 |
|---|---|---|---|
| `AppleDeveloper/13-organization-team-id.png` | 深圳市闪现生活科技有限公司、Organization / Membership 状态、Team ID | Apple ID 邮箱、联系人完整电话、付款信息、D-U-N-S 编码完整值 | 若 Team ID 不同于 `L2TYJNDTJK`，先同步工程、AASA 和 ExportOptions |
| `AppleDeveloper/14-bundle-id-capabilities.png` | Bundle ID `com.mewpow.xiaonaiping`、当前 Team、App Groups `group.com.mewpow.xiaonaiping.shared`、Associated Domains `applinks:api.mewpow.com` | 无关 App、人员信息、Apple ID 邮箱 | `check_universal_links.py`、`check_wechat_client_configuration.py`、`check_ios_release_readiness.py` |
| `AppleDeveloper/15-distribution-certificate-profile.png` | App Store Distribution certificate / provisioning profile 类型、Bundle ID、Team ID、有效状态 | 证书私钥、provisioning profile 原文件、下载链接、个人邮箱 | 人工复核证书/Profile；导出后运行 `check_ios_app_bundle.py` |
| `AppleDeveloper/16-account-roles-access.png` | 当前 Apple ID、角色列表、Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限、提交审核权限 | Apple ID 邮箱、联系人完整电话、付款信息、无关成员 | 人工复核当前权限；导出后运行 `check_testflight_precheck.py` |
| `08b-wechat-universal-link-aasa.png` | AASA endpoint、`新 Team ID.com.mewpow.xiaonaiping`、Associated Domains、`XNPWeChatUniversalLink`、微信开放平台 Universal Link | Apple ID 邮箱、完整手机号、AppSecret、验证码、token | `check_wechat_client_configuration.py` |
| `05-signed-archive.png` | Xcode Organizer / Archive 成功状态、`com.mewpow.xiaonaiping`、version、build、App Store Distribution | Apple ID 邮箱、证书私钥、provisioning profile、导出的 `.ipa` 路径 | `check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json` |
| `06-testflight.png` | App Store Connect / TestFlight build 版本、build、处理完成或可测试状态、选中 build 与 App Store Connect 一致 | 测试员邮箱、Apple ID 邮箱、内部备注 | `check_testflight_precheck.py`；人工核对截图中的版本/build |
| `12-real-device-regression.md` | iOS 26.5、TestFlight 或 Xcode 签名真机包、RD-01 到 RD-24 全部通过、证据文件路径 | 验证码、完整手机号、微信凭证、token、对象存储 key、真实宝宝照片 | 人工核对 RD-01 到 RD-24；运行 `check_testflight_precheck.py` 和 `check_production_readiness.py` |

## D-U-N-S 交付当天执行记录模板

复制下面清单到当天的私有执行记录或工单中填写；不要把 D-U-N-S 编码完整值、Apple ID 邮箱、联系人完整电话、付款信息、证书私钥、provisioning profile 或 AppSecret 写进仓库。

- [ ] Apple Developer Organization enrollment 已继续提交。
- [ ] 主体确认为深圳市闪现生活科技有限公司。
- [ ] Team ID 已从 Apple Developer 后台确认。
- [ ] 当前 Apple ID 已确认具备 Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限，并已归档 `AppleDeveloper/16-account-roles-access.png`。
- [ ] 若 Team ID 不是 `L2TYJNDTJK`，已同步 `App/iOS/project.yml`、`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj` 和 `Backend/static/apple-app-site-association`。
- [ ] 若 Team ID 不是 `L2TYJNDTJK`，AASA 已使用 `新 Team ID.com.mewpow.xiaonaiping`，Associated Domains 仍包含 `applinks:api.mewpow.com`，微信开放平台 Universal Link 与 `XNPWeChatUniversalLink` 同轮一致。
- [ ] 若 Team ID 漂移，已重新归档 `08b-wechat-universal-link-aasa.png`。
- [ ] Bundle ID `com.mewpow.xiaonaiping` 已归属当前组织 Team。
- [ ] App Groups `group.com.mewpow.xiaonaiping.shared` 已归属当前组织 Team。
- [ ] Associated Domains 已包含 `applinks:api.mewpow.com`。
- [ ] App Store Distribution certificate / provisioning profile 可用于 Archive。
- [ ] 已注入真实微信 Release 值，不使用 placeholder `wx...`。
- [ ] `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` 已按当前 Team ID 复核；若 Team ID 漂移，已同步 `teamID`。
- [ ] ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`、`distributionBundleIdentifier=com.mewpow.xiaonaiping`、`manageAppVersionAndBuildNumber=false`、`testFlightInternalTestingOnly=false`、`uploadSymbols=true`；当前工程/模板值仍为 `L2TYJNDTJK`，只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用。
- [ ] Archive 成功截图已按 `05-signed-archive.png` 归档。
- [ ] TestFlight 构建处理完成截图已按 `06-testflight.png` 归档。
- [ ] `AppleDeveloper/13-organization-team-id.png`、`AppleDeveloper/14-bundle-id-capabilities.png`、`AppleDeveloper/15-distribution-certificate-profile.png`、`AppleDeveloper/16-account-roles-access.png`、`05-signed-archive.png`、`06-testflight.png` 和 `12-real-device-regression.md` 已按页面证据索引归档并脱敏。
- [ ] Archive / TestFlight 后已重跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_app_store_assets.py` 和 `check_production_readiness.py`，并人工核对 `12-real-device-regression.md`。

证据文件名：

| 证据 | 文件 |
| --- | --- |
| Apple Developer 组织页 / Team ID | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png` |
| Bundle ID / Identifier capabilities | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png` |
| App Store Distribution 证书 / Profile | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png` |
| 账号权限 / Roles and Access | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png` |
| 微信 Universal Link / AASA 同轮核对 | `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` |
| App Store Distribution Archive | `Docs/08_Release/AppStoreEvidence/05-signed-archive.png` |
| TestFlight 构建处理完成 | `Docs/08_Release/AppStoreEvidence/06-testflight.png` |
| iOS 26.5 真机回归 | `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md` |

## Archive / TestFlight 当天执行记录模板

复制下面清单到当天的私有执行记录或工单中填写；这里只记录执行结论和证据路径，不记录 Apple ID 邮箱、测试员邮箱、D-U-N-S 编码完整值、证书私钥、provisioning profile、AppSecret 或验证码。

- [ ] Xcode 已登录 Apple Developer 账号并选择组织 Team。
- [ ] 当前 Apple ID 已确认具备证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限。
- [ ] Team ID 漂移检查已完成；若不是 `L2TYJNDTJK`，已同步 project.yml、project.pbxproj、AASA `appID` / `appIDs`。
- [ ] 若 Team ID 漂移，已重新归档 `08b-wechat-universal-link-aasa.png`。
- [ ] App Store Distribution certificate / provisioning profile 已可用于 `com.mewpow.xiaonaiping` Archive。
- [ ] 真实 `XNP_WECHAT_APP_ID`、`XNP_WECHAT_URL_SCHEME`、`XNP_WECHAT_UNIVERSAL_LINK` 已注入 Release 配置。
- [ ] `prepare_wechat_release_env.py` 已生成 `/tmp/xnp-wechat-release.env`，且未写入 `XNP_WECHAT_APP_SECRET`。
- [ ] Archive 命令使用 `-archivePath /tmp/XiaoNaiPing-CN.xcarchive archive`。
- [ ] 导出 / 上传命令使用 `xcodebuild -exportArchive` 和 `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`。
- [ ] ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`、`distributionBundleIdentifier=com.mewpow.xiaonaiping`；当前工程/模板值仍为 `L2TYJNDTJK`，只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用。
- [ ] `testFlightInternalTestingOnly=false`，本轮构建不限制为仅内部 TestFlight。
- [ ] 导出的 `.app` 或 `.ipa` 仅保存在本机私有路径或临时路径，不提交到仓库。
- [ ] 导出后已重跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_app_store_assets.py` 和 `check_production_readiness.py`，并人工核对 `12-real-device-regression.md`。
- [ ] TestFlight build 号和版本号已和 App Store Connect 选中的构建、`12-real-device-regression.md` 环境信息一致。
- [ ] `05-signed-archive.png` 能证明 App Store Distribution Archive 成功。
- [ ] `06-testflight.png` 能证明 TestFlight 构建已处理完成并可测试。
- [ ] `12-real-device-regression.md` 已记录 iOS 26.5 TestFlight 或签名真机包回归，RD-01 到 RD-24 全部通过。

## 重跑命令

```bash
python3 Backend/scripts/prepare_wechat_release_env.py --app-id "$REAL_WECHAT_APP_ID" --output-env /tmp/xnp-wechat-release.env --output-json Backend/proof/wechat-release-env-validation-20260704T-current.json
. /tmp/xnp-wechat-release.env && xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive XNP_WECHAT_APP_ID="$XNP_WECHAT_APP_ID" XNP_WECHAT_URL_SCHEME="$XNP_WECHAT_URL_SCHEME" XNP_WECHAT_UNIVERSAL_LINK="$XNP_WECHAT_UNIVERSAL_LINK" archive
xcodebuild -exportArchive -archivePath /tmp/XiaoNaiPing-CN.xcarchive -exportPath /tmp/XiaoNaiPing-CN-AppStoreConnect -exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist -allowProvisioningUpdates
python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json
python3 Backend/scripts/check_wechat_client_configuration.py
. /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json
python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json
python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app
python3 Backend/scripts/check_app_store_assets.py --allow-incomplete
python3 Backend/scripts/check_review_notes.py --allow-incomplete
python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --require-huawei-obs --require-screenshots --allow-incomplete
```

不要把 App Store Connect API key、Apple ID 邮箱、验证码、provisioning profile、证书私钥或导出的 `.ipa` 提交到仓库。`Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` 只保存无密钥的导出参数；真实账号凭证只存在 Xcode Accounts、Keychain 或私有 CI secret。

## 不可替代项

1. D-U-N-S 交付不等于 Apple Developer 企业注册完成。
2. Team ID 写入工程不等于 App Store Distribution signing 可用。
3. Archive 成功截图不替代 TestFlight 构建处理完成截图。
4. TestFlight 构建不替代 iOS 26.5 真机回归。
5. 模拟器、iOS 27 真机、debug 微信值、placeholder `wx...` 都不能替代 App Store 提交证据。
