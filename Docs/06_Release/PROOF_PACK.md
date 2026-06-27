# PROOF_PACK.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：中国大陆首发提交证据包
- 日期：2026-06-18

## 已确认事实

1. 每个可发布版本都必须有证据包。
2. 第一版只面向 iOS。
3. 隐私审查和测试证据是上线前必需项。

## 合理推断

1. 对儿童和家庭数据，证据包必须记录隐私决策。
2. 如果启用服务器存储，证据包必须包含上传字段和删除测试结果。

## 待我确认的问题

1. 证据包是否需要同时输出给外部测试家庭阅读。
2. 是否需要归档 TestFlight 反馈。

## 不进入第一版的功能

1. macOS 发布证据。
2. 付费能力证据。
3. 社区审核证据。

## 本版本完成内容

1. 新增最小第一方后端：恢复密钥账号、手机号登录接口、微信登录接口、备份上传/恢复、照片原图上传/下载/删除、账号删除。
2. 新增 iOS 云备份接入：Keychain 会话、云备份 API 客户端、资料页账号、手机号/微信入口与备份操作。
3. 新增隐私政策草案、App Store 元数据草案、账号删除说明和后端部署说明。
4. 新增对象存储抽象，默认磁盘模式和可选华为云 OBS 模式。
5. 新增本地发布流验证脚本和 JSON 证据。
6. 新增可由正式 API 域名托管的 `/privacy`、`/terms`、`/support` 公开页面。
7. 新增 App Store 截图计划和生产回滚方案草案。
8. 新增生产发布预检脚本，用于检查 Release API、华为云 OBS、远端验证、截图证据和 App Store URL 是否已补齐。
9. 新增 App Store 可填写提交包和机器可读隐私标签草案。
10. 新增无密钥后端部署包生成脚本和 manifest 校验。
11. 新增香港区第二批上架 runbook：`Docs/08_Release/HONG_KONG_APP_STORE_RUNBOOK.md`。
12. 新增 App 内跟随系统语言的繁体中文香港 `zh-Hant-HK` 资源。
13. 新增 App 内中国大陆 / 香港疫苗模板地区切换，已安装用户不按所在地隐藏模板入口。
14. 新增中国大陆上线执行包：`Docs/08_Release/LAUNCH_EXECUTION_PACKET.md`。
15. 新增 ICP / App 备案材料包：`Docs/08_Release/MAINLAND_FILING_MATERIALS.md`。
16. 新增测试账号与真机回归清单：`Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`。
17. 新增 iOS Release 包体自检文档：`Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md`。
18. 新增微信客户端配置交接文档：`Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md`。
19. 新增 2026-06-26 上线闸门复跑报告：`Docs/08_Release/LAUNCH_GATE_RERUN_20260626.md`。
20. 新增 TestFlight 客户端预检脚本和 iOS 26.5 安装启动烟测证据。
21. 新增 App Store Connect 文案材料预检脚本和 proof。
22. 新增 App Store 提交包预检脚本和 proof，固定官方 Apple 入口、Review Notes、Do Not Submit 禁区、隐私标签来源、截图边界和预提交命令。

## 需求对应关系

