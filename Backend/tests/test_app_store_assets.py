from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_app_store_assets.py"
EXPECTED_SCREENSHOTS = [
    "01-home-iphone16pro.png",
    "02-record-iphone16pro.png",
    "03-growth-iphone16pro.png",
    "04-profile-iphone16pro.png",
    "05-profile-backup-iphone16pro.png",
]


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return len(data).to_bytes(4, "big") + kind + data + zlib.crc32(kind + data).to_bytes(4, "big")


def write_png(path: Path, width: int, height: int, color_type: int = 2, blank: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    channels = {2: 3, 6: 4}[color_type]
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            if blank:
                rgb = (245, 245, 245)
            else:
                rgb = ((x * 3) % 256, (y * 5) % 256, ((x + y) * 7) % 256)
            rows.extend(rgb)
            if channels == 4:
                rows.append(255)
    ihdr = (
        width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + bytes([8, color_type, 0, 0, 0])
    )
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(rows)))
        + png_chunk(b"IEND", b"")
    )


def valid_provenance() -> dict:
    return {
        "status": "iOS 26.5 Debug simulator App Store screenshot candidates; not a TestFlight, signed-device, or Release build final evidence substitute",
        "device": {"name": "iPhone 17 Pro", "runtime": "iOS 26.5"},
        "app": {"bundleId": "com.mewpow.xiaonaiping", "sdkName": "iphonesimulator26.5"},
        "command": "python3 Backend/scripts/capture_ios_screenshots.py --device IOS_26_5_SIMULATOR_UDID",
        "finalFiles": EXPECTED_SCREENSHOTS,
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
    sizes = [(640, 920)] * 5 if valid else [(640, 920), (100, 100)]
    filenames = EXPECTED_SCREENSHOTS if valid else ["01-home-iphone16pro.png", "unexpected.png"]
    for filename, (width, height) in zip(filenames, sizes):
        write_png(root / f"Docs/08_Release/AppStoreEvidence/10-final-screenshots/{filename}", width, height, color_type=6)
    write(
        root / "Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json",
        json.dumps(valid_provenance(), ensure_ascii=False),
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


if __name__ == "__main__":
    unittest.main()
