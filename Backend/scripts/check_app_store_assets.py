#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACCEPTED_IPHONE_SCREENSHOT_SIZES = {
    (1260, 2736),
    (2736, 1260),
    (1290, 2796),
    (2796, 1290),
    (1320, 2868),
    (2868, 1320),
    (1284, 2778),
    (2778, 1284),
    (1242, 2688),
    (2688, 1242),
    (1179, 2556),
    (2556, 1179),
    (1206, 2622),
    (2622, 1206),
    (1170, 2532),
    (2532, 1170),
    (1125, 2436),
    (2436, 1125),
    (1080, 2340),
    (2340, 1080),
    (1242, 2208),
    (2208, 1242),
    (750, 1334),
    (1334, 750),
    (640, 1096),
    (640, 1136),
    (1136, 600),
    (1136, 640),
    (640, 920),
    (640, 960),
    (960, 600),
    (960, 640),
}

PNG_COLOR_TYPES_WITH_ALPHA = {4, 6}
PNG_CHANNELS_BY_COLOR_TYPE = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
EXPECTED_FINAL_SCREENSHOT_FILENAMES = [
    "01-home-iphone16pro.png",
    "02-record-iphone16pro.png",
    "03-growth-iphone16pro.png",
    "04-profile-iphone16pro.png",
    "05-profile-backup-iphone16pro.png",
]
EXPECTED_SCREENSHOT_RUNTIME = "iOS 26.5"
EXPECTED_SCREENSHOT_SDK = "iphonesimulator26.5"
SCREENSHOT_PROVENANCE_FILE = "PROVENANCE.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def png_info(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()[:33]
    except OSError as error:
        return {"valid": False, "error": str(error)}
    if len(data) < 26 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return {"valid": False, "error": "not a PNG with IHDR header"}
    return {
        "valid": True,
        "width": int.from_bytes(data[16:20], "big"),
        "height": int.from_bytes(data[20:24], "big"),
        "bitDepth": data[24],
        "colorType": data[25],
    }


def paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def unfilter_png_scanline(filter_type: int, row: bytearray, previous: bytes, bytes_per_pixel: int) -> bytes:
    for index, value in enumerate(row):
        left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
        up = previous[index] if previous else 0
        upper_left = previous[index - bytes_per_pixel] if previous and index >= bytes_per_pixel else 0
        if filter_type == 1:
            row[index] = (value + left) & 0xFF
        elif filter_type == 2:
            row[index] = (value + up) & 0xFF
        elif filter_type == 3:
            row[index] = (value + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            row[index] = (value + paeth_predictor(left, up, upper_left)) & 0xFF
        elif filter_type != 0:
            raise ValueError(f"unsupported PNG filter type {filter_type}")
    return bytes(row)


def png_visual_metrics(path: Path, max_sampled_pixels: int = 20000) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as error:
        return {"valid": False, "error": str(error)}
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return {"valid": False, "error": "not a PNG"}

    offset = 8
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width = int.from_bytes(chunk_data[0:4], "big")
            height = int.from_bytes(chunk_data[4:8], "big")
            bit_depth = chunk_data[8]
            color_type = chunk_data[9]
            interlace = chunk_data[12]
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if not all(value is not None for value in [width, height, bit_depth, color_type, interlace]):
        return {"valid": False, "error": "missing IHDR"}
    if bit_depth != 8 or interlace != 0 or color_type not in PNG_CHANNELS_BY_COLOR_TYPE:
        return {
            "valid": False,
            "error": f"unsupported PNG encoding: bitDepth={bit_depth}, colorType={color_type}, interlace={interlace}",
        }
    if not idat:
        return {"valid": False, "error": "missing IDAT image data"}

    channels = PNG_CHANNELS_BY_COLOR_TYPE[int(color_type)]
    stride = int(width) * channels
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as error:
        return {"valid": False, "error": f"invalid IDAT data: {error}"}

    expected_length = (stride + 1) * int(height)
    if len(raw) < expected_length:
        return {"valid": False, "error": f"truncated image data: {len(raw)} < {expected_length}"}

    rows: list[bytes] = []
    previous = bytes(stride)
    cursor = 0
    try:
        for _ in range(int(height)):
            filter_type = raw[cursor]
            cursor += 1
            row = bytearray(raw[cursor : cursor + stride])
            cursor += stride
            restored = unfilter_png_scanline(filter_type, row, previous, channels)
            rows.append(restored)
            previous = restored
    except ValueError as error:
        return {"valid": False, "error": str(error)}

    total_pixels = int(width) * int(height)
    step = max(1, total_pixels // max_sampled_pixels)
    sampled = 0
    unique_pixels: set[tuple[int, ...]] = set()
    channel_mins = [255, 255, 255]
    channel_maxes = [0, 0, 0]
    for pixel_index in range(0, total_pixels, step):
        row = rows[pixel_index // int(width)]
        column = pixel_index % int(width)
        start = column * channels
        pixel = tuple(row[start : start + channels])
        if color_type in {0, 3}:
            rgb = (pixel[0], pixel[0], pixel[0])
        else:
            rgb = pixel[:3]
        unique_pixels.add(rgb)
        sampled += 1
        for index, value in enumerate(rgb):
            channel_mins[index] = min(channel_mins[index], value)
            channel_maxes[index] = max(channel_maxes[index], value)

    return {
        "valid": True,
        "sampledPixels": sampled,
        "uniqueSampledPixels": len(unique_pixels),
        "maxChannelRange": max(channel_maxes[index] - channel_mins[index] for index in range(3)),
    }


def screenshot_files(path: Path) -> list[Path]:
    return sorted(
        file
        for file in path.rglob("*")
        if file.is_file() and file.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )


def screenshot_provenance_failures(data: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    device = data.get("device", {})
    app = data.get("app", {})
    final_files = data.get("finalFiles", [])
    status = str(data.get("status", "")).lower()
    command = str(data.get("command", ""))
    if not isinstance(device, dict):
        failures.append("device must be an object")
        device = {}
    if not isinstance(app, dict):
        failures.append("app must be an object")
        app = {}
    if not isinstance(final_files, list):
        failures.append("finalFiles must be an array")
        final_files = []

    if device.get("runtime") != EXPECTED_SCREENSHOT_RUNTIME:
        failures.append(f"device.runtime must be {EXPECTED_SCREENSHOT_RUNTIME}")
    if app.get("sdkName") != EXPECTED_SCREENSHOT_SDK:
        failures.append(f"app.sdkName must be {EXPECTED_SCREENSHOT_SDK}")
    missing_files = [
        filename for filename in EXPECTED_FINAL_SCREENSHOT_FILENAMES
        if filename not in {str(item) for item in final_files}
    ]
    if missing_files:
        failures.append("finalFiles missing: " + ", ".join(missing_files))
    for marker in ("not a testflight", "signed-device", "release build final evidence substitute"):
        if marker not in status:
            failures.append("status must keep simulator candidates separate from TestFlight/signed-device/Release evidence")
            break
    if "capture_ios_screenshots.py" not in command:
        failures.append("command must reference screenshot capture")
    return failures


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    report = Report()

    app_icon_set = root / args.app_icon_set
    app_icon_contents = read_json(app_icon_set / "Contents.json")
    app_icon_images = app_icon_contents.get("images", []) if isinstance(app_icon_contents.get("images", []), list) else []
    app_store_icon_entry = next(
        (
            entry
            for entry in app_icon_images
            if isinstance(entry, dict)
            and entry.get("filename")
            and entry.get("size") == "1024x1024"
            and entry.get("idiom") in {"universal", "ios-marketing"}
        ),
        None,
    )
    report.add(
        "appIconCatalogHas1024Entry",
        app_store_icon_entry is not None,
        "1024x1024 AppIcon entry found" if app_store_icon_entry else "missing 1024x1024 AppIcon entry",
    )

    icon_filename = app_store_icon_entry.get("filename", "") if isinstance(app_store_icon_entry, dict) else ""
    icon_path = app_icon_set / icon_filename if icon_filename else app_icon_set / "AppIcon-1024.png"
    icon_info = png_info(icon_path)
    icon_size = (icon_info.get("width"), icon_info.get("height"))
    report.add(
        "appIcon1024PngValid",
        icon_info.get("valid") is True and icon_size == (1024, 1024),
        f"{icon_path}: {icon_info}",
    )
    report.add(
        "appIconHasNoAlpha",
        icon_info.get("valid") is True and icon_info.get("colorType") not in PNG_COLOR_TYPES_WITH_ALPHA,
        f"PNG colorType={icon_info.get('colorType', '<invalid>')}",
    )

    final_screenshot_dir = root / args.final_screenshot_dir
    screenshots = screenshot_files(final_screenshot_dir)
    screenshot_names = [screenshot.name for screenshot in screenshots]
    report.add(
        "finalScreenshotsCount",
        len(screenshots) >= args.min_screenshots,
        f"{len(screenshots)} screenshots under {args.final_screenshot_dir}",
    )
    missing_expected_screenshots = [
        filename
        for filename in EXPECTED_FINAL_SCREENSHOT_FILENAMES
        if filename not in screenshot_names
    ]
    unexpected_screenshots = [
        filename
        for filename in screenshot_names
        if filename not in EXPECTED_FINAL_SCREENSHOT_FILENAMES
    ]
    report.add(
        "finalScreenshotsExpectedUploadOrder",
        not missing_expected_screenshots and not unexpected_screenshots,
        "expected upload filenames present in order"
        if not missing_expected_screenshots and not unexpected_screenshots
        else "missing: "
        + ", ".join(missing_expected_screenshots)
        + "; unexpected: "
        + ", ".join(unexpected_screenshots),
    )
    invalid_screenshots: list[str] = []
    screenshot_details: list[dict[str, Any]] = []
    for screenshot in screenshots:
        info = png_info(screenshot) if screenshot.suffix.lower() == ".png" else {"valid": False, "error": "only PNG screenshots are allowed for this gate"}
        size = (info.get("width"), info.get("height"))
        detail = {
            "path": str(screenshot.relative_to(root)),
            "width": info.get("width"),
            "height": info.get("height"),
            "colorType": info.get("colorType"),
        }
        screenshot_details.append(detail)
        if info.get("valid") is not True or size not in ACCEPTED_IPHONE_SCREENSHOT_SIZES:
            invalid_screenshots.append(f"{screenshot.name}: {info}")
    report.add(
        "finalScreenshotsAcceptedSizes",
        not invalid_screenshots and bool(screenshots),
        "all screenshot sizes accepted: " + json.dumps(screenshot_details, ensure_ascii=False)
        if not invalid_screenshots and screenshots
        else "; ".join(invalid_screenshots) or "no screenshots",
    )
    flat_screenshots: list[str] = []
    screenshot_content_details: list[dict[str, Any]] = []
    for screenshot in screenshots:
        metrics = png_visual_metrics(screenshot) if screenshot.suffix.lower() == ".png" else {"valid": False, "error": "not PNG"}
        detail = {"path": str(screenshot.relative_to(root)), **metrics}
        screenshot_content_details.append(detail)
        if (
            metrics.get("valid") is not True
            or int(metrics.get("uniqueSampledPixels", 0)) < 16
            or int(metrics.get("maxChannelRange", 0)) < 24
        ):
            flat_screenshots.append(f"{screenshot.name}: {metrics}")
    report.add(
        "finalScreenshotsNotBlank",
        not flat_screenshots and bool(screenshots),
        "all screenshots have non-blank pixel content: " + json.dumps(screenshot_content_details, ensure_ascii=False)
        if not flat_screenshots and screenshots
        else "; ".join(flat_screenshots) or "no screenshots",
    )
    report.add(
        "finalScreenshotsNoBabyPhotoNames",
        not any("baby" in screenshot.name.lower() or "宝宝" in screenshot.name for screenshot in screenshots),
        "screenshot filenames do not suggest real baby photos",
    )

    provenance_path = final_screenshot_dir / SCREENSHOT_PROVENANCE_FILE
    provenance = read_json(provenance_path)
    provenance_failures = screenshot_provenance_failures(provenance) if provenance else ["missing provenance file"]
    report.add(
        "finalScreenshotsIOS265ProvenancePresent",
        bool(provenance) and not provenance_failures,
        "iOS 26.5 screenshot provenance present and bounded to simulator candidates"
        if provenance and not provenance_failures
        else "; ".join(provenance_failures),
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--app-icon-set", default="App/iOS/XiaoNaiPing/Assets.xcassets/AppIcon.appiconset")
    parser.add_argument("--final-screenshot-dir", default="Docs/08_Release/AppStoreEvidence/10-final-screenshots")
    parser.add_argument("--min-screenshots", type=int, default=5)
    parser.add_argument("--output", default="Backend/proof/app-store-assets.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"App Store assets passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"App Store assets incomplete: {output_path}")
    print(f"failed required checks: {failed}")
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
