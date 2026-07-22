#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path


DEFAULT_TABS = ["home", "record", "growth", "profile", "profile-sync"]


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=check)


def png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def boot_device(device: str) -> None:
    run(["xcrun", "simctl", "boot", device], check=False)
    run(["xcrun", "simctl", "bootstatus", device, "-b"])


def capture_tab(device: str, bundle_id: str, tab: str, output_path: Path, settle_seconds: float) -> None:
    selected_tab = "profile" if tab == "profile-sync" else tab
    launch_args = [
        "xcrun",
        "simctl",
        "launch",
        device,
        bundle_id,
        "-XNPScreenshotData",
        "-XNPScreenshotTab",
        selected_tab,
    ]
    if tab == "profile-sync":
        launch_args.append("-XNPScreenshotSyncSheet")
    run(["xcrun", "simctl", "terminate", device, bundle_id], check=False)
    run(launch_args)
    time.sleep(settle_seconds)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run(["xcrun", "simctl", "io", device, "screenshot", str(output_path)])
    width, height = png_size(output_path)
    print(f"captured {tab}: {output_path} ({width}x{height})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="4C0B71E2-AE32-427E-A26E-6CDCDA1743B6")
    parser.add_argument("--app", default="/tmp/xnp-dd-debug/Build/Products/Debug-iphonesimulator/XiaoNaiPing.app")
    parser.add_argument("--bundle-id", default="com.mewpow.xiaonaiping")
    parser.add_argument("--output-dir", default="Docs/08_Release/Screenshots")
    parser.add_argument("--tabs", nargs="*", default=DEFAULT_TABS)
    parser.add_argument("--settle-seconds", type=float, default=2.0)
    parser.add_argument("--shutdown", action="store_true")
    args = parser.parse_args()

    app_path = Path(args.app)
    if not app_path.exists():
        raise SystemExit(f"app not found: {app_path}")

    output_dir = Path(args.output_dir)
    boot_device(args.device)
    run(["xcrun", "simctl", "install", args.device, str(app_path)])

    for tab in args.tabs:
        capture_tab(args.device, args.bundle_id, tab, output_dir / f"{tab}-iphone16pro.png", args.settle_seconds)

    if args.shutdown:
        run(["xcrun", "simctl", "shutdown", args.device], check=False)


if __name__ == "__main__":
    main()
