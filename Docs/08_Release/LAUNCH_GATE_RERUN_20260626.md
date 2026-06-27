# LAUNCH_GATE_RERUN_20260626.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 日期：2026-06-26
- 用途：上线闸门复跑、App Store Connect 素材、TestFlight 前检查和审核说明边界汇总
- 当前结论：不能提交 App Store。2026-06-27 00:58 CST 已用 iOS 26.5 Release simulator app 重新跑完整上线闸门；iOS 26.5 构建、构建日志 iOS 26.5-only 检查、安装启动烟测、Bundle ID、Release API、隐私清单内容、Review Notes、状态展示边界、公开页面状态展示边界、法务草案状态展示边界、隐私标签 Health and Fitness 边界、Universal Links、微信客户端配置交接、中国大陆备案材料包、签名归档/TestFlight 材料包、App Store Connect 人工证据材料包、短信/微信/OBS 供应商证据材料包、远端 API、诊断脱敏、App Store 资源、App Store Connect 文案材料、新版本说明、截图计划 iOS 26.5 限制、App Store 提交包状态展示边界、审核测试账号脱敏证据、审核测试账号填写说明防泄漏、上线阻断行动包、TestFlight 客户端预检、主 App 审核 surface 文案、真机回归模板严格性、`RealDevice/` 稳定证据文件名、真机回归审核边界确认项、复跑命令当前 iOS 26.5 构建日志引用和 Release entitlements Associated Domains 槽位均通过；上线目标总审计仍未通过，真实微信 provider、iOS 包体微信 AppID / URL Scheme、真实 iOS 26.5 TestFlight / 签名真机证据和 App Store 人工证据仍阻断。

## iOS 26.5 环境

| 项目 | 结果 |
|---|---|
| Xcode | `Xcode 26.5` / build `17F42` |
| SDK | `iphoneos26.5`、`iphonesimulator26.5` |
| 模拟器 runtime | `iOS 26.5 (23F77)` |
| 本机测试设备 | `iPhone 17 Pro`，iOS 26.5 |
| 真机可用性 | `蓝蓝` iPhone 16 Pro Max 为 iOS 26.5 但当前 unavailable；`面面` iPhone 16 Plus 当前 available 但为 iOS 27.0，按本项目规则未用于本机测试 |

## 构建结果

| 命令 | 结果 |
|---|---|
| `xcodebuild ... -configuration Release -sdk iphonesimulator26.5 -destination 'platform=iOS Simulator,id=07D2E9B8-B283-4F62-88D7-AFF7B7E82ED4' ... build` | 通过 |
| `xcodebuild ... -configuration Release -sdk iphoneos26.5 -destination 'generic/platform=iOS' ... build` | 通过 |

Release iPhoneOS 产物路径：

```text
/tmp/XiaoNaiPing-Gate-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app
```

关键 `Info.plist`：

| Key | 当前值 | 结论 |
|---|---|---|
| `CFBundleDisplayName` | 小奶瓶 | 通过 |
| `CFBundleIdentifier` | `com.mewpow.xiaonaiping` | 通过 |
| `CFBundleShortVersionString` | `1.0` | 通过 |
| `CFBundleVersion` | `1` | 通过 |
| `XNPAPIBaseURL` | `https://api.mewpow.com/xiaonaiping` | 通过 |
| `XNPWeChatAppID` | 空 | 阻断 |
| `XNPWeChatURLScheme` | 空 | 阻断 |
| `XNPWeChatUniversalLink` | `https://api.mewpow.com/xiaonaiping/wechat/` | 通过 |

## Gate 结果

