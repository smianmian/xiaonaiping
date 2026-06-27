#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_APP_NAME = "小奶瓶"
EXPECTED_BUNDLE_ID = "com.mewpow.xiaonaiping"
EXPECTED_SUBTITLE = "温柔记录宝宝每一天"
EXPECTED_PRIVACY_URL = "https://api.mewpow.com/xiaonaiping/privacy"
EXPECTED_SUPPORT_URL = "https://api.mewpow.com/xiaonaiping/support"
EXPECTED_TERMS_URL = "https://api.mewpow.com/xiaonaiping/terms"
EXPECTED_KEYWORDS = {"宝宝记录", "育儿", "喂奶", "睡眠", "尿布", "成长记录", "疫苗提醒", "相册"}
EXPECTED_PRIVACY_CATEGORY_REQUIREMENTS = {
    "Identifiers": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "Contact Info": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "User Content": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "Photos or Videos": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "Health and Fitness": {
        "linkedToUser": True,
        "purposes": {"App Functionality"},
    },
    "Usage Data": {
        "linkedToUser": True,
        "purposes": {"Analytics"},
    },
    "Diagnostics": {
        "linkedToUser": False,
        "purposes": {"App Functionality", "Analytics"},
    },
}
EXPECTED_PRIVACY_CATEGORIES = set(EXPECTED_PRIVACY_CATEGORY_REQUIREMENTS)
EXPECTED_APP_PRIVACY_FLAGS = {
    "targetsChildrenDirectly": False,
    "containsThirdPartyAdvertising": False,
    "containsThirdPartyAnalytics": False,
    "usesTracking": False,
}
USAGE_DATA_BOUNDARY_MARKERS = (
    "no baby content",
    "photos",
    "phone numbers",
    "wechat identifiers",
    "advertising id",
    "device fingerprint",
)
HEALTH_DATA_BOUNDARY_MARKERS = (
    "user-entered",
    "no healthkit",
    "sensors",
    "hospital records",
    "stress detection",
    "medical interpretation",
    "health advice",
    "pressure reminders",
    "feeding advice",
    "medical diagnosis",
    "status display only",
)
EXPECTED_SCREENSHOTS = {
    "01-home-iphone16pro.png": "记录宝宝今天的小变化",
    "02-record-iphone16pro.png": "半夜也能低负担记录",
    "03-growth-iphone16pro.png": "一个月的成长，轻轻回看",
    "04-profile-iphone16pro.png": "设置、隐私和资料都在这里",
    "05-profile-backup-iphone16pro.png": "主动备份，也能主动删除",
}
SCREENSHOT_COPY_FORBIDDEN_MARKERS = (
    "健康建议",
    "喂养推荐",
    "医疗判断",
    "医疗诊断",
    "治疗建议",
    "压力提醒",
    "压力评估",
    "心理健康判断",
    "微信登录成功",
    "微信登录可用",
)
SCREENSHOT_BOUNDARY_MARKERS = (
    "不使用真实宝宝照片",
    "不展示真实手机号",
    "恢复密钥",
    "token",
    "对象存储 key",
    "不展示 `127.0.0.1`",
    "debug code",
    "internal dashboard",
    "不写医疗诊断",
    "治疗",
    "疫苗建议",
    "医生替代",
    "专业健康结论",
    "微信登录未完成开放平台配置前",
    "不截图暗示微信登录已经可用",
)
IN_APP_COMPANION_COPY_FILES = (
    "App/iOS/XiaoNaiPing/Views/FeedingRecordView.swift",
    "App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/Localizable.strings",
)
COMPANION_COPY_TRIGGER_MARKERS = (
    "Apple Watch",
    "Watch App",
    "watchOS",
    "手表",
    "手錶",
)
COMPANION_COPY_SAFE_MARKERS = (
    "系统通知",
    "系統通知",
    "镜像通知",
    "鏡像通知",
    "跟随系统通知",
    "跟隨系統通知",
    "不在 App Store 文案",
    "不承诺",
    "不宣称",
)
DISALLOWED_CATEGORY_ALTERNATIVES = {
    "生活 / 健康健美",
    "健康健美，正式提交前二选一",
    "Lifestyle or Health & Fitness",
    "choose one before submission",
    "如選健康健美",
}
EXTERNAL_AUTH_BOUNDARY_MARKERS = (
    "手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充",
    "微信 provider 未配置",
    "缺真实微信 Release build setting",
    "缺真实 `wx...` URL Scheme",
    "缺人工证据和 iOS 26.5 真机回归记录",
)
REVIEW_ACCOUNT_BOUNDARY_MARKERS = (
    "App Review Information",
    "恢复密钥测试账号",
    "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
    "Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md",
    ".env.xnp-review-account",
    "不得写入 App Store Connect 文案、审核备注、截图或仓库文档",
    "手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充",
)
FORBIDDEN_REVIEW_ACCOUNT_SECRET_PATTERNS = {
    "recoveryKeyAssignment": re.compile(r"XNP_REVIEW_RECOVERY_KEY\s*="),
    "bearerToken": re.compile(r"Bearer\s+[A-Za-z0-9._-]+"),
    "debugWeChatCode": re.compile(r"debug_wechat_[A-Za-z0-9_:-]+"),
    "apiKey": re.compile(r"sk-[A-Za-z0-9]{12,}"),
    "mainlandPhoneNumber": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "chinaPhoneNumber": re.compile(r"\+86\s?1[3-9]\d{9}"),
}
EXPECTED_SCREENSHOT_PLAN_MARKERS = (
    "-sdk iphonesimulator26.5",
    "OS=26.5",
    "XiaoNaiPing-DebugScreenshots-26_5",
    "capture_ios_screenshots.py",
    "--tabs home record growth profile profile-backup",
    "TestFlight 或签名真机包最终截图",
)
KEYWORDS_MAX_BYTES = 100
PROMOTIONAL_TEXT_MAX_CHARS = 170
LONG_TEXT_MAX_CHARS = 4000
FILL_SHEET_PATTERN = "APP_STORE_CONNECT_FILL_SHEET_*.md"
FALLBACK_FILL_SHEET = "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md"


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


