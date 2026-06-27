# CHINA_MAINLAND_APP_STORE_RUNBOOK.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 公司主体：深圳市闪现生活科技有限公司
- 目标地区：中国大陆 App Store 第一批
- 当前结论：资料路径已补齐，但不得提交，直到 `Backend/proof/production-readiness.json` 为 `ready: true`，并补齐签名、TestFlight、备案和 App Store Connect 证据。

## 提交前硬门禁

以下任一项未完成时，不允许提交审核：

1. `Backend/proof/production-readiness.json` 的 `ready` 必须为 `true`。
2. App Store Connect 公司主体必须是深圳市闪现生活科技有限公司。
3. 中国大陆 APP 备案、适用 ICP / 联网服务判断必须留存证据。
4. Release 包必须完成 App Store Distribution 签名归档。
5. TestFlight 至少完成一轮外部或内部审核流程验证。
6. 隐私标签必须和真实 App 行为、隐私政策、SDK 清单一致。
7. `App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy` 必须进入 app bundle，并与 App Store 隐私标签一致。
8. OBS、手机号短信、微信登录必须是真实生产配置，不允许使用 debug 通道。

## App Store Connect 设置

| 项目 | 填写方式 |
|---|---|
| App 名称 | 小奶瓶 |
| Bundle ID | `com.mewpow.xiaonaiping` |
| SKU | `xiaonaiping-ios-1`，或 App Store Connect 中尚未使用的公司内部 SKU |
| 类别 | 生活，若改为健康健美需重新复核医疗声明 |
| 价格 | 免费 |
| 可售地区 | Specific Countries or Regions -> China mainland |
| 主语言 | 简体中文 |
| 第二批语言 | 繁体中文香港，`zh-Hant-HK` 已在 App 内准备 |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy`，正式提交前建议切到小奶瓶专属子域名 |
| Support URL | `https://api.mewpow.com/xiaonaiping/support`，正式提交前建议切到小奶瓶专属子域名 |

第一批不要勾选香港、美国或其他地区。香港第二批单独复用 `Docs/08_Release/HONG_KONG_APP_STORE_RUNBOOK.md`。

## 审核说明

提交审核说明应包含：

1. App 用于父母或照护者记录宝宝成长，不面向儿童直接使用。
2. 第一版免费，无 IAP、无广告、无第三方分析 SDK。
3. 疫苗模板只用于记录和提醒，不提供医疗诊断或专业接种建议。
4. 数据默认本地优先；账号与备份由用户主动开启。
5. 登录方式：恢复密钥、手机号验证码、微信授权。
6. 云端备份包含宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。
7. 删除路径：资料 -> 账号与备份 -> 删除云端账号与备份。
8. 如果审核需要测试账号，应使用生产测试手机号和微信测试号，不得使用 debug code。

## 隐私标签填写

以 `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` 为源文件，提交前逐项核对：

| App Store 类别 | 小奶瓶实际行为 |
|---|---|
| Identifiers | 账号 ID、会话 token、微信 openid/unionid hash |
| Contact Info | 手机号验证码登录 |
| User Content | 宝宝档案、备注、记录、照片元数据 |
| Photos or Videos | 用户主动加入 App 的宝宝照片原图 |
| Health and Fitness | 喂养、睡眠、成长、疫苗提醒记录 |
| Diagnostics | Apple 原生崩溃诊断 |

不得勾选 Tracking，不得声明第三方广告或跨 App 追踪。

## 证据归档

提交前把以下证据放入 `Docs/08_Release/AppStoreEvidence/`，文件名不要包含密码、手机号明文、宝宝真实照片或密钥：

具体截图保留字段、脱敏字段和可接受文件类型见 `Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md`。不要用 `.md` 待办文件冒充 `01-...` 到 `09-...` 人工证据；gate 只接受截图、PDF 或 JSON 等真实证据文件。

