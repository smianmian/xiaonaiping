#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FALLBACK_FILL_SHEET = Path("Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md")
FILL_SHEET_PATTERN = "APP_STORE_CONNECT_FILL_SHEET_*.md"
SUBMISSION_PACKET = Path("Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md")
CHINA_MAINLAND_RUNBOOK = Path("Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md")
EVIDENCE_README = Path("Docs/08_Release/AppStoreEvidence/README.md")
CAPTURE_GUIDE = Path("Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md")
PRIVACY_LABEL = Path("Docs/08_Release/APP_STORE_PRIVACY_LABEL.json")
EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")

EXPECTED_COMPANY = "深圳市闪现生活科技有限公司"
EXPECTED_APP_NAME = "小奶瓶"
EXPECTED_BUNDLE_ID = "com.mewpow.xiaonaiping"
EXPECTED_PRIVACY_URL = "https://api.mewpow.com/xiaonaiping/privacy"
EXPECTED_SUPPORT_URL = "https://api.mewpow.com/xiaonaiping/support"
EXPECTED_PRIVACY_CATEGORIES = {
    "Identifiers",
    "Contact Info",
    "User Content",
    "Photos or Videos",
    "Health and Fitness",
    "Usage Data",
    "Diagnostics",
}
EVIDENCE_FILENAME_MARKERS = (
    "01-company-account.png",
    "02-mainland-availability.png",
    "04-privacy-label.png",
)
CAPTURE_GUIDE_MARKERS = (
    "`01-company-account.png`",
    "App Store Connect 账号主体为深圳市闪现生活科技有限公司",
    "团队/法律主体名称、账号页标题",
    "邮箱、电话、付款信息",
    "`02-mainland-availability.png`",
    "首发只选 China mainland / 中国大陆",
    "App 名称、可售地区选择状态",
    "无关账号信息",
    "`04-privacy-label.png`",
    "App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写",
    "已采集类别、未追踪、用途",
    "账号邮箱",
)
FILL_SHEET_MARKERS = (
    EXPECTED_COMPANY,
    EXPECTED_APP_NAME,
    EXPECTED_BUNDLE_ID,
    "Specific Countries or Regions -> China mainland",
    "Hong Kong",
    EXPECTED_PRIVACY_URL,
    EXPECTED_SUPPORT_URL,
    "APP_STORE_PRIVACY_LABEL.json",
    "Identifiers",
    "Contact Info",
    "User Content",
    "Photos or Videos",
    "Health and Fitness",
    "Usage Data",
    "Diagnostics",
    "否",
    "不接入 HealthKit",
    "不提供压力评估",
)
PRE_SUBMIT_COMMAND_MARKERS = (
    "check_app_store_connect_materials.py",
    "check_app_store_connect_evidence_materials.py",
    "check_app_store_evidence.py",
)
FORBIDDEN_COMPLETION_MARKERS = {
    "01-company-account": (
        "公司主体证据已完成",
        "App Store Connect 主体证据已完成",
        "companyAccount 已完成",
        "01-company-account 已完成",
    ),
    "02-mainland-availability": (
        "可售地区证据已完成",
        "中国大陆可售地区证据已完成",
        "mainlandAvailability 已完成",
        "02-mainland-availability 已完成",
    ),
    "04-privacy-label": (
        "隐私标签证据已完成",
        "App Privacy 证据已完成",
        "privacyLabel 已完成",
        "04-privacy-label 已完成",
    ),
}
FORBIDDEN_SECRET_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
}
ACCEPTED_EVIDENCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".json"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def latest_fill_sheet(root: Path) -> str:
    candidates = sorted((root / "Docs/08_Release").glob(FILL_SHEET_PATTERN))
    if not candidates:
        return str(FALLBACK_FILL_SHEET)
    return str(candidates[-1].relative_to(root))


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def forbidden_secret_hits(text: str) -> list[str]:
    return sorted(name for name, pattern in FORBIDDEN_SECRET_PATTERNS.items() if pattern.search(text))


def archived_real_evidence_present(root: Path, stem: str) -> bool:
    evidence_root = root / EVIDENCE_ROOT
    if not evidence_root.exists():
        return False
    for suffix in ACCEPTED_EVIDENCE_SUFFIXES:
        path = evidence_root / f"{stem}{suffix}"
        if path.is_file() and path.stat().st_size > 0:
            return True
    return False


