#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PLACEHOLDER_HOSTS = (
    "api.example.com",
    "example.com",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
)
LOCAL_PROOF_TIMEZONE = timezone(timedelta(hours=8))
DEFAULT_DEPLOYMENT_PROOF = "Backend/proof/huawei-baota-deploy.json"
DEFAULT_STORAGE_PROOF = "Backend/proof/storage-backend.json"

XNP_NAMESPACE_MARKERS = ("xiaonaiping", "xnp")
WECHAT_APP_ID_RE = re.compile(r"^wx[a-f0-9]{16}$")
WECHAT_SAMPLE_APP_ID_BODIES = {
    "0123456789abcdef",
    "1234567890abcdef",
    "abcdef1234567890",
    "fedcba9876543210",
}

FORBIDDEN_SHARED_SERVICE_MARKERS = (
    "emotion",
    "emotion-isle",
    "emotion_isle",
    "yidaimao",
    "yi-gen-dai-mao",
    "daimao",
    "ydm",
    "一根呆毛",
    "情绪",
)

ISOLATION_ENV_NAMES = (
    "XNP_DATA_DIR",
    "XNP_MYSQL_HOST",
    "XNP_MYSQL_USER",
    "XNP_MYSQL_DATABASE",
    "HUAWEI_OBS_ENDPOINT",
    "HUAWEI_OBS_BUCKET",
    "HUAWEI_OBS_PREFIX",
    "XNP_SMS_WEBHOOK_URL",
)

REQUIRED_DOCS = {
    "privacyReview": "Docs/07_PrivacySecurity/PRIVACY_REVIEW.md",
    "sdkInventory": "Docs/07_PrivacySecurity/SDK_DATA_INVENTORY.md",
    "testPlan": "Docs/05_QA/TEST_PLAN.md",
    "releaseChecklist": "Docs/06_Release/RELEASE_CHECKLIST.md",
    "proofPack": "Docs/06_Release/PROOF_PACK.md",
    "regionalStrategy": "Docs/08_Release/REGIONAL_LAUNCH_STRATEGY.md",
    "appStoreMetadata": "Docs/08_Release/APP_STORE_METADATA.md",
    "appStorePrivacyLabel": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
    "appStoreSubmissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
    "mainlandFilingMaterials": "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
    "privacyPolicyDraft": "Docs/08_Release/PRIVACY_POLICY_DRAFT.md",
    "termsDraft": "Docs/08_Release/TERMS_OF_USE_DRAFT.md",
    "screenshotPlan": "Docs/08_Release/SCREENSHOT_PLAN.md",
    "rollbackPlan": "Docs/06_Release/ROLLBACK_PLAN.md",
}

STATIC_PAGE_MARKERS = {
    "/privacy": "小奶瓶隐私政策",
    "/terms": "小奶瓶用户协议",
    "/support": "小奶瓶支持",
}