1. `01-company-account.png`：深圳市闪现生活科技有限公司主体截图。
2. `02-mainland-availability.png`：只选择中国大陆可售地区截图。
3. `03-app-filing.pdf` 或 `03-app-filing.png`：APP 备案 / 适用判断证据。
4. `04-privacy-label.png`：App Store Connect 隐私标签截图。
5. `05-signed-archive.png`：App Store Distribution Archive 成功截图。
6. `06-testflight.png`：TestFlight 构建和测试状态截图。
7. `07-sms-provider.png`：短信签名、模板、验证码发送成功证据，隐藏密钥和手机号中段。
8. `08-wechat-open-platform.png`：微信开放平台移动应用、Bundle ID、URL Scheme / Universal Link 配置证据。
9. `09-obs-policy.png`：OBS bucket、生命周期、加密、删除验证证据，隐藏 AK/SK。
10. `10-final-screenshots/`：最终 App Store 截图，不使用真实宝宝照片。
11. `11-test-account-redacted.json`：审核测试账号 redacted 证据；恢复密钥只保存在本机 `.env.xnp-review-account`。
12. `12-real-device-regression.md`：复制 `12-real-device-regression.template.md` 后填写；只记录 iOS 26.5 TestFlight 或签名真机包回归结论，RD-01 到 RD-24 状态必须全部为“通过”。

## 本地命令

正式提交前从仓库根目录跑（建议先执行统一脚本）：

```bash
Backend/scripts/run_launch_readiness.sh \
  --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
  --base-url https://api.mewpow.com/xiaonaiping \
  --live-check
```

与上面脚本等价的完整命令清单如下（可作为排障时逐条回退）：

```bash
python3 Backend/scripts/collect_deployment_proof.py --env-file /srv/xiaonaiping/private/xiaonaiping-api.env --base-url https://api.mewpow.com/xiaonaiping --service-active --public-internal-blocked --output Backend/proof/huawei-baota-deploy-20260620.json
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
python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness.json
python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json
python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --require-huawei-obs --require-screenshots --require-app-store-evidence --live-check --output Backend/proof/production-readiness.json
python3 Backend/scripts/check_app_store_evidence.py --output Backend/proof/app-store-evidence.json
python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive archive
```

如果上面任一门禁失败，不能提交。`collect_deployment_proof.py` 必须只在服务器或可信机器运行，输出不得包含密码、token、AK/SK。`verify_auth_providers.py` 默认不会发短信；正式短信服务商配置后，需另跑 `--send-test-sms --phone +...` 证明验证码链路。`check_provider_evidence_materials.py` 只证明短信、微信开放平台和 OBS 人工证据材料要求完整，不替代 `07-sms-provider`、`08-wechat-open-platform` 或 `09-obs-policy` 的真实截图/PDF/JSON。Archive 命令必须在配置 Apple Developer Team 和 App Store Distribution 签名后成功；archive 后还要用导出的 `.app` 重新跑 `check_ios_app_bundle.py`。

## 当前阻断项

以 `Backend/proof/production-readiness.json` 为准。当前仍需补齐：

1. 华为云 OBS 生产 bucket、AK/SK、endpoint 和删除验证。
2. 真实短信 webhook 服务商，并用 `Backend/proof/auth-providers.json` 证明配置完成；最终短信发送需显式测试手机号。
3. 微信开放平台 AppID/AppSecret、真实 `wx...` URL Scheme 和 Universal Link 后台绑定；当前 iOS 已接入 WechatOpenSDK，`CFBundleURLTypes` 已接入 `XNP_WECHAT_URL_SCHEME` build setting，Universal Link / AASA 预检已通过，Release 包已禁止未配置时点击假微信登录，但 `Backend/proof/auth-providers.json`、`Backend/proof/ios-release-readiness.json` 和 `Backend/proof/ios-app-bundle.json` 仍会阻断未配置真实微信的提交。
4. 中国大陆 APP 备案和适用联网服务合规证据。
5. App Store Distribution 签名归档和 TestFlight 证据。
6. 真机回归证据。
