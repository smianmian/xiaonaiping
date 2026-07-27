from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.server import ServerConfig, XiaoNaiPingHandler, create_http_server
from api.storage import DiskObjectStorage


class APITestCase(unittest.TestCase):
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

    def request(
        self,
        method: str,
        path: str,
        body=None,
        token: str | None = None,
        content_type: str = "application/json",
        extra_headers: dict[str, str] | None = None,
    ):
        data = None
        headers = {}
        if body is not None:
            if isinstance(body, bytes):
                data = body
            else:
                data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = content_type
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update(extra_headers)

        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = response.read()
            response_type = response.headers.get("Content-Type", "")
            if response_type.startswith("application/json"):
                return response.status, json.loads(payload.decode("utf-8"))
            return response.status, payload

    def test_account_sync_photo_restore_and_delete(self) -> None:
        status, created = self.request("POST", "/v1/accounts")
        self.assertEqual(status, 201)
        token = created["sessionToken"]

        sync = {"baby": {"name": "宝宝"}, "records": [{"id": "feed-1"}]}
        status, uploaded = self.request("PUT", "/v1/sync", sync, token=token)
        self.assertEqual(status, 200)
        self.assertEqual(uploaded["sizeBytes"], len(json.dumps(sync).encode("utf-8")))

        status, restored = self.request("GET", "/v1/sync", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(restored, sync)

        photo_body = b"not-a-real-jpeg-but-test-bytes"
        status, photo = self.request(
            "PUT",
            "/v1/photos/photo_1",
            photo_body,
            token=token,
            content_type="image/jpeg",
        )
        self.assertEqual(status, 200)
        self.assertEqual(photo["photoId"], "photo_1")

        status, listed = self.request("GET", "/v1/photos", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(listed["photos"][0]["photoId"], "photo_1")

        status, downloaded = self.request("GET", "/v1/photos/photo_1", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(downloaded, photo_body)

        status, recovered = self.request("POST", "/v1/sessions/recover", {"recoveryKey": created["recoveryKey"]})
        self.assertEqual(status, 200)
        self.assertEqual(recovered["accountId"], created["accountId"])

        status, deleted = self.request("DELETE", "/v1/account", token=token)
        self.assertEqual(status, 200)
        self.assertTrue(deleted["syncDeleted"])
        self.assertEqual(deleted["photoCountDeleted"], 1)

        with self.assertRaises(urllib.error.HTTPError) as context:
            self.request("GET", "/v1/sync", token=token)
        self.assertEqual(context.exception.code, 401)

    def test_sync_requires_json(self) -> None:
        _, created = self.request("POST", "/v1/accounts")
        with self.assertRaises(urllib.error.HTTPError) as context:
            self.request("PUT", "/v1/sync", b"not-json", token=created["sessionToken"])
        self.assertEqual(context.exception.code, 400)

    def test_public_policy_terms_and_support_pages(self) -> None:
        for path, keyword in [
            ("/privacy", "小奶瓶隐私政策"),
            ("/terms", "小奶瓶用户协议"),
            ("/support", "小奶瓶支持"),
        ]:
            status, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertIn(keyword.encode("utf-8"), body)

        status, dashboard = self.request("GET", "/internal/dashboard")
        self.assertEqual(status, 200)
        self.assertIn("小奶瓶数据后台".encode("utf-8"), dashboard)

    def test_support_page_assets_are_public(self) -> None:
        for path in [
            "/support-assets/app-icon-108.png",
            "/support-assets/operation-flow.jpg",
            "/support-assets/screenshot-home.jpg",
        ]:
            status, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertGreater(len(body), 1000)

    def test_internal_dashboard_blocks_public_forwarded_clients(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as context:
            self.request("GET", "/internal/dashboard", extra_headers={"X-Forwarded-For": "8.8.8.8"})
        self.assertEqual(context.exception.code, 404)

    def test_apple_app_site_association_routes(self) -> None:
        for path in ["/apple-app-site-association", "/.well-known/apple-app-site-association"]:
            status, payload = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertIn("applinks", payload)
            details = payload["applinks"]["details"]
            xnp_detail = next(
                detail for detail in details if detail["appID"] == "L2TYJNDTJK.com.mewpow.xiaonaiping"
            )
            self.assertIn("/xiaonaiping/wechat/*", xnp_detail["paths"])

    def test_internal_metrics_are_aggregated_and_admin_only(self) -> None:
        _, created = self.request("POST", "/v1/accounts")
        token = created["sessionToken"]
        self.request("PUT", "/v1/sync", {"baby": {"name": "不应出现在指标里"}}, token=token)
        self.request(
            "PUT",
            "/v1/photos/photo_metrics",
            b"photo-bytes",
            token=token,
            content_type="image/jpeg",
        )
        self.request("PUT", "/v1/sync", {"baby": {"name": "不应出现在指标里", "revision": 2}}, token=token)
        self.request("POST", "/v1/family", {}, token=token)

        with self.assertRaises(urllib.error.HTTPError) as context:
            self.request("GET", "/internal/metrics")
        self.assertEqual(context.exception.code, 401)

        status, metrics = self.request("GET", "/internal/metrics", token="admin-test-token")
        self.assertEqual(status, 200)
        self.assertEqual(metrics["databaseBackend"], "sqlite")
        self.assertEqual(metrics["storageBackend"], "disk")
        self.assertEqual(metrics["totalAccounts"], 1)
        self.assertEqual(metrics["activeAccounts"], 1)
        self.assertEqual(metrics["accountsWithSync"], 1)
        self.assertGreater(metrics["syncBytes"], 0)
        self.assertEqual(metrics["photoObjects"], 1)
        self.assertEqual(metrics["deletionAudit"]["deletedAccounts"], 0)
        self.assertEqual(metrics["family"], {"families": 1, "members": 1, "familiesWithPartner": 0})
        self.assertEqual(metrics["series"]["windowDays"], 30)
        self.assertEqual(metrics["series"]["newAccountsDaily"][0]["count"], 1)
        self.assertEqual(metrics["series"]["syncActivityDaily"][0]["count"], 1)
        self.assertEqual(metrics["series"]["photoUploadsDaily"][0]["count"], 1)
        self.assertNotIn("不应出现在指标里", json.dumps(metrics, ensure_ascii=False))

    def test_analytics_events_are_whitelisted_aggregated_and_deleted(self) -> None:
        _, created = self.request("POST", "/v1/accounts")
        token = created["sessionToken"]

        with self.assertRaises(urllib.error.HTTPError) as context:
            self.request("POST", "/v1/analytics/events", {"events": []})
        self.assertEqual(context.exception.code, 401)

        status, response = self.request(
            "POST",
            "/v1/analytics/events",
            {
                "events": [
                    {
                        "eventId": "event_valid_123",
                        "name": "record_created",
                        "occurredAt": "2026-06-24T00:00:00+00:00",
                        "properties": {
                            "recordType": "feeding",
                            "source": "record",
                            "result": "success",
                            "platform": "ios",
                        },
                    },
                    {
                        "eventId": "event_bad_123",
                        "name": "record_created",
                        "occurredAt": "2026-06-24T00:00:00+00:00",
                        "properties": {"babyName": "不应落库"},
                    },
                ]
            },
            token=token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["accepted"], 1)
        self.assertEqual(response["dropped"], 1)

        status, metrics = self.request("GET", "/internal/metrics", token="admin-test-token")
        self.assertEqual(status, 200)
        self.assertEqual(metrics["analytics"]["eventsLast7d"], 1)
        self.assertEqual(metrics["analytics"]["actorsLast7d"], 1)
        self.assertEqual(metrics["analytics"]["topEventsLast7d"][0], {"eventName": "record_created", "count": 1})
        self.assertNotIn("不应落库", json.dumps(metrics, ensure_ascii=False))

        status, deleted = self.request("DELETE", "/v1/account", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(deleted["analyticsEventsDeleted"], 1)

    def test_phone_login_creates_and_reuses_account(self) -> None:
        status, sent = self.request("POST", "/v1/auth/phone/request-code", {"phoneNumber": "+85251234567"})
        self.assertEqual(status, 200)
        self.assertEqual(len(sent["debugCode"]), 6)

        status, session = self.request(
            "POST",
            "/v1/auth/phone/verify",
            {"phoneNumber": "+85251234567", "code": sent["debugCode"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(session["authProvider"], "phone")
        self.assertNotIn("recoveryKey", session)

        status, sent_again = self.request("POST", "/v1/auth/phone/request-code", {"phoneNumber": "+85251234567"})
        self.assertEqual(status, 200)
        status, session_again = self.request(
            "POST",
            "/v1/auth/phone/verify",
            {"phoneNumber": "+85251234567", "code": sent_again["debugCode"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(session_again["accountId"], session["accountId"])
        self.assertNotIn("recoveryKey", session_again)

    def test_phone_login_rejects_wrong_code(self) -> None:
        status, sent = self.request("POST", "/v1/auth/phone/request-code", {"phoneNumber": "+85251234567"})
        self.assertEqual(status, 200)
        self.assertNotEqual(sent["debugCode"], "000000")
        with self.assertRaises(urllib.error.HTTPError) as context:
            self.request(
                "POST",
                "/v1/auth/phone/verify",
                {"phoneNumber": "+85251234567", "code": "000000"},
            )
        self.assertEqual(context.exception.code, 401)

    def test_wechat_login_creates_and_reuses_account(self) -> None:
        status, session = self.request("POST", "/v1/auth/wechat/login", {"code": "debug_wechat_openid_1"})
        self.assertEqual(status, 200)
        self.assertEqual(session["authProvider"], "wechat")
        self.assertNotIn("recoveryKey", session)

        status, session_again = self.request("POST", "/v1/auth/wechat/login", {"code": "debug_wechat_openid_1"})
        self.assertEqual(status, 200)
        self.assertEqual(session_again["accountId"], session["accountId"])
        self.assertNotIn("recoveryKey", session_again)

    def test_deleted_identity_cannot_reuse_deleted_account(self) -> None:
        _, session = self.request("POST", "/v1/auth/wechat/login", {"code": "debug_wechat_openid_2"})
        token = session["sessionToken"]
        _, deleted = self.request("DELETE", "/v1/account", token=token)
        self.assertEqual(deleted["accountId"], session["accountId"])

        _, new_session = self.request("POST", "/v1/auth/wechat/login", {"code": "debug_wechat_openid_2"})
        self.assertNotEqual(new_session["accountId"], session["accountId"])

    def test_request_log_path_redacts_photo_object_keys(self) -> None:
        self.assertEqual(
            XiaoNaiPingHandler.redacted_log_path("/v1/photos/private_photo_key_123?token=secret"),
            "/v1/photos/<redacted>",
        )
        self.assertEqual(XiaoNaiPingHandler.redacted_log_path("/v1/sync?token=secret"), "/v1/sync")


class ProductionAuthProviderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.servers: list[ThreadingHTTPServer] = []
        self.threads: list[threading.Thread] = []

    def tearDown(self) -> None:
        for server in self.servers:
            server.shutdown()
        for thread in self.threads:
            thread.join(timeout=3)
        for server in self.servers:
            server.server_close()
        self.tempdir.cleanup()

    def start_server(self, handler: type[BaseHTTPRequestHandler]) -> str:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.servers.append(server)
        self.threads.append(thread)
        host, port = server.server_address
        return f"http://{host}:{port}"

    def start_api(self, config: ServerConfig) -> str:
        server = create_http_server("127.0.0.1", 0, config)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.servers.append(server)
        self.threads.append(thread)
        host, port = server.server_address
        return f"http://{host}:{port}"

    def request(self, base_url: str, method: str, path: str, body=None):
        data = None
        headers = {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(base_url + path, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = response.read()
            return response.status, json.loads(payload.decode("utf-8"))

    def test_phone_login_uses_production_sms_webhook(self) -> None:
        calls: list[dict[str, object]] = []

        class SMSWebhookHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args) -> None:
                pass

            def do_POST(self) -> None:
                payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                calls.append(
                    {
                        "signature": self.headers.get("X-XNP-Signature"),
                        "body": json.loads(payload.decode("utf-8")),
                    }
                )
                self.send_response(200)
                self.end_headers()

        sms_url = self.start_server(SMSWebhookHandler)
        data_dir = Path(self.tempdir.name) / "phone"
        api_url = self.start_api(
            ServerConfig(
                data_dir=data_dir,
                secret_key="test-secret",
                object_storage=DiskObjectStorage(data_dir / "objects"),
                sms_provider="webhook",
                sms_secret="sms-secret",
                sms_webhook_url=sms_url,
            )
        )

        status, sent = self.request(api_url, "POST", "/v1/auth/phone/request-code", {"phoneNumber": "+85251234567"})
        self.assertEqual(status, 200)
        self.assertEqual(sent, {"sent": True, "expiresInSeconds": 600})
        self.assertEqual(len(calls), 1)
        sent_code = calls[0]["body"]["code"]

        status, session = self.request(
            api_url,
            "POST",
            "/v1/auth/phone/verify",
            {"phoneNumber": "+85251234567", "code": sent_code},
        )
        self.assertEqual(status, 200)
        self.assertEqual(session["authProvider"], "phone")
        self.assertTrue(session["accountId"])
        self.assertNotIn("recoveryKey", session)

    def test_app_review_phone_login_does_not_send_sms(self) -> None:
        calls: list[dict[str, object]] = []

        class SMSWebhookHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args) -> None:
                pass

            def do_POST(self) -> None:
                calls.append({})
                self.send_response(200)
                self.end_headers()

        sms_url = self.start_server(SMSWebhookHandler)
        data_dir = Path(self.tempdir.name) / "app-review-phone"
        api_url = self.start_api(
            ServerConfig(
                data_dir=data_dir,
                secret_key="test-secret",
                object_storage=DiskObjectStorage(data_dir / "objects"),
                sms_provider="webhook",
                sms_secret="sms-secret",
                sms_webhook_url=sms_url,
                app_review_phone_number="+15555550100",
                app_review_phone_code="123456",
            )
        )

        status, sent = self.request(
            api_url,
            "POST",
            "/v1/auth/phone/request-code",
            {"phoneNumber": "+15555550100"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(sent, {"sent": True, "expiresInSeconds": 600})
        self.assertEqual(calls, [])

        status, session = self.request(
            api_url,
            "POST",
            "/v1/auth/phone/verify",
            {"phoneNumber": "+15555550100", "code": "123456"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(session["authProvider"], "phone")
        self.assertNotIn("recoveryKey", session)

    def test_wechat_login_exchanges_code_in_production_mode(self) -> None:
        calls: list[dict[str, list[str]]] = []

        class WeChatTokenHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args) -> None:
                pass

            def do_GET(self) -> None:
                calls.append(parse_qs(urlparse(self.path).query))
                payload = json.dumps({"openid": "openid_prod_1", "unionid": "union_prod_1"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        wechat_url = self.start_server(WeChatTokenHandler)
        data_dir = Path(self.tempdir.name) / "wechat"
        api_url = self.start_api(
            ServerConfig(
                data_dir=data_dir,
                secret_key="test-secret",
                object_storage=DiskObjectStorage(data_dir / "objects"),
                wechat_app_id="wx_test",
                wechat_app_secret="wechat-secret",
                wechat_access_token_url=wechat_url,
            )
        )

        status, session = self.request(api_url, "POST", "/v1/auth/wechat/login", {"code": "real_code"})
        self.assertEqual(status, 200)
        self.assertEqual(session["authProvider"], "wechat")
        self.assertTrue(session["accountId"])
        self.assertNotIn("recoveryKey", session)
        self.assertEqual(calls[0]["appid"], ["wx_test"])
        self.assertEqual(calls[0]["code"], ["real_code"])


if __name__ == "__main__":
    unittest.main()