| Gate | 证据 | 当前结果 |
|---|---|---|
| 完整上线闸门复跑 | `Backend/scripts/run_launch_readiness.sh --deployment-proof Backend/proof/huawei-baota-deploy-20260625T080412Z.json --storage-proof Backend/proof/storage-backend-20260625T080039Z.json --app-path /private/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260627-sim-current.log --ios-device-log Backend/proof/xcodebuild-release-ios265-20260627-device-current.log --base-url https://api.mewpow.com/xiaonaiping` | 2026-06-27 00:58 CST 已执行，proof 刷新为 `20260626T165817Z`；脚本二次读取 proof 的 `passed` / `ready` 字段，iOS 26.5 构建、微信客户端配置交接、中国大陆备案材料、签名归档/TestFlight 材料、App Store Connect 人工证据材料、短信/微信/OBS 供应商证据材料、TestFlight 客户端预检和上线阻断行动包为 `[proof-ok]`，TestFlight 清单与同轮 App Store 人工证据联动检查通过且已检查 `RealDevice/` 稳定证据文件名，但不替代真机证据，真实微信配置与人工证据为 `[incomplete]`，总命令返回非 0 |
| 已知阻断范围 | `Backend/proof/launch-blocker-scope.json` | 通过；当前红项均落在生产私有 env / MySQL / OBS / namespace、短信人工证据、微信 provider、iOS `wx...` URL Scheme 和 App Store 人工证据范围内，无未知假红 |
| 上线目标总审计 | `Backend/proof/launch-objective-audit.json` | 2026-06-27 00:58 CST 复核仍未通过：`weChatConfigurationGreen`、`realDeviceRegressionEvidenceReady`、`appStoreManualEvidenceReady`、`productionReadinessGreen`；`appStoreAssetsReady`、`reviewTestAccountEvidenceReady`、`weChatClientConfigurationHandoffReady`、`mainlandFilingMaterialsReady`、`signedArchiveTestFlightMaterialsReady`、`appStoreConnectEvidenceMaterialsReady`、`providerEvidenceMaterialsReady`、`testFlightRegressionPlanReadyButNotEvidence` 已通过，说明 App Store 图标/截图资源、审核测试账号脱敏证据、微信客户端交接、中国大陆备案材料包、签名归档/TestFlight 材料包、App Store Connect 人工证据材料包、短信/微信/OBS 供应商证据材料包和 TestFlight / 真机回归计划已具备，但不能替代真实微信开放平台值、真实真机回归或人工证据 |
| 上线阻断行动包 | `Backend/proof/launch-blocker-action-packet.json` | 通过；`Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260626.md` 已覆盖当前 4 个上线目标红项、10 个外部证据文件名、微信开放平台动作、本机测试只使用 iOS 26.5、模拟器不能替代真机证据、复跑命令和当前 iOS 26.5 simulator/device 构建日志文件名 |
| 后端单元测试 | `python3 -m unittest discover -s Backend/tests` | 通过，165 tests |
| iOS 26.5 构建 proof | `Backend/proof/ios-265-build.json` | 通过；Release Simulator 为 `iphonesimulator26.5`，Release iPhoneOS 为 `iphoneos26.5`；`simulatorBuildLogIOS265Only` 和 `deviceBuildLogIOS265Only` 均通过，构建日志未混入非 26.5 SDK / runtime 标记；simulator / device 包内 `PrivacyInfo.xcprivacy` 均已验证 tracking 关闭、tracking domains 为空、采集数据类型与 App Store 隐私标签对齐且每项不用于追踪 |
| iOS 26.5 真机可用性 | `Backend/proof/ios265-device-availability.json` | 通过；`蓝蓝` 是 iOS 26.5 但 unavailable，`面面` 可用但 iOS 27.0，未纳入本机测试 |
| Review Notes | `Backend/proof/review-notes.json` | 通过；审核说明覆盖灵动岛/小组件/状态展示、用户输入数据来源、不生成健康建议/压力提醒/喂养建议、无 HealthKit / 无医疗边界，且未暴露恢复密钥、token、debug code、API key 或完整手机号 |
| 法务草案 | `Backend/proof/legal-drafts.json` | 通过；隐私政策草案和用户协议草案均包含灵动岛/锁屏 Live Activity/小组件只做状态展示、只反映用户主动记录数据、不生成健康建议/压力提醒/喂养建议、无 HealthKit / 传感器 / 医院系统 / 第三方健康数据源边界 |
| App Store 资源 | `Backend/proof/app-store-assets.json` | 通过；1024 图标、5 张最终候选截图尺寸、上传顺序文件名、非空白像素内容和 iOS 26.5 screenshot provenance 均通过；当前截图为 iPhone 17 Pro / iOS 26.5 Debug simulator seed 候选，不替代 TestFlight、签名真机或 Release build 最终证据 |
| App Store Connect 文案材料 | `Backend/proof/app-store-connect-materials.json` | 通过；名称、副标题、分类、年龄分级、URL、关键词 UTF-8 bytes 限制、新版本说明、隐私标签采集/关联身份/用途/追踪/App flags、Health and Fitness 用户输入数据来源和无 HealthKit / 传感器 / 医院系统 / 压力检测 / 医疗解释 / 健康建议 / 压力提醒 / 喂养建议边界、疫苗模板仅记录提醒且不构成医疗建议、截图文案、截图禁区、未完成微信成功态禁用、审核备注状态展示边界、审核测试账号填写说明指向脱敏证据、本地 ignored `.env.xnp-review-account` 和 App Review Information 安全字段且拒绝恢复密钥/Bearer/debug/完整手机号泄漏、截图计划 iOS 26.5 命令限制和“手机号/微信仍待真实服务商与开放平台证据”的提交边界均通过 |
| App Store Connect 人工证据材料 | `Backend/proof/app-store-connect-evidence-materials.json` | 通过；`01-company-account.png`、`02-mainland-availability.png`、`04-privacy-label.png` 的保留字段、脱敏字段、隐私标签 JSON 一致性、预提交命令和“未归档真实文件前不得声称完成”的边界均通过；该 proof 只证明材料包完整，不替代真实 App Store Connect 主体、可售地区或隐私标签截图 |
| App Store 提交包 | `Backend/proof/app-store-submission-packet.json` | 通过；官方 Apple 入口、Export Compliance、年龄分级/受监管医疗器械回答、Review Notes 状态展示边界、Do Not Submit 禁区、隐私标签来源、Release Bundle Verification 的 iOS 26.5 proof 绑定、截图边界、微信客户端配置交接命令、中国大陆备案材料命令、签名归档/TestFlight 材料命令、App Store Connect 人工证据材料命令、短信/微信/OBS 供应商证据材料命令、上线阻断行动包命令、预提交命令和 secret 泄漏扫描均通过 |
| 中国大陆备案材料 | `Backend/proof/mainland-filing-materials.json` | 通过；`MAINLAND_FILING_MATERIALS.md` 覆盖中国大陆首发/App 备案/ICP/公安联网备案路径、拟填字段、公司/后台待取材料、`AppStoreEvidence` 文件名、`03-app-filing` 截图/PDF 脱敏要求、拿到真实备案编号后再改 App/网页/Review Notes、以及备案完成前不得假写占位备案号；该 proof 只证明材料包完整，不替代 `app-store-evidence.json` 里的真实备案文件 |
| 签名归档 / TestFlight 材料 | `Backend/proof/signed-archive-testflight-materials.json` | 通过；提交包记录当前 archive 命令和无 Development Team 的签名阻断，材料要求配置 Apple Developer Team 与 App Store Distribution signing 后再上传，archive 后用导出的 `.app` 重新跑 `check_ios_app_bundle.py`，并用 `05-signed-archive.png`、`06-testflight.png` 归档真实证据；该 proof 只证明材料包和边界完整，不替代真实签名归档、TestFlight 构建处理完成截图或 iOS 26.5 真机回归 |
| 短信 / 微信 / OBS 供应商证据材料 | `Backend/proof/provider-evidence-materials.json` | 通过；`Backend/deploy/aliyun-sms-webhook-adapter.md`、`Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md`、`Backend/deploy/huawei-obs.md`、`AppStoreEvidence` README / Capture Guide 和提交包命令已覆盖 `07-sms-provider.png`、`08-wechat-open-platform.png`、`09-obs-policy.png` 的保留字段、脱敏字段、provider/storage 验证命令和“未归档真实文件前不得声称完成”的边界；该 proof 只证明材料包完整，不替代真实短信服务商截图、微信开放平台截图或 OBS 策略截图 |
| 公开审核页面 | `Backend/proof/public-pages.json` | 通过；`/privacy`、`/terms`、`/support` 均包含账号方式、公司主体、首发地区或支持说明，并同步状态展示、不生成健康建议/压力提醒/喂养建议边界 |
| Universal Links / AASA | `Backend/proof/universal-links.json` | 通过 |
| 微信客户端配置交接 | `Backend/proof/wechat-client-configuration.json` | 通过；`WECHAT_CLIENT_CONFIGURATION.md` 已写清 `wx + 16 hex`、`XNP_WECHAT_*` 客户端值、服务端 AppSecret 边界、iOS 26.5 本机验证命令、服务端 provider 验证命令、证据归档路径，且 `project.yml` / `Info.plist` / Release entitlements 槽位仍已接好 |
| 诊断脱敏 | `Backend/proof/diagnostics-redaction.json` | 通过 |
| 远端 API | `Backend/proof/remote-api.json` | 通过 |
| TestFlight 客户端预检 | `Backend/proof/testflight-precheck.json` | 通过；资料页账号与备份入口、恢复密钥/手机号/微信登录、云备份、云恢复、云端账号删除、生产 API endpoint 绑定均通过；Widget/Live Activity/通知/App Group/共享数据边界均通过，本地通知授权、首次请求、拒绝、未知状态、喝奶闹钟取消移除 pending notification 和失败/拒绝提示均通过，保存喝奶闹钟会按灵动岛开关同步 Live Activity，取消喝奶闹钟会结束 Live Activity，灵动岛喝奶提醒开关、测试入口、sync/endAll 路径和偏好持久化均通过，且账号与备份、主 App 审核 surface、Widget/Live Activity/本地通知展示文案未出现 debug 替代、医疗、健康建议、压力或心理判断标记 |
| TestFlight / 真机回归清单 | `Backend/proof/testflight-regression-plan.json` | 通过；RD-01 到 RD-24、恢复密钥账号、iOS 26.5 烟测、外部短信/微信待配置边界、证据路径、`12-real-device-regression.template.md` 严格性、`RealDevice/00-overview.png` 与 `RealDevice/RD-01...RD-24...png` 稳定证据文件名和“计划不替代真机证据”边界均通过；模板必勾项已包含灵动岛喝奶提醒开关、锁屏/桌面小组件和审核边界文案，且模板要求状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断；`app-store-evidence` gate 还会要求 RD-01 到 RD-24 每一行填写 `.png` / `.jpg` / `.jpeg` / `.mp4` / `.mov` / `.pdf` 截图或录屏文件路径，并逐项勾选 Live Activity / 小组件只做状态展示、只反映用户主动记录数据、无 HealthKit/传感器/医院系统/第三方健康数据源、不生成健康建议/压力提醒/喂养建议/医疗判断，不能只写目录 |
| iOS 26.5 安装启动烟测 | `Backend/proof/sim-launch-ios265-20260626.json` | 通过；iPhone 17 Pro / iOS 26.5，启动输出 `com.mewpow.xiaonaiping: 92544` |
| Huawei OBS 存储 proof | `Backend/proof/storage-backend-20260625T080039Z.json` | 通过；本机无 OBS 凭证，2026-06-26 未能现场重跑 Huawei OBS 脚本 |
| iOS Release readiness | `Backend/proof/ios-release-readiness.json` | 未通过：`weChatReleaseBuildSettingsConfigured`；当前脚本已拒绝 dry-run / debug / test / placeholder 微信值；`privacyManifestMatchesPrivacyLabel` 已通过双向检查，manifest 采集数据类型和 App Store 隐私标签类别不漏不多 |
| iOS app bundle | `Backend/proof/ios-app-bundle.json` | 未通过；当前 proof 已指向 iOS 26.5 Release simulator app，失败项为 `weChatNativeConfigPresent`、`weChatURLTypePresent`；当前脚本已拒绝假 `wx...` URL Scheme |
| Auth providers | `Backend/proof/auth-providers.json` | 未通过：`wechatProviderConfigured`；短信 provider 在 current proof 中已通过，但短信服务商人工证据仍未归档 |
| App Store 人工证据 | `Backend/proof/app-store-evidence.json` | 未通过：审核测试账号脱敏证据已通过；最终候选截图及 iOS 26.5 provenance 已通过；仍缺公司主体、可售地区、备案、隐私标签、签名归档、TestFlight、短信、微信、OBS 策略截图和真机回归结果；文字型人工证据会扫描恢复密钥、Bearer token、debug 微信 code、API key 和完整手机号，命中会被拒绝；真机回归证据必须填完 iOS 26.5 环境、安装方式、截图/录屏路径，RD-01 到 RD-24 状态必须全部为“通过”，并勾选 iOS 26.5、冷启动、登录、云备份/恢复、账号删除、通知权限、灵动岛喝奶提醒开关、锁屏/桌面小组件、审核边界文案，以及 Live Activity / 小组件只做状态展示、只反映用户主动记录数据、无 HealthKit/传感器/医院系统/第三方健康数据源、不生成健康建议/压力提醒/喂养建议/医疗判断 |
| Production readiness | `Backend/proof/production-readiness.json` | 未通过：微信 provider、iOS 微信包体、App Store 人工证据；App Store Connect 文案、App Store Connect 人工证据材料包、中国大陆备案材料包、签名归档/TestFlight 材料包、短信/微信/OBS 供应商证据材料包、TestFlight 客户端预检和 iOS 26.5 启动 proof 已在总闸门中通过 |