def latest_fill_sheet(root: Path) -> str:
    release_dir = root / "Docs/08_Release"
    candidates = sorted(release_dir.glob(FILL_SHEET_PATTERN))
    if not candidates:
        return FALLBACK_FILL_SHEET
    return str(candidates[-1].relative_to(root))


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def extract_first_code_block(section: str) -> str:
    match = re.search(r"```(?:text)?\s*(.*?)\s*```", section, re.DOTALL)
    return match.group(1).strip() if match else ""


def utf8_bytes(value: str) -> int:
    return len(value.encode("utf-8"))


def screenshot_copy_rows(section: str) -> str:
    rows = [
        line
        for line in section.splitlines()
        if re.match(r"^\|\s*[1-9][0-9]*\s*\|", line.strip())
    ]
    return "\n".join(rows)


def forbidden_review_account_secret_hits(text: str) -> list[str]:
    return sorted(
        name
        for name, pattern in FORBIDDEN_REVIEW_ACCOUNT_SECRET_PATTERNS.items()
        if pattern.search(text)
    )


def in_app_companion_copy_findings(root: Path) -> dict[str, list[str]]:
    missing_files: list[str] = []
    bounded_mentions: list[str] = []
    risky_mentions: list[str] = []
    for relative_path in IN_APP_COMPANION_COPY_FILES:
        text = read_text(root / relative_path)
        if not text:
            missing_files.append(relative_path)
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not any(marker in line for marker in COMPANION_COPY_TRIGGER_MARKERS):
                continue
            finding = f"{relative_path}:{line_number}:{line.strip()}"
            if any(marker in line for marker in COMPANION_COPY_SAFE_MARKERS):
                bounded_mentions.append(finding)
            else:
                risky_mentions.append(finding)

    return {
        "missingFiles": missing_files,
        "boundedMentions": bounded_mentions,
        "riskyMentions": risky_mentions,
    }


