#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_DOC = Path("Docs/08_Release/MAINLAND_FILING_MATERIALS.md")
EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")
APP_FILING_EVIDENCE_PATTERNS = ("03-app-filing.pdf", "03-app-filing.png")
REQUIRED_STATUS_MARKERS = (
    "中国大陆 App Store 首发",
    "https://api.mewpow.com/xiaonaiping",
    "小奶瓶专属子域名",
    "显著位置展示备案编号",
    "链接工信部备案系统",
    "公安联网备案",
)
REQUIRED_FIELD_MARKERS = (
    "深圳市闪现生活科技有限公司",
    "小奶瓶",
    "iOS 原生 App",
    "com.mewpow.xiaonaiping",
    "xiaonaiping-ios-1",
    "父母/照护者记录宝宝喂养、睡眠、排便、成长、疫苗提醒和照片时间线",
    "否，面向父母和照护者",
    "否，不提供诊断、治疗、处方或专业疫苗建议",
    "中国大陆 App Store",
    "香港 App Store",
    "https://api.mewpow.com/xiaonaiping/privacy",
    "https://api.mewpow.com/xiaonaiping/terms",
    "https://api.mewpow.com/xiaonaiping/support",
    "华为云中国大陆 ECS",
    "宝塔 MySQL",
    "华为云 OBS",
    "xiaonaiping_prod",
    "恢复密钥、手机号验证码、微信授权",
)
REQUIRED_COLLECTION_MARKERS = (
    "营业执照电子版",
    "法定代表人",
    "App 负责人",
    "域名证书",
    "云服务器公网 IP",
    "App 图标",
    "隐私政策 URL",
    "App Store Connect 公司主体截图",
    "中国大陆只选择可售地区截图",
    "短信服务商签名",
    "微信开放平台移动应用",
    "OBS bucket",
    "备案编号",
    "公安联网备案提交/通过证明",
)
REQUIRED_EVIDENCE_FILENAMES = (
    "01-company-account.png",
    "02-mainland-availability.png",
    "03-app-filing.pdf",
    ".png",
    "04-privacy-label.png",
    "05-signed-archive.png",
    "06-testflight.png",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "09-obs-policy.png",
    "10-final-screenshots/",
    "11-test-account-redacted.json",
)
REQUIRED_PRE_CODE_MARKERS = (
    "拿到备案编号后再做，不提前写占位号",
    "隐私政策、用户协议、支持页底部展示备案编号",
    "App 内“数据与隐私”或“关于小奶瓶”展示备案编号和备案系统链接",
    "App Store Review Notes 补充备案编号",
    "Backend/scripts/check_public_pages.py",
    "Backend/scripts/check_review_notes.py",
    "Backend/scripts/check_production_readiness.py",
)
REQUIRED_SEQUENCE_MARKERS = (
    "确认专属域名",
    "华为云/接入商备案系统",
    "备案通过后补 App 内/网页备案编号展示",
    "完成公安联网备案并归档证明",
    "再提交 App Store Connect 中国大陆审核",
)
REQUIRED_REDACTION_MARKERS = (
    "遮个人证件细节",
    "App 名称、主体、备案号或提交状态",
    "App 备案/ICP/适用判断进度或结果",
)
FORBIDDEN_PRETEND_COMPLETE_MARKERS = (
    "备案已完成",
    "APP 备案已通过",
    "ICP 备案已通过",
    "公安联网备案已通过",
)
FORBIDDEN_FAKE_NUMBER_PATTERNS = {
    "zeroIcpNumber": re.compile(r"[\u4e00-\u9fa5]?ICP备0{6,}号?"),
    "placeholderAppFilingNumber": re.compile(r"(APP|App|app)?备案(号|编号)[：:]\s*(待填|TODO|TBD|占位|示例)"),
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


def has_app_filing_evidence(root: Path) -> bool:
    evidence_root = root / EVIDENCE_ROOT
    return any((evidence_root / pattern).is_file() for pattern in APP_FILING_EVIDENCE_PATTERNS)


def fake_number_hits(text: str) -> list[str]:
    return sorted(name for name, pattern in FORBIDDEN_FAKE_NUMBER_PATTERNS.items() if pattern.search(text))


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
    materials_path = root / args.materials
    text = read_text(materials_path)
    report = Report()

    report.add("materialsDocumentPresent", bool(text), str(materials_path) if text else "missing mainland filing materials")

    status_section = extract_section(text, "当前判断")
    missing_status = missing_markers(status_section, REQUIRED_STATUS_MARKERS)
    report.add(
        "currentJudgmentCoversLaunchAndFilingPath",
        bool(status_section) and not missing_status,
        "missing: " + ", ".join(missing_status) if missing_status else "mainland-first filing path and post-filing display boundary present",
    )

    field_section = extract_section(text, "拟填信息")
    missing_fields = missing_markers(field_section, REQUIRED_FIELD_MARKERS)
    report.add(
        "draftFilingFieldsComplete",
        bool(field_section) and not missing_fields,
        "missing: " + ", ".join(missing_fields) if missing_fields else "draft filing fields cover entity, app, URLs, cloud, storage, and auth methods",
    )

    collection_section = extract_section(text, "需要向公司/后台拿到的材料")
    missing_collection = missing_markers(collection_section, REQUIRED_COLLECTION_MARKERS)
    report.add(
        "externalMaterialCollectionListComplete",
        bool(collection_section) and not missing_collection,
        "missing: " + ", ".join(missing_collection) if missing_collection else "external company/cloud/provider material list is complete",
    )

    evidence_section = extract_section(text, "证据归档文件名")
    missing_evidence = missing_markers(evidence_section, REQUIRED_EVIDENCE_FILENAMES)
    report.add(
        "evidenceArchiveFilenamesMatchGate",
        bool(evidence_section) and not missing_evidence,
        "missing: " + ", ".join(missing_evidence) if missing_evidence else "evidence filenames align with AppStoreEvidence gate",
    )

    pre_code_section = extract_section(text, "上线前需要改代码的备案项")
    missing_pre_code = missing_markers(pre_code_section, REQUIRED_PRE_CODE_MARKERS)
    report.add(
        "postFilingCodeChangesDeferredUntilRealNumber",
        bool(pre_code_section) and not missing_pre_code,
        "missing: " + ", ".join(missing_pre_code) if missing_pre_code else "filing number UI/page/review-note changes are explicitly deferred until real filing number",
    )

    sequence_section = extract_section(text, "提交顺序")
    missing_sequence = missing_markers(sequence_section, REQUIRED_SEQUENCE_MARKERS)
    report.add(
        "submissionSequenceKeepsFilingBeforeChinaReview",
        bool(sequence_section) and not missing_sequence,
        "missing: " + ", ".join(missing_sequence) if missing_sequence else "submission order keeps filing and public-security evidence before China App Store review",
    )

    capture_guide = read_text(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md")
    missing_redaction = missing_markers(capture_guide, REQUIRED_REDACTION_MARKERS)
    report.add(
        "captureGuideCoversFilingEvidenceRedaction",
        bool(capture_guide) and not missing_redaction,
        "missing: " + ", ".join(missing_redaction) if missing_redaction else "capture guide describes filing evidence contents and redaction boundary",
    )

    actual_app_filing_evidence = has_app_filing_evidence(root)
    pretend_complete_hits = sorted(marker for marker in FORBIDDEN_PRETEND_COMPLETE_MARKERS if marker in text)
    fake_hits = fake_number_hits(text)
    report.add(
        "doesNotPretendFilingCompleteBeforeEvidence",
        (actual_app_filing_evidence or not pretend_complete_hits) and not fake_hits,
        "completionClaims="
        + ", ".join(pretend_complete_hits)
        + "; fakeNumbers="
        + ", ".join(fake_hits)
        if pretend_complete_hits or fake_hits
        else "materials do not claim App/ICP/public-security filing is complete before archived evidence",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--materials", default=str(EXPECTED_DOC))
    parser.add_argument("--output", default="Backend/proof/mainland-filing-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"mainland filing materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"mainland filing materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
