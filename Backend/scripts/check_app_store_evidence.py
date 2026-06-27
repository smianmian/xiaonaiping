#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVIDENCE_ROOT = Path("Docs/08_Release/AppStoreEvidence")
DEFAULT_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".json"}
TEXT_EVIDENCE_EXTENSIONS = {".json", ".md", ".txt"}
REAL_DEVICE_EVIDENCE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".mp4", ".mov", ".pdf")
MIN_MANUAL_EVIDENCE_BYTES = 10 * 1024
REQUIRED_RD_IDS = {f"RD-{index:02d}" for index in range(1, 25)}
REQUIRED_REAL_DEVICE_ENV_FIELDS = ["设备", "iOS", "安装方式", "App 版本", "Build", "网络", "证据截图/录屏"]
REQUIRED_REAL_DEVICE_VISUAL_FIELDS = [
    "灵动岛紧凑态结论",
    "灵动岛展开态结论",
    "锁屏通知栈结论",
    "桌面小组件结论",
]
REQUIRED_VISUAL_CONCLUSION_PATTERNS = {
    "灵动岛紧凑态结论": re.compile(r"(无裁剪|不裁剪|边缘完整|未右移|不右移|未压到岛中心|不压到岛中心)"),
    "灵动岛展开态结论": re.compile(r"(无裁剪|不裁剪|边缘完整|未贴边|不贴边|未被吞|不被吞)"),
    "锁屏通知栈结论": re.compile(r"(无裁剪|不裁剪|边缘完整|不遮挡|无遮挡)"),
    "桌面小组件结论": re.compile(r"(无裁剪|不裁剪|无溢出|边缘完整|不展示隐私照片)"),
}
REQUIRED_VISUAL_RD_PATH_PATTERNS = {
    "RD-17": re.compile(r"(notification|permission|通知|权限)", re.IGNORECASE),
    "RD-18": re.compile(r"(?=.*(watch|apple-?watch))(?=.*(mirror|notification|镜像|通知))", re.IGNORECASE),
    "RD-22": re.compile(r"(?=.*(live-?activity|dynamic-?island|island|灵动岛))(?=.*(switch|toggle|开关))", re.IGNORECASE),
    "RD-23": re.compile(r"(?=.*(widget|小组件))(?=.*(lock-?screen|锁屏))", re.IGNORECASE),
    "RD-24": re.compile(r"(review|boundary|审核|边界)", re.IGNORECASE),
}
PENDING_REAL_DEVICE_MARKERS = ("待测", "待填", "待真实", "TODO", "TBD")
APP_STORE_ASSETS_PROOF = Path("Backend/proof/app-store-assets.json")
MANUAL_EVIDENCE_CHECKLIST = Path("Docs/08_Release/APP_STORE_EVIDENCE_CHECKLIST_20260627.md")
REQUIRED_FINAL_SCREENSHOT_ASSET_CHECKS = [
    "finalScreenshotsCount",
    "finalScreenshotsExpectedUploadOrder",
    "finalScreenshotsAcceptedSizes",
    "finalScreenshotsNotBlank",
    "finalScreenshotsNoBabyPhotoNames",
    "finalScreenshotsIOS265ProvenancePresent",
]
TEMPLATE_REAL_DEVICE_MARKERS = (
    "复制本文件为 `12-real-device-regression.md` 后再填写",
    "12-real-device-regression.md Template",
)
FORBIDDEN_REAL_DEVICE_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
}

