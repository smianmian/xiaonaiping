#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_STORE_SUBMISSION_PACKET = Path("Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md")
IOS_RELEASE_BUNDLE_VERIFICATION = Path("Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md")
CHINA_MAINLAND_RUNBOOK = Path("Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md")
APP_STORE_EVIDENCE_README = Path("Docs/08_Release/AppStoreEvidence/README.md")
APP_STORE_EVIDENCE_CAPTURE_GUIDE = Path("Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md")
EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")

SIGNING_SECTION_MARKERS = (
    "## Signing and Archive Status",
    "xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing",
    "-configuration Release",
    "-destination 'generic/platform=iOS'",
    "-archivePath /tmp/XiaoNaiPing-CN.xcarchive archive",
    "failed because Xcode signing has no Development Team configured",
    "Apple Developer Team",
    "App Store Distribution signing",
    "before uploading a build to App Store Connect",
)
POST_ARCHIVE_VERIFICATION_MARKERS = (
    "archive 后还要用导出的 `.app` 重新跑 `check_ios_app_bundle.py`",
    "Backend/proof/ios-265-build.json",
    "Backend/proof/ios-app-bundle.json",
    "iphoneos26.5",
    "iOS 26.5",
    "App Store Distribution 签名归档",
    "TestFlight 上传后的同一套包体扫描和真机回归证据",
)
EVIDENCE_FILENAME_MARKERS = (
    "05-signed-archive.png",
    "06-testflight.png",
)
CAPTURE_GUIDE_MARKERS = (
    "`05-signed-archive.png`",
    "App Store Distribution archive 成功",
    "Bundle ID、版本、build、archive success / uploaded status",
    "Apple ID 邮箱",
    "`06-testflight.png`",
    "TestFlight 构建已处理完成并可测试",
    "Build 号、版本、处理状态、测试状态",
    "测试员邮箱",
)
TESTFLIGHT_BOUNDARY_MARKERS = (
    "TestFlight or signed-device final screenshots",
    "TestFlight / 签名真机回归",
    "不替代 TestFlight / 签名真机回归",
    "TestFlight 或签名真机包",
    "iOS 26.5",
)
PRE_SUBMIT_COMMAND_MARKERS = (
    "check_signed_archive_testflight_materials.py",
    "check_ios_app_bundle.py",
    "check_testflight_precheck.py",
    "check_testflight_regression_plan.py",
    "check_app_store_evidence.py",
)
FORBIDDEN_PRETEND_COMPLETE_MARKERS = (
    "Archive 已完成",
    "Archive 已上传",
    "TestFlight 已完成",
    "TestFlight 已通过",
    "signedArchive 已完成",
    "testFlight 已完成",
)
FORBIDDEN_STALE_RUNTIME_PATTERNS = {
    "iphoneos18": re.compile(r"iphoneos18\.\d+"),
    "iphonesimulator18": re.compile(r"iphonesimulator18\.\d+"),
    "ios18Destination": re.compile(r"OS=18\.\d+"),
    "ios27Claim": re.compile(r"iOS 27\.0.*(?:TestFlight|签名真机|真机回归|提交证据)"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def archived_real_evidence_present(root: Path, filename: str) -> bool:
    path = root / EVIDENCE_ROOT / filename
    return path.is_file() and path.stat().st_size > 0


def stale_runtime_hits(text: str) -> list[str]:
    return sorted(name for name, pattern in FORBIDDEN_STALE_RUNTIME_PATTERNS.items() if pattern.search(text))


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
    packet = read_text(root / args.submission_packet)
    bundle_verification = read_text(root / args.bundle_verification)
    runbook = read_text(root / args.runbook)
    evidence_readme = read_text(root / args.evidence_readme)
    capture_guide = read_text(root / args.capture_guide)
    report = Report()

    report.add("submissionPacketPresent", bool(packet), args.submission_packet if packet else "missing submission packet")
    report.add("bundleVerificationPresent", bool(bundle_verification), args.bundle_verification if bundle_verification else "missing bundle verification doc")
    report.add("chinaRunbookPresent", bool(runbook), args.runbook if runbook else "missing China mainland runbook")
    report.add("evidenceReadmePresent", bool(evidence_readme), args.evidence_readme if evidence_readme else "missing AppStoreEvidence README")
    report.add("captureGuidePresent", bool(capture_guide), args.capture_guide if capture_guide else "missing capture guide")

    signing_section = extract_section(packet, "Signing and Archive Status")
    missing_signing = missing_markers(packet, SIGNING_SECTION_MARKERS)
    report.add(
        "signingArchiveStatusDocumentsCurrentBlocker",
        bool(signing_section) and not missing_signing,
        "missing: " + ", ".join(missing_signing)
        if missing_signing
        else "submission packet documents archive command and current signing blocker",
    )

    post_archive_text = bundle_verification + "\n" + runbook + "\n" + packet
    missing_post_archive = missing_markers(post_archive_text, POST_ARCHIVE_VERIFICATION_MARKERS)
    report.add(
        "postArchiveBundleVerificationRequired",
        not missing_post_archive,
        "missing: " + ", ".join(missing_post_archive)
        if missing_post_archive
        else "post-archive flow requires iOS 26.5 bundle proof and exported .app scanning",
    )

    evidence_text = evidence_readme + "\n" + capture_guide + "\n" + runbook
    missing_evidence_names = missing_markers(evidence_text, EVIDENCE_FILENAME_MARKERS)
    report.add(
        "signedArchiveAndTestFlightEvidenceFilenamesPresent",
        not missing_evidence_names,
        "missing: " + ", ".join(missing_evidence_names)
        if missing_evidence_names
        else "05-signed-archive and 06-testflight evidence filenames are documented",
    )

    missing_capture_markers = missing_markers(capture_guide, CAPTURE_GUIDE_MARKERS)
    report.add(
        "signedArchiveAndTestFlightEvidenceRedactionCovered",
        not missing_capture_markers,
        "missing: " + ", ".join(missing_capture_markers)
        if missing_capture_markers
        else "capture guide covers archive/TestFlight status fields and redaction boundaries",
    )

    boundary_text = packet + "\n" + bundle_verification + "\n" + evidence_readme
    missing_testflight_boundary = missing_markers(boundary_text, TESTFLIGHT_BOUNDARY_MARKERS)
    report.add(
        "testFlightEvidenceBoundaryPresent",
        not missing_testflight_boundary,
        "missing: " + ", ".join(missing_testflight_boundary)
        if missing_testflight_boundary
        else "materials keep TestFlight/signed-device screenshots and regression evidence separate from local simulator proof",
    )

    missing_commands = missing_markers(packet, PRE_SUBMIT_COMMAND_MARKERS)
    report.add(
        "preSubmitCommandsIncludeArchiveTestFlightGate",
        not missing_commands,
        "missing: " + ", ".join(missing_commands)
        if missing_commands
        else "submission packet pre-submit commands include archive/TestFlight material, bundle, client, regression, and evidence gates",
    )

    signed_evidence_present = archived_real_evidence_present(root, "05-signed-archive.png")
    testflight_evidence_present = archived_real_evidence_present(root, "06-testflight.png")
    pretend_hits = [
        marker
        for marker in FORBIDDEN_PRETEND_COMPLETE_MARKERS
        if marker in packet + "\n" + evidence_readme + "\n" + runbook
    ]
    report.add(
        "doesNotPretendArchiveOrTestFlightCompleteBeforeEvidence",
        (signed_evidence_present and testflight_evidence_present) or not pretend_hits,
        "completionClaims=" + ", ".join(pretend_hits)
        if pretend_hits
        else "materials do not claim signed archive/TestFlight is complete before archived evidence",
    )

    runtime_hits = stale_runtime_hits(packet + "\n" + bundle_verification + "\n" + runbook + "\n" + evidence_readme)
    report.add(
        "archiveTestFlightMaterialsAvoidStaleRuntimeClaims",
        not runtime_hits,
        "found: " + ", ".join(runtime_hits) if runtime_hits else "archive/TestFlight materials avoid stale iOS 18 or iOS 27 evidence claims",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--submission-packet", default=str(APP_STORE_SUBMISSION_PACKET))
    parser.add_argument("--bundle-verification", default=str(IOS_RELEASE_BUNDLE_VERIFICATION))
    parser.add_argument("--runbook", default=str(CHINA_MAINLAND_RUNBOOK))
    parser.add_argument("--evidence-readme", default=str(APP_STORE_EVIDENCE_README))
    parser.add_argument("--capture-guide", default=str(APP_STORE_EVIDENCE_CAPTURE_GUIDE))
    parser.add_argument("--output", default="Backend/proof/signed-archive-testflight-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"signed archive/TestFlight materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"signed archive/TestFlight materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
