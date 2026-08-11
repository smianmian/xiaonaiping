from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

from scripts.check_app_store_assets import (
    EXPECTED_BUNDLE_ID,
    EXPECTED_SCREENSHOT_RUNTIME,
    EXPECTED_UPLOAD_SOURCE_EVIDENCE,
    FINAL_SCREENSHOT_UPLOAD_REDACTION_MARKERS,
    UPLOAD_PROVENANCE_TEMPLATE_NOTE_MARKERS,
    UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS,
    UPLOAD_PROVENANCE_TEMPLATE_STATUS,
)


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_app_store_assets.py"
EXPECTED_SCREENSHOTS = [
    "01-home-iphone16pro.png",
    "02-record-iphone16pro.png",
    "03-growth-iphone16pro.png",
    "04-profile-iphone16pro.png",
    "05-profile-sync-iphone16pro.png",
]


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return len(data).to_bytes(4, "big") + kind + data + zlib.crc32(kind + data).to_bytes(4, "big")


def write_png(path: Path, width: int, height: int, color_type: int = 2, blank: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    channels = {2: 3, 6: 4}[color_type]
    if blank:
        pixel = bytes((245, 245, 245, 255)) if channels == 4 else bytes((245, 245, 245))
        scanline = b"\x00" + pixel * width
    else:
        pixels = bytearray()
        for x in range(width):
            pixels.extend(((x * 3) % 256, (x * 5) % 256, (x * 7) % 256))
            if channels == 4:
                pixels.append(255)
        scanline = b"\x00" + bytes(pixels)
    rows = scanline * height
    ihdr = (
        width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + bytes([8, color_type, 0, 0, 0])
    )
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(rows))
        + png_chunk(b"IEND", b"")
    )


