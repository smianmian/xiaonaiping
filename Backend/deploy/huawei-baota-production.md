# Huawei Cloud + Baota Production Runbook

## Scope

- Project: 小奶瓶 / XiaoNaiPing
- Target: Huawei Cloud China mainland ECS with Baota-managed MySQL
- Company: 深圳市闪现生活科技有限公司
- Rule: never reuse Emotion App databases, users, directories, ports, process names, buckets, or Nginx sites

This file is a secret-free public handoff. Real IPs, passwords, certificates, Baota panel URLs, and access keys must stay only on the server or in private ops records.

## Dedicated Names

Use XiaoNaiPing-specific names only:

| Item | Required namespace |
|---|---|
| Deploy directory | `/srv/xiaonaiping` |
| Data directory | `/srv/xiaonaiping/data` |
| Private env | `/srv/xiaonaiping/private/xiaonaiping-api.env` |
| Linux user | `xiaonaiping` |
| systemd service | `xiaonaiping-api.service` |
| Internal API port | `8787`, or another XiaoNaiPing-only port |
| MySQL database | `xiaonaiping_prod` |
| MySQL user | `xiaonaiping_app` |
| OBS bucket/prefix | bucket containing `xiaonaiping`, prefix `xiaonaiping` |

Do not use names containing `emotion`, `ydm`, `daimao`, `一根呆毛`, or `情绪`.

## Baota MySQL Setup

In the Baota panel, create a fresh MySQL database:

1. Database name: `xiaonaiping_prod`
2. Database user: `xiaonaiping_app`
3. Charset: `utf8mb4`
4. Permission scope: only `xiaonaiping_prod`
5. Remote access: off unless the database is on a private network and explicitly needed

The app only needs normal CRUD privileges on its own database. Do not grant access to any Emotion App schema.

## Server Directories

Run these as an administrator on the Huawei Cloud ECS:

```bash
sudo useradd --system --home /srv/xiaonaiping --shell /usr/sbin/nologin xiaonaiping || true
sudo mkdir -p /srv/xiaonaiping/current /srv/xiaonaiping/releases /srv/xiaonaiping/private /srv/xiaonaiping/data
sudo chown -R xiaonaiping:xiaonaiping /srv/xiaonaiping
sudo chmod 700 /srv/xiaonaiping/private
```

Upload the secret-free backend bundle to a new release directory under `/srv/xiaonaiping/releases/`, then point `/srv/xiaonaiping/current` to that release. Do not upload production `.env` files from a developer machine into git.

## Private Env

Create `/srv/xiaonaiping/private/xiaonaiping-api.env` from `Backend/deploy/production-config.example`, replacing every placeholder privately.

Minimum production values:

```bash
XNP_DEPLOYMENT_TARGET=huawei_baota
XNP_HOST=127.0.0.1
XNP_PORT=8787
XNP_DATA_DIR=/srv/xiaonaiping/data
XNP_DATABASE_BACKEND=mysql
XNP_MYSQL_HOST=127.0.0.1
XNP_MYSQL_PORT=3306
XNP_MYSQL_USER=xiaonaiping_app
XNP_MYSQL_DATABASE=xiaonaiping_prod
XNP_STORAGE_BACKEND=huawei_obs
HUAWEI_OBS_PREFIX=xiaonaiping
```

For Aliyun SMS, set the main API webhook to the local adapter:

```bash
XNP_SMS_PROVIDER=webhook
XNP_SMS_WEBHOOK_URL=http://127.0.0.1:8791/send
XNP_SMS_TEMPLATE_ID=<approved-aliyun-template-code>
```

Keep `XNP_SECRET_KEY`, `XNP_ADMIN_TOKEN`, `XNP_MYSQL_PASSWORD`, `HUAWEI_OBS_ACCESS_KEY_ID`, `HUAWEI_OBS_SECRET_ACCESS_KEY`, SMS secrets, Aliyun AccessKey values, and WeChat secrets private.

## Install And Migrate

```bash
cd /srv/xiaonaiping/current/Backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-production.txt
set -a
. /srv/xiaonaiping/private/xiaonaiping-api.env
set +a
python3 scripts/migrate_database.py
```

The migration must create only XiaoNaiPing tables inside `xiaonaiping_prod`.

## Direct Deploy From Local

After local backend changes are ready, deploy only the XiaoNaiPing backend with:

```bash
XNP_DEPLOY_HOST=root@YOUR_SERVER \
XNP_API_BASE_URL=https://YOUR_XIAONAIPING_API_DOMAIN \
Backend/deploy/deploy-huawei-baota.sh
```