ACCEPTED_IPHONE_SCREENSHOT_SIZES = {
    (1260, 2736),
    (2736, 1260),
    (1290, 2796),
    (2796, 1290),
    (1320, 2868),
    (2868, 1320),
    (1284, 2778),
    (2778, 1284),
    (1242, 2688),
    (2688, 1242),
    (1179, 2556),
    (2556, 1179),
    (1206, 2622),
    (2622, 1206),
    (1170, 2532),
    (2532, 1170),
    (1125, 2436),
    (2436, 1125),
    (1080, 2340),
    (2340, 1080),
    (1242, 2208),
    (2208, 1242),
    (750, 1334),
    (1334, 750),
    (640, 1096),
    (640, 1136),
    (1136, 600),
    (1136, 640),
    (640, 920),
    (640, 960),
    (960, 600),
    (960, 640),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def expected_proof_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def timestamp_matches_date(value: Any, expected_date: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value.startswith(expected_date)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return expected_date in {
        parsed.astimezone(timezone.utc).date().isoformat(),
        parsed.astimezone(LOCAL_PROOF_TIMEZONE).date().isoformat(),
    }


def proof_has_current_timestamp(data: dict[str, Any], expected_date: str) -> tuple[bool, str]:
    for key in ("startedAt", "completedAt", "checkedAt", "verifiedAt"):
        if timestamp_matches_date(data.get(key), expected_date):
            return True, f"{key}={data.get(key)}"
    return False, "missing current timestamp in startedAt, completedAt, checkedAt"


def current_dated_proof_path(root: Path, explicit_path: str, default_path: str, proof_stem: str, expected_date: str) -> str:
    if explicit_path:
        return explicit_path
    compact_date = expected_date.replace("-", "")
    current_path = f"Backend/proof/{proof_stem}-{compact_date}T-current.json"
    if (root / current_path).is_file():
        return current_path
    return default_path


def configured_wechat_app_id(value: str) -> bool:
    value = value.strip()
    if not value or not WECHAT_APP_ID_RE.fullmatch(value):
        return False
    body = value[2:].lower()
    return body not in WECHAT_SAMPLE_APP_ID_BODIES and len(set(body)) > 1


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def latest_sim_launch_proof(root: Path) -> Path:
    candidates = sorted((root / "Backend/proof").glob("sim-launch-ios265-*.json"))
    if candidates:
        return candidates[-1]
    return root / "Backend/proof/sim-launch-ios265-20260626.json"


def parse_release_api_base_url(project_yml: Path) -> str:
    text = read_text(project_yml)
    lines = text.splitlines()
    in_release = False
    release_indent = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if re.fullmatch(r"Release:\s*", stripped):
            in_release = True
            release_indent = indent
            continue
        if in_release and indent <= release_indent:
            break
        if in_release:
            match = re.search(r'XNP_API_BASE_URL:\s*"?([^"]*)"?\s*$', line)
            if match:
                return match.group(1).strip()
    return ""


def is_placeholder_url(value: str) -> bool:
    lower = value.lower()
    return any(host in lower for host in PLACEHOLDER_HOSTS)


def has_xnp_namespace(value: str) -> bool:
    lower = value.lower()
    return any(marker in lower for marker in XNP_NAMESPACE_MARKERS)


def forbidden_marker(value: str) -> str:
    lower = value.lower()
    for marker in FORBIDDEN_SHARED_SERVICE_MARKERS:
        if marker.lower() in lower:
            return marker
    return ""


def proof_passed(path: Path, require_https: bool = False) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    checks = data.get("checks")
    failed_checks = data.get("failedChecks")
    api_base_url = data.get("apiBaseUrl", "")
    if require_https and not str(api_base_url).startswith("https://"):
        return False, f"proof apiBaseUrl is not https: {api_base_url}"
    if require_https and is_placeholder_url(str(api_base_url)):
        return False, f"proof apiBaseUrl is placeholder: {api_base_url}"
    if data.get("passed") is not True:
        return False, f"proof passed=false, failedChecks={failed_checks}"
    if not isinstance(checks, dict) or not checks:
        return False, "proof has no checks"
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        return False, "failed checks: " + ", ".join(failed)
    return True, f"passed {len(checks)} checks"


def shared_service_hits(effective_base_url: str, deployment_values: dict[str, str] | None = None) -> list[str]:
    values = {"effectiveApiBaseUrl": effective_base_url}
    for name in ISOLATION_ENV_NAMES:
        values[name] = os.environ.get(name, "")
    if deployment_values:
        values.update(
            {
                f"deploymentProof.{name}": value
                for name, value in deployment_values.items()
                if not name.startswith("__")
            }
        )

    hits = []
    for name, value in values.items():
        marker = forbidden_marker(value)
        if marker:
            hits.append(f"{name} contains {marker}")
    return hits


def namespace_failures(require_huawei_obs: bool, deployment_values: dict[str, str] | None = None) -> list[str]:
    deployment_values = deployment_values or {}
    provider_checks = deployment_values.get("__providerChecks", {})
    obs_bucket_has_namespace = isinstance(provider_checks, dict) and provider_checks.get("obsBucketHasXiaoNaiPingNamespace") is True
    required_values = {
        "XNP_DATA_DIR": os.environ.get("XNP_DATA_DIR", "") or deployment_values.get("XNP_DATA_DIR", ""),
        "XNP_MYSQL_USER": os.environ.get("XNP_MYSQL_USER", "") or deployment_values.get("XNP_MYSQL_USER", ""),
        "XNP_MYSQL_DATABASE": os.environ.get("XNP_MYSQL_DATABASE", "") or deployment_values.get("XNP_MYSQL_DATABASE", ""),
    }
    obs_bucket = os.environ.get("HUAWEI_OBS_BUCKET", "") or deployment_values.get("HUAWEI_OBS_BUCKET", "")
    obs_prefix = os.environ.get("HUAWEI_OBS_PREFIX", "") or deployment_values.get("HUAWEI_OBS_PREFIX", "")
    if require_huawei_obs or obs_bucket:
        required_values["HUAWEI_OBS_BUCKET"] = obs_bucket
    if require_huawei_obs or obs_prefix:
        required_values["HUAWEI_OBS_PREFIX"] = obs_prefix

    failures: list[str] = []
    for name, value in required_values.items():
        if name == "HUAWEI_OBS_BUCKET" and obs_bucket_has_namespace:
            continue
        if not value or not has_xnp_namespace(value):
            failures.append(name)
    return failures


def fetch_text(base_url: str, path: str) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + path, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status < 300, body
    except urllib.error.URLError as error:
        return False, str(error)


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        header = path.read_bytes()[:33]
    except OSError:
        return None
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    width = int.from_bytes(header[16:20], "big")
    height = int.from_bytes(header[20:24], "big")
    return width, height


def jpeg_size(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None

    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            return None
        segment_length = int.from_bytes(data[index:index + 2], "big")
        if segment_length < 2 or index + segment_length > len(data):
            return None
        if marker in range(0xC0, 0xC4) or marker in range(0xC5, 0xC8) or marker in range(0xC9, 0xCC) or marker in range(0xCD, 0xD0):
            height = int.from_bytes(data[index + 3:index + 5], "big")
            width = int.from_bytes(data[index + 5:index + 7], "big")
            return width, height
        index += segment_length
    return None


def image_size(path: Path) -> tuple[int, int] | None:
    if path.suffix.lower() == ".png":
        return png_size(path)
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return jpeg_size(path)
    return None


def screenshot_evidence(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"missing {path}"

    candidates = [file for file in path.rglob("*") if file.is_file() and file.suffix.lower() in {".png", ".jpg", ".jpeg"}]
    if not candidates:
        return False, f"no PNG/JPEG screenshots under {path}"

    details = []
    for file in candidates:
        size = image_size(file)
        if size is None:
            details.append(f"{file.name}: unreadable")
            continue
        details.append(f"{file.name}: {size[0]}x{size[1]}")
        if size in ACCEPTED_IPHONE_SCREENSHOT_SIZES:
            return True, "; ".join(details)
    return False, "; ".join(details)


def app_store_evidence(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    missing = data.get("missingEvidence", [])
    if data.get("ready") is True and missing == []:
        return True, "App Store manual evidence is complete"
    if isinstance(missing, list) and missing:
        return False, "missing evidence: " + ", ".join(str(item) for item in missing)
    return False, "App Store manual evidence is not ready"


def app_store_assets_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"App Store assets proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed asset checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "App Store assets proof did not pass"


def app_store_connect_materials_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"App Store Connect materials proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed App Store Connect material checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "App Store Connect materials proof did not pass"


def app_store_connect_evidence_materials_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"App Store Connect evidence materials proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed App Store Connect evidence material checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "App Store Connect evidence materials proof did not pass"


def app_store_submission_packet_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"App Store submission packet proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed App Store submission packet checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "App Store submission packet proof did not pass"


def mainland_filing_materials_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"mainland filing materials proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed mainland filing material checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "mainland filing materials proof did not pass"


def signed_archive_testflight_materials_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"signed archive/TestFlight materials proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed signed archive/TestFlight material checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "signed archive/TestFlight materials proof did not pass"


def provider_evidence_materials_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"provider evidence materials proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed provider evidence material checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "provider evidence materials proof did not pass"


def auth_providers_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"auth provider proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed auth provider checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "auth provider proof did not pass"


def diagnostics_redaction_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"diagnostics redaction proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed diagnostics redaction checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "diagnostics redaction proof did not pass"


def public_pages_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"public pages proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed public page checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "public pages proof did not pass"


def review_notes_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"review notes proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed review notes checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "review notes proof did not pass"


def legal_drafts_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"legal drafts proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed legal draft checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "legal drafts proof did not pass"


def universal_links_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"universal links proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed universal link checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "universal links proof did not pass"


def storage_proof(path: Path, require_huawei_obs: bool) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    if data.get("passed") is not True:
        return False, "storage proof passed=false"
    backend = str(data.get("storageBackend", "")).strip().lower()
    if require_huawei_obs and backend != "huawei_obs":
        return False, f"storage proof backend is {backend or '<empty>'}, expected huawei_obs"
    return True, f"storage proof passed with backend {backend or '<empty>'}"


def ios_release_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"iOS release proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed iOS checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "iOS release proof did not pass"


def ios_app_bundle_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        app_path = data.get("appPath", "<unknown app>")
        return True, f"iOS app bundle proof passed {len(checks) if isinstance(checks, dict) else 0} checks for {app_path}"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed iOS app bundle checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "iOS app bundle proof did not pass"


def ios_265_build_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        simulator_app = data.get("simulatorAppPath", "<unknown simulator app>")
        device_app = data.get("deviceAppPath", "<unknown device app>")
        return True, f"iOS 26.5 build proof passed {len(checks) if isinstance(checks, dict) else 0} checks for {simulator_app} and {device_app}"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed iOS 26.5 build checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "iOS 26.5 build proof did not pass"


def testflight_precheck_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        app_path = data.get("appPath", "<unknown app>")
        return True, f"TestFlight client precheck passed {len(checks) if isinstance(checks, dict) else 0} checks for {app_path}"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed TestFlight precheck checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "TestFlight precheck proof did not pass"


def testflight_regression_plan_proof(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    failed_checks = data.get("failedRequiredChecks", [])
    if data.get("passed") is True and failed_checks == []:
        checks = data.get("checks", {})
        return True, f"TestFlight regression plan proof passed {len(checks) if isinstance(checks, dict) else 0} checks"
    if isinstance(failed_checks, list) and failed_checks:
        return False, "failed TestFlight regression plan checks: " + ", ".join(str(item) for item in failed_checks)
    return False, "TestFlight regression plan proof did not pass"


def ios_sim_launch_proof(path: Path, expected_runtime: str) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, f"missing {path}"
    except json.JSONDecodeError as error:
        return False, f"invalid JSON: {error}"

    simulator = data.get("simulator", {}) if isinstance(data.get("simulator", {}), dict) else {}
    app = data.get("app", {}) if isinstance(data.get("app", {}), dict) else {}
    runtime = str(simulator.get("runtime", "")).strip()
    dt_platform_version = str(app.get("dtPlatformVersion", "")).strip()
    dt_sdk_name = str(app.get("dtSdkName", "")).strip()
    launch_output = str(data.get("launchOutput", "")).strip()

    failures: list[str] = []
    if data.get("passed") is not True:
        failures.append("passed")
    if runtime != expected_runtime:
        failures.append("simulator.runtime")
    expected_platform_version = expected_runtime.replace("iOS ", "")
    if dt_platform_version != expected_platform_version:
        failures.append("app.dtPlatformVersion")
    if expected_platform_version not in dt_sdk_name:
        failures.append("app.dtSdkName")
    if "com.mewpow.xiaonaiping:" not in launch_output:
        failures.append("launchOutput")

    if failures:
        return False, "invalid iOS simulator launch proof fields: " + ", ".join(failures)
    return True, f"{expected_runtime} simulator install/launch proof passed: {launch_output}"



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
            "ready": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    report = Report()
    deployment_proof_path = current_dated_proof_path(
        root,
        args.deployment_proof,
        DEFAULT_DEPLOYMENT_PROOF,
        "huawei-baota-deploy",
        args.expected_proof_date,
    )
    storage_proof_path = current_dated_proof_path(
        root,
        args.storage_proof,
        DEFAULT_STORAGE_PROOF,
        "storage-backend",
        args.expected_proof_date,
    )
    deployment_proof = read_json(root / deployment_proof_path)
    deployment_current, deployment_current_evidence = proof_has_current_timestamp(deployment_proof, args.expected_proof_date)
    report.add(
        "deploymentProofCurrent",
        deployment_current,
        deployment_current_evidence,
    )
    private_env_status = deployment_proof.get("privateEnvStatus", {})
    private_env_set = set(private_env_status.get("set", [])) if isinstance(private_env_status, dict) else set()
    deployment_paths = deployment_proof.get("remotePaths", {}) if isinstance(deployment_proof.get("remotePaths", {}), dict) else {}
    deployment_runtime = deployment_proof.get("runtime", {}) if isinstance(deployment_proof.get("runtime", {}), dict) else {}
    deployment_isolation = deployment_proof.get("isolation", {}) if isinstance(deployment_proof.get("isolation", {}), dict) else {}
    deployment_public_route = deployment_proof.get("publicRoute", {}) if isinstance(deployment_proof.get("publicRoute", {}), dict) else {}
    deployment_public_env = deployment_proof.get("publicEnvValues", {}) if isinstance(deployment_proof.get("publicEnvValues", {}), dict) else {}
    deployment_provider_checks = deployment_proof.get("providerChecks", {}) if isinstance(deployment_proof.get("providerChecks", {}), dict) else {}
    deployment_values = {
        "XNP_DATA_DIR": str(deployment_paths.get("dataDir", "")),
        "XNP_MYSQL_USER": str(deployment_isolation.get("mysqlUser", "")),
        "XNP_MYSQL_DATABASE": str(deployment_isolation.get("mysqlDatabase", "")),
        "HUAWEI_OBS_BUCKET": str(deployment_public_env.get("HUAWEI_OBS_BUCKET", "")),
        "HUAWEI_OBS_PREFIX": os.environ.get("HUAWEI_OBS_PREFIX", "") or str(deployment_public_env.get("HUAWEI_OBS_PREFIX", "")) or ("xiaonaiping" if "HUAWEI_OBS_PREFIX" in private_env_set else ""),
        "__providerChecks": deployment_provider_checks,
    }

    def proof_key_set(name: str) -> bool:
        return name in private_env_set

    project_release_url = parse_release_api_base_url(root / "App/iOS/project.yml")
    effective_base_url = args.base_url or os.environ.get("XNP_API_BASE_URL") or project_release_url
    base_source = "--base-url" if args.base_url else "XNP_API_BASE_URL env" if os.environ.get("XNP_API_BASE_URL") else "App/iOS/project.yml Release"

    report.add(
        "productionApiBaseUrlPresent",
        bool(effective_base_url),
        f"{base_source}: {effective_base_url or '<empty>'}",
    )
    report.add(
        "productionApiBaseUrlUsesHttps",
        effective_base_url.startswith("https://"),
        effective_base_url or "<empty>",
    )
    report.add(
        "productionApiBaseUrlNotPlaceholder",
        bool(effective_base_url) and not is_placeholder_url(effective_base_url),
        effective_base_url or "<empty>",
    )

    secret_key = os.environ.get("XNP_SECRET_KEY", "")
    secret_from_proof = proof_key_set("XNP_SECRET_KEY")
    report.add(
        "productionSecretConfigured",
        (len(secret_key) >= 32 and "change" not in secret_key.lower() and "replace" not in secret_key.lower()) or secret_from_proof,
        "XNP_SECRET_KEY is set with production-looking length"
        if secret_key
        else "remote private env reports XNP_SECRET_KEY=set"
        if secret_from_proof
        else "XNP_SECRET_KEY is missing",
    )
    data_dir = os.environ.get("XNP_DATA_DIR", "") or deployment_values["XNP_DATA_DIR"]
    report.add(
        "productionDataDirConfigured",
        bool(data_dir),
        "XNP_DATA_DIR is set" if data_dir else "XNP_DATA_DIR is missing",
    )
    auth_debug_mode = os.environ.get("XNP_AUTH_DEBUG_MODE", "").strip() or str(deployment_public_env.get("XNP_AUTH_DEBUG_MODE", "")).strip()
    auth_debug_disabled_from_proof = deployment_provider_checks.get("authDebugModeDisabled") is True
    report.add(
        "authDebugModeDisabled",
        auth_debug_mode in {"", "0", "false", "False"} or auth_debug_disabled_from_proof,
        f"XNP_AUTH_DEBUG_MODE={auth_debug_mode or '<empty>'}"
        if not auth_debug_disabled_from_proof
        else "deployment proof reports authDebugModeDisabled=true",
    )

    database_backend = os.environ.get("XNP_DATABASE_BACKEND", "").strip().lower() or str(deployment_runtime.get("databaseBackend", "")).strip().lower()
    report.add(
        "mysqlDatabaseSelected",
        database_backend == "mysql",
        f"XNP_DATABASE_BACKEND={database_backend or '<empty>'}",
    )
    mysql_required_env = [
        "XNP_MYSQL_HOST",
        "XNP_MYSQL_USER",
        "XNP_MYSQL_PASSWORD",
        "XNP_MYSQL_DATABASE",
    ]
    missing_mysql = [name for name in mysql_required_env if not os.environ.get(name) and not proof_key_set(name)]
    report.add(
        "mysqlDatabaseEnvPresent",
        not missing_mysql,
        "missing: " + ", ".join(missing_mysql) if missing_mysql else "all required XNP_MYSQL_* variables are set",
    )

    storage_backend = (
        os.environ.get("XNP_STORAGE_BACKEND", "").strip().lower()
        or str(deployment_public_env.get("XNP_STORAGE_BACKEND", "")).strip().lower()
        or str(deployment_runtime.get("storageBackend", "")).strip().lower()
    )
    storage_backend_from_proof = deployment_provider_checks.get("storageBackendIsHuaweiOBS") is True
    report.add(
        "huaweiObsSelected",
        storage_backend == "huawei_obs" or storage_backend_from_proof,
        f"XNP_STORAGE_BACKEND={storage_backend or '<empty>'}"
        if not storage_backend_from_proof
        else "deployment proof reports storageBackendIsHuaweiOBS=true",
        required=args.require_huawei_obs,
    )
    huawei_required_env = [
        "HUAWEI_OBS_ACCESS_KEY_ID",
        "HUAWEI_OBS_SECRET_ACCESS_KEY",
        "HUAWEI_OBS_ENDPOINT",
        "HUAWEI_OBS_BUCKET",
    ]
    missing_huawei = [name for name in huawei_required_env if not os.environ.get(name) and not proof_key_set(name)]
    report.add(
        "huaweiObsEnvPresent",
        not missing_huawei,
        "missing: " + ", ".join(missing_huawei) if missing_huawei else "all required HUAWEI_OBS_* variables are set",
        required=args.require_huawei_obs,
    )

    sms_provider = os.environ.get("XNP_SMS_PROVIDER", "").strip() or str(deployment_public_env.get("XNP_SMS_PROVIDER", "")).strip()
    sms_secret = os.environ.get("XNP_SMS_SECRET", "").strip() or ("configured-in-remote-private-env" if proof_key_set("XNP_SMS_SECRET") else "")
    sms_webhook_url = os.environ.get("XNP_SMS_WEBHOOK_URL", "").strip() or str(deployment_public_env.get("XNP_SMS_WEBHOOK_URL", "")).strip() or ("configured-in-remote-private-env" if proof_key_set("XNP_SMS_WEBHOOK_URL") else "")
    sms_provider_is_webhook = sms_provider == "webhook" or deployment_provider_checks.get("smsProviderIsWebhook") is True
    sms_missing = []
    if not sms_provider_is_webhook:
        sms_missing.append("XNP_SMS_PROVIDER=webhook")
    if not sms_secret:
        sms_missing.append("XNP_SMS_SECRET")
    if not sms_webhook_url:
        sms_missing.append("XNP_SMS_WEBHOOK_URL")
    report.add(
        "phoneLoginProviderConfigured",
        not sms_missing,
        "SMS webhook provider is configured" if not sms_missing else "missing: " + ", ".join(sms_missing),
    )

    wechat_app_id_value = os.environ.get("XNP_WECHAT_APP_ID", "").strip() or str(deployment_public_env.get("XNP_WECHAT_APP_ID", "")).strip()
    wechat_app_id_configured = (
        configured_wechat_app_id(wechat_app_id_value)
        if wechat_app_id_value
        else deployment_provider_checks.get("wechatAppIDConfigured") is True
    )
    wechat_app_secret = os.environ.get("XNP_WECHAT_APP_SECRET", "").strip() or ("configured-in-remote-private-env" if proof_key_set("XNP_WECHAT_APP_SECRET") else "")
    report.add(
        "wechatLoginProviderConfigured",
        bool(wechat_app_id_configured and wechat_app_secret),
        "valid XNP_WECHAT_APP_ID and XNP_WECHAT_APP_SECRET are set"
        if wechat_app_id_configured and wechat_app_secret
        else "missing valid XNP_WECHAT_APP_ID (wx + 16 hex) or XNP_WECHAT_APP_SECRET",
    )

    admin_token = os.environ.get("XNP_ADMIN_TOKEN", "")
    admin_token_from_proof = proof_key_set("XNP_ADMIN_TOKEN")
    report.add(
        "privateOperationsDashboardConfigured",
        len(admin_token) >= 32 or admin_token_from_proof,
        "XNP_ADMIN_TOKEN is set with production-looking length"
        if admin_token
        else "remote private env reports XNP_ADMIN_TOKEN=set"
        if admin_token_from_proof
        else "XNP_ADMIN_TOKEN is missing",
    )
    internal_paths_blocked = deployment_public_route.get("publicInternalPathsBlocked") is True
    blocked_paths = deployment_public_route.get("blockedPaths", [])
    report.add(
        "publicInternalDashboardBlocked",
        internal_paths_blocked,
        "public internal paths blocked: " + ", ".join(blocked_paths)
        if internal_paths_blocked and isinstance(blocked_paths, list)
        else "deployment proof does not show public /internal blocking",
    )

    namespace_missing = namespace_failures(args.require_huawei_obs, deployment_values)
    report.add(
        "xiaonaipingProductionNamespaceConfigured",
        not namespace_missing,
        "missing xiaonaiping/xnp namespace in: " + ", ".join(namespace_missing)
        if namespace_missing
        else "data directory, MySQL identity, and object storage namespace are xiaonaiping-specific",
    )

    shared_hits = shared_service_hits(effective_base_url, deployment_values)
    report.add(
        "sharedServiceNamespaceRejected",
        not shared_hits,
        "; ".join(shared_hits) if shared_hits else "no Emotion/YDM/Daimao namespace markers in deployment values",
    )

    for check_name, relative_path in REQUIRED_DOCS.items():
        path = root / relative_path
        report.add(check_name + "Exists", path.exists(), relative_path)

    app_metadata = read_text(root / "Docs/08_Release/APP_STORE_METADATA.md")
    report.add(
        "appStoreUrlsFinalized",
        bool(app_metadata) and "api.example.com" not in app_metadata,
        "APP_STORE_METADATA.md still contains api.example.com" if "api.example.com" in app_metadata else "no placeholder App Store URL found",
    )

    local_passed, local_evidence = proof_passed(root / "Backend/proof/release-flow.json")
    report.add("localReleaseFlowProofPassed", local_passed, local_evidence)

    remote_passed, remote_evidence = proof_passed(root / args.remote_proof, require_https=True)
    report.add("remoteReleaseFlowProofPassed", remote_passed, remote_evidence)

    storage_passed, storage_evidence = storage_proof(root / storage_proof_path, args.require_huawei_obs)
    report.add(
        "storageBackendProofPassed",
        storage_passed,
        storage_evidence,
        required=args.require_huawei_obs,
    )
    storage_current, storage_current_evidence = proof_has_current_timestamp(read_json(root / storage_proof_path), args.expected_proof_date)
    report.add(
        "storageBackendProofCurrent",
        storage_current,
        storage_current_evidence,
        required=args.require_huawei_obs,
    )

    ios_passed, ios_evidence = ios_release_proof(root / args.ios_release_proof)
    report.add("iosReleaseReadinessProofPassed", ios_passed, ios_evidence)

    ios_bundle_passed, ios_bundle_evidence = ios_app_bundle_proof(root / args.ios_app_bundle_proof)
    report.add("iosAppBundleProofPassed", ios_bundle_passed, ios_bundle_evidence)

    ios_265_build_passed, ios_265_build_evidence = ios_265_build_proof(root / args.ios_265_build_proof)
    report.add("ios265BuildProofPassed", ios_265_build_passed, ios_265_build_evidence)

    testflight_precheck_passed, testflight_precheck_evidence = testflight_precheck_proof(root / args.testflight_precheck_proof)
    report.add("testFlightClientPrecheckProofPassed", testflight_precheck_passed, testflight_precheck_evidence)

    testflight_regression_plan_passed, testflight_regression_plan_evidence = testflight_regression_plan_proof(root / args.testflight_regression_plan_proof)
    report.add("testFlightRegressionPlanProofPassed", testflight_regression_plan_passed, testflight_regression_plan_evidence)

    sim_launch_path = root / args.sim_launch_proof if args.sim_launch_proof else latest_sim_launch_proof(root)
    sim_launch_passed, sim_launch_evidence = ios_sim_launch_proof(sim_launch_path, args.expected_sim_runtime)
    report.add("ios265SimulatorLaunchProofPassed", sim_launch_passed, sim_launch_evidence)

    app_store_assets_passed, app_store_assets_evidence = app_store_assets_proof(root / args.app_store_assets_proof)
    report.add("appStoreAssetsProofPassed", app_store_assets_passed, app_store_assets_evidence)

    app_store_connect_materials_passed, app_store_connect_materials_evidence = app_store_connect_materials_proof(root / args.app_store_connect_materials_proof)
    report.add("appStoreConnectMaterialsProofPassed", app_store_connect_materials_passed, app_store_connect_materials_evidence)

    app_store_connect_evidence_materials_passed, app_store_connect_evidence_materials_evidence = app_store_connect_evidence_materials_proof(root / args.app_store_connect_evidence_materials_proof)
    report.add("appStoreConnectEvidenceMaterialsProofPassed", app_store_connect_evidence_materials_passed, app_store_connect_evidence_materials_evidence)

    app_store_submission_packet_passed, app_store_submission_packet_evidence = app_store_submission_packet_proof(root / args.app_store_submission_packet_proof)
    report.add("appStoreSubmissionPacketProofPassed", app_store_submission_packet_passed, app_store_submission_packet_evidence)

    mainland_filing_materials_passed, mainland_filing_materials_evidence = mainland_filing_materials_proof(root / args.mainland_filing_materials_proof)
    report.add("mainlandFilingMaterialsProofPassed", mainland_filing_materials_passed, mainland_filing_materials_evidence)

    signed_archive_testflight_materials_passed, signed_archive_testflight_materials_evidence = signed_archive_testflight_materials_proof(root / args.signed_archive_testflight_materials_proof)
    report.add("signedArchiveTestFlightMaterialsProofPassed", signed_archive_testflight_materials_passed, signed_archive_testflight_materials_evidence)

    provider_evidence_materials_passed, provider_evidence_materials_evidence = provider_evidence_materials_proof(root / args.provider_evidence_materials_proof)
    report.add("providerEvidenceMaterialsProofPassed", provider_evidence_materials_passed, provider_evidence_materials_evidence)

    auth_providers_passed, auth_providers_evidence = auth_providers_proof(root / args.auth_providers_proof)
    report.add("authProvidersProofPassed", auth_providers_passed, auth_providers_evidence)

    diagnostics_passed, diagnostics_evidence = diagnostics_redaction_proof(root / args.diagnostics_redaction_proof)
    report.add("diagnosticsRedactionProofPassed", diagnostics_passed, diagnostics_evidence)

    public_pages_passed, public_pages_evidence = public_pages_proof(root / args.public_pages_proof)
    report.add("publicPagesProofPassed", public_pages_passed, public_pages_evidence)

    review_notes_passed, review_notes_evidence = review_notes_proof(root / args.review_notes_proof)
    report.add("reviewNotesProofPassed", review_notes_passed, review_notes_evidence)

    legal_drafts_passed, legal_drafts_evidence = legal_drafts_proof(root / args.legal_drafts_proof)
    report.add("legalDraftsProofPassed", legal_drafts_passed, legal_drafts_evidence)

    universal_links_passed, universal_links_evidence = universal_links_proof(root / args.universal_links_proof)
    report.add("universalLinksProofPassed", universal_links_passed, universal_links_evidence)

    screenshot_path = root / args.screenshot_dir
    screenshot_passed, screenshot_detail = screenshot_evidence(screenshot_path)
    report.add(
        "appStoreScreenshotsCaptured",
        screenshot_passed,
        screenshot_detail,
        required=args.require_screenshots,
    )

    if args.live_check:
        for path, marker in STATIC_PAGE_MARKERS.items():
            ok, body_or_error = fetch_text(effective_base_url, path) if effective_base_url else (False, "missing base URL")
            report.add(
                "live" + path.title().replace("/", "") + "Available",
                ok and marker in body_or_error,
                path if ok else body_or_error,
            )

    evidence_passed, evidence_detail = app_store_evidence(root / args.app_store_evidence)
    report.add(
        "appStoreManualEvidenceReady",
        evidence_passed,
        evidence_detail,
        required=args.require_app_store_evidence,
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--base-url", default="")
    parser.add_argument("--remote-proof", default="Backend/proof/remote-api.json")
    parser.add_argument("--deployment-proof", default="")
    parser.add_argument("--storage-proof", default="")
    parser.add_argument("--ios-release-proof", default="Backend/proof/ios-release-readiness.json")
    parser.add_argument("--ios-app-bundle-proof", default="Backend/proof/ios-app-bundle.json")
    parser.add_argument("--ios-265-build-proof", default="Backend/proof/ios-265-build.json")
    parser.add_argument("--testflight-precheck-proof", default="Backend/proof/testflight-precheck.json")
    parser.add_argument("--testflight-regression-plan-proof", default="Backend/proof/testflight-regression-plan.json")
    parser.add_argument("--sim-launch-proof")
    parser.add_argument("--expected-sim-runtime", default="iOS 26.5")
    parser.add_argument("--app-store-assets-proof", default="Backend/proof/app-store-assets.json")
    parser.add_argument("--app-store-connect-materials-proof", default="Backend/proof/app-store-connect-materials.json")
    parser.add_argument("--app-store-connect-evidence-materials-proof", default="Backend/proof/app-store-connect-evidence-materials.json")
    parser.add_argument("--app-store-submission-packet-proof", default="Backend/proof/app-store-submission-packet.json")
    parser.add_argument("--mainland-filing-materials-proof", default="Backend/proof/mainland-filing-materials.json")
    parser.add_argument("--signed-archive-testflight-materials-proof", default="Backend/proof/signed-archive-testflight-materials.json")
    parser.add_argument("--provider-evidence-materials-proof", default="Backend/proof/provider-evidence-materials.json")
    parser.add_argument("--auth-providers-proof", default="Backend/proof/auth-providers.json")
    parser.add_argument("--diagnostics-redaction-proof", default="Backend/proof/diagnostics-redaction.json")
    parser.add_argument("--public-pages-proof", default="Backend/proof/public-pages.json")
    parser.add_argument("--review-notes-proof", default="Backend/proof/review-notes.json")
    parser.add_argument("--legal-drafts-proof", default="Backend/proof/legal-drafts.json")
    parser.add_argument("--universal-links-proof", default="Backend/proof/universal-links.json")
    parser.add_argument("--app-store-evidence", default="Backend/proof/app-store-evidence.json")
    parser.add_argument("--screenshot-dir", default="Docs/08_Release/Screenshots")
    parser.add_argument("--output", default="Backend/proof/production-readiness.json")
    parser.add_argument("--expected-proof-date", default=expected_proof_date())
    parser.add_argument("--require-huawei-obs", action="store_true")
    parser.add_argument("--require-screenshots", action="store_true")
    parser.add_argument("--require-app-store-evidence", action="store_true")
    parser.add_argument("--live-check", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(args.repo_root) / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["ready"]:
        print(f"production readiness passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"production readiness incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
