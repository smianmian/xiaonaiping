#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_STORE_SUBMISSION_PACKET = Path("Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md")
IOS_RELEASE_BUNDLE_VERIFICATION = Path("Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md")
CHINA_MAINLAND_RUNBOOK = Path("Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md")
APP_STORE_EVIDENCE_README = Path("Docs/08_Release/AppStoreEvidence/README.md")
APP_STORE_EVIDENCE_CAPTURE_GUIDE = Path("Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md")
DUNS_HANDOFF = Path("Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md")
DUNS_POST_DELIVERY_ACTIONS = Path("Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json")
EXPORT_OPTIONS_PLIST = Path("Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist")
APPLE_DEVELOPER_TEAM_SIGNING_TEMPLATE = Path("Docs/08_Release/AppStoreEvidence/_templates/apple-developer-team-signing-evidence.template.json")
APPLE_DEVELOPER_EXTERNAL_STATUS_POLL_TEMPLATE = Path(
    "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json"
)
APPLE_DEVELOPER_DUNS_POST_DELIVERY_EXECUTION_TEMPLATE = Path(
    "Docs/08_Release/AppStoreEvidence/AppleDeveloper/DUNS-POST-DELIVERY-EXECUTION-RESULT.template.json"
)
APPLE_DEVELOPER_ORG_SIGNING_RESULT_TEMPLATE = Path(
    "Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json"
)
EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")
APP_STORE_METADATA = Path("Docs/08_Release/APP_STORE_METADATA.md")
MAINLAND_FILING_MATERIALS = Path("Docs/08_Release/MAINLAND_FILING_MATERIALS.md")
PRIVACY_PAGE = Path("Backend/static/privacy.html")
TERMS_PAGE = Path("Backend/static/terms.html")
SUPPORT_PAGE = Path("Backend/static/support.html")
PROJECT_YML = Path("App/iOS/project.yml")
PBXPROJ = Path("App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj")
EXPECTED_LEGAL_ENTITY = "深圳市闪现生活科技有限公司"