## App Store Connect 素材

可填写素材文件：`Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md`。

机器校验证据：`Backend/proof/app-store-connect-materials.json`，当前 `passed=true`。

已覆盖：

1. App 名称：小奶瓶。
2. 副标题：温柔记录宝宝每一天。
3. 描述、新版本说明、宣传文本和关键词；关键词按 UTF-8 bytes 控制，当前为 73 bytes，低于 100 bytes。
4. 主分类：生活；第二分类建议留空。
5. 年龄分级建议：预期 `4+`，以 App Store Connect 问卷自动计算为准；不选择 Kids 类目。
6. 隐私政策 URL：`https://api.mewpow.com/xiaonaiping/privacy`。
7. 技术支持 URL：`https://api.mewpow.com/xiaonaiping/support`。
8. App Privacy 标签的采集、关联身份、用途、追踪、第三方广告/分析开关。
9. 截图上传顺序和截图文案。
10. 审核测试账号填写说明：恢复密钥测试账号只填入 App Review Information 安全字段，脱敏证据指向 `Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json`，真实恢复密钥只保存在 ignored `.env.xnp-review-account`，不得写入 App Store Connect 文案、审核备注、截图或仓库文档。

## App Store Connect 人工证据材料

机器校验证据：`Backend/proof/app-store-connect-evidence-materials.json`，当前 `passed=true`。

