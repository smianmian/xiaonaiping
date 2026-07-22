from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_provider_evidence_materials.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_submission_packet() -> str:
    return """
# APP_STORE_SUBMISSION_PACKET.md

## Pre-Submit Commands

```bash
python3 Backend/scripts/verify_auth_providers.py
python3 Backend/scripts/verify_storage_backend.py
python3 Backend/scripts/check_wechat_client_configuration.py
python3 Backend/scripts/check_provider_evidence_materials.py
python3 Backend/scripts/check_app_store_evidence.py
```
""".lstrip()


def valid_runbook() -> str:
    return """
# CHINA_MAINLAND_APP_STORE_RUNBOOK.md

7. `07-sms-provider.png`：短信签名、账号登录/验证验证码模板、模板审核状态、发送区域、验证码发送成功证据；模板不含营销、不含医疗、不含育儿建议，隐藏密钥和手机号中段。
8. `08-wechat-open-platform.png`：微信开放平台移动应用、Bundle ID、URL Scheme / Universal Link 配置证据。
8b. `08b-wechat-universal-link-aasa.png`：AASA、Team ID、Associated Domains、微信 Universal Link 同轮核对证据。
9. `09-obs-policy.png`：OBS bucket、生命周期、加密、删除验证证据，隐藏 AK/SK 和完整对象 key。
""".lstrip()


def valid_evidence_readme() -> str:
    return """
# AppStoreEvidence

| 文件名 | 证明什么 | 脱敏要求 | 当前状态 |
| --- | --- | --- | --- |
| `07-sms-provider.png` | 真实短信服务商、签名、账号登录/验证验证码模板、模板审核状态、发送区域和发送成功；模板不含营销、不含医疗、不含育儿建议 | 手机号中段打码，隐藏密钥 | 未完成 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置 | 可见 AppID、Bundle ID、URL Scheme / Universal Link；隐藏 AppSecret | 未完成 |
| `08b-wechat-universal-link-aasa.png` | AASA、Team ID、Associated Domains、微信 Universal Link 同轮核对 | 可见 AASA endpoint、Team ID、Associated Domains、微信 Universal Link；隐藏 Apple ID 邮箱、完整手机号、AppSecret | 未完成 |
| `09-obs-policy.png` | 华为 OBS bucket、生命周期、加密、删除策略 | 隐藏 AK/SK 和完整对象路径 | 未完成 |
""".lstrip()


def valid_capture_guide() -> str:
    return """
# CAPTURE_GUIDE.md

| 文件 | 必须能证明 | 保留字段 | 必须遮挡 |
|---|---|---|---|
| `07-sms-provider.png` | 真实短信签名、账号登录/验证验证码模板和发送成功；模板不含营销、不含医疗、不含育儿建议 | 服务商、签名、模板 ID/名称、模板审核状态、发送区域、发送成功状态 | AccessKey、Secret、完整手机号、验证码 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置完成 | AppID、Bundle ID、URL Scheme、Universal Link | AppSecret、管理员账号 |
| `08b-wechat-universal-link-aasa.png` | AASA、Team ID、Associated Domains、微信 Universal Link 同轮核对 | AASA endpoint、Team ID、Bundle ID、`applinks:api.mewpow.com`、`/xiaonaiping/wechat/`、`XNPWeChatUniversalLink` | Apple ID 邮箱、完整手机号、AppSecret |
| `09-obs-policy.png` | OBS bucket 私有访问、加密、生命周期、删除验证 | bucket/prefix、区域、加密/生命周期/删除策略状态 | AK/SK、完整对象 key |
""".lstrip()


def valid_sms_doc() -> str:
    return """
# Aliyun SMS Webhook Adapter

小奶瓶 API 用 `XNP_SMS_SECRET` 对 webhook body 做 HMAC-SHA256。adapter 使用阿里云 Dysmsapi `SendSms` 发送验证码。
建议使用只允许 `dysms:SendSms` 的 RAM 子账号。
App Store 证据归档到 `07-sms-provider.png`，必须能看到短信签名、账号登录/验证验证码模板、模板审核状态、发送区域和发送成功；模板不含营销、不含医疗、不含育儿建议；必须遮挡 AccessKey、Secret、完整手机号、验证码和 `XNP_SMS_SECRET`。

## 短信服务商截图字段清单

| 截图/导出项 | 必须保留 | 必须遮挡 |
|---|---|---|
| 短信服务商控制台 | 服务商名称、阿里云 Dysmsapi 或最终生产短信服务商 | 登录账号 |
| 短信签名 | 已审核通过的签名名称和审核状态 | 无关账号信息 |
| 验证码模板 | 模板 ID / 名称、账号登录/验证用途、模板内容摘要、模板审核状态、发送区域；不含营销、不含医疗、不含育儿建议 | 验证码示例明文 |
| 发送成功记录 | 发送成功状态、发送时间、脱敏手机号片段 | 完整手机号、验证码 |
| RAM / 权限边界 | 只允许 `dysms:SendSms` 的最小权限说明 | AccessKey、Secret |
| 小奶瓶服务端 proof | `Backend/proof/auth-providers.json` 中短信 provider / live send 结果 | `XNP_SMS_SECRET`、token、完整手机号 |

真实实发验证必须使用 `verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE` 单独触发；默认 `verify_auth_providers.py --live-check` 只证明 provider 配置存在，不替代短信服务商截图或真实实发截图。
真实实发 proof 输出到 `Backend/proof/auth-providers-sms-live-YYYYMMDDT-current.json`；只有两份 auth provider proof 都通过，且 `07-sms-provider.png` / `.pdf` / `.json` 已归档后，才能同步到 `Backend/proof/auth-providers.json`。

## 真实短信实发执行包

结构化执行包见 `Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260630.json`。该 JSON 只用于上线当天按顺序核对短信服务商截图、provider 配置 proof、真实实发 proof 和稳定 alias 同步；它不是证据、不是短信密钥容器，也不能作为提交许可。

1. `Backend/proof/auth-providers-20260630T-current.json` 只证明 provider 配置存在，不能替代真实实发。
2. `Backend/proof/auth-providers-sms-live-20260630T-current.json` 必须由 `verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE` 单独生成。
3. `07-sms-provider.png` 或 `.pdf` 必须来自短信服务商后台，保留服务商、签名、账号登录/验证模板、模板审核状态、发送区域、发送成功状态和脱敏手机号片段。
4. 模板必须只用于账号登录/验证，不含营销、不含医疗、不含育儿建议。
5. 只有 provider 配置 proof 和 sms-live proof 都通过，并且 `07-sms-provider.*` 已归档后，才能把 `auth-providers-sms-live-20260630T-current.json` 同步到稳定 alias `auth-providers.json`。
6. 全流程不得写入 AccessKey、SecretKey、webhook secret、`XNP_SMS_SECRET`、完整手机号、验证码、token、请求签名或私有后台路径。
""".lstrip()


def valid_sms_adapter_server() -> str:
    return """
const MAX_BODY_BYTES = 16 * 1024;
const DEFAULT_HOST = '127.0.0.1';
const DEFAULT_PORT = 8791;
const DEFAULT_ENDPOINT = 'https://dysmsapi.aliyuncs.com';

function expectedSignature(secret, payload) {
  return crypto.createHmac('sha256', secret).update(payload).digest('hex');
}
function timingSafeEqualHex(left, right) {
  return crypto.timingSafeEqual(Buffer.from(left, 'hex'), Buffer.from(right, 'hex'));
}
function verifyWebhookSignature(secret, body, signature) {
  return true;
}
function normalizeAliyunPhoneNumber(phoneNumber) {
  return phoneNumber;
}
if (process.env.XNP_SMS_ADAPTER_MOCK === '1' || process.env.SMS_MOCK === '1') {}
client.request('SendSms', params, { method: 'POST' });
const result = {};
const response = {
  requestId: result.RequestId || null,
};
maskedPhone(payload && payload.phoneNumber);
if (req.method === 'GET' && req.url === '/healthz') {}
if (req.method === 'POST' && req.url === '/send') {}
const code = 'invalid_signature';
verifyWebhookSignature(secret, body, req.headers['x-xnp-signature']);
""".lstrip()


def valid_sms_adapter_env_example() -> str:
    return """
XNP_SMS_ADAPTER_HOST=127.0.0.1
XNP_SMS_ADAPTER_PORT=8791
XNP_SMS_SECRET=replace-with-same-secret-as-xiaonaiping-api
XNP_SMS_ADAPTER_MOCK=0
ALIYUN_ACCESS_KEY_ID=replace-in-private-deployment
ALIYUN_ACCESS_KEY_SECRET=replace-in-private-deployment
ALIYUN_SIGN_NAME=深圳市闪现生活科技
ALIYUN_TEMPLATE_CODE=SMS_508990073
ALIYUN_REGION_ID=cn-hangzhou
ALIYUN_SMS_ENDPOINT=https://dysmsapi.aliyuncs.com
""".lstrip()


def valid_sms_adapter_service_example() -> str:
    return """
[Unit]
Description=XiaoNaiPing Aliyun SMS Webhook Adapter

[Service]
User=xiaonaiping
Group=xiaonaiping
WorkingDirectory=/srv/xiaonaiping/current/Backend/sms/aliyun-webhook-adapter
EnvironmentFile=/srv/xiaonaiping/private/xiaonaiping-aliyun-sms-adapter.env
ExecStart=/usr/local/bin/node /srv/xiaonaiping/current/Backend/sms/aliyun-webhook-adapter/server.js
Restart=always
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
""".lstrip()


def valid_production_config_example() -> str:
    return """
XNP_SMS_PROVIDER=webhook
XNP_SMS_WEBHOOK_URL=http://127.0.0.1:8791/send
XNP_SMS_SECRET=replace-in-private-deployment
XNP_SMS_TEMPLATE_ID=SMS_508990073
""".lstrip()


def valid_wechat_doc() -> str:
    return """
# WECHAT_CLIENT_CONFIGURATION.md

微信开放平台移动应用 AppID：格式为 `wx + 16 hex`。归档到 `08-wechat-open-platform.png`。
截图要能看到 AppID、Bundle ID、URL Scheme、Universal Link。AppSecret 只配置在服务端，不能写进 iOS 工程或仓库。
""".lstrip()


