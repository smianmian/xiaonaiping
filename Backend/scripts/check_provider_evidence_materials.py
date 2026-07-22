#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_STORE_SUBMISSION_PACKET = Path("Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md")
CHINA_MAINLAND_RUNBOOK = Path("Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md")
APP_STORE_EVIDENCE_README = Path("Docs/08_Release/AppStoreEvidence/README.md")
APP_STORE_EVIDENCE_CAPTURE_GUIDE = Path("Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md")
WECHAT_CLIENT_CONFIGURATION = Path("Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md")
EXTERNAL_PLATFORM_EVIDENCE_HANDOFF = Path("Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md")
EXTERNAL_PLATFORM_CAPTURE_WORKBENCH = Path("Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_20260704.md")
EXTERNAL_PLATFORM_CAPTURE_PACKET = Path("Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260704.json")
EXTERNAL_PLATFORM_CAPTURE_RESULT_TEMPLATE = Path(
    "Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json"
)
SMS_LIVE_SEND_PACKET = Path("Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260704.json")
OBS_STORAGE_PROOF_PACKET = Path("Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260704.json")
PRODUCTION_PROOF_REFRESH_PACKET = Path("Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260704.json")
PRODUCTION_PROOF_REFRESH_STATUS = Path("Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260704.json")
PRODUCTION_PROOF_REFRESH_STATUS_SCRIPT = Path("Backend/scripts/check_production_proof_refresh_status.py")
SMS_ADAPTER_DOC = Path("Backend/deploy/aliyun-sms-webhook-adapter.md")
SMS_ADAPTER_SERVER = Path("Backend/sms/aliyun-webhook-adapter/server.js")
SMS_ADAPTER_ENV_EXAMPLE = Path("Backend/deploy/aliyun-sms-adapter.env.example")
SMS_ADAPTER_SERVICE_EXAMPLE = Path("Backend/deploy/xiaonaiping-aliyun-sms-adapter.service.example")
PRODUCTION_CONFIG_EXAMPLE = Path("Backend/deploy/production-config.example")
OBS_HANDOFF_DOC = Path("Backend/deploy/huawei-obs.md")
EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")
SMS_PROVIDER_TEMPLATE = Path("Docs/08_Release/AppStoreEvidence/_templates/sms-provider-evidence.template.json")
WECHAT_OPEN_PLATFORM_TEMPLATE = Path("Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json")
OBS_POLICY_TEMPLATE = Path("Docs/08_Release/AppStoreEvidence/_templates/obs-policy-evidence.template.json")

