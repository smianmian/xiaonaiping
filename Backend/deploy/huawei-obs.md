# Huawei Cloud OBS Handoff

This handoff keeps production secrets out of the repository. Use it only in the private deployment workspace.

## Backend Mode

Set:

```bash
XNP_STORAGE_BACKEND=huawei_obs
HUAWEI_OBS_ACCESS_KEY_ID=...
HUAWEI_OBS_SECRET_ACCESS_KEY=...
HUAWEI_OBS_ENDPOINT=...
HUAWEI_OBS_BUCKET=...
HUAWEI_OBS_PREFIX=xiaonaiping
```

Install the optional SDK:

```bash
pip install -r Backend/requirements-obs.txt
```

## Bucket Rules

1. Use a private bucket.
2. Do not allow public object listing or public object reads.
3. Do not place baby names, birthdays, notes, or original filenames in object keys.
4. Keep server-side AK/SK only on the backend host or secret manager.
5. Keep iOS clients on the first-party API; do not give the app direct OBS write credentials.
6. Verify account deletion removes all objects under `HUAWEI_OBS_PREFIX/{accountId}/`.
7. Run `python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend.json` with the production private env loaded.

## Evidence Required Before App Store Submit

1. API health check over HTTPS.
2. Release-flow verification against the production API:
   `export XNP_REMOTE_TEST_PHONE=+8613800000000; python3 Backend/scripts/verify_remote_api.py --base-url https://api.mewpow.com/xiaonaiping --phone "$XNP_REMOTE_TEST_PHONE" --output Backend/proof/remote-api.json`（会在终端提示输入该手机号收到的短信验证码）。
3. Production readiness verification:
   `python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --require-huawei-obs --require-screenshots --live-check --output Backend/proof/production-readiness.json`
4. Object storage verification:
   `python3 Backend/scripts/verify_storage_backend.py --output Backend/proof/storage-backend.json`
5. Auth provider verification:
   `python3 Backend/scripts/verify_auth_providers.py --live-check --output Backend/proof/auth-providers.json`
6. Diagnostics redaction verification:
   `python3 Backend/scripts/check_diagnostics_redaction.py --output Backend/proof/diagnostics-redaction.json`
7. Public pages verification:
   `python3 Backend/scripts/check_public_pages.py --output Backend/proof/public-pages.json`
8. Review Notes verification:
   `python3 Backend/scripts/check_review_notes.py --output Backend/proof/review-notes.json`
9. Universal Links verification:
   `python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json`
10. Secret-free deployment bundle:
   `python3 Backend/scripts/build_deploy_bundle.py --output-dir Backend/proof/deploy-bundles`
11. OBS lifecycle and sync settings screenshot or exported policy.
12. Deletion proof showing account sync and photo objects are gone after `DELETE /v1/account`.

## App Store Evidence Archive

Archive Huawei OBS manual evidence to `Docs/08_Release/AppStoreEvidence/09-obs-policy.png`, or the same stem as `.pdf` / `.json`. The capture must show:

1. A private bucket for XiaoNaiPing, with bucket, prefix, and 区域 visible.
2. Server-side access only: keep iOS clients on the first-party API and keep server-side AK/SK off the app.
3. Encryption enabled or exported policy showing the production 加密 status.
4. Lifecycle rules for sync/photo objects.
5. 删除验证 showing account sync and photo objects are removed after `DELETE /v1/account`.

The evidence must redact AK/SK, full object key / 完整对象 key, internal private paths, baby names, birthdays, notes, and original filenames.
