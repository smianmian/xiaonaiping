import Foundation

struct CloudAccountSession: Codable, Equatable {
    var accountId: String
    var sessionToken: String
    var createdAt: String?
    var authProvider: String?
}

struct PhoneCodeResponse: Decodable, Equatable {
    var sent: Bool
    var expiresInSeconds: Int
    var debugCode: String?
}

struct CloudBackupPayload: Codable {
    var schemaVersion: Int
    var generatedAt: Date
    var hasCompletedOnboarding: Bool
    var baby: Baby
    var feedingRecords: [FeedingRecord]
    var sleepRecords: [SleepRecord]
    var diaperRecords: [DiaperRecord]
    var growthRecords: [GrowthRecord]
    var vaccineRecords: [VaccineRecord]
    var milestones: [Milestone]
    var babyPhotos: [BabyPhoto]
}

struct LocalPhotoBackupAsset {
    var photo: BabyPhoto
    var fileURL: URL
}

struct CloudPhotoListResponse: Decodable {
    var photos: [CloudPhotoMetadata]
}

struct CloudPhotoMetadata: Decodable, Equatable {
    var photoId: String
    var contentType: String
    var sizeBytes: Int
    var sha256: String
    var updatedAt: String
}

struct CloudAccountDeletionResponse: Decodable, Equatable {
    var accountId: String
    var deletedAt: String
    var backupDeleted: Bool
    var photoCountDeleted: Int
}

struct CloudBackupStatusResponse: Decodable, Equatable {
    var updatedAt: String?
    var sizeBytes: Int?
}

struct CloudErrorEnvelope: Decodable {
    var error: CloudServerError
}

struct CloudServerError: Decodable {
    var code: String
    var message: String
}

enum CloudBackupError: LocalizedError {
    case missingBaseURL
    case missingSession
    case invalidPhoneNumber
    case invalidVerificationCode
    case invalidResponse
    case server(String)

    var errorDescription: String? {
        switch self {
        case .missingBaseURL:
            return "云端服务尚未配置。"
        case .missingSession:
            return "请先登录账号。"
        case .invalidPhoneNumber:
            return "手机号格式不正确。请使用以 + 开头的 E.164 格式，例如 +8613800138000。"
        case .invalidVerificationCode:
            return "验证码格式不正确。请填写 6 位数字。"
        case .invalidResponse:
            return "服务器返回内容无法识别。"
        case .server(let message):
            return message
        }
    }
}
