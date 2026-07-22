#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_APP_NAME = "小奶瓶"
EXPECTED_BUNDLE_ID = "com.mewpow.xiaonaiping"
EXPECTED_SUBTITLE = "温柔记录宝宝每一天"
EXPECTED_PRIVACY_URL = "https://api.mewpow.com/xiaonaiping/privacy"
EXPECTED_SUPPORT_URL = "https://api.mewpow.com/xiaonaiping/support"
EXPECTED_TERMS_URL = "https://api.mewpow.com/xiaonaiping/terms"
EXPECTED_KEYWORDS = {"宝宝记录", "育儿", "喂奶", "睡眠", "尿布", "成长记录", "疫苗提醒", "相册"}
EXPECTED_PRIVACY_CATEGORY_REQUIREMENTS = {
    "Identifiers": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "Contact Info": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "User Content": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "Photos or Videos": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "Health and Fitness": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "Usage Data": {
        "linkedToUser": True,
        "purposes": {"Analytics"},
    },
    "Diagnostics": {
        "linkedToUser": False,
        "purposes": {"App Functionality", "Analytics"},
    },
}
EXPECTED_PRIVACY_CATEGORIES = set(EXPECTED_PRIVACY_CATEGORY_REQUIREMENTS)
EXPECTED_APP_PRIVACY_FLAGS = {
    "targetsChildrenDirectly": False,
    "containsThirdPartyAdvertising": False,
    "containsThirdPartyAnalytics": False,
    "usesTracking": False,
}
USAGE_DATA_BOUNDARY_MARKERS = (
    "no baby content",
    "photos",
    "phone numbers",
    "wechat identifiers",
    "advertising id",
    "device fingerprint",
)
HEALTH_DATA_BOUNDARY_MARKERS = (
    "user-entered",
    "no healthkit",
    "sensors",
    "hospital records",
    "stress detection",
    "medical interpretation",
    "health advice",
    "pressure reminders",
    "feeding advice",
    "medical diagnosis",
    "status display only",
)
EXPECTED_SCREENSHOTS = {
    "01-home-iphone16pro.png": "记录宝宝今天的小变化",
    "02-record-iphone16pro.png": "半夜也能低负担记录",
    "03-growth-iphone16pro.png": "一个月的成长，轻轻回看",
    "04-profile-iphone16pro.png": "设置、隐私和资料都在这里",
    "05-profile-sync-iphone16pro.png": "主动同步，也能主动删除",
}
SCREENSHOT_COPY_FORBIDDEN_MARKERS = (
    "健康建议",
    "喂养推荐",
    "医疗判断",
    "医疗诊断",
    "治疗建议",
    "压力提醒",
    "压力评估",
    "心理健康判断",
    "微信登录成功",
    "微信登录可用",
)
SCREENSHOT_BOUNDARY_MARKERS = (
    "不使用真实宝宝照片",
    "不展示真实手机号",
    "恢复密钥",
    "token",
    "对象存储 key",
    "不展示 `127.0.0.1`",
    "debug code",
    "internal dashboard",
    "不写医疗诊断",
    "治疗",
    "疫苗建议",
    "医生替代",
    "专业健康结论",
    "微信登录未完成开放平台配置前",
    "不截图暗示微信登录已经可用",
)
IN_APP_COMPANION_COPY_FILES = (
    "App/iOS/XiaoNaiPing/Views/FeedingRecordView.swift",
    "App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/Localizable.strings",
)
COMPANION_COPY_TRIGGER_MARKERS = (
    "Apple Watch",
    "Watch App",
    "watchOS",
    "手表",
    "手錶",
)
COMPANION_COPY_SAFE_MARKERS = (
    "系统通知",
    "系統通知",
    "镜像通知",
    "鏡像通知",
    "跟随系统通知",
    "跟隨系統通知",
    "不在 App Store 文案",
    "不承诺",
    "不宣称",
)
DISALLOWED_CATEGORY_ALTERNATIVES = {
    "生活 / 健康健美",
    "健康健美，正式提交前二选一",
    "Lifestyle or Health & Fitness",
    "choose one before submission",
    "如選健康健美",
}
EXTERNAL_AUTH_BOUNDARY_MARKERS = (
    "手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充",
    "微信 provider 未配置",
    "缺真实微信 Release build setting",
    "缺真实 `wx...` URL Scheme",
    "缺人工证据和 iOS 26.5 真机回归记录",
)
DEFERRED_AUTH_PUBLIC_COPY_MARKERS = (
    "恢复密钥测试账号",
    "手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充",
    "Phone and WeChat sign-in will be added as account-recovery paths only after real SMS provider, WeChat Open Platform, live-send, and real-device evidence are complete",
)
PUBLIC_DESCRIPTION_FORBIDDEN_INTERNAL_MARKERS = (
    "当前审核主路径",
    "待真实短信服务",
    "待真实服务证据",
    "不把手机号或微信登录作为当前审核登录路径",
    "手机号/微信登录待",
    "微信 provider 未配置",
    "debug code",
)
REVIEW_NOTES_FORBIDDEN_INTERNAL_MARKERS = (
    "当前审核主路径",
    "手机号和微信登录待真实短信服务",
    "不把手机号或微信登录作为当前审核登录路径",
)
PREMATURE_AUTH_PUBLIC_CLAIM_MARKERS = (
    "可通过恢复密钥、手机号或微信登录",
    "可透過恢復密鑰、手機號碼或微信登入",
    "支持恢复密钥、手机号、微信登录",
    "支援恢復密鑰、手機號碼、微信登入",
    "手机号/微信/恢复密钥账号同步恢复",
    "手機號碼/微信/恢復密鑰帳號同步恢復",
    "使用恢复密钥、手机号或微信登录并主动同步",
    "使用恢復密鑰、手機號碼或微信登入並主動同步",
    "账号支持恢复密钥、手机号和微信登录",
    "帳號支援恢復密鑰、手機號碼和微信登入",
    "When you sign in with a recovery key, phone number, or WeChat",
    "phone/WeChat/recovery-key sync and restore",
)
REVIEW_ACCOUNT_BOUNDARY_MARKERS = (
    "App Review Information",
    "恢复密钥测试账号",
    "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
    "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
    ".env.xnp-review-account",
    "不得写入 App Store Connect 文案、审核备注、截图或仓库文档",
    "手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充",
)
FORBIDDEN_REVIEW_ACCOUNT_SECRET_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+(?=[A-Za-z0-9._-]{8,})(?=[A-Za-z0-9._-]*[._-])[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
    "placeholderFilingNumber": re.compile(r"ICP备0{4,}号?|ICP备待|待备案号|占位备案号|示例备案号|placeholder filing", re.IGNORECASE),
}
EXPECTED_SCREENSHOT_PLAN_MARKERS = (
    "-sdk iphonesimulator26.5",
    "OS=26.5",
    "XiaoNaiPing-DebugScreenshots-26_5",
    "capture_ios_screenshots.py",
    "--tabs home record growth profile profile-sync",
    "TestFlight 或签名真机包最终截图",
)
METADATA_CURRENT_MARKERS = (
    "日期：2026-06-27",
    "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
    "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260627.md",
    "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
    "Backend/proof/launch-objective-audit.json",
    "Backend/proof/production-readiness.json",
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "iOS 26.5 TestFlight / 签名真机回归证据",
)
METADATA_DESCRIPTION_DEFERRAL_MARKERS = (
    "也可以在新增喂养后按 5 分钟一档手动顺延下一次提醒",
    "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
    "也可以在新增餵養後按 5 分鐘一檔手動順延下一次提醒",
    "不會根據奶量、月齡、感測器或健康資料自動推算餵養時間",
    "manually defer it in 5-minute steps after adding a feeding",
    "does not infer feeding times from volume, age, sensors, or health data",
)
KEYWORDS_MAX_BYTES = 100
APP_NAME_MAX_CHARS = 30
SUBTITLE_MAX_CHARS = 30
PROMOTIONAL_TEXT_MAX_CHARS = 170
LONG_TEXT_MAX_CHARS = 4000
APP_STORE_CONNECT_SUBMISSION_BOUNDARY_REQUIREMENTS = (
    "production-readiness.json ready=true",
    "launch-objective-audit.json ready=true",
    "D-U-N-S delivered and Apple Developer Organization enrollment resumed",
    "Apple Developer Team ID confirmed",
    "App Store Distribution Archive created",
    "TestFlight build processed",
    "微信开放平台 AppID/AppSecret/Universal Link configured",
    "短信服务商截图 and real send proof archived",
    "OBS private bucket policy and deletion proof archived",
    "APP 备案 / ICP applicability evidence archived",
    "iOS 26.5 TestFlight or signed real-device regression completed",
)
REVIEW_NOTES_BOUNDARY_CHECKLIST = {
    "liveActivityAndWidgetsStatusOnly": True,
    "manualDeferralOptions": ["不顺延", "+5 分钟", "+10 分钟", "+15 分钟", "+20 分钟", "+25 分钟", "+30 分钟"],
    "deferralCalculation": "本顿结束时间 + 固定间隔 + 顺延分钟；本顿无喂养时长时按本顿发生时间计算",
    "deferralPersistenceBoundary": "只写入下一次 remindAt；不新增持久化字段",
    "noAutomaticFeedingInference": True,
    "noFeedingAdvice": True,
    "noHealthDataSource": True,
    "reviewLoginBoundary": "优先使用恢复密钥测试账号；手机号和微信测试号等待真实服务证据；不依赖 debug code",
}
REVIEW_NOTES_BOUNDARY_TEXT_MARKERS = (
    "灵动岛和锁屏 Live Activity",
    "桌面/锁屏小组件",
    "不顺延",
    "+5",
    "+10",
    "+15",
    "+20",
    "+25",
    "+30 分钟",
    "本顿结束时间 + 固定间隔 + 顺延分钟",
    "本顿无喂养时长时按本顿发生时间计算",
    "不新增持久化字段",
    "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
    "不构成喂养建议",
    "不接入 HealthKit",
    "恢复密钥测试账号",
    "不依赖 debug code",
)
FILL_SHEET_PATTERN = "APP_STORE_CONNECT_FILL_SHEET_*.md"
DEFAULT_EXPECTED_MATERIAL_DATE = "20260704"
FALLBACK_FILL_SHEET = "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md"
DEFAULT_COPY_PASTE_PACKET = "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md"
DEFAULT_APP_STORE_CONNECT_DRAFT_JSON = "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json"
DEFAULT_APP_STORE_CONNECT_FIELD_FREEZE_PACKET = (
    "Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260627.json"
)
DEFAULT_REVIEW_INFORMATION_PACKET = "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md"
DEFAULT_REVIEW_ACCOUNT_EVIDENCE = "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json"
DEFAULT_APP_REVIEW_TEST_ACCOUNT_PACKET = "Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260627.json"
DEFAULT_PRIVACY_ANSWERS = "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md"
DEFAULT_AGE_RATING_ANSWERS = "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md"
DEFAULT_VERSION_RELEASE_SETTINGS = "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md"
DEFAULT_FINAL_ENTRY_AUDIT = "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md"
DEFAULT_APP_STORE_CONNECT_ENTRY_SESSION_PACKET = (
    "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json"
)
DEFAULT_APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_PACKET = (
    "Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260627.json"
)
DEFAULT_ASC_BACKFILL_RESULT_TEMPLATE = (
    "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-BACKFILL-RESULT.template.json"
)
DEFAULT_ASC_PRIVACY_AGE_REVIEW_RESULT_TEMPLATE = (
    "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-PRIVACY-AGE-REVIEW-RESULT.template.json"
)
FIELD_BUDGET_DOC_LABELS = (
    ("fill sheet", "APP_STORE_CONNECT_FILL_SHEET_20260627.md"),
    ("copy paste packet", "APP_STORE_CONNECT_COPY_PASTE_20260627.md"),
    ("final entry audit", "APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md"),
)
AGE_RATING_ANSWERS_MARKERS = (
    "# 小奶瓶 App Store 年龄分级与医疗器械答案表",
    "日期：2026-06-27",
    "set-an-app-age-rating",
    "declare-regulated-medical-device-status",
    "Kids Category",
    "父母和照护者",
    "不面向儿童直接使用",
    "第一版免费，无 IAP",
    "没有公开 UGC",
    "聊天",
    "社交匹配",
    "Web access",
    "无内置开放网页浏览器",
    "Age Categories and Override",
    "Not Applicable",
    "Made for Kids / Kids Category",
    "User-generated public content",
    "Messaging / chat",
    "Purchases",
    "Advertising / tracking",
    "Gambling / contests",
    "Mature or objectionable content",
    "Health-related records",
    "Medical advice",
    "不接入 HealthKit",
    "传感器",
    "医院系统",
    "手动顺延下一次提醒",
    "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
    "Regulated Medical Device",
    "`No`",
    "not a medical device",
    "does not provide diagnosis, prevention, monitoring, treatment, disease prediction",
    "FDA",
    "CE mark",
    "UKCA",
    "提交前重检项",
)
AGE_RATING_REFERENCE_MARKERS = (
    "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
    "年龄分级",
    "医疗器械",
)
COPY_PASTE_PACKET_MARKERS = (
    "# 小奶瓶 App Store Connect 可复制字段包",
    "日期：2026-06-27",
    "源文件：`Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md`",
    "App Privacy 逐项答案表另见：`Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md`",
    "版本页和发布设置另见：`Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md`",
    "最终人工粘贴和同轮证据核对另见：`Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md`",
    "App 名称：小奶瓶",
    "Bundle ID：com.mewpow.xiaonaiping",
    "SKU：xiaonaiping-ios-1",
    "副标题：温柔记录宝宝每一天",
    "主类别：生活",
    "第二类别：留空",
    "首发地区：Specific Countries or Regions -> China mainland",
    "第二批地区：Hong Kong",
    "隐私政策 URL：https://api.mewpow.com/xiaonaiping/privacy",
    "技术支持 URL：https://api.mewpow.com/xiaonaiping/support",
    "用户协议 URL：https://api.mewpow.com/xiaonaiping/terms",
    "宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册",
    "逐项答案表：Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
    "不选择 Kids 类目",
    "预期年龄分级为 4+",
    "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
    "用于追踪：否",
    "审核备注",
    "喝奶提醒",
    "手动顺延下一次提醒",
    "5 分钟一档",
    "+5、+10、+15、+20、+25、+30 分钟",
    "本顿结束时间 + 固定间隔 + 顺延分钟",
    "本顿无喂养时长时按本顿发生时间",
    "不新增持久化字段",
    "正式提交包不提供、不依赖 debug code",
    "D-U-N-S 交付后必须回 Apple Developer 继续 Organization enrollment",
    "iOS 26.5 TestFlight 或 Xcode 签名真机包回归必须完成",
    "模拟器和 iOS 27 不能替代",
)
COPY_PASTE_SYNC_SECTION_PAIRS = (
    ("关键词", "关键词"),
    ("宣传文本", "宣传文本"),
    ("描述", "描述"),
    ("新版本说明", "新版本说明"),
    ("审核备注可粘贴文本", "审核备注"),
)
APP_INFORMATION_COPY_FIELDS = (
    "App 名称",
    "Bundle ID",
    "SKU",
    "副标题",
    "主类别",
    "第二类别",
    "价格",
    "首发地区",
    "第二批地区",
    "版权",
    "隐私政策 URL",
    "技术支持 URL",
    "用户协议 URL",
)
REVIEW_INFORMATION_PACKET_MARKERS = (
    "# 小奶瓶 App Review Information 私密字段包",
    "日期：2026-06-27",
    "platform-version-information",
    "developer.apple.com/distribute/app-review",
    "Contact Information",
    "First Name / Last Name",
    "Email",
    "Phone Number",
    "不写入仓库",
    "Sign-In Information",
    "Sign-in required",
    "Yes",
    "review-recovery-key-account",
    ".env.xnp-review-account",
    "XNP_REVIEW_RECOVERY_KEY",
    "App Review Information 私密字段",
    "手机号测试号和微信测试号必须等真实短信服务商和微信开放平台配置完成后再补",
    "Notes 可粘贴文本",
    "恢复密钥登录",
    "虚构宝宝资料",
    "立即同步",
    "云端恢复",
    "删除云端账号与同步",
    "正式提交包不得依赖 debug code",
    "不生成健康建议、压力提醒、喂养建议或医疗判断",
    "11-test-account-redacted.json",
    "12-real-device-regression.md",
    "05-signed-archive.png",
    "06-testflight.png",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "不得填写或提交",
    "debug_wechat_*",
    "127.0.0.1",
    "localhost",
    "不得声称手机号登录、微信登录、TestFlight、备案或 App Store 人工证据已完成",
)
REVIEW_ACCOUNT_EVIDENCE_LOCK_MARKERS = (
    "## 审核测试账号脱敏证据一致性锁",
    "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
    "只保存可审核的脱敏状态",
    "不保存恢复密钥本身",
    "App Review Information 的 Sign-In Information",
    "`accountId`",
    "`baseUrl`",
    "https://api.mewpow.com/xiaonaiping",
    "`recoveryKeyStored`",
    "`.env.xnp-review-account`",
    "`recoveryVerified`",
    "`syncSeeded`",
    "`containsSecret`",
    "`false`",
    "Username 仍使用 `review-recovery-key-account`",
    "Password 只从 `.env.xnp-review-account` 的 `XNP_REVIEW_RECOVERY_KEY` 复制到 App Store Connect 私密字段",
    "check_app_store_evidence.py --allow-incomplete",
    "check_app_store_connect_materials.py",
    "不得新增 `secret`、`token`、`password`、`code` 字段",
    "不得包含恢复密钥、验证码、bearer 凭证、完整手机号或 API key",
)
REVIEW_INFORMATION_SUBMISSION_BLOCKER_MARKERS = (
    "## 提交前阻断项",
    "Backend/proof/production-readiness.json",
    "Backend/proof/launch-objective-audit.json",
    "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260627.md",
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "AppleDeveloper/16-account-roles-access.png",
    "App Store Distribution Archive",
    "TestFlight",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "09-obs-policy.png",
    "03-app-filing",
    "04-privacy-label",
    "17-age-rating-result",
    "05-signed-archive.png",
    "06-testflight.png",
    "12-real-device-regression.md",
    "10-final-screenshots/UPLOAD_PROVENANCE.json",
    "不能只保存草稿后提交审核",
    "不能把恢复密钥测试账号当成上线完成证据",
)
APP_REVIEW_TEST_ACCOUNT_PACKET_REFERENCE_MARKERS = (
    "APP_REVIEW_TEST_ACCOUNT_PACKET_20260627.json",
    "review-test-account-packet-not-evidence",
    "不保存恢复密钥",
    "不能作为提交许可",
)
APP_REVIEW_TEST_ACCOUNT_REQUIRED_SOURCE_FILES = {
    "reviewInformation": "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
    "redactedAccountEvidence": "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
    "realDeviceRegressionPlan": "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
    "focusedCapturePacket": "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260627.json",
    "appStoreConnectEntrySessionPacket": "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
    "appStoreSubmissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
}
APP_REVIEW_TEST_ACCOUNT_EVIDENCE_ROOT = "Docs/08_Release/AppStoreEvidence/RealDevice/"
APP_REVIEW_TEST_ACCOUNT_PRIVATE_MARKERS = (
    ".env.xnp-review-account",
    "XNP_REVIEW_RECOVERY_KEY",
    "repositoryStorageAllowed",
    "false",
    "App Store Connect App Review Information private Sign-In Information field",
    "Review Notes source files",
    "Markdown",
    "JSON proof",
    "screenshots",
    "screen recordings",
    "logs",
    "App Store metadata",
)
APP_REVIEW_TEST_ACCOUNT_SIGN_IN_MARKERS = (
    "signInRequired",
    "review-recovery-key-account",
    ".env.xnp-review-account:XNP_REVIEW_RECOVERY_KEY",
    "Phone test account pending real SMS provider screenshot and live-send proof",
    "WeChat test account pending real WeChat Open Platform configuration and RD-14 iOS 26.5 login proof",
    "debugCodeAllowed",
    "false",
)
APP_REVIEW_TEST_ACCOUNT_REDACTED_EVIDENCE_MARKERS = (
    "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
    "non-empty redacted account id",
    "https://api.mewpow.com/xiaonaiping",
    ".env.xnp-review-account",
    "recoveryVerified",
    "syncSeeded",
    "containsSecret",
    "secret",
    "token",
    "password",
    "code",
    "complete phone number",
    "recovery key",
)
APP_REVIEW_TEST_ACCOUNT_EVIDENCE_FILE_TARGETS = {
    "reviewAccountRedacted": "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
    "RD-10": "RealDevice/RD-10-recovery-login.png",
    "RD-13": "RealDevice/RD-13-phone-login.png",
    "RD-14": "RealDevice/RD-14-wechat-login.png",
    "RD-15": "RealDevice/RD-15-account-delete.png",
}
APP_REVIEW_TEST_ACCOUNT_EVIDENCE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsAppReviewFill", False),
    ("sourceIsAllowedEvidenceRoot", False),
    ("sameBuildAsReviewBuild", False),
    ("runtimeIsIos265", False),
    ("realEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
APP_REVIEW_TEST_ACCOUNT_DEPENDENCY_FIELDS = (
    "artifactId",
    "target",
    "proves",
    "doesNotProve",
    "requiredBeforeSubmit",
    "initialStatus",
)
APP_REVIEW_TEST_ACCOUNT_DEPENDENCY_MATRIX = {
    "reviewAccountRedacted": {
        "target": "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
        "proves": [
            "redacted App Review recovery-key account evidence exists without storing the recovery key",
            "recovery-key login account is prepared, verified, sync-seeded, and tied to the production base URL",
        ],
        "doesNotProve": [
            "RD-10 recovery-key real-device login passed",
            "RD-13 phone login passed",
            "RD-14 WeChat login passed",
            "RD-15 account deletion passed",
            "Submit for Review is allowed",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "RD-10": {
        "target": "RealDevice/RD-10-recovery-login.png",
        "proves": [
            "recovery-key account login succeeds on the same iOS 26.5 TestFlight or signed review build",
        ],
        "doesNotProve": [
            "redacted account JSON is secret-free",
            "phone login provider is live",
            "WeChat provider is live",
            "account deletion passed",
            "Submit for Review is allowed",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "RD-13": {
        "target": "RealDevice/RD-13-phone-login.png",
        "proves": [
            "phone login can send and verify a real SMS code on the same iOS 26.5 review build",
        ],
        "doesNotProve": [
            "SMS provider console evidence exists",
            "SMS live-send proof is archived",
            "review recovery-key account is valid",
            "WeChat login passed",
            "Submit for Review is allowed",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "RD-14": {
        "target": "RealDevice/RD-14-wechat-login.png",
        "proves": [
            "WeChat authorization opens and returns to the app on the same iOS 26.5 review build",
        ],
        "doesNotProve": [
            "WeChat Open Platform evidence exists",
            "Universal Link AASA proof is archived",
            "server AppSecret proof is green",
            "phone login passed",
            "Submit for Review is allowed",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "RD-15": {
        "target": "RealDevice/RD-15-account-delete.png",
        "proves": [
            "cloud account deletion flow completes on the same iOS 26.5 review build",
            "old token invalidation and sync/photo deletion boundary are verified for the review account",
        ],
        "doesNotProve": [
            "production storage proof is green",
            "OBS deletion policy evidence is archived",
            "review recovery-key login passed",
            "phone or WeChat login passed",
            "Submit for Review is allowed",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
}
APP_REVIEW_TEST_ACCOUNT_RD_TARGETS = {
    "RD-10": (
        "RealDevice/RD-10-recovery-login.png",
        "recovery-key account login succeeded",
        "same TestFlight or Xcode signed iOS 26.5 build",
        "recovery key",
    ),
    "RD-13": (
        "RealDevice/RD-13-phone-login.png",
        "real SMS code can be sent and verified",
        "07-sms-provider evidence and SMS live-send proof exist",
        "complete phone number",
    ),
    "RD-14": (
        "RealDevice/RD-14-wechat-login.png",
        "WeChat authorization opens and returns to the app",
        "08-wechat-open-platform evidence",
        "Universal Link",
        "AppSecret",
    ),
    "RD-15": (
        "RealDevice/RD-15-account-delete.png",
        "cloud account deletion completed",
        "old token invalidated",
        "cloud sync and photo object deletion boundary verified",
    ),
}
APP_REVIEW_TEST_ACCOUNT_LIFECYCLE_MARKERS = (
    "redacted review account",
    "fictional baby profile",
    "fictional baby records",
    "Verify recovery-key login",
    "Verify sync and restore path",
    "Verify cloud account deletion invalidates old token",
    "Do not use phone or WeChat as the primary review account",
    "Do not use debug code",
)
APP_REVIEW_TEST_ACCOUNT_STOP_CONDITIONS = {
    "missingRecoveryKeyEnv": (
        ".env.xnp-review-account",
        "XNP_REVIEW_RECOVERY_KEY",
        "Do not fill App Review Information",
    ),
    "redactedEvidenceMissingOrSecret": (
        "11-test-account-redacted.json",
        "containsSecret is not false",
        "secret/token/password/code",
    ),
    "recoveryVerificationFailed": (
        "recoveryVerified",
        "syncSeeded",
        "Do not submit Review Information",
    ),
    "phoneProviderNotLive": (
        "RD-13",
        "07-sms-provider",
        "SMS live-send proof",
    ),
    "wechatProviderNotLive": (
        "RD-14",
        "08-wechat-open-platform",
        "Release wx URL Scheme",
    ),
    "screenshotLeaksCredential": (
        "RD-10/RD-13/RD-14/RD-15",
        "recovery key",
        "complete phone number",
        "AppSecret",
    ),
    "accountDeletionUnverified": (
        "RD-15",
        "old token invalidation",
        "sync/photo deletion",
    ),
    "ios265RealDeviceEvidenceMissing": (
        "iOS 26.5",
        "Do not use simulator, iOS 27, or another build",
    ),
    "productionReadinessStillRed": (
        "production-readiness.json",
        "Do not submit for review",
    ),
    "appStoreEvidenceIncomplete": (
        "app-store-evidence.json",
        "Do not submit for review",
    ),
}
APP_REVIEW_TEST_ACCOUNT_REDACTION_MARKERS = (
    "recovery key",
    "verification code",
    "complete phone number",
    "Apple ID email",
    "contact full phone number",
    "token",
    "Bearer token",
    "AppSecret",
    "SMS secret",
    "OBS AK/SK",
    "object storage key",
    "real baby photo",
    "debug code",
)
APP_REVIEW_TEST_ACCOUNT_POST_FILL_GATES = (
    "check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
    "check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json",
    "check_review_notes.py --output Backend/proof/review-notes.json",
    "check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260627T-current.json",
    "check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
APP_REVIEW_TEST_ACCOUNT_COMPLETION_MARKERS = (
    "review-test-account-packet-not-evidence",
    "not submission permission",
    "does not prove App Review Information has been filled",
    "does not store the recovery key",
    "does not prove phone or WeChat login",
    "does not replace iOS 26.5 real-device regression",
    "app-store-evidence.json ready=true",
    "production-readiness.json ready=true",
    "launch-objective-audit.json ready=true",
)
PRIVACY_ANSWERS_MARKERS = (
    "# 小奶瓶 App Store Privacy 逐项答案表",
    "日期：2026-06-27",
    "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
    "app-privacy-details",
    "overview-of-app-privacy-details",
    "Data Used to Track You",
    "No",
    "Tracking Domains",
    "None",
    "PrivacyInfo.xcprivacy",
    "Third-Party Advertising",
    "Third-Party Analytics",
    "Kids Category",
    "Privacy Policy URL",
    "https://api.mewpow.com/xiaonaiping/privacy",
    "Data Linked to You",
    "Identifiers",
    "Contact Info",
    "User Content",
    "Photos or Videos",
    "Health and Fitness",
    "Usage Data",
    "Data Not Linked to You",
    "Diagnostics",
    "Not Collected",
    "Location",
    "Contacts",
    "Purchases",
    "Advertising Data",
    "Health and Fitness 边界",
    "用户主动输入",
    "不接入 HealthKit、传感器、医院系统或第三方健康数据源",
    "status display only",
    "不生成健康建议、压力提醒、喂养建议或医疗判断",
    "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
    "Usage Data 边界",
    "baby content",
    "photo keys",
    "phone numbers",
    "WeChat identifiers",
    "advertising ID",
    "device fingerprint",
    "check_ios_release_readiness.py",
    "check_diagnostics_redaction.py",
    "04-privacy-label.png",
)
VERSION_RELEASE_SETTINGS_MARKERS = (
    "# 小奶瓶 App Store Version 与发布设置表",
    "日期：2026-06-27",
    "Version Information",
    "Version",
    "`1.0`",
    "Build",
    "CURRENT_PROJECT_VERSION=1",
    "TestFlight 构建处理完成",
    "What's New",
    "Promotional Text",
    "Description",
    "Keywords",
    "Support URL",
    "Marketing URL",
    "留空",
    "Pricing and Availability",
    "Price",
    "Free",
    "Specific Countries or Regions -> China mainland",
    "China mainland only",
    "Do not select",
    "Hong Kong, United States, all other regions",
    "02-mainland-availability.png",
    "Version Release",
    "Manually release this version after App Review approval",
    "Phased release",
    "Off",
    "审核通过不等于可以自动上线",
    "Export Compliance",
    "Uses encryption",
    "Apple 平台安全、Keychain、HTTPS 和标准系统/网络加密",
    "Custom cryptography",
    "No",
    "VPN",
    "DRM",
    "End-to-end encrypted messaging",
    "Advertising Identifier / Tracking",
    "Uses IDFA",
    "Tracking",
    "Third-party advertising",
    "Third-party analytics SDK",
    "Content Rights",
    "User-added photos",
    "不使用真实宝宝照片",
    "05-signed-archive.png",
    "06-testflight.png",
    "12-real-device-regression.md",
    "check_signed_archive_testflight_materials.py",
)
FINAL_ENTRY_AUDIT_MARKERS = (
    "# 小奶瓶 App Store Connect 终填审计表",
    "日期：2026-06-27",
    "同一天同一轮",
    "App Store Connect 选中的 build",
    "App 版本",
    "Build 号",
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "App 名称",
    "小奶瓶",
    "副标题",
    "温柔记录宝宝每一天",
    "描述",
    "关键词",
    "主类别：生活",
    "第二类别：留空",
    "年龄分级",
    "APP_STORE_AGE_RATING_ANSWERS_20260627.md",
    "隐私政策 URL",
    EXPECTED_PRIVACY_URL,
    "技术支持 URL",
    EXPECTED_SUPPORT_URL,
    "审核备注",
    "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
    "APP_STORE_REVIEW_INFORMATION_20260627.md",
    "APP_STORE_PRIVACY_ANSWERS_20260627.md",
    "APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
    "01-company-account.png",
    "02-mainland-availability.png",
    "03-app-filing",
    "04-privacy-label.png",
    "05-signed-archive.png",
    "06-testflight.png",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "09-obs-policy.png",
    "10-final-screenshots/",
    "11-test-account-redacted.json",
    "12-real-device-regression.md",
    "17-age-rating-result",
    "## 人工填写后回填验收模板",
    "App Store Connect 页面值已逐项对照",
    "App 名称 / 副标题 / 描述 / 关键词 / 主类别 / 第二类别",
    "隐私政策 URL / 技术支持 URL / 用户协议 URL",
    "App Privacy / 年龄分级 / 审核备注",
    "App Store Connect 选中 build 与 `06-testflight.png`、`12-real-device-regression.md` 和 `APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md` 一致",
    "截图上传顺序与 `10-final-screenshots/`、`APP_STORE_EVIDENCE_CHECKLIST_20260627.md` 和 `SCREENSHOT_PLAN.md` 一致",
    "价格、首发地区和手动发布设置与 `APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md` 和 `02-mainland-availability.png` 一致",
    "若任一页面值与源文件不一致，先修正 App Store Connect 或源文件，再重跑本页复跑命令；不提交审核",
    "回填记录不得写入恢复密钥、验证码、AppSecret、D-U-N-S 编码完整值、Apple ID 邮箱、完整手机号或测试员邮箱",
    "check_app_store_connect_materials.py",
    "check_app_store_evidence.py --allow-incomplete",
    "check_launch_objective_audit.py --allow-incomplete",
    "production-readiness.json",
    "launch-objective-audit.json",
    "不得写入恢复密钥",
    "不得写入验证码",
    "不得写入 AppSecret",
    "不得写入 D-U-N-S 编码完整值",
    "不得写入证书私钥",
    "不得声称完成",
)
FINAL_ENTRY_PAGE_EVIDENCE_MARKERS = (
    "## App Store Connect 页面回填证据索引",
    "Docs/08_Release/AppStoreEvidence/AppStoreConnect/",
    "不替代 `01-company-account.png`",
    "`02-mainland-availability.png`",
    "`04-privacy-label.png`",
    "`05-signed-archive.png`",
    "`06-testflight.png`",
    "`12-real-device-regression.md`",
    "`17-age-rating-result`",
    "AppStoreConnect/ASC-01-app-information.png",
    "App 名称、副标题、Bundle ID、SKU、主类别生活、第二类别留空、版权、隐私政策 URL、技术支持 URL、用户协议 URL",
    "AppStoreConnect/ASC-02-version-information.png",
    "Version `1.0`、选中 build、描述、关键词、新版本说明、截图上传顺序",
    "AppStoreConnect/ASC-03-pricing-availability-release.png",
    "Free、Specific Countries or Regions -> China mainland、手动发布、Phased release off",
    "AppStoreConnect/ASC-04-app-privacy.png",
    "Tracking 为 No、Data Linked to You / Data Not Linked to You、Health and Fitness / Usage Data / Diagnostics",
    "AppStoreConnect/ASC-05-age-rating.png",
    "Kids Category 未选择、Regulated Medical Device 为 No",
    "AppStoreConnect/ASC-06-review-information.png",
    "Sign-in required、恢复密钥测试账号说明、审核备注、联系人字段已填",
    "AppStoreConnect/ASC-07-build-testflight-link.png",
    "选中 build、TestFlight 构建状态、版本和 build 与真机回归一致",
    "AppStoreConnect/ASC-08-submit-review-precheck.png",
    "Submit for Review 前页面无未处理警告",
    "必须保留",
    "必须遮挡",
    "恢复密钥",
    "验证码",
    "完整手机号",
    "AppSecret",
    "证书私钥",
    "Apple ID 邮箱",
    "check_app_store_connect_materials.py",
    "check_app_store_evidence.py --allow-incomplete",
    "check_launch_objective_audit.py --allow-incomplete",
    "`AppStoreConnect/ASC-01-app-information.png` 到 `AppStoreConnect/ASC-08-submit-review-precheck.png` 已按页面回填证据索引归档并脱敏",
)
ASC_PAGE_EVIDENCE_DOES_NOT_REPLACE = (
    "01-company-account.png",
    "02-mainland-availability.png",
    "04-privacy-label.png",
    "05-signed-archive.png",
    "06-testflight.png",
    "12-real-device-regression.md",
    "17-age-rating-result",
)
ASC_PAGE_EVIDENCE_ITEMS = {
    "AppStoreConnect/ASC-01-app-information.png": {
        "captures": (
            "App 名称",
            "副标题",
            "Bundle ID",
            "SKU",
            "主类别生活",
            "第二类别留空",
            "版权",
            "隐私政策 URL",
            "技术支持 URL",
            "用户协议 URL",
        ),
        "redact": (
            "Apple ID 邮箱",
            "电话",
            "付款信息",
            "D-U-N-S 编码完整值",
        ),
        "crossCheck": (
            "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
            "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
            "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        ),
    },
    "AppStoreConnect/ASC-02-version-information.png": {
        "captures": (
            "Version 1.0",
            "选中 build",
            "描述",
            "关键词",
            "新版本说明",
            "截图上传顺序",
        ),
        "redact": (
            "测试员邮箱",
            "Apple ID 邮箱",
            "恢复密钥",
            "验证码",
        ),
        "crossCheck": (
            "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
            "Docs/08_Release/AppStoreEvidence/10-final-screenshots/",
            "06-testflight.png",
        ),
    },
    "AppStoreConnect/ASC-03-pricing-availability-release.png": {
        "captures": (
            "Free",
            "Specific Countries or Regions -> China mainland",
            "手动发布",
            "Phased release off",
        ),
        "redact": (
            "付款信息",
            "税务信息",
            "无关地区账号资料",
        ),
        "crossCheck": (
            "02-mainland-availability.png",
            "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
        ),
    },
    "AppStoreConnect/ASC-04-app-privacy.png": {
        "captures": (
            "Tracking 为 No",
            "Data Linked to You",
            "Data Not Linked to You",
            "Health and Fitness",
            "Usage Data",
            "Diagnostics",
        ),
        "redact": (
            "Apple ID 邮箱",
            "账号私密信息",
        ),
        "crossCheck": (
            "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md",
            "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
            "04-privacy-label.png",
        ),
    },
    "AppStoreConnect/ASC-05-age-rating.png": {
        "captures": (
            "4+ 或 App Store Connect 自动计算结果",
            "Kids Category 未选择",
            "Regulated Medical Device 为 No",
        ),
        "redact": (
            "Apple ID 邮箱",
            "电话",
            "付款信息",
        ),
        "crossCheck": (
            "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
            "17-age-rating-result",
        ),
    },
    "AppStoreConnect/ASC-06-review-information.png": {
        "captures": (
            "Sign-in required",
            "恢复密钥测试账号说明",
            "审核备注",
            "联系人字段已填",
        ),
        "redact": (
            "恢复密钥",
            "验证码",
            "完整手机号",
            "Apple ID 邮箱",
            "联系人完整电话",
        ),
        "crossCheck": (
            "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
            "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
        ),
    },
    "AppStoreConnect/ASC-07-build-testflight-link.png": {
        "captures": (
            "选中 build",
            "TestFlight 构建状态",
            "版本和 build 与真机回归一致",
        ),
        "redact": (
            "测试员邮箱",
            "Apple ID 邮箱",
            "内部备注",
        ),
        "crossCheck": (
            "06-testflight.png",
            "12-real-device-regression.md",
        ),
    },
    "AppStoreConnect/ASC-08-submit-review-precheck.png": {
        "captures": (
            "Submit for Review 前页面无未处理警告",
            "所有字段与本审计表一致",
        ),
        "redact": (
            "恢复密钥",
            "验证码",
            "完整手机号",
            "AppSecret",
            "证书私钥",
            "Apple ID 邮箱",
        ),
        "crossCheck": (
            "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
            "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
            "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
        ),
    },
}
FIELD_AUDIT_MATRIX_ITEMS = {
    "appName": (
        "App 名称",
        EXPECTED_APP_NAME,
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-01-app-information.png",
        "01-company-account.png",
        "D-U-N-S delivered",
        "Apple Developer Organization enrollment",
        "Apple ID 邮箱",
        "D-U-N-S 编码完整值",
    ),
    "subtitle": (
        "副标题",
        EXPECTED_SUBTITLE,
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-01-app-information.png",
        "Backend/proof/app-store-connect-materials.json",
        "Apple ID 邮箱",
    ),
    "description": (
        "描述",
        "versionInformation.description",
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-02-version-information.png",
        "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
        "Backend/proof/app-store-evidence.json",
        "本地优先",
        "不提供医疗诊断",
        "疫苗模板仅用于记录和提醒",
        "手动顺延下一次提醒",
        "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
        "恢复密钥",
        "验证码",
        "完整手机号",
    ),
    "keywords": (
        "关键词",
        "宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册",
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-02-version-information.png",
        "Backend/proof/app-store-connect-materials.json",
        "100 UTF-8 bytes",
        "73 bytes",
        "Apple ID 邮箱",
    ),
    "promotionalText": (
        "宣传文本",
        "versionInformation.promotionalText",
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-02-version-information.png",
        "Backend/proof/app-store-connect-materials.json",
        "低负担",
        "记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片",
        "不写医疗诊断",
        "不写喂养建议",
        "Apple ID 邮箱",
    ),
    "whatsNew": (
        "新版本说明",
        "versionInformation.whatsNew",
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
        "AppStoreConnect/ASC-02-version-information.png",
        "喝奶提醒与手动顺延",
        "恢复密钥账号同步恢复",
        "云端账号删除",
        "Apple ID 邮箱",
    ),
    "category": (
        "分类",
        "主类别：生活；第二类别：留空",
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
        "AppStoreConnect/ASC-01-app-information.png",
        "Backend/proof/app-store-connect-materials.json",
        "不选择健康健美",
        "不选择 Kids 类目",
        "Apple ID 邮箱",
    ),
    "ageRating": (
        "年龄分级",
        "预期 4+；以 App Store Connect 自动计算结果为准",
        "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
        "AppStoreConnect/ASC-05-age-rating.png",
        "17-age-rating-result",
        "Kids Category 未选择",
        "Regulated Medical Device 为 No",
        "not a medical device",
        "Apple ID 邮箱",
        "电话",
    ),
    "privacyPolicyUrl": (
        "隐私政策 URL",
        EXPECTED_PRIVACY_URL,
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        "Backend/static/privacy.html",
        "AppStoreConnect/ASC-01-app-information.png",
        "AppStoreConnect/ASC-04-app-privacy.png",
        "04-privacy-label.png",
        "Backend/proof/public-pages.json",
        "Apple ID 邮箱",
        "账号私密信息",
    ),
    "supportUrl": (
        "技术支持 URL",
        EXPECTED_SUPPORT_URL,
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        "Backend/static/support.html",
        "AppStoreConnect/ASC-01-app-information.png",
        "Backend/proof/public-pages.json",
        "Apple ID 邮箱",
    ),
    "termsUrl": (
        "用户协议 URL",
        EXPECTED_TERMS_URL,
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Backend/static/terms.html",
        "AppStoreConnect/ASC-01-app-information.png",
        "Backend/proof/public-pages.json",
        "Apple ID 邮箱",
    ),
    "reviewNotes": (
        "审核备注",
        "reviewNotes.text",
        "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
        "AppStoreConnect/ASC-06-review-information.png",
        "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
        "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
        "Backend/proof/app-store-evidence.json",
        "不提供医疗诊断",
        "不构成喂养建议",
        "手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充",
        "正式提交包不提供、不依赖 debug code",
        "恢复密钥",
        "验证码",
        "完整手机号",
        "AppSecret",
        "Apple ID 邮箱",
    ),
}
FIELD_AUDIT_MATRIX_ROW_IDS = tuple(FIELD_AUDIT_MATRIX_ITEMS.keys())
FIELD_AUDIT_MATRIX_EXACT_VALUES = {
    "appName": {"field": "App 名称", "value": EXPECTED_APP_NAME},
    "subtitle": {"field": "副标题", "value": EXPECTED_SUBTITLE},
    "description": {"field": "描述", "valueSource": "versionInformation.description"},
    "keywords": {"field": "关键词", "value": "宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册"},
    "promotionalText": {"field": "宣传文本", "valueSource": "versionInformation.promotionalText"},
    "whatsNew": {"field": "新版本说明", "valueSource": "versionInformation.whatsNew"},
    "category": {"field": "分类", "value": "主类别：生活；第二类别：留空"},
    "ageRating": {"field": "年龄分级", "value": "预期 4+；以 App Store Connect 自动计算结果为准"},
    "privacyPolicyUrl": {"field": "隐私政策 URL", "value": EXPECTED_PRIVACY_URL},
    "supportUrl": {"field": "技术支持 URL", "value": EXPECTED_SUPPORT_URL},
    "termsUrl": {"field": "用户协议 URL", "value": EXPECTED_TERMS_URL},
    "reviewNotes": {"field": "审核备注", "valueSource": "reviewNotes.text"},
}
FIELD_AUDIT_MATRIX_RULE_MARKERS = (
    "source-locked-before-submit",
    "只能从本矩阵列出的源文件复制",
    "不得只改 App Store Connect 页面而不回写源文件",
    "页面截图只证明字段已回填",
    "不替代外部平台",
    "TestFlight",
    "签名归档",
    "备案",
    "隐私标签",
    "iOS 26.5 真机回归证据",
    "check_app_store_connect_materials.py",
    "check_app_store_submission_packet.py",
    "check_app_store_evidence.py --allow-incomplete",
)
FIELD_FREEZE_RULE_MARKERS = (
    "field-freeze-plan-not-evidence",
    "App Store Connect 草稿字段冻结",
    "只能从 sourceFiles 复制",
    "不得现场改字后只改 App Store Connect 页面",
    "任一字段改字必须回写源文件",
    "ASC 页面截图只证明回填",
    "不能替代 D-U-N-S、Archive、TestFlight、短信、微信、OBS、备案、隐私标签、最终截图或 iOS 26.5 真机回归证据",
)
FIELD_FREEZE_SOURCE_FILES = {
    "draftJson": "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
    "fillSheet": "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
    "copyPastePacket": "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
    "finalEntryAudit": "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
    "privacyAnswers": "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md",
    "ageRatingAnswers": "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
    "reviewInformation": "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
    "entrySessionPacket": "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
    "appStoreSubmissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
}
FIELD_FREEZE_POST_GATES = (
    "check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
    "check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
    "check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
FIELD_FREEZE_COMPLETION_MARKERS = (
    "field-freeze-plan-not-evidence",
    "not App Store Connect live evidence",
    "not submission permission",
    "canSubmitFromThisPacket=false",
    "production-readiness.json ready=true",
    "launch-objective-audit.json ready=true",
    "app-store-evidence.json ready=true",
)
FIELD_FREEZE_BUDGET_SPECS = (
    ("appName", "App 名称", "characters", APP_NAME_MAX_CHARS, "appInformation.appName"),
    ("subtitle", "副标题", "characters", SUBTITLE_MAX_CHARS, "appInformation.subtitle"),
    ("keywords", "关键词", "utf8Bytes", KEYWORDS_MAX_BYTES, "versionInformation.keywords"),
    ("promotionalText", "宣传文本", "characters", PROMOTIONAL_TEXT_MAX_CHARS, "versionInformation.promotionalText"),
    ("description", "描述", "characters", LONG_TEXT_MAX_CHARS, "versionInformation.description"),
    ("whatsNew", "新版本说明", "characters", LONG_TEXT_MAX_CHARS, "versionInformation.whatsNew"),
    ("reviewNotes", "审核备注", "characters", LONG_TEXT_MAX_CHARS, "reviewNotes.text"),
)
FIELD_FREEZE_BUDGET_IDS = tuple(spec[0] for spec in FIELD_FREEZE_BUDGET_SPECS)
FIELD_FREEZE_SOURCE_LOCK_MATCH_KEYS = (
    "field",
    "value",
    "valueSource",
    "sourceFiles",
    "ascEvidence",
    "blockerProofs",
    "mustKeepBoundary",
    "redact",
)
FIELD_FREEZE_SOURCE_LOCK_STATUS = "locked-from-draft-not-live-evidence"
FIELD_FREEZE_PASTE_SEQUENCE_FIELDS = (
    "id",
    "order",
    "ascPage",
    "ascField",
    "inputType",
    "sourceValuePath",
    "copySource",
    "ascEvidence",
    "prePasteCheck",
    "postPasteGate",
    "pasteRequired",
    "initialStatus",
)
FIELD_FREEZE_PASTE_SEQUENCE_SPECS = (
    {
        "id": "appName",
        "order": 1,
        "ascPage": "ASC-01 App Information",
        "ascField": "App Name",
        "inputType": "text",
        "sourceValuePath": "appInformation.appName",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
        "prePasteCheck": "fieldSourceLockMatrix.appName.matchesDraftRow=true",
    },
    {
        "id": "subtitle",
        "order": 2,
        "ascPage": "ASC-01 App Information",
        "ascField": "Subtitle",
        "inputType": "text",
        "sourceValuePath": "appInformation.subtitle",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
        "prePasteCheck": "fieldSourceLockMatrix.subtitle.matchesDraftRow=true",
    },
    {
        "id": "description",
        "order": 3,
        "ascPage": "ASC-02 Version Information",
        "ascField": "Description",
        "inputType": "textarea",
        "sourceValuePath": "versionInformation.description",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-02-version-information.png"],
        "prePasteCheck": "fieldBudgetMatrix.description.withinLimit=true",
    },
    {
        "id": "keywords",
        "order": 4,
        "ascPage": "ASC-02 Version Information",
        "ascField": "Keywords",
        "inputType": "keyword-list",
        "sourceValuePath": "versionInformation.keywords",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-02-version-information.png"],
        "prePasteCheck": "fieldBudgetMatrix.keywords.withinLimit=true",
    },
    {
        "id": "promotionalText",
        "order": 5,
        "ascPage": "ASC-02 Version Information",
        "ascField": "Promotional Text",
        "inputType": "textarea",
        "sourceValuePath": "versionInformation.promotionalText",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-02-version-information.png"],
        "prePasteCheck": "fieldBudgetMatrix.promotionalText.withinLimit=true",
    },
    {
        "id": "whatsNew",
        "order": 6,
        "ascPage": "ASC-02 Version Information",
        "ascField": "What's New",
        "inputType": "textarea",
        "sourceValuePath": "versionInformation.whatsNew",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-02-version-information.png"],
        "prePasteCheck": "fieldBudgetMatrix.whatsNew.withinLimit=true",
    },
    {
        "id": "category",
        "order": 7,
        "ascPage": "ASC-01 App Information",
        "ascField": "Primary Category / Secondary Category",
        "inputType": "category-selector",
        "sourceValuePath": "appInformation.primaryCategory + appInformation.secondaryCategory",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
        "prePasteCheck": "fieldSourceLockMatrix.category.matchesDraftRow=true",
    },
    {
        "id": "ageRating",
        "order": 8,
        "ascPage": "ASC-05 Age Rating",
        "ascField": "Age Rating questionnaire",
        "inputType": "questionnaire",
        "sourceValuePath": "ageRating.answerSheet",
        "copySource": "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-05-age-rating.png", "17-age-rating-result.png 或 .pdf"],
        "prePasteCheck": "fieldSourceLockMatrix.ageRating.matchesDraftRow=true",
    },
    {
        "id": "privacyPolicyUrl",
        "order": 9,
        "ascPage": "ASC-01 App Information / ASC-04 App Privacy",
        "ascField": "Privacy Policy URL",
        "inputType": "url",
        "sourceValuePath": "appInformation.privacyPolicyUrl",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "ascEvidence": [
            "AppStoreConnect/ASC-01-app-information.png",
            "AppStoreConnect/ASC-04-app-privacy.png",
        ],
        "prePasteCheck": "fieldSourceLockMatrix.privacyPolicyUrl.matchesDraftRow=true",
    },
    {
        "id": "supportUrl",
        "order": 10,
        "ascPage": "ASC-01 App Information",
        "ascField": "Support URL",
        "inputType": "url",
        "sourceValuePath": "appInformation.supportUrl",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
        "prePasteCheck": "fieldSourceLockMatrix.supportUrl.matchesDraftRow=true",
    },
    {
        "id": "termsUrl",
        "order": 11,
        "ascPage": "ASC-01 App Information",
        "ascField": "License Agreement URL",
        "inputType": "url",
        "sourceValuePath": "appInformation.termsUrl",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
        "prePasteCheck": "fieldSourceLockMatrix.termsUrl.matchesDraftRow=true",
    },
    {
        "id": "reviewNotes",
        "order": 12,
        "ascPage": "ASC-06 App Review Information",
        "ascField": "Review Notes",
        "inputType": "review-notes-textarea",
        "sourceValuePath": "reviewNotes.text",
        "copySource": "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "ascEvidence": ["AppStoreConnect/ASC-06-review-information.png"],
        "prePasteCheck": "fieldBudgetMatrix.reviewNotes.withinLimit=true",
    },
)
FIELD_FREEZE_PASTE_SEQUENCE_IDS = tuple(item["id"] for item in FIELD_FREEZE_PASTE_SEQUENCE_SPECS)
FIELD_FREEZE_PASTE_SEQUENCE_POST_GATE = (
    "check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json"
)
FINAL_SUBMIT_GUARD_MARKERS = (
    "## Submit for Review 总守卫",
    "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
    "Backend/proof/launch-objective-audit.json",
    "`ready=true`",
    "Backend/proof/production-readiness.json",
    "Backend/proof/app-store-evidence.json",
    "Backend/proof/testflight-regression-plan.json",
    "`passed=true`",
    "Backend/proof/provider-evidence-materials.json",
    "Backend/proof/mainland-filing-materials.json",
    "Backend/proof/signed-archive-testflight-materials.json",
    "真实 App Store / 外部平台 / TestFlight / iOS 26.5 真机证据均已归档",
    "`passed=false`",
    "`failedRequiredChecks` / `missingEvidence`",
    "不点击 Submit for Review",
)
FINAL_FIELD_SOURCE_LOCK_MARKERS = (
    "## 终填字段源文件一致性锁",
    "App Store Connect 页面值不能成为唯一来源",
    "人工粘贴时只允许从下表源文件复制",
    "先修正 App Store Connect 或源文件",
    "check_app_store_connect_materials.py",
    "check_app_store_submission_packet.py",
    "App 名称 / 副标题 / 主类别 / 第二类别",
    "关键词 / 描述 / 审核备注",
    "年龄分级",
    "隐私政策 URL / 技术支持 URL / 用户协议 URL",
    "App Privacy",
    "Sign-In Information",
    "版本发布设置",
    "截图上传顺序",
    "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
    "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
    "APP_STORE_AGE_RATING_ANSWERS_20260627.md",
    "APP_STORE_PRIVACY_LABEL.json",
    "Backend/static/privacy.html",
    "Backend/static/support.html",
    "Backend/static/terms.html",
    "APP_STORE_PRIVACY_ANSWERS_20260627.md",
    "APP_STORE_REVIEW_INFORMATION_20260627.md",
    "11-test-account-redacted.json",
    "APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
    "SCREENSHOT_PLAN.md",
    "APP_STORE_EVIDENCE_CHECKLIST_20260627.md",
    "10-final-screenshots/PROVENANCE.json",
    "AppStoreConnect/ASC-01-app-information.png",
    "AppStoreConnect/ASC-02-version-information.png",
    "AppStoreConnect/ASC-04-app-privacy.png",
    "AppStoreConnect/ASC-05-age-rating.png",
    "AppStoreConnect/ASC-06-review-information.png",
    "AppStoreConnect/ASC-07-build-testflight-link.png",
    "不得只改 App Store Connect 页面而不回写源文件",
    "任一字段改字后",
    "回填截图只证明页面已经填入",
    "不替代源文件、外部后台证据、TestFlight 或真机回归",
)
SCREENSHOT_UPLOAD_MATRIX_MARKERS = (
    "## App Store Connect 截图上传矩阵",
    "https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/",
    "一到十张",
    "`.jpeg`、`.jpg`、`.png`",
    "iPhone 6.9\" display",
    "1260 x 2736",
    "1290 x 2796",
    "1320 x 2868",
    "当前候选为 iPhone 17 Pro Max / iPhone 6.9\" display / 1320 x 2868",
    "不能把 Debug simulator 候选图声称为 TestFlight、签名真机或 App Store Connect 上传最终证据",
    "Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json",
    "AppStoreConnect/ASC-02-version-information.png",
    "TestFlight 或签名真机包最终截图",
    "iOS 26.5",
    "TARGETED_DEVICE_FAMILY=1",
    "如果 App Store Connect 要求 iPad 截图，先复核工程 target family",
)
ENTRY_SESSION_PACKET_REFERENCE_MARKERS = (
    "APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
    "entry-session-plan-not-evidence",
    "不是 App Store Connect 人工证据",
    "不能作为提交许可",
)
ENTRY_SESSION_TARGET_PAGE_EVIDENCE_FILES = {
    "appInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-01-app-information.png",
    "versionInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-02-version-information.png",
    "pricingAvailabilityRelease": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-03-pricing-availability-release.png",
    "appPrivacy": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-04-app-privacy.png",
    "ageRating": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-05-age-rating.png",
    "reviewInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-06-review-information.png",
    "buildTestflightLink": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-07-build-testflight-link.png",
    "submitReviewPrecheck": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-08-submit-review-precheck.png",
}
ENTRY_SESSION_PAGE_EVIDENCE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsEntrySession", False),
    ("sourceIsAllowedAppStoreConnectEvidenceRoot", False),
    ("matchesFieldSourceLocks", False),
    ("realPageEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
ENTRY_SESSION_FIELD_LOCK_REQUIREMENTS = {
    "appName": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-01-app-information.png",
        "D-U-N-S 编码完整值",
    ),
    "subtitle": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-01-app-information.png",
    ),
    "description": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-02-version-information.png",
        "手动顺延下一次提醒",
        "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
    ),
    "keywords": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-02-version-information.png",
        "100 UTF-8 bytes",
    ),
    "promotionalText": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "AppStoreConnect/ASC-02-version-information.png",
        "低负担",
        "不写医疗诊断",
        "不写喂养建议",
    ),
    "whatsNew": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
        "AppStoreConnect/ASC-02-version-information.png",
        "喝奶提醒与手动顺延",
        "恢复密钥账号同步恢复",
    ),
    "category": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
        "AppStoreConnect/ASC-01-app-information.png",
        "不选择 Kids 类目",
    ),
    "privacyPolicyUrl": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_PRIVACY_LABEL.json",
        "Backend/static/privacy.html",
        "AppStoreConnect/ASC-04-app-privacy.png",
    ),
    "supportUrl": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Backend/static/support.html",
        "AppStoreConnect/ASC-01-app-information.png",
    ),
    "termsUrl": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "Backend/static/terms.html",
        "AppStoreConnect/ASC-01-app-information.png",
    ),
    "appPrivacy": (
        "APP_STORE_PRIVACY_ANSWERS_20260627.md",
        "APP_STORE_PRIVACY_LABEL.json",
        "AppStoreConnect/ASC-04-app-privacy.png",
        "04-privacy-label.png",
    ),
    "ageRating": (
        "APP_STORE_AGE_RATING_ANSWERS_20260627.md",
        "APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
        "AppStoreConnect/ASC-05-age-rating.png",
        "Regulated Medical Device 为 No",
    ),
    "reviewNotes": (
        "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
        "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
        "APP_STORE_REVIEW_INFORMATION_20260627.md",
        "AppStoreConnect/ASC-06-review-information.png",
        "正式提交包不提供、不依赖 debug code",
    ),
    "signInInformation": (
        "APP_STORE_REVIEW_INFORMATION_20260627.md",
        "11-test-account-redacted.json",
        "AppStoreConnect/ASC-06-review-information.png",
        "恢复密钥",
    ),
    "versionReleaseSettings": (
        "APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
        "AppStoreConnect/ASC-03-pricing-availability-release.png",
        "AppStoreConnect/ASC-07-build-testflight-link.png",
        "手动发布",
    ),
    "screenshots": (
        "SCREENSHOT_PLAN.md",
        "APP_STORE_EVIDENCE_CHECKLIST_20260627.md",
        "UPLOAD_PROVENANCE.json",
        "iPhone 6.9",
        "iOS 26.5",
    ),
}
ENTRY_SESSION_SEQUENCE_IDS = (
    "openAppleDeveloperAccountContext",
    "createOrOpenAppRecord",
    "fillAppInformation",
    "fillPricingAvailability",
    "fillVersionInformation",
    "fillAppPrivacy",
    "fillAgeRating",
    "fillReviewInformation",
    "attachBuildAndScreenshots",
    "capturePostFillPages",
    "runPostEntryGates",
)
ENTRY_SESSION_STOP_CONDITIONS = (
    "companyAccountEvidenceMissing",
    "dunsOrTeamIdMissing",
    "appRecordCreatedUnderWrongEntity",
    "bundleIdOrSkuMismatch",
    "keywordsOverLimit",
    "privacyUrlMismatch",
    "privacyLabelMissing",
    "ageRatingResultMissing",
    "reviewAccountSecretLeak",
    "signedArchiveMissing",
    "buildOrTestFlightMissing",
    "finalScreenshotsMissing",
    "smsProviderMissing",
    "wechatOpenPlatformMissing",
    "mainlandFilingMissing",
    "obsPolicyMissing",
    "ios265RealDeviceRegressionMissing",
    "productionReadinessStillRed",
    "launchObjectiveAuditStillRed",
    "appStoreEvidenceIncomplete",
    "xiaonaipingSubmitProofsNotReady",
)
ENTRY_SESSION_REDACTION_MARKERS = (
    "Apple ID 邮箱",
    "联系电话",
    "付款信息",
    "税务信息",
    "恢复密钥",
    "验证码",
    "完整手机号",
    "D-U-N-S 编码完整值",
    "AppSecret",
    "证书私钥",
    "token",
    "测试员邮箱",
)
ENTRY_SESSION_POST_ENTRY_GATES = (
    "check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
    "check_app_store_connect_evidence_materials.py --output Backend/proof/app-store-connect-evidence-materials.json",
    "check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
    "check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    "check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
    "check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260627T-current.json",
    "check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
ENTRY_SESSION_COMPLETION_MARKERS = (
    "entry-session-plan-not-evidence",
    "does not prove App Store Connect has been filled",
    "does not replace external platform evidence",
    "cannot authorize Submit for Review",
    "production-readiness.json ready=true",
    "launch-objective-audit.json ready=true",
    "app-store-evidence.json ready=true",
    "testflight-regression-plan.json passed=true",
    "provider-evidence-materials.json passed=true",
    "mainland-filing-materials.json passed=true",
    "signed-archive-testflight-materials.json passed=true",
    "iOS 26.5 real-device evidence",
    "不是 App Store Connect 人工证据",
    "不能作为提交许可",
)
ENTRY_SESSION_FORBIDDEN_COMPLETION_MARKERS = (
    "cross-app canSubmit=true",
    "cross-app-submission-readiness",
    "check-cross-app-submit-ready",
    "canSubmit=true",
)
SUBMIT_REVIEW_PREFLIGHT_SOURCE_FILES = {
    "draftJson": "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
    "fieldFreezePacket": "Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260627.json",
    "entrySessionPacket": "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
    "finalEntryAudit": "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
    "submissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
    "appStoreEvidenceProof": "Backend/proof/app-store-evidence.json",
    "productionReadinessProof": "Backend/proof/production-readiness.json",
    "launchObjectiveAuditProof": "Backend/proof/launch-objective-audit.json",
    "testFlightRegressionPlanProof": "Backend/proof/testflight-regression-plan.json",
    "providerEvidenceProof": "Backend/proof/provider-evidence-materials.json",
    "mainlandFilingMaterialsProof": "Backend/proof/mainland-filing-materials.json",
    "signedArchiveTestFlightMaterialsProof": "Backend/proof/signed-archive-testflight-materials.json",
}
SUBMIT_REVIEW_PREFLIGHT_TARGET_PAGE_EVIDENCE = {
    "submitReviewPrecheck": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-08-submit-review-precheck.png",
    "buildTestflightLink": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-07-build-testflight-link.png",
    "reviewInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-06-review-information.png",
    "appPrivacy": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-04-app-privacy.png",
    "ageRating": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-05-age-rating.png",
}
SUBMIT_REVIEW_PREFLIGHT_GREEN_CHECKS = {
    "appStoreEvidenceReady": (
        "Backend/proof/app-store-evidence.json",
        "ready=true",
        "companyAccount",
        "mainlandAvailability",
        "mainlandFiling",
        "privacyLabel",
        "ageRatingResult",
        "signedArchive",
        "testFlight",
        "appleDeveloperAccountAccess",
        "smsProvider",
        "wechatOpenPlatform",
        "wechatUniversalLinkAasa",
        "huaweiObsPolicy",
        "finalScreenshots",
        "realDeviceRegression",
    ),
    "productionReadinessGreen": (
        "Backend/proof/production-readiness.json",
        "ready=true",
        "productionSecretConfigured",
        "mysqlDatabaseSelected",
        "huaweiObsSelected",
        "phoneLoginProviderConfigured",
        "wechatLoginProviderConfigured",
        "publicInternalDashboardBlocked",
        "iosReleaseReadinessProofPassed",
        "iosAppBundleProofPassed",
        "testFlightRegressionPlanProofPassed",
        "appStoreAssetsProofPassed",
        "authProvidersProofPassed",
        "appStoreManualEvidenceReady",
    ),
    "launchObjectiveAuditGreen": (
        "Backend/proof/launch-objective-audit.json",
        "ready=true",
        "ios265PhysicalDeviceAvailabilityReady",
        "weChatConfigurationGreen",
        "appStoreAssetsReady",
        "testFlightRegressionPlanReadyButNotEvidence",
        "realDeviceRegressionEvidenceReady",
        "appStoreManualEvidenceReady",
        "productionReadinessGreen",
    ),
    "testFlightRegressionEvidenceReady": (
        "Backend/proof/testflight-regression-plan.json",
        "passed=true",
        "ios265DeviceAvailabilityProofReferenced",
    ),
    "providerEvidenceReady": (
        "Backend/proof/provider-evidence-materials.json",
        "passed=true",
        "smsProvider live send proof",
        "WeChat Open Platform evidence",
        "Huawei OBS private bucket proof",
    ),
    "signedArchiveAndTestFlightReady": (
        "Backend/proof/signed-archive-testflight-materials.json",
        "passed=true",
        "D-U-N-S delivered",
        "Apple Developer Organization enrollment resumed",
        "Team ID confirmed",
        "App Store Distribution Archive",
        "TestFlight processed build",
    ),
    "mainlandFilingReady": (
        "Backend/proof/mainland-filing-materials.json",
        "passed=true",
        "APP 备案",
        "ICP applicability",
        "公安联网备案 applicability",
    ),
}
SUBMIT_REVIEW_PREFLIGHT_GREEN_CHECK_IDS = tuple(SUBMIT_REVIEW_PREFLIGHT_GREEN_CHECKS)
SUBMIT_REVIEW_PREFLIGHT_DEPENDENCY_FIELDS = (
    "id",
    "proof",
    "proves",
    "doesNotProve",
    "requiredBeforeSubmit",
    "initialStatus",
)
SUBMIT_REVIEW_PREFLIGHT_DEPENDENCY_MATRIX = (
    {
        "id": "appStoreEvidenceReady",
        "proof": "Backend/proof/app-store-evidence.json",
        "proves": [
            "all required XiaoNaiPing App Store manual evidence files are archived and redaction-reviewed",
            "company account, mainland availability, filing, privacy label, age rating result, signed archive, TestFlight, providers, final screenshots, and real-device evidence are indexed",
        ],
        "doesNotProve": [
            "production-readiness.json ready=true",
            "launch-objective-audit.json ready=true",
            "ASC-08 Submit for Review can be clicked",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    {
        "id": "productionReadinessGreen",
        "proof": "Backend/proof/production-readiness.json",
        "proves": [
            "production backend, storage, auth providers, iOS release proofs, App Store assets, and manual evidence are ready together",
            "required production checks have ready=true",
        ],
        "doesNotProve": [
            "App Store Connect live pages have been filled",
            "D-U-N-S or Apple Developer permission screenshots by itself",
            "iOS 26.5 real-device visual evidence by itself",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    {
        "id": "launchObjectiveAuditGreen",
        "proof": "Backend/proof/launch-objective-audit.json",
        "proves": [
            "top-level XiaoNaiPing launch objective is ready across iOS 26.5, WeChat, assets, TestFlight regression, real-device evidence, App Store manual evidence, and production readiness",
            "no known launch objective blocker remains",
        ],
        "doesNotProve": [
            "App Store Connect page screenshots by itself",
            "external platform evidence by itself",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    {
        "id": "testFlightRegressionEvidenceReady",
        "proof": "Backend/proof/testflight-regression-plan.json",
        "proves": [
            "iOS 26.5 TestFlight or signed-device regression plan and evidence gate passed",
            "iOS 26.5 physical device availability and RD evidence references are accepted",
        ],
        "doesNotProve": [
            "App Store Connect selected build screenshot",
            "production backend readiness",
            "WeChat Open Platform credentials",
            "all App Store manual evidence",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    {
        "id": "providerEvidenceReady",
        "proof": "Backend/proof/provider-evidence-materials.json",
        "proves": [
            "provider evidence worksheets and templates for SMS, WeChat, OBS, production proof, and redaction are complete",
            "provider capture gates distinguish screenshots, live proofs, and stable aliases",
        ],
        "doesNotProve": [
            "real SMS live-send proof exists",
            "real WeChat Open Platform credentials are configured",
            "OBS policy screenshot exists",
            "production-readiness.json ready=true",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    {
        "id": "signedArchiveAndTestFlightReady",
        "proof": "Backend/proof/signed-archive-testflight-materials.json",
        "proves": [
            "D-U-N-S post-delivery, Apple Developer organization, signing, Archive, TestFlight, permission, and evidence templates are complete as a materials gate",
            "Archive and TestFlight execution dependencies are locally checkable",
        ],
        "doesNotProve": [
            "D-U-N-S has actually been delivered",
            "App Store Distribution archive has actually been uploaded",
            "TestFlight build is processed",
            "ASC-07 build is selected",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    {
        "id": "mainlandFilingReady",
        "proof": "Backend/proof/mainland-filing-materials.json",
        "proves": [
            "mainland filing material plan, evidence templates, public copy consistency, and filing-value absence gates are complete",
            "APP filing, ICP applicability, and public-security filing applicability workflow is locally checkable",
        ],
        "doesNotProve": [
            "real APP filing has been approved",
            "ICP or public-security evidence has been archived",
            "App Store mainland availability screenshot exists",
            "production-readiness.json ready=true",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
)
SUBMIT_REVIEW_PREFLIGHT_DECISION_MARKERS = (
    "do-not-click-submit-for-review",
    "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-08-submit-review-precheck.png",
    "correct Organization",
    "com.mewpow.xiaonaiping",
    "selected TestFlight build",
    "App Privacy complete",
    "Age Rating result complete",
    "Review Information complete",
    "final iOS 26.5 screenshots uploaded",
    "no unresolved App Store Connect validation errors",
    "01-company-account.png",
    "05-signed-archive.png",
    "06-testflight.png",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "09-obs-policy.png",
    "10-final-screenshots/UPLOAD_PROVENANCE.json",
    "12-real-device-regression.md",
    "17-age-rating-result",
)
SUBMIT_REVIEW_PREFLIGHT_POST_GATES = (
    "check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
    "check_app_store_connect_evidence_materials.py --output Backend/proof/app-store-connect-evidence-materials.json",
    "check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
    "check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    "check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
    "check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260627T-current.json",
    "check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
SUBMIT_REVIEW_PREFLIGHT_COMPLETION_MARKERS = (
    "preflight-plan-not-evidence",
    "not App Store Connect live evidence",
    "not external platform evidence",
    "not submission permission",
    "app-store-evidence.json ready=true",
    "production-readiness.json ready=true",
    "launch-objective-audit.json ready=true",
    "iOS 26.5 real-device regression",
    "TestFlight processed build",
    "provider-evidence-materials.json passed=true",
    "mainland-filing-materials.json passed=true",
    "signed-archive-testflight-materials.json passed=true",
    "不是 App Store Connect 人工证据",
    "不能作为提交许可",
    "不能替代 D-U-N-S、Archive、TestFlight、短信、微信、OBS、备案、隐私标签、最终截图或 iOS 26.5 真机回归证据",
    "Submit for Review 只能在所有 required proof 为 true 后人工执行",
)
ASC_BACKFILL_RESULT_TEMPLATE_INSTRUCTION_MARKERS = (
    "Copy this file to ASC-BACKFILL-RESULT.json only after the live App Store Connect session.",
    "captured-live-backfill",
    "every listed screenshot file exists",
    "evidenceFileChecks",
    "file size",
    "SHA-256",
    "same-session backfill confirmation",
    "approved AppStoreConnect evidence-root confirmation",
    "field-freeze confirmation",
    "redaction review result",
    "fieldEntryChecks",
    "App 名称、副标题、描述、关键词、宣传文本、新版本说明、分类、年龄分级、隐私政策 URL、技术支持 URL、用户协议 URL 和审核备注",
    "APP_STORE_CONNECT_FIELD_FREEZE_PACKET_",
    "has been redacted",
    "Do not treat this result file as submit permission",
    "Backend/proof/app-store-evidence.json ready=true",
    "Backend/proof/production-readiness.json ready=true",
    "Backend/proof/launch-objective-audit.json ready=true",
    "Backend/proof/testflight-regression-plan.json passed=true",
    "Backend/proof/provider-evidence-materials.json passed=true",
    "Backend/proof/mainland-filing-materials.json passed=true",
    "Backend/proof/signed-archive-testflight-materials.json passed=true",
    "cannot replace XiaoNaiPing App Store evidence",
    "Do not fill secrets",
    "complete D-U-N-S number",
    "AppSecret",
    "SMS secret",
    "WeChat secret",
    "OBS AK/SK",
)
ASC_BACKFILL_RESULT_TEMPLATE_SCREENSHOTS = {
    "appInformation": ("ASC-01-app-information.png", "pageValuesMatchSource"),
    "versionInformation": ("ASC-02-version-information.png", "pageValuesMatchSource"),
    "pricingAvailabilityRelease": ("ASC-03-pricing-availability-release.png", "pageValuesMatchSource"),
    "appPrivacy": ("ASC-04-app-privacy.png", "trackingNoVisible"),
    "ageRating": ("ASC-05-age-rating.png", "kidsCategoryNotSelected"),
    "reviewInformation": ("ASC-06-review-information.png", "privateFieldsRedactedInStoredEvidence"),
    "buildTestFlightLink": ("ASC-07-build-testflight-link.png", "sameBuildAsRealDeviceRegression"),
    "submitReviewPrecheck": ("ASC-08-submit-review-precheck.png", "canSubmitTrueVisible"),
}
ASC_BACKFILL_RESULT_TEMPLATE_FILE_CHECKS = {
    "appInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-01-app-information.png",
    "versionInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-02-version-information.png",
    "pricingAvailabilityRelease": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-03-pricing-availability-release.png",
    "appPrivacy": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-04-app-privacy.png",
    "ageRating": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-05-age-rating.png",
    "reviewInformation": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-06-review-information.png",
    "buildTestFlightLink": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-07-build-testflight-link.png",
    "submitReviewPrecheck": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-08-submit-review-precheck.png",
}
ASC_BACKFILL_RESULT_TEMPLATE_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameSessionAsBackfill": False,
    "sourceIsAppStoreConnectEvidenceRoot": False,
    "fieldFreezeConfirmed": False,
    "secretValuesNotRecorded": False,
}
ASC_BACKFILL_RESULT_TEMPLATE_PRIVATE_FIELD_TARGETS = {
    "targetPage": "AppStoreConnect/ASC-06-review-information.png",
    "targetPrivateEvidence": "Docs/08_Release/AppStoreEvidence/16-app-review-information-private.png",
}
ASC_BACKFILL_RESULT_TEMPLATE_PRIVATE_FIELD_PLACEHOLDERS = {
    "reviewCredentialsOnlyInPrivateFields": False,
    "reviewNotesContainNoCredentials": False,
    "testPhoneOnlyInPrivateField": False,
    "verificationCodeOnlyInPrivateField": False,
    "recoveryKeyOnlyInPrivateField": False,
    "wechatTestAccountOnlyInPrivateField": False,
    "appleSignInTestNotesOnlyInPrivateField": False,
    "providerSecretsNeverEntered": False,
    "secretValuesNotRecorded": False,
    "privateScreenshotRedacted": False,
    "notCommittedToRepo": False,
}
ASC_BACKFILL_RESULT_TEMPLATE_XNP_PROOFS = {
    "appStoreEvidence": "Backend/proof/app-store-evidence.json",
    "productionReadiness": "Backend/proof/production-readiness.json",
    "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
    "testflightRegressionPlan": "Backend/proof/testflight-regression-plan.json",
    "providerEvidence": "Backend/proof/provider-evidence-materials.json",
    "mainlandFilingMaterials": "Backend/proof/mainland-filing-materials.json",
    "signedArchiveTestFlightMaterials": "Backend/proof/signed-archive-testflight-materials.json",
}
ASC_BACKFILL_RESULT_TEMPLATE_RERUN_PROOFS = {
    "checkAppStoreConnectMaterials": "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
    "checkAppStoreEvidence": "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
    "checkTestFlightRegressionPlan": "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    "checkProviderEvidenceMaterials": "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "checkMainlandFilingMaterials": "python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "checkSignedArchiveTestFlightMaterials": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
    "checkProductionReadiness": "python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-20260627T-current.json",
    "checkLaunchObjectiveAudit": "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
}
def asc_backfill_result_template_session_scalars(path_date: str) -> dict[str, str]:
    return {
        "sessionId": f"xnp-asc-backfill-{dashed_date(path_date)}",
        "fieldFreezePacket": f"Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_{path_date}.json",
        "evidenceRoot": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/",
    }


def asc_backfill_result_template_session_source_files(path_date: str) -> dict[str, str]:
    return {
        "draftJson": f"Docs/08_Release/APP_STORE_CONNECT_DRAFT_{path_date}.json",
        "fillSheet": f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
        "copyPastePacket": f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
        "fieldFreezePacket": f"Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_{path_date}.json",
        "finalEntryAudit": f"Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_{path_date}.md",
        "reviewInformation": f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md",
    }


ASC_BACKFILL_RESULT_TEMPLATE_SESSION_PAGE_GROUPS = {
    "appInformation": ("appName", "subtitle", "category", "privacyPolicyUrl", "supportUrl", "termsUrl"),
    "versionInformation": ("description", "keywords", "promotionalText", "whatsNew"),
    "ageRating": ("ageRating",),
    "reviewInformation": ("reviewNotes",),
}
ASC_BACKFILL_RESULT_TEMPLATE_SESSION_PAGE_EVIDENCE = {
    "appInformation": "AppStoreConnect/ASC-01-app-information.png",
    "versionInformation": "AppStoreConnect/ASC-02-version-information.png",
    "ageRating": "AppStoreConnect/ASC-05-age-rating.png",
    "reviewInformation": "AppStoreConnect/ASC-06-review-information.png",
}
ASC_BACKFILL_RESULT_TEMPLATE_SESSION_FLAGS = (
    "allFieldsMatchFieldFreezePacket",
    "allPageValuesVisibleOrConfirmed",
    "allScreenshotsSameBackfillSession",
    "noAscOnlyTextEdits",
    "anyTextChangeWrittenBackToSourceFiles",
    "allLengthAndChoiceLimitsRechecked",
    "allSensitiveFieldsRedacted",
    "appStoreConnectSaveSucceeded",
)
ASC_BACKFILL_RESULT_TEMPLATE_STOP_CONDITION_MARKERS = {
    "fieldChangedOnlyInAsc": (
        "differs from the field freeze packet",
        "source files were not updated",
        "regenerate materials",
    ),
    "mixedBackfillSessionScreenshots": (
        "ASC-01",
        "ASC-02",
        "ASC-05",
        "ASC-06",
        "different backfill sessions",
    ),
    "reviewPrivateSecretVisible": (
        "recovery key",
        "complete phone number",
        "Apple ID email",
        "provider secret",
    ),
    "privateReviewInfoLeakedToPublicCopy": (
        "test phone/account",
        "verification code",
        "recovery key",
        "public review notes",
        "App Review Information private fields only",
    ),
    "ageRatingOrPrivacyMismatch": (
        "age rating",
        "privacy policy URL",
        "support URL",
        "review notes",
        "App Store Connect materials gate",
    ),
}
ASC_BACKFILL_RESULT_TEMPLATE_FIELD_ENTRY_TARGETS = {
    "appName": "AppStoreConnect/ASC-01-app-information.png",
    "subtitle": "AppStoreConnect/ASC-01-app-information.png",
    "description": "AppStoreConnect/ASC-02-version-information.png",
    "keywords": "AppStoreConnect/ASC-02-version-information.png",
    "promotionalText": "AppStoreConnect/ASC-02-version-information.png",
    "whatsNew": "AppStoreConnect/ASC-02-version-information.png",
    "category": "AppStoreConnect/ASC-01-app-information.png",
    "ageRating": "AppStoreConnect/ASC-05-age-rating.png",
    "privacyPolicyUrl": "AppStoreConnect/ASC-01-app-information.png",
    "supportUrl": "AppStoreConnect/ASC-01-app-information.png",
    "termsUrl": "AppStoreConnect/ASC-01-app-information.png",
    "reviewNotes": "AppStoreConnect/ASC-06-review-information.png",
}
ASC_BACKFILL_RESULT_TEMPLATE_FIELD_ENTRY_PLACEHOLDERS = {
    "sourceMatchesFieldFreeze": False,
    "pageValueVisibleOrConfirmed": False,
    "sameSessionAsBackfill": False,
    "copyPastedWithoutAscOnlyEdit": False,
    "lengthOrChoiceLimitChecked": False,
    "redactionChecked": False,
}
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_SOURCE_FILES = {
    "privacyAnswers": "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md",
    "privacyLabel": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
    "ageRatingAnswers": "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
    "reviewInformation": "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
    "entrySessionPacket": "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
    "ascBackfillResultTemplate": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-BACKFILL-RESULT.template.json",
    "appStoreEvidence": "Backend/proof/app-store-evidence.json",
    "productionReadiness": "Backend/proof/production-readiness.json",
    "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
}
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_TARGETS = {
    "appPrivacyPage": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-04-app-privacy.png",
    "privacyLabelEvidence": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
    "ageRatingPage": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-05-age-rating.png",
    "ageRatingResult": "Docs/08_Release/AppStoreEvidence/17-age-rating-result.png",
    "reviewInformationPage": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-06-review-information.png",
    "reviewAccountRedacted": "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
}
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_FILE_CHECK_FIELDS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameSessionAsAscBackfill": False,
    "sourceIsAllowedEvidenceRoot": False,
    "sourceMatchesAnswerSheet": False,
    "realEvidenceNotTemplate": False,
    "secretValuesNotRecorded": False,
}
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_DEPENDENCY_MATRIX = {
    "appPrivacyPage": {
        "target": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-04-app-privacy.png",
        "proves": [
            "App Store Connect App Privacy page values are visible",
            "Tracking is No",
            "data categories match APP_STORE_PRIVACY_LABEL.json and APP_STORE_PRIVACY_ANSWERS",
        ],
        "doesNotProve": [
            "04-privacy-label final evidence",
            "app-store-evidence.json ready=true",
            "production-readiness.json ready=true",
            "Submit for Review permission",
        ],
        "requiredBeforeCapturedLiveStatus": True,
        "initialStatus": "pending",
    },
    "privacyLabelEvidence": {
        "target": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
        "proves": [
            "final App Privacy label evidence is archived",
            "privacy label matches APP_STORE_PRIVACY_LABEL.json",
            "Tracking remains No",
        ],
        "doesNotProve": [
            "ASC-04 page backfill by itself",
            "age rating result",
            "review account redaction",
            "Submit for Review permission",
        ],
        "requiredBeforeCapturedLiveStatus": True,
        "initialStatus": "pending",
    },
    "ageRatingPage": {
        "target": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-05-age-rating.png",
        "proves": [
            "App Store Connect age rating answers page is visible",
            "Kids Category is not selected",
            "regulated medical device answer is No",
        ],
        "doesNotProve": [
            "17-age-rating-result final evidence",
            "legal review",
            "launch-objective-audit.json ready=true",
            "Submit for Review permission",
        ],
        "requiredBeforeCapturedLiveStatus": True,
        "initialStatus": "pending",
    },
    "ageRatingResult": {
        "target": "Docs/08_Release/AppStoreEvidence/17-age-rating-result.png",
        "proves": [
            "final App Store Connect age rating result is archived",
            "result aligns with APP_STORE_AGE_RATING_ANSWERS",
            "medical device boundary remains No",
        ],
        "doesNotProve": [
            "App Privacy label evidence",
            "review account evidence",
            "production-readiness.json ready=true",
            "Submit for Review permission",
        ],
        "requiredBeforeCapturedLiveStatus": True,
        "initialStatus": "pending",
    },
    "reviewInformationPage": {
        "target": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-06-review-information.png",
        "proves": [
            "App Review Information page values are visible",
            "Sign-in required is Yes",
            "review notes preserve Live Activity, widget, manual deferral, no HealthKit, no feeding advice, and no medical device boundaries",
        ],
        "doesNotProve": [
            "review account redacted proof",
            "SMS provider evidence",
            "WeChat Open Platform evidence",
            "iOS 26.5 real-device regression",
            "Submit for Review permission",
        ],
        "requiredBeforeCapturedLiveStatus": True,
        "initialStatus": "pending",
    },
    "reviewAccountRedacted": {
        "target": "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
        "proves": [
            "review account evidence is archived without recovery key or tokens",
            "recovery-key login path is documented for App Review",
            "phone and WeChat test accounts wait for real provider evidence",
        ],
        "doesNotProve": [
            "SMS provider evidence",
            "WeChat Open Platform evidence",
            "RD-10 recovery-key real-device login",
            "RD-13 phone login",
            "RD-14 WeChat login",
            "Submit for Review permission",
        ],
        "requiredBeforeCapturedLiveStatus": True,
        "initialStatus": "pending",
    },
}
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_DEPENDENCY_MATRIX_SCHEMA = (
    "artifactId",
    "target",
    "proves",
    "doesNotProve",
    "requiredBeforeCapturedLiveStatus",
    "initialStatus",
)
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_SECTION_MARKERS = {
    "appPrivacy": (
        "Tracking 为 No",
        "Data Used to Track You = No",
        "Data Linked to You includes Identifiers, Contact Info, User Content, Photos or Videos, Health and Fitness, Usage Data",
        "Data Not Linked to You includes Diagnostics",
        "Health and Fitness is user-entered baby care records only",
        "Usage Data excludes baby content, photos, phone numbers, WeChat identifiers, advertising ID, and device fingerprint",
        "Backend/proof/app-store-evidence.json ready=true",
        "production-readiness.json ready=true",
        "iOS 26.5 real-device proof",
    ),
    "ageRating": (
        "Kids Category 未选择",
        "Age Categories and Override = Not Applicable",
        "Regulated Medical Device 为 No",
        "not a medical device",
        "no diagnosis, prevention, monitoring, treatment, disease prediction",
        "vaccine template is records and reminders only",
        "manual feeding reminder deferral is not feeding advice",
        "17-age-rating-result.png 或 .pdf",
        "launch-objective-audit.json ready=true",
    ),
    "reviewInformation": (
        "Sign-in required = Yes",
        "review-recovery-key-account",
        ".env.xnp-review-account:XNP_REVIEW_RECOVERY_KEY",
        "手机号测试号和微信测试号必须等真实短信服务商和微信开放平台配置完成后再补",
        "正式提交包不提供、不依赖 debug code",
        "manual reminder deferral",
        "no HealthKit",
        "no feeding advice",
        "07-sms-provider.png",
        "08-wechat-open-platform.png",
        "12-real-device-regression.md",
    ),
}
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_STOP_CONDITIONS = (
    "privacyLabelEvidenceMissing",
    "ageRatingResultMissing",
    "reviewAccountRedactedEvidenceMissing",
    "appPrivacyMismatch",
    "ageRatingMedicalDeviceMismatch",
    "reviewInformationSecretLeak",
    "debugCodePresent",
    "xiaoNaiPingProofsStillRed",
    "productionReadinessStillRed",
    "launchObjectiveAuditStillRed",
)
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_POST_GATES = (
    "check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
    "check_app_store_connect_evidence_materials.py --output Backend/proof/app-store-connect-evidence-materials.json",
    "check_review_notes.py --output Backend/proof/review-notes.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
    "check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-20260627T-current.json",
    "check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
ASC_PRIVACY_AGE_REVIEW_TEMPLATE_MARKERS = (
    "ASC-04, ASC-05, ASC-06, 04-privacy-label, 17-age-rating-result, and 11-test-account-redacted",
    "not privacy-label evidence",
    "not age-rating evidence",
    "not review-account evidence",
    "not submission permission",
    "Do not use ASC-04, ASC-05, or ASC-06 page screenshots to replace XiaoNaiPing app-store-evidence.json",
    "final screenshot provenance",
    "iOS 26.5 real-device proof",
    "recovery keys",
    "complete phone numbers",
    "AppSecret",
    "OBS AK/SK",
    "privacy-age-review-result-template-not-evidence",
    "cannot authorize Submit for Review",
    "不能作为提交许可",
    "不能替代 D-U-N-S、Archive、TestFlight、短信、微信、OBS、备案、隐私标签、年龄分级结果、最终截图或 iOS 26.5 真机回归证据",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def latest_fill_sheet(root: Path) -> str:
    release_dir = root / "Docs/08_Release"
    candidates = sorted(release_dir.glob(FILL_SHEET_PATTERN))
    if not candidates:
        return FALLBACK_FILL_SHEET
    return str(candidates[-1].relative_to(root))


def path_date_from(*values: str) -> str:
    for value in values:
        match = re.search(r"20\d{6}", value or "")
        if match:
            return match.group(0)
    return "20260627"


def dashed_date(path_date: str) -> str:
    return f"{path_date[:4]}-{path_date[4:6]}-{path_date[6:8]}"


def dated_markers(markers: tuple[str, ...], path_date: str) -> tuple[str, ...]:
    return tuple(
        marker.replace("20260627", path_date).replace("2026-06-27", dashed_date(path_date))
        for marker in markers
    )


def dated_doc_path(default_path: str, path_date: str) -> str:
    return default_path.replace("20260627", path_date)


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def extract_first_code_block(section: str) -> str:
    match = re.search(r"```(?:text)?\s*(.*?)\s*```", section, re.DOTALL)
    return match.group(1).strip() if match else ""


def draft_text_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    if isinstance(value, dict):
        return draft_text_value(value.get("pasteText"))
    return ""


def nested_value(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def app_store_connect_draft_json_failures(
    draft: dict[str, Any],
    path_date: str,
    *,
    keywords: str,
    promo: str,
    description: str,
    release_notes: str,
    review_text: str,
) -> list[str]:
    if not draft:
        return ["missing draft JSON"]

    failures: list[str] = []
    expected_scalars = {
        "artifactType": "app-store-connect-draft",
        "status": "draft-only-not-submission",
        "date": dashed_date(path_date),
    }
    for key, expected in expected_scalars.items():
        if draft.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    expected_sources = {
        "fillSheet": f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
        "copyPastePacket": f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
        "metadata": "Docs/08_Release/APP_STORE_METADATA.md",
        "privacyLabel": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        "privacyAnswers": f"Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_{path_date}.md",
        "ageRatingAnswers": f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
        "reviewInformation": f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md",
        "versionReleaseSettings": f"Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_{path_date}.md",
        "finalEntryAudit": f"Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_{path_date}.md",
    }
    for key, expected in expected_sources.items():
        if nested_value(draft, "sourceFiles", key) != expected:
            failures.append(f"sourceFiles.{key} must be {expected}")

    expected_app_info = {
        "appName": EXPECTED_APP_NAME,
        "bundleId": EXPECTED_BUNDLE_ID,
        "sku": "xiaonaiping-ios-1",
        "subtitle": EXPECTED_SUBTITLE,
        "primaryCategory": "生活",
        "secondaryCategory": "留空",
        "price": "免费",
        "firstReleaseRegion": "China mainland",
        "secondReleaseRegion": "Hong Kong",
        "copyright": "© 2026 深圳市闪现生活科技有限公司",
        "privacyPolicyUrl": EXPECTED_PRIVACY_URL,
        "supportUrl": EXPECTED_SUPPORT_URL,
        "termsUrl": EXPECTED_TERMS_URL,
    }
    for key, expected in expected_app_info.items():
        if nested_value(draft, "appInformation", key) != expected:
            failures.append(f"appInformation.{key} must be {expected}")

    version_info = draft.get("versionInformation", {})
    if not isinstance(version_info, dict):
        failures.append("versionInformation must be an object")
        version_info = {}
    expected_text_fields = {
        "keywords": keywords,
        "promotionalText": promo,
        "description": description,
        "whatsNew": release_notes,
    }
    for key, expected in expected_text_fields.items():
        if draft_text_value(version_info.get(key)) != expected:
            failures.append(f"versionInformation.{key} differs from fill sheet")

    app_name = nested_value(draft, "appInformation", "appName")
    if isinstance(app_name, str) and len(app_name) > APP_NAME_MAX_CHARS:
        failures.append(f"appInformation.appName exceeds {APP_NAME_MAX_CHARS} characters")
    subtitle = nested_value(draft, "appInformation", "subtitle")
    if isinstance(subtitle, str) and len(subtitle) > SUBTITLE_MAX_CHARS:
        failures.append(f"appInformation.subtitle exceeds {SUBTITLE_MAX_CHARS} characters")
    draft_keywords = draft_text_value(version_info.get("keywords"))
    if draft_keywords and utf8_bytes(draft_keywords) > KEYWORDS_MAX_BYTES:
        failures.append(f"versionInformation.keywords exceeds {KEYWORDS_MAX_BYTES} UTF-8 bytes")
    version_char_limits = {
        "promotionalText": PROMOTIONAL_TEXT_MAX_CHARS,
        "description": LONG_TEXT_MAX_CHARS,
        "whatsNew": LONG_TEXT_MAX_CHARS,
    }
    for key, limit in version_char_limits.items():
        value = draft_text_value(version_info.get(key))
        if value and len(value) > limit:
            failures.append(f"versionInformation.{key} exceeds {limit} characters")

    age_rating = draft.get("ageRating", {})
    if not isinstance(age_rating, dict):
        failures.append("ageRating must be an object")
        age_rating = {}
    expected_age_rating = {
        "answerSheet": f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
        "expectedRating": "4+",
        "kidsCategory": "No",
        "ageCategoriesAndOverride": "Not Applicable",
        "regulatedMedicalDevice": "No",
    }
    for key, expected in expected_age_rating.items():
        if age_rating.get(key) != expected:
            failures.append(f"ageRating.{key} must be {expected}")
    age_boundary_text = json.dumps(age_rating, ensure_ascii=False)
    for marker in (
        "not a medical device",
        "no diagnosis",
        "no treatment",
        "no disease prediction",
        "no HealthKit",
        "no sensors",
        "no hospital records",
        "no automatic feeding inference",
    ):
        if marker not in age_boundary_text:
            failures.append(f"ageRating boundary missing {marker}")

    app_privacy = draft.get("appPrivacy", {})
    if not isinstance(app_privacy, dict):
        failures.append("appPrivacy must be an object")
        app_privacy = {}
    if app_privacy.get("privacyLabel") != "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json":
        failures.append("appPrivacy.privacyLabel must point to APP_STORE_PRIVACY_LABEL.json")
    if app_privacy.get("privacyAnswers") != f"Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_{path_date}.md":
        failures.append(f"appPrivacy.privacyAnswers must point to {path_date} answer sheet")
    for key in ("usesTracking", "thirdPartyAdvertising", "thirdPartyAnalytics"):
        if app_privacy.get(key) is not False:
            failures.append(f"appPrivacy.{key} must be false")
    privacy_categories = app_privacy.get("dataCategories")
    if not isinstance(privacy_categories, list):
        failures.append("appPrivacy.dataCategories must be an array")
    elif set(str(category) for category in privacy_categories) != EXPECTED_PRIVACY_CATEGORIES:
        failures.append("appPrivacy.dataCategories must match privacy label categories")

    review_notes = draft.get("reviewNotes", {})
    if not isinstance(review_notes, dict):
        failures.append("reviewNotes must be an object")
        review_notes = {}
    if review_notes.get("reviewInformation") != f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md":
        failures.append(f"reviewNotes.reviewInformation must point to {path_date} review information")
    if review_notes.get("signInRequired") is not True:
        failures.append("reviewNotes.signInRequired must be true")
    if review_notes.get("preferredTestAccount") != "recovery-key":
        failures.append("reviewNotes.preferredTestAccount must be recovery-key")
    if review_notes.get("debugCodeAllowed") is not False:
        failures.append("reviewNotes.debugCodeAllowed must be false")
    if review_notes.get("realSmsWechatAccountsPending") is not True:
        failures.append("reviewNotes.realSmsWechatAccountsPending must be true")
    if draft_text_value(review_notes.get("text")) != review_text:
        failures.append("reviewNotes.text differs from fill sheet")
    review_note_text = draft_text_value(review_notes.get("text"))
    if review_note_text and len(review_note_text) > LONG_TEXT_MAX_CHARS:
        failures.append(f"reviewNotes.text exceeds {LONG_TEXT_MAX_CHARS} characters")
    boundary_checklist = review_notes.get("boundaryChecklist")
    if not isinstance(boundary_checklist, dict):
        failures.append("reviewNotes.boundaryChecklist must be an object")
    else:
        for key, expected in REVIEW_NOTES_BOUNDARY_CHECKLIST.items():
            if boundary_checklist.get(key) != expected:
                failures.append(f"reviewNotes.boundaryChecklist.{key} must be {expected!r}")
        for marker in REVIEW_NOTES_BOUNDARY_TEXT_MARKERS:
            if marker not in review_note_text:
                failures.append(f"reviewNotes.text missing boundary marker {marker}")

    submission = draft.get("submissionBoundary", {})
    if not isinstance(submission, dict):
        failures.append("submissionBoundary must be an object")
        submission = {}
    if submission.get("canSubmitFromThisDraft") is not False:
        failures.append("submissionBoundary.canSubmitFromThisDraft must be false")
    requirements = submission.get("requiresBeforeSubmit")
    if not isinstance(requirements, list):
        failures.append("submissionBoundary.requiresBeforeSubmit must be an array")
    else:
        requirement_values: list[str] = []
        seen_requirements: set[str] = set()
        for requirement in requirements:
            if not isinstance(requirement, str) or not requirement:
                failures.append("submissionBoundary.requiresBeforeSubmit entry must be a non-empty string")
                continue
            if requirement in seen_requirements:
                failures.append(f"submissionBoundary.requiresBeforeSubmit duplicate {requirement}")
            seen_requirements.add(requirement)
            requirement_values.append(requirement)
        if tuple(requirement_values) != APP_STORE_CONNECT_SUBMISSION_BOUNDARY_REQUIREMENTS:
            failures.append("submissionBoundary.requiresBeforeSubmit order must match launch submission blocker order")
    submission_text = json.dumps(submission, ensure_ascii=False)
    for marker in (
        "production-readiness.json ready=true",
        "launch-objective-audit.json ready=true",
        "D-U-N-S",
        "Apple Developer Organization enrollment",
        "Team ID",
        "Archive",
        "TestFlight",
        "微信开放平台",
        "短信服务商",
        "OBS",
        "APP 备案",
        "iOS 26.5",
    ):
        if marker not in submission_text:
            failures.append(f"submissionBoundary missing {marker}")

    secret_hits = forbidden_review_account_secret_hits(json.dumps(draft, ensure_ascii=False))
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def app_store_connect_page_evidence_map_failures(
    draft: dict[str, Any],
    path_date: str,
) -> list[str]:
    page_map = draft.get("pageEvidenceMap") if isinstance(draft, dict) else None
    if not isinstance(page_map, dict):
        return ["pageEvidenceMap must be an object"]

    failures: list[str] = []
    if page_map.get("directory") != "Docs/08_Release/AppStoreEvidence/AppStoreConnect/":
        failures.append("pageEvidenceMap.directory must be Docs/08_Release/AppStoreEvidence/AppStoreConnect/")
    if page_map.get("status") != "post-fill-page-evidence-only":
        failures.append("pageEvidenceMap.status must be post-fill-page-evidence-only")

    does_not_replace = page_map.get("doesNotReplace")
    does_not_replace_set = {str(item) for item in does_not_replace} if isinstance(does_not_replace, list) else set()
    for marker in ASC_PAGE_EVIDENCE_DOES_NOT_REPLACE:
        if marker not in does_not_replace_set:
            failures.append(f"pageEvidenceMap.doesNotReplace missing {marker}")

    items = page_map.get("items")
    if not isinstance(items, list):
        return failures + ["pageEvidenceMap.items must be an array"]

    by_file: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            failures.append("pageEvidenceMap.items entry must be an object")
            continue
        file_name = item.get("file")
        if not isinstance(file_name, str) or not file_name:
            failures.append("pageEvidenceMap.items entry missing file")
            continue
        if file_name in by_file:
            failures.append(f"pageEvidenceMap.items duplicate {file_name}")
        by_file[file_name] = item

    for file_name, requirements in ASC_PAGE_EVIDENCE_ITEMS.items():
        item = by_file.get(file_name)
        if not item:
            failures.append(f"pageEvidenceMap.items missing {file_name}")
            continue
        item_text = json.dumps(item, ensure_ascii=False)
        for section, markers in requirements.items():
            dated_required_markers = dated_markers(tuple(str(marker) for marker in markers), path_date)
            for marker in dated_required_markers:
                if marker not in item_text:
                    failures.append(f"{file_name}.{section} missing {marker}")

    unexpected_secret_hits = forbidden_review_account_secret_hits(json.dumps(page_map, ensure_ascii=False))
    if unexpected_secret_hits:
        failures.append("pageEvidenceMap secret hits: " + ", ".join(unexpected_secret_hits))
    return failures


def app_store_connect_field_audit_matrix_failures(
    draft: dict[str, Any],
    path_date: str,
) -> list[str]:
    matrix = draft.get("fieldAuditMatrix") if isinstance(draft, dict) else None
    if not isinstance(matrix, dict):
        return ["fieldAuditMatrix must be an object"]

    failures: list[str] = []
    matrix_text = json.dumps(matrix, ensure_ascii=False)
    for marker in dated_markers(FIELD_AUDIT_MATRIX_RULE_MARKERS, path_date):
        if marker not in matrix_text:
            failures.append(f"fieldAuditMatrix rule missing {marker}")

    rows = matrix.get("rows")
    if not isinstance(rows, list):
        return failures + ["fieldAuditMatrix.rows must be an array"]

    by_id: dict[str, dict[str, Any]] = {}
    row_ids: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            failures.append("fieldAuditMatrix.rows entry must be an object")
            continue
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id:
            failures.append("fieldAuditMatrix.rows entry missing id")
            continue
        if row_id in by_id:
            failures.append(f"fieldAuditMatrix.rows duplicate {row_id}")
        by_id[row_id] = row
        row_ids.append(row_id)

    if tuple(row_ids) != FIELD_AUDIT_MATRIX_ROW_IDS:
        failures.append("fieldAuditMatrix.rows order must match App Store Connect field order")

    for row_id, markers in FIELD_AUDIT_MATRIX_ITEMS.items():
        row = by_id.get(row_id)
        if not row:
            failures.append(f"fieldAuditMatrix.rows missing {row_id}")
            continue
        expected_values = FIELD_AUDIT_MATRIX_EXACT_VALUES.get(row_id, {})
        for key, expected in expected_values.items():
            if row.get(key) != expected:
                failures.append(f"fieldAuditMatrix.{row_id}.{key} must be {expected}")
        row_text = json.dumps(row, ensure_ascii=False)
        for marker in dated_markers(markers, path_date):
            if marker not in row_text:
                failures.append(f"fieldAuditMatrix.{row_id} missing {marker}")

    unexpected_secret_hits = forbidden_review_account_secret_hits(matrix_text)
    if unexpected_secret_hits:
        failures.append("fieldAuditMatrix secret hits: " + ", ".join(unexpected_secret_hits))
    return failures


def expected_field_freeze_budget_matrix(
    *,
    keywords: str,
    promo: str,
    description: str,
    release_notes: str,
    review_text: str,
) -> list[dict[str, Any]]:
    values = {
        "appName": EXPECTED_APP_NAME,
        "subtitle": EXPECTED_SUBTITLE,
        "keywords": keywords,
        "promotionalText": promo,
        "description": description,
        "whatsNew": release_notes,
        "reviewNotes": review_text,
    }
    rows: list[dict[str, Any]] = []
    for row_id, field, metric, limit, value_source in FIELD_FREEZE_BUDGET_SPECS:
        value = values[row_id]
        used = utf8_bytes(value) if metric == "utf8Bytes" else len(value)
        rows.append(
            {
                "id": row_id,
                "field": field,
                "valueSource": value_source,
                "metric": metric,
                "limit": limit,
                "used": used,
                "remaining": limit - used,
                "withinLimit": used <= limit,
                "sourceValuePresent": bool(value),
            }
        )
    return rows


def expected_field_freeze_paste_sequence_matrix(path_date: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in FIELD_FREEZE_PASTE_SEQUENCE_SPECS:
        row = dict(spec)
        row["copySource"] = row["copySource"].replace("20260627", path_date)
        row["postPasteGate"] = FIELD_FREEZE_PASTE_SEQUENCE_POST_GATE
        row["pasteRequired"] = True
        row["initialStatus"] = "pending"
        rows.append(row)
    return rows


def app_store_connect_field_freeze_packet_failures(
    packet: dict[str, Any],
    draft: dict[str, Any],
    path_date: str,
    *,
    keywords: str,
    promo: str,
    description: str,
    release_notes: str,
    review_text: str,
) -> list[str]:
    if not packet:
        return ["missing App Store Connect field freeze packet"]

    failures: list[str] = []
    expected_scalars: dict[str, Any] = {
        "artifactType": "app-store-connect-field-freeze-packet",
        "status": "field-freeze-plan-not-evidence",
        "date": dashed_date(path_date),
        "project": "XiaoNaiPing",
        "appName": EXPECTED_APP_NAME,
        "bundleId": EXPECTED_BUNDLE_ID,
        "canSubmitFromThisPacket": False,
    }
    for key, expected in expected_scalars.items():
        if packet.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    for key, expected in FIELD_FREEZE_SOURCE_FILES.items():
        dated_expected = expected.replace("20260627", path_date)
        if nested_value(packet, "sourceFiles", key) != dated_expected:
            failures.append(f"sourceFiles.{key} must be {dated_expected}")

    packet_text = json.dumps(packet, ensure_ascii=False)
    for marker in dated_markers(FIELD_FREEZE_RULE_MARKERS, path_date):
        if marker not in packet_text:
            failures.append(f"fieldFreezeRules missing {marker}")

    fields = packet.get("fields")
    if not isinstance(fields, list):
        return failures + ["fields must be an array"]

    by_id: dict[str, dict[str, Any]] = {}
    field_ids: list[str] = []
    for field in fields:
        if not isinstance(field, dict):
            failures.append("fields entry must be an object")
            continue
        field_id = field.get("id")
        if not isinstance(field_id, str) or not field_id:
            failures.append("fields entry missing id")
            continue
        if field_id in by_id:
            failures.append(f"fields duplicate {field_id}")
        by_id[field_id] = field
        field_ids.append(field_id)

    if tuple(field_ids) != FIELD_AUDIT_MATRIX_ROW_IDS:
        failures.append("fields order must match App Store Connect field order")

    for field_id, markers in FIELD_AUDIT_MATRIX_ITEMS.items():
        field = by_id.get(field_id)
        if not field:
            failures.append(f"fields missing {field_id}")
            continue
        for key, expected in FIELD_AUDIT_MATRIX_EXACT_VALUES.get(field_id, {}).items():
            if field.get(key) != expected:
                failures.append(f"fields.{field_id}.{key} must be {expected}")
        field_text = json.dumps(field, ensure_ascii=False)
        for marker in dated_markers(markers, path_date):
            if marker not in field_text:
                failures.append(f"fields.{field_id} missing {marker}")
        if "freezeAction" not in field_text or "回写源文件" not in field_text:
            failures.append(f"fields.{field_id} missing freezeAction source-file rewrite boundary")

    draft_rows: dict[str, dict[str, Any]] = {}
    draft_field_audit = draft.get("fieldAuditMatrix") if isinstance(draft, dict) else {}
    if isinstance(draft_field_audit, dict):
        for row in draft_field_audit.get("rows", []):
            if not isinstance(row, dict):
                continue
            row_id = row.get("id")
            if isinstance(row_id, str) and row_id:
                draft_rows[row_id] = row

    source_lock_matrix = packet.get("fieldSourceLockMatrix")
    if not isinstance(source_lock_matrix, list):
        failures.append("fieldSourceLockMatrix must be an array")
    else:
        by_lock_id: dict[str, dict[str, Any]] = {}
        lock_ids: list[str] = []
        for row in source_lock_matrix:
            if not isinstance(row, dict):
                failures.append("fieldSourceLockMatrix entry must be an object")
                continue
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                failures.append("fieldSourceLockMatrix entry missing id")
                continue
            if row_id in by_lock_id:
                failures.append(f"fieldSourceLockMatrix duplicate {row_id}")
            by_lock_id[row_id] = row
            lock_ids.append(row_id)
        if tuple(lock_ids) != FIELD_AUDIT_MATRIX_ROW_IDS:
            failures.append("fieldSourceLockMatrix order must match App Store Connect field order")
        for field_id in FIELD_AUDIT_MATRIX_ROW_IDS:
            row = by_lock_id.get(field_id)
            if not isinstance(row, dict):
                failures.append(f"fieldSourceLockMatrix missing {field_id}")
                continue
            expected_source = (
                f"Docs/08_Release/APP_STORE_CONNECT_DRAFT_{path_date}.json:"
                f"fieldAuditMatrix.rows.{field_id}"
            )
            expected_scalars = {
                "draftRowId": field_id,
                "freezeFieldId": field_id,
                "sourceObject": expected_source,
                "status": FIELD_FREEZE_SOURCE_LOCK_STATUS,
                "matchesDraftRow": True,
                "matchesFreezeField": True,
            }
            for key, expected in expected_scalars.items():
                if row.get(key) != expected:
                    failures.append(f"fieldSourceLockMatrix.{field_id}.{key} must be {expected!r}")
            draft_row = draft_rows.get(field_id)
            freeze_field = by_id.get(field_id)
            if not isinstance(draft_row, dict):
                failures.append(f"fieldSourceLockMatrix.{field_id} missing draft fieldAuditMatrix row")
                continue
            if not isinstance(freeze_field, dict):
                failures.append(f"fieldSourceLockMatrix.{field_id} missing freeze field")
                continue
            expected_match_keys = [
                key
                for key in FIELD_FREEZE_SOURCE_LOCK_MATCH_KEYS
                if key in draft_row
            ]
            if row.get("requiredMatches") != expected_match_keys:
                failures.append(
                    f"fieldSourceLockMatrix.{field_id}.requiredMatches must be {expected_match_keys!r}"
                )
            for key in expected_match_keys:
                if freeze_field.get(key) != draft_row.get(key):
                    failures.append(
                        f"fieldSourceLockMatrix.{field_id}.{key} must match draft fieldAuditMatrix row"
                    )

    paste_sequence_matrix = packet.get("pasteSequenceMatrix")
    if not isinstance(paste_sequence_matrix, list):
        failures.append("pasteSequenceMatrix must be an array")
    else:
        by_paste_id: dict[str, dict[str, Any]] = {}
        paste_ids: list[str] = []
        for row in paste_sequence_matrix:
            if not isinstance(row, dict):
                failures.append("pasteSequenceMatrix entry must be an object")
                continue
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                failures.append("pasteSequenceMatrix entry missing id")
                continue
            if row_id in by_paste_id:
                failures.append(f"pasteSequenceMatrix duplicate {row_id}")
            by_paste_id[row_id] = row
            paste_ids.append(row_id)
        if tuple(paste_ids) != FIELD_FREEZE_PASTE_SEQUENCE_IDS:
            failures.append("pasteSequenceMatrix order must match App Store Connect field order")
        for expected_row in expected_field_freeze_paste_sequence_matrix(path_date):
            row_id = expected_row["id"]
            row = by_paste_id.get(row_id)
            if not row:
                failures.append(f"pasteSequenceMatrix missing {row_id}")
                continue
            if tuple(row) != FIELD_FREEZE_PASTE_SEQUENCE_FIELDS:
                failures.append(f"pasteSequenceMatrix.{row_id} keys must match paste sequence schema")
            freeze_field = by_id.get(row_id)
            for key, expected in expected_row.items():
                if row.get(key) != expected:
                    failures.append(f"pasteSequenceMatrix.{row_id}.{key} must be {expected!r}")
            if isinstance(freeze_field, dict):
                copy_source = row.get("copySource")
                if copy_source not in freeze_field.get("sourceFiles", []):
                    failures.append(f"pasteSequenceMatrix.{row_id}.copySource must be one of field sourceFiles")
                if row.get("ascEvidence") != freeze_field.get("ascEvidence"):
                    failures.append(f"pasteSequenceMatrix.{row_id}.ascEvidence must match freeze field")

    budget_matrix = packet.get("fieldBudgetMatrix")
    if not isinstance(budget_matrix, list):
        failures.append("fieldBudgetMatrix must be an array")
    else:
        by_budget_id: dict[str, dict[str, Any]] = {}
        budget_ids: list[str] = []
        for row in budget_matrix:
            if not isinstance(row, dict):
                failures.append("fieldBudgetMatrix entry must be an object")
                continue
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                failures.append("fieldBudgetMatrix entry missing id")
                continue
            if row_id in by_budget_id:
                failures.append(f"fieldBudgetMatrix duplicate {row_id}")
            by_budget_id[row_id] = row
            budget_ids.append(row_id)
        if tuple(budget_ids) != FIELD_FREEZE_BUDGET_IDS:
            failures.append("fieldBudgetMatrix order must match App Store Connect text budget order")
        for expected_row in expected_field_freeze_budget_matrix(
            keywords=keywords,
            promo=promo,
            description=description,
            release_notes=release_notes,
            review_text=review_text,
        ):
            row_id = expected_row["id"]
            row = by_budget_id.get(row_id)
            if not row:
                failures.append(f"fieldBudgetMatrix missing {row_id}")
                continue
            if tuple(row) != tuple(expected_row):
                failures.append(f"fieldBudgetMatrix.{row_id} keys must match text budget schema")
            for key, expected in expected_row.items():
                if row.get(key) != expected:
                    failures.append(f"fieldBudgetMatrix.{row_id}.{key} must be {expected!r}")

    post_gate_text = json.dumps(packet.get("postFreezeGates"), ensure_ascii=False)
    for marker in dated_markers(FIELD_FREEZE_POST_GATES, path_date):
        if marker not in post_gate_text:
            failures.append(f"postFreezeGates missing {marker}")

    completion_text = str(packet.get("completionRule", ""))
    for marker in FIELD_FREEZE_COMPLETION_MARKERS:
        if marker not in completion_text:
            failures.append(f"completionRule missing {marker}")

    unexpected_secret_hits = forbidden_review_account_secret_hits(packet_text)
    if unexpected_secret_hits:
        failures.append("fieldFreezePacket secret hits: " + ", ".join(unexpected_secret_hits))
    return failures


def app_store_connect_entry_session_packet_failures(
    packet: dict[str, Any],
    path_date: str,
) -> list[str]:
    if not packet:
        return ["missing entry session packet JSON"]

    failures: list[str] = []
    expected_scalars: dict[str, Any] = {
        "artifactType": "app-store-connect-entry-session-packet",
        "status": "entry-session-plan-not-evidence",
        "date": dashed_date(path_date),
        "project": "XiaoNaiPing",
        "appName": EXPECTED_APP_NAME,
        "bundleId": EXPECTED_BUNDLE_ID,
        "sku": "xiaonaiping-ios-1",
        "canSubmitFromThisPacket": False,
    }
    for key, expected in expected_scalars.items():
        if packet.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    expected_sources = {
        "draftJson": f"Docs/08_Release/APP_STORE_CONNECT_DRAFT_{path_date}.json",
        "fillSheet": f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
        "copyPastePacket": f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
        "finalEntryAudit": f"Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_{path_date}.md",
        "executionSheet": f"Docs/08_Release/AppStoreEvidence/AppStoreConnect/EXECUTION_SHEET_{path_date}.md",
        "privacyAnswers": f"Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_{path_date}.md",
        "privacyLabel": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        "ageRatingAnswers": f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
        "reviewInformation": f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md",
        "versionReleaseSettings": f"Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_{path_date}.md",
        "screenshotPlan": "Docs/08_Release/SCREENSHOT_PLAN.md",
        "evidenceChecklist": f"Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_{path_date}.md",
        "submissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
        "submitReviewPreflight": f"Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_{path_date}.json",
        "privacyAgeReviewResultTemplate": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-PRIVACY-AGE-REVIEW-RESULT.template.json",
    }
    for key, expected in expected_sources.items():
        if nested_value(packet, "sourceFiles", key) != expected:
            failures.append(f"sourceFiles.{key} must be {expected}")

    for key, expected in ENTRY_SESSION_TARGET_PAGE_EVIDENCE_FILES.items():
        if nested_value(packet, "targetPageEvidenceFiles", key) != expected:
            failures.append(f"targetPageEvidenceFiles.{key} must be {expected}")

    page_evidence_checks = packet.get("pageEvidenceFileChecks")
    if not isinstance(page_evidence_checks, list):
        failures.append("pageEvidenceFileChecks must be an array")
        page_evidence_checks = []
    page_check_order: list[str] = []
    page_check_by_id: dict[str, dict[str, Any]] = {}
    for item in page_evidence_checks:
        if not isinstance(item, dict):
            failures.append("pageEvidenceFileChecks entry must be an object")
            continue
        artifact_id = item.get("artifactId")
        if not isinstance(artifact_id, str) or not artifact_id:
            failures.append("pageEvidenceFileChecks entry missing artifactId")
            continue
        if artifact_id in page_check_by_id:
            failures.append(f"pageEvidenceFileChecks duplicate {artifact_id}")
        page_check_by_id[artifact_id] = item
        page_check_order.append(artifact_id)
    expected_page_check_order = tuple(ENTRY_SESSION_TARGET_PAGE_EVIDENCE_FILES)
    if tuple(page_check_order) != expected_page_check_order:
        failures.append("pageEvidenceFileChecks order must match targetPageEvidenceFiles")
    for artifact_id, expected_target in ENTRY_SESSION_TARGET_PAGE_EVIDENCE_FILES.items():
        item = page_check_by_id.get(artifact_id)
        if not item:
            failures.append(f"pageEvidenceFileChecks.{artifact_id} missing object")
            continue
        if item.get("target") != expected_target:
            failures.append(f"pageEvidenceFileChecks.{artifact_id}.target must be {expected_target}")
        for field, expected in ENTRY_SESSION_PAGE_EVIDENCE_FILE_CHECK_FIELDS:
            if item.get(field) != expected:
                failures.append(f"pageEvidenceFileChecks.{artifact_id}.{field} must be {expected!r}")

    field_locks = packet.get("fieldSourceLocks")
    if not isinstance(field_locks, list):
        failures.append("fieldSourceLocks must be an array")
        field_locks = []
    field_locks_by_id: dict[str, dict[str, Any]] = {}
    for lock in field_locks:
        if not isinstance(lock, dict):
            failures.append("fieldSourceLocks entry must be an object")
            continue
        lock_id = lock.get("id")
        if not isinstance(lock_id, str) or not lock_id:
            failures.append("fieldSourceLocks entry missing id")
            continue
        if lock_id in field_locks_by_id:
            failures.append(f"fieldSourceLocks duplicate {lock_id}")
        field_locks_by_id[lock_id] = lock
    for lock_id, markers in ENTRY_SESSION_FIELD_LOCK_REQUIREMENTS.items():
        lock = field_locks_by_id.get(lock_id)
        if not lock:
            failures.append(f"fieldSourceLocks missing {lock_id}")
            continue
        lock_text = json.dumps(lock, ensure_ascii=False)
        for marker in dated_markers(markers, path_date):
            if marker not in lock_text:
                failures.append(f"fieldSourceLocks.{lock_id} missing {marker}")

    sequence = packet.get("entrySequence")
    if not isinstance(sequence, list):
        failures.append("entrySequence must be an array")
        sequence = []
    sequence_ids: list[str] = []
    sequence_by_id: dict[str, dict[str, Any]] = {}
    for item in sequence:
        if not isinstance(item, dict):
            failures.append("entrySequence entry must be an object")
            continue
        step_id = item.get("id")
        if not isinstance(step_id, str) or not step_id:
            failures.append("entrySequence entry missing id")
            continue
        if step_id in sequence_by_id:
            failures.append(f"entrySequence duplicate id {step_id}")
        sequence_by_id[step_id] = item
        sequence_ids.append(step_id)
    if tuple(sequence_ids) != ENTRY_SESSION_SEQUENCE_IDS:
        failures.append("entrySequence order must match App Store Connect entry-session order")
    for step_id in ENTRY_SESSION_SEQUENCE_IDS:
        if step_id not in sequence_by_id:
            failures.append(f"entrySequence missing {step_id}")
    sequence_text = json.dumps(sequence, ensure_ascii=False)
    for marker in (
        "01-company-account.png",
        "AppleDeveloper/16-account-roles-access.png",
        "ASC-01-app-information.png",
        "ASC-08",
        "05-signed-archive.png",
        "06-testflight.png",
        "12-real-device-regression.md",
        "iOS 26.5",
    ):
        if marker not in sequence_text:
            failures.append(f"entrySequence missing marker {marker}")

    stop_conditions = packet.get("stopConditions")
    if not isinstance(stop_conditions, list):
        failures.append("stopConditions must be an array")
        stop_condition_set: set[str] = set()
    else:
        stop_condition_set = set()
        for item in stop_conditions:
            condition = str(item)
            if condition in stop_condition_set:
                failures.append(f"stopConditions duplicate {condition}")
            stop_condition_set.add(condition)
    for marker in ENTRY_SESSION_STOP_CONDITIONS:
        if marker not in stop_condition_set:
            failures.append(f"stopConditions missing {marker}")

    redaction = packet.get("redactionChecklist")
    redaction_text = json.dumps(redaction, ensure_ascii=False)
    if not isinstance(redaction, list):
        failures.append("redactionChecklist must be an array")
    for marker in ENTRY_SESSION_REDACTION_MARKERS:
        if marker not in redaction_text:
            failures.append(f"redactionChecklist missing {marker}")

    post_gates_text = json.dumps(packet.get("postEntryGates"), ensure_ascii=False)
    if not isinstance(packet.get("postEntryGates"), list):
        failures.append("postEntryGates must be an array")
    for marker in dated_markers(ENTRY_SESSION_POST_ENTRY_GATES, path_date):
        if marker not in post_gates_text:
            failures.append(f"postEntryGates missing {marker}")

    completion_text = json.dumps(
        [packet.get("completionRule"), packet.get("noSubmitBoundary")],
        ensure_ascii=False,
    )
    for marker in dated_markers(ENTRY_SESSION_COMPLETION_MARKERS, path_date):
        if marker not in completion_text:
            failures.append(f"completion boundary missing {marker}")
    for marker in ENTRY_SESSION_FORBIDDEN_COMPLETION_MARKERS:
        if marker in completion_text:
            failures.append(f"completion boundary must not include stale cross-app marker {marker}")

    secret_hits = forbidden_review_account_secret_hits(json.dumps(packet, ensure_ascii=False))
    if secret_hits:
        failures.append("entrySessionPacket secret hits: " + ", ".join(secret_hits))
    return failures


def app_store_connect_submit_review_preflight_failures(
    packet: dict[str, Any],
    path_date: str,
) -> list[str]:
    if not packet:
        return ["missing Submit for Review preflight packet JSON"]

    failures: list[str] = []
    expected_scalars: dict[str, Any] = {
        "artifactType": "app-store-connect-submit-review-preflight",
        "status": "preflight-plan-not-evidence",
        "date": dashed_date(path_date),
        "project": "XiaoNaiPing",
        "appName": EXPECTED_APP_NAME,
        "bundleId": EXPECTED_BUNDLE_ID,
        "canSubmitFromThisPacket": False,
    }
    for key, expected in expected_scalars.items():
        if packet.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    for key, expected in SUBMIT_REVIEW_PREFLIGHT_SOURCE_FILES.items():
        dated_expected = expected.replace("20260627", path_date)
        if nested_value(packet, "sourceFiles", key) != dated_expected:
            failures.append(f"sourceFiles.{key} must be {dated_expected}")

    for key, expected in SUBMIT_REVIEW_PREFLIGHT_TARGET_PAGE_EVIDENCE.items():
        if nested_value(packet, "targetPageEvidence", key) != expected:
            failures.append(f"targetPageEvidence.{key} must be {expected}")

    green_checks = packet.get("mustBeGreenBeforeSubmit")
    if not isinstance(green_checks, list):
        failures.append("mustBeGreenBeforeSubmit must be an array")
        green_checks = []
    check_ids: list[str] = []
    checks_by_id: dict[str, dict[str, Any]] = {}
    for item in green_checks:
        if not isinstance(item, dict):
            failures.append("mustBeGreenBeforeSubmit entry must be an object")
            continue
        check_id = item.get("id")
        if not isinstance(check_id, str) or not check_id:
            failures.append("mustBeGreenBeforeSubmit entry missing id")
            continue
        if check_id in checks_by_id:
            failures.append(f"mustBeGreenBeforeSubmit duplicate {check_id}")
        checks_by_id[check_id] = item
        check_ids.append(check_id)
    if tuple(check_ids) != SUBMIT_REVIEW_PREFLIGHT_GREEN_CHECK_IDS:
        failures.append("mustBeGreenBeforeSubmit order must match Submit for Review blocker order")

    for check_id, markers in SUBMIT_REVIEW_PREFLIGHT_GREEN_CHECKS.items():
        item = checks_by_id.get(check_id)
        if not item:
            failures.append(f"mustBeGreenBeforeSubmit missing {check_id}")
            continue
        proof, required_state, *evidence_markers = markers
        if item.get("proof") != proof:
            failures.append(f"mustBeGreenBeforeSubmit.{check_id}.proof must be {proof}")
        if item.get("requiredState") != required_state:
            failures.append(f"mustBeGreenBeforeSubmit.{check_id}.requiredState must be {required_state}")
        item_text = json.dumps(item, ensure_ascii=False)
        for marker in evidence_markers:
            if marker not in item_text:
                failures.append(f"mustBeGreenBeforeSubmit.{check_id} missing {marker}")

    dependency_matrix = packet.get("submissionDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("submissionDependencyMatrix must be an array")
    else:
        dependency_ids: list[str] = []
        dependency_by_id: dict[str, dict[str, Any]] = {}
        for item in dependency_matrix:
            if not isinstance(item, dict):
                failures.append("submissionDependencyMatrix entry must be an object")
                continue
            dependency_id = item.get("id")
            if not isinstance(dependency_id, str) or not dependency_id:
                failures.append("submissionDependencyMatrix entry missing id")
                continue
            if dependency_id in dependency_by_id:
                failures.append(f"submissionDependencyMatrix duplicate {dependency_id}")
            dependency_by_id[dependency_id] = item
            dependency_ids.append(dependency_id)

        expected_dependency_ids = tuple(item["id"] for item in SUBMIT_REVIEW_PREFLIGHT_DEPENDENCY_MATRIX)
        if tuple(dependency_ids) != expected_dependency_ids:
            failures.append("submissionDependencyMatrix order must match Submit for Review dependency order")

        for expected in SUBMIT_REVIEW_PREFLIGHT_DEPENDENCY_MATRIX:
            dependency_id = expected["id"]
            item = dependency_by_id.get(dependency_id)
            if not item:
                failures.append(f"submissionDependencyMatrix missing {dependency_id}")
                continue
            if tuple(item) != SUBMIT_REVIEW_PREFLIGHT_DEPENDENCY_FIELDS:
                failures.append(
                    f"submissionDependencyMatrix.{dependency_id} keys must be "
                    + ", ".join(SUBMIT_REVIEW_PREFLIGHT_DEPENDENCY_FIELDS)
                )
            for field in SUBMIT_REVIEW_PREFLIGHT_DEPENDENCY_FIELDS:
                if item.get(field) == expected[field]:
                    continue
                expected_value = expected[field]
                if isinstance(expected_value, list):
                    expected_text = ", ".join(expected_value)
                elif isinstance(expected_value, bool):
                    expected_text = str(expected_value)
                else:
                    expected_text = str(expected_value)
                failures.append(f"submissionDependencyMatrix.{dependency_id}.{field} must be {expected_text}")

    decision_text = json.dumps(packet.get("submitButtonDecision"), ensure_ascii=False)
    if not isinstance(packet.get("submitButtonDecision"), dict):
        failures.append("submitButtonDecision must be an object")
    for marker in SUBMIT_REVIEW_PREFLIGHT_DECISION_MARKERS:
        if marker not in decision_text:
            failures.append(f"submitButtonDecision missing {marker}")

    redaction = packet.get("redactionChecklist")
    redaction_text = json.dumps(redaction, ensure_ascii=False)
    if not isinstance(redaction, list):
        failures.append("redactionChecklist must be an array")
    for marker in ENTRY_SESSION_REDACTION_MARKERS:
        if marker not in redaction_text:
            failures.append(f"redactionChecklist missing {marker}")

    post_gates_text = json.dumps(packet.get("postPreflightGates"), ensure_ascii=False)
    if not isinstance(packet.get("postPreflightGates"), list):
        failures.append("postPreflightGates must be an array")
    for marker in dated_markers(SUBMIT_REVIEW_PREFLIGHT_POST_GATES, path_date):
        if marker not in post_gates_text:
            failures.append(f"postPreflightGates missing {marker}")

    completion_text = json.dumps(
        [packet.get("completionRule"), packet.get("noSubmitBoundary")],
        ensure_ascii=False,
    )
    for marker in SUBMIT_REVIEW_PREFLIGHT_COMPLETION_MARKERS:
        if marker not in completion_text:
            failures.append(f"completion boundary missing {marker}")

    secret_hits = forbidden_review_account_secret_hits(json.dumps(packet, ensure_ascii=False))
    if secret_hits:
        failures.append("submitReviewPreflight secret hits: " + ", ".join(secret_hits))
    return failures


def app_store_connect_backfill_result_template_failures(
    template: dict[str, Any],
    path_date: str,
) -> list[str]:
    if not template:
        return ["missing ASC backfill result template JSON"]

    failures: list[str] = []
    expected_scalars: dict[str, Any] = {
        "status": "template-not-evidence",
        "app": EXPECTED_APP_NAME,
        "bundleId": EXPECTED_BUNDLE_ID,
        "expectedDate": dashed_date(path_date),
        "capturedAt": "",
        "capturedBy": "佘鹏辉 / Penghui She",
        "canSubmitAtCapture": False,
        "submissionReadinessProof": "Backend/proof/launch-objective-audit.json",
        "doNotTreatAsSubmitPermission": True,
        "redactionReviewed": False,
    }
    for key, expected in expected_scalars.items():
        if template.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    expected_sources = (
        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
        f"Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_{path_date}.md",
        "Backend/proof/app-store-evidence.json",
        "Backend/proof/production-readiness.json",
        "Backend/proof/launch-objective-audit.json",
        "Backend/proof/testflight-regression-plan.json",
        "Backend/proof/provider-evidence-materials.json",
        "Backend/proof/mainland-filing-materials.json",
        "Backend/proof/signed-archive-testflight-materials.json",
    )
    if tuple(template.get("sourceDocuments") or ()) != expected_sources:
        failures.append(
            "sourceDocuments must match ASC copy, final audit, and XiaoNaiPing proofs"
        )
    if template.get("xiaonaipingSubmissionProofs") != ASC_BACKFILL_RESULT_TEMPLATE_XNP_PROOFS:
        failures.append("xiaonaipingSubmissionProofs must lock XiaoNaiPing App Store, production, audit, TestFlight, provider, filing, and signing proofs")

    field_freeze = template.get("fieldFreeze")
    if not isinstance(field_freeze, dict):
        failures.append("fieldFreeze must be an object")
        field_freeze = {}
    if tuple(field_freeze.get("sourceSnapshot") or ()) != expected_sources:
        failures.append("fieldFreeze.sourceSnapshot must match sourceDocuments")
    if field_freeze.get("screenshotsRefreshed") is not False:
        failures.append("fieldFreeze.screenshotsRefreshed must be False")
    expected_rerun_proofs = {
        key: dated_markers((value,), path_date)[0]
        for key, value in ASC_BACKFILL_RESULT_TEMPLATE_RERUN_PROOFS.items()
    }
    if field_freeze.get("rerunProofs") != expected_rerun_proofs:
        failures.append("fieldFreeze.rerunProofs must include XiaoNaiPing proof reruns")

    session = template.get("backfillSessionIntegrity")
    if not isinstance(session, dict):
        failures.append("backfillSessionIntegrity must be an object")
    else:
        for key, expected in asc_backfill_result_template_session_scalars(path_date).items():
            if session.get(key) != expected:
                failures.append(f"backfillSessionIntegrity.{key} must be {expected}")

        source_files = session.get("sourceFiles")
        if source_files != asc_backfill_result_template_session_source_files(path_date):
            failures.append("backfillSessionIntegrity.sourceFiles must lock draft, fill sheet, copy-paste, field freeze, final audit, and review information")

        page_groups = session.get("pageGroups")
        if not isinstance(page_groups, dict):
            failures.append("backfillSessionIntegrity.pageGroups must be an object")
        else:
            if tuple(page_groups) != tuple(ASC_BACKFILL_RESULT_TEMPLATE_SESSION_PAGE_GROUPS):
                failures.append("backfillSessionIntegrity.pageGroups order must match ASC page groups")
            for group, expected_fields in ASC_BACKFILL_RESULT_TEMPLATE_SESSION_PAGE_GROUPS.items():
                if tuple(page_groups.get(group) or ()) != expected_fields:
                    failures.append(f"backfillSessionIntegrity.pageGroups.{group} must be {', '.join(expected_fields)}")

        page_evidence = session.get("pageEvidence")
        if page_evidence != ASC_BACKFILL_RESULT_TEMPLATE_SESSION_PAGE_EVIDENCE:
            failures.append("backfillSessionIntegrity.pageEvidence must map ASC-01/02/05/06 to draft field evidence")

        flags = session.get("sessionFlags")
        if not isinstance(flags, dict):
            failures.append("backfillSessionIntegrity.sessionFlags must be an object")
        else:
            if tuple(flags) != ASC_BACKFILL_RESULT_TEMPLATE_SESSION_FLAGS:
                failures.append("backfillSessionIntegrity.sessionFlags order must match source/page/session/redaction checks")
            for flag in ASC_BACKFILL_RESULT_TEMPLATE_SESSION_FLAGS:
                if flags.get(flag) is not False:
                    failures.append(f"backfillSessionIntegrity.sessionFlags.{flag} must be False")

        stop_conditions = session.get("stopConditions")
        if not isinstance(stop_conditions, list):
            failures.append("backfillSessionIntegrity.stopConditions must be a list")
        else:
            by_id: dict[str, dict[str, Any]] = {}
            order: list[Any] = []
            for item in stop_conditions:
                if not isinstance(item, dict):
                    failures.append("backfillSessionIntegrity.stopConditions entries must be objects")
                    continue
                condition_id = item.get("id")
                order.append(condition_id)
                if not isinstance(condition_id, str) or not condition_id:
                    failures.append("backfillSessionIntegrity.stopConditions entry missing id")
                    continue
                if condition_id in by_id:
                    failures.append(f"backfillSessionIntegrity.stopConditions duplicate {condition_id}")
                by_id[condition_id] = item
            if tuple(order) != tuple(ASC_BACKFILL_RESULT_TEMPLATE_STOP_CONDITION_MARKERS):
                failures.append("backfillSessionIntegrity.stopConditions order must match ASC backfill stop conditions")
            for condition_id, markers in ASC_BACKFILL_RESULT_TEMPLATE_STOP_CONDITION_MARKERS.items():
                item = by_id.get(condition_id)
                if not isinstance(item, dict):
                    failures.append(f"backfillSessionIntegrity.stopConditions missing {condition_id}")
                    continue
                text = json.dumps(item, ensure_ascii=False)
                for marker in markers:
                    if marker not in text:
                        failures.append(f"backfillSessionIntegrity.stopConditions.{condition_id} missing {marker}")

    instruction_text = json.dumps(template.get("instructions"), ensure_ascii=False)
    for marker in ASC_BACKFILL_RESULT_TEMPLATE_INSTRUCTION_MARKERS:
        if marker not in instruction_text:
            failures.append(f"instructions missing {marker}")

    private_field_checks = template.get("appReviewInformationPrivateFieldChecks")
    if not isinstance(private_field_checks, dict):
        failures.append("appReviewInformationPrivateFieldChecks must be an object")
    else:
        for key, expected in ASC_BACKFILL_RESULT_TEMPLATE_PRIVATE_FIELD_TARGETS.items():
            if private_field_checks.get(key) != expected:
                failures.append(f"appReviewInformationPrivateFieldChecks.{key} must be {expected}")
        for key, expected in ASC_BACKFILL_RESULT_TEMPLATE_PRIVATE_FIELD_PLACEHOLDERS.items():
            if private_field_checks.get(key) != expected:
                failures.append(f"appReviewInformationPrivateFieldChecks.{key} must be {expected!r}")

    field_entries = template.get("fieldEntryChecks")
    if not isinstance(field_entries, list):
        failures.append("fieldEntryChecks must be a list")
    else:
        entries_by_id: dict[str, dict[str, Any]] = {}
        entry_order: list[Any] = []
        for entry in field_entries:
            if not isinstance(entry, dict):
                failures.append("fieldEntryChecks entries must be objects")
                continue
            entry_id = entry.get("id")
            entry_order.append(entry_id)
            if not isinstance(entry_id, str) or not entry_id:
                failures.append("fieldEntryChecks entry missing id")
                continue
            if entry_id in entries_by_id:
                failures.append(f"fieldEntryChecks duplicate {entry_id}")
            entries_by_id[entry_id] = entry

        if tuple(entry_order) != FIELD_AUDIT_MATRIX_ROW_IDS:
            failures.append("fieldEntryChecks order must match App Store Connect field order")

        expected_field_freeze_packet = f"Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_{path_date}.json"
        for field_id in FIELD_AUDIT_MATRIX_ROW_IDS:
            entry = entries_by_id.get(field_id)
            if not isinstance(entry, dict):
                failures.append(f"fieldEntryChecks.{field_id} missing object")
                continue
            for key, expected in FIELD_AUDIT_MATRIX_EXACT_VALUES.get(field_id, {}).items():
                if entry.get(key) != expected:
                    failures.append(f"fieldEntryChecks.{field_id}.{key} must be {expected}")
            if entry.get("sourceFieldFreezePacket") != expected_field_freeze_packet:
                failures.append(
                    f"fieldEntryChecks.{field_id}.sourceFieldFreezePacket must be {expected_field_freeze_packet}"
                )
            expected_target = ASC_BACKFILL_RESULT_TEMPLATE_FIELD_ENTRY_TARGETS[field_id]
            if entry.get("targetPage") != expected_target:
                failures.append(f"fieldEntryChecks.{field_id}.targetPage must be {expected_target}")
            for key, expected in ASC_BACKFILL_RESULT_TEMPLATE_FIELD_ENTRY_PLACEHOLDERS.items():
                if entry.get(key) != expected:
                    failures.append(f"fieldEntryChecks.{field_id}.{key} must be {expected!r}")

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

        if tuple(artifact_order) != tuple(ASC_BACKFILL_RESULT_TEMPLATE_FILE_CHECKS):
            failures.append("evidenceFileChecks order must match App Store Connect backfill workflow")

        for artifact_id, target_marker in ASC_BACKFILL_RESULT_TEMPLATE_FILE_CHECKS.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"evidenceFileChecks.{artifact_id} missing object")
                continue
            if target_marker not in str(check.get("target", "")):
                failures.append(f"evidenceFileChecks.{artifact_id}.target missing {target_marker}")
            for key, expected in ASC_BACKFILL_RESULT_TEMPLATE_FILE_CHECK_PLACEHOLDERS.items():
                if check.get(key) != expected:
                    failures.append(f"evidenceFileChecks.{artifact_id}.{key} must be {expected!r}")

    screenshots = template.get("screenshots")
    if not isinstance(screenshots, dict):
        failures.append("screenshots must be an object")
        screenshots = {}
    for section, (expected_file, required_flag) in ASC_BACKFILL_RESULT_TEMPLATE_SCREENSHOTS.items():
        section_value = screenshots.get(section)
        if not isinstance(section_value, dict):
            failures.append(f"screenshots.{section} must be an object")
            continue
        if tuple(section_value.get("screenshotFiles") or ()) != (expected_file,):
            failures.append(f"screenshots.{section}.screenshotFiles must be {expected_file}")
        if section_value.get(required_flag) is not False:
            failures.append(f"screenshots.{section}.{required_flag} must be False")
    age_rating = screenshots.get("ageRating") if isinstance(screenshots, dict) else {}
    if isinstance(age_rating, dict) and age_rating.get("regulatedMedicalDeviceAnswerVisible") is not False:
        failures.append("screenshots.ageRating.regulatedMedicalDeviceAnswerVisible must be False")

    template_text = json.dumps(template, ensure_ascii=False)
    for marker in (
        "This template is not evidence",
        "captured-live-backfill",
        "all screenshots exist",
        "fieldEntryChecks confirm every App Store Connect draft field",
        "matches the field-freeze packet and ASC page evidence",
        "evidenceFileChecks are filled with file size",
        "SHA-256",
        "same-session",
        "approved root",
        "field-freeze",
        "redactionReviewed is true",
        "current XiaoNaiPing submission proofs are attached",
        "XiaoNaiPing proof reruns stay current before Submit for Review",
    ):
        if marker not in template_text:
            failures.append(f"notes missing {marker}")

    secret_hits = forbidden_review_account_secret_hits(template_text)
    if secret_hits:
        failures.append("ascBackfillResultTemplate secret hits: " + ", ".join(secret_hits))
    return failures


def app_store_connect_privacy_age_review_template_failures(
    template: dict[str, Any],
    path_date: str,
) -> list[str]:
    if not template:
        return ["missing ASC privacy/age/review result template JSON"]

    failures: list[str] = []
    expected_scalars: dict[str, Any] = {
        "artifactType": "asc-privacy-age-review-result-template",
        "status": "template-not-evidence",
        "date": dashed_date(path_date),
        "project": "XiaoNaiPing",
        "appName": EXPECTED_APP_NAME,
        "bundleId": EXPECTED_BUNDLE_ID,
        "capturedAt": "",
        "capturedBy": "佘鹏辉 / Penghui She",
        "canSubmitFromThisTemplate": False,
        "doNotTreatAsSubmitPermission": True,
        "redactionReviewed": False,
    }
    for key, expected in expected_scalars.items():
        if template.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    for key, expected in ASC_PRIVACY_AGE_REVIEW_TEMPLATE_SOURCE_FILES.items():
        dated_expected = expected.replace("20260627", path_date)
        if nested_value(template, "sourceFiles", key) != dated_expected:
            failures.append(f"sourceFiles.{key} must be {dated_expected}")

    for key, expected in ASC_PRIVACY_AGE_REVIEW_TEMPLATE_TARGETS.items():
        if nested_value(template, "targetEvidenceFiles", key) != expected:
            failures.append(f"targetEvidenceFiles.{key} must be {expected}")

    file_checks = template.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append("evidenceFileChecks must be a list")
        file_checks = []
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
    if tuple(artifact_order) != tuple(ASC_PRIVACY_AGE_REVIEW_TEMPLATE_TARGETS):
        failures.append("evidenceFileChecks order must match privacy/age/review target evidence workflow")
    for artifact_id, expected_target in ASC_PRIVACY_AGE_REVIEW_TEMPLATE_TARGETS.items():
        check = checks_by_artifact.get(artifact_id)
        if not isinstance(check, dict):
            failures.append(f"evidenceFileChecks.{artifact_id} missing object")
            continue
        if check.get("target") != expected_target:
            failures.append(f"evidenceFileChecks.{artifact_id}.target must be {expected_target}")
        for key, expected in ASC_PRIVACY_AGE_REVIEW_TEMPLATE_FILE_CHECK_FIELDS.items():
            if check.get(key) != expected:
                failures.append(f"evidenceFileChecks.{artifact_id}.{key} must be {expected!r}")

    dependency_matrix = template.get("evidenceDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("evidenceDependencyMatrix must be a list")
        dependency_matrix = []
    matrix_order: list[Any] = []
    matrix_by_artifact: dict[str, dict[str, Any]] = {}
    for entry in dependency_matrix:
        if not isinstance(entry, dict):
            failures.append("evidenceDependencyMatrix entries must be objects")
            continue
        artifact_id = entry.get("artifactId")
        matrix_order.append(artifact_id)
        if not isinstance(artifact_id, str) or not artifact_id:
            failures.append("evidenceDependencyMatrix entry missing artifactId")
            continue
        if artifact_id in matrix_by_artifact:
            failures.append(f"evidenceDependencyMatrix duplicate {artifact_id}")
        matrix_by_artifact[artifact_id] = entry
    if tuple(matrix_order) != tuple(ASC_PRIVACY_AGE_REVIEW_TEMPLATE_DEPENDENCY_MATRIX):
        failures.append("evidenceDependencyMatrix order must match privacy/age/review target evidence workflow")
    for artifact_id, expected in ASC_PRIVACY_AGE_REVIEW_TEMPLATE_DEPENDENCY_MATRIX.items():
        entry = matrix_by_artifact.get(artifact_id)
        if not isinstance(entry, dict):
            failures.append(f"evidenceDependencyMatrix.{artifact_id} missing object")
            continue
        if tuple(entry) != ASC_PRIVACY_AGE_REVIEW_TEMPLATE_DEPENDENCY_MATRIX_SCHEMA:
            failures.append(
                f"evidenceDependencyMatrix.{artifact_id} keys must be "
                + ", ".join(ASC_PRIVACY_AGE_REVIEW_TEMPLATE_DEPENDENCY_MATRIX_SCHEMA)
            )
        for key, expected_value in expected.items():
            if entry.get(key) != expected_value:
                if isinstance(expected_value, list):
                    failures.append(
                        f"evidenceDependencyMatrix.{artifact_id}.{key} must be "
                        + ", ".join(expected_value)
                    )
                else:
                    failures.append(f"evidenceDependencyMatrix.{artifact_id}.{key} must be {expected_value}")

    sections = template.get("resultSections")
    if not isinstance(sections, list):
        failures.append("resultSections must be a list")
        sections = []
    section_order: list[Any] = []
    sections_by_id: dict[str, dict[str, Any]] = {}
    for section in sections:
        if not isinstance(section, dict):
            failures.append("resultSections entries must be objects")
            continue
        section_id = section.get("id")
        section_order.append(section_id)
        if not isinstance(section_id, str) or not section_id:
            failures.append("resultSections entry missing id")
            continue
        if section_id in sections_by_id:
            failures.append(f"resultSections duplicate {section_id}")
        sections_by_id[section_id] = section
    if tuple(section_order) != tuple(ASC_PRIVACY_AGE_REVIEW_TEMPLATE_SECTION_MARKERS):
        failures.append("resultSections order must be appPrivacy, ageRating, reviewInformation")
    for section_id, markers in ASC_PRIVACY_AGE_REVIEW_TEMPLATE_SECTION_MARKERS.items():
        section = sections_by_id.get(section_id)
        if not isinstance(section, dict):
            failures.append(f"resultSections.{section_id} missing object")
            continue
        section_text = json.dumps(section, ensure_ascii=False)
        for marker in markers:
            if marker not in section_text:
                failures.append(f"resultSections.{section_id} missing {marker}")

    stop_conditions = template.get("stopConditions")
    if not isinstance(stop_conditions, list):
        failures.append("stopConditions must be a list")
        stop_condition_set: set[str] = set()
    else:
        stop_condition_set = set()
        for condition in stop_conditions:
            condition_text = str(condition)
            if condition_text in stop_condition_set:
                failures.append(f"stopConditions duplicate {condition_text}")
            stop_condition_set.add(condition_text)
    for marker in ASC_PRIVACY_AGE_REVIEW_TEMPLATE_STOP_CONDITIONS:
        if marker not in stop_condition_set:
            failures.append(f"stopConditions missing {marker}")

    redaction_text = json.dumps(template.get("redactionChecklist"), ensure_ascii=False)
    if not isinstance(template.get("redactionChecklist"), list):
        failures.append("redactionChecklist must be a list")
    for marker in ENTRY_SESSION_REDACTION_MARKERS + ("complete D-U-N-S number", "provisioning profile contents"):
        if marker not in redaction_text:
            failures.append(f"redactionChecklist missing {marker}")

    post_gates_text = json.dumps(template.get("postResultGates"), ensure_ascii=False)
    if not isinstance(template.get("postResultGates"), list):
        failures.append("postResultGates must be a list")
    for marker in dated_markers(ASC_PRIVACY_AGE_REVIEW_TEMPLATE_POST_GATES, path_date):
        if marker not in post_gates_text:
            failures.append(f"postResultGates missing {marker}")

    template_text = json.dumps(template, ensure_ascii=False)
    for marker in ASC_PRIVACY_AGE_REVIEW_TEMPLATE_MARKERS:
        if marker not in template_text:
            failures.append(f"template missing {marker}")

    secret_hits = forbidden_review_account_secret_hits(template_text)
    if secret_hits:
        failures.append("ascPrivacyAgeReviewResultTemplate secret hits: " + ", ".join(secret_hits))
    return failures


def copy_paste_sync_failures(fill_sheet: str, copy_paste_packet: str) -> list[str]:
    failures: list[str] = []
    for fill_heading, copy_heading in COPY_PASTE_SYNC_SECTION_PAIRS:
        fill_value = extract_first_code_block(extract_section(fill_sheet, fill_heading))
        copy_value = extract_first_code_block(extract_section(copy_paste_packet, copy_heading))
        if not fill_value:
            failures.append(f"{fill_heading}: missing fill sheet code block")
        elif not copy_value:
            failures.append(f"{copy_heading}: missing copy-paste code block")
        elif fill_value != copy_value:
            failures.append(f"{copy_heading}: differs from fill sheet {fill_heading}")
    return failures


def strip_cell_markup(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_app_information_table(section: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [strip_cell_markup(cell) for cell in stripped.strip("|").split("|")]
        if len(cells) < 2 or cells[0] == "字段":
            continue
        rows[cells[0]] = cells[1]
    return rows


def parse_app_information_copy_block(section: str) -> dict[str, str]:
    block = extract_first_code_block(section)
    rows: dict[str, str] = {}
    for line in block.splitlines():
        if "：" not in line:
            continue
        key, value = line.split("：", 1)
        rows[key.strip()] = strip_cell_markup(value)
    return rows


def normalize_app_information_copy_value(field: str, value: str) -> str:
    if field == "第二类别" and value.startswith("留空"):
        return "留空"
    return value


def app_information_copy_sync_failures(fill_sheet: str, copy_paste_packet: str) -> list[str]:
    failures: list[str] = []
    fill_section = extract_section(fill_sheet, "App 信息")
    copy_section = extract_section(copy_paste_packet, "App 信息")
    if not fill_section:
        return ["App 信息: missing fill sheet section"]
    if not copy_section:
        return ["App 信息: missing copy-paste section"]

    fill_rows = parse_app_information_table(fill_section)
    copy_rows = parse_app_information_copy_block(copy_section)
    copy_order = tuple(copy_rows)
    if copy_order != APP_INFORMATION_COPY_FIELDS:
        failures.append("App 信息 copy-paste field order must match fill sheet entry order")

    for field in APP_INFORMATION_COPY_FIELDS:
        fill_value = fill_rows.get(field)
        copy_value = copy_rows.get(field)
        if fill_value is None:
            failures.append(f"App 信息.{field} missing from fill sheet")
            continue
        if copy_value is None:
            failures.append(f"App 信息.{field} missing from copy-paste packet")
            continue
        expected = normalize_app_information_copy_value(field, fill_value)
        if copy_value != expected:
            failures.append(f"App 信息.{field} copy value must be {expected}")
    return failures


def utf8_bytes(value: str) -> int:
    return len(value.encode("utf-8"))


def char_budget_row(label: str, limit: int, value: str) -> str:
    return f"| {label} | {limit} 字符 | {len(value)} 字符 | 剩余 {limit - len(value)} 字符 |"


def byte_budget_row(label: str, limit: int, value: str) -> str:
    used = utf8_bytes(value)
    return f"| {label} | {limit} UTF-8 bytes | {used} bytes | 剩余 {limit - used} bytes |"


def expected_field_budget_rows(
    *,
    keywords: str,
    promo: str,
    description: str,
    release_notes: str,
    review_text: str,
) -> list[str]:
    return [
        char_budget_row("App 名称", 30, EXPECTED_APP_NAME),
        char_budget_row("副标题", 30, EXPECTED_SUBTITLE),
        byte_budget_row("关键词", KEYWORDS_MAX_BYTES, keywords),
        char_budget_row("宣传文本", PROMOTIONAL_TEXT_MAX_CHARS, promo),
        char_budget_row("描述", LONG_TEXT_MAX_CHARS, description),
        char_budget_row("新版本说明", LONG_TEXT_MAX_CHARS, release_notes),
        char_budget_row("审核备注", LONG_TEXT_MAX_CHARS, review_text),
    ]


def field_budget_failures(documents: list[tuple[str, str]], expected_rows: list[str]) -> list[str]:
    failures: list[str] = []
    for label, text in documents:
        section = extract_section(text, "字段预算")
        if not section:
            failures.append(f"{label}: missing ## 字段预算")
            continue
        if "关键词按 UTF-8 bytes 计算" not in section:
            failures.append(f"{label}: missing UTF-8 bytes note")
        for row in expected_rows:
            if row not in section:
                failures.append(f"{label}: missing {row}")
    return failures


def screenshot_copy_rows(section: str) -> str:
    rows = [
        line
        for line in section.splitlines()
        if re.match(r"^\|\s*[1-9][0-9]*\s*\|", line.strip())
    ]
    return "\n".join(rows)


def forbidden_review_account_secret_hits(text: str) -> list[str]:
    return sorted(
        name
        for name, pattern in FORBIDDEN_REVIEW_ACCOUNT_SECRET_PATTERNS.items()
        if pattern.search(text)
    )


def review_account_evidence_failures(evidence: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not evidence:
        return ["missing Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json"]
    if not evidence.get("accountId"):
        failures.append("accountId missing")
    if evidence.get("baseUrl") != "https://api.mewpow.com/xiaonaiping":
        failures.append("baseUrl mismatch")
    if evidence.get("recoveryKeyStored") != ".env.xnp-review-account":
        failures.append("recoveryKeyStored must be .env.xnp-review-account")
    if evidence.get("recoveryVerified") is not True:
        failures.append("recoveryVerified must be true")
    if evidence.get("syncSeeded") is not True:
        failures.append("syncSeeded must be true")
    if evidence.get("containsSecret") is not False:
        failures.append("containsSecret must be false")

    forbidden_fields = sorted(
        key
        for key in evidence
        if key != "containsSecret"
        and any(marker in str(key).lower() for marker in ("secret", "token", "password", "code"))
    )
    if forbidden_fields:
        failures.append("forbidden fields: " + ", ".join(forbidden_fields))

    secret_hits = forbidden_review_account_secret_hits(json.dumps(evidence, ensure_ascii=False))
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def app_review_test_account_packet_failures(
    packet: dict[str, Any],
    path_date: str,
    review_account_evidence: dict[str, Any],
) -> list[str]:
    if not packet:
        return ["missing app review test account packet JSON"]

    failures: list[str] = []
    expected_scalars: dict[str, Any] = {
        "artifactType": "app-review-test-account-packet",
        "status": "review-test-account-packet-not-evidence",
        "date": dashed_date(path_date),
        "project": "XiaoNaiPing",
        "appName": EXPECTED_APP_NAME,
        "evidenceRoot": APP_REVIEW_TEST_ACCOUNT_EVIDENCE_ROOT,
        "canSubmitFromThisPacket": False,
    }
    for key, expected in expected_scalars.items():
        if packet.get(key) != expected:
            failures.append(f"{key} must be {str(expected).lower() if isinstance(expected, bool) else expected}")

    for key, expected in APP_REVIEW_TEST_ACCOUNT_REQUIRED_SOURCE_FILES.items():
        dated_expected = expected.replace("20260627", path_date)
        if nested_value(packet, "sourceFiles", key) != dated_expected:
            failures.append(f"sourceFiles.{key} must be {dated_expected}")

    private_source = packet.get("privateCredentialSource")
    if not isinstance(private_source, dict):
        failures.append("privateCredentialSource must be an object")
        private_source = {}
    private_text = json.dumps(private_source, ensure_ascii=False)
    for marker in APP_REVIEW_TEST_ACCOUNT_PRIVATE_MARKERS:
        if marker not in private_text:
            failures.append(f"privateCredentialSource missing {marker}")
    if private_source.get("repositoryStorageAllowed") is not False:
        failures.append("privateCredentialSource.repositoryStorageAllowed must be false")

    sign_in = packet.get("appReviewSignInFields")
    if not isinstance(sign_in, dict):
        failures.append("appReviewSignInFields must be an object")
        sign_in = {}
    expected_sign_in: dict[str, Any] = {
        "signInRequired": True,
        "username": "review-recovery-key-account",
        "credentialSource": ".env.xnp-review-account:XNP_REVIEW_RECOVERY_KEY",
        "debugCodeAllowed": False,
    }
    for key, expected in expected_sign_in.items():
        if sign_in.get(key) != expected:
            failures.append(f"appReviewSignInFields.{key} must be {str(expected).lower() if isinstance(expected, bool) else expected}")
    sign_in_text = json.dumps(sign_in, ensure_ascii=False)
    for marker in APP_REVIEW_TEST_ACCOUNT_SIGN_IN_MARKERS:
        if marker not in sign_in_text:
            failures.append(f"appReviewSignInFields missing {marker}")

    redacted_required = packet.get("redactedEvidenceRequired")
    if not isinstance(redacted_required, dict):
        failures.append("redactedEvidenceRequired must be an object")
        redacted_required = {}
    expected_redacted_required: dict[str, Any] = {
        "targetFile": "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
        "baseUrl": "https://api.mewpow.com/xiaonaiping",
        "recoveryKeyStored": ".env.xnp-review-account",
        "recoveryVerified": True,
        "syncSeeded": True,
        "containsSecret": False,
    }
    for key, expected in expected_redacted_required.items():
        if redacted_required.get(key) != expected:
            failures.append(f"redactedEvidenceRequired.{key} must be {str(expected).lower() if isinstance(expected, bool) else expected}")
    redacted_text = json.dumps(redacted_required, ensure_ascii=False)
    for marker in APP_REVIEW_TEST_ACCOUNT_REDACTED_EVIDENCE_MARKERS:
        if marker not in redacted_text:
            failures.append(f"redactedEvidenceRequired missing {marker}")

    evidence_file_checks = packet.get("evidenceFileChecks")
    if not isinstance(evidence_file_checks, list):
        failures.append("evidenceFileChecks must be an array")
        evidence_file_checks = []
    evidence_check_order: list[str] = []
    evidence_check_by_id: dict[str, dict[str, Any]] = {}
    for item in evidence_file_checks:
        if not isinstance(item, dict):
            failures.append("evidenceFileChecks entry must be an object")
            continue
        artifact_id = item.get("artifactId")
        if not isinstance(artifact_id, str) or not artifact_id:
            failures.append("evidenceFileChecks entry missing artifactId")
            continue
        if artifact_id in evidence_check_by_id:
            failures.append(f"evidenceFileChecks duplicate {artifact_id}")
        evidence_check_by_id[artifact_id] = item
        evidence_check_order.append(artifact_id)
    expected_evidence_order = tuple(APP_REVIEW_TEST_ACCOUNT_EVIDENCE_FILE_TARGETS)
    if tuple(evidence_check_order) != expected_evidence_order:
        failures.append("evidenceFileChecks order must match App Review test-account evidence workflow")
    for artifact_id, expected_target in APP_REVIEW_TEST_ACCOUNT_EVIDENCE_FILE_TARGETS.items():
        item = evidence_check_by_id.get(artifact_id)
        if not item:
            failures.append(f"evidenceFileChecks.{artifact_id} missing object")
            continue
        if item.get("target") != expected_target:
            failures.append(f"evidenceFileChecks.{artifact_id}.target must be {expected_target}")
        for field, expected in APP_REVIEW_TEST_ACCOUNT_EVIDENCE_FILE_CHECK_FIELDS:
            if item.get(field) != expected:
                failures.append(f"evidenceFileChecks.{artifact_id}.{field} must be {expected!r}")

    dependency_matrix = packet.get("evidenceDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("evidenceDependencyMatrix must be an array")
        dependency_matrix = []
    dependency_order: list[str] = []
    dependency_by_id: dict[str, dict[str, Any]] = {}
    for item in dependency_matrix:
        if not isinstance(item, dict):
            failures.append("evidenceDependencyMatrix entry must be an object")
            continue
        artifact_id = item.get("artifactId")
        if not isinstance(artifact_id, str) or not artifact_id:
            failures.append("evidenceDependencyMatrix entry missing artifactId")
            continue
        if artifact_id in dependency_by_id:
            failures.append(f"evidenceDependencyMatrix duplicate {artifact_id}")
        dependency_by_id[artifact_id] = item
        dependency_order.append(artifact_id)
        if tuple(item) != APP_REVIEW_TEST_ACCOUNT_DEPENDENCY_FIELDS:
            failures.append(
                f"evidenceDependencyMatrix.{artifact_id}.fields must be "
                + " -> ".join(APP_REVIEW_TEST_ACCOUNT_DEPENDENCY_FIELDS)
            )
    expected_dependency_order = tuple(APP_REVIEW_TEST_ACCOUNT_DEPENDENCY_MATRIX)
    if tuple(dependency_order) != expected_dependency_order:
        failures.append("evidenceDependencyMatrix order must match App Review test-account evidence workflow")
    for artifact_id, expected in APP_REVIEW_TEST_ACCOUNT_DEPENDENCY_MATRIX.items():
        item = dependency_by_id.get(artifact_id)
        if not item:
            failures.append(f"evidenceDependencyMatrix.{artifact_id} missing object")
            continue
        for field, expected_value in expected.items():
            if item.get(field) != expected_value:
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.{field} must be {expected_value}")

    if not review_account_evidence:
        failures.append("redacted account evidence missing")
    else:
        if not review_account_evidence.get("accountId"):
            failures.append("redacted account evidence accountId missing")
        for key in ("baseUrl", "recoveryKeyStored", "recoveryVerified", "syncSeeded", "containsSecret"):
            if review_account_evidence.get(key) != redacted_required.get(key):
                failures.append(f"redactedEvidenceRequired.{key} must match review account evidence")

    targets = packet.get("realDeviceEvidenceTargets")
    if not isinstance(targets, list):
        failures.append("realDeviceEvidenceTargets must be an array")
        targets = []
    targets_by_id: dict[str, dict[str, Any]] = {}
    for target in targets:
        if not isinstance(target, dict):
            failures.append("realDeviceEvidenceTargets entry must be an object")
            continue
        target_id = target.get("id")
        if not isinstance(target_id, str) or not target_id:
            failures.append("realDeviceEvidenceTargets entry missing id")
            continue
        if target_id in targets_by_id:
            failures.append(f"realDeviceEvidenceTargets duplicate {target_id}")
        targets_by_id[target_id] = target
    for target_id, markers in APP_REVIEW_TEST_ACCOUNT_RD_TARGETS.items():
        target = targets_by_id.get(target_id)
        if not target:
            failures.append(f"realDeviceEvidenceTargets missing {target_id}")
            continue
        target_text = json.dumps(target, ensure_ascii=False)
        for marker in markers:
            if marker not in target_text:
                failures.append(f"realDeviceEvidenceTargets.{target_id} missing {marker}")

    lifecycle_text = json.dumps(packet.get("accountLifecycleChecks"), ensure_ascii=False)
    if not isinstance(packet.get("accountLifecycleChecks"), list):
        failures.append("accountLifecycleChecks must be an array")
    for marker in APP_REVIEW_TEST_ACCOUNT_LIFECYCLE_MARKERS:
        if marker not in lifecycle_text:
            failures.append(f"accountLifecycleChecks missing {marker}")

    stop_conditions = packet.get("stopConditions")
    if not isinstance(stop_conditions, list):
        failures.append("stopConditions must be an array")
        stop_conditions = []
    stop_conditions_by_id: dict[str, dict[str, Any]] = {}
    for condition in stop_conditions:
        if not isinstance(condition, dict):
            failures.append("stopConditions entry must be an object")
            continue
        condition_id = condition.get("id")
        if not isinstance(condition_id, str) or not condition_id:
            failures.append("stopConditions entry missing id")
            continue
        if condition_id in stop_conditions_by_id:
            failures.append(f"stopConditions duplicate {condition_id}")
        stop_conditions_by_id[condition_id] = condition
    for condition_id, markers in APP_REVIEW_TEST_ACCOUNT_STOP_CONDITIONS.items():
        condition = stop_conditions_by_id.get(condition_id)
        if not condition:
            failures.append(f"stopConditions missing {condition_id}")
            continue
        condition_text = json.dumps(condition, ensure_ascii=False)
        for marker in markers:
            if marker not in condition_text:
                failures.append(f"stopConditions.{condition_id} missing {marker}")

    redaction_text = json.dumps(packet.get("redactionChecklist"), ensure_ascii=False)
    if not isinstance(packet.get("redactionChecklist"), list):
        failures.append("redactionChecklist must be an array")
    for marker in APP_REVIEW_TEST_ACCOUNT_REDACTION_MARKERS:
        if marker not in redaction_text:
            failures.append(f"redactionChecklist missing {marker}")

    post_fill_gates_text = json.dumps(packet.get("postFillGates"), ensure_ascii=False)
    if not isinstance(packet.get("postFillGates"), list):
        failures.append("postFillGates must be an array")
    for marker in dated_markers(APP_REVIEW_TEST_ACCOUNT_POST_FILL_GATES, path_date):
        if marker not in post_fill_gates_text:
            failures.append(f"postFillGates missing {marker}")

    completion_text = str(packet.get("completionRule", ""))
    for marker in APP_REVIEW_TEST_ACCOUNT_COMPLETION_MARKERS:
        if marker not in completion_text:
            failures.append(f"completionRule missing {marker}")

    secret_hits = forbidden_review_account_secret_hits(json.dumps(packet, ensure_ascii=False))
    if secret_hits:
        failures.append("appReviewTestAccountPacket secret hits: " + ", ".join(secret_hits))
    return failures


def in_app_companion_copy_findings(root: Path) -> dict[str, list[str]]:
    missing_files: list[str] = []
    bounded_mentions: list[str] = []
    risky_mentions: list[str] = []
    for relative_path in IN_APP_COMPANION_COPY_FILES:
        text = read_text(root / relative_path)
        if not text:
            missing_files.append(relative_path)
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not any(marker in line for marker in COMPANION_COPY_TRIGGER_MARKERS):
                continue
            finding = f"{relative_path}:{line_number}:{line.strip()}"
            if any(marker in line for marker in COMPANION_COPY_SAFE_MARKERS):
                bounded_mentions.append(finding)
            else:
                risky_mentions.append(finding)

    return {
        "missingFiles": missing_files,
        "boundedMentions": bounded_mentions,
        "riskyMentions": risky_mentions,
    }


def privacy_label_failures(privacy_label: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    privacy_app = privacy_label.get("app", {})
    if not isinstance(privacy_app, dict):
        failures.append("app must be an object")
        privacy_app = {}

    for key, expected in EXPECTED_APP_PRIVACY_FLAGS.items():
        if privacy_app.get(key) is not expected:
            failures.append(f"app.{key} must be {str(expected).lower()}")

    categories = privacy_label.get("dataCategories", [])
    if not isinstance(categories, list):
        return failures + ["dataCategories must be an array"]

    categories_by_name: dict[str, dict[str, Any]] = {}
    for item in categories:
        if not isinstance(item, dict):
            failures.append("dataCategories entry must be an object")
            continue
        category = item.get("category")
        if not isinstance(category, str) or not category:
            failures.append("dataCategories entry missing category")
            continue
        if category in categories_by_name:
            failures.append(f"{category} is duplicated")
        categories_by_name[category] = item
        if item.get("usedForTracking") is not False:
            failures.append(f"{category}.usedForTracking must be false")

    missing_categories = sorted(EXPECTED_PRIVACY_CATEGORIES - set(categories_by_name))
    if missing_categories:
        failures.append("missing categories: " + ", ".join(missing_categories))

    unexpected_collected = sorted(
        category
        for category, item in categories_by_name.items()
        if category not in EXPECTED_PRIVACY_CATEGORIES and item.get("collected") is True
    )
    if unexpected_collected:
        failures.append("unexpected collected categories: " + ", ".join(unexpected_collected))

    for category, expected in EXPECTED_PRIVACY_CATEGORY_REQUIREMENTS.items():
        item = categories_by_name.get(category)
        if not item:
            continue
        if item.get("collected") is not True:
            failures.append(f"{category}.collected must be true")
        if item.get("linkedToUser") is not expected["linkedToUser"]:
            failures.append(f"{category}.linkedToUser must be {str(expected['linkedToUser']).lower()}")
        purposes = item.get("purposes")
        if not isinstance(purposes, list):
            failures.append(f"{category}.purposes must be an array")
            continue
        missing_purposes = sorted(expected["purposes"] - {str(purpose) for purpose in purposes})
        if missing_purposes:
            failures.append(f"{category}.purposes missing: " + ", ".join(missing_purposes))

    usage_data = categories_by_name.get("Usage Data")
    usage_text = json.dumps(usage_data, ensure_ascii=False).lower() if usage_data else ""
    missing_usage_boundaries = [
        marker for marker in USAGE_DATA_BOUNDARY_MARKERS
        if marker not in usage_text
    ]
    if missing_usage_boundaries:
        failures.append("Usage Data boundary missing: " + ", ".join(missing_usage_boundaries))

    health_data = categories_by_name.get("Health and Fitness")
    health_text = json.dumps(health_data, ensure_ascii=False).lower() if health_data else ""
    missing_health_boundaries = [
        marker for marker in HEALTH_DATA_BOUNDARY_MARKERS
        if marker not in health_text
    ]
    if missing_health_boundaries:
        failures.append("Health and Fitness boundary missing: " + ", ".join(missing_health_boundaries))

    return failures


def fetch_public_url(url: str) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "XiaoNaiPingReleaseGate/1.0"})
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return {
                "ok": 200 <= int(response.status) < 300,
                "status": int(response.status),
                "contentType": response.headers.get("content-type", ""),
                "hasCompany": "深圳市闪现生活科技有限公司" in body,
                "hasProduct": EXPECTED_APP_NAME in body,
                "length": len(body),
            }
    except (urllib.error.URLError, TimeoutError) as error:
        return {"ok": False, "error": str(error)}


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
    fill_sheet_arg = args.fill_sheet or latest_fill_sheet(root)
    expected_path_date = path_date_from(fill_sheet_arg)
    expected_material_date = args.expected_material_date
    fill_sheet_path = root / fill_sheet_arg
    metadata_path = root / args.metadata
    copy_paste_packet_path = root / (
        args.copy_paste_packet or dated_doc_path(DEFAULT_COPY_PASTE_PACKET, expected_path_date)
    )
    draft_json_path = root / (
        args.draft_json or dated_doc_path(DEFAULT_APP_STORE_CONNECT_DRAFT_JSON, expected_path_date)
    )
    field_freeze_packet_path = root / (
        args.field_freeze_packet
        or dated_doc_path(DEFAULT_APP_STORE_CONNECT_FIELD_FREEZE_PACKET, expected_path_date)
    )
    entry_session_packet_path = root / (
        args.entry_session_packet
        or dated_doc_path(DEFAULT_APP_STORE_CONNECT_ENTRY_SESSION_PACKET, expected_path_date)
    )
    submit_review_preflight_packet_path = root / (
        args.submit_review_preflight_packet
        or dated_doc_path(DEFAULT_APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_PACKET, expected_path_date)
    )
    asc_backfill_result_template_path = root / args.asc_backfill_result_template
    asc_privacy_age_review_result_template_path = root / args.asc_privacy_age_review_result_template
    review_information_packet_path = root / (
        args.review_information_packet or dated_doc_path(DEFAULT_REVIEW_INFORMATION_PACKET, expected_path_date)
    )
    app_review_test_account_packet_path = root / (
        args.app_review_test_account_packet
        or dated_doc_path(DEFAULT_APP_REVIEW_TEST_ACCOUNT_PACKET, expected_path_date)
    )
    review_account_evidence_path = root / args.review_account_evidence
    privacy_answers_path = root / (
        args.privacy_answers or dated_doc_path(DEFAULT_PRIVACY_ANSWERS, expected_path_date)
    )
    age_rating_answers_path = root / (
        args.age_rating_answers or dated_doc_path(DEFAULT_AGE_RATING_ANSWERS, expected_path_date)
    )
    version_release_settings_path = root / (
        args.version_release_settings or dated_doc_path(DEFAULT_VERSION_RELEASE_SETTINGS, expected_path_date)
    )
    final_entry_audit_path = root / (
        args.final_entry_audit or dated_doc_path(DEFAULT_FINAL_ENTRY_AUDIT, expected_path_date)
    )
    privacy_label_path = root / args.privacy_label
    screenshot_plan_path = root / args.screenshot_plan
    fill_sheet = read_text(fill_sheet_path)
    metadata = read_text(metadata_path)
    copy_paste_packet = read_text(copy_paste_packet_path)
    app_store_connect_draft = read_json(draft_json_path)
    app_store_connect_field_freeze_packet = read_json(field_freeze_packet_path)
    app_store_connect_entry_session_packet = read_json(entry_session_packet_path)
    app_store_connect_submit_review_preflight_packet = read_json(submit_review_preflight_packet_path)
    asc_backfill_result_template = read_json(asc_backfill_result_template_path)
    asc_privacy_age_review_result_template = read_json(asc_privacy_age_review_result_template_path)
    review_information_packet = read_text(review_information_packet_path)
    app_review_test_account_packet = read_json(app_review_test_account_packet_path)
    review_account_evidence = read_json(review_account_evidence_path)
    privacy_answers = read_text(privacy_answers_path)
    age_rating_answers = read_text(age_rating_answers_path)
    version_release_settings = read_text(version_release_settings_path)
    final_entry_audit = read_text(final_entry_audit_path)
    privacy_label = read_json(privacy_label_path)
    screenshot_plan = read_text(screenshot_plan_path)
    report = Report()

    report.add(
        "appStoreConnectMaterialDateCurrent",
        expected_path_date == expected_material_date,
        f"selected material date {expected_path_date}; expected {expected_material_date}; fillSheet={fill_sheet_arg}",
    )
    report.add("fillSheetPresent", bool(fill_sheet), str(fill_sheet_path) if fill_sheet else "missing fill sheet")
    report.add("metadataPresent", bool(metadata), str(metadata_path) if metadata else "missing metadata doc")
    report.add("copyPastePacketPresent", bool(copy_paste_packet), str(copy_paste_packet_path) if copy_paste_packet else "missing copy-paste packet")
    report.add("appStoreConnectDraftJsonPresent", bool(app_store_connect_draft), str(draft_json_path) if app_store_connect_draft else "missing App Store Connect draft JSON")
    report.add(
        "appStoreConnectFieldFreezePacketPresent",
        bool(app_store_connect_field_freeze_packet),
        str(field_freeze_packet_path)
        if app_store_connect_field_freeze_packet
        else "missing App Store Connect field freeze packet JSON",
    )
    report.add(
        "appStoreConnectEntrySessionPacketPresent",
        bool(app_store_connect_entry_session_packet),
        str(entry_session_packet_path)
        if app_store_connect_entry_session_packet
        else "missing App Store Connect entry session packet JSON",
    )
    report.add(
        "appStoreConnectSubmitReviewPreflightPresent",
        bool(app_store_connect_submit_review_preflight_packet),
        str(submit_review_preflight_packet_path)
        if app_store_connect_submit_review_preflight_packet
        else "missing App Store Connect Submit for Review preflight packet JSON",
    )
    report.add(
        "ascBackfillResultTemplatePresent",
        bool(asc_backfill_result_template),
        str(asc_backfill_result_template_path)
        if asc_backfill_result_template
        else "missing ASC backfill result template JSON",
    )
    report.add(
        "ascPrivacyAgeReviewResultTemplatePresent",
        bool(asc_privacy_age_review_result_template),
        str(asc_privacy_age_review_result_template_path)
        if asc_privacy_age_review_result_template
        else "missing ASC privacy/age/review result template JSON",
    )
    report.add("reviewInformationPacketPresent", bool(review_information_packet), str(review_information_packet_path) if review_information_packet else "missing review information packet")
    report.add(
        "appReviewTestAccountPacketPresent",
        bool(app_review_test_account_packet),
        str(app_review_test_account_packet_path)
        if app_review_test_account_packet
        else "missing app review test account packet JSON",
    )
    report.add("privacyAnswersPresent", bool(privacy_answers), str(privacy_answers_path) if privacy_answers else "missing privacy answers packet")
    report.add("ageRatingAnswersPresent", bool(age_rating_answers), str(age_rating_answers_path) if age_rating_answers else "missing age rating answer sheet")
    report.add("versionReleaseSettingsPresent", bool(version_release_settings), str(version_release_settings_path) if version_release_settings else "missing version release settings")
    report.add("finalEntryAuditPresent", bool(final_entry_audit), str(final_entry_audit_path) if final_entry_audit else "missing final App Store Connect entry audit")
    report.add("privacyLabelPresent", bool(privacy_label), str(privacy_label_path) if privacy_label else "missing privacy label JSON")
    report.add("screenshotPlanPresent", bool(screenshot_plan), str(screenshot_plan_path) if screenshot_plan else "missing screenshot plan")
    copy_paste_markers = dated_markers(COPY_PASTE_PACKET_MARKERS, expected_path_date)
    missing_copy_paste_markers = [marker for marker in copy_paste_markers if marker not in copy_paste_packet]
    copy_paste_secret_hits = forbidden_review_account_secret_hits(copy_paste_packet)
    report.add(
        "copyPastePacketCompleteAndRedacted",
        bool(copy_paste_packet) and not missing_copy_paste_markers and not copy_paste_secret_hits,
        "missing: "
        + ", ".join(missing_copy_paste_markers)
        + "; secretHits: "
        + ", ".join(copy_paste_secret_hits)
        if missing_copy_paste_markers or copy_paste_secret_hits
        else "copy-paste packet covers App Store Connect fields, review notes, D-U-N-S handoff, and iOS 26.5 final evidence boundaries without secrets",
    )
    copy_paste_sync = copy_paste_sync_failures(fill_sheet, copy_paste_packet)
    report.add(
        "copyPastePacketMatchesFillSheetDraft",
        bool(fill_sheet) and bool(copy_paste_packet) and not copy_paste_sync,
        "; ".join(copy_paste_sync)
        if copy_paste_sync
        else "copy-paste packet text matches fill sheet for keywords, promotional text, description, release notes, and review notes",
    )
    app_info_copy_sync = app_information_copy_sync_failures(fill_sheet, copy_paste_packet)
    report.add(
        "copyPasteAppInformationMatchesFillSheet",
        bool(fill_sheet) and bool(copy_paste_packet) and not app_info_copy_sync,
        "; ".join(app_info_copy_sync)
        if app_info_copy_sync
        else "copy-paste App 信息 block matches fill sheet for name, bundle, SKU, subtitle, categories, regions, copyright, and public URLs",
    )
    review_information_markers = dated_markers(REVIEW_INFORMATION_PACKET_MARKERS, expected_path_date)
    missing_review_information_markers = [
        marker for marker in review_information_markers if marker not in review_information_packet
    ]
    review_information_secret_hits = forbidden_review_account_secret_hits(review_information_packet)
    report.add(
        "reviewInformationPacketCompleteAndRedacted",
        bool(review_information_packet) and not missing_review_information_markers and not review_information_secret_hits,
        "missing: "
        + ", ".join(missing_review_information_markers)
        + "; secretHits: "
        + ", ".join(review_information_secret_hits)
        if missing_review_information_markers or review_information_secret_hits
        else "App Review Information private-field packet covers contact info, sign-in, notes, evidence, and redaction boundaries without secrets",
    )
    missing_review_account_evidence_lock = [
        marker for marker in REVIEW_ACCOUNT_EVIDENCE_LOCK_MARKERS if marker not in review_information_packet
    ]
    review_account_evidence_problems = review_account_evidence_failures(review_account_evidence)
    report.add(
        "reviewAccountRedactedEvidenceMatchesReviewInfo",
        bool(review_information_packet)
        and not missing_review_account_evidence_lock
        and not review_account_evidence_problems,
        "missing: "
        + ", ".join(missing_review_account_evidence_lock)
        + "; evidenceProblems: "
        + ", ".join(review_account_evidence_problems)
        if missing_review_account_evidence_lock or review_account_evidence_problems
        else "App Review Information sign-in fields are backed by redacted account evidence without storing recovery keys, phone numbers, tokens, or debug credentials",
    )
    review_information_submission_blockers = dated_markers(
        REVIEW_INFORMATION_SUBMISSION_BLOCKER_MARKERS,
        expected_path_date,
    )
    missing_review_information_submission_blockers = [
        marker for marker in review_information_submission_blockers
        if marker not in review_information_packet
    ]
    report.add(
        "reviewInformationSubmissionBlockersPresent",
        bool(review_information_packet) and not missing_review_information_submission_blockers,
        "missing: " + ", ".join(missing_review_information_submission_blockers)
        if missing_review_information_submission_blockers
        else "review information packet keeps D-U-N-S, Apple Developer, Archive/TestFlight, external provider, filing, age rating, final screenshot, real-device evidence, and proof-gate blockers separate from test-account notes",
    )
    app_review_test_account_reference_markers = dated_markers(
        APP_REVIEW_TEST_ACCOUNT_PACKET_REFERENCE_MARKERS,
        expected_path_date,
    )
    missing_app_review_test_account_reference_markers = [
        marker for marker in app_review_test_account_reference_markers
        if marker not in review_information_packet
    ]
    report.add(
        "appReviewTestAccountPacketReferenced",
        bool(review_information_packet) and not missing_app_review_test_account_reference_markers,
        "missing: " + ", ".join(missing_app_review_test_account_reference_markers)
        if missing_app_review_test_account_reference_markers
        else "review information packet links the structured review-test-account packet and keeps its no-secret, no-submit boundary explicit",
    )
    app_review_test_account_packet_problems = app_review_test_account_packet_failures(
        app_review_test_account_packet,
        expected_path_date,
        review_account_evidence,
    )
    report.add(
        "appReviewTestAccountPacketValid",
        bool(app_review_test_account_packet) and not app_review_test_account_packet_problems,
        "; ".join(app_review_test_account_packet_problems)
        if app_review_test_account_packet_problems
        else "App Review test-account packet locks private recovery-key handling, redacted evidence, RD-10/RD-13/RD-14/RD-15 capture targets, stop conditions, redaction checklist, post-fill gates, and no-submit boundary",
    )
    privacy_answer_markers = dated_markers(PRIVACY_ANSWERS_MARKERS, expected_path_date)
    missing_privacy_answer_markers = [marker for marker in privacy_answer_markers if marker not in privacy_answers]
    privacy_answer_secret_hits = forbidden_review_account_secret_hits(privacy_answers)
    report.add(
        "privacyAnswersCompleteAndRedacted",
        bool(privacy_answers) and not missing_privacy_answer_markers and not privacy_answer_secret_hits,
        "missing: "
        + ", ".join(missing_privacy_answer_markers)
        + "; secretHits: "
        + ", ".join(privacy_answer_secret_hits)
        if missing_privacy_answer_markers or privacy_answer_secret_hits
        else "App Privacy answer sheet maps privacy label JSON into App Store Connect tracking/linking/purpose answers without secrets",
    )
    age_rating_answer_markers = dated_markers(AGE_RATING_ANSWERS_MARKERS, expected_path_date)
    missing_age_rating_answer_markers = [
        marker for marker in age_rating_answer_markers if marker not in age_rating_answers
    ]
    age_rating_answer_secret_hits = forbidden_review_account_secret_hits(age_rating_answers)
    report.add(
        "ageRatingAnswersCompleteAndRedacted",
        bool(age_rating_answers) and not missing_age_rating_answer_markers and not age_rating_answer_secret_hits,
        "missing: "
        + ", ".join(missing_age_rating_answer_markers)
        + "; secretHits: "
        + ", ".join(age_rating_answer_secret_hits)
        if missing_age_rating_answer_markers or age_rating_answer_secret_hits
        else "age rating answer sheet covers Kids, web access, public UGC, chat, purchases, ads/tracking, gambling, mature content, health records, and regulated medical-device answers without secrets",
    )
    age_rating_reference_text = fill_sheet + "\n" + metadata + "\n" + copy_paste_packet
    age_rating_reference_markers = dated_markers(AGE_RATING_REFERENCE_MARKERS, expected_path_date)
    missing_age_rating_references = [
        marker for marker in age_rating_reference_markers if marker not in age_rating_reference_text
    ]
    report.add(
        "ageRatingAnswerSheetReferencedByDraft",
        bool(age_rating_reference_text) and not missing_age_rating_references,
        "missing: " + ", ".join(missing_age_rating_references)
        if missing_age_rating_references
        else "App Store Connect draft, copy-paste packet, or metadata references the dedicated age rating / medical device answer sheet",
    )
    version_release_markers = dated_markers(VERSION_RELEASE_SETTINGS_MARKERS, expected_path_date)
    missing_version_release_markers = [
        marker for marker in version_release_markers if marker not in version_release_settings
    ]
    version_release_secret_hits = forbidden_review_account_secret_hits(version_release_settings)
    report.add(
        "versionReleaseSettingsCompleteAndRedacted",
        bool(version_release_settings) and not missing_version_release_markers and not version_release_secret_hits,
        "missing: "
        + ", ".join(missing_version_release_markers)
        + "; secretHits: "
        + ", ".join(version_release_secret_hits)
        if missing_version_release_markers or version_release_secret_hits
        else "App Store version/release settings cover build selection, pricing/availability, manual release, export compliance, IDFA/tracking, content rights, and evidence boundaries without secrets",
    )
    release_notes_for_version_settings = extract_first_code_block(extract_section(fill_sheet, "新版本说明"))
    report.add(
        "versionReleaseSettingsMatchesFillSheetWhatsNew",
        bool(version_release_settings)
        and bool(release_notes_for_version_settings)
        and release_notes_for_version_settings in version_release_settings,
        "What's New differs from fill sheet 新版本说明"
        if version_release_settings and release_notes_for_version_settings not in version_release_settings
        else "version release settings What's New matches fill sheet 新版本说明",
    )
    final_entry_markers = dated_markers(FINAL_ENTRY_AUDIT_MARKERS, expected_path_date)
    missing_final_entry_markers = [marker for marker in final_entry_markers if marker not in final_entry_audit]
    final_entry_secret_hits = forbidden_review_account_secret_hits(final_entry_audit)
    report.add(
        "finalEntryAuditCompleteAndRedacted",
        bool(final_entry_audit) and not missing_final_entry_markers and not final_entry_secret_hits,
        "missing: "
        + ", ".join(missing_final_entry_markers)
        + "; secretHits: "
        + ", ".join(final_entry_secret_hits)
        if missing_final_entry_markers or final_entry_secret_hits
        else "final App Store Connect entry audit maps paste fields, same-round build/version, evidence files, rerun gates, and redaction boundaries without secrets",
    )
    missing_page_evidence_markers = [
        marker for marker in FINAL_ENTRY_PAGE_EVIDENCE_MARKERS if marker not in final_entry_audit
    ]
    report.add(
        "finalEntryPageEvidenceIndexPresent",
        bool(final_entry_audit) and not missing_page_evidence_markers,
        "missing: " + ", ".join(missing_page_evidence_markers)
        if missing_page_evidence_markers
        else "final App Store Connect audit lists post-fill page evidence filenames, keep/redact fields, cross-check sources, and rerun gates without treating page screenshots as external proof substitutes",
    )
    final_submit_guard_markers = dated_markers(FINAL_SUBMIT_GUARD_MARKERS, expected_path_date)
    missing_final_submit_guard_markers = [
        marker for marker in final_submit_guard_markers if marker not in final_entry_audit
    ]
    report.add(
        "finalSubmitReviewGuardRequiresXiaoNaiPingProofs",
        bool(final_entry_audit) and not missing_final_submit_guard_markers,
        "missing: " + ", ".join(missing_final_submit_guard_markers)
        if missing_final_submit_guard_markers
        else "final App Store Connect audit requires XiaoNaiPing App Store, production, launch, TestFlight, provider, filing, and signing proofs before Submit for Review",
    )
    field_source_lock_markers = dated_markers(FINAL_FIELD_SOURCE_LOCK_MARKERS, expected_path_date)
    missing_field_source_lock_markers = [
        marker for marker in field_source_lock_markers if marker not in final_entry_audit
    ]
    report.add(
        "finalFieldSourceConsistencyLockPresent",
        bool(final_entry_audit) and not missing_field_source_lock_markers,
        "missing: " + ", ".join(missing_field_source_lock_markers)
        if missing_field_source_lock_markers
        else "final App Store Connect audit locks draft fields to source files and treats ASC screenshots only as page-fill evidence",
    )
    entry_session_reference_markers = dated_markers(
        ENTRY_SESSION_PACKET_REFERENCE_MARKERS,
        expected_path_date,
    )
    missing_entry_session_reference_markers = [
        marker for marker in entry_session_reference_markers if marker not in final_entry_audit
    ]
    report.add(
        "appStoreConnectEntrySessionPacketReferenced",
        bool(final_entry_audit) and not missing_entry_session_reference_markers,
        "missing: " + ", ".join(missing_entry_session_reference_markers)
        if missing_entry_session_reference_markers
        else "final App Store Connect audit links the entry-session packet and keeps its plan-not-evidence, no-submit boundary explicit",
    )
    metadata_current_markers = dated_markers(METADATA_CURRENT_MARKERS, expected_path_date)
    missing_metadata_current_markers = [marker for marker in metadata_current_markers if marker not in metadata]
    report.add(
        "metadataCurrentLaunchHandoffPresent",
        bool(metadata) and not missing_metadata_current_markers,
        "missing: " + ", ".join(missing_metadata_current_markers)
        if missing_metadata_current_markers
        else "metadata draft is current and points to fill sheet, D-U-N-S, external evidence, and launch proof gates",
    )
    missing_metadata_description_deferral_markers = [
        marker for marker in METADATA_DESCRIPTION_DEFERRAL_MARKERS if marker not in metadata
    ]
    report.add(
        "metadataDraftDescriptionCoversCurrentReminderBehavior",
        bool(metadata) and not missing_metadata_description_deferral_markers,
        "missing: " + ", ".join(missing_metadata_description_deferral_markers)
        if missing_metadata_description_deferral_markers
        else "metadata descriptions in Simplified Chinese, Traditional Chinese, and English cover 5-minute manual feeding reminder deferral without automatic volume, age, sensor, or health-data inference",
    )
    stale_blocking_proofs = [
        "Backend/proof/production-readiness-20260627T-current.json",
        "Backend/proof/auth-providers-20260627T-current.json",
        "Backend/proof/ios-app-bundle-20260627T-current-ios265.json",
        "Backend/proof/app-store-evidence-20260627T-current.json",
    ]
    stale_proof_refs = sorted(proof for proof in stale_blocking_proofs if proof in fill_sheet)
    required_latest_proofs = [
        "Backend/proof/production-readiness.json",
        "Backend/proof/auth-providers.json",
        "Backend/proof/ios-release-readiness.json",
        "Backend/proof/ios-app-bundle.json",
        "Backend/proof/app-store-evidence.json",
    ]
    missing_latest_proofs = [proof for proof in required_latest_proofs if proof not in fill_sheet]
    report.add(
        "blockingProofReferencesUseLatestSnapshots",
        not stale_proof_refs and not missing_latest_proofs,
        "staleRefs="
        + ", ".join(stale_proof_refs)
        + "; missingLatest="
        + ", ".join(missing_latest_proofs)
        if stale_proof_refs or missing_latest_proofs
        else "blocking proof references use stable latest aliases",
    )
    combined_materials = (
        fill_sheet
        + "\n"
        + metadata
        + "\n"
        + copy_paste_packet
        + "\n"
        + review_information_packet
        + "\n"
        + privacy_answers
        + "\n"
        + version_release_settings
    )
    missing_external_auth_boundaries = [
        marker for marker in EXTERNAL_AUTH_BOUNDARY_MARKERS if marker not in combined_materials
    ]
    report.add(
        "externalAuthSubmissionBoundaryPresent",
        not missing_external_auth_boundaries,
        "missing: " + ", ".join(missing_external_auth_boundaries)
        if missing_external_auth_boundaries
        else "materials clearly separate draft login copy from pending SMS/WeChat provider and iOS bundle evidence",
    )
    missing_deferred_auth_markers = [
        marker for marker in DEFERRED_AUTH_PUBLIC_COPY_MARKERS if marker not in combined_materials
    ]
    premature_auth_claims = sorted(
        marker for marker in PREMATURE_AUTH_PUBLIC_CLAIM_MARKERS if marker in combined_materials
    )
    report.add(
        "deferredSmsWechatPublicCopyBounded",
        not missing_deferred_auth_markers and not premature_auth_claims,
        "missing: "
        + ", ".join(missing_deferred_auth_markers)
        + "; prematureClaims="
        + ", ".join(premature_auth_claims)
        if missing_deferred_auth_markers or premature_auth_claims
        else "public App Store draft copy uses recovery-key as the current review path and defers phone/WeChat login until real provider, live-send, and real-device evidence are complete",
    )

    report.add("appNameMatches", f"| App 名称 | {EXPECTED_APP_NAME} |" in fill_sheet, EXPECTED_APP_NAME)
    report.add("bundleIdentifierMatches", EXPECTED_BUNDLE_ID in fill_sheet and EXPECTED_BUNDLE_ID in metadata, EXPECTED_BUNDLE_ID)
    report.add("subtitleWithinLimit", EXPECTED_SUBTITLE in fill_sheet and len(EXPECTED_SUBTITLE) <= 30, EXPECTED_SUBTITLE)
    report.add("skuPresent", "`xiaonaiping-ios-1`" in fill_sheet, "SKU xiaonaiping-ios-1")
    report.add("primaryCategoryLifestyle", "| 主类别 | 生活 |" in fill_sheet or "| Category | Lifestyle |" in metadata, "primary category Lifestyle/生活")
    report.add("secondaryCategoryBlank", "| 第二类别 | 留空" in fill_sheet, "second category is blank in fill sheet")

    category_hits = sorted(marker for marker in DISALLOWED_CATEGORY_ALTERNATIVES if marker in fill_sheet or marker in metadata)
    report.add(
        "metadataNoHealthFitnessCategoryAlternative",
        not category_hits,
        "found: " + ", ".join(category_hits) if category_hits else "metadata does not suggest Health & Fitness as an alternate category",
    )

    report.add("firstReleaseMainland", "China mainland" in fill_sheet and "Specific Countries or Regions" in fill_sheet, "China mainland first")
    report.add("secondReleaseHongKong", "Hong Kong" in fill_sheet, "Hong Kong second")
    report.add("priceFree", "| 价格 | 免费 |" in fill_sheet or "| Price | Free |" in metadata, "free V1")
    report.add("copyrightCompany", "深圳市闪现生活科技有限公司" in fill_sheet, "company copyright present")

    public_urls_ok = all(url in fill_sheet and url in metadata for url in [EXPECTED_PRIVACY_URL, EXPECTED_SUPPORT_URL, EXPECTED_TERMS_URL])
    label_urls_ok = privacy_label.get("privacyPolicyUrl") == EXPECTED_PRIVACY_URL and privacy_label.get("supportUrl") == EXPECTED_SUPPORT_URL
    report.add(
        "publicUrlsMatch",
        public_urls_ok and label_urls_ok,
        "privacy/support/terms URLs match fill sheet, metadata, and privacy label"
        if public_urls_ok and label_urls_ok
        else "URL mismatch in fill sheet, metadata, or privacy label",
    )

    expected_public_urls = [EXPECTED_PRIVACY_URL, EXPECTED_SUPPORT_URL, EXPECTED_TERMS_URL]
    public_url_results = {url: fetch_public_url(url) for url in expected_public_urls}
    public_url_failures = [
        f"{url}: {result}"
        for url, result in public_url_results.items()
        if not (result.get("ok") and result.get("hasCompany") and result.get("hasProduct"))
    ]
    report.add(
        "publicUrlsReachable",
        not public_url_failures,
        "privacy/support/terms URLs return 2xx and contain company/product markers"
        if not public_url_failures
        else "; ".join(public_url_failures),
    )

    keywords = extract_first_code_block(extract_section(fill_sheet, "关键词"))
    keyword_set = {item.strip() for item in keywords.split(",") if item.strip()}
    missing_keywords = sorted(EXPECTED_KEYWORDS - keyword_set)
    keyword_bytes = utf8_bytes(keywords)
    report.add(
        "keywordsCompleteAndWithinLimit",
        bool(keywords) and not missing_keywords and keyword_bytes <= KEYWORDS_MAX_BYTES,
        f"chars={len(keywords)}, bytes={keyword_bytes}, missing={missing_keywords}",
    )

    promo = extract_first_code_block(extract_section(fill_sheet, "宣传文本"))
    report.add(
        "promotionalTextWithinLimit",
        bool(promo) and len(promo) <= PROMOTIONAL_TEXT_MAX_CHARS,
        f"len={len(promo)}",
    )

    release_notes = extract_first_code_block(extract_section(fill_sheet, "新版本说明"))
    release_notes_markers = ["第一版", "宝宝档案", "日常记录", "喝奶提醒与手动顺延", "成长记录", "疫苗提醒", "照片时间线", "账号同步恢复", "云端账号删除"]
    missing_release_notes_markers = [marker for marker in release_notes_markers if marker not in release_notes]
    report.add(
        "releaseNotesCompleteAndWithinLimit",
        bool(release_notes) and len(release_notes) <= LONG_TEXT_MAX_CHARS and not missing_release_notes_markers,
        f"len={len(release_notes)}, missing={missing_release_notes_markers}",
    )

    description = extract_first_code_block(extract_section(fill_sheet, "描述"))
    description_markers = [
        "本地优先",
        "恢复密钥",
        "照片原图",
        "5 分钟一档",
        "手动顺延",
        "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
        "不构成喂养建议",
        "不提供医疗诊断",
        "疫苗模板仅用于记录和提醒",
    ]
    missing_description_markers = [marker for marker in description_markers if marker not in description]
    internal_description_markers = [
        marker for marker in PUBLIC_DESCRIPTION_FORBIDDEN_INTERNAL_MARKERS if marker in description
    ]
    report.add(
        "descriptionCompleteAndWithinLimit",
        (
            bool(description)
            and len(description) <= LONG_TEXT_MAX_CHARS
            and not missing_description_markers
            and not internal_description_markers
        ),
        (
            f"len={len(description)}, missing={missing_description_markers}, "
            f"internalMarkers={internal_description_markers}"
        ),
    )

    age_section = extract_section(fill_sheet, "年龄分级建议")
    age_markers = ["4+", "不选择 Kids 类目", "不面向儿童直接使用", "不接入 HealthKit", "不提供压力评估"]
    missing_age_markers = [marker for marker in age_markers if marker not in age_section]
    report.add(
        "ageRatingBoundaryPresent",
        not missing_age_markers,
        "missing: " + ", ".join(missing_age_markers) if missing_age_markers else "4+ / not Kids / non-medical boundaries present",
    )

    privacy_app = privacy_label.get("app", {}) if isinstance(privacy_label.get("app", {}), dict) else {}
    privacy_failures = privacy_label_failures(privacy_label)
    report.add(
        "privacyLabelMatchesAppStoreDraft",
        privacy_app.get("name") == EXPECTED_APP_NAME
        and privacy_app.get("bundleId") == EXPECTED_BUNDLE_ID
        and not privacy_failures,
        "; ".join(privacy_failures) if privacy_failures else "privacy label categories, purposes, linking, tracking, and app flags match draft",
    )

    screenshot_section = extract_section(fill_sheet, "截图文案")
    screenshot_rows = screenshot_copy_rows(screenshot_section)
    missing_screenshots = [
        f"{filename} / {title}"
        for filename, title in EXPECTED_SCREENSHOTS.items()
        if filename not in fill_sheet or title not in fill_sheet
    ]
    report.add(
        "screenshotCopyComplete",
        not missing_screenshots,
        "missing: " + "; ".join(missing_screenshots) if missing_screenshots else "5 screenshot filenames and titles present",
    )
    screenshot_copy_forbidden_hits = [
        marker for marker in SCREENSHOT_COPY_FORBIDDEN_MARKERS if marker in screenshot_rows
    ]
    missing_screenshot_boundary_markers = [
        marker for marker in SCREENSHOT_BOUNDARY_MARKERS if marker not in screenshot_section
    ]
    report.add(
        "screenshotCopyAvoidsUnavailableOrMedicalClaims",
        bool(screenshot_rows) and not screenshot_copy_forbidden_hits and not missing_screenshot_boundary_markers,
        "forbiddenInRows="
        + ", ".join(screenshot_copy_forbidden_hits)
        + "; missingBoundary="
        + ", ".join(missing_screenshot_boundary_markers)
        if screenshot_copy_forbidden_hits or missing_screenshot_boundary_markers
        else "screenshot table avoids unavailable WeChat success claims and medical/health advice claims; screenshot boundaries are present",
    )

    missing_screenshot_plan_markers = [
        marker for marker in EXPECTED_SCREENSHOT_PLAN_MARKERS if marker not in screenshot_plan
    ]
    disallowed_screenshot_runtime_markers = sorted(
        set(
            re.findall(r"OS=(?!26\.5\b)[0-9][0-9.]*", screenshot_plan)
            + re.findall(r"-sdk iphone(?:simulator|os)(?!26\.5\b)[0-9.]*", screenshot_plan)
            + re.findall(r"Runtime:\s+iOS\s+(?!26\.5\b)[0-9][0-9.]*", screenshot_plan)
        )
    )
    report.add(
        "screenshotPlanUsesIOS265Only",
        bool(screenshot_plan)
        and not missing_screenshot_plan_markers
        and not disallowed_screenshot_runtime_markers,
        "missing: "
        + ", ".join(missing_screenshot_plan_markers)
        + "; disallowedRuntimeMarkers: "
        + ", ".join(disallowed_screenshot_runtime_markers)
        if missing_screenshot_plan_markers or disallowed_screenshot_runtime_markers
        else "screenshot capture plan uses iOS 26.5 simulator commands and keeps final TestFlight/signed-build screenshots separate",
    )
    screenshot_upload_matrix_text = fill_sheet + "\n" + final_entry_audit + "\n" + screenshot_plan
    missing_screenshot_upload_matrix = [
        marker for marker in SCREENSHOT_UPLOAD_MATRIX_MARKERS if marker not in screenshot_upload_matrix_text
    ]
    report.add(
        "appStoreScreenshotUploadMatrixPresent",
        bool(fill_sheet) and bool(final_entry_audit) and bool(screenshot_plan) and not missing_screenshot_upload_matrix,
        "missing: " + ", ".join(missing_screenshot_upload_matrix)
        if missing_screenshot_upload_matrix
        else "App Store Connect screenshot upload matrix ties Apple screenshot specs, current iPhone 6.9 candidates, final iOS 26.5 TestFlight/signed screenshots, and ASC page evidence together",
    )

    companion_copy = in_app_companion_copy_findings(root)
    report.add(
        "inAppCompanionCopyBounded",
        not companion_copy["missingFiles"]
        and not companion_copy["riskyMentions"]
        and bool(companion_copy["boundedMentions"]),
        "missingFiles="
        + ", ".join(companion_copy["missingFiles"])
        + "; riskyMentions="
        + " | ".join(companion_copy["riskyMentions"])
        + "; boundedMentions="
        + " | ".join(companion_copy["boundedMentions"])
        if companion_copy["missingFiles"] or companion_copy["riskyMentions"]
        else "Apple Watch mentions in app UI are bounded to system notification mirroring, not Watch App or watchOS support",
    )

    review_text = extract_first_code_block(extract_section(fill_sheet, "审核备注可粘贴文本"))
    report.add(
        "reviewNotesPasteTextWithinLimit",
        bool(review_text) and len(review_text) <= LONG_TEXT_MAX_CHARS,
        f"len={len(review_text)}",
    )
    draft_json_problems = app_store_connect_draft_json_failures(
        app_store_connect_draft,
        expected_path_date,
        keywords=keywords,
        promo=promo,
        description=description,
        release_notes=release_notes,
        review_text=review_text,
    )
    report.add(
        "appStoreConnectDraftJsonMatchesFillSheet",
        not draft_json_problems,
        "; ".join(draft_json_problems)
        if draft_json_problems
        else "structured App Store Connect draft JSON matches fill sheet fields, age rating, privacy, review notes, and non-submission boundary",
    )
    page_evidence_map_problems = app_store_connect_page_evidence_map_failures(
        app_store_connect_draft,
        expected_path_date,
    )
    report.add(
        "appStoreConnectDraftPageEvidenceMapComplete",
        bool(app_store_connect_draft) and not page_evidence_map_problems,
        "; ".join(page_evidence_map_problems)
        if page_evidence_map_problems
        else "structured App Store Connect draft JSON maps ASC-01 through ASC-08 page-fill screenshots to required captures, redactions, cross-check sources, and non-substitution boundaries",
    )
    field_audit_matrix_problems = app_store_connect_field_audit_matrix_failures(
        app_store_connect_draft,
        expected_path_date,
    )
    report.add(
        "appStoreConnectDraftFieldAuditMatrixComplete",
        bool(app_store_connect_draft) and not field_audit_matrix_problems,
        "; ".join(field_audit_matrix_problems)
        if field_audit_matrix_problems
        else "structured App Store Connect draft JSON locks app name, subtitle, description, keywords, category, age rating, privacy/support/terms URLs, and review notes to source files, ASC page evidence, blockers, and redaction boundaries",
    )
    field_freeze_packet_problems = app_store_connect_field_freeze_packet_failures(
        app_store_connect_field_freeze_packet,
        app_store_connect_draft,
        expected_path_date,
        keywords=keywords,
        promo=promo,
        description=description,
        release_notes=release_notes,
        review_text=review_text,
    )
    report.add(
        "appStoreConnectFieldFreezePacketValid",
        bool(app_store_connect_field_freeze_packet) and not field_freeze_packet_problems,
        "; ".join(field_freeze_packet_problems)
        if field_freeze_packet_problems
        else "App Store Connect field freeze packet locks every draft field requested for live entry to source files, ASC page evidence, redaction rules, and no-submit boundaries",
    )
    entry_session_packet_problems = app_store_connect_entry_session_packet_failures(
        app_store_connect_entry_session_packet,
        expected_path_date,
    )
    report.add(
        "appStoreConnectEntrySessionPacketValid",
        bool(app_store_connect_entry_session_packet) and not entry_session_packet_problems,
        "; ".join(entry_session_packet_problems)
        if entry_session_packet_problems
        else "App Store Connect entry-session packet locks fill sequence, source files, ASC page evidence targets, stop conditions, redaction checklist, post-entry gates, and no-submit boundary",
    )
    submit_review_preflight_packet_problems = app_store_connect_submit_review_preflight_failures(
        app_store_connect_submit_review_preflight_packet,
        expected_path_date,
    )
    report.add(
        "appStoreConnectSubmitReviewPreflightValid",
        bool(app_store_connect_submit_review_preflight_packet) and not submit_review_preflight_packet_problems,
        "; ".join(submit_review_preflight_packet_problems)
        if submit_review_preflight_packet_problems
        else "App Store Connect Submit for Review preflight packet locks ASC-08 evidence, green proof requirements, remaining blockers, redaction checklist, post-preflight gates, and no-submit boundary",
    )
    asc_backfill_result_template_problems = app_store_connect_backfill_result_template_failures(
        asc_backfill_result_template,
        expected_path_date,
    )
    report.add(
        "ascBackfillResultTemplateValid",
        bool(asc_backfill_result_template) and not asc_backfill_result_template_problems,
        "; ".join(asc_backfill_result_template_problems)
        if asc_backfill_result_template_problems
        else "ASC backfill result template keeps live result status pending, XiaoNaiPing proof sources, ASC-01..ASC-08 screenshot files, redaction, and no-submit boundary locked",
    )
    asc_privacy_age_review_template_problems = app_store_connect_privacy_age_review_template_failures(
        asc_privacy_age_review_result_template,
        expected_path_date,
    )
    report.add(
        "ascPrivacyAgeReviewResultTemplateValid",
        bool(asc_privacy_age_review_result_template) and not asc_privacy_age_review_template_problems,
        "; ".join(asc_privacy_age_review_template_problems)
        if asc_privacy_age_review_template_problems
        else "ASC privacy/age/review result template locks ASC-04/05/06, privacy label, age rating result, review account redaction, answer-sheet matching, post-result gates, redaction, and no-submit boundary",
    )
    field_budget_rows = expected_field_budget_rows(
        keywords=keywords,
        promo=promo,
        description=description,
        release_notes=release_notes,
        review_text=review_text,
    )
    field_budget_documents = [
        (FIELD_BUDGET_DOC_LABELS[0][0], fill_sheet),
        (FIELD_BUDGET_DOC_LABELS[1][0], copy_paste_packet),
        (FIELD_BUDGET_DOC_LABELS[2][0], final_entry_audit),
    ]
    field_budget_problems = field_budget_failures(field_budget_documents, field_budget_rows)
    report.add(
        "appStoreConnectFieldBudgetTablesCurrent",
        not field_budget_problems,
        "field budget tables match current draft lengths"
        if not field_budget_problems
        else "; ".join(field_budget_problems),
    )
    review_markers = [
        "Live Activity",
        "小组件",
        "状态展示",
        "手动顺延下一次提醒",
        "5 分钟一档",
        "+5、+10、+15、+20、+25、+30 分钟",
        "本顿结束时间 + 固定间隔 + 顺延分钟",
        "本顿无喂养时长时按本顿发生时间",
        "不新增持久化字段",
        "不根据奶量、月龄",
        "用户在 App 内输入",
        "不生成健康建议、压力提醒、喂养建议",
        "不接入 HealthKit",
        "不提供压力评估",
        "不是医疗器械",
        "debug code",
    ]
    missing_review_markers = [marker for marker in review_markers if marker not in review_text]
    review_internal_markers = [
        marker for marker in REVIEW_NOTES_FORBIDDEN_INTERNAL_MARKERS if marker in review_text
    ]
    report.add(
        "reviewNotesPasteTextHasBoundary",
        not missing_review_markers and not review_internal_markers,
        "missing: "
        + ", ".join(missing_review_markers)
        + "; internalMarkers="
        + ", ".join(review_internal_markers)
        if missing_review_markers or review_internal_markers
        else "review paste text has Live Activity/widget/source/health boundaries and avoids internal auth placeholder wording",
    )

    vaccine_boundary_markers = [
        "疫苗模板仅用于记录和提醒",
        "实际接种安排请以医生和当地官方信息为准",
        "不构成医疗建议",
        "不作为医疗建议",
        "不替代医生建议",
    ]
    vaccine_boundary_text = fill_sheet + "\n" + metadata + "\n" + screenshot_plan
    missing_vaccine_boundary_markers = [
        marker for marker in vaccine_boundary_markers if marker not in vaccine_boundary_text
    ]
    report.add(
        "vaccineBoundarySpecific",
        not missing_vaccine_boundary_markers,
        "missing: " + ", ".join(missing_vaccine_boundary_markers)
        if missing_vaccine_boundary_markers
        else "vaccine copy is bounded as records/reminders and points users to doctors/local official information",
    )

    companion_surface_markers = [
        "灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒",
        "固定间隔",
        "宝宝昵称/头像缩略图",
        "桌面/锁屏小组件只读展示今日摘要",
        "手动顺延下一次提醒",
        "5 分钟一档",
        "+5、+10、+15、+20、+25、+30 分钟",
        "本顿结束时间 + 固定间隔 + 顺延分钟",
        "本顿无喂养时长时按本顿发生时间",
        "顺延只改变下一次提醒时间",
        "不新增持久化字段",
        "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
        "也不构成喂养建议",
        "这些状态展示只反映用户主动记录的数据",
        "不生成健康建议、压力提醒、喂养建议或医疗判断",
        "不接入 HealthKit、传感器、医院系统或第三方健康数据源",
        "不提供压力评估、心理健康判断或医疗诊断",
    ]
    companion_surface_text = fill_sheet + "\n" + metadata
    missing_companion_surface_markers = [
        marker for marker in companion_surface_markers if marker not in companion_surface_text
    ]
    report.add(
        "liveActivityWidgetBoundarySpecific",
        not missing_companion_surface_markers,
        "missing: " + ", ".join(missing_companion_surface_markers)
        if missing_companion_surface_markers
        else "Live Activity and widget copy is bounded to feeding reminder / local summary, not health advice or medical judgment",
    )

    feeding_reminder_deferral_markers = [
        "手动顺延下一次提醒",
        "固定喝奶间隔",
        "5 分钟一档",
        "+5、+10、+15、+20、+25、+30 分钟",
        "本顿结束时间 + 固定间隔 + 顺延分钟",
        "本顿无喂养时长时按本顿发生时间",
        "顺延只改变下一次提醒时间",
        "不新增持久化字段",
        "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
        "也不构成喂养建议",
    ]
    missing_feeding_reminder_deferral_markers = [
        marker for marker in feeding_reminder_deferral_markers if marker not in fill_sheet + "\n" + metadata + "\n" + copy_paste_packet
    ]
    report.add(
        "feedingReminderDeferralBoundarySpecific",
        not missing_feeding_reminder_deferral_markers,
        "missing: " + ", ".join(missing_feeding_reminder_deferral_markers)
        if missing_feeding_reminder_deferral_markers
        else "manual feeding reminder deferral is bounded to user-set schedule, not volume/month-age inference or feeding advice",
    )

    screenshot_companion_boundary_markers = [
        "当前 5 张候选图不展示灵动岛/锁屏 Live Activity 或小组件",
        "不得写成健康建议、喂养推荐或医疗判断",
        "正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图",
    ]
    missing_screenshot_companion_boundary_markers = [
        marker for marker in screenshot_companion_boundary_markers if marker not in fill_sheet + "\n" + screenshot_plan
    ]
    report.add(
        "screenshotCompanionSurfaceBoundarySpecific",
        not missing_screenshot_companion_boundary_markers,
        "missing: " + ", ".join(missing_screenshot_companion_boundary_markers)
        if missing_screenshot_companion_boundary_markers
        else "screenshot plan does not imply unverified Live Activity/widget success and keeps iOS 26.5 final proof separate",
    )

    review_account_section = extract_section(fill_sheet, "审核测试账号填写说明")
    missing_review_account_markers = [
        marker for marker in REVIEW_ACCOUNT_BOUNDARY_MARKERS if marker not in review_account_section
    ]
    review_account_secret_hits = forbidden_review_account_secret_hits(fill_sheet + "\n" + copy_paste_packet + "\n" + review_information_packet)
    report.add(
        "reviewAccountInstructionsRedacted",
        bool(review_account_section) and not missing_review_account_markers and not review_account_secret_hits,
        "missing: "
        + ", ".join(missing_review_account_markers)
        + "; secretHits: "
        + ", ".join(review_account_secret_hits)
        if missing_review_account_markers or review_account_secret_hits
        else "review account instructions point to redacted evidence and keep recovery key only in ignored local storage / App Review Information",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--fill-sheet")
    parser.add_argument("--copy-paste-packet")
    parser.add_argument("--draft-json")
    parser.add_argument("--field-freeze-packet")
    parser.add_argument("--entry-session-packet")
    parser.add_argument("--submit-review-preflight-packet")
    parser.add_argument(
        "--asc-backfill-result-template",
        default=DEFAULT_ASC_BACKFILL_RESULT_TEMPLATE,
    )
    parser.add_argument(
        "--asc-privacy-age-review-result-template",
        default=DEFAULT_ASC_PRIVACY_AGE_REVIEW_RESULT_TEMPLATE,
    )
    parser.add_argument("--review-information-packet")
    parser.add_argument("--app-review-test-account-packet")
    parser.add_argument("--review-account-evidence", default=DEFAULT_REVIEW_ACCOUNT_EVIDENCE)
    parser.add_argument("--privacy-answers")
    parser.add_argument("--age-rating-answers")
    parser.add_argument("--version-release-settings")
    parser.add_argument("--final-entry-audit")
    parser.add_argument("--metadata", default="Docs/08_Release/APP_STORE_METADATA.md")
    parser.add_argument("--privacy-label", default="Docs/08_Release/APP_STORE_PRIVACY_LABEL.json")
    parser.add_argument("--screenshot-plan", default="Docs/08_Release/SCREENSHOT_PLAN.md")
    parser.add_argument("--expected-material-date", default=DEFAULT_EXPECTED_MATERIAL_DATE)
    parser.add_argument("--output", default="Backend/proof/app-store-connect-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"App Store Connect materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"App Store Connect materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