MANUAL_EVIDENCE_CHECKLIST_MARKERS = [
    "仍需补齐的人工证据",
    "真机回归必须覆盖",
    "RD 用例列表",
    "灵动岛 / 小组件 / Apple Watch 边界",
    "遮挡与脱敏规则",
    "当前不可替代项",
    "采集后必跑",
    "01-company-account.png",
    "02-mainland-availability.png",
    "03-app-filing.pdf",
    "03-app-filing.png",
    "04-privacy-label.png",
    "05-signed-archive.png",
    "06-testflight.png",
    "07-sms-provider.png",
    "08-wechat-open-platform.png",
    "09-obs-policy.png",
    "10-final-screenshots/",
    "01-home-iphone16pro.png",
    "02-record-iphone16pro.png",
    "03-growth-iphone16pro.png",
    "04-profile-iphone16pro.png",
    "05-profile-backup-iphone16pro.png",
    "11-test-account-redacted.json",
    "12-real-device-regression.md",
    "单个 RD 文件不低于 10KB",
    "iOS 26.5",
    "TestFlight",
    "Xcode 签名真机包",
    "灵动岛紧凑态结论",
    "灵动岛展开态结论",
    "锁屏通知栈结论",
    "桌面小组件结论",
    "Apple Watch 只作为系统镜像通知",
    "不在 App Store 文案中承诺 Watch App",
    "RD-18、RD-22、RD-23、RD-24 不能复用总览图或同一份泛证据",
    "RD-17 路径必须体现 notification、permission、通知或权限",
    "RD-18 路径必须同时体现 watch 和 mirror / notification",
    "RD-22 路径必须体现 live-activity、dynamic-island、island 或灵动岛",
    "RD-22 路径必须体现 switch、toggle 或开关",
    "RD-23 路径必须同时体现 widget / 小组件 和 lock-screen / 锁屏",
    "不生成健康建议、压力提醒、喂养建议或医疗判断",
    "不接入 HealthKit、传感器、医院系统或第三方健康数据源",
    "不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议",
]