def privacy_label_failures(privacy_label: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    privacy_app = privacy_label.get("app", {})
    if not isinstance(privacy_app, dict):
        failures.append("app must be an object")
        privacy_app = {}

    for key, expected in EXPECTED_APP_PRIVACY_FLAGS.items():
        if privacy_app.get(key) is not expected:
            failures.append(f"app.{key} must be {str(expected).lower()}")

    categories = privacy_label.get("dataCategories", [])
    if not isinstance(categories, list):
        return failures + ["dataCategories must be an array"]

    categories_by_name: dict[str, dict[str, Any]] = {}
    for item in categories:
        if not isinstance(item, dict):
            failures.append("dataCategories entry must be an object")
            continue
        category = item.get("category")
        if not isinstance(category, str) or not category:
            failures.append("dataCategories entry missing category")
            continue
        if category in categories_by_name:
            failures.append(f"{category} is duplicated")
        categories_by_name[category] = item
        if item.get("usedForTracking") is not False:
            failures.append(f"{category}.usedForTracking must be false")

    missing_categories = sorted(EXPECTED_PRIVACY_CATEGORIES - set(categories_by_name))
    if missing_categories:
        failures.append("missing categories: " + ", ".join(missing_categories))

    unexpected_collected = sorted(
        category
        for category, item in categories_by_name.items()
        if category not in EXPECTED_PRIVACY_CATEGORIES and item.get("collected") is True
    )
    if unexpected_collected:
        failures.append("unexpected collected categories: " + ", ".join(unexpected_collected))

    for category, expected in EXPECTED_PRIVACY_CATEGORY_REQUIREMENTS.items():
        item = categories_by_name.get(category)
        if not item:
            continue
        if item.get("collected") is not True:
            failures.append(f"{category}.collected must be true")
        if item.get("linkedToUser") is not expected["linkedToUser"]:
            failures.append(f"{category}.linkedToUser must be {str(expected['linkedToUser']).lower()}")
        purposes = item.get("purposes")
        if not isinstance(purposes, list):
            failures.append(f"{category}.purposes must be an array")
            continue
        missing_purposes = sorted(expected["purposes"] - {str(purpose) for purpose in purposes})
        if missing_purposes:
            failures.append(f"{category}.purposes missing: " + ", ".join(missing_purposes))

    usage_data = categories_by_name.get("Usage Data")
    usage_text = json.dumps(usage_data, ensure_ascii=False).lower() if usage_data else ""
    missing_usage_boundaries = [
        marker for marker in USAGE_DATA_BOUNDARY_MARKERS
        if marker not in usage_text
    ]
    if missing_usage_boundaries:
        failures.append("Usage Data boundary missing: " + ", ".join(missing_usage_boundaries))

    health_data = categories_by_name.get("Health and Fitness")
    health_text = json.dumps(health_data, ensure_ascii=False).lower() if health_data else ""
    missing_health_boundaries = [
        marker for marker in HEALTH_DATA_BOUNDARY_MARKERS
        if marker not in health_text
    ]
    if missing_health_boundaries:
        failures.append("Health and Fitness boundary missing: " + ", ".join(missing_health_boundaries))

    return failures


def fetch_public_url(url: str) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "XiaoNaiPingReleaseGate/1.0"})
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return {
                "ok": 200 <= int(response.status) < 300,
                "status": int(response.status),
                "contentType": response.headers.get("content-type", ""),
                "hasCompany": "深圳市闪现生活科技有限公司" in body,
                "hasProduct": EXPECTED_APP_NAME in body,
                "length": len(body),
            }
    except (urllib.error.URLError, TimeoutError) as error:
        return {"ok": False, "error": str(error)}


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
    fill_sheet_path = root / fill_sheet_arg
    metadata_path = root / args.metadata
    privacy_label_path = root / args.privacy_label
    screenshot_plan_path = root / args.screenshot_plan
    fill_sheet = read_text(fill_sheet_path)
    metadata = read_text(metadata_path)
    privacy_label = read_json(privacy_label_path)
    screenshot_plan = read_text(screenshot_plan_path)
    report = Report()

    report.add("fillSheetPresent", bool(fill_sheet), str(fill_sheet_path) if fill_sheet else "missing fill sheet")
    report.add("metadataPresent", bool(metadata), str(metadata_path) if metadata else "missing metadata doc")
    report.add("privacyLabelPresent", bool(privacy_label), str(privacy_label_path) if privacy_label else "missing privacy label JSON")
    report.add("screenshotPlanPresent", bool(screenshot_plan), str(screenshot_plan_path) if screenshot_plan else "missing screenshot plan")
    legacy_blocking_proofs = [
        "Backend/proof/production-readiness.json",
        "Backend/proof/auth-providers.json",
        "Backend/proof/ios-app-bundle.json",
        "Backend/proof/app-store-evidence.json",
    ]
    stale_proof_refs = sorted(proof for proof in legacy_blocking_proofs if proof in fill_sheet)
    required_latest_proofs = [
        "Backend/proof/production-readiness-20260627T-current.json",
        "Backend/proof/auth-providers-20260627T-current.json",
        "Backend/proof/ios-release-readiness.json",
        "Backend/proof/ios-app-bundle-20260627T-current-ios265.json",
        "Backend/proof/app-store-evidence-20260627T-current.json",
    ]
    missing_latest_proofs = [proof for proof in required_latest_proofs if proof not in fill_sheet]
    report.add(
        "blockingProofReferencesUseLatestSnapshots",
        not stale_proof_refs and not missing_latest_proofs,
        "staleRefs="
        + ", ".join(stale_proof_refs)
        + "; missingLatest="
        + ", ".join(missing_latest_proofs)
        if stale_proof_refs or missing_latest_proofs
        else "blocking proof references use latest snapshot filenames",
    )
    combined_materials = fill_sheet + "\n" + metadata
    missing_external_auth_boundaries = [
        marker for marker in EXTERNAL_AUTH_BOUNDARY_MARKERS if marker not in combined_materials
    ]
    report.add(
        "externalAuthSubmissionBoundaryPresent",
        not missing_external_auth_boundaries,
        "missing: " + ", ".join(missing_external_auth_boundaries)
        if missing_external_auth_boundaries
        else "materials clearly separate draft login copy from pending SMS/WeChat provider and iOS bundle evidence",
    )

    report.add("appNameMatches", f"| App 名称 | {EXPECTED_APP_NAME} |" in fill_sheet, EXPECTED_APP_NAME)
    report.add("bundleIdentifierMatches", EXPECTED_BUNDLE_ID in fill_sheet and EXPECTED_BUNDLE_ID in metadata, EXPECTED_BUNDLE_ID)
    report.add("subtitleWithinLimit", EXPECTED_SUBTITLE in fill_sheet and len(EXPECTED_SUBTITLE) <= 30, EXPECTED_SUBTITLE)
    report.add("skuPresent", "`xiaonaiping-ios-1`" in fill_sheet, "SKU xiaonaiping-ios-1")
    report.add("primaryCategoryLifestyle", "| 主类别 | 生活 |" in fill_sheet or "| Category | Lifestyle |" in metadata, "primary category Lifestyle/生活")
    report.add("secondaryCategoryBlank", "| 第二类别 | 留空" in fill_sheet, "second category is blank in fill sheet")

    category_hits = sorted(marker for marker in DISALLOWED_CATEGORY_ALTERNATIVES if marker in fill_sheet or marker in metadata)
    report.add(
        "metadataNoHealthFitnessCategoryAlternative",
        not category_hits,
        "found: " + ", ".join(category_hits) if category_hits else "metadata does not suggest Health & Fitness as an alternate category",
    )

    report.add("firstReleaseMainland", "China mainland" in fill_sheet and "Specific Countries or Regions" in fill_sheet, "China mainland first")
    report.add("secondReleaseHongKong", "Hong Kong" in fill_sheet, "Hong Kong second")
    report.add("priceFree", "| 价格 | 免费 |" in fill_sheet or "| Price | Free |" in metadata, "free V1")
    report.add("copyrightCompany", "深圳市闪现生活科技有限公司" in fill_sheet, "company copyright present")

    public_urls_ok = all(url in fill_sheet and url in metadata for url in [EXPECTED_PRIVACY_URL, EXPECTED_SUPPORT_URL, EXPECTED_TERMS_URL])
    label_urls_ok = privacy_label.get("privacyPolicyUrl") == EXPECTED_PRIVACY_URL and privacy_label.get("supportUrl") == EXPECTED_SUPPORT_URL
    report.add(
        "publicUrlsMatch",
        public_urls_ok and label_urls_ok,
        "privacy/support/terms URLs match fill sheet, metadata, and privacy label"
        if public_urls_ok and label_urls_ok
        else "URL mismatch in fill sheet, metadata, or privacy label",
    )

    expected_public_urls = [EXPECTED_PRIVACY_URL, EXPECTED_SUPPORT_URL, EXPECTED_TERMS_URL]
    public_url_results = {url: fetch_public_url(url) for url in expected_public_urls}
    public_url_failures = [
        f"{url}: {result}"
        for url, result in public_url_results.items()
        if not (result.get("ok") and result.get("hasCompany") and result.get("hasProduct"))
    ]
    report.add(
        "publicUrlsReachable",
        not public_url_failures,
        "privacy/support/terms URLs return 2xx and contain company/product markers"
        if not public_url_failures
        else "; ".join(public_url_failures),
    )

    keywords = extract_first_code_block(extract_section(fill_sheet, "关键词"))
    keyword_set = {item.strip() for item in keywords.split(",") if item.strip()}
    missing_keywords = sorted(EXPECTED_KEYWORDS - keyword_set)
    keyword_bytes = utf8_bytes(keywords)
    report.add(
        "keywordsCompleteAndWithinLimit",
        bool(keywords) and not missing_keywords and keyword_bytes <= KEYWORDS_MAX_BYTES,
        f"chars={len(keywords)}, bytes={keyword_bytes}, missing={missing_keywords}",
    )

    promo = extract_first_code_block(extract_section(fill_sheet, "宣传文本"))
    report.add(
        "promotionalTextWithinLimit",
        bool(promo) and len(promo) <= PROMOTIONAL_TEXT_MAX_CHARS,
        f"len={len(promo)}",
    )

    release_notes = extract_first_code_block(extract_section(fill_sheet, "新版本说明"))
    release_notes_markers = ["第一版", "宝宝档案", "日常记录", "成长记录", "疫苗提醒", "照片时间线", "账号备份恢复", "云端账号删除"]
    missing_release_notes_markers = [marker for marker in release_notes_markers if marker not in release_notes]
    report.add(
        "releaseNotesCompleteAndWithinLimit",
        bool(release_notes) and len(release_notes) <= LONG_TEXT_MAX_CHARS and not missing_release_notes_markers,
        f"len={len(release_notes)}, missing={missing_release_notes_markers}",
    )

    description = extract_first_code_block(extract_section(fill_sheet, "描述"))
    description_markers = ["本地优先", "恢复密钥", "手机号", "微信", "照片原图", "不提供医疗诊断", "疫苗模板仅用于记录和提醒"]
    missing_description_markers = [marker for marker in description_markers if marker not in description]
    report.add(
        "descriptionCompleteAndWithinLimit",
        bool(description) and len(description) <= LONG_TEXT_MAX_CHARS and not missing_description_markers,
        f"len={len(description)}, missing={missing_description_markers}",
    )

    age_section = extract_section(fill_sheet, "年龄分级建议")
    age_markers = ["4+", "不选择 Kids 类目", "不面向儿童直接使用", "不接入 HealthKit", "不提供压力评估"]
    missing_age_markers = [marker for marker in age_markers if marker not in age_section]
    report.add(
        "ageRatingBoundaryPresent",
        not missing_age_markers,
        "missing: " + ", ".join(missing_age_markers) if missing_age_markers else "4+ / not Kids / non-medical boundaries present",
    )

    privacy_app = privacy_label.get("app", {}) if isinstance(privacy_label.get("app", {}), dict) else {}
    privacy_failures = privacy_label_failures(privacy_label)
    report.add(
        "privacyLabelMatchesAppStoreDraft",
        privacy_app.get("name") == EXPECTED_APP_NAME
        and privacy_app.get("bundleId") == EXPECTED_BUNDLE_ID
        and not privacy_failures,
        "; ".join(privacy_failures) if privacy_failures else "privacy label categories, purposes, linking, tracking, and app flags match draft",
    )

    screenshot_section = extract_section(fill_sheet, "截图文案")
    screenshot_rows = screenshot_copy_rows(screenshot_section)
    missing_screenshots = [
        f"{filename} / {title}"
        for filename, title in EXPECTED_SCREENSHOTS.items()
        if filename not in fill_sheet or title not in fill_sheet
    ]
    report.add(
        "screenshotCopyComplete",
        not missing_screenshots,
        "missing: " + "; ".join(missing_screenshots) if missing_screenshots else "5 screenshot filenames and titles present",
    )
    screenshot_copy_forbidden_hits = [
        marker for marker in SCREENSHOT_COPY_FORBIDDEN_MARKERS if marker in screenshot_rows
    ]
    missing_screenshot_boundary_markers = [
        marker for marker in SCREENSHOT_BOUNDARY_MARKERS if marker not in screenshot_section
    ]
    report.add(
        "screenshotCopyAvoidsUnavailableOrMedicalClaims",
        bool(screenshot_rows) and not screenshot_copy_forbidden_hits and not missing_screenshot_boundary_markers,
        "forbiddenInRows="
        + ", ".join(screenshot_copy_forbidden_hits)
        + "; missingBoundary="
        + ", ".join(missing_screenshot_boundary_markers)
        if screenshot_copy_forbidden_hits or missing_screenshot_boundary_markers
        else "screenshot table avoids unavailable WeChat success claims and medical/health advice claims; screenshot boundaries are present",
    )

    missing_screenshot_plan_markers = [
        marker for marker in EXPECTED_SCREENSHOT_PLAN_MARKERS if marker not in screenshot_plan
    ]
    disallowed_screenshot_runtime_markers = sorted(
        set(
            re.findall(r"OS=(?!26\.5\b)[0-9][0-9.]*", screenshot_plan)
            + re.findall(r"-sdk iphone(?:simulator|os)(?!26\.5\b)[0-9.]*", screenshot_plan)
            + re.findall(r"Runtime:\s+iOS\s+(?!26\.5\b)[0-9][0-9.]*", screenshot_plan)
        )
    )
    report.add(
        "screenshotPlanUsesIOS265Only",
        bool(screenshot_plan)
        and not missing_screenshot_plan_markers
        and not disallowed_screenshot_runtime_markers,
        "missing: "
        + ", ".join(missing_screenshot_plan_markers)
        + "; disallowedRuntimeMarkers: "
        + ", ".join(disallowed_screenshot_runtime_markers)
        if missing_screenshot_plan_markers or disallowed_screenshot_runtime_markers
        else "screenshot capture plan uses iOS 26.5 simulator commands and keeps final TestFlight/signed-build screenshots separate",
    )

    companion_copy = in_app_companion_copy_findings(root)
    report.add(
        "inAppCompanionCopyBounded",
        not companion_copy["missingFiles"]
        and not companion_copy["riskyMentions"]
        and bool(companion_copy["boundedMentions"]),
        "missingFiles="
        + ", ".join(companion_copy["missingFiles"])
        + "; riskyMentions="
        + " | ".join(companion_copy["riskyMentions"])
        + "; boundedMentions="
        + " | ".join(companion_copy["boundedMentions"])
        if companion_copy["missingFiles"] or companion_copy["riskyMentions"]
        else "Apple Watch mentions in app UI are bounded to system notification mirroring, not Watch App or watchOS support",
    )

    review_text = extract_first_code_block(extract_section(fill_sheet, "审核备注可粘贴文本"))
    review_markers = [
        "Live Activity",
        "小组件",
        "状态展示",
        "用户在 App 内输入",
        "不生成健康建议、压力提醒、喂养建议",
        "不接入 HealthKit",
        "不提供压力评估",
        "不是医疗器械",
        "debug code",
    ]
    missing_review_markers = [marker for marker in review_markers if marker not in review_text]
    report.add(
        "reviewNotesPasteTextHasBoundary",
        not missing_review_markers,
        "missing: " + ", ".join(missing_review_markers) if missing_review_markers else "review paste text has Live Activity/widget/source/health boundaries",
    )

    vaccine_boundary_markers = [
        "疫苗模板仅用于记录和提醒",
        "实际接种安排请以医生和当地官方信息为准",
        "不构成医疗建议",
        "不作为医疗建议",
        "不替代医生建议",
    ]
    vaccine_boundary_text = fill_sheet + "\n" + metadata + "\n" + screenshot_plan
    missing_vaccine_boundary_markers = [
        marker for marker in vaccine_boundary_markers if marker not in vaccine_boundary_text
    ]
    report.add(
        "vaccineBoundarySpecific",
        not missing_vaccine_boundary_markers,
        "missing: " + ", ".join(missing_vaccine_boundary_markers)
        if missing_vaccine_boundary_markers
        else "vaccine copy is bounded as records/reminders and points users to doctors/local official information",
    )

    companion_surface_markers = [
        "灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒",
        "固定间隔",
        "宝宝昵称/头像缩略图",
        "桌面/锁屏小组件只读展示今日摘要",
        "这些状态展示只反映用户主动记录的数据",
        "不生成健康建议、压力提醒、喂养建议或医疗判断",
        "不接入 HealthKit、传感器、医院系统或第三方健康数据源",
        "不提供压力评估、心理健康判断或医疗诊断",
    ]
    companion_surface_text = fill_sheet + "\n" + metadata
    missing_companion_surface_markers = [
        marker for marker in companion_surface_markers if marker not in companion_surface_text
    ]
    report.add(
        "liveActivityWidgetBoundarySpecific",
        not missing_companion_surface_markers,
        "missing: " + ", ".join(missing_companion_surface_markers)
        if missing_companion_surface_markers
        else "Live Activity and widget copy is bounded to feeding reminder / local summary, not health advice or medical judgment",
    )

    screenshot_companion_boundary_markers = [
        "当前 5 张候选图不展示灵动岛/锁屏 Live Activity 或小组件",
        "不得写成健康建议、喂养推荐或医疗判断",
        "正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图",
    ]
    missing_screenshot_companion_boundary_markers = [
        marker for marker in screenshot_companion_boundary_markers if marker not in fill_sheet + "\n" + screenshot_plan
    ]
    report.add(
        "screenshotCompanionSurfaceBoundarySpecific",
        not missing_screenshot_companion_boundary_markers,
        "missing: " + ", ".join(missing_screenshot_companion_boundary_markers)
        if missing_screenshot_companion_boundary_markers
        else "screenshot plan does not imply unverified Live Activity/widget success and keeps iOS 26.5 final proof separate",
    )

    review_account_section = extract_section(fill_sheet, "审核测试账号填写说明")
    missing_review_account_markers = [
        marker for marker in REVIEW_ACCOUNT_BOUNDARY_MARKERS if marker not in review_account_section
    ]
    review_account_secret_hits = forbidden_review_account_secret_hits(fill_sheet)
    report.add(
        "reviewAccountInstructionsRedacted",
        bool(review_account_section) and not missing_review_account_markers and not review_account_secret_hits,
        "missing: "
        + ", ".join(missing_review_account_markers)
        + "; secretHits: "
        + ", ".join(review_account_secret_hits)
        if missing_review_account_markers or review_account_secret_hits
        else "review account instructions point to redacted evidence and keep recovery key only in ignored local storage / App Review Information",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--fill-sheet")
    parser.add_argument("--metadata", default="Docs/08_Release/APP_STORE_METADATA.md")
    parser.add_argument("--privacy-label", default="Docs/08_Release/APP_STORE_PRIVACY_LABEL.json")
    parser.add_argument("--screenshot-plan", default="Docs/08_Release/SCREENSHOT_PLAN.md")
    parser.add_argument("--output", default="Backend/proof/app-store-connect-materials.json")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"App Store Connect materials passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"App Store Connect materials incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
