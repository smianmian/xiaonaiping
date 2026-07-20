import Combine
import Foundation

@MainActor
final class CloudBackupController: ObservableObject {
    @Published private(set) var isWorking = false
    @Published private(set) var isSyncing = false
    @Published private(set) var statusTitle = "未登录"
    @Published private(set) var statusDetail = "登录后会自动同步宝宝资料、记录和照片。"

    private let sessionStore = CloudAccountSessionStore()
    private var scheduledSyncTask: Task<Void, Never>?

    init() {
        if sessionStore.session != nil {
            statusTitle = "已登录"
            statusDetail = "资料会自动同步到你的账号。"
        } else if !isServiceConfigured {
            statusTitle = "同步服务暂不可用"
            statusDetail = "请检查网络后重试自动同步。"
        }
    }

    var hasSession: Bool {
        sessionStore.session != nil
    }

    var isServiceConfigured: Bool {
        CloudBackupConfiguration.apiBaseURL != nil
    }

    var serviceStatusLabel: String {
        hasSession ? "自动同步" : (isServiceConfigured ? "请登录" : "未配置")
    }

    var isWeChatLoginConfigured: Bool {
        isNativeWeChatLoginConfigured
    }

    var isNativeWeChatLoginConfigured: Bool {
        CloudBackupConfiguration.isWeChatLoginConfigured
    }

    var isNativeWeChatLoginAvailable: Bool {
        isNativeWeChatLoginConfigured && WeChatLoginService.shared.isNativeLoginAvailable
    }

    var isDebugWeChatLoginAvailable: Bool {
        #if DEBUG
        return isServiceConfigured
        #else
        return false
        #endif
    }

    var accountSummary: String {
        guard let accountId = sessionStore.session?.accountId else { return "未登录" }
        let provider = sessionStore.session?.authProvider ?? "账号"
        return "\(provider) · " + String(accountId.prefix(8)) + "..."
    }

    func requestPhoneCode(phoneNumber: String) async {
        await perform("正在发送验证码", "正在请求手机号登录验证码。") {
            let normalizedPhoneNumber = normalizePhoneNumber(phoneNumber)
            guard Self.validateE164PhoneNumber(normalizedPhoneNumber) else {
                throw CloudBackupError.invalidPhoneNumber
            }

            let client = try makeClient()
            let response = try await client.requestPhoneCode(phoneNumber: normalizedPhoneNumber)
            statusTitle = response.sent ? "验证码已发送" : "验证码未发送"
            statusDetail = "验证码有效期约 \(response.expiresInSeconds / 60) 分钟。"
        }
    }

    func verifyPhoneCode(phoneNumber: String, code: String, store: BabyRecordStore) async {
        await perform("正在登录", "正在验证手机号验证码。") {
            let normalizedPhoneNumber = normalizePhoneNumber(phoneNumber)
            let normalizedCode = normalizeVerificationCode(code)
            guard Self.validateE164PhoneNumber(normalizedPhoneNumber) else {
                throw CloudBackupError.invalidPhoneNumber
            }
            guard Self.validateSmsCode(normalizedCode) else {
                throw CloudBackupError.invalidVerificationCode
            }

            let client = try makeClient()
            let session = try await client.verifyPhoneCode(phoneNumber: normalizedPhoneNumber, code: normalizedCode)
            await completeLogin(session, client: client, store: store, provider: "phone")
        }
    }

    func loginWithWeChat(store: BabyRecordStore) async {
        await perform("正在登录微信", "正在通过微信授权登录。") {
            guard isNativeWeChatLoginAvailable else {
                throw CloudBackupError.server("当前设备无法使用微信授权，请改用手机号登录。")
            }

            let client = try makeClient()
            let code = try await WeChatLoginService.shared.requestAuthorizationCode()
            let session = try await client.loginWithWeChat(code: code)
            await completeLogin(session, client: client, store: store, provider: "wechat")
        }
    }

    func scheduleAutomaticSync(store: BabyRecordStore) {
        guard hasSession, store.hasCompletedOnboarding else { return }
        scheduledSyncTask?.cancel()
        scheduledSyncTask = Task { [weak self, weak store] in
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            guard !Task.isCancelled, let self, let store else { return }
            await self.syncIfNeeded(store: store)
        }
    }

    func syncIfNeeded(store: BabyRecordStore) async {
        guard hasSession, store.hasCompletedOnboarding, !isSyncing else { return }
        guard let session = sessionStore.session else { return }

        isSyncing = true
        statusTitle = "正在同步"
        statusDetail = "正在安全上传资料和照片。"
        defer { isSyncing = false }

        do {
            let client = try makeClient()
            try await uploadEverything(store: store, client: client, token: session.sessionToken)
            statusTitle = "已同步"
            statusDetail = "资料和照片已自动保存到服务器。"
        } catch {
            statusTitle = "待同步"
            statusDetail = "联网后会自动重试同步。"
        }
    }

