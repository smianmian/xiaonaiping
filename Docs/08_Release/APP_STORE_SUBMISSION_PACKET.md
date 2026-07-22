# APP_STORE_SUBMISSION_PACKET.md

## Status

- Project: 小奶瓶 / Baby growth record
- Stage: China mainland App Store Connect fillable packet
- Date: 2026-06-30
- Company: 深圳市闪现生活科技有限公司
- Current conclusion: China mainland submission materials are drafted and current screenshot candidates are archived, but not ready until filing/compliance, WeChat login provider, App Store Connect evidence, TestFlight, signed archive, and real-device regression are complete
- Manual evidence capture guide: `Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md`

## Current 2026-06-30 Gate Status

| Gate | Current proof | Status | Blocking detail |
|---|---|---|---|
| App Store Connect materials | `Backend/proof/app-store-connect-materials.json` | passed=true | Metadata, screenshot copy, privacy-label source, review-note boundaries are fillable. |
| App Store manual evidence | `Backend/proof/app-store-evidence-20260630T-current.json`; stable alias `Backend/proof/app-store-evidence.json` | ready=false | Missing company account, mainland availability, filing, privacy label, age rating result, signed archive, TestFlight, Apple Developer role/access evidence, SMS, WeChat, OBS policy, final screenshot upload provenance, and real-device regression evidence. |
| Production readiness | `Backend/proof/production-readiness.json` | ready=false | `productionSecretConfigured`, `productionDataDirConfigured`, `mysqlDatabaseSelected`, `mysqlDatabaseEnvPresent`, `phoneLoginProviderConfigured`, `wechatLoginProviderConfigured`, `privateOperationsDashboardConfigured`, `publicInternalDashboardBlocked`, `xiaonaipingProductionNamespaceConfigured`, `iosReleaseReadinessProofPassed`, `iosAppBundleProofPassed`, `testFlightRegressionPlanProofPassed`, `appStoreAssetsProofPassed`, `authProvidersProofPassed`; rerun after private production env, provider proof, iOS bundle, TestFlight plan, screenshot/assets proof, and production access controls are refreshed. |
| Auth providers | `Backend/proof/auth-providers.json` | passed=false | `smsProviderConfigured` and `wechatProviderConfigured` remain blocked until real production SMS and WeChat Open Platform provider proof are configured. |
| iOS 26.5 app bundle | `Backend/proof/ios-app-bundle.json` | passed=false | `weChatNativeConfigPresent` and `weChatURLTypePresent` remain blocked until real `XNPWeChatAppID` and `wx...` URL scheme are in the Release bundle. |
| XiaoNaiPing submit permission | `Backend/proof/app-store-evidence.json`; `Backend/proof/production-readiness.json`; `Backend/proof/launch-objective-audit.json`; `Backend/proof/testflight-regression-plan.json`; `Backend/proof/provider-evidence-materials.json`; `Backend/proof/mainland-filing-materials.json`; `Backend/proof/signed-archive-testflight-materials.json` | not ready | Submit for Review is blocked until XiaoNaiPing's own App Store evidence, production readiness, launch objective audit, TestFlight regression, provider evidence, mainland filing, signed Archive/TestFlight materials, and iOS 26.5 real-device evidence are ready/passed. Emotion Isle / cross-app status is historical reference only and cannot authorize this app. |

Manual evidence checklist: `Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260630.md`. Manual evidence execution packet: `Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260630.json`. The `manualEvidenceChecklist` and `manualEvidencePacket` checks cover RD-01 through RD-24, iOS 26.5 only, App Store Connect page evidence, final screenshot upload provenance, Live Activity, 小组件, provider evidence, redaction rules, no-submit boundaries, and the boundary that 小奶瓶不生成健康建议、压力提醒、喂养建议或医疗判断.

Copy-paste field packet for App Store Connect draft creation: `Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260630.md`. It mirrors `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260630.md` and keeps the same no-submit boundary: no debug code, no recovery key, no full phone number, no D-U-N-S code value, and no claim that WeChat/TestFlight/real-device evidence is complete before proof files exist.

## Official Apple Checkpoints

Use these Apple pages when filling App Store Connect:

1. App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
2. App privacy details: https://developer.apple.com/help/app-store-connect/manage-app-privacy/overview-of-app-privacy-details/
3. Privacy nutrition label fields: https://developer.apple.com/app-store/app-privacy-details/
4. Screenshot specifications: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications
5. Age rating: https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating
6. Regulated medical device declaration: https://developer.apple.com/help/app-store-connect/manage-app-information/declare-regulated-medical-device-status

## App Information

