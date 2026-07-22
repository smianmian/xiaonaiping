from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "inspect_final_screenshot_upload_files.py"
EXPECTED_SCREENSHOTS = [
    "01-home-iphone16pro.png",
    "02-record-iphone16pro.png",
    "03-growth-iphone16pro.png",
    "04-profile-iphone16pro.png",
    "05-profile-sync-iphone16pro.png",
]
REDACTION_CHECKS = [
    "real baby photo",
    "complete phone number",
    "verification code",
    "recovery key",
    "token",
    "object storage key",
    "local server marker",
    "debug marker",
    "internal dashboard",
    "Apple ID email",
    "unavailable WeChat success claim",
    "medical advice claim",
    "feeding recommendation claim",
    "pressure reminder claim",
]


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return len(data).to_bytes(4, "big") + kind + data + zlib.crc32(kind + data).to_bytes(4, "big")


def write_png(path: Path, width: int, height: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(((x * 3) % 256, (y * 5) % 256, ((x + y) * 7) % 256))
    ihdr = width.to_bytes(4, "big") + height.to_bytes(4, "big") + bytes([8, 2, 0, 0, 0])
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(rows)))
        + png_chunk(b"IEND", b"")
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screenshot_dir(root: Path) -> Path:
    return root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots"


def write_screenshots(root: Path, size: tuple[int, int] = (1320, 2868)) -> None:
    for filename in EXPECTED_SCREENSHOTS:
        write_png(screenshot_dir(root) / filename, size[0], size[1])


def write_upload_source_evidence(root: Path) -> None:
    evidence_root = root / "Docs/08_Release/AppStoreEvidence"
    write_png(evidence_root / "05-signed-archive.png", 1320, 2868)
    write_png(evidence_root / "06-testflight.png", 1320, 2868)
    write_png(evidence_root / "AppStoreConnect/ASC-07-build-testflight-link.png", 1320, 2868)
    write_png(evidence_root / "AppStoreConnect/ASC-02-version-information.png", 1320, 2868)
    regression = evidence_root / "12-real-device-regression.md"
    regression.parent.mkdir(parents=True, exist_ok=True)
    regression.write_text(
        "iOS 26.5 real-device regression evidence placeholder for unit test.\n"
        "RD-01 through RD-24 are represented here only to satisfy file-shape validation in a temporary fixture.\n",
        encoding="utf-8",
    )


def valid_upload_provenance(root: Path) -> dict:
    directory = screenshot_dir(root)
    return {
        "evidenceType": "final-app-store-upload",
        "status": "final App Store upload evidence captured from the same iOS 26.5 TestFlight build",
        "capturedAt": "2026-06-29T13:14:00+08:00",
        "installSource": "TestFlight",
        "appStoreDeviceSlot": 'iPhone 6.9" display',
        "device": {"name": "iPhone 17 Pro Max", "runtime": "iOS 26.5"},
        "app": {"bundleId": "com.mewpow.xiaonaiping", "version": "1.0", "build": "1"},
        "sourceEvidence": {
            "signedArchive": "../05-signed-archive.png",
            "testFlight": "../06-testflight.png",
            "appStoreConnectBuild": "../AppStoreConnect/ASC-07-build-testflight-link.png",
            "appStoreConnectScreenshotOrder": "../AppStoreConnect/ASC-02-version-information.png",
            "realDeviceRegression": "../12-real-device-regression.md",
        },
        "finalFiles": EXPECTED_SCREENSHOTS,
        "fileChecks": [
            {
                "filename": filename,
                "width": 1320,
                "height": 2868,
                "fileSizeBytes": (directory / filename).stat().st_size,
                "sha256": sha256_file(directory / filename),
                "redactionChecked": True,
                "matchesFinalUploadOrder": True,
                "secretValuesNotRecorded": True,
            }
            for filename in EXPECTED_SCREENSHOTS
        ],
        "redactionChecks": REDACTION_CHECKS,
    }


class FinalScreenshotUploadFileMetricsTest(unittest.TestCase):
    def run_inspector(self, root: Path, require_complete: bool = False) -> subprocess.CompletedProcess[str]:
        output = root / "Backend/proof/final-screenshot-upload-file-metrics.json"
        args = [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(root),
            "--output",
            str(output),
        ]
        if require_complete:
            args.append("--require-complete")
        return subprocess.run(args, text=True, capture_output=True)

    def read_report(self, root: Path) -> dict:
        return json.loads((root / "Backend/proof/final-screenshot-upload-file-metrics.json").read_text(encoding="utf-8"))

    def test_metrics_are_written_without_claiming_submit_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_screenshots(root)

            completed = self.run_inspector(root)
            report = self.read_report(root)

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertFalse(report["ready"])
            self.assertFalse(report["canSubmitFromThisReport"])
            self.assertTrue(report["metricsReady"])
            self.assertFalse(report["uploadProvenance"]["exists"])
            self.assertIn("missing UPLOAD_PROVENANCE.json", report["failedChecks"])
            self.assertEqual(report["fileChecksDraft"][0]["sha256"], sha256_file(screenshot_dir(root) / EXPECTED_SCREENSHOTS[0]))
            self.assertFalse(report["fileChecksDraft"][0]["redactionChecked"])

    def test_require_complete_fails_without_upload_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_screenshots(root)

            completed = self.run_inspector(root, require_complete=True)

            self.assertEqual(completed.returncode, 1)
            self.assertIn("missing UPLOAD_PROVENANCE.json", completed.stdout)

    def test_valid_upload_provenance_makes_report_ready_but_not_submit_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_screenshots(root)
            write_upload_source_evidence(root)
            (screenshot_dir(root) / "UPLOAD_PROVENANCE.json").write_text(
                json.dumps(valid_upload_provenance(root), ensure_ascii=False),
                encoding="utf-8",
            )

            completed = self.run_inspector(root, require_complete=True)
            report = self.read_report(root)

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertTrue(report["ready"])
            self.assertTrue(report["uploadProvenance"]["valid"])
            self.assertFalse(report["canSubmitFromThisReport"])

    def test_wrong_dimensions_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_screenshots(root, size=(1206, 2622))

            completed = self.run_inspector(root, require_complete=True)
            report = self.read_report(root)

            self.assertEqual(completed.returncode, 1)
            self.assertFalse(report["metricsReady"])
            self.assertIn(
                "01-home-iphone16pro.png: screenshot must be 1320x2868 for the current upload provenance template",
                report["failedChecks"],
            )


if __name__ == "__main__":
    unittest.main()