def valid_external_handoff() -> str:
    return """
# 小奶瓶外部平台证据交接包

## 1. 微信开放平台证据

证据文件：`Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png`
必须可见：AppID，格式为 `wx + 16 hex`。Bundle ID：`com.mewpow.xiaonaiping`。URL Scheme equal to AppID。Universal Link：`https://api.mewpow.com/xiaonaiping/wechat/`。

### 微信 Universal Link / AASA 证据

证据文件：

- `Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png`
- `Backend/proof/universal-links-20260630T-current.json`
- `Backend/proof/wechat-client-configuration-20260630T-current.json`

Apple 新组织 Team ID 获批后，AASA 中的 App ID 使用 `新 Team ID.com.mewpow.xiaonaiping`，不能继续使用旧 Team ID。`https://api.mewpow.com/.well-known/apple-app-site-association` 可访问，返回 `application/json`。AASA 覆盖 `applinks` 和 `/xiaonaiping/wechat/`。Associated Domains 包含 `applinks:api.mewpow.com`。微信开放平台后台 Universal Link 与 iOS Release 包中的 `XNPWeChatUniversalLink` 完全一致。真机微信登录回调从微信回到 App。D-U-N-S 后拿到新 Team ID，必须先更新 AASA、Associated Domains 和 Release 包。

## 2. 短信服务商证据

证据文件：`Docs/08_Release/AppStoreEvidence/07-sms-provider.png`。必须可见短信签名、账号登录/验证验证码模板、模板审核状态、发送区域、发送成功记录和真实实发验证；模板内容不含营销、不含医疗、不含育儿建议。

## 3. OBS / 存储证据

证据文件：`Docs/08_Release/AppStoreEvidence/09-obs-policy.png`。提交前必须刷新当天 storage proof。

## 4. 备案、隐私和 App Store Connect 证据

需要 `01-company-account`、`02-mainland-availability`、`03-app-filing`、`04-privacy-label`。

## 5. 生产 proof 刷新顺序

```bash
XNP_DEPLOY_HOST=root@YOUR_SERVER Backend/deploy/deploy-huawei-baota.sh
python3 Backend/scripts/collect_deployment_proof.py --output Backend/proof/huawei-baota-deploy-20260630T-current.json
python3 Backend/scripts/verify_remote_api.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/remote-api-20260630T-current.json
python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend-20260630T-current.json
python3 Backend/scripts/verify_auth_providers.py --live-check --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/auth-providers-20260630T-current.json --allow-incomplete
python3 Backend/scripts/verify_auth_providers.py --live-check --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/auth-providers-sms-live-20260630T-current.json --allow-incomplete
python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --remote-proof Backend/proof/remote-api-20260630T-current.json --storage-proof Backend/proof/storage-backend-20260630T-current.json --auth-providers-proof Backend/proof/auth-providers-sms-live-20260630T-current.json --require-huawei-obs --require-screenshots --require-app-store-evidence --live-check --output Backend/proof/production-readiness-20260630T-current.json --allow-incomplete
cp Backend/proof/huawei-baota-deploy-20260630T-current.json Backend/proof/huawei-baota-deploy-current.json
cp Backend/proof/huawei-baota-deploy-20260630T-current.json Backend/proof/huawei-baota-deploy.json
cp Backend/proof/remote-api-20260630T-current.json Backend/proof/remote-api.json
cp Backend/proof/storage-backend-20260630T-current.json Backend/proof/storage-backend-current.json
cp Backend/proof/storage-backend-20260630T-current.json Backend/proof/storage-backend.json
cp Backend/proof/auth-providers-sms-live-20260630T-current.json Backend/proof/auth-providers.json
cp Backend/proof/ios-app-bundle-20260630T-current-ios265.json Backend/proof/ios-app-bundle.json
cp Backend/proof/app-store-evidence-20260630T-current.json Backend/proof/app-store-evidence.json
cp Backend/proof/production-readiness-20260630T-current.json Backend/proof/production-readiness.json
```

`Backend/proof/auth-providers-20260630T-current.json` 保留配置 proof 和微信 provider 检查；`Backend/proof/auth-providers-sms-live-20260630T-current.json` 保留真实实发 proof。只有两份 auth provider proof 都通过，且 `07-sms-provider.png` / `.pdf` / `.json` 已归档后，才能把 sms-live proof 同步到稳定 alias。`Backend/proof/auth-providers.json` 必须来自 `Backend/proof/auth-providers-sms-live-20260630T-current.json`，不能来自未实发短信的配置 proof。

同轮 current proof 变绿后，必须同步到稳定 alias，至少包括 `Backend/proof/huawei-baota-deploy.json`、`Backend/proof/remote-api.json`、`Backend/proof/storage-backend.json`、`Backend/proof/auth-providers.json`、`Backend/proof/ios-app-bundle.json`、`Backend/proof/app-store-evidence.json` 和 `Backend/proof/production-readiness.json`。

必须复核 `deploymentProofCurrent`、`storageBackendProofCurrent`、`authProvidersProofPassed` 和 `appStoreManualEvidenceReady`；不得写入 root 密码、SSH key、AK/SK、AppSecret、完整手机号或验证码。

## Current proof 日期滚动规则

`YYYYMMDDT-current` 必须以实际执行当天日期生成。今天是 2026-06-30 时，新的部署、远端 API、storage、auth providers、iOS app bundle、App Store evidence 和 production readiness 输出都应使用 `20260630T-current`；不得继续把 `20260627T-current` 当成 fresh proof。

跨日执行时按这个顺序处理：

1. 先新建当天 `YYYYMMDDT-current` proof，不要只改文件名。
2. 确认 proof 内时间戳、部署时间、storage 验证时间、auth providers 验证时间和人工证据归档时间属于同一天同一轮。
3. 当前轮 `production-readiness.json` 和 `launch-objective-audit.json` 只读取已同步的稳定 alias。
4. 如果跨日，先新建当天 current proof，再同步 alias；不要把旧日期 current 文件复制成新日期文件。
5. 同一天同一轮 proof 变绿后，再同步稳定 alias：`huawei-baota-deploy.json`、`remote-api.json`、`storage-backend.json`、`auth-providers.json`、`ios-app-bundle.json`、`app-store-evidence.json` 和 `production-readiness.json`。
6. 汇报时同时写明 `YYYYMMDDT-current` 文件名和稳定 alias 是否已同步，避免 `production-readiness.json` / `launch-objective-audit.json` 继续读取旧结果。

## 外部平台证据索引与脱敏复核

任一截图、proof 或 alias 缺失时，不提交 App Store Connect 审核。

| 证据 / proof | 必须保留 | 必须遮挡 | 复跑或复核命令 |
|---|---|---|---|
| `07-sms-provider.png` | 短信服务商、签名、账号登录/验证验证码模板、模板审核状态、发送区域、发送成功状态、脱敏手机号片段；模板不含营销、不含医疗、不含育儿建议 | `AccessKey`、Secret、`XNP_SMS_SECRET`、完整手机号、验证码 | `verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE` |
| `08-wechat-open-platform.png` | AppID、Bundle ID、URL Scheme、Universal Link、移动应用审核/配置状态 | `AppSecret`、管理员账号、完整手机号、验证码、token | `check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260630T-current.json` |
| `08b-wechat-universal-link-aasa.png` / `Backend/proof/universal-links-20260630T-current.json` / `Backend/proof/wechat-client-configuration-20260630T-current.json` | Team ID、Bundle ID、AASA endpoint、`applinks:api.mewpow.com`、`/xiaonaiping/wechat/`、`XNPWeChatUniversalLink` | Apple ID 邮箱、完整手机号、`AppSecret`、验证码、token | `check_universal_links.py --output Backend/proof/universal-links-20260630T-current.json` |
| `09-obs-policy.png` / `Backend/proof/storage-backend-20260630T-current.json` | OBS bucket/prefix、区域、私有访问、加密、生命周期、删除验证 | `AK/SK`、`HUAWEI_OBS_SECRET_ACCESS_KEY`、完整对象 key、真实宝宝照片、内部私有路径 | `verify_storage_backend.py --output Backend/proof/storage-backend-20260630T-current.json` |
| `Backend/proof/huawei-baota-deploy-20260630T-current.json` | 服务状态、部署路径、HTTPS base URL、internal 阻断结果、进程/环境字段是否脱敏 | root 密码、SSH key、私有 env 原文、token、恢复密钥 | `collect_deployment_proof.py --output Backend/proof/huawei-baota-deploy-20260630T-current.json` |
| `Backend/proof/remote-api-20260630T-current.json` | 生产 API HTTPS 健康检查、公开接口行为、版本/时间戳 | token、恢复密钥、验证码、完整手机号 | `verify_remote_api.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/remote-api-20260630T-current.json` |
| `Backend/proof/auth-providers-20260630T-current.json` | 手机号 provider、微信 provider、debug code 拒绝、配置 proof | `AppSecret`、`XNP_SMS_SECRET`、完整手机号、验证码、token | `verify_auth_providers.py --live-check --output Backend/proof/auth-providers-20260630T-current.json` |
| `Backend/proof/auth-providers-sms-live-20260630T-current.json` | 手机号 provider、微信 provider、debug code 拒绝、真实实发 proof 和真实短信实发结论 | `AppSecret`、`XNP_SMS_SECRET`、完整手机号、验证码、token | `verify_auth_providers.py --live-check --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE --output Backend/proof/auth-providers-sms-live-20260630T-current.json` |
| `Backend/proof/production-readiness-20260630T-current.json` | `deploymentProofCurrent`、`storageBackendProofCurrent`、`authProvidersProofPassed`、`appStoreManualEvidenceReady` 和最终 `passed` | root 密码、SSH key、`AccessKey`、`AK/SK`、`AppSecret`、完整手机号、验证码 | `check_production_readiness.py --output Backend/proof/production-readiness-20260630T-current.json` |
| `01-company-account.png` / `02-mainland-availability.png` / `03-app-filing` / `04-privacy-label.png` | 公司主体、中国大陆可售区、APP 备案或适用判断、隐私标签填写结果 | Apple ID 邮箱、电话、付款信息、证件细节、D-U-N-S 完整值 | `check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence-20260630T-current.json` |
| 稳定 alias：`Backend/proof/huawei-baota-deploy.json`、`Backend/proof/remote-api.json`、`Backend/proof/storage-backend.json`、`Backend/proof/auth-providers.json`、`Backend/proof/app-store-evidence.json`、`Backend/proof/production-readiness.json` | 必须和同轮 `20260630T-current` proof 同步 | 不保留旧红项、不混入旧日期 proof | `check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json` 后再跑提交包和总 readiness |

## 外部平台上线当天执行记录模板

复制下面清单到当天的私有执行记录或工单中填写；所有项必须来自同一天同一轮操作。

- [ ] 08-wechat-open-platform.png 已归档。
- [ ] 08b-wechat-universal-link-aasa.png 已归档。
- [ ] 微信 AppID、URL Scheme、Universal Link 已与 Release 包和服务端 env 对齐。
- [ ] AASA、Associated Domains、Release 包和微信开放平台 Universal Link 已同轮核对。
- [ ] auth-providers-20260630T-current.json 已证明微信 provider。
- [ ] auth-providers-sms-live-20260630T-current.json 已证明真实短信实发。
- [ ] 07-sms-provider.png 已归档。
- [ ] verify_auth_providers.py --send-test-sms --require-sms-live-send 已完成真实实发验证。
- [ ] 09-obs-policy.png 已归档。
- [ ] storage-backend-20260630T-current.json 已通过。
- [ ] 01-company-account.png、02-mainland-availability.png、03-app-filing、04-privacy-label 已归档。
- [ ] production-readiness-20260630T-current.json 已变绿。
- [ ] 已同步稳定 alias，且 auth-providers.json 来自 auth-providers-sms-live-20260630T-current.json。
- [ ] 未记录 root 密码、SSH key、AK/SK、AppSecret、完整手机号、验证码、恢复密钥或 token。
- [ ] 如果任一项未通过，不提交 App Store Connect 审核。

## 6. 真机 / TestFlight 证据

必须是 iOS 26.5 签名真机包或 iOS 26.5 TestFlight。RD-01 到 RD-24 必须全部通过。iOS 27、模拟器、模板文档、空截图、debug code、placeholder `wx...` 都不能替代。
""".lstrip()


def valid_external_capture_workbench() -> str:
    return """
# 小奶瓶外部平台现场采集工作台

日期：2026-06-30

结论：这份工作台用于现场采集微信开放平台、短信服务商、OBS、备案、隐私标签和生产 proof。它不是提交许可，也不代表这些外部平台已经配置完成；只有小奶瓶自己的 `provider-evidence-materials.json`、`mainland-filing-materials.json`、`signed-archive-testflight-materials.json`、`app-store-evidence.json`、`production-readiness.json`、`launch-objective-audit.json` 和 iOS 26.5 真机回归均通过后，才允许进入 App Store Connect 提交审核。

允许的外部平台文件名：`07-sms-provider.png`、`08-wechat-open-platform.png`、`08b-wechat-universal-link-aasa.png`、`09-obs-policy.png`、`03-app-filing.png`、`04-privacy-label.png`、`12-real-device-regression.md`。

来源文件：

- `Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260630.json`
- `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md`
- `Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260630.md`
- `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json`
- `Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md`
- `Docs/08_Release/AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260630.md`
- `Backend/proof/production-readiness-20260630T-current.json`
- `Backend/proof/provider-evidence-materials.json`
- `Backend/proof/mainland-filing-materials.json`
- `Backend/proof/signed-archive-testflight-materials.json`

结果文件必须记录 `canSubmitAtCapture`、`redactionReviewed`、小奶瓶 required proof 组、各平台截图路径、复跑 proof 和真机联动状态。

## 2. 微信开放平台现场采集

采集后立刻复跑：

```bash
python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260630T-current.json
python3 Backend/scripts/verify_auth_providers.py --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --output Backend/proof/auth-providers-20260630T-current.json --allow-incomplete
```

## 3. Universal Link / AASA 现场采集

```bash
python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links-20260630T-current.json
python3 Backend/scripts/check_ios_app_bundle.py --output Backend/proof/ios-app-bundle-20260630T-current-ios265.json
```

## 4. 短信服务商现场采集

短信 provider 服务器 proof 只能证明后端配置存在，不能替代服务商截图和真实短信实发。
验证码模板，必须能证明只用于账号登录/验证。模板审核状态和发送区域必须可见。模板内容不含营销、不含医疗、不含育儿建议。
真实实发 proof 必须单独保存为 `Backend/proof/auth-providers-sms-live-20260630T-current.json`，并且只有它和 `Backend/proof/auth-providers-20260630T-current.json` 都通过后，才能把 sms-live proof 同步到稳定 alias `Backend/proof/auth-providers.json`。

```bash
python3 Backend/scripts/verify_auth_providers.py --live-check --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --output Backend/proof/auth-providers-sms-live-20260630T-current.json --allow-incomplete
```

## 5. OBS / 对象存储现场采集

```bash
python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend-20260630T-current.json
```

## 6. 备案、隐私标签和 URL 现场采集

小奶瓶不提供医疗诊断。

## 7. 真机/TestFlight 现场联动

iOS 26.5 TestFlight 和 12-real-device-regression.md 必须补齐。

## 8. 最终复跑顺序

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json
python3 Backend/scripts/check_production_readiness.py --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --remote-proof Backend/proof/remote-api-20260630T-current.json --storage-proof Backend/proof/storage-backend-20260630T-current.json --auth-providers-proof Backend/proof/auth-providers-sms-live-20260630T-current.json --ios-app-bundle-proof Backend/proof/ios-app-bundle-20260630T-current-ios265.json --app-store-evidence Backend/proof/app-store-evidence-20260630T-current.json --output Backend/proof/production-readiness-20260630T-current.json --allow-incomplete
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit-20260630T-current.json
python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json
python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json
python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json
```

## 9. 禁止项

- 不写当前可以提交审核。
- 不把短信 provider 服务器 proof 当成短信服务商截图。
- 不把后台截图当成真机登录 proof。
- 不保存完整手机号、验证码、恢复密钥、AppSecret、AK/SK、token、私钥、证书密码或真实宝宝照片。
""".lstrip()