| Field | Value to enter | Status |
|---|---|---|
| Bundle ID | `com.mewpow.xiaonaiping` | Confirmed in build |
| App name, Chinese | 小奶瓶 | Draft |
| App name, English | Xiao Nai Ping | Draft |
| Subtitle, Chinese | 温柔记录宝宝每一天 | Draft |
| App name, Traditional Chinese | 小奶瓶 | Draft |
| Subtitle, Traditional Chinese | 溫柔記錄寶寶每一天 | Draft |
| Subtitle, English | Gentle baby daily log | Draft |
| In-app language | Follows iOS system language; `zh-Hant-HK` resources included | Needs human copy review |
| Category | Lifestyle | Recommended for China mainland V1 |
| Price | Free | Confirmed for V1 |
| Regions | China mainland first; Hong Kong second | Use Specific Countries or Regions |
| Phone login | SMS verification | Needs production provider |
| WeChat login | WeChat authorization | Needs Open Platform configuration |
| Copyright | `© 2026 深圳市闪现生活科技有限公司` | Confirm App Store Connect account entity before submit |

## URLs

Current public URLs use the verified `/xiaonaiping` path on `api.mewpow.com` until a dedicated XiaoNaiPing API subdomain is configured.

| Field | Current draft | Required before submit |
|---|---|---|
| Privacy Policy URL | `https://api.mewpow.com/xiaonaiping/privacy` | Verified transitional HTTPS URL; prefer dedicated subdomain before final submit |
| Support URL | `https://api.mewpow.com/xiaonaiping/support` | Verified transitional HTTPS URL; prefer dedicated subdomain before final submit |
| Terms URL | `https://api.mewpow.com/xiaonaiping/terms` | Verified transitional HTTPS URL; prefer dedicated subdomain before final submit |

## China Mainland Availability

In App Store Connect, set Pricing and Availability to Specific Countries or Regions and select China mainland for the first submission only after required filing and compliance information is complete. Hong Kong is the second launch batch.

The installed app must work without region gating and must allow switching between China mainland and Hong Kong vaccine reminder templates.

## D-U-N-S / Apple Developer Handoff

D-U-N-S 交付后的动作已整理在 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md`。拿到 D-U-N-S 编码后，先回 Apple Developer 继续深圳市闪现生活科技有限公司的 Organization enrollment；完成后确认组织 Team ID、Bundle ID `com.mewpow.xiaonaiping`、App Groups `group.com.mewpow.xiaonaiping.shared`、Associated Domains、App Store Distribution certificate / provisioning profile、Archive 和 TestFlight。

当前工程已写入 Development Team `L2TYJNDTJK`，但企业注册完成后必须以 Apple Developer 后台显示的组织 Team ID 为准。如果组织 Team ID 不是 `L2TYJNDTJK`，必须同步更新 `App/iOS/project.yml`、`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`、`Backend/static/apple-app-site-association`，并重跑 Universal Links、微信客户端配置、iOS release readiness、Archive/TestFlight 材料和 production readiness gates。

## Signing and Archive Status

Current archive command:

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive archive
xcodebuild -exportArchive -archivePath /tmp/XiaoNaiPing-CN.xcarchive -exportPath /tmp/XiaoNaiPing-CN-AppStoreConnect -exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist -allowProvisioningUpdates
```

Export options template: `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`. It must stay non-secret and use `method=app-store-connect`, `destination=upload`, `teamID=L2TYJNDTJK`, `distributionBundleIdentifier=com.mewpow.xiaonaiping`, `manageAppVersionAndBuildNumber=false`, `testFlightInternalTestingOnly=false`, and `uploadSymbols=true`.

Current result: Development Team `L2TYJNDTJK` is wired in `project.yml` and `XiaoNaiPing.xcodeproj/project.pbxproj`, but no successful App Store Distribution archive evidence is archived yet. Before uploading a build to App Store Connect, complete the D-U-N-S / Apple Developer organization handoff, confirm the Apple account has App Store Distribution signing/provisioning access, inject the real WeChat release values, create the signed archive, export/upload with the App Store Connect ExportOptions template, scan the exported `.app` again with `check_ios_app_bundle.py`, and archive `05-signed-archive.png` plus `06-testflight.png`. Do not commit App Store Connect API keys, Apple ID email addresses, verification codes, provisioning profiles, certificate private keys, or exported `.ipa` files.

## Export Compliance

Current implementation uses Apple platform security, Keychain storage, HTTPS transport, and standard system/network encryption only. It does not implement custom cryptography, VPN, DRM, or end-to-end encrypted messaging.

