from __future__ import annotations

import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_universal_links.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_plist(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        plistlib.dump(value, file)


def write_universal_link_repo(root: Path, current: bool) -> None:
    associated_domain = "applinks:api.mewpow.com" if current else ""
    universal_link = "https://api.mewpow.com/xiaonaiping/wechat/" if current else ""
    write(
        root / "App/iOS/project.yml",
        f"""
targets:
  XiaoNaiPing:
    entitlements:
      path: XiaoNaiPing/XiaoNaiPing.entitlements
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: com.mewpow.xiaonaiping
        DEVELOPMENT_TEAM: L2TYJNDTJK
      configs:
        Release:
          XNP_WECHAT_UNIVERSAL_LINK: "{universal_link}"
          XNP_ASSOCIATED_DOMAIN: "{associated_domain}"
""".lstrip(),
    )
    write_plist(
        root / "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements",
        {"com.apple.developer.associated-domains": ["$(XNP_ASSOCIATED_DOMAIN)"] if current else []},
    )
    paths = ["/wechat/*", "/xiaonaiping/wechat/*"] if current else ["/old/*"]
    write(
        root / "Backend/static/apple-app-site-association",
        json.dumps(
            {
                "applinks": {
                    "apps": [],
                    "details": [
                        {
                            "appID": "L2TYJNDTJK.com.mewpow.xiaonaiping",
                            "paths": paths,
                        }
                    ],
                }
            }
        ),
    )
    routes = """
STATIC_ROUTES = {
    "/apple-app-site-association": ("apple-app-site-association", "application/json; charset=utf-8"),
    "/.well-known/apple-app-site-association": ("apple-app-site-association", "application/json; charset=utf-8"),
}
""" if current else "STATIC_ROUTES = {}\n"
    write(root / "Backend/api/server.py", routes)


class UniversalLinksTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "universal-links.json"
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

    def test_current_universal_links_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_universal_link_repo(root, current=True)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertFalse(report["containsSecrets"])

    def test_missing_universal_link_setup_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_universal_link_repo(root, current=False)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("aasaWeChatCallbackPathsPresent", report["failedRequiredChecks"])
            self.assertIn("backendAASARoutesConfigured", report["failedRequiredChecks"])
            self.assertIn("iosAssociatedDomainsEntitlementPresent", report["failedRequiredChecks"])
            self.assertIn("releaseWeChatUniversalLinkConfigured", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
