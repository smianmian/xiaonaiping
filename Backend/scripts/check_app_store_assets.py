#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
IPHONE_6_9_SCREENSHOT_SIZES = {
    (1260, 2736),
    (2736, 1260),
    (1290, 2796),
    (2796, 1290),
    (1320, 2868),
    (2868, 1320),
}

PNG_COLOR_TYPES_WITH_ALPHA = {4, 6}
PNG_CHANNELS_BY_COLOR_TYPE = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
EXPECTED_FINAL_SCREENSHOT_FILENAMES = [
    "01-home-iphone16pro.png",
    "02-record-iphone16pro.png",
    "03-growth-iphone16pro.png",
    "04-profile-iphone16pro.png",
    "05-profile-sync-iphone16pro.png",
]
EXPECTED_BUNDLE_ID = "com.mewpow.xiaonaiping"
EXPECTED_APP_NAME = "小奶瓶"
EXPECTED_SCREENSHOT_RUNTIME = "iOS 26.5"
EXPECTED_SCREENSHOT_SDK = "iphonesimulator26.5"
SCREENSHOT_PROVENANCE_FILE = "PROVENANCE.json"
SCREENSHOT_UPLOAD_PROVENANCE_FILE = "UPLOAD_PROVENANCE.json"
SCREENSHOT_UPLOAD_PROVENANCE_TEMPLATE_FILE = "UPLOAD_PROVENANCE.template.json"
EXPECTED_UPLOAD_SOURCE_EVIDENCE = {
    "signedArchive": "../05-signed-archive.png",
    "testFlight": "../06-testflight.png",
    "appStoreConnectBuild": "../AppStoreConnect/ASC-07-build-testflight-link.png",
    "appStoreConnectScreenshotOrder": "../AppStoreConnect/ASC-02-version-information.png",
    "realDeviceRegression": "../12-real-device-regression.md",
}
SCREENSHOT_FILENAME_FORBIDDEN_MARKERS = (
    "baby",
    "宝宝",
    "localhost",
    "127.0.0.1",
    "debug",
    "token",
    "bearer",
    "credential",
    "凭证",
    "wechat-success",
    "微信登录成功",
    "medical",
    "医疗",
    "pressure",
    "压力",
)
PROVENANCE_FORBIDDEN_MARKERS = (
    "127.0.0.1",
    "localhost",
    "Bearer ",
    "debug_wechat",
    "sk-",
)
FINAL_SCREENSHOT_UPLOAD_REDACTION_MARKERS = (
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
)
UPLOAD_PROVENANCE_TEMPLATE_STATUS = (
    "final App Store upload evidence captured from the same iOS 26.5 TestFlight build "
    "or Xcode signed device build used for release regression"
)
UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS = {
    "capturedAt": "YYYY-MM-DDTHH:MM:SS+08:00",
    "device.name": "FILL_WITH_PHYSICAL_DEVICE_NAME",
    "app.version": "FILL_WITH_APP_VERSION",
    "app.build": "FILL_WITH_BUILD_NUMBER",
    "fileSizeBytes": "FILL_WITH_FILE_SIZE_BYTES",
    "sha256": "FILL_WITH_SHA256",
}
UPLOAD_PROVENANCE_TEMPLATE_NOTE_MARKERS = (
    "Copy this file to UPLOAD_PROVENANCE.json only after the screenshots are captured or accepted from the same iOS 26.5 TestFlight build or Xcode signed device build.",
    "Do not use Debug simulator candidate screenshots as final App Store upload evidence.",
)
UPLOAD_PROVENANCE_FINAL_FORBIDDEN_TEMPLATE_MARKERS = (
    "YYYY-MM-DDTHH:MM:SS+08:00",
    "FILL_WITH_",
    "Copy this file to UPLOAD_PROVENANCE.json",
    "Do not use Debug simulator candidate screenshots as final App Store upload evidence.",
)


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


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested_value(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def is_iso_timestamp_with_timezone(value: str) -> bool:
    if not value or "YYYY" in value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def is_filled(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and "FILL_WITH_" not in text and "YYYY-MM-DD" not in text


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
    provenance_text = json.dumps(data, ensure_ascii=False)
    leaked_markers = [marker for marker in PROVENANCE_FORBIDDEN_MARKERS if marker in provenance_text]
    if leaked_markers:
        failures.append("provenance contains forbidden local/debug/secret markers: " + ", ".join(leaked_markers))
    return failures


def screenshot_candidate_readme_failures(readme: str, provenance: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    captured_at = str(provenance.get("capturedAt", ""))
    captured_date = captured_at[:10] if len(captured_at) >= 10 else ""
    if not readme:
        return ["missing final screenshot README.md"]
    if not captured_date:
        failures.append("PROVENANCE.json capturedAt must include YYYY-MM-DD")
    elif f"Date: {captured_date}" not in readme:
        failures.append(f"README.md Date must match PROVENANCE.json capturedAt date {captured_date}")
    for marker in ("PROVENANCE.json", "not TestFlight", "UPLOAD_PROVENANCE.json"):
        if marker not in readme:
            failures.append(f"README.md missing {marker}")
    return failures


def screenshot_upload_provenance_template_failures(data: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    device = data.get("device", {})
    app = data.get("app", {})
    source_evidence = data.get("sourceEvidence", {})
    final_files = data.get("finalFiles", [])
    file_checks = data.get("fileChecks", [])
    redaction_checks = data.get("redactionChecks", [])
    notes = data.get("notes", [])
    if not isinstance(device, dict):
        failures.append("device must be an object")
        device = {}
    if not isinstance(app, dict):
        failures.append("app must be an object")
        app = {}
    if not isinstance(source_evidence, dict):
        failures.append("sourceEvidence must be an object")
        source_evidence = {}
    if not isinstance(final_files, list):
        failures.append("finalFiles must be an array")
        final_files = []
    if not isinstance(file_checks, list):
        failures.append("fileChecks must be an array")
        file_checks = []
    if not isinstance(redaction_checks, list):
        failures.append("redactionChecks must be an array")
        redaction_checks = []
    if not isinstance(notes, list):
        failures.append("notes must be an array")
        notes = []

    expected_scalars = {
        "evidenceType": "final-app-store-upload",
        "status": UPLOAD_PROVENANCE_TEMPLATE_STATUS,
        "capturedAt": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["capturedAt"],
        "installSource": "TestFlight",
        "appStoreDeviceSlot": 'iPhone 6.9" display',
    }
    for key, expected in expected_scalars.items():
        if data.get(key) != expected:
            failures.append(f"{key} must be {expected}")
    if device.get("name") != UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["device.name"]:
        failures.append(
            "device.name must be "
            + UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["device.name"]
        )
    if device.get("runtime") != EXPECTED_SCREENSHOT_RUNTIME:
        failures.append(f"device.runtime must be {EXPECTED_SCREENSHOT_RUNTIME}")
    if app.get("bundleId") != EXPECTED_BUNDLE_ID:
        failures.append(f"app.bundleId must be {EXPECTED_BUNDLE_ID}")
    if app.get("version") != UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["app.version"]:
        failures.append("app.version must be " + UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["app.version"])
    if app.get("build") != UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["app.build"]:
        failures.append("app.build must be " + UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["app.build"])
    for key, expected in EXPECTED_UPLOAD_SOURCE_EVIDENCE.items():
        if source_evidence.get(key) != expected:
            failures.append(f"sourceEvidence.{key} must be {expected}")
    if final_files != EXPECTED_FINAL_SCREENSHOT_FILENAMES:
        failures.append("finalFiles must match expected upload order exactly")
    if len(file_checks) != len(EXPECTED_FINAL_SCREENSHOT_FILENAMES):
        failures.append("fileChecks must include one entry for each final file")
    for index, expected_filename in enumerate(EXPECTED_FINAL_SCREENSHOT_FILENAMES):
        check = file_checks[index] if index < len(file_checks) and isinstance(file_checks[index], dict) else {}
        if not check:
            failures.append(f"fileChecks.{expected_filename} missing object")
            continue
        expected_scalars_for_file: dict[str, Any] = {
            "filename": expected_filename,
            "width": 1320,
            "height": 2868,
            "fileSizeBytes": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["fileSizeBytes"],
            "sha256": UPLOAD_PROVENANCE_TEMPLATE_PLACEHOLDERS["sha256"],
            "redactionChecked": False,
            "matchesFinalUploadOrder": False,
            "secretValuesNotRecorded": False,
        }
        for key, expected in expected_scalars_for_file.items():
            if check.get(key) != expected:
                failures.append(f"fileChecks.{expected_filename}.{key} must be {expected}")
    if tuple(str(item) for item in redaction_checks) != FINAL_SCREENSHOT_UPLOAD_REDACTION_MARKERS:
        failures.append(
            "redactionChecks order must be "
            + " -> ".join(FINAL_SCREENSHOT_UPLOAD_REDACTION_MARKERS)
        )
    notes_text = json.dumps(notes, ensure_ascii=False)
    for marker in UPLOAD_PROVENANCE_TEMPLATE_NOTE_MARKERS:
        if marker not in notes_text:
            failures.append(f"notes missing {marker}")
    template_text = json.dumps(data, ensure_ascii=False)
    leaked_markers = [marker for marker in PROVENANCE_FORBIDDEN_MARKERS if marker in template_text]
    if leaked_markers:
        failures.append("upload provenance template contains forbidden local/debug/secret markers: " + ", ".join(leaked_markers))
    return failures


def screenshot_upload_provenance_failures(data: dict[str, Any], final_screenshot_dir: Path) -> list[str]:
    failures: list[str] = []
    device = data.get("device", {})
    app = data.get("app", {})
    final_files = data.get("finalFiles", [])
    file_checks = data.get("fileChecks", [])
    source_evidence = data.get("sourceEvidence", {})
    redaction_checks = data.get("redactionChecks", [])
    status = str(data.get("status", "")).lower()
    evidence_type = str(data.get("evidenceType", ""))
    install_source = str(data.get("installSource", ""))
    device_slot = str(data.get("appStoreDeviceSlot", ""))
    captured_at = str(data.get("capturedAt", ""))
    if not isinstance(device, dict):
        failures.append("device must be an object")
        device = {}
    if not isinstance(app, dict):
        failures.append("app must be an object")
        app = {}
    if not isinstance(final_files, list):
        failures.append("finalFiles must be an array")
        final_files = []
    if not isinstance(file_checks, list):
        failures.append("fileChecks must be an array")
        file_checks = []
    if not isinstance(source_evidence, dict):
        failures.append("sourceEvidence must bind signed archive, TestFlight, App Store Connect build, and real-device regression evidence")
        source_evidence = {}
    if not isinstance(redaction_checks, list):
        failures.append("redactionChecks must be an array")
        redaction_checks = []
    if evidence_type != "final-app-store-upload":
        failures.append("evidenceType must be final-app-store-upload")
    if not is_iso_timestamp_with_timezone(captured_at):
        failures.append("capturedAt must be an ISO timestamp with timezone, not a template placeholder")
    if install_source not in {"TestFlight", "Xcode 签名真机包"}:
        failures.append("installSource must be TestFlight or Xcode 签名真机包")
    if device_slot != 'iPhone 6.9" display':
        failures.append('appStoreDeviceSlot must be iPhone 6.9" display')
    if not is_filled(device.get("name")):
        failures.append("device.name must be filled with the physical device name")
    if device.get("runtime") != EXPECTED_SCREENSHOT_RUNTIME:
        failures.append(f"device.runtime must be {EXPECTED_SCREENSHOT_RUNTIME}")
    if app.get("bundleId") != EXPECTED_BUNDLE_ID:
        failures.append(f"app.bundleId must be {EXPECTED_BUNDLE_ID}")
    if not is_filled(app.get("version")):
        failures.append("app.version must be filled with the App Store version")
    if not is_filled(app.get("build")):
        failures.append("app.build must be filled with the selected build number")
    if "final app store upload" not in status:
        failures.append("status must say final App Store upload")
    if any(marker in status for marker in ("candidate", "debug simulator", "not a testflight")):
        failures.append("status must not describe candidate or Debug simulator evidence")
    missing_files = [
        filename for filename in EXPECTED_FINAL_SCREENSHOT_FILENAMES
        if filename not in {str(item) for item in final_files}
    ]
    if missing_files:
        failures.append("finalFiles missing: " + ", ".join(missing_files))
    if final_files != EXPECTED_FINAL_SCREENSHOT_FILENAMES:
        failures.append("finalFiles must match expected upload order exactly")
    if len(file_checks) != len(EXPECTED_FINAL_SCREENSHOT_FILENAMES):
        failures.append("fileChecks must include one entry for each final file")
    for index, expected_filename in enumerate(EXPECTED_FINAL_SCREENSHOT_FILENAMES):
        check = file_checks[index] if index < len(file_checks) and isinstance(file_checks[index], dict) else {}
        if not check:
            failures.append(f"fileChecks.{expected_filename} missing object")
            continue
        screenshot_path = final_screenshot_dir / expected_filename
        if not screenshot_path.exists():
            failures.append(f"fileChecks.{expected_filename} cannot validate missing screenshot file")
            continue
        info = png_info(screenshot_path)
        expected_size = screenshot_path.stat().st_size
        expected_sha = sha256_file(screenshot_path)
        expected_scalars_for_file: dict[str, Any] = {
            "filename": expected_filename,
            "width": 1320,
            "height": 2868,
            "fileSizeBytes": expected_size,
            "sha256": expected_sha,
            "redactionChecked": True,
            "matchesFinalUploadOrder": True,
            "secretValuesNotRecorded": True,
        }
        for key, expected in expected_scalars_for_file.items():
            if check.get(key) != expected:
                failures.append(f"fileChecks.{expected_filename}.{key} must be {expected}")
        if expected_size < 10240:
            failures.append(f"fileChecks.{expected_filename}.fileSizeBytes must be at least 10240")
        if info.get("valid") is not True or (info.get("width"), info.get("height")) != (1320, 2868):
            failures.append(f"fileChecks.{expected_filename} must describe a valid 1320x2868 PNG")
    for key, expected in EXPECTED_UPLOAD_SOURCE_EVIDENCE.items():
        if source_evidence.get(key) != expected:
            failures.append(f"sourceEvidence.{key} must be {expected}")
        else:
            source_path = (final_screenshot_dir / expected).resolve()
            allowed_root = final_screenshot_dir.parents[0].resolve()
            if not str(source_path).startswith(str(allowed_root) + "/"):
                failures.append(f"sourceEvidence.{key} must stay under AppStoreEvidence: {expected}")
                continue
            if not source_path.is_file():
                failures.append(f"sourceEvidence.{key} file missing: {source_path.relative_to(allowed_root)}")
                continue
            min_size = 100 if source_path.suffix.lower() == ".md" else 10240
            actual_size = source_path.stat().st_size
            if actual_size < min_size:
                failures.append(
                    f"sourceEvidence.{key} file is too small: "
                    f"{source_path.relative_to(allowed_root)}, size={actual_size}, minimum={min_size}"
                )
    redaction_text = json.dumps(redaction_checks, ensure_ascii=False)
    for marker in FINAL_SCREENSHOT_UPLOAD_REDACTION_MARKERS:
        if marker not in redaction_text:
            failures.append(f"redactionChecks missing {marker}")
    provenance_text = json.dumps(data, ensure_ascii=False)
    template_markers = [
        marker
        for marker in UPLOAD_PROVENANCE_FINAL_FORBIDDEN_TEMPLATE_MARKERS
        if marker in provenance_text
    ]
    if template_markers:
        failures.append("UPLOAD_PROVENANCE.json still contains template markers: " + ", ".join(template_markers))
    leaked_markers = [marker for marker in PROVENANCE_FORBIDDEN_MARKERS if marker in provenance_text]
    if leaked_markers:
        failures.append("upload provenance contains forbidden local/debug/secret markers: " + ", ".join(leaked_markers))
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
    non_6_9_screenshots: list[str] = []
    for detail in screenshot_details:
        size = (detail.get("width"), detail.get("height"))
        if size not in IPHONE_6_9_SCREENSHOT_SIZES:
            non_6_9_screenshots.append(f"{Path(str(detail.get('path'))).name}: {size}")
    report.add(
        "finalScreenshotsIphone69SlotReady",
        bool(screenshots) and not non_6_9_screenshots,
        "all screenshots match iPhone 6.9-inch upload sizes"
        if screenshots and not non_6_9_screenshots
        else "not 6.9-inch upload size: " + ", ".join(non_6_9_screenshots),
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
    risky_screenshot_names = [
        screenshot.name
        for screenshot in screenshots
        if any(marker.lower() in screenshot.name.lower() for marker in SCREENSHOT_FILENAME_FORBIDDEN_MARKERS)
    ]
    report.add(
        "finalScreenshotsNoRiskyFilenames",
        not risky_screenshot_names,
        "screenshot filenames do not include real-baby, local, debug, token, WeChat-success, medical, or pressure markers"
        if not risky_screenshot_names
        else "risky screenshot filenames: " + ", ".join(risky_screenshot_names),
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
    readme_path = final_screenshot_dir / "README.md"
    readme = read_text(readme_path)
    readme_failures = screenshot_candidate_readme_failures(readme, provenance) if provenance else ["missing provenance file"]
    report.add(
        "finalScreenshotsCandidateReadmeMatchesProvenance",
        bool(readme) and bool(provenance) and not readme_failures,
        "final screenshot candidate README date and boundary match PROVENANCE.json"
        if readme and provenance and not readme_failures
        else "; ".join(readme_failures),
    )
    upload_provenance_template_path = final_screenshot_dir / args.final_screenshot_upload_template
    upload_provenance_template = read_json(upload_provenance_template_path)
    upload_provenance_template_failures = (
        screenshot_upload_provenance_template_failures(upload_provenance_template)
        if upload_provenance_template
        else ["missing upload provenance template file"]
    )
    report.add(
        "finalScreenshotsUploadProvenanceTemplateValid",
        bool(upload_provenance_template) and not upload_provenance_template_failures,
        "final screenshot upload provenance template locks placeholders, same-build source evidence, iOS 26.5, iPhone 6.9 slot, upload order, and redaction checklist"
        if upload_provenance_template and not upload_provenance_template_failures
        else "; ".join(upload_provenance_template_failures),
    )
    upload_provenance_path = final_screenshot_dir / SCREENSHOT_UPLOAD_PROVENANCE_FILE
    upload_provenance = read_json(upload_provenance_path)
    upload_provenance_failures = (
        screenshot_upload_provenance_failures(upload_provenance, final_screenshot_dir)
        if upload_provenance
        else ["missing upload provenance file"]
    )
    report.add(
        "finalScreenshotsUploadProvenancePresent",
        bool(upload_provenance) and not upload_provenance_failures,
        "final App Store screenshot upload provenance is tied to iOS 26.5 TestFlight or signed-device evidence"
        if upload_provenance and not upload_provenance_failures
        else "; ".join(upload_provenance_failures),
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--app-icon-set", default="App/iOS/XiaoNaiPing/Assets.xcassets/AppIcon.appiconset")
    parser.add_argument("--final-screenshot-dir", default="Docs/08_Release/AppStoreEvidence/10-final-screenshots")
    parser.add_argument("--final-screenshot-upload-template", default=SCREENSHOT_UPLOAD_PROVENANCE_TEMPLATE_FILE)
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