已覆盖：

1. `01-company-account.png`：App Store Connect 账号主体为深圳市闪现生活科技有限公司；保留团队/法律主体名称和账号页标题，遮邮箱、电话、付款信息。
2. `02-mainland-availability.png`：首发只选 China mainland / 中国大陆；保留 App 名称和可售地区选择状态，遮无关账号信息。
3. `04-privacy-label.png`：App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写；保留已采集类别、未追踪、用途，遮账号邮箱。
4. `check_app_store_connect_evidence_materials.py` 只证明材料要求完整，不会让 `app-store-evidence.json` 对主体、可售地区或隐私标签的真实人工证据变绿。

## 备案 / App 备案材料

可用材料文件：`Docs/08_Release/MAINLAND_FILING_MATERIALS.md`。

机器校验证据：`Backend/proof/mainland-filing-materials.json`，当前 `passed=true`。

已覆盖：

1. 中国大陆首发、App 备案、适用 ICP / 公安联网备案路径。
2. 主办单位、App 名称、Bundle ID、服务内容、首发/第二批地区、隐私政策/用户协议/支持/API URL、华为云 ECS / MySQL / OBS 和账号方式。
3. 需要向公司/后台取得的营业执照、负责人、域名、云服务器、App Store Connect、短信、微信开放平台、OBS 和备案证明材料。
4. `AppStoreEvidence` 归档文件名和 `03-app-filing.pdf` / `.png` 的截图/PDF 脱敏要求。
5. 拿到真实备案编号后再改 App 内/网页/Review Notes，不提前写占位备案号。

