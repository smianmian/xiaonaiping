from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_deploy_bundle.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


class DeployBundleTest(unittest.TestCase):
    def test_bundle_contains_backend_files_and_excludes_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write(root / "Backend/api/server.py", "print('server')\n")
            write(root / "Backend/static/privacy.html", "<h1>privacy</h1>\n")
            write(root / "Backend/deploy/.env", "SECRET=do-not-ship\n")
            write(root / "Backend/deploy/.env.example", "SECRET=placeholder\n")
            write(root / "Backend/requirements-obs.txt", "esdk-obs-python\n")
            write(root / "Backend/requirements-production.txt", "PyMySQL\nesdk-obs-python\n")
            write(root / "Backend/README.md", "# Backend\n")

            output_dir = root / "out"
            subprocess.run(
                [sys.executable, str(SCRIPT), "--repo-root", str(root), "--output-dir", str(output_dir)],
                text=True,
                capture_output=True,
                check=True,
            )

            bundles = list(output_dir.glob("*.tar.gz"))
            manifests = list(output_dir.glob("*.manifest.json"))
            self.assertEqual(len(bundles), 1)
            self.assertEqual(len(manifests), 1)

            manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
            self.assertFalse(manifest["containsSecrets"])
            manifest_paths = {item["path"] for item in manifest["files"]}
            self.assertIn("Backend/api/server.py", manifest_paths)
            self.assertIn("Backend/deploy/.env.example", manifest_paths)
            self.assertIn("Backend/requirements-production.txt", manifest_paths)
            self.assertNotIn("Backend/deploy/.env", manifest_paths)

            with tarfile.open(bundles[0], "r:gz") as archive:
                archive_paths = set(archive.getnames())
            self.assertIn("Backend/static/privacy.html", archive_paths)
            self.assertNotIn("Backend/deploy/.env", archive_paths)


if __name__ == "__main__":
    unittest.main()
