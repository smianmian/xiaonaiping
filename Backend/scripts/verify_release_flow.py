#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.server import ServerConfig, create_http_server
from api.storage import DiskObjectStorage


def request(base_url: str, method: str, path: str, body: Any = None, token: str | None = None, content_type: str = "application/json"):
    data = None
    headers = {}
    if body is not None:
        if isinstance(body, bytes):
            data = body
        else:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = content_type
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request_obj = urllib.request.Request(base_url + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request_obj, timeout=10) as response:
        response_body = response.read()
        response_type = response.headers.get("Content-Type", "")
        if response_type.startswith("application/json"):
            return response.status, json.loads(response_body.decode("utf-8"))
        return response.status, response_body


def run_flow() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tempdir:
        data_dir = Path(tempdir)
        config = ServerConfig(
            data_dir=data_dir,
            secret_key="release-flow-local-secret",
            object_storage=DiskObjectStorage(data_dir / "objects"),
            auth_debug_mode=True,
        )
        server = create_http_server("127.0.0.1", 0, config)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

        try:
            started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            status, created = request(base_url, "POST", "/v1/accounts")
            token = created["sessionToken"]

            backup = {
                "schemaVersion": 1,
                "baby": {"name": "ReleaseFlowBaby", "birthDate": "2026-06-01"},
                "feedingRecords": [{"id": "feeding-1", "amountML": 90}],
                "photoIds": ["photo_release_1"],
            }
            backup_bytes = json.dumps(backup, ensure_ascii=False).encode("utf-8")
            status, backup_upload = request(base_url, "PUT", "/v1/backup", backup, token=token)
            status, backup_restore = request(base_url, "GET", "/v1/backup", token=token)

            photo_bytes = b"release-flow-photo-bytes"
            status, photo_upload = request(
                base_url,
                "PUT",
                "/v1/photos/photo_release_1",
                photo_bytes,
                token=token,
                content_type="image/jpeg",
            )
            status, photo_list = request(base_url, "GET", "/v1/photos", token=token)
            status, photo_download = request(base_url, "GET", "/v1/photos/photo_release_1", token=token)
            status, recovered = request(base_url, "POST", "/v1/sessions/recover", {"recoveryKey": created["recoveryKey"]})
            status, phone_code = request(base_url, "POST", "/v1/auth/phone/request-code", {"phoneNumber": "+85251234567"})
            status, phone_session = request(
                base_url,
                "POST",
                "/v1/auth/phone/verify",
                {"phoneNumber": "+85251234567", "code": phone_code["debugCode"]},
            )
            status, wechat_session = request(base_url, "POST", "/v1/auth/wechat/login", {"code": "debug_wechat_release_flow"})
            status, deleted = request(base_url, "DELETE", "/v1/account", token=token)

            token_rejected_after_delete = False
            try:
                request(base_url, "GET", "/v1/backup", token=token)
            except urllib.error.HTTPError as error:
                token_rejected_after_delete = error.code == 401

            return {
                "startedAt": started_at,
                "completedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "apiBaseUrl": base_url,
                "checks": {
                    "accountCreated": bool(created.get("accountId")) and created.get("recoveryKey", "").startswith("xnp_"),
                    "backupUploaded": backup_upload.get("sizeBytes") == len(backup_bytes),
                    "backupRestored": backup_restore == backup,
                    "photoUploaded": photo_upload.get("photoId") == "photo_release_1",
                    "photoListed": photo_list.get("photos", [{}])[0].get("photoId") == "photo_release_1",
                    "photoDownloaded": photo_download == photo_bytes,
                    "recoveryKeyWorks": recovered.get("accountId") == created.get("accountId"),
                    "phoneLoginWorks": phone_session.get("authProvider") == "phone" and bool(phone_session.get("accountId")),
                    "wechatLoginWorks": wechat_session.get("authProvider") == "wechat" and bool(wechat_session.get("accountId")),
                    "accountDeleteRemovedBackup": deleted.get("backupDeleted") is True,
                    "accountDeleteRemovedPhoto": deleted.get("photoCountDeleted") == 1,
                    "tokenRejectedAfterDelete": token_rejected_after_delete,
                },
                "deletedAt": deleted.get("deletedAt"),
            }
        finally:
            server.shutdown()
            thread.join(timeout=3)
            server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="Backend/proof/release-flow.json")
    args = parser.parse_args()

    result = run_flow()
    failed = [name for name, passed in result["checks"].items() if not passed]
    result["passed"] = not failed
    result["failedChecks"] = failed

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if failed:
        raise SystemExit(f"release flow failed: {', '.join(failed)}")
    print(f"release flow passed: {output_path}")


if __name__ == "__main__":
    main()
