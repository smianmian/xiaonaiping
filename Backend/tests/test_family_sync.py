from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.server import ServerConfig, create_http_server
from api.storage import DiskObjectStorage


class FamilySyncTestCase(unittest.TestCase):
    """家人共享（多看护人逐条增量同步）的行为契约。

    覆盖：建家庭幂等、邀请码加入、成员上限、非成员拒绝、
    逐条 LWW（新者胜/旧者弃）、seq 游标增量拉取、墓碑传播。
    """

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        data_dir = Path(self.tempdir.name)
        config = ServerConfig(
            data_dir=data_dir,
            secret_key="test-secret",
            object_storage=DiskObjectStorage(data_dir / "objects"),
            auth_debug_mode=True,
            admin_token="admin-test-token",
        )
        self.server = create_http_server("127.0.0.1", 0, config)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=3)
        self.server.server_close()
        self.tempdir.cleanup()

    def request(self, method: str, path: str, body=None, token: str | None = None):
        data = None
        headers = {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def make_account(self) -> str:
        status, created = self.request("POST", "/v1/accounts")
        self.assertEqual(status, 201)
        return created["sessionToken"]

    def envelope(self, record_type: str, record_id: str, payload: dict, updated_at_ms: int, deleted_at_ms=None):
        item = {
            "recordType": record_type,
            "recordId": record_id,
            "payload": json.dumps(payload),
            "updatedAtMs": updated_at_ms,
        }
        if deleted_at_ms is not None:
            item["deletedAtMs"] = deleted_at_ms
        return item

    # ---- 家庭生命周期 ----

    def test_create_family_is_idempotent(self) -> None:
        token = self.make_account()
        status, first = self.request("POST", "/v1/family", body={}, token=token)
        self.assertEqual(status, 201)
        self.assertEqual(first["family"]["role"], "owner")
        self.assertEqual(first["family"]["memberCount"], 1)
        invite = first["family"]["inviteCode"]
        self.assertRegex(invite, r"^[A-Z0-9]{6}$")

        status, second = self.request("POST", "/v1/family", body={}, token=token)
        self.assertEqual(status, 200)
        self.assertEqual(second["family"]["inviteCode"], invite)

    def test_join_by_invite_code_and_membership_info(self) -> None:
        owner = self.make_account()
        member = self.make_account()
        _, created = self.request("POST", "/v1/family", body={}, token=owner)
        invite = created["family"]["inviteCode"]

        status, joined = self.request("POST", "/v1/family/join", body={"inviteCode": invite.lower()}, token=member)
        self.assertEqual(status, 201)
        self.assertEqual(joined["family"]["role"], "member")
        self.assertEqual(joined["family"]["memberCount"], 2)

        status, info = self.request("GET", "/v1/family", token=owner)
        self.assertEqual(status, 200)
        self.assertEqual(info["family"]["memberCount"], 2)

    def test_join_with_bad_code_fails(self) -> None:
        member = self.make_account()
        status, body = self.request("POST", "/v1/family/join", body={"inviteCode": "NOPE99"}, token=member)
        self.assertEqual(status, 404)
        self.assertEqual(body["error"]["code"], "invite_code_not_found")

    def test_non_member_cannot_touch_records(self) -> None:
        outsider = self.make_account()
        status, body = self.request(
            "PUT",
            "/v1/family/records",
            body={"records": [self.envelope("feeding", "r1", {"amountML": 100}, 1000)]},
            token=outsider,
        )
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "not_in_family")

        status, body = self.request("GET", "/v1/family/records?since=0", token=outsider)
        self.assertEqual(status, 403)

    # ---- 逐条 LWW 与增量拉取 ----

    def test_push_pull_roundtrip_between_members(self) -> None:
        owner = self.make_account()
        member = self.make_account()
        _, created = self.request("POST", "/v1/family", body={}, token=owner)
        self.request("POST", "/v1/family/join", body={"inviteCode": created["family"]["inviteCode"]}, token=member)

        status, pushed = self.request(
            "PUT",
            "/v1/family/records",
            body={
                "records": [
                    self.envelope("feeding", "feed-1", {"amountML": 120}, 1000),
                    self.envelope("sleep", "sleep-1", {"minutes": 45}, 1001),
                ]
            },
            token=owner,
        )
        self.assertEqual(status, 200)
        self.assertEqual(pushed["accepted"], 2)

        status, pulled = self.request("GET", "/v1/family/records?since=0", token=member)
        self.assertEqual(status, 200)
        self.assertEqual(len(pulled["records"]), 2)
        self.assertFalse(pulled["hasMore"])
        self.assertFalse(pulled["records"][0]["mine"])
        types = {item["recordType"] for item in pulled["records"]}
        self.assertEqual(types, {"feeding", "sleep"})

        # 游标之后再拉，应该为空。
        cursor = pulled["cursor"]
        status, empty = self.request("GET", f"/v1/family/records?since={cursor}", token=member)
        self.assertEqual(status, 200)
        self.assertEqual(empty["records"], [])
        self.assertEqual(empty["cursor"], cursor)

    def test_lww_newer_wins_and_stale_is_skipped(self) -> None:
        owner = self.make_account()
        member = self.make_account()
        _, created = self.request("POST", "/v1/family", body={}, token=owner)
        self.request("POST", "/v1/family/join", body={"inviteCode": created["family"]["inviteCode"]}, token=member)

        self.request(
            "PUT",
            "/v1/family/records",
            body={"records": [self.envelope("feeding", "feed-1", {"amountML": 120}, 2000)]},
            token=owner,
        )
        # 成员用更旧的 updatedAtMs 覆盖：必须被拒。
        status, stale = self.request(
            "PUT",
            "/v1/family/records",
            body={"records": [self.envelope("feeding", "feed-1", {"amountML": 60}, 1500)]},
            token=member,
        )
        self.assertEqual(status, 200)
        self.assertEqual(stale["accepted"], 0)
        self.assertEqual(stale["staleSkipped"], 1)

        # 更新的版本覆盖成功，且拉取端拿到的是新 payload。
        status, fresh = self.request(
            "PUT",
            "/v1/family/records",
            body={"records": [self.envelope("feeding", "feed-1", {"amountML": 150}, 2500)]},
            token=member,
        )
        self.assertEqual(fresh["accepted"], 1)

        status, pulled = self.request("GET", "/v1/family/records?since=0", token=owner)
        payloads = [json.loads(item["payload"]) for item in pulled["records"] if item["recordType"] == "feeding"]
        self.assertEqual(payloads, [{"amountML": 150}])

    def test_tombstone_propagates(self) -> None:
        owner = self.make_account()
        member = self.make_account()
        _, created = self.request("POST", "/v1/family", body={}, token=owner)
        self.request("POST", "/v1/family/join", body={"inviteCode": created["family"]["inviteCode"]}, token=member)

        self.request(
            "PUT",
            "/v1/family/records",
            body={"records": [self.envelope("diaper", "d-1", {"kind": "大便"}, 1000)]},
            token=owner,
        )
        self.request(
            "PUT",
            "/v1/family/records",
            body={"records": [self.envelope("diaper", "d-1", {}, 2000, deleted_at_ms=2000)]},
            token=member,
        )

        status, pulled = self.request("GET", "/v1/family/records?since=0", token=owner)
        diaper = [item for item in pulled["records"] if item["recordType"] == "diaper"]
        self.assertEqual(len(diaper), 1)
        self.assertEqual(diaper[0]["deletedAtMs"], 2000)

    def test_family_member_limit(self) -> None:
        owner = self.make_account()
        _, created = self.request("POST", "/v1/family", body={}, token=owner)
        invite = created["family"]["inviteCode"]
        for _ in range(5):
            token = self.make_account()
            status, _ = self.request("POST", "/v1/family/join", body={"inviteCode": invite}, token=token)
            self.assertEqual(status, 201)

        extra = self.make_account()
        status, body = self.request("POST", "/v1/family/join", body={"inviteCode": invite}, token=extra)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"]["code"], "family_full")

    def test_invalid_record_type_rejected(self) -> None:
        owner = self.make_account()
        self.request("POST", "/v1/family", body={}, token=owner)
        status, body = self.request(
            "PUT",
            "/v1/family/records",
            body={"records": [self.envelope("photo", "p1", {}, 1000)]},
            token=owner,
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "invalid_record_type")


if __name__ == "__main__":
    unittest.main()
