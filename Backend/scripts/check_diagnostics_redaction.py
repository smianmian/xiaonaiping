#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


THIRD_PARTY_CRASH_MARKERS = (
    "Crashlytics",
    "FirebaseCrashlytics",
    "FirebaseCore",
    "Sentry",
    "Bugsnag",
    "Instabug",
    "Datadog",
    "NewRelic",
    "AppCenterCrashes",
)

CLIENT_LOGGING_RE = re.compile(r"\b(print|debugPrint|NSLog|os_log)\s*\(|\bLogger\s*\(")
DIAGNOSTIC_PRIVACY_TYPES = {
    "NSPrivacyCollectedDataTypeCrashData",
    "NSPrivacyCollectedDataTypePerformanceData",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def scan_files(root: Path, relative: str, suffixes: set[str]) -> list[Path]:
    base = root / relative
    if not base.exists():
        return []
    return [path for path in base.rglob("*") if path.is_file() and path.suffix in suffixes]


def third_party_crash_hits(root: Path) -> list[str]:
    files = scan_files(root, "App/iOS", {".swift", ".m", ".mm", ".h", ".yml", ".pbxproj"})
    hits: list[str] = []
    for path in files:
        text = read_text(path)
        for marker in THIRD_PARTY_CRASH_MARKERS:
            if marker in text:
                hits.append(f"{path.relative_to(root)} contains {marker}")
    return hits


def client_logging_hits(root: Path) -> list[str]:
    files = scan_files(root, "App/iOS/XiaoNaiPing", {".swift"})
    hits: list[str] = []
    for path in files:
        for index, line in enumerate(read_text(path).splitlines(), start=1):
            if CLIENT_LOGGING_RE.search(line):
                hits.append(f"{path.relative_to(root)}:{index}")
    return hits


def privacy_manifest_diagnostics(root: Path) -> tuple[bool, str]:
    path = root / "App/iOS/XiaoNaiPing/PrivacyInfo.xcprivacy"
    try:
        with path.open("rb") as handle:
            data = plistlib.load(handle)
    except FileNotFoundError:
        return False, f"missing {path.relative_to(root)}"
    except (plistlib.InvalidFileException, ValueError) as error:
        return False, f"invalid privacy manifest: {error}"

    encoded = json.dumps(data, ensure_ascii=False)
    missing = sorted(value for value in DIAGNOSTIC_PRIVACY_TYPES if value not in encoded)
    if missing:
        return False, "missing diagnostic privacy types: " + ", ".join(missing)
    return True, "PrivacyInfo.xcprivacy declares crash and performance diagnostics"


def backend_photo_log_redacted(root: Path) -> tuple[bool, str]:
    path = root / "Backend/api/server.py"
    text = read_text(path)
    required = [
        "def redacted_log_path",
        '"/v1/photos/<redacted>"',
        "redacted_log_path(self.path)",
    ]
    missing = [value for value in required if value not in text]
    if missing:
        return False, "missing backend log redaction markers: " + ", ".join(missing)
    return True, "Backend HTTP logs redact /v1/photos/{photoId} paths"


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
            "containsSecrets": False,
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(root: Path) -> dict[str, Any]:
    started_at = utc_now()
    report = Report()

    crash_hits = third_party_crash_hits(root)
    report.add(
        "iosNoThirdPartyCrashOrAnalyticsSDK",
        not crash_hits,
        "no third-party crash/analytics SDK markers found" if not crash_hits else "; ".join(crash_hits),
    )

    logging_hits = client_logging_hits(root)
    report.add(
        "iosNoClientLoggingCalls",
        not logging_hits,
        "no Swift print/debug/logger calls found" if not logging_hits else "logging calls: " + ", ".join(logging_hits),
    )

    manifest_passed, manifest_evidence = privacy_manifest_diagnostics(root)
    report.add("privacyManifestDiagnosticsDeclared", manifest_passed, manifest_evidence)

    backend_passed, backend_evidence = backend_photo_log_redacted(root)
    report.add("backendPhotoLogPathRedacted", backend_passed, backend_evidence)

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output", default=str(repo_root() / "Backend/proof/diagnostics-redaction.json"))
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(Path(args.repo_root).resolve())
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"diagnostics redaction passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"diagnostics redaction incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
