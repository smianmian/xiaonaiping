# XiaoNaiPing Backend

This is the first-party minimal backend for the V1 App Store path. It covers account recovery keys, authenticated sync/restore, private photo object storage, account deletion, and privacy-safe first-party analytics.

It intentionally does not include a user-content admin console, third-party analytics SDKs, subscriptions, public sharing, or client-side cloud credentials. It includes a private aggregate-only operations and analytics dashboard.

## Local Run

```bash
cd Backend
XNP_SECRET_KEY=replace-in-private-deploy XNP_DATA_DIR=.xnp-data python3 api/server.py
```

The local API listens on `http://127.0.0.1:8787` by default.

## Required Endpoints

- `POST /v1/accounts`
- `POST /v1/sessions/recover`
- `POST /v1/auth/phone/request-code`
- `POST /v1/auth/phone/verify`
- `POST /v1/auth/wechat/login`
- `GET /v1/account`
- `PUT /v1/sync`
- `GET /v1/sync`
- `PUT /v1/photos/{photoId}`
- `GET /v1/photos`
- `GET /v1/photos/{photoId}`
- `DELETE /v1/photos/{photoId}`
- `DELETE /v1/account`
- `POST /v1/analytics/events`
- `GET /internal/dashboard`
- `GET /internal/metrics` with `Authorization: Bearer <XNP_ADMIN_TOKEN>`

All endpoints except account creation, recovery, phone auth, WeChat auth, health, and public pages require `Authorization: Bearer <sessionToken>`.
Phone login supports a production SMS webhook provider via `XNP_SMS_PROVIDER=webhook`, `XNP_SMS_WEBHOOK_URL`, and `XNP_SMS_SECRET`. A XiaoNaiPing-only Aliyun Dysmsapi adapter is available in `Backend/sms/aliyun-webhook-adapter`; see `Backend/deploy/aliyun-sms-webhook-adapter.md`. WeChat login exchanges the iOS authorization code with WeChat Open Platform via `XNP_WECHAT_APP_ID` and `XNP_WECHAT_APP_SECRET`. `XNP_AUTH_DEBUG_MODE=1` is only for local tests and screenshots.
Analytics uses only first-party whitelisted events and enum properties. It rejects user content, baby profile data, photo keys, phone numbers, WeChat identifiers, recovery keys, tokens, location, User-Agent, and device fingerprints.

## Storage

- SQLite stores accounts, latest JSON sync payloads, photo metadata, deletion audit rows, and whitelisted analytics events.
- Production uses MySQL with `XNP_DATABASE_BACKEND=mysql` and the `XNP_MYSQL_*` variables. The current mainland target is Huawei Cloud ECS with a Baota-managed XiaoNaiPing-only MySQL database.
- In local/default mode, photo binaries are stored under `XNP_DATA_DIR/objects/{accountId}/photos`.
- In Huawei Cloud mode, set `XNP_STORAGE_BACKEND=huawei_obs` and configure the `HUAWEI_OBS_*` environment variables from a private env file.
- Account deletion marks the account deleted, removes sync rows, removes photo metadata, deletes the account object directory, and removes that account's analytics events.

## Verification

```bash
cd Backend
python3 -m unittest tests/test_api.py
python3 ../Backend/scripts/verify_release_flow.py --output ../Backend/proof/release-flow.json
```

`Backend/proof/release-flow.json` records a local release-flow proof covering account creation, sync upload/restore, photo upload/list/download, recovery key login, account deletion, and token rejection after deletion.

After deploying a real HTTPS API, run:

```bash
python3 Backend/scripts/verify_remote_api.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/remote-api.json
python3 Backend/scripts/verify_auth_providers.py --live-check --output Backend/proof/auth-providers.json
python3 Backend/scripts/check_diagnostics_redaction.py --output Backend/proof/diagnostics-redaction.json
python3 Backend/scripts/check_public_pages.py --output Backend/proof/public-pages.json
python3 Backend/scripts/check_review_notes.py --output Backend/proof/review-notes.json
python3 Backend/scripts/check_legal_drafts.py --output Backend/proof/legal-drafts.json
python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json
python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --require-huawei-obs --require-screenshots --require-app-store-evidence --live-check --output Backend/proof/production-readiness.json
```

