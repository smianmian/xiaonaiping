import Foundation

@MainActor
final class CloudBackupController: ObservableObject {
    @Published private(set) var isWorking = false
    @Published private(set) var statusTitle = "未开启"
    @Published private(set) var statusDetail = "还没有创建云端账号。"
    @Published var recoveryKeyToShow: String?

    private let sessionStore = CloudAccountSessionStore()

    init() {
        if sessionStore.session != nil {
            statusTitle = "已登录"
            statusDetail = "可以继续备份或恢复同一账号下的资料。"
        } else if !isServiceConfigured {
            statusDetail = "云端服务尚未开放，当前记录只保存在本机。"
        }
    }

    var hasSession: Bool {
        sessionStore.session != nil
    }

    var isServiceConfigured: Bool {
        CloudBackupConfiguration.apiBaseURL != nil
    }

    var serviceStatusLabel: String {
        if hasSession {
            return "已开启"
        }
        return isServiceConfigured ? "可开启" : "未配置"
    }

    var isWeChatLoginConfigured: Bool {
        isNativeWeChatLoginConfigured || isDebugWeChatLoginAvailable
    }

    var isNativeWeChatLoginConfigured: Bool {
        CloudBackupConfiguration.isWeChatLoginConfigured
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

    func createAccountAndBackup(store: BabyRecordStore) async {
        await perform("正在备份", "正在加密通道上传记录与照片原图。") {
            let client = try makeClient()
            var session = sessionStore.session
            if session == nil {
                let created = try await client.createAccount()
                sessionStore.save(created)
                session = created
                recoveryKeyToShow = created.recoveryKey
                await trackAnalyticsEvent(
                    "account_created",
                    properties: ["authProvider": "recovery_key", "source": "backup", "feature": "account"],
                    client: client,
                    token: created.sessionToken
                )
            }

            guard let session else { throw CloudBackupError.missingSession }
            try await uploadEverything(store: store, client: client, token: session.sessionToken)
            await trackAnalyticsEvent(
                "cloud_backup_completed",
                properties: ["source": "backup", "result": "success", "feature": "cloud_backup"],
                client: client,
                token: session.sessionToken
            )
            statusTitle = "已备份"
            statusDetail = "最近一次备份完成；本机记录和照片原图已上传到私有账号空间。"
        }
    }

    func requestPhoneCode(phoneNumber: String) async {
        await perform("正在发送验证码", "正在请求手机号登录验证码。") {
            let normalizedPhoneNumber = normalizePhoneNumber(phoneNumber)
            guard !normalizedPhoneNumber.isEmpty else {
                throw CloudBackupError.invalidPhoneNumber
            }
            guard Self.validateE164PhoneNumber(normalizedPhoneNumber) else {
                throw CloudBackupError.invalidPhoneNumber
            }

            let client = try makeClient()
            let response = try await client.requestPhoneCode(phoneNumber: normalizedPhoneNumber)
            statusTitle = response.sent ? "验证码已发送" : "验证码未发送"
            if let debugCode = response.debugCode {
                statusDetail = "Debug 验证码：\(debugCode)。生产环境必须接入真实短信服务。"
            } else {
                statusDetail = "验证码有效期约 \(response.expiresInSeconds / 60) 分钟。"
            }
        }
    }

    func verifyPhoneCode(phoneNumber: String, code: String) async {
        await perform("正在登录", "正在验证手机号验证码。") {
            let normalizedPhoneNumber = normalizePhoneNumber(phoneNumber)
            let normalizedCode = normalizeVerificationCode(code)
            guard !normalizedPhoneNumber.isEmpty, Self.validateE164PhoneNumber(normalizedPhoneNumber) else {
                throw CloudBackupError.invalidPhoneNumber
            }
            guard !normalizedCode.isEmpty, Self.validateSmsCode(normalizedCode) else {
                throw CloudBackupError.invalidVerificationCode
            }

            let client = try makeClient()
            let session = try await client.verifyPhoneCode(phoneNumber: normalizedPhoneNumber, code: normalizedCode)
            sessionStore.save(session)
            recoveryKeyToShow = session.recoveryKey
            await trackAnalyticsEvent(
                "login_completed",
                properties: ["authProvider": "phone", "source": "profile", "feature": "account"],
                client: client,
                token: session.sessionToken
            )
            if session.recoveryKey != nil {
                await trackAnalyticsEvent(
                    "account_created",
                    properties: ["authProvider": "phone", "source": "profile", "feature": "account"],
                    client: client,
                    token: session.sessionToken
                )
            }
            statusTitle = "手机号已登录"
            statusDetail = "手机号登录已连接到私有备份账号。"
        }
    }

    static func validateE164PhoneNumber(_ phoneNumber: String) -> Bool {
        guard phoneNumber.hasPrefix("+") else { return false }
        let digits = phoneNumber.dropFirst()
        guard (7...15).contains(digits.count) else { return false }
        guard let firstDigit = digits.first, firstDigit != "0" else { return false }
        return digits.allSatisfy { $0.isWholeNumber }
    }

    static func validateSmsCode(_ code: String) -> Bool {
        let trimmed = code.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.count == 6 && !trimmed.isEmpty && trimmed.allSatisfy(\.isWholeNumber)
    }

    func recoverSession(recoveryKey: String) async {
        await perform("正在登录", "正在使用恢复密钥连接账号。") {
            let client = try makeClient()
            let trimmedKey = recoveryKey.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !trimmedKey.isEmpty else { throw CloudBackupError.missingRecoveryKey }
            let session = try await client.recoverSession(recoveryKey: trimmedKey)
            sessionStore.save(session)
            await trackAnalyticsEvent(
                "login_completed",
                properties: ["authProvider": "recovery_key", "source": "profile", "feature": "account"],
                client: client,
                token: session.sessionToken
            )
            statusTitle = "账号已恢复"
            statusDetail = "已连接原来的私有备份账号，可以继续恢复云端资料。"
        }
    }

    func loginWithWeChat() async {
        await perform("正在登录微信", "正在通过微信授权登录。") {
            let client = try makeClient()
            if CloudBackupConfiguration.isWeChatLoginConfigured {
                let code = try await WeChatLoginService.shared.requestAuthorizationCode()
                let session = try await client.loginWithWeChat(code: code)
                await finishWeChatLogin(
                    session,
                    client: client,
                    detail: "微信授权已连接到私有备份账号。"
                )
                return
            }

            #if DEBUG
            let session = try await client.loginWithWeChat(code: "debug_wechat_ios")
            await finishWeChatLogin(
                session,
                client: client,
                detail: "Debug 微信登录已连接到私有备份账号。配置微信开放平台后会优先拉起真实微信授权。"
            )
            #else
            throw CloudBackupError.server("微信登录未启用：请先完成微信 OpenSDK、AppID、URL Scheme、Universal Link 和服务端凭证配置。")
            #endif
        }
    }

    private func finishWeChatLogin(
        _ session: CloudAccountSession,
        client: CloudBackupAPIClient,
        detail: String
    ) async {
        sessionStore.save(session)
        recoveryKeyToShow = session.recoveryKey
        await trackAnalyticsEvent(
            "login_completed",
            properties: ["authProvider": "wechat", "source": "profile", "feature": "account"],
            client: client,
            token: session.sessionToken
        )
        if session.recoveryKey != nil {
            await trackAnalyticsEvent(
                "account_created",
                properties: ["authProvider": "wechat", "source": "profile", "feature": "account"],
                client: client,
                token: session.sessionToken
            )
        }
        statusTitle = "微信已登录"
        statusDetail = detail
    }

    func restoreLatestBackup(store: BabyRecordStore) async {
        await perform("正在恢复", "正在从云端恢复同一账号下的记录与照片。") {
            let client = try makeClient()
            guard let session = sessionStore.session else { throw CloudBackupError.missingSession }
            let backupData = try await client.downloadBackup(token: session.sessionToken)
            try store.restoreCloudBackupData(backupData)

            let availablePhotos = try await client.listPhotos(token: session.sessionToken)
            let availablePhotoIDs = Set(availablePhotos.map(\.photoId))
            for photo in store.babyPhotos where availablePhotoIDs.contains(photo.id.uuidString) {
                let data = try await client.downloadPhoto(id: photo.id, token: session.sessionToken)
                try store.restoreCloudPhotoData(for: photo, data: data)
            }

            statusTitle = "已恢复"
            statusDetail = "云端记录已恢复到本机；可恢复的照片原图也已写回 App 私有空间。"
            await trackAnalyticsEvent(
                "cloud_restore_completed",
                properties: ["source": "restore", "result": "success", "feature": "cloud_restore"],
                client: client,
                token: session.sessionToken
            )
        }
    }

    func deleteCloudPhoto(_ photo: BabyPhoto) async -> Bool {
        isWorking = true
        statusTitle = "正在删除照片"
        statusDetail = "正在删除私有账号空间里的照片原图。"
        defer { isWorking = false }

        do {
            let client = try makeClient()
            guard let session = sessionStore.session else { throw CloudBackupError.missingSession }
            try await client.deletePhoto(id: photo.id, token: session.sessionToken)
            statusTitle = "云端照片已删除"
            statusDetail = "照片原图已从私有账号空间删除。"
            return true
        } catch {
            statusTitle = "照片删除失败"
            statusDetail = error.localizedDescription
            return false
        }
    }

    func deleteCloudAccount(store: BabyRecordStore) async {
        await perform("正在删除", "正在删除账号、云端备份和云端照片原图。") {
            let client = try makeClient()
            guard let session = sessionStore.session else { throw CloudBackupError.missingSession }
            let response = try await client.deleteAccount(token: session.sessionToken)
            sessionStore.clear()
            store.markCloudAccountDeletedLocally()
            statusTitle = "云端已删除"
            statusDetail = "账号和云端备份已删除，照片原图删除数量：\(response.photoCountDeleted)。本机资料仍保留。"
        }
    }

    func clearRecoveryKeyNotice() {
        recoveryKeyToShow = nil
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
        do {
            try await client.trackAnalyticsEvent(name: name, properties: safeProperties, token: token)
        } catch {
            return
        }
    }
}
