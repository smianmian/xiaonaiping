#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.storage import ObjectStorageError, build_object_storage


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_flow(data_dir: Path, account_id: str) -> dict:
    storage = build_object_storage(data_dir)
    first_photo_id = "storage_probe_one"
    second_photo_id = "storage_probe_two"
    payload = b"xiaonaiping-storage-verification"

    checks = {
        "photoUploaded": False,
        "photoDownloaded": False,
        "photoDeleted": False,
        "accountDeleteRemovedPhotos": False,
    }

    storage.put_photo(account_id, first_photo_id, payload, "image/jpeg")
    checks["photoUploaded"] = True
    checks["photoDownloaded"] = storage.get_photo(account_id, first_photo_id) == payload
    storage.delete_photo(account_id, first_photo_id)
    checks["photoDeleted"] = storage.get_photo(account_id, first_photo_id) is None

    storage.put_photo(account_id, first_photo_id, payload, "image/jpeg")
    storage.put_photo(account_id, second_photo_id, payload, "image/jpeg")
    storage.delete_account(account_id)
    checks["accountDeleteRemovedPhotos"] = (
        storage.get_photo(account_id, first_photo_id) is None
        and storage.get_photo(account_id, second_photo_id) is None
    )

    failed = [name for name, passed in checks.items() if not passed]
    return {
        "startedAt": utc_now(),
        "completedAt": utc_now(),
        "containsSecrets": False,
        "storageBackend": os.environ.get("XNP_STORAGE_BACKEND", "disk"),
        "dataDir": str(data_dir),
        "accountId": account_id,
        "checks": checks,
        "passed": not failed,
        "failedChecks": failed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=os.environ.get("XNP_DATA_DIR", ".xnp-data"))
    parser.add_argument("--account-id", default="")
    parser.add_argument("--output", default="Backend/proof/storage-backend.json")
    args = parser.parse_args()

    account_id = args.account_id or "storage_probe_" + uuid.uuid4().hex
    try:
        result = run_flow(Path(args.data_dir).resolve(), account_id)
    except ObjectStorageError as error:
        result = {
            "startedAt": utc_now(),
            "completedAt": utc_now(),
            "containsSecrets": False,
            "storageBackend": os.environ.get("XNP_STORAGE_BACKEND", "disk"),
            "dataDir": str(Path(args.data_dir).resolve()),
            "accountId": account_id,
            "checks": {},
            "passed": False,
            "failedChecks": ["storageBackend"],
            "error": str(error),
        }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not result["passed"]:
        raise SystemExit("storage backend verification failed: " + ", ".join(result["failedChecks"]))
    print(f"storage backend verification passed: {output_path}")


if __name__ == "__main__":
    main()