def write_blob(path: Path, size: int = 12 * 1024) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"proof" * (size // 5 + 1))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_provenance() -> dict:
    return {
        "capturedAt": "2026-06-28T10:47:00+08:00",
        "status": "iOS 26.5 Debug simulator App Store screenshot candidates; not a TestFlight, signed-device, or Release build final evidence substitute",
        "device": {"name": "iPhone 17 Pro", "runtime": "iOS 26.5"},
        "app": {"bundleId": "com.mewpow.xiaonaiping", "sdkName": "iphonesimulator26.5"},
        "command": "python3 Backend/scripts/capture_ios_screenshots.py --device IOS_26_5_SIMULATOR_UDID",
        "finalFiles": EXPECTED_SCREENSHOTS,
    }


def valid_upload_provenance(root: Path) -> dict:
    screenshot_dir = root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots"
    def file_check(filename: str) -> dict:
        path = screenshot_dir / filename
        return {
            "filename": filename,
            "width": 1320,
            "height": 2868,
            "fileSizeBytes": path.stat().st_size if path.exists() else 0,
            "sha256": sha256_file(path) if path.exists() else "0" * 64,
            "redactionChecked": True,
            "matchesFinalUploadOrder": True,
            "secretValuesNotRecorded": True,
        }

    return {
        "evidenceType": "final-app-store-upload",
        "status": "iOS 26.5 TestFlight final App Store upload evidence for iPhone 6.9 display",
        "capturedAt": "2026-06-28T13:14:00+08:00",
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
        "fileChecks": [file_check(filename) for filename in EXPECTED_SCREENSHOTS],
        "redactionChecks": [
            "real baby photo",
            "complete phone number",
            "verification code",
            "account credentials",
            "WeChat credentials",
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
        ],
    }


def valid_upload_provenance_template() -> dict:
    return {
        "evidenceType": "final-app-store-upload",
        "status": UPLOAD_PROVENANCE_TEMPLATE_STATUS,
        "capturedAt": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["capturedAt"],
        "installSource": "TestFlight",
        "appStoreDeviceSlot": 'iPhone 6.9" display',
        "device": {
            "name": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["device.name"],
            "runtime": EXPECTED_SCREENSHOT_RUNTIME,
        },
        "app": {
            "bundleId": EXPECTED_BUNDLE_ID,
            "version": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["app.version"],
            "build": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["app.build"],
        },
        "sourceEvidence": dict(EXPECTED_UPLOAD_SOURCE_EVIDENCE),
        "finalFiles": list(EXPECTED_SCREENSHOTS),
        "fileChecks": [
            {
                "filename": filename,
                "width": 1320,
                "height": 2868,
                "fileSizeBytes": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["fileSizeBytes"],
                "sha256": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["sha256"],
                "redactionChecked": False,
                "matchesFinalUploadOrder": False,
                "secretValuesNotRecorded": False,
            }
            for filename in EXPECTED_SCREENSHOTS
        ],
        "redactionChecks": list(FINAL_SCREENSHOT_UPLOAD_REDACTION_MARKERS),
        "notes": list(UPLOAD_PROVENANCE_TEMPLATE_NOTE_MARKERS),
    }


def write_assets(root: Path, valid: bool) -> None:
    write(
        root / "App/iOS/XiaoNaiPing/Assets.xcassets/AppIcon.appiconset/Contents.json",
        json.dumps(
            {
                "images": [
                    {
                        "filename": "AppIcon-1024.png",
                        "idiom": "universal",
                        "platform": "ios",
                        "size": "1024x1024",
                    }
                ],
                "info": {"author": "xcode", "version": 1},
            }
        ),
    )
    write_png(
        root / "App/iOS/XiaoNaiPing/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png",
        1024,
        1024,
        color_type=2 if valid else 6,
    )
    sizes = [(1320, 2868)] * 5 if valid else [(640, 920), (100, 100)]
    filenames = EXPECTED_SCREENSHOTS if valid else ["01-home-iphone16pro.png", "unexpected.png"]
    for filename, (width, height) in zip(filenames, sizes):
        write_png(root / f"Docs/08_Release/AppStoreEvidence/10-final-screenshots/{filename}", width, height, color_type=6)
    write(
        root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json",
        json.dumps(valid_provenance(), ensure_ascii=False),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/README.md",
        "\n".join(
            [
                "# Final Screenshot Candidates",
                "",
                "Date: 2026-06-28",
                "",
                "These screenshots are current candidates. PROVENANCE.json records the iOS 26.5 capture.",
                "These are not TestFlight final evidence.",
                "Final upload evidence must add UPLOAD_PROVENANCE.json.",
            ]
        ),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
        json.dumps(valid_upload_provenance(root), ensure_ascii=False),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.template.json",
        json.dumps(valid_upload_provenance_template(), ensure_ascii=False),
    )
    for relative_path in [
        "Docs/08_Release/AppStoreEvidence/05-signed-archive.png",
        "Docs/08_Release/AppStoreEvidence/06-testflight.png",
        "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-07-build-testflight-link.png",
        "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-02-version-information.png",
    ]:
        write_blob(root / relative_path)
    write(
        root / "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
        "iOS 26.5 TestFlight real-device regression source evidence\n" * 3,
    )


class AppStoreAssetsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/app-store-assets.json"
        completed = subprocess.run(
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
        self.assertIn("App Store assets", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_assets_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_icon_alpha_and_bad_screenshot_size_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=False)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appIconHasNoAlpha", report["failedRequiredChecks"])
            self.assertIn("finalScreenshotsCount", report["failedRequiredChecks"])
            self.assertIn("finalScreenshotsExpectedUploadOrder", report["failedRequiredChecks"])
            self.assertIn("finalScreenshotsAcceptedSizes", report["failedRequiredChecks"])

    def test_blank_screenshots_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            for filename in EXPECTED_SCREENSHOTS:
                write_png(root / f"Docs/08_Release/AppStoreEvidence/10-final-screenshots/{filename}", 640, 920, color_type=2, blank=True)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsNotBlank", report["failedRequiredChecks"])

    def test_missing_or_stale_ios265_provenance_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json",
                json.dumps(
                    {
                        **valid_provenance(),
                        "device": {"name": "iPhone 16 Pro", "runtime": "iOS 18.5"},
                        "app": {"bundleId": "com.mewpow.xiaonaiping", "sdkName": "iphonesimulator18.5"},
                    },
                    ensure_ascii=False,
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsIOS265ProvenancePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["finalScreenshotsIOS265ProvenancePresent"]["evidence"]
            self.assertIn("device.runtime must be iOS 26.5", evidence)
            self.assertIn("app.sdkName must be iphonesimulator26.5", evidence)

    def test_stale_screenshot_candidate_readme_date_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/README.md",
                "# Final Screenshot Candidates\n\nDate: 2026-06-27\n\nPROVENANCE.json\nnot TestFlight\nUPLOAD_PROVENANCE.json\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsCandidateReadmeMatchesProvenance", report["failedRequiredChecks"])
            self.assertIn(
                "README.md Date must match PROVENANCE.json capturedAt date 2026-06-28",
                report["checks"]["finalScreenshotsCandidateReadmeMatchesProvenance"]["evidence"],
            )

    def test_missing_final_upload_provenance_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                json.dumps(
                    {
                        "evidenceType": "candidate",
                        "status": "iOS 26.5 Debug simulator screenshot candidate, not a TestFlight final upload",
                        "installSource": "Debug simulator",
                        "appStoreDeviceSlot": 'iPhone 6.3" display',
                        "device": {"name": "iPhone 17 Pro", "runtime": "iOS 26.5"},
                        "finalFiles": EXPECTED_SCREENSHOTS,
                    },
                    ensure_ascii=False,
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenancePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["finalScreenshotsUploadProvenancePresent"]["evidence"]
            self.assertIn("evidenceType must be final-app-store-upload", evidence)
            self.assertIn("capturedAt must be an ISO timestamp with timezone", evidence)
            self.assertIn("installSource must be TestFlight or Xcode 签名真机包", evidence)
            self.assertIn('appStoreDeviceSlot must be iPhone 6.9" display', evidence)

    def test_copied_upload_provenance_template_is_not_final_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                json.dumps(valid_upload_provenance_template(), ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenancePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["finalScreenshotsUploadProvenancePresent"]["evidence"]
            self.assertIn("capturedAt must be an ISO timestamp with timezone", evidence)
            self.assertIn("device.name must be filled with the physical device name", evidence)
            self.assertIn("app.version must be filled with the App Store version", evidence)
            self.assertIn("UPLOAD_PROVENANCE.json still contains template markers", evidence)

    def test_upload_provenance_must_bind_app_store_connect_selected_build(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            provenance = valid_upload_provenance(root)
            del provenance["sourceEvidence"]["appStoreConnectBuild"]
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                json.dumps(provenance, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenancePresent", report["failedRequiredChecks"])
            self.assertIn(
                "sourceEvidence.appStoreConnectBuild must be ../AppStoreConnect/ASC-07-build-testflight-link.png",
                report["checks"]["finalScreenshotsUploadProvenancePresent"]["evidence"],
            )

    def test_upload_provenance_must_bind_app_store_connect_screenshot_order(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            provenance = valid_upload_provenance(root)
            del provenance["sourceEvidence"]["appStoreConnectScreenshotOrder"]
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                json.dumps(provenance, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenancePresent", report["failedRequiredChecks"])
            self.assertIn(
                "sourceEvidence.appStoreConnectScreenshotOrder must be ../AppStoreConnect/ASC-02-version-information.png",
                report["checks"]["finalScreenshotsUploadProvenancePresent"]["evidence"],
            )

    def test_upload_provenance_requires_real_source_evidence_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            (root / "Docs/08_Release/AppStoreEvidence/06-testflight.png").unlink()

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenancePresent", report["failedRequiredChecks"])
            self.assertIn(
                "sourceEvidence.testFlight file missing: 06-testflight.png",
                report["checks"]["finalScreenshotsUploadProvenancePresent"]["evidence"],
            )

    def test_upload_provenance_final_files_must_match_exact_upload_order(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            provenance = valid_upload_provenance(root)
            provenance["finalFiles"] = [
                "02-record-iphone16pro.png",
                "01-home-iphone16pro.png",
                "03-growth-iphone16pro.png",
                "04-profile-iphone16pro.png",
                "04-profile-iphone16pro.png",
            ]
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                json.dumps(provenance, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenancePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["finalScreenshotsUploadProvenancePresent"]["evidence"]
            self.assertIn("finalFiles missing: 05-profile-sync-iphone16pro.png", evidence)
            self.assertIn("finalFiles must match expected upload order exactly", evidence)

    def test_upload_provenance_must_include_redaction_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            provenance = valid_upload_provenance(root)
            provenance["redactionChecks"] = ["token"]
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                json.dumps(provenance, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenancePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["finalScreenshotsUploadProvenancePresent"]["evidence"]
            self.assertIn("redactionChecks missing real baby photo", evidence)
            self.assertIn("redactionChecks missing unavailable WeChat success claim", evidence)
            self.assertIn("redactionChecks missing medical advice claim", evidence)
            self.assertIn("redactionChecks missing pressure reminder claim", evidence)

    def test_upload_provenance_file_checks_must_match_actual_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            provenance = valid_upload_provenance(root)
            provenance["fileChecks"][0]["sha256"] = "0" * 64
            provenance["fileChecks"][0]["redactionChecked"] = False
            provenance["fileChecks"][0]["secretValuesNotRecorded"] = False
            provenance["fileChecks"][1]["matchesFinalUploadOrder"] = False
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                json.dumps(provenance, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenancePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["finalScreenshotsUploadProvenancePresent"]["evidence"]
            self.assertIn("fileChecks.01-home-iphone16pro.png.sha256 must be", evidence)
            self.assertIn("fileChecks.01-home-iphone16pro.png.redactionChecked must be True", evidence)
            self.assertIn("fileChecks.01-home-iphone16pro.png.secretValuesNotRecorded must be True", evidence)
            self.assertIn("fileChecks.02-record-iphone16pro.png.matchesFinalUploadOrder must be True", evidence)

    def test_upload_provenance_template_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            template = valid_upload_provenance_template()
            template["capturedAt"] = "2026-06-28T13:14:00+08:00"
            template["device"]["name"] = "iPhone 17 Pro Max"
            template["app"]["version"] = "1.0"
            template["fileChecks"][0]["secretValuesNotRecorded"] = True
            template["finalFiles"] = template["finalFiles"][:-1]
            template["redactionChecks"] = ["token"]
            template["notes"] = []
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.template.json",
                json.dumps(template, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsUploadProvenanceTemplateValid", report["failedRequiredChecks"])
            evidence = report["checks"]["finalScreenshotsUploadProvenanceTemplateValid"]["evidence"]
            self.assertIn("capturedAt must be YYYY-MM-DDTHH:MM:SS+08:00", evidence)
            self.assertIn("device.name must be FILL_WITH_PHYSICAL_DEVICE_NAME", evidence)
            self.assertIn("app.version must be FILL_WITH_APP_VERSION", evidence)
            self.assertIn("fileChecks.01-home-iphone16pro.png.secretValuesNotRecorded must be False", evidence)
            self.assertIn("finalFiles must match expected upload order exactly", evidence)
            self.assertIn("redactionChecks order must be", evidence)
            self.assertIn("notes missing Copy this file to UPLOAD_PROVENANCE.json", evidence)

    def test_non_iphone69_upload_sizes_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            write_png(root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/01-home-iphone16pro.png", 1206, 2622, color_type=2)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsIphone69SlotReady", report["failedRequiredChecks"])
            self.assertIn(
                "01-home-iphone16pro.png",
                report["checks"]["finalScreenshotsIphone69SlotReady"]["evidence"],
            )

    def test_risky_screenshot_filename_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            risky_path = root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/01-debug-token-iphone16pro.png"
            (root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/01-home-iphone16pro.png").rename(risky_path)
            provenance = valid_provenance()
            provenance["finalFiles"] = [
                "01-debug-token-iphone16pro.png" if filename == "01-home-iphone16pro.png" else filename
                for filename in EXPECTED_SCREENSHOTS
            ]
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json",
                json.dumps(provenance, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsNoRiskyFilenames", report["failedRequiredChecks"])

    def test_provenance_local_or_secret_marker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_assets(root, valid=True)
            provenance = valid_provenance()
            provenance["command"] = provenance["command"] + " --api http://127.0.0.1:8787"
            write(
                root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json",
                json.dumps(provenance, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalScreenshotsIOS265ProvenancePresent", report["failedRequiredChecks"])
            self.assertIn("127.0.0.1", report["checks"]["finalScreenshotsIOS265ProvenancePresent"]["evidence"])


if __name__ == "__main__":
    unittest.main()