def valid_obs_doc() -> str:
    return """
# Huawei Cloud OBS Handoff

Use a private bucket. Keep server-side AK/SK only on the backend host.
App Store 证据归档到 `09-obs-policy.png`，必须能看到 bucket、prefix、区域、加密、生命周期和删除验证；必须遮挡 AK/SK 和完整对象 key。

## OBS 私有访问与删除验证执行包

结构化执行包见 `Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260630.json`。该 JSON 只用于上线当天按顺序核对 OBS 后台截图、storage proof、production readiness 和稳定 alias 同步；它不是证据、不是 OBS 密钥容器，也不能作为提交许可。

1. `09-obs-policy.png` 只证明后台截图，不等于 `Backend/proof/storage-backend-20260630T-current.json`。
2. `production-readiness-20260630T-current.json` 必须同轮读取 storage proof。
3. 变绿后同步 `Backend/proof/storage-backend.json` 和 `Backend/proof/production-readiness.json` 稳定 alias。
4. 不保存 public bucket、signed URL、完整对象 key、真实宝宝照片、AK/SK 或 SecretKey。
""".lstrip()


def template_evidence_file_checks(target_files: dict[str, str]) -> list[dict[str, object]]:
    return [
        {
            "artifactId": artifact_id,
            "target": target,
            "fileSizeBytes": "FILL_AFTER_CAPTURE",
            "sha256": "FILL_AFTER_CAPTURE",
            "redactionChecked": False,
            "sameRoundAsTemplateCapture": False,
            "sourceIsAllowedEvidenceRoot": False,
            "realEvidenceNotTemplate": False,
            "secretValuesNotRecorded": False,
        }
        for artifact_id, target in target_files.items()
    ]


def external_capture_evidence_file_checks(target_files: dict[str, str]) -> list[dict[str, object]]:
    return [
        {
            "artifactId": artifact_id,
            "target": target,
            "fileSizeBytes": "FILL_AFTER_CAPTURE",
            "sha256": "FILL_AFTER_CAPTURE",
            "redactionChecked": False,
            "sameRoundAsExternalPlatformCapture": False,
            "sourceIsAllowedEvidenceRoot": False,
            "realEvidenceNotTemplate": False,
            "secretValuesNotRecorded": False,
        }
        for artifact_id, target in target_files.items()
    ]


