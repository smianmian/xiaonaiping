#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_CASE_IDS = {f"RD-{index:02d}" for index in range(1, 25)}
REQUIRED_COVERAGE_MARKERS = {
    "coldStart": ("RD-01", "冷启动", "首页"),
    "babyProfile": ("RD-02", "创建宝宝档案"),
    "feedingRecord": ("RD-03", "记录喂养"),
    "sleepRecord": ("RD-04", "记录睡眠"),
    "diaperRecord": ("RD-05", "记录排便"),
    "growthRecord": ("RD-06", "成长记录"),
    "vaccineTemplate": ("RD-07", "疫苗模板切换", "不构成医疗建议"),
    "photoPermissionDenied": ("RD-08", "相册权限拒绝"),
    "photoPermissionAllowed": ("RD-09", "相册权限允许", "不自动扫描系统相册"),
    "recoveryKeyLogin": ("RD-10", "恢复密钥账号登录"),
    "cloudBackup": ("RD-11", "云备份"),
    "cloudRestore": ("RD-12", "云恢复"),
    "phoneLogin": ("RD-13", "手机号登录"),
    "wechatLogin": ("RD-14", "微信登录"),
    "accountDeletion": ("RD-15", "删除云端账号与备份"),
    "offlineSave": ("RD-16", "断网保存"),
    "notificationPermission": ("RD-17", "通知权限"),
    "appleWatchMirror": ("RD-18", "Apple Watch"),
    "publicUrls": ("RD-19", "隐私政策/用户协议/支持 URL"),
    "diagnosticsRedaction": ("RD-20", "崩溃/日志脱敏"),
    "bundleSelfCheck": ("RD-21", "Release 包体自检"),
    "liveActivitySwitch": ("RD-22", "灵动岛喝奶提醒开关"),
    "widgets": ("RD-23", "锁屏/桌面小组件"),
    "reviewBoundary": ("RD-24", "审核边界文案"),
}
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    re.compile(r"sk-[A-Za-z0-9]{12,}"),
)
REQUIRED_TEMPLATE_MARKERS = (
    "不要把恢复密钥、验证码、完整手机号、token、真实宝宝照片或对象存储 key 写进来",
    "本项目真机回归只接受 iOS 26.5",
    "iOS 27.0 不能作为本项目真机回归证据",
    "- iOS：26.5",
    "- 安装方式：TestFlight",
    "安装方式只能填写 `TestFlight` 或 `Xcode 签名真机包` 其中一个",
    "- [ ] iOS 26.5",
    "- [ ] 微信登录",
    "- [ ] 账号删除",
    "- [ ] 灵动岛喝奶提醒开关",
    "- [ ] 锁屏/桌面小组件",
    "- [ ] 审核边界文案",
    "RD-01",
    "RD-24",
    "最终提交前每一行都必须改成“通过”",
    "Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔",
    "小组件只读展示本机今日摘要",
    "状态展示只反映用户主动记录的数据",
    "不生成健康建议、压力提醒、喂养建议",
    "不接入 HealthKit",
    "不提供压力评估",
)
REQUIRED_REAL_DEVICE_EVIDENCE_PATHS = {
    "overview": "RealDevice/00-overview.png",
    "RD-01": "RealDevice/RD-01-cold-start.png",
    "RD-02": "RealDevice/RD-02-baby-profile.png",
    "RD-03": "RealDevice/RD-03-feeding-record.png",
    "RD-04": "RealDevice/RD-04-sleep-record.png",
    "RD-05": "RealDevice/RD-05-diaper-record.png",
    "RD-06": "RealDevice/RD-06-growth-record.png",
    "RD-07": "RealDevice/RD-07-vaccine-template.png",
    "RD-08": "RealDevice/RD-08-photo-denied.png",
    "RD-09": "RealDevice/RD-09-photo-allowed.png",
    "RD-10": "RealDevice/RD-10-recovery-login.png",
    "RD-11": "RealDevice/RD-11-cloud-backup.png",
    "RD-12": "RealDevice/RD-12-cloud-restore.png",
    "RD-13": "RealDevice/RD-13-phone-login.png",
    "RD-14": "RealDevice/RD-14-wechat-login.png",
    "RD-15": "RealDevice/RD-15-account-delete.png",
    "RD-16": "RealDevice/RD-16-offline-save.png",
    "RD-17": "RealDevice/RD-17-notification-permission.png",
    "RD-18": "RealDevice/RD-18-watch-mirror.png",
    "RD-19": "RealDevice/RD-19-public-urls.png",
    "RD-20": "RealDevice/RD-20-diagnostics-redaction.png",
    "RD-21": "RealDevice/RD-21-release-bundle.png",
    "RD-22": "RealDevice/RD-22-live-activity-switch.png",
    "RD-23": "RealDevice/RD-23-widget-summary.png",
    "RD-24": "RealDevice/RD-24-review-boundary.png",
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


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def extract_regression_cases(text: str) -> dict[str, dict[str, str]]:
    cases: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        case_id = cells[0]
        if re.fullmatch(r"RD-\d{2}", case_id):
            cases[case_id] = {
                "case": cells[1],
                "expected": cells[2],
                "result": cells[3],
                "line": line,
            }
    return cases


def contains_all(text: str, markers: tuple[str, ...]) -> bool:
    return all(marker in text for marker in markers)


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


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
    plan_path = root / args.plan
    review_account_path = root / args.review_account
    sim_launch_path = root / args.sim_launch_proof
    device_availability_path = root / args.device_availability_proof
    app_store_evidence_path = root / args.app_store_evidence_proof
    template_path = root / args.real_device_template
    text = read_text(plan_path)
    template = read_text(template_path)
    review_account = read_json(review_account_path)
    sim_launch = read_json(sim_launch_path)
    device_availability = read_json(device_availability_path)
    app_store_evidence = read_json(app_store_evidence_path)
    cases = extract_regression_cases(text)
    report = Report()

    report.add("regressionPlanPresent", bool(text), str(plan_path) if text else "missing regression plan")

    report.add(
        "realDeviceRegressionTemplatePresent",
        bool(template),
        str(template_path) if template else "missing real-device regression template",
    )
    template_missing = missing_markers(template, REQUIRED_TEMPLATE_MARKERS)
    report.add(
        "realDeviceRegressionTemplateStrict",
        not template_missing,
        "missing: " + ", ".join(template_missing)
        if template_missing
        else "real-device evidence template keeps iOS 26.5, exact TestFlight/signed-device install method, RD-01..RD-24, and review boundary requirements",
    )
    missing_evidence_path_markers = [
        path
        for path in REQUIRED_REAL_DEVICE_EVIDENCE_PATHS.values()
        if path not in text or path not in template
    ]
    report.add(
        "realDeviceEvidenceFilenamePlanPresent",
        not missing_evidence_path_markers,
        "missing: " + ", ".join(missing_evidence_path_markers)
        if missing_evidence_path_markers
        else "real-device plan and template provide stable RealDevice/ evidence filenames for overview and RD-01..RD-24",
    )

    review_account_ok = (
        review_account.get("recoveryVerified") is True
        and review_account.get("backupSeeded") is True
        and review_account.get("containsSecret") is False
        and review_account.get("recoveryKeyStored") == ".env.xnp-review-account"
    )
    report.add(
        "reviewAccountRedactedProofPresent",
        review_account_ok,
        "redacted review account proof is verified and secret-free" if review_account_ok else f"invalid {review_account_path}",
    )

    report.add(
        "appReviewLoginInstructionsSafe",
        contains_all(text, ("恢复密钥登录", ".env.xnp-review-account", "不使用 debug code", "不使用未配置完成的微信登录替代恢复密钥审核路径")),
        "recovery-key review login path is documented and debug/unfinished WeChat substitutes are forbidden",
    )

    report.add(
        "realDeviceEnvironmentPlanPresent",
        contains_all(text, ("iOS 26.5", "TestFlight / Xcode 签名真机包", "Wi-Fi + 蜂窝网络", "中国大陆", "12-real-device-regression.md")),
        "real-device/TestFlight environment, network, region, and evidence path are present",
    )

    sim_info = sim_launch.get("simulator", {}) if isinstance(sim_launch.get("simulator", {}), dict) else {}
    sim_app = sim_launch.get("app", {}) if isinstance(sim_launch.get("app", {}), dict) else {}
    sim_ok = (
        sim_launch.get("passed") is True
        and sim_info.get("runtime") == "iOS 26.5"
        and sim_app.get("dtPlatformVersion") == "26.5"
        and "com.mewpow.xiaonaiping:" in str(sim_launch.get("launchOutput", ""))
        and "不替代 TestFlight / 签名真机回归" in text
    )
    report.add(
        "ios265SmokeProofReferenced",
        sim_ok,
        "iOS 26.5 simulator launch proof is referenced and explicitly not treated as TestFlight evidence"
        if sim_ok
        else f"invalid or missing {sim_launch_path}",
    )
    launch_output = str(sim_launch.get("launchOutput", "")).strip()
    report.add(
        "ios265SmokeTextMatchesProof",
        bool(launch_output) and launch_output in text,
        f"launchOutput={launch_output or '<missing>'}",
    )

    device_availability_ok = (
        device_availability.get("passed") is True
        and device_availability.get("requiredIOS") == "26.5"
        and "当前本机真机可用性" in text
        and "不符合本项目 iOS 26.5 本机测试规则" in text
    )
    report.add(
        "ios265DeviceAvailabilityProofReferenced",
        device_availability_ok,
        "iOS 26.5 physical-device availability proof is referenced and non-26.5 devices are excluded"
        if device_availability_ok
        else f"invalid or missing {device_availability_path}",
    )

    missing_case_ids = sorted(REQUIRED_CASE_IDS - set(cases))
    report.add(
        "regressionCaseIdsComplete",
        not missing_case_ids,
        "missing: " + ", ".join(missing_case_ids) if missing_case_ids else "RD-01 through RD-24 are present",
    )

    missing_coverage = [
        name
        for name, markers in REQUIRED_COVERAGE_MARKERS.items()
        if not contains_all(text, markers)
    ]
    report.add(
        "regressionCoverageComplete",
        not missing_coverage,
        "missing coverage: " + ", ".join(missing_coverage) if missing_coverage else "all required real-device regression areas are covered",
    )

    rd13 = cases.get("RD-13", {}).get("line", "")
    rd14 = cases.get("RD-14", {}).get("line", "")
    report.add(
        "externalAuthCasesMarkedPending",
        "待真实短信配置" in rd13 and "待微信开放平台配置" in rd14,
        "SMS and WeChat cases are explicitly pending real providers",
    )

    report.add(
        "passCriteriaSeparateExternalAuthAndEvidence",
        contains_all(
            text,
            (
                "RD-01 到 RD-12、RD-15 到 RD-24 必须通过",
                "RD-13 和 RD-14 必须在真实短信和微信配置完成后通过",
                "不能用 debug code 代替",
                "每轮真机回归必须附截图或录屏证据",
            ),
        ),
        "pass criteria separates real-provider auth from core regression and requires evidence",
    )

    app_store_evidence_checks = app_store_evidence.get("checks", {})
    real_device_evidence = (
        app_store_evidence_checks.get("realDeviceRegression", {})
        if isinstance(app_store_evidence_checks, dict)
        else {}
    )
    real_device_evidence_ready = (
        isinstance(real_device_evidence, dict)
        and real_device_evidence.get("passed") is True
    )
    regression_pending_statement = contains_all(
        text,
        (
            "TestFlight 真机回归尚未完成",
            "不替代 TestFlight / 签名真机回归",
            "12-real-device-regression.md",
        ),
    )
    report.add(
        "realDeviceEvidenceGateSeparated",
        real_device_evidence_ready or regression_pending_statement,
        "real-device evidence is complete"
        if real_device_evidence_ready
        else "plan explicitly states TestFlight/signed-device regression is still incomplete and points to 12-real-device-regression.md"
        if regression_pending_statement
        else f"missing real-device evidence status from {plan_path} or {app_store_evidence_path}",
    )

    report.add(
        "reviewBoundaryCasesPresent",
        contains_all(
            text,
            (
                "HealthKit",
                "传感器",
                "状态展示",
                "健康建议",
                "压力评估",
                "压力提醒",
                "心理健康判断",
                "医疗诊断",
                "喂养建议",
                "不展示照片原图",
                "token",
                "云端对象 key",
            ),
        ),
        "Live Activity/widget/review boundary terms are present",
    )

    secret_hits = [pattern.pattern for pattern in FORBIDDEN_SECRET_PATTERNS if pattern.search(text)]
    report.add(
        "regressionPlanDoesNotExposeSecrets",
        not secret_hits,
        "found secret-like markers: " + ", ".join(secret_hits) if secret_hits else "no recovery key assignments, tokens, debug codes, or API-key markers found",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--plan", default="Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md")
    parser.add_argument("--review-account", default="Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json")
    parser.add_argument("--sim-launch-proof", default="Backend/proof/sim-launch-ios265-20260626.json")
    parser.add_argument("--device-availability-proof", default="Backend/proof/ios265-device-availability.json")
    parser.add_argument("--app-store-evidence-proof", default="Backend/proof/app-store-evidence.json")
    parser.add_argument("--real-device-template", default="Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md")
    parser.add_argument("--output", default="Backend/proof/testflight-regression-plan.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"TestFlight regression plan passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"TestFlight regression plan incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
