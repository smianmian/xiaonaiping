from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_signed_archive_testflight_materials.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_submission_packet() -> str:
    return """
# APP_STORE_SUBMISSION_PACKET.md

## Signing and Archive Status

Current archive command:

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive archive
xcodebuild -exportArchive -archivePath /tmp/XiaoNaiPing-CN.xcarchive -exportPath /tmp/XiaoNaiPing-CN-AppStoreConnect -exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist -allowProvisioningUpdates
```

ExportOptions use `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` with method=app-store-connect, destination=upload, teamID=L2TYJNDTJK, distributionBundleIdentifier=com.mewpow.xiaonaiping, manageAppVersionAndBuildNumber=false, testFlightInternalTestingOnly=false, and uploadSymbols=true. Do not commit App Store Connect API key, Apple ID 邮箱, 验证码, provisioning profile, 证书私钥 or exported `.ipa`.

## D-U-N-S / Apple Developer Handoff

D-U-N-S 交付后的动作已整理在 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md`。拿到 D-U-N-S 编码后，先回 Apple Developer 继续深圳市闪现生活科技有限公司的 Organization enrollment；完成后确认组织 Team ID、Bundle ID `com.mewpow.xiaonaiping`、App Groups `group.com.mewpow.xiaonaiping.shared`、Associated Domains、App Store Distribution certificate / provisioning profile、Archive 和 TestFlight。

Current result: Development Team `L2TYJNDTJK` is wired in `project.yml` and `XiaoNaiPing.xcodeproj/project.pbxproj`, but no successful App Store Distribution archive evidence is archived yet. Before uploading a build to App Store Connect, complete the D-U-N-S / Apple Developer handoff, confirm the Apple account, App Store Distribution signing, real WeChat release values, and post-archive bundle scan.

## Screenshot Status

Final screenshots require TestFlight or signed-device final screenshots. No real baby photos. Copy review for medical and privacy claims. 本地模拟器和候选截图不替代 TestFlight / 签名真机回归；最终证据必须来自 iOS 26.5 TestFlight 或签名真机包。

## Pre-Submit Commands

```bash
python3 Backend/scripts/check_signed_archive_testflight_materials.py
python3 Backend/scripts/check_ios_app_bundle.py
python3 Backend/scripts/check_testflight_precheck.py
python3 Backend/scripts/check_testflight_regression_plan.py
python3 Backend/scripts/check_app_store_evidence.py
```
""".lstrip()


def valid_bundle_verification() -> str:
    return """
# IOS_RELEASE_BUNDLE_VERIFICATION.md

Current iOS 26.5 bundle evidence is captured by `Backend/proof/ios-265-build.json` and `Backend/proof/ios-app-bundle.json`.
Release iPhoneOS artifact uses `iphoneos26.5`.

## 仍需补齐

1. App Store Distribution 签名归档。
2. TestFlight 上传后的同一套包体扫描和真机回归证据。
""".lstrip()


def valid_runbook() -> str:
    return """
# CHINA_MAINLAND_APP_STORE_RUNBOOK.md

- 公司主体：深圳市闪现生活科技有限公司

Archive 命令必须在配置 Apple Developer Team 和 App Store Distribution 签名后成功；导出 / 上传使用 `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`，该文件必须保持 `method=app-store-connect`、`destination=upload`、`manageAppVersionAndBuildNumber=false`、`testFlightInternalTestingOnly=false`；不要把 App Store Connect API key、Apple ID 邮箱、验证码、provisioning profile、证书私钥或导出的 `.ipa` 提交到仓库。archive 后还要用导出的 `.app` 重新跑 `check_ios_app_bundle.py`。

拿到 Team ID 后还必须确认当前 Apple ID 的角色权限：Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限都要具备，并归档 `AppleDeveloper/16-account-roles-access.png`。不能只用 Team ID 截图替代权限截图；权限不足时先找 Account Holder 或管理员补权限，再继续证书、Archive、TestFlight 或 Submit for Review。

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive archive
xcodebuild -exportArchive -archivePath /tmp/XiaoNaiPing-CN.xcarchive -exportPath /tmp/XiaoNaiPing-CN-AppStoreConnect -exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist -allowProvisioningUpdates
```

## 证据归档

5. `05-signed-archive.png`：App Store Distribution Archive 成功截图。
6. `06-testflight.png`：TestFlight 构建和测试状态截图。
13. `AppleDeveloper/16-account-roles-access.png`：当前 Apple ID 角色列表、证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限；遮 Apple ID 邮箱、联系人完整电话、付款信息和无关成员。
""".lstrip()


def valid_evidence_readme() -> str:
    return """
# AppStoreEvidence

| 文件名 | 证明什么 |
| --- | --- |
| `05-signed-archive.png` | App Store Distribution Archive 成功 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试 |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归；TestFlight 或签名真机包；不替代 TestFlight / 签名真机回归 |
| `01-company-account.png` | App Store Connect 主体为深圳市闪现生活科技有限公司 |
| `AppleDeveloper/13-organization-team-id.png` | Apple Developer 组织页确认主体、Membership 和 Team ID |
| `AppleDeveloper/14-bundle-id-capabilities.png` | Bundle ID / Identifier 页确认 `com.mewpow.xiaonaiping`、App Groups、Associated Domains |
| `AppleDeveloper/15-distribution-certificate-profile.png` | App Store Distribution 证书 / Profile 可用于 Archive |
| `AppleDeveloper/16-account-roles-access.png` | 账号权限 / Roles and Access 确认当前 Apple ID 有 Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限 |
| `08b-wechat-universal-link-aasa.png` | AASA、Associated Domains、微信开放平台 Universal Link 同轮核对 |
""".lstrip()


def valid_capture_guide() -> str:
    return """
# CAPTURE_GUIDE.md

| 文件 | 必须能证明 | 保留字段 | 必须遮挡 |
|---|---|---|---|
| `05-signed-archive.png` | App Store Distribution archive 成功 | Bundle ID、版本、build、archive success / uploaded status | Apple ID 邮箱 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试 | Build 号、版本、处理状态、测试状态 | 测试员邮箱 |
| `AppleDeveloper/13-organization-team-id.png` | Apple Developer 组织页 | 深圳市闪现生活科技有限公司、Team ID、Membership 状态 | Apple ID 邮箱、联系人电话、付款信息、D-U-N-S 编码完整值 |
| `AppleDeveloper/14-bundle-id-capabilities.png` | Bundle ID / Identifier 页 | Bundle ID、Team、`group.com.mewpow.xiaonaiping.shared`、`applinks:api.mewpow.com` | 无关 App、人员信息 |
| `AppleDeveloper/15-distribution-certificate-profile.png` | App Store Distribution 证书 / Profile | 类型、Bundle ID、Team ID、有效状态 | 证书私钥、下载链接、个人邮箱 |
| `AppleDeveloper/16-account-roles-access.png` | 当前 Apple ID 有证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限 | 当前 Apple ID 所属团队、角色列表、Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限、提交审核权限 | Apple ID 邮箱、联系人完整电话、付款信息、无关成员 |
""".lstrip()


