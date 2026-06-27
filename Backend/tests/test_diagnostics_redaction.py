from __future__ import annotations

import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_diagnostics_redaction.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_privacy_manifest(path: Path, include_diagnostics: bool) -> None:
    collected = []
    if include_diagnostics:
        collected = [
            {
                "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeCrashData",
                "NSPrivacyCollectedDataTypeLinked": False,
                "NSPrivacyCollectedDataTypeTracking": False,
                "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
            },
            {
                "NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypePerformanceData",
                "NSPrivacyCollectedDataTypeLinked": False,
                "NSPrivacyCollectedDataTypeTracking": False,
                "NSPrivacyCollectedDataTypePurposes": ["NSPrivacyCollectedDataTypePurposeAppFunctionality"],
            },
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        plistlib.dump(
            {
                "NSPrivacyTracking": False,
                "NSPrivacyTrackingDomains": [],
                "NSPrivacyCollectedDataTypes": collected,
                "NSPrivacyAccessedAPITypes": [],
            },
            handle,
        )


def write_minimal_repo(root: Path, safe: bool) -> None:
    write(
        root / "Backend/api/server.py",
        """
class XiaoNaiPingHandler:
    @staticmethod
    def redacted_log_path(raw_path):
        if raw_path.startswith("/v1/photos/"):
            return "/v1/photos/<redacted>"
        return raw_path

    def log_message(self):
        path = self.redacted_log_path(self.path)
        print(path)
""".lstrip()
        if safe
        else """
class XiaoNaiPingHandler:
    def log_message(self):
        print(self.path)
""".lstrip(),
    )
    write(
        root / "App/iOS/project.yml",
        "name: XiaoNaiPing\n" if safe else "packages:\n  FirebaseCrashlytics: {}\n",
    )
    write(
        root / "App/iOS/XiaoNaiPing/App.swift",
        "struct AppRoot {}\n" if safe else "func leak() { print(\"baby name\") }\n",
    )
    write_privacy_manifest(root / "App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy", include_diagnostics=safe)


class DiagnosticsRedactionTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "diagnostics-redaction.json"
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

    def test_safe_repo_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_repo(root, safe=True)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertTrue(report["checks"]["backendPhotoLogPathRedacted"]["passed"])
            self.assertFalse(report["containsSecrets"])

    def test_sensitive_diagnostics_markers_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_repo(root, safe=False)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("iosNoThirdPartyCrashOrAnalyticsSDK", report["failedRequiredChecks"])
            self.assertIn("iosNoClientLoggingCalls", report["failedRequiredChecks"])
            self.assertIn("privacyManifestDiagnosticsDeclared", report["failedRequiredChecks"])
            self.assertIn("backendPhotoLogPathRedacted", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