## 签名归档 / TestFlight 材料

可用材料文件：`Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md`、`Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md`、`Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md`。

机器校验证据：`Backend/proof/signed-archive-testflight-materials.json`，当前 `passed=true`。

已覆盖：

1. 当前 archive 命令和“缺 Development Team / App Store Distribution signing”的真实阻断。
2. 配置签名后必须用 archive 导出的 `.app` 重跑 `check_ios_app_bundle.py`。
3. `05-signed-archive.png` 和 `06-testflight.png` 的归档文件名、保留字段和脱敏要求。
4. 本地模拟器和候选截图不替代 TestFlight / 签名真机回归；最终证据必须来自 iOS 26.5 TestFlight 或签名真机包。

## 短信 / 微信 / OBS 供应商证据材料

机器校验证据：`Backend/proof/provider-evidence-materials.json`，当前 `passed=true`。

已覆盖：

1. `07-sms-provider.png`：真实短信服务商、签名、模板和发送成功证据；遮挡 AccessKey、Secret、`XNP_SMS_SECRET`、完整手机号和验证码。
2. `08-wechat-open-platform.png`：微信开放平台 AppID、Bundle ID、URL Scheme、Universal Link 和移动应用状态；遮挡 AppSecret 和管理员账号，AppSecret 只在服务端私有 env。
3. `09-obs-policy.png`：华为 OBS bucket / prefix、区域、加密、生命周期和删除验证；遮挡 AK/SK、完整对象 key、宝宝姓名、生日、备注和原始文件名。
4. `check_provider_evidence_materials.py` 只证明材料要求完整，不会让 `app-store-evidence.json` 对短信、微信、OBS 的真实人工证据变绿。

