#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")
DEFAULT_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".json"}
TEXT_EVIDENCE_EXTENSIONS = {".json", ".md", ".txt"}
REAL_DEVICE_EVIDENCE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".mp4", ".mov", ".pdf")
MIN_MANUAL_EVIDENCE_BYTES = 10 * 1024
REQUIRED_RD_IDS = {f"RD-{index:02d}" for index in range(1, 25)}
REQUIRED_REAL_DEVICE_ENV_FIELDS = ["设备", "iOS", "安装方式", "App 版本", "Build", "网络", "证据截图/录屏"]
REQUIRED_REAL_DEVICE_VISUAL_FIELDS = [
    "灵动岛紧凑态结论",
    "灵动岛展开态结论",
    "锁屏通知栈结论",
    "锁屏小组件结论",
    "桌面小组件结论",
]
REQUIRED_VISUAL_CONCLUSION_PATTERNS = {
    "灵动岛紧凑态结论": re.compile(r"(无裁剪|不裁剪|边缘完整|未右移|不右移|未压到岛中心|不压到岛中心)"),
    "灵动岛展开态结论": re.compile(r"(无裁剪|不裁剪|边缘完整|未贴边|不贴边|未被吞|不被吞)"),
    "锁屏通知栈结论": re.compile(r"(无裁剪|不裁剪|边缘完整|不遮挡|无遮挡)"),
    "锁屏小组件结论": re.compile(r"(无裁剪|不裁剪|无溢出|边缘完整|不展示隐私照片)"),
    "桌面小组件结论": re.compile(r"(无裁剪|不裁剪|无溢出|边缘完整|不展示隐私照片)"),
}
REQUIRED_VISUAL_RD_PATH_PATTERNS = {
    "RD-17": re.compile(r"(notification|permission|通知|权限)", re.IGNORECASE),
    "RD-18": re.compile(r"(?=.*(watch|apple-?watch))(?=.*(mirror|notification|镜像|通知))", re.IGNORECASE),
    "RD-22": re.compile(r"(?=.*(live-?activity|dynamic-?island|island|灵动岛))(?=.*(switch|toggle|开关|compact|expanded|紧凑|展开))", re.IGNORECASE),
    "RD-23": re.compile(r"(widget|小组件|lock-?screen|锁屏)", re.IGNORECASE),
    "RD-24": re.compile(r"(review|boundary|审核|边界)", re.IGNORECASE),
}
REQUIRED_AUTH_ACCOUNT_RD_PATH_PATTERNS = {
    "RD-10": re.compile(r"(recovery|恢复)", re.IGNORECASE),
    "RD-13": re.compile(r"(phone|sms|手机号|验证码)", re.IGNORECASE),
    "RD-14": re.compile(r"(wechat|微信)", re.IGNORECASE),
    "RD-15": re.compile(r"((account|账号).*(delete|删除)|(delete|删除).*(account|账号)|account-?delete)", re.IGNORECASE),
}
REQUIRED_FOCUSED_REAL_DEVICE_EVIDENCE_PATHS = {
    "recoveryLogin": "RealDevice/RD-10-recovery-login.png",
    "phoneLogin": "RealDevice/RD-13-phone-login.png",
    "wechatLogin": "RealDevice/RD-14-wechat-login.png",
    "accountDelete": "RealDevice/RD-15-account-delete.png",
    "notificationAllowed": "RealDevice/RD-17-notification-allowed.png",
    "notificationDenied": "RealDevice/RD-17-notification-denied.png",
    "dynamicIslandCompact": "RealDevice/RD-22-dynamic-island-compact.png",
    "dynamicIslandExpanded": "RealDevice/RD-22-dynamic-island-expanded.png",
    "lockScreenNotificationStack": "RealDevice/RD-23-lock-screen-notification-stack.png",
    "lockScreenWidgetSummary": "RealDevice/RD-23-lock-screen-widget-summary.png",
    "homeWidgetSummary": "RealDevice/RD-23-home-widget-summary.png",
}
PENDING_REAL_DEVICE_MARKERS = ("待测", "待填", "待真实", "TODO", "TBD")
APP_STORE_ASSETS_PROOF = Path("Backend/proof/app-store-assets.json")
MANUAL_EVIDENCE_CHECKLIST_TEMPLATE = "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_{date}.md"
MANUAL_EVIDENCE_PACKET_TEMPLATE = "Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_{date}.json"
REQUIRED_FINAL_SCREENSHOT_ASSET_CHECKS = [
    "finalScreenshotsCount",
    "finalScreenshotsExpectedUploadOrder",
    "finalScreenshotsAcceptedSizes",
    "finalScreenshotsIphone69SlotReady",
    "finalScreenshotsNotBlank",
    "finalScreenshotsNoRiskyFilenames",
    "finalScreenshotsIOS265ProvenancePresent",
    "finalScreenshotsUploadProvenanceTemplateValid",
    "finalScreenshotsUploadProvenancePresent",
]
TEMPLATE_REAL_DEVICE_MARKERS = (
    "复制本文件为 `12-real-device-regression.md` 后再填写",
    "12-real-device-regression.md Template",
)
FORBIDDEN_REAL_DEVICE_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
}

