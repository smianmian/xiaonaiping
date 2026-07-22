# 小奶瓶 App Store Version 与发布设置表

日期：2026-06-29

状态：用于 App Store Connect 的版本页、价格与可售地区、发布方式和合规问题填写。本文只准备草稿，不能替代真实 App Store Distribution Archive、TestFlight 构建、备案或 App Store Connect 人工证据。

## Version Information

| 字段 | 当前填写 |
|---|---|
| Version | `1.0` |
| Build | 等 TestFlight 构建处理完成后选择对应 build；当前工程 `CURRENT_PROJECT_VERSION=1`，但不能在未上传构建前假填完成 |
| What's New | 第一版：宝宝档案、日常记录、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。 |
| Promotional Text | 用低负担的方式记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片。 |
| Description | 复制 `Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260629.md` 的描述 |
| Keywords | 宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册 |
| Support URL | `https://api.mewpow.com/xiaonaiping/support` |
| Marketing URL | 留空 |

## Pricing and Availability

| 字段 | 当前填写 |
|---|---|
| Price | Free |
| Availability | Specific Countries or Regions -> China mainland |
| First batch | China mainland only |
| Do not select | Hong Kong, United States, all other regions |
| Second batch | Hong Kong，等中国大陆首发证据稳定后按 `HONG_KONG_APP_STORE_RUNBOOK.md` 单独处理 |

中国大陆可售地区截图必须归档为 `Docs/08_Release/AppStoreEvidence/02-mainland-availability.png`。未归档前不得声称可售地区证据完成。

## Version Release

| 字段 | 当前填写 |
|---|---|
| Release option | Manually release this version after App Review approval |
| Phased release | Off |
| Reason | 中国大陆首发依赖备案、App Store 人工证据、iOS 26.5 真机/TestFlight 回归、生产 proof、微信开放平台和短信服务商证据；审核通过不等于可以自动上线 |

## Export Compliance

| 字段 | 当前填写 |
|---|---|
| Uses encryption | Yes，使用 Apple 平台安全、Keychain、HTTPS 和标准系统/网络加密 |
| Custom cryptography | No |
| VPN | No |
| DRM | No |
| End-to-end encrypted messaging | No |
| Re-check trigger | 如新增自定义加密、VPN、DRM、E2EE、加密通信 SDK 或安全 SDK，必须重新复核 |

## Advertising Identifier / Tracking

| 字段 | 当前填写 |
|---|---|
| Uses IDFA | No |
| Tracking | No |
| Third-party advertising | No |
| Third-party analytics SDK | No |
| Evidence | `Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260629.md` 和 `App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy` |

## Content Rights

| 字段 | 当前填写 |
|---|---|
| Contains, shows, or accesses third-party content | No for App Store metadata and screenshots |
| User-added photos | 用户主动加入 App 的私有照片，仅用于账号同步恢复，不用于 App Store 公开截图或公开分享 |
| Screenshot rule | 不使用真实宝宝照片，除非另有明确授权 |

## 提交前重检

1. 只有 `Backend/proof/production-readiness.json` 为 `ready=true` 后才允许提交审核。
2. 只有 `05-signed-archive.png`、`06-testflight.png`、`12-real-device-regression.md` 和 `02-mainland-availability.png` 归档后，才允许把版本提交状态写成完成。
3. 版本 Build 必须来自 App Store Connect / TestFlight 已处理完成构建，不能只用本地 build number 代替。
4. 若 Team ID、Bundle ID、版本号、build 号、可售地区、价格、发布方式、加密、IDFA、隐私标签或截图变化，必须重跑 `check_app_store_connect_materials.py`、`check_app_store_connect_evidence_materials.py`、`check_signed_archive_testflight_materials.py` 和 `check_production_readiness.py`。
