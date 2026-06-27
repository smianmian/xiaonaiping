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
CHINA_MAINLAND_RUNBOOK = Path("Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md")
APP_STORE_EVIDENCE_README = Path("Docs/08_Release/AppStoreEvidence/README.md")
APP_STORE_EVIDENCE_CAPTURE_GUIDE = Path("Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md")
WECHAT_CLIENT_CONFIGURATION = Path("Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md")
SMS_ADAPTER_DOC = Path("Backend/deploy/aliyun-sms-webhook-adapter.md")
OBS_HANDOFF_DOC = Path("Backend/deploy/huawei-obs.md")
EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")

EVIDENCE_FILENAME_MARKERS = (
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "09-obs-policy.png",
)
CAPTURE_GUIDE_MARKERS = (
    "`07-sms-provider.png`",
    "真实短信签名、模板和发送成功",
    "AccessKey、Secret、完整手机号、验证码",
    "`08-wechat-open-platform.png`",
    "AppID、Bundle ID、URL Scheme、Universal Link",
    "AppSecret、管理员账号",
    "`09-obs-policy.png`",
    "bucket/prefix、区域、加密/生命周期/删除策略状态",
    "AK/SK、完整对象 key",
)
SMS_MATERIAL_MARKERS = (
    "07-sms-provider.png",
    "阿里云 Dysmsapi",
    "HMAC-SHA256",
    "dysms:SendSms",
    "签名",
    "模板",
    "发送成功",
    "AccessKey",
    "Secret",
    "完整手机号",
    "验证码",
    "XNP_SMS_SECRET",
)
WECHAT_MATERIAL_MARKERS = (
    "08-wechat-open-platform.png",
    "wx + 16 hex",
    "AppID",
    "Bundle ID",
    "URL Scheme",
    "Universal Link",
    "AppSecret",
    "服务端",
    "不能写进 iOS 工程或仓库",
)
OBS_MATERIAL_MARKERS = (
    "09-obs-policy.png",
    "private bucket",
    "bucket",
    "prefix",
    "区域",
    "加密",
    "生命周期",
    "删除验证",
    "AK/SK",
    "完整对象 key",
    "server-side",
)
PRE_SUBMIT_COMMAND_MARKERS = (
    "verify_auth_providers.py",
    "verify_storage_backend.py",
    "check_wechat_client_configuration.py",
    "check_provider_evidence_materials.py",
    "check_app_store_evidence.py",
)
FORBIDDEN_COMPLETION_MARKERS = {
    "07-sms-provider": (
        "短信服务商证据已完成",
        "短信 provider 已完成",
        "smsProvider 已完成",
        "07-sms-provider 已完成",
    ),
    "08-wechat-open-platform": (
        "微信开放平台证据已完成",
        "WeChat Open Platform proof complete",
        "wechatOpenPlatform 已完成",
        "08-wechat-open-platform 已完成",
    ),
    "09-obs-policy": (
        "OBS 策略证据已完成",
        "OBS policy proof complete",
        "huaweiObsPolicy 已完成",
        "09-obs-policy 已完成",
    ),
}
FORBIDDEN_SECRET_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9_-]+\.[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
    "plainProviderSecretAssignment": re.compile(
        r"(?:XNP_SMS_SECRET|XNP_WECHAT_APP_SECRET|ALIYUN_ACCESS_KEY_SECRET|HUAWEI_OBS_SECRET_ACCESS_KEY)\s*=\s*(?![<.])\S{8,}"
    ),
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
    runbook = read_text(root / args.runbook)
    evidence_readme = read_text(root / args.evidence_readme)
    capture_guide = read_text(root / args.capture_guide)
    wechat_doc = read_text(root / args.wechat_client_configuration)
    sms_doc = read_text(root / args.sms_adapter_doc)
    obs_doc = read_text(root / args.obs_handoff_doc)
    report = Report()

    report.add("submissionPacketPresent", bool(packet), args.submission_packet if packet else "missing submission packet")
    report.add("chinaRunbookPresent", bool(runbook), args.runbook if runbook else "missing China mainland runbook")
    report.add("evidenceReadmePresent", bool(evidence_readme), args.evidence_readme if evidence_readme else "missing AppStoreEvidence README")
    report.add("captureGuidePresent", bool(capture_guide), args.capture_guide if capture_guide else "missing capture guide")
    report.add("smsAdapterDocPresent", bool(sms_doc), args.sms_adapter_doc if sms_doc else "missing SMS adapter doc")
    report.add("wechatClientConfigurationPresent", bool(wechat_doc), args.wechat_client_configuration if wechat_doc else "missing WeChat handoff doc")
    report.add("obsHandoffDocPresent", bool(obs_doc), args.obs_handoff_doc if obs_doc else "missing OBS handoff doc")

    evidence_index_text = evidence_readme + "\n" + capture_guide + "\n" + runbook
    missing_evidence_names = missing_markers(evidence_index_text, EVIDENCE_FILENAME_MARKERS)
    report.add(
        "providerEvidenceFilenamesPresent",
        not missing_evidence_names,
        "missing: " + ", ".join(missing_evidence_names)
        if missing_evidence_names
        else "07 SMS, 08 WeChat, and 09 OBS evidence filenames are documented",
    )

    missing_capture_markers = missing_markers(capture_guide, CAPTURE_GUIDE_MARKERS)
    report.add(
        "providerEvidenceRedactionCovered",
        not missing_capture_markers,
        "missing: " + ", ".join(missing_capture_markers)
        if missing_capture_markers
        else "capture guide covers provider fields to keep and secrets to redact",
    )

    missing_sms_markers = missing_markers(sms_doc + "\n" + capture_guide + "\n" + runbook, SMS_MATERIAL_MARKERS)
    report.add(
        "smsProviderMaterialCoversSignatureTemplateSendAndSecrets",
        not missing_sms_markers,
        "missing: " + ", ".join(missing_sms_markers)
        if missing_sms_markers
        else "SMS material covers signature, template, send success, webhook signing, and secret redaction",
    )

    missing_wechat_markers = missing_markers(wechat_doc + "\n" + capture_guide + "\n" + runbook, WECHAT_MATERIAL_MARKERS)
    report.add(
        "wechatOpenPlatformMaterialCoversClientServerSecretBoundary",
        not missing_wechat_markers,
        "missing: " + ", ".join(missing_wechat_markers)
        if missing_wechat_markers
        else "WeChat material covers AppID, Bundle ID, URL Scheme, Universal Link, server AppSecret, and evidence path",
    )

    missing_obs_markers = missing_markers(obs_doc + "\n" + capture_guide + "\n" + runbook, OBS_MATERIAL_MARKERS)
    report.add(
        "huaweiObsMaterialCoversBucketEncryptionLifecycleDeletion",
        not missing_obs_markers,
        "missing: " + ", ".join(missing_obs_markers)
        if missing_obs_markers
        else "OBS material covers bucket/prefix, region, encryption, lifecycle, deletion validation, and key redaction",
    )

    missing_commands = missing_markers(packet + "\n" + runbook, PRE_SUBMIT_COMMAND_MARKERS)
    report.add(
        "preSubmitCommandsIncludeProviderEvidenceGate",
        not missing_commands,
        "missing: " + ", ".join(missing_commands)
        if missing_commands
        else "pre-submit commands include provider evidence material gate and related live provider/storage checks",
    )

    all_materials = "\n".join([packet, runbook, evidence_readme, capture_guide, wechat_doc, sms_doc, obs_doc])
    secret_hits = forbidden_secret_hits(all_materials)
    report.add(
        "providerEvidenceMaterialsDoNotExposeSecrets",
        not secret_hits,
        "found: " + ", ".join(secret_hits)
        if secret_hits
        else "provider evidence materials do not expose recovery keys, tokens, debug codes, API keys, full phone numbers, or literal provider secrets",
    )

    pretend_hits: list[str] = []
    for stem, markers in FORBIDDEN_COMPLETION_MARKERS.items():
        if archived_real_evidence_present(root, stem):
            continue
        pretend_hits.extend(marker for marker in markers if marker in all_materials)
    report.add(
        "doesNotPretendProviderEvidenceCompleteBeforeFiles",
        not pretend_hits,
        "completionClaims=" + ", ".join(pretend_hits)
        if pretend_hits
        else "materials do not claim SMS/WeChat/OBS evidence is complete before archived real evidence files exist",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--submission-packet", default=str(APP_STORE_SUBMISSION_PACKET))
    parser.add_argument("--runbook", default=str(CHINA_MAINLAND_RUNBOOK))
    parser.add_argument("--evidence-readme", default=str(APP_STORE_EVIDENCE_README))
    parser.add_argument("--capture-guide", default=str(APP_STORE_EVIDENCE_CAPTURE_GUIDE))
    parser.add_argument("--wechat-client-configuration", default=str(WECHAT_CLIENT_CONFIGURATION))
    parser.add_argument("--sms-adapter-doc", default=str(SMS_ADAPTER_DOC))
    parser.add_argument("--obs-handoff-doc", default=str(OBS_HANDOFF_DOC))
    parser.add_argument("--output", default="Backend/proof/provider-evidence-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"provider evidence materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"provider evidence materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