MANUAL_EVIDENCE_CHECKLIST_MARKERS = [
    "仍需补齐的人工证据",
    "真机回归必须覆盖",
    "RD 用例列表",
    "灵动岛 / 小组件 / Apple Watch 边界",
    "遮挡与脱敏规则",
    "当前不可替代项",
    "采集后必跑",
    "同轮人工证据索引模板",
    "同一天同一轮采集",
    "App 版本",
    "Build 号",
    "01-company-account.png 到 09-obs-policy.png、`08b-wechat-universal-link-aasa.png` 和 17-age-rating-result",
    "10-final-screenshots/",
    "12-real-device-regression.md",
    "每个文件已脱敏",
    "单个文件不低于 10KB",
    "App Store Connect 选中的 build 与 TestFlight / 12-real-device-regression.md 一致",
    "check_app_store_evidence.py --allow-incomplete",
    "production-readiness.json",
    "01-company-account.png",
    "02-mainland-availability.png",
    "03-app-filing.pdf",
    "03-app-filing.png",
    "04-privacy-label.png",
    "17-age-rating-result.png",
    "17-age-rating-result.pdf",
    "05-signed-archive.png",
    "06-testflight.png",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "08b-wechat-universal-link-aasa.png",
    "09-obs-policy.png",
    "10-final-screenshots/",
    "10-final-screenshots/UPLOAD_PROVENANCE.json",
    "final-app-store-upload",
    "iPhone 6.9",
    "TestFlight 或 Xcode 签名真机包最终截图",
    "01-home-iphone16pro.png",
    "02-record-iphone16pro.png",
    "03-growth-iphone16pro.png",
    "04-profile-iphone16pro.png",
    "05-profile-sync-iphone16pro.png",
    "11-test-account-redacted.json",
    "12-real-device-regression.md",
    "AppleDeveloper/16-account-roles-access.png",
    "证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限",
    "单个 RD 文件不低于 10KB",
    "iOS 26.5",
    "TestFlight",
    "Xcode 签名真机包",
    "灵动岛紧凑态结论",
    "灵动岛展开态结论",
    "锁屏通知栈结论",
    "锁屏小组件结论",
    "桌面小组件结论",
    "Apple Watch 只作为系统镜像通知",
    "不在 App Store 文案中承诺 Watch App",
    "RD-10、RD-13、RD-14、RD-15、RD-18、RD-22、RD-23、RD-24 不能复用总览图或同一份泛证据",
    "RD-10 恢复密钥登录必须使用独立证据文件",
    "RD-13 手机号登录必须使用独立证据文件",
    "RD-14 微信登录必须使用独立证据文件",
    "RD-15 账号删除必须使用独立证据文件",
    "RD-17 通知权限允许和拒绝必须使用独立证据文件",
    "RD-22 灵动岛紧凑态和展开态必须使用独立证据文件",
    "RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须使用独立证据文件",
    "RealDevice/RD-10-recovery-login.png",
    "RealDevice/RD-13-phone-login.png",
    "RealDevice/RD-14-wechat-login.png",
    "RealDevice/RD-15-account-delete.png",
    "RD-10 路径必须体现 recovery 或恢复",
    "RD-13 路径必须体现 phone、sms、手机号或验证码",
    "RD-14 路径必须体现 wechat 或微信",
    "RD-15 路径必须体现 account / delete 或账号 / 删除",
    "RD-17 路径必须体现 notification、permission、通知或权限",
    "RD-18 路径必须同时体现 watch 和 mirror / notification",
    "RD-22 路径必须体现 live-activity、dynamic-island、island 或灵动岛",
    "RD-22 路径必须体现 switch、toggle、开关、compact 或 expanded",
    "RD-23 代表路径必须体现 widget / 小组件或 lock-screen / 锁屏",
    "RealDevice/RD-17-notification-allowed.png",
    "RealDevice/RD-17-notification-denied.png",
    "RealDevice/RD-22-dynamic-island-compact.png",
    "RealDevice/RD-22-dynamic-island-expanded.png",
    "RealDevice/RD-23-lock-screen-notification-stack.png",
    "RealDevice/RD-23-lock-screen-widget-summary.png",
    "RealDevice/RD-23-home-widget-summary.png",
    "不生成健康建议、压力提醒、喂养建议或医疗判断",
    "不接入 HealthKit、传感器、医院系统或第三方健康数据源",
    "不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议",
]