def valid_duns_handoff() -> str:
    return """
# Apple Developer D-U-N-S Handoff

日期：2026-07-04

状态：D-U-N-S 编码交付后的执行清单。本文只准备动作和证据边界，不写入 D-U-N-S 编码、联系人电话、Apple ID 邮箱、付款信息、证书私钥或描述文件私密内容。

## 目标

D-U-N-S 交付后，立刻回到 Apple Developer 继续深圳市闪现生活科技有限公司的 Organization enrollment。当前工程已把 Development Team 写为 `L2TYJNDTJK`。如果 Apple Developer 显示的组织 Team ID 不是 `L2TYJNDTJK`，必须同步更新 `App/iOS/project.yml`、`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`、`Backend/static/apple-app-site-association`，并重新归档 `08b-wechat-universal-link-aasa.png`，然后重跑 `Backend/scripts/check_universal_links.py`、`Backend/scripts/check_wechat_client_configuration.py`、`Backend/scripts/check_ios_release_readiness.py`、`Backend/scripts/check_provider_evidence_materials.py` 和 `Backend/scripts/check_signed_archive_testflight_materials.py`。

## 企业主体一致性锁

D-U-N-S 交付后，Apple Developer Organization enrollment、App Store Connect 公司账号、App Store metadata、备案材料和公开法律页必须统一为深圳市闪现生活科技有限公司。不能用个人账号或其他公司主体完成证书、Archive、TestFlight 或 Submit for Review。

| 核对位置 | 必须一致的主体字段 | 证据或复跑 |
| --- | --- | --- |
| Apple Developer 组织页 | 深圳市闪现生活科技有限公司、Organization / Membership 状态、Team ID | `AppleDeveloper/13-organization-team-id.png`、`check_signed_archive_testflight_materials.py` |
| App Store Connect 公司主体 | 深圳市闪现生活科技有限公司 | `Docs/08_Release/AppStoreEvidence/01-company-account.png`、`check_app_store_connect_materials.py` |
| App Store metadata | `Docs/08_Release/APP_STORE_METADATA.md` 的公司主体、Copyright 和提交阻断说明 | `check_app_store_connect_materials.py` |
| 中国大陆备案材料 | `Docs/08_Release/MAINLAND_FILING_MATERIALS.md` 的公司主体 / 主办单位 | `check_mainland_filing_materials.py` |
| App Store 提交包 | `Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md` 的 Company / Copyright | `check_app_store_submission_packet.py` |
| 公开法律页 | `Backend/static/privacy.html`、`Backend/static/terms.html`、`Backend/static/support.html` 的开发者主体 | `check_legal_drafts.py`、`check_public_pages.py` |

主体不一致时不得继续 Archive / TestFlight / Submit for Review；先修正主体材料、重新归档 `01-company-account.png` 和 `AppleDeveloper/13-organization-team-id.png`，再重跑 `check_signed_archive_testflight_materials.py`、`check_mainland_filing_materials.py`、`check_app_store_connect_materials.py` 和 `check_production_readiness.py`。

## Apple Developer 联系人姓名锁

Apple Developer Organization enrollment、D&B 补充信息和后续 Apple 联系人资料里的联系人姓名必须使用证件姓名：佘鹏辉 / Penghui She。不能使用余鹏辉，不能使用 Penghui Yu；如果 Apple 或 D&B 页面出现旧错名，先更正联系人姓名再继续提交或缴费。

## D-U-N-S 到手后的动作

1. 打开 Apple Developer，继续 Organization enrollment。
2. 进入 Certificates, Identifiers & Profiles。
3. 确认 Bundle ID `com.mewpow.xiaonaiping`。
4. 确认 App Groups 包含 `group.com.mewpow.xiaonaiping.shared`。
5. 确认 Associated Domains 可用。
6. 创建 App Store Distribution certificate / provisioning profile。
7. 确认当前 Apple ID 有 Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限，并归档 `Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png`。
8. 如果 Team ID 漂移，确认 AASA 使用 `新 Team ID.com.mewpow.xiaonaiping`，Associated Domains 包含 `applinks:api.mewpow.com`，微信开放平台 Universal Link 与 `XNPWeChatUniversalLink` 一致，并重新归档 `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png`。
9. 执行 Archive。
10. 使用 `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` 执行 `xcodebuild -exportArchive`，ExportOptions 必须是 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`、`distributionBundleIdentifier=com.mewpow.xiaonaiping`、`manageAppVersionAndBuildNumber=false`、`testFlightInternalTestingOnly=false`、`uploadSymbols=true`。当前工程/模板值仍为 `L2TYJNDTJK`；只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用。
11. 上传 TestFlight。
12. 归档 `Docs/08_Release/AppStoreEvidence/05-signed-archive.png` 和 `Docs/08_Release/AppStoreEvidence/06-testflight.png`。

## Apple Developer / App Store Connect 权限锁

拿到 Team ID 后，先确认当前 Apple ID 的权限，再配证书、Archive、上传 TestFlight 或点 Submit for Review。必须归档 `AppleDeveloper/16-account-roles-access.png`：保留当前 Apple ID 所属团队、角色列表、Certificates, Identifiers & Profiles 访问状态、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限；遮挡 Apple ID 邮箱、联系人完整电话、付款信息和无关成员。不能只用 Team ID 截图替代权限截图。

如果当前账号缺少 App Store Distribution certificate / provisioning profile 创建权限、App 管理权限、构建上传权限、TestFlight 管理权限或提交审核权限，不得继续 Archive / TestFlight / Submit for Review；先让 Account Holder 或管理员补权限，再重跑 `check_signed_archive_testflight_materials.py`、`check_app_store_connect_materials.py` 和 `check_app_store_evidence.py --allow-incomplete`。

## Team ID 漂移同步矩阵

Apple Developer 显示的组织 Team ID 是最终口径。

| 位置 | 必须同步的字段 | 证据 | 复跑 gate |
| --- | --- | --- | --- |
| `App/iOS/project.yml` | `DEVELOPMENT_TEAM` | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png` | `check_ios_release_readiness.py`、`check_ios_app_bundle.py` |
| `App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj` | `DEVELOPMENT_TEAM` | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png` | `check_ios_release_readiness.py`、`check_ios_app_bundle.py` |
| `Backend/static/apple-app-site-association` | `appID` / `appIDs` 使用新 Team ID，例如 `新 Team ID.com.mewpow.xiaonaiping` | `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` | `check_universal_links.py`、`check_wechat_client_configuration.py` |
| `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` | `teamID` | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png` | `check_signed_archive_testflight_materials.py` |
| `Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md` | `XNPWeChatUniversalLink` | `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` | `check_wechat_client_configuration.py`、`check_provider_evidence_materials.py` |
| `Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md` | 当前 Team ID | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png` | `check_app_store_submission_packet.py`、`check_signed_archive_testflight_materials.py` |
| `Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md` | 当前 Team ID | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png` | `check_app_store_submission_packet.py`、`check_production_readiness.py` |

## Team ID 预导出一致性锁

Apple Developer 后台 Team ID 是最终值。执行 `xcodebuild -exportArchive` 前，必须把下面口径逐项核对为同一个 Team ID；只要任一项不一致，不得执行 `xcodebuild -exportArchive`。直到这些 Team ID 口径一致，才允许继续导出和上传。

| 核对项 | 必须一致的字段 | 证据或 proof |
| --- | --- | --- |
| Apple Developer 组织页 | 页面显示的组织 Team ID | `AppleDeveloper/13-organization-team-id.png` |
| XcodeGen 工程源 | `App/iOS/project.yml` 的 `DEVELOPMENT_TEAM` | `Backend/proof/ios-release-readiness.json` |
| Xcode 工程文件 | `App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj` 的 `DEVELOPMENT_TEAM` | `Backend/proof/ios-release-readiness.json` |
| ExportOptions | `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` 的 `teamID` | `AppleDeveloper/15-distribution-certificate-profile.png` |
| AASA | `Backend/static/apple-app-site-association` 的 `appID` / `appIDs` Team 前缀 | `08b-wechat-universal-link-aasa.png`、`Backend/proof/universal-links.json` |
| 微信客户端配置 | Associated Domains、`XNPWeChatUniversalLink` 和 AASA Team ID | `Backend/proof/wechat-client-configuration.json` |
| 导出前包体检查 | Release app bundle 中的 Team / Associated Domains / 微信值 | `Backend/proof/ios-app-bundle.json` |

如果 ExportOptions 仍是 `L2TYJNDTJK` 但 Apple 页面显示新 Team ID，先更新 ExportOptions `teamID`、工程签名、AASA 和微信 Universal Link 证据，再重新生成 Archive / TestFlight。不要用旧 Team ID 的 Archive 或 TestFlight 证据补交。

## Apple Developer 页面证据索引与脱敏复核

这些文件只证明 Apple Developer 组织注册、签名能力、Archive 和 TestFlight 链路，不替代微信开放平台、短信服务商、OBS、备案或 iOS 26.5 真机回归证据。

| 文件名 | 必须保留 | 必须遮挡 | 复跑或复核命令 |
|---|---|---|---|
| `AppleDeveloper/13-organization-team-id.png` | 深圳市闪现生活科技有限公司、Organization / Membership 状态、Team ID | Apple ID 邮箱、联系人完整电话、付款信息、D-U-N-S 编码完整值 | 若 Team ID 不同于 `L2TYJNDTJK`，先同步工程、AASA 和 ExportOptions |
| `AppleDeveloper/14-bundle-id-capabilities.png` | Bundle ID `com.mewpow.xiaonaiping`、当前 Team、App Groups `group.com.mewpow.xiaonaiping.shared`、Associated Domains `applinks:api.mewpow.com` | 无关 App、人员信息、Apple ID 邮箱 | `check_universal_links.py`、`check_wechat_client_configuration.py`、`check_ios_release_readiness.py` |
| `AppleDeveloper/15-distribution-certificate-profile.png` | App Store Distribution certificate / provisioning profile 类型、Bundle ID、Team ID、有效状态 | 证书私钥、provisioning profile 原文件、下载链接、个人邮箱 | `check_signed_archive_testflight_materials.py` |
| `AppleDeveloper/16-account-roles-access.png` | 当前 Apple ID、角色列表、Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限、提交审核权限 | Apple ID 邮箱、联系人完整电话、付款信息、无关成员 | `check_signed_archive_testflight_materials.py`、`check_app_store_connect_materials.py`、`check_app_store_evidence.py --allow-incomplete` |
| `08b-wechat-universal-link-aasa.png` | AASA endpoint、`新 Team ID.com.mewpow.xiaonaiping`、Associated Domains、`XNPWeChatUniversalLink`、微信开放平台 Universal Link | Apple ID 邮箱、完整手机号、AppSecret、验证码、token | `check_provider_evidence_materials.py`、`check_wechat_client_configuration.py` |
| `05-signed-archive.png` | Xcode Organizer / Archive 成功状态、`com.mewpow.xiaonaiping`、version、build、App Store Distribution | Apple ID 邮箱、证书私钥、provisioning profile、导出的 `.ipa` 路径 | `check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json` |
| `06-testflight.png` | App Store Connect / TestFlight build 版本、build、处理完成或可测试状态、选中 build 与 App Store Connect 一致 | 测试员邮箱、Apple ID 邮箱、内部备注 | `check_testflight_precheck.py`、`check_testflight_regression_plan.py` |
| `12-real-device-regression.md` | iOS 26.5、TestFlight 或 Xcode 签名真机包、RD-01 到 RD-24 全部通过、证据文件路径 | 恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 | `check_testflight_regression_plan.py`、`check_app_store_evidence.py --allow-incomplete` |

## D-U-N-S 交付当天执行记录模板

复制下面清单到当天的私有执行记录或工单中填写；不要把 D-U-N-S 编码完整值、Apple ID 邮箱、联系人完整电话、付款信息、证书私钥、provisioning profile 或 AppSecret 写进仓库。

- [ ] Apple Developer Organization enrollment 已继续提交。
- [ ] Team ID 已从 Apple Developer 后台确认。
- [ ] 当前 Apple ID 已确认具备 Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限，并已归档 `AppleDeveloper/16-account-roles-access.png`。
- [ ] 若 Team ID 不是 `L2TYJNDTJK`，已同步 `App/iOS/project.yml`、`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj` 和 `Backend/static/apple-app-site-association`。
- [ ] 若 Team ID 不是 `L2TYJNDTJK`，AASA 已使用 `新 Team ID.com.mewpow.xiaonaiping`，Associated Domains 仍包含 `applinks:api.mewpow.com`，微信开放平台 Universal Link 与 `XNPWeChatUniversalLink` 同轮一致。
- [ ] 若 Team ID 漂移，已重新归档 `08b-wechat-universal-link-aasa.png`。
- [ ] Bundle ID `com.mewpow.xiaonaiping` 已归属当前组织 Team。
- [ ] App Store Distribution certificate / provisioning profile 可用于 Archive。
- [ ] 已注入真实微信 Release 值，不使用 placeholder `wx...`。
- [ ] `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist` 已按当前 Team ID 复核；若 Team ID 漂移，已同步 `teamID`。
- [ ] ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`、`distributionBundleIdentifier=com.mewpow.xiaonaiping`、`manageAppVersionAndBuildNumber=false`、`testFlightInternalTestingOnly=false`、`uploadSymbols=true`；当前工程/模板值仍为 `L2TYJNDTJK`，只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用。
- [ ] `AppleDeveloper/13-organization-team-id.png`、`AppleDeveloper/14-bundle-id-capabilities.png`、`AppleDeveloper/15-distribution-certificate-profile.png`、`AppleDeveloper/16-account-roles-access.png`、`05-signed-archive.png`、`06-testflight.png` 和 `12-real-device-regression.md` 已按页面证据索引归档并脱敏。
- [ ] Archive / TestFlight 后已重跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_testflight_regression_plan.py`、`check_app_store_evidence.py` 和 `check_production_readiness.py`。

| 证据 | 文件 |
| --- | --- |
| Apple Developer 组织页 / Team ID | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png` |
| Bundle ID / Identifier capabilities | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png` |
| App Store Distribution 证书 / Profile | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png` |
| 账号权限 / Roles and Access | `Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png` |
| 微信 Universal Link / AASA 同轮核对 | `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png` |
| iOS 26.5 真机回归 | `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md` |

## Archive / TestFlight 当天执行记录模板

复制下面清单到当天的私有执行记录或工单中填写；这里只记录执行结论和证据路径，不记录 Apple ID 邮箱、测试员邮箱、D-U-N-S 编码完整值、证书私钥、provisioning profile、AppSecret、恢复密钥或验证码。

- [ ] Xcode 已登录 Apple Developer 账号并选择组织 Team。
- [ ] 当前 Apple ID 已确认具备证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限。
- [ ] Team ID 漂移检查已完成；若不是 `L2TYJNDTJK`，已同步 project.yml、project.pbxproj、AASA `appID` / `appIDs`。
- [ ] 若 Team ID 漂移，已重新归档 `08b-wechat-universal-link-aasa.png`。
- [ ] 真实 `XNP_WECHAT_APP_ID`、`XNP_WECHAT_URL_SCHEME`、`XNP_WECHAT_UNIVERSAL_LINK` 已注入 Release 配置。
- [ ] `prepare_wechat_release_env.py` 已生成 `/tmp/xnp-wechat-release.env`，且未写入 `XNP_WECHAT_APP_SECRET`。
- [ ] Archive 命令使用 `-archivePath /tmp/XiaoNaiPing-CN.xcarchive archive`。
- [ ] 导出 / 上传命令使用 `xcodebuild -exportArchive` 和 `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`。
- [ ] ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`、`distributionBundleIdentifier=com.mewpow.xiaonaiping`；当前工程/模板值仍为 `L2TYJNDTJK`，只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用。
- [ ] `testFlightInternalTestingOnly=false`，本轮构建不限制为仅内部 TestFlight。
- [ ] 导出的 `.app` 或 `.ipa` 仅保存在本机私有路径或临时路径，不提交到仓库。
- [ ] TestFlight build 号和版本号已和 App Store Connect 选中的构建、`12-real-device-regression.md` 环境信息一致。
- [ ] `05-signed-archive.png` 能证明 App Store Distribution Archive 成功。
- [ ] `06-testflight.png` 能证明 TestFlight 构建已处理完成并可测试。

```bash
. /tmp/xnp-wechat-release.env && xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive XNP_WECHAT_APP_ID="$XNP_WECHAT_APP_ID" XNP_WECHAT_URL_SCHEME="$XNP_WECHAT_URL_SCHEME" XNP_WECHAT_UNIVERSAL_LINK="$XNP_WECHAT_UNIVERSAL_LINK" archive
xcodebuild -exportArchive -archivePath /tmp/XiaoNaiPing-CN.xcarchive -exportPath /tmp/XiaoNaiPing-CN-AppStoreConnect -exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist -allowProvisioningUpdates
. /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json
```

不要把 App Store Connect API key、Apple ID 邮箱、验证码、provisioning profile、证书私钥或导出的 `.ipa` 提交到仓库。
""".lstrip()


def valid_project_yml() -> str:
    return """
targets:
  XiaoNaiPing:
    settings:
      base:
        CODE_SIGN_STYLE: Automatic
        DEVELOPMENT_TEAM: L2TYJNDTJK
      configs:
        Release:
          CODE_SIGN_ENTITLEMENTS: XiaoNaiPing/XiaoNaiPing.entitlements
""".lstrip()


def valid_pbxproj() -> str:
    return """
{
  buildSettings = {
    CODE_SIGN_ENTITLEMENTS = XiaoNaiPing/XiaoNaiPing.entitlements;
    CODE_SIGN_STYLE = Automatic;
    DEVELOPMENT_TEAM = L2TYJNDTJK;
  };
}
""".lstrip()


