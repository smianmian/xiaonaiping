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

struct CloudSyncPayload: Codable {
    var schemaVersion: Int
    var generatedAt: Date
    var hasCompletedOnboarding: Bool
    var baby: Baby
    /// 多宝宝：schemaVersion 2 起携带；老包只有单个 baby。
    var babies: [Baby]?
    var activeBabyID: UUID?
    var feedingRecords: [FeedingRecord]
    var waterRecords: [WaterRecord]
    var sleepRecords: [SleepRecord]
    var diaperRecords: [DiaperRecord]
    var growthRecords: [GrowthRecord]
    var vaccineRecords: [VaccineRecord]
    var milestones: [Milestone]
    var babyPhotos: [BabyPhoto]

    private enum CodingKeys: String, CodingKey {
        case schemaVersion, generatedAt, hasCompletedOnboarding, baby, babies, activeBabyID, feedingRecords, waterRecords, sleepRecords, diaperRecords, growthRecords, vaccineRecords, milestones, babyPhotos
    }

    init(
        schemaVersion: Int,
        generatedAt: Date,
        hasCompletedOnboarding: Bool,
        baby: Baby,
        babies: [Baby]? = nil,
        activeBabyID: UUID? = nil,
        feedingRecords: [FeedingRecord],
        waterRecords: [WaterRecord] = [],
        sleepRecords: [SleepRecord],
        diaperRecords: [DiaperRecord],
        growthRecords: [GrowthRecord],
        vaccineRecords: [VaccineRecord],
        milestones: [Milestone],
        babyPhotos: [BabyPhoto]
    ) {
        self.schemaVersion = schemaVersion
        self.generatedAt = generatedAt
        self.hasCompletedOnboarding = hasCompletedOnboarding
        self.baby = baby
        self.babies = babies
        self.activeBabyID = activeBabyID
        self.feedingRecords = feedingRecords
        self.waterRecords = waterRecords
        self.sleepRecords = sleepRecords
        self.diaperRecords = diaperRecords
        self.growthRecords = growthRecords
        self.vaccineRecords = vaccineRecords
        self.milestones = milestones
        self.babyPhotos = babyPhotos
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try container.decode(Int.self, forKey: .schemaVersion)
        generatedAt = try container.decode(Date.self, forKey: .generatedAt)
        hasCompletedOnboarding = try container.decode(Bool.self, forKey: .hasCompletedOnboarding)
        baby = try container.decode(Baby.self, forKey: .baby)
        babies = try container.decodeIfPresent([Baby].self, forKey: .babies)
        activeBabyID = try container.decodeIfPresent(UUID.self, forKey: .activeBabyID)
        feedingRecords = try container.decode([FeedingRecord].self, forKey: .feedingRecords)
        waterRecords = try container.decodeIfPresent([WaterRecord].self, forKey: .waterRecords) ?? []
        sleepRecords = try container.decode([SleepRecord].self, forKey: .sleepRecords)
        diaperRecords = try container.decode([DiaperRecord].self, forKey: .diaperRecords)
        growthRecords = try container.decode([GrowthRecord].self, forKey: .growthRecords)
        vaccineRecords = try container.decode([VaccineRecord].self, forKey: .vaccineRecords)
        milestones = try container.decode([Milestone].self, forKey: .milestones)
        babyPhotos = try container.decode([BabyPhoto].self, forKey: .babyPhotos)
    }
}

struct LocalPhotoSyncAsset {
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
    var syncDeleted: Bool
    var photoCountDeleted: Int
}

struct CloudSyncStatusResponse: Decodable, Equatable {
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

enum CloudSyncError: LocalizedError {
    case missingBaseURL
    case missingSession
    case invalidPhoneNumber
    case invalidVerificationCode
    case invalidResponse
    case server(String)

    var errorDescription: String? {
        switch self {
        case .missingBaseURL:
            return "账号服务暂不可用，请稍后重试。"
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
