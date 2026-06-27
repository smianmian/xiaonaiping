from __future__ import annotations

import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_testflight_precheck.py"


def write_plist(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as file:
        plistlib.dump(value, file)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_complete_fixture(root: Path) -> Path:
    app = root / "Build/XiaoNaiPing.app"
    write_plist(
        app / "Info.plist",
        {
            "CFBundleIdentifier": "com.mewpow.xiaonaiping",
            "XNPAPIBaseURL": "https://api.mewpow.com/xiaonaiping",
            "NSSupportsLiveActivities": True,
        },
    )
    write_plist(
        app / "PlugIns/XiaoNaiPingWidgets.appex/Info.plist",
        {
            "NSExtension": {
                "NSExtensionPointIdentifier": "com.apple.widgetkit-extension",
            },
        },
    )

    ios = root / "App/iOS"
    write_plist(
        ios / "XiaoNaiPing/XiaoNaiPing.entitlements",
        {
            "com.apple.developer.associated-domains": ["$(XNP_ASSOCIATED_DOMAIN)"],
            "com.apple.security.application-groups": ["group.com.mewpow.xiaonaiping"],
        },
    )
    write_plist(
        ios / "XiaoNaiPingWidgets/XiaoNaiPingWidgets.entitlements",
        {
            "com.apple.security.application-groups": ["group.com.mewpow.xiaonaiping"],
        },
    )
    write_text(
        ios / "project.yml",
        'XNP_ASSOCIATED_DOMAIN: "applinks:api.mewpow.com"\n',
    )
    write_text(
        ios / "XiaoNaiPingWidgets/XiaoNaiPingWidgets.swift",
        """
struct XiaoNaiPingTodayWidget {}
struct FeedingReminderLiveActivityWidget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: FeedingReminderActivityAttributes.self) { _ in
        } dynamicIsland: { _ in
            DynamicIsland { DynamicIslandExpandedRegion(.bottom) {} }
        }
    }
}
@main
struct XiaoNaiPingWidgetsBundle: WidgetBundle {
    var body: some Widget {
        XiaoNaiPingTodayWidget()
        FeedingReminderLiveActivityWidget()
    }
}
""",
    )
    write_text(
        ios / "XiaoNaiPing/Models/AppNotificationScheduler.swift",
        """
UNUserNotificationCenter.current().getNotificationSettings { settings in
    switch settings.authorizationStatus {
    case .notDetermined:
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
            if !granted { complete(.denied, completion: completion) }
        }
    case .denied:
        complete(.denied, completion: completion)
    @unknown default:
        complete(.failed, completion: completion)
    }
}
let trigger = UNCalendarNotificationTrigger(dateMatching: DateComponents(), repeats: false)
let request = UNNotificationRequest(identifier: "id", content: UNMutableNotificationContent(), trigger: trigger)
UNUserNotificationCenter.current().add(request) { _ in }
static func removeFeedingReminder() {
    UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: feedingReminderIdentifiers)
}
""",
    )
    write_text(
        ios / "XiaoNaiPing/Views/FeedingRecordView.swift",
        """
struct FeedingRecordView {
    private func saveReminder() {
        syncLiveActivity()
    }
    private func cancelReminder() {
        AppNotificationScheduler.removeFeedingReminder()
        endLiveActivity()
        notificationMessage = "喝奶闹钟已取消。"
    }
    private func syncLiveActivity() {
        guard store.feedingLiveActivityEnabled else {
            FeedingReminderLiveActivityController.endAll()
            return
        }
        FeedingReminderLiveActivityController.sync(
            reminder: store.nextFeedingReminder,
            babyName: store.baby.name,
            babyAvatarData: store.baby.avatarImageData
        )
    }
    private func endLiveActivity() {
        FeedingReminderLiveActivityController.endAll()
    }
    func notificationMessage(for result: NotificationScheduleResult) -> String {
        switch result {
        case .denied:
            return "通知权限未开启。喝奶时间已保留在喂养页，不会弹出系统提醒。"
        case .failed:
            return "通知安排失败。喝奶时间已保留在喂养页。"
        default:
            return ""
        }
    }
}
	""",
    )
    for review_surface in [
        "HomeView.swift",
        "GrowthView.swift",
        "VaccineView.swift",
        "AlbumView.swift",
    ]:
        write_text(
            ios / f"XiaoNaiPing/Views/{review_surface}",
            'struct ReviewSurface { let label = "记录宝宝日常" }\n',
        )
    write_text(
        ios / "XiaoNaiPingShared/XiaoNaiPingShared.swift",
        """
struct SharedTodaySnapshot {
    var hasCompletedOnboarding: Bool
    var babyName: String
    var daysSinceBirth: Int
    var feedingCount: Int
    var milkAmountML: Int
    var lastFeedingAt: Date?
    var ongoingSleepStartAt: Date?
    var nextFeedingReminderAt: Date?
    var feedingReminderRepeatIntervalMinutes: Int?
    var poopCount: Int
    var peeCount: Int
    var generatedAt: Date
}
struct FeedingReminderActivityAttributes {
    struct ContentState {
        var babyName: String
        var nextReminderAt: Date
        var repeatIntervalMinutes: Int?
        var babyAvatarData: Data?
    }
}
""",
    )
    write_text(
        ios / "XiaoNaiPing/Views/ProfileView.swift",
        """
struct ProfileView {
    var body: some View {
        ProfileMenuRow(icon: "icloud.and.arrow.up", title: "账号与备份", value: cloudBackup.serviceStatusLabel)
        DataStatusSheet(kind: .backup, cloudBackup: cloudBackup)
        Toggle(isOn: Binding(
            get: { store.feedingLiveActivityEnabled },
            set: { setFeedingLiveActivityEnabled($0) }
        )) { Text("灵动岛喝奶提醒") }
        Button("测试灵动岛") { testFeedingLiveActivity() }
    }
    func setFeedingLiveActivityEnabled(_ isEnabled: Bool) {
        if isEnabled {
            FeedingReminderLiveActivityController.sync(reminder: store.nextFeedingReminder, babyName: "宝宝", babyAvatarData: nil)
        } else {
            FeedingReminderLiveActivityController.endAll()
        }
    }
}
private struct DataStatusSheet: View {
    var body: some View {
        Text("手机号登录")
        Button("获取") {
            Task { await cloudBackup.requestPhoneCode(phoneNumber: normalizedPhoneNumber) }
        }
        Button("手机号登录") {
            Task { await cloudBackup.verifyPhoneCode(phoneNumber: normalizedPhoneNumber, code: normalizedPhoneCode) }
        }
        Button("微信登录") {
            Task { await cloudBackup.loginWithWeChat() }
        }
        .disabled(cloudBackup.isWorking || !cloudBackup.isWeChatLoginConfigured)
        Text("恢复密钥登录")
        Button("使用恢复密钥登录") {
            Task { await cloudBackup.recoverSession(recoveryKey: recoveryKey) }
        }
        _ = CloudBackupController.validateE164PhoneNumber(normalizedPhoneNumber)
        _ = CloudBackupController.validateSmsCode(normalizedPhoneCode)
        Button("立即备份") {
            Task { await cloudBackup.createAccountAndBackup(store: store) }
        }
        Button("从云端恢复") {
            Task { await cloudBackup.restoreLatestBackup(store: store) }
        }
        Button("删除云端账号与备份") {
            Task { await cloudBackup.deleteCloudAccount(store: store) }
        }
        Text("本机资料保留")
    }
}
""",
    )
    write_text(
        ios / "XiaoNaiPing/Services/CloudBackupController.swift",
        """
final class CloudBackupController {
    func createAccountAndBackup(store: BabyRecordStore) async {}
    func requestPhoneCode(phoneNumber: String) async {}
    func verifyPhoneCode(phoneNumber: String, code: String) async {}
    func recoverSession(recoveryKey: String) async {}
    func loginWithWeChat() async {}
    func restoreLatestBackup(store: BabyRecordStore) async {
        client.downloadPhoto(id: photo.id, token: token)
    }
    func deleteCloudAccount(store: BabyRecordStore) async {
        sessionStore.clear()
        store.markCloudAccountDeletedLocally()
    }
    private func uploadEverything(store: BabyRecordStore, client: CloudBackupAPIClient, token: String) async throws {
        client.uploadPhoto(id: asset.photo.id, data: data, token: token)
    }
}
""",
    )
    write_text(
        ios / "XiaoNaiPing/Services/CloudBackupAPIClient.swift",
        """
final class CloudBackupAPIClient {
    func createAccount() async throws {
        _ = try await request(path: "/v1/accounts", method: "POST", body: Data())
    }
    func recoverSession(recoveryKey: String) async throws {
        _ = try await request(path: "/v1/sessions/recover", method: "POST", body: body)
    }
    func requestPhoneCode(phoneNumber: String) async throws {
        _ = try await request(path: "/v1/auth/phone/request-code", method: "POST", body: body)
    }
    func verifyPhoneCode(phoneNumber: String, code: String) async throws {
        _ = try await request(path: "/v1/auth/phone/verify", method: "POST", body: body)
    }
    func loginWithWeChat(code: String) async throws {
        _ = try await request(path: "/v1/auth/wechat/login", method: "POST", body: body)
    }
    func uploadBackup(_ data: Data, token: String) async throws {
        _ = try await request(path: "/v1/backup", method: "PUT", body: data, token: token)
    }
    func downloadBackup(token: String) async throws {
        _ = try await request(path: "/v1/backup", method: "GET", token: token)
    }
    func uploadPhoto(id: UUID, data: Data, token: String) async throws {
        _ = try await request(path: "/v1/photos/\\(id.uuidString)", method: "PUT", body: data, token: token)
    }
    func listPhotos(token: String) async throws {
        _ = try await request(path: "/v1/photos", method: "GET", token: token)
    }
    func deleteAccount(token: String) async throws {
        _ = try await request(path: "/v1/account", method: "DELETE", token: token)
    }
}
""",
    )
    write_text(
        ios / "XiaoNaiPing/Models/BabyRecordStore.swift",
        """
final class BabyRecordStore {
    @Published var feedingLiveActivityEnabled = true
    func setFeedingLiveActivityEnabled(_ isEnabled: Bool) {
        feedingLiveActivityEnabled = isEnabled
    }
    func restore(_ state: AppState) {
        feedingLiveActivityEnabled = state.feedingLiveActivityEnabled
    }
}
struct AppState {
    var feedingLiveActivityEnabled: Bool
    enum CodingKeys: String, CodingKey {
        case feedingLiveActivityEnabled
    }
}
""",
    )
    return app


class TestFlightPrecheckTest(unittest.TestCase):
    def run_checker(self, app: Path, root: Path) -> dict:
        output = root / "proof.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--app",
                str(app),
                "--repo-root",
                str(root),
                "--output",
                str(output),
                "--allow-incomplete",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("TestFlight precheck", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_complete_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            app = write_complete_fixture(root)

            report = self.run_checker(app, root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_widget_scope_and_remote_push_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            app = write_complete_fixture(root)
            write_plist(app / "Info.plist", {"CFBundleIdentifier": "com.mewpow.xiaonaiping"})
            write_plist(app / "PlugIns/XiaoNaiPingWidgets.appex/Info.plist", {"NSExtension": {}})
            write_text(root / "App/iOS/XiaoNaiPingWidgets/XiaoNaiPingWidgets.swift", "struct OnlyWidget {}\n")
            write_text(
                root / "App/iOS/XiaoNaiPing/Models/AppNotificationScheduler.swift",
                "registerForRemoteNotifications()\n",
            )
            write_text(
                root / "App/iOS/XiaoNaiPingShared/XiaoNaiPingShared.swift",
                """
struct SharedTodaySnapshot {
    var babyName: String
    var backupToken: String
}
struct FeedingReminderActivityAttributes {
    struct ContentState {
        var babyName: String
        var nextReminderAt: Date
        var phone: String
    }
}
""",
            )
            write_text(root / "App/iOS/XiaoNaiPing/Views/StressView.swift", "let value = \"stress\"\n")
            write_text(
                root / "App/iOS/XiaoNaiPingWidgets/XiaoNaiPingWidgets.swift",
                'struct OnlyWidget { let label = "健康建议" }\n',
            )
            write_text(
                root / "App/iOS/XiaoNaiPing/Models/AppNotificationScheduler.swift",
                'registerForRemoteNotifications()\nlet title = "医疗建议"\n',
            )
            write_text(
                root / "App/iOS/XiaoNaiPing/Views/FeedingRecordView.swift",
                'struct FeedingRecordView { let title = "提醒" }\n',
            )
            write_text(
                root / "App/iOS/XiaoNaiPing/Views/ProfileView.swift",
                "struct ProfileView { let label = \"灵动岛\"; let debug = \"debug_wechat_ios\" }\n",
            )
            write_text(
                root / "App/iOS/XiaoNaiPing/Services/CloudBackupController.swift",
                "final class CloudBackupController {}\n",
            )
            write_text(
                root / "App/iOS/XiaoNaiPing/Services/CloudBackupAPIClient.swift",
                "final class CloudBackupAPIClient {}\n",
            )
            write_text(
                root / "App/iOS/XiaoNaiPing/Models/BabyRecordStore.swift",
                "final class BabyRecordStore {}\n",
            )

            report = self.run_checker(app, root)

            self.assertFalse(report["passed"])
            self.assertIn("releaseApiBaseURLMatches", report["failedRequiredChecks"])
            self.assertIn("liveActivitiesEnabledInAppPlist", report["failedRequiredChecks"])
            self.assertIn("widgetExtensionPointIsWidgetKit", report["failedRequiredChecks"])
            self.assertIn("widgetBundleIncludesTodayAndLiveActivity", report["failedRequiredChecks"])
            self.assertIn("localNotificationSchedulerPresent", report["failedRequiredChecks"])
            self.assertIn("remotePushNotConfigured", report["failedRequiredChecks"])
            self.assertIn("localNotificationPermissionDecisionPathsPresent", report["failedRequiredChecks"])
            self.assertIn("feedingNotificationCancellationPathPresent", report["failedRequiredChecks"])
            self.assertIn("feedingReminderLiveActivitySaveCancelPathsPresent", report["failedRequiredChecks"])
            self.assertIn("localNotificationDeniedAndFailureCopyPresent", report["failedRequiredChecks"])
            self.assertIn("feedingLiveActivityToggleControlPresent", report["failedRequiredChecks"])
            self.assertIn("feedingLiveActivityPreferencePersisted", report["failedRequiredChecks"])
            self.assertIn("accountBackupReviewEntryPresent", report["failedRequiredChecks"])
            self.assertIn("accountLoginClientSurfacesPresent", report["failedRequiredChecks"])
            self.assertIn("cloudBackupRestoreDeleteClientSurfacesPresent", report["failedRequiredChecks"])
            self.assertIn("accountBackupReviewSurfaceAvoidsDebugSubstitutes", report["failedRequiredChecks"])
            self.assertIn("cloudBackupControllerCoreFlowsPresent", report["failedRequiredChecks"])
            self.assertIn("cloudBackupServiceEndpointsPresent", report["failedRequiredChecks"])
            self.assertIn("sharedWidgetSnapshotPayloadIsScoped", report["failedRequiredChecks"])
            self.assertIn("liveActivityPayloadIsScoped", report["failedRequiredChecks"])
            self.assertIn("widgetAndLiveActivityCopyAvoidsHealthClaims", report["failedRequiredChecks"])
            self.assertIn("localNotificationCopyAvoidsHealthClaims", report["failedRequiredChecks"])
            self.assertIn("mainAppReviewSurfaceAvoidsHealthClaims", report["failedRequiredChecks"])
            self.assertIn("noHealthKitOrPressureSourceSurface", report["failedRequiredChecks"])

    def test_main_app_review_surface_health_claims_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            app = write_complete_fixture(root)
            write_text(root / "App/iOS/XiaoNaiPing/Views/HomeView.swift", 'let claim = "健康建议"\n')

            report = self.run_checker(app, root)

            self.assertFalse(report["passed"])
            self.assertIn("mainAppReviewSurfaceAvoidsHealthClaims", report["failedRequiredChecks"])


if __name__ == "__main__":
    unittest.main()
