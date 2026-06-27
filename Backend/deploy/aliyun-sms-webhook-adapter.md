# Aliyun SMS Webhook Adapter

小奶瓶主 API 不直接接入阿里云短信 SDK。生产短信链路为：

1. iOS 请求 `POST /v1/auth/phone/request-code`。
2. 小奶瓶 API 生成 6 位验证码，写入 `phone_login_codes`。
3. 小奶瓶 API 用 `XNP_SMS_SECRET` 对 webhook body 做 HMAC-SHA256。
4. 本机 adapter 校验 `X-XNP-Signature`。
5. adapter 使用阿里云 Dysmsapi `SendSms` 发送验证码。

## 文件

- Adapter：`Backend/sms/aliyun-webhook-adapter/server.js`
- 主 API env 示例：`Backend/deploy/production-config.example`
- Adapter env 示例：`Backend/deploy/aliyun-sms-adapter.env.example`
- systemd 示例：`Backend/deploy/xiaonaiping-aliyun-sms-adapter.service.example`

## 主 API 私有环境

`/srv/xiaonaiping/private/xiaonaiping-api.env` 里配置：

```bash
XNP_SMS_PROVIDER=webhook
XNP_SMS_WEBHOOK_URL=http://127.0.0.1:8791/send
XNP_SMS_SECRET=<same-random-secret-as-adapter>
XNP_SMS_TEMPLATE_ID=<approved-aliyun-template-code>
```

`XNP_SMS_SECRET` 必须是随机共享密钥，不能进入仓库、客户端或聊天记录。

## Adapter 私有环境

`/srv/xiaonaiping/private/xiaonaiping-aliyun-sms-adapter.env` 里配置：

```bash
XNP_SMS_ADAPTER_HOST=127.0.0.1
XNP_SMS_ADAPTER_PORT=8791
XNP_SMS_SECRET=<same-random-secret-as-main-api>
XNP_SMS_ADAPTER_MOCK=0

ALIYUN_ACCESS_KEY_ID=<aliyun-ram-access-key-id>
ALIYUN_ACCESS_KEY_SECRET=<aliyun-ram-access-key-secret>
ALIYUN_SIGN_NAME=<approved-sign-name>
ALIYUN_TEMPLATE_CODE=<approved-template-code>
ALIYUN_REGION_ID=cn-hangzhou
ALIYUN_SMS_ENDPOINT=https://dysmsapi.aliyuncs.com
```

建议使用只允许 `dysms:SendSms` 的 RAM 子账号，不要复用一根呆毛生产数据库、服务名或日志目录。

## 部署步骤

```bash
cd /srv/xiaonaiping/current/Backend/sms/aliyun-webhook-adapter
npm install --omit=dev --no-audit --no-fund

sudo cp /srv/xiaonaiping/current/Backend/deploy/xiaonaiping-aliyun-sms-adapter.service.example \
  /etc/systemd/system/xiaonaiping-aliyun-sms-adapter.service
sudo systemctl daemon-reload
sudo systemctl enable --now xiaonaiping-aliyun-sms-adapter.service
```

健康检查：

```bash
curl -fsS http://127.0.0.1:8791/healthz
```

## 验证

不实际发短信的本地测试：

```bash
python3 -m unittest Backend.tests.test_aliyun_sms_adapter
```

生产发短信前先跑离线门禁：

```bash
python3 Backend/scripts/verify_auth_providers.py \
  --deployment-proof Backend/proof/huawei-baota-deploy.json \
  --base-url https://api.mewpow.com/xiaonaiping \
  --live-check \
  --output Backend/proof/auth-providers.json
```

最终运营商实发测试需要显式传入测试手机号：

```bash
python3 Backend/scripts/verify_auth_providers.py \
  --deployment-proof Backend/proof/huawei-baota-deploy.json \
  --base-url https://api.mewpow.com/xiaonaiping \
  --live-check \
  --send-test-sms \
  --require-sms-live-send \
  --phone <redacted-test-phone> \
  --output Backend/proof/auth-providers.json
```

不要在输出、截图或提交说明里暴露验证码、AccessKey、`XNP_SMS_SECRET`。

## App Store 证据归档

短信服务商人工证据归档到 `Docs/08_Release/AppStoreEvidence/07-sms-provider.png`，也可使用同名 `.pdf` 或 `.json`。截图必须能证明：

1. 服务商为阿里云 Dysmsapi 或最终生产短信服务商。
2. 已通过短信签名和模板审核，可看到签名、模板 ID / 名称和发送区域。
3. 生产链路使用 `XNP_SMS_SECRET` + HMAC-SHA256 保护 webhook，adapter 只允许 RAM 子账号调用 `dysms:SendSms`。
4. 测试发送状态为成功，且对应 `Backend/proof/auth-providers.json` 的真实发送或 provider 检查。

截图或导出文件必须遮挡 AccessKey、Secret、`XNP_SMS_SECRET`、完整手机号和验证码；只能保留服务商名称、签名、模板、发送成功状态和必要的脱敏手机号片段。