Remote API, auth provider, storage, iOS bundle, App Store evidence, and production readiness reports must all pass before App Store submission.

## Production Database

Install the production dependencies and initialize the schema before starting the service:

```bash
pip install -r Backend/requirements-production.txt
XNP_DATABASE_BACKEND=mysql python3 Backend/scripts/migrate_database.py
```

Required MySQL variables are `XNP_MYSQL_HOST`, `XNP_MYSQL_PORT`, `XNP_MYSQL_USER`, `XNP_MYSQL_PASSWORD`, and `XNP_MYSQL_DATABASE`. For Baota MySQL on the same Huawei Cloud ECS, use a XiaoNaiPing-only database such as `xiaonaiping_prod` and user such as `xiaonaiping_app`.

The private dashboard is available at `/internal/dashboard` only from local/private clients. Public `X-Forwarded-For` clients receive `404` even if a reverse proxy accidentally forwards the route. Its aggregate API is disabled until `XNP_ADMIN_TOKEN` is configured; the token must not be placed in the iOS app.

Use `Backend/deploy/production-config.example` as the private environment-file checklist. Replace every placeholder outside the repository. The Nginx example denies public access to `/internal/` and only permits private-network source ranges; this proxy proof is still required before release.

Use `Backend/deploy/huawei-baota-production.md` for the Huawei Cloud + Baota MySQL production handoff. Production readiness rejects deployment values that point at Emotion/YDM/Daimao namespaces.

## Production Handoff

Production deployment must provide:

- A private `XNP_SECRET_KEY`.
- A private `XNP_DATA_DIR` with syncs enabled.
- Huawei Cloud + Baota MySQL configuration and a successful `Backend/scripts/migrate_database.py` run.
- HTTPS termination and request size limits in the reverse proxy.
- A real API domain configured in the iOS Release build through `XNP_API_BASE_URL`.
- Production SMS webhook configuration for phone login: `XNP_SMS_PROVIDER=webhook`, `XNP_SMS_WEBHOOK_URL`, `XNP_SMS_SECRET`, and optional `XNP_SMS_TEMPLATE_ID`.
- If using Aliyun SMS, run the separate `xiaonaiping-aliyun-sms-adapter.service` with its own private env file and approved Aliyun sign/template.
- WeChat Open Platform AppID/AppSecret and iOS URL Scheme/Universal Link setup for WeChat login. `XNP_WECHAT_ACCESS_TOKEN_URL` is optional and defaults to WeChat's access-token endpoint.
- Auth provider proof from `Backend/scripts/verify_auth_providers.py`. The script checks SMS/WeChat provider configuration and public rejection of `debug_wechat_*` without exposing secrets; it only sends a real SMS when explicitly run with `--send-test-sms --phone-env XNP_SMS_TEST_PHONE`.
- Diagnostics redaction proof from `Backend/scripts/check_diagnostics_redaction.py`, including redacted photo object paths in backend request logs.
- Public page proof from `Backend/scripts/check_public_pages.py`, keeping privacy, terms, and support copy aligned with the launch region and account methods.
- Review Notes proof from `Backend/scripts/check_review_notes.py`, keeping App Store review notes aligned with privacy, sync, deletion, vaccine, and debug-code boundaries.
- Legal draft proof from `Backend/scripts/check_legal_drafts.py`, keeping privacy policy and terms drafts current, company-specific, China-mainland-first, and aligned with phone/WeChat/recovery-key accounts.
- Universal Links proof from `Backend/scripts/check_universal_links.py`, keeping AASA hosting, iOS Associated Domains, and WeChat callback paths aligned.
- Object storage lifecycle, sync, and deletion verification evidence in the release proof pack.
- A private `XNP_ADMIN_TOKEN` with the dashboard restricted by Nginx/VPN or an equivalent internal access control.
- Optional Huawei Cloud OBS setup is documented in `Backend/deploy/huawei-obs.md`.

Build a secret-free deployment bundle for handoff:

```bash
python3 Backend/scripts/build_deploy_bundle.py --output-dir Backend/proof/deploy-bundles
```

The generated manifest records file hashes and confirms that private `.env` files are not included.
