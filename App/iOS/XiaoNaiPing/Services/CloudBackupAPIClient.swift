import Foundation

struct CloudBackupConfiguration {
    static var apiBaseURL: URL? {
        for key in ["XNPAPIBaseURL", "XNP_API_BASE_URL"] {
            if let value = stringValue(forInfoDictionaryKey: key) {
                return URL(string: value)
            }
        }

        #if DEBUG
        if let value = normalizedConfigurationValue(ProcessInfo.processInfo.environment["XNP_API_BASE_URL"]) {
            return URL(string: value)
        }
        #endif

        return nil
    }

    static var weChatAppID: String? {
        stringValue(forInfoDictionaryKey: "XNPWeChatAppID")
    }

    static var weChatURLScheme: String? {
        stringValue(forInfoDictionaryKey: "XNPWeChatURLScheme")
    }

    static var weChatUniversalLink: URL? {
        guard let value = stringValue(forInfoDictionaryKey: "XNPWeChatUniversalLink") else {
            return nil
        }
        return URL(string: value)
    }

    static var isWeChatLoginConfigured: Bool {
        guard let appID = weChatAppID,
              let urlScheme = weChatURLScheme,
              let universalLink = weChatUniversalLink else {
            return false
        }
        return appID.hasPrefix("wx")
        && urlScheme.hasPrefix("wx")
        && universalLink.scheme?.lowercased() == "https"
        && universalLink.host?.isEmpty == false
    }

    private static func stringValue(forInfoDictionaryKey key: String) -> String? {
        normalizedConfigurationValue(Bundle.main.object(forInfoDictionaryKey: key) as? String)
    }

    private static func normalizedConfigurationValue(_ rawValue: String?) -> String? {
        guard let rawValue else {
            return nil
        }
        let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty, !value.contains("$(") else {
            return nil
        }
        return value
    }
}

private struct CloudAnalyticsEventsRequest: Encodable {
    var events: [CloudAnalyticsEventRequest]
}

private struct CloudAnalyticsEventRequest: Encodable {
    var eventId: String
    var name: String
    var occurredAt: String
    var properties: [String: String]
}

final class CloudBackupAPIClient {
    private let baseURL: URL
    private let urlSession: URLSession
    private let jsonDecoder = JSONDecoder()

    init(baseURL: URL, urlSession: URLSession = .shared) {
        self.baseURL = baseURL
        self.urlSession = urlSession
    }

    func createAccount() async throws -> CloudAccountSession {
        let data = try await request(path: "/v1/accounts", method: "POST", body: Data())
        return try decode(CloudAccountSession.self, from: data)
    }

    func recoverSession(recoveryKey: String) async throws -> CloudAccountSession {
        let body = try JSONEncoder().encode(["recoveryKey": recoveryKey])
        let data = try await request(path: "/v1/sessions/recover", method: "POST", body: body)
        return try decode(CloudAccountSession.self, from: data)
    }

    func requestPhoneCode(phoneNumber: String) async throws -> PhoneCodeResponse {
        let body = try JSONEncoder().encode(["phoneNumber": phoneNumber])
        let data = try await request(path: "/v1/auth/phone/request-code", method: "POST", body: body)
        return try decode(PhoneCodeResponse.self, from: data)
    }

    func verifyPhoneCode(phoneNumber: String, code: String) async throws -> CloudAccountSession {
        let body = try JSONEncoder().encode(["phoneNumber": phoneNumber, "code": code])
        let data = try await request(path: "/v1/auth/phone/verify", method: "POST", body: body)
        return try decode(CloudAccountSession.self, from: data)
    }

    func loginWithWeChat(code: String) async throws -> CloudAccountSession {
        let body = try JSONEncoder().encode(["code": code])
        let data = try await request(path: "/v1/auth/wechat/login", method: "POST", body: body)
        return try decode(CloudAccountSession.self, from: data)
    }

    func uploadBackup(_ data: Data, token: String) async throws -> CloudBackupStatusResponse {
        let responseData = try await request(path: "/v1/backup", method: "PUT", body: data, token: token)
        return try decode(CloudBackupStatusResponse.self, from: responseData)
    }

    func downloadBackup(token: String) async throws -> Data {
        try await request(path: "/v1/backup", method: "GET", token: token)
    }

    func uploadPhoto(id: UUID, data: Data, token: String) async throws {
        _ = try await request(
            path: "/v1/photos/\(id.uuidString)",
            method: "PUT",
            body: data,
            token: token,
            contentType: "image/jpeg"
        )
    }

    func listPhotos(token: String) async throws -> [CloudPhotoMetadata] {
        let data = try await request(path: "/v1/photos", method: "GET", token: token)
        return try decode(CloudPhotoListResponse.self, from: data).photos
    }

    func downloadPhoto(id: UUID, token: String) async throws -> Data {
        try await request(path: "/v1/photos/\(id.uuidString)", method: "GET", token: token)
    }

    func deletePhoto(id: UUID, token: String) async throws {
        _ = try await request(path: "/v1/photos/\(id.uuidString)", method: "DELETE", token: token)
    }

    func deleteAccount(token: String) async throws -> CloudAccountDeletionResponse {
        let data = try await request(path: "/v1/account", method: "DELETE", token: token)
        return try decode(CloudAccountDeletionResponse.self, from: data)
    }

    func trackAnalyticsEvent(name: String, properties: [String: String], token: String) async throws {
        let event = CloudAnalyticsEventRequest(
            eventId: UUID().uuidString,
            name: name,
            occurredAt: ISO8601DateFormatter().string(from: Date()),
            properties: properties
        )
        let body = try JSONEncoder().encode(CloudAnalyticsEventsRequest(events: [event]))
        _ = try await request(path: "/v1/analytics/events", method: "POST", body: body, token: token)
    }

    private func request(
        path: String,
        method: String,
        body: Data? = nil,
        token: String? = nil,
        contentType: String = "application/json"
    ) async throws -> Data {
        let url = baseURL.appendingPathComponent(path.trimmingCharacters(in: CharacterSet(charactersIn: "/")))
        var request = URLRequest(url: url)
        request.httpMethod = method
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            request.httpBody = body
            request.setValue(contentType, forHTTPHeaderField: "Content-Type")
        }

        let (data, response) = try await urlSession.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw CloudBackupError.invalidResponse
        }
        guard (200..<300).contains(httpResponse.statusCode) else {
            if let envelope = try? jsonDecoder.decode(CloudErrorEnvelope.self, from: data) {
                throw CloudBackupError.server(envelope.error.message)
            }
            throw CloudBackupError.server("云端请求失败：HTTP \(httpResponse.statusCode)")
        }
        return data
    }

    private func decode<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
        do {
            return try jsonDecoder.decode(type, from: data)
        } catch {
            throw CloudBackupError.invalidResponse
        }
    }
}
