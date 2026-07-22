#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_DOC = Path("Docs/08_Release/MAINLAND_FILING_MATERIALS.md")
GAP_ASSESSMENT_DOC = Path("Docs/08_Release/CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md")
COMPLIANCE_DOC = Path("Docs/07_PrivacySecurity/CHINA_MAINLAND_COMPLIANCE.md")
APP_STORE_COMPLIANCE_TIMELINE_DOC = Path("Docs/08_Release/APP_STORE_COMPLIANCE_TIMELINE.md")
REGIONAL_STRATEGY_DOC = Path("Docs/08_Release/REGIONAL_LAUNCH_STRATEGY.md")
FILING_EXECUTION_PACKET = Path("Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260704.json")
MAINLAND_FILING_PRIVACY_TEMPLATE = Path(
    "Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json"
)
EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")
APP_FILING_EVIDENCE_PATTERNS = ("03-app-filing.pdf", "03-app-filing.png")
REQUIRED_STATUS_MARKERS = (
    "中国大陆 App Store 首发",
    "https://api.mewpow.com/xiaonaiping",
    "小奶瓶专属子域名",
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "iOS 26.5",
    "显著位置展示备案编号",
    "链接工信部备案系统",
    "公安联网备案",
)
REQUIRED_DEVELOPER_HANDOFF_MARKERS = (
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
)
REQUIRED_EXTERNAL_PLATFORM_HANDOFF_MARKERS = (
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "微信开放平台",
    "短信服务商",
    "OBS",
    "生产 proof",
    "iOS 26.5 真机/TestFlight",
)
REQUIRED_FIELD_MARKERS = (
    "深圳市闪现生活科技有限公司",
    "小奶瓶",
    "iOS 原生 App",
    "com.mewpow.xiaonaiping",
    "xiaonaiping-ios-1",
    "父母/照护者记录宝宝喂养、睡眠、排便、成长、疫苗提醒和照片时间线",
    "否，面向父母和照护者",
    "否，不提供诊断、治疗、处方或专业疫苗建议",
    "中国大陆 App Store",
    "香港 App Store",
    "https://api.mewpow.com/xiaonaiping/privacy",
    "https://api.mewpow.com/xiaonaiping/terms",
    "https://api.mewpow.com/xiaonaiping/support",
    "华为云中国大陆 ECS",
    "宝塔 MySQL",
    "华为云 OBS",
    "xiaonaiping_prod",
    "恢复密钥、手机号验证码、微信授权",
)
REQUIRED_COLLECTION_MARKERS = (
    "营业执照电子版",
    "法定代表人",
    "App 负责人",
    "域名证书",
    "云服务器公网 IP",
    "App 图标",
    "隐私政策 URL",
    "App Store Connect 公司主体截图",
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "App Store Connect 公司主体绑定证明",
    "中国大陆只选择可售地区截图",
    "短信服务商签名",
    "微信开放平台移动应用",
    "OBS bucket",
    "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "生产 proof",
    "iOS 26.5 真机/TestFlight",
    "备案编号",
    "公安联网备案提交/通过证明",
)
REQUIRED_EVIDENCE_FILENAMES = (
    "01-company-account.png",
    "02-mainland-availability.png",
    "03-app-filing.pdf",
    ".png",
    "04-privacy-label.png",
    "05-signed-archive.png",
    "06-testflight.png",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "09-obs-policy.png",
    "10-final-screenshots/",
    "11-test-account-redacted.json",
)
REQUIRED_PRE_CODE_MARKERS = (
    "拿到备案编号后再做，不提前写占位号",
    "隐私政策、用户协议、支持页底部展示备案编号",
    "App 内“数据与隐私”或“关于小奶瓶”展示备案编号和备案系统链接",
    "App Store Review Notes 补充备案编号",
    "Backend/scripts/check_public_pages.py",
    "Backend/scripts/check_review_notes.py",
    "Backend/scripts/check_production_readiness.py",
)
REQUIRED_SEQUENCE_MARKERS = (
    "确认专属域名",
    "APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "D-U-N-S 后的 Apple Developer 公司主体",
    "Team ID",
    "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "微信、短信、OBS、生产 proof",
    "iOS 26.5 真机/TestFlight",
    "华为云/接入商备案系统",
    "备案通过后补 App 内/网页备案编号展示",
    "完成公安联网备案并归档证明",
    "再提交 App Store Connect 中国大陆审核",
)
REQUIRED_FILING_EXECUTION_TEMPLATE_MARKERS = (
    "## 备案 / ICP / 公安联网备案当天执行记录模板",
    "Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260704.json",
    "结构化执行包",
    "同一天同一轮操作",
    "营业执照电子版、法定代表人、App 负责人、网络安全负责人材料已确认",
    "域名证书、域名实名认证、DNS 解析、云服务器公网 IP、接入商信息已确认",
    "Apple Developer Organization enrollment / Team ID 和 App Store Connect 公司主体截图已归档",
    "03-app-filing.pdf 或 03-app-filing.png 已归档",
    "备案系统提交状态、备案号或适用判断结果可见",
    "备案通过前不在公开页、App 内或 Review Notes 写占位备案号",
    "备案通过后再更新 Backend/static/privacy.html、terms.html、support.html",
    "App 内“数据与隐私”或“关于小奶瓶”展示备案编号和工信部备案系统链接",
    "公安联网备案提交/通过证明已归档",
    "check_public_pages.py、check_review_notes.py、check_mainland_filing_materials.py、check_production_readiness.py 已复跑",
    "不记录完整证件号、联系人完整电话、验证码、AK/SK、AppSecret、恢复密钥或 token",
    "如果任一项未通过，不提交中国大陆 App Store 审核",
)
REQUIRED_FILING_EXECUTION_PACKET_DOC_MARKERS = (
    "Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260704.json",
    "结构化执行包",
    "不是备案证据",
    "不能作为提交许可",
)
FILING_EXECUTION_PACKET_SCALARS = {
    "artifactType": "mainland-filing-execution-packet",
    "status": "execution-packet-not-evidence",
    "date": "2026-07-04",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
    "company": "深圳市闪现生活科技有限公司",
}
FILING_EXECUTION_PACKET_SOURCE_FILES = {
    "mainlandFilingMaterials": "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
    "chinaMainlandGapAssessment": "Docs/08_Release/CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md",
    "chinaMainlandCompliance": "Docs/07_PrivacySecurity/CHINA_MAINLAND_COMPLIANCE.md",
    "regionalLaunchStrategy": "Docs/08_Release/REGIONAL_LAUNCH_STRATEGY.md",
    "externalPlatformHandoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "appleDeveloperDunsHandoff": "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "appStoreConnectDraft": "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260704.json",
    "appStoreSubmissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
    "captureGuide": "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
    "evidenceChecklist": "Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260704.md",
}
FILING_EXECUTION_PACKET_TARGETS = {
    "companyAccount": "Docs/08_Release/AppStoreEvidence/01-company-account.png",
    "mainlandAvailability": "Docs/08_Release/AppStoreEvidence/02-mainland-availability.png",
    "appFilingPdf": "Docs/08_Release/AppStoreEvidence/03-app-filing.pdf",
    "appFilingPng": "Docs/08_Release/AppStoreEvidence/03-app-filing.png",
    "publicSecurityFiling": "Docs/08_Release/AppStoreEvidence/03b-public-security-filing.png",
    "privacyLabel": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
    "ageRatingResult": "Docs/08_Release/AppStoreEvidence/17-age-rating-result.png",
    "publicUrlsRealDevice": "Docs/08_Release/AppStoreEvidence/RealDevice/RD-19-public-urls.png",
    "mainlandFilingProof": "Backend/proof/mainland-filing-materials.json",
    "appStoreEvidenceCurrent": "Backend/proof/app-store-evidence-20260704T-current.json",
    "productionReadinessCurrent": "Backend/proof/production-readiness-20260704T-current.json",
}
FILING_EXECUTION_PACKET_DEPENDENCY_FIELDS = (
    "artifactId",
    "target",
    "proves",
    "doesNotProve",
    "requiredBeforeMainlandSubmit",
    "initialStatus",
)
FILING_EXECUTION_PACKET_DEPENDENCY_MATRIX = {
    "companyAccount": {
        "proves": [
            "App Store Connect account legal entity is 深圳市闪现生活科技有限公司",
            "company account evidence exists for China mainland filing and ASC materials",
        ],
        "doesNotProve": [
            "D-U-N-S delivery",
            "Apple Developer Team ID",
            "App filing receipt",
            "Submit for Review permission",
        ],
    },
    "mainlandAvailability": {
        "proves": [
            "China mainland availability selection is visible in App Store Connect",
            "mainland launch region evidence is archived for the same submission round",
        ],
        "doesNotProve": [
            "APP/ICP filing completion",
            "public-security filing",
            "production readiness",
            "iOS 26.5 real-device regression",
        ],
    },
    "appFilingPdf": {
        "proves": [
            "filing system PDF receipt, status, filing number, or applicability result is archived",
            "APP/ICP filing evidence can be reviewed without relying on a screenshot crop",
        ],
        "doesNotProve": [
            "public-security filing",
            "public pages were updated",
            "App Store Connect privacy label",
            "production readiness",
        ],
    },
    "appFilingPng": {
        "proves": [
            "filing system screen shows App name, company, status, filing number, or applicability result",
            "visual filing evidence is archived under the App Store evidence root",
        ],
        "doesNotProve": [
            "public-security filing",
            "legal pages contain the real filing number",
            "App Store Connect mainland availability",
            "production readiness",
        ],
    },
    "publicSecurityFiling": {
        "proves": [
            "public-security filing submission or approval evidence is archived when applicable",
            "post-ICP public-security filing handoff has a target evidence file",
        ],
        "doesNotProve": [
            "APP/ICP filing completion",
            "App Store Connect mainland availability",
            "privacy label",
            "Submit for Review permission",
        ],
    },
    "privacyLabel": {
        "proves": [
            "App Store Connect App Privacy label result is archived",
            "privacy label is available for China mainland review materials",
        ],
        "doesNotProve": [
            "privacy policy URL is reachable on device",
            "APP/ICP filing completion",
            "age rating result",
            "production readiness",
        ],
    },
    "ageRatingResult": {
        "proves": [
            "App Store Connect age rating result is archived",
            "age rating answer sheet has produced a visible ASC result",
        ],
        "doesNotProve": [
            "privacy label",
            "APP/ICP filing completion",
            "final screenshot upload",
            "review approval",
        ],
    },
    "publicUrlsRealDevice": {
        "proves": [
            "privacy, terms, and support URLs are reachable on iOS 26.5 real device or signed-device flow",
            "public legal URLs are not only checked from local files",
        ],
        "doesNotProve": [
            "filing receipt",
            "public pages contain a real filing number",
            "production readiness",
            "full real-device regression",
        ],
    },
    "mainlandFilingProof": {
        "proves": [
            "mainland filing materials checker passed for the current structured packet",
            "local filing materials include required boundaries and no placeholder filing numbers",
        ],
        "doesNotProve": [
            "real APP/ICP filing receipt exists",
            "real public-security filing exists",
            "App Store evidence is ready",
            "production readiness is ready",
        ],
    },
    "appStoreEvidenceCurrent": {
        "proves": [
            "same-day App Store evidence gate status is archived",
            "missing manual evidence is visible before China mainland submission",
        ],
        "doesNotProve": [
            "production readiness",
            "launch objective audit",
            "external platform credentials",
            "filing receipt by itself",
        ],
    },
    "productionReadinessCurrent": {
        "proves": [
            "same-day production readiness gate status is archived",
            "production blockers are visible before China mainland submission",
        ],
        "doesNotProve": [
            "App Store manual evidence",
            "APP/ICP filing receipt",
            "public-security filing",
            "Submit for Review permission",
        ],
    },
}
FILING_EXECUTION_PACKET_EVIDENCE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsFilingExecution", False),
    ("sourceIsAllowedEvidenceRoot", False),
    ("realEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
FILING_EXECUTION_PACKET_SEPARATION_MARKERS = (
    "this packet is not a filing receipt",
    "03-app-filing.pdf or 03-app-filing.png",
    "do not write placeholder filing numbers",
    "do not use simulator screenshots as iOS 26.5 real-device evidence",
    "do not use provider templates",
    "launch-objective-audit.json are ready=true",
)
FILING_EXECUTION_PACKET_SEQUENCE_IDS = (
    "confirmCompanyAndDomain",
    "confirmDeveloperAndProviderDependencies",
    "submitMainlandFiling",
    "captureFilingEvidence",
    "deferPublicNumberUpdatesUntilRealNumber",
    "completePublicSecurityFiling",
    "refreshPostFilingGates",
)
FILING_EXECUTION_PACKET_SEQUENCE_MARKERS = (
    "business license",
    "domain certificate",
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "WeChat Open Platform",
    "SMS provider",
    "OBS",
    "iOS 26.5",
    "Huawei Cloud",
    "03-app-filing.pdf",
    "03-app-filing.png",
    "Backend/static/privacy.html",
    "Backend/static/terms.html",
    "Backend/static/support.html",
    "App Store Review Notes",
    "03b-public-security-filing.png",
    "check_mainland_filing_materials.py",
    "check_public_pages.py",
    "check_review_notes.py",
    "check_app_store_connect_materials.py",
    "check_app_store_evidence.py",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
)
FILING_EXECUTION_PACKET_REDACTION_MARKERS = (
    "personal ID card numbers",
    "full contact phone numbers",
    "verification codes",
    "Huawei Cloud AK/SK",
    "AppSecret",
    "recovery keys",
    "tokens",
    "server passwords",
    "real baby photos",
)
FILING_EXECUTION_PACKET_STOP_CONDITIONS = {
    "noCompanyAccountEvidence": ("01-company-account.png", "Stop China mainland App Store review preparation"),
    "noDunsOrTeamId": ("D-U-N-S", "Apple Developer Organization enrollment", "Team ID"),
    "noExternalProviderEvidence": ("SMS provider", "WeChat Open Platform", "OBS", "production current proof"),
    "noRealFilingNumber": ("No real filing number", "Do not update public pages, App UI, or Review Notes"),
    "placeholderFilingNumberDetected": ("placeholder filing number", "Remove the placeholder"),
    "noIos265RealDeviceOrTestFlightEvidence": ("iOS 26.5", "Do not use iOS 27, simulator"),
    "productionReadinessNotReady": ("production-readiness.json", "launch-objective-audit.json", "ready=true"),
}
FILING_EXECUTION_PACKET_STOP_CONDITION_IDS = tuple(FILING_EXECUTION_PACKET_STOP_CONDITIONS)
FILING_EXECUTION_PACKET_POST_GATES = (
    "check_mainland_filing_materials.py",
    "check_public_pages.py",
    "check_review_notes.py",
    "check_app_store_connect_materials.py",
    "check_app_store_evidence.py",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
)
FILING_EXECUTION_PACKET_COMPLETION_MARKERS = (
    "execution-packet-not-evidence",
    "not submission permission",
    "03-app-filing.pdf or 03-app-filing.png exists",
    "public pages, app UI, and Review Notes",
    "public-security filing evidence",
    "app-store-evidence.json is ready=true",
    "production-readiness.json is ready=true",
    "launch-objective-audit.json is ready=true",
)
FILING_EXECUTION_PACKET_FORBIDDEN_SECRET_MARKERS = (
    "sk-",
    "Bearer ",
    "debug_wechat_",
    "XNP_REVIEW_RECOVERY_KEY=",
)
MAINLAND_FILING_PRIVACY_TEMPLATE_SCALARS = {
    "artifactType": "mainland-filing-privacy-evidence-template",
    "status": "template-only-not-evidence",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
    "company": "深圳市闪现生活科技有限公司",
}
MAINLAND_FILING_PRIVACY_TEMPLATE_TARGETS = {
    "companyAccount": "Docs/08_Release/AppStoreEvidence/01-company-account.png",
    "mainlandAvailability": "Docs/08_Release/AppStoreEvidence/02-mainland-availability.png",
    "mainlandFiling": "Docs/08_Release/AppStoreEvidence/03-app-filing.png or .pdf",
    "privacyLabel": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
    "ageRatingResult": "Docs/08_Release/AppStoreEvidence/17-age-rating-result.png or .pdf",
}
MAINLAND_FILING_PRIVACY_TEMPLATE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsTemplateCapture", False),
    ("sourceIsAllowedEvidenceRoot", False),
    ("realEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
MAINLAND_FILING_PRIVACY_TEMPLATE_DO_NOT_RENAME = (
    "01-company-account.json",
    "02-mainland-availability.json",
    "03-app-filing.json",
    "04-privacy-label.json",
    "17-age-rating-result.json",
)
MAINLAND_FILING_PRIVACY_TEMPLATE_FIELDS = {
    "legalEntity": "深圳市闪现生活科技有限公司",
    "saleRegion": "China mainland only for first launch",
    "filing": "APP filing number, filing progress, or documented applicability judgment",
    "privacyPolicyUrl": "https://api.mewpow.com/xiaonaiping/privacy",
    "termsUrl": "https://api.mewpow.com/xiaonaiping/terms",
    "supportUrl": "https://api.mewpow.com/xiaonaiping/support",
    "privacyLabelSource": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
    "tracking": "No tracking",
    "medicalBoundary": "no HealthKit, no sensors, no hospital system, no medical diagnosis, no treatment advice, no professional vaccine advice",
}
MAINLAND_FILING_PRIVACY_TEMPLATE_REDACTION_MARKERS = (
    "Hide Apple ID email",
    "Hide complete phone numbers",
    "Hide payment details",
    "Hide personal ID details",
    "Hide complete D-U-N-S value",
    "Hide verification codes and tokens",
    "Keep app name, legal entity, China mainland availability, filing status/result, privacy categories, and URLs visible",
)
MAINLAND_FILING_PRIVACY_TEMPLATE_POST_CAPTURE_MARKERS = (
    "check_mainland_filing_materials.py",
    "mainland-filing-materials-20260704T-current.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-07-04",
    "app-store-evidence-20260704T-current.json",
    "check_app_store_connect_materials.py --allow-incomplete",
    "app-store-connect-materials-20260704-current.json",
)
MAINLAND_FILING_PRIVACY_TEMPLATE_COMPLETION_MARKERS = (
    "template is only a capture worksheet",
    "App Store evidence gate remains incomplete",
    "each target evidence file is captured",
    "real App Store Connect",
    "filing",
    "privacy",
    "age-rating surface",
    "passes redaction/size checks",
)
REQUIRED_REDACTION_MARKERS = (
    "遮个人证件细节",
    "App 名称、主体、备案号或提交状态",
    "App 备案/ICP/适用判断进度或结果",
)
REQUIRED_GAP_ASSESSMENT_MARKERS = (
    "日期：2026-07-04",
    "Backend/proof/production-readiness.json",
    "Backend/proof/launch-objective-audit.json",
    "Backend/proof/remote-api.json",
    "Backend/proof/provider-evidence-materials.json",
    "Backend/proof/mainland-filing-materials.json",
    "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "20260704T-current",
    "deploymentProofCurrent",
    "storageBackendProofCurrent",
    "wechatLoginProviderConfigured",
    "ios265PhysicalDeviceAvailabilityReady",
    "appStoreManualEvidenceReady",
    "不得提交中国大陆 App Store",
    "不能用旧 proof、模拟器或模板文档替代",
)
REQUIRED_COMPLIANCE_MARKERS = (
    "日期：2026-07-04",
    "Backend/proof/production-readiness.json",
    "Backend/proof/launch-objective-audit.json",
    "Docs/08_Release/CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md",
    "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "APP 备案",
    "ICP",
    "公安联网备案",
    "微信开放平台",
    "短信服务商",
    "OBS",
    "App Store Connect 人工证据",
    "iOS 26.5",
    "TestFlight",
    "不得直接提交",
)
REQUIRED_APP_STORE_COMPLIANCE_TIMELINE_MARKERS = (
    "日期：2026-07-04",
    "App Store 合规时间线当前版",
    "Backend/proof/production-readiness.json",
    "Backend/proof/launch-objective-audit.json",
    "Backend/proof/app-store-submission-packet.json",
    "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260704.json",
    "Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260704.json",
    "Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260704.json",
    "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
    "Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json",
    "D-U-N-S",
    "Apple Developer Organization enrollment",
    "Team ID",
    "App Store Distribution Archive",
    "TestFlight",
    "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260704.md",
    "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260704.md",
    "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260704.md",
    "Docs/08_Release/XNP_PRODUCTION_PRIVACY_EVIDENCE_WORKBENCH_20260704.md",
    "Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260704.json",
    "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260704.json",
    "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260704.json",
    "Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260704.json",
    "Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260704.json",
    "Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260704.json",
    "iOS 26.5",
    "stableAliasSyncAllowed=false",
    "不得提交 App Store Connect 审核",
)
REQUIRED_REGIONAL_STRATEGY_MARKERS = (
    "日期：2026-07-04",
    "中国大陆 App Store 为第一批",
    "香港 App Store 为第二批",
    "Backend/proof/production-readiness.json",
    "Backend/proof/launch-objective-audit.json",
    "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "20260704T-current",
    "APP 备案",
    "微信/短信/OBS",
    "iOS 26.5 真机/TestFlight",
    "不得提交",
)
STALE_CURRENT_DAY_MARKERS = (
    "日期：2026-06-18",
    "日期：2026-06-28",
    "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260628.md",
    "20260628T-current",
)
FORBIDDEN_PRETEND_COMPLETE_MARKERS = (
    "备案已完成",
    "APP 备案已通过",
    "ICP 备案已通过",
    "公安联网备案已通过",
)
FORBIDDEN_FAKE_NUMBER_PATTERNS = {
    "zeroIcpNumber": re.compile(r"[\u4e00-\u9fa5]?ICP备0{6,}号?"),
    "placeholderAppFilingNumber": re.compile(r"(APP|App|app)?备案(号|编号)[：:]\s*(待填|TODO|TBD|占位|示例)"),
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


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def as_searchable_text(value: Any) -> str:
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return "\n".join(as_searchable_text(item) for item in value)
    return str(value or "")


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


def has_app_filing_evidence(root: Path) -> bool:
    evidence_root = root / EVIDENCE_ROOT
    return any((evidence_root / pattern).is_file() for pattern in APP_FILING_EVIDENCE_PATTERNS)


def fake_number_hits(text: str) -> list[str]:
    return sorted(name for name, pattern in FORBIDDEN_FAKE_NUMBER_PATTERNS.items() if pattern.search(text))


def filing_execution_packet_failures(packet: dict[str, Any]) -> list[str]:
    if not packet:
        return ["mainland filing execution packet invalid or missing"]

    failures: list[str] = []
    for key, expected in FILING_EXECUTION_PACKET_SCALARS.items():
        if packet.get(key) != expected:
            failures.append(f"{key} must be {expected}")

    if packet.get("canSubmitFromThisPacket") is not False:
        failures.append("canSubmitFromThisPacket must be false")

    source_files = packet.get("sourceFiles")
    if not isinstance(source_files, dict):
        failures.append("sourceFiles must be an object")
    else:
        if tuple(source_files) != tuple(FILING_EXECUTION_PACKET_SOURCE_FILES):
            failures.append(
                "sourceFiles order must be "
                + " -> ".join(FILING_EXECUTION_PACKET_SOURCE_FILES)
            )
        for key, expected in FILING_EXECUTION_PACKET_SOURCE_FILES.items():
            if source_files.get(key) != expected:
                failures.append(f"sourceFiles.{key} must be {expected}")

    target_files = packet.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        failures.append("targetEvidenceFiles must be an object")
    else:
        if tuple(target_files) != tuple(FILING_EXECUTION_PACKET_TARGETS):
            failures.append(
                "targetEvidenceFiles order must be "
                + " -> ".join(FILING_EXECUTION_PACKET_TARGETS)
            )
        for key, expected in FILING_EXECUTION_PACKET_TARGETS.items():
            if target_files.get(key) != expected:
                failures.append(f"targetEvidenceFiles.{key} must be {expected}")

    evidence_checks = packet.get("evidenceFileChecks")
    if not isinstance(evidence_checks, list):
        failures.append("evidenceFileChecks must be a list")
    else:
        seen: set[str] = set()
        by_artifact: dict[str, dict[str, Any]] = {}
        for item in evidence_checks:
            if not isinstance(item, dict):
                failures.append("evidenceFileChecks entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in seen:
                failures.append(f"evidenceFileChecks duplicate {artifact_id}")
                continue
            seen.add(artifact_id)
            by_artifact[artifact_id] = item
        expected_ids = tuple(FILING_EXECUTION_PACKET_TARGETS)
        if tuple(by_artifact) != expected_ids:
            failures.append("evidenceFileChecks order must be " + " -> ".join(expected_ids))
        for artifact_id, expected_target in FILING_EXECUTION_PACKET_TARGETS.items():
            check = by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != expected_target:
                failures.append(f"evidenceFileChecks.{artifact_id}.target must be {expected_target}")
            for field, expected in FILING_EXECUTION_PACKET_EVIDENCE_FILE_CHECK_FIELDS:
                if check.get(field) != expected:
                    failures.append(f"evidenceFileChecks.{artifact_id}.{field} must be {expected!r}")

    dependency_matrix = packet.get("evidenceDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("evidenceDependencyMatrix must be a list")
    else:
        seen: set[str] = set()
        by_artifact: dict[str, dict[str, Any]] = {}
        for item in dependency_matrix:
            if not isinstance(item, dict):
                failures.append("evidenceDependencyMatrix entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("evidenceDependencyMatrix entry missing artifactId")
                continue
            if artifact_id in seen:
                failures.append(f"evidenceDependencyMatrix duplicate {artifact_id}")
                continue
            seen.add(artifact_id)
            by_artifact[artifact_id] = item
        expected_ids = tuple(FILING_EXECUTION_PACKET_TARGETS)
        if tuple(by_artifact) != expected_ids:
            failures.append("evidenceDependencyMatrix order must be " + " -> ".join(expected_ids))
        for artifact_id, expected in FILING_EXECUTION_PACKET_DEPENDENCY_MATRIX.items():
            item = by_artifact.get(artifact_id)
            if not isinstance(item, dict):
                failures.append(f"evidenceDependencyMatrix.{artifact_id} missing object")
                continue
            if tuple(item) != FILING_EXECUTION_PACKET_DEPENDENCY_FIELDS:
                failures.append(f"evidenceDependencyMatrix.{artifact_id} keys must match dependency schema")
            expected_target = FILING_EXECUTION_PACKET_TARGETS[artifact_id]
            if item.get("target") != expected_target:
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.target must be {expected_target}")
            if item.get("proves") != expected["proves"]:
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.proves must be {expected['proves']}")
            if item.get("doesNotProve") != expected["doesNotProve"]:
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.doesNotProve must be {expected['doesNotProve']}")
            if item.get("requiredBeforeMainlandSubmit") is not True:
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.requiredBeforeMainlandSubmit must be True")
            if item.get("initialStatus") != "pending":
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.initialStatus must be pending")

    separation_text = as_searchable_text(packet.get("separationRules"))
    for marker in FILING_EXECUTION_PACKET_SEPARATION_MARKERS:
        if marker not in separation_text:
            failures.append(f"separationRules missing {marker}")

    sequence = packet.get("preSubmissionSequence")
    if not isinstance(sequence, list):
        failures.append("preSubmissionSequence must be a list")
    else:
        sequence_ids = [
            item.get("step")
            for item in sequence
            if isinstance(item, dict)
        ]
        if tuple(sequence_ids) != FILING_EXECUTION_PACKET_SEQUENCE_IDS:
            failures.append("preSubmissionSequence order must be " + " -> ".join(FILING_EXECUTION_PACKET_SEQUENCE_IDS))
        sequence_text = as_searchable_text(sequence)
        for marker in FILING_EXECUTION_PACKET_SEQUENCE_MARKERS:
            if marker not in sequence_text:
                failures.append(f"preSubmissionSequence missing {marker}")

    redaction_text = as_searchable_text(packet.get("redactionChecklist"))
    for marker in FILING_EXECUTION_PACKET_REDACTION_MARKERS:
        if marker not in redaction_text:
            failures.append(f"redactionChecklist missing {marker}")

    stop_conditions = packet.get("stopConditions")
    if not isinstance(stop_conditions, list):
        failures.append("stopConditions must be a list")
    else:
        stop_condition_ids = tuple(
            item.get("id")
            for item in stop_conditions
            if isinstance(item, dict)
        )
        if stop_condition_ids != FILING_EXECUTION_PACKET_STOP_CONDITION_IDS:
            failures.append(
                "stopConditions order must be "
                + " -> ".join(FILING_EXECUTION_PACKET_STOP_CONDITION_IDS)
            )
        by_id = {
            item.get("id"): item
            for item in stop_conditions
            if isinstance(item, dict)
        }
        for stop_id, markers in FILING_EXECUTION_PACKET_STOP_CONDITIONS.items():
            item = by_id.get(stop_id)
            if not item:
                failures.append(f"stopConditions missing {stop_id}")
                continue
            item_text = as_searchable_text(item)
            for marker in markers:
                if marker not in item_text:
                    failures.append(f"stopConditions.{stop_id} missing {marker}")

    post_gate_text = as_searchable_text(packet.get("postExecutionGates"))
    for marker in FILING_EXECUTION_PACKET_POST_GATES:
        if marker not in post_gate_text:
            failures.append(f"postExecutionGates missing {marker}")

    completion_rule = str(packet.get("completionRule", ""))
    for marker in FILING_EXECUTION_PACKET_COMPLETION_MARKERS:
        if marker not in completion_rule:
            failures.append(f"completionRule missing {marker}")

    packet_text = as_searchable_text(packet)
    secret_hits = [marker for marker in FILING_EXECUTION_PACKET_FORBIDDEN_SECRET_MARKERS if marker in packet_text]
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def mainland_filing_privacy_template_failures(template: dict[str, Any]) -> list[str]:
    if not template:
        return ["mainland filing privacy evidence template invalid or missing"]

    failures: list[str] = []
    for key, expected in MAINLAND_FILING_PRIVACY_TEMPLATE_SCALARS.items():
        if template.get(key) != expected:
            failures.append(f"mainlandFilingPrivacyTemplate.{key} must be {expected}")

    target_files = template.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        failures.append("mainlandFilingPrivacyTemplate.targetEvidenceFiles must be an object")
    else:
        if tuple(target_files) != tuple(MAINLAND_FILING_PRIVACY_TEMPLATE_TARGETS):
            failures.append(
                "mainlandFilingPrivacyTemplate.targetEvidenceFiles order must be "
                + " -> ".join(MAINLAND_FILING_PRIVACY_TEMPLATE_TARGETS)
            )
        for key, expected in MAINLAND_FILING_PRIVACY_TEMPLATE_TARGETS.items():
            if target_files.get(key) != expected:
                failures.append(f"mainlandFilingPrivacyTemplate.targetEvidenceFiles.{key} must be {expected}")

    file_checks = template.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append("mainlandFilingPrivacyTemplate.evidenceFileChecks must be a list")
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for check in file_checks:
            if not isinstance(check, dict):
                failures.append("mainlandFilingPrivacyTemplate.evidenceFileChecks entries must be objects")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("mainlandFilingPrivacyTemplate.evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in checks_by_artifact:
                failures.append(f"mainlandFilingPrivacyTemplate.evidenceFileChecks duplicate {artifact_id}")
            checks_by_artifact[artifact_id] = check
        if tuple(artifact_order) != tuple(MAINLAND_FILING_PRIVACY_TEMPLATE_TARGETS):
            failures.append("mainlandFilingPrivacyTemplate.evidenceFileChecks order must match targetEvidenceFiles")
        for artifact_id, expected_target in MAINLAND_FILING_PRIVACY_TEMPLATE_TARGETS.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"mainlandFilingPrivacyTemplate.evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != expected_target:
                failures.append(f"mainlandFilingPrivacyTemplate.evidenceFileChecks.{artifact_id}.target must be {expected_target}")
            for field, expected in MAINLAND_FILING_PRIVACY_TEMPLATE_FILE_CHECK_FIELDS:
                if check.get(field) != expected:
                    failures.append(
                        f"mainlandFilingPrivacyTemplate.evidenceFileChecks.{artifact_id}.{field} must be {expected!r}"
                    )

    do_not_rename_text = as_searchable_text(template.get("doNotRenameThisTemplateTo"))
    for marker in MAINLAND_FILING_PRIVACY_TEMPLATE_DO_NOT_RENAME:
        if marker not in do_not_rename_text:
            failures.append(f"mainlandFilingPrivacyTemplate.doNotRenameThisTemplateTo missing {marker}")

    fields = template.get("fieldsToVerify")
    if not isinstance(fields, dict):
        failures.append("mainlandFilingPrivacyTemplate.fieldsToVerify must be an object")
    else:
        for key, expected in MAINLAND_FILING_PRIVACY_TEMPLATE_FIELDS.items():
            if fields.get(key) != expected:
                failures.append(f"mainlandFilingPrivacyTemplate.fieldsToVerify.{key} must be {expected}")

    redaction_text = as_searchable_text(template.get("redactionChecklist"))
    for marker in MAINLAND_FILING_PRIVACY_TEMPLATE_REDACTION_MARKERS:
        if marker not in redaction_text:
            failures.append(f"mainlandFilingPrivacyTemplate.redactionChecklist missing {marker}")

    post_capture_text = as_searchable_text(template.get("postCaptureChecks"))
    for marker in MAINLAND_FILING_PRIVACY_TEMPLATE_POST_CAPTURE_MARKERS:
        if marker not in post_capture_text:
            failures.append(f"mainlandFilingPrivacyTemplate.postCaptureChecks missing {marker}")

    completion_rule = str(template.get("completionRule", ""))
    for marker in MAINLAND_FILING_PRIVACY_TEMPLATE_COMPLETION_MARKERS:
        if marker not in completion_rule:
            failures.append(f"mainlandFilingPrivacyTemplate.completionRule missing {marker}")

    template_text = as_searchable_text(template)
    secret_hits = [marker for marker in FILING_EXECUTION_PACKET_FORBIDDEN_SECRET_MARKERS if marker in template_text]
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
    materials_path = root / args.materials
    text = read_text(materials_path)
    mainland_filing_privacy_template_path = root / args.mainland_filing_privacy_template
    mainland_filing_privacy_template = read_json(mainland_filing_privacy_template_path)
    report = Report()

    report.add("materialsDocumentPresent", bool(text), str(materials_path) if text else "missing mainland filing materials")
    report.add(
        "mainlandFilingPrivacyEvidenceTemplatePresent",
        bool(mainland_filing_privacy_template),
        str(mainland_filing_privacy_template_path)
        if mainland_filing_privacy_template
        else "missing mainland filing/privacy evidence template",
    )

    status_section = extract_section(text, "当前判断")
    missing_status = missing_markers(status_section, REQUIRED_STATUS_MARKERS)
    report.add(
        "currentJudgmentCoversLaunchAndFilingPath",
        bool(status_section) and not missing_status,
        "missing: " + ", ".join(missing_status) if missing_status else "mainland-first filing path and post-filing display boundary present",
    )

    missing_developer_handoff = missing_markers(text, REQUIRED_DEVELOPER_HANDOFF_MARKERS)
    report.add(
        "dunsAppleDeveloperDependencyDocumented",
        bool(text) and not missing_developer_handoff,
        "missing: " + ", ".join(missing_developer_handoff)
        if missing_developer_handoff
        else "D-U-N-S follow-up, Apple Developer Organization enrollment, and Team ID dependency are documented",
    )

    missing_external_handoff = missing_markers(text, REQUIRED_EXTERNAL_PLATFORM_HANDOFF_MARKERS)
    report.add(
        "externalPlatformEvidenceHandoffDocumented",
        bool(text) and not missing_external_handoff,
        "missing: " + ", ".join(missing_external_handoff)
        if missing_external_handoff
        else "WeChat, SMS, OBS, production proof, and iOS 26.5 evidence handoff is documented",
    )

    field_section = extract_section(text, "拟填信息")
    missing_fields = missing_markers(field_section, REQUIRED_FIELD_MARKERS)
    report.add(
        "draftFilingFieldsComplete",
        bool(field_section) and not missing_fields,
        "missing: " + ", ".join(missing_fields) if missing_fields else "draft filing fields cover entity, app, URLs, cloud, storage, and auth methods",
    )

    collection_section = extract_section(text, "需要向公司/后台拿到的材料")
    missing_collection = missing_markers(collection_section, REQUIRED_COLLECTION_MARKERS)
    report.add(
        "externalMaterialCollectionListComplete",
        bool(collection_section) and not missing_collection,
        "missing: " + ", ".join(missing_collection) if missing_collection else "external company/cloud/provider material list is complete",
    )

    evidence_section = extract_section(text, "证据归档文件名")
    missing_evidence = missing_markers(evidence_section, REQUIRED_EVIDENCE_FILENAMES)
    report.add(
        "evidenceArchiveFilenamesMatchGate",
        bool(evidence_section) and not missing_evidence,
        "missing: " + ", ".join(missing_evidence) if missing_evidence else "evidence filenames align with AppStoreEvidence gate",
    )

    pre_code_section = extract_section(text, "上线前需要改代码的备案项")
    missing_pre_code = missing_markers(pre_code_section, REQUIRED_PRE_CODE_MARKERS)
    report.add(
        "postFilingCodeChangesDeferredUntilRealNumber",
        bool(pre_code_section) and not missing_pre_code,
        "missing: " + ", ".join(missing_pre_code) if missing_pre_code else "filing number UI/page/review-note changes are explicitly deferred until real filing number",
    )

    sequence_section = extract_section(text, "提交顺序")
    missing_sequence = missing_markers(sequence_section, REQUIRED_SEQUENCE_MARKERS)
    report.add(
        "submissionSequenceKeepsFilingBeforeChinaReview",
        bool(sequence_section) and not missing_sequence,
        "missing: " + ", ".join(missing_sequence) if missing_sequence else "submission order keeps filing and public-security evidence before China App Store review",
    )

    execution_template_section = extract_section(text, "备案 / ICP / 公安联网备案当天执行记录模板")
    missing_execution_template = missing_markers(text, REQUIRED_FILING_EXECUTION_TEMPLATE_MARKERS)
    report.add(
        "filingSameDayExecutionTemplatePresent",
        bool(execution_template_section) and not missing_execution_template,
        "missing: " + ", ".join(missing_execution_template)
        if missing_execution_template
        else "filing execution template ties company/domain/cloud/App Store evidence, filing proof, public-security filing, post-number updates, reruns, and redaction into one China review decision",
    )

    missing_packet_doc = missing_markers(text, REQUIRED_FILING_EXECUTION_PACKET_DOC_MARKERS)
    report.add(
        "filingExecutionPacketReferenced",
        bool(text) and not missing_packet_doc,
        "missing: " + ", ".join(missing_packet_doc)
        if missing_packet_doc
        else "mainland filing materials reference the structured execution packet and keep it separate from real evidence or submission permission",
    )

    filing_execution_packet_path = root / FILING_EXECUTION_PACKET
    filing_execution_packet = read_json(filing_execution_packet_path)
    report.add(
        "filingExecutionPacketPresent",
        bool(filing_execution_packet),
        str(filing_execution_packet_path)
        if filing_execution_packet
        else "missing mainland filing execution packet",
    )
    filing_execution_failures = filing_execution_packet_failures(filing_execution_packet)
    report.add(
        "filingExecutionPacketValid",
        not filing_execution_failures,
        "; ".join(filing_execution_failures)
        if filing_execution_failures
        else "mainland filing execution packet locks source files, target evidence files, stop conditions, redaction, post-execution gates, and no-submission boundary",
    )
    mainland_filing_template_failures = mainland_filing_privacy_template_failures(mainland_filing_privacy_template)
    report.add(
        "mainlandFilingPrivacyEvidenceTemplateValid",
        not mainland_filing_template_failures,
        "; ".join(mainland_filing_template_failures)
        if mainland_filing_template_failures
        else "mainland filing/privacy evidence template covers company account, China mainland availability, filing, privacy label, age rating result, URLs, medical/privacy boundary, redaction, post-capture gates, and template-only completion boundary",
    )

    capture_guide = read_text(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md")
    missing_redaction = missing_markers(capture_guide, REQUIRED_REDACTION_MARKERS)
    report.add(
        "captureGuideCoversFilingEvidenceRedaction",
        bool(capture_guide) and not missing_redaction,
        "missing: " + ", ".join(missing_redaction) if missing_redaction else "capture guide describes filing evidence contents and redaction boundary",
    )

    gap_assessment = read_text(root / "Docs/08_Release/CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md")
    missing_gap_markers = missing_markers(gap_assessment, REQUIRED_GAP_ASSESSMENT_MARKERS)
    report.add(
        "chinaMainlandGapAssessmentCurrent",
        bool(gap_assessment) and not missing_gap_markers,
        "missing: " + ", ".join(missing_gap_markers)
        if missing_gap_markers
        else "China mainland launch gap assessment references current proof gates, current blockers, and no-submission boundary",
    )
    regional_strategy = read_text(root / REGIONAL_STRATEGY_DOC)
    missing_regional_markers = missing_markers(regional_strategy, REQUIRED_REGIONAL_STRATEGY_MARKERS)
    report.add(
        "regionalLaunchStrategyCurrent",
        bool(regional_strategy) and not missing_regional_markers,
        "missing: " + ", ".join(missing_regional_markers)
        if missing_regional_markers
        else "regional launch strategy uses current China-first, Hong Kong-second, 2026-07-04 proof, handoff, and no-submission boundaries",
    )
    app_store_compliance_timeline = read_text(root / APP_STORE_COMPLIANCE_TIMELINE_DOC)
    missing_timeline_markers = missing_markers(
        app_store_compliance_timeline,
        REQUIRED_APP_STORE_COMPLIANCE_TIMELINE_MARKERS,
    )
    report.add(
        "appStoreComplianceTimelineCurrent",
        bool(app_store_compliance_timeline) and not missing_timeline_markers,
        "missing: " + ", ".join(missing_timeline_markers)
        if missing_timeline_markers
        else "App Store compliance timeline uses current 2026-07-04 App Store Connect, D-U-N-S, TestFlight, provider, filing, production, iOS 26.5, and no-submission boundaries",
    )
    stale_current_markers = [
        marker
        for marker in STALE_CURRENT_DAY_MARKERS
        if marker in text + "\n" + gap_assessment + "\n" + regional_strategy + "\n" + app_store_compliance_timeline
    ]
    report.add(
        "mainlandMaterialsUseCurrentDayHandoff",
        not stale_current_markers,
        "stale: " + ", ".join(stale_current_markers)
        if stale_current_markers
        else "mainland filing materials and China gap assessment use the current 2026-07-04 external handoff and current proof names",
    )

    compliance = read_text(root / COMPLIANCE_DOC)
    missing_compliance_markers = missing_markers(compliance, REQUIRED_COMPLIANCE_MARKERS)
    report.add(
        "chinaMainlandComplianceCurrent",
        bool(compliance) and not missing_compliance_markers,
        "missing: " + ", ".join(missing_compliance_markers)
        if missing_compliance_markers
        else "China mainland compliance note points to current filing materials, handoffs, proof gates, external evidence, iOS 26.5/TestFlight, and no-submission boundary",
    )

    actual_app_filing_evidence = has_app_filing_evidence(root)
    pretend_complete_hits = sorted(marker for marker in FORBIDDEN_PRETEND_COMPLETE_MARKERS if marker in text)
    fake_hits = fake_number_hits(text)
    report.add(
        "doesNotPretendFilingCompleteBeforeEvidence",
        (actual_app_filing_evidence or not pretend_complete_hits) and not fake_hits,
        "completionClaims="
        + ", ".join(pretend_complete_hits)
        + "; fakeNumbers="
        + ", ".join(fake_hits)
        if pretend_complete_hits or fake_hits
        else "materials do not claim App/ICP/public-security filing is complete before archived evidence",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--materials", default=str(EXPECTED_DOC))
    parser.add_argument("--mainland-filing-privacy-template", default=str(MAINLAND_FILING_PRIVACY_TEMPLATE))
    parser.add_argument("--output", default="Backend/proof/mainland-filing-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"mainland filing materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"mainland filing materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
