from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.server import ServerConfig, create_http_server
from api.storage import DiskObjectStorage


SCRIPT = BACKEND_ROOT / "scripts" / "verify_auth_providers.py"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def deployment_proof(configured: bool) -> dict:
    set_names = [
        "XNP_SECRET_KEY",
        "XNP_ADMIN_TOKEN",
    ]
    provider_checks = {
        "authDebugModeDisabled": True,
        "smsProviderIsWebhook": configured,
        "smsWebhookURLConfigured": configured,
        "wechatAppIDConfigured": configured,
        "wechatAppSecretConfigured": configured,
    }
    public_env = {"XNP_AUTH_DEBUG_MODE": "0"}
    if configured:
        set_names.extend(
            [
                "XNP_SMS_SECRET",
                "XNP_SMS_WEBHOOK_URL",
                "XNP_WECHAT_APP_ID",
                "XNP_WECHAT_APP_SECRET",
            ]
        )
        public_env["XNP_SMS_PROVIDER"] = "webhook"
    return {
        "privateEnvStatus": {
            "set": set_names,
            "empty": [] if configured else ["XNP_SMS_SECRET", "XNP_SMS_WEBHOOK_URL", "XNP_WECHAT_APP_ID", "XNP_WECHAT_APP_SECRET"],
        },
        "publicEnvValues": public_env,
        "providerChecks": provider_checks,
        "publicRoute": {"baseUrl": "https://api.xiaonaiping.test"},
    }


class AuthProviderVerificationTest(unittest.TestCase):
    def run_checker(self, root: Path, proof: dict, *extra_args: str) -> dict:
        proof_path = root / "deploy-proof.json"
        output = root / "auth-providers.json"
        write_json(proof_path, proof)
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("XNP_") and not key.startswith("HUAWEI_OBS_")
        }
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--deployment-proof",
                str(proof_path),
                "--output",
                str(output),
                "--allow-incomplete",
                *extra_args,
            ],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(output.read_text(encoding="utf-8"))

    def start_api(self, root: Path, auth_debug_mode: bool) -> tuple[str, object, threading.Thread]:
        config = ServerConfig(
            data_dir=root / "data",
            secret_key="test-secret",
            object_storage=DiskObjectStorage(root / "objects"),
            auth_debug_mode=auth_debug_mode,
        )
        server = create_http_server("127.0.0.1", 0, config)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        return f"http://{host}:{port}", server, thread

    def test_missing_provider_config_fails_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            report = self.run_checker(root, deployment_proof(configured=False))

            self.assertFalse(report["passed"])
            self.assertFalse(report["containsSecrets"])
            self.assertIn("smsProviderConfigured", report["failedRequiredChecks"])
            self.assertIn("wechatProviderConfigured", report["failedRequiredChecks"])
            self.assertNotIn("test-secret", json.dumps(report))

    def test_deployment_proof_can_pass_offline_provider_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            report = self.run_checker(root, deployment_proof(configured=True))

            self.assertTrue(report["passed"])
            self.assertTrue(report["checks"]["smsProviderConfigured"]["passed"])
            self.assertTrue(report["checks"]["wechatProviderConfigured"]["passed"])
            self.assertFalse(report["checks"]["smsLiveSendVerified"]["required"])

    def test_sample_wechat_app_id_fails_provider_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            proof = deployment_proof(configured=True)
            proof["publicEnvValues"]["XNP_WECHAT_APP_ID"] = "wx1234567890abcdef"

            report = self.run_checker(root, proof)

            self.assertFalse(report["passed"])
            self.assertFalse(report["checks"]["wechatProviderConfigured"]["passed"])
            self.assertIn("wechatProviderConfigured", report["failedRequiredChecks"])

    def test_live_check_accepts_production_rejection_of_debug_wechat_code(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            base_url, server, thread = self.start_api(root, auth_debug_mode=False)
            try:
                report = self.run_checker(
                    root,
                    deployment_proof(configured=True),
                    "--live-check",
                    "--allow-insecure-http",
                    "--base-url",
                    base_url,
                )
            finally:
                server.shutdown()
                thread.join(timeout=3)
                server.server_close()

            self.assertTrue(report["passed"])
            self.assertTrue(report["checks"]["wechatDebugLoginRejected"]["passed"])

    def test_live_check_rejects_debug_wechat_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            base_url, server, thread = self.start_api(root, auth_debug_mode=True)
            try:
                report = self.run_checker(
                    root,
                    deployment_proof(configured=True),
                    "--live-check",
                    "--allow-insecure-http",
                    "--base-url",
                    base_url,
                )
            finally:
                server.shutdown()
                thread.join(timeout=3)
                server.server_close()

            self.assertFalse(report["passed"])
            self.assertFalse(report["checks"]["wechatDebugLoginRejected"]["passed"])


if __name__ == "__main__":
    unittest.main()
