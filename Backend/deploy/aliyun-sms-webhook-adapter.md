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

`Backend/scripts/verify_auth_providers.py` 会检查短信 provider 配置；adapter 必须保留 HMAC-SHA256 签名校验、`/healthz` 和 `/send` 端点、阿里云 `SendSms` 调用、mock 关闭的 env 示例、systemd 私有 `EnvironmentFile`，以及主 API 的本机 webhook env 示例。配置检查只证明链路具备，不代表短信服务商截图或真实运营商实发已完成。

## 主 API 私有环境

`/srv/xiaonaiping/private/xiaonaiping-api.env` 里配置：

```bash
XNP_SMS_PROVIDER=webhook
XNP_SMS_WEBHOOK_URL=http://127.0.0.1:8791/send
XNP_SMS_SECRET=<same-random-secret-as-adapter>
XNP_SMS_TEMPLATE_ID=SMS_508990073
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
ALIYUN_SIGN_NAME=深圳市闪现生活科技
ALIYUN_TEMPLATE_CODE=SMS_508990073
ALIYUN_REGION_ID=cn-hangzhou
ALIYUN_SMS_ENDPOINT=https://dysmsapi.aliyuncs.com
```

建议使用只允许 `dysms:SendSms` 的 RAM 子账号，不要复用一根呆毛生产数据库、服务名或日志目录。

## 部署步骤

常规后端部署使用 `Backend/deploy/deploy-huawei-baota.sh`。当主 API 私有环境里的
`XNP_SMS_PROVIDER=webhook` 且 `XNP_SMS_WEBHOOK_URL=http://127.0.0.1:8791/send`
时，部署脚本会要求 `/srv/xiaonaiping/private/xiaonaiping-aliyun-sms-adapter.env`
存在，安装 `xiaonaiping-aliyun-sms-adapter.service`，重启服务，并检查
`http://127.0.0.1:8791/healthz`。

手工补救步骤如下：

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

先在本地私密 shell 或私有 env 文件里设置 `XNP_SMS_TEST_PHONE`，不要 echo 这个值，不要把完整手机号写进命令历史、截图、日志或仓库文件。

```bash
python3 Backend/scripts/verify_auth_providers.py \
  --deployment-proof Backend/proof/huawei-baota-deploy.json \
  --base-url https://api.mewpow.com/xiaonaiping \
  --live-check \
  --send-test-sms \
  --require-sms-live-send \
  --phone-env XNP_SMS_TEST_PHONE \
  --output Backend/proof/auth-providers-sms-live-YYYYMMDDT-current.json
```

上线当天不要用同一个 `--output` 覆盖配置 proof。先把 provider 配置检查写入 `Backend/proof/auth-providers-YYYYMMDDT-current.json`，再把真实短信实发检查写入 `Backend/proof/auth-providers-sms-live-YYYYMMDDT-current.json`。只有两份 auth provider proof 都通过，且 `07-sms-provider.png` / `.pdf` / `.json` 已归档后，才能把 sms-live proof 同步到 `Backend/proof/auth-providers.json` 作为稳定 alias。

不要在输出、截图或提交说明里暴露验证码、AccessKey、`XNP_SMS_SECRET`、`XNP_SMS_TEST_PHONE` 的完整值。

## App Store 证据归档

短信服务商人工证据归档到 `Docs/08_Release/AppStoreEvidence/07-sms-provider.png`，也可使用同名 `.pdf` 或 `.json`。截图必须能证明：

1. 服务商为阿里云 Dysmsapi 或最终生产短信服务商。
2. 已通过短信签名和模板审核，可看到签名、模板 ID / 名称、模板审核状态和发送区域。
3. 验证码模板只用于账号登录/验证，不含营销、不含医疗、不含育儿建议，不写健康建议、喂养建议、医疗诊断、治疗建议或专业疫苗建议。
4. 生产链路使用 `XNP_SMS_SECRET` + HMAC-SHA256 保护 webhook，adapter 只允许 RAM 子账号调用 `dysms:SendSms`。
5. 测试发送状态为成功，且对应 `Backend/proof/auth-providers.json` 的真实发送或 provider 检查。

截图或导出文件必须遮挡 AccessKey、Secret、`XNP_SMS_SECRET`、完整手机号和验证码；只能保留服务商名称、签名、模板、发送成功状态和必要的脱敏手机号片段。

## 短信服务商截图字段清单

| 截图/导出项 | 必须保留 | 必须遮挡 |
|---|---|---|
| 短信服务商控制台 | 服务商名称、阿里云 Dysmsapi 或最终生产短信服务商 | 登录账号、无关业务 |
| 短信签名 | 已审核通过的签名名称和审核状态 | 无关账号信息 |
| 验证码模板 | 模板 ID / 名称、账号登录/验证用途、模板内容摘要、模板审核状态、发送区域；不含营销、不含医疗、不含育儿建议 | 验证码示例明文 |
| 发送成功记录 | 发送成功状态、发送时间、脱敏手机号片段 | 完整手机号、验证码 |
| RAM / 权限边界 | 只允许 `dysms:SendSms` 的最小权限说明 | AccessKey、Secret |
| 小奶瓶服务端 proof | `Backend/proof/auth-providers.json` 中短信 provider / live send 结果 | `XNP_SMS_SECRET`、token、完整手机号 |

真实实发验证必须使用 `verify_auth_providers.py --send-test-sms --require-sms-live-send --phone-env XNP_SMS_TEST_PHONE` 单独触发；默认 `verify_auth_providers.py --live-check` 只证明 provider 配置存在，不替代短信服务商截图或真实实发截图。