    func deleteCloudPhoto(_ photo: BabyPhoto) async -> Bool {
        isWorking = true
        statusTitle = "正在删除照片"
        statusDetail = "正在删除云端照片原图。"
        defer { isWorking = false }

        do {
            let client = try makeClient()
            guard let session = sessionStore.session else { throw CloudBackupError.missingSession }
            try await client.deletePhoto(id: photo.id, token: session.sessionToken)
            statusTitle = "云端照片已删除"
            statusDetail = "照片原图已从服务器删除。"
            return true
        } catch {
            statusTitle = "照片删除失败"
            statusDetail = "照片删除会在联网后自动重试。"
            return false
        }
    }

    func deleteCloudAccount(store: BabyRecordStore) async {
        await perform("正在删除", "正在删除账号、云端记录和照片原图。") {
            let client = try makeClient()
            guard let session = sessionStore.session else { throw CloudBackupError.missingSession }
            let response = try await client.deleteAccount(token: session.sessionToken)
            sessionStore.clear()
            store.markCloudAccountDeletedLocally()
            statusTitle = "云端已删除"
            statusDetail = "账号和同步资料已删除，照片原图删除数量：\(response.photoCountDeleted)。"
        }
    }

    func signOut() {
        scheduledSyncTask?.cancel()
        sessionStore.clear()
        statusTitle = "已退出账号"
        statusDetail = "已退出当前账号；下次登录后会恢复自动同步。"
    }

    static func validateE164PhoneNumber(_ phoneNumber: String) -> Bool {
        guard phoneNumber.hasPrefix("+") else { return false }
        let digits = phoneNumber.dropFirst()
        guard (7...15).contains(digits.count), let firstDigit = digits.first, firstDigit != "0" else { return false }
        return digits.allSatisfy(\.isWholeNumber)
    }

    static func validateSmsCode(_ code: String) -> Bool {
        let trimmed = code.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.count == 6 && trimmed.allSatisfy(\.isWholeNumber)
    }

    private func completeLogin(
        _ session: CloudAccountSession,
        client: CloudBackupAPIClient,
        store: BabyRecordStore,
        provider: String
    ) async {
        sessionStore.save(session)
        await trackAnalyticsEvent(
            "login_completed",
            properties: ["authProvider": provider, "source": "app", "feature": "account"],
            client: client,
            token: session.sessionToken
        )

        if store.hasCompletedOnboarding {
            await syncIfNeeded(store: store)
            return
        }

        do {
            try await restoreRemoteData(store: store, client: client, token: session.sessionToken)
            statusTitle = "已登录"
            statusDetail = "已恢复服务器中的宝宝资料。"
        } catch {
            statusTitle = "已登录"
            statusDetail = "完成建档后会自动同步到服务器。"
        }
    }

    private func restoreRemoteData(store: BabyRecordStore, client: CloudBackupAPIClient, token: String) async throws {
        let backupData = try await client.downloadBackup(token: token)
        try store.restoreCloudBackupData(backupData)

        let availablePhotos = try await client.listPhotos(token: token)
        let availablePhotoIDs = Set(availablePhotos.map(\.photoId))
        for photo in store.babyPhotos where availablePhotoIDs.contains(photo.id.uuidString) {
            let data = try await client.downloadPhoto(id: photo.id, token: token)
            try store.restoreCloudPhotoData(for: photo, data: data)
        }
    }

    private func uploadEverything(store: BabyRecordStore, client: CloudBackupAPIClient, token: String) async throws {
        _ = try await client.uploadBackup(store.encodedCloudBackupData(), token: token)
        for asset in store.localPhotoBackupAssets() {
            let data = try Data(contentsOf: asset.fileURL)
            try await client.uploadPhoto(id: asset.photo.id, data: data, token: token)
            store.markCloudPhotoBackedUp(asset.photo)
        }
        store.markCloudBackupCompleted()
        _ = try await client.uploadBackup(store.encodedCloudBackupData(), token: token)
    }

    private func perform(_ workingTitle: String, _ workingDetail: String, operation: () async throws -> Void) async {
        isWorking = true
        statusTitle = workingTitle
        statusDetail = workingDetail
        do {
            try await operation()
        } catch {
            statusTitle = "操作失败"
            statusDetail = error.localizedDescription
        }
        isWorking = false
    }

    private func normalizePhoneNumber(_ phoneNumber: String) -> String {
        String(phoneNumber.filter { $0 == "+" || $0.isWholeNumber })
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func normalizeVerificationCode(_ code: String) -> String {
        code.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func makeClient() throws -> CloudBackupAPIClient {
        guard let baseURL = CloudBackupConfiguration.apiBaseURL else {
            throw CloudBackupError.missingBaseURL
        }
        return CloudBackupAPIClient(baseURL: baseURL)
    }

    private func trackAnalyticsEvent(
        _ name: String,
        properties: [String: String],
        client: CloudBackupAPIClient,
        token: String
    ) async {
        var safeProperties = properties
        safeProperties["platform"] = "ios"
        try? await client.trackAnalyticsEvent(name: name, properties: safeProperties, token: token)
    }
}
