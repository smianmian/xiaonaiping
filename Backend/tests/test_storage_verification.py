from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_storage_backend.py"


class StorageVerificationTest(unittest.TestCase):
    def test_disk_storage_flow_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            output = root / "storage.json"
            env = os.environ.copy()
            env["XNP_STORAGE_BACKEND"] = "disk"
            env["XNP_DATA_DIR"] = str(root / "data")

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--output",
                    str(output),
                ],
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )
            report = json.loads(output.read_text(encoding="utf-8"))

            self.assertTrue(report["passed"])
            self.assertTrue(report["checks"]["accountDeleteRemovedPhotos"])


if __name__ == "__main__":
    unittest.main()