Use this statement when answering App Store Connect export compliance. Re-check before submission if any new SDK, custom encryption, or encrypted communication feature is added.

## Age Rating And Medical Device Answers

Dedicated answer sheet: `Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md`. Use that sheet when stepping through App Store Connect; the final rating is still governed by the App Store Connect 问卷自动计算结果为准.

Use these answers when filling App Store Connect. Re-check if any feature changes before submission.

| Field | Answer |
|---|---|
| Expected age rating | 4+，以 App Store Connect questionnaire 结果为准 |
| Kids category | Do not select Kids；小奶瓶面向父母和照护者，不面向儿童直接使用 |
| Regulated Medical Device | No |
| Medical device explanation | 小奶瓶 is not a medical device, does not provide diagnosis, does not provide treatment, and does not predict disease |
| Health data source boundary | Records come from user-entered baby care logs only; no HealthKit, sensors, hospital records, stress detection, or medical interpretation |
| Vaccine boundary | Vaccine templates are records and reminders only; no professional vaccine advice |

## Review Notes

小奶瓶用于父母或照护者记录宝宝成长。第一版免费，无 IAP，无广告，无第三方分析 SDK，不提供医疗诊断、治疗建议或专业疫苗建议，不是医疗器械，也不作为医疗器械使用。产品交互分析只使用自有后端第一方白名单事件，不采集宝宝内容、照片、照片 key、手机号、微信标识、定位、广告标识或设备指纹。

数据默认本地优先保存。用户可以在“资料 -> 账号与同步”中使用恢复密钥登录并主动同步。同步会上传宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。App Review 测试使用 App Review Information 中提供的恢复密钥测试账号；手机号和微信测试账号会在真实短信服务与微信开放平台证据完成后补充；服务端保存哈希后的账号标识，不采集邮箱。

账号删除路径为：“资料 -> 账号与同步 -> 删除云端账号与同步”。该操作会删除账号、云端 JSON 同步和云端照片原图，本机资料默认保留，用户可以另行清空本地记录或删除宝宝档案。

疫苗模板仅用于记录和提醒，App 内文案不构成医疗建议。

灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。

审核测试登录请优先使用 App Review Information 中提供的恢复密钥测试账号。手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充；正式提交包不得提供或依赖 debug code。

## Do Not Submit Or Screenshot

Do not include any of the following in App Store Connect metadata, screenshots, Review Notes, or the uploaded app bundle:

1. Real baby photos, real family names, real phone numbers, recovery keys, tokens, account IDs, API keys, or object-storage keys.
2. Debug login codes, local API addresses, `127.0.0.1`, `localhost`, internal dashboard paths, or engineering notes.
3. Claims about medical diagnosis, treatment, professional vaccine advice, infant health conclusions, or doctor replacement.
4. Paid, subscription, membership, ad, community, sharing, or public UGC claims; these are not in V1.
5. Screens or copy for features that still depend on missing external configuration, especially WeChat login before Open Platform proof is archived.
6. Internal Markdown, HTML, env, sync, or README files inside the `.app` bundle.
7. Claims that Live Activity, widgets, vaccine templates, or growth summaries are generated from sensors, HealthKit, hospital records, stress detection, or medical interpretation.

## Privacy Label Fill Source

Use `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` as the source of truth for App Store Connect privacy answers. The final submitted privacy label must match:

1. The iOS app behavior, including phone and WeChat login.
2. `Docs/07_PrivacySecurity/SDK_DATA_INVENTORY.md`.
3. `Docs/07_PrivacySecurity/PRIVACY_REVIEW.md`.
4. The live privacy policy page.
5. `App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy` in the app bundle.

Current Privacy Manifest status: present in the iOS target, tracking disabled, and bidirectionally aligned with the draft privacy label categories for user identifiers, phone number, user content, photos, health records, product interaction usage data, crash data, and performance data. Re-run `Backend/scripts/check_ios_release_readiness.py` after changing privacy labels, SDKs, account flows, photo handling, crash reporting, or analytics.

## Release Bundle Verification

Reusable evidence format is now captured in `Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md`.

Current iOS 26.5 bundle evidence is captured by:

- `Backend/proof/xcodebuild-release-ios265-20260629-stable.log`
- `Backend/proof/xcodebuild-release-ios265-20260629-device-current.log`
- `Backend/proof/ios-app-bundle.json`
- reusable current aliases `Backend/proof/ios-265-build.json` and `Backend/proof/ios-app-bundle.json` when regenerated by the launch scripts