def valid_sms_provider_template() -> str:
    target_files = {
        "smsProvider": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
        "smsLiveProof": "Backend/proof/auth-providers-sms-live-20260630T-current.json",
    }
    return json.dumps(
        {
            "artifactType": "sms-provider-evidence-template",
            "status": "template-only-not-evidence",
            "project": "XiaoNaiPing",
            "appName": "小奶瓶",
            "targetEvidenceFiles": target_files,
            "evidenceFileChecks": template_evidence_file_checks(target_files),
            "doNotRenameThisTemplateTo": [
                "07-sms-provider.json",
                "07-sms-provider.png",
                "07-sms-provider.pdf",
            ],
            "fieldsToVerify": {
                "providerName": "阿里云 Dysmsapi or the current production SMS provider",
                "smsSignName": "approved account-login/verification SMS signature",
                "templateCode": "approved verification-code template ID",
                "templatePurpose": "account login / verification only",
                "templateAuditStatus": "approved",
                "sendRegion": "China mainland or the configured production send region",
                "sendResult": "at least one successful real send",
                "recipientPhone": "masked middle digits",
                "templateBoundary": "no marketing, no medical wording, no feeding advice, no vaccine advice",
            },
            "serverProofToRefresh": [
                "Backend/proof/auth-providers-20260630T-current.json",
                "Backend/proof/auth-providers-sms-live-20260630T-current.json",
            ],
            "redactionChecklist": [
                "Hide XNP_SMS_SECRET",
                "Hide webhook secret",
                "Hide AccessKey and SecretKey",
                "Hide complete phone numbers",
                "Hide verification code values",
                "Hide tokens, request signatures, and private backend paths",
                "Keep provider name, signature, template ID/name, audit status, send region, and successful send state visible",
            ],
            "postCaptureChecks": [
                "python3 Backend/scripts/verify_auth_providers.py --live-check --base-url https://api.mewpow.com/xiaonaiping --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --output Backend/proof/auth-providers-20260630T-current.json --allow-incomplete",
                "python3 Backend/scripts/verify_auth_providers.py --live-check --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE --base-url https://api.mewpow.com/xiaonaiping --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --output Backend/proof/auth-providers-sms-live-20260630T-current.json --allow-incomplete",
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
            ],
            "completionRule": "This template is only a capture worksheet. The App Store evidence gate remains incomplete until real 07-sms-provider.png/PDF/JSON evidence exists, the real SMS live-send proof passes, and the production auth provider proof is refreshed in the same evidence round.",
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def valid_sms_live_send_packet() -> str:
    return json.dumps(
        {
            "artifactType": "sms-provider-live-send-packet",
            "status": "live-send-packet-not-evidence",
            "date": "2026-06-30",
            "project": "XiaoNaiPing",
            "appName": "小奶瓶",
            "sourceFiles": {
                "smsAdapterHandoff": "Backend/deploy/aliyun-sms-webhook-adapter.md",
                "smsProviderEvidenceTemplate": "Docs/08_Release/AppStoreEvidence/_templates/sms-provider-evidence.template.json",
                "externalPlatformHandoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                "externalPlatformCapturePacket": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260630.json",
                "captureGuide": "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                "appStoreEvidenceReadme": "Docs/08_Release/AppStoreEvidence/README.md",
            },
            "localSecretHandling": {
                "testPhoneEnv": "XNP_SMS_TEST_PHONE",
                "storage": "private local shell environment or private env file only",
                "forbidden": [
                    "full phone number in command line",
                    "echoing the env value",
                    "committing the phone value",
                ],
            },
            "targetEvidenceFiles": {
                "smsProviderConsole": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
                "smsProviderConsolePdf": "Docs/08_Release/AppStoreEvidence/07-sms-provider.pdf",
                "providerConfigProof": "Backend/proof/auth-providers-20260630T-current.json",
                "smsLiveSendProof": "Backend/proof/auth-providers-sms-live-20260630T-current.json",
                "stableAuthAlias": "Backend/proof/auth-providers.json",
            },
            "evidenceFileChecks": [
                {
                    "artifactId": "smsProviderConsole",
                    "target": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png or .pdf",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsSmsLiveSend": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "providerConfigProof",
                    "target": "Backend/proof/auth-providers-20260630T-current.json",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsSmsLiveSend": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "smsLiveSendProof",
                    "target": "Backend/proof/auth-providers-sms-live-20260630T-current.json",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsSmsLiveSend": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "stableAuthAlias",
                    "target": "Backend/proof/auth-providers.json",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsSmsLiveSend": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
            ],
            "evidenceDependencyMatrix": [
                {
                    "artifactId": "smsProviderConsole",
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
                {
                    "artifactId": "providerConfigProof",
                    "target": "Backend/proof/auth-providers-20260630T-current.json",
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
                {
                    "artifactId": "smsLiveSendProof",
                    "target": "Backend/proof/auth-providers-sms-live-20260630T-current.json",
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
                {
                    "artifactId": "stableAuthAlias",
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
            ],
            "separationRules": [
                "providerConfigProof is not smsLiveSendProof",
                "verify_auth_providers.py --live-check only proves provider configuration",
                "verify_auth_providers.py --send-test-sms --require-sms-live-send is required for real live send proof",
                "stableAuthAlias must be copied from auth-providers-sms-live-20260630T-current.json",
            ],
            "consoleEvidenceMustKeep": [
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
            ],
            "redactionChecklist": [
                "XNP_SMS_SECRET",
                "webhook secret",
                "AccessKey",
                "SecretKey",
                "complete phone numbers",
                "verification code values",
                "tokens",
                "request signatures",
            ],
            "executionOrder": [
                {"step": "confirmProviderTemplate"},
                {"step": "captureProviderConsole"},
                {"step": "refreshProviderConfigProof"},
                {
                    "step": "runRealSmsLiveSend",
                    "command": "python3 Backend/scripts/verify_auth_providers.py --live-check --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE --base-url https://api.mewpow.com/xiaonaiping --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --output Backend/proof/auth-providers-sms-live-20260630T-current.json --allow-incomplete",
                },
                {
                    "step": "refreshAppStoreEvidence",
                    "command": "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30",
                },
                {
                    "step": "syncStableAuthAlias",
                    "command": "cp Backend/proof/auth-providers-sms-live-20260630T-current.json Backend/proof/auth-providers.json",
                },
            ],
            "postExecutionGates": [
                "python3 Backend/scripts/check_provider_evidence_materials.py",
                "python3 Backend/scripts/check_production_readiness.py",
                "python3 Backend/scripts/check_launch_objective_audit.py",
            ],
            "completionRule": "SMS evidence is complete only after real 07-sms-provider.png or PDF exists; app-store-evidence.json is ready=true; production-readiness.json plus launch-objective-audit.json are ready=true.",
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def valid_wechat_open_platform_template() -> str:
    target_files = {
        "mobileApplication": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
        "universalLinkAASA": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
    }
    return json.dumps(
        {
            "artifactType": "wechat-open-platform-evidence-template",
            "status": "template-only-not-evidence",
            "project": "XiaoNaiPing",
            "appName": "小奶瓶",
            "bundleId": "com.mewpow.xiaonaiping",
            "targetEvidenceFiles": target_files,
            "evidenceFileChecks": template_evidence_file_checks(target_files),
            "doNotRenameThisTemplateTo": [
                "08-wechat-open-platform.json",
                "08-wechat-open-platform.png",
                "08b-wechat-universal-link-aasa.json",
                "08b-wechat-universal-link-aasa.png",
            ],
            "wechatOpenPlatformFieldsToVerify": {
                "mobileAppName": "小奶瓶",
                "iosBundleId": "com.mewpow.xiaonaiping",
                "appId": "wx + 16 lowercase hex characters from WeChat Open Platform",
                "urlScheme": "same value as appId",
                "universalLink": "https://api.mewpow.com/xiaonaiping/wechat/",
                "configurationStatus": "approved or active in WeChat Open Platform",
            },
            "serverOnlySecrets": {
                "XNP_WECHAT_APP_SECRET": "must be stored only in private server env; never in iOS project, screenshots, JSON evidence, or repository"
            },
            "redactionChecklist": [
                "Hide AppSecret completely",
                "Hide administrator account details",
                "Hide complete phone numbers and verification codes",
                "Hide access tokens, session tokens, and private backend paths",
                "Keep AppID, Bundle ID, URL Scheme, Universal Link, and configuration status visible",
            ],
            "postCaptureChecks": [
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
                "python3 Backend/scripts/check_wechat_client_configuration.py --output Backend/proof/wechat-client-configuration-20260630T-current.json",
                ". /tmp/xnp-wechat-release.env && python3 Backend/scripts/check_ios_release_readiness.py --output Backend/proof/ios-release-readiness-20260630T-current-ios265.json",
                "python3 Backend/scripts/check_ios_app_bundle.py --app <Release XiaoNaiPing.app from iOS 26.5 build> --output Backend/proof/ios-app-bundle-20260630T-current-ios265.json",
                "python3 Backend/scripts/verify_auth_providers.py --deployment-proof Backend/proof/huawei-baota-deploy-20260630T-current.json --base-url https://api.mewpow.com/xiaonaiping --live-check --output Backend/proof/auth-providers-20260630T-current.json --allow-incomplete",
                "python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan-20260630T-current.json",
                "python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-20260630T-current.json",
                "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
            ],
            "completionRule": "This template is only a capture worksheet. The App Store evidence gate is still incomplete until real 08-wechat-open-platform.png or PDF evidence exists; real 08b-wechat-universal-link-aasa.png or PDF evidence proves same-round AASA alignment; real wx AppID and URL Scheme are injected into the Release build; server-side XNP_WECHAT_APP_SECRET is configured; auth-providers-20260630T-current.json is refreshed; RD-14 iOS 26.5 WeChat login evidence passes on TestFlight or a signed real device build; production-readiness.json is ready=true; and launch-objective-audit.json is ready=true.",
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def valid_obs_policy_template() -> str:
    target_files = {
        "obsPolicy": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
        "storageProof": "Backend/proof/storage-backend-20260630T-current.json",
    }
    return json.dumps(
        {
            "artifactType": "obs-policy-evidence-template",
            "status": "template-only-not-evidence",
            "project": "XiaoNaiPing",
            "appName": "小奶瓶",
            "targetEvidenceFiles": target_files,
            "evidenceFileChecks": template_evidence_file_checks(target_files),
            "doNotRenameThisTemplateTo": [
                "09-obs-policy.json",
                "09-obs-policy.png",
                "09-obs-policy.pdf",
            ],
            "fieldsToVerify": {
                "provider": "Huawei Cloud OBS",
                "bucketOrPrefix": "private bucket or XiaoNaiPing-specific prefix",
                "region": "production OBS region",
                "accessPolicy": "private access, no public baby photo bucket",
                "serverSideFlow": "upload, download, delete",
                "encryption": "enabled or documented production setting",
                "lifecycleOrDeletionPolicy": "configured lifecycle or deletion boundary",
                "accountDeletionResult": "account deletion clears corresponding baby photos and object data",
            },
            "serverProofToRefresh": [
                "Backend/proof/storage-backend-20260630T-current.json",
                "Backend/proof/production-readiness-20260630T-current.json",
            ],
            "redactionChecklist": [
                "Hide HUAWEI_OBS_ACCESS_KEY_ID and HUAWEI_OBS_SECRET_ACCESS_KEY",
                "Hide SecretKey and temporary signed URLs",
                "Hide complete object keys",
                "Hide real baby photos and private family media",
                "Hide private server paths",
                "Keep provider, bucket or prefix, region, private policy, encryption/lifecycle/deletion state, and storage proof summary visible",
            ],
            "postCaptureChecks": [
                "python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend-20260630T-current.json",
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
                "python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --storage-proof Backend/proof/storage-backend-20260630T-current.json --app-store-evidence Backend/proof/app-store-evidence-20260630T-current.json --require-huawei-obs --require-app-store-evidence --live-check --output Backend/proof/production-readiness-20260630T-current.json --allow-incomplete",
            ],
            "completionRule": "This template is only a capture worksheet. The App Store evidence gate remains incomplete until real 09-obs-policy.png/PDF/JSON evidence exists and same-round storage/production proof proves private OBS access plus account deletion cleanup.",
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def valid_obs_storage_packet() -> str:
    return json.dumps(
        {
            "artifactType": "obs-storage-proof-packet",
            "status": "storage-proof-packet-not-evidence",
            "date": "2026-06-30",
            "project": "XiaoNaiPing",
            "appName": "小奶瓶",
            "sourceFiles": {
                "obsHandoff": "Backend/deploy/huawei-obs.md",
                "obsPolicyEvidenceTemplate": "Docs/08_Release/AppStoreEvidence/_templates/obs-policy-evidence.template.json",
                "externalPlatformHandoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                "externalPlatformCapturePacket": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260630.json",
                "captureGuide": "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                "appStoreEvidenceReadme": "Docs/08_Release/AppStoreEvidence/README.md",
            },
            "targetEvidenceFiles": {
                "obsPolicyConsole": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
                "obsPolicyConsolePdf": "Docs/08_Release/AppStoreEvidence/09-obs-policy.pdf",
                "storageProof": "Backend/proof/storage-backend-20260630T-current.json",
                "productionReadinessCurrent": "Backend/proof/production-readiness-20260630T-current.json",
                "stableStorageAlias": "Backend/proof/storage-backend.json",
                "stableProductionReadinessAlias": "Backend/proof/production-readiness.json",
            },
            "evidenceFileChecks": [
                {
                    "artifactId": "obsPolicyConsole",
                    "target": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png or .pdf",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsObsStorageProof": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "storageProof",
                    "target": "Backend/proof/storage-backend-20260630T-current.json",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsObsStorageProof": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "productionReadinessCurrent",
                    "target": "Backend/proof/production-readiness-20260630T-current.json",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsObsStorageProof": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "stableStorageAlias",
                    "target": "Backend/proof/storage-backend.json",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsObsStorageProof": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
                {
                    "artifactId": "stableProductionReadinessAlias",
                    "target": "Backend/proof/production-readiness.json",
                    "fileSizeBytes": "FILL_AFTER_CAPTURE",
                    "sha256": "FILL_AFTER_CAPTURE",
                    "redactionChecked": False,
                    "sameRoundAsObsStorageProof": False,
                    "sourceIsAllowedEvidenceRoot": False,
                    "realEvidenceNotTemplate": False,
                    "secretValuesNotRecorded": False,
                },
            ],
            "evidenceDependencyMatrix": [
                {
                    "artifactId": "obsPolicyConsole",
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
                {
                    "artifactId": "storageProof",
                    "target": "Backend/proof/storage-backend-20260630T-current.json",
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
                {
                    "artifactId": "productionReadinessCurrent",
                    "target": "Backend/proof/production-readiness-20260630T-current.json",
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
                {
                    "artifactId": "stableStorageAlias",
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
                {
                    "artifactId": "stableProductionReadinessAlias",
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
            ],
            "separationRules": [
                "obsConsoleScreenshot is not storageProof",
                "storageProof is not App Store manual evidence",
                "productionReadinessCurrent is not storageProof alone",
                "stable aliases sync only after current storage, production, and App Store evidence gates are green",
                "no public bucket",
                "no signed URL",
                "no full object key",
                "no real baby photos",
            ],
            "consoleEvidenceMustKeep": [
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
            ],
            "redactionChecklist": [
                "HUAWEI_OBS_ACCESS_KEY_ID",
                "HUAWEI_OBS_SECRET_ACCESS_KEY",
                "AK/SK",
                "SecretKey",
                "temporary signed URLs",
                "complete object keys",
                "real baby photos",
                "private server paths",
                "account IDs",
            ],
            "executionOrder": [
                {"step": "confirmBucketPolicy"},
                {"step": "captureObsConsole"},
                {
                    "step": "refreshStorageProof",
                    "command": "python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend-20260630T-current.json",
                },
                {
                    "step": "refreshAppStoreEvidence",
                    "command": "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
                },
                {
                    "step": "refreshProductionReadiness",
                    "command": "python3 Backend/scripts/check_production_readiness.py --storage-proof Backend/proof/storage-backend-20260630T-current.json --app-store-evidence Backend/proof/app-store-evidence-20260630T-current.json --require-huawei-obs --require-app-store-evidence --live-check --output Backend/proof/production-readiness-20260630T-current.json --allow-incomplete",
                },
                {
                    "step": "syncStableStorageAliases",
                    "commands": [
                        "cp Backend/proof/storage-backend-20260630T-current.json Backend/proof/storage-backend.json",
                        "cp Backend/proof/production-readiness-20260630T-current.json Backend/proof/production-readiness.json",
                    ],
                },
            ],
            "postExecutionGates": [
                "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
                "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260630T-current.json",
                "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
            ],
            "completionRule": "This packet is not evidence and not submission permission. OBS storage proof is complete only after real 09-obs-policy.png or PDF exists, current storage proof passes, account deletion cleanup is proven, production-readiness.json ready=true, and launch-objective-audit.json ready=true.",
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def valid_external_capture_packet() -> str:
    target_files = {
        "wechatOpenPlatform": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
        "wechatUniversalLinkAasa": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
        "smsProviderConsole": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
        "huaweiObsPolicy": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
        "mainlandFiling": "Docs/08_Release/AppStoreEvidence/03-app-filing.png",
        "privacyLabel": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
        "productionReadinessCurrent": "Backend/proof/production-readiness-20260630T-current.json",
    }
    return json.dumps(
        {
            "artifactType": "external-platform-capture-packet",
            "status": "template-only-not-evidence",
            "date": "2026-06-30",
            "project": "XiaoNaiPing",
            "appName": "小奶瓶",
            "sourceFiles": {
                "handoff": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                "workbench": "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_20260630.md",
                "captureGuide": "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                "appStoreEvidenceReadme": "Docs/08_Release/AppStoreEvidence/README.md",
                "wechatConfiguration": "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md",
                "mainlandFilingMaterials": "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
            },
            "allowedEvidenceRoot": "Docs/08_Release/AppStoreEvidence/",
            "targetEvidenceFiles": target_files,
            "evidenceFileChecks": external_capture_evidence_file_checks(target_files),
            "evidenceDependencyMatrix": [
                {
                    "artifactId": "wechatOpenPlatform",
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
                {
                    "artifactId": "wechatUniversalLinkAasa",
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
                {
                    "artifactId": "smsProviderConsole",
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
                {
                    "artifactId": "huaweiObsPolicy",
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
                {
                    "artifactId": "mainlandFiling",
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
                {
                    "artifactId": "privacyLabel",
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
                {
                    "artifactId": "productionReadinessCurrent",
                    "target": "Backend/proof/production-readiness-20260630T-current.json",
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
            ],
            "requirements": [
                "sameDayEvidenceRoundRequired",
                "stableAliasSyncRequired",
                "canSubmitFalseUntilAllEvidenceReady",
                "doNotUseProviderConfigProofAsSmsLiveSendProof",
                "doNotUseConsoleScreenshotsAsRealDeviceProof",
            ],
            "cases": [
                {
                    "id": "wechatOpenPlatform",
                    "target": "Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
                    "markers": [
                        "微信开放平台",
                        "wx + 16 hex",
                        "Bundle ID",
                        "URL Scheme equal to AppID",
                        "Universal Link",
                        "AppSecret",
                        "Backend/proof/wechat-client-configuration-20260630T-current.json",
                        "Backend/proof/auth-providers-20260630T-current.json",
                    ],
                },
                {
                    "id": "wechatAasa",
                    "target": "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png",
                    "markers": [
                        "AASA",
                        "Associated Domains",
                        "applinks:api.mewpow.com",
                        "/xiaonaiping/wechat/",
                        "XNPWeChatUniversalLink",
                        "Apple 新组织 Team ID + com.mewpow.xiaonaiping",
                        "Backend/proof/universal-links-20260630T-current.json",
                        "Backend/proof/ios-app-bundle-20260630T-current-ios265.json",
                    ],
                },
                {
                    "id": "smsProvider",
                    "target": "Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
                    "markers": [
                        "短信服务商",
                        "账号登录/验证验证码模板",
                        "模板审核状态",
                        "发送区域",
                        "真实实发验证",
                        "不含营销",
                        "不含医疗",
                        "不含育儿建议",
                        "Backend/proof/auth-providers-sms-live-20260630T-current.json",
                    ],
                },
                {
                    "id": "huaweiObs",
                    "target": "Docs/08_Release/AppStoreEvidence/09-obs-policy.png",
                    "markers": [
                        "华为云 OBS",
                        "private bucket",
                        "bucket 或专用 prefix",
                        "私有访问策略",
                        "加密",
                        "生命周期",
                        "删除验证",
                        "Backend/proof/storage-backend-20260630T-current.json",
                    ],
                },
                {
                    "id": "mainlandFiling",
                    "target": "Docs/08_Release/AppStoreEvidence/03-app-filing.png",
                    "markers": [
                        "APP 备案",
                        "ICP",
                        "公安联网备案",
                        "备案通过前不写占位备案号",
                        "Backend/proof/mainland-filing-materials.json",
                    ],
                },
                {
                    "id": "privacyLabel",
                    "target": "Docs/08_Release/AppStoreEvidence/04-privacy-label.png",
                    "markers": [
                        "App Privacy",
                        "Tracking 为否",
                        "APP_STORE_PRIVACY_LABEL.json",
                        "隐私政策 URL",
                        "技术支持 URL",
                    ],
                },
                {
                    "id": "productionProof",
                    "target": "Backend/proof/production-readiness-20260630T-current.json",
                    "markers": [
                        "production readiness",
                        "huawei-baota-deploy-20260630T-current.json",
                        "remote-api-20260630T-current.json",
                        "storage-backend-20260630T-current.json",
                        "auth-providers-sms-live-20260630T-current.json",
                        "app-store-evidence-20260630T-current.json",
                    ],
                },
            ],
            "postCaptureCommands": [
                "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
                "python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json",
                "python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness-20260630T-current.json",
                "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
            ],
            "completionRule": "template-only-not-evidence; not submission permission; only after real external platform evidence files, app-store-evidence.json ready=true, production-readiness.json ready=true, launch-objective-audit.json ready=true.",
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def valid_external_capture_result_template() -> str:
    template_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json"
    )
    return template_path.read_text(encoding="utf-8")


def valid_production_proof_refresh_packet() -> str:
    packet_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json"
    )
    return packet_path.read_text(encoding="utf-8")


def valid_production_proof_refresh_status() -> str:
    target_proofs = json.loads(valid_production_proof_refresh_packet())["targetProofFiles"]
    failed_checks_by_artifact = {
        "deploymentProofCurrent": [
            "Huawei OBS storage backend is not selected",
            "production SMS webhook provider is not fully configured",
        ],
        "authProvidersConfigCurrent": ["smsProviderConfigured", "wechatProviderConfigured"],
        "appStoreEvidenceCurrent": ["smsProvider", "wechatOpenPlatform", "finalScreenshots"],
        "productionReadinessCurrent": ["authProvidersProofPassed", "appStoreAssetsProofPassed"],
        "launchObjectiveAudit": ["productionReadinessGreen"],
        "stableAuthProvidersAlias": ["smsProviderConfigured", "wechatProviderConfigured"],
        "stableAppStoreEvidenceAlias": ["smsProvider", "wechatOpenPlatform", "finalScreenshots"],
        "stableProductionReadinessAlias": ["authProvidersProofPassed", "appStoreAssetsProofPassed"],
    }
    missing_artifacts = {"authProvidersSmsLiveCurrent"}
    proof_statuses: list[dict[str, object]] = []
    for artifact_id, target in target_proofs.items():
        exists = artifact_id not in missing_artifacts
        failed_checks = failed_checks_by_artifact.get(artifact_id, [])
        proof_statuses.append(
            {
                "artifactId": artifact_id,
                "target": target,
                "exists": exists,
                "fileSizeBytes": 256 if exists else 0,
                "sha256": "0" * 64 if exists else None,
                "jsonParsed": exists,
                "currentDateStamped": exists,
                "passedOrReadyVerified": exists and not failed_checks,
                "failedRequiredChecks": failed_checks,
                "realProofNotTemplate": exists,
                "secretValuesNotRecorded": True,
                "secretScanHits": [],
                "stableAliasSyncedOnlyAfterGreen": False,
                "syncBlockedReason": "stable alias remains blocked until same-round current proofs are all green"
                if artifact_id.startswith("stable")
                else "",
            }
        )

    failed_proofs = [
        {
            "artifactId": item["artifactId"],
            "failedRequiredChecks": item["failedRequiredChecks"],
        }
        for item in proof_statuses
        if item["exists"] and (not item["passedOrReadyVerified"] or item["failedRequiredChecks"])
    ]
    missing_proofs = [str(item["artifactId"]) for item in proof_statuses if not item["exists"]]
    return json.dumps(
        {
            "artifactType": "production-proof-refresh-status",
            "status": "current-proof-status-not-submit-permission",
            "date": "2026-06-30",
            "checkedAt": "2026-06-30T00:00:00.000Z",
            "project": "XiaoNaiPing",
            "appName": "小奶瓶",
            "xnpRoot": "/tmp/xiaonaiping",
            "baseUrl": "https://api.mewpow.com/xiaonaiping",
            "sourcePlan": "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json",
            "canSubmitFromThisStatus": False,
            "stableAliasSyncAllowed": False,
            "stableAliasSyncReason": "current proof files are incomplete or failed; do not sync stable aliases",
            "proofFileStatuses": proof_statuses,
            "summary": {
                "totalProofFiles": len(proof_statuses),
                "existingProofFiles": len(proof_statuses) - len(missing_proofs),
                "missingProofFiles": len(missing_proofs),
                "failedProofFiles": len(failed_proofs),
                "secretScanFailures": 0,
                "deploymentProofCurrentExists": True,
                "authProvidersSmsLiveCurrentExists": False,
                "stableAliasesBlocked": True,
            },
            "missingProofs": missing_proofs,
            "failedProofs": failed_proofs,
            "secretScanFailures": [],
            "nextActions": [
                "Do not sync stable aliases until every same-round current proof is green.",
                "Configure production private env, MySQL, Huawei OBS, SMS live send, and WeChat AppSecret without recording secret values in proof files.",
                "Capture App Store Connect, Apple Developer, SMS, WeChat, OBS, filing, final screenshots, and iOS 26.5 real-device evidence before Submit for Review.",
            ],
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def valid_production_proof_refresh_status_script() -> str:
    return """
STATUS_ARTIFACT_TYPE = "production-proof-refresh-status"
STATUS_VALUE = "current-proof-status-not-submit-permission"
stableAliasSyncAllowed = False
proofFileStatuses = []
secretScanFailures = []
allowIncompleteFlag = "--allow-incomplete"
""".lstrip()


def write_valid_docs(root: Path) -> None:
    write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", valid_submission_packet())
    write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook())
    write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_evidence_readme())
    write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide())
    write(root / "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md", valid_wechat_doc())
    write(root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md", valid_external_handoff())
    write(root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_20260630.md", valid_external_capture_workbench())
    write(root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260630.json", valid_external_capture_packet())
    write(
        root / "Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json",
        valid_external_capture_result_template(),
    )
    write(root / "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260630.json", valid_sms_live_send_packet())
    write(root / "Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260630.json", valid_obs_storage_packet())
    write(root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json", valid_production_proof_refresh_packet())
    write(root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260630.json", valid_production_proof_refresh_status())
    write(root / "Backend/scripts/check_production_proof_refresh_status.py", valid_production_proof_refresh_status_script())
    write(root / "Backend/deploy/aliyun-sms-webhook-adapter.md", valid_sms_doc())
    write(root / "Backend/sms/aliyun-webhook-adapter/server.js", valid_sms_adapter_server())
    write(root / "Backend/deploy/aliyun-sms-adapter.env.example", valid_sms_adapter_env_example())
    write(root / "Backend/deploy/xiaonaiping-aliyun-sms-adapter.service.example", valid_sms_adapter_service_example())
    write(root / "Backend/deploy/production-config.example", valid_production_config_example())
    write(root / "Backend/deploy/huawei-obs.md", valid_obs_doc())
    write(root / "Docs/08_Release/AppStoreEvidence/_templates/sms-provider-evidence.template.json", valid_sms_provider_template())
    write(
        root / "Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json",
        valid_wechat_open_platform_template(),
    )
    write(root / "Docs/08_Release/AppStoreEvidence/_templates/obs-policy-evidence.template.json", valid_obs_policy_template())


class ProviderEvidenceMaterialsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/provider-evidence-materials.json"
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
        self.assertIn("provider evidence materials", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_materials_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_sha256_digits_are_not_treated_as_phone_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            status = json.loads(valid_production_proof_refresh_status())
            status["proofFileStatuses"][0]["sha256"] = "a19279187045" + ("b" * 52)
            write(
                root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260630.json",
                json.dumps(status, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_external_provider_templates_are_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            sms_template = json.loads(valid_sms_provider_template())
            del sms_template["targetEvidenceFiles"]["smsLiveProof"]
            sms_template["evidenceFileChecks"] = [
                check for check in sms_template["evidenceFileChecks"] if check["artifactId"] != "smsProvider"
            ]
            sms_template["evidenceFileChecks"][0]["target"] = "Backend/proof/auth-providers-wrong.json"
            sms_template["evidenceFileChecks"][0]["sha256"] = "already-filled"
            sms_template["evidenceFileChecks"][0]["sameRoundAsTemplateCapture"] = True
            sms_template["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            sms_template["postCaptureChecks"] = [
                check for check in sms_template["postCaptureChecks"] if "--send-test-sms" not in check
            ]
            sms_template["completionRule"] = "This is a template."
            wechat_template = json.loads(valid_wechat_open_platform_template())
            del wechat_template["wechatOpenPlatformFieldsToVerify"]["urlScheme"]
            wechat_template["serverOnlySecrets"] = {}
            wechat_template["postCaptureChecks"] = [
                check for check in wechat_template["postCaptureChecks"] if "check_testflight_regression_plan.py" not in check
            ]
            wechat_template["completionRule"] = "This is a template."
            obs_template = json.loads(valid_obs_policy_template())
            del obs_template["targetEvidenceFiles"]["storageProof"]
            obs_template["redactionChecklist"] = []
            write(
                root / "Docs/08_Release/AppStoreEvidence/_templates/sms-provider-evidence.template.json",
                json.dumps(sms_template, ensure_ascii=False),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json",
                json.dumps(wechat_template, ensure_ascii=False),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/_templates/obs-policy-evidence.template.json",
                json.dumps(obs_template, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalProviderEvidenceTemplatesValid", report["failedRequiredChecks"])
            evidence = report["checks"]["externalProviderEvidenceTemplatesValid"]["evidence"]
            self.assertIn("sms.targetEvidenceFiles.smsLiveProof", evidence)
            self.assertIn("sms.evidenceFileChecks order must match targetEvidenceFiles", evidence)
            self.assertIn("sms.evidenceFileChecks.smsProvider missing object", evidence)
            self.assertIn("sms.evidenceFileChecks.smsLiveProof.target must be Backend/proof/auth-providers-sms-live-20260630T-current.json", evidence)
            self.assertIn("sms.evidenceFileChecks.smsLiveProof.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("sms.evidenceFileChecks.smsLiveProof.sameRoundAsTemplateCapture must be False", evidence)
            self.assertIn("sms.evidenceFileChecks.smsLiveProof.secretValuesNotRecorded must be False", evidence)
            self.assertIn("sms.postCaptureChecks missing --send-test-sms", evidence)
            self.assertIn("sms.completionRule missing real SMS live-send proof", evidence)
            self.assertIn("wechat.wechatOpenPlatformFieldsToVerify.urlScheme", evidence)
            self.assertIn("wechat.serverOnlySecrets.XNP_WECHAT_APP_SECRET", evidence)
            self.assertIn("wechat.postCaptureChecks missing check_testflight_regression_plan.py", evidence)
            self.assertIn("wechat.completionRule missing real 08b-wechat-universal-link-aasa.png", evidence)
            self.assertIn("wechat.completionRule missing RD-14 iOS 26.5", evidence)
            self.assertIn("obs.targetEvidenceFiles.storageProof", evidence)
            self.assertIn("obs.redactionChecklist", evidence)

    def test_sms_live_send_packet_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_sms_live_send_packet())
            packet["status"] = "evidence"
            packet.pop("localSecretHandling")
            packet["targetEvidenceFiles"].pop("smsLiveSendProof")
            packet["evidenceDependencyMatrix"] = [
                item
                for item in packet["evidenceDependencyMatrix"]
                if item["artifactId"] != "smsLiveSendProof"
            ]
            packet["evidenceDependencyMatrix"][1]["target"] = "Backend/proof/auth-providers.json"
            packet["evidenceDependencyMatrix"][-1]["requiredBeforeAliasSync"] = True
            packet["executionOrder"] = [
                step for step in packet["executionOrder"] if step["step"] != "runRealSmsLiveSend"
            ]
            packet["completionRule"] = "SMS is done."
            write(
                root / "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("smsLiveSendPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["smsLiveSendPacketValid"]["evidence"]
            self.assertIn("smsLiveSendPacket missing live-send-packet-not-evidence", evidence)
            self.assertIn("smsLiveSendPacket missing localSecretHandling", evidence)
            self.assertIn("smsLiveSendPacket.targetEvidenceFiles.smsLiveSendProof missing", evidence)
            self.assertIn(
                "smsLiveSendPacket.evidenceDependencyMatrix order must be "
                "smsProviderConsole -> providerConfigProof -> smsLiveSendProof -> stableAuthAlias",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.evidenceDependencyMatrix.providerConfigProof.target must be "
                "Backend/proof/auth-providers-20260630T-current.json",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.evidenceDependencyMatrix.smsLiveSendProof missing object",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.evidenceDependencyMatrix.stableAuthAlias.requiredBeforeAliasSync "
                "must be False",
                evidence,
            )
            self.assertIn("smsLiveSendPacket.executionOrder must be", evidence)
            self.assertIn("SMS evidence is complete only after real 07-sms-provider.png or PDF exists", evidence)

    def test_sms_live_send_packet_requires_env_phone_and_blocks_literal_phone_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_sms_live_send_packet())
            packet["localSecretHandling"] = {
                "testPhoneEnv": "XNP_SMS_TEST_PHONE=+8613800138000",
                "storage": "shared release worksheet",
                "forbidden": ["committing the phone value"],
            }
            for step in packet["executionOrder"]:
                if step["step"] == "runRealSmsLiveSend":
                    step["command"] = (
                        "python3 Backend/scripts/verify_auth_providers.py --live-check "
                        "--send-test-sms --require-sms-live-send --phone +8613800138000 "
                        "--output Backend/proof/auth-providers-sms-live-20260630T-current.json"
                    )
            write(
                root / "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("smsLiveSendPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["smsLiveSendPacketValid"]["evidence"]
            self.assertIn(
                "smsLiveSendPacket.localSecretHandling.testPhoneEnv must be XNP_SMS_TEST_PHONE",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.localSecretHandling.storage must be "
                "private local shell environment or private env file only",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.localSecretHandling.forbidden must be "
                "full phone number in command line -> echoing the env value -> committing the phone value",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.executionOrder.runRealSmsLiveSend.command missing "
                "--phone-env XNP_SMS_TEST_PHONE",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.executionOrder.runRealSmsLiveSend.command "
                "must use --phone-env XNP_SMS_TEST_PHONE and must not use --phone or literal phone numbers",
                evidence,
            )

    def test_sms_live_send_packet_requires_evidence_file_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_sms_live_send_packet())
            packet["evidenceFileChecks"] = [
                item for item in packet["evidenceFileChecks"] if item["artifactId"] != "smsProviderConsole"
            ]
            packet["evidenceFileChecks"][0]["target"] = "Backend/proof/auth-providers-wrong.json"
            packet["evidenceFileChecks"][0]["sha256"] = "already-filled"
            packet["evidenceFileChecks"][0]["sameRoundAsSmsLiveSend"] = True
            packet["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            write(
                root / "Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("smsLiveSendPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["smsLiveSendPacketValid"]["evidence"]
            self.assertIn("smsLiveSendPacket.evidenceFileChecks.smsProviderConsole missing object", evidence)
            self.assertIn(
                "smsLiveSendPacket.evidenceFileChecks.providerConfigProof.target must be "
                "Backend/proof/auth-providers-20260630T-current.json",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.evidenceFileChecks.providerConfigProof.sha256 must be 'FILL_AFTER_CAPTURE'",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.evidenceFileChecks.providerConfigProof.sameRoundAsSmsLiveSend must be False",
                evidence,
            )
            self.assertIn(
                "smsLiveSendPacket.evidenceFileChecks.providerConfigProof.secretValuesNotRecorded must be False",
                evidence,
            )

    def test_obs_storage_packet_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_obs_storage_packet())
            packet["status"] = "evidence"
            packet["targetEvidenceFiles"].pop("storageProof")
            packet["executionOrder"] = [
                step for step in packet["executionOrder"] if step["step"] != "refreshStorageProof"
            ]
            packet["completionRule"] = "OBS storage is done."
            write(
                root / "Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("obsStorageProofPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["obsStorageProofPacketValid"]["evidence"]
            self.assertIn("obsStorageProofPacket missing storage-proof-packet-not-evidence", evidence)
            self.assertIn("obsStorageProofPacket.targetEvidenceFiles.storageProof missing", evidence)
            self.assertIn("obsStorageProofPacket.executionOrder must be", evidence)
            self.assertIn("OBS storage proof is complete only after real 09-obs-policy.png or PDF exists", evidence)

    def test_obs_storage_packet_requires_evidence_file_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_obs_storage_packet())
            packet["evidenceFileChecks"] = [
                item for item in packet["evidenceFileChecks"] if item["artifactId"] != "obsPolicyConsole"
            ]
            packet["evidenceFileChecks"][0]["target"] = "Backend/proof/storage-backend-wrong.json"
            packet["evidenceFileChecks"][0]["sha256"] = "already-filled"
            packet["evidenceFileChecks"][0]["sameRoundAsObsStorageProof"] = True
            packet["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            write(
                root / "Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("obsStorageProofPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["obsStorageProofPacketValid"]["evidence"]
            self.assertIn("obsStorageProofPacket.evidenceFileChecks.obsPolicyConsole missing object", evidence)
            self.assertIn(
                "obsStorageProofPacket.evidenceFileChecks.storageProof.target must be "
                "Backend/proof/storage-backend-20260630T-current.json",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceFileChecks.storageProof.sha256 must be 'FILL_AFTER_CAPTURE'",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceFileChecks.storageProof.sameRoundAsObsStorageProof must be False",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceFileChecks.storageProof.secretValuesNotRecorded must be False",
                evidence,
            )

    def test_obs_storage_packet_requires_dependency_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_obs_storage_packet())
            packet["evidenceDependencyMatrix"] = [
                item
                for item in packet["evidenceDependencyMatrix"]
                if item["artifactId"] != "storageProof"
            ]
            packet["evidenceDependencyMatrix"][0]["target"] = "Docs/08_Release/AppStoreEvidence/09-obs-policy-copy.png"
            packet["evidenceDependencyMatrix"][0]["proves"] = ["OBS screenshot exists"]
            packet["evidenceDependencyMatrix"][0]["requiredBeforeSubmit"] = False
            packet["evidenceDependencyMatrix"][0]["initialStatus"] = "captured"
            packet["evidenceDependencyMatrix"][0]["extra"] = "unexpected"
            write(
                root / "Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("obsStorageProofPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["obsStorageProofPacketValid"]["evidence"]
            self.assertIn(
                "obsStorageProofPacket.evidenceDependencyMatrix order must be "
                "obsPolicyConsole -> storageProof -> productionReadinessCurrent -> stableStorageAlias -> "
                "stableProductionReadinessAlias",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceDependencyMatrix.storageProof missing object",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceDependencyMatrix.obsPolicyConsole.fields must be "
                "artifactId -> target -> proves -> doesNotProve -> requiredBeforeSubmit -> initialStatus",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceDependencyMatrix.obsPolicyConsole.target must be "
                "Docs/08_Release/AppStoreEvidence/09-obs-policy.png or .pdf",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceDependencyMatrix.obsPolicyConsole.proves must be "
                "['Huawei OBS console shows private bucket or prefix, region, policy, encryption, lifecycle, "
                "and deletion posture', 'OBS console evidence can be inspected without exposing AK/SK, "
                "signed URLs, object keys, or baby photos']",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceDependencyMatrix.obsPolicyConsole.requiredBeforeSubmit must be True",
                evidence,
            )
            self.assertIn(
                "obsStorageProofPacket.evidenceDependencyMatrix.obsPolicyConsole.initialStatus must be pending",
                evidence,
            )

    def test_external_platform_capture_packet_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_external_capture_packet())
            packet["requirements"].remove("doNotUseProviderConfigProofAsSmsLiveSendProof")
            packet["allowedEvidenceRoot"] = "Docs/08_Release/AppStoreEvidence/ExternalPlatform/"
            packet["targetEvidenceFiles"].pop("productionReadinessCurrent")
            packet["evidenceFileChecks"] = [
                check for check in packet["evidenceFileChecks"] if check["artifactId"] != "smsProviderConsole"
            ]
            packet["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/08-wechat-wrong.png"
            packet["evidenceFileChecks"][0]["sha256"] = "already-filled"
            packet["evidenceFileChecks"][0]["sameRoundAsExternalPlatformCapture"] = True
            packet["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            packet["evidenceDependencyMatrix"] = [
                item
                for item in packet["evidenceDependencyMatrix"]
                if item["artifactId"] != "smsProviderConsole"
            ]
            packet["evidenceDependencyMatrix"][4]["proves"] = ["App Store Privacy label page"]
            packet["evidenceDependencyMatrix"][5]["requiredBeforeSubmit"] = False
            packet["evidenceDependencyMatrix"][5]["initialStatus"] = "captured"
            packet["cases"] = [
                case
                for case in packet["cases"]
                if case["target"] != "Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png"
            ]
            for case in packet["cases"]:
                if case["target"] == "Docs/08_Release/AppStoreEvidence/07-sms-provider.png":
                    case["markers"] = ["短信服务商", "账号登录/验证验证码模板"]
                if case["target"] == "Backend/proof/production-readiness-20260630T-current.json":
                    case["markers"] = ["production readiness"]
            packet["postCaptureCommands"] = [
                "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json"
            ]
            packet["completionRule"] = "template-only-not-evidence"
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalPlatformCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["externalPlatformCapturePacketValid"]["evidence"]
            self.assertIn("requirements missing doNotUseProviderConfigProofAsSmsLiveSendProof", evidence)
            self.assertIn(
                "allowedEvidenceRoot must be Docs/08_Release/AppStoreEvidence/",
                evidence,
            )
            self.assertIn("targetEvidenceFiles.productionReadinessCurrent missing", evidence)
            self.assertIn("evidenceFileChecks order must match external platform capture workflow", evidence)
            self.assertIn("evidenceFileChecks.smsProviderConsole missing object", evidence)
            self.assertIn(
                "evidenceFileChecks.wechatOpenPlatform.target must be Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
                evidence,
            )
            self.assertIn("evidenceFileChecks.wechatOpenPlatform.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("evidenceFileChecks.wechatOpenPlatform.sameRoundAsExternalPlatformCapture must be False", evidence)
            self.assertIn("evidenceFileChecks.wechatOpenPlatform.secretValuesNotRecorded must be False", evidence)
            self.assertIn("evidenceDependencyMatrix order must match external platform capture workflow", evidence)
            self.assertIn("evidenceDependencyMatrix.smsProviderConsole missing object", evidence)
            self.assertIn(
                "evidenceDependencyMatrix.privacyLabel.proves must be App Store Privacy label page matches APP_STORE_PRIVACY_LABEL.json and Tracking is No",
                evidence,
            )
            self.assertIn("evidenceDependencyMatrix.productionReadinessCurrent.requiredBeforeSubmit must be True", evidence)
            self.assertIn("evidenceDependencyMatrix.productionReadinessCurrent.initialStatus must be pending", evidence)
            self.assertIn("cases missing Docs/08_Release/AppStoreEvidence/08b-wechat-universal-link-aasa.png", evidence)
            self.assertIn("Docs/08_Release/AppStoreEvidence/07-sms-provider.png missing 真实实发验证", evidence)
            self.assertIn("Backend/proof/production-readiness-20260630T-current.json missing huawei-baota-deploy-20260630T-current.json", evidence)
            self.assertIn("postCaptureCommands missing python3 Backend/scripts/check_app_store_evidence.py", evidence)
            self.assertIn("completionRule missing real external platform evidence files", evidence)

    def test_external_platform_capture_packet_rejects_duplicate_or_mismatched_case_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_external_capture_packet())
            for case in packet["cases"]:
                if case["target"] == "Docs/08_Release/AppStoreEvidence/09-obs-policy.png":
                    case["id"] = "smsProvider"
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalPlatformCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["externalPlatformCapturePacketValid"]["evidence"]
            self.assertIn("cases duplicate id smsProvider", evidence)
            self.assertIn("Docs/08_Release/AppStoreEvidence/09-obs-policy.png id must be huaweiObs", evidence)

    def test_external_platform_capture_packet_rejects_extra_or_reordered_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_external_capture_packet())
            cases = packet["cases"]
            packet["cases"] = [
                cases[1],
                cases[0],
                *cases[2:],
                {
                    "id": "extraExternalEvidence",
                    "target": "Docs/08_Release/AppStoreEvidence/99-extra.png",
                    "markers": ["不应进入正式外部平台采集包"],
                },
            ]
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalPlatformCapturePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["externalPlatformCapturePacketValid"]["evidence"]
            self.assertIn("cases order must match external platform capture workflow", evidence)

    def test_external_platform_capture_result_template_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            template = json.loads(valid_external_capture_result_template())
            template["status"] = "captured-live-external-platforms"
            template["canSubmitAtCapture"] = True
            template["capturedBy"] = "Penghui She"
            template["currentProofs"]["xnpIosBundle"] = "Backend/proof/ios-app-bundle-20260630T-current.json"
            template["currentProofs"]["cross-app-submission-readiness"] = (
                "/Users/smianmian/Emotion Isle/output/cross-app-submission-readiness-20260630-current.json"
            )
            template["xiaonaipingRequiredProofs"].pop("productionReadiness")
            template["crossAppDoesNotReplaceXiaoNaiPingProof"] = False
            template["instructions"].append("旧口径：cross-app-submission-readiness canSubmit=true")
            template["postCaptureProofReruns"] = {
                "checkCrossAppSubmitReady": "check-cross-app-submit-ready"
            }
            template["postCaptureRerunCommands"] = [
                command
                for command in template["postCaptureRerunCommands"]
                if "check_provider_evidence_materials.py" not in command
                and "auth-providers-sms-live-20260630T-current.json" not in command
            ]
            template["sameRoundEvidenceManifest"]["allDependenciesCurrentAndPassed"] = True
            template["sameRoundEvidenceManifest"]["sameRoundProofLinks"] = [
                link
                for link in template["sameRoundEvidenceManifest"]["sameRoundProofLinks"]
                if "MAINLAND_FILING_EXECUTION_PACKET" not in link
            ]
            template["externalPlatforms"]["smsProvider"]["evidenceFiles"] = [
                "Docs/08_Release/AppStoreEvidence/07-provider.png"
            ]
            template["externalPlatforms"]["smsLiveSend"]["liveSendSucceeded"] = True
            del template["externalPlatforms"]["wechatOpenPlatform"]["reviewStatusApprovedOrOnline"]
            template["redactionReviewed"]["completePhoneHidden"] = True
            template["evidenceFileChecks"] = [
                check
                for check in template["evidenceFileChecks"]
                if check["artifactId"] != "smsProviderConsole"
            ]
            template["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/08-wechat-wrong.png"
            template["evidenceFileChecks"][0]["sha256"] = "already-filled"
            template["evidenceFileChecks"][0]["sameRoundAsCapture"] = True
            template["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            template["operatorNotes"] = "captured"
            write(
                root / "Docs/08_Release/AppStoreEvidence/ExternalPlatform/EXTERNAL-PLATFORM-CAPTURE-RESULT.template.json",
                json.dumps(template, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalPlatformCaptureResultTemplateValid", report["failedRequiredChecks"])
            evidence = report["checks"]["externalPlatformCaptureResultTemplateValid"]["evidence"]
            self.assertIn("externalPlatformCaptureResultTemplate.status must be 'template-not-evidence'", evidence)
            self.assertIn("externalPlatformCaptureResultTemplate.canSubmitAtCapture must be False", evidence)
            self.assertIn("externalPlatformCaptureResultTemplate.capturedBy must be '佘鹏辉 / Penghui She'", evidence)
            self.assertIn("externalPlatformCaptureResultTemplate.currentProofs.xnpIosBundle", evidence)
            self.assertIn(
                "externalPlatformCaptureResultTemplate.xiaonaipingRequiredProofs must lock XiaoNaiPing provider",
                evidence,
            )
            self.assertIn("externalPlatformCaptureResultTemplate.crossAppDoesNotReplaceXiaoNaiPingProof must be true", evidence)
            self.assertIn(
                "externalPlatformCaptureResultTemplate.postCaptureProofReruns must include XiaoNaiPing post-capture proof reruns",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate must not include stale cross-app submit marker check-cross-app-submit-ready",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate must not include stale cross-app submit marker canSubmit=true",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.postCaptureRerunCommands missing "
                "python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.postCaptureRerunCommands missing "
                "Backend/proof/auth-providers-sms-live-20260630T-current.json",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.sameRoundEvidenceManifest.allDependenciesCurrentAndPassed must be False",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.sameRoundEvidenceManifest.sameRoundProofLinks must include external capture, SMS, WeChat, OBS, mainland filing, production refresh, and current proof links in order",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.evidenceFileChecks order must match external evidence workflow",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.evidenceFileChecks.smsProviderConsole missing object",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.evidenceFileChecks.wechatOpenPlatform.target missing Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.evidenceFileChecks.wechatOpenPlatform.sha256 must be 'FILL_AFTER_CAPTURE'",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.evidenceFileChecks.wechatOpenPlatform.sameRoundAsCapture must be False",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.evidenceFileChecks.wechatOpenPlatform.secretValuesNotRecorded must be False",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.externalPlatforms.smsProvider.evidenceFiles missing Docs/08_Release/AppStoreEvidence/07-sms-provider.png",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.externalPlatforms.smsLiveSend.liveSendSucceeded must be false in template",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.externalPlatforms.wechatOpenPlatform.reviewStatusApprovedOrOnline must be false in template",
                evidence,
            )
            self.assertIn(
                "externalPlatformCaptureResultTemplate.redactionReviewed.completePhoneHidden must be false in template",
                evidence,
            )
            self.assertIn("externalPlatformCaptureResultTemplate.operatorNotes must be empty in template", evidence)

    def test_missing_provider_rows_and_redaction_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_evidence_readme().replace("09-obs-policy.png", "09-storage.png"))
            write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook().replace("09-obs-policy.png", "09-storage.png"))
            write(
                root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                valid_capture_guide().replace("09-obs-policy.png", "09-storage.png").replace("完整手机号、验证码", "手机号"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("providerEvidenceFilenamesPresent", report["failedRequiredChecks"])
            self.assertIn("providerEvidenceRedactionCovered", report["failedRequiredChecks"])

    def test_sms_capture_sheet_must_cover_real_send_and_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Backend/deploy/aliyun-sms-webhook-adapter.md",
                valid_sms_doc()
                .replace("## 短信服务商截图字段清单", "## 截图字段")
                .replace("verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE", "")
                .replace("不替代短信服务商截图或真实实发截图", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("smsProviderMaterialCoversSignatureTemplateSendAndSecrets", report["failedRequiredChecks"])
            evidence = report["checks"]["smsProviderMaterialCoversSignatureTemplateSendAndSecrets"]["evidence"]
            self.assertIn("## 短信服务商截图字段清单", evidence)
            self.assertIn("verify_auth_providers.py --send-test-sms", evidence)
            self.assertIn("不替代短信服务商截图或真实实发截图", evidence)

    def test_sms_template_boundary_must_reject_marketing_medical_or_parenting_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)

            def loosen(text: str) -> str:
                for marker in (
                    "账号登录/验证",
                    "模板审核状态",
                    "发送区域",
                    "不含营销",
                    "不含医疗",
                    "不含育儿建议",
                    "验证码模板，必须能证明只用于账号登录/验证。模板审核状态和发送区域必须可见。模板内容不含营销、不含医疗、不含育儿建议。\n",
                ):
                    text = text.replace(marker, "")
                return text

            write(root / "Backend/deploy/aliyun-sms-webhook-adapter.md", loosen(valid_sms_doc()))
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", loosen(valid_capture_guide()))
            write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", loosen(valid_runbook()))
            write(root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md", loosen(valid_external_handoff()))
            write(root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_20260630.md", loosen(valid_external_capture_workbench()))

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("smsProviderMaterialCoversSignatureTemplateSendAndSecrets", report["failedRequiredChecks"])
            self.assertIn("externalPlatformEvidenceHandoffReady", report["failedRequiredChecks"])
            self.assertIn("externalPlatformCaptureWorkbenchCurrent", report["failedRequiredChecks"])
            sms_evidence = report["checks"]["smsProviderMaterialCoversSignatureTemplateSendAndSecrets"]["evidence"]
            self.assertIn("账号登录/验证", sms_evidence)
            self.assertIn("模板审核状态", sms_evidence)
            self.assertIn("发送区域", sms_evidence)
            self.assertIn("不含营销", sms_evidence)
            self.assertIn("不含医疗", sms_evidence)
            self.assertIn("不含育儿建议", sms_evidence)

    def test_sms_adapter_runtime_assets_must_cover_signed_webhook_and_private_env(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Backend/sms/aliyun-webhook-adapter/server.js",
                valid_sms_adapter_server()
                .replace("verifyWebhookSignature(secret, body, req.headers['x-xnp-signature']);", "")
                .replace("if (req.method === 'GET' && req.url === '/healthz') {}", ""),
            )
            write(
                root / "Backend/deploy/aliyun-sms-adapter.env.example",
                valid_sms_adapter_env_example().replace("XNP_SMS_ADAPTER_MOCK=0\n", ""),
            )
            write(
                root / "Backend/deploy/xiaonaiping-aliyun-sms-adapter.service.example",
                valid_sms_adapter_service_example().replace("EnvironmentFile=/srv/xiaonaiping/private/xiaonaiping-aliyun-sms-adapter.env\n", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("smsAdapterRuntimeAssetsPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["smsAdapterRuntimeAssetsPresent"]["evidence"]
            self.assertIn("server:verifyWebhookSignature(secret, body, req.headers['x-xnp-signature'])", evidence)
            self.assertIn("server:req.method === 'GET' && req.url === '/healthz'", evidence)
            self.assertIn("env:XNP_SMS_ADAPTER_MOCK=0", evidence)
            self.assertIn("service:EnvironmentFile=/srv/xiaonaiping/private/xiaonaiping-aliyun-sms-adapter.env", evidence)

    def test_completion_claim_without_archived_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
                valid_submission_packet() + "\n短信服务商证据已完成。OBS 策略证据已完成。\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("doesNotPretendProviderEvidenceCompleteBeforeFiles", report["failedRequiredChecks"])
            evidence = report["checks"]["doesNotPretendProviderEvidenceCompleteBeforeFiles"]["evidence"]
            self.assertIn("短信服务商证据已完成", evidence)
            self.assertIn("OBS 策略证据已完成", evidence)

    def test_external_platform_handoff_must_cover_real_evidence_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                valid_external_handoff().replace("真实实发验证", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalPlatformEvidenceHandoffReady", report["failedRequiredChecks"])

    def test_wechat_universal_link_aasa_evidence_boundary_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/AppStoreEvidence/README.md",
                valid_evidence_readme().replace("08b-wechat-universal-link-aasa.png", "08b-aasa.png"),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                valid_capture_guide()
                .replace("08b-wechat-universal-link-aasa.png", "08b-aasa.png")
                .replace("AASA、Team ID、Associated Domains、微信 Universal Link 同轮核对", "")
                .replace("`applinks:api.mewpow.com`", ""),
            )
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                valid_external_handoff()
                .replace("08b-wechat-universal-link-aasa.png", "08b-aasa.png")
                .replace("Backend/proof/universal-links-20260630T-current.json", "")
                .replace("Backend/proof/wechat-client-configuration-20260630T-current.json", "")
                .replace("Associated Domains 包含 `applinks:api.mewpow.com`。", "")
                .replace("微信开放平台后台 Universal Link 与 iOS Release 包中的 `XNPWeChatUniversalLink` 完全一致。", "")
                .replace("AASA、Associated Domains、Release 包和微信开放平台 Universal Link 已同轮核对。", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("wechatUniversalLinkAasaEvidenceBoundaryPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["wechatUniversalLinkAasaEvidenceBoundaryPresent"]["evidence"]
            self.assertIn("08b-wechat-universal-link-aasa.png", evidence)
            self.assertIn("Backend/proof/universal-links-20260630T-current.json", evidence)

    def test_production_proof_refresh_plan_must_pin_current_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                valid_external_handoff()
                .replace("python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend-20260630T-current.json\n", "")
                .replace("Backend/proof/production-readiness-20260630T-current.json", "Backend/proof/production-readiness.json")
                .replace("cp Backend/proof/huawei-baota-deploy-20260630T-current.json Backend/proof/huawei-baota-deploy.json\n", "")
                .replace("cp Backend/proof/storage-backend-20260630T-current.json Backend/proof/storage-backend.json\n", "")
                .replace("cp Backend/proof/auth-providers-sms-live-20260630T-current.json Backend/proof/auth-providers.json\n", "")
                .replace("不得写入 root 密码、SSH key、AK/SK、AppSecret、完整手机号或验证码。", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionProofRefreshPlanCoversCurrentProofs", report["failedRequiredChecks"])
            evidence = report["checks"]["productionProofRefreshPlanCoversCurrentProofs"]["evidence"]
            self.assertIn("Backend/proof/production-readiness-20260630T-current.json", evidence)
            self.assertIn("cp Backend/proof/huawei-baota-deploy-20260630T-current.json Backend/proof/huawei-baota-deploy.json", evidence)
            self.assertIn("cp Backend/proof/storage-backend-20260630T-current.json Backend/proof/storage-backend.json", evidence)
            self.assertIn("cp Backend/proof/auth-providers-sms-live-20260630T-current.json Backend/proof/auth-providers.json", evidence)
            self.assertIn("不得写入 root 密码", evidence)

    def test_production_proof_refresh_packet_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_production_proof_refresh_packet())
            packet["targetProofFiles"]["productionReadinessCurrent"] = "Backend/proof/production-readiness.json"
            packet["proofFileChecks"] = [
                item
                for item in packet["proofFileChecks"]
                if item["artifactId"] != "stableRemoteApiAlias"
            ]
            packet["proofFileChecks"][0]["target"] = "Backend/proof/huawei-baota-deploy.json"
            packet["proofFileChecks"][0]["sha256"] = "already-filled"
            packet["proofFileChecks"][0]["generatedInSameRefreshRound"] = True
            packet["proofFileChecks"][0]["passedOrReadyVerified"] = True
            packet["proofFileChecks"][0]["stableAliasSyncedOnlyAfterGreen"] = True
            packet["proofFileChecks"][0]["realProofNotTemplate"] = True
            packet["separationRules"].remove("stable aliases sync only after same-round current proofs pass")
            next(
                item
                for item in packet["refreshSequence"]
                if item["step"] == "refreshProductionReadinessCurrent"
            )["command"] = "python3 Backend/scripts/check_production_readiness.py"
            packet["stopConditions"] = [
                item
                for item in packet["stopConditions"]
                if item["id"] != "smsLiveSendProofMissing"
            ]
            packet["postRefreshGates"] = [
                gate
                for gate in packet["postRefreshGates"]
                if "check_launch_blocker_action_packet.py" not in gate
            ]
            packet["completionRule"] = "done"
            write(
                root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionProofRefreshPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["productionProofRefreshPacketValid"]["evidence"]
            self.assertIn("productionProofRefreshPacket.targetProofFiles.productionReadinessCurrent must be Backend/proof/production-readiness-20260630T-current.json", evidence)
            self.assertIn("productionProofRefreshPacket.proofFileChecks order must match targetProofFiles", evidence)
            self.assertIn("productionProofRefreshPacket.proofFileChecks.stableRemoteApiAlias missing object", evidence)
            self.assertIn(
                "productionProofRefreshPacket.proofFileChecks.deploymentProofCurrent.target must be Backend/proof/huawei-baota-deploy-20260630T-current.json",
                evidence,
            )
            self.assertIn("productionProofRefreshPacket.proofFileChecks.deploymentProofCurrent.sha256 must be 'FILL_AFTER_REFRESH'", evidence)
            self.assertIn("productionProofRefreshPacket.proofFileChecks.deploymentProofCurrent.generatedInSameRefreshRound must be False", evidence)
            self.assertIn("productionProofRefreshPacket.proofFileChecks.deploymentProofCurrent.passedOrReadyVerified must be False", evidence)
            self.assertIn("productionProofRefreshPacket.proofFileChecks.deploymentProofCurrent.stableAliasSyncedOnlyAfterGreen must be False", evidence)
            self.assertIn("productionProofRefreshPacket.proofFileChecks.deploymentProofCurrent.realProofNotTemplate must be False", evidence)
            self.assertIn("productionProofRefreshPacket.separationRules missing stable aliases sync only after same-round current proofs pass", evidence)
            self.assertIn("productionProofRefreshPacket.refreshSequence.refreshProductionReadinessCurrent missing --auth-providers-proof Backend/proof/auth-providers-sms-live-20260630T-current.json", evidence)
            self.assertIn("productionProofRefreshPacket.stopConditions missing smsLiveSendProofMissing", evidence)
            self.assertIn("productionProofRefreshPacket.postRefreshGates missing check_launch_blocker_action_packet.py", evidence)
            self.assertIn("productionProofRefreshPacket.completionRule missing refresh-plan-not-evidence", evidence)

    def test_production_proof_refresh_packet_rejects_duplicate_or_reordered_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            packet = json.loads(valid_production_proof_refresh_packet())
            sequence = packet["refreshSequence"]
            packet["refreshSequence"] = [
                sequence[1],
                sequence[0],
                *sequence[2:],
                dict(sequence[-1]),
            ]
            packet["stopConditions"].append(dict(packet["stopConditions"][0]))
            write(
                root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_PACKET_20260630.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionProofRefreshPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["productionProofRefreshPacketValid"]["evidence"]
            self.assertIn("productionProofRefreshPacket.refreshSequence duplicate refreshLaunchObjectiveAudit", evidence)
            self.assertIn("productionProofRefreshPacket.refreshSequence order must match production proof refresh workflow", evidence)
            self.assertIn("productionProofRefreshPacket.stopConditions duplicate noDeployHost", evidence)

    def test_production_proof_refresh_status_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            status = json.loads(valid_production_proof_refresh_status())
            status["stableAliasSyncAllowed"] = True
            status["summary"]["stableAliasesBlocked"] = False
            status["missingProofs"] = []
            status["proofFileStatuses"][0]["target"] = "Backend/proof/huawei-baota-deploy.json"
            status["proofFileStatuses"][0]["secretScanHits"] = ["smsSecretAssignment"]
            status["secretScanFailures"] = [
                {"artifactId": "deploymentProofCurrent", "secretScanHits": ["smsSecretAssignment"]}
            ]
            write(
                root / "Docs/08_Release/PRODUCTION_PROOF_REFRESH_STATUS_20260630.json",
                json.dumps(status, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionProofRefreshStatusValid", report["failedRequiredChecks"])
            evidence = report["checks"]["productionProofRefreshStatusValid"]["evidence"]
            self.assertIn(
                "productionProofRefreshStatus.proofFileStatuses.deploymentProofCurrent.target must be Backend/proof/huawei-baota-deploy-20260630T-current.json",
                evidence,
            )
            self.assertIn("productionProofRefreshStatus.proofFileStatuses.deploymentProofCurrent.secretScanHits must be empty", evidence)
            self.assertIn("productionProofRefreshStatus.stableAliasSyncAllowed must match same-round current proof green state", evidence)
            self.assertIn("productionProofRefreshStatus.missingProofs must match missing proofFileStatuses", evidence)
            self.assertIn("productionProofRefreshStatus.summary.stableAliasesBlocked must be True", evidence)
            self.assertIn("productionProofRefreshStatus.secretScanFailures must be empty", evidence)

    def test_sms_live_send_proof_must_not_overwrite_provider_config_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Backend/deploy/aliyun-sms-webhook-adapter.md",
                valid_sms_doc()
                .replace("auth-providers-sms-live-YYYYMMDDT-current.json", "auth-providers-YYYYMMDDT-current.json")
                .replace("只有两份 auth provider proof 都通过", "auth provider proof 通过"),
            )
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                valid_external_handoff()
                .replace("Backend/proof/auth-providers-sms-live-20260630T-current.json", "Backend/proof/auth-providers-20260630T-current.json")
                .replace("只有两份 auth provider proof 都通过", "auth provider proof 通过")
                .replace("不能来自未实发短信的配置 proof", ""),
            )
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_20260630.md",
                valid_external_capture_workbench().replace(
                    "Backend/proof/auth-providers-sms-live-20260630T-current.json",
                    "Backend/proof/auth-providers-20260630T-current.json",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("smsLiveSendProofKeptSeparateFromProviderConfigProof", report["failedRequiredChecks"])
            evidence = report["checks"]["smsLiveSendProofKeptSeparateFromProviderConfigProof"]["evidence"]
            self.assertIn("Backend/proof/auth-providers-sms-live-20260630T-current.json", evidence)
            self.assertIn("不能来自未实发短信的配置 proof", evidence)

    def test_production_proof_date_rollover_rule_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                valid_external_handoff()
                .replace("## Current proof 日期滚动规则", "## Proof 日期")
                .replace("20260630T-current", "")
                .replace("不得继续把 `20260627T-current` 当成 fresh proof", "")
                .replace("proof 内时间戳", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("productionProofDateRolloverRulePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["productionProofDateRolloverRulePresent"]["evidence"]
            self.assertIn("## Current proof 日期滚动规则", evidence)
            self.assertIn("20260630T-current", evidence)
            self.assertIn("不得继续把 `20260627T-current` 当成 fresh proof", evidence)
            self.assertIn("proof 内时间戳", evidence)

    def test_external_platform_execution_template_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                valid_external_handoff()
                .replace("## 外部平台上线当天执行记录模板", "## 上线当天记录")
                .replace("auth-providers-20260630T-current.json 已证明微信 provider。", "")
                .replace("auth-providers-sms-live-20260630T-current.json 已证明真实短信实发。", "")
                .replace("production-readiness-20260630T-current.json 已变绿。", "")
                .replace("如果任一项未通过，不提交 App Store Connect 审核。", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalPlatformSameDayExecutionTemplatePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["externalPlatformSameDayExecutionTemplatePresent"]["evidence"]
            self.assertIn("## 外部平台上线当天执行记录模板", evidence)
            self.assertIn("auth-providers-20260630T-current.json 已证明微信 provider", evidence)
            self.assertIn("auth-providers-sms-live-20260630T-current.json 已证明真实短信实发", evidence)
            self.assertIn("production-readiness-20260630T-current.json 已变绿", evidence)
            self.assertIn("如果任一项未通过，不提交 App Store Connect 审核", evidence)

    def test_external_platform_evidence_index_and_redaction_review_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                valid_external_handoff()
                .replace("## 外部平台证据索引与脱敏复核", "## 证据索引")
                .replace("verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE", "")
                .replace("Backend/proof/auth-providers-sms-live-20260630T-current.json", "")
                .replace("Backend/proof/huawei-baota-deploy-20260630T-current.json", "Backend/proof/huawei-baota-deploy.json")
                .replace("HUAWEI_OBS_SECRET_ACCESS_KEY", "")
                .replace("check_app_store_evidence.py --allow-incomplete", "check_app_store_evidence.py")
                .replace("稳定 alias", "alias"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalPlatformEvidenceIndexAndRedactionReviewPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["externalPlatformEvidenceIndexAndRedactionReviewPresent"]["evidence"]
            self.assertIn("## 外部平台证据索引与脱敏复核", evidence)
            self.assertIn("verify_auth_providers.py --send-test-sms --require-sms-live-send", evidence)
            self.assertIn("Backend/proof/auth-providers-sms-live-20260630T-current.json", evidence)
            self.assertIn("Backend/proof/huawei-baota-deploy-20260630T-current.json", evidence)
            self.assertIn("HUAWEI_OBS_SECRET_ACCESS_KEY", evidence)
            self.assertIn("check_app_store_evidence.py --allow-incomplete", evidence)
            self.assertIn("稳定 alias", evidence)

    def test_external_platform_capture_workbench_must_use_current_day_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            stale_workbench = (
                valid_external_capture_workbench()
                .replace("20260630T-current", "20260627T-current")
                .replace("XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md", "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260627.md")
                .replace("APP_STORE_CONNECT_COPY_PASTE_20260630.md", "APP_STORE_CONNECT_COPY_PASTE_20260627.md")
                .replace("EXECUTION_SHEET_20260630.md", "EXECUTION_SHEET_20260627.md")
                .replace("--date 2026-06-30", "--date 2026-06-27")
            )
            stale_workbench += (
                "\n旧提交守卫：`canSubmit=true`。\n"
                "npm --prefix \"/Users/smianmian/Emotion Isle\" run check-cross-app-submit-ready "
                "-- --date 2026-06-30 --output output/cross-app-submission-readiness-20260630-current.json\n"
            )
            write(root / "Docs/08_Release/XNP_EXTERNAL_PLATFORM_CAPTURE_WORKBENCH_20260630.md", stale_workbench)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalPlatformCaptureWorkbenchCurrent", report["failedRequiredChecks"])
            evidence = report["checks"]["externalPlatformCaptureWorkbenchCurrent"]["evidence"]
            self.assertIn("stale: 20260627T-current", evidence)
            self.assertIn("check-cross-app-submit-ready", evidence)
            self.assertIn("`canSubmit=true`", evidence)
            self.assertIn("XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260627.md", evidence)
            self.assertIn("APP_STORE_CONNECT_COPY_PASTE_20260627.md", evidence)
            self.assertIn("AppStoreEvidence/RealDevice/EXECUTION_SHEET_20260627.md", evidence)
            self.assertIn("--date 2026-06-27", evidence)


if __name__ == "__main__":
    unittest.main()
