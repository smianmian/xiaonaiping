#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check_app_store_assets import (
    EXPECTED_FINAL_SCREENSHOT_FILENAMES,
    IPHONE_6_9_SCREENSHOT_SIZES,
    SCREENSHOT_UPLOAD_PROVENANCE_FILE,
    png_info,
    screenshot_upload_provenance_failures,
    sha256_file,
)


DEFAULT_SCREENSHOT_DIR = "Docs/08_Release/AppStoreEvidence/10-final-screenshots"
DEFAULT_OUTPUT = "Backend/proof/final-screenshot-upload-file-metrics-20260630-current.json"
EXPECTED_UPLOAD_SIZE = (1320, 2868)


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


def screenshot_metric(screenshot_dir: Path, filename: str, index: int) -> dict[str, Any]:
    path = screenshot_dir / filename
    metric: dict[str, Any] = {
        "index": index,
        "filename": filename,
        "exists": path.exists(),
        "passed": False,
        "issues": [],
    }
    if not path.exists():
        metric["issues"].append("missing screenshot file")
        return metric

    info = png_info(path)
    size = path.stat().st_size
    sha256 = sha256_file(path)
    width = info.get("width")
    height = info.get("height")
    metric.update(
        {
            "path": str(path),
            "fileSizeBytes": size,
            "sha256": sha256,
            "png": info,
            "width": width,
            "height": height,
            "matchesExpectedUploadSize": (width, height) == EXPECTED_UPLOAD_SIZE,
            "matchesIphone69Slot": (width, height) in IPHONE_6_9_SCREENSHOT_SIZES,
            "fileCheckDraft": {
                "filename": filename,
                "width": width,
                "height": height,
                "fileSizeBytes": size,
                "sha256": sha256,
                "redactionChecked": False,
                "matchesFinalUploadOrder": False,
                "secretValuesNotRecorded": False,
            },
        }
    )

    if info.get("valid") is not True:
        metric["issues"].append("not a valid PNG")
    if size < 10240:
        metric["issues"].append("file is too small for final screenshot evidence")
    if (width, height) != EXPECTED_UPLOAD_SIZE:
        metric["issues"].append("screenshot must be 1320x2868 for the current upload provenance template")
    if (width, height) not in IPHONE_6_9_SCREENSHOT_SIZES:
        metric["issues"].append('screenshot does not match an iPhone 6.9" App Store upload size')

    metric["passed"] = not metric["issues"]
    return metric


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    screenshot_dir = Path(args.screenshot_dir)
    if not screenshot_dir.is_absolute():
        screenshot_dir = root / screenshot_dir

    started_at = utc_now()
    screenshots = [
        screenshot_metric(screenshot_dir, filename, index + 1)
        for index, filename in enumerate(EXPECTED_FINAL_SCREENSHOT_FILENAMES)
    ]
    screenshot_issues = [
        f"{item['filename']}: {issue}"
        for item in screenshots
        for issue in item.get("issues", [])
    ]

    upload_provenance_path = screenshot_dir / SCREENSHOT_UPLOAD_PROVENANCE_FILE
    upload_provenance = read_json(upload_provenance_path)
    upload_provenance_failures = (
        screenshot_upload_provenance_failures(upload_provenance, screenshot_dir)
        if upload_provenance
        else ["missing UPLOAD_PROVENANCE.json"]
    )

    ready = not screenshot_issues and bool(upload_provenance) and not upload_provenance_failures
    return {
        "artifactType": "final-screenshot-upload-file-metrics",
        "generatedAt": started_at,
        "finishedAt": utc_now(),
        "project": "XiaoNaiPing",
        "appName": "小奶瓶",
        "bundleId": "com.mewpow.xiaonaiping",
        "canSubmitFromThisReport": False,
        "ready": ready,
        "metricsReady": not screenshot_issues,
        "expectedScreenshotOrder": EXPECTED_FINAL_SCREENSHOT_FILENAMES,
        "expectedUploadSize": {"width": EXPECTED_UPLOAD_SIZE[0], "height": EXPECTED_UPLOAD_SIZE[1]},
        "screenshotDir": str(screenshot_dir),
        "screenshots": screenshots,
        "uploadProvenance": {
            "path": str(upload_provenance_path),
            "exists": bool(upload_provenance),
            "valid": bool(upload_provenance) and not upload_provenance_failures,
            "issues": upload_provenance_failures,
        },
        "fileChecksDraft": [item.get("fileCheckDraft") for item in screenshots if item.get("fileCheckDraft")],
        "doesNotProve": [
            "screenshots were uploaded to App Store Connect",
            "screenshots came from the selected TestFlight or signed physical-device build",
            "manual redaction review passed",
            "Submit for Review is allowed",
        ],
        "nextAction": (
            "After the same iOS 26.5 TestFlight or Xcode signed physical-device build is used for final screenshots, "
            "copy the fileChecksDraft values into UPLOAD_PROVENANCE.json and set redaction/order/secret booleans true only after manual verification."
        ),
        "failedChecks": screenshot_issues + upload_provenance_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--screenshot-dir", default=DEFAULT_SCREENSHOT_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    report = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if report["ready"]:
        print(f"Final screenshot upload file metrics ready: {output_path}")
        return

    print(f"Final screenshot upload file metrics incomplete: {output_path}")
    print("failed checks: " + ", ".join(report["failedChecks"]))
    if args.require_complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
