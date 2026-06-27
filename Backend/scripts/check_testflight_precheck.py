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


EXPECTED_SHARED_SNAPSHOT_FIELDS = {
    "hasCompletedOnboarding",
    "babyName",
    "daysSinceBirth",
    "feedingCount",
    "milkAmountML",
    "lastFeedingAt",
    "ongoingSleepStartAt",
    "nextFeedingReminderAt",
    "feedingReminderRepeatIntervalMinutes",
    "poopCount",
    "peeCount",
    "generatedAt",
}

EXPECTED_LIVE_ACTIVITY_STATE_FIELDS = {
    "babyName",
    "nextReminderAt",
    "repeatIntervalMinutes",
    "babyAvatarData",
}

FORBIDDEN_APP_SOURCE_MARKERS = {
    "import HealthKit",
    "HKHealthStore",
    "压力",
    "压力评估",
    "心理评估",
    "stress",
}

FORBIDDEN_REVIEW_SURFACE_MARKERS = {
    "HealthKit",
    "HKHealth",
    "传感器",
    "医院",
    "医疗",
    "医疗器械",
    "诊断",
    "治疗",
    "压力",
    "心理",
    "建议",
    "sensor",
    "hospital",
    "medical",
    "diagnosis",
    "treatment",
    "stress",
}