The script builds a secret-free backend bundle, uploads it to a new `/srv/xiaonaiping/releases/<timestamp>` release, runs migrations with the private server env, switches `/srv/xiaonaiping/current`, restarts only `xiaonaiping-api.service`, and refreshes remote API, storage backend, and deployment proof JSON files. It refuses non-`xiaonaiping` deploy roots and non-`xiaonaiping-api.service` services.

## systemd

Copy `Backend/deploy/xiaonaiping-api.service.example` to:

```bash
sudo cp Backend/deploy/xiaonaiping-api.service.example /etc/systemd/system/xiaonaiping-api.service
sudo systemctl daemon-reload
sudo systemctl enable xiaonaiping-api
sudo systemctl restart xiaonaiping-api
sudo systemctl status xiaonaiping-api --no-pager
```

Only restart `xiaonaiping-api`. Do not restart PM2, Node, or Emotion App services.

For Aliyun SMS, copy `Backend/deploy/xiaonaiping-aliyun-sms-adapter.service.example` to:

```bash
sudo cp Backend/deploy/xiaonaiping-aliyun-sms-adapter.service.example /etc/systemd/system/xiaonaiping-aliyun-sms-adapter.service
sudo systemctl daemon-reload
sudo systemctl enable xiaonaiping-aliyun-sms-adapter
sudo systemctl restart xiaonaiping-aliyun-sms-adapter
curl -fsS http://127.0.0.1:8791/healthz
```

The adapter uses `/srv/xiaonaiping/private/xiaonaiping-aliyun-sms-adapter.env`; do not store Aliyun AccessKey values in the main repo.

## Baota Nginx Site

Create a separate Baota website for the XiaoNaiPing API domain. Use `Backend/deploy/nginx.conf.example` as the reverse-proxy baseline:

- public API routes proxy to `http://127.0.0.1:8787`
- `/internal/` is restricted to private office/VPN ranges
- upload size is at least `25m`
- HTTPS certificate matches the XiaoNaiPing API domain

Do not edit an existing Emotion App Nginx site.

## Verification

Run these from a trusted machine after DNS and HTTPS are ready:

```bash
curl -fsS https://YOUR_XIAONAIPING_API_DOMAIN/healthz
python3 Backend/scripts/collect_deployment_proof.py \
  --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
  --base-url https://YOUR_XIAONAIPING_API_DOMAIN \
  --service-active \
  --public-internal-blocked \
  --output Backend/proof/huawei-baota-deploy-YYYYMMDD.json
export XNP_REMOTE_TEST_PHONE=+8613800000000
python3 Backend/scripts/verify_remote_api.py --base-url https://YOUR_XIAONAIPING_API_DOMAIN --phone "$XNP_REMOTE_TEST_PHONE" --output Backend/proof/remote-api.json
python3 Backend/scripts/verify_auth_providers.py --live-check --base-url https://YOUR_XIAONAIPING_API_DOMAIN --output Backend/proof/auth-providers.json
python3 Backend/scripts/check_diagnostics_redaction.py --output Backend/proof/diagnostics-redaction.json
python3 Backend/scripts/check_public_pages.py --output Backend/proof/public-pages.json
python3 Backend/scripts/check_review_notes.py --output Backend/proof/review-notes.json
python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json
XNP_API_BASE_URL=https://YOUR_XIAONAIPING_API_DOMAIN \
python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --live-check --output Backend/proof/production-readiness.json
```

`collect_deployment_proof.py` must be run only on the server or a trusted machine that can read the private env. It records which secret keys are present without writing secret values to JSON. Do not paste raw private env files into chat, tickets, or git.
`verify_auth_providers.py` does not send SMS unless explicitly run with `--send-test-sms --phone-env XNP_SMS_TEST_PHONE`; run that final carrier test only after the Aliyun SMS sign, template, RAM credentials, and adapter service are configured.

The production readiness report must pass these isolation checks:

- `xiaonaipingProductionNamespaceConfigured`
- `sharedServiceNamespaceRejected`

## Rollback

Rollback must only touch XiaoNaiPing:

```bash
sudo ln -sfn /srv/xiaonaiping/releases/PREVIOUS_RELEASE /srv/xiaonaiping/current
sudo systemctl restart xiaonaiping-api
```

Do not roll back shared Nginx, shared MySQL, or any Emotion App service as part of a XiaoNaiPing rollback.