MANUAL_EVIDENCE_PACKET_SOURCE_FILES = {
    "evidenceChecklist": "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_{date}.md",
    "captureGuide": "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
    "appStoreEvidenceReadme": "Docs/08_Release/AppStoreEvidence/README.md",
    "appStoreConnectExecutionSheet": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/EXECUTION_SHEET_{date}.md",
    "appStoreConnectEntrySessionPacket": "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_{date}.json",
    "externalPlatformCapturePacket": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_{date}.json",
    "finalScreenshotUploadPacket": "Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_{date}.json",
    "privacyLabel": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
    "ageRatingAnswers": "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{date}.md",
    "submissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
}
MANUAL_EVIDENCE_PACKET_TARGET_FILES = {
    "companyAccount": "Docs/08_Release/AppStoreEvidence/01-company-account.png",
    "mainlandAvailability": "Docs/08_Release/AppStoreEvidence/02-mainland-availability.png",
    "mainlandFiling": "Docs/08_Release/AppStoreEvidence/03-app-filing.png or .pdf",
    "privacyLabel": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png or .pdf",
    "ageRatingResult": "Docs/08_Release/AppStoreEvidence/17-age-rating-result.png or .pdf",
    "signedArchive": "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
    "testFlight": "Docs/08_Release/AppStoreEvidence/06-testflight.png",
    "appleDeveloperAccountAccess": "Docs/08_Release/AppStoreEvidence/AppleDeveloper/16-account-roles-access.png",
    "smsProvider": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
    "wechatOpenPlatform": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
    "wechatUniversalLinkAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
    "huaweiObsPolicy": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
    "appStoreConnectAppInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-01-app-information.png",
    "appStoreConnectVersionInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-02-version-information.png",
    "appStoreConnectPricingAvailabilityRelease": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-03-pricing-availability-release.png",
    "appStoreConnectAppPrivacy": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-04-app-privacy.png",
    "appStoreConnectAgeRating": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-05-age-rating.png",
    "appStoreConnectReviewInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-06-review-information.png",
    "appStoreConnectBuildTestflightLink": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-07-build-testflight-link.png",
    "appStoreConnectSubmitReviewPrecheck": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-08-submit-review-precheck.png",
    "finalScreenshotUploadProvenance": "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
    "realDeviceRegression": "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
}
MANUAL_EVIDENCE_PACKET_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameRoundAsManualEvidencePacket": False,
    "sourceIsAllowedEvidenceRoot": False,
    "realEvidenceNotTemplate": False,
    "secretValuesNotRecorded": False,
}
MANUAL_EVIDENCE_PACKET_DEPENDENCY_FIELDS = (
    "artifactId",
    "target",
    "proves",
    "doesNotProve",
    "requiredBeforeSubmit",
    "initialStatus",
)
MANUAL_EVIDENCE_PACKET_DEPENDENCY_MATRIX = {
    "companyAccount": {
        "proves": ["Apple Developer company enrollment target", "App Store Connect organization account context"],
        "doesNotProve": ["D-U-N-S delivery is complete", "production build is signed", "mainland filing is complete"],
    },
    "mainlandAvailability": {
        "proves": ["China mainland availability selection", "manual release availability boundary"],
        "doesNotProve": ["ICP/App filing number exists", "production API is ready", "review approval is granted"],
    },
    "mainlandFiling": {
        "proves": ["mainland filing submission, receipt, number, or applicability decision", "filing material is tied to XiaoNaiPing"],
        "doesNotProve": ["public security filing is complete", "App Store review can be submitted", "production evidence is ready"],
    },
    "privacyLabel": {
        "proves": ["App Store privacy label entry matches APP_STORE_PRIVACY_LABEL.json", "tracking remains disabled"],
        "doesNotProve": ["privacy policy URL is reachable", "public legal pages are current", "age rating is complete"],
    },
    "ageRatingResult": {
        "proves": ["App Store age rating answers were entered", "medical and Kids Category answers stay within release boundary"],
        "doesNotProve": ["privacy label is complete", "review notes are complete", "China mainland availability is enabled"],
    },
    "signedArchive": {
        "proves": ["signed App Store archive exists for the release build", "archive can be tied to the release version and build"],
        "doesNotProve": ["TestFlight processing is complete", "real-device regression passed", "App Store Connect build is selected"],
    },
    "testFlight": {
        "proves": ["TestFlight build is processed or available", "release build is visible in Apple's distribution flow"],
        "doesNotProve": ["same-build real-device regression passed", "final screenshots are uploaded", "Submit for Review is allowed"],
    },
    "appleDeveloperAccountAccess": {
        "proves": ["Apple Developer role/access page was captured", "operator has the account access evidence required for release"],
        "doesNotProve": ["company enrollment is finalized", "certificates and profiles are valid", "App Store Connect metadata is complete"],
    },
    "smsProvider": {
        "proves": ["SMS provider console/configuration evidence exists", "phone-login provider is ready for manual review capture"],
        "doesNotProve": ["live SMS send proof passed", "auth provider proof is green", "test account login succeeded"],
    },
    "wechatOpenPlatform": {
        "proves": ["WeChat Open Platform app configuration evidence exists", "iOS bundle and Universal Link fields can be inspected"],
        "doesNotProve": ["server AppSecret is configured", "Universal Link AASA is reachable", "real-device WeChat login passed"],
    },
    "wechatUniversalLinkAasa": {
        "proves": ["WeChat Universal Link AASA evidence exists", "associated domain response can be inspected"],
        "doesNotProve": ["WeChat Open Platform credentials are correct", "iOS entitlement build is signed", "RD-14 WeChat login passed"],
    },
    "huaweiObsPolicy": {
        "proves": ["Huawei OBS bucket or policy evidence exists", "object storage access posture was captured"],
        "doesNotProve": ["storage-backend proof is green", "sync/restore passed on device", "production readiness is green"],
    },
    "appStoreConnectAppInformation": {
        "proves": ["App Store Connect app information page was entered", "name, subtitle, category, and policy URLs can be reviewed"],
        "doesNotProve": ["version information is complete", "privacy questionnaire is complete", "Submit for Review is allowed"],
    },
    "appStoreConnectVersionInformation": {
        "proves": ["App Store Connect version metadata was entered", "release notes and description can be reviewed"],
        "doesNotProve": ["build is selected", "availability is correct", "review information is complete"],
    },
    "appStoreConnectPricingAvailabilityRelease": {
        "proves": ["pricing, availability, and release setting page was entered", "China mainland and manual release selection can be reviewed"],
        "doesNotProve": ["filing is complete", "build is selected", "App Review information is complete"],
    },
    "appStoreConnectAppPrivacy": {
        "proves": ["App Store Connect App Privacy page was entered", "privacy answers can be compared with the frozen label"],
        "doesNotProve": ["public privacy policy is reachable", "age rating is complete", "all external evidence is captured"],
    },
    "appStoreConnectAgeRating": {
        "proves": ["App Store Connect age rating page was entered", "age-rating result can be checked against the answer sheet"],
        "doesNotProve": ["privacy label is complete", "review notes are complete", "mainland availability is enabled"],
    },
    "appStoreConnectReviewInformation": {
        "proves": ["review contact, notes, and test account page was entered", "reviewer-facing access notes can be inspected"],
        "doesNotProve": ["test account login passed", "real-device regression passed", "Submit for Review has no warnings"],
    },
    "appStoreConnectBuildTestflightLink": {
        "proves": ["App Store Connect version is linked to a build or TestFlight build context", "selected build can be compared with other same-build evidence"],
        "doesNotProve": ["signed archive was produced locally", "final screenshots are uploaded", "real-device regression passed"],
    },
    "appStoreConnectSubmitReviewPrecheck": {
        "proves": ["Submit for Review precheck page was reached", "remaining App Store Connect warnings can be captured before submission"],
        "doesNotProve": ["review was submitted", "production readiness is green", "external provider evidence is complete"],
    },
    "finalScreenshotUploadProvenance": {
        "proves": ["final screenshot upload provenance is recorded", "screenshots are tied to version, build, runtime, and capture round"],
        "doesNotProve": ["screenshots are already accepted by Apple", "TestFlight build is processed", "real-device regression passed"],
    },
    "realDeviceRegression": {
        "proves": ["iOS 26.5 real-device regression record exists", "manual RD cases are tied to the same release evidence round"],
        "doesNotProve": ["TestFlight processing is complete", "App Store Connect metadata is complete", "Submit for Review is allowed"],
    },
}
MANUAL_EVIDENCE_PACKET_MARKERS = [
    "sameDaySameRoundRequired",
    "realEvidenceOnly",
    "noTemplateAsEvidence",
    "evidenceFileChecks",
    "evidenceDependencyMatrix",
    "requiredBeforeSubmit",
    "file size",
    "SHA-256",
    "redaction",
    "same-round capture",
    "allowed evidence root",
    "real-evidence-not-template",
    "secret-values-not-recorded",
    "iOS26.5OnlyForLocalProof",
    "sameBuildForTestFlightFinalScreenshotsAndRealDeviceRegression",
    "canSubmitFalseUntilProductionReadinessAndLaunchAuditReady",
    "App Store Connect 真实页面",
    "不写占位备案号",
    "不把 Debug simulator 候选截图当最终上传证据",
    "不把模板、执行包或 Markdown 当证据",
    "不声称微信、短信、OBS、TestFlight、签名归档或真机回归已完成",
    "check_app_store_assets.py",
    "check_app_store_evidence.py",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
    "manual-evidence-plan-not-evidence",
    "not submission permission",
    "app-store-evidence.json ready=true",
    "production-readiness.json ready=true",
    "launch-objective-audit.json ready=true",
]
CAPTURE_GUIDANCE_MARKERS = {
    "captureGuide": {
        "path": "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
        "markers": [
            "锁屏小组件视觉结论",
            "锁屏小组件要证明 accessoryCircular / accessoryRectangular / accessoryInline",
            "RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须拆成",
            "RealDevice/RD-23-lock-screen-notification-stack.png",
            "RealDevice/RD-23-lock-screen-widget-summary.png",
            "RealDevice/RD-23-home-widget-summary.png",
        ],
    },
    "appStoreEvidenceReadme": {
        "path": "Docs/08_Release/AppStoreEvidence/README.md",
        "markers": [
            "锁屏小组件视觉结论",
            "RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须使用独立证据文件",
            "RealDevice/RD-23-lock-screen-notification-stack.png",
            "RealDevice/RD-23-lock-screen-widget-summary.png",
            "RealDevice/RD-23-home-widget-summary.png",
            "锁屏小组件内容不裁剪不展示隐私照片",
            "Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_{date}.json",
            "RealDevice/FOCUSED_CAPTURE_PACKET_{date}.json",
            "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date {display_date} --output Backend/proof/app-store-evidence-{date}T-current.json",
        ],
    },
}