REQUIRED_EVIDENCE = {
    "companyAccount": {
        "patterns": ["01-company-account.*"],
        "description": "深圳市闪现生活科技有限公司 App Store Connect 主体证据",
    },
    "mainlandAvailability": {
        "patterns": ["02-mainland-availability.*"],
        "description": "App Store Connect 只选择中国大陆可售地区",
    },
    "mainlandFiling": {
        "patterns": ["03-app-filing.*"],
        "description": "中国大陆 APP 备案或适用判断证据",
    },
    "privacyLabel": {
        "patterns": ["04-privacy-label.*"],
        "description": "App Store Connect 隐私标签截图或导出",
    },
    "signedArchive": {
        "patterns": ["05-signed-archive.*"],
        "description": "App Store Distribution Archive 成功证据",
    },
    "testFlight": {
        "patterns": ["06-testflight.*"],
        "description": "TestFlight 构建和测试状态证据",
    },
    "smsProvider": {
        "patterns": ["07-sms-provider.*"],
        "description": "真实短信签名、模板和验证码发送成功证据",
    },
    "wechatOpenPlatform": {
        "patterns": ["08-wechat-open-platform.*"],
        "description": "微信开放平台移动应用、Bundle ID、URL Scheme / Universal Link 配置证据",
    },
    "huaweiObsPolicy": {
        "patterns": ["09-obs-policy.*"],
        "description": "华为云 OBS bucket、生命周期、加密和删除验证证据",
    },
    "finalScreenshots": {
        "patterns": ["10-final-screenshots/*.png", "10-final-screenshots/*.jpg", "10-final-screenshots/*.jpeg"],
        "description": "最终 App Store 截图，不使用真实宝宝照片",
        "minFiles": 5,
        "allowedExtensions": [".png", ".jpg", ".jpeg"],
        "expectedFilenames": [
            "01-home-iphone16pro.png",
            "02-record-iphone16pro.png",
            "03-growth-iphone16pro.png",
            "04-profile-iphone16pro.png",
            "05-profile-backup-iphone16pro.png",
        ],
    },
    "reviewTestAccount": {
        "patterns": ["11-test-account-redacted.json"],
        "description": "App Review 恢复密钥测试账号脱敏证据",
        "allowedExtensions": [".json"],
    },
    "realDeviceRegression": {
        "patterns": ["12-real-device-regression.md"],
        "description": "TestFlight 或签名真机回归结果",
        "allowedExtensions": [".md"],
        "requiredCheckedItems": [
            "iOS 26.5",
            "冷启动",
            "手机号登录",
            "微信登录",
            "恢复密钥登录",
            "云备份",
            "云恢复",
            "账号删除",
            "通知权限",
            "灵动岛喝奶提醒开关",
            "灵动岛紧凑态头像和进度环未压到岛中心",
            "灵动岛展开态文字和数字未贴边或被吞",
            "锁屏通知栈上下相邻通知不遮挡提醒卡片",
            "锁屏/桌面小组件",
            "桌面小组件内容不裁剪不展示隐私照片",
            "审核边界文案",
            "Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔",
            "小组件只读展示本机今日摘要",
            "Apple Watch 只作为系统镜像通知，不在 App Store 文案中承诺 Watch App",
            "状态展示只反映用户主动记录的数据",
            "不生成健康建议、压力提醒、喂养建议或医疗判断",
            "不接入 HealthKit、传感器、医院系统或第三方健康数据源",
            "不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议",
        ],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def matching_files(root: Path, patterns: list[str], allowed_extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(
            path
            for path in root.glob(pattern)
            if path.is_file() and path.stat().st_size > 0 and path.suffix.lower() in allowed_extensions
        )
    return sorted(set(files))


def checked(text: str, label: str) -> bool:
    return any(
        line.strip().lower().startswith("- [x]") and label in line
        for line in text.splitlines()
    )


def validate_checked_items(files: list[Path], labels: list[str]) -> tuple[bool, list[str]]:
    if not files:
        return False, labels
    text = files[0].read_text(encoding="utf-8")
    missing = [label for label in labels if not checked(text, label)]
    return not missing, missing


def validate_review_test_account(files: list[Path]) -> tuple[bool, dict[str, Any]]:
    if not files:
        return False, {"missingFile": "11-test-account-redacted.json"}

    text = files[0].read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False, {"invalidJson": True}

    if not isinstance(data, dict):
        return False, {"invalidJsonObject": True}

    details: dict[str, Any] = {}
    if not data.get("accountId"):
        details["missingAccountId"] = True
    if data.get("recoveryKeyStored") != ".env.xnp-review-account":
        details["invalidRecoveryKeyStorage"] = data.get("recoveryKeyStored") or "<missing>"
    if data.get("recoveryVerified") is not True:
        details["recoveryVerified"] = data.get("recoveryVerified")
    if data.get("backupSeeded") is not True:
        details["backupSeeded"] = data.get("backupSeeded")
    if data.get("containsSecret") is not False:
        details["containsSecret"] = data.get("containsSecret")

    forbidden_fields = sorted(
        key
        for key in data
        if key != "containsSecret"
        and any(marker in str(key).lower() for marker in ("secret", "token", "password", "code"))
    )
    if forbidden_fields:
        details["forbiddenFields"] = forbidden_fields

    forbidden_hits = sorted(
        name
        for name, pattern in FORBIDDEN_REAL_DEVICE_PATTERNS.items()
        if pattern.search(text)
    )
    if forbidden_hits:
        details["forbiddenSecretMarkers"] = forbidden_hits

    return not details, details


def text_evidence_redaction_hits(files: list[Path]) -> list[str]:
    hits: list[str] = []
    for path in files:
        if path.suffix.lower() not in TEXT_EVIDENCE_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name, pattern in FORBIDDEN_REAL_DEVICE_PATTERNS.items():
            if pattern.search(text):
                hits.append(f"{path.name}:{name}")
    return sorted(hits)


def validate_generic_manual_evidence(files: list[Path], min_files: int) -> tuple[bool, dict[str, Any]]:
    large_enough = [path for path in files if path.stat().st_size >= MIN_MANUAL_EVIDENCE_BYTES]
    too_small = [
        {"file": path.name, "size": path.stat().st_size}
        for path in files
        if path.stat().st_size < MIN_MANUAL_EVIDENCE_BYTES
    ]

    details: dict[str, Any] = {
        "minimumBytes": MIN_MANUAL_EVIDENCE_BYTES,
    }
    if too_small:
        details["smallEvidenceFiles"] = too_small
    if len(large_enough) < min_files:
        details["largeEnoughFiles"] = [path.name for path in large_enough]
    return len(large_enough) >= min_files, details


def rd_case_statuses(text: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| RD-"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        match = re.search(r"\bRD-\d{2}\b", cells[0])
        if match:
            statuses[match.group(0)] = cells[1]
    return statuses


def rd_case_evidence_paths(text: str) -> dict[str, str]:
    evidence_paths: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| RD-"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        match = re.search(r"\bRD-\d{2}\b", cells[0])
        if match:
            evidence_paths[match.group(0)] = cells[2]
    return evidence_paths


def env_field_value(text: str, field: str) -> str:
    match = re.search(rf"^\s*-\s*{re.escape(field)}[：:]\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def evidence_file_details(evidence_root: Path, raw_value: str) -> dict[str, Any]:
    value = raw_value.strip().strip("`")
    if not value:
        return {"path": raw_value, "exists": False, "error": "empty"}
    if Path(value).is_absolute():
        return {"path": value, "exists": False, "error": "absolute paths are not accepted"}

    repo_root_path = evidence_root.parents[2]
    if value.startswith(str(EVIDENCE_ROOT)):
        candidate = repo_root_path / value
    else:
        candidate = evidence_root / value

    try:
        resolved_root = evidence_root.resolve()
        resolved_candidate = candidate.resolve(strict=False)
        inside_evidence_root = resolved_candidate.is_relative_to(resolved_root)
    except OSError:
        inside_evidence_root = False

    if not inside_evidence_root:
        return {"path": value, "exists": False, "error": "path must stay inside Docs/08_Release/AppStoreEvidence"}
    if candidate.suffix.lower() not in REAL_DEVICE_EVIDENCE_EXTENSIONS:
        return {"path": value, "exists": False, "error": "unsupported extension"}
    if not candidate.exists() or not candidate.is_file():
        return {"path": value, "exists": False, "error": "missing file"}
    size = candidate.stat().st_size
    if size < MIN_MANUAL_EVIDENCE_BYTES:
        return {
            "path": value,
            "exists": False,
            "error": "evidence file is too small to be reliable",
            "size": size,
            "minimumBytes": MIN_MANUAL_EVIDENCE_BYTES,
        }
    return {"path": value, "exists": True, "size": size}


def validate_real_device_regression(files: list[Path], labels: list[str]) -> tuple[bool, dict[str, Any]]:
    if not files:
        return False, {"missingCheckedItems": labels}

    text = files[0].read_text(encoding="utf-8")
    evidence_root = files[0].parent
    missing_checked_items = [label for label in labels if not checked(text, label)]
    missing_env_fields = [
        field
        for field in REQUIRED_REAL_DEVICE_ENV_FIELDS
        if not env_field_value(text, field)
    ]
    missing_visual_fields = [
        field
        for field in REQUIRED_REAL_DEVICE_VISUAL_FIELDS
        if not env_field_value(text, field)
    ]
    invalid_visual_conclusions = {
        field: env_field_value(text, field)
        for field, pattern in REQUIRED_VISUAL_CONCLUSION_PATTERNS.items()
        if env_field_value(text, field) and not pattern.search(env_field_value(text, field))
    }
    missing_rd_ids = sorted(rd_id for rd_id in REQUIRED_RD_IDS if rd_id not in text)
    rd_statuses = rd_case_statuses(text)
    rd_evidence_paths = rd_case_evidence_paths(text)
    failed_rd_statuses = {
        rd_id: status
        for rd_id, status in sorted(rd_statuses.items())
        if rd_id in REQUIRED_RD_IDS and status != "通过"
    }
    missing_rd_evidence_paths = sorted(
        rd_id
        for rd_id in REQUIRED_RD_IDS
        if not rd_evidence_paths.get(rd_id, "").strip()
    )
    invalid_rd_evidence_paths = {
        rd_id: value
        for rd_id, value in sorted(rd_evidence_paths.items())
        if rd_id in REQUIRED_RD_IDS
        and value.strip()
        and not value.lower().endswith(REAL_DEVICE_EVIDENCE_EXTENSIONS)
    }
    missing_rd_evidence_files = {
        rd_id: details
        for rd_id, details in sorted(
            (
                (rd_id, evidence_file_details(evidence_root, value))
                for rd_id, value in rd_evidence_paths.items()
                if rd_id in REQUIRED_RD_IDS and value.strip()
            ),
            key=lambda item: item[0],
        )
        if details.get("exists") is not True
    }
    visual_rd_paths = {
        rd_id: rd_evidence_paths.get(rd_id, "").strip().strip("`")
        for rd_id in REQUIRED_VISUAL_RD_PATH_PATTERNS
    }
    visual_rd_paths_present = {rd_id: value for rd_id, value in visual_rd_paths.items() if value}
    invalid_visual_rd_path_semantics = {
        rd_id: value
        for rd_id, value in sorted(visual_rd_paths_present.items())
        if not REQUIRED_VISUAL_RD_PATH_PATTERNS[rd_id].search(value)
    }
    duplicate_visual_rd_evidence_paths = sorted(
        value
        for value in set(visual_rd_paths_present.values())
        if list(visual_rd_paths_present.values()).count(value) > 1
    )
    environment_evidence = env_field_value(text, "证据截图/录屏").strip().strip("`")
    reused_environment_visual_rd_paths = {
        rd_id: value
        for rd_id, value in sorted(visual_rd_paths_present.items())
        if environment_evidence and value == environment_evidence
    }
    pending_markers = sorted(marker for marker in PENDING_REAL_DEVICE_MARKERS if marker in text)
    template_markers = sorted(marker for marker in TEMPLATE_REAL_DEVICE_MARKERS if marker in text)
    forbidden_hits = sorted(
        name
        for name, pattern in FORBIDDEN_REAL_DEVICE_PATTERNS.items()
        if pattern.search(text)
    )

    ios_value = env_field_value(text, "iOS")
    ios_265_only = ios_value == "26.5" or ios_value == "iOS 26.5"
    install_method = env_field_value(text, "安装方式")
    install_method_ok = install_method in {"TestFlight", "Xcode 签名真机包"}
    environment_evidence_details = evidence_file_details(evidence_root, environment_evidence)

    details: dict[str, Any] = {}
    if missing_checked_items:
        details["missingCheckedItems"] = missing_checked_items
    if missing_env_fields:
        details["missingEnvironmentFields"] = missing_env_fields
    if missing_visual_fields:
        details["missingVisualConclusionFields"] = missing_visual_fields
    if invalid_visual_conclusions:
        details["invalidVisualConclusions"] = invalid_visual_conclusions
    if missing_rd_ids:
        details["missingRegressionCaseIds"] = missing_rd_ids
    if failed_rd_statuses:
        details["failedRegressionCaseStatuses"] = failed_rd_statuses
    if missing_rd_evidence_paths:
        details["missingRegressionEvidencePaths"] = missing_rd_evidence_paths
    if invalid_rd_evidence_paths:
        details["invalidRegressionEvidencePaths"] = invalid_rd_evidence_paths
    if missing_rd_evidence_files:
        details["missingRegressionEvidenceFiles"] = missing_rd_evidence_files
    if invalid_visual_rd_path_semantics:
        details["invalidVisualRegressionEvidenceNames"] = invalid_visual_rd_path_semantics
    if duplicate_visual_rd_evidence_paths:
        details["duplicateVisualRegressionEvidencePaths"] = duplicate_visual_rd_evidence_paths
    if reused_environment_visual_rd_paths:
        details["reusedEnvironmentVisualRegressionEvidence"] = reused_environment_visual_rd_paths
    if pending_markers:
        details["pendingMarkers"] = pending_markers
    if template_markers:
        details["templateMarkers"] = template_markers
    if forbidden_hits:
        details["forbiddenSecretMarkers"] = forbidden_hits
    if not ios_265_only:
        details["invalidIOSVersion"] = ios_value or "<missing>"
    if not install_method_ok:
        details["invalidInstallMethod"] = install_method or "<missing>"
    if environment_evidence_details.get("exists") is not True:
        details["invalidEnvironmentEvidenceFile"] = environment_evidence_details

    return not details, details


def validate_final_screenshots_asset_proof(root: Path) -> tuple[bool, dict[str, Any]]:
    proof_path = root / APP_STORE_ASSETS_PROOF
    data = read_json(proof_path)
    checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
    failed_asset_checks = [
        name
        for name in REQUIRED_FINAL_SCREENSHOT_ASSET_CHECKS
        if not isinstance(checks.get(name), dict) or checks[name].get("passed") is not True
    ]

    details: dict[str, Any] = {
        "assetProof": str(APP_STORE_ASSETS_PROOF),
    }
    if not data:
        details["missingOrInvalidAssetProof"] = True
    if data.get("passed") is not True:
        details["assetProofPassed"] = data.get("passed")
    if failed_asset_checks:
        details["failedAssetChecks"] = failed_asset_checks

    return len(details) == 1, details


def validate_manual_evidence_checklist(root: Path) -> tuple[bool, dict[str, Any]]:
    checklist_path = root / MANUAL_EVIDENCE_CHECKLIST
    if not checklist_path.exists():
        return False, {
            "file": str(MANUAL_EVIDENCE_CHECKLIST),
            "missingFile": True,
        }

    text = checklist_path.read_text(encoding="utf-8")
    missing_markers = [
        marker
        for marker in [*MANUAL_EVIDENCE_CHECKLIST_MARKERS, *(f"RD-{index:02d}" for index in range(1, 25))]
        if marker not in text
    ]
    details: dict[str, Any] = {
        "file": str(MANUAL_EVIDENCE_CHECKLIST),
        "markersChecked": len(MANUAL_EVIDENCE_CHECKLIST_MARKERS) + 24,
    }
    if missing_markers:
        details["missingMarkers"] = missing_markers
    return not missing_markers, details


def build_report(root: Path) -> dict[str, Any]:
    evidence_root = root / EVIDENCE_ROOT
    checks: dict[str, dict[str, Any]] = {}
    checklist_passed, checklist_details = validate_manual_evidence_checklist(root)
    checks["manualEvidenceChecklist"] = {
        "passed": checklist_passed,
        "description": "人工证据清单覆盖全部 App Store / TestFlight / 真机回归证据项",
        **checklist_details,
    }
    for name, spec in REQUIRED_EVIDENCE.items():
        allowed_extensions = {
            str(extension).lower()
            for extension in spec.get("allowedExtensions", DEFAULT_ALLOWED_EXTENSIONS)
        }
        files = matching_files(evidence_root, spec["patterns"], allowed_extensions)
        min_files = int(spec.get("minFiles", 1))
        passed = len(files) >= min_files
        checks[name] = {
            "passed": passed,
            "description": spec["description"],
            "patterns": [str(EVIDENCE_ROOT / pattern) for pattern in spec["patterns"]],
            "allowedExtensions": sorted(allowed_extensions),
            "minFiles": min_files,
            "files": [str(path.relative_to(root)) for path in files],
        }
        if "requiredCheckedItems" in spec:
            checks[name]["requiredCheckedItems"] = list(spec["requiredCheckedItems"])
        if passed and name not in {"finalScreenshots", "reviewTestAccount", "realDeviceRegression"}:
            passed, manual_details = validate_generic_manual_evidence(files, min_files)
            checks[name].update(manual_details)
            checks[name]["passed"] = passed
        if name not in {"reviewTestAccount", "realDeviceRegression"}:
            redaction_hits = text_evidence_redaction_hits(files)
            if redaction_hits:
                checks[name]["forbiddenTextEvidenceMarkers"] = redaction_hits
                checks[name]["passed"] = False
                passed = False
        expected_filenames = [str(filename) for filename in spec.get("expectedFilenames", [])]
        if expected_filenames:
            file_names = {path.name for path in files}
            missing_expected = [filename for filename in expected_filenames if filename not in file_names]
            if missing_expected:
                checks[name]["missingExpectedFilenames"] = missing_expected
                checks[name]["passed"] = False
                passed = False
        if passed and name == "finalScreenshots":
            passed, final_screenshot_details = validate_final_screenshots_asset_proof(root)
            checks[name].update(final_screenshot_details)
            checks[name]["passed"] = passed
            continue
        if passed and name == "reviewTestAccount":
            passed, review_account_details = validate_review_test_account(files)
            checks[name].update(review_account_details)
            checks[name]["passed"] = passed
            continue
        missing_checked_items: list[str] = []
        if passed and "requiredCheckedItems" in spec:
            if name == "realDeviceRegression":
                passed, real_device_details = validate_real_device_regression(files, list(spec["requiredCheckedItems"]))
                checks[name].update(real_device_details)
            else:
                passed, missing_checked_items = validate_checked_items(files, list(spec["requiredCheckedItems"]))
                if missing_checked_items:
                    checks[name]["missingCheckedItems"] = missing_checked_items
            checks[name]["passed"] = passed
            continue

    missing = [name for name, check in checks.items() if not check["passed"]]
    return {
        "startedAt": utc_now(),
        "completedAt": utc_now(),
        "ready": not missing,
        "missingEvidence": missing,
        "evidenceRoot": str(EVIDENCE_ROOT),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output", default="Backend/proof/app-store-evidence.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    result = build_report(root)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["ready"]:
        print(f"App Store evidence passed: {output_path}")
        return

    missing = ", ".join(result["missingEvidence"])
    print(f"App Store evidence incomplete: {output_path}", file=sys.stderr)
    print(f"missing evidence: {missing}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