SIGNING_SECTION_MARKERS = (
    "## Signing and Archive Status",
    "xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing",
    "-configuration Release",
    "-destination 'generic/platform=iOS'",
    "-archivePath /tmp/XiaoNaiPing-CN.xcarchive archive",
    "Development Team `L2TYJNDTJK`",
    "project.yml",
    "XiaoNaiPing.xcodeproj/project.pbxproj",
    "App Store Distribution archive",
    "D-U-N-S / Apple Developer",
    "real WeChat release values",
    "App Store Distribution signing",
    "uploading a build to App Store Connect",
    "xcodebuild -exportArchive",
    "-exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
)
PROJECT_SIGNING_MARKERS = (
    "DEVELOPMENT_TEAM: L2TYJNDTJK",
    "CODE_SIGN_STYLE: Automatic",
    "CODE_SIGN_ENTITLEMENTS: XiaoNaiPing/XiaoNaiPing.entitlements",
    "DEVELOPMENT_TEAM = L2TYJNDTJK;",
    "CODE_SIGN_STYLE = Automatic;",
    "CODE_SIGN_ENTITLEMENTS = XiaoNaiPing/XiaoNaiPing.entitlements;",
)
DUNS_HANDOFF_MARKERS = (
    "D-U-N-S 交付后",
    "Apple Developer",
    "深圳市闪现生活科技有限公司",
    "Organization enrollment",
    "Team ID",
    "`L2TYJNDTJK`",
    "如果 Apple Developer 显示的组织 Team ID 不是 `L2TYJNDTJK`",
    "`App/iOS/project.yml`",
    "`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`",
    "`Backend/static/apple-app-site-association`",
    "Certificates, Identifiers & Profiles",
    "`com.mewpow.xiaonaiping`",
    "`group.com.mewpow.xiaonaiping.shared`",
    "Associated Domains",
    "App Store Distribution certificate / provisioning profile",
    "Archive",
    "TestFlight",
    "`Docs/08_Release/AppStoreEvidence/05-signed-archive.png`",
    "`Docs/08_Release/AppStoreEvidence/06-testflight.png`",
    "不写入 D-U-N-S 编码、联系人电话、Apple ID 邮箱、付款信息、证书私钥或描述文件私密内容",
    "## D-U-N-S 交付当天执行记录模板",
    "不要把 D-U-N-S 编码完整值、Apple ID 邮箱、联系人完整电话、付款信息、证书私钥、provisioning profile 或 AppSecret 写进仓库",
    "Apple Developer Organization enrollment 已继续提交",
    "Team ID 已从 Apple Developer 后台确认",
    "若 Team ID 不是 `L2TYJNDTJK`，已同步 `App/iOS/project.yml`、`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj` 和 `Backend/static/apple-app-site-association`",
    "Bundle ID `com.mewpow.xiaonaiping` 已归属当前组织 Team",
    "App Store Distribution certificate / provisioning profile 可用于 Archive",
    "已注入真实微信 Release 值，不使用 placeholder `wx...`",
    "Archive / TestFlight 后已重跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_testflight_regression_plan.py`、`check_app_store_evidence.py` 和 `check_production_readiness.py`",
    "`Docs/08_Release/AppStoreEvidence/12-real-device-regression.md`",
)
CONFIRMED_TEAM_ID_EXPORT_MARKERS = (
    "日期：2026-07-04",
    "`teamID=<confirmed Apple Developer Team ID>`",
    "当前工程/模板值仍为 `L2TYJNDTJK`",
    "只有 Apple Developer 后台确认同一 Team ID 后才可直接沿用",
    "如果 ExportOptions 仍是 `L2TYJNDTJK` 但 Apple 页面显示新 Team ID",
    "不要用旧 Team ID 的 Archive 或 TestFlight 证据补交",
    "已按当前 Team ID 复核；若 Team ID 漂移，已同步 `teamID`",
)
STALE_HARDCODED_TEAM_ID_EXPORT_MARKERS = (
    "ExportOptions 必须是 `method=app-store-connect`、`destination=upload`、`teamID=L2TYJNDTJK`",
    "ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=L2TYJNDTJK`",
)
DUNS_EVIDENCE_FILENAME_MARKERS = (
    "`AppleDeveloper/13-organization-team-id.png`",
    "`AppleDeveloper/14-bundle-id-capabilities.png`",
    "`AppleDeveloper/15-distribution-certificate-profile.png`",
    "`AppleDeveloper/16-account-roles-access.png`",
    "`08b-wechat-universal-link-aasa.png`",
    "Apple Developer 组织页",
    "Bundle ID / Identifier 页",
    "App Store Distribution 证书 / Profile",
    "账号权限 / Roles and Access",
)
DUNS_LEGAL_ENTITY_CONSISTENCY_MARKERS = (
    "## 企业主体一致性锁",
    "深圳市闪现生活科技有限公司",
    "`Docs/08_Release/APP_STORE_METADATA.md`",
    "`Docs/08_Release/MAINLAND_FILING_MATERIALS.md`",
    "`Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md`",
    "`Backend/static/privacy.html`",
    "`Backend/static/terms.html`",
    "`Backend/static/support.html`",
    "`Docs/08_Release/AppStoreEvidence/01-company-account.png`",
    "`AppleDeveloper/13-organization-team-id.png`",
    "不能用个人账号或其他公司主体",
    "主体不一致时不得继续 Archive / TestFlight / Submit for Review",
    "`check_signed_archive_testflight_materials.py`",
    "`check_mainland_filing_materials.py`",
    "`check_app_store_connect_materials.py`",
)
DUNS_CONTACT_IDENTITY_MARKERS = (
    "## Apple Developer 联系人姓名锁",
    "佘鹏辉",
    "Penghui She",
    "不能使用余鹏辉",
    "不能使用 Penghui Yu",
    "Apple Developer Organization enrollment",
    "D&B",
    "联系人姓名",
    "证件姓名",
)
STALE_CONTACT_IDENTITY_MARKERS = (
    "余鹏辉",
    "Penghui Yu",
)
APPLE_DEVELOPER_ACCOUNT_ACCESS_LOCK_MARKERS = (
    "## Apple Developer / App Store Connect 权限锁",
    "`AppleDeveloper/16-account-roles-access.png`",
    "当前 Apple ID",
    "Certificates, Identifiers & Profiles",
    "App Store Distribution certificate / provisioning profile",
    "App 管理权限",
    "构建上传权限",
    "TestFlight 管理权限",
    "提交审核权限",
    "不能只用 Team ID 截图替代权限截图",
    "Apple ID 邮箱",
    "联系人完整电话",
    "付款信息",
    "角色列表",
    "`check_signed_archive_testflight_materials.py`",
    "`check_app_store_connect_materials.py`",
    "`check_app_store_evidence.py --allow-incomplete`",
)
DUNS_WECHAT_AASA_SYNC_MARKERS = (
    "08b-wechat-universal-link-aasa.png",
    "AASA",
    "Associated Domains",
    "applinks:api.mewpow.com",
    "XNPWeChatUniversalLink",
    "新 Team ID.com.mewpow.xiaonaiping",
    "微信开放平台 Universal Link",
    "check_provider_evidence_materials.py",
)
TEAM_ID_PROPAGATION_MATRIX_MARKERS = (
    "## Team ID 漂移同步矩阵",
    "Apple Developer 显示的组织 Team ID",
    "`App/iOS/project.yml`",
    "`DEVELOPMENT_TEAM`",
    "`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`",
    "`Backend/static/apple-app-site-association`",
    "`appID` / `appIDs`",
    "`Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`",
    "`teamID`",
    "`Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md`",
    "`XNPWeChatUniversalLink`",
    "`Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md`",
    "`Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md`",
    "`Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png`",
    "`Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png`",
    "`Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png`",
    "`Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png`",
    "`check_universal_links.py`",
    "`check_wechat_client_configuration.py`",
    "`check_ios_release_readiness.py`",
    "`check_ios_app_bundle.py`",
    "`check_signed_archive_testflight_materials.py`",
    "`check_provider_evidence_materials.py`",
    "`check_app_store_submission_packet.py`",
    "`check_production_readiness.py`",
)
TEAM_ID_PRE_EXPORT_CONSISTENCY_MARKERS = (
    "## Team ID 预导出一致性锁",
    "Apple Developer 后台 Team ID 是最终值",
    "`AppleDeveloper/13-organization-team-id.png`",
    "`App/iOS/project.yml`",
    "`App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj`",
    "`Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`",
    "`Backend/static/apple-app-site-association`",
    "`AppleDeveloper/15-distribution-certificate-profile.png`",
    "`08b-wechat-universal-link-aasa.png`",
    "`Backend/proof/ios-release-readiness.json`",
    "`Backend/proof/ios-app-bundle.json`",
    "`Backend/proof/universal-links.json`",
    "`Backend/proof/wechat-client-configuration.json`",
    "不得执行 `xcodebuild -exportArchive`",
    "直到这些 Team ID 口径一致",
    "如果 ExportOptions 仍是 `L2TYJNDTJK` 但 Apple 页面显示新 Team ID",
    "先更新 ExportOptions `teamID`",
    "重新生成 Archive / TestFlight",
)
ARCHIVE_TESTFLIGHT_EXECUTION_TEMPLATE_MARKERS = (
    "## Archive / TestFlight 当天执行记录模板",
    "Xcode 已登录 Apple Developer 账号并选择组织 Team",
    "Team ID 漂移检查已完成；若不是 `L2TYJNDTJK`，已同步 project.yml、project.pbxproj、AASA `appID` / `appIDs`",
    "若 Team ID 漂移，已重新归档 `08b-wechat-universal-link-aasa.png`",
    "真实 `XNP_WECHAT_APP_ID`、`XNP_WECHAT_URL_SCHEME`、`XNP_WECHAT_UNIVERSAL_LINK` 已注入 Release 配置",
    "prepare_wechat_release_env.py",
    "/tmp/xnp-wechat-release.env",
    ". /tmp/xnp-wechat-release.env && xcodebuild",
    'XNP_WECHAT_APP_ID="$XNP_WECHAT_APP_ID"',
    'XNP_WECHAT_URL_SCHEME="$XNP_WECHAT_URL_SCHEME"',
    'XNP_WECHAT_UNIVERSAL_LINK="$XNP_WECHAT_UNIVERSAL_LINK"',
    "Archive 命令使用 `-archivePath /tmp/XiaoNaiPing-CN.xcarchive archive`",
    "导出 / 上传命令使用 `xcodebuild -exportArchive` 和 `Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist`",
    ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py",
    "ExportOptions 使用 `method=app-store-connect`、`destination=upload`、`teamID=<confirmed Apple Developer Team ID>`、`distributionBundleIdentifier=com.mewpow.xiaonaiping`",
    "`testFlightInternalTestingOnly=false`",
    "导出的 `.app` 或 `.ipa` 仅保存在本机私有路径或临时路径，不提交到仓库",
    "TestFlight build 号和版本号已和 App Store Connect 选中的构建、`12-real-device-regression.md` 环境信息一致",
    "`05-signed-archive.png` 能证明 App Store Distribution Archive 成功",
    "`06-testflight.png` 能证明 TestFlight 构建已处理完成并可测试",
    "不记录 Apple ID 邮箱、测试员邮箱、D-U-N-S 编码完整值、证书私钥、provisioning profile、AppSecret、恢复密钥或验证码",
)
APPLE_DEVELOPER_PAGE_EVIDENCE_INDEX_MARKERS = (
    "## Apple Developer 页面证据索引与脱敏复核",
    "Docs/08_Release/AppStoreEvidence/",
    "不替代微信开放平台、短信服务商、OBS、备案或 iOS 26.5 真机回归证据",
    "AppleDeveloper/13-organization-team-id.png",
    "深圳市闪现生活科技有限公司、Organization / Membership 状态、Team ID",
    "AppleDeveloper/14-bundle-id-capabilities.png",
    "Bundle ID `com.mewpow.xiaonaiping`、当前 Team、App Groups `group.com.mewpow.xiaonaiping.shared`、Associated Domains `applinks:api.mewpow.com`",
    "AppleDeveloper/15-distribution-certificate-profile.png",
    "App Store Distribution certificate / provisioning profile 类型、Bundle ID、Team ID、有效状态",
    "08b-wechat-universal-link-aasa.png",
    "AASA endpoint、`新 Team ID.com.mewpow.xiaonaiping`、Associated Domains、`XNPWeChatUniversalLink`、微信开放平台 Universal Link",
    "05-signed-archive.png",
    "Xcode Organizer / Archive 成功状态、`com.mewpow.xiaonaiping`、version、build、App Store Distribution",
    "06-testflight.png",
    "App Store Connect / TestFlight build 版本、build、处理完成或可测试状态、选中 build 与 App Store Connect 一致",
    "12-real-device-regression.md",
    "iOS 26.5、TestFlight 或 Xcode 签名真机包、RD-01 到 RD-24 全部通过、证据文件路径",
    "必须保留",
    "必须遮挡",
    "Apple ID 邮箱",
    "联系人完整电话",
    "D-U-N-S 编码完整值",
    "证书私钥",
    "provisioning profile",
    "AppSecret",
    "恢复密钥",
    "验证码",
    "完整手机号",
    "check_universal_links.py",
    "check_wechat_client_configuration.py",
    ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
    "check_signed_archive_testflight_materials.py",
    "check_provider_evidence_materials.py",
    "check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
    "check_testflight_precheck.py",
    "check_testflight_regression_plan.py",
    "check_app_store_evidence.py --allow-incomplete",
    "`AppleDeveloper/13-organization-team-id.png`、`AppleDeveloper/14-bundle-id-capabilities.png`、`AppleDeveloper/15-distribution-certificate-profile.png`、`AppleDeveloper/16-account-roles-access.png`、`05-signed-archive.png`、`06-testflight.png` 和 `12-real-device-regression.md` 已按页面证据索引归档并脱敏",
)
TEAM_SIGNING_TEMPLATE_REQUIRED_TARGETS = {
    "organizationTeamId": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
    "bundleIdCapabilities": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
    "distributionCertificateProfile": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png",
    "accountRolesAccess": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
    "wechatAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
    "signedArchive": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
    "testFlight": "Docs/08_Release/AppStoreEvidence/06-testflight.png",
    "realDeviceRegression": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
}
TEAM_SIGNING_TEMPLATE_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameRoundAsTemplateCapture": False,
    "sourceIsAllowedEvidenceRoot": False,
    "teamIdOrBuildMatchesTemplate": False,
    "realEvidenceNotTemplate": False,
    "secretValuesNotRecorded": False,
}
TEAM_SIGNING_TEMPLATE_REQUIRED_LIST_VALUES = {
    "doNotRenameThisTemplateTo": (
        "13-organization-team-id.json",
        "14-bundle-id-capabilities.json",
        "15-distribution-certificate-profile.json",
        "16-account-roles-access.json",
        "05-signed-archive.json",
        "06-testflight.json",
    ),
    "bundleAndCapabilityChecks": (
        "com.mewpow.xiaonaiping is under the current organization Team",
        "com.mewpow.xiaonaiping.widgets is under the current organization Team",
        "group.com.mewpow.xiaonaiping.shared is enabled for app and widget",
        "Associated Domains includes applinks:api.mewpow.com",
        "XiaoNaiPing does not enable HealthKit",
    ),
    "archiveAndTestFlightChecks": (
        "App Store Distribution certificate is valid",
        "Provisioning profile is App Store distribution, not development/ad-hoc",
        "Archive succeeds for com.mewpow.xiaonaiping",
        "ExportOptions method is app-store-connect",
        "ExportOptions destination is upload",
        "TestFlight build is processed and testable",
        "Version/build matches App Store Connect selection and 12-real-device-regression.md",
    ),
    "redactionChecklist": (
        "Hide Apple ID email",
        "Hide complete phone numbers",
        "Hide payment and tax details",
        "Hide complete D-U-N-S number",
        "Hide certificate private keys and provisioning profile files",
        "Hide App Store Connect API keys",
        "Hide XNP_WECHAT_APP_SECRET, SMS secrets, OBS AK/SK, verification codes, bearer tokens, recovery keys, and complete phone numbers",
    ),
}
TEAM_SIGNING_TEMPLATE_REQUIRED_TEAM_KEYS = (
    "appleDeveloperTeamId",
    "projectYmlDevelopmentTeam",
    "pbxprojDevelopmentTeam",
    "exportOptionsTeamId",
    "aasaTeamPrefix",
    "associatedDomains",
    "wechatUniversalLink",
)
TEAM_SIGNING_TEMPLATE_REQUIRED_POST_CAPTURE_COMMANDS = (
    "check_signed_archive_testflight_materials.py",
    "check_ios_release_readiness.py",
    "check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app",
    "check_testflight_precheck.py --app /path/to/XiaoNaiPing.app",
    "check_testflight_regression_plan.py",
    "check_provider_evidence_materials.py",
    "check_app_store_evidence.py --allow-incomplete --date 2026-07-04",
    "check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete",
)
EXTERNAL_STATUS_POLL_TEMPLATE_SCALARS = {
    "status": "template-not-evidence",
    "copyTo": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.json",
    "capturedAt": "",
    "capturedBy": "佘鹏辉 / Penghui She",
}
EXTERNAL_STATUS_POLL_PURPOSE_MARKERS = (
    "D&B",
    "Apple Developer enrollment",
    "Apple Developer email",
    "App Store Connect drafts",
    "without treating the poll as submit permission",
)
EXTERNAL_STATUS_POLL_ORGANIZATION = {
    "legalEntityName": EXPECTED_LEGAL_ENTITY,
    "region": "China mainland",
    "contact": "佘鹏辉 / Penghui She",
}
EXTERNAL_STATUS_POLL_SOURCES = {
    "dnbSelfServicePortal": {
        "source": "D&B Self-Service Portal",
        "stringFields": ("checkedAt", "orderStatus", "deliveryStatus", "redactedScreenshotPath", "notes"),
        "falseFlags": ("canReturnToAppleDeveloperEnrollment",),
    },
    "appleDeveloperEnrollment": {
        "source": "Apple Developer Enrollment",
        "stringFields": ("checkedAt", "pageState", "buttonState", "entityTypeShown", "redactedScreenshotPath", "notes"),
        "falseFlags": ("canContinueOrganizationEnrollment",),
    },
    "appleDeveloperEmail": {
        "source": "developer@email.apple.com",
        "stringFields": ("checkedAt", "latestRelevantSubject", "latestRelevantDecision", "redactedScreenshotPath", "notes"),
        "falseFlags": ("canContinueEnrollmentFromEmail",),
    },
    "appStoreConnectDraft": {
        "source": "App Store Connect",
        "stringFields": ("checkedAt", "redactedScreenshotPath", "notes"),
        "falseFlags": ("ydmDraftSaved", "xnpDraftSaved"),
        "emptyLists": ("missingFields",),
    },
}
EXTERNAL_STATUS_POLL_TARGET_EVIDENCE_FILES = {
    "dnbSelfServicePortal": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/status-dnb-self-service.png",
    "appleDeveloperEnrollment": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/status-apple-developer-enrollment.png",
    "appleDeveloperEmail": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/status-apple-developer-email.png",
    "appStoreConnectDraft": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/status-app-store-connect-draft.png",
}
EXTERNAL_STATUS_POLL_EVIDENCE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsStatusPoll", False),
    ("sourceIsAppleDeveloperEvidenceRoot", False),
    ("realEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
EXTERNAL_STATUS_POLL_SWITCH_FLAGS = (
    "dunsDelivered",
    "appleOrganizationCanContinue",
    "appleOrganizationApproved",
    "paymentOrMembershipActive",
    "teamIdAvailable",
)
EXTERNAL_STATUS_POLL_BOUNDARY_VALUES = {
    "doNotTreatAsSubmitPermission": True,
    "canSubmitAtCapture": False,
    "doNotReapplyDuns": True,
    "doNotSwitchToIndividual": True,
    "doNotRepeatOrganizationSubmissionWhenButtonDisabled": True,
    "redactionReviewed": False,
    "xiaonaipingSubmitPermissionProof": "Backend/proof/launch-objective-audit.json",
    "historicalCrossAppStatusIsReferenceOnly": True,
}
EXTERNAL_STATUS_POLL_MUST_NOT_STORE = (
    "complete D-U-N-S Number",
    "Apple ID verification code",
    "full ID number",
    "full phone number",
    "bank account",
    "card number",
    "CVV",
    "AppSecret",
    "token",
    "private key",
    "SMS verification code",
)
EXTERNAL_STATUS_POLL_POST_COMMANDS = (
    "check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
    "check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
    "check_app_store_connect_materials.py --expected-material-date 20260704 --output Backend/proof/app-store-connect-materials.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-07-04 --output Backend/proof/app-store-evidence.json",
    "check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness.json",
    "check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
EXTERNAL_STATUS_POLL_XNP_GUARD_PROOFS = {
    "signedArchiveTestFlightMaterials": "Backend/proof/signed-archive-testflight-materials.json",
    "appStoreSubmissionPacket": "Backend/proof/app-store-submission-packet.json",
    "appStoreConnectMaterials": "Backend/proof/app-store-connect-materials.json",
    "appStoreEvidence": "Backend/proof/app-store-evidence.json",
    "productionReadiness": "Backend/proof/production-readiness.json",
    "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
    "testflightRegressionPlan": "Backend/proof/testflight-regression-plan.json",
    "providerEvidenceMaterials": "Backend/proof/provider-evidence-materials.json",
    "mainlandFilingMaterials": "Backend/proof/mainland-filing-materials.json",
}
EXTERNAL_STATUS_POLL_XNP_RERUNS = {
    "checkSignedArchiveTestFlightMaterials": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
    "checkAppStoreSubmissionPacket": "python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
    "checkAppStoreConnectMaterials": "python3 Backend/scripts/check_app_store_connect_materials.py --expected-material-date 20260704 --output Backend/proof/app-store-connect-materials.json",
    "checkAppStoreEvidence": "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-07-04 --output Backend/proof/app-store-evidence.json",
    "checkTestFlightRegressionPlan": "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    "checkProviderEvidenceMaterials": "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "checkMainlandFilingMaterials": "python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "checkProductionReadiness": "python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness.json",
    "checkLaunchObjectiveAudit": "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
}
EXTERNAL_STATUS_POLL_COMPLETION_MARKERS = (
    "external-status-poll-template-not-evidence",
    "wait, continue Apple Developer Organization enrollment",
    "post-delivery signing workflow",
    "cannot authorize Submit for Review",
    "cannot replace XiaoNaiPing signed archive",
    "production readiness",
    "launch objective audit",
    "provider evidence",
    "filing evidence",
    "final screenshots",
    "iOS 26.5 real-device proof",
)
DUNS_POST_DELIVERY_EXECUTION_TEMPLATE_SCALARS = {
    "status": "template-not-evidence",
    "allowedFinalStatus": "captured-live-duns-post-delivery",
    "doNotTreatAsSubmitPermission": True,
    "canSubmitAtCapture": False,
    "company": EXPECTED_LEGAL_ENTITY,
    "capturedAt": "",
    "capturedBy": "佘鹏辉 / Penghui She",
    "crossAppDoesNotReplaceXiaoNaiPingProof": True,
    "operatorNotes": "",
}
DUNS_POST_DELIVERY_EXECUTION_INSTRUCTION_MARKERS = (
    "Copy this file to DUNS-POST-DELIVERY-EXECUTION-RESULT.json",
    "D&B delivery",
    "Apple Developer Organization continuation",
    "Do not store the complete D-U-N-S number",
    "same-round execution index",
    "does not replace D&B screenshots/PDFs",
    "Apple Developer official status",
    "Team ID proof",
    "Archive",
    "TestFlight",
    "XiaoNaiPing production proof",
    "iOS 26.5 real-device evidence",
    "XiaoNaiPing submit permission",
    "cannot replace XiaoNaiPing WeChat, AASA, SMS, OBS, filing, final screenshot, production, or iOS 26.5 real-device proof",
)
DUNS_POST_DELIVERY_EXECUTION_QUEUE = {
    "save-redacted-dnb-delivery-proof": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png or .pdf",
    "continue-apple-organization-enrollment": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/17-apple-org-enrollment-continued.png or .pdf",
    "submit-or-pay-on-apple-official-page": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/19-apple-developer-payment-receipt.png or .pdf",
    "confirm-team-provider-context-before-signing": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/18-team-context-and-app-record.png or .pdf",
    "refresh-xiaonaiping-auth-and-app-bundle-proofs": "Backend/proof/ios-app-bundle-20260704T-current-ios265.json",
}
DUNS_POST_DELIVERY_EXECUTION_EVIDENCE_FILES = {
    "dunsDelivery": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png or .pdf",
    "appleOrganizationEnrollmentContinued": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/17-apple-org-enrollment-continued.png or .pdf",
    "appleDunsLookupError": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/20-duns-lookup-error.png or .pdf",
    "teamContextAndAppRecord": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/18-team-context-and-app-record.png or .pdf",
    "paymentReceipt": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/19-apple-developer-payment-receipt.png or .pdf",
    "xnpWechatAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
}
DUNS_POST_DELIVERY_EXECUTION_FILE_PLACEHOLDERS = {
    "captured": False,
    "redactionChecked": False,
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "sameRoundAsDunsPostDelivery": False,
    "sourceIsAllowedEvidenceRoot": False,
    "realEvidenceNotTemplate": False,
    "secretValuesNotRecorded": False,
}
DUNS_POST_DELIVERY_EXECUTION_POST_RERUNS = {
    "checkDunsPostDelivery": "latest visible historical reference: /Users/smianmian/Emotion Isle/output/duns-post-delivery-apple-developer-runbook-20260629-current.json; generate and review a 2026-07-04 current source before treating it as same-day evidence",
    "checkSignedArchiveTestFlightMaterials": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
    "checkIOSAppBundle": "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle-20260704T-current-ios265.json",
    "checkWechatClientConfiguration": "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260704-current.json",
    "checkProviderEvidenceMaterials": "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "checkMainlandFilingMaterials": "python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "checkAppStoreSubmissionPacket": "python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
    "checkAppStoreEvidence": "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json",
    "checkProductionReadiness": "python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness.json",
    "checkLaunchObjectiveAudit": "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
}
ORG_SIGNING_RESULT_TEMPLATE_SCALARS = {
    "status": "template-not-evidence",
    "allowedFinalStatus": "captured-live-apple-developer-org",
    "doNotTreatAsSubmitPermission": True,
    "company": EXPECTED_LEGAL_ENTITY,
    "capturedAt": "",
    "capturedBy": "佘鹏辉 / Penghui She",
    "canSubmitAtCapture": False,
}
ORG_SIGNING_RESULT_TEMPLATE_INSTRUCTION_MARKERS = (
    "Copy this file to APPLE-DEVELOPER-ORG-SIGNING-RESULT.json",
    "live D-U-N-S delivery",
    "Apple Organization approval",
    "Team ID",
    "signing",
    "Archive",
    "TestFlight evidence",
    "Do not fill secrets",
    "does not replace screenshots",
    "XiaoNaiPing production readiness",
    "App Store evidence",
    "launch objective audit",
    "iOS 26.5 real-device evidence",
    "XiaoNaiPing submit permission",
    "Cross-app / Emotion Isle proof is historical reference only",
    "cannot replace XiaoNaiPing signing",
    "evidenceFileChecks",
    "file size",
    "SHA-256",
    "same-round Team ID/build confirmation",
    "approved evidence-root confirmation",
    "redaction review result",
)
ORG_SIGNING_RESULT_TEMPLATE_APPS = ("Yi Gen Dai Mao", "XiaoNaiPing")
ORG_SIGNING_RESULT_TEMPLATE_CURRENT_PROOFS = {
    "dunsPostDeliveryRunbook": "/Users/smianmian/Emotion Isle/output/duns-post-delivery-apple-developer-runbook-20260629-current.json",
    "xnpSignedArchiveTestFlightMaterials": "Backend/proof/signed-archive-testflight-materials.json",
    "xnpAppStoreSubmissionPacket": "Backend/proof/app-store-submission-packet.json",
    "xnpAppStoreConnectMaterials": "Backend/proof/app-store-connect-materials.json",
    "xnpAppStoreEvidence": "Backend/proof/app-store-evidence.json",
    "xnpProductionReadiness": "Backend/proof/production-readiness-20260704T-current.json",
    "xnpLaunchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
    "xnpRealDeviceCaptureWorkbench": "Docs/08_Release/AppStoreEvidence/RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json",
}
ORG_SIGNING_RESULT_TEMPLATE_XNP_REQUIRED_PROOFS = {
    "signedArchiveTestFlightMaterials": "Backend/proof/signed-archive-testflight-materials.json",
    "iosReleaseReadiness": "Backend/proof/ios-release-readiness.json",
    "iosAppBundle": "Backend/proof/ios-app-bundle.json",
    "testflightRegressionPlan": "Backend/proof/testflight-regression-plan.json",
    "providerEvidenceMaterials": "Backend/proof/provider-evidence-materials.json",
    "mainlandFilingMaterials": "Backend/proof/mainland-filing-materials.json",
    "appStoreSubmissionPacket": "Backend/proof/app-store-submission-packet.json",
    "appStoreConnectMaterials": "Backend/proof/app-store-connect-materials.json",
    "appStoreEvidence": "Backend/proof/app-store-evidence.json",
    "productionReadiness": "Backend/proof/production-readiness.json",
    "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
}
ORG_SIGNING_RESULT_TEMPLATE_POST_CAPTURE_RERUNS = {
    "checkSignedArchiveTestFlightMaterials": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
    "checkIOSReleaseReadiness": ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
    "checkIOSAppBundle": "python3 Backend/scripts/check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app --output Backend/proof/ios-app-bundle.json",
    "checkTestFlightRegressionPlan": "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    "checkProviderEvidenceMaterials": "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "checkMainlandFilingMaterials": "python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "checkAppStoreSubmissionPacket": "python3 Backend/scripts/check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
    "checkAppStoreConnectMaterials": "python3 Backend/scripts/check_app_store_connect_materials.py --expected-material-date 20260704 --output Backend/proof/app-store-connect-materials.json",
    "checkAppStoreEvidence": "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence.json",
    "checkProductionReadiness": "python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness.json",
    "checkLaunchObjectiveAudit": "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
}
ORG_SIGNING_RESULT_TEMPLATE_FILE_CHECKS = {
    "dunsDelivery": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png",
    "organizationEnrollment": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/17-apple-org-enrollment-continued.png",
    "organizationTeamId": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
    "bundleIdCapabilities": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
    "distributionCertificateProfile": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png",
    "accountRolesAccess": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
    "teamContextAndBundleOwnership": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/18-team-context-and-app-record.png",
    "paymentReceipt": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/19-apple-developer-payment-receipt.png",
    "wechatAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
    "signedArchive": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
    "testFlight": "Docs/08_Release/AppStoreEvidence/06-testflight.png",
    "realDeviceRegression": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
}
ORG_SIGNING_RESULT_TEMPLATE_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameRoundAsTeamIdOrBuild": False,
    "sourceIsApprovedEvidenceRoot": False,
    "secretValuesNotRecorded": False,
}
ORG_SIGNING_RESULT_TEMPLATE_SECTIONS = {
    "dunsDelivery": {
        "fileMarker": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-duns-delivery.png",
        "flags": ("legalEntityNameVisible", "chinaMainlandVisible", "completeDunsHidden"),
    },
    "organizationEnrollment": {
        "fileMarker": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/17-apple-org-enrollment-continued.png",
        "flags": ("entityTypeOrganizationVisible", "individualNotSelected", "approvalOrSubmittedStatusVisible"),
    },
    "paymentReceipt": {
        "fileMarker": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/19-apple-developer-payment-receipt.png",
        "flags": ("organizationMembershipVisible", "paymentAndInvoiceSecretsHidden"),
    },
    "teamContextAndBundleOwnership": {
        "fileMarker": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/18-team-context-and-app-record.png",
        "flags": ("sameOrganizationTeamAcrossApps", "sameTeamAsAasaArchiveAndTestFlight", "providerIsOrganizationNotIndividual"),
    },
    "certificatesProfiles": {
        "fileMarker": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png",
        "flags": ("appStoreDistributionCertificateVisible", "xnpMainAndWidgetProfilesVisible"),
    },
    "archive": {
        "fileMarker": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
        "flags": ("appStoreDistributionArchive", "sameVersionBuildAsTestFlight"),
    },
    "testFlight": {
        "fileMarker": "Docs/08_Release/AppStoreEvidence/06-testflight.png",
        "flags": ("buildProcessedAndTestable", "sameBuildAsArchiveAndRealDeviceCapture"),
    },
    "xnpWechatAasa": {
        "fileMarker": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
        "flags": ("sameTeamIdAsOrganization", "sameUniversalLinkAsWechatOpenPlatform"),
    },
}
ORG_SIGNING_RESULT_TEMPLATE_REDACTION_FLAGS = (
    "appleIdEmailHidden",
    "completePhoneHidden",
    "completeDunsHidden",
    "paymentDataHidden",
    "taxAndInvoiceDataHidden",
    "certificatePrivateKeysHidden",
    "appSecretsTokensAndVerificationCodesHidden",
)
FORBIDDEN_CROSS_APP_SUBMIT_PERMISSION_MARKERS = (
    "cross-app-submission-readiness canSubmit=true",
    "cross-app-submission-readiness-20260629-current.json has canSubmit=true",
    "cross-app-submission-readiness-20260629-current.json",
    "cross-app-submission-readiness-20260704-current.json has canSubmit=true",
    "cross-app-submission-readiness-20260704-current.json",
    "check-cross-app-submit-ready",
    "checkCrossAppSubmitReady",
    "crossAppSubmissionReadinessProof",
)
DUNS_ACTIONS_REQUIRED_SCALARS = {
    "artifactType": "apple-developer-duns-post-delivery-actions",
    "status": "action-plan-not-evidence",
    "date": "2026-07-04",
    "company": EXPECTED_LEGAL_ENTITY,
}
DUNS_ACTIONS_REQUIRED_SOURCE_FILES = {
    "handoff": "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "externalStatusPollTemplate": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/EXTERNAL-STATUS-POLL-RESULT.template.json",
    "dunsPostDeliveryExecutionTemplate": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/DUNS-POST-DELIVERY-EXECUTION-RESULT.template.json",
    "orgSigningResultTemplate": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/APPLE-DEVELOPER-ORG-SIGNING-RESULT.template.json",
    "teamSigningTemplate": "Docs/08_Release/AppStoreEvidence/_templates/apple-developer-team-signing-evidence.template.json",
    "exportOptions": "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
    "appStoreSubmissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
    "testflightRegressionPlan": "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
}
DUNS_ACTIONS_REQUIRED_SOURCE_IDS = tuple(DUNS_ACTIONS_REQUIRED_SOURCE_FILES)
DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGETS = {
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
DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGET_IDS = tuple(DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGETS)
DUNS_ACTIONS_REQUIRED_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameRoundAsDunsPostDelivery": False,
    "sourceIsAllowedEvidenceRoot": False,
    "teamIdOrBuildMatchesActionPacket": False,
    "realEvidenceNotTemplate": False,
    "secretValuesNotRecorded": False,
}
DUNS_ACTIONS_EVIDENCE_ARCHIVAL_FIELDS = (
    "artifactId",
    "upstreamAction",
    "target",
    "mustArchiveBefore",
    "rerunGate",
    "doesNotReplace",
    "initialStatus",
)
DUNS_ACTIONS_EVIDENCE_ARCHIVAL_MATRIX = {
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
DUNS_ACTIONS_REQUIRED_ACCOUNT_PERMISSION_MATRIX = {
    "certificates-identifiers-profiles-access": {
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
    "app-management-access": {
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
    "build-upload-access": {
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
    "testflight-management-access": {
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
    "submit-review-access": {
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
    "account-holder-admin-escalation": {
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
}
DUNS_ACTIONS_REQUIRED_ACCOUNT_PERMISSION_IDS = tuple(DUNS_ACTIONS_REQUIRED_ACCOUNT_PERMISSION_MATRIX)
DUNS_ACTIONS_REQUIRED_TEAM_SYNC_MATRIX = {
    "project-yml-main-app": (
        "App/iOS/project.yml",
        "targets.XiaoNaiPing.settings.base.DEVELOPMENT_TEAM",
        "<confirmed Apple Developer Team ID>",
        "AppleDeveloper/13-organization-team-id.png",
        "check_ios_release_readiness.py",
        "check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app",
        "Do not archive",
    ),
    "project-yml-widget": (
        "App/iOS/project.yml",
        "targets.XiaoNaiPingWidgets.settings.base.DEVELOPMENT_TEAM",
        "group.com.mewpow.xiaonaiping.shared",
        "AppleDeveloper/14-bundle-id-capabilities.png",
        "check_ios_release_readiness.py",
        "check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app",
        "same Team",
    ),
    "xcodeproj-development-team": (
        "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj",
        "DEVELOPMENT_TEAM",
        "DevelopmentTeam",
        "<confirmed Apple Developer Team ID>",
        "check_ios_release_readiness.py",
        "check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app",
    ),
    "export-options-team-id": (
        "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
        "teamID",
        "<confirmed Apple Developer Team ID>",
        "AppleDeveloper/15-distribution-certificate-profile.png",
        "check_signed_archive_testflight_materials.py",
        "xcodebuild -exportArchive",
    ),
    "aasa-team-prefix": (
        "Backend/static/apple-app-site-association",
        "appID",
        "appIDs",
        "<confirmed Apple Developer Team ID>.com.mewpow.xiaonaiping",
        "08b-wechat-universal-link-aasa.png",
        "check_universal_links.py",
        "check_wechat_client_configuration.py",
    ),
    "wechat-release-universal-link": (
        "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md",
        "XNPWeChatUniversalLink",
        "applinks:api.mewpow.com",
        "https://api.mewpow.com/xiaonaiping/wechat/",
        "check_wechat_client_configuration.py",
        "check_provider_evidence_materials.py",
        "RD-14",
    ),
    "submission-runbook-team-id": (
        "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
        "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md",
        "current Team ID",
        "<confirmed Apple Developer Team ID>",
        "check_app_store_submission_packet.py",
        "check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete",
        "old Team ID",
    ),
}
DUNS_ACTIONS_REQUIRED_TEAM_SYNC_IDS = tuple(DUNS_ACTIONS_REQUIRED_TEAM_SYNC_MATRIX.keys())
DUNS_ACTIONS_REQUIRED_TEAM_SYNC_EXACT_VALUES = {
    "project-yml-main-app": {
        "path": "App/iOS/project.yml",
        "field": "targets.XiaoNaiPing.settings.base.DEVELOPMENT_TEAM",
        "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
        "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
    },
    "project-yml-widget": {
        "path": "App/iOS/project.yml",
        "field": "targets.XiaoNaiPingWidgets.settings.base.DEVELOPMENT_TEAM",
        "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
        "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
    },
    "xcodeproj-development-team": {
        "path": "App/iOS/XiaoNaiPing.xcodeproj/project.pbxproj",
        "field": "DEVELOPMENT_TEAM and DevelopmentTeam",
        "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
        "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/13-organization-team-id.png",
    },
    "export-options-team-id": {
        "path": "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
        "field": "teamID",
        "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
        "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/15-distribution-certificate-profile.png",
    },
    "aasa-team-prefix": {
        "path": "Backend/static/apple-app-site-association",
        "field": "appID and appIDs Team prefix",
        "expectedWhenDrifted": "<confirmed Apple Developer Team ID>.com.mewpow.xiaonaiping",
        "evidence": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
    },
    "wechat-release-universal-link": {
        "path": "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md",
        "field": "XNPWeChatUniversalLink / Associated Domains / WeChat Open Platform Universal Link",
        "expectedWhenDrifted": "Same confirmed Team ID, applinks:api.mewpow.com, and https://api.mewpow.com/xiaonaiping/wechat/ in the same evidence round",
        "evidence": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
    },
    "submission-runbook-team-id": {
        "path": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md and Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md",
        "field": "current Team ID, Archive/TestFlight prerequisites, and no-submit boundary",
        "expectedWhenDrifted": "<confirmed Apple Developer Team ID>",
        "evidence": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/14-bundle-id-capabilities.png",
    },
}
DUNS_ACTIONS_REQUIRED_CAPABILITY_SIGNING_MATRIX = {
    "main-app-bundle-id": {
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
    "widget-bundle-id": {
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
    "shared-app-group": {
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
    "main-associated-domain": {
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
    "app-store-distribution-signing": {
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
}
DUNS_ACTIONS_REQUIRED_CAPABILITY_SIGNING_IDS = tuple(DUNS_ACTIONS_REQUIRED_CAPABILITY_SIGNING_MATRIX)
DUNS_ACTIONS_REQUIRED_MILESTONE_GATE_MATRIX = {
    "duns-delivered": {
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
    "organization-enrollment-continued": {
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
    "team-id-confirmed": {
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
    "account-permissions-confirmed": {
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
    "bundle-capabilities-confirmed": {
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
    "team-id-and-wechat-synced": {
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
    "distribution-signing-ready": {
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
    "release-archive-created": {
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
    "testflight-processed": {
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
    "ios265-regression-completed": {
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
    "submission-gates-green": {
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
}
DUNS_ACTIONS_REQUIRED_MILESTONE_GATE_IDS = tuple(DUNS_ACTIONS_REQUIRED_MILESTONE_GATE_MATRIX)
DUNS_ACTIONS_REQUIRED_SEQUENCE_IDS = (
    "continue-organization-enrollment",
    "confirm-team-id",
    "confirm-account-roles",
    "verify-bundle-capabilities",
    "sync-team-id-if-drifted",
    "configure-real-wechat-release-values",
    "verify-distribution-certificate-profile",
    "archive-release-build",
    "export-upload-testflight",
    "wait-testflight-processing",
    "rerun-post-archive-gates",
    "run-ios265-real-device-regression",
    "archive-app-store-evidence",
)
DUNS_ACTIONS_REQUIRED_STOP_CONDITIONS = {
    "duns-not-delivered-or-entity-mismatch": (
        "D-U-N-S",
        "深圳市闪现生活科技有限公司",
        "do not continue Organization enrollment",
        "request Apple or D&B correction",
    ),
    "team-id-drift-unsynced": (
        "Team ID differs from L2TYJNDTJK",
        "do not exportArchive",
        "project signing",
        "ExportOptions",
        "AASA",
        "WeChat Universal Link",
    ),
    "account-permissions-missing": (
        "Certificates, Identifiers & Profiles",
        "App management",
        "build upload",
        "TestFlight management",
        "submit-review",
        "Account Holder",
    ),
    "distribution-signing-missing": (
        "App Store Distribution certificate",
        "provisioning profile",
        "com.mewpow.xiaonaiping.widgets",
        "do not Archive",
        "AppleDeveloper/15-distribution-certificate-profile.png",
    ),
    "wechat-release-values-missing": (
        "XNP_WECHAT_APP_ID",
        "XNP_WECHAT_URL_SCHEME",
        "XNP_WECHAT_UNIVERSAL_LINK",
        "do not upload TestFlight",
        "RD-14",
    ),
    "testflight-not-processed": (
        "TestFlight build",
        "processed",
        "testable",
        "do not start iOS 26.5 regression",
        "06-testflight.png",
    ),
    "ios265-device-unavailable": (
        "iOS 26.5",
        "physical iPhone",
        "do not substitute iOS 27",
        "ios265-device-availability.json",
        "12-real-device-regression.md",
    ),
}
DUNS_ACTIONS_REQUIRED_REDACTION_MARKERS = (
    "D-U-N-S number",
    "Apple ID email",
    "complete phone numbers",
    "payment",
    "certificate private keys",
    "provisioning profile files",
    "App Store Connect API keys",
    "XNP_WECHAT_APP_SECRET",
    "verification codes",
    "recovery keys",
)
DUNS_ACTIONS_REQUIRED_POST_ARCHIVE_COMMANDS = (
    "check_universal_links.py",
    "check_wechat_client_configuration.py",
    ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py",
    "check_ios_app_bundle.py --app /path/to/XiaoNaiPing.app",
    "check_testflight_precheck.py --app /path/to/XiaoNaiPing.app",
    "check_testflight_regression_plan.py",
    "check_signed_archive_testflight_materials.py",
    "check_app_store_evidence.py --allow-incomplete",
    "check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete",
)
EXPORT_OPTIONS_MARKERS = (
    "Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
    "xcodebuild -exportArchive",
    "-archivePath /tmp/XiaoNaiPing-CN.xcarchive",
    "-exportPath /tmp/XiaoNaiPing-CN-AppStoreConnect",
    "-exportOptionsPlist Docs/08_Release/XCODE_EXPORT_OPTIONS_APP_STORE_CONNECT.plist",
    "method=app-store-connect",
    "destination=upload",
    "manageAppVersionAndBuildNumber=false",
    "testFlightInternalTestingOnly=false",
    "uploadSymbols=true",
    "不要把 App Store Connect API key、Apple ID 邮箱、验证码、provisioning profile、证书私钥或导出的 `.ipa` 提交到仓库",
)
EXPECTED_EXPORT_OPTIONS = {
    "destination": "upload",
    "distributionBundleIdentifier": "com.mewpow.xiaonaiping",
    "generateAppStoreInformation": False,
    "manageAppVersionAndBuildNumber": False,
    "method": "app-store-connect",
    "signingStyle": "automatic",
    "stripSwiftSymbols": True,
    "teamID": "L2TYJNDTJK",
    "testFlightInternalTestingOnly": False,
    "uploadSymbols": True,
}
FORBIDDEN_EXPORT_OPTIONS_KEYS = (
    "provisioningProfiles",
    "signingCertificate",
    "installerSigningCertificate",
)
POST_ARCHIVE_VERIFICATION_MARKERS = (
    "archive 后还要用导出的 `.app` 重新跑 `check_ios_app_bundle.py`",
    "Backend/proof/ios-265-build.json",
    "Backend/proof/ios-app-bundle.json",
    "iphoneos26.5",
    "iOS 26.5",
    "App Store Distribution 签名归档",
    "TestFlight 上传后的同一套包体扫描和真机回归证据",
)
EVIDENCE_FILENAME_MARKERS = (
    "05-signed-archive.png",
    "06-testflight.png",
)
CAPTURE_GUIDE_MARKERS = (
    "`05-signed-archive.png`",
    "App Store Distribution archive 成功",
    "Bundle ID、版本、build、archive success / uploaded status",
    "Apple ID 邮箱",
    "`06-testflight.png`",
    "TestFlight 构建已处理完成并可测试",
    "Build 号、版本、处理状态、测试状态",
    "测试员邮箱",
)
TESTFLIGHT_BOUNDARY_MARKERS = (
    "TestFlight or signed-device final screenshots",
    "TestFlight / 签名真机回归",
    "不替代 TestFlight / 签名真机回归",
    "TestFlight 或签名真机包",
    "iOS 26.5",
)
PRE_SUBMIT_COMMAND_MARKERS = (
    "check_signed_archive_testflight_materials.py",
    "check_ios_app_bundle.py",
    "check_testflight_precheck.py",
    "check_testflight_regression_plan.py",
    "check_app_store_evidence.py",
)
FORBIDDEN_PRETEND_COMPLETE_MARKERS = (
    "Archive 已完成",
    "Archive 已上传",
    "TestFlight 已完成",
    "TestFlight 已通过",
    "signedArchive 已完成",
    "testFlight 已完成",
)
FORBIDDEN_STALE_RUNTIME_PATTERNS = {
    "iphoneos18": re.compile(r"iphoneos18\.\d+"),
    "iphonesimulator18": re.compile(r"iphonesimulator18\.\d+"),
    "ios18Destination": re.compile(r"OS=18\.\d+"),
    "ios27Claim": re.compile(r"iOS 27\.0.*(?:TestFlight|签名真机|真机回归|提交证据)"),
}
FORBIDDEN_SECRET_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
    "plainProviderSecretAssignment": re.compile(
        r"(?:XNP_SMS_SECRET|XNP_WECHAT_APP_SECRET|ALIYUN_ACCESS_KEY_SECRET|HUAWEI_OBS_SECRET_ACCESS_KEY)\s*=\s*(?![<.]|replace-)\S{8,}"
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_plist(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            data = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def archived_real_evidence_present(root: Path, filename: str) -> bool:
    path = root / EVIDENCE_ROOT / filename
    return path.is_file() and path.stat().st_size > 0


def stale_runtime_hits(text: str) -> list[str]:
    return sorted(name for name, pattern in FORBIDDEN_STALE_RUNTIME_PATTERNS.items() if pattern.search(text))


def forbidden_secret_hits(text: str) -> list[str]:
    return sorted(name for name, pattern in FORBIDDEN_SECRET_PATTERNS.items() if pattern.search(text))


def export_options_failures(options: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not options:
        return ["missing or invalid plist"]
    for key, expected_value in EXPECTED_EXPORT_OPTIONS.items():
        if options.get(key) != expected_value:
            failures.append(f"{key} must be {expected_value!r}")
    for key in FORBIDDEN_EXPORT_OPTIONS_KEYS:
        if key in options:
            failures.append(f"{key} must not be committed in shared export options")
    return failures


def team_signing_template_failures(template: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not template:
        return ["missing or invalid apple developer team signing evidence template"]
    expected_scalars = {
        "artifactType": "apple-developer-team-signing-evidence-template",
        "status": "template-only-not-evidence",
        "project": "XiaoNaiPing",
        "company": EXPECTED_LEGAL_ENTITY,
    }
    for key, expected_value in expected_scalars.items():
        if template.get(key) != expected_value:
            failures.append(f"{key} must be {expected_value}")
    targets = template.get("targetEvidenceFiles")
    if not isinstance(targets, dict):
        failures.append("targetEvidenceFiles must be an object")
    else:
        for key, expected_value in TEAM_SIGNING_TEMPLATE_REQUIRED_TARGETS.items():
            if targets.get(key) != expected_value:
                failures.append(f"targetEvidenceFiles.{key} must be {expected_value}")
    file_checks = template.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append("evidenceFileChecks must be a list")
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for check in file_checks:
            if not isinstance(check, dict):
                failures.append("evidenceFileChecks entries must be objects")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in checks_by_artifact:
                failures.append(f"evidenceFileChecks duplicate {artifact_id}")
            checks_by_artifact[artifact_id] = check
        if tuple(artifact_order) != tuple(TEAM_SIGNING_TEMPLATE_REQUIRED_TARGETS):
            failures.append("evidenceFileChecks order must match Apple Developer signing evidence workflow")
        for artifact_id, target_marker in TEAM_SIGNING_TEMPLATE_REQUIRED_TARGETS.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != target_marker:
                failures.append(f"evidenceFileChecks.{artifact_id}.target must be {target_marker}")
            for key, expected_value in TEAM_SIGNING_TEMPLATE_FILE_CHECK_PLACEHOLDERS.items():
                if check.get(key) != expected_value:
                    failures.append(f"evidenceFileChecks.{artifact_id}.{key} must be {expected_value!r}")
    team_checks = template.get("teamConsistencyChecks")
    if not isinstance(team_checks, dict):
        failures.append("teamConsistencyChecks must be an object")
    else:
        for key in TEAM_SIGNING_TEMPLATE_REQUIRED_TEAM_KEYS:
            if key not in team_checks:
                failures.append(f"teamConsistencyChecks.{key} missing")
    for key, expected_values in TEAM_SIGNING_TEMPLATE_REQUIRED_LIST_VALUES.items():
        values = template.get(key)
        if not isinstance(values, list):
            failures.append(f"{key} must be a list")
            continue
        for expected_value in expected_values:
            if expected_value not in values:
                failures.append(f"{key} missing {expected_value}")
    post_capture_checks = template.get("postCaptureChecks")
    if not isinstance(post_capture_checks, list):
        failures.append("postCaptureChecks must be a list")
    else:
        post_capture_text = "\n".join(str(item) for item in post_capture_checks)
        for command in TEAM_SIGNING_TEMPLATE_REQUIRED_POST_CAPTURE_COMMANDS:
            if command not in post_capture_text:
                failures.append(f"postCaptureChecks missing {command}")
    completion_rule = str(template.get("completionRule", ""))
    for marker in (
        "template is only a capture worksheet",
        "gates remain incomplete",
        "real target evidence files exist",
        "same-round proof checks pass",
    ):
        if marker not in completion_rule:
            failures.append(f"completionRule missing {marker}")
    return failures


def external_status_poll_template_failures(template: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not template:
        return ["missing or invalid Apple Developer external status poll template"]

    for key, expected_value in EXTERNAL_STATUS_POLL_TEMPLATE_SCALARS.items():
        if template.get(key) != expected_value:
            failures.append(f"externalStatusPollTemplate.{key} must be {expected_value!r}")

    purpose = str(template.get("purpose", ""))
    for marker in EXTERNAL_STATUS_POLL_PURPOSE_MARKERS:
        if marker not in purpose:
            failures.append(f"externalStatusPollTemplate.purpose missing {marker}")

    organization = template.get("organization")
    if not isinstance(organization, dict):
        failures.append("externalStatusPollTemplate.organization must be an object")
    else:
        for key, expected_value in EXTERNAL_STATUS_POLL_ORGANIZATION.items():
            if organization.get(key) != expected_value:
                failures.append(f"externalStatusPollTemplate.organization.{key} must be {expected_value}")

    sources = template.get("sources")
    if not isinstance(sources, dict):
        failures.append("externalStatusPollTemplate.sources must be an object")
    else:
        for section, rules in EXTERNAL_STATUS_POLL_SOURCES.items():
            source = sources.get(section)
            if not isinstance(source, dict):
                failures.append(f"externalStatusPollTemplate.sources.{section} missing")
                continue
            if source.get("source") != rules["source"]:
                failures.append(f"externalStatusPollTemplate.sources.{section}.source must be {rules['source']}")
            for field in rules.get("stringFields", ()):
                if source.get(field) != "":
                    failures.append(f"externalStatusPollTemplate.sources.{section}.{field} must be empty")
            for flag in rules.get("falseFlags", ()):
                if source.get(flag) is not False:
                    failures.append(f"externalStatusPollTemplate.sources.{section}.{flag} must be false")
            for list_name in rules.get("emptyLists", ()):
                if source.get(list_name) != []:
                    failures.append(f"externalStatusPollTemplate.sources.{section}.{list_name} must be empty")

    target_files = template.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        failures.append("externalStatusPollTemplate.targetEvidenceFiles must be an object")
    else:
        if tuple(target_files) != tuple(EXTERNAL_STATUS_POLL_TARGET_EVIDENCE_FILES):
            failures.append("externalStatusPollTemplate.targetEvidenceFiles order must match status poll sources")
        for key, expected in EXTERNAL_STATUS_POLL_TARGET_EVIDENCE_FILES.items():
            if key not in target_files:
                failures.append(f"externalStatusPollTemplate.targetEvidenceFiles.{key} missing")
            elif target_files.get(key) != expected:
                failures.append(f"externalStatusPollTemplate.targetEvidenceFiles.{key} must be {expected}")

    evidence_file_checks = template.get("evidenceFileChecks")
    if not isinstance(evidence_file_checks, list):
        failures.append("externalStatusPollTemplate.evidenceFileChecks must be an array")
    else:
        seen: set[str] = set()
        by_artifact: dict[str, dict[str, Any]] = {}
        for item in evidence_file_checks:
            if not isinstance(item, dict):
                failures.append("externalStatusPollTemplate.evidenceFileChecks entry must be an object")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("externalStatusPollTemplate.evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in seen:
                failures.append(f"externalStatusPollTemplate.evidenceFileChecks duplicate {artifact_id}")
                continue
            seen.add(artifact_id)
            by_artifact[artifact_id] = item
        if tuple(by_artifact) != tuple(EXTERNAL_STATUS_POLL_TARGET_EVIDENCE_FILES):
            failures.append("externalStatusPollTemplate.evidenceFileChecks order must match status poll sources")
        for artifact_id, expected_target in EXTERNAL_STATUS_POLL_TARGET_EVIDENCE_FILES.items():
            check = by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"externalStatusPollTemplate.evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != expected_target:
                failures.append(f"externalStatusPollTemplate.evidenceFileChecks.{artifact_id}.target must be {expected_target}")
            for field, expected in EXTERNAL_STATUS_POLL_EVIDENCE_FILE_CHECK_FIELDS:
                if check.get(field) != expected:
                    failures.append(
                        f"externalStatusPollTemplate.evidenceFileChecks.{artifact_id}.{field} must be {expected!r}"
                    )

    switch_criteria = template.get("switchCriteria")
    if not isinstance(switch_criteria, dict):
        failures.append("externalStatusPollTemplate.switchCriteria must be an object")
    else:
        for flag in EXTERNAL_STATUS_POLL_SWITCH_FLAGS:
            if switch_criteria.get(flag) is not False:
                failures.append(f"externalStatusPollTemplate.switchCriteria.{flag} must be false")

    boundaries = template.get("boundaries")
    if not isinstance(boundaries, dict):
        failures.append("externalStatusPollTemplate.boundaries must be an object")
    else:
        for key, expected_value in EXTERNAL_STATUS_POLL_BOUNDARY_VALUES.items():
            if boundaries.get(key) != expected_value:
                failures.append(f"externalStatusPollTemplate.boundaries.{key} must be {expected_value!r}")

    must_not_store_text = "\n".join(str(item) for item in template.get("mustNotStore", []))
    for marker in EXTERNAL_STATUS_POLL_MUST_NOT_STORE:
        if marker not in must_not_store_text:
            failures.append(f"externalStatusPollTemplate.mustNotStore missing {marker}")

    post_capture_text = "\n".join(str(item) for item in template.get("postCaptureCommands", []))
    for command in EXTERNAL_STATUS_POLL_POST_COMMANDS:
        if command not in post_capture_text:
            failures.append(f"externalStatusPollTemplate.postCaptureCommands missing {command}")

    if template.get("xiaonaipingStatusGuardProofs") != EXTERNAL_STATUS_POLL_XNP_GUARD_PROOFS:
        failures.append("externalStatusPollTemplate.xiaonaipingStatusGuardProofs must lock XiaoNaiPing signing, App Store Connect, App Store submission, App Store evidence, production, launch audit, TestFlight, provider, and filing proofs")
    if template.get("crossAppDoesNotReplaceXiaoNaiPingProof") is not True:
        failures.append("externalStatusPollTemplate.crossAppDoesNotReplaceXiaoNaiPingProof must be true")
    if template.get("postStatusPollXiaoNaiPingProofReruns") != EXTERNAL_STATUS_POLL_XNP_RERUNS:
        failures.append("externalStatusPollTemplate.postStatusPollXiaoNaiPingProofReruns must include XiaoNaiPing post-status local proof reruns")

    completion_rule = str(template.get("completionRule", ""))
    for marker in EXTERNAL_STATUS_POLL_COMPLETION_MARKERS:
        if marker not in completion_rule:
            failures.append(f"externalStatusPollTemplate.completionRule missing {marker}")

    template_text = json.dumps(template, ensure_ascii=False)
    leaked_submit_markers = [
        marker for marker in FORBIDDEN_CROSS_APP_SUBMIT_PERMISSION_MARKERS if marker in template_text
    ]
    if leaked_submit_markers:
        failures.append(
            "externalStatusPollTemplate must not depend on stale cross-app submission readiness: "
            + ", ".join(leaked_submit_markers)
        )

    secret_hits = forbidden_secret_hits(template_text)
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def duns_post_delivery_execution_template_failures(template: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not template:
        return ["missing or invalid D-U-N-S post-delivery execution result template"]

    for key, expected_value in DUNS_POST_DELIVERY_EXECUTION_TEMPLATE_SCALARS.items():
        if template.get(key) != expected_value:
            failures.append(f"dunsPostDeliveryExecutionTemplate.{key} must be {expected_value!r}")

    instruction_text = "\n".join(str(item) for item in template.get("instructions", []))
    for marker in DUNS_POST_DELIVERY_EXECUTION_INSTRUCTION_MARKERS:
        if marker not in instruction_text:
            failures.append(f"dunsPostDeliveryExecutionTemplate.instructions missing {marker}")
    template_text = json.dumps(template, ensure_ascii=False)
    leaked_submit_markers = [
        marker for marker in FORBIDDEN_CROSS_APP_SUBMIT_PERMISSION_MARKERS if marker in template_text
    ]
    if leaked_submit_markers:
        failures.append(
            "dunsPostDeliveryExecutionTemplate.instructions must not depend on cross-app submission readiness: "
            + ", ".join(leaked_submit_markers)
        )

    if tuple(template.get("apps", [])) != ("XiaoNaiPing",):
        failures.append("dunsPostDeliveryExecutionTemplate.apps must be XiaoNaiPing only")

    queue = template.get("first60MinuteQueue")
    if not isinstance(queue, list):
        failures.append("dunsPostDeliveryExecutionTemplate.first60MinuteQueue must be a list")
    else:
        queue_by_step: dict[str, dict[str, Any]] = {}
        queue_order: list[Any] = []
        for item in queue:
            if not isinstance(item, dict):
                failures.append("dunsPostDeliveryExecutionTemplate.first60MinuteQueue entries must be objects")
                continue
            step = item.get("step")
            queue_order.append(step)
            if not isinstance(step, str) or not step:
                failures.append("dunsPostDeliveryExecutionTemplate.first60MinuteQueue entry missing step")
                continue
            if step in queue_by_step:
                failures.append(f"dunsPostDeliveryExecutionTemplate.first60MinuteQueue duplicate {step}")
            queue_by_step[step] = item
        if tuple(queue_order) != tuple(DUNS_POST_DELIVERY_EXECUTION_QUEUE):
            failures.append("dunsPostDeliveryExecutionTemplate.first60MinuteQueue order must match D-U-N-S first-hour workflow")
        for step, expected_evidence in DUNS_POST_DELIVERY_EXECUTION_QUEUE.items():
            item = queue_by_step.get(step)
            if not isinstance(item, dict):
                failures.append(f"dunsPostDeliveryExecutionTemplate.first60MinuteQueue.{step} missing")
                continue
            if item.get("done") is not False:
                failures.append(f"dunsPostDeliveryExecutionTemplate.first60MinuteQueue.{step}.done must be false in template")
            if item.get("requiredEvidence") != expected_evidence:
                failures.append(
                    f"dunsPostDeliveryExecutionTemplate.first60MinuteQueue.{step}.requiredEvidence must be {expected_evidence}"
                )

    identity = template.get("identityAndEntityMatch")
    if not isinstance(identity, dict):
        failures.append("dunsPostDeliveryExecutionTemplate.identityAndEntityMatch must be an object")
    else:
        for flag in (
            "legalEntityNameVisible",
            "chinaMainlandVisible",
            "companyAddressMatchesBusinessLicense",
            "contactIsPenghuiShe",
        ):
            if identity.get(flag) is not False:
                failures.append(f"dunsPostDeliveryExecutionTemplate.identityAndEntityMatch.{flag} must be false in template")
        if set(identity.get("wrongNamesAbsent", [])) != set(STALE_CONTACT_IDENTITY_MARKERS):
            failures.append("dunsPostDeliveryExecutionTemplate.identityAndEntityMatch.wrongNamesAbsent must keep stale-name blockers")

    continuation = template.get("appleDeveloperContinuation")
    if not isinstance(continuation, dict):
        failures.append("dunsPostDeliveryExecutionTemplate.appleDeveloperContinuation must be an object")
    else:
        expected_continuation = {
            "entityType": "Organization",
            "appleOfficialPageOnly": True,
            "organizationNotIndividual": True,
            "appleIdEmailHiddenInProof": False,
            "completePhoneHiddenInProof": False,
            "submittedOrPendingOrApprovedVisible": False,
        }
        for key, expected_value in expected_continuation.items():
            if continuation.get(key) != expected_value:
                failures.append(f"dunsPostDeliveryExecutionTemplate.appleDeveloperContinuation.{key} must be {expected_value!r}")

    duns_lookup = template.get("appleDunsLookupFailureHandling")
    if not isinstance(duns_lookup, dict):
        failures.append("dunsPostDeliveryExecutionTemplate.appleDunsLookupFailureHandling must be an object")
    else:
        expected_lookup = {
            "lookupStatus": "not-run",
            "notFoundOrMismatchScreenshot": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/20-duns-lookup-error.png or .pdf",
            "waitForDnbApplePropagation": False,
            "appleDeveloperSupportCaseIdRedacted": "",
            "doNotSwitchToIndividual": True,
            "doNotUseOtherCompanyDuns": True,
            "doNotRepeatSubmitSameError": True,
        }
        for key, expected_value in expected_lookup.items():
            if duns_lookup.get(key) != expected_value:
                failures.append(f"dunsPostDeliveryExecutionTemplate.appleDunsLookupFailureHandling.{key} must be {expected_value!r}")

    for section_name, false_flags in {
        "paymentAndInvoiceRedaction": (
            "paymentSuccessOrMembershipActiveVisible",
            "cardNumberHidden",
            "cvvHidden",
            "invoiceDetailsHidden",
            "taxAndBankDetailsHidden",
        ),
        "teamIdAndProviderContext": (
            "teamIdCapturedAfterOrganizationApproval",
            "teamIdStoredOnlyWhereNeededForMigrationAndAppleBackends",
            "sameOrganizationTeamAcrossApps",
            "sameTeamAsAasaArchiveAndTestFlight",
            "providerIsOrganizationNotIndividual",
            "oldPersonalTeamNotUsed",
        ),
        "certificatesProfilesArchiveTestFlightChain": (
            "xnpWechatAasaUsesSameOrganizationTeam",
            "xnpMainAndWidgetProfilesCreated",
            "appStoreDistributionCertificateCreated",
            "archiveUsesAppStoreDistribution",
            "testFlightBuildProcessed",
            "ios265RealDeviceOrTestFlightRegressionCaptured",
        ),
    }.items():
        section = template.get(section_name)
        if not isinstance(section, dict):
            failures.append(f"dunsPostDeliveryExecutionTemplate.{section_name} must be an object")
            continue
        for flag in false_flags:
            if section.get(flag) is not False:
                failures.append(f"dunsPostDeliveryExecutionTemplate.{section_name}.{flag} must be false in template")

    evidence_files = template.get("evidenceFiles")
    if not isinstance(evidence_files, list):
        failures.append("dunsPostDeliveryExecutionTemplate.evidenceFiles must be a list")
    else:
        by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for item in evidence_files:
            if not isinstance(item, dict):
                failures.append("dunsPostDeliveryExecutionTemplate.evidenceFiles entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("dunsPostDeliveryExecutionTemplate.evidenceFiles entry missing artifactId")
                continue
            if artifact_id in by_artifact:
                failures.append(f"dunsPostDeliveryExecutionTemplate.evidenceFiles duplicate {artifact_id}")
            by_artifact[artifact_id] = item
        if tuple(artifact_order) != tuple(DUNS_POST_DELIVERY_EXECUTION_EVIDENCE_FILES):
            failures.append("dunsPostDeliveryExecutionTemplate.evidenceFiles order must match D-U-N-S post-delivery execution evidence order")
        for artifact_id, expected_target in DUNS_POST_DELIVERY_EXECUTION_EVIDENCE_FILES.items():
            item = by_artifact.get(artifact_id)
            if not isinstance(item, dict):
                failures.append(f"dunsPostDeliveryExecutionTemplate.evidenceFiles.{artifact_id} missing object")
                continue
            if item.get("target") != expected_target:
                failures.append(f"dunsPostDeliveryExecutionTemplate.evidenceFiles.{artifact_id}.target must be {expected_target}")
            for key, expected_value in DUNS_POST_DELIVERY_EXECUTION_FILE_PLACEHOLDERS.items():
                if item.get(key) != expected_value:
                    failures.append(
                        f"dunsPostDeliveryExecutionTemplate.evidenceFiles.{artifact_id}.{key} must be {expected_value!r}"
                    )

    redaction_reviewed = template.get("redactionReviewed")
    if not isinstance(redaction_reviewed, dict):
        failures.append("dunsPostDeliveryExecutionTemplate.redactionReviewed must be an object")
    else:
        if redaction_reviewed.get("neverStoreCompleteDunsNumber") is not True:
            failures.append("dunsPostDeliveryExecutionTemplate.redactionReviewed.neverStoreCompleteDunsNumber must be true")
        for flag in (
            "appleIdEmailHidden",
            "completePhoneHidden",
            "paymentDataHidden",
            "taxAndInvoiceDataHidden",
            "bankAccountHidden",
            "certificatePrivateKeysHidden",
            "appSecretsTokensAndVerificationCodesHidden",
        ):
            if redaction_reviewed.get(flag) is not False:
                failures.append(f"dunsPostDeliveryExecutionTemplate.redactionReviewed.{flag} must be false in template")

    if template.get("postCaptureProofReruns") != DUNS_POST_DELIVERY_EXECUTION_POST_RERUNS:
        failures.append("dunsPostDeliveryExecutionTemplate.postCaptureProofReruns must include D-U-N-S and XiaoNaiPing local proof reruns")

    secret_hits = forbidden_secret_hits(template_text)
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def org_signing_result_template_failures(template: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not template:
        return ["missing or invalid Apple Developer org signing result template"]

    for key, expected_value in ORG_SIGNING_RESULT_TEMPLATE_SCALARS.items():
        if template.get(key) != expected_value:
            failures.append(f"orgSigningResultTemplate.{key} must be {expected_value!r}")

    instruction_text = "\n".join(str(item) for item in template.get("instructions", []))
    for marker in ORG_SIGNING_RESULT_TEMPLATE_INSTRUCTION_MARKERS:
        if marker not in instruction_text:
            failures.append(f"orgSigningResultTemplate.instructions missing {marker}")
    template_text = json.dumps(template, ensure_ascii=False)
    leaked_submit_markers = [
        marker for marker in FORBIDDEN_CROSS_APP_SUBMIT_PERMISSION_MARKERS if marker in template_text
    ]
    if leaked_submit_markers:
        failures.append(
            "orgSigningResultTemplate.instructions must not depend on cross-app submission readiness: "
            + ", ".join(leaked_submit_markers)
        )

    if tuple(template.get("apps", [])) != ORG_SIGNING_RESULT_TEMPLATE_APPS:
        failures.append("orgSigningResultTemplate.apps must be Yi Gen Dai Mao -> XiaoNaiPing")

    current_proofs = template.get("currentProofs")
    if not isinstance(current_proofs, dict):
        failures.append("orgSigningResultTemplate.currentProofs must be an object")
    else:
        for key, expected_value in ORG_SIGNING_RESULT_TEMPLATE_CURRENT_PROOFS.items():
            if current_proofs.get(key) != expected_value:
                failures.append(f"orgSigningResultTemplate.currentProofs.{key} must be {expected_value}")
    if template.get("xiaonaipingRequiredProofs") != ORG_SIGNING_RESULT_TEMPLATE_XNP_REQUIRED_PROOFS:
        failures.append(
            "orgSigningResultTemplate.xiaonaipingRequiredProofs must lock XiaoNaiPing signing, iOS, TestFlight, provider, filing, App Store, production, and launch audit proofs"
        )
    if template.get("crossAppDoesNotReplaceXiaoNaiPingProof") is not True:
        failures.append("orgSigningResultTemplate.crossAppDoesNotReplaceXiaoNaiPingProof must be true")
    if template.get("postCaptureProofReruns") != ORG_SIGNING_RESULT_TEMPLATE_POST_CAPTURE_RERUNS:
        failures.append("orgSigningResultTemplate.postCaptureProofReruns must include XiaoNaiPing post-capture local proof reruns")

    file_checks = template.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append("orgSigningResultTemplate.evidenceFileChecks must be a list")
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for check in file_checks:
            if not isinstance(check, dict):
                failures.append("orgSigningResultTemplate.evidenceFileChecks entries must be objects")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("orgSigningResultTemplate.evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in checks_by_artifact:
                failures.append(f"orgSigningResultTemplate.evidenceFileChecks duplicate {artifact_id}")
            checks_by_artifact[artifact_id] = check

        if tuple(artifact_order) != tuple(ORG_SIGNING_RESULT_TEMPLATE_FILE_CHECKS):
            failures.append("orgSigningResultTemplate.evidenceFileChecks order must match D-U-N-S -> signing -> Archive -> TestFlight evidence workflow")

        for artifact_id, target_marker in ORG_SIGNING_RESULT_TEMPLATE_FILE_CHECKS.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"orgSigningResultTemplate.evidenceFileChecks.{artifact_id} missing object")
                continue
            if target_marker not in str(check.get("target", "")):
                failures.append(f"orgSigningResultTemplate.evidenceFileChecks.{artifact_id}.target missing {target_marker}")
            for key, expected_value in ORG_SIGNING_RESULT_TEMPLATE_FILE_CHECK_PLACEHOLDERS.items():
                if check.get(key) != expected_value:
                    failures.append(
                        f"orgSigningResultTemplate.evidenceFileChecks.{artifact_id}.{key} must be {expected_value!r}"
                    )

    apple_org = template.get("appleDeveloperOrg")
    if not isinstance(apple_org, dict):
        failures.append("orgSigningResultTemplate.appleDeveloperOrg must be an object")
    else:
        if apple_org.get("status") != "pending":
            failures.append("orgSigningResultTemplate.appleDeveloperOrg.status must be pending in template")
        for section, rules in ORG_SIGNING_RESULT_TEMPLATE_SECTIONS.items():
            section_value = apple_org.get(section)
            if not isinstance(section_value, dict):
                failures.append(f"orgSigningResultTemplate.appleDeveloperOrg.{section} missing")
                continue
            evidence_text = "\n".join(str(item) for item in section_value.get("evidenceFiles", []))
            if rules["fileMarker"] not in evidence_text:
                failures.append(
                    f"orgSigningResultTemplate.appleDeveloperOrg.{section}.evidenceFiles missing {rules['fileMarker']}"
                )
            for flag in rules["flags"]:
                if section_value.get(flag) is not False:
                    failures.append(f"orgSigningResultTemplate.appleDeveloperOrg.{section}.{flag} must be false in template")

    redaction_reviewed = template.get("redactionReviewed")
    if not isinstance(redaction_reviewed, dict):
        failures.append("orgSigningResultTemplate.redactionReviewed must be an object")
    else:
        for flag in ORG_SIGNING_RESULT_TEMPLATE_REDACTION_FLAGS:
            if redaction_reviewed.get(flag) is not False:
                failures.append(f"orgSigningResultTemplate.redactionReviewed.{flag} must be false in template")

    if template.get("operatorNotes") != "":
        failures.append("orgSigningResultTemplate.operatorNotes must be empty in template")

    secret_hits = forbidden_secret_hits(template_text)
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def duns_post_delivery_actions_failures(actions: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not actions:
        return ["missing or invalid D-U-N-S post-delivery action packet"]

    for key, expected_value in DUNS_ACTIONS_REQUIRED_SCALARS.items():
        if actions.get(key) != expected_value:
            failures.append(f"{key} must be {expected_value}")

    sources = actions.get("sourceFiles")
    if not isinstance(sources, dict):
        failures.append("sourceFiles must be an object")
    else:
        if tuple(sources) != DUNS_ACTIONS_REQUIRED_SOURCE_IDS:
            failures.append("sourceFiles order must match D-U-N-S status -> org signing -> TestFlight workflow")
        for key, expected_value in DUNS_ACTIONS_REQUIRED_SOURCE_FILES.items():
            if sources.get(key) != expected_value:
                failures.append(f"sourceFiles.{key} must be {expected_value}")

    evidence_targets = actions.get("targetEvidenceFiles")
    if not isinstance(evidence_targets, dict):
        failures.append("targetEvidenceFiles must be an object")
    else:
        if tuple(evidence_targets) != DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGET_IDS:
            failures.append("targetEvidenceFiles order must match Apple Developer evidence capture order")
        for key, expected_value in DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGETS.items():
            if evidence_targets.get(key) != expected_value:
                failures.append(f"targetEvidenceFiles.{key} must be {expected_value}")

    file_checks = actions.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append("evidenceFileChecks must be a list")
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for check in file_checks:
            if not isinstance(check, dict):
                failures.append("evidenceFileChecks entries must be objects")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in checks_by_artifact:
                failures.append(f"evidenceFileChecks duplicate {artifact_id}")
            checks_by_artifact[artifact_id] = check

        if tuple(artifact_order) != DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGET_IDS:
            failures.append("evidenceFileChecks order must match Apple Developer evidence capture order")

        for artifact_id, target_marker in DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGETS.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != target_marker:
                failures.append(f"evidenceFileChecks.{artifact_id}.target must be {target_marker}")
            for key, expected_value in DUNS_ACTIONS_REQUIRED_FILE_CHECK_PLACEHOLDERS.items():
                if check.get(key) != expected_value:
                    failures.append(f"evidenceFileChecks.{artifact_id}.{key} must be {expected_value!r}")

    archival_matrix = actions.get("evidenceArchivalMatrix")
    if not isinstance(archival_matrix, list):
        failures.append("evidenceArchivalMatrix must be a list")
    else:
        by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for item in archival_matrix:
            if not isinstance(item, dict):
                failures.append("evidenceArchivalMatrix entry must be an object")
                continue
            artifact_id = item.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceArchivalMatrix entry missing artifactId")
                continue
            if artifact_id in by_artifact:
                failures.append(f"evidenceArchivalMatrix duplicate {artifact_id}")
            by_artifact[artifact_id] = item
        if tuple(artifact_order) != DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGET_IDS:
            failures.append("evidenceArchivalMatrix order must match D-U-N-S post-delivery evidence order")
        for artifact_id, expected in DUNS_ACTIONS_EVIDENCE_ARCHIVAL_MATRIX.items():
            item = by_artifact.get(artifact_id)
            if not isinstance(item, dict):
                failures.append(f"evidenceArchivalMatrix.{artifact_id} missing object")
                continue
            if tuple(item) != DUNS_ACTIONS_EVIDENCE_ARCHIVAL_FIELDS:
                failures.append(f"evidenceArchivalMatrix.{artifact_id} keys must match archival schema")
            expected_values = {
                "artifactId": artifact_id,
                "target": DUNS_ACTIONS_REQUIRED_EVIDENCE_TARGETS[artifact_id],
                "initialStatus": "pending",
                **expected,
            }
            for key, expected_value in expected_values.items():
                if item.get(key) != expected_value:
                    failures.append(f"evidenceArchivalMatrix.{artifact_id}.{key} must be {expected_value}")

    account_permission_matrix = actions.get("accountPermissionMatrix")
    if not isinstance(account_permission_matrix, list):
        failures.append("accountPermissionMatrix must be a list")
    else:
        by_id: dict[str, dict[str, Any]] = {}
        permission_ids: list[str] = []
        for item in account_permission_matrix:
            if not isinstance(item, dict):
                failures.append("accountPermissionMatrix entry must be an object")
                continue
            permission_id = item.get("id")
            if not isinstance(permission_id, str) or not permission_id:
                failures.append("accountPermissionMatrix entry missing id")
                continue
            permission_ids.append(permission_id)
            if permission_id in by_id:
                failures.append(f"accountPermissionMatrix duplicate id {permission_id}")
                continue
            by_id[permission_id] = item
        if tuple(permission_ids) != DUNS_ACTIONS_REQUIRED_ACCOUNT_PERMISSION_IDS:
            failures.append("accountPermissionMatrix order must match Apple Developer permission gate order")
        for permission_id, expected in DUNS_ACTIONS_REQUIRED_ACCOUNT_PERMISSION_MATRIX.items():
            item = by_id.get(permission_id)
            if not item:
                failures.append(f"accountPermissionMatrix missing {permission_id}")
                continue
            expected_keys = ("id", *expected.keys())
            if tuple(item) != expected_keys:
                failures.append(f"accountPermissionMatrix.{permission_id} keys must match permission schema")
            for key, expected_value in expected.items():
                if item.get(key) != expected_value:
                    failures.append(f"accountPermissionMatrix.{permission_id}.{key} must be {expected_value}")

    team_sync_matrix = actions.get("teamIdDriftSyncMatrix")
    if not isinstance(team_sync_matrix, list):
        failures.append("teamIdDriftSyncMatrix must be a list")
    else:
        by_id: dict[str, dict[str, Any]] = {}
        sync_ids: list[str] = []
        for item in team_sync_matrix:
            if not isinstance(item, dict):
                failures.append("teamIdDriftSyncMatrix entry must be an object")
                continue
            sync_id = item.get("id")
            if not isinstance(sync_id, str) or not sync_id:
                failures.append("teamIdDriftSyncMatrix entry missing id")
                continue
            sync_ids.append(sync_id)
            if sync_id in by_id:
                failures.append(f"teamIdDriftSyncMatrix duplicate id {sync_id}")
                continue
            by_id[sync_id] = item
        if tuple(sync_ids) != DUNS_ACTIONS_REQUIRED_TEAM_SYNC_IDS:
            failures.append("teamIdDriftSyncMatrix order must match Team ID propagation order")
        for sync_id, markers in DUNS_ACTIONS_REQUIRED_TEAM_SYNC_MATRIX.items():
            item = by_id.get(sync_id)
            if not item:
                failures.append(f"teamIdDriftSyncMatrix missing {sync_id}")
                continue
            for key, expected_value in DUNS_ACTIONS_REQUIRED_TEAM_SYNC_EXACT_VALUES.get(sync_id, {}).items():
                if item.get(key) != expected_value:
                    failures.append(f"teamIdDriftSyncMatrix.{sync_id}.{key} must be {expected_value}")
            item_text = json.dumps(item, ensure_ascii=False)
            for marker in markers:
                if marker not in item_text:
                    failures.append(f"teamIdDriftSyncMatrix.{sync_id} missing {marker}")

    capability_matrix = actions.get("capabilitySigningMatrix")
    if not isinstance(capability_matrix, list):
        failures.append("capabilitySigningMatrix must be a list")
    else:
        by_id: dict[str, dict[str, Any]] = {}
        capability_ids: list[str] = []
        for item in capability_matrix:
            if not isinstance(item, dict):
                failures.append("capabilitySigningMatrix entry must be an object")
                continue
            capability_id = item.get("id")
            if not isinstance(capability_id, str) or not capability_id:
                failures.append("capabilitySigningMatrix entry missing id")
                continue
            capability_ids.append(capability_id)
            if capability_id in by_id:
                failures.append(f"capabilitySigningMatrix duplicate id {capability_id}")
                continue
            by_id[capability_id] = item
        if tuple(capability_ids) != DUNS_ACTIONS_REQUIRED_CAPABILITY_SIGNING_IDS:
            failures.append("capabilitySigningMatrix order must match Bundle ID -> entitlements -> signing workflow")
        for capability_id, expected in DUNS_ACTIONS_REQUIRED_CAPABILITY_SIGNING_MATRIX.items():
            item = by_id.get(capability_id)
            if not item:
                failures.append(f"capabilitySigningMatrix missing {capability_id}")
                continue
            expected_keys = ("id", *expected.keys())
            if tuple(item) != expected_keys:
                failures.append(f"capabilitySigningMatrix.{capability_id} keys must match capability/signing schema")
            for key, expected_value in expected.items():
                if item.get(key) != expected_value:
                    failures.append(f"capabilitySigningMatrix.{capability_id}.{key} must be {expected_value}")

    milestone_matrix = actions.get("postDeliveryMilestoneGateMatrix")
    if not isinstance(milestone_matrix, list):
        failures.append("postDeliveryMilestoneGateMatrix must be a list")
    else:
        by_id: dict[str, dict[str, Any]] = {}
        milestone_ids: list[str] = []
        for item in milestone_matrix:
            if not isinstance(item, dict):
                failures.append("postDeliveryMilestoneGateMatrix entry must be an object")
                continue
            milestone_id = item.get("id")
            if not isinstance(milestone_id, str) or not milestone_id:
                failures.append("postDeliveryMilestoneGateMatrix entry missing id")
                continue
            milestone_ids.append(milestone_id)
            if milestone_id in by_id:
                failures.append(f"postDeliveryMilestoneGateMatrix duplicate id {milestone_id}")
                continue
            by_id[milestone_id] = item
        if tuple(milestone_ids) != DUNS_ACTIONS_REQUIRED_MILESTONE_GATE_IDS:
            failures.append("postDeliveryMilestoneGateMatrix order must match D-U-N-S -> Apple Developer -> Archive -> TestFlight exit gates")
        for milestone_id, expected in DUNS_ACTIONS_REQUIRED_MILESTONE_GATE_MATRIX.items():
            item = by_id.get(milestone_id)
            if not item:
                failures.append(f"postDeliveryMilestoneGateMatrix missing {milestone_id}")
                continue
            expected_keys = ("id", *expected.keys())
            if tuple(item) != expected_keys:
                failures.append(f"postDeliveryMilestoneGateMatrix.{milestone_id} keys must match milestone schema")
            for key, expected_value in expected.items():
                if item.get(key) != expected_value:
                    failures.append(f"postDeliveryMilestoneGateMatrix.{milestone_id}.{key} must be {expected_value}")

    sequence = actions.get("actionSequence")
    if not isinstance(sequence, list):
        failures.append("actionSequence must be a list")
    else:
        sequence_ids: list[str] = []
        seen_sequence_ids: set[str] = set()
        for item in sequence:
            if not isinstance(item, dict):
                failures.append("actionSequence entry must be an object")
                continue
            sequence_id = item.get("id")
            if not isinstance(sequence_id, str) or not sequence_id:
                failures.append("actionSequence entry missing id")
                continue
            if sequence_id in seen_sequence_ids:
                failures.append(f"actionSequence duplicate id {sequence_id}")
            seen_sequence_ids.add(sequence_id)
            sequence_ids.append(sequence_id)
        if tuple(sequence_ids) != DUNS_ACTIONS_REQUIRED_SEQUENCE_IDS:
            failures.append("actionSequence order must match D-U-N-S -> Team ID -> signing -> Archive -> TestFlight -> iOS 26.5 regression")
        sequence_text = json.dumps(sequence, ensure_ascii=False)
        for marker in (
            "Organization enrollment",
            "Team ID",
            "AppleDeveloper/16-account-roles-access.png",
            "com.mewpow.xiaonaiping",
            "com.mewpow.xiaonaiping.widgets",
            "group.com.mewpow.xiaonaiping.shared",
            "applinks:api.mewpow.com",
            "XNP_WECHAT_APP_ID",
            "XNP_WECHAT_URL_SCHEME",
            "XNP_WECHAT_UNIVERSAL_LINK",
            "prepare_wechat_release_env.py",
            "/tmp/xnp-wechat-release.env",
            'XNP_WECHAT_APP_ID=\\"$XNP_WECHAT_APP_ID\\"',
            'XNP_WECHAT_URL_SCHEME=\\"$XNP_WECHAT_URL_SCHEME\\"',
            'XNP_WECHAT_UNIVERSAL_LINK=\\"$XNP_WECHAT_UNIVERSAL_LINK\\"',
            "App Store Distribution",
            ". /tmp/xnp-wechat-release.env && xcodebuild",
            "xcodebuild -exportArchive",
            "method=app-store-connect",
            "destination=upload",
            "teamID=<confirmed Apple Developer Team ID>",
            "testFlightInternalTestingOnly=false",
            "iOS 26.5",
            "RD-01 到 RD-24",
        ):
            if marker not in sequence_text:
                failures.append(f"actionSequence missing {marker}")

    redaction_text = "\n".join(str(item) for item in actions.get("redactionChecklist", []))
    for marker in DUNS_ACTIONS_REQUIRED_REDACTION_MARKERS:
        if marker not in redaction_text:
            failures.append(f"redactionChecklist missing {marker}")

    stop_conditions = actions.get("stopConditions")
    if not isinstance(stop_conditions, list):
        failures.append("stopConditions must be a list")
    else:
        by_id: dict[str, dict[str, Any]] = {}
        for item in stop_conditions:
            if not isinstance(item, dict):
                failures.append("stopConditions entry must be an object")
                continue
            stop_id = item.get("id")
            if not isinstance(stop_id, str) or not stop_id:
                failures.append("stopConditions entry missing id")
                continue
            if stop_id in by_id:
                failures.append(f"stopConditions duplicate id {stop_id}")
                continue
            by_id[stop_id] = item
        for stop_id, markers in DUNS_ACTIONS_REQUIRED_STOP_CONDITIONS.items():
            item = by_id.get(stop_id)
            if not item:
                failures.append(f"stopConditions missing {stop_id}")
                continue
            item_text = json.dumps(item, ensure_ascii=False)
            for marker in markers:
                if marker not in item_text:
                    failures.append(f"stopConditions.{stop_id} missing {marker}")

    post_archive_text = "\n".join(str(item) for item in actions.get("postArchiveChecks", []))
    for command in DUNS_ACTIONS_REQUIRED_POST_ARCHIVE_COMMANDS:
        if command not in post_archive_text:
            failures.append(f"postArchiveChecks missing {command}")

    completion_rule = str(actions.get("completionRule", ""))
    for marker in (
        "action plan only",
        "does not prove D-U-N-S delivery",
        "does not prove Archive",
        "does not prove TestFlight",
        "real target evidence files exist",
        "same-round proof checks pass",
    ):
        if marker not in completion_rule:
            failures.append(f"completionRule missing {marker}")

    if actions.get("canSubmitFromThisPacket") is not False:
        failures.append("canSubmitFromThisPacket must be false")
    secret_hits = [
        marker for marker in ("sk-", "Bearer ", "debug_wechat_", "XNP_REVIEW_RECOVERY_KEY=")
        if marker in json.dumps(actions, ensure_ascii=False)
    ]
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    packet = read_text(root / args.submission_packet)
    bundle_verification = read_text(root / args.bundle_verification)
    runbook = read_text(root / args.runbook)
    evidence_readme = read_text(root / args.evidence_readme)
    capture_guide = read_text(root / args.capture_guide)
    duns_handoff = read_text(root / args.duns_handoff)
    duns_post_delivery_actions = read_json(root / args.duns_post_delivery_actions)
    metadata = read_text(root / args.metadata)
    mainland_filing = read_text(root / args.mainland_filing)
    privacy_page = read_text(root / args.privacy_page)
    terms_page = read_text(root / args.terms_page)
    support_page = read_text(root / args.support_page)
    export_options = read_plist(root / args.export_options_plist)
    team_signing_template = read_json(root / args.team_signing_template)
    external_status_poll_template = read_json(root / args.external_status_poll_template)
    duns_post_delivery_execution_template = read_json(root / args.duns_post_delivery_execution_template)
    org_signing_result_template = read_json(root / args.org_signing_result_template)
    project_signing_text = read_text(root / args.project_yml) + "\n" + read_text(root / args.pbxproj)
    report = Report()

    report.add("submissionPacketPresent", bool(packet), args.submission_packet if packet else "missing submission packet")
    report.add("bundleVerificationPresent", bool(bundle_verification), args.bundle_verification if bundle_verification else "missing bundle verification doc")
    report.add("chinaRunbookPresent", bool(runbook), args.runbook if runbook else "missing China mainland runbook")
    report.add("evidenceReadmePresent", bool(evidence_readme), args.evidence_readme if evidence_readme else "missing AppStoreEvidence README")
    report.add("captureGuidePresent", bool(capture_guide), args.capture_guide if capture_guide else "missing capture guide")
    report.add("dunsHandoffPresent", bool(duns_handoff), args.duns_handoff if duns_handoff else "missing D-U-N-S handoff doc")
    report.add(
        "dunsPostDeliveryActionsPresent",
        bool(duns_post_delivery_actions),
        args.duns_post_delivery_actions if duns_post_delivery_actions else "missing or invalid D-U-N-S post-delivery action packet",
    )
    report.add("exportOptionsPlistPresent", bool(export_options), args.export_options_plist if export_options else "missing or invalid ExportOptions plist")
    report.add("appleDeveloperTeamSigningTemplatePresent", bool(team_signing_template), args.team_signing_template if team_signing_template else "missing or invalid Apple Developer team signing template")
    report.add(
        "appleDeveloperExternalStatusPollTemplatePresent",
        bool(external_status_poll_template),
        args.external_status_poll_template
        if external_status_poll_template
        else "missing or invalid Apple Developer external status poll template",
    )
    report.add(
        "appleDeveloperDunsPostDeliveryExecutionTemplatePresent",
        bool(duns_post_delivery_execution_template),
        args.duns_post_delivery_execution_template
        if duns_post_delivery_execution_template
        else "missing or invalid D-U-N-S post-delivery execution result template",
    )
    report.add(
        "appleDeveloperOrgSigningResultTemplatePresent",
        bool(org_signing_result_template),
        args.org_signing_result_template
        if org_signing_result_template
        else "missing or invalid Apple Developer org signing result template",
    )

    signing_section = extract_section(packet, "Signing and Archive Status")
    missing_signing = missing_markers(packet, SIGNING_SECTION_MARKERS)
    report.add(
        "signingArchiveStatusDocumentsCurrentBlocker",
        bool(signing_section) and not missing_signing,
        "missing: " + ", ".join(missing_signing)
        if missing_signing
        else "submission packet documents archive command and current signing blocker",
    )

    missing_project_signing = missing_markers(project_signing_text, PROJECT_SIGNING_MARKERS)
    report.add(
        "projectSigningConfigurationWired",
        not missing_project_signing,
        "missing: " + ", ".join(missing_project_signing)
        if missing_project_signing
        else "project.yml and Xcode project wire Development Team, automatic signing, and Release entitlements",
    )

    duns_handoff_text = duns_handoff + "\n" + packet + "\n" + runbook + "\n" + evidence_readme
    missing_duns_handoff = missing_markers(duns_handoff_text, DUNS_HANDOFF_MARKERS)
    report.add(
        "dunsAppleDeveloperHandoffReady",
        bool(duns_handoff) and not missing_duns_handoff,
        "missing: " + ", ".join(missing_duns_handoff)
        if missing_duns_handoff
        else "D-U-N-S handoff covers Apple Developer organization enrollment, Team ID drift, certificates, Archive, TestFlight, and redaction boundaries",
    )
    duns_actions_problems = duns_post_delivery_actions_failures(duns_post_delivery_actions)
    report.add(
        "dunsPostDeliveryActionsValid",
        not duns_actions_problems,
        "; ".join(duns_actions_problems)
        if duns_actions_problems
        else "D-U-N-S post-delivery action packet covers Organization enrollment, Team ID, account permissions, capabilities, Team ID drift, WeChat release values, distribution signing, Archive, TestFlight, stop conditions, post-archive gates, iOS 26.5 regression, redaction, and non-evidence boundaries",
    )
    missing_confirmed_team_id_export_markers = missing_markers(duns_handoff, CONFIRMED_TEAM_ID_EXPORT_MARKERS)
    stale_hardcoded_team_id_export_markers = [
        marker for marker in STALE_HARDCODED_TEAM_ID_EXPORT_MARKERS if marker in duns_handoff
    ]
    confirmed_team_id_evidence = []
    if missing_confirmed_team_id_export_markers:
        confirmed_team_id_evidence.append("missing: " + ", ".join(missing_confirmed_team_id_export_markers))
    if stale_hardcoded_team_id_export_markers:
        confirmed_team_id_evidence.append("stale: " + ", ".join(stale_hardcoded_team_id_export_markers))
    report.add(
        "dunsExportOptionsUsesConfirmedTeamId",
        bool(duns_handoff)
        and not missing_confirmed_team_id_export_markers
        and not stale_hardcoded_team_id_export_markers,
        "; ".join(confirmed_team_id_evidence)
        if confirmed_team_id_evidence
        else "D-U-N-S handoff requires ExportOptions teamID to use the confirmed Apple Developer Team ID and treats L2TYJNDTJK as reusable only after Apple confirms the same Team ID",
    )

    duns_evidence_filename_text = duns_handoff + "\n" + evidence_readme + "\n" + capture_guide
    missing_duns_evidence_filenames = missing_markers(
        duns_evidence_filename_text,
        DUNS_EVIDENCE_FILENAME_MARKERS,
    )
    report.add(
        "dunsAppleDeveloperEvidenceFilenamesPresent",
        not missing_duns_evidence_filenames,
        "missing: " + ", ".join(missing_duns_evidence_filenames)
        if missing_duns_evidence_filenames
        else "D-U-N-S follow-up has stable Apple Developer evidence filenames for Team ID, Bundle ID capabilities, and distribution certificate/profile",
    )
    legal_entity_text = "\n".join(
        [
            duns_handoff,
            packet,
            runbook,
            evidence_readme,
            capture_guide,
            metadata,
            mainland_filing,
            privacy_page,
            terms_page,
            support_page,
        ]
    )
    missing_legal_entity_markers = missing_markers(
        legal_entity_text,
        DUNS_LEGAL_ENTITY_CONSISTENCY_MARKERS,
    )
    legal_entity_sources = {
        args.duns_handoff: duns_handoff,
        args.submission_packet: packet,
        args.runbook: runbook,
        args.evidence_readme: evidence_readme,
        args.capture_guide: capture_guide,
        args.metadata: metadata,
        args.mainland_filing: mainland_filing,
        args.privacy_page: privacy_page,
        args.terms_page: terms_page,
        args.support_page: support_page,
    }
    missing_legal_entity_sources = [
        path for path, text in legal_entity_sources.items() if EXPECTED_LEGAL_ENTITY not in text
    ]
    report.add(
        "dunsLegalEntityConsistencyLockPresent",
        bool(duns_handoff)
        and not missing_legal_entity_markers
        and not missing_legal_entity_sources,
        "missingMarkers: "
        + ", ".join(missing_legal_entity_markers)
        + "; missingEntityIn: "
        + ", ".join(missing_legal_entity_sources)
        if missing_legal_entity_markers or missing_legal_entity_sources
        else "D-U-N-S handoff locks Apple Developer organization, App Store metadata, filing materials, submission packet, evidence checklist, and public legal pages to the same company entity",
    )
    contact_identity_text = duns_handoff + "\n" + packet + "\n" + runbook
    missing_contact_identity_markers = missing_markers(contact_identity_text, DUNS_CONTACT_IDENTITY_MARKERS)
    stale_contact_scan_text = (
        contact_identity_text
        .replace("不能使用余鹏辉", "")
        .replace("不能使用 Penghui Yu", "")
    )
    stale_contact_identity_hits = [
        marker for marker in STALE_CONTACT_IDENTITY_MARKERS if marker in stale_contact_scan_text
    ]
    contact_identity_evidence = []
    if missing_contact_identity_markers:
        contact_identity_evidence.append("missing: " + ", ".join(missing_contact_identity_markers))
    if stale_contact_identity_hits:
        contact_identity_evidence.append("stale: " + ", ".join(stale_contact_identity_hits))
    report.add(
        "dunsContactIdentityLockPresent",
        bool(duns_handoff)
        and not missing_contact_identity_markers
        and not stale_contact_identity_hits,
        "; ".join(contact_identity_evidence)
        if contact_identity_evidence
        else "D-U-N-S handoff locks Apple Developer contact identity to 佘鹏辉 / Penghui She and blocks stale Penghui Yu spelling",
    )
    account_access_text = duns_handoff + "\n" + evidence_readme + "\n" + capture_guide + "\n" + runbook
    missing_account_access_lock = missing_markers(
        account_access_text,
        APPLE_DEVELOPER_ACCOUNT_ACCESS_LOCK_MARKERS,
    )
    report.add(
        "appleDeveloperAccountAccessLockPresent",
        bool(duns_handoff) and not missing_account_access_lock,
        "missing: " + ", ".join(missing_account_access_lock)
        if missing_account_access_lock
        else "D-U-N-S follow-up requires Apple Developer/App Store Connect account access evidence before certificates, Archive, TestFlight, or submit-review work",
    )
    duns_wechat_aasa_text = duns_handoff + "\n" + evidence_readme + "\n" + capture_guide
    missing_duns_wechat_aasa_markers = missing_markers(
        duns_wechat_aasa_text,
        DUNS_WECHAT_AASA_SYNC_MARKERS,
    )
    report.add(
        "dunsTeamIdWechatAasaSyncCovered",
        not missing_duns_wechat_aasa_markers,
        "missing: " + ", ".join(missing_duns_wechat_aasa_markers)
        if missing_duns_wechat_aasa_markers
        else "D-U-N-S handoff ties Team ID drift to WeChat Universal Link/AASA evidence and provider material gate",
    )

    missing_team_id_matrix_markers = missing_markers(duns_handoff, TEAM_ID_PROPAGATION_MATRIX_MARKERS)
    report.add(
        "dunsTeamIdPropagationMatrixPresent",
        bool(duns_handoff) and not missing_team_id_matrix_markers,
        "missing: " + ", ".join(missing_team_id_matrix_markers)
        if missing_team_id_matrix_markers
        else "D-U-N-S handoff has a Team ID drift matrix covering files, fields, evidence, and required gates",
    )
    missing_team_id_pre_export_markers = missing_markers(duns_handoff, TEAM_ID_PRE_EXPORT_CONSISTENCY_MARKERS)
    report.add(
        "dunsTeamIdPreExportConsistencyLockPresent",
        bool(duns_handoff) and not missing_team_id_pre_export_markers,
        "missing: " + ", ".join(missing_team_id_pre_export_markers)
        if missing_team_id_pre_export_markers
        else "D-U-N-S handoff blocks exportArchive until Apple Developer Team ID, project signing, ExportOptions, AASA, and proof outputs agree",
    )

    missing_archive_execution_template = missing_markers(
        duns_handoff,
        ARCHIVE_TESTFLIGHT_EXECUTION_TEMPLATE_MARKERS,
    )
    report.add(
        "archiveTestFlightExecutionRecordTemplatePresent",
        bool(duns_handoff) and not missing_archive_execution_template,
        "missing: " + ", ".join(missing_archive_execution_template)
        if missing_archive_execution_template
        else "D-U-N-S handoff has an Archive/TestFlight same-day execution template covering account, Team ID drift, real WeChat Release values, export/upload evidence, and redaction",
    )
    missing_apple_developer_page_evidence = missing_markers(
        duns_handoff,
        APPLE_DEVELOPER_PAGE_EVIDENCE_INDEX_MARKERS,
    )
    report.add(
        "appleDeveloperPageEvidenceIndexPresent",
        bool(duns_handoff) and not missing_apple_developer_page_evidence,
        "missing: " + ", ".join(missing_apple_developer_page_evidence)
        if missing_apple_developer_page_evidence
        else "D-U-N-S handoff indexes Apple Developer, Archive, TestFlight, AASA, and iOS 26.5 regression page evidence with keep/redact fields and rerun gates",
    )

    team_signing_template_problems = team_signing_template_failures(team_signing_template)
    report.add(
        "appleDeveloperTeamSigningTemplateValid",
        not team_signing_template_problems,
        "; ".join(team_signing_template_problems)
        if team_signing_template_problems
        else "Apple Developer team signing template covers target evidence files, Team ID consistency, capabilities, archive/TestFlight checks, redaction, post-capture gates, and template-only completion boundary",
    )
    external_status_poll_template_problems = external_status_poll_template_failures(external_status_poll_template)
    report.add(
        "appleDeveloperExternalStatusPollTemplateValid",
        not external_status_poll_template_problems,
        "; ".join(external_status_poll_template_problems)
        if external_status_poll_template_problems
        else "Apple Developer external status poll template covers D&B, Apple Developer enrollment, Apple email, App Store Connect drafts, switch criteria, redaction boundaries, and XiaoNaiPing local proof refresh without becoming submission permission",
    )
    duns_post_delivery_execution_template_problems = duns_post_delivery_execution_template_failures(duns_post_delivery_execution_template)
    report.add(
        "appleDeveloperDunsPostDeliveryExecutionTemplateValid",
        not duns_post_delivery_execution_template_problems,
        "; ".join(duns_post_delivery_execution_template_problems)
        if duns_post_delivery_execution_template_problems
        else "D-U-N-S post-delivery execution result template locks first-hour Apple Developer continuation, evidence files, redaction placeholders, same-round reruns, XiaoNaiPing proof boundaries, and no-submit status",
    )
    org_signing_result_template_problems = org_signing_result_template_failures(org_signing_result_template)
    report.add(
        "appleDeveloperOrgSigningResultTemplateValid",
        not org_signing_result_template_problems,
        "; ".join(org_signing_result_template_problems)
        if org_signing_result_template_problems
        else "Apple Developer org signing result template indexes D-U-N-S delivery, organization enrollment, payment, Team context, certificate/profile, Archive, TestFlight, AASA, XiaoNaiPing required proofs, historical cross-app boundary, and redaction fields without becoming evidence or submission permission",
    )

    export_options_failures_found = export_options_failures(export_options)
    report.add(
        "appStoreConnectExportOptionsPlistValid",
        not export_options_failures_found,
        "; ".join(export_options_failures_found)
        if export_options_failures_found
        else "ExportOptions plist is configured for App Store Connect upload, automatic signing, current Team ID, stable bundle id, symbol upload, and non-internal-only TestFlight distribution",
    )

    export_plan_text = duns_handoff + "\n" + packet + "\n" + runbook
    missing_export_plan_markers = missing_markers(export_plan_text, EXPORT_OPTIONS_MARKERS)
    report.add(
        "archiveExportUploadPlanPresent",
        bool(export_plan_text) and not missing_export_plan_markers,
        "missing: " + ", ".join(missing_export_plan_markers)
        if missing_export_plan_markers
        else "materials document xcodebuild exportArchive/upload command, ExportOptions path and key boundaries, and secret redaction",
    )

    post_archive_text = bundle_verification + "\n" + runbook + "\n" + packet
    missing_post_archive = missing_markers(post_archive_text, POST_ARCHIVE_VERIFICATION_MARKERS)
    report.add(
        "postArchiveBundleVerificationRequired",
        not missing_post_archive,
        "missing: " + ", ".join(missing_post_archive)
        if missing_post_archive
        else "post-archive flow requires iOS 26.5 bundle proof and exported .app scanning",
    )

    evidence_text = evidence_readme + "\n" + capture_guide + "\n" + runbook
    missing_evidence_names = missing_markers(evidence_text, EVIDENCE_FILENAME_MARKERS)
    report.add(
        "signedArchiveAndTestFlightEvidenceFilenamesPresent",
        not missing_evidence_names,
        "missing: " + ", ".join(missing_evidence_names)
        if missing_evidence_names
        else "05-signed-archive and 06-testflight evidence filenames are documented",
    )

    missing_capture_markers = missing_markers(capture_guide, CAPTURE_GUIDE_MARKERS)
    report.add(
        "signedArchiveAndTestFlightEvidenceRedactionCovered",
        not missing_capture_markers,
        "missing: " + ", ".join(missing_capture_markers)
        if missing_capture_markers
        else "capture guide covers archive/TestFlight status fields and redaction boundaries",
    )

    boundary_text = packet + "\n" + bundle_verification + "\n" + evidence_readme
    missing_testflight_boundary = missing_markers(boundary_text, TESTFLIGHT_BOUNDARY_MARKERS)
    report.add(
        "testFlightEvidenceBoundaryPresent",
        not missing_testflight_boundary,
        "missing: " + ", ".join(missing_testflight_boundary)
        if missing_testflight_boundary
        else "materials keep TestFlight/signed-device screenshots and regression evidence separate from local simulator proof",
    )

    missing_commands = missing_markers(packet, PRE_SUBMIT_COMMAND_MARKERS)
    report.add(
        "preSubmitCommandsIncludeArchiveTestFlightGate",
        not missing_commands,
        "missing: " + ", ".join(missing_commands)
        if missing_commands
        else "submission packet pre-submit commands include archive/TestFlight material, bundle, client, regression, and evidence gates",
    )

    signed_evidence_present = archived_real_evidence_present(root, "05-signed-archive.png")
    testflight_evidence_present = archived_real_evidence_present(root, "06-testflight.png")
    pretend_hits = [
        marker
        for marker in FORBIDDEN_PRETEND_COMPLETE_MARKERS
        if marker in packet + "\n" + evidence_readme + "\n" + runbook
    ]
    report.add(
        "doesNotPretendArchiveOrTestFlightCompleteBeforeEvidence",
        (signed_evidence_present and testflight_evidence_present) or not pretend_hits,
        "completionClaims=" + ", ".join(pretend_hits)
        if pretend_hits
        else "materials do not claim signed archive/TestFlight is complete before archived evidence",
    )

    runtime_hits = stale_runtime_hits(packet + "\n" + bundle_verification + "\n" + runbook + "\n" + evidence_readme)
    report.add(
        "archiveTestFlightMaterialsAvoidStaleRuntimeClaims",
        not runtime_hits,
        "found: " + ", ".join(runtime_hits) if runtime_hits else "archive/TestFlight materials avoid stale iOS 18 or iOS 27 evidence claims",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--submission-packet", default=str(APP_STORE_SUBMISSION_PACKET))
    parser.add_argument("--bundle-verification", default=str(IOS_RELEASE_BUNDLE_VERIFICATION))
    parser.add_argument("--runbook", default=str(CHINA_MAINLAND_RUNBOOK))
    parser.add_argument("--evidence-readme", default=str(APP_STORE_EVIDENCE_README))
    parser.add_argument("--capture-guide", default=str(APP_STORE_EVIDENCE_CAPTURE_GUIDE))
    parser.add_argument("--duns-handoff", default=str(DUNS_HANDOFF))
    parser.add_argument("--duns-post-delivery-actions", default=str(DUNS_POST_DELIVERY_ACTIONS))
    parser.add_argument("--metadata", default=str(APP_STORE_METADATA))
    parser.add_argument("--mainland-filing", default=str(MAINLAND_FILING_MATERIALS))
    parser.add_argument("--privacy-page", default=str(PRIVACY_PAGE))
    parser.add_argument("--terms-page", default=str(TERMS_PAGE))
    parser.add_argument("--support-page", default=str(SUPPORT_PAGE))
    parser.add_argument("--export-options-plist", default=str(EXPORT_OPTIONS_PLIST))
    parser.add_argument("--team-signing-template", default=str(APPLE_DEVELOPER_TEAM_SIGNING_TEMPLATE))
    parser.add_argument("--external-status-poll-template", default=str(APPLE_DEVELOPER_EXTERNAL_STATUS_POLL_TEMPLATE))
    parser.add_argument(
        "--duns-post-delivery-execution-template",
        default=str(APPLE_DEVELOPER_DUNS_POST_DELIVERY_EXECUTION_TEMPLATE),
    )
    parser.add_argument("--org-signing-result-template", default=str(APPLE_DEVELOPER_ORG_SIGNING_RESULT_TEMPLATE))
    parser.add_argument("--project-yml", default=str(PROJECT_YML))
    parser.add_argument("--pbxproj", default=str(PBXPROJ))
    parser.add_argument("--output", default="Backend/proof/signed-archive-testflight-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"signed archive/TestFlight materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"signed archive/TestFlight materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
