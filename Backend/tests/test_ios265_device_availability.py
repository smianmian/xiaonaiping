from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from importlib import util
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_ios265_device_availability.py"
SPEC = util.spec_from_file_location("check_ios265_device_availability", SCRIPT)
MODULE = util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def device(name: str, os_version: str, model: str, available: bool) -> dict:
    capabilities = [
        {"featureIdentifier": "com.apple.coredevice.feature.tags", "name": "Modify Tags"},
    ]
    connection = {"pairingState": "paired", "tunnelState": "unavailable"}
    props = {"name": name, "osVersionNumber": os_version}
    if available:
        capabilities.append(
            {
                "featureIdentifier": "com.apple.coredevice.feature.connectdevice",
                "name": "Connect to Device",
            }
        )
        connection["transportType"] = "localNetwork"
        props["screenViewingURL"] = f"devices://device/open?id={name}"
    return {
        "identifier": name,
        "capabilities": capabilities,
        "connectionProperties": connection,
        "deviceProperties": props,
        "hardwareProperties": {
            "deviceType": "iPhone",
            "marketingName": model,
            "platform": "iOS",
            "reality": "physical",
        },
    }


def write_devices(path: Path, devices: list[dict]) -> None:
    path.write_text(json.dumps({"result": {"devices": devices}}, ensure_ascii=False), encoding="utf-8")


class IOS265DeviceAvailabilityTest(unittest.TestCase):
    def run_checker(self, devices: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            devices_json = root / "devices.json"
            output = root / "ios265-device-availability.json"
            write_devices(devices_json, devices)
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--devices-json",
                    str(devices_json),
                    "--output",
                    str(output),
                    "--allow-incomplete",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            return json.loads(output.read_text(encoding="utf-8"))

    def test_available_ios27_does_not_count_as_eligible_or_pass(self) -> None:
        report = self.run_checker(
            [
                device("lanlan", "26.5", "iPhone 16 Pro Max", available=False),
                device("mianmian", "27.0", "iPhone 16 Plus", available=True),
            ]
        )

        self.assertFalse(report["passed"])
        self.assertEqual(report["failedRequiredChecks"], ["eligibleIOS265PhysicalIphoneAvailable"])
        self.assertEqual(report["eligibleIOS265PhysicalIphones"], [])
        self.assertEqual(report["unavailableIOS265PhysicalIphones"][0]["name"], "lanlan")
        self.assertEqual(report["availableNonIOS265PhysicalIphones"][0]["name"], "mianmian")

    def test_available_ios265_is_eligible(self) -> None:
        report = self.run_checker(
            [
                device("lanlan", "26.5", "iPhone 16 Pro Max", available=True),
            ]
        )

        self.assertTrue(report["passed"])
        self.assertEqual(report["eligibleIOS265PhysicalIphones"][0]["name"], "lanlan")
        self.assertTrue(report["checks"]["eligibleIOS265PhysicalIphoneAvailable"]["passed"])

    def test_devicectl_timeout_returns_error_instead_of_hanging(self) -> None:
        with mock.patch.object(
            MODULE.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(cmd=["xcrun", "devicectl"], timeout=0.01),
        ):
            data, error = MODULE.collect_devicectl_json(timeout_seconds=0.01)

        self.assertEqual(data, {})
        self.assertIn("devicectl timed out after", error)


if __name__ == "__main__":
    unittest.main()