| 需求 | 证据 |
|---|---|
| 后端账号 | `Backend/api/server.py` 中 `POST /v1/accounts` 和 `POST /v1/sessions/recover` |
| 手机号登录 | `POST /v1/auth/phone/request-code`、`POST /v1/auth/phone/verify`；服务端支持生产短信 webhook，真实服务商待配置 |
| 微信登录 | `POST /v1/auth/wechat/login`；服务端支持微信 code 换 openid/unionid，iOS 已补 OpenSDK 授权桥，真实 SDK 依赖和开放平台凭证待配置 |
| 备份恢复 | `PUT /v1/backup`、`GET /v1/backup`；iOS `CloudBackupController.restoreLatestBackup` |
| 照片云存储 | `PUT /v1/photos/{photoId}`、`GET /v1/photos/{photoId}`、`DELETE /v1/photos/{photoId}`；`Backend/api/storage.py` |
| 账号删除 | `DELETE /v1/account`；资料页二次确认入口 |
| 隐私政策 | `Docs/08_Release/PRIVACY_POLICY_DRAFT.md` |
| App Store 元数据 | `Docs/08_Release/APP_STORE_METADATA.md` |
| App Store 提交包 | `Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md` |
| App Store 隐私标签 | `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` |
| iOS Privacy Manifest | `App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy` |
| 中国大陆 App Store runbook | `Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md` |
| 中国大陆上线执行包 | `Docs/08_Release/LAUNCH_EXECUTION_PACKET.md` |
| ICP / App 备案材料包 | `Docs/08_Release/MAINLAND_FILING_MATERIALS.md` |
| 测试账号与真机回归清单 | `Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md` |
| iOS Release 包体自检文档 | `Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md` |
| 微信客户端配置交接 | `Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md` |
| 2026-06-26 上线闸门复跑 | `Docs/08_Release/LAUNCH_GATE_RERUN_20260626.md` |
| 2026-06-26 上线阻断行动包 | `Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260626.md` |
| 香港区第二批上架 runbook | `Docs/08_Release/HONG_KONG_APP_STORE_RUNBOOK.md` |
| 香港繁中 App 内语言 | `App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/Localizable.strings` 和 `App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/InfoPlist.strings` |
| 发布流证据 | `Backend/proof/release-flow.json` |
| 无密钥部署证明采集 | `Backend/scripts/collect_deployment_proof.py` |
| 生产发布预检 | `Backend/scripts/check_production_readiness.py` 和 `Backend/proof/production-readiness.json` |
| 已知阻断范围预检 | `Backend/scripts/check_launch_blocker_scope.py` 和 `Backend/proof/launch-blocker-scope.json` |
| 上线目标总审计 | `Backend/scripts/check_launch_objective_audit.py` 和 `Backend/proof/launch-objective-audit.json` |
| 上线阻断行动包预检 | `Backend/scripts/check_launch_blocker_action_packet.py` 和 `Backend/proof/launch-blocker-action-packet.json` |
| App Store 资源预检 | `Backend/scripts/check_app_store_assets.py` 和 `Backend/proof/app-store-assets.json` |
| App Store Connect 文案材料预检 | `Backend/scripts/check_app_store_connect_materials.py` 和 `Backend/proof/app-store-connect-materials.json` |
| App Store 提交包预检 | `Backend/scripts/check_app_store_submission_packet.py` 和 `Backend/proof/app-store-submission-packet.json` |
| iOS 26.5 构建预检 | `Backend/scripts/check_ios_265_build_proof.py` 和 `Backend/proof/ios-265-build.json` |
| iOS 26.5 真机可用性预检 | `Backend/scripts/check_ios265_device_availability.py` 和 `Backend/proof/ios265-device-availability.json` |
| iOS 发布预检 | `Backend/scripts/check_ios_release_readiness.py` 和 `Backend/proof/ios-release-readiness.json` |
| iOS Release 产物预检 | `Backend/scripts/check_ios_app_bundle.py` 和 `Backend/proof/ios-app-bundle.json` |
| TestFlight 客户端预检 | `Backend/scripts/check_testflight_precheck.py` 和 `Backend/proof/testflight-precheck.json` |
| TestFlight / 真机回归清单预检 | `Backend/scripts/check_testflight_regression_plan.py` 和 `Backend/proof/testflight-regression-plan.json` |
| iOS 26.5 安装启动烟测 | `Backend/proof/sim-launch-ios265-20260626.json` |
| 认证服务商预检 | `Backend/scripts/verify_auth_providers.py` 和 `Backend/proof/auth-providers.json` |
| 诊断与日志脱敏预检 | `Backend/scripts/check_diagnostics_redaction.py` 和 `Backend/proof/diagnostics-redaction.json` |
| 公开审核页面预检 | `Backend/scripts/check_public_pages.py` 和 `Backend/proof/public-pages.json` |
| Review Notes 预检 | `Backend/scripts/check_review_notes.py` 和 `Backend/proof/review-notes.json` |
| 法务草案预检 | `Backend/scripts/check_legal_drafts.py` 和 `Backend/proof/legal-drafts.json` |
| Universal Links / AASA 预检 | `Backend/scripts/check_universal_links.py` 和 `Backend/proof/universal-links.json` |
| 微信客户端配置交接预检 | `Backend/scripts/check_wechat_client_configuration.py` 和 `Backend/proof/wechat-client-configuration.json` |
| App Store 人工证据门禁 | `Backend/scripts/check_app_store_evidence.py` 和 `Backend/proof/app-store-evidence.json` |
| 对象存储验证 | `Backend/scripts/verify_storage_backend.py` 和 `Backend/proof/storage-backend.json` |
| 后端部署包 | `Backend/scripts/build_deploy_bundle.py` 和 `Backend/proof/deploy-bundles/*.manifest.json` |
| 公开审核 URL | `Backend/static/privacy.html`、`Backend/static/terms.html`、`Backend/static/support.html` |
| 截图计划 | `Docs/08_Release/SCREENSHOT_PLAN.md` |
| 回滚方案 | `Docs/06_Release/ROLLBACK_PLAN.md` |
| 中国大陆 / 香港疫苗模板切换 | `App/iOS/XiaoNaiPing/Views/VaccineView.swift` 和 `App/iOS/XiaoNaiPing/Models/BabyRecordStore.swift` |

## 截图证据

已补 5 张 iPhone 16 Pro 模拟器截图：

1. `Docs/08_Release/Screenshots/home-iphone16pro.png`
2. `Docs/08_Release/Screenshots/record-iphone16pro.png`
3. `Docs/08_Release/Screenshots/growth-iphone16pro.png`
4. `Docs/08_Release/Screenshots/profile-iphone16pro.png`
5. `Docs/08_Release/Screenshots/profile-backup-iphone16pro.png`

