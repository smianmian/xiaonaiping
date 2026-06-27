from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_wechat_client_configuration.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_doc() -> str:
    return """
# WECHAT_CLIENT_CONFIGURATION.md

AppID format is wx + 16 hex. Client values are XNP_WECHAT_APP_ID,
XNP_WECHAT_URL_SCHEME, and XNP_WECHAT_UNIVERSAL_LINK. XNP_WECHAT_APP_SECRET
只配置在服务端，不能写进 iOS 工程。Evidence goes to 08-wechat-open-platform.

本机验证只使用 iOS 26.5。iOS 27.0 不能作为本机测试环境。

```bash
xcodebuild -sdk iphonesimulator26.5
xcodebuild -sdk iphoneos26.5
python3 Backend/scripts/check_ios_release_readiness.py
python3 Backend/scripts/check_ios_app_bundle.py
python3 Backend/scripts/prepare_wechat_release_env.py
python3 Backend/scripts/verify_auth_providers.py
python3 Backend/scripts/check_launch_objective_audit.py
```
""".lstrip()


def valid_project_yml() -> str:
    return """
settings:
  configs:
    Release:
      XNP_WECHAT_APP_ID: "$(XNP_WECHAT_APP_ID)"
      XNP_WECHAT_URL_SCHEME: "$(XNP_WECHAT_URL_SCHEME)"
      XNP_WECHAT_UNIVERSAL_LINK: "https://api.mewpow.com/xiaonaiping/wechat/"
      XNP_ASSOCIATED_DOMAIN: "applinks:api.mewpow.com"
""".lstrip()


def valid_info_plist() -> str:
    return """
<plist>
<dict>
  <key>CFBundleURLTypes</key>
  <array>
    <dict>
      <key>CFBundleURLSchemes</key>
      <array>
        <string>$(XNP_WECHAT_URL_SCHEME)</string>
      </array>
    </dict>
  </array>
  <key>LSApplicationQueriesSchemes</key>
  <array>
    <string>weixin</string>
    <string>weixinULAPI</string>
  </array>
  <key>XNPWeChatAppID</key>
  <string>$(XNP_WECHAT_APP_ID)</string>
  <key>XNPWeChatURLScheme</key>
  <string>$(XNP_WECHAT_URL_SCHEME)</string>
  <key>XNPWeChatUniversalLink</key>
  <string>$(XNP_WECHAT_UNIVERSAL_LINK)</string>
</dict>
</plist>
    """.lstrip()


def valid_entitlements() -> str:
    return """
<plist>
<dict>
  <key>com.apple.developer.associated-domains</key>
  <array>
    <string>$(XNP_ASSOCIATED_DOMAIN)</string>
  </array>
</dict>
</plist>
""".lstrip()


def write_valid_inputs(root: Path, doc: str | None = None) -> None:
    write(root / "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md", doc if doc is not None else valid_doc())
    write(root / "App/iOS/project.yml", valid_project_yml())
    write(root / "App/iOS/XiaoNaiPing/Info.plist", valid_info_plist())
    write(root / "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements", valid_entitlements())


class WeChatClientConfigurationTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/wechat-client-configuration.json"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(root),
                "--output",
                str(output),
                "--allow-incomplete",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(output.read_text(encoding="utf-8"))

    def test_complete_configuration_handoff_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_ios_265_commands_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc().replace("-sdk iphoneos26.5", "-sdk iphoneos")
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ios265ValidationCommandsPresent", report["failedRequiredChecks"])
            self.assertEqual(report["checks"]["ios265ValidationCommandsPresent"]["missingMarkers"], ["-sdk iphoneos26.5"])

    def test_app_secret_assignment_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc() + "\nexport XNP_WECHAT_APP_SECRET=secret\n"
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("docDoesNotAssignAppSecret", report["failedRequiredChecks"])

    def test_missing_auth_provider_validation_command_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            doc = valid_doc().replace("python3 Backend/scripts/verify_auth_providers.py\n", "")
            write_valid_inputs(root, doc)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("proofRegenerationCommandsPresent", report["failedRequiredChecks"])
            self.assertEqual(
                report["checks"]["proofRegenerationCommandsPresent"]["missingMarkers"],
                ["verify_auth_providers.py"],
            )

    def test_missing_associated_domains_entitlement_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_inputs(root)
            write(root / "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements", "<plist><dict></dict></plist>\n")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("associatedDomainsEntitlementWired", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
