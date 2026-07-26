import Foundation

/// 家庭成员身份信息（服务端 /v1/family 返回）。
struct FamilyInfo: Codable, Equatable {
    var familyId: String
    var role: String
    var inviteCode: String
    var memberCount: Int
}

struct FamilyInfoResponse: Codable {
    var family: FamilyInfo?
}

/// 逐条同步的信封：payload 是记录本体的 JSON 文本，
/// LWW 冲突用 updatedAtMs 毫秒时间戳（新者胜），删除用 deletedAtMs 墓碑。
struct FamilyRecordEnvelope: Codable {
    var recordType: String
    var recordId: String
    var payload: String
    var updatedAtMs: Int
    var deletedAtMs: Int?
    var mine: Bool?
}

struct FamilyPushRequest: Codable {
    var records: [FamilyRecordEnvelope]
}

struct FamilyPushResponse: Codable {
    var accepted: Int
    var staleSkipped: Int
    var cursor: Int
}

struct FamilyPullResponse: Codable {
    var records: [FamilyRecordEnvelope]
    var cursor: Int
    var hasMore: Bool
}

/// 本地删除的墓碑：随状态一起持久化，推送给家庭成员后仍保留一段时间，
/// 保证晚上线的设备也能收到删除。
struct FamilyTombstone: Codable, Equatable, Identifiable {
    var recordType: String
    var recordId: String
    var deletedAt: Date

    var id: String { "\(recordType)-\(recordId)" }
}

enum FamilyRecordType: String, CaseIterable {
    case feeding
    case water
    case sleep
    case diaper
    case growth
    case vaccine
    case milestone
    case health
}