REQUIRED_EVIDENCE = {
    "companyAccount": {
        "patterns": ["01-company-account.*"],
        "description": "深圳市闪现生活科技有限公司 App Store Connect 主体证据",
    },
    "mainlandAvailability": {
        "patterns": ["02-mainland-availability.*"],
        "description": "App Store Connect 只选择中国大陆可售地区",
    },
    "mainlandFiling": {
        "patterns": ["03-app-filing.*"],
        "description": "中国大陆 APP 备案或适用判断证据",
    },
    "privacyLabel": {
        "patterns": ["04-privacy-label.*"],
        "description": "App Store Connect 隐私标签截图或导出",
    },
    "ageRatingResult": {
        "patterns": ["17-age-rating-result.*"],
        "description": "App Store Connect 年龄分级结果页截图或导出",
    },
    "signedArchive": {
        "patterns": ["05-signed-archive.*"],
        "description": "App Store Distribution Archive 成功证据",
    },
    "testFlight": {
        "patterns": ["06-testflight.*"],
        "description": "TestFlight 构建和测试状态证据",
    },
    "appleDeveloperAccountAccess": {
        "patterns": ["AppleDeveloper/16-account-roles-access.*"],
        "description": "当前 Apple ID 具备证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限",
    },
    "smsProvider": {
        "patterns": ["07-sms-provider.*"],
        "description": "真实短信签名、模板和验证码发送成功证据",
    },
    "wechatOpenPlatform": {
        "patterns": ["08-wechat-open-platform.*"],
        "description": "微信开放平台移动应用、Bundle ID、URL Scheme / Universal Link 配置证据",
    },
    "wechatUniversalLinkAasa": {
        "patterns": ["08b-wechat-universal-link-aasa.*"],
        "description": "微信 Universal Link、AASA、Associated Domains 和 Team ID 同轮核对证据",
    },
    "huaweiObsPolicy": {
        "patterns": ["09-obs-policy.*"],
        "description": "华为云 OBS bucket、生命周期、加密和删除验证证据",
    },
    "finalScreenshots": {
        "patterns": ["10-final-screenshots/*.png", "10-final-screenshots/*.jpg", "10-final-screenshots/*.jpeg"],
        "description": "最终 App Store 截图，不使用真实宝宝照片",
        "minFiles": 5,
        "allowedExtensions": [".png", ".jpg", ".jpeg"],
        "expectedFilenames": [
            "01-home-iphone16pro.png",
            "02-record-iphone16pro.png",
            "03-growth-iphone16pro.png",
            "04-profile-iphone16pro.png",
            "05-profile-sync-iphone16pro.png",
        ],
    },
    "reviewTestAccount": {
        "patterns": ["11-test-account-redacted.json"],
        "description": "App Review 恢复密钥测试账号脱敏证据",
        "allowedExtensions": [".json"],
    },
    "realDeviceRegression": {
        "patterns": ["12-real-device-regression.md"],
        "description": "TestFlight 或签名真机回归结果",
        "allowedExtensions": [".md"],
        "requiredCheckedItems": [
            "iOS 26.5",
            "冷启动",
            "手机号登录",
            "微信登录",
            "恢复密钥登录",
            "云同步",
            "云恢复",
            "账号删除",
            "通知权限",
            "通知权限允许独立截图",
            "通知权限拒绝独立截图",
            "灵动岛喝奶提醒开关",
            "灵动岛紧凑态头像和进度环未压到岛中心",
            "灵动岛展开态文字和数字未贴边或被吞",
            "锁屏通知栈上下相邻通知不遮挡提醒卡片",
            "锁屏/桌面小组件",
            "灵动岛紧凑态独立截图",
            "灵动岛展开态独立截图",
            "锁屏通知栈独立截图",
            "锁屏小组件独立截图",
            "桌面小组件独立截图",
            "锁屏小组件内容不裁剪不展示隐私照片",
            "桌面小组件内容不裁剪不展示隐私照片",
            "审核边界文案",
            "Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔",
            "小组件只读展示本机今日摘要",
            "Apple Watch 只作为系统镜像通知，不在 App Store 文案中承诺 Watch App",
            "状态展示只反映用户主动记录的数据",
            "不生成健康建议、压力提醒、喂养建议或医疗判断",
            "不接入 HealthKit、传感器、医院系统或第三方健康数据源",
            "不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议",
        ],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today_path_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def infer_path_date(date_arg: str, output_arg: str) -> str:
    if date_arg:
        return date_arg.replace("-", "")
    match = re.search(r"20\d{6}", output_arg)
    if match:
        return match.group(0)
    return today_path_date()


def manual_evidence_checklist_path(path_date: str) -> Path:
    return Path(MANUAL_EVIDENCE_CHECKLIST_TEMPLATE.format(date=path_date))


def manual_evidence_packet_path(path_date: str) -> Path:
    return Path(MANUAL_EVIDENCE_PACKET_TEMPLATE.format(date=path_date))


def display_date(path_date: str) -> str:
    if re.fullmatch(r"\d{8}", path_date):
        return f"{path_date[:4]}-{path_date[4:6]}-{path_date[6:]}"
    return path_date


def dated_values(values: dict[str, str], path_date: str) -> dict[str, str]:
    return {
        key: value.format(date=path_date, display_date=display_date(path_date))
        for key, value in values.items()
    }


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def matching_files(root: Path, patterns: list[str], allowed_extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(
            path
            for path in root.glob(pattern)
            if path.is_file() and path.stat().st_size > 0 and path.suffix.lower() in allowed_extensions
        )
    return sorted(set(files))


def checked(text: str, label: str) -> bool:
    return any(
        line.strip().lower().startswith("- [x]") and label in line
        for line in text.splitlines()
    )


def validate_checked_items(files: list[Path], labels: list[str]) -> tuple[bool, list[str]]:
    if not files:
        return False, labels
    text = files[0].read_text(encoding="utf-8")
    missing = [label for label in labels if not checked(text, label)]
    return not missing, missing


def validate_review_test_account(files: list[Path]) -> tuple[bool, dict[str, Any]]:
    if not files:
        return False, {"missingFile": "11-test-account-redacted.json"}

    text = files[0].read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False, {"invalidJson": True}

    if not isinstance(data, dict):
        return False, {"invalidJsonObject": True}

    details: dict[str, Any] = {}
    if not data.get("accountId"):
        details["missingAccountId"] = True
    if data.get("recoveryKeyStored") != ".env.xnp-review-account":
        details["invalidRecoveryKeyStorage"] = data.get("recoveryKeyStored") or "<missing>"
    if data.get("recoveryVerified") is not True:
        details["recoveryVerified"] = data.get("recoveryVerified")
    if data.get("syncSeeded") is not True:
        details["syncSeeded"] = data.get("syncSeeded")
    if data.get("containsSecret") is not False:
        details["containsSecret"] = data.get("containsSecret")

    forbidden_fields = sorted(
        key
        for key in data
        if key != "containsSecret"
        and any(marker in str(key).lower() for marker in ("secret", "token", "password", "code"))
    )
    if forbidden_fields:
        details["forbiddenFields"] = forbidden_fields

    forbidden_hits = sorted(
        name
        for name, pattern in FORBIDDEN_REAL_DEVICE_PATTERNS.items()
        if pattern.search(text)
    )
    if forbidden_hits:
        details["forbiddenSecretMarkers"] = forbidden_hits

    return not details, details


def text_evidence_redaction_hits(files: list[Path]) -> list[str]:
    hits: list[str] = []
    for path in files:
        if path.suffix.lower() not in TEXT_EVIDENCE_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name, pattern in FORBIDDEN_REAL_DEVICE_PATTERNS.items():
            if pattern.search(text):
                hits.append(f"{path.name}:{name}")
    return sorted(hits)


def validate_generic_manual_evidence(files: list[Path], min_files: int) -> tuple[bool, dict[str, Any]]:
    large_enough = [path for path in files if path.stat().st_size >= MIN_MANUAL_EVIDENCE_BYTES]
    too_small = [
        {"file": path.name, "size": path.stat().st_size}
        for path in files
        if path.stat().st_size < MIN_MANUAL_EVIDENCE_BYTES
    ]

    details: dict[str, Any] = {
        "minimumBytes": MIN_MANUAL_EVIDENCE_BYTES,
    }
    if too_small:
        details["smallEvidenceFiles"] = too_small
    if len(large_enough) < min_files:
        details["largeEnoughFiles"] = [path.name for path in large_enough]
    return len(large_enough) >= min_files, details


def rd_case_statuses(text: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| RD-"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        match = re.search(r"\bRD-\d{2}\b", cells[0])
        if match:
            statuses[match.group(0)] = cells[1]
    return statuses


def rd_case_evidence_paths(text: str) -> dict[str, str]:
    evidence_paths: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| RD-"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        match = re.search(r"\bRD-\d{2}\b", cells[0])
        if match:
            evidence_paths[match.group(0)] = cells[2]
    return evidence_paths


def env_field_value(text: str, field: str) -> str:
    match = re.search(rf"^\s*-\s*{re.escape(field)}[：:]\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def evidence_file_details(evidence_root: Path, raw_value: str) -> dict[str, Any]:
    value = raw_value.strip().strip("`")
    if not value:
        return {"path": raw_value, "exists": False, "error": "empty"}
    if Path(value).is_absolute():
        return {"path": value, "exists": False, "error": "absolute paths are not accepted"}

    repo_root_path = evidence_root.parents[2]
    if value.startswith(str(EVIDENCE_ROOT)):
        candidate = repo_root_path / value
    else:
        candidate = evidence_root / value

    try:
        resolved_root = evidence_root.resolve()
        resolved_candidate = candidate.resolve(strict=False)
        inside_evidence_root = resolved_candidate.is_relative_to(resolved_root)
    except OSError:
        inside_evidence_root = False

    if not inside_evidence_root:
        return {"path": value, "exists": False, "error": "path must stay inside Docs/08_Release/AppStoreEvidence"}
    if candidate.suffix.lower() not in REAL_DEVICE_EVIDENCE_EXTENSIONS:
        return {"path": value, "exists": False, "error": "unsupported extension"}
    if not candidate.exists() or not candidate.is_file():
        return {"path": value, "exists": False, "error": "missing file"}
    size = candidate.stat().st_size
    if size < MIN_MANUAL_EVIDENCE_BYTES:
        return {
            "path": value,
            "exists": False,
            "error": "evidence file is too small to be reliable",
            "size": size,
            "minimumBytes": MIN_MANUAL_EVIDENCE_BYTES,
        }
    return {"path": value, "exists": True, "size": size}


def validate_real_device_regression(files: list[Path], labels: list[str]) -> tuple[bool, dict[str, Any]]:
    if not files:
        return False, {"missingCheckedItems": labels}

    text = files[0].read_text(encoding="utf-8")
    evidence_root = files[0].parent
    missing_checked_items = [label for label in labels if not checked(text, label)]
    missing_env_fields = [
        field
        for field in REQUIRED_REAL_DEVICE_ENV_FIELDS
        if not env_field_value(text, field)
    ]
    missing_visual_fields = [
        field
        for field in REQUIRED_REAL_DEVICE_VISUAL_FIELDS
        if not env_field_value(text, field)
    ]
    invalid_visual_conclusions = {
        field: env_field_value(text, field)
        for field, pattern in REQUIRED_VISUAL_CONCLUSION_PATTERNS.items()
        if env_field_value(text, field) and not pattern.search(env_field_value(text, field))
    }
    missing_rd_ids = sorted(rd_id for rd_id in REQUIRED_RD_IDS if rd_id not in text)
    rd_statuses = rd_case_statuses(text)
    rd_evidence_paths = rd_case_evidence_paths(text)
    failed_rd_statuses = {
        rd_id: status
        for rd_id, status in sorted(rd_statuses.items())
        if rd_id in REQUIRED_RD_IDS and status != "通过"
    }
    missing_rd_evidence_paths = sorted(
        rd_id
        for rd_id in REQUIRED_RD_IDS
        if not rd_evidence_paths.get(rd_id, "").strip()
    )
    invalid_rd_evidence_paths = {
        rd_id: value
        for rd_id, value in sorted(rd_evidence_paths.items())
        if rd_id in REQUIRED_RD_IDS
        and value.strip()
        and not value.lower().endswith(REAL_DEVICE_EVIDENCE_EXTENSIONS)
    }
    missing_rd_evidence_files = {
        rd_id: details
        for rd_id, details in sorted(
            (
                (rd_id, evidence_file_details(evidence_root, value))
                for rd_id, value in rd_evidence_paths.items()
                if rd_id in REQUIRED_RD_IDS and value.strip()
            ),
            key=lambda item: item[0],
        )
        if details.get("exists") is not True
    }
    visual_rd_paths = {
        rd_id: rd_evidence_paths.get(rd_id, "").strip().strip("`")
        for rd_id in REQUIRED_VISUAL_RD_PATH_PATTERNS
    }
    visual_rd_paths_present = {rd_id: value for rd_id, value in visual_rd_paths.items() if value}
    invalid_visual_rd_path_semantics = {
        rd_id: value
        for rd_id, value in sorted(visual_rd_paths_present.items())
        if not REQUIRED_VISUAL_RD_PATH_PATTERNS[rd_id].search(value)
    }
    duplicate_visual_rd_evidence_paths = sorted(
        value
        for value in set(visual_rd_paths_present.values())
        if list(visual_rd_paths_present.values()).count(value) > 1
    )
    environment_evidence = env_field_value(text, "证据截图/录屏").strip().strip("`")
    reused_environment_visual_rd_paths = {
        rd_id: value
        for rd_id, value in sorted(visual_rd_paths_present.items())
        if environment_evidence and value == environment_evidence
    }
    auth_account_rd_paths = {
        rd_id: rd_evidence_paths.get(rd_id, "").strip().strip("`")
        for rd_id in REQUIRED_AUTH_ACCOUNT_RD_PATH_PATTERNS
    }
    auth_account_rd_paths_present = {rd_id: value for rd_id, value in auth_account_rd_paths.items() if value}
    invalid_auth_account_rd_path_semantics = {
        rd_id: value
        for rd_id, value in sorted(auth_account_rd_paths_present.items())
        if not REQUIRED_AUTH_ACCOUNT_RD_PATH_PATTERNS[rd_id].search(value)
    }
    duplicate_auth_account_rd_evidence_paths = sorted(
        value
        for value in set(auth_account_rd_paths_present.values())
        if list(auth_account_rd_paths_present.values()).count(value) > 1
    )
    reused_environment_auth_account_rd_paths = {
        rd_id: value
        for rd_id, value in sorted(auth_account_rd_paths_present.items())
        if environment_evidence and value == environment_evidence
    }
    missing_focused_evidence_path_markers = {
        name: path
        for name, path in REQUIRED_FOCUSED_REAL_DEVICE_EVIDENCE_PATHS.items()
        if path not in text
    }
    focused_evidence_file_details = {
        name: details
        for name, details in sorted(
            (
                (name, evidence_file_details(evidence_root, path))
                for name, path in REQUIRED_FOCUSED_REAL_DEVICE_EVIDENCE_PATHS.items()
                if path in text
            ),
            key=lambda item: item[0],
        )
        if details.get("exists") is not True
    }
    pending_markers = sorted(marker for marker in PENDING_REAL_DEVICE_MARKERS if marker in text)
    template_markers = sorted(marker for marker in TEMPLATE_REAL_DEVICE_MARKERS if marker in text)
    forbidden_hits = sorted(
        name
        for name, pattern in FORBIDDEN_REAL_DEVICE_PATTERNS.items()
        if pattern.search(text)
    )

    ios_value = env_field_value(text, "iOS")
    ios_265_only = ios_value == "26.5" or ios_value == "iOS 26.5"
    install_method = env_field_value(text, "安装方式")
    install_method_ok = install_method in {"TestFlight", "Xcode 签名真机包"}
    environment_evidence_details = evidence_file_details(evidence_root, environment_evidence)

    details: dict[str, Any] = {}
    if missing_checked_items:
        details["missingCheckedItems"] = missing_checked_items
    if missing_env_fields:
        details["missingEnvironmentFields"] = missing_env_fields
    if missing_visual_fields:
        details["missingVisualConclusionFields"] = missing_visual_fields
    if invalid_visual_conclusions:
        details["invalidVisualConclusions"] = invalid_visual_conclusions
    if missing_rd_ids:
        details["missingRegressionCaseIds"] = missing_rd_ids
    if failed_rd_statuses:
        details["failedRegressionCaseStatuses"] = failed_rd_statuses
    if missing_rd_evidence_paths:
        details["missingRegressionEvidencePaths"] = missing_rd_evidence_paths
    if invalid_rd_evidence_paths:
        details["invalidRegressionEvidencePaths"] = invalid_rd_evidence_paths
    if missing_rd_evidence_files:
        details["missingRegressionEvidenceFiles"] = missing_rd_evidence_files
    if invalid_visual_rd_path_semantics:
        details["invalidVisualRegressionEvidenceNames"] = invalid_visual_rd_path_semantics
    if duplicate_visual_rd_evidence_paths:
        details["duplicateVisualRegressionEvidencePaths"] = duplicate_visual_rd_evidence_paths
    if reused_environment_visual_rd_paths:
        details["reusedEnvironmentVisualRegressionEvidence"] = reused_environment_visual_rd_paths
    if invalid_auth_account_rd_path_semantics:
        details["invalidAuthAccountRegressionEvidenceNames"] = invalid_auth_account_rd_path_semantics
    if duplicate_auth_account_rd_evidence_paths:
        details["duplicateAuthAccountRegressionEvidencePaths"] = duplicate_auth_account_rd_evidence_paths
    if reused_environment_auth_account_rd_paths:
        details["reusedEnvironmentAuthAccountEvidence"] = reused_environment_auth_account_rd_paths
    if missing_focused_evidence_path_markers:
        details["missingFocusedEvidencePathMarkers"] = missing_focused_evidence_path_markers
    if focused_evidence_file_details:
        details["missingFocusedEvidenceFiles"] = focused_evidence_file_details
    if pending_markers:
        details["pendingMarkers"] = pending_markers
    if template_markers:
        details["templateMarkers"] = template_markers
    if forbidden_hits:
        details["forbiddenSecretMarkers"] = forbidden_hits
    if not ios_265_only:
        details["invalidIOSVersion"] = ios_value or "<missing>"
    if not install_method_ok:
        details["invalidInstallMethod"] = install_method or "<missing>"
    if environment_evidence_details.get("exists") is not True:
        details["invalidEnvironmentEvidenceFile"] = environment_evidence_details

    return not details, details


def validate_final_screenshots_asset_proof(root: Path) -> tuple[bool, dict[str, Any]]:
    proof_path = root / APP_STORE_ASSETS_PROOF
    data = read_json(proof_path)
    checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
    failed_asset_checks = [
        name
        for name in REQUIRED_FINAL_SCREENSHOT_ASSET_CHECKS
        if not isinstance(checks.get(name), dict) or checks[name].get("passed") is not True
    ]

    details: dict[str, Any] = {
        "assetProof": str(APP_STORE_ASSETS_PROOF),
    }
    if not data:
        details["missingOrInvalidAssetProof"] = True
    if data.get("passed") is not True:
        details["assetProofPassed"] = data.get("passed")
    if failed_asset_checks:
        details["failedAssetChecks"] = failed_asset_checks

    return len(details) == 1, details


def validate_manual_evidence_checklist(root: Path, path_date: str) -> tuple[bool, dict[str, Any]]:
    relative_checklist_path = manual_evidence_checklist_path(path_date)
    checklist_path = root / relative_checklist_path
    if not checklist_path.exists():
        return False, {
            "file": str(relative_checklist_path),
            "missingFile": True,
        }

    text = checklist_path.read_text(encoding="utf-8")
    missing_markers = [
        marker
        for marker in [*MANUAL_EVIDENCE_CHECKLIST_MARKERS, *(f"RD-{index:02d}" for index in range(1, 25))]
        if marker not in text
    ]
    details: dict[str, Any] = {
        "file": str(relative_checklist_path),
        "markersChecked": len(MANUAL_EVIDENCE_CHECKLIST_MARKERS) + 24,
    }
    if missing_markers:
        details["missingMarkers"] = missing_markers
    return not missing_markers, details


def validate_manual_evidence_packet(root: Path, path_date: str) -> tuple[bool, dict[str, Any]]:
    relative_packet_path = manual_evidence_packet_path(path_date)
    packet_path = root / relative_packet_path
    if not packet_path.exists():
        return False, {
            "file": str(relative_packet_path),
            "missingFile": True,
        }

    data = read_json(packet_path)
    if not data:
        return False, {
            "file": str(relative_packet_path),
            "invalidJson": True,
        }

    details: dict[str, Any] = {
        "file": str(relative_packet_path),
        "sourceFilesChecked": len(MANUAL_EVIDENCE_PACKET_SOURCE_FILES),
        "targetFilesChecked": len(MANUAL_EVIDENCE_PACKET_TARGET_FILES),
        "dependencyMatrixEntriesChecked": len(MANUAL_EVIDENCE_PACKET_DEPENDENCY_MATRIX),
        "markersChecked": len(MANUAL_EVIDENCE_PACKET_MARKERS),
    }
    invalid_fields: dict[str, Any] = {}
    expected_date = display_date(path_date)
    expected_fields = {
        "artifactType": "app-store-manual-evidence-packet",
        "status": "manual-evidence-plan-not-evidence",
        "date": expected_date,
        "canSubmitFromThisPacket": False,
    }
    for key, expected in expected_fields.items():
        if data.get(key) != expected:
            invalid_fields[key] = data.get(key, "<missing>")
    if invalid_fields:
        details["invalidFields"] = invalid_fields

    source_files = data.get("sourceFiles")
    if not isinstance(source_files, dict):
        details["missingSourceFilesObject"] = True
        source_files = {}
    expected_sources = dated_values(MANUAL_EVIDENCE_PACKET_SOURCE_FILES, path_date)
    missing_sources = sorted(key for key in expected_sources if key not in source_files)
    invalid_sources = {
        key: source_files.get(key)
        for key, expected in expected_sources.items()
        if key in source_files and source_files.get(key) != expected
    }
    if missing_sources:
        details["missingSourceFiles"] = missing_sources
    if invalid_sources:
        details["invalidSourceFiles"] = invalid_sources

    target_files = data.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        details["missingTargetEvidenceFilesObject"] = True
        target_files = {}
    missing_targets = sorted(key for key in MANUAL_EVIDENCE_PACKET_TARGET_FILES if key not in target_files)
    invalid_targets = {
        key: target_files.get(key)
        for key, expected in MANUAL_EVIDENCE_PACKET_TARGET_FILES.items()
        if key in target_files and target_files.get(key) != expected
    }
    if missing_targets:
        details["missingTargetEvidenceFiles"] = missing_targets
    if invalid_targets:
        details["invalidTargetEvidenceFiles"] = invalid_targets

    file_checks = data.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        details["missingEvidenceFileChecksObject"] = True
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        invalid_file_check_entries: list[str] = []
        duplicate_file_checks: list[str] = []
        for check in file_checks:
            if not isinstance(check, dict):
                invalid_file_check_entries.append("<non-object>")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                invalid_file_check_entries.append("<missing-artifactId>")
                continue
            if artifact_id in checks_by_artifact:
                duplicate_file_checks.append(artifact_id)
            checks_by_artifact[artifact_id] = check
        if tuple(artifact_order) != tuple(MANUAL_EVIDENCE_PACKET_TARGET_FILES):
            details["invalidEvidenceFileCheckOrder"] = artifact_order
        if invalid_file_check_entries:
            details["invalidEvidenceFileCheckEntries"] = invalid_file_check_entries
        if duplicate_file_checks:
            details["duplicateEvidenceFileChecks"] = duplicate_file_checks

        missing_file_checks = sorted(
            artifact_id for artifact_id in MANUAL_EVIDENCE_PACKET_TARGET_FILES if artifact_id not in checks_by_artifact
        )
        invalid_file_check_targets = {
            artifact_id: checks_by_artifact[artifact_id].get("target")
            for artifact_id, expected in MANUAL_EVIDENCE_PACKET_TARGET_FILES.items()
            if artifact_id in checks_by_artifact and checks_by_artifact[artifact_id].get("target") != expected
        }
        invalid_file_check_placeholders: dict[str, dict[str, Any]] = {}
        for artifact_id, check in checks_by_artifact.items():
            invalid_values = {
                key: check.get(key)
                for key, expected in MANUAL_EVIDENCE_PACKET_FILE_CHECK_PLACEHOLDERS.items()
                if check.get(key) != expected
            }
            if invalid_values:
                invalid_file_check_placeholders[artifact_id] = invalid_values
        if missing_file_checks:
            details["missingEvidenceFileChecks"] = missing_file_checks
        if invalid_file_check_targets:
            details["invalidEvidenceFileCheckTargets"] = invalid_file_check_targets
        if invalid_file_check_placeholders:
            details["invalidEvidenceFileCheckPlaceholders"] = invalid_file_check_placeholders

    dependency_matrix = data.get("evidenceDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        details["missingEvidenceDependencyMatrixObject"] = True
    else:
        matrix_by_artifact: dict[str, dict[str, Any]] = {}
        dependency_order: list[Any] = []
        invalid_dependency_entries: list[str] = []
        invalid_dependency_fields: dict[str, list[str]] = {}
        duplicate_dependencies: list[str] = []
        for index, entry in enumerate(dependency_matrix):
            if not isinstance(entry, dict):
                invalid_dependency_entries.append("<non-object>")
                continue
            artifact_id = entry.get("artifactId")
            dependency_order.append(artifact_id)
            artifact_key = artifact_id if isinstance(artifact_id, str) and artifact_id else f"<entry-{index}>"
            if tuple(entry) != MANUAL_EVIDENCE_PACKET_DEPENDENCY_FIELDS:
                invalid_dependency_fields[artifact_key] = list(entry)
            if not isinstance(artifact_id, str) or not artifact_id:
                invalid_dependency_entries.append("<missing-artifactId>")
                continue
            if artifact_id in matrix_by_artifact:
                duplicate_dependencies.append(artifact_id)
            matrix_by_artifact[artifact_id] = entry
        if tuple(dependency_order) != tuple(MANUAL_EVIDENCE_PACKET_TARGET_FILES):
            details["invalidEvidenceDependencyMatrixOrder"] = dependency_order
        if invalid_dependency_entries:
            details["invalidEvidenceDependencyMatrixEntries"] = invalid_dependency_entries
        if invalid_dependency_fields:
            details["invalidEvidenceDependencyMatrixFields"] = invalid_dependency_fields
        if duplicate_dependencies:
            details["duplicateEvidenceDependencyMatrixEntries"] = duplicate_dependencies

        missing_dependencies = sorted(
            artifact_id
            for artifact_id in MANUAL_EVIDENCE_PACKET_TARGET_FILES
            if artifact_id not in matrix_by_artifact
        )
        unexpected_dependencies = sorted(
            artifact_id
            for artifact_id in matrix_by_artifact
            if artifact_id not in MANUAL_EVIDENCE_PACKET_TARGET_FILES
        )
        invalid_dependency_targets = {
            artifact_id: matrix_by_artifact[artifact_id].get("target")
            for artifact_id, expected in MANUAL_EVIDENCE_PACKET_TARGET_FILES.items()
            if artifact_id in matrix_by_artifact and matrix_by_artifact[artifact_id].get("target") != expected
        }
        invalid_dependency_proves = {
            artifact_id: matrix_by_artifact[artifact_id].get("proves")
            for artifact_id, expected in MANUAL_EVIDENCE_PACKET_DEPENDENCY_MATRIX.items()
            if artifact_id in matrix_by_artifact and matrix_by_artifact[artifact_id].get("proves") != expected["proves"]
        }
        invalid_dependency_does_not_prove = {
            artifact_id: matrix_by_artifact[artifact_id].get("doesNotProve")
            for artifact_id, expected in MANUAL_EVIDENCE_PACKET_DEPENDENCY_MATRIX.items()
            if artifact_id in matrix_by_artifact
            and matrix_by_artifact[artifact_id].get("doesNotProve") != expected["doesNotProve"]
        }
        invalid_dependency_required = {
            artifact_id: matrix_by_artifact[artifact_id].get("requiredBeforeSubmit")
            for artifact_id in MANUAL_EVIDENCE_PACKET_DEPENDENCY_MATRIX
            if artifact_id in matrix_by_artifact
            and matrix_by_artifact[artifact_id].get("requiredBeforeSubmit") is not True
        }
        invalid_dependency_status = {
            artifact_id: matrix_by_artifact[artifact_id].get("initialStatus")
            for artifact_id in MANUAL_EVIDENCE_PACKET_DEPENDENCY_MATRIX
            if artifact_id in matrix_by_artifact and matrix_by_artifact[artifact_id].get("initialStatus") != "pending"
        }
        if missing_dependencies:
            details["missingEvidenceDependencyMatrixEntries"] = missing_dependencies
        if unexpected_dependencies:
            details["unexpectedEvidenceDependencyMatrixEntries"] = unexpected_dependencies
        if invalid_dependency_targets:
            details["invalidEvidenceDependencyMatrixTargets"] = invalid_dependency_targets
        if invalid_dependency_proves:
            details["invalidEvidenceDependencyMatrixProves"] = invalid_dependency_proves
        if invalid_dependency_does_not_prove:
            details["invalidEvidenceDependencyMatrixDoesNotProve"] = invalid_dependency_does_not_prove
        if invalid_dependency_required:
            details["invalidEvidenceDependencyMatrixRequiredBeforeSubmit"] = invalid_dependency_required
        if invalid_dependency_status:
            details["invalidEvidenceDependencyMatrixInitialStatus"] = invalid_dependency_status

    packet_text = json.dumps(data, ensure_ascii=False, sort_keys=True)
    missing_markers = [marker for marker in MANUAL_EVIDENCE_PACKET_MARKERS if marker not in packet_text]
    if missing_markers:
        details["missingMarkers"] = missing_markers

    return len(details) == 5, details


def validate_capture_guidance(root: Path, path_date: str) -> tuple[bool, dict[str, Any]]:
    details: dict[str, Any] = {
        "filesChecked": len(CAPTURE_GUIDANCE_MARKERS),
    }
    missing_files: list[str] = []
    missing_markers: dict[str, list[str]] = {}
    for label, requirement in CAPTURE_GUIDANCE_MARKERS.items():
        path = root / str(requirement["path"])
        if not path.exists():
            missing_files.append(str(requirement["path"]))
            continue
        text = path.read_text(encoding="utf-8")
        markers = [str(marker).format(date=path_date, display_date=display_date(path_date)) for marker in requirement["markers"]]
        missing = [marker for marker in markers if marker not in text]
        if missing:
            missing_markers[label] = missing
    if missing_files:
        details["missingFiles"] = missing_files
    if missing_markers:
        details["missingMarkers"] = missing_markers
    return not missing_files and not missing_markers, details


def build_report(root: Path, path_date: str) -> dict[str, Any]:
    evidence_root = root / EVIDENCE_ROOT
    checks: dict[str, dict[str, Any]] = {}
    checklist_passed, checklist_details = validate_manual_evidence_checklist(root, path_date)
    checks["manualEvidenceChecklist"] = {
        "passed": checklist_passed,
        "description": "人工证据清单覆盖全部 App Store / TestFlight / 真机回归证据项",
        **checklist_details,
    }
    packet_passed, packet_details = validate_manual_evidence_packet(root, path_date)
    checks["manualEvidencePacket"] = {
        "passed": packet_passed,
        "description": "人工证据现场执行包锁定真实证据、同轮采集、脱敏和复跑边界",
        **packet_details,
    }
    capture_guidance_passed, capture_guidance_details = validate_capture_guidance(root, path_date)
    checks["captureGuidance"] = {
        "passed": capture_guidance_passed,
        "description": "人工证据入口指南和 README 必须要求 RD-23 锁屏通知栈、锁屏小组件和桌面小组件三份独立证据",
        **capture_guidance_details,
    }
    for name, spec in REQUIRED_EVIDENCE.items():
        allowed_extensions = {
            str(extension).lower()
            for extension in spec.get("allowedExtensions", DEFAULT_ALLOWED_EXTENSIONS)
        }
        files = matching_files(evidence_root, spec["patterns"], allowed_extensions)
        min_files = int(spec.get("minFiles", 1))
        passed = len(files) >= min_files
        checks[name] = {
            "passed": passed,
            "description": spec["description"],
            "patterns": [str(EVIDENCE_ROOT / pattern) for pattern in spec["patterns"]],
            "allowedExtensions": sorted(allowed_extensions),
            "minFiles": min_files,
            "files": [str(path.relative_to(root)) for path in files],
        }
        if "requiredCheckedItems" in spec:
            checks[name]["requiredCheckedItems"] = list(spec["requiredCheckedItems"])
        if passed and name not in {"finalScreenshots", "reviewTestAccount", "realDeviceRegression"}:
            passed, manual_details = validate_generic_manual_evidence(files, min_files)
            checks[name].update(manual_details)
            checks[name]["passed"] = passed
        if name not in {"reviewTestAccount", "realDeviceRegression"}:
            redaction_hits = text_evidence_redaction_hits(files)
            if redaction_hits:
                checks[name]["forbiddenTextEvidenceMarkers"] = redaction_hits
                checks[name]["passed"] = False
                passed = False
        expected_filenames = [str(filename) for filename in spec.get("expectedFilenames", [])]
        if expected_filenames:
            file_names = {path.name for path in files}
            missing_expected = [filename for filename in expected_filenames if filename not in file_names]
            if missing_expected:
                checks[name]["missingExpectedFilenames"] = missing_expected
                checks[name]["passed"] = False
                passed = False
        if passed and name == "finalScreenshots":
            passed, final_screenshot_details = validate_final_screenshots_asset_proof(root)
            checks[name].update(final_screenshot_details)
            checks[name]["passed"] = passed
            continue
        if passed and name == "reviewTestAccount":
            passed, review_account_details = validate_review_test_account(files)
            checks[name].update(review_account_details)
            checks[name]["passed"] = passed
            continue
        missing_checked_items: list[str] = []
        if passed and "requiredCheckedItems" in spec:
            if name == "realDeviceRegression":
                passed, real_device_details = validate_real_device_regression(files, list(spec["requiredCheckedItems"]))
                checks[name].update(real_device_details)
            else:
                passed, missing_checked_items = validate_checked_items(files, list(spec["requiredCheckedItems"]))
                if missing_checked_items:
                    checks[name]["missingCheckedItems"] = missing_checked_items
            checks[name]["passed"] = passed
            continue

    missing = [name for name, check in checks.items() if not check["passed"]]
    return {
        "startedAt": utc_now(),
        "completedAt": utc_now(),
        "expectedPathDate": path_date,
        "ready": not missing,
        "missingEvidence": missing,
        "evidenceRoot": str(EVIDENCE_ROOT),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output", default="Backend/proof/app-store-evidence.json")
    parser.add_argument("--date", default="")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    path_date = infer_path_date(args.date, args.output)
    result = build_report(root, path_date)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["ready"]:
        print(f"App Store evidence passed: {output_path}")
        return

    missing = ", ".join(result["missingEvidence"])
    print(f"App Store evidence incomplete: {output_path}", file=sys.stderr)
    print(f"missing evidence: {missing}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