以上截图均已人工查看确认非空白，其中 `profile-backup-iphone16pro.png` 展示了手机号登录、验证码输入、手机号登录按钮、微信登录和恢复密钥登录。2026-06-25 已重新生成候选图，避免出现 `127.0.0.1`、token、真实宝宝照片和 Debug 文案。当前截图仍是候选截图，正式 TestFlight / 签名真机截图仍需补齐。

## 测试证据

1. `python3 -m unittest discover -s Backend/tests` 通过，覆盖后端、脚本和发布闸门测试，包括生产短信 webhook、微信 code exchange 替身、认证服务商 proof、诊断脱敏 proof、公开审核页面 proof、Review Notes proof、法务草案 proof、Universal Links / AASA proof、App Store 资源、App Store Connect 文案材料、App Store Connect 人工证据材料、iOS 26.5 构建预检、TestFlight 客户端预检、TestFlight / 真机回归清单预检、短信/微信/OBS 供应商证据材料预检和生产预检。
2. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/xnp-dd-debug build CODE_SIGNING_ALLOWED=NO` 通过。
3. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/xnp-dd-release build CODE_SIGNING_ALLOWED=NO` 通过。
4. `cd Backend && python3 -m unittest discover -s tests` 通过，确认从 Backend 工作目录执行也可用。
5. `py_compile` 通过，覆盖 11 个 Python 文件，包括后端、发布验证脚本、截图脚本和测试文件；编译产物写入 `/private/tmp/xnp-pyc`，避免系统缓存权限问题。
6. `python3 Backend/scripts/verify_release_flow.py --output Backend/proof/release-flow.json` 通过，包含恢复密钥、手机号 debug 登录和微信 debug 登录。
7. `python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --require-huawei-obs --require-screenshots --require-app-store-evidence --live-check --allow-incomplete --output Backend/proof/production-readiness.json` 已生成当前预检报告，结论为未就绪；公网 HTTPS、App Store URL、远端证据、Secret、MySQL、OBS、Admin Token、生产 debug 关闭、公网 internal 封禁、live 静态页、App Store 资源预检、诊断脱敏预检、公开审核页面预检、Review Notes 预检、法务草案预检和 Universal Links / AASA 预检均已通过，剩余失败项为微信服务端配置、iOS 微信 Release 配置、认证服务商 proof 和 App Store 人工证据。
8. `python3 Backend/scripts/capture_ios_screenshots.py --device 4C0B71E2-AE32-427E-A26E-6CDCDA1743B6 --app /tmp/xnp-dd-debug/Build/Products/Debug-iphonesimulator/XiaoNaiPing.app --output-dir Docs/08_Release/Screenshots --shutdown` 已生成截图证据。
9. `python3 Backend/scripts/build_deploy_bundle.py --output-dir Backend/proof/deploy-bundles` 已生成无密钥部署包和 manifest，最新文件为 `xiaonaiping-backend-20260620T073007Z.tar.gz`，manifest 中 `containsSecrets` 为 `false`。
10. `Backend/proof/huawei-baota-deploy-20260620.json` 记录华为云 ECS + 宝塔 MySQL 部署证据：独立目录 `/srv/xiaonaiping`、独立 systemd 服务 `xiaonaiping-api.service`、独立数据库 `xiaonaiping_prod`、独立用户 `xiaonaiping_app`，未复用情绪 App 目录、服务或数据库。
11. 公网 HTTPS 过渡路径 `https://api.mewpow.com/xiaonaiping` 已配置到独立 `xiaonaiping-api.service`；`Backend/proof/remote-api.json` 通过健康检查、隐私/协议/支持页、账号创建、备份上传/恢复、照片上传/下载、恢复密钥登录、账号删除和删除后 token 失效。公网 `/xiaonaiping/internal` 和 `/xiaonaiping/internal/` 已由 Nginx 返回 404，服务器本机 `127.0.0.1:8787/internal/dashboard` 仍可用于内网/SSH 运维。
12. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive archive` 未通过；Xcode 报错：`Signing for "XiaoNaiPing" requires a development team`。
13. `plutil -lint App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/Localizable.strings App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/InfoPlist.strings` 通过。
14. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/xnp-dd-release-l10n-final build CODE_SIGNING_ALLOWED=NO` 通过，并确认 App bundle 内包含 `zh-Hant-HK.lproj/Localizable.strings` 和 `zh-Hant-HK.lproj/InfoPlist.strings`。
15. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/xnp-dd-release-mainland-vaccine-final build CODE_SIGNING_ALLOWED=NO` 通过，覆盖中国大陆 / 香港疫苗模板切换改动。
16. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPingRemoteAPI-Release CODE_SIGNING_ALLOWED=NO -quiet build` 通过；产物 `Info.plist` 中 `XNPAPIBaseURL=https://api.mewpow.com/xiaonaiping`。
17. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/XiaoNaiPingRemoteAPI-Debug CODE_SIGNING_ALLOWED=NO -quiet build` 通过；Debug 产物 `XNPAPIBaseURL` 为空，仍可用环境变量接本地后端。
18. `python3 -m unittest Backend/tests/test_collect_deployment_proof.py Backend/tests/test_auth_provider_verification.py Backend/tests/test_diagnostics_redaction.py Backend/tests/test_public_pages.py Backend/tests/test_review_notes.py Backend/tests/test_legal_drafts.py Backend/tests/test_universal_links.py Backend/tests/test_app_store_assets.py Backend/tests/test_app_store_connect_materials.py Backend/tests/test_ios_265_build_proof.py Backend/tests/test_ios_app_bundle.py Backend/tests/test_ios_release_readiness.py Backend/tests/test_production_readiness.py Backend/tests/test_testflight_precheck.py Backend/tests/test_testflight_regression_plan.py Backend/tests/test_app_store_evidence.py Backend/tests/test_storage_verification.py Backend/tests/test_api.py Backend/tests/test_database.py` 通过；覆盖无密钥部署证明采集、认证服务商预检、诊断脱敏预检、公开审核页面预检、Review Notes 预检、法务草案预检、Universal Links / AASA 预检、App Store 资源预检、App Store Connect 文案材料预检、iOS 26.5 构建预检、iOS Release 产物预检、iOS 发布预检、TestFlight 客户端预检、TestFlight / 真机回归清单预检、生产预检远端证明读取、生产 debug 关闭、App Store 人工证据、对象存储验证、internal 公网封禁和错误命名空间拒绝测试。
19. `python3 Backend/scripts/verify_remote_api.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/remote-api.json` 于 2026-06-24 通过，远程账号、备份、照片、恢复密钥和删除闭环均为 true。
20. `python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json` 已生成 App Store 人工证据缺口报告，当前 `ready=false`，缺少公司主体、可售地区、备案、隐私标签、签名归档、TestFlight、短信服务商截图、微信开放平台截图、OBS 策略截图和 iOS 26.5 真机回归记录；5 张当前 iPhone 17 Pro / iOS 26.5 Debug simulator 截图已归档到 `Docs/08_Release/AppStoreEvidence/10-final-screenshots/` 作为最终候选截图，并由 `PROVENANCE.json` 记录来源。`app-store-evidence` 会要求 `app-store-assets` 的截图数量、上传顺序、尺寸、非空白、无真实宝宝照片文件名和 iOS 26.5 provenance 全部通过。真机回归证据已加严为必须填完 iOS 26.5 环境、安装方式、截图/录屏路径，RD-01 到 RD-24 不得保留待测占位，审核边界确认项必须全部勾选，也不得包含完整手机号、恢复密钥、token 或 debug code。
21. `XNP_STORAGE_BACKEND=disk XNP_DATA_DIR=/private/tmp/xnp-storage-verification python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend.json` 通过，证明对象存储验证脚本可执行；当前证明是 `disk`，不能替代正式 OBS 证明。
22. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/XiaoNaiPing-Continue-Debug CODE_SIGNING_ALLOWED=NO -quiet build` 通过。
23. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-Continue-Release CODE_SIGNING_ALLOWED=NO -quiet build` 通过；产物 `XNPAPIBaseURL=https://api.mewpow.com/xiaonaiping`。
24. `python3 Backend/scripts/check_ios_release_readiness.py --allow-incomplete --output Backend/proof/ios-release-readiness.json` 已生成 iOS 发布预检报告，当前 `passed=false`，失败项为 `weChatReleaseBuildSettingsConfigured`；Privacy Manifest 存在、进入资源、tracking 关闭，并与 App Store 隐私标签草案中的账号、手机号、用户内容、照片、健康、产品交互和诊断类别双向匹配，既不漏声明也不多声明。`CFBundleURLTypes` 已接到 `$(XNP_WECHAT_URL_SCHEME)`，拿到真实 `wx...` 后可通过 build setting 注入；`weChatAuthorizationBridgePresent=true`，已检查 OpenSDK 注册、授权请求、URL/Universal Link 回调和后端 code exchange 调用。
25. Release 里的微信登录按钮已改为按 `CloudBackupConfiguration.isWeChatLoginConfigured` 禁用；没有 WeChat OpenSDK、AppID、URL Scheme、Universal Link 时，不再让用户点击假微信登录后才失败。配置齐全后，iOS 端会通过 `WeChatLoginService` 拉起微信授权并把返回 code 交给 `/v1/auth/wechat/login`。
26. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/XiaoNaiPing-IOSGate-Debug CODE_SIGNING_ALLOWED=NO -quiet build` 通过。
27. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-IOSGate-Release CODE_SIGNING_ALLOWED=NO -quiet build` 通过；产物 `XNPAPIBaseURL=https://api.mewpow.com/xiaonaiping`。当前 iOS 发布预检已确认 Universal Link / AASA 通过，仍由微信 AppID、真实 `wx...` URL Scheme 和 OpenSDK 依赖阻断。
28. `plutil -lint App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy` 通过；该文件已加入 `App/iOS/project.yml` 和 Xcode Copy Bundle Resources。
29. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/XiaoNaiPing-PrivacyManifest-Debug CODE_SIGNING_ALLOWED=NO -quiet build` 通过。
30. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-PrivacyManifest-Release CODE_SIGNING_ALLOWED=NO -quiet build` 通过；产物内已确认存在 `PrivacyInfo.xcprivacy`，并且 `XNPAPIBaseURL=https://api.mewpow.com/xiaonaiping`。
31. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-BundleGate-Release CODE_SIGNING_ALLOWED=NO -quiet build` 通过。
32. `python3 Backend/scripts/check_ios_app_bundle.py --app /tmp/XiaoNaiPing-WeChatSlot-Release/Build/Products/Release-iphoneos/XiaoNaiPing.app --allow-incomplete --output Backend/proof/ios-app-bundle.json` 已生成 iOS Release 产物预检报告，当前 `passed=false`，失败项为 `weChatNativeConfigPresent`、`weChatURLTypePresent`；产物中的 Release API、Privacy Manifest（含 ProductInteraction）、繁中香港资源和 debug 微信码缺失检查均已通过。由于 Release `XNP_WECHAT_*` build settings 仍为空，构建产物没有真实 `wx...` URL Scheme。
33. `python3 Backend/scripts/check_app_store_assets.py --output Backend/proof/app-store-assets.json` 已生成 App Store 资源预检报告，当前 `passed=true`；1024 x 1024 AppIcon PNG、无 alpha、5 张最终候选截图数量、尺寸、上传顺序文件名、非空白像素内容和 iOS 26.5 screenshot provenance 均通过。
34. `Backend/scripts/collect_deployment_proof.py` 已新增并通过测试，可从 `/srv/xiaonaiping/private/xiaonaiping-api.env` 生成不含密码、token、AK/SK 的部署证明，记录 OBS、短信、微信、MySQL 和 namespace 状态；正式服务器 env 变更后必须刷新 `Backend/proof/huawei-baota-deploy-20260620.json` 或生成新的 dated proof。
35. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-WeChatSlot-Release CODE_SIGNING_ALLOWED=NO -quiet build` 通过；验证 `CFBundleURLTypes` build setting 插槽未破坏 Release 构建。
36. `python3 Backend/scripts/verify_auth_providers.py --live-check --allow-incomplete --output Backend/proof/auth-providers.json` 已生成认证服务商预检报告，当前 `passed=false`，失败项为 `wechatProviderConfigured`；短信 webhook 和一次短信发送探测已通过，线上 `/v1/auth/wechat/login` 已拒绝 `debug_wechat_*` 调试码并返回 HTTP 501，证明生产 debug 入口未打开。最终提交前仍需归档短信服务商人工证据，并完成微信开放平台配置。
37. `python3 Backend/scripts/check_diagnostics_redaction.py --output Backend/proof/diagnostics-redaction.json` 已生成诊断与日志脱敏预检报告，当前 `passed=true`；iOS 未发现第三方 crash/analytics SDK 标记、未发现 Swift 客户端日志调用、Privacy Manifest 声明 crash/performance diagnostics、后端 HTTP 日志会把 `/v1/photos/{photoId}` 记录为 `/v1/photos/<redacted>`。TestFlight 真实崩溃样本仍需在上传构建后人工归档。
38. `python3 Backend/scripts/check_public_pages.py --output Backend/proof/public-pages.json` 已生成公开审核页面预检报告，当前 `passed=true`；`/privacy`、`/terms`、`/support` 已改为中国大陆首发、香港第二批、深圳市闪现生活科技有限公司主体和恢复密钥/手机号/微信账号方式，并清除了旧的区域发布策略文案。
39. `python3 Backend/scripts/check_review_notes.py --output Backend/proof/review-notes.json` 已生成 Review Notes 预检报告，当前 `passed=true`；审核说明覆盖免费、无 IAP、无广告、无第三方分析、无医疗建议、本地优先、恢复密钥/手机号/微信登录、主动备份、照片原图、删除路径、疫苗边界和不依赖 debug code。
40. `python3 Backend/scripts/check_legal_drafts.py --output Backend/proof/legal-drafts.json` 已生成法务草案预检报告，当前 `passed=true`；隐私政策和用户协议草案日期已更新到 2026-06-24，覆盖中国大陆首发、香港第二批、深圳市闪现生活科技有限公司主体、恢复密钥/手机号/微信登录、照片原图备份、删除路径和非医疗建议边界。
41. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' -derivedDataPath /tmp/XiaoNaiPing-WeChatBridge-Debug CODE_SIGNING_ALLOWED=NO -quiet build` 和 `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-WeChatBridge-Release CODE_SIGNING_ALLOWED=NO -quiet build` 均通过，验证新增微信授权桥没有破坏当前无 SDK 构建；真实 WeChat OpenSDK 依赖、AppID、URL Scheme 和 Universal Link 仍需外部配置后复测。
42. `python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json` 已生成 Universal Links / AASA 预检报告，当前 `passed=true`；后端会托管 `/apple-app-site-association` 和 `/.well-known/apple-app-site-association`，AASA 覆盖 `JGCT3GY9CT.com.mewpow.xiaonaiping`、`/wechat/*` 和当前过渡路径 `/xiaonaiping/wechat/*`，iOS entitlements 已接入 `$(XNP_ASSOCIATED_DOMAIN)`，Release 当前使用 `applinks:api.mewpow.com` 与 `https://api.mewpow.com/xiaonaiping/wechat/`。
43. 历史候选截图曾用旧模拟器重截 5 张；当前提交口径不再把旧 runtime 截图命令作为本机验证证据。2026-06-27 已用 iPhone 17 Pro / iOS 26.5 Debug simulator、截图 seed data 和生产 API URL injection 重截 `Docs/08_Release/Screenshots/` 并同步到 `Docs/08_Release/AppStoreEvidence/10-final-screenshots/`，来源证明为 `PROVENANCE.json`。
44. 已创建恢复密钥审核测试账号并写入虚构宝宝测试数据；密钥仅保存在本机忽略文件 `.env.xnp-review-account`，仓库证据为 `Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json`。
45. `xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -derivedDataPath /tmp/XiaoNaiPing-BundleReuse-Release CODE_SIGNING_ALLOWED=NO -quiet build` 通过；修正 `Audio/README.md` 误入 Release `.app` 后，新包手动扫描没有 README / Markdown / HTML / env 文件。
46. `python3 Backend/scripts/check_ios_app_bundle.py --app /tmp/XiaoNaiPing-BundleReuse-Release/Build/Products/Release-iphoneos/XiaoNaiPing.app --allow-incomplete --output Backend/proof/ios-app-bundle.json` 已刷新，当前失败项仅为 `weChatNativeConfigPresent`、`weChatURLTypePresent`；新增包体内容检查 `releaseBundleInternalDocsAbsent` 和 `releaseBundleForbiddenTextMarkersAbsent` 均通过。
47. `Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md` 已记录微信客户端配置的已完成项、不可造假的后台值、真实 `wx...` 注入命令和截图归档要求。
48. 已用明显假的 `wxclientdryrun123456` 完成微信客户端注入干跑：Release `Info.plist` 可写入 `XNPWeChatAppID` / `XNPWeChatURLScheme` / `XNPWeChatUniversalLink`。2026-06-26 已收紧 `check_ios_release_readiness.py` 和 `check_ios_app_bundle.py`，当前脚本会拒绝 dry-run / debug / test / placeholder 微信值；旧版干跑通过结果只证明客户端注入机制可用，不是 App Store 提交证据。
49. 2026-06-27 00:58 CST 按 iOS 26.5 复跑上线闸门：Release Simulator 构建、Release iPhoneOS 构建、后端单测 165 tests、Review Notes、法务草案、App Store 资源、App Store Connect 文案材料、App Store Connect 人工证据材料、App Store 提交包、公开页、Universal Links、诊断脱敏、远端 API、TestFlight 客户端预检、主 App 审核 surface 文案、iOS 26.5 包内隐私清单内容检查、iOS 26.5 安装启动烟测、截图 provenance gate、真机回归模板严格性、`RealDevice/` 稳定证据文件名和真机回归审核边界确认项均通过；真实微信、真实 iOS 26.5 TestFlight / 签名真机回归和 App Store 人工证据仍阻断。本轮 proof 刷新为 `20260626T165817Z`，详见 `Docs/08_Release/LAUNCH_GATE_RERUN_20260626.md`。
50. `python3 Backend/scripts/check_testflight_precheck.py --app /tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app --output Backend/proof/testflight-precheck.json --allow-incomplete` 通过；验证 Widget extension、Live Activity / Dynamic Island、本地通知、App Group、Associated Domains、共享 widget payload、无 HealthKit / 压力评估源码面，并检查主 App 审核 surface、Widget/Live Activity/本地通知展示文案未出现医疗、健康建议、压力或心理判断标记。
51. `xcrun simctl install 07D2E9B8-B283-4F62-88D7-AFF7B7E82ED4 /tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app` 与 `xcrun simctl launch --terminate-running-process 07D2E9B8-B283-4F62-88D7-AFF7B7E82ED4 com.mewpow.xiaonaiping` 在 iPhone 17 Pro / iOS 26.5 通过，启动输出 `com.mewpow.xiaonaiping: 92544`，证据为 `Backend/proof/sim-launch-ios265-20260626.json`。
52. `Backend/proof/production-readiness.json` 已纳入 `testFlightClientPrecheckProofPassed`、`ios265SimulatorLaunchProofPassed`、`appStoreConnectEvidenceMaterialsProofPassed` 和 `providerEvidenceMaterialsProofPassed`；四项均通过，当前总闸门失败项仍包含微信 provider、iOS 微信 Release 配置、认证服务商 proof 和 App Store 人工证据；短信 provider 在 current proof 中已通过，但短信服务商人工证据仍未归档。
53. `python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json --allow-incomplete` 通过；默认读取最新日期的 `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md`，验证 App 名称、副标题、Bundle ID、主分类/第二分类、首发地区、价格、URL、关键词、描述、年龄分级、隐私标签采集/关联身份/用途/追踪/App flags、截图文案和审核备注边界。
54. `python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json --allow-incomplete` 通过；验证恢复密钥审核账号 redacted proof、RD-01 到 RD-24 覆盖、真实短信/微信待配置标记、真机证据路径、iOS 26.5 烟测引用、无密钥泄露、`12-real-device-regression.template.md` 仍要求 iOS 26.5 / TestFlight 或签名真机包 / 脱敏证据，清单和模板都包含 `RealDevice/00-overview.png` 与 `RealDevice/RD-01...RD-24...png` 稳定证据文件名，以及计划 proof 不替代真实 TestFlight / 签名真机证据。
55. `python3 Backend/scripts/check_ios_265_build_proof.py --output Backend/proof/ios-265-build.json --allow-incomplete` 通过；验证 Release Simulator `iphonesimulator26.5`、Release iPhoneOS `iphoneos26.5`、Bundle ID、Release API、Live Activities、Widget extension，以及 simulator / device 包内 `PrivacyInfo.xcprivacy` 的 tracking 关闭、tracking domains 为空、采集数据类型与 App Store 隐私标签对齐且每项不用于追踪。
56. `python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json` 通过；验证 App Review Guidelines、隐私标签、截图规格、年龄分级、受监管医疗设备声明等官方 Apple 入口，以及提交包里的 Export Compliance、年龄分级/受监管医疗器械回答、Live Activity / 小组件 / HealthKit / 压力评估 / 医疗诊断边界、App Store Connect 人工证据材料 gate 命令和供应商证据材料 gate 命令。
57. `python3 Backend/scripts/check_launch_blocker_scope.py --output Backend/proof/launch-blocker-scope.json` 通过；验证当前红项只落在已知真实阻断范围内：生产私有 env、MySQL、OBS、namespace、短信人工证据、微信 provider、iOS 微信配置和 App Store 人工证据。该 proof 只说明阻断项范围可解释，不代表可以提交。
58. `python3 Backend/scripts/check_ios265_device_availability.py --output Backend/proof/ios265-device-availability.json` 通过；记录当前 iOS 26.5 真机 `蓝蓝` 不可用、当前可用 iPhone `面面` 为 iOS 27.0，因此不符合本项目本机测试只用 iOS 26.5 的规则，未纳入真机回归。
59. `Backend/scripts/run_launch_readiness.sh` 已收紧日志判定：对使用 `--allow-incomplete` 生成的 proof，会二次读取 JSON 的 `passed` / `ready` 字段；只有真通过才打印 `[proof-ok]`，未通过会打印 `[incomplete]` 并让总命令返回非 0，避免 proof 文件生成成功被误读为上线闸门通过。
60. `python3 Backend/scripts/check_launch_objective_audit.py --output Backend/proof/launch-objective-audit.json --allow-incomplete` 已新增上线目标总审计 proof；它把本轮目标中的 iOS 26.5、Bundle ID、WeChat、隐私清单内容、后端 proof、App Store 图标/截图资源、App Store Connect 文案、App Store Connect 人工证据材料、供应商证据材料、TestFlight 客户端前检查、TestFlight / 真机回归计划、真机证据和审核说明逐项映射到权威 JSON。当前 `ready=false`，失败项为微信配置、真实 iOS 26.5 TestFlight / 签名真机回归证据、App Store 人工证据和生产 readiness。
61. `python3 Backend/scripts/check_launch_blocker_action_packet.py --output Backend/proof/launch-blocker-action-packet.json --allow-incomplete` 已新增上线阻断行动包 proof；它读取当前 `launch-objective-audit.json`、`app-store-evidence.json` 和 `ios-265-build.json`，验证 `Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260626.md` 覆盖当前红项、每个外部证据文件名、微信开放平台配置动作、本机测试只使用 iOS 26.5、真机证据不能由模拟器替代、复跑命令，以及当前 iOS 26.5 simulator/device 构建日志文件名。
62. `python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration.json` 已新增微信客户端配置交接 proof；它验证 `WECHAT_CLIENT_CONFIGURATION.md` 写清真实 `wx + 16 hex` AppID/URL Scheme、Universal Link、服务端 AppSecret 边界、iOS 26.5 本机验证命令、证据归档路径，并确认 `project.yml`、`Info.plist` 和 Release entitlements 的微信 / Associated Domains 槽位仍已接好。
63. `python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json` 已新增短信/微信/OBS 供应商证据材料 proof；它验证 `07-sms-provider.png`、`08-wechat-open-platform.png`、`09-obs-policy.png` 的保留字段、脱敏字段、provider/storage 验证命令和“未归档真实文件前不得声称完成”的边界。该 proof 不替代真实短信服务商截图、微信开放平台截图或 OBS 策略截图。
64. `python3 Backend/scripts/check_app_store_connect_evidence_materials.py --output Backend/proof/app-store-connect-evidence-materials.json` 已新增 App Store Connect 人工证据材料 proof；默认读取最新日期的 `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md`，验证 `01-company-account.png`、`02-mainland-availability.png`、`04-privacy-label.png` 的保留字段、脱敏字段、隐私标签 JSON 一致性、预提交命令和“未归档真实文件前不得声称完成”的边界。该 proof 不替代真实 App Store Connect 主体、可售地区或隐私标签截图。
65. `Backend/proof/testflight-regression-plan.json` 已新增 `realDeviceEvidenceFilenamePlanPresent` 检查；机器验证 `Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md` 和 `Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md` 同时列出 `RealDevice/00-overview.png` 与 RD-01 到 RD-24 的稳定截图/录屏文件名，后续真机回归不能只写目录或临时口头路径。