## TestFlight 前检查

检查文件：`Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`。

已补充：

1. 本机测试固定 iOS 26.5。
2. 真机启动、恢复密钥登录、云备份、云恢复、账号删除、通知权限。
3. 灵动岛喝奶提醒开关、锁屏/桌面小组件、审核边界文案。
4. Live Activity 和小组件不得展示照片原图、备注、token、对象 key、压力评估、健康建议或医疗诊断。
5. 已生成 `Backend/proof/testflight-precheck.json`，验证资料页账号与备份入口、恢复密钥/手机号/微信登录、云备份、云恢复、云端账号删除、生产 API endpoint 绑定、Widget extension、Live Activity、Dynamic Island、本地通知、App Group、Associated Domains 和共享 payload 边界。
6. 已生成 `Backend/proof/testflight-regression-plan.json`，验证 RD-01 到 RD-24 覆盖登录、云备份、云恢复、账号删除、通知权限、灵动岛、小组件、审核边界、证据路径，`12-real-device-regression.template.md` 仍要求 iOS 26.5 / TestFlight 或签名真机包 / 脱敏证据，清单和模板都包含 `RealDevice/00-overview.png` 与 `RealDevice/RD-01...RD-24...png` 稳定证据文件名，以及 TestFlight / 签名真机回归尚未完成的明确边界；`Backend/proof/app-store-evidence.json` 会额外拒绝空白或目录型 RD 证据路径。
7. 已生成 `Backend/proof/sim-launch-ios265-20260626.json`，验证 iOS 26.5 模拟器安装和启动成功。

仍需真实 TestFlight / 签名真机执行并归档；当前可用真机是 iOS 27.0，不符合本项目“本机测试只用 iOS 26.5”的规则，未执行真机回归：

```text
Docs/08_Release/AppStoreEvidence/12-real-device-regression.md
```

## 审核说明边界

已同步到 `Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md`、`Docs/08_Release/APP_STORE_METADATA.md` 和 `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md`：

1. 灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图。
2. 桌面/锁屏小组件只读展示今日摘要。
3. 这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。
4. 所有摘要来自用户在 App 内输入并保存在本机记录的数据。
5. 不接入 HealthKit、传感器、医院系统或第三方健康数据源。
6. 不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议。

`Backend/scripts/check_review_notes.py` 已新增检查，确保 Review Notes 覆盖灵动岛、小组件、状态展示、用户输入数据来源、无 HealthKit / 无压力评估和不生成健康建议/压力提醒/喂养建议边界。

## 当前不可提交原因

1. 真实微信开放平台 AppID / AppSecret 未配置。
2. iOS Release 包缺真实 `wx...` AppID / URL Scheme；假 `wx...` dry-run 值已不能让 Release 或 bundle gate 通过。
3. App Store Connect 人工证据未补齐。
4. App Store Distribution 签名归档和 TestFlight 未完成。
5. 中国大陆 APP 备案 / ICP / 大陆合规证据未归档。
