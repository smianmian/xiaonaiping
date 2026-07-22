#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def collect_devicectl_json(timeout_seconds: float) -> tuple[dict[str, Any], str]:
    with tempfile.NamedTemporaryFile(prefix="xnp-devices-", suffix=".json", delete=True) as file:
        try:
            completed = subprocess.run(
                ["xcrun", "devicectl", "list", "devices", "--json-output", file.name],
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return {}, f"devicectl timed out after {timeout_seconds:g}s"
        if completed.returncode != 0:
            return {}, (completed.stderr or completed.stdout or "devicectl failed").strip()
        data = read_json(Path(file.name))
        return data, completed.stdout.strip()


def device_name(device: dict[str, Any]) -> str:
    props = device.get("deviceProperties", {})
    if isinstance(props, dict):
        name = props.get("name")
        if isinstance(name, str) and name:
            return name
    display = device.get("displayName")
    return str(display) if display else "<unknown>"


def os_version(device: dict[str, Any]) -> str:
    props = device.get("deviceProperties", {})
    if not isinstance(props, dict):
        return ""
    for key in ("osVersionNumber", "osVersion", "productVersion"):
        value = props.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def marketing_name(device: dict[str, Any]) -> str:
    hardware = device.get("hardwareProperties", {})
    if not isinstance(hardware, dict):
        return ""
    for key in ("marketingName", "productType", "deviceType"):
        value = hardware.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def platform(device: dict[str, Any]) -> str:
    hardware = device.get("hardwareProperties", {})
    if not isinstance(hardware, dict):
        return ""
    value = hardware.get("platform")
    return str(value) if value else ""


def device_type(device: dict[str, Any]) -> str:
    hardware = device.get("hardwareProperties", {})
    if not isinstance(hardware, dict):
        return ""
    value = hardware.get("deviceType")
    return str(value) if value else ""


def is_physical_iphone(device: dict[str, Any]) -> bool:
    return platform(device) == "iOS" and device_type(device) == "iPhone"


def is_available(device: dict[str, Any]) -> bool:
    capabilities = device.get("capabilities", [])
    if not isinstance(capabilities, list):
        capabilities = []
    feature_ids = {
        str(item.get("featureIdentifier", ""))
        for item in capabilities
        if isinstance(item, dict)
    }
    props = device.get("deviceProperties", {})
    conn = device.get("connectionProperties", {})
    if not isinstance(props, dict):
        props = {}
    if not isinstance(conn, dict):
        conn = {}
    return (
        "com.apple.coredevice.feature.connectdevice" in feature_ids
        or "com.apple.coredevice.feature.acquireusageassertion" in feature_ids
        or bool(props.get("screenViewingURL"))
        or bool(conn.get("transportType"))
    )


def summarize_device(device: dict[str, Any], required_ios: str) -> dict[str, Any]:
    version = os_version(device)
    available = is_available(device)
    return {
        "name": device_name(device),
        "identifier": str(device.get("identifier", "")),
        "model": marketing_name(device),
        "platform": platform(device),
        "deviceType": device_type(device),
        "osVersion": version,
        "available": available,
        "eligibleForLocalTesting": is_physical_iphone(device) and version == required_ios and available,
        "ignoredBecause": ""
        if is_physical_iphone(device) and version == required_ios and available
        else "not iPhone"
        if device_type(device) != "iPhone"
        else f"not iOS {required_ios}"
        if version != required_ios
        else "iOS 26.5 device unavailable",
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    if args.devices_json:
        source = args.devices_json
        data = read_json(Path(args.devices_json))
        collection_error = "" if data else f"missing or invalid {args.devices_json}"
    else:
        source = "xcrun devicectl list devices"
        data, collection_error = collect_devicectl_json(args.devicectl_timeout_seconds)

    raw_devices = data.get("result", {}).get("devices", []) if isinstance(data.get("result"), dict) else []
    devices = [device for device in raw_devices if isinstance(device, dict)]
    iphones = [summarize_device(device, args.required_ios) for device in devices if is_physical_iphone(device)]
    eligible = [device for device in iphones if device["eligibleForLocalTesting"]]
    unavailable_required = [
        device for device in iphones if device["osVersion"] == args.required_ios and not device["available"]
    ]
    available_wrong_version = [
        device for device in iphones if device["available"] and device["osVersion"] != args.required_ios
    ]

    checks = {
        "deviceListReadable": {
            "passed": bool(devices),
            "required": True,
            "evidence": source if devices else collection_error,
        },
        "physicalIphonesListed": {
            "passed": bool(iphones),
            "required": True,
            "evidence": f"{len(iphones)} physical iPhone device(s) listed",
        },
        "ios265PolicyEnforced": {
            "passed": True,
            "required": True,
            "evidence": f"local project testing requires iOS {args.required_ios}; non-{args.required_ios} available devices are not eligible",
        },
        "eligibleIOS265PhysicalIphoneAvailable": {
            "passed": bool(eligible),
            "required": True,
            "evidence": "eligible iOS 26.5 iPhone available"
            if eligible
            else "no available physical iPhone on iOS 26.5",
        },
    }
    failed_required = [
        name
        for name, check in checks.items()
        if check["required"] and check["passed"] is not True
    ]

    return {
        "startedAt": started_at,
        "completedAt": utc_now(),
        "passed": not failed_required,
        "requiredIOS": args.required_ios,
        "failedRequiredChecks": failed_required,
        "eligibleIOS265PhysicalIphones": eligible,
        "unavailableIOS265PhysicalIphones": unavailable_required,
        "availableNonIOS265PhysicalIphones": available_wrong_version,
        "devices": iphones,
        "checks": checks,
        "meaning": {
            "passed": "Device availability was inspected and local iOS 26.5 policy is enforced.",
            "notRealDeviceRegression": "This proof does not replace TestFlight or signed physical-device regression.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--devices-json", default="")
    parser.add_argument("--devicectl-timeout-seconds", type=float, default=60.0)
    parser.add_argument("--required-ios", default="26.5")
    parser.add_argument("--output", default="Backend/proof/ios265-device-availability.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root() / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"iOS 26.5 device availability proof passed: {output_path}")
        return
    failed = ", ".join(result["failedRequiredChecks"])
    if args.allow_incomplete:
        print(f"iOS 26.5 device availability proof incomplete: {output_path}")
        print(f"failed required checks: {failed}")
        return
    raise SystemExit(f"iOS 26.5 device availability proof failed: {failed}")


if __name__ == "__main__":
    main()
