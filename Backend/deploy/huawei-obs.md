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
   `python3 Backend/scripts/verify_remote_api.py --base-url https://api.mewpow.com/xiaonaiping --output Backend/proof/remote-api.json`
3. Production readiness verification:
   `python3 Backend/scripts/check_production_readiness.py --base-url https://api.mewpow.com/xiaonaiping --require-huawei-obs --require-screenshots --require-app-store-evidence --live-check --output Backend/proof/production-readiness.json`
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
9. Legal drafts verification:
   `python3 Backend/scripts/check_legal_drafts.py --output Backend/proof/legal-drafts.json`
10. Universal Links verification:
   `python3 Backend/scripts/check_universal_links.py --output Backend/proof/universal-links.json`
11. Secret-free deployment bundle:
   `python3 Backend/scripts/build_deploy_bundle.py --output-dir Backend/proof/deploy-bundles`
12. OBS lifecycle and sync settings screenshot or exported policy.
13. Deletion proof showing account sync and photo objects are gone after `DELETE /v1/account`.

## App Store Evidence Archive

Archive Huawei OBS manual evidence to `Docs/08_Release/AppStoreEvidence/09-obs-policy.png`, or the same stem as `.pdf` / `.json`. The capture must show:

1. A private bucket for XiaoNaiPing, with bucket, prefix, and 区域 visible.
2. Server-side access only: keep iOS clients on the first-party API and keep server-side AK/SK off the app.
3. Encryption enabled or exported policy showing the production 加密 status.
4. Lifecycle rules for sync/photo objects.
5. 删除验证 showing account sync and photo objects are removed after `DELETE /v1/account`.

The evidence must redact AK/SK, full object key / 完整对象 key, internal private paths, baby names, birthdays, notes, and original filenames.

## OBS 私有访问与删除验证执行包

结构化执行包见 `Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260704.json`。该 JSON 只用于上线当天按顺序核对 OBS 后台截图、storage proof、production readiness 和稳定 alias 同步；它不是证据、不是 OBS 密钥容器，也不能作为提交许可。

执行包必须保持这些边界：

1. `09-obs-policy.png` 或同 stem PDF/JSON 只证明后台私有策略截图，不等于 `Backend/proof/storage-backend-20260704T-current.json`。
2. `storage-backend-20260704T-current.json` 只证明服务端对象存储 upload/download/delete 和删除验证，不等于 App Store 手工证据。
3. `production-readiness-20260704T-current.json` 必须同轮读取 storage proof 和 App Store evidence；不能只靠旧的 `production-readiness.json`。
4. 只有 current storage proof、production readiness 和 App Store evidence 都变绿后，才同步 `Backend/proof/storage-backend.json` 和 `Backend/proof/production-readiness.json` 稳定 alias。
5. 不保存 public bucket、signed URL、完整对象 key、真实宝宝照片、AK/SK、SecretKey、账号 ID 或私有服务器路径。