## 隐私审查结果

隐私复核已更新到 `Docs/07_PrivacySecurity/PRIVACY_REVIEW.md`。当前结论：最小实现已具备账号、备份、照片和账号删除闭环；正式提交前仍需真实隐私政策 URL、生产服务器区域、删除 SLA、对象存储策略和 TestFlight / App Store Connect 真实崩溃样本归档。
`App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy` 已补齐为当前 iOS bundle 隐私清单，声明不追踪，并与 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` 中已声明采集的账号标识、手机号、用户内容、照片、健康记录、产品交互和诊断数据双向匹配。
`Backend/proof/diagnostics-redaction.json` 已补代码层诊断与日志脱敏证据，后端照片对象路径不再进入访问日志明文。
`Backend/proof/legal-drafts.json` 已补隐私政策和用户协议草案当前性证据，避免旧版香港/美国首发、排除中国大陆、恢复密钥单一账号和公司主体占位文案进入提交包。
`Backend/proof/universal-links.json` 已补微信 Universal Link / AASA 证据，避免 App 端配置了微信登录但域名回调链路缺失。

## 数据删除证据

后端单元测试和 `Backend/proof/release-flow.json` 覆盖账号删除后 token 失效、备份删除和照片对象删除。生产环境仍需补充对象存储生命周期和备份删除验证截图/日志。

## 已知问题

1. Release 构建已配置 `XNP_API_BASE_URL=https://api.mewpow.com/xiaonaiping`；后续仍建议切到小奶瓶专属子域名。
2. 后端已部署到华为云 ECS 内网回环并使用宝塔 MySQL 独立库；公网目前使用 `https://api.mewpow.com/xiaonaiping` 过渡路径，后续仍建议切到小奶瓶专属子域名。
3. 未完成 App Store Connect 创建、正式全套截图、隐私标签填写和审核说明提交。
4. 未完成 TestFlight 外部测试。
5. 未完成生产对象存储区域、备份策略和删除 SLA 证明；华为云 OBS 模式已有配置骨架，未做真实云端验证。
6. `Backend/proof/production-readiness.json` 当前 `ready=false`。未通过的必需项以该 JSON 的 `failedRequiredChecks` 为准；当前预检剩余阻断项包含微信 provider、iOS 微信 Release 配置、认证服务商 proof 和 App Store 人工证据；签名/TestFlight、中国大陆备案/合规证据仍是发布流程阻断项，截图候选已归档。
7. 手机号登录和微信登录已有服务端实现路径；短信 provider 在本轮 current proof 中已通过，但短信服务商人工证据仍未归档。微信 provider 仍未通过。iOS 已接入 WechatOpenSDK 授权桥和 Universal Link / AASA 基础配置，但微信开放平台凭证、真实 `wx...` AppID / URL Scheme 和 Universal Link 后台绑定未完成，不能用于 App Store 提交。Release 包已禁用未配置时点击假微信登录，Release 和 bundle gate 也已拒绝假 `wx...` dry-run 值；这只是防止假功能，不等于微信登录完成。
8. App Store 真机归档未通过，必须先在 Xcode 配置 Apple Developer Team 和 App Store Distribution 签名。
9. 中国大陆简体中文元数据和截图需要最终人工校对；香港繁中资源保留给第二批发布。
10. 中国大陆首发仍缺 APP 备案、适用的 ICP / 联网服务判断、App Store Connect 大陆合规信息、专属 API 子域名和生产对象存储证据。
11. Release 包体内容扫描已通过，但微信原生 AppID 和 URL Scheme 仍阻断 `ios-app-bundle.json`。

## 是否允许发布

当前不允许正式发布 App Store。允许进入下一步生产部署和 TestFlight 准备。
