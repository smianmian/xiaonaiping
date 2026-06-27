from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


class ObjectStorageError(RuntimeError):
    pass


class ObjectStorage:
    def put_photo(self, account_id: str, photo_id: str, data: bytes, content_type: str) -> None:
        raise NotImplementedError

    def get_photo(self, account_id: str, photo_id: str) -> bytes | None:
        raise NotImplementedError

    def delete_photo(self, account_id: str, photo_id: str) -> None:
        raise NotImplementedError

    def delete_account(self, account_id: str) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class DiskObjectStorage(ObjectStorage):
    object_root: Path

    def put_photo(self, account_id: str, photo_id: str, data: bytes, content_type: str) -> None:
        destination = self._photo_path(account_id, photo_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)

    def get_photo(self, account_id: str, photo_id: str) -> bytes | None:
        path = self._photo_path(account_id, photo_id)
        if not path.exists():
            return None
        return path.read_bytes()

    def delete_photo(self, account_id: str, photo_id: str) -> None:
        path = self._photo_path(account_id, photo_id)
        if path.exists():
            path.unlink()

    def delete_account(self, account_id: str) -> None:
        account_dir = self.object_root / account_id
        if account_dir.exists():
            shutil.rmtree(account_dir)

    def _photo_path(self, account_id: str, photo_id: str) -> Path:
        return self.object_root / account_id / "photos" / f"{photo_id}.bin"


class HuaweiOBSObjectStorage(ObjectStorage):
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        endpoint: str,
        bucket: str,
        prefix: str = "xiaonaiping",
        security_token: str | None = None,
    ) -> None:
        try:
            from obs import ObsClient
        except ImportError as error:
            raise ObjectStorageError("缺少华为云 OBS Python SDK，请先安装 esdk-obs-python。") from error

        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.client = ObsClient(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            server=endpoint,
            security_token=security_token,
        )

    def put_photo(self, account_id: str, photo_id: str, data: bytes, content_type: str) -> None:
        key = self._photo_key(account_id, photo_id)
        response = self.client.putContent(self.bucket, key, data, headers={"Content-Type": content_type})
        self._ensure_success(response, "putContent")

    def get_photo(self, account_id: str, photo_id: str) -> bytes | None:
        key = self._photo_key(account_id, photo_id)
        response = self.client.getObject(self.bucket, key, loadStreamInMemory=True)
        if getattr(response, "status", 0) == 404:
            return None
        self._ensure_success(response, "getObject")
        body = getattr(response, "body", None)
        response_body = getattr(body, "response", None)
        if isinstance(response_body, bytes):
            return response_body
        if isinstance(response_body, str):
            return response_body.encode("utf-8")
        if hasattr(response_body, "read"):
            return response_body.read()
        buffer = getattr(body, "buffer", None)
        if isinstance(buffer, bytes):
            return buffer
        raise ObjectStorageError("OBS getObject 返回内容无法识别。")

    def delete_photo(self, account_id: str, photo_id: str) -> None:
        response = self.client.deleteObject(self.bucket, self._photo_key(account_id, photo_id))
        if getattr(response, "status", 0) != 404:
            self._ensure_success(response, "deleteObject")

    def delete_account(self, account_id: str) -> None:
        prefix = self._account_prefix(account_id)
        marker = None
        while True:
            response = self.client.listObjects(self.bucket, prefix=prefix, marker=marker)
            self._ensure_success(response, "listObjects")
            body = getattr(response, "body", None)
            contents = getattr(body, "contents", []) or []
            for item in contents:
                key = getattr(item, "key", None)
                if key:
                    delete_response = self.client.deleteObject(self.bucket, key)
                    if getattr(delete_response, "status", 0) != 404:
                        self._ensure_success(delete_response, "deleteObject")

            if not getattr(body, "is_truncated", False):
                break
            marker = getattr(body, "next_marker", None) or (getattr(contents[-1], "key", None) if contents else None)
            if not marker:
                break

    def _account_prefix(self, account_id: str) -> str:
        parts = [part for part in [self.prefix, account_id] if part]
        return "/".join(parts) + "/"

    def _photo_key(self, account_id: str, photo_id: str) -> str:
        return self._account_prefix(account_id) + f"photos/{photo_id}.bin"

    @staticmethod
    def _ensure_success(response, operation: str) -> None:
        status = getattr(response, "status", 0)
        if status < 300:
            return
        code = getattr(response, "errorCode", "unknown")
        message = getattr(response, "errorMessage", "unknown error")
        raise ObjectStorageError(f"OBS {operation} failed: {status} {code} {message}")


def build_object_storage(data_dir: Path) -> ObjectStorage:
    backend = os.environ.get("XNP_STORAGE_BACKEND", "disk").strip().lower()
    if backend == "disk":
        return DiskObjectStorage(data_dir / "objects")
    if backend == "huawei_obs":
        required = {
            "access_key_id": os.environ.get("HUAWEI_OBS_ACCESS_KEY_ID"),
            "secret_access_key": os.environ.get("HUAWEI_OBS_SECRET_ACCESS_KEY"),
            "endpoint": os.environ.get("HUAWEI_OBS_ENDPOINT"),
            "bucket": os.environ.get("HUAWEI_OBS_BUCKET"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ObjectStorageError("缺少华为云 OBS 配置：" + ", ".join(missing))
        return HuaweiOBSObjectStorage(
            access_key_id=required["access_key_id"] or "",
            secret_access_key=required["secret_access_key"] or "",
            endpoint=required["endpoint"] or "",
            bucket=required["bucket"] or "",
            prefix=os.environ.get("HUAWEI_OBS_PREFIX", "xiaonaiping"),
            security_token=os.environ.get("HUAWEI_OBS_SECURITY_TOKEN"),
        )
    raise ObjectStorageError(f"不支持的对象存储后端：{backend}")