EVIDENCE_FILENAME_MARKERS = (
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "08b-wechat-universal-link-aasa.png",
    "09-obs-policy.png",
)
CAPTURE_GUIDE_MARKERS = (
    "`07-sms-provider.png`",
    "真实短信签名、账号登录/验证验证码模板和发送成功",
    "模板不含营销、不含医疗、不含育儿建议",
    "模板审核状态、发送区域",
    "AccessKey、Secret、完整手机号、验证码",
    "`08-wechat-open-platform.png`",
    "AppID、Bundle ID、URL Scheme、Universal Link",
    "AppSecret、管理员账号",
    "`08b-wechat-universal-link-aasa.png`",
    "AASA、Team ID、Associated Domains、微信 Universal Link",
    "Apple ID 邮箱、完整手机号、AppSecret",
    "`09-obs-policy.png`",
    "bucket/prefix、区域、加密/生命周期/删除策略状态",
    "AK/SK、完整对象 key",
)
SMS_MATERIAL_MARKERS = (
    "07-sms-provider.png",
    "阿里云 Dysmsapi",
    "HMAC-SHA256",
    "dysms:SendSms",
    "签名",
    "模板",
    "账号登录/验证",
    "不含营销",
    "不含医疗",
    "不含育儿建议",
    "模板审核状态",
    "发送区域",
    "发送成功",
    "AccessKey",
    "Secret",
    "完整手机号",
    "验证码",
    "XNP_SMS_SECRET",
    "## 短信服务商截图字段清单",
    "短信服务商控制台",
    "短信签名",
    "验证码模板",
    "账号登录/验证",
    "模板审核状态",
    "发送区域",
    "发送成功记录",
    "脱敏手机号片段",
    "RAM / 权限边界",
    "只允许 `dysms:SendSms`",
    "verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE",
    "默认 `verify_auth_providers.py --live-check` 只证明 provider 配置存在",
    "不替代短信服务商截图或真实实发截图",
    "auth-providers-sms-live-YYYYMMDDT-current.json",
    "只有两份 auth provider proof 都通过",
)
SMS_LIVE_SEND_PROOF_MARKERS = (
    "Backend/proof/auth-providers-20260704T-current.json",
    "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "--output Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "--auth-providers-proof Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "cp Backend/proof/auth-providers-sms-live-20260704T-current.json Backend/proof/auth-providers.json",
    "配置 proof",
    "真实实发 proof",
    "只有两份 auth provider proof 都通过",
    "不能来自未实发短信的配置 proof",
)
SMS_LIVE_SEND_PACKET_DOC_MARKERS = (
    "## 真实短信实发执行包",
    "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260704.json",
    "不是证据",
    "不是短信密钥容器",
    "不能作为提交许可",
    "auth-providers-20260704T-current.json",
    "auth-providers-sms-live-20260704T-current.json",
    "verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE",
    "07-sms-provider.png",
    "账号登录/验证",
    "不含营销",
    "不含医疗",
    "不含育儿建议",
    "auth-providers.json",
    "完整手机号",
    "验证码",
)
SMS_LIVE_SEND_PACKET_MARKERS = (
    "sms-provider-live-send-packet",
    "live-send-packet-not-evidence",
    "2026-07-04",
    "XiaoNaiPing",
    "小奶瓶",
    "Backend/deploy/aliyun-sms-webhook-adapter.md",
    "Docs/08_Release/AppStoreEvidence/_templates/sms-provider-evidence.template.json",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260704.json",
    "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
    "Docs/08_Release/AppStoreEvidence/README.md",
    "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
    "Docs/08_Release/AppStoreEvidence/07-sms-provider.pdf",
    "Backend/proof/auth-providers-20260704T-current.json",
    "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "Backend/proof/auth-providers.json",
    "localSecretHandling",
    "XNP_SMS_TEST_PHONE",
    "private local shell environment or private env file only",
    "full phone number in command line",
    "echoing the env value",
    "committing the phone value",
    "evidenceFileChecks",
    "fileSizeBytes",
    "sha256",
    "FILL_AFTER_CAPTURE",
    "sameRoundAsSmsLiveSend",
    "sourceIsAllowedEvidenceRoot",
    "realEvidenceNotTemplate",
    "secretValuesNotRecorded",
    "providerConfigProof is not smsLiveSendProof",
    "verify_auth_providers.py --live-check only proves provider configuration",
    "verify_auth_providers.py --send-test-sms --require-sms-live-send is required for real live send proof",
    "stableAuthAlias must be copied from auth-providers-sms-live-20260704T-current.json",
    "provider name",
    "阿里云 Dysmsapi",
    "approved SMS signature",
    "account-login/verification template ID or name",
    "template audit status",
    "send region",
    "successful send state",
    "masked recipient phone fragment",
    "account login / verification only",
    "no marketing wording",
    "no medical wording",
    "no feeding advice",
    "no vaccine advice",
    "XNP_SMS_SECRET",
    "webhook secret",
    "AccessKey",
    "SecretKey",
    "complete phone numbers",
    "verification code values",
    "tokens",
    "request signatures",
    "confirmProviderTemplate",
    "captureProviderConsole",
    "refreshProviderConfigProof",
    "runRealSmsLiveSend",
    "check_app_store_evidence.py --allow-incomplete --date 2026-07-04",
    "cp Backend/proof/auth-providers-sms-live-20260704T-current.json Backend/proof/auth-providers.json",
    "check_provider_evidence_materials.py",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
    "SMS evidence is complete only after real 07-sms-provider.png or PDF exists",
    "app-store-evidence.json is ready=true",
    "production-readiness.json plus launch-objective-audit.json are ready=true",
)
SMS_LIVE_SEND_PACKET_TARGET_EVIDENCE_FILES = {
    "smsProviderConsole": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
    "smsProviderConsolePdf": "Docs/08_Release/AppStoreEvidence/07-sms-provider.pdf",
    "providerConfigProof": "Backend/proof/auth-providers-20260704T-current.json",
    "smsLiveSendProof": "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "stableAuthAlias": "Backend/proof/auth-providers.json",
}
SMS_LIVE_SEND_PACKET_EVIDENCE_FILE_CHECKS = {
    "smsProviderConsole": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png or .pdf",
    "providerConfigProof": "Backend/proof/auth-providers-20260704T-current.json",
    "smsLiveSendProof": "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "stableAuthAlias": "Backend/proof/auth-providers.json",
}
SMS_LIVE_SEND_PACKET_EVIDENCE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsSmsLiveSend", False),
    ("sourceIsAllowedEvidenceRoot", False),
    ("realEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
SMS_LIVE_SEND_PACKET_LOCAL_SECRET_HANDLING = {
    "testPhoneEnv": "XNP_SMS_TEST_PHONE",
    "storage": "private local shell environment or private env file only",
    "forbidden": [
        "full phone number in command line",
        "echoing the env value",
        "committing the phone value",
    ],
}
SMS_LIVE_SEND_PACKET_REAL_SEND_COMMAND_MARKERS = (
    "verify_auth_providers.py",
    "--live-check",
    "--send-test-sms",
    "--require-sms-live-send",
    "--phone-env XNP_SMS_TEST_PHONE",
    "--output Backend/proof/auth-providers-sms-live-20260704T-current.json",
)
SMS_LIVE_SEND_PACKET_DEPENDENCY_MATRIX = {
    "smsProviderConsole": {
        "target": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png or .pdf",
        "proves": [
            "provider name",
            "approved SMS signature",
            "account-login/verification template",
            "template audit status",
            "send region",
            "masked recipient phone fragment",
            "no marketing, medical, feeding advice, or vaccine advice",
        ],
        "doesNotProve": [
            "provider configuration proof",
            "real SMS live send proof",
            "stable auth alias",
            "App Store submission readiness",
        ],
        "requiredBeforeAliasSync": False,
        "initialStatus": "pending",
    },
    "providerConfigProof": {
        "target": "Backend/proof/auth-providers-20260704T-current.json",
        "proves": [
            "production SMS provider configuration",
            "live-check reached provider configuration",
            "secrets are redacted",
        ],
        "doesNotProve": [
            "real SMS live send proof",
            "SMS provider console screenshot",
            "stable auth alias",
        ],
        "requiredBeforeAliasSync": True,
        "initialStatus": "pending",
    },
    "smsLiveSendProof": {
        "target": "Backend/proof/auth-providers-sms-live-20260704T-current.json",
        "proves": [
            "real SMS sent to redacted test phone",
            "--send-test-sms",
            "--require-sms-live-send",
            "verification code value is redacted",
        ],
        "doesNotProve": [
            "SMS provider console screenshot",
            "App Store evidence ready",
            "production readiness ready",
        ],
        "requiredBeforeAliasSync": True,
        "initialStatus": "pending",
    },
    "stableAuthAlias": {
        "target": "Backend/proof/auth-providers.json",
        "proves": [
            "stable alias synced from sms live-send proof only after provider config and live send pass",
            "same evidence round",
        ],
        "doesNotProve": [
            "App Store evidence ready",
            "production readiness ready",
            "launch objective audit ready",
        ],
        "requiredBeforeAliasSync": False,
        "initialStatus": "pending",
    },
}
SMS_LIVE_SEND_PACKET_DEPENDENCY_IDS = tuple(SMS_LIVE_SEND_PACKET_DEPENDENCY_MATRIX)
SMS_ADAPTER_SERVER_MARKERS = (
    "const MAX_BODY_BYTES = 16 * 1024",
    "const DEFAULT_HOST = '127.0.0.1'",
    "const DEFAULT_PORT = 8791",
    "https://dysmsapi.aliyuncs.com",
    "crypto.createHmac('sha256', secret).update(payload).digest('hex')",
    "crypto.timingSafeEqual",
    "verifyWebhookSignature(secret, body, req.headers['x-xnp-signature'])",
    "normalizeAliyunPhoneNumber",
    "XNP_SMS_ADAPTER_MOCK",
    "SMS_MOCK",
    "client.request('SendSms', params, { method: 'POST' })",
    "requestId: result.RequestId || null",
    "maskedPhone(payload && payload.phoneNumber)",
    "req.method === 'GET' && req.url === '/healthz'",
    "req.method === 'POST' && req.url === '/send'",
    "invalid_signature",
)
SMS_ADAPTER_ENV_MARKERS = (
    "XNP_SMS_ADAPTER_HOST=127.0.0.1",
    "XNP_SMS_ADAPTER_PORT=8791",
    "XNP_SMS_SECRET=replace-with-same-secret-as-xiaonaiping-api",
    "XNP_SMS_ADAPTER_MOCK=0",
    "ALIYUN_ACCESS_KEY_ID=replace-in-private-deployment",
    "ALIYUN_ACCESS_KEY_SECRET=replace-in-private-deployment",
    "ALIYUN_SIGN_NAME=深圳市闪现生活科技",
    "ALIYUN_TEMPLATE_CODE=SMS_508990073",
    "ALIYUN_REGION_ID=cn-hangzhou",
    "ALIYUN_SMS_ENDPOINT=https://dysmsapi.aliyuncs.com",
)
SMS_ADAPTER_SERVICE_MARKERS = (
    "Description=XiaoNaiPing Aliyun SMS Webhook Adapter",
    "User=xiaonaiping",
    "Group=xiaonaiping",
    "WorkingDirectory=/srv/xiaonaiping/current/Backend/sms/aliyun-webhook-adapter",
    "EnvironmentFile=/srv/xiaonaiping/private/xiaonaiping-aliyun-sms-adapter.env",
    "ExecStart=/usr/local/bin/node /srv/xiaonaiping/current/Backend/sms/aliyun-webhook-adapter/server.js",
    "Restart=always",
    "NoNewPrivileges=true",
    "PrivateTmp=true",
    "ProtectSystem=full",
)
SMS_API_ENV_MARKERS = (
    "XNP_SMS_PROVIDER=webhook",
    "XNP_SMS_WEBHOOK_URL=http://127.0.0.1:8791/send",
    "XNP_SMS_SECRET=replace-in-private-deployment",
    "XNP_SMS_TEMPLATE_ID=SMS_508990073",
)
WECHAT_MATERIAL_MARKERS = (
    "08-wechat-open-platform.png",
    "wx + 16 hex",
    "AppID",
    "Bundle ID",
    "URL Scheme",
    "Universal Link",
    "AppSecret",
    "服务端",
    "不能写进 iOS 工程或仓库",
)
WECHAT_UNIVERSAL_LINK_AASA_MARKERS = (
    "08b-wechat-universal-link-aasa.png",
    "Backend/proof/universal-links-20260704T-current.json",
    "Backend/proof/wechat-client-configuration-20260704T-current.json",
    "Apple 新组织 Team ID",
    "新 Team ID.com.mewpow.xiaonaiping",
    "https://api.mewpow.com/.well-known/apple-app-site-association",
    "application/json",
    "applinks",
    "/xiaonaiping/wechat/",
    "Associated Domains",
    "applinks:api.mewpow.com",
    "XNPWeChatUniversalLink",
    "真机微信登录回调",
    "AASA、Associated Domains 和 Release 包",
)
OBS_MATERIAL_MARKERS = (
    "09-obs-policy.png",
    "private bucket",
    "bucket",
    "prefix",
    "区域",
    "加密",
    "生命周期",
    "删除验证",
    "AK/SK",
    "完整对象 key",
    "server-side",
)
OBS_STORAGE_PACKET_DOC_MARKERS = (
    "## OBS 私有访问与删除验证执行包",
    "Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260704.json",
    "不是证据",
    "不是 OBS 密钥容器",
    "不能作为提交许可",
    "09-obs-policy.png",
    "storage-backend-20260704T-current.json",
    "production-readiness-20260704T-current.json",
    "storage-backend.json",
    "production-readiness.json",
    "稳定 alias",
    "public bucket",
    "signed URL",
    "完整对象 key",
    "真实宝宝照片",
    "AK/SK",
    "SecretKey",
)
OBS_STORAGE_PACKET_MARKERS = (
    "obs-storage-proof-packet",
    "storage-proof-packet-not-evidence",
    "2026-07-04",
    "XiaoNaiPing",
    "小奶瓶",
    "Backend/deploy/huawei-obs.md",
    "Docs/08_Release/AppStoreEvidence/_templates/obs-policy-evidence.template.json",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260704.json",
    "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
    "Docs/08_Release/AppStoreEvidence/README.md",
    "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
    "Docs/08_Release/AppStoreEvidence/09-obs-policy.pdf",
    "Backend/proof/storage-backend-20260704T-current.json",
    "Backend/proof/production-readiness-20260704T-current.json",
    "Backend/proof/storage-backend.json",
    "Backend/proof/production-readiness.json",
    "evidenceFileChecks",
    "evidenceDependencyMatrix",
    "requiredBeforeSubmit",
    "fileSizeBytes",
    "sha256",
    "FILL_AFTER_CAPTURE",
    "sameRoundAsObsStorageProof",
    "sourceIsAllowedEvidenceRoot",
    "realEvidenceNotTemplate",
    "secretValuesNotRecorded",
    "obsConsoleScreenshot is not storageProof",
    "storageProof is not App Store manual evidence",
    "productionReadinessCurrent is not storageProof alone",
    "stable aliases sync only after current storage, production, and App Store evidence gates are green",
    "no public bucket",
    "no signed URL",
    "no full object key",
    "no real baby photos",
    "Huawei Cloud OBS",
    "private bucket",
    "XiaoNaiPing bucket or prefix",
    "production OBS region",
    "private access policy",
    "server-side upload/download/delete flow",
    "encryption",
    "lifecycle policy",
    "deletion policy",
    "account deletion cleanup",
    "storage proof summary",
    "HUAWEI_OBS_ACCESS_KEY_ID",
    "HUAWEI_OBS_SECRET_ACCESS_KEY",
    "AK/SK",
    "SecretKey",
    "temporary signed URLs",
    "complete object keys",
    "real baby photos",
    "private server paths",
    "account IDs",
    "confirmBucketPolicy",
    "captureObsConsole",
    "refreshStorageProof",
    "refreshAppStoreEvidence",
    "refreshProductionReadiness",
    "syncStableStorageAliases",
    "verify_storage_backend.py --output Backend/proof/storage-backend-20260704T-current.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-07-04",
    "--require-huawei-obs",
    "--require-app-store-evidence",
    "cp Backend/proof/storage-backend-20260704T-current.json Backend/proof/storage-backend.json",
    "cp Backend/proof/production-readiness-20260704T-current.json Backend/proof/production-readiness.json",
    "check_provider_evidence_materials.py",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
    "OBS storage proof is complete only after real 09-obs-policy.png or PDF exists",
    "current storage proof passes",
    "production-readiness.json ready=true",
    "launch-objective-audit.json ready=true",
)
OBS_STORAGE_PACKET_TARGET_EVIDENCE_FILES = {
    "obsPolicyConsole": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
    "obsPolicyConsolePdf": "Docs/08_Release/AppStoreEvidence/09-obs-policy.pdf",
    "storageProof": "Backend/proof/storage-backend-20260704T-current.json",
    "productionReadinessCurrent": "Backend/proof/production-readiness-20260704T-current.json",
    "stableStorageAlias": "Backend/proof/storage-backend.json",
    "stableProductionReadinessAlias": "Backend/proof/production-readiness.json",
}
OBS_STORAGE_PACKET_EVIDENCE_FILE_CHECKS = {
    "obsPolicyConsole": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png or .pdf",
    "storageProof": "Backend/proof/storage-backend-20260704T-current.json",
    "productionReadinessCurrent": "Backend/proof/production-readiness-20260704T-current.json",
    "stableStorageAlias": "Backend/proof/storage-backend.json",
    "stableProductionReadinessAlias": "Backend/proof/production-readiness.json",
}
OBS_STORAGE_PACKET_EVIDENCE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsObsStorageProof", False),
    ("sourceIsAllowedEvidenceRoot", False),
    ("realEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
OBS_STORAGE_PACKET_DEPENDENCY_FIELDS = (
    "artifactId",
    "target",
    "proves",
    "doesNotProve",
    "requiredBeforeSubmit",
    "initialStatus",
)
OBS_STORAGE_PACKET_DEPENDENCY_MATRIX = {
    "obsPolicyConsole": {
        "target": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png or .pdf",
        "proves": [
            "Huawei OBS console shows private bucket or prefix, region, policy, encryption, lifecycle, and deletion posture",
            "OBS console evidence can be inspected without exposing AK/SK, signed URLs, object keys, or baby photos",
        ],
        "doesNotProve": [
            "storage-backend current proof passed",
            "account deletion cleanup passed",
            "production readiness is green",
            "stable storage alias is safe to sync",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "storageProof": {
        "target": "Backend/proof/storage-backend-20260704T-current.json",
        "proves": [
            "same-round storage backend proof passed or records the current storage failure",
            "server-side upload, download, delete, and account deletion cleanup checks were rerun",
        ],
        "doesNotProve": [
            "OBS console evidence was captured",
            "production readiness is green",
            "App Store evidence is complete",
            "stable storage alias is safe to sync by itself",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "productionReadinessCurrent": {
        "target": "Backend/proof/production-readiness-20260704T-current.json",
        "proves": [
            "same-round production readiness result after storage, App Store evidence, auth, and deployment gates",
        ],
        "doesNotProve": [
            "OBS console evidence was captured",
            "storage proof passed by itself",
            "App Store manual evidence is complete",
            "stable aliases were synced safely",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "stableStorageAlias": {
        "target": "Backend/proof/storage-backend.json",
        "proves": [
            "stable storage proof alias was synced from the same-round current storage proof after green gates",
        ],
        "doesNotProve": [
            "current storage proof is fresh if timestamp drifted",
            "production readiness is green",
            "OBS console evidence was captured",
            "App Store submission is allowed",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "stableProductionReadinessAlias": {
        "target": "Backend/proof/production-readiness.json",
        "proves": [
            "stable production readiness alias was synced from the same-round current readiness proof after green gates",
        ],
        "doesNotProve": [
            "current production readiness is fresh if timestamp drifted",
            "storage proof passed independently",
            "App Store evidence is complete",
            "Submit for Review is allowed",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
}
PRODUCTION_PROOF_REFRESH_PACKET_SCALARS = {
    "artifactType": "production-proof-refresh-packet",
    "status": "refresh-plan-not-evidence",
    "date": "2026-07-04",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
    "baseUrl": "https://api.mewpow.com/xiaonaiping",
    "canSubmitFromThisPacket": False,
}
PRODUCTION_PROOF_REFRESH_SOURCE_FILES = {
    "launchBlockerActionPacket": "Docs/08_Release/LAUNCH_BLOCKER_ACTION_PACKET_20260704.md",
    "externalPlatformHandoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "productionConfigExample": "Backend/deploy/production-config.example",
    "runLaunchReadiness": "Backend/scripts/run_launch_readiness.sh",
    "collectDeploymentProof": "Backend/scripts/collect_deployment_proof.py",
    "verifyRemoteApi": "Backend/scripts/verify_remote_api.py",
    "verifyStorageBackend": "Backend/scripts/verify_storage_backend.py",
    "verifyAuthProviders": "Backend/scripts/verify_auth_providers.py",
    "checkAppStoreEvidence": "Backend/scripts/check_app_store_evidence.py",
    "checkProductionReadiness": "Backend/scripts/check_production_readiness.py",
    "checkLaunchObjectiveAudit": "Backend/scripts/check_launch_objective_audit.py",
}
PRODUCTION_PROOF_REFRESH_TARGET_PROOFS = {
    "deploymentProofCurrent": "Backend/proof/huawei-baota-deploy-20260704T-current.json",
    "remoteApiCurrent": "Backend/proof/remote-api-20260704T-current.json",
    "storageBackendCurrent": "Backend/proof/storage-backend-20260704T-current.json",
    "authProvidersConfigCurrent": "Backend/proof/auth-providers-20260704T-current.json",
    "authProvidersSmsLiveCurrent": "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "wechatClientConfigurationCurrent": "Backend/proof/wechat-client-configuration-20260704T-current.json",
    "iosReleaseReadinessCurrent": "Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
    "iosAppBundleCurrent": "Backend/proof/ios-app-bundle-20260704T-current-ios265.json",
    "appStoreEvidenceCurrent": "Backend/proof/app-store-evidence-20260704T-current.json",
    "productionReadinessCurrent": "Backend/proof/production-readiness-20260704T-current.json",
    "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
    "stableDeploymentAlias": "Backend/proof/huawei-baota-deploy.json",
    "stableRemoteApiAlias": "Backend/proof/remote-api.json",
    "stableStorageAlias": "Backend/proof/storage-backend.json",
    "stableAuthProvidersAlias": "Backend/proof/auth-providers.json",
    "stableWechatClientConfigurationAlias": "Backend/proof/wechat-client-configuration.json",
    "stableIosReleaseReadinessAlias": "Backend/proof/ios-release-readiness.json",
    "stableIosAppBundleAlias": "Backend/proof/ios-app-bundle.json",
    "stableAppStoreEvidenceAlias": "Backend/proof/app-store-evidence.json",
    "stableProductionReadinessAlias": "Backend/proof/production-readiness.json",
}
PRODUCTION_PROOF_REFRESH_PROOF_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_REFRESH"),
    ("sha256", "FILL_AFTER_REFRESH"),
    ("generatedInSameRefreshRound", False),
    ("sourceIsExpectedProofPath", False),
    ("currentDateStamped", False),
    ("passedOrReadyVerified", False),
    ("stableAliasSyncedOnlyAfterGreen", False),
    ("realProofNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
PRODUCTION_PROOF_REFRESH_SEPARATION_RULES = (
    "this packet is not deployment proof",
    "this packet is not production readiness",
    "do not copy old 20260627T-current proof into 20260704T-current proof",
    "stable aliases sync only after same-round current proofs pass",
    "do not use simulator evidence as iOS 26.5 real-device proof",
    "do not use provider templates as SMS, WeChat, OBS, App Store, or filing evidence",
    "do not claim Submit for Review until production-readiness.json, app-store-evidence.json, and launch-objective-audit.json are ready=true",
)
PRODUCTION_PROOF_REFRESH_SEQUENCE = (
    ("confirmPrivateProductionEnv", ("XNP_SECRET_KEY", "XNP_DATA_DIR", "xiaonaiping_prod", "XiaoNaiPing production namespace")),
    ("refreshDeploymentProof", ("XNP_DEPLOY_HOST=root@YOUR_SERVER Backend/deploy/deploy-huawei-baota.sh", "Backend/proof/huawei-baota-deploy-20260704T-current.json", "xiaonaiping_app")),
    ("refreshRemoteApiProof", ("verify_remote_api.py", "Backend/proof/remote-api-20260704T-current.json")),
    ("refreshStorageProof", ("verify_storage_backend.py", "Backend/proof/storage-backend-20260704T-current.json")),
    ("refreshAuthProviderConfigProof", ("verify_auth_providers.py --live-check", "Backend/proof/auth-providers-20260704T-current.json")),
    ("refreshWechatClientConfigurationProof", ("check_wechat_client_configuration.py", "Backend/proof/wechat-client-configuration-20260704T-current.json")),
    ("refreshIosReleaseReadinessProof", ("check_ios_release_readiness.py", "Backend/proof/ios-release-readiness-20260704T-current-ios265.json")),
    ("refreshIosAppBundleProof", ("check_ios_app_bundle.py", "Backend/proof/ios-app-bundle-20260704T-current-ios265.json")),
    ("refreshSmsLiveSendProof", ("--send-test-sms", "--require-sms-live-send", "Backend/proof/auth-providers-sms-live-20260704T-current.json")),
    ("refreshAppStoreEvidenceProof", ("check_app_store_evidence.py --allow-incomplete --date 2026-07-04", "Backend/proof/app-store-evidence-20260704T-current.json")),
    ("refreshProductionReadinessCurrent", ("check_production_readiness.py", "--auth-providers-proof Backend/proof/auth-providers-sms-live-20260704T-current.json", "Backend/proof/production-readiness-20260704T-current.json")),
    ("syncStableAliasesAfterGreen", ("cp Backend/proof/huawei-baota-deploy-20260704T-current.json Backend/proof/huawei-baota-deploy.json", "cp Backend/proof/auth-providers-sms-live-20260704T-current.json Backend/proof/auth-providers.json", "cp Backend/proof/wechat-client-configuration-20260704T-current.json Backend/proof/wechat-client-configuration.json", "cp Backend/proof/ios-release-readiness-20260704T-current-ios265.json Backend/proof/ios-release-readiness.json", "cp Backend/proof/ios-app-bundle-20260704T-current-ios265.json Backend/proof/ios-app-bundle.json", "Never sync stable aliases from incomplete current proofs")),
    ("refreshLaunchObjectiveAudit", ("check_launch_objective_audit.py", "Backend/proof/launch-objective-audit.json")),
)
PRODUCTION_PROOF_REFRESH_STOP_CONDITIONS = {
    "noDeployHost": ("wrong server", "Stop production refresh"),
    "missingPrivateEnv": ("xiaonaiping-api.env", "do not create fake local env files"),
    "productionSecretOrDatabaseMissing": ("XNP_SECRET_KEY", "xiaonaiping_prod", "xiaonaiping_app"),
    "obsProofMissingOrStale": ("storage-backend-20260704T-current.json", "syncing stable aliases"),
    "smsLiveSendProofMissing": ("auth-providers-sms-live-20260704T-current.json", "provider configuration proof alone"),
    "wechatProviderMissing": ("real wx AppID/AppSecret", "WeChat Open Platform evidence"),
    "appStoreEvidenceIncomplete": ("app-store-evidence-20260704T-current.json", "Submit for Review readiness"),
    "ios265EvidenceMissing": ("iOS 26.5", "Do not use iOS 27"),
    "productionReadinessStillRed": ("production-readiness-20260704T-current.json", "do not submit"),
}
PRODUCTION_PROOF_REFRESH_POST_GATES = (
    "check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
    "check_launch_blocker_action_packet.py --allow-incomplete --output Backend/proof/launch-blocker-action-packet.json",
    "check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json",
    "check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
PRODUCTION_PROOF_REFRESH_COMPLETION_MARKERS = (
    "refresh-plan-not-evidence",
    "not submission permission",
    "same-day production proof refresh workflow",
    "stable aliases are synced from the same-round current proofs",
    "production-readiness.json ready=true",
    "app-store-evidence.json ready=true",
    "launch-objective-audit.json ready=true",
)
PRODUCTION_PROOF_REFRESH_STATUS_SCALARS = {
    "artifactType": "production-proof-refresh-status",
    "status": "current-proof-status-not-submit-permission",
    "date": "2026-07-04",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
    "baseUrl": "https://api.mewpow.com/xiaonaiping",
    "sourcePlan": str(PRODUCTION_PROOF_REFRESH_PACKET),
    "canSubmitFromThisStatus": False,
}
PRODUCTION_PROOF_REFRESH_STATUS_SUMMARY_FIELDS = (
    "totalProofFiles",
    "existingProofFiles",
    "missingProofFiles",
    "failedProofFiles",
    "secretScanFailures",
    "deploymentProofCurrentExists",
    "authProvidersSmsLiveCurrentExists",
    "stableAliasesBlocked",
)
PRODUCTION_PROOF_REFRESH_STATUS_NEXT_ACTION_MARKERS = (
    "Do not sync stable aliases",
    "production private env",
    "MySQL",
    "Huawei OBS",
    "SMS live send",
    "WeChat AppSecret",
    "App Store Connect",
    "Apple Developer",
    "final screenshots",
    "iOS 26.5 real-device evidence",
)
PRODUCTION_PROOF_REFRESH_STATUS_SCRIPT_MARKERS = (
    "STATUS_ARTIFACT_TYPE",
    "production-proof-refresh-status",
    "STATUS_VALUE",
    "current-proof-status-not-submit-permission",
    "stableAliasSyncAllowed",
    "proofFileStatuses",
    "secretScanFailures",
    "--allow-incomplete",
)
EXTERNAL_PLATFORM_HANDOFF_MARKERS = (
    "微信开放平台证据",
    "08-wechat-open-platform",
    "08b-wechat-universal-link-aasa",
    "wx + 16 hex",
    "Bundle ID：`com.mewpow.xiaonaiping`",
    "URL Scheme equal to AppID",
    "Universal Link：`https://api.mewpow.com/xiaonaiping/wechat/`",
    "短信服务商证据",
    "07-sms-provider",
    "短信签名",
    "账号登录/验证验证码模板",
    "模板审核状态",
    "发送区域",
    "不含营销",
    "不含医疗",
    "不含育儿建议",
    "发送成功记录",
    "真实实发验证",
    "OBS / 存储证据",
    "09-obs-policy",
    "提交前必须刷新当天 storage proof",
    "备案、隐私和 App Store Connect 证据",
    "01-company-account",
    "02-mainland-availability",
    "03-app-filing",
    "04-privacy-label",
    "生产 proof 刷新顺序",
    "XNP_DEPLOY_HOST=root@YOUR_SERVER Backend/deploy/deploy-huawei-baota.sh",
    "iOS 26.5 签名真机包或 iOS 26.5 TestFlight",
    "RD-01 到 RD-24",
    "iOS 27、模拟器、模板文档、空截图、debug code、placeholder `wx...` 都不能替代",
)
PRODUCTION_PROOF_REFRESH_MARKERS = (
    "collect_deployment_proof.py",
    "verify_remote_api.py",
    "verify_storage_backend.py",
    "verify_auth_providers.py",
    "--live-check",
    "--send-test-sms",
    "--require-sms-live-send",
    "check_production_readiness.py",
    "Backend/proof/huawei-baota-deploy-20260704T-current.json",
    "Backend/proof/remote-api-20260704T-current.json",
    "Backend/proof/storage-backend-20260704T-current.json",
    "Backend/proof/auth-providers-20260704T-current.json",
    "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "Backend/proof/production-readiness-20260704T-current.json",
    "--auth-providers-proof Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "cp Backend/proof/huawei-baota-deploy-20260704T-current.json Backend/proof/huawei-baota-deploy-current.json",
    "cp Backend/proof/huawei-baota-deploy-20260704T-current.json Backend/proof/huawei-baota-deploy.json",
    "cp Backend/proof/remote-api-20260704T-current.json Backend/proof/remote-api.json",
    "cp Backend/proof/storage-backend-20260704T-current.json Backend/proof/storage-backend-current.json",
    "cp Backend/proof/storage-backend-20260704T-current.json Backend/proof/storage-backend.json",
    "cp Backend/proof/auth-providers-sms-live-20260704T-current.json Backend/proof/auth-providers.json",
    "cp Backend/proof/ios-app-bundle-20260704T-current-ios265.json Backend/proof/ios-app-bundle.json",
    "cp Backend/proof/app-store-evidence-20260704T-current.json Backend/proof/app-store-evidence.json",
    "cp Backend/proof/production-readiness-20260704T-current.json Backend/proof/production-readiness.json",
    "至少包括 `Backend/proof/huawei-baota-deploy.json`",
    "`Backend/proof/storage-backend.json`",
    "deploymentProofCurrent",
    "storageBackendProofCurrent",
    "authProvidersProofPassed",
    "appStoreManualEvidenceReady",
    "不得写入 root 密码、SSH key、AK/SK、AppSecret、完整手机号或验证码",
)
PROOF_DATE_ROLLOVER_MARKERS = (
    "## Current proof 日期滚动规则",
    "`YYYYMMDDT-current`",
    "以实际执行当天日期生成",
    "2026-07-04",
    "20260704T-current",
    "不得继续把 `20260627T-current` 当成 fresh proof",
    "同一天同一轮",
    "稳定 alias",
    "production-readiness.json",
    "launch-objective-audit.json",
    "如果跨日，先新建当天 current proof，再同步 alias",
    "不要只改文件名",
    "proof 内时间戳",
)
EXTERNAL_PLATFORM_EXECUTION_TEMPLATE_MARKERS = (
    "## 外部平台上线当天执行记录模板",
    "同一天同一轮操作",
    "08-wechat-open-platform.png 已归档",
    "08b-wechat-universal-link-aasa.png 已归档",
    "微信 AppID、URL Scheme、Universal Link 已与 Release 包和服务端 env 对齐",
    "AASA、Associated Domains、Release 包和微信开放平台 Universal Link 已同轮核对",
    "auth-providers-20260704T-current.json 已证明微信 provider",
    "auth-providers-sms-live-20260704T-current.json 已证明真实短信实发",
    "07-sms-provider.png 已归档",
    "verify_auth_providers.py --send-test-sms --require-sms-live-send",
    "09-obs-policy.png 已归档",
    "storage-backend-20260704T-current.json 已通过",
    "01-company-account.png、02-mainland-availability.png、03-app-filing、04-privacy-label 已归档",
    "production-readiness-20260704T-current.json 已变绿",
    "已同步稳定 alias",
    "auth-providers-sms-live-20260704T-current.json",
    "未记录 root 密码、SSH key、AK/SK、AppSecret、完整手机号、验证码、恢复密钥或 token",
    "如果任一项未通过，不提交 App Store Connect 审核",
)
EXTERNAL_PLATFORM_EVIDENCE_INDEX_MARKERS = (
    "## 外部平台证据索引与脱敏复核",
    "07-sms-provider.png",
    "verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE",
    "08-wechat-open-platform.png",
    "08b-wechat-universal-link-aasa.png",
    "Backend/proof/universal-links-20260704T-current.json",
    "Backend/proof/wechat-client-configuration-20260704T-current.json",
    "09-obs-policy.png",
    "Backend/proof/storage-backend-20260704T-current.json",
    "Backend/proof/huawei-baota-deploy-20260704T-current.json",
    "Backend/proof/remote-api-20260704T-current.json",
    "Backend/proof/auth-providers-20260704T-current.json",
    "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "--output Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "Backend/proof/production-readiness-20260704T-current.json",
    "01-company-account.png",
    "02-mainland-availability.png",
    "03-app-filing",
    "04-privacy-label.png",
    "必须保留",
    "必须遮挡",
    "AppSecret",
    "AccessKey",
    "AK/SK",
    "XNP_SMS_SECRET",
    "HUAWEI_OBS_SECRET_ACCESS_KEY",
    "完整手机号",
    "验证码",
    "恢复密钥",
    "check_provider_evidence_materials.py",
    "check_app_store_evidence.py --allow-incomplete",
    "check_production_readiness.py",
    "稳定 alias",
    "不提交 App Store Connect 审核",
)
EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_MARKERS = (
    "# 小奶瓶外部平台现场采集工作台",
    "日期：2026-07-04",
    "这份工作台用于现场采集微信开放平台、短信服务商、OBS、备案、隐私标签和生产 proof",
    "不是提交许可",
    "provider-evidence-materials.json",
    "mainland-filing-materials.json",
    "signed-archive-testflight-materials.json",
    "小奶瓶 required proof 组",
    "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "APP_STORE_CONNECT_COPY_PASTE_20260704.md",
    "APP_STORE_PRIVACY_LABEL.json",
    "AppStoreEvidence/CAPTURE_GUIDE.md",
    "AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260704.md",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "08b-wechat-universal-link-aasa.png",
    "09-obs-policy.png",
    "03-app-filing.png",
    "04-privacy-label.png",
    "12-real-device-regression.md",
    "微信开放平台现场采集",
    "短信服务商现场采集",
    "验证码模板，必须能证明只用于账号登录/验证",
    "模板审核状态和发送区域",
    "模板内容不含营销、不含医疗、不含育儿建议",
    "OBS / 对象存储现场采集",
    "备案、隐私标签和 URL 现场采集",
    "真机/TestFlight 现场联动",
    "最终复跑顺序",
    "禁止项",
    "20260704T-current",
    "huawei-baota-deploy-20260704T-current.json",
    "remote-api-20260704T-current.json",
    "storage-backend-20260704T-current.json",
    "auth-providers-20260704T-current.json",
    "wechat-client-configuration-20260704T-current.json",
    "universal-links-20260704T-current.json",
    "ios-app-bundle-20260704T-current-ios265.json",
    "app-store-evidence-20260704T-current.json",
    "production-readiness-20260704T-current.json",
    "launch-objective-audit-20260704T-current.json",
    "--date 2026-07-04",
    "check_launch_objective_audit.py",
    "check_provider_evidence_materials.py",
    "check_mainland_filing_materials.py",
    "check_signed_archive_testflight_materials.py",
    "不写当前可以提交审核",
    "不把短信 provider 服务器 proof 当成短信服务商截图",
    "不把后台截图当成真机登录 proof",
    "不保存完整手机号、验证码、恢复密钥、AppSecret、AK/SK、token、私钥、证书密码或真实宝宝照片",
)
EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_STALE_MARKERS = (
    "20260627T-current",
    "20260627-current",
    "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260627.md",
    "APP_STORE_CONNECT_COPY_PASTE_20260627.md",
    "AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260627.md",
    "--date 2026-06-27",
    "cross-app-submission-readiness-20260704-current.json",
    "check-cross-app-submit-ready",
    "`canSubmit=true`",
)
SMS_PROVIDER_TEMPLATE_SCALARS = {
    "artifactType": "sms-provider-evidence-template",
    "status": "template-only-not-evidence",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
}
SMS_PROVIDER_TEMPLATE_TARGETS = {
    "smsProvider": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
    "smsLiveProof": "Backend/proof/auth-providers-sms-live-20260704T-current.json",
}
SMS_PROVIDER_TEMPLATE_OBJECT_KEYS = {
    "fieldsToVerify": (
        "providerName",
        "smsSignName",
        "templateCode",
        "templatePurpose",
        "templateAuditStatus",
        "sendRegion",
        "sendResult",
        "recipientPhone",
        "templateBoundary",
    ),
}
SMS_PROVIDER_TEMPLATE_LIST_MARKERS = {
    "doNotRenameThisTemplateTo": (
        "07-sms-provider.json",
        "07-sms-provider.png",
        "07-sms-provider.pdf",
    ),
    "serverProofToRefresh": (
        "Backend/proof/auth-providers-20260704T-current.json",
        "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    ),
    "redactionChecklist": (
        "XNP_SMS_SECRET",
        "AccessKey",
        "complete phone numbers",
        "verification code",
        "provider name",
    ),
}
SMS_PROVIDER_TEMPLATE_POST_CAPTURE_MARKERS = (
    "verify_auth_providers.py --live-check",
    "--send-test-sms",
    "--require-sms-live-send",
    "auth-providers-sms-live-20260704T-current.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-07-04",
)
SMS_PROVIDER_TEMPLATE_COMPLETION_MARKERS = (
    "only a capture worksheet",
    "real 07-sms-provider.png/PDF/JSON evidence",
    "real SMS live-send proof",
    "production auth provider proof",
)
WECHAT_OPEN_PLATFORM_TEMPLATE_SCALARS = {
    "artifactType": "wechat-open-platform-evidence-template",
    "status": "template-only-not-evidence",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
    "bundleId": "com.mewpow.xiaonaiping",
}
WECHAT_OPEN_PLATFORM_TEMPLATE_TARGETS = {
    "mobileApplication": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
    "universalLinkAASA": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
}
WECHAT_OPEN_PLATFORM_TEMPLATE_OBJECT_KEYS = {
    "wechatOpenPlatformFieldsToVerify": (
        "mobileAppName",
        "iosBundleId",
        "appId",
        "urlScheme",
        "universalLink",
        "configurationStatus",
    ),
    "serverOnlySecrets": ("XNP_WECHAT_APP_SECRET",),
}
WECHAT_OPEN_PLATFORM_TEMPLATE_LIST_MARKERS = {
    "doNotRenameThisTemplateTo": (
        "08-wechat-open-platform.json",
        "08-wechat-open-platform.png",
        "08b-wechat-universal-link-aasa.json",
        "08b-wechat-universal-link-aasa.png",
    ),
    "redactionChecklist": (
        "AppSecret",
        "administrator account",
        "complete phone numbers",
        "access tokens",
        "AppID, Bundle ID, URL Scheme, Universal Link",
    ),
}
WECHAT_OPEN_PLATFORM_TEMPLATE_POST_CAPTURE_MARKERS = (
    "check_app_store_evidence.py --allow-incomplete --date 2026-07-04",
    "check_wechat_client_configuration.py",
    "wechat-client-configuration-20260704T-current.json",
    ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260704T-current-ios265.json",
    "check_ios_app_bundle.py",
    "iOS 26.5",
    "verify_auth_providers.py",
    "check_testflight_regression_plan.py",
    "check_production_readiness.py",
    "check_launch_objective_audit.py",
)
WECHAT_OPEN_PLATFORM_TEMPLATE_COMPLETION_MARKERS = (
    "only a capture worksheet",
    "real 08-wechat-open-platform.png",
    "real 08b-wechat-universal-link-aasa.png",
    "real wx AppID",
    "XNP_WECHAT_APP_SECRET",
    "auth-providers-20260704T-current.json",
    "RD-14 iOS 26.5",
    "production-readiness.json",
    "launch-objective-audit.json",
)
OBS_POLICY_TEMPLATE_SCALARS = {
    "artifactType": "obs-policy-evidence-template",
    "status": "template-only-not-evidence",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
}
OBS_POLICY_TEMPLATE_TARGETS = {
    "obsPolicy": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
    "storageProof": "Backend/proof/storage-backend-20260704T-current.json",
}
OBS_POLICY_TEMPLATE_OBJECT_KEYS = {
    "fieldsToVerify": (
        "provider",
        "bucketOrPrefix",
        "region",
        "accessPolicy",
        "serverSideFlow",
        "encryption",
        "lifecycleOrDeletionPolicy",
        "accountDeletionResult",
    ),
}
OBS_POLICY_TEMPLATE_LIST_MARKERS = {
    "doNotRenameThisTemplateTo": (
        "09-obs-policy.json",
        "09-obs-policy.png",
        "09-obs-policy.pdf",
    ),
    "serverProofToRefresh": (
        "Backend/proof/storage-backend-20260704T-current.json",
        "Backend/proof/production-readiness-20260704T-current.json",
    ),
    "redactionChecklist": (
        "HUAWEI_OBS_ACCESS_KEY_ID",
        "HUAWEI_OBS_SECRET_ACCESS_KEY",
        "SecretKey",
        "complete object keys",
        "real baby photos",
        "private server paths",
    ),
}
OBS_POLICY_TEMPLATE_POST_CAPTURE_MARKERS = (
    "verify_storage_backend.py",
    "storage-backend-20260704T-current.json",
    "check_app_store_evidence.py --allow-incomplete --date 2026-07-04",
    "check_production_readiness.py",
    "--require-huawei-obs",
    "--require-app-store-evidence",
)
OBS_POLICY_TEMPLATE_COMPLETION_MARKERS = (
    "only a capture worksheet",
    "real 09-obs-policy.png/PDF/JSON evidence",
    "same-round storage/production proof",
    "account deletion cleanup",
)
EXTERNAL_CAPTURE_PACKET_SCALARS = {
    "artifactType": "external-platform-capture-packet",
    "status": "template-only-not-evidence",
    "date": "2026-07-04",
    "project": "XiaoNaiPing",
    "appName": "小奶瓶",
}
EXTERNAL_CAPTURE_PACKET_SOURCE_FILES = {
    "handoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md",
    "workbench": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_20260704.md",
    "captureGuide": "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
    "appStoreEvidenceReadme": "Docs/08_Release/AppStoreEvidence/README.md",
    "wechatConfiguration": "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md",
    "mainlandFilingMaterials": "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
}
EXTERNAL_CAPTURE_PACKET_ALLOWED_EVIDENCE_ROOT = "Docs/08_Release/AppStoreEvidence/"
EXTERNAL_CAPTURE_PACKET_REQUIREMENTS = (
    "sameDayEvidenceRoundRequired",
    "stableAliasSyncRequired",
    "canSubmitFalseUntilAllEvidenceReady",
    "doNotUseProviderConfigProofAsSmsLiveSendProof",
    "doNotUseConsoleScreenshotsAsRealDeviceProof",
)
EXTERNAL_CAPTURE_PACKET_TARGET_EVIDENCE_FILES = {
    "wechatOpenPlatform": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
    "wechatUniversalLinkAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
    "smsProviderConsole": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
    "huaweiObsPolicy": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
    "mainlandFiling": "Docs/08_Release/AppStoreEvidence/03-app-filing.png",
    "privacyLabel": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
    "productionReadinessCurrent": "Backend/proof/production-readiness-20260704T-current.json",
}
EXTERNAL_CAPTURE_PACKET_EVIDENCE_FILE_CHECK_FIELDS = (
    ("fileSizeBytes", "FILL_AFTER_CAPTURE"),
    ("sha256", "FILL_AFTER_CAPTURE"),
    ("redactionChecked", False),
    ("sameRoundAsExternalPlatformCapture", False),
    ("sourceIsAllowedEvidenceRoot", False),
    ("realEvidenceNotTemplate", False),
    ("secretValuesNotRecorded", False),
)
EXTERNAL_CAPTURE_PACKET_DEPENDENCY_MATRIX = {
    "wechatOpenPlatform": {
        "target": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
        "proves": [
            "WeChat mobile app AppID, Bundle ID, URL Scheme, Universal Link, and configuration status",
            "AppSecret is redacted and server-only",
        ],
        "doesNotProve": [
            "wechat Universal Link AASA evidence",
            "RD-14 real-device WeChat login",
            "auth provider proof",
            "App Store submission readiness",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "wechatUniversalLinkAasa": {
        "target": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
        "proves": [
            "AASA endpoint, Associated Domains, Team ID, Bundle ID, and WeChat Universal Link alignment",
        ],
        "doesNotProve": [
            "WeChat Open Platform mobile app approval",
            "RD-14 real-device WeChat login",
            "auth provider proof",
            "App Store submission readiness",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "smsProviderConsole": {
        "target": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
        "proves": [
            "SMS provider console, approved signature, login verification template, send region, and send record",
            "template has no marketing, medical, feeding advice, or vaccine advice",
        ],
        "doesNotProve": [
            "provider configuration proof",
            "real SMS live-send proof",
            "stable auth alias",
            "App Store submission readiness",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "huaweiObsPolicy": {
        "target": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
        "proves": [
            "Huawei OBS private bucket or prefix, private policy, encryption, lifecycle, and deletion policy",
        ],
        "doesNotProve": [
            "storage backend proof",
            "account deletion cleanup by itself",
            "production readiness",
            "App Store submission readiness",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "mainlandFiling": {
        "target": "Docs/08_Release/AppStoreEvidence/03-app-filing.png",
        "proves": [
            "APP filing, ICP, public security filing, filing number, or applicability decision for XiaoNaiPing",
        ],
        "doesNotProve": [
            "mainland App Store availability",
            "public legal pages are live",
            "App Store privacy label",
            "App Store submission readiness",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "privacyLabel": {
        "target": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
        "proves": [
            "App Store Privacy label page matches APP_STORE_PRIVACY_LABEL.json and Tracking is No",
        ],
        "doesNotProve": [
            "privacy policy URL is live",
            "PrivacyInfo.xcprivacy bundle manifest",
            "production readiness",
            "App Store submission readiness",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
    "productionReadinessCurrent": {
        "target": "Backend/proof/production-readiness-20260704T-current.json",
        "proves": [
            "same-round production readiness proof result after deployment, storage, auth providers, App Store evidence, and stable alias checks",
        ],
        "doesNotProve": [
            "real external platform screenshot files",
            "iOS 26.5 real-device regression",
            "App Store Connect manual evidence by itself",
            "App Store submission readiness unless launch-objective-audit.json is ready=true",
        ],
        "requiredBeforeSubmit": True,
        "initialStatus": "pending",
    },
}
EXTERNAL_CAPTURE_PACKET_DEPENDENCY_MATRIX_SCHEMA = (
    "artifactId",
    "target",
    "proves",
    "doesNotProve",
    "requiredBeforeSubmit",
    "initialStatus",
)
EXTERNAL_CAPTURE_PACKET_CASES = {
    "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png": (
        "wechatOpenPlatform",
        "微信开放平台",
        "wx + 16 hex",
        "Bundle ID",
        "URL Scheme equal to AppID",
        "Universal Link",
        "AppSecret",
        "Backend/proof/wechat-client-configuration-20260704T-current.json",
        "Backend/proof/auth-providers-20260704T-current.json",
    ),
    "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png": (
        "wechatAasa",
        "AASA",
        "Associated Domains",
        "applinks:api.mewpow.com",
        "/xiaonaiping/wechat/",
        "XNPWeChatUniversalLink",
        "Backend/proof/universal-links-20260704T-current.json",
        "Backend/proof/ios-app-bundle-20260704T-current-ios265.json",
    ),
    "Docs/08_Release/AppStoreEvidence/07-sms-provider.png": (
        "smsProvider",
        "短信服务商",
        "账号登录/验证验证码模板",
        "模板审核状态",
        "发送区域",
        "真实实发验证",
        "不含营销",
        "不含医疗",
        "不含育儿建议",
        "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    ),
    "Docs/08_Release/AppStoreEvidence/09-obs-policy.png": (
        "huaweiObs",
        "华为云 OBS",
        "private bucket",
        "bucket 或专用 prefix",
        "私有访问策略",
        "加密",
        "生命周期",
        "删除验证",
        "Backend/proof/storage-backend-20260704T-current.json",
    ),
    "Docs/08_Release/AppStoreEvidence/03-app-filing.png": (
        "mainlandFiling",
        "APP 备案",
        "ICP",
        "公安联网备案",
        "备案通过前不写占位备案号",
        "Backend/proof/mainland-filing-materials.json",
    ),
    "Docs/08_Release/AppStoreEvidence/04-privacy-label.png": (
        "privacyLabel",
        "App Privacy",
        "Tracking 为否",
        "APP_STORE_PRIVACY_LABEL.json",
        "隐私政策 URL",
        "技术支持 URL",
    ),
    "Backend/proof/production-readiness-20260704T-current.json": (
        "productionProof",
        "production readiness",
        "huawei-baota-deploy-20260704T-current.json",
        "remote-api-20260704T-current.json",
        "storage-backend-20260704T-current.json",
        "auth-providers-sms-live-20260704T-current.json",
        "app-store-evidence-20260704T-current.json",
    ),
}
EXTERNAL_CAPTURE_PACKET_TARGETS = tuple(EXTERNAL_CAPTURE_PACKET_CASES)
EXTERNAL_CAPTURE_PACKET_POST_COMMANDS = (
    "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-07-04 --output Backend/proof/app-store-evidence-20260704T-current.json",
    "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260704T-current.json",
    "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
)
EXTERNAL_CAPTURE_PACKET_COMPLETION_MARKERS = (
    "template-only-not-evidence",
    "not submission permission",
    "real external platform evidence files",
    "production-readiness.json ready=true",
    "launch-objective-audit.json ready=true",
    "app-store-evidence.json ready=true",
)
EXTERNAL_CAPTURE_RESULT_TEMPLATE_SCALARS = {
    "status": "template-not-evidence",
    "allowedFinalStatus": "captured-live-external-platforms",
    "doNotTreatAsSubmitPermission": True,
    "project": "XiaoNaiPing",
    "company": "深圳市闪现生活科技有限公司",
    "capturedAt": "",
    "capturedBy": "佘鹏辉 / Penghui She",
    "canSubmitAtCapture": False,
}
EXTERNAL_CAPTURE_RESULT_TEMPLATE_INSTRUCTION_MARKERS = (
    "Copy this file to EXTERNAL-PLATFORM-CAPTURE-RESULT.json",
    "live WeChat Open Platform",
    "SMS provider",
    "OBS",
    "filing",
    "privacy label",
    "live-send evidence",
    "Do not fill secrets",
    "It does not replace screenshots",
    "SMS live-send proof",
    "XiaoNaiPing provider evidence",
    "filing evidence",
    "App Store evidence",
    "production proof",
    "launch objective audit",
    "iOS 26.5 real-device evidence",
    "any historical cross-app status",
    "Cross-app / Emotion Isle proof is historical reference only",
    "cannot replace XiaoNaiPing WeChat",
    "evidenceFileChecks",
    "file size",
    "SHA-256",
    "same-round confirmation",
    "allowed-root confirmation",
    "redaction review result",
)
EXTERNAL_CAPTURE_RESULT_TEMPLATE_CURRENT_PROOFS = {
    "xnpProductionReadiness": "Backend/proof/production-readiness-20260704T-current.json",
    "xnpAppStoreEvidence": "Backend/proof/app-store-evidence-20260704T-current.json",
    "xnpAuthProviders": "Backend/proof/auth-providers-20260704T-current.json",
    "xnpStorageBackend": "Backend/proof/storage-backend-20260704T-current.json",
    "xnpIosBundle": "Backend/proof/ios-app-bundle-20260704T-current-ios265.json",
    "xnpProviderEvidenceMaterials": "Backend/proof/provider-evidence-materials.json",
    "xnpMainlandFilingMaterials": "Backend/proof/mainland-filing-materials.json",
    "xnpSignedArchiveTestFlightMaterials": "Backend/proof/signed-archive-testflight-materials.json",
    "xnpLaunchObjectiveAudit": "Backend/proof/launch-objective-audit-20260704T-current.json",
}
EXTERNAL_CAPTURE_RESULT_TEMPLATE_XNP_REQUIRED_PROOFS = {
    "providerEvidenceMaterials": "Backend/proof/provider-evidence-materials.json",
    "mainlandFilingMaterials": "Backend/proof/mainland-filing-materials.json",
    "authProviders": "Backend/proof/auth-providers.json",
    "storageBackend": "Backend/proof/storage-backend.json",
    "iosAppBundle": "Backend/proof/ios-app-bundle.json",
    "testflightRegressionPlan": "Backend/proof/testflight-regression-plan.json",
    "signedArchiveTestFlightMaterials": "Backend/proof/signed-archive-testflight-materials.json",
    "appStoreEvidence": "Backend/proof/app-store-evidence.json",
    "productionReadiness": "Backend/proof/production-readiness.json",
    "launchObjectiveAudit": "Backend/proof/launch-objective-audit.json",
}
EXTERNAL_CAPTURE_RESULT_TEMPLATE_POST_CAPTURE_RERUNS = {
    "checkProviderEvidenceMaterials": "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "checkMainlandFilingMaterials": "python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "checkAppStoreEvidence": "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-07-04 --output Backend/proof/app-store-evidence-20260704T-current.json",
    "checkProductionReadiness": "python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-20260704T-current.json",
    "checkLaunchObjectiveAudit": "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
    "checkTestFlightRegressionPlan": "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    "checkSignedArchiveTestFlightMaterials": "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
}
EXTERNAL_CAPTURE_RESULT_TEMPLATE_POST_CAPTURE_COMMANDS = (
    "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
    "python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json",
    "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-07-04 --output Backend/proof/app-store-evidence-20260704T-current.json",
    "python3 Backend/scripts/verify_auth_providers.py --live-check --base-url https://api.mewpow.com/xiaonaiping",
    "Backend/proof/auth-providers-20260704T-current.json",
    "python3 Backend/scripts/verify_auth_providers.py --live-check --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE",
    "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping",
    "--auth-providers-proof Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "Backend/proof/production-readiness-20260704T-current.json",
    "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit-20260704T-current.json",
    "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json",
    "python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json",
)
EXTERNAL_CAPTURE_RESULT_TEMPLATE_FORBIDDEN_MARKERS = (
    "cross-app-submission-readiness",
    "check-cross-app-submit-ready",
    "canSubmit=true",
)
EXTERNAL_CAPTURE_RESULT_TEMPLATE_SAME_ROUND_PROOF_LINKS = (
    "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260704.json",
    "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260704.json",
    "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260704.json",
    "Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260704.json",
    "Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260704.json",
    "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260704.json",
    "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "Backend/proof/wechat-client-configuration-20260704T-current.json",
    "Backend/proof/universal-links-20260704T-current.json",
    "Backend/proof/storage-backend-20260704T-current.json",
    "Backend/proof/production-readiness-20260704T-current.json",
)
EXTERNAL_CAPTURE_RESULT_TEMPLATE_FILE_CHECKS = {
    "smsProviderConsole": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
    "wechatOpenPlatform": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
    "wechatUniversalLinkAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
    "smsLiveSendProof": "Backend/proof/auth-providers-sms-live-20260704T-current.json",
    "huaweiObsPolicy": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
    "mainlandFiling": "Docs/08_Release/AppStoreEvidence/03-app-filing.png",
    "privacyLabel": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
    "ageRatingResult": "Docs/08_Release/AppStoreEvidence/17-age-rating-result.png",
}
EXTERNAL_CAPTURE_RESULT_TEMPLATE_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameRoundAsCapture": False,
    "sourceIsAllowedEvidenceRoot": False,
    "secretValuesNotRecorded": False,
}
EXTERNAL_CAPTURE_RESULT_TEMPLATE_SECTIONS = {
    "wechatOpenPlatform": {
        "fileKey": "evidenceFiles",
        "fileMarker": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
        "flags": (
            "appIdVisible",
            "appNameXiaoNaiPingVisible",
            "companyVisible",
            "bundleIdVisible",
            "urlSchemeEqualsAppId",
            "universalLinkVisible",
            "reviewStatusApprovedOrOnline",
            "sameMobileAppAcrossFields",
        ),
    },
    "wechatUniversalLinkAasa": {
        "fileKey": "evidenceFiles",
        "fileMarker": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
        "flags": (
            "newTeamIdAndBundleIdVisible",
            "associatedDomainVisible",
            "aasaResponseVisible",
            "wechatUniversalLinkMatchesReleaseBundle",
        ),
    },
    "smsProvider": {
        "fileKey": "evidenceFiles",
        "fileMarker": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
        "flags": (
            "providerNameVisible",
            "smsSignatureVisible",
            "verificationTemplateVisible",
            "templateApproved",
            "sendRecordVisible",
        ),
    },
    "smsLiveSend": {
        "fileKey": "proofFiles",
        "fileMarker": "Backend/proof/auth-providers-sms-live-20260704T-current.json",
        "flags": (
            "liveSendSucceeded",
            "redactedPhoneVisible",
            "sameTemplateAsProviderScreenshot",
            "sameRoundAsAuthProviderProof",
        ),
    },
    "huaweiObs": {
        "fileKey": "evidenceFiles",
        "fileMarker": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
        "flags": (
            "bucketOrPrefixVisible",
            "privateAccessPolicyVisible",
            "uploadDownloadDeleteProofVisible",
            "accountDeletionObjectCleanupVerified",
        ),
    },
    "mainlandFiling": {
        "fileKey": "evidenceFiles",
        "fileMarker": "Docs/08_Release/AppStoreEvidence/03-app-filing.png",
        "flags": (
            "chinaMainlandVisible",
            "companyVisible",
            "appNameVisible",
            "filingNumberOrApplicabilityVisible",
        ),
    },
    "privacyLabel": {
        "fileKey": "evidenceFiles",
        "fileMarker": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
        "flags": (
            "privacyPolicyUrlVisible",
            "termsUrlVisible",
            "supportUrlVisible",
            "trackingNoVisible",
            "matchesPrivacyLabelJson",
            "noHealthKitOrMedicalDiagnosisClaims",
        ),
    },
    "productionProofs": {
        "flags": (
            "productionReadinessCurrent",
            "authProvidersCurrent",
            "storageBackendCurrent",
            "appStoreEvidenceCurrent",
        ),
    },
    "realDeviceFollowup": {
        "flags": (
            "ios265TestFlight",
            "phoneLogin",
            "wechatLogin",
            "recoveryKeyLogin",
            "cloudSyncAndRestore",
            "accountDelete",
            "notificationPermission",
            "liveActivityAndWidgets",
        ),
    },
}
EXTERNAL_CAPTURE_RESULT_TEMPLATE_REDACTION_FLAGS = (
    "completePhoneHidden",
    "verificationCodesHidden",
    "appSecretHidden",
    "smsSecretsHidden",
    "obsSecretsHidden",
    "tokensHidden",
    "privateObjectKeysHidden",
    "babyPhotosHidden",
    "appleIdEmailHidden",
    "completeDunsHidden",
)
PRE_SUBMIT_COMMAND_MARKERS = (
    "verify_auth_providers.py",
    "verify_storage_backend.py",
    "check_wechat_client_configuration.py",
    "check_provider_evidence_materials.py",
    "check_app_store_evidence.py",
)
FORBIDDEN_COMPLETION_MARKERS = {
    "07-sms-provider": (
        "短信服务商证据已完成",
        "短信 provider 已完成",
        "smsProvider 已完成",
        "07-sms-provider 已完成",
    ),
    "08-wechat-open-platform": (
        "微信开放平台证据已完成",
        "WeChat Open Platform proof complete",
        "wechatOpenPlatform 已完成",
        "08-wechat-open-platform 已完成",
    ),
    "09-obs-policy": (
        "OBS 策略证据已完成",
        "OBS policy proof complete",
        "huaweiObsPolicy 已完成",
        "09-obs-policy 已完成",
    ),
}
FORBIDDEN_SECRET_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<![A-Za-z0-9])1[3-9]\d{9}(?![A-Za-z0-9])"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}(?![A-Za-z0-9])"),
    "plainProviderSecretAssignment": re.compile(
        r"(?:XNP_SMS_SECRET|XNP_WECHAT_APP_SECRET|ALIYUN_ACCESS_KEY_SECRET|HUAWEI_OBS_SECRET_ACCESS_KEY)\s*=\s*(?![<.]|replace-)\S{8,}"
    ),
}
SHA256_JSON_FIELD_PATTERN = re.compile(r'("sha256"\s*:\s*")[0-9a-fA-F]{64}(")')
DIRECT_PHONE_FLAG_PATTERN = re.compile(r"(^|\s)--phone(?!-env)(?:\s|=)")
ACCEPTED_EVIDENCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".json"}
PROVIDER_TEMPLATE_EVIDENCE_FILE_CHECK_PLACEHOLDERS = {
    "fileSizeBytes": "FILL_AFTER_CAPTURE",
    "sha256": "FILL_AFTER_CAPTURE",
    "redactionChecked": False,
    "sameRoundAsTemplateCapture": False,
    "sourceIsAllowedEvidenceRoot": False,
    "realEvidenceNotTemplate": False,
    "secretValuesNotRecorded": False,
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


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def forbidden_secret_hits(text: str) -> list[str]:
    scan_text = SHA256_JSON_FIELD_PATTERN.sub(r"\1<SHA256>\2", text)
    return sorted(name for name, pattern in FORBIDDEN_SECRET_PATTERNS.items() if pattern.search(scan_text))


def as_searchable_text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value or "")


def provider_template_failures(
    label: str,
    template: dict[str, Any] | None,
    *,
    scalars: dict[str, str],
    target_evidence_files: dict[str, str],
    object_keys: dict[str, tuple[str, ...]],
    list_markers: dict[str, tuple[str, ...]],
    post_capture_markers: tuple[str, ...],
    completion_markers: tuple[str, ...],
) -> list[str]:
    if template is None:
        return [f"{label}.template invalid or missing"]

    failures: list[str] = []
    for key, expected in scalars.items():
        if template.get(key) != expected:
            failures.append(f"{label}.{key} != {expected}")

    target_files = template.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        failures.append(f"{label}.targetEvidenceFiles missing")
    else:
        for key, expected in target_evidence_files.items():
            if target_files.get(key) != expected:
                failures.append(f"{label}.targetEvidenceFiles.{key} missing {expected}")

    file_checks = template.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append(f"{label}.evidenceFileChecks missing")
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for check in file_checks:
            if not isinstance(check, dict):
                failures.append(f"{label}.evidenceFileChecks entries must be objects")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append(f"{label}.evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in checks_by_artifact:
                failures.append(f"{label}.evidenceFileChecks duplicate {artifact_id}")
            checks_by_artifact[artifact_id] = check
        if tuple(artifact_order) != tuple(target_evidence_files):
            failures.append(f"{label}.evidenceFileChecks order must match targetEvidenceFiles")
        for artifact_id, expected_target in target_evidence_files.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"{label}.evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != expected_target:
                failures.append(f"{label}.evidenceFileChecks.{artifact_id}.target must be {expected_target}")
            for key, expected in PROVIDER_TEMPLATE_EVIDENCE_FILE_CHECK_PLACEHOLDERS.items():
                if check.get(key) != expected:
                    failures.append(f"{label}.evidenceFileChecks.{artifact_id}.{key} must be {expected!r}")

    for object_name, keys in object_keys.items():
        value = template.get(object_name)
        if not isinstance(value, dict):
            failures.append(f"{label}.{object_name} missing")
            continue
        failures.extend(f"{label}.{object_name}.{key} missing" for key in keys if key not in value)

    for list_name, markers in list_markers.items():
        text = as_searchable_text(template.get(list_name))
        failures.extend(f"{label}.{list_name} missing {marker}" for marker in markers if marker not in text)

    post_capture_text = as_searchable_text(template.get("postCaptureChecks"))
    failures.extend(
        f"{label}.postCaptureChecks missing {marker}"
        for marker in post_capture_markers
        if marker not in post_capture_text
    )

    completion_rule = as_searchable_text(template.get("completionRule"))
    failures.extend(
        f"{label}.completionRule missing {marker}"
        for marker in completion_markers
        if marker not in completion_rule
    )
    return failures


def external_capture_packet_failures(packet: dict[str, Any] | None) -> list[str]:
    if packet is None:
        return ["externalPlatformCapturePacket invalid or missing"]

    failures: list[str] = []
    for key, expected in EXTERNAL_CAPTURE_PACKET_SCALARS.items():
        if packet.get(key) != expected:
            failures.append(f"{key} != {expected}")

    source_files = packet.get("sourceFiles")
    if not isinstance(source_files, dict):
        failures.append("sourceFiles missing")
    else:
        for key, expected in EXTERNAL_CAPTURE_PACKET_SOURCE_FILES.items():
            if source_files.get(key) != expected:
                failures.append(f"sourceFiles.{key} missing {expected}")

    if packet.get("allowedEvidenceRoot") != EXTERNAL_CAPTURE_PACKET_ALLOWED_EVIDENCE_ROOT:
        failures.append(
            "allowedEvidenceRoot must be "
            f"{EXTERNAL_CAPTURE_PACKET_ALLOWED_EVIDENCE_ROOT}"
        )

    requirements_text = as_searchable_text(packet.get("requirements"))
    for marker in EXTERNAL_CAPTURE_PACKET_REQUIREMENTS:
        if marker not in requirements_text:
            failures.append(f"requirements missing {marker}")

    target_files = packet.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        failures.append("targetEvidenceFiles missing")
    else:
        if tuple(target_files) != tuple(EXTERNAL_CAPTURE_PACKET_TARGET_EVIDENCE_FILES):
            failures.append("targetEvidenceFiles order must match external platform capture workflow")
        for key, expected in EXTERNAL_CAPTURE_PACKET_TARGET_EVIDENCE_FILES.items():
            if key not in target_files:
                failures.append(f"targetEvidenceFiles.{key} missing")
            elif target_files.get(key) != expected:
                failures.append(f"targetEvidenceFiles.{key} must be {expected}")

    evidence_checks = packet.get("evidenceFileChecks")
    if not isinstance(evidence_checks, list):
        failures.append("evidenceFileChecks missing")
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
        if tuple(by_artifact) != tuple(EXTERNAL_CAPTURE_PACKET_TARGET_EVIDENCE_FILES):
            failures.append("evidenceFileChecks order must match external platform capture workflow")
        for artifact_id, expected_target in EXTERNAL_CAPTURE_PACKET_TARGET_EVIDENCE_FILES.items():
            check = by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != expected_target:
                failures.append(f"evidenceFileChecks.{artifact_id}.target must be {expected_target}")
            for field, expected in EXTERNAL_CAPTURE_PACKET_EVIDENCE_FILE_CHECK_FIELDS:
                if check.get(field) != expected:
                    failures.append(f"evidenceFileChecks.{artifact_id}.{field} must be {expected!r}")

    dependency_matrix = packet.get("evidenceDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("evidenceDependencyMatrix missing")
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
        if tuple(by_artifact) != tuple(EXTERNAL_CAPTURE_PACKET_DEPENDENCY_MATRIX):
            failures.append("evidenceDependencyMatrix order must match external platform capture workflow")
        for artifact_id, expected in EXTERNAL_CAPTURE_PACKET_DEPENDENCY_MATRIX.items():
            item = by_artifact.get(artifact_id)
            if not isinstance(item, dict):
                failures.append(f"evidenceDependencyMatrix.{artifact_id} missing object")
                continue
            if tuple(item) != EXTERNAL_CAPTURE_PACKET_DEPENDENCY_MATRIX_SCHEMA:
                failures.append(f"evidenceDependencyMatrix.{artifact_id} keys must match dependency schema")
            if item.get("target") != expected["target"]:
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.target must be {expected['target']}")
            for field in ("proves", "doesNotProve"):
                if tuple(item.get(field) or ()) != tuple(expected[field]):
                    failures.append(
                        f"evidenceDependencyMatrix.{artifact_id}.{field} must be "
                        + ", ".join(expected[field])
                    )
            if item.get("requiredBeforeSubmit") is not expected["requiredBeforeSubmit"]:
                failures.append(
                    f"evidenceDependencyMatrix.{artifact_id}.requiredBeforeSubmit must be {expected['requiredBeforeSubmit']}"
                )
            if item.get("initialStatus") != expected["initialStatus"]:
                failures.append(f"evidenceDependencyMatrix.{artifact_id}.initialStatus must be {expected['initialStatus']}")

    cases = packet.get("cases")
    if not isinstance(cases, list):
        return failures + ["cases missing"]

    cases_by_target: dict[str, dict[str, Any]] = {}
    cases_by_id: dict[str, str] = {}
    case_targets: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            failures.append("cases entry is not an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            failures.append("cases entry missing id")
        elif case_id in cases_by_id:
            failures.append(f"cases duplicate id {case_id}")
        else:
            cases_by_id[case_id] = str(case.get("target", ""))
        target = case.get("target")
        if not isinstance(target, str) or not target:
            failures.append("cases entry missing target")
            continue
        case_targets.append(target)
        if target in cases_by_target:
            failures.append(f"cases duplicate {target}")
        cases_by_target[target] = case

    if tuple(case_targets) != EXTERNAL_CAPTURE_PACKET_TARGETS:
        failures.append("cases order must match external platform capture workflow")

    for target, markers in EXTERNAL_CAPTURE_PACKET_CASES.items():
        case = cases_by_target.get(target)
        if not case:
            failures.append(f"cases missing {target}")
            continue
        expected_id = markers[0]
        if case.get("id") != expected_id:
            failures.append(f"{target} id must be {expected_id}")
        case_text = as_searchable_text(case)
        for marker in markers:
            if marker not in case_text:
                failures.append(f"{target} missing {marker}")

    post_capture_text = as_searchable_text(packet.get("postCaptureCommands"))
    for command in EXTERNAL_CAPTURE_PACKET_POST_COMMANDS:
        if command not in post_capture_text:
            failures.append(f"postCaptureCommands missing {command}")

    completion_text = as_searchable_text(packet.get("completionRule"))
    for marker in EXTERNAL_CAPTURE_PACKET_COMPLETION_MARKERS:
        if marker not in completion_text:
            failures.append(f"completionRule missing {marker}")

    secret_hits = forbidden_secret_hits(as_searchable_text(packet))
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def external_capture_result_template_failures(template: dict[str, Any] | None) -> list[str]:
    if template is None:
        return ["externalPlatformCaptureResultTemplate invalid or missing"]

    failures: list[str] = []
    for key, expected in EXTERNAL_CAPTURE_RESULT_TEMPLATE_SCALARS.items():
        if template.get(key) != expected:
            failures.append(f"externalPlatformCaptureResultTemplate.{key} must be {expected!r}")

    instruction_text = as_searchable_text(template.get("instructions"))
    for marker in EXTERNAL_CAPTURE_RESULT_TEMPLATE_INSTRUCTION_MARKERS:
        if marker not in instruction_text:
            failures.append(f"externalPlatformCaptureResultTemplate.instructions missing {marker}")
    template_text = as_searchable_text(template)
    for marker in EXTERNAL_CAPTURE_RESULT_TEMPLATE_FORBIDDEN_MARKERS:
        if marker in template_text:
            failures.append(
                "externalPlatformCaptureResultTemplate must not include stale cross-app submit marker "
                + marker
            )

    current_proofs = template.get("currentProofs")
    if not isinstance(current_proofs, dict):
        failures.append("externalPlatformCaptureResultTemplate.currentProofs missing")
    else:
        for key, expected in EXTERNAL_CAPTURE_RESULT_TEMPLATE_CURRENT_PROOFS.items():
            if current_proofs.get(key) != expected:
                failures.append(f"externalPlatformCaptureResultTemplate.currentProofs.{key} must be {expected}")
    if template.get("xiaonaipingRequiredProofs") != EXTERNAL_CAPTURE_RESULT_TEMPLATE_XNP_REQUIRED_PROOFS:
        failures.append(
            "externalPlatformCaptureResultTemplate.xiaonaipingRequiredProofs must lock XiaoNaiPing provider, filing, auth, storage, iOS, TestFlight, App Store, production, and launch audit proofs"
        )
    if template.get("crossAppDoesNotReplaceXiaoNaiPingProof") is not True:
        failures.append("externalPlatformCaptureResultTemplate.crossAppDoesNotReplaceXiaoNaiPingProof must be true")
    if template.get("postCaptureProofReruns") != EXTERNAL_CAPTURE_RESULT_TEMPLATE_POST_CAPTURE_RERUNS:
        failures.append("externalPlatformCaptureResultTemplate.postCaptureProofReruns must include XiaoNaiPing post-capture proof reruns and signed archive/TestFlight rerun")
    post_capture_commands = template.get("postCaptureRerunCommands")
    if not isinstance(post_capture_commands, list):
        failures.append("externalPlatformCaptureResultTemplate.postCaptureRerunCommands missing")
    else:
        post_capture_command_text = as_searchable_text(post_capture_commands)
        for marker in EXTERNAL_CAPTURE_RESULT_TEMPLATE_POST_CAPTURE_COMMANDS:
            if marker not in post_capture_command_text:
                failures.append(
                    "externalPlatformCaptureResultTemplate.postCaptureRerunCommands missing "
                    + marker
                )

    manifest = template.get("sameRoundEvidenceManifest")
    if not isinstance(manifest, dict):
        failures.append("externalPlatformCaptureResultTemplate.sameRoundEvidenceManifest missing")
    else:
        expected_scalars: dict[str, Any] = {
            "captureRoundId": "xnp-external-platforms-2026-07-04",
            "captureDate": "2026-07-04",
            "hashAlgorithm": "sha256",
            "captureResultSha256": "FILL_AFTER_CAPTURE",
            "allDependenciesCurrentAndPassed": False,
        }
        for key, expected in expected_scalars.items():
            if manifest.get(key) != expected:
                failures.append(
                    f"externalPlatformCaptureResultTemplate.sameRoundEvidenceManifest.{key} must be {expected!r}"
                )
        if tuple(manifest.get("sameRoundProofLinks") or ()) != EXTERNAL_CAPTURE_RESULT_TEMPLATE_SAME_ROUND_PROOF_LINKS:
            failures.append(
                "externalPlatformCaptureResultTemplate.sameRoundEvidenceManifest.sameRoundProofLinks must include external capture, SMS, WeChat, OBS, mainland filing, production refresh, and current proof links in order"
            )
        notes_text = str(manifest.get("notes", ""))
        for marker in ("capturedAt", "file date", "SHA-256", "rerun proof", "capture round"):
            if marker not in notes_text:
                failures.append(
                    f"externalPlatformCaptureResultTemplate.sameRoundEvidenceManifest.notes missing {marker}"
                )

    file_checks = template.get("evidenceFileChecks")
    if not isinstance(file_checks, list):
        failures.append("externalPlatformCaptureResultTemplate.evidenceFileChecks missing")
    else:
        checks_by_artifact: dict[str, dict[str, Any]] = {}
        artifact_order: list[Any] = []
        for check in file_checks:
            if not isinstance(check, dict):
                failures.append("externalPlatformCaptureResultTemplate.evidenceFileChecks entries must be objects")
                continue
            artifact_id = check.get("artifactId")
            artifact_order.append(artifact_id)
            if not isinstance(artifact_id, str):
                failures.append("externalPlatformCaptureResultTemplate.evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in checks_by_artifact:
                failures.append(f"externalPlatformCaptureResultTemplate.evidenceFileChecks duplicate {artifact_id}")
            checks_by_artifact[artifact_id] = check

        expected_artifact_order = tuple(EXTERNAL_CAPTURE_RESULT_TEMPLATE_FILE_CHECKS)
        if tuple(artifact_order) != expected_artifact_order:
            failures.append("externalPlatformCaptureResultTemplate.evidenceFileChecks order must match external evidence workflow")

        for artifact_id, target_marker in EXTERNAL_CAPTURE_RESULT_TEMPLATE_FILE_CHECKS.items():
            check = checks_by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"externalPlatformCaptureResultTemplate.evidenceFileChecks.{artifact_id} missing object")
                continue
            target_text = as_searchable_text(check.get("target"))
            if target_marker not in target_text:
                failures.append(
                    "externalPlatformCaptureResultTemplate.evidenceFileChecks."
                    f"{artifact_id}.target missing {target_marker}"
                )
            for key, expected in EXTERNAL_CAPTURE_RESULT_TEMPLATE_FILE_CHECK_PLACEHOLDERS.items():
                if check.get(key) != expected:
                    failures.append(
                        "externalPlatformCaptureResultTemplate.evidenceFileChecks."
                        f"{artifact_id}.{key} must be {expected!r}"
                    )

    external_platforms = template.get("externalPlatforms")
    if not isinstance(external_platforms, dict):
        failures.append("externalPlatformCaptureResultTemplate.externalPlatforms missing")
    else:
        for section, expected in EXTERNAL_CAPTURE_RESULT_TEMPLATE_SECTIONS.items():
            section_value = external_platforms.get(section)
            if not isinstance(section_value, dict):
                failures.append(f"externalPlatformCaptureResultTemplate.externalPlatforms.{section} missing")
                continue
            file_key = expected.get("fileKey")
            file_marker = expected.get("fileMarker")
            if isinstance(file_key, str) and isinstance(file_marker, str):
                file_text = as_searchable_text(section_value.get(file_key))
                if file_marker not in file_text:
                    failures.append(
                        "externalPlatformCaptureResultTemplate.externalPlatforms."
                        f"{section}.{file_key} missing {file_marker}"
                    )
            for flag in expected.get("flags", ()):
                if section_value.get(flag) is not False:
                    failures.append(
                        "externalPlatformCaptureResultTemplate.externalPlatforms."
                        f"{section}.{flag} must be false in template"
                    )

    redaction_reviewed = template.get("redactionReviewed")
    if not isinstance(redaction_reviewed, dict):
        failures.append("externalPlatformCaptureResultTemplate.redactionReviewed missing")
    else:
        for flag in EXTERNAL_CAPTURE_RESULT_TEMPLATE_REDACTION_FLAGS:
            if redaction_reviewed.get(flag) is not False:
                failures.append(f"externalPlatformCaptureResultTemplate.redactionReviewed.{flag} must be false in template")

    if template.get("operatorNotes") != "":
        failures.append("externalPlatformCaptureResultTemplate.operatorNotes must be empty in template")

    secret_hits = forbidden_secret_hits(as_searchable_text(template))
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def sms_live_send_packet_failures(packet: dict[str, Any] | None) -> list[str]:
    if packet is None:
        return ["smsLiveSendPacket invalid or missing"]

    failures: list[str] = []
    packet_text = as_searchable_text(packet)
    for marker in SMS_LIVE_SEND_PACKET_MARKERS:
        if marker not in packet_text:
            failures.append(f"smsLiveSendPacket missing {marker}")

    local_secret_handling = packet.get("localSecretHandling")
    if not isinstance(local_secret_handling, dict):
        failures.append("smsLiveSendPacket.localSecretHandling missing")
    else:
        for key, expected in SMS_LIVE_SEND_PACKET_LOCAL_SECRET_HANDLING.items():
            value = local_secret_handling.get(key)
            if value != expected:
                if isinstance(expected, list):
                    expected_value = " -> ".join(expected)
                else:
                    expected_value = str(expected)
                failures.append(f"smsLiveSendPacket.localSecretHandling.{key} must be {expected_value}")

    target_files = packet.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        failures.append("smsLiveSendPacket.targetEvidenceFiles missing")
    else:
        if tuple(target_files) != tuple(SMS_LIVE_SEND_PACKET_TARGET_EVIDENCE_FILES):
            failures.append(
                "smsLiveSendPacket.targetEvidenceFiles order must be "
                + " -> ".join(SMS_LIVE_SEND_PACKET_TARGET_EVIDENCE_FILES)
            )
        for key, expected in SMS_LIVE_SEND_PACKET_TARGET_EVIDENCE_FILES.items():
            if key not in target_files:
                failures.append(f"smsLiveSendPacket.targetEvidenceFiles.{key} missing")
            elif target_files.get(key) != expected:
                failures.append(f"smsLiveSendPacket.targetEvidenceFiles.{key} must be {expected}")

    evidence_checks = packet.get("evidenceFileChecks")
    if not isinstance(evidence_checks, list):
        failures.append("smsLiveSendPacket.evidenceFileChecks missing")
    else:
        seen: set[str] = set()
        by_artifact: dict[str, dict[str, Any]] = {}
        for item in evidence_checks:
            if not isinstance(item, dict):
                failures.append("smsLiveSendPacket.evidenceFileChecks entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("smsLiveSendPacket.evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in seen:
                failures.append(f"smsLiveSendPacket.evidenceFileChecks duplicate {artifact_id}")
                continue
            seen.add(artifact_id)
            by_artifact[artifact_id] = item
        expected_ids = tuple(SMS_LIVE_SEND_PACKET_EVIDENCE_FILE_CHECKS)
        if tuple(by_artifact) != expected_ids:
            failures.append(
                "smsLiveSendPacket.evidenceFileChecks order must be "
                + " -> ".join(expected_ids)
            )
        for artifact_id, expected_target in SMS_LIVE_SEND_PACKET_EVIDENCE_FILE_CHECKS.items():
            check = by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"smsLiveSendPacket.evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != expected_target:
                failures.append(
                    f"smsLiveSendPacket.evidenceFileChecks.{artifact_id}.target must be {expected_target}"
                )
            for field, expected in SMS_LIVE_SEND_PACKET_EVIDENCE_FILE_CHECK_FIELDS:
                if check.get(field) != expected:
                    failures.append(
                        f"smsLiveSendPacket.evidenceFileChecks.{artifact_id}.{field} must be {expected!r}"
                    )

    dependency_matrix = packet.get("evidenceDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("smsLiveSendPacket.evidenceDependencyMatrix missing")
    else:
        seen_dependencies: set[str] = set()
        by_dependency_artifact: dict[str, dict[str, Any]] = {}
        for item in dependency_matrix:
            if not isinstance(item, dict):
                failures.append("smsLiveSendPacket.evidenceDependencyMatrix entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("smsLiveSendPacket.evidenceDependencyMatrix entry missing artifactId")
                continue
            if artifact_id in seen_dependencies:
                failures.append(f"smsLiveSendPacket.evidenceDependencyMatrix duplicate {artifact_id}")
                continue
            seen_dependencies.add(artifact_id)
            by_dependency_artifact[artifact_id] = item
        if tuple(by_dependency_artifact) != SMS_LIVE_SEND_PACKET_DEPENDENCY_IDS:
            failures.append(
                "smsLiveSendPacket.evidenceDependencyMatrix order must be "
                + " -> ".join(SMS_LIVE_SEND_PACKET_DEPENDENCY_IDS)
            )
        for artifact_id, expected in SMS_LIVE_SEND_PACKET_DEPENDENCY_MATRIX.items():
            row = by_dependency_artifact.get(artifact_id)
            if not isinstance(row, dict):
                failures.append(f"smsLiveSendPacket.evidenceDependencyMatrix.{artifact_id} missing object")
                continue
            if row.get("target") != expected["target"]:
                failures.append(
                    f"smsLiveSendPacket.evidenceDependencyMatrix.{artifact_id}.target "
                    f"must be {expected['target']}"
                )
            for field in ("proves", "doesNotProve"):
                if row.get(field) != expected[field]:
                    expected_value = json.dumps(expected[field], ensure_ascii=False)
                    failures.append(
                        f"smsLiveSendPacket.evidenceDependencyMatrix.{artifact_id}.{field} "
                        f"must be {expected_value}"
                    )
            for field in ("requiredBeforeAliasSync", "initialStatus"):
                if row.get(field) != expected[field]:
                    failures.append(
                        f"smsLiveSendPacket.evidenceDependencyMatrix.{artifact_id}.{field} "
                        f"must be {expected[field]!r}"
                    )

    execution_order = packet.get("executionOrder")
    if not isinstance(execution_order, list):
        failures.append("smsLiveSendPacket.executionOrder missing")
    else:
        steps = [str(step.get("step")) for step in execution_order if isinstance(step, dict)]
        expected_steps = [
            "confirmProviderTemplate",
            "captureProviderConsole",
            "refreshProviderConfigProof",
            "runRealSmsLiveSend",
            "refreshAppStoreEvidence",
            "syncStableAuthAlias",
        ]
        if steps != expected_steps:
            failures.append("smsLiveSendPacket.executionOrder must be " + " -> ".join(expected_steps))
        by_step = {str(step.get("step")): step for step in execution_order if isinstance(step, dict)}
        run_sms_step = by_step.get("runRealSmsLiveSend")
        if not isinstance(run_sms_step, dict):
            failures.append("smsLiveSendPacket.executionOrder.runRealSmsLiveSend missing")
        else:
            command = run_sms_step.get("command")
            if not isinstance(command, str) or not command:
                failures.append("smsLiveSendPacket.executionOrder.runRealSmsLiveSend.command missing")
            else:
                for marker in SMS_LIVE_SEND_PACKET_REAL_SEND_COMMAND_MARKERS:
                    if marker not in command:
                        failures.append(
                            f"smsLiveSendPacket.executionOrder.runRealSmsLiveSend.command missing {marker}"
                        )
                command_secret_hits = forbidden_secret_hits(command)
                has_literal_phone = any(
                    hit in command_secret_hits for hit in ("mainlandPhoneNumber", "chinaPhoneNumber")
                )
                if DIRECT_PHONE_FLAG_PATTERN.search(command) or has_literal_phone:
                    failures.append(
                        "smsLiveSendPacket.executionOrder.runRealSmsLiveSend.command "
                        "must use --phone-env XNP_SMS_TEST_PHONE and must not use --phone or literal phone numbers"
                    )

    secret_hits = forbidden_secret_hits(packet_text)
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def obs_storage_packet_failures(packet: dict[str, Any] | None) -> list[str]:
    if packet is None:
        return ["obsStorageProofPacket invalid or missing"]

    failures: list[str] = []
    packet_text = as_searchable_text(packet)
    for marker in OBS_STORAGE_PACKET_MARKERS:
        if marker not in packet_text:
            failures.append(f"obsStorageProofPacket missing {marker}")

    target_files = packet.get("targetEvidenceFiles")
    if not isinstance(target_files, dict):
        failures.append("obsStorageProofPacket.targetEvidenceFiles missing")
    else:
        if tuple(target_files) != tuple(OBS_STORAGE_PACKET_TARGET_EVIDENCE_FILES):
            failures.append(
                "obsStorageProofPacket.targetEvidenceFiles order must be "
                + " -> ".join(OBS_STORAGE_PACKET_TARGET_EVIDENCE_FILES)
            )
        for key, expected in OBS_STORAGE_PACKET_TARGET_EVIDENCE_FILES.items():
            if key not in target_files:
                failures.append(f"obsStorageProofPacket.targetEvidenceFiles.{key} missing")
            elif target_files.get(key) != expected:
                failures.append(f"obsStorageProofPacket.targetEvidenceFiles.{key} must be {expected}")

    evidence_checks = packet.get("evidenceFileChecks")
    if not isinstance(evidence_checks, list):
        failures.append("obsStorageProofPacket.evidenceFileChecks missing")
    else:
        seen: set[str] = set()
        by_artifact: dict[str, dict[str, Any]] = {}
        for item in evidence_checks:
            if not isinstance(item, dict):
                failures.append("obsStorageProofPacket.evidenceFileChecks entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("obsStorageProofPacket.evidenceFileChecks entry missing artifactId")
                continue
            if artifact_id in seen:
                failures.append(f"obsStorageProofPacket.evidenceFileChecks duplicate {artifact_id}")
                continue
            seen.add(artifact_id)
            by_artifact[artifact_id] = item
        expected_ids = tuple(OBS_STORAGE_PACKET_EVIDENCE_FILE_CHECKS)
        if tuple(by_artifact) != expected_ids:
            failures.append(
                "obsStorageProofPacket.evidenceFileChecks order must be "
                + " -> ".join(expected_ids)
            )
        for artifact_id, expected_target in OBS_STORAGE_PACKET_EVIDENCE_FILE_CHECKS.items():
            check = by_artifact.get(artifact_id)
            if not isinstance(check, dict):
                failures.append(f"obsStorageProofPacket.evidenceFileChecks.{artifact_id} missing object")
                continue
            if check.get("target") != expected_target:
                failures.append(
                    f"obsStorageProofPacket.evidenceFileChecks.{artifact_id}.target must be {expected_target}"
                )
            for field, expected in OBS_STORAGE_PACKET_EVIDENCE_FILE_CHECK_FIELDS:
                if check.get(field) != expected:
                    failures.append(
                        f"obsStorageProofPacket.evidenceFileChecks.{artifact_id}.{field} must be {expected!r}"
                    )

    dependency_matrix = packet.get("evidenceDependencyMatrix")
    if not isinstance(dependency_matrix, list):
        failures.append("obsStorageProofPacket.evidenceDependencyMatrix missing")
    else:
        seen: set[str] = set()
        by_artifact: dict[str, dict[str, Any]] = {}
        for item in dependency_matrix:
            if not isinstance(item, dict):
                failures.append("obsStorageProofPacket.evidenceDependencyMatrix entries must be objects")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("obsStorageProofPacket.evidenceDependencyMatrix entry missing artifactId")
                continue
            if artifact_id in seen:
                failures.append(f"obsStorageProofPacket.evidenceDependencyMatrix duplicate {artifact_id}")
                continue
            seen.add(artifact_id)
            by_artifact[artifact_id] = item
            if tuple(item) != OBS_STORAGE_PACKET_DEPENDENCY_FIELDS:
                failures.append(
                    f"obsStorageProofPacket.evidenceDependencyMatrix.{artifact_id}.fields must be "
                    + " -> ".join(OBS_STORAGE_PACKET_DEPENDENCY_FIELDS)
                )
        expected_ids = tuple(OBS_STORAGE_PACKET_DEPENDENCY_MATRIX)
        if tuple(by_artifact) != expected_ids:
            failures.append(
                "obsStorageProofPacket.evidenceDependencyMatrix order must be " + " -> ".join(expected_ids)
            )
        for artifact_id, expected in OBS_STORAGE_PACKET_DEPENDENCY_MATRIX.items():
            item = by_artifact.get(artifact_id)
            if not isinstance(item, dict):
                failures.append(f"obsStorageProofPacket.evidenceDependencyMatrix.{artifact_id} missing object")
                continue
            for field, expected_value in expected.items():
                if item.get(field) != expected_value:
                    failures.append(
                        f"obsStorageProofPacket.evidenceDependencyMatrix.{artifact_id}.{field} must be {expected_value}"
                    )

    execution_order = packet.get("executionOrder")
    if not isinstance(execution_order, list):
        failures.append("obsStorageProofPacket.executionOrder missing")
    else:
        steps = [str(step.get("step")) for step in execution_order if isinstance(step, dict)]
        expected_steps = [
            "confirmBucketPolicy",
            "captureObsConsole",
            "refreshStorageProof",
            "refreshAppStoreEvidence",
            "refreshProductionReadiness",
            "syncStableStorageAliases",
        ]
        if steps != expected_steps:
            failures.append("obsStorageProofPacket.executionOrder must be " + " -> ".join(expected_steps))

    secret_hits = forbidden_secret_hits(packet_text)
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def production_proof_refresh_packet_failures(packet: dict[str, Any] | None) -> list[str]:
    if packet is None:
        return ["productionProofRefreshPacket invalid or missing"]

    failures: list[str] = []
    for key, expected in PRODUCTION_PROOF_REFRESH_PACKET_SCALARS.items():
        if packet.get(key) != expected:
            failures.append(f"productionProofRefreshPacket.{key} must be {expected}")

    source_files = packet.get("sourceFiles")
    if not isinstance(source_files, dict):
        failures.append("productionProofRefreshPacket.sourceFiles missing")
    else:
        for key, expected in PRODUCTION_PROOF_REFRESH_SOURCE_FILES.items():
            if source_files.get(key) != expected:
                failures.append(f"productionProofRefreshPacket.sourceFiles.{key} must be {expected}")

    target_proofs = packet.get("targetProofFiles")
    if not isinstance(target_proofs, dict):
        failures.append("productionProofRefreshPacket.targetProofFiles missing")
    else:
        for key, expected in PRODUCTION_PROOF_REFRESH_TARGET_PROOFS.items():
            if target_proofs.get(key) != expected:
                failures.append(f"productionProofRefreshPacket.targetProofFiles.{key} must be {expected}")

    proof_file_checks = packet.get("proofFileChecks")
    if not isinstance(proof_file_checks, list):
        failures.append("productionProofRefreshPacket.proofFileChecks missing")
    else:
        proof_check_order: list[str] = []
        proof_check_by_id: dict[str, dict[str, Any]] = {}
        for item in proof_file_checks:
            if not isinstance(item, dict):
                failures.append("productionProofRefreshPacket.proofFileChecks entry must be an object")
                continue
            artifact_id = item.get("artifactId")
            if not isinstance(artifact_id, str) or not artifact_id:
                failures.append("productionProofRefreshPacket.proofFileChecks entry missing artifactId")
                continue
            if artifact_id in proof_check_by_id:
                failures.append(f"productionProofRefreshPacket.proofFileChecks duplicate {artifact_id}")
            proof_check_by_id[artifact_id] = item
            proof_check_order.append(artifact_id)
        expected_order = tuple(PRODUCTION_PROOF_REFRESH_TARGET_PROOFS)
        if tuple(proof_check_order) != expected_order:
            failures.append("productionProofRefreshPacket.proofFileChecks order must match targetProofFiles")
        for artifact_id, expected_target in PRODUCTION_PROOF_REFRESH_TARGET_PROOFS.items():
            item = proof_check_by_id.get(artifact_id)
            if not item:
                failures.append(f"productionProofRefreshPacket.proofFileChecks.{artifact_id} missing object")
                continue
            if item.get("target") != expected_target:
                failures.append(
                    f"productionProofRefreshPacket.proofFileChecks.{artifact_id}.target must be {expected_target}"
                )
            for field, expected in PRODUCTION_PROOF_REFRESH_PROOF_FILE_CHECK_FIELDS:
                if item.get(field) != expected:
                    failures.append(
                        f"productionProofRefreshPacket.proofFileChecks.{artifact_id}.{field} must be {expected!r}"
                    )

    separation_text = as_searchable_text(packet.get("separationRules"))
    for marker in PRODUCTION_PROOF_REFRESH_SEPARATION_RULES:
        if marker not in separation_text:
            failures.append(f"productionProofRefreshPacket.separationRules missing {marker}")

    refresh_sequence = packet.get("refreshSequence")
    if not isinstance(refresh_sequence, list):
        failures.append("productionProofRefreshPacket.refreshSequence missing")
        refresh_sequence = []
    sequence_steps: list[str] = []
    sequence_by_step: dict[str, dict[str, Any]] = {}
    for item in refresh_sequence:
        if not isinstance(item, dict):
            failures.append("productionProofRefreshPacket.refreshSequence entry must be an object")
            continue
        step = item.get("step")
        if not isinstance(step, str) or not step:
            failures.append("productionProofRefreshPacket.refreshSequence entry missing step")
            continue
        if step in sequence_by_step:
            failures.append(f"productionProofRefreshPacket.refreshSequence duplicate {step}")
        sequence_by_step[step] = item
        sequence_steps.append(step)

    expected_steps = tuple(step for step, _markers in PRODUCTION_PROOF_REFRESH_SEQUENCE)
    if tuple(sequence_steps) != expected_steps:
        failures.append("productionProofRefreshPacket.refreshSequence order must match production proof refresh workflow")
    for step, markers in PRODUCTION_PROOF_REFRESH_SEQUENCE:
        item = sequence_by_step.get(step)
        if not item:
            failures.append(f"productionProofRefreshPacket.refreshSequence missing {step}")
            continue
        item_text = as_searchable_text(item)
        for marker in markers:
            if marker not in item_text:
                failures.append(f"productionProofRefreshPacket.refreshSequence.{step} missing {marker}")

    stop_conditions = packet.get("stopConditions")
    if not isinstance(stop_conditions, list):
        failures.append("productionProofRefreshPacket.stopConditions missing")
        stop_conditions = []
    stop_by_id: dict[str, dict[str, Any]] = {}
    for item in stop_conditions:
        if not isinstance(item, dict):
            failures.append("productionProofRefreshPacket.stopConditions entry must be an object")
            continue
        stop_id = item.get("id")
        if not isinstance(stop_id, str) or not stop_id:
            failures.append("productionProofRefreshPacket.stopConditions entry missing id")
            continue
        if stop_id in stop_by_id:
            failures.append(f"productionProofRefreshPacket.stopConditions duplicate {stop_id}")
        stop_by_id[stop_id] = item
    for stop_id, markers in PRODUCTION_PROOF_REFRESH_STOP_CONDITIONS.items():
        item = stop_by_id.get(stop_id)
        if not item:
            failures.append(f"productionProofRefreshPacket.stopConditions missing {stop_id}")
            continue
        item_text = as_searchable_text(item)
        for marker in markers:
            if marker not in item_text:
                failures.append(f"productionProofRefreshPacket.stopConditions.{stop_id} missing {marker}")

    post_gate_text = as_searchable_text(packet.get("postRefreshGates"))
    for marker in PRODUCTION_PROOF_REFRESH_POST_GATES:
        if marker not in post_gate_text:
            failures.append(f"productionProofRefreshPacket.postRefreshGates missing {marker}")

    completion_text = str(packet.get("completionRule", ""))
    for marker in PRODUCTION_PROOF_REFRESH_COMPLETION_MARKERS:
        if marker not in completion_text:
            failures.append(f"productionProofRefreshPacket.completionRule missing {marker}")

    secret_hits = forbidden_secret_hits(as_searchable_text(packet))
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def production_proof_refresh_status_failures(status: dict[str, Any] | None) -> list[str]:
    if status is None:
        return ["productionProofRefreshStatus invalid or missing"]

    failures: list[str] = []
    for key, expected in PRODUCTION_PROOF_REFRESH_STATUS_SCALARS.items():
        if status.get(key) != expected:
            failures.append(f"productionProofRefreshStatus.{key} must be {expected}")

    stable_alias_sync_allowed = status.get("stableAliasSyncAllowed")
    if not isinstance(stable_alias_sync_allowed, bool):
        failures.append("productionProofRefreshStatus.stableAliasSyncAllowed must be boolean")
        stable_alias_sync_allowed = False

    proof_statuses = status.get("proofFileStatuses")
    proof_status_by_id: dict[str, dict[str, Any]] = {}
    proof_status_order: list[str] = []
    if not isinstance(proof_statuses, list):
        failures.append("productionProofRefreshStatus.proofFileStatuses missing")
        proof_statuses = []
    for item in proof_statuses:
        if not isinstance(item, dict):
            failures.append("productionProofRefreshStatus.proofFileStatuses entry must be an object")
            continue
        artifact_id = item.get("artifactId")
        if not isinstance(artifact_id, str) or not artifact_id:
            failures.append("productionProofRefreshStatus.proofFileStatuses entry missing artifactId")
            continue
        if artifact_id in proof_status_by_id:
            failures.append(f"productionProofRefreshStatus.proofFileStatuses duplicate {artifact_id}")
        proof_status_by_id[artifact_id] = item
        proof_status_order.append(artifact_id)

    expected_order = tuple(PRODUCTION_PROOF_REFRESH_TARGET_PROOFS)
    if tuple(proof_status_order) != expected_order:
        failures.append("productionProofRefreshStatus.proofFileStatuses order must match targetProofFiles")

    missing_from_status: list[str] = []
    failed_from_status: list[dict[str, Any]] = []
    secret_failures_from_status: list[dict[str, Any]] = []
    for artifact_id, expected_target in PRODUCTION_PROOF_REFRESH_TARGET_PROOFS.items():
        item = proof_status_by_id.get(artifact_id)
        if not item:
            failures.append(f"productionProofRefreshStatus.proofFileStatuses.{artifact_id} missing object")
            continue
        if item.get("target") != expected_target:
            failures.append(
                f"productionProofRefreshStatus.proofFileStatuses.{artifact_id}.target must be {expected_target}"
            )
        exists = item.get("exists")
        json_parsed = item.get("jsonParsed")
        current_date_stamped = item.get("currentDateStamped")
        passed_or_ready = item.get("passedOrReadyVerified")
        real_proof_not_template = item.get("realProofNotTemplate")
        secret_values_not_recorded = item.get("secretValuesNotRecorded")
        stable_alias_synced_only_after_green = item.get("stableAliasSyncedOnlyAfterGreen")
        for field, value in (
            ("exists", exists),
            ("jsonParsed", json_parsed),
            ("currentDateStamped", current_date_stamped),
            ("passedOrReadyVerified", passed_or_ready),
            ("realProofNotTemplate", real_proof_not_template),
            ("secretValuesNotRecorded", secret_values_not_recorded),
            ("stableAliasSyncedOnlyAfterGreen", stable_alias_synced_only_after_green),
        ):
            if not isinstance(value, bool):
                failures.append(f"productionProofRefreshStatus.proofFileStatuses.{artifact_id}.{field} must be boolean")

        failed_checks = item.get("failedRequiredChecks")
        if not isinstance(failed_checks, list):
            failures.append(
                f"productionProofRefreshStatus.proofFileStatuses.{artifact_id}.failedRequiredChecks must be list"
            )
            failed_checks = []
        secret_hits = item.get("secretScanHits")
        if not isinstance(secret_hits, list):
            failures.append(
                f"productionProofRefreshStatus.proofFileStatuses.{artifact_id}.secretScanHits must be list"
            )
            secret_hits = []
        if secret_values_not_recorded is not True:
            failures.append(
                f"productionProofRefreshStatus.proofFileStatuses.{artifact_id}.secretValuesNotRecorded must be true"
            )
        if secret_hits:
            failures.append(
                f"productionProofRefreshStatus.proofFileStatuses.{artifact_id}.secretScanHits must be empty"
            )

        if exists is False:
            missing_from_status.append(artifact_id)
            if item.get("fileSizeBytes") != 0:
                failures.append(
                    f"productionProofRefreshStatus.proofFileStatuses.{artifact_id}.fileSizeBytes must be 0 when missing"
                )
            if item.get("sha256") is not None:
                failures.append(
                    f"productionProofRefreshStatus.proofFileStatuses.{artifact_id}.sha256 must be null when missing"
                )
        elif exists is True and (passed_or_ready is not True or failed_checks):
            failed_from_status.append({"artifactId": artifact_id, "failedRequiredChecks": [str(check) for check in failed_checks]})

        if secret_hits:
            secret_failures_from_status.append(
                {"artifactId": artifact_id, "secretScanHits": [str(hit) for hit in secret_hits]}
            )

    current_proof_statuses = [
        proof_status_by_id[artifact_id]
        for artifact_id in PRODUCTION_PROOF_REFRESH_TARGET_PROOFS
        if artifact_id in proof_status_by_id and not artifact_id.startswith("stable")
    ]
    same_round_current_green = bool(current_proof_statuses) and all(
        item.get("exists") is True
        and item.get("jsonParsed") is True
        and item.get("currentDateStamped") is True
        and item.get("passedOrReadyVerified") is True
        and not item.get("failedRequiredChecks")
        and item.get("secretValuesNotRecorded") is True
        for item in current_proof_statuses
    )
    if stable_alias_sync_allowed is not same_round_current_green:
        failures.append("productionProofRefreshStatus.stableAliasSyncAllowed must match same-round current proof green state")

    missing_proofs = status.get("missingProofs")
    if missing_proofs != missing_from_status:
        failures.append("productionProofRefreshStatus.missingProofs must match missing proofFileStatuses")

    failed_proofs = status.get("failedProofs")
    if failed_proofs != failed_from_status:
        failures.append("productionProofRefreshStatus.failedProofs must match failed proofFileStatuses")

    secret_scan_failures = status.get("secretScanFailures")
    if secret_scan_failures != secret_failures_from_status:
        failures.append("productionProofRefreshStatus.secretScanFailures must match proofFileStatuses secret hits")
    if secret_scan_failures:
        failures.append("productionProofRefreshStatus.secretScanFailures must be empty")

    summary = status.get("summary")
    if not isinstance(summary, dict):
        failures.append("productionProofRefreshStatus.summary missing")
    else:
        for field in PRODUCTION_PROOF_REFRESH_STATUS_SUMMARY_FIELDS:
            if field not in summary:
                failures.append(f"productionProofRefreshStatus.summary.{field} missing")
        expected_summary = {
            "totalProofFiles": len(PRODUCTION_PROOF_REFRESH_TARGET_PROOFS),
            "existingProofFiles": len(PRODUCTION_PROOF_REFRESH_TARGET_PROOFS) - len(missing_from_status),
            "missingProofFiles": len(missing_from_status),
            "failedProofFiles": len(failed_from_status),
            "secretScanFailures": len(secret_failures_from_status),
            "deploymentProofCurrentExists": proof_status_by_id.get("deploymentProofCurrent", {}).get("exists") is True,
            "authProvidersSmsLiveCurrentExists": proof_status_by_id.get("authProvidersSmsLiveCurrent", {}).get("exists") is True,
            "stableAliasesBlocked": not same_round_current_green,
        }
        for field, expected in expected_summary.items():
            if summary.get(field) != expected:
                failures.append(f"productionProofRefreshStatus.summary.{field} must be {expected}")

    stable_alias_reason = status.get("stableAliasSyncReason")
    if not isinstance(stable_alias_reason, str) or not stable_alias_reason.strip():
        failures.append("productionProofRefreshStatus.stableAliasSyncReason missing")
    elif same_round_current_green and "may be synced" not in stable_alias_reason:
        failures.append("productionProofRefreshStatus.stableAliasSyncReason must allow sync when current proofs are green")
    elif not same_round_current_green and "do not sync stable aliases" not in stable_alias_reason:
        failures.append("productionProofRefreshStatus.stableAliasSyncReason must block stable alias sync when current proofs are red")

    next_action_text = as_searchable_text(status.get("nextActions"))
    for marker in PRODUCTION_PROOF_REFRESH_STATUS_NEXT_ACTION_MARKERS:
        if marker not in next_action_text:
            failures.append(f"productionProofRefreshStatus.nextActions missing {marker}")

    secret_hits = forbidden_secret_hits(as_searchable_text(status))
    if secret_hits:
        failures.append("secret hits: " + ", ".join(secret_hits))
    return failures


def archived_real_evidence_present(root: Path, stem: str) -> bool:
    evidence_root = root / EVIDENCE_ROOT
    if not evidence_root.exists():
        return False
    for suffix in ACCEPTED_EVIDENCE_SUFFIXES:
        path = evidence_root / f"{stem}{suffix}"
        if path.is_file() and path.stat().st_size > 0:
            return True
    return False


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
    runbook = read_text(root / args.runbook)
    evidence_readme = read_text(root / args.evidence_readme)
    capture_guide = read_text(root / args.capture_guide)
    wechat_doc = read_text(root / args.wechat_client_configuration)
    external_handoff = read_text(root / args.external_platform_handoff)
    external_capture_workbench = read_text(root / args.external_platform_capture_workbench)
    sms_doc = read_text(root / args.sms_adapter_doc)
    sms_adapter_server = read_text(root / args.sms_adapter_server)
    sms_adapter_env_example = read_text(root / args.sms_adapter_env_example)
    sms_adapter_service_example = read_text(root / args.sms_adapter_service_example)
    production_config_example = read_text(root / args.production_config_example)
    obs_doc = read_text(root / args.obs_handoff_doc)
    sms_provider_template_path = root / args.sms_provider_template
    wechat_open_platform_template_path = root / args.wechat_open_platform_template
    obs_policy_template_path = root / args.obs_policy_template
    external_capture_packet_path = root / args.external_platform_capture_packet
    external_capture_result_template_path = root / args.external_platform_capture_result_template
    sms_live_send_packet_path = root / args.sms_live_send_packet
    obs_storage_proof_packet_path = root / args.obs_storage_proof_packet
    production_proof_refresh_packet_path = root / args.production_proof_refresh_packet
    production_proof_refresh_status_path = root / args.production_proof_refresh_status
    production_proof_refresh_status_script_path = root / args.production_proof_refresh_status_script
    sms_provider_template = read_json(sms_provider_template_path)
    wechat_open_platform_template = read_json(wechat_open_platform_template_path)
    obs_policy_template = read_json(obs_policy_template_path)
    external_capture_packet = read_json(external_capture_packet_path)
    external_capture_result_template = read_json(external_capture_result_template_path)
    sms_live_send_packet = read_json(sms_live_send_packet_path)
    obs_storage_proof_packet = read_json(obs_storage_proof_packet_path)
    production_proof_refresh_packet = read_json(production_proof_refresh_packet_path)
    production_proof_refresh_status = read_json(production_proof_refresh_status_path)
    production_proof_refresh_status_script = read_text(production_proof_refresh_status_script_path)
    report = Report()

    report.add("submissionPacketPresent", bool(packet), args.submission_packet if packet else "missing submission packet")
    report.add("chinaRunbookPresent", bool(runbook), args.runbook if runbook else "missing China mainland runbook")
    report.add("evidenceReadmePresent", bool(evidence_readme), args.evidence_readme if evidence_readme else "missing AppStoreEvidence README")
    report.add("captureGuidePresent", bool(capture_guide), args.capture_guide if capture_guide else "missing capture guide")
    report.add("smsAdapterDocPresent", bool(sms_doc), args.sms_adapter_doc if sms_doc else "missing SMS adapter doc")
    report.add("smsAdapterServerPresent", bool(sms_adapter_server), args.sms_adapter_server if sms_adapter_server else "missing SMS adapter server")
    report.add("smsAdapterEnvExamplePresent", bool(sms_adapter_env_example), args.sms_adapter_env_example if sms_adapter_env_example else "missing SMS adapter env example")
    report.add("smsAdapterServiceExamplePresent", bool(sms_adapter_service_example), args.sms_adapter_service_example if sms_adapter_service_example else "missing SMS adapter service example")
    report.add("productionConfigExamplePresent", bool(production_config_example), args.production_config_example if production_config_example else "missing production config example")
    report.add("wechatClientConfigurationPresent", bool(wechat_doc), args.wechat_client_configuration if wechat_doc else "missing WeChat handoff doc")
    report.add("externalPlatformEvidenceHandoffPresent", bool(external_handoff), args.external_platform_handoff if external_handoff else "missing external platform evidence handoff doc")
    report.add(
        "externalPlatformCaptureWorkbenchPresent",
        bool(external_capture_workbench),
        args.external_platform_capture_workbench if external_capture_workbench else "missing external platform capture workbench",
    )
    report.add("obsHandoffDocPresent", bool(obs_doc), args.obs_handoff_doc if obs_doc else "missing OBS handoff doc")
    report.add(
        "smsProviderEvidenceTemplatePresent",
        sms_provider_template_path.is_file(),
        args.sms_provider_template if sms_provider_template_path.is_file() else "missing SMS provider evidence template",
    )
    report.add(
        "wechatOpenPlatformEvidenceTemplatePresent",
        wechat_open_platform_template_path.is_file(),
        args.wechat_open_platform_template if wechat_open_platform_template_path.is_file() else "missing WeChat Open Platform evidence template",
    )
    report.add(
        "huaweiObsEvidenceTemplatePresent",
        obs_policy_template_path.is_file(),
        args.obs_policy_template if obs_policy_template_path.is_file() else "missing Huawei OBS evidence template",
    )
    report.add(
        "externalPlatformCapturePacketPresent",
        external_capture_packet_path.is_file(),
        args.external_platform_capture_packet if external_capture_packet_path.is_file() else "missing external platform capture packet",
    )
    report.add(
        "externalPlatformCaptureResultTemplatePresent",
        external_capture_result_template_path.is_file(),
        args.external_platform_capture_result_template
        if external_capture_result_template_path.is_file()
        else "missing external platform capture result template",
    )
    report.add(
        "smsLiveSendPacketPresent",
        sms_live_send_packet_path.is_file(),
        args.sms_live_send_packet if sms_live_send_packet_path.is_file() else "missing SMS live-send packet",
    )
    report.add(
        "obsStorageProofPacketPresent",
        obs_storage_proof_packet_path.is_file(),
        args.obs_storage_proof_packet if obs_storage_proof_packet_path.is_file() else "missing OBS storage proof packet",
    )
    report.add(
        "productionProofRefreshPacketPresent",
        production_proof_refresh_packet_path.is_file(),
        args.production_proof_refresh_packet
        if production_proof_refresh_packet_path.is_file()
        else "missing production proof refresh packet",
    )
    report.add(
        "productionProofRefreshStatusPresent",
        production_proof_refresh_status_path.is_file(),
        args.production_proof_refresh_status
        if production_proof_refresh_status_path.is_file()
        else "missing production proof refresh status",
    )
    report.add(
        "productionProofRefreshStatusScriptPresent",
        production_proof_refresh_status_script_path.is_file(),
        args.production_proof_refresh_status_script
        if production_proof_refresh_status_script_path.is_file()
        else "missing production proof refresh status script",
    )

    evidence_index_text = evidence_readme + "\n" + capture_guide + "\n" + runbook
    missing_evidence_names = missing_markers(evidence_index_text, EVIDENCE_FILENAME_MARKERS)
    report.add(
        "providerEvidenceFilenamesPresent",
        not missing_evidence_names,
        "missing: " + ", ".join(missing_evidence_names)
        if missing_evidence_names
        else "07 SMS, 08 WeChat, and 09 OBS evidence filenames are documented",
    )

    missing_capture_markers = missing_markers(capture_guide, CAPTURE_GUIDE_MARKERS)
    report.add(
        "providerEvidenceRedactionCovered",
        not missing_capture_markers,
        "missing: " + ", ".join(missing_capture_markers)
        if missing_capture_markers
        else "capture guide covers provider fields to keep and secrets to redact",
    )

    missing_sms_markers = missing_markers(sms_doc + "\n" + capture_guide + "\n" + runbook, SMS_MATERIAL_MARKERS)
    report.add(
        "smsProviderMaterialCoversSignatureTemplateSendAndSecrets",
        not missing_sms_markers,
        "missing: " + ", ".join(missing_sms_markers)
        if missing_sms_markers
        else "SMS material covers signature, template, send success, webhook signing, and secret redaction",
    )
    sms_live_send_text = sms_doc + "\n" + external_handoff + "\n" + external_capture_workbench
    missing_sms_live_send_markers = missing_markers(sms_live_send_text, SMS_LIVE_SEND_PROOF_MARKERS)
    report.add(
        "smsLiveSendProofKeptSeparateFromProviderConfigProof",
        not missing_sms_live_send_markers,
        "missing: " + ", ".join(missing_sms_live_send_markers)
        if missing_sms_live_send_markers
        else "SMS live-send proof is kept separate from provider config proof and the stable auth alias comes from the sms-live proof only after both proofs pass",
    )
    missing_sms_live_send_packet_doc_markers = missing_markers(sms_doc, SMS_LIVE_SEND_PACKET_DOC_MARKERS)
    report.add(
        "smsLiveSendPacketReferenced",
        bool(sms_doc) and not missing_sms_live_send_packet_doc_markers,
        "missing: " + ", ".join(missing_sms_live_send_packet_doc_markers)
        if missing_sms_live_send_packet_doc_markers
        else "SMS adapter handoff points to the structured live-send execution packet and states it is not evidence, not a secret container, and not submission permission",
    )
    missing_sms_runtime_markers = (
        [f"server:{marker}" for marker in missing_markers(sms_adapter_server, SMS_ADAPTER_SERVER_MARKERS)]
        + [f"env:{marker}" for marker in missing_markers(sms_adapter_env_example, SMS_ADAPTER_ENV_MARKERS)]
        + [f"service:{marker}" for marker in missing_markers(sms_adapter_service_example, SMS_ADAPTER_SERVICE_MARKERS)]
        + [f"api-env:{marker}" for marker in missing_markers(production_config_example, SMS_API_ENV_MARKERS)]
    )
    report.add(
        "smsAdapterRuntimeAssetsPresent",
        bool(sms_adapter_server)
        and bool(sms_adapter_env_example)
        and bool(sms_adapter_service_example)
        and bool(production_config_example)
        and not missing_sms_runtime_markers,
        "missing: " + ", ".join(missing_sms_runtime_markers)
        if missing_sms_runtime_markers
        else "SMS adapter runtime assets cover signed webhook verification, Aliyun SendSms, health/send endpoints, mock-off env example, systemd private env, and API webhook env",
    )

    missing_wechat_markers = missing_markers(wechat_doc + "\n" + capture_guide + "\n" + runbook, WECHAT_MATERIAL_MARKERS)
    report.add(
        "wechatOpenPlatformMaterialCoversClientServerSecretBoundary",
        not missing_wechat_markers,
        "missing: " + ", ".join(missing_wechat_markers)
        if missing_wechat_markers
        else "WeChat material covers AppID, Bundle ID, URL Scheme, Universal Link, server AppSecret, and evidence path",
    )
    missing_wechat_aasa_markers = missing_markers(external_handoff + "\n" + evidence_readme + "\n" + capture_guide, WECHAT_UNIVERSAL_LINK_AASA_MARKERS)
    report.add(
        "wechatUniversalLinkAasaEvidenceBoundaryPresent",
        not missing_wechat_aasa_markers,
        "missing: " + ", ".join(missing_wechat_aasa_markers)
        if missing_wechat_aasa_markers
        else "WeChat Universal Link/AASA evidence covers Team ID drift, AASA endpoint, Associated Domains, Release bundle value, callback proof, and redaction boundary",
    )

    missing_obs_markers = missing_markers(obs_doc + "\n" + capture_guide + "\n" + runbook, OBS_MATERIAL_MARKERS)
    report.add(
        "huaweiObsMaterialCoversBucketEncryptionLifecycleDeletion",
        not missing_obs_markers,
        "missing: " + ", ".join(missing_obs_markers)
        if missing_obs_markers
        else "OBS material covers bucket/prefix, region, encryption, lifecycle, deletion validation, and key redaction",
    )
    missing_obs_storage_packet_doc_markers = missing_markers(obs_doc, OBS_STORAGE_PACKET_DOC_MARKERS)
    report.add(
        "obsStorageProofPacketReferenced",
        bool(obs_doc) and not missing_obs_storage_packet_doc_markers,
        "missing: " + ", ".join(missing_obs_storage_packet_doc_markers)
        if missing_obs_storage_packet_doc_markers
        else "OBS handoff points to the structured storage proof execution packet and states it is not evidence, not a secret container, and not submission permission",
    )

    external_provider_template_failures = (
        provider_template_failures(
            "sms",
            sms_provider_template,
            scalars=SMS_PROVIDER_TEMPLATE_SCALARS,
            target_evidence_files=SMS_PROVIDER_TEMPLATE_TARGETS,
            object_keys=SMS_PROVIDER_TEMPLATE_OBJECT_KEYS,
            list_markers=SMS_PROVIDER_TEMPLATE_LIST_MARKERS,
            post_capture_markers=SMS_PROVIDER_TEMPLATE_POST_CAPTURE_MARKERS,
            completion_markers=SMS_PROVIDER_TEMPLATE_COMPLETION_MARKERS,
        )
        + provider_template_failures(
            "wechat",
            wechat_open_platform_template,
            scalars=WECHAT_OPEN_PLATFORM_TEMPLATE_SCALARS,
            target_evidence_files=WECHAT_OPEN_PLATFORM_TEMPLATE_TARGETS,
            object_keys=WECHAT_OPEN_PLATFORM_TEMPLATE_OBJECT_KEYS,
            list_markers=WECHAT_OPEN_PLATFORM_TEMPLATE_LIST_MARKERS,
            post_capture_markers=WECHAT_OPEN_PLATFORM_TEMPLATE_POST_CAPTURE_MARKERS,
            completion_markers=WECHAT_OPEN_PLATFORM_TEMPLATE_COMPLETION_MARKERS,
        )
        + provider_template_failures(
            "obs",
            obs_policy_template,
            scalars=OBS_POLICY_TEMPLATE_SCALARS,
            target_evidence_files=OBS_POLICY_TEMPLATE_TARGETS,
            object_keys=OBS_POLICY_TEMPLATE_OBJECT_KEYS,
            list_markers=OBS_POLICY_TEMPLATE_LIST_MARKERS,
            post_capture_markers=OBS_POLICY_TEMPLATE_POST_CAPTURE_MARKERS,
            completion_markers=OBS_POLICY_TEMPLATE_COMPLETION_MARKERS,
        )
    )
    report.add(
        "externalProviderEvidenceTemplatesValid",
        not external_provider_template_failures,
        "missing: " + ", ".join(external_provider_template_failures)
        if external_provider_template_failures
        else "SMS, WeChat Open Platform, and Huawei OBS evidence templates cover target evidence files, proof outputs, required fields, redaction, post-capture checks, and template-only completion boundaries",
    )
    external_capture_packet_problems = external_capture_packet_failures(external_capture_packet)
    report.add(
        "externalPlatformCapturePacketValid",
        bool(external_capture_packet) and not external_capture_packet_problems,
        "missing: " + ", ".join(external_capture_packet_problems)
        if external_capture_packet_problems
        else "structured external platform capture packet covers WeChat, AASA, SMS, OBS, filing/privacy, production proof, same-day alias sync, redaction, post-capture gates, and template-only evidence boundary",
    )
    external_capture_result_template_problems = external_capture_result_template_failures(
        external_capture_result_template
    )
    report.add(
        "externalPlatformCaptureResultTemplateValid",
        bool(external_capture_result_template) and not external_capture_result_template_problems,
        "missing: " + ", ".join(external_capture_result_template_problems)
        if external_capture_result_template_problems
        else "external platform capture result template indexes same-round WeChat, AASA, SMS, live-send, OBS, filing, privacy label, production proof, iOS 26.5 follow-up, and redaction fields without becoming evidence or submission permission",
    )
    sms_live_send_packet_problems = sms_live_send_packet_failures(sms_live_send_packet)
    report.add(
        "smsLiveSendPacketValid",
        bool(sms_live_send_packet) and not sms_live_send_packet_problems,
        "missing: " + ", ".join(sms_live_send_packet_problems)
        if sms_live_send_packet_problems
        else "structured SMS live-send packet separates provider config proof, real live-send proof, provider console screenshot, stable auth alias sync, redaction, and non-evidence completion boundary",
    )
    obs_storage_packet_problems = obs_storage_packet_failures(obs_storage_proof_packet)
    report.add(
        "obsStorageProofPacketValid",
        bool(obs_storage_proof_packet) and not obs_storage_packet_problems,
        "missing: " + ", ".join(obs_storage_packet_problems)
        if obs_storage_packet_problems
        else "structured OBS storage proof packet separates OBS console evidence, storage proof, production readiness, stable alias sync, redaction, and non-evidence completion boundary",
    )
    production_proof_refresh_packet_problems = production_proof_refresh_packet_failures(production_proof_refresh_packet)
    report.add(
        "productionProofRefreshPacketValid",
        bool(production_proof_refresh_packet) and not production_proof_refresh_packet_problems,
        "missing: " + ", ".join(production_proof_refresh_packet_problems)
        if production_proof_refresh_packet_problems
        else "structured production proof refresh packet pins same-day deployment, remote API, storage, auth, App Store evidence, readiness, stable alias sync, stop conditions, and post-refresh gates",
    )
    missing_status_script_markers = missing_markers(
        production_proof_refresh_status_script,
        PRODUCTION_PROOF_REFRESH_STATUS_SCRIPT_MARKERS,
    )
    report.add(
        "productionProofRefreshStatusScriptReady",
        bool(production_proof_refresh_status_script) and not missing_status_script_markers,
        "missing: " + ", ".join(missing_status_script_markers)
        if missing_status_script_markers
        else "production proof refresh status script can generate same-round current proof status, stable alias sync gates, and secret scan results",
    )
    production_proof_refresh_status_problems = production_proof_refresh_status_failures(
        production_proof_refresh_status
    )
    report.add(
        "productionProofRefreshStatusValid",
        bool(production_proof_refresh_status) and not production_proof_refresh_status_problems,
        "missing: " + ", ".join(production_proof_refresh_status_problems)
        if production_proof_refresh_status_problems
        else "production proof refresh status snapshot is internally consistent, redaction-clean, and blocks stable alias sync until same-round current proofs are green",
    )

    missing_external_handoff_markers = missing_markers(external_handoff, EXTERNAL_PLATFORM_HANDOFF_MARKERS)
    report.add(
        "externalPlatformEvidenceHandoffReady",
        bool(external_handoff) and not missing_external_handoff_markers,
        "missing: " + ", ".join(missing_external_handoff_markers)
        if missing_external_handoff_markers
        else "external platform handoff covers WeChat, SMS, OBS, filing/privacy/App Store evidence, production proof refresh, and iOS 26.5 real-device evidence boundaries",
    )
    missing_production_refresh_markers = missing_markers(external_handoff, PRODUCTION_PROOF_REFRESH_MARKERS)
    report.add(
        "productionProofRefreshPlanCoversCurrentProofs",
        bool(external_handoff) and not missing_production_refresh_markers,
        "missing: " + ", ".join(missing_production_refresh_markers)
        if missing_production_refresh_markers
        else "production proof refresh plan pins deployment, remote API, storage, auth provider, and production-readiness current proof outputs without secrets",
    )
    missing_date_rollover_markers = missing_markers(external_handoff, PROOF_DATE_ROLLOVER_MARKERS)
    report.add(
        "productionProofDateRolloverRulePresent",
        bool(external_handoff) and not missing_date_rollover_markers,
        "missing: " + ", ".join(missing_date_rollover_markers)
        if missing_date_rollover_markers
        else "external platform handoff prevents stale date-specific current proofs from being reused after the run date changes",
    )
    missing_execution_template_markers = missing_markers(external_handoff, EXTERNAL_PLATFORM_EXECUTION_TEMPLATE_MARKERS)
    report.add(
        "externalPlatformSameDayExecutionTemplatePresent",
        bool(external_handoff) and not missing_execution_template_markers,
        "missing: " + ", ".join(missing_execution_template_markers)
        if missing_execution_template_markers
        else "external platform handoff has a same-day execution template tying WeChat, SMS, OBS, App Store evidence, production proof, stable aliases, and redaction into one submission decision",
    )
    missing_evidence_index_markers = missing_markers(external_handoff, EXTERNAL_PLATFORM_EVIDENCE_INDEX_MARKERS)
    report.add(
        "externalPlatformEvidenceIndexAndRedactionReviewPresent",
        bool(external_handoff) and not missing_evidence_index_markers,
        "missing: " + ", ".join(missing_evidence_index_markers)
        if missing_evidence_index_markers
        else "external platform handoff indexes WeChat, SMS, OBS, production proof, App Store evidence, stable aliases, verification commands, and redaction fields before submission",
    )
    missing_capture_workbench_markers = missing_markers(
        external_capture_workbench,
        EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_MARKERS,
    )
    stale_capture_workbench_markers = [
        marker
        for marker in EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_STALE_MARKERS
        if marker in external_capture_workbench
    ]
    capture_workbench_evidence = []
    if missing_capture_workbench_markers:
        capture_workbench_evidence.append("missing: " + ", ".join(missing_capture_workbench_markers))
    if stale_capture_workbench_markers:
        capture_workbench_evidence.append("stale: " + ", ".join(stale_capture_workbench_markers))
    report.add(
        "externalPlatformCaptureWorkbenchCurrent",
        bool(external_capture_workbench)
        and not missing_capture_workbench_markers
        and not stale_capture_workbench_markers,
        "; ".join(capture_workbench_evidence)
        if capture_workbench_evidence
        else "2026-07-04 external platform capture workbench pins same-day proof outputs, cross-app date, evidence filenames, and non-submission boundaries without stale current markers",
    )

    missing_commands = missing_markers(packet + "\n" + runbook, PRE_SUBMIT_COMMAND_MARKERS)
    report.add(
        "preSubmitCommandsIncludeProviderEvidenceGate",
        not missing_commands,
        "missing: " + ", ".join(missing_commands)
        if missing_commands
        else "pre-submit commands include provider evidence material gate and related live provider/storage checks",
    )

    all_materials = "\n".join([
        packet,
        runbook,
        evidence_readme,
        capture_guide,
        wechat_doc,
        external_handoff,
        external_capture_workbench,
        sms_doc,
        sms_adapter_server,
        sms_adapter_env_example,
        sms_adapter_service_example,
        production_config_example,
        obs_doc,
        as_searchable_text(sms_provider_template),
        as_searchable_text(wechat_open_platform_template),
        as_searchable_text(obs_policy_template),
        as_searchable_text(external_capture_packet),
        as_searchable_text(external_capture_result_template),
        as_searchable_text(sms_live_send_packet),
        as_searchable_text(obs_storage_proof_packet),
        as_searchable_text(production_proof_refresh_packet),
        as_searchable_text(production_proof_refresh_status),
        production_proof_refresh_status_script,
    ])
    secret_hits = forbidden_secret_hits(all_materials)
    report.add(
        "providerEvidenceMaterialsDoNotExposeSecrets",
        not secret_hits,
        "found: " + ", ".join(secret_hits)
        if secret_hits
        else "provider evidence materials do not expose recovery keys, tokens, debug codes, API keys, full phone numbers, or literal provider secrets",
    )

    pretend_hits: list[str] = []
    for stem, markers in FORBIDDEN_COMPLETION_MARKERS.items():
        if archived_real_evidence_present(root, stem):
            continue
        pretend_hits.extend(marker for marker in markers if marker in all_materials)
    report.add(
        "doesNotPretendProviderEvidenceCompleteBeforeFiles",
        not pretend_hits,
        "completionClaims=" + ", ".join(pretend_hits)
        if pretend_hits
        else "materials do not claim SMS/WeChat/OBS evidence is complete before archived real evidence files exist",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--submission-packet", default=str(APP_STORE_SUBMISSION_PACKET))
    parser.add_argument("--runbook", default=str(CHINA_MAINLAND_RUNBOOK))
    parser.add_argument("--evidence-readme", default=str(APP_STORE_EVIDENCE_README))
    parser.add_argument("--capture-guide", default=str(APP_STORE_EVIDENCE_CAPTURE_GUIDE))
    parser.add_argument("--wechat-client-configuration", default=str(WECHAT_CLIENT_CONFIGURATION))
    parser.add_argument("--external-platform-handoff", default=str(EXTERNAL_PLATFORM_EVIDENCE_HANDOFF))
    parser.add_argument("--external-platform-capture-workbench", default=str(EXTERNAL_PLATFORM_CAPTURE_WORKBENCH))
    parser.add_argument("--sms-adapter-doc", default=str(SMS_ADAPTER_DOC))
    parser.add_argument("--sms-adapter-server", default=str(SMS_ADAPTER_SERVER))
    parser.add_argument("--sms-adapter-env-example", default=str(SMS_ADAPTER_ENV_EXAMPLE))
    parser.add_argument("--sms-adapter-service-example", default=str(SMS_ADAPTER_SERVICE_EXAMPLE))
    parser.add_argument("--production-config-example", default=str(PRODUCTION_CONFIG_EXAMPLE))
    parser.add_argument("--obs-handoff-doc", default=str(OBS_HANDOFF_DOC))
    parser.add_argument("--sms-provider-template", default=str(SMS_PROVIDER_TEMPLATE))
    parser.add_argument("--wechat-open-platform-template", default=str(WECHAT_OPEN_PLATFORM_TEMPLATE))
    parser.add_argument("--obs-policy-template", default=str(OBS_POLICY_TEMPLATE))
    parser.add_argument("--external-platform-capture-packet", default=str(EXTERNAL_PLATFORM_CAPTURE_PACKET))
    parser.add_argument(
        "--external-platform-capture-result-template",
        default=str(EXTERNAL_PLATFORM_CAPTURE_RESULT_TEMPLATE),
    )
    parser.add_argument("--sms-live-send-packet", default=str(SMS_LIVE_SEND_PACKET))
    parser.add_argument("--obs-storage-proof-packet", default=str(OBS_STORAGE_PROOF_PACKET))
    parser.add_argument("--production-proof-refresh-packet", default=str(PRODUCTION_PROOF_REFRESH_PACKET))
    parser.add_argument("--production-proof-refresh-status", default=str(PRODUCTION_PROOF_REFRESH_STATUS))
    parser.add_argument(
        "--production-proof-refresh-status-script",
        default=str(PRODUCTION_PROOF_REFRESH_STATUS_SCRIPT),
    )
    parser.add_argument("--output", default="Backend/proof/provider-evidence-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"provider evidence materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"provider evidence materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