def privacy_label_failures(data: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    app = data.get("app", {}) if isinstance(data.get("app", {}), dict) else {}
    if app.get("name") != EXPECTED_APP_NAME:
        failures.append("app.name")
    if app.get("bundleId") != EXPECTED_BUNDLE_ID:
        failures.append("app.bundleId")
    if app.get("usesTracking") is not False:
        failures.append("app.usesTracking")
    if app.get("containsThirdPartyAdvertising") is not False:
        failures.append("app.containsThirdPartyAdvertising")
    if app.get("containsThirdPartyAnalytics") is not False:
        failures.append("app.containsThirdPartyAnalytics")
    if data.get("privacyPolicyUrl") != EXPECTED_PRIVACY_URL:
        failures.append("privacyPolicyUrl")
    if data.get("supportUrl") != EXPECTED_SUPPORT_URL:
        failures.append("supportUrl")

    categories = data.get("dataCategories", [])
    if not isinstance(categories, list):
        return failures + ["dataCategories"]
    by_name: dict[str, dict[str, Any]] = {}
    for item in categories:
        if isinstance(item, dict) and isinstance(item.get("category"), str):
            by_name[item["category"]] = item
    missing = sorted(EXPECTED_PRIVACY_CATEGORIES - set(by_name))
    if missing:
        failures.append("missing categories: " + ", ".join(missing))
    for category in EXPECTED_PRIVACY_CATEGORIES & set(by_name):
        item = by_name[category]
        if item.get("collected") is not True:
            failures.append(f"{category}.collected")
        if item.get("usedForTracking") is not False:
            failures.append(f"{category}.usedForTracking")
        if not isinstance(item.get("purposes"), list) or not item.get("purposes"):
            failures.append(f"{category}.purposes")
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
    fill_sheet_arg = args.fill_sheet or latest_fill_sheet(root)
    fill_sheet = read_text(root / fill_sheet_arg)
    packet = read_text(root / args.submission_packet)
    runbook = read_text(root / args.runbook)
    evidence_readme = read_text(root / args.evidence_readme)
    capture_guide = read_text(root / args.capture_guide)
    privacy_label = read_json(root / args.privacy_label)
    report = Report()

    report.add("fillSheetPresent", bool(fill_sheet), fill_sheet_arg if fill_sheet else "missing fill sheet")
    report.add("submissionPacketPresent", bool(packet), args.submission_packet if packet else "missing submission packet")
    report.add("chinaRunbookPresent", bool(runbook), args.runbook if runbook else "missing China mainland runbook")
    report.add("evidenceReadmePresent", bool(evidence_readme), args.evidence_readme if evidence_readme else "missing AppStoreEvidence README")
    report.add("captureGuidePresent", bool(capture_guide), args.capture_guide if capture_guide else "missing capture guide")
    report.add("privacyLabelJsonPresent", bool(privacy_label), args.privacy_label if privacy_label else "missing privacy label JSON")

    evidence_index_text = evidence_readme + "\n" + capture_guide + "\n" + runbook
    missing_filenames = missing_markers(evidence_index_text, EVIDENCE_FILENAME_MARKERS)
    report.add(
        "appStoreConnectEvidenceFilenamesPresent",
        not missing_filenames,
        "missing: " + ", ".join(missing_filenames)
        if missing_filenames
        else "01 company account, 02 mainland availability, and 04 privacy label evidence filenames are documented",
    )

    missing_capture = missing_markers(capture_guide, CAPTURE_GUIDE_MARKERS)
    report.add(
        "appStoreConnectEvidenceRedactionCovered",
        not missing_capture,
        "missing: " + ", ".join(missing_capture)
        if missing_capture
        else "capture guide covers company account, mainland availability, and privacy label fields/redaction",
    )

    missing_fill_sheet = missing_markers(fill_sheet, FILL_SHEET_MARKERS)
    report.add(
        "appStoreConnectFillSheetCoversEvidenceFields",
        not missing_fill_sheet,
        "missing: " + ", ".join(missing_fill_sheet)
        if missing_fill_sheet
        else "fill sheet covers company, app, bundle, region, URLs, privacy categories, no tracking, and health boundary",
    )

    privacy_failures = privacy_label_failures(privacy_label)
    report.add(
        "privacyLabelJsonMatchesEvidenceChecklist",
        not privacy_failures,
        "failures: " + ", ".join(privacy_failures)
        if privacy_failures
        else "privacy label JSON matches expected App Store Connect evidence categories, URLs, and tracking flags",
    )

    missing_commands = missing_markers(packet + "\n" + runbook, PRE_SUBMIT_COMMAND_MARKERS)
    report.add(
        "preSubmitCommandsIncludeAppStoreConnectEvidenceGate",
        not missing_commands,
        "missing: " + ", ".join(missing_commands)
        if missing_commands
        else "pre-submit commands include App Store Connect materials, evidence-materials, and final evidence gates",
    )

    all_materials = "\n".join([fill_sheet, packet, runbook, evidence_readme, capture_guide, json.dumps(privacy_label, ensure_ascii=False)])
    secret_hits = forbidden_secret_hits(all_materials)
    report.add(
        "appStoreConnectEvidenceMaterialsDoNotExposeSecrets",
        not secret_hits,
        "found: " + ", ".join(secret_hits)
        if secret_hits
        else "App Store Connect evidence materials do not expose recovery keys, tokens, debug codes, API keys, or complete phone numbers",
    )

    pretend_hits: list[str] = []
    for stem, markers in FORBIDDEN_COMPLETION_MARKERS.items():
        if archived_real_evidence_present(root, stem):
            continue
        pretend_hits.extend(marker for marker in markers if marker in all_materials)
    report.add(
        "doesNotPretendAppStoreConnectEvidenceCompleteBeforeFiles",
        not pretend_hits,
        "completionClaims=" + ", ".join(pretend_hits)
        if pretend_hits
        else "materials do not claim company account, mainland availability, or privacy label evidence is complete before real files exist",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--fill-sheet")
    parser.add_argument("--submission-packet", default=str(SUBMISSION_PACKET))
    parser.add_argument("--runbook", default=str(CHINA_MAINLAND_RUNBOOK))
    parser.add_argument("--evidence-readme", default=str(EVIDENCE_README))
    parser.add_argument("--capture-guide", default=str(CAPTURE_GUIDE))
    parser.add_argument("--privacy-label", default=str(PRIVACY_LABEL))
    parser.add_argument("--output", default="Backend/proof/app-store-connect-evidence-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"App Store Connect evidence materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"App Store Connect evidence materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