MAIN_APP_REVIEW_SURFACE_PATHS = (
    "XiaoNaiPing/Views/ProfileView.swift",
    "XiaoNaiPing/Views/HomeView.swift",
    "XiaoNaiPing/Views/FeedingRecordView.swift",
    "XiaoNaiPing/Views/GrowthView.swift",
    "XiaoNaiPing/Views/VaccineView.swift",
    "XiaoNaiPing/Views/AlbumView.swift",
    "XiaoNaiPing/Models/AppNotificationScheduler.swift",
    "XiaoNaiPing/Services/CloudBackupController.swift",
    "XiaoNaiPingShared/XiaoNaiPingShared.swift",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_plist(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            data = plistlib.load(file)
    except (FileNotFoundError, plistlib.InvalidFileException, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def source_tree(root: Path) -> Path:
    return root / "App/iOS"


def extract_type_body(text: str, declaration_name: str) -> str:
    match = re.search(rf"\b(?:struct|enum|class)\s+{re.escape(declaration_name)}\b", text)
    if not match:
        return ""
    start = text.find("{", match.end())
    if start < 0:
        return ""

    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : index]
    return ""


def swift_var_names(type_body: str) -> set[str]:
    result: set[str] = set()
    for match in re.finditer(r"^\s*(?:let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*:", type_body, re.MULTILINE):
        result.add(match.group(1))
    return result


def plist_array_contains(plist: dict[str, Any], key: str, expected: str) -> bool:
    value = plist.get(key)
    return isinstance(value, list) and expected in value


def source_marker_hits(root: Path, markers: set[str]) -> list[str]:
    hits: list[str] = []
    for path in sorted(source_tree(root).rglob("*.swift")):
        text = read_text(path)
        for marker in markers:
            if marker in text:
                hits.append(f"{path.relative_to(root)} contains {marker}")
    return hits


def text_marker_hits(files: list[tuple[Path, str]], markers: set[str], root: Path) -> list[str]:
    hits: list[str] = []
    for path, text in files:
        for marker in sorted(markers):
            if marker in text:
                hits.append(f"{path.relative_to(root)} contains {marker}")
    return hits


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str, app_path: Path, root: Path) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "appPath": str(app_path),
            "repoRoot": str(root),
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    started_at = utc_now()
    root = Path(args.repo_root).resolve()
    app_path = Path(args.app).resolve()
    info = read_plist(app_path / "Info.plist")
    widget_path = app_path / "PlugIns/XiaoNaiPingWidgets.appex"
    widget_info = read_plist(widget_path / "Info.plist")

    app_entitlements = read_plist(source_tree(root) / "XiaoNaiPing/XiaoNaiPing.entitlements")
    widget_entitlements = read_plist(source_tree(root) / "XiaoNaiPingWidgets/XiaoNaiPingWidgets.entitlements")
    widget_source = read_text(source_tree(root) / "XiaoNaiPingWidgets/XiaoNaiPingWidgets.swift")
    notification_source = read_text(source_tree(root) / "XiaoNaiPing/Models/AppNotificationScheduler.swift")
    shared_source = read_text(source_tree(root) / "XiaoNaiPingShared/XiaoNaiPingShared.swift")
    profile_source = read_text(source_tree(root) / "XiaoNaiPing/Views/ProfileView.swift")
    feeding_source = read_text(source_tree(root) / "XiaoNaiPing/Views/FeedingRecordView.swift")
    store_source = read_text(source_tree(root) / "XiaoNaiPing/Models/BabyRecordStore.swift")
    cloud_controller_source = read_text(source_tree(root) / "XiaoNaiPing/Services/CloudBackupController.swift")
    cloud_api_source = read_text(source_tree(root) / "XiaoNaiPing/Services/CloudBackupAPIClient.swift")
    project_source = read_text(source_tree(root) / "project.yml") + "\n" + read_text(source_tree(root) / "XiaoNaiPing.xcodeproj/project.pbxproj")

    report = Report()
    report.add("appBundleExists", app_path.is_dir(), str(app_path))
    report.add("infoPlistPresent", bool(info), str(app_path / "Info.plist") if info else "missing or invalid app Info.plist")

    bundle_id = str(info.get("CFBundleIdentifier", ""))
    report.add(
        "bundleIdentifierMatches",
        bundle_id == args.expected_bundle_id,
        f"CFBundleIdentifier={bundle_id or '<missing>'}",
    )

    api_url = str(info.get("XNPAPIBaseURL", "")).strip()
    report.add(
        "releaseApiBaseURLMatches",
        api_url == args.expected_api_url,
        f"XNPAPIBaseURL={api_url or '<missing>'}",
    )
    report.add(
        "liveActivitiesEnabledInAppPlist",
        info.get("NSSupportsLiveActivities") is True,
        f"NSSupportsLiveActivities={info.get('NSSupportsLiveActivities', '<missing>')}",
    )

    extension_id = widget_info.get("NSExtension", {}).get("NSExtensionPointIdentifier") if widget_info else None
    report.add("widgetExtensionBundled", widget_path.is_dir(), str(widget_path))
    report.add(
        "widgetExtensionPointIsWidgetKit",
        extension_id == "com.apple.widgetkit-extension",
        f"NSExtensionPointIdentifier={extension_id or '<missing>'}",
    )

    widget_markers = {
        "WidgetBundle",
        "XiaoNaiPingTodayWidget()",
        "FeedingReminderLiveActivityWidget()",
        "ActivityConfiguration(for: FeedingReminderActivityAttributes.self)",
    }
    missing_widget_markers = sorted(marker for marker in widget_markers if marker not in widget_source)
    report.add(
        "widgetBundleIncludesTodayAndLiveActivity",
        not missing_widget_markers,
        "missing: " + ", ".join(missing_widget_markers) if missing_widget_markers else "today widget and Live Activity widget are registered",
    )
    report.add(
        "liveActivityDefinesDynamicIsland",
        "DynamicIsland" in widget_source and "DynamicIslandExpandedRegion" in widget_source,
        "DynamicIsland and expanded regions found" if "DynamicIsland" in widget_source else "missing DynamicIsland implementation",
    )

    report.add(
        "appGroupEntitlementPresentForApp",
        plist_array_contains(app_entitlements, "com.apple.security.application-groups", args.expected_app_group),
        f"app entitlement application group={args.expected_app_group}",
    )
    report.add(
        "appGroupEntitlementPresentForWidget",
        plist_array_contains(widget_entitlements, "com.apple.security.application-groups", args.expected_app_group),
        f"widget entitlement application group={args.expected_app_group}",
    )
    associated_domains = app_entitlements.get("com.apple.developer.associated-domains")
    associated_domain_value = args.expected_associated_domain
    associated_domain_wired = isinstance(associated_domains, list) and "$(XNP_ASSOCIATED_DOMAIN)" in associated_domains
    associated_domain_configured = associated_domain_value in project_source
    report.add(
        "associatedDomainEntitlementWiredForApp",
        associated_domain_wired and associated_domain_configured,
        f"entitlement wired={associated_domain_wired}, project config contains {associated_domain_value}={associated_domain_configured}",
    )

    notification_markers = {
        "UNUserNotificationCenter.current().requestAuthorization",
        "UNUserNotificationCenter.current().add(request)",
        "UNCalendarNotificationTrigger",
    }
    missing_notification_markers = sorted(marker for marker in notification_markers if marker not in notification_source)
    report.add(
        "localNotificationSchedulerPresent",
        not missing_notification_markers,
        "missing: " + ", ".join(missing_notification_markers) if missing_notification_markers else "local notification authorization and calendar scheduling found",
    )
    remote_push_markers = {"registerForRemoteNotifications", "didRegisterForRemoteNotifications", "aps-environment"}
    remote_push_hits = sorted(marker for marker in remote_push_markers if marker in notification_source or marker in project_source)
    report.add(
        "remotePushNotConfigured",
        not remote_push_hits,
        "found: " + ", ".join(remote_push_hits) if remote_push_hits else "no remote push registration or aps-environment entitlement found",
    )

    notification_permission_markers = {
        "UNUserNotificationCenter.current().getNotificationSettings",
        "case .notDetermined:",
        "UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])",
        "case .denied:",
        "complete(.denied, completion: completion)",
        "@unknown default:",
    }
    missing_notification_permission_markers = sorted(marker for marker in notification_permission_markers if marker not in notification_source)
    report.add(
        "localNotificationPermissionDecisionPathsPresent",
        not missing_notification_permission_markers,
        "missing: " + ", ".join(missing_notification_permission_markers)
        if missing_notification_permission_markers
        else "local notification flow covers current settings, first-run authorization, denial, and unknown status",
    )

    notification_cancel_markers = {
        "static func removeFeedingReminder()",
        "removePendingNotificationRequests(withIdentifiers: feedingReminderIdentifiers)",
    }
    missing_notification_cancel_markers = sorted(marker for marker in notification_cancel_markers if marker not in notification_source)
    feeding_cancel_markers = {
        "AppNotificationScheduler.removeFeedingReminder()",
        "endLiveActivity()",
        "喝奶闹钟已取消。",
    }
    missing_feeding_cancel_markers = sorted(marker for marker in feeding_cancel_markers if marker not in feeding_source)
    report.add(
        "feedingNotificationCancellationPathPresent",
        not missing_notification_cancel_markers and not missing_feeding_cancel_markers,
        "scheduler missing: "
        + ", ".join(missing_notification_cancel_markers)
        + "; UI missing: "
        + ", ".join(missing_feeding_cancel_markers)
        if missing_notification_cancel_markers or missing_feeding_cancel_markers
        else "feeding reminder cancel path removes pending notifications and confirms cancellation",
    )
    feeding_live_activity_save_markers = {
        "private func saveReminder()",
        "syncLiveActivity()",
        "guard store.feedingLiveActivityEnabled else",
        "FeedingReminderLiveActivityController.endAll()",
        "FeedingReminderLiveActivityController.sync(",
        "reminder: store.nextFeedingReminder",
        "babyName: store.baby.name",
    }
    missing_feeding_live_activity_save_markers = sorted(marker for marker in feeding_live_activity_save_markers if marker not in feeding_source)
    feeding_live_activity_cancel_markers = {
        "private func cancelReminder()",
        "private func endLiveActivity()",
        "FeedingReminderLiveActivityController.endAll()",
    }
    missing_feeding_live_activity_cancel_markers = sorted(marker for marker in feeding_live_activity_cancel_markers if marker not in feeding_source)
    report.add(
        "feedingReminderLiveActivitySaveCancelPathsPresent",
        not missing_feeding_live_activity_save_markers and not missing_feeding_live_activity_cancel_markers,
        "save missing: "
        + ", ".join(missing_feeding_live_activity_save_markers)
        + "; cancel missing: "
        + ", ".join(missing_feeding_live_activity_cancel_markers)
        if missing_feeding_live_activity_save_markers or missing_feeding_live_activity_cancel_markers
        else "feeding reminder save syncs Live Activity through the user toggle and cancel ends Live Activity",
    )

    notification_denial_copy_markers = {
        "通知权限未开启。喝奶时间已保留在喂养页，不会弹出系统提醒。",
        "通知安排失败。喝奶时间已保留在喂养页。",
    }
    missing_notification_denial_copy_markers = sorted(marker for marker in notification_denial_copy_markers if marker not in feeding_source)
    report.add(
        "localNotificationDeniedAndFailureCopyPresent",
        not missing_notification_denial_copy_markers,
        "missing: " + ", ".join(missing_notification_denial_copy_markers)
        if missing_notification_denial_copy_markers
        else "feeding reminder UI explains denied permission and scheduling failure without health claims",
    )

    live_activity_control_markers = {
        "Toggle(isOn: Binding",
        "store.feedingLiveActivityEnabled",
        "setFeedingLiveActivityEnabled",
        "FeedingReminderLiveActivityController.sync",
        "FeedingReminderLiveActivityController.endAll",
        "测试灵动岛",
    }
    missing_live_activity_control_markers = sorted(marker for marker in live_activity_control_markers if marker not in profile_source)
    report.add(
        "feedingLiveActivityToggleControlPresent",
        not missing_live_activity_control_markers,
        "missing: " + ", ".join(missing_live_activity_control_markers)
        if missing_live_activity_control_markers
        else "Profile view exposes a feeding Live Activity toggle, test entry, sync path, and shutdown path",
    )

    live_activity_preference_markers = {
        "@Published var feedingLiveActivityEnabled",
        "func setFeedingLiveActivityEnabled",
        "case feedingLiveActivityEnabled",
        "feedingLiveActivityEnabled = state.feedingLiveActivityEnabled",
    }
    missing_live_activity_preference_markers = sorted(marker for marker in live_activity_preference_markers if marker not in store_source)
    report.add(
        "feedingLiveActivityPreferencePersisted",
        not missing_live_activity_preference_markers,
        "missing: " + ", ".join(missing_live_activity_preference_markers)
        if missing_live_activity_preference_markers
        else "feeding Live Activity user preference is stored and restored with app state",
    )

    account_backup_entry_markers = {
        "DataStatusSheet(kind: .backup",
        "账号与备份",
        "cloudBackup.serviceStatusLabel",
    }
    missing_account_backup_entry_markers = sorted(marker for marker in account_backup_entry_markers if marker not in profile_source)
    report.add(
        "accountBackupReviewEntryPresent",
        not missing_account_backup_entry_markers,
        "missing: " + ", ".join(missing_account_backup_entry_markers)
        if missing_account_backup_entry_markers
        else "Profile exposes the Account & Backup entry used by App Review",
    )

    account_login_surface_markers = {
        "手机号登录",
        "await cloudBackup.requestPhoneCode",
        "await cloudBackup.verifyPhoneCode",
        "微信登录",
        "await cloudBackup.loginWithWeChat",
        "!cloudBackup.isWeChatLoginConfigured",
        "恢复密钥登录",
        "await cloudBackup.recoverSession",
        "CloudBackupController.validateE164PhoneNumber",
        "CloudBackupController.validateSmsCode",
    }
    missing_account_login_surface_markers = sorted(marker for marker in account_login_surface_markers if marker not in profile_source)
    report.add(
        "accountLoginClientSurfacesPresent",
        not missing_account_login_surface_markers,
        "missing: " + ", ".join(missing_account_login_surface_markers)
        if missing_account_login_surface_markers
        else "Profile exposes recovery-key, phone, and gated WeChat login paths",
    )

    backup_restore_delete_surface_markers = {
        "await cloudBackup.createAccountAndBackup",
        "await cloudBackup.restoreLatestBackup",
        "await cloudBackup.deleteCloudAccount",
        "立即备份",
        "从云端恢复",
        "删除云端账号与备份",
        "本机资料保留",
    }
    missing_backup_restore_delete_surface_markers = sorted(
        marker for marker in backup_restore_delete_surface_markers if marker not in profile_source
    )
    report.add(
        "cloudBackupRestoreDeleteClientSurfacesPresent",
        not missing_backup_restore_delete_surface_markers,
        "missing: " + ", ".join(missing_backup_restore_delete_surface_markers)
        if missing_backup_restore_delete_surface_markers
        else "Profile exposes backup, cloud restore, and cloud account deletion flows",
    )

    account_debug_surface_markers = {
        "debug_wechat_ios",
        "Debug 验证码",
        "sessionToken",
        "Bearer ",
        "AppSecret",
    }
    account_debug_surface_hits = sorted(marker for marker in account_debug_surface_markers if marker in profile_source)
    report.add(
        "accountBackupReviewSurfaceAvoidsDebugSubstitutes",
        not account_debug_surface_hits,
        "found: " + ", ".join(account_debug_surface_hits)
        if account_debug_surface_hits
        else "Account & Backup review surface avoids debug codes, bearer tokens, and AppSecret markers",
    )

    cloud_controller_markers = {
        "func createAccountAndBackup",
        "func requestPhoneCode",
        "func verifyPhoneCode",
        "func recoverSession",
        "func loginWithWeChat",
        "func restoreLatestBackup",
        "func deleteCloudAccount",
        "sessionStore.clear()",
        "store.markCloudAccountDeletedLocally()",
        "private func uploadEverything",
        "client.uploadPhoto",
        "client.downloadPhoto",
    }
    missing_cloud_controller_markers = sorted(marker for marker in cloud_controller_markers if marker not in cloud_controller_source)
    report.add(
        "cloudBackupControllerCoreFlowsPresent",
        not missing_cloud_controller_markers,
        "missing: " + ", ".join(missing_cloud_controller_markers)
        if missing_cloud_controller_markers
        else "CloudBackupController wires account creation, login, backup, restore, photos, and cloud account deletion",
    )

    cloud_api_endpoint_markers = {
        'request(path: "/v1/accounts", method: "POST"',
        'request(path: "/v1/sessions/recover", method: "POST"',
        'request(path: "/v1/auth/phone/request-code", method: "POST"',
        'request(path: "/v1/auth/phone/verify", method: "POST"',
        'request(path: "/v1/auth/wechat/login", method: "POST"',
        'request(path: "/v1/backup", method: "PUT"',
        'request(path: "/v1/backup", method: "GET"',
        'path: "/v1/photos/\\(id.uuidString)"',
        'request(path: "/v1/photos", method: "GET"',
        'request(path: "/v1/account", method: "DELETE"',
    }
    missing_cloud_api_endpoint_markers = sorted(marker for marker in cloud_api_endpoint_markers if marker not in cloud_api_source)
    report.add(
        "cloudBackupServiceEndpointsPresent",
        not missing_cloud_api_endpoint_markers,
        "missing: " + ", ".join(missing_cloud_api_endpoint_markers)
        if missing_cloud_api_endpoint_markers
        else "CloudBackupAPIClient uses production account, login, backup, photo, and account deletion endpoints",
    )

    shared_fields = swift_var_names(extract_type_body(shared_source, "SharedTodaySnapshot"))
    unexpected_shared_fields = sorted(shared_fields - EXPECTED_SHARED_SNAPSHOT_FIELDS)
    missing_shared_fields = sorted(EXPECTED_SHARED_SNAPSHOT_FIELDS - shared_fields)
    report.add(
        "sharedWidgetSnapshotPayloadIsScoped",
        not unexpected_shared_fields and not missing_shared_fields,
        "unexpected: "
        + ", ".join(unexpected_shared_fields)
        + "; missing: "
        + ", ".join(missing_shared_fields)
        if unexpected_shared_fields or missing_shared_fields
        else "shared snapshot contains only today summary fields",
    )

    state_fields = swift_var_names(extract_type_body(extract_type_body(shared_source, "FeedingReminderActivityAttributes"), "ContentState"))
    unexpected_state_fields = sorted(state_fields - EXPECTED_LIVE_ACTIVITY_STATE_FIELDS)
    missing_state_fields = sorted(EXPECTED_LIVE_ACTIVITY_STATE_FIELDS - state_fields)
    report.add(
        "liveActivityPayloadIsScoped",
        not unexpected_state_fields and not missing_state_fields,
        "unexpected: "
        + ", ".join(unexpected_state_fields)
        + "; missing: "
        + ", ".join(missing_state_fields)
        if unexpected_state_fields or missing_state_fields
        else "Live Activity state contains only reminder timing, baby name, and optional avatar data",
    )

    widget_review_hits = text_marker_hits(
        [
            (source_tree(root) / "XiaoNaiPingWidgets/XiaoNaiPingWidgets.swift", widget_source),
            (source_tree(root) / "XiaoNaiPingShared/XiaoNaiPingShared.swift", shared_source),
        ],
        FORBIDDEN_REVIEW_SURFACE_MARKERS,
        root,
    )
    report.add(
        "widgetAndLiveActivityCopyAvoidsHealthClaims",
        not widget_review_hits,
        "found: " + "; ".join(widget_review_hits) if widget_review_hits else "widget and Live Activity surfaces avoid medical/health/stress claim markers",
    )

    notification_review_hits = text_marker_hits(
        [(source_tree(root) / "XiaoNaiPing/Models/AppNotificationScheduler.swift", notification_source)],
        FORBIDDEN_REVIEW_SURFACE_MARKERS,
        root,
    )
    report.add(
        "localNotificationCopyAvoidsHealthClaims",
        not notification_review_hits,
        "found: " + "; ".join(notification_review_hits) if notification_review_hits else "local notification copy avoids medical/health/stress claim markers",
    )

    main_app_review_files = [
        (source_tree(root) / relative_path, read_text(source_tree(root) / relative_path))
        for relative_path in MAIN_APP_REVIEW_SURFACE_PATHS
    ]
    main_app_review_hits = text_marker_hits(main_app_review_files, FORBIDDEN_REVIEW_SURFACE_MARKERS, root)
    report.add(
        "mainAppReviewSurfaceAvoidsHealthClaims",
        not main_app_review_hits,
        "found: " + "; ".join(main_app_review_hits)
        if main_app_review_hits
        else "main app review surfaces avoid medical/health/stress claim markers",
    )

    health_hits = source_marker_hits(root, FORBIDDEN_APP_SOURCE_MARKERS)
    report.add(
        "noHealthKitOrPressureSourceSurface",
        not health_hits,
        "found: " + "; ".join(health_hits) if health_hits else "no HealthKit or pressure/stress source markers found",
    )

    return report.to_dict(started_at, utc_now(), app_path, root)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--expected-api-url", default="https://api.mewpow.com/xiaonaiping")
    parser.add_argument("--expected-bundle-id", default="com.mewpow.xiaonaiping")
    parser.add_argument("--expected-app-group", default="group.com.mewpow.xiaonaiping")
    parser.add_argument("--expected-associated-domain", default="applinks:api.mewpow.com")
    parser.add_argument("--output", default=str(repo_root() / "Backend/proof/testflight-precheck.json"))
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"TestFlight precheck passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"TestFlight precheck incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