1. `Backend/proof/ios-265-build.json` proves the Release Simulator artifact was built with `iphonesimulator26.5`.
2. `Backend/proof/ios-265-build.json` proves the Release iPhoneOS artifact was built with `iphoneos26.5`.
3. Bundle ID remains `com.mewpow.xiaonaiping`.
4. Release API remains `XNPAPIBaseURL=https://api.mewpow.com/xiaonaiping`.
5. `PrivacyInfo.xcprivacy` is bundled, declares tracking disabled, has no tracking domains, and its collected data types align with the App Store privacy label.
6. `Backend/proof/ios-app-bundle.json` still blocks submission on `weChatNativeConfigPresent` and `weChatURLTypePresent`, because real WeChat AppID and non-placeholder `wx...` URL Scheme are not configured.
7. Do not replace this section with ad-hoc `/tmp/...` package paths; use the current proof files above.

## Screenshot Status

Current candidate screenshots:

| File | Size | Purpose |
|---|---:|---|
| `Docs/08_Release/AppStoreEvidence/10-final-screenshots/01-home-iphone16pro.png` | 1320 x 2868 | Today/home summary proof |
| `Docs/08_Release/AppStoreEvidence/10-final-screenshots/02-record-iphone16pro.png` | 1320 x 2868 | Quick record proof |
| `Docs/08_Release/AppStoreEvidence/10-final-screenshots/03-growth-iphone16pro.png` | 1320 x 2868 | Growth chart proof |
| `Docs/08_Release/AppStoreEvidence/10-final-screenshots/04-profile-iphone16pro.png` | 1320 x 2868 | Settings/profile proof |
| `Docs/08_Release/AppStoreEvidence/10-final-screenshots/05-profile-sync-iphone16pro.png` | 1320 x 2868 | Account sync, recovery-key review path, and cloud deletion proof |

Final App Store screenshots still need:

1. TestFlight or signed-device final screenshots.
2. No real baby photos unless separately authorized.
3. Copy review for medical and privacy claims.
4. Simplified Chinese metadata and in-app copy review; Traditional Chinese (Hong Kong) remains for the second batch.
5. App Store Connect upload evidence archived in `Docs/06_Release/PROOF_PACK.md`.

本地模拟器和候选截图不替代 TestFlight / 签名真机回归；最终证据必须来自 iOS 26.5 TestFlight 或签名真机包。

## Review Test Account

Current recovery-key review account is prepared and verified. Redacted proof is archived at `Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json`. The recovery key is stored only in local ignored file `.env.xnp-review-account`; do not commit or paste it into public docs, App Store Connect metadata, Review Notes, or screenshots. Use `Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md` when filling App Review Information.

## Pre-Submit Commands

Run these after the Huawei Cloud deployment and production URLs are ready:

```bash
Backend/scripts/run_launch_readiness.sh \
  --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
  --base-url https://api.mewpow.com/xiaonaiping \
  --app-path /path/to/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260629-stable.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260629-device-current.log \
  --live-check

python3 Backend/scripts/verify_remote_api.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/remote-api.json
python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend.json
python3 Backend/scripts/verify_auth_providers.py --live-check --output Backend/proof/auth-providers.json
python3 Backend/scripts/check_diagnostics_redaction.py --output Backend/proof/diagnostics-redaction.json
python3 Backend/scripts/check_public_pages.py --output Backend/proof/public-pages.json
python3 Backend/scripts/check_review_notes.py --output Backend/proof/review-notes.json
python3 Backend/scripts/check_legal_drafts.py --output Backend/proof/legal-drafts.json
python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json
python3 Backend/scripts/check_app_store_assets.py --output Backend/proof/app-store-assets.json
python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json
python3 Backend/scripts/check_app_store_connect_evidence_materials.py --output Backend/proof/app-store-connect-evidence-materials.json
python3 Backend/scripts/check_ios_265_build_proof.py --output Backend/proof/ios-265-build.json
python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness.json
python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json
python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app --output Backend/proof/testflight-precheck.json
python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json
python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration.json
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json
python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json
python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json
python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json
python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --require-huawei-obs --require-screenshots --require-app-store-evidence --live-check --output Backend/proof/production-readiness.json
python3 Backend/scripts/check_launch_objective_audit.py --output Backend/proof/launch-objective-audit.json
python3 Backend/scripts/check_launch_blocker_action_packet.py --output Backend/proof/launch-blocker-action-packet.json
```

