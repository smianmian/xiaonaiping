from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import subprocess
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SCRIPT = BACKEND_ROOT / "sms" / "aliyun-webhook-adapter" / "server.js"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def signed_request(base_url: str, path: str, body: dict, secret: str, signature: str | None = None):
    payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
    supplied_signature = signature or hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    request = urllib.request.Request(
        base_url + path,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-XNP-Signature": supplied_signature,
        },
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


class AliyunSMSAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = "adapter-test-secret"
        self.port = free_port()
        env = os.environ.copy()
        env.update(
            {
                "XNP_SMS_ADAPTER_HOST": "127.0.0.1",
                "XNP_SMS_ADAPTER_PORT": str(self.port),
                "XNP_SMS_SECRET": self.secret,
                "XNP_SMS_ADAPTER_MOCK": "1",
                "ALIYUN_TEMPLATE_CODE": "SMS_TEST",
            }
        )
        self.process = subprocess.Popen(
            ["node", str(ADAPTER_SCRIPT)],
            cwd=str(ADAPTER_SCRIPT.parent),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.wait_for_health()

    def tearDown(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)
        if self.process.stdout is not None:
            self.process.stdout.close()
        if self.process.stderr is not None:
            self.process.stderr.close()

    def wait_for_health(self) -> None:
        deadline = time.time() + 5
        while time.time() < deadline:
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate(timeout=1)
                raise AssertionError(f"adapter exited early\nstdout={stdout}\nstderr={stderr}")
            try:
                with urllib.request.urlopen(self.base_url + "/healthz", timeout=1) as response:
                    if response.status == 200:
                        return
            except OSError:
                time.sleep(0.05)
        raise AssertionError("adapter did not start")

    def test_signed_webhook_sends_in_mock_mode(self) -> None:
        status, response = signed_request(
            self.base_url,
            "/send",
            {
                "phoneNumber": "+8613800138000",
                "code": "123456",
                "ttlSeconds": 600,
                "purpose": "login",
                "templateId": "SMS_TEST",
            },
            self.secret,
        )

        self.assertEqual(status, 200)
        self.assertEqual(response["sent"], True)
        self.assertEqual(response["provider"], "aliyun_mock")
        self.assertNotIn("123456", json.dumps(response))

    def test_invalid_signature_is_rejected(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as context:
            signed_request(
                self.base_url,
                "/send",
                {"phoneNumber": "+8613800138000", "code": "123456", "templateId": "SMS_TEST"},
                self.secret,
                signature="0" * 64,
            )

        self.assertEqual(context.exception.code, 401)

    def test_invalid_payload_is_rejected_after_signature(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as context:
            signed_request(
                self.base_url,
                "/send",
                {"phoneNumber": "bad-phone", "code": "123456", "templateId": "SMS_TEST"},
                self.secret,
            )

        self.assertEqual(context.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