def valid_export_options() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>destination</key>
\t<string>upload</string>
\t<key>distributionBundleIdentifier</key>
\t<string>com.mewpow.xiaonaiping</string>
\t<key>generateAppStoreInformation</key>
\t<false/>
\t<key>manageAppVersionAndBuildNumber</key>
\t<false/>
\t<key>method</key>
\t<string>app-store-connect</string>
\t<key>signingStyle</key>
\t<string>automatic</string>
\t<key>stripSwiftSymbols</key>
\t<true/>
\t<key>teamID</key>
\t<string>L2TYJNDTJK</string>
\t<key>testFlightInternalTestingOnly</key>
\t<false/>
\t<key>uploadSymbols</key>
\t<true/>
</dict>
</plist>
"""


def valid_team_signing_template() -> str:
    target_files = {
        "organizationTeamId": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
        "bundleIdCapabilities": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
        "distributionCertificateProfile": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png",
        "accountRolesAccess": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
        "wechatAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
        "signedArchive": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
        "testFlight": "Docs/08_Release/AppStoreEvidence/06-testflight.png",
        "realDeviceRegression": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
    }
    return json.dumps(
        {
            "artifactType": "apple-developer-team-signing-evidence-template",
            "status": "template-only-not-evidence",
            "project": "XiaoNaiPing",
            "company": "深圳市闪现生活科技有限公司",
            "targetEvidenceFiles": target_files,
            "evidenceFileChecks": [
                {
                    "artifactId": artifact_id,
                    "target": target,
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsTemplateCapture": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "teamIdOrBuildMatchesTemplate": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                }
                for artifact_id, target in target_files.items()
            ],
            "doNotRenameThisTemplateTo": [
                "13-organization-team-id.json",
                "14-bundle-id-capabilities.json",
                "15-distribution-certificate-profile.json",
                "16-account-roles-access.json",
                "05-signed-archive.json",
                "06-testflight.json",
            ],
            "teamConsistencyChecks": {
                "appleDeveloperTeamId": "Team ID displayed on Apple Developer Organization page",
                "projectYmlDevelopmentTeam": "App/iOS/project.yml DEVELOPMENT_TEAM",
                "pbxprojDevelopmentTeam": "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj DEVELOPMENT_TEAM",
                "exportOptionsTeamId": "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist teamID",
                "aasaTeamPrefix": "Backend/static/apple-app-site-association appID/appIDs Team prefix",
                "associatedDomains": "applinks:api.mewpow.com",
                "wechatUniversalLink": "https://api.mewpow.com/xiaonaiping/wechat/",
            },
            "bundleAndCapabilityChecks": [
                "com.mewpow.xiaonaiping is under the current organization Team",
                "com.mewpow.xiaonaiping.widgets is under the current organization Team",
                "group.com.mewpow.xiaonaiping.shared is enabled for app and widget",
                "Associated Domains includes applinks:api.mewpow.com",
                "XiaoNaiPing does not enable HealthKit",
            ],
            "archiveAndTestFlightChecks": [
                "App Store Distribution certificate is valid",
                "Provisioning profile is App Store distribution, not development/ad-hoc",
                "Archive succeeds for com.mewpow.xiaonaiping",
                "ExportOptions method is app-store-connect",
                "ExportOptions destination is upload",
                "TestFlight build is processed and testable",
                "Version/build matches App Store Connect selection and 12-real-device-regression.md",
            ],
            "redactionChecklist": [
                "Hide Apple ID email",
                "Hide complete phone numbers",
                "Hide payment and tax details",
                "Hide complete D-U-N-S number",
                "Hide certificate private keys and provisioning profile files",
                "Hide App Store Connect API keys",
                "Hide XNP_WECHAT_APP_SECRET, SMS secrets, OBS AK/SK, verification codes, bearer tokens, recovery keys, and complete phone numbers",
            ],
            "postCaptureChecks": [
                "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials-20260704T-current.json",
                ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle-20260704T-current-ios265.json",
                "python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app --output Backend/proof/testflight-precheck-20260704T-current-ios265.json",
                "python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan-20260704T-current.json --allow-incomplete",
                "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials-20260704T-current.json",
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-07-04 --output Backend/proof/app-store-evidence-20260704T-current.json",
                "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260704T-current.json",
            ],
            "completionRule": "This template is only a capture worksheet. The Apple Developer, signing, Archive, TestFlight, and real-device gates remain incomplete until the real target evidence files exist and same-round proof checks pass.",
        },
        ensure_ascii=False,
        indent=2,
    )


def valid_duns_post_delivery_actions() -> str:
    target_files = {
        "dunsDelivery": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png or .pdf",
        "organizationEnrollment": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/17-apple-org-enrollment-continued.png or .pdf",
        "organizationTeamId": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
        "bundleIdCapabilities": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
        "distributionCertificateProfile": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png",
        "accountRolesAccess": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
        "wechatAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
        "signedArchive": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
        "testFlight": "Docs/08_Release/AppStoreEvidence/06-testflight.png",
        "realDeviceRegression": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
    }
    archival_rules = {
        "dunsDelivery": {
            "upstreamAction": "D-U-N-S delivered for 深圳市闪现生活科技有限公司",
            "mustArchiveBefore": "continue-organization-enrollment",
            "rerunGate": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
            "doesNotReplace": [
                "Apple Developer Organization enrollment approval",
                "Team ID confirmation",
                "Archive",
                "TestFlight",
            ],
        },
        "organizationEnrollment": {
            "upstreamAction": "Continue Apple Developer Organization enrollment after D-U-N-S delivery",
            "mustArchiveBefore": "confirm-team-id",
            "rerunGate": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
            "doesNotReplace": [
                "Team ID confirmation",
                "account permissions",
                "certificate/profile readiness",
                "Archive",
            ],
        },
        "organizationTeamId": {
            "upstreamAction": "Confirm Apple Developer organization Team ID",
            "mustArchiveBefore": "team-id-drift-sync",
            "rerunGate": ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
            "doesNotReplace": [
                "account permissions",
                "capabilities",
                "distribution signing",
                "WeChat AASA sync",
            ],
        },
        "bundleIdCapabilities": {
            "upstreamAction": "Verify Bundle ID, App Group, and Associated Domains under confirmed Team ID",
            "mustArchiveBefore": "verify-distribution-certificate-profile",
            "rerunGate": "python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json",
            "doesNotReplace": [
                "distribution certificate/profile",
                "Archive",
                "TestFlight",
                "real-device regression",
            ],
        },
        "distributionCertificateProfile": {
            "upstreamAction": (
                "Create or select App Store Distribution certificate and provisioning profiles for "
                "com.mewpow.xiaonaiping and com.mewpow.xiaonaiping.widgets"
            ),
            "mustArchiveBefore": "archive-release-build",
            "rerunGate": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
            "doesNotReplace": [
                "Archive success",
                "TestFlight processing",
                "iOS 26.5 regression",
                "App Store evidence",
            ],
        },
        "accountRolesAccess": {
            "upstreamAction": "Confirm Apple ID roles and permissions",
            "mustArchiveBefore": "create-certificates-or-upload-build",
            "rerunGate": "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
            "doesNotReplace": [
                "Team ID confirmation",
                "certificate/profile readiness",
                "Archive",
                "Submit for Review permission proof",
            ],
        },
        "wechatAasa": {
            "upstreamAction": "Recapture AASA and WeChat Universal Link after Team ID confirmation",
            "mustArchiveBefore": "upload-testflight-or-run-rd14",
            "rerunGate": "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration.json",
            "doesNotReplace": [
                "WeChat Open Platform credentials",
                "Release bundle scan",
                "RD-14 real WeChat login",
                "provider evidence materials",
            ],
        },
        "signedArchive": {
            "upstreamAction": "Archive Release build with App Store Distribution signing",
            "mustArchiveBefore": "export-upload-testflight",
            "rerunGate": "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
            "doesNotReplace": [
                "TestFlight processed build",
                "final screenshots",
                "iOS 26.5 real-device regression",
                "Submit for Review",
            ],
        },
        "testFlight": {
            "upstreamAction": "Wait for App Store Connect TestFlight build processed and testable state",
            "mustArchiveBefore": "run-ios265-real-device-regression",
            "rerunGate": "python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app --output Backend/proof/testflight-precheck.json",
            "doesNotReplace": [
                "real-device regression",
                "final screenshot upload provenance",
                "App Store evidence ready",
                "production readiness",
            ],
        },
        "realDeviceRegression": {
            "upstreamAction": "Complete RD-01 to RD-24 on iOS 26.5 TestFlight or signed real-device build",
            "mustArchiveBefore": "final-submit-gates",
            "rerunGate": "python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json",
            "doesNotReplace": [
                "production readiness",
                "App Store evidence ready",
                "launch objective audit ready",
                "Submit for Review",
            ],
        },
    }
    return json.dumps(
        {
            "artifactType": "apple-developer-duns-post-delivery-actions",
            "status": "action-plan-not-evidence",
            "date": "2026-07-04",
            "company": "深圳市闪现生活科技有限公司",
            "canSubmitFromThisPacket": False,
            "sourceFiles": {
                "handoff": "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                "externalStatusPollTemplate": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json",
                "dunsPostDeliveryExecutionTemplate": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/DUNS-POST-DELIVERY-EXECUTION-RESULT.template.json",
                "orgSigningResultTemplate": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json",
                "teamSigningTemplate": "Docs/08_Release/AppStoreEvidence/_templates/apple-developer-team-signing-evidence.template.json",
                "exportOptions": "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
                "appStoreSubmissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
                "testflightRegressionPlan": "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
            },
            "targetEvidenceFiles": target_files,
            "evidenceFileChecks": [
                {
                    "artifactId": artifact_id,
                    "target": target,
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsDunsPostDelivery": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "teamIdOrBuildMatchesActionPacket": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                }
                for artifact_id, target in target_files.items()
            ],
            "evidenceArchivalMatrix": [
                {
                    "artifactId": artifact_id,
                    "upstreamAction": archival_rules[artifact_id]["upstreamAction"],
                    "target": target,
                    "mustArchiveBefore": archival_rules[artifact_id]["mustArchiveBefore"],
                    "rerunGate": archival_rules[artifact_id]["rerunGate"],
                    "doesNotReplace": archival_rules[artifact_id]["doesNotReplace"],
                    "initialStatus": "pending",
                }
                for artifact_id, target in target_files.items()
            ],
            "accountPermissionMatrix": [
                {
                    "id": "certificates-identifiers-profiles-access",
                    "requiredPermission": "Certificates, Identifiers & Profiles access",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
                    "mustShow": [
                        "current Apple ID belongs to the confirmed organization Team",
                        "Certificates, Identifiers & Profiles access is visible",
                        "App ID, App Group, Associated Domains, certificate, and profile work is allowed",
                    ],
                    "blocksActions": [
                        "verify-bundle-capabilities",
                        "verify-distribution-certificate-profile",
                        "archive-release-build",
                    ],
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                    ],
                    "stopCondition": "account-permissions-missing",
                    "redaction": ["hide Apple ID email", "hide complete phone numbers", "hide unrelated members"],
                    "initialStatus": "pending",
                },
                {
                    "id": "app-management-access",
                    "requiredPermission": "App management access for com.mewpow.xiaonaiping",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
                    "mustShow": [
                        "current Apple ID can manage the 小奶瓶 App Store Connect app record",
                        "metadata, pricing, App Privacy, age rating, and build selection are editable",
                        "App Store Connect page work stays under the confirmed organization Team",
                    ],
                    "blocksActions": [
                        "App Store Connect field backfill",
                        "build selection",
                        "submit-review preflight",
                    ],
                    "rerunGates": [
                        "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
                        "python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
                    ],
                    "stopCondition": "account-permissions-missing",
                    "redaction": ["hide Apple ID email", "hide complete phone numbers", "hide payment and tax details"],
                    "initialStatus": "pending",
                },
                {
                    "id": "build-upload-access",
                    "requiredPermission": "Build upload permission",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
                    "mustShow": [
                        "current Apple ID can upload builds for the confirmed Team",
                        "xcodebuild exportArchive upload is allowed",
                        "upload does not require storing App Store Connect API keys in the repository",
                    ],
                    "blocksActions": [
                        "export-upload-testflight",
                        "wait-testflight-processing",
                    ],
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                        "python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app --output Backend/proof/testflight-precheck.json",
                    ],
                    "stopCondition": "account-permissions-missing",
                    "redaction": ["hide Apple ID email", "hide App Store Connect API keys", "hide exported ipa path if private"],
                    "initialStatus": "pending",
                },
                {
                    "id": "testflight-management-access",
                    "requiredPermission": "TestFlight management permission",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
                    "mustShow": [
                        "current Apple ID can view and manage TestFlight builds",
                        "processed or testable state can be captured in 06-testflight.png",
                        "same build can be selected for iOS 26.5 real-device regression",
                    ],
                    "blocksActions": [
                        "wait-testflight-processing",
                        "run-ios265-real-device-regression",
                        "archive-app-store-evidence",
                    ],
                    "rerunGates": [
                        "python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json",
                        "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json",
                    ],
                    "stopCondition": "account-permissions-missing",
                    "redaction": ["hide Apple ID email", "hide tester emails", "hide internal notes"],
                    "initialStatus": "pending",
                },
                {
                    "id": "submit-review-access",
                    "requiredPermission": "Submit for Review permission",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
                    "mustShow": [
                        "current Apple ID can reach Submit for Review preflight",
                        "submit action remains blocked until app-store-evidence, production-readiness, and launch-objective-audit are ready",
                        "ASC-08 preflight capture is separate from final submit permission",
                    ],
                    "blocksActions": [
                        "submit-review preflight",
                        "Submit for Review",
                    ],
                    "rerunGates": [
                        "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
                        "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json",
                        "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
                    ],
                    "stopCondition": "account-permissions-missing",
                    "redaction": ["hide Apple ID email", "hide complete phone numbers", "hide payment and tax details"],
                    "initialStatus": "pending",
                },
                {
                    "id": "account-holder-admin-escalation",
                    "requiredPermission": "Account Holder or Admin can grant missing roles",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
                    "mustShow": [
                        "missing permission owner is identified without exposing personal email",
                        "Account Holder or administrator can grant the missing role",
                        "do not proceed with certificates, Archive, TestFlight, or Submit for Review until recaptured",
                    ],
                    "blocksActions": [
                        "verify-distribution-certificate-profile",
                        "archive-release-build",
                        "export-upload-testflight",
                        "Submit for Review",
                    ],
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                        "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
                    ],
                    "stopCondition": "account-permissions-missing",
                    "redaction": ["hide Apple ID email", "hide complete phone numbers", "hide unrelated members"],
                    "initialStatus": "pending",
                },
            ],
            "teamIdDriftSyncMatrix": [
                {
                    "id": "project-yml-main-app",
                    "path": "App/iOS/project.yml",
                    "field": "targets.XiaoNaiPing.settings.base.DEVELOPMENT_TEAM",
                    "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
                    "rerunGates": [
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                        "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
                    ],
                    "stopIfUnsynced": "Do not archive or export while project.yml still points at the old Team ID.",
                },
                {
                    "id": "project-yml-widget",
                    "path": "App/iOS/project.yml",
                    "field": "targets.XiaoNaiPingWidgets.settings.base.DEVELOPMENT_TEAM",
                    "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
                    "rerunGates": [
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                        "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
                    ],
                    "stopIfUnsynced": "Do not use a main-app-only Team ID update; widget App Group entitlement group.com.mewpow.xiaonaiping.shared must remain under the same Team.",
                },
                {
                    "id": "xcodeproj-development-team",
                    "path": "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj",
                    "field": "DEVELOPMENT_TEAM and DevelopmentTeam",
                    "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
                    "rerunGates": [
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                        "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
                    ],
                    "stopIfUnsynced": "Regenerate or update the Xcode project before archive; do not mix project.yml and pbxproj Team IDs.",
                },
                {
                    "id": "export-options-team-id",
                    "path": "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
                    "field": "teamID",
                    "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png",
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                    ],
                    "stopIfUnsynced": "Do not run xcodebuild -exportArchive while ExportOptions teamID still points at the old Team ID.",
                },
                {
                    "id": "aasa-team-prefix",
                    "path": "Backend/static/apple-app-site-association",
                    "field": "appID and appIDs Team prefix",
                    "expectedWhenDrifted": "<confirmed Apple Developer Team ID>.com.mewpow.xiaonaiping",
                    "evidence": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
                    "rerunGates": [
                        "python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json",
                        "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration.json",
                    ],
                    "stopIfUnsynced": "Do not upload TestFlight while Universal Link AASA still uses the old Team prefix.",
                },
                {
                    "id": "wechat-release-universal-link",
                    "path": "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md",
                    "field": "XNPWeChatUniversalLink / Associated Domains / WeChat Open Platform Universal Link",
                    "expectedWhenDrifted": "Same confirmed Team ID, applinks:api.mewpow.com, and https://api.mewpow.com/xiaonaiping/wechat/ in the same evidence round",
                    "evidence": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
                    "rerunGates": [
                        "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration.json",
                        "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
                    ],
                    "stopIfUnsynced": "Keep RD-14 blocked until WeChat Open Platform, AASA, Release bundle, and server proof all point at the same Universal Link.",
                },
                {
                    "id": "submission-runbook-team-id",
                    "path": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md and Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md",
                    "field": "current Team ID, Archive/TestFlight prerequisites, and no-submit boundary",
                    "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
                    "rerunGates": [
                        "python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
                        "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json",
                    ],
                    "stopIfUnsynced": "Do not hand App Store Connect operators a runbook that still references the old Team ID as current.",
                },
            ],
            "capabilitySigningMatrix": [
                {
                    "id": "main-app-bundle-id",
                    "target": "XiaoNaiPing",
                    "bundleId": "com.mewpow.xiaonaiping",
                    "portalObject": "Identifier / App ID",
                    "requiredAppleDeveloperState": "Identifier belongs to <confirmed Apple Developer Team ID>",
                    "projectEvidence": [
                        "App/iOS/project.yml",
                        "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj",
                    ],
                    "appleEvidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
                    "rerunGates": [
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                        "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
                    ],
                    "stopCondition": "team-id-drift-unsynced",
                },
                {
                    "id": "widget-bundle-id",
                    "target": "XiaoNaiPingWidgets",
                    "bundleId": "com.mewpow.xiaonaiping.widgets",
                    "portalObject": "Identifier / App Extension App ID",
                    "requiredAppleDeveloperState": "Extension Identifier belongs to <confirmed Apple Developer Team ID>",
                    "projectEvidence": [
                        "App/iOS/project.yml",
                        "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj",
                    ],
                    "appleEvidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
                    "rerunGates": [
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                        "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
                    ],
                    "stopCondition": "team-id-drift-unsynced",
                },
                {
                    "id": "shared-app-group",
                    "target": "XiaoNaiPing + XiaoNaiPingWidgets",
                    "entitlement": "com.apple.security.application-groups",
                    "requiredValue": "group.com.mewpow.xiaonaiping.shared",
                    "projectEvidence": [
                        "App/iOS/project.yml",
                        "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements",
                        "App/iOS/XiaoNaiPingWidgets/XiaoNaiPingWidgets.entitlements",
                    ],
                    "appleEvidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
                    "rerunGates": [
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                        "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
                    ],
                    "stopCondition": "team-id-drift-unsynced",
                },
                {
                    "id": "main-associated-domain",
                    "target": "XiaoNaiPing",
                    "entitlement": "com.apple.developer.associated-domains",
                    "requiredValue": "applinks:api.mewpow.com",
                    "serverEvidence": "Backend/static/apple-app-site-association",
                    "appleEvidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
                    "providerEvidence": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
                    "rerunGates": [
                        "python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json",
                        "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration.json",
                    ],
                    "stopCondition": "wechat-release-values-missing",
                },
                {
                    "id": "app-store-distribution-signing",
                    "target": "XiaoNaiPing archive/export",
                    "bundleId": "com.mewpow.xiaonaiping",
                    "requiredAppleDeveloperState": "App Store Distribution certificate and App Store provisioning profile match confirmed Team ID and bundle ID",
                    "exportOptions": "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
                    "appleEvidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png",
                    "archiveEvidence": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
                    "testFlightEvidence": "Docs/08_Release/AppStoreEvidence/06-testflight.png",
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                        "python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app --output Backend/proof/testflight-precheck.json",
                        "python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json",
                    ],
                    "stopCondition": "distribution-signing-missing",
                },
            ],
            "postDeliveryMilestoneGateMatrix": [
                {
                    "id": "duns-delivered",
                    "unlocksAction": "continue-organization-enrollment",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png or .pdf"],
                    "exitCriteria": [
                        "D-U-N-S delivered for 深圳市闪现生活科技有限公司",
                        "complete D-U-N-S value is not recorded in repository",
                    ],
                    "blockedByStopConditions": ["duns-not-delivered-or-entity-mismatch"],
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "organization-enrollment-continued",
                    "unlocksAction": "confirm-team-id",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/AppleDeveloper/17-apple-org-enrollment-continued.png or .pdf"],
                    "exitCriteria": [
                        "Apple Developer Organization enrollment continued under 深圳市闪现生活科技有限公司",
                        "Apple ID email, contact phone, payment, and tax details are redacted",
                    ],
                    "blockedByStopConditions": ["duns-not-delivered-or-entity-mismatch"],
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "team-id-confirmed",
                    "unlocksAction": "confirm-account-roles",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png"],
                    "exitCriteria": [
                        "confirmed Apple Developer Team ID is captured",
                        "Team ID drift decision is recorded before signing or export",
                    ],
                    "blockedByStopConditions": ["team-id-drift-unsynced"],
                    "rerunGates": [
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "account-permissions-confirmed",
                    "unlocksAction": "verify-bundle-capabilities",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png"],
                    "exitCriteria": [
                        "Certificates, Identifiers & Profiles access is visible",
                        "App management, build upload, TestFlight management, and Submit for Review permissions are visible",
                    ],
                    "blockedByStopConditions": ["account-permissions-missing"],
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                        "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "bundle-capabilities-confirmed",
                    "unlocksAction": "sync-team-id-if-drifted",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png"],
                    "exitCriteria": [
                        "com.mewpow.xiaonaiping and com.mewpow.xiaonaiping.widgets belong to the confirmed Team ID",
                        "group.com.mewpow.xiaonaiping.shared and applinks:api.mewpow.com are enabled",
                    ],
                    "blockedByStopConditions": ["team-id-drift-unsynced"],
                    "rerunGates": [
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                        "python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "team-id-and-wechat-synced",
                    "unlocksAction": "configure-real-wechat-release-values",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png"],
                    "exitCriteria": [
                        "AASA Team prefix, Associated Domains, and WeChat Universal Link are from the same evidence round",
                        "RD-14 remains blocked until real WeChat Open Platform proof and Release values pass",
                    ],
                    "blockedByStopConditions": ["team-id-drift-unsynced", "wechat-release-values-missing"],
                    "rerunGates": [
                        "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration.json",
                        "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "distribution-signing-ready",
                    "unlocksAction": "archive-release-build",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png"],
                    "exitCriteria": [
                        "App Store Distribution certificate and provisioning profile match confirmed Team ID",
                        "com.mewpow.xiaonaiping profile is App Store distribution, not development or ad-hoc",
                        "com.mewpow.xiaonaiping.widgets profile is App Store distribution, not development or ad-hoc",
                    ],
                    "blockedByStopConditions": ["distribution-signing-missing"],
                    "rerunGates": [
                        "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                        ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "release-archive-created",
                    "unlocksAction": "export-upload-testflight",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/05-signed-archive.png"],
                    "exitCriteria": [
                        "Release archive succeeds for com.mewpow.xiaonaiping under confirmed Team ID",
                        "Archive evidence does not replace TestFlight processing or iOS 26.5 regression",
                    ],
                    "blockedByStopConditions": ["distribution-signing-missing", "wechat-release-values-missing"],
                    "rerunGates": [
                        "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
                        "python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app --output Backend/proof/testflight-precheck.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "testflight-processed",
                    "unlocksAction": "run-ios265-real-device-regression",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/06-testflight.png"],
                    "exitCriteria": [
                        "TestFlight build is processed and testable",
                        "same version and build are selected for App Store Connect and iOS 26.5 regression",
                    ],
                    "blockedByStopConditions": ["testflight-not-processed"],
                    "rerunGates": [
                        "python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app --output Backend/proof/testflight-precheck.json",
                        "python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "ios265-regression-completed",
                    "unlocksAction": "archive-app-store-evidence",
                    "requiredEvidence": ["Docs/08_Release/AppStoreEvidence/12-real-device-regression.md"],
                    "exitCriteria": [
                        "RD-01 to RD-24 pass on iOS 26.5 TestFlight or signed real-device build",
                        "iOS 27, simulator, and different-build evidence are not used",
                    ],
                    "blockedByStopConditions": ["ios265-device-unavailable"],
                    "rerunGates": [
                        "python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json",
                        "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
                {
                    "id": "submission-gates-green",
                    "unlocksAction": "Submit for Review",
                    "requiredEvidence": [
                        "Backend/proof/app-store-evidence.json",
                        "Backend/proof/production-readiness.json",
                        "Backend/proof/launch-objective-audit.json",
                    ],
                    "exitCriteria": [
                        "app-store-evidence.json ready=true",
                        "production-readiness.json ready=true",
                        "launch-objective-audit.json ready=true",
                    ],
                    "blockedByStopConditions": [
                        "app-store-evidence-incomplete",
                        "production-readiness-incomplete",
                        "launch-objective-audit-incomplete",
                    ],
                    "rerunGates": [
                        "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json",
                        "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json",
                        "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
                    ],
                    "initialStatus": "pending",
                    "canSubmitFromMilestone": False,
                },
            ],
            "actionSequence": [
                {"id": "continue-organization-enrollment", "action": "Continue Apple Developer Organization enrollment.", "boundary": "D-U-N-S only on Apple pages."},
                {"id": "confirm-team-id", "action": "Confirm Team ID.", "boundary": "L2TYJNDTJK only if Apple confirms it."},
                {"id": "confirm-account-roles", "action": "Confirm AppleDeveloper/16-account-roles-access.png with roles."},
                {"id": "verify-bundle-capabilities", "action": "Verify com.mewpow.xiaonaiping, group.com.mewpow.xiaonaiping.shared, and applinks:api.mewpow.com."},
                {"id": "sync-team-id-if-drifted", "action": "Update teamID=<confirmed Apple Developer Team ID> and AASA if Team ID drifted."},
                {
                    "id": "configure-real-wechat-release-values",
                    "action": "Set XNP_WECHAT_APP_ID, XNP_WECHAT_URL_SCHEME, and XNP_WECHAT_UNIVERSAL_LINK.",
                    "command": (
                        "python3 Backend/scripts/prepare_wechat_release_env.py --app-id \"$REAL_WECHAT_APP_ID\" "
                        "--output-env /tmp/xnp-wechat-release.env --output-json "
                        "Backend/proof/wechat-release-env-validation-20260704T-current.json"
                    ),
                },
                {
                    "id": "verify-distribution-certificate-profile",
                    "action": (
                        "Create or select App Store Distribution certificate and provisioning profiles for "
                        "com.mewpow.xiaonaiping and com.mewpow.xiaonaiping.widgets under the confirmed Team ID."
                    ),
                },
                {
                    "id": "archive-release-build",
                    "action": "Run Release archive.",
                    "command": (
                        ". /tmp/xnp-wechat-release.env && xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj "
                        "-scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' "
                        "-archivePath /tmp/XiaoNaiPing-CN.xcarchive XNP_WECHAT_APP_ID=\"$XNP_WECHAT_APP_ID\" "
                        "XNP_WECHAT_URL_SCHEME=\"$XNP_WECHAT_URL_SCHEME\" "
                        "XNP_WECHAT_UNIVERSAL_LINK=\"$XNP_WECHAT_UNIVERSAL_LINK\" archive"
                    ),
                },
                {"id": "export-upload-testflight", "action": "Run xcodebuild -exportArchive using method=app-store-connect, destination=upload, teamID=<confirmed Apple Developer Team ID>, testFlightInternalTestingOnly=false."},
                {"id": "wait-testflight-processing", "action": "Wait for TestFlight processed state."},
                {"id": "rerun-post-archive-gates", "action": "Rerun post-archive gates without iOS 27 or simulator proof."},
                {"id": "run-ios265-real-device-regression", "action": "Run iOS 26.5 RD-01 到 RD-24."},
                {"id": "archive-app-store-evidence", "action": "Archive same-round App Store evidence."},
            ],
            "redactionChecklist": [
                "Hide complete D-U-N-S number",
                "Hide Apple ID email",
                "Hide complete phone numbers",
                "Hide payment and tax details",
                "Hide certificate private keys",
                "Hide provisioning profile files",
                "Hide App Store Connect API keys",
                "Hide XNP_WECHAT_APP_SECRET, verification codes, recovery keys, and complete phone numbers",
            ],
            "stopConditions": [
                {
                    "id": "duns-not-delivered-or-entity-mismatch",
                    "condition": "D-U-N-S is not delivered or Apple enrollment entity does not match 深圳市闪现生活科技有限公司.",
                    "stop": "do not continue Organization enrollment.",
                    "recovery": "request Apple or D&B correction before entering any D-U-N-S value again.",
                },
                {
                    "id": "team-id-drift-unsynced",
                    "condition": "Team ID differs from L2TYJNDTJK and project signing, ExportOptions, AASA, or WeChat Universal Link are not synchronized.",
                    "stop": "do not exportArchive.",
                    "recovery": "Synchronize project signing, ExportOptions, AASA, and WeChat Universal Link, then rerun release gates.",
                },
                {
                    "id": "account-permissions-missing",
                    "condition": "Current Apple ID lacks Certificates, Identifiers & Profiles, App management, build upload, TestFlight management, or submit-review permission.",
                    "stop": "Do not create certificates, Archive, upload builds, or submit review.",
                    "recovery": "Ask the Account Holder or administrator to grant the missing permissions and recapture AppleDeveloper/16-account-roles-access.png.",
                },
                {
                    "id": "distribution-signing-missing",
                    "condition": "App Store Distribution certificate or provisioning profile is missing or does not match com.mewpow.xiaonaiping or com.mewpow.xiaonaiping.widgets.",
                    "stop": "do not Archive.",
                    "recovery": "Fix signing under the confirmed Team ID and recapture AppleDeveloper/15-distribution-certificate-profile.png.",
                },
                {
                    "id": "wechat-release-values-missing",
                    "condition": "XNP_WECHAT_APP_ID, XNP_WECHAT_URL_SCHEME, or XNP_WECHAT_UNIVERSAL_LINK is missing or placeholder.",
                    "stop": "do not upload TestFlight.",
                    "recovery": "Inject real WeChat release values, rerun bundle gates, and keep RD-14 blocked until real WeChat login passes.",
                },
                {
                    "id": "testflight-not-processed",
                    "condition": "TestFlight build is uploaded but not processed or not testable.",
                    "stop": "do not start iOS 26.5 regression.",
                    "recovery": "Wait for processed and testable state, then capture 06-testflight.png.",
                },
                {
                    "id": "ios265-device-unavailable",
                    "condition": "No iOS 26.5 physical iPhone is available.",
                    "stop": "do not substitute iOS 27, simulator, or another build for real-device proof.",
                    "recovery": "Refresh ios265-device-availability.json and fill 12-real-device-regression.md only after an iOS 26.5 physical iPhone is available.",
                },
            ],
            "postArchiveChecks": [
                "python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json",
                "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration.json",
                ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
                "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
                "python3 Backend/scripts/check_testflight_precheck.py --app /path/to/XiaoNaiPing.app --output Backend/proof/testflight-precheck.json",
                "python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json",
                "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json",
                "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json",
            ],
            "completionRule": "This is an action plan only. It does not prove D-U-N-S delivery, does not prove Archive, and does not prove TestFlight. The gates remain incomplete until real target evidence files exist and same-round proof checks pass.",
        },
        ensure_ascii=False,
        indent=2,
    )


def valid_metadata() -> str:
    return """
