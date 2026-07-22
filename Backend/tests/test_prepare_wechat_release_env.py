from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_wechat_release_env.py"
VALID_APP_ID = "wxa4f19c3e802b7d65"


class PrepareWeChatReleaseEnvTest(unittest.TestCase):
    def test_valid_values_write_env_and_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            env_path = root / "wechat.env"
            proof_path = root / "wechat.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--app-id",
                    VALID_APP_ID,
                    "--output-env",
                    str(env_path),
                    "--output-json",
                    str(proof_path),
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            env_text = env_path.read_text(encoding="utf-8")
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            self.assertTrue(proof["passed"])
            self.assertFalse(proof["containsSecrets"])
            self.assertIn(f"export XNP_WECHAT_APP_ID={VALID_APP_ID}", env_text)
            self.assertIn(f"export XNP_WECHAT_URL_SCHEME={VALID_APP_ID}", env_text)
            self.assertIn("XNP_WECHAT_UNIVERSAL_LINK", env_text)
            self.assertNotIn("SECRET", env_text)
            self.assertIn('XNP_WECHAT_APP_ID="$XNP_WECHAT_APP_ID"', env_text)
            self.assertIn('XNP_WECHAT_URL_SCHEME="$XNP_WECHAT_URL_SCHEME"', env_text)
            self.assertIn('XNP_WECHAT_UNIVERSAL_LINK="$XNP_WECHAT_UNIVERSAL_LINK"', env_text)
            self.assertEqual(
                proof["xcodebuildBuildSettingTemplate"],
                [
                    'XNP_WECHAT_APP_ID="$XNP_WECHAT_APP_ID"',
                    'XNP_WECHAT_URL_SCHEME="$XNP_WECHAT_URL_SCHEME"',
                    'XNP_WECHAT_UNIVERSAL_LINK="$XNP_WECHAT_UNIVERSAL_LINK"',
                ],
            )
            self.assertEqual(proof["envValues"], {})

    def test_placeholder_app_id_fails(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--app-id",
                "wxclientdryrun123456",
            ],
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("appIDLooksReal", result.stderr)

    def test_sample_app_id_fails(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--app-id",
                "wx1234567890abcdef",
            ],
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("appIDLooksReal", result.stderr)

    def test_repeated_hex_app_id_fails(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--app-id",
                "wx0000000000000000",
            ],
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("appIDLooksReal", result.stderr)

    def test_mismatched_url_scheme_fails(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--app-id",
                VALID_APP_ID,
                "--url-scheme",
                "wxabcdef1234567890",
            ],
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("urlSchemeMatchesAppID", result.stderr)

    def test_non_https_universal_link_fails(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--app-id",
                VALID_APP_ID,
                "--universal-link",
                "http://api.mewpow.com/xiaonaiping/wechat/",
            ],
            text=True,
            capture_output=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("universalLinkAllowed", result.stderr)


if __name__ == "__main__":
    unittest.main()
