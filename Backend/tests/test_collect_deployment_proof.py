from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "collect_deployment_proof.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


class CollectDeploymentProofTest(unittest.TestCase):
    def run_collector(self, env_file: Path) -> dict:
        output = env_file.parent / "deploy-proof.json"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--env-file",
                str(env_file),
                "--output",
                str(output),
                "--service-active",
                "--public-internal-blocked",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(output.read_text(encoding="utf-8"))

    def test_collects_non_secret_provider_state(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            env_file = Path(tempdir) / "xiaonaiping-api.env"
            write(
                env_file,
                """
XNP_DEPLOYMENT_TARGET=huawei_baota
XNP_HOST=127.0.0.1
XNP_PORT=8787
XNP_DATA_DIR=/srv/xiaonaiping/data
XNP_SECRET_KEY=super-secret-value
XNP_ADMIN_TOKEN=super-admin-token
XNP_AUTH_DEBUG_MODE=0
XNP_DATABASE_BACKEND=mysql
XNP_MYSQL_HOST=127.0.0.1
XNP_MYSQL_PORT=3306
XNP_MYSQL_USER=xiaonaiping_app
XNP_MYSQL_PASSWORD=mysql-secret
XNP_MYSQL_DATABASE=xiaonaiping_prod
XNP_STORAGE_BACKEND=huawei_obs
HUAWEI_OBS_ACCESS_KEY_ID=obs-ak
HUAWEI_OBS_SECRET_ACCESS_KEY=obs-sk
HUAWEI_OBS_ENDPOINT=https://obs.cn-south-1.myhuaweicloud.com
HUAWEI_OBS_BUCKET=xiaonaiping-prod-private
HUAWEI_OBS_PREFIX=xiaonaiping
XNP_SMS_PROVIDER=webhook
XNP_SMS_WEBHOOK_URL=https://sms.xiaonaiping.cn/send
XNP_SMS_SECRET=sms-secret
XNP_WECHAT_APP_ID=wxa4f19c3e802b7d65
XNP_WECHAT_APP_SECRET=wechat-secret
""".strip(),
            )

            proof = self.run_collector(env_file)
            serialized = json.dumps(proof, ensure_ascii=False)

            self.assertFalse(proof["containsSecrets"])
            self.assertNotIn("super-secret-value", serialized)
            self.assertNotIn("mysql-secret", serialized)
            self.assertNotIn("obs-sk", serialized)
            self.assertNotIn("sms-secret", serialized)
            self.assertNotIn("wechat-secret", serialized)
            self.assertTrue(proof["providerChecks"]["storageBackendIsHuaweiOBS"])
            self.assertTrue(proof["providerChecks"]["obsBucketHasXiaoNaiPingNamespace"])
            self.assertTrue(proof["providerChecks"]["smsProviderIsWebhook"])
            self.assertTrue(proof["providerChecks"]["wechatAppIDConfigured"])
            self.assertEqual(proof["remainingProductionBlockers"], [])

    def test_placeholders_are_reported_as_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            env_file = Path(tempdir) / "xiaonaiping-api.env"
            write(
                env_file,
                """
XNP_DATA_DIR=/srv/xiaonaiping/data
XNP_STORAGE_BACKEND=disk
HUAWEI_OBS_BUCKET=replace-with-bucket
HUAWEI_OBS_PREFIX=xiaonaiping
XNP_SMS_PROVIDER=
XNP_WECHAT_APP_ID=replace-with-wechat-app-id
XNP_WECHAT_APP_SECRET=
""".strip(),
            )

            proof = self.run_collector(env_file)

            self.assertIn("HUAWEI_OBS_BUCKET", proof["privateEnvStatus"]["placeholder"])
            self.assertIn("XNP_WECHAT_APP_ID", proof["privateEnvStatus"]["placeholder"])
            self.assertFalse(proof["providerChecks"]["storageBackendIsHuaweiOBS"])
            self.assertFalse(proof["providerChecks"]["smsProviderIsWebhook"])
            self.assertTrue(proof["remainingProductionBlockers"])

    def test_sample_wechat_app_id_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            env_file = Path(tempdir) / "xiaonaiping-api.env"
            write(
                env_file,
                """
XNP_DATA_DIR=/srv/xiaonaiping/data
XNP_STORAGE_BACKEND=huawei_obs
HUAWEI_OBS_BUCKET=xiaonaiping-prod-private
HUAWEI_OBS_PREFIX=xiaonaiping
XNP_SMS_PROVIDER=webhook
XNP_SMS_WEBHOOK_URL=https://sms.xiaonaiping.cn/send
XNP_SMS_SECRET=sms-secret
XNP_WECHAT_APP_ID=wx1234567890abcdef
XNP_WECHAT_APP_SECRET=wechat-secret
""".strip(),
            )

            proof = self.run_collector(env_file)

            self.assertFalse(proof["providerChecks"]["wechatAppIDConfigured"])
            self.assertTrue(
                any("WeChat Open Platform AppID/AppSecret" in blocker for blocker in proof["remainingProductionBlockers"])
            )

    def test_missing_env_file_fails_before_writing_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            missing_env = Path(tempdir) / "missing.env"
            output = Path(tempdir) / "deploy-proof.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--env-file",
                    str(missing_env),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("env file not found", completed.stderr + completed.stdout)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