# APP_STORE_METADATA.md

- 公司主体：深圳市闪现生活科技有限公司
- Copyright：© 2026 深圳市闪现生活科技有限公司
""".lstrip()


def valid_mainland_filing() -> str:
    return """
# 中国大陆备案材料

- 公司主体：深圳市闪现生活科技有限公司

| 字段 | 草案 | 状态 |
| --- | --- | --- |
| 主办单位 | 深圳市闪现生活科技有限公司 | 待营业执照和备案主体确认 |
""".lstrip()


def valid_privacy_page() -> str:
    return "<html><body><p>开发者主体：深圳市闪现生活科技有限公司。</p></body></html>\n"


def valid_terms_page() -> str:
    return "<html><body><p>开发者主体：深圳市闪现生活科技有限公司。</p></body></html>\n"


def valid_support_page() -> str:
    return "<html><body><p>开发者主体：深圳市闪现生活科技有限公司。</p></body></html>\n"


def valid_external_status_poll_template() -> str:
    template_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json"
    )
    return template_path.read_text(encoding="utf-8")


def valid_duns_post_delivery_execution_template() -> str:
    template_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/DUNS-POST-DELIVERY-EXECUTION-RESULT.template.json"
    )
    return template_path.read_text(encoding="utf-8")


def valid_org_signing_result_template() -> str:
    template_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json"
    )
    return template_path.read_text(encoding="utf-8")


def write_valid_docs(root: Path) -> None:
    write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", valid_submission_packet())
    write(root / "Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md", valid_bundle_verification())
    write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook())
    write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_evidence_readme())
    write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide())
    write(root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md", valid_duns_handoff())
    write(root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json", valid_duns_post_delivery_actions())
    write(root / "Docs/08_Release/APP_STORE_METADATA.md", valid_metadata())
    write(root / "Docs/08_Release/MAINLAND_FILING_MATERIALS.md", valid_mainland_filing())
    write(root / "Backend/static/privacy.html", valid_privacy_page())
    write(root / "Backend/static/terms.html", valid_terms_page())
    write(root / "Backend/static/support.html", valid_support_page())
    write(root / "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist", valid_export_options())
    write(root / "Docs/08_Release/AppStoreEvidence/_templates/apple-developer-team-signing-evidence.template.json", valid_team_signing_template())
    write(
        root / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json",
        valid_external_status_poll_template(),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/DUNS-POST-DELIVERY-EXECUTION-RESULT.template.json",
        valid_duns_post_delivery_execution_template(),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json",
        valid_org_signing_result_template(),
    )
    write(root / "App/iOS/project.yml", valid_project_yml())
    write(root / "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj", valid_pbxproj())


class SignedArchiveTestFlightMaterialsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/signed-archive-testflight-materials.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(root),
                "--output",
                str(output),
                "--allow-incomplete",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("signed archive/TestFlight materials", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_materials_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_apple_developer_result_templates_are_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            poll = json.loads(valid_external_status_poll_template())
            poll["status"] = "captured-live-status-poll"
            poll["sources"]["dnbSelfServicePortal"]["canReturnToAppleDeveloperEnrollment"] = True
            poll["sources"]["appStoreConnectDraft"]["missingFields"] = ["payment"]
            poll["targetEvidenceFiles"].pop("appStoreConnectDraft")
            poll["evidenceFileChecks"] = [
                check for check in poll["evidenceFileChecks"] if check["artifactId"] != "appleDeveloperEmail"
            ]
            poll["evidenceFileChecks"][0]["target"] = (
                "Docs/08_Release/AppStoreEvidence/AppleDeveloper/status-dnb-copy.png"
            )
            poll["evidenceFileChecks"][0]["sha256"] = "already-filled"
            poll["evidenceFileChecks"][0]["sameRoundAsStatusPoll"] = True
            poll["evidenceFileChecks"][0]["sourceIsAppleDeveloperEvidenceRoot"] = True
            poll["evidenceFileChecks"][0]["realEvidenceNotTemplate"] = True
            poll["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            poll["switchCriteria"]["teamIdAvailable"] = True
            poll["boundaries"]["canSubmitAtCapture"] = True
            poll["mustNotStore"] = ["complete D-U-N-S Number"]
            poll["xiaonaipingStatusGuardProofs"].pop("productionReadiness")
            poll["crossAppDoesNotReplaceXiaoNaiPingProof"] = False
            poll["postStatusPollXiaoNaiPingProofReruns"] = {
                "checkCrossAppSubmitReady": "check-cross-app-submit-ready"
            }
            poll["completionRule"] = "done"
            write(
                root / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json",
                json.dumps(poll, ensure_ascii=False),
            )
            result = json.loads(valid_org_signing_result_template())
            result["status"] = "captured-live-apple-developer-org"
            result["canSubmitAtCapture"] = True
            result["currentProofs"]["xnpProductionReadiness"] = "Backend/proof/production-readiness.json"
            result["xiaonaipingRequiredProofs"].pop("productionReadiness")
            result["crossAppDoesNotReplaceXiaoNaiPingProof"] = False
            result["instructions"].append("cross-app-submission-readiness canSubmit=true")
            result["postCaptureProofReruns"] = {
                "checkCrossAppSubmitReady": "check-cross-app-submit-ready"
            }
            result["appleDeveloperOrg"]["status"] = "captured-live-apple-developer-org"
            result["appleDeveloperOrg"]["archive"]["appStoreDistributionArchive"] = True
            result["appleDeveloperOrg"]["testFlight"]["evidenceFiles"] = [
                "Docs/08_Release/AppStoreEvidence/06-tf.png"
            ]
            result["evidenceFileChecks"] = [
                check
                for check in result["evidenceFileChecks"]
                if check["artifactId"] != "organizationTeamId"
            ]
            result["evidenceFileChecks"][1]["target"] = "/tmp/apple-org-enrollment.png"
            result["evidenceFileChecks"][1]["sha256"] = "already-filled"
            result["evidenceFileChecks"][1]["sameRoundAsTeamIdOrBuild"] = True
            result["evidenceFileChecks"][1]["secretValuesNotRecorded"] = True
            result["redactionReviewed"]["completeDunsHidden"] = True
            result["operatorNotes"] = "captured"
            write(
                root / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json",
                json.dumps(result, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appleDeveloperExternalStatusPollTemplateValid", report["failedRequiredChecks"])
            self.assertIn("appleDeveloperOrgSigningResultTemplateValid", report["failedRequiredChecks"])
            poll_evidence = report["checks"]["appleDeveloperExternalStatusPollTemplateValid"]["evidence"]
            self.assertIn("externalStatusPollTemplate.status must be 'template-not-evidence'", poll_evidence)
            self.assertIn(
                "externalStatusPollTemplate.sources.dnbSelfServicePortal.canReturnToAppleDeveloperEnrollment must be false",
                poll_evidence,
            )
            self.assertIn("externalStatusPollTemplate.sources.appStoreConnectDraft.missingFields must be empty", poll_evidence)
            self.assertIn("externalStatusPollTemplate.targetEvidenceFiles.appStoreConnectDraft missing", poll_evidence)
            self.assertIn(
                "externalStatusPollTemplate.evidenceFileChecks order must match status poll sources",
                poll_evidence,
            )
            self.assertIn(
                "externalStatusPollTemplate.evidenceFileChecks.appleDeveloperEmail missing object",
                poll_evidence,
            )
            self.assertIn(
                "externalStatusPollTemplate.evidenceFileChecks.dnbSelfServicePortal.target must be Docs/08_Release/AppStoreEvidence/AppleDeveloper/status-dnb-self-service.png",
                poll_evidence,
            )
            self.assertIn(
                "externalStatusPollTemplate.evidenceFileChecks.dnbSelfServicePortal.sha256 must be 'FILL_AFTER_CAPTURE'",
                poll_evidence,
            )
            self.assertIn(
                "externalStatusPollTemplate.evidenceFileChecks.dnbSelfServicePortal.sameRoundAsStatusPoll must be False",
                poll_evidence,
            )
            self.assertIn(
                "externalStatusPollTemplate.evidenceFileChecks.dnbSelfServicePortal.sourceIsAppleDeveloperEvidenceRoot must be False",
                poll_evidence,
            )
            self.assertIn(
                "externalStatusPollTemplate.evidenceFileChecks.dnbSelfServicePortal.realEvidenceNotTemplate must be False",
                poll_evidence,
            )
            self.assertIn(
                "externalStatusPollTemplate.evidenceFileChecks.dnbSelfServicePortal.secretValuesNotRecorded must be False",
                poll_evidence,
            )
            self.assertIn("externalStatusPollTemplate.switchCriteria.teamIdAvailable must be false", poll_evidence)
            self.assertIn("externalStatusPollTemplate.boundaries.canSubmitAtCapture must be False", poll_evidence)
            self.assertIn("externalStatusPollTemplate.mustNotStore missing Apple ID verification code", poll_evidence)
            self.assertIn("externalStatusPollTemplate.xiaonaipingStatusGuardProofs must lock XiaoNaiPing signing", poll_evidence)
            self.assertIn("externalStatusPollTemplate.crossAppDoesNotReplaceXiaoNaiPingProof must be true", poll_evidence)
            self.assertIn(
                "externalStatusPollTemplate.postStatusPollXiaoNaiPingProofReruns must include XiaoNaiPing post-status local proof reruns",
                poll_evidence,
            )
            self.assertIn("externalStatusPollTemplate.completionRule missing external-status-poll-template-not-evidence", poll_evidence)
            result_evidence = report["checks"]["appleDeveloperOrgSigningResultTemplateValid"]["evidence"]
            self.assertIn("orgSigningResultTemplate.status must be 'template-not-evidence'", result_evidence)
            self.assertIn("orgSigningResultTemplate.canSubmitAtCapture must be False", result_evidence)
            self.assertIn("orgSigningResultTemplate.currentProofs.xnpProductionReadiness", result_evidence)
            self.assertIn("orgSigningResultTemplate.xiaonaipingRequiredProofs must lock XiaoNaiPing signing", result_evidence)
            self.assertIn("orgSigningResultTemplate.crossAppDoesNotReplaceXiaoNaiPingProof must be true", result_evidence)
            self.assertIn(
                "orgSigningResultTemplate.instructions must not depend on cross-app submission readiness",
                result_evidence,
            )
            self.assertIn("orgSigningResultTemplate.postCaptureProofReruns must include XiaoNaiPing post-capture local proof reruns", result_evidence)
            self.assertIn(
                "orgSigningResultTemplate.evidenceFileChecks order must match D-U-N-S -> signing -> Archive -> TestFlight evidence workflow",
                result_evidence,
            )
            self.assertIn(
                "orgSigningResultTemplate.evidenceFileChecks.organizationTeamId missing object",
                result_evidence,
            )
            self.assertIn(
                "orgSigningResultTemplate.evidenceFileChecks.organizationEnrollment.target missing Docs/08_Release/AppStoreEvidence/AppleDeveloper/17-apple-org-enrollment-continued.png",
                result_evidence,
            )
            self.assertIn(
                "orgSigningResultTemplate.evidenceFileChecks.organizationEnrollment.sha256 must be 'FILL_AFTER_CAPTURE'",
                result_evidence,
            )
            self.assertIn(
                "orgSigningResultTemplate.evidenceFileChecks.organizationEnrollment.sameRoundAsTeamIdOrBuild must be False",
                result_evidence,
            )
            self.assertIn(
                "orgSigningResultTemplate.evidenceFileChecks.organizationEnrollment.secretValuesNotRecorded must be False",
                result_evidence,
            )
            self.assertIn("orgSigningResultTemplate.appleDeveloperOrg.status must be pending in template", result_evidence)
            self.assertIn(
                "orgSigningResultTemplate.appleDeveloperOrg.archive.appStoreDistributionArchive must be false in template",
                result_evidence,
            )
            self.assertIn(
                "orgSigningResultTemplate.appleDeveloperOrg.testFlight.evidenceFiles missing Docs/08_Release/AppStoreEvidence/06-testflight.png",
                result_evidence,
            )
            self.assertIn(
                "orgSigningResultTemplate.redactionReviewed.completeDunsHidden must be false in template",
                result_evidence,
            )
            self.assertIn("orgSigningResultTemplate.operatorNotes must be empty in template", result_evidence)

    def test_duns_post_delivery_execution_template_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            template = json.loads(valid_duns_post_delivery_execution_template())
            template["status"] = "captured-live-duns-post-delivery"
            template["canSubmitAtCapture"] = True
            template["instructions"] = [
                "Copy this file to DUNS-POST-DELIVERY-EXECUTION-RESULT.json",
                "cross-app-submission-readiness canSubmit=true",
            ]
            template["apps"] = ["Yi Gen Dai Mao", "XiaoNaiPing"]
            template["first60MinuteQueue"] = [
                item
                for item in template["first60MinuteQueue"]
                if item["step"] != "confirm-team-provider-context-before-signing"
            ]
            template["first60MinuteQueue"][0]["done"] = True
            template["identityAndEntityMatch"]["contactIsPenghuiShe"] = True
            template["identityAndEntityMatch"]["wrongNamesAbsent"] = ["Penghui Yu"]
            template["appleDeveloperContinuation"]["organizationNotIndividual"] = False
            template["appleDunsLookupFailureHandling"]["doNotSwitchToIndividual"] = False
            template["paymentAndInvoiceRedaction"]["cardNumberHidden"] = True
            template["teamIdAndProviderContext"]["sameTeamAsAasaArchiveAndTestFlight"] = True
            template["certificatesProfilesArchiveTestFlightChain"]["testFlightBuildProcessed"] = True
            template["evidenceFiles"] = [
                item for item in template["evidenceFiles"] if item["artifactId"] != "paymentReceipt"
            ]
            template["evidenceFiles"][0]["target"] = "Docs/08_Release/AppStoreEvidence/AppleDeveloper/duns-copy.png"
            template["evidenceFiles"][0]["sameRoundAsDunsPostDelivery"] = True
            template["evidenceFiles"][0]["secretValuesNotRecorded"] = True
            template["redactionReviewed"]["neverStoreCompleteDunsNumber"] = False
            template["redactionReviewed"]["completePhoneHidden"] = True
            template["postCaptureProofReruns"] = {"checkCrossAppSubmitReady": "check-cross-app-submit-ready"}
            template["operatorNotes"] = "captured"
            write(
                root / "Docs/08_Release/AppStoreEvidence/AppleDeveloper/DUNS-POST-DELIVERY-EXECUTION-RESULT.template.json",
                json.dumps(template, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appleDeveloperDunsPostDeliveryExecutionTemplateValid", report["failedRequiredChecks"])
            evidence = report["checks"]["appleDeveloperDunsPostDeliveryExecutionTemplateValid"]["evidence"]
            self.assertIn("dunsPostDeliveryExecutionTemplate.status must be 'template-not-evidence'", evidence)
            self.assertIn("dunsPostDeliveryExecutionTemplate.canSubmitAtCapture must be False", evidence)
            self.assertIn("dunsPostDeliveryExecutionTemplate.instructions missing D&B delivery", evidence)
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.instructions must not depend on cross-app submission readiness",
                evidence,
            )
            self.assertIn("dunsPostDeliveryExecutionTemplate.apps must be XiaoNaiPing only", evidence)
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.first60MinuteQueue order must match D-U-N-S first-hour workflow",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.first60MinuteQueue.save-redacted-dnb-delivery-proof.done must be false in template",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.first60MinuteQueue.confirm-team-provider-context-before-signing missing",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.identityAndEntityMatch.contactIsPenghuiShe must be false in template",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.identityAndEntityMatch.wrongNamesAbsent must keep stale-name blockers",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.appleDeveloperContinuation.organizationNotIndividual must be True",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.appleDunsLookupFailureHandling.doNotSwitchToIndividual must be True",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.paymentAndInvoiceRedaction.cardNumberHidden must be false in template",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.teamIdAndProviderContext.sameTeamAsAasaArchiveAndTestFlight must be false in template",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.certificatesProfilesArchiveTestFlightChain.testFlightBuildProcessed must be false in template",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.evidenceFiles order must match D-U-N-S post-delivery execution evidence order",
                evidence,
            )
            self.assertIn("dunsPostDeliveryExecutionTemplate.evidenceFiles.paymentReceipt missing object", evidence)
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.evidenceFiles.dunsDelivery.target must be Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png or .pdf",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.evidenceFiles.dunsDelivery.sameRoundAsDunsPostDelivery must be False",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.evidenceFiles.dunsDelivery.secretValuesNotRecorded must be False",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.redactionReviewed.neverStoreCompleteDunsNumber must be true",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.redactionReviewed.completePhoneHidden must be false in template",
                evidence,
            )
            self.assertIn(
                "dunsPostDeliveryExecutionTemplate.postCaptureProofReruns must include D-U-N-S and XiaoNaiPing local proof reruns",
                evidence,
            )
            self.assertIn("dunsPostDeliveryExecutionTemplate.operatorNotes must be ''", evidence)

    def test_duns_post_delivery_action_packet_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            actions = json.loads(valid_duns_post_delivery_actions())
            actions["sourceFiles"].pop("externalStatusPollTemplate")
            actions["targetEvidenceFiles"].pop("accountRolesAccess")
            actions["evidenceFileChecks"] = [
                check
                for check in actions["evidenceFileChecks"]
                if check["artifactId"] != "accountRolesAccess"
            ]
            actions["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-team-copy.png"
            actions["evidenceFileChecks"][0]["sha256"] = "already-filled"
            actions["evidenceFileChecks"][0]["sameRoundAsDunsPostDelivery"] = True
            actions["evidenceFileChecks"][0]["sourceIsAllowedEvidenceRoot"] = True
            actions["evidenceFileChecks"][0]["teamIdOrBuildMatchesActionPacket"] = True
            actions["evidenceFileChecks"][0]["realEvidenceNotTemplate"] = True
            actions["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            actions["evidenceArchivalMatrix"] = [
                item
                for item in actions["evidenceArchivalMatrix"]
                if item["artifactId"] != "testFlight"
            ]
            actions["evidenceArchivalMatrix"][0]["target"] = "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-team-copy.png"
            actions["evidenceArchivalMatrix"][4]["mustArchiveBefore"] = "submit-review"
            actions["evidenceArchivalMatrix"][7]["initialStatus"] = "captured"
            actions["accountPermissionMatrix"] = [
                item
                for item in actions["accountPermissionMatrix"]
                if item["id"] != "testflight-management-access"
            ]
            actions["accountPermissionMatrix"][1]["evidence"] = "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-roles.png"
            actions["accountPermissionMatrix"][2]["initialStatus"] = "captured"
            actions["actionSequence"] = [
                item for item in actions["actionSequence"]
                if item["id"] != "confirm-team-id"
            ]
            actions["actionSequence"][0]["action"] = "Continue enrollment."
            for item in actions["actionSequence"]:
                if item["id"] == "verify-distribution-certificate-profile":
                    item["action"] = item["action"].replace(
                        " and com.mewpow.xiaonaiping.widgets", ""
                    )
            actions["teamIdDriftSyncMatrix"] = [
                item for item in actions["teamIdDriftSyncMatrix"]
                if item["id"] != "project-yml-widget"
            ]
            actions["teamIdDriftSyncMatrix"][3]["rerunGates"] = ["python3 Backend/scripts/check_universal_links.py"]
            actions["capabilitySigningMatrix"] = [
                item for item in actions["capabilitySigningMatrix"]
                if item["id"] != "main-associated-domain"
            ]
            actions["capabilitySigningMatrix"][0]["bundleId"] = "com.mewpow.copy"
            actions["postDeliveryMilestoneGateMatrix"] = [
                item
                for item in actions["postDeliveryMilestoneGateMatrix"]
                if item["id"] != "testflight-processed"
            ]
            actions["postDeliveryMilestoneGateMatrix"][2]["requiredEvidence"] = [
                "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-team-copy.png"
            ]
            actions["postDeliveryMilestoneGateMatrix"][3]["canSubmitFromMilestone"] = True
            actions["postDeliveryMilestoneGateMatrix"][6]["exitCriteria"] = [
                criterion
                for criterion in actions["postDeliveryMilestoneGateMatrix"][6]["exitCriteria"]
                if "com.mewpow.xiaonaiping.widgets profile" not in criterion
            ]
            actions["postDeliveryMilestoneGateMatrix"][6]["initialStatus"] = "captured"
            actions["redactionChecklist"] = ["Hide Apple ID email"]
            actions["stopConditions"] = [
                item for item in actions["stopConditions"]
                if item["id"] != "ios265-device-unavailable"
            ]
            actions["stopConditions"][0]["stop"] = "Continue anyway."
            actions["postArchiveChecks"] = ["python3 Backend/scripts/check_ios_app_bundle.py"]
            actions["completionRule"] = "This is a checklist."
            actions["canSubmitFromThisPacket"] = True
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
                json.dumps(actions, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsPostDeliveryActionsValid", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsPostDeliveryActionsValid"]["evidence"]
            self.assertIn("sourceFiles order must match D-U-N-S status -> org signing -> TestFlight workflow", evidence)
            self.assertIn(
                "sourceFiles.externalStatusPollTemplate must be Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json",
                evidence,
            )
            self.assertIn("targetEvidenceFiles.accountRolesAccess", evidence)
            self.assertIn("evidenceFileChecks order must match Apple Developer evidence capture order", evidence)
            self.assertIn(
                "evidenceFileChecks.dunsDelivery.target must be Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png or .pdf",
                evidence,
            )
            self.assertIn("evidenceFileChecks.accountRolesAccess missing object", evidence)
            self.assertIn("evidenceFileChecks.dunsDelivery.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("evidenceFileChecks.dunsDelivery.sameRoundAsDunsPostDelivery must be False", evidence)
            self.assertIn("evidenceFileChecks.dunsDelivery.sourceIsAllowedEvidenceRoot must be False", evidence)
            self.assertIn("evidenceFileChecks.dunsDelivery.teamIdOrBuildMatchesActionPacket must be False", evidence)
            self.assertIn("evidenceFileChecks.dunsDelivery.realEvidenceNotTemplate must be False", evidence)
            self.assertIn("evidenceFileChecks.dunsDelivery.secretValuesNotRecorded must be False", evidence)
            self.assertIn("evidenceArchivalMatrix order must match D-U-N-S post-delivery evidence order", evidence)
            self.assertIn(
                "evidenceArchivalMatrix.dunsDelivery.target must be Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png or .pdf",
                evidence,
            )
            self.assertIn(
                "evidenceArchivalMatrix.distributionCertificateProfile.mustArchiveBefore must be archive-release-build",
                evidence,
            )
            self.assertIn("evidenceArchivalMatrix.signedArchive.initialStatus must be pending", evidence)
            self.assertIn("evidenceArchivalMatrix.testFlight missing object", evidence)
            self.assertIn("accountPermissionMatrix order must match Apple Developer permission gate order", evidence)
            self.assertIn(
                "accountPermissionMatrix.app-management-access.evidence must be Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
                evidence,
            )
            self.assertIn("accountPermissionMatrix.build-upload-access.initialStatus must be pending", evidence)
            self.assertIn("accountPermissionMatrix missing testflight-management-access", evidence)
            self.assertIn("actionSequence order must match", evidence)
            self.assertIn("actionSequence missing Organization enrollment", evidence)
            self.assertIn("actionSequence missing com.mewpow.xiaonaiping.widgets", evidence)
            self.assertIn("teamIdDriftSyncMatrix missing project-yml-widget", evidence)
            self.assertIn("teamIdDriftSyncMatrix.aasa-team-prefix missing check_wechat_client_configuration.py", evidence)
            self.assertIn("capabilitySigningMatrix order must match Bundle ID -> entitlements -> signing workflow", evidence)
            self.assertIn("capabilitySigningMatrix.main-app-bundle-id.bundleId must be com.mewpow.xiaonaiping", evidence)
            self.assertIn("capabilitySigningMatrix missing main-associated-domain", evidence)
            self.assertIn(
                "postDeliveryMilestoneGateMatrix order must match D-U-N-S -> Apple Developer -> Archive -> TestFlight exit gates",
                evidence,
            )
            self.assertIn(
                "postDeliveryMilestoneGateMatrix.team-id-confirmed.requiredEvidence must be "
                "['Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png']",
                evidence,
            )
            self.assertIn("postDeliveryMilestoneGateMatrix.account-permissions-confirmed.canSubmitFromMilestone must be False", evidence)
            self.assertIn("postDeliveryMilestoneGateMatrix.distribution-signing-ready.exitCriteria must be", evidence)
            self.assertIn("postDeliveryMilestoneGateMatrix.distribution-signing-ready.initialStatus must be pending", evidence)
            self.assertIn("postDeliveryMilestoneGateMatrix missing testflight-processed", evidence)
            self.assertIn("redactionChecklist missing D-U-N-S number", evidence)
            self.assertIn("stopConditions.duns-not-delivered-or-entity-mismatch missing do not continue Organization enrollment", evidence)
            self.assertIn("stopConditions missing ios265-device-unavailable", evidence)
            self.assertIn("postArchiveChecks missing check_universal_links.py", evidence)
            self.assertIn("completionRule missing action plan only", evidence)
            self.assertIn("canSubmitFromThisPacket must be false", evidence)

    def test_duns_post_delivery_action_packet_rejects_duplicate_ids_and_misbound_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            actions = json.loads(valid_duns_post_delivery_actions())
            actions["sourceFiles"] = {
                "teamSigningTemplate": actions["sourceFiles"]["teamSigningTemplate"],
                "handoff": actions["sourceFiles"]["handoff"],
                "externalStatusPollTemplate": actions["sourceFiles"]["externalStatusPollTemplate"],
                "orgSigningResultTemplate": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/ORG-SIGNING-COPY.json",
                "exportOptions": actions["sourceFiles"]["exportOptions"],
                "appStoreSubmissionPacket": actions["sourceFiles"]["appStoreSubmissionPacket"],
                "testflightRegressionPlan": actions["sourceFiles"]["testflightRegressionPlan"],
                "extraSource": "Docs/08_Release/extra.md",
            }
            actions["teamIdDriftSyncMatrix"].append(dict(actions["teamIdDriftSyncMatrix"][0]))
            actions["teamIdDriftSyncMatrix"][1]["path"] = "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj"
            actions["capabilitySigningMatrix"].append(dict(actions["capabilitySigningMatrix"][0]))
            actions["capabilitySigningMatrix"][1]["target"] = "WrongWidget"
            actions["actionSequence"].append(dict(actions["actionSequence"][-1]))
            actions["stopConditions"].append(dict(actions["stopConditions"][0]))
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
                json.dumps(actions, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsPostDeliveryActionsValid", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsPostDeliveryActionsValid"]["evidence"]
            self.assertIn("sourceFiles order must match D-U-N-S status -> org signing -> TestFlight workflow", evidence)
            self.assertIn(
                "sourceFiles.orgSigningResultTemplate must be Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json",
                evidence,
            )
            self.assertIn("teamIdDriftSyncMatrix duplicate id project-yml-main-app", evidence)
            self.assertIn("teamIdDriftSyncMatrix.project-yml-widget.path must be App/iOS/project.yml", evidence)
            self.assertIn("capabilitySigningMatrix duplicate id main-app-bundle-id", evidence)
            self.assertIn("capabilitySigningMatrix.widget-bundle-id.target must be XiaoNaiPingWidgets", evidence)
            self.assertIn("actionSequence duplicate id archive-app-store-evidence", evidence)
            self.assertIn("stopConditions duplicate id duns-not-delivered-or-entity-mismatch", evidence)

    def test_duns_post_delivery_action_packet_rejects_extra_or_reordered_target_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            actions = json.loads(valid_duns_post_delivery_actions())
            targets = actions["targetEvidenceFiles"]
            actions["targetEvidenceFiles"] = {
                "accountRolesAccess": targets["accountRolesAccess"],
                "organizationTeamId": targets["organizationTeamId"],
                "bundleIdCapabilities": targets["bundleIdCapabilities"],
                "distributionCertificateProfile": targets["distributionCertificateProfile"],
                "wechatAasa": targets["wechatAasa"],
                "signedArchive": "Docs/08_Release/AppStoreEvidence/05-archive-copy.png",
                "testFlight": targets["testFlight"],
                "realDeviceRegression": targets["realDeviceRegression"],
                "extraEvidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/99-extra.png",
            }
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
                json.dumps(actions, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsPostDeliveryActionsValid", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsPostDeliveryActionsValid"]["evidence"]
            self.assertIn("targetEvidenceFiles order must match Apple Developer evidence capture order", evidence)
            self.assertIn(
                "targetEvidenceFiles.signedArchive must be Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
                evidence,
            )

    def test_duns_post_delivery_team_sync_matrix_rejects_extra_or_reordered_items(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            actions = json.loads(valid_duns_post_delivery_actions())
            matrix = actions["teamIdDriftSyncMatrix"]
            actions["teamIdDriftSyncMatrix"] = [
                matrix[1],
                matrix[0],
                *matrix[2:],
                {
                    "id": "extra-team-sync-note",
                    "path": "Docs/08_Release/notes.md",
                    "field": "manual note",
                    "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
                    "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
                    "rerunGates": ["python3 Backend/scripts/check_signed_archive_testflight_materials.py"],
                    "stopIfUnsynced": "Extra notes must not change the Team ID propagation matrix.",
                },
            ]
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
                json.dumps(actions, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsPostDeliveryActionsValid", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsPostDeliveryActionsValid"]["evidence"]
            self.assertIn("teamIdDriftSyncMatrix order must match Team ID propagation order", evidence)

    def test_missing_evidence_names_and_redaction_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook().replace("06-testflight.png", "06-build.png"))
            write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_evidence_readme().replace("06-testflight.png", "06-build.png"))
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide().replace("06-testflight.png", "06-build.png").replace("Apple ID 邮箱", ""))

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("signedArchiveAndTestFlightEvidenceFilenamesPresent", report["failedRequiredChecks"])
            self.assertIn("signedArchiveAndTestFlightEvidenceRedactionCovered", report["failedRequiredChecks"])

    def test_completion_claim_without_archived_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
                valid_submission_packet() + "\nArchive 已完成。TestFlight 已完成。\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("doesNotPretendArchiveOrTestFlightCompleteBeforeEvidence", report["failedRequiredChecks"])
            evidence = report["checks"]["doesNotPretendArchiveOrTestFlightCompleteBeforeEvidence"]["evidence"]
            self.assertIn("Archive 已完成", evidence)
            self.assertIn("TestFlight 已完成", evidence)

    def test_project_signing_configuration_must_be_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(root / "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj", valid_pbxproj().replace("DEVELOPMENT_TEAM = L2TYJNDTJK;\n", ""))

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("projectSigningConfigurationWired", report["failedRequiredChecks"])

    def test_export_options_must_target_app_store_connect_upload(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
                valid_export_options()
                .replace("<string>app-store-connect</string>", "<string>app-store</string>")
                .replace("<string>L2TYJNDTJK</string>", "<string>WRONGTEAM</string>")
                .replace("<key>testFlightInternalTestingOnly</key>\n\t<false/>", "<key>testFlightInternalTestingOnly</key>\n\t<true/>")
                .replace("</dict>", "\t<key>provisioningProfiles</key>\n\t<dict/>\n</dict>"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectExportOptionsPlistValid", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectExportOptionsPlistValid"]["evidence"]
            self.assertIn("method must be 'app-store-connect'", evidence)
            self.assertIn("teamID must be 'L2TYJNDTJK'", evidence)
            self.assertIn("testFlightInternalTestingOnly must be False", evidence)
            self.assertIn("provisioningProfiles must not be committed", evidence)

    def test_duns_handoff_must_cover_team_and_archive_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff().replace("Team ID 已从 Apple Developer 后台确认", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsAppleDeveloperHandoffReady", report["failedRequiredChecks"])

    def test_duns_same_day_execution_template_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("## D-U-N-S 交付当天执行记录模板", "## 执行记录")
                .replace("Team ID 已从 Apple Developer 后台确认", "")
                .replace("不要把 D-U-N-S 编码完整值、Apple ID 邮箱、联系人完整电话、付款信息、证书私钥、provisioning profile 或 AppSecret 写进仓库", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsAppleDeveloperHandoffReady", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsAppleDeveloperHandoffReady"]["evidence"]
            self.assertIn("## D-U-N-S 交付当天执行记录模板", evidence)
            self.assertIn("Team ID 已从 Apple Developer 后台确认", evidence)
            self.assertIn("不要把 D-U-N-S 编码完整值", evidence)

    def test_duns_apple_developer_evidence_filenames_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("`AppleDeveloper/13-organization-team-id.png`", "")
                .replace("`AppleDeveloper/14-bundle-id-capabilities.png`", "")
                .replace("`AppleDeveloper/15-distribution-certificate-profile.png`", "")
                .replace("`Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png`", "")
                .replace("`Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png`", "")
                .replace("`Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png`", ""),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/README.md",
                valid_evidence_readme()
                .replace("`AppleDeveloper/13-organization-team-id.png`", "")
                .replace("`AppleDeveloper/14-bundle-id-capabilities.png`", "")
                .replace("`AppleDeveloper/15-distribution-certificate-profile.png`", ""),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                valid_capture_guide()
                .replace("`AppleDeveloper/13-organization-team-id.png`", "")
                .replace("`AppleDeveloper/14-bundle-id-capabilities.png`", "")
                .replace("`AppleDeveloper/15-distribution-certificate-profile.png`", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsAppleDeveloperEvidenceFilenamesPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsAppleDeveloperEvidenceFilenamesPresent"]["evidence"]
            self.assertIn("`AppleDeveloper/13-organization-team-id.png`", evidence)
            self.assertIn("`AppleDeveloper/14-bundle-id-capabilities.png`", evidence)
            self.assertIn("`AppleDeveloper/15-distribution-certificate-profile.png`", evidence)

    def test_apple_developer_account_access_lock_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("## Apple Developer / App Store Connect 权限锁", "## Apple 权限")
                .replace("`AppleDeveloper/16-account-roles-access.png`", "`AppleDeveloper/16-roles.png`")
                .replace("构建上传权限", "")
                .replace("TestFlight 管理权限", "")
                .replace("不能只用 Team ID 截图替代权限截图", ""),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/README.md",
                valid_evidence_readme()
                .replace("`AppleDeveloper/16-account-roles-access.png`", "`AppleDeveloper/16-roles.png`")
                .replace("构建上传权限", "")
                .replace("TestFlight 管理权限", ""),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                valid_capture_guide()
                .replace("`AppleDeveloper/16-account-roles-access.png`", "`AppleDeveloper/16-roles.png`")
                .replace("构建上传权限", "")
                .replace("TestFlight 管理权限", ""),
            )
            write(
                root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md",
                valid_runbook()
                .replace("AppleDeveloper/16-account-roles-access.png", "AppleDeveloper/16-roles.png")
                .replace("构建上传权限", "")
                .replace("TestFlight 管理权限", "")
                .replace("不能只用 Team ID 截图替代权限截图", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appleDeveloperAccountAccessLockPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["appleDeveloperAccountAccessLockPresent"]["evidence"]
            self.assertIn("## Apple Developer / App Store Connect 权限锁", evidence)
            self.assertIn("`AppleDeveloper/16-account-roles-access.png`", evidence)
            self.assertIn("构建上传权限", evidence)
            self.assertIn("TestFlight 管理权限", evidence)
            self.assertIn("不能只用 Team ID 截图替代权限截图", evidence)

    def test_duns_team_id_drift_must_cover_wechat_aasa_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("08b-wechat-universal-link-aasa.png", "08b-aasa.png")
                .replace("新 Team ID.com.mewpow.xiaonaiping", "")
                .replace("check_provider_evidence_materials.py", ""),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/README.md",
                valid_evidence_readme().replace("08b-wechat-universal-link-aasa.png", "08b-aasa.png"),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                valid_capture_guide().replace("08b-wechat-universal-link-aasa.png", "08b-aasa.png"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsTeamIdWechatAasaSyncCovered", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsTeamIdWechatAasaSyncCovered"]["evidence"]
            self.assertIn("08b-wechat-universal-link-aasa.png", evidence)
            self.assertIn("新 Team ID.com.mewpow.xiaonaiping", evidence)
            self.assertIn("check_provider_evidence_materials.py", evidence)

    def test_duns_team_id_drift_requires_propagation_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("## Team ID 漂移同步矩阵", "## Team ID 同步")
                .replace("`Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`", "")
                .replace("`Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md`", "")
                .replace("`check_app_store_submission_packet.py`", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsTeamIdPropagationMatrixPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsTeamIdPropagationMatrixPresent"]["evidence"]
            self.assertIn("## Team ID 漂移同步矩阵", evidence)
            self.assertIn("`Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`", evidence)
            self.assertIn("`Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md`", evidence)
            self.assertIn("`check_app_store_submission_packet.py`", evidence)

    def test_team_id_pre_export_consistency_lock_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("## Team ID 预导出一致性锁", "## Team ID 导出核对")
                .replace("不得执行 `xcodebuild -exportArchive`", "")
                .replace("如果 ExportOptions 仍是 `L2TYJNDTJK` 但 Apple 页面显示新 Team ID", "")
                .replace("先更新 ExportOptions `teamID`", "")
                .replace("Backend/proof/ios-app-bundle.json", "Backend/proof/bundle.json"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsTeamIdPreExportConsistencyLockPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsTeamIdPreExportConsistencyLockPresent"]["evidence"]
            self.assertIn("## Team ID 预导出一致性锁", evidence)
            self.assertIn("不得执行 `xcodebuild -exportArchive`", evidence)
            self.assertIn("如果 ExportOptions 仍是 `L2TYJNDTJK` 但 Apple 页面显示新 Team ID", evidence)
            self.assertIn("先更新 ExportOptions `teamID`", evidence)
            self.assertIn("`Backend/proof/ios-app-bundle.json`", evidence)

    def test_duns_export_options_team_id_must_use_confirmed_team_id(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            stale_handoff = (
                valid_duns_handoff()
                .replace("日期：2026-07-04", "日期：2026-06-27")
                .replace(
                    "ExportOptions 必须是 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`",
                    "ExportOptions 必须是 `method=app-store-connect`、`destination=upload`、`teamID=L2TYJNDTJK`",
                )
                .replace(
                    "ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`",
                    "ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=L2TYJNDTJK`",
                )
                .replace("当前工程/模板值仍为 `L2TYJNDTJK`；只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用。", "")
                .replace("当前工程/模板值仍为 `L2TYJNDTJK`，只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用。", "")
            )
            write(root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md", stale_handoff)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsExportOptionsUsesConfirmedTeamId", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsExportOptionsUsesConfirmedTeamId"]["evidence"]
            self.assertIn("`teamID=<confirmed Apple Developer Team ID>`", evidence)
            self.assertIn("stale: ExportOptions 必须是", evidence)
            self.assertIn("ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=L2TYJNDTJK`", evidence)

    def test_archive_testflight_execution_template_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff().replace("## Archive / TestFlight 当天执行记录模板", "## Archive 当天记录"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("archiveTestFlightExecutionRecordTemplatePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["archiveTestFlightExecutionRecordTemplatePresent"]["evidence"]
            self.assertIn("## Archive / TestFlight 当天执行记录模板", evidence)

    def test_apple_developer_page_evidence_index_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("## Apple Developer 页面证据索引与脱敏复核", "## Apple Developer 证据")
                .replace("AppleDeveloper/15-distribution-certificate-profile.png", "AppleDeveloper/profile.png")
                .replace("check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json", "check_ios_app_bundle.py")
                .replace("check_app_store_evidence.py --allow-incomplete", "check_app_store_evidence.py")
                .replace("`AppleDeveloper/13-organization-team-id.png`、`AppleDeveloper/14-bundle-id-capabilities.png`、`AppleDeveloper/15-distribution-certificate-profile.png`、`05-signed-archive.png`、`06-testflight.png` 和 `12-real-device-regression.md` 已按页面证据索引归档并脱敏", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appleDeveloperPageEvidenceIndexPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["appleDeveloperPageEvidenceIndexPresent"]["evidence"]
            self.assertIn("## Apple Developer 页面证据索引与脱敏复核", evidence)
            self.assertIn("AppleDeveloper/15-distribution-certificate-profile.png", evidence)
            self.assertIn("check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json", evidence)
            self.assertIn("check_app_store_evidence.py --allow-incomplete", evidence)
            self.assertIn("AppleDeveloper/16-account-roles-access.png", evidence)
            self.assertIn("已按页面证据索引归档并脱敏", evidence)

    def test_apple_developer_team_signing_template_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            broken_template = json.loads(valid_team_signing_template())
            del broken_template["targetEvidenceFiles"]["wechatAasa"]
            broken_template["evidenceFileChecks"] = [
                item
                for item in broken_template["evidenceFileChecks"]
                if item["artifactId"] != "accountRolesAccess"
            ]
            broken_template["evidenceFileChecks"][0]["target"] = (
                "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-team-copy.png"
            )
            broken_template["evidenceFileChecks"][0]["sha256"] = "already-filled"
            broken_template["evidenceFileChecks"][0]["sameRoundAsTemplateCapture"] = True
            broken_template["evidenceFileChecks"][0]["sourceIsAllowedEvidenceRoot"] = True
            broken_template["evidenceFileChecks"][0]["teamIdOrBuildMatchesTemplate"] = True
            broken_template["evidenceFileChecks"][0]["realEvidenceNotTemplate"] = True
            broken_template["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            broken_template["postCaptureChecks"] = [
                item
                for item in broken_template["postCaptureChecks"]
                if "check_testflight_precheck.py" not in item
                and "check_testflight_regression_plan.py" not in item
                and "check_production_readiness.py" not in item
            ]
            broken_template["completionRule"] = "This template is only a capture worksheet."
            write(
                root / "Docs/08_Release/AppStoreEvidence/_templates/apple-developer-team-signing-evidence.template.json",
                json.dumps(broken_template, ensure_ascii=False, indent=2),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appleDeveloperTeamSigningTemplateValid", report["failedRequiredChecks"])
            evidence = report["checks"]["appleDeveloperTeamSigningTemplateValid"]["evidence"]
            self.assertIn("targetEvidenceFiles.wechatAasa", evidence)
            self.assertIn("evidenceFileChecks order must match Apple Developer signing evidence workflow", evidence)
            self.assertIn("evidenceFileChecks.accountRolesAccess missing object", evidence)
            self.assertIn(
                "evidenceFileChecks.organizationTeamId.target must be "
                "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
                evidence,
            )
            self.assertIn("evidenceFileChecks.organizationTeamId.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn(
                "evidenceFileChecks.organizationTeamId.sameRoundAsTemplateCapture must be False",
                evidence,
            )
            self.assertIn(
                "evidenceFileChecks.organizationTeamId.sourceIsAllowedEvidenceRoot must be False",
                evidence,
            )
            self.assertIn(
                "evidenceFileChecks.organizationTeamId.teamIdOrBuildMatchesTemplate must be False",
                evidence,
            )
            self.assertIn("evidenceFileChecks.organizationTeamId.realEvidenceNotTemplate must be False", evidence)
            self.assertIn("evidenceFileChecks.organizationTeamId.secretValuesNotRecorded must be False", evidence)
            self.assertIn("check_testflight_precheck.py --app /path/to/XiaoNaiPing.app", evidence)
            self.assertIn("check_testflight_regression_plan.py", evidence)
            self.assertIn("check_production_readiness.py --require-huawei-obs", evidence)
            self.assertIn("completionRule missing gates remain incomplete", evidence)

    def test_duns_handoff_must_lock_legal_entity_across_submission_and_public_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("## 企业主体一致性锁", "## 主体核对")
                .replace("不能用个人账号或其他公司主体", "")
                .replace("主体不一致时不得继续 Archive / TestFlight / Submit for Review", ""),
            )
            write(
                root / "Docs/08_Release/APP_STORE_METADATA.md",
                valid_metadata().replace("深圳市闪现生活科技有限公司", "其他公司"),
            )
            write(
                root / "Backend/static/privacy.html",
                valid_privacy_page().replace("深圳市闪现生活科技有限公司", "其他公司"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsLegalEntityConsistencyLockPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsLegalEntityConsistencyLockPresent"]["evidence"]
            self.assertIn("## 企业主体一致性锁", evidence)
            self.assertIn("不能用个人账号或其他公司主体", evidence)
            self.assertIn("Docs/08_Release/APP_STORE_METADATA.md", evidence)
            self.assertIn("Backend/static/privacy.html", evidence)

    def test_duns_contact_identity_lock_rejects_stale_name(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("## Apple Developer 联系人姓名锁", "## Apple Developer 联系人")
                .replace("佘鹏辉 / Penghui She", "余鹏辉 / Penghui Yu"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsContactIdentityLockPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["dunsContactIdentityLockPresent"]["evidence"]
            self.assertIn("## Apple Developer 联系人姓名锁", evidence)
            self.assertIn("佘鹏辉", evidence)
            self.assertIn("Penghui She", evidence)
            self.assertIn("stale: 余鹏辉, Penghui Yu", evidence)

    def test_archive_export_upload_plan_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                valid_duns_handoff()
                .replace("xcodebuild -exportArchive", "xcodebuild -export")
                .replace("method=app-store-connect", "method=app-store")
                .replace("testFlightInternalTestingOnly=false", "testFlightInternalTestingOnly=true")
                .replace("不要把 App Store Connect API key", "不要把 Apple 凭证"),
            )
            write(
                root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
                valid_submission_packet()
                .replace("xcodebuild -exportArchive", "xcodebuild -export")
                .replace("method=app-store-connect", "method=app-store")
                .replace("testFlightInternalTestingOnly=false", "testFlightInternalTestingOnly=true")
                .replace("不要把 App Store Connect API key", "不要把 Apple 凭证"),
            )
            write(
                root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md",
                valid_runbook()
                .replace("xcodebuild -exportArchive", "xcodebuild -export")
                .replace("method=app-store-connect", "method=app-store")
                .replace("testFlightInternalTestingOnly=false", "testFlightInternalTestingOnly=true")
                .replace("不要把 App Store Connect API key", "不要把 Apple 凭证"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("archiveExportUploadPlanPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["archiveExportUploadPlanPresent"]["evidence"]
            self.assertIn("xcodebuild -exportArchive", evidence)
            self.assertIn("method=app-store-connect", evidence)
            self.assertIn("testFlightInternalTestingOnly=false", evidence)
            self.assertIn("不要把 App Store Connect API key", evidence)


if __name__ == "__main__":
    unittest.main()
