#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path


INCLUDE_PATHS = [
    "Backend/api",
    "Backend/static",
    "Backend/deploy",
    "Backend/scripts",
    "Backend/sms",
    "Backend/requirements-obs.txt",
    "Backend/requirements-production.txt",
    "Backend/README.md",
]

EXCLUDE_NAMES = {
    "__pycache__",
    ".DS_Store",
    ".env",
    "node_modules",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def should_include(path: Path) -> bool:
    if any(part in EXCLUDE_NAMES for part in path.parts):
        return False
    if path.suffix == ".pyc":
        return False
    return path.is_file()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for relative in INCLUDE_PATHS:
        path = root / relative
        if path.is_dir():
            files.extend(file for file in path.rglob("*") if should_include(file))
        elif should_include(path):
            files.append(path)
    return sorted(set(files))


def build_bundle(root: Path, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_path = output_dir / f"xiaonaiping-backend-{timestamp}.tar.gz"
    manifest_path = output_dir / f"xiaonaiping-backend-{timestamp}.manifest.json"
    files = collect_files(root)

    manifest = {
        "createdAt": utc_now(),
        "bundle": bundle_path.name,
        "containsSecrets": False,
        "files": [
            {
                "path": str(path.relative_to(root)),
                "sizeBytes": path.stat().st_size,
                "sha256": file_digest(path),
            }
            for path in files
        ],
    }

    with tarfile.open(bundle_path, "w:gz") as archive:
        for path in files:
            archive.add(path, arcname=str(path.relative_to(root)))

    manifest["bundleSha256"] = file_digest(bundle_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return bundle_path, manifest_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output-dir", default="Backend/proof/deploy-bundles")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    bundle_path, manifest_path = build_bundle(root, output_dir)
    print(f"deploy bundle written: {bundle_path}")
    print(f"deploy manifest written: {manifest_path}")


if __name__ == "__main__":
    main()