Do not submit while `production-readiness.json` has `"ready": false`.
Do not submit while `auth-providers.json` has `"passed": false`; this gate checks production SMS webhook configuration, WeChat Open Platform provider configuration, and rejection of `debug_wechat_*` on the public API. The final SMS carrier test must be run explicitly with `--send-test-sms --phone-env XNP_SMS_TEST_PHONE` after the provider is configured.
Do not submit while `diagnostics-redaction.json` has `"passed": false`; this gate checks no third-party crash/analytics SDK markers, no Swift client logging calls, diagnostics in Privacy Manifest, and redacted backend photo-object request logs.
Do not submit while `public-pages.json` has `"passed": false`; this gate checks public privacy, terms, and support pages match China mainland first launch, Hong Kong second batch, the company entity, recovery-key-first account copy, and deferred phone/WeChat login copy.
Do not submit while `review-notes.json` has `"passed": false`; this gate checks the App Store Review Notes cover free/no IAP/no ads/no analytics, no medical advice, no medical-device use, account methods, private sync, original photos, deletion path, vaccine boundary, and no debug code dependency.
Do not submit while `legal-drafts.json` has `"passed": false`; this gate checks privacy and terms drafts are current, China mainland first, Hong Kong second, company-specific, and not recovery-key-only.
Do not submit while `universal-links.json` has `"passed": false`; this gate checks AASA hosting, iOS Associated Domains entitlement, Release WeChat Universal Link, and callback path coverage.
Do not submit while `app-store-assets.json` has `"passed": false`; this gate checks the 1024 x 1024 app icon, alpha channel, and final screenshot count and sizes.
Do not submit while `app-store-connect-materials.json` has `"passed": false`; this gate checks App Store Connect name, subtitle, category, age rating, URLs, keywords, privacy-label source, screenshot copy, and review-note boundaries.
Do not submit while `app-store-connect-evidence-materials.json` has `"passed": false`; this gate checks company account, mainland availability, and App Privacy evidence filenames, retained fields, redaction boundaries, privacy label JSON alignment, and the rule that material docs must not claim these evidence files are complete before real files exist.
Do not submit while `mainland-filing-materials.json` has `"passed": false`; this gate checks the China mainland App filing / ICP material checklist, AppStoreEvidence file naming, redaction guidance, and the rule that filing-number UI/page/review-note changes wait for a real archived filing number.
Do not submit while `signed-archive-testflight-materials.json` has `"passed": false`; this gate checks archive/TestFlight commands, evidence filenames, redaction guidance, iOS 26.5 bundle scan boundaries, and the rule that local simulator proof does not replace signed archive or TestFlight evidence.
Do not submit while `provider-evidence-materials.json` has `"passed": false`; this gate checks SMS provider, WeChat Open Platform, and Huawei OBS evidence filenames, required visible fields, redaction boundaries, provider/storage validation commands, and the rule that material docs must not claim `07-sms-provider`, `08-wechat-open-platform`, or `09-obs-policy` evidence is complete before real files exist.
Do not submit while `ios-265-build.json` has `"passed": false`; this gate checks the Release Simulator and Release iPhoneOS artifacts were built with iOS 26.5 and include the expected Bundle ID, Release API URL, non-tracking Privacy Manifest data types, Live Activities support, and Widget extension.
Do not submit while `testflight-regression-plan.json` has `"passed": false`; this gate checks the review test account proof, RD-01 to RD-24 coverage, real-provider auth boundaries, iOS 26.5 smoke proof reference, screenshot/recording evidence path, and explicit separation between the regression plan and real TestFlight/signed-device evidence. A passing plan proof does not replace `app-store-evidence.json` real-device evidence.
Do not submit while `wechat-client-configuration.json` has `"passed": false`; this gate checks the WeChat client handoff document, iOS 26.5 validation commands, Info.plist slots, Release build settings, Associated Domains, and the rule that AppSecret stays server-side.
Do not submit while `ios-release-readiness.json` has `"passed": false`; this gate currently blocks on missing real WeChat AppID and real `wx...` Release URL scheme. WechatOpenSDK is wired into the iOS target, `CFBundleURLTypes` is already wired to `XNP_WECHAT_URL_SCHEME`, and Universal Links / AASA have their own passing proof.
Do not submit while `ios-app-bundle.json` has `"passed": false`; this gate checks the built `.app`, including Release API URL, Privacy Manifest, Traditional Chinese Hong Kong resources, absence of debug WeChat code, absence of internal docs/local/debug/API-key markers, and WeChat native URL configuration.
Do not submit while `launch-objective-audit.json` has `"ready": false`; this gate maps the actual launch objective to proof files.
Do not submit while `launch-blocker-action-packet.json` has `"passed": false`; this gate checks the current red launch objective items are mapped to concrete external evidence filenames, iOS 26.5-only testing, WeChat Open Platform actions, and rerun commands.
