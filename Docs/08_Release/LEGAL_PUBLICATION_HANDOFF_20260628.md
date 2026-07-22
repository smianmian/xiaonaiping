# 小奶瓶法务页面发布交接表

日期：2026-06-28

状态：用于正式发布隐私政策、用户协议和支持页前的字段交接。本文件只记录需要补齐的公开字段和不得造假的边界，不替代正式法务审核。

## 当前公开 URL

| 页面 | 当前过渡 URL | 发布前要求 |
|---|---|---|
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` | App Store Connect、App 内、静态页和备案材料保持一致；优先切到小奶瓶专属子域名 |
| 用户协议 URL | `https://api.mewpow.com/xiaonaiping/terms` | App Store Connect、App 内、静态页和备案材料保持一致 |
| 支持 URL | `https://api.mewpow.com/xiaonaiping/support` | App Store Connect、App 内、静态页和备案材料保持一致 |

## 发布前必须补齐

1. 公司主体：深圳市闪现生活科技有限公司。
2. 隐私联系邮箱：由公司确认后填入公开隐私政策和 App Store Connect。
3. 支持邮箱：由公司确认后填入支持页和用户协议。
4. 正式服务域名：确认是否继续使用 `https://api.mewpow.com/xiaonaiping` 过渡路径，或切换小奶瓶专属子域名。
5. 服务器区域和云资源：华为云中国大陆 ECS、宝塔 MySQL、华为云 OBS，以生产 proof 和对象存储 proof 为准。
6. 第三方/平台服务：短信服务商、微信开放平台、Apple TestFlight / App Store Connect、华为云 OBS。
7. 删除 SLA：账号删除、云端 JSON 同步删除、云端照片原图删除、第一方埋点删除和删除审计保留边界。
8. 备案编号：拿到真实 App 备案 / ICP 编号后再更新隐私政策、用户协议、支持页、App 内展示和 Review Notes。

## 公开 URL 一致性清单

如果隐私政策、用户协议或支持 URL 从 `https://api.mewpow.com/xiaonaiping` 过渡路径切到小奶瓶专属子域名，不要只改一处 URL。必须同步检查并更新：

1. `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260628.md`
2. `Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260628.md`
3. `Docs/08_Release/APP_STORE_METADATA.md`
4. `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json`
5. `Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260628.md`
6. `Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260628.md`
7. `Docs/08_Release/MAINLAND_FILING_MATERIALS.md`
8. `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260628.md`
9. `Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md`
10. `Backend/static/privacy.html`
11. `Backend/static/terms.html`
12. `Backend/static/support.html`

发布当天还要归档 `Docs/08_Release/AppStoreEvidence/RealDevice/RD-19-public-urls.png`，证明 iOS 26.5 TestFlight 或 Xcode 签名真机包内能打开隐私政策、用户协议和支持 URL。该截图/录屏不得展示后台 token、邮箱收件箱、完整手机号或内部 dashboard。

## 不得写入公开页面或仓库

1. 不得写占位邮箱、测试邮箱、个人邮箱或未确认的隐私联系邮箱。
2. 不得写占位备案号、示例备案号或 `0` 组成的备案编号。
3. 不得写完整手机号、完整证件号、恢复密钥、session token、AccessKey、Secret、AppSecret、对象 key 或验证码。
4. 不得声称短信服务商、微信开放平台、OBS、备案、TestFlight 或 App Store Connect 人工证据已完成，除非对应证据已归档到 `Docs/08_Release/AppStoreEvidence/` 并通过 proof gate。
5. 不得把小奶瓶描述为医疗器械、诊断工具、治疗工具、健康建议工具、压力评估工具或自动喂养建议工具。

## 发布当天复跑

```bash
python3 Backend/scripts/check_public_pages.py --output Backend/proof/public-pages.json
python3 Backend/scripts/check_review_notes.py --output Backend/proof/review-notes.json
python3 Backend/scripts/check_legal_drafts.py --output Backend/proof/legal-drafts.json
python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json
python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json
python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --require-huawei-obs --require-screenshots --require-app-store-evidence --live-check --output Backend/proof/production-readiness.json
```
