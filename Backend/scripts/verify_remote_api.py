#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

    request_obj = urllib.request.Request(base_url.rstrip("/") + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request_obj, timeout=15) as response:
        response_body = response.read()
        response_type = response.headers.get("Content-Type", "")
        if response_type.startswith("application/json"):
            return response.status, json.loads(response_body.decode("utf-8"))
        return response.status, response_body


def run_remote_flow(base_url: str, phone_number: str) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status, health = request(base_url, "GET", "/healthz")
    status, privacy = request(base_url, "GET", "/privacy")
    status, terms = request(base_url, "GET", "/terms")
    status, support = request(base_url, "GET", "/support")

    status, code_request = request(
        base_url,
        "POST",
        "/v1/auth/phone/request-code",
        {"phoneNumber": phone_number},
    )
    phone_code = getpass.getpass("输入刚收到的短信验证码：")
    status, phone_session = request(
        base_url,
        "POST",
        "/v1/auth/phone/verify",
        {"phoneNumber": phone_number, "code": phone_code},
    )
    token = phone_session["sessionToken"]

    sync = {
        "schemaVersion": 1,
        "baby": {"name": "RemoteVerificationBaby", "birthDate": "2026-06-01"},
        "feedingRecords": [{"id": "remote-feeding-1", "amountML": 90}],
        "photoIds": ["remote_photo_1"],
    }
    sync_bytes = json.dumps(sync, ensure_ascii=False).encode("utf-8")
    status, sync_upload = request(base_url, "PUT", "/v1/sync", sync, token=token)
    status, sync_restore = request(base_url, "GET", "/v1/sync", token=token)

    photo_bytes = b"remote-verification-photo-bytes"
    status, photo_upload = request(
        base_url,
        "PUT",
        "/v1/photos/remote_photo_1",
        photo_bytes,
        token=token,
        content_type="image/jpeg",
    )
    status, photo_list = request(base_url, "GET", "/v1/photos", token=token)
    status, photo_download = request(base_url, "GET", "/v1/photos/remote_photo_1", token=token)
    status, analytics_event = request(
        base_url,
        "POST",
        "/v1/analytics/events",
        {
            "events": [
                {
                    "eventId": "remote_" + uuid.uuid4().hex,
                    "name": "cloud_sync_completed",
                    "occurredAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "properties": {"source": "sync", "result": "success", "platform": "ios"},
                }
            ]
        },
        token=token,
    )
    status, deleted = request(base_url, "DELETE", "/v1/account", token=token)

    token_rejected_after_delete = False
    try:
        request(base_url, "GET", "/v1/sync", token=token)
    except urllib.error.HTTPError as error:
        token_rejected_after_delete = error.code == 401

    return {
        "startedAt": started_at,
        "completedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "apiBaseUrl": base_url,
        "checks": {
            "healthz": health.get("status") == "ok",
            "privacyPage": "小奶瓶隐私政策".encode("utf-8") in privacy,
            "termsPage": "小奶瓶用户协议".encode("utf-8") in terms,
            "supportPage": "小奶瓶支持".encode("utf-8") in support,
            "phoneCodeRequested": code_request.get("sent") is True,
            "phoneAccountAuthenticated": phone_session.get("authProvider") == "phone" and bool(phone_session.get("accountId")),
            "syncUploaded": sync_upload.get("sizeBytes") == len(sync_bytes),
            "syncRestored": sync_restore == sync,
            "photoUploaded": photo_upload.get("photoId") == "remote_photo_1",
            "photoListed": photo_list.get("photos", [{}])[0].get("photoId") == "remote_photo_1",
            "photoDownloaded": photo_download == photo_bytes,
            "analyticsEventAccepted": analytics_event.get("accepted") == 1 and analytics_event.get("dropped") == 0,
            "accountDeleteRemovedSync": deleted.get("syncDeleted") is True,
            "accountDeleteRemovedPhoto": deleted.get("photoCountDeleted") == 1,
            "accountDeleteRemovedAnalytics": deleted.get("analyticsEventsDeleted") == 1,
            "tokenRejectedAfterDelete": token_rejected_after_delete,
        },
        "deletedAt": deleted.get("deletedAt"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("XNP_API_BASE_URL"))
    parser.add_argument("--phone", default=os.environ.get("XNP_REMOTE_TEST_PHONE"))
    parser.add_argument("--output", default="Backend/proof/remote-api.json")
    args = parser.parse_args()

    if not args.base_url:
        raise SystemExit("missing --base-url or XNP_API_BASE_URL")
    if not args.base_url.startswith("https://"):
        raise SystemExit("production verification requires an https:// base URL")
    if not args.phone:
        raise SystemExit("missing --phone or XNP_REMOTE_TEST_PHONE")

    result = run_remote_flow(args.base_url, args.phone)
    failed = [name for name, passed in result["checks"].items() if not passed]
    result["passed"] = not failed
    result["failedChecks"] = failed

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if failed:
        raise SystemExit(f"remote API verification failed: {', '.join(failed)}")
    print(f"remote API verification passed: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as error:
        print(f"HTTP error: {error.code} {error.reason}", file=sys.stderr)
        raise
