import Foundation

struct VaccineRecord: Identifiable, Equatable, Codable {
    static let pendingStatus = "待接种"
    static let bookedStatus = "已预约"
    static let administeredStatus = "已接种"
    static let legacyCompletedStatus = "已完成"

    var id = UUID()
    /// 多宝宝：记录归属；旧数据缺省用 legacy 默认值，迁移时归到首个宝宝。
    var babyId: UUID = RecordCodingDefaults.babyId
    var title: String
    var status: String
    var tintName: String
    var icon: String
    var dueText: String = ""
    var dueDays: Int? = nil
    var region: String? = nil
    var note: String? = nil
    var administeredAt: Date? = nil
    /// 家人共享 LWW 用的最后修改时间；旧数据缺省回退到 distantPast。
    var updatedAt: Date = Date()

    var isAdministered: Bool {
        status == Self.administeredStatus || status == Self.legacyCompletedStatus
    }

    var displayStatus: String {
        isAdministered ? Self.administeredStatus : status
    }

    private enum CodingKeys: String, CodingKey {
        case id
        case babyId
        case title
        case status
        case tintName
        case icon
        case dueText
        case dueDays
        case region
        case note
        case administeredAt
        case updatedAt
    }
}

extension VaccineRecord {
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        babyId = try container.decodeIfPresent(UUID.self, forKey: .babyId) ?? RecordCodingDefaults.babyId
        title = try container.decodeIfPresent(String.self, forKey: .title) ?? ""
        status = try container.decodeIfPresent(String.self, forKey: .status) ?? Self.pendingStatus
        tintName = try container.decodeIfPresent(String.self, forKey: .tintName) ?? "orange"
        icon = try container.decodeIfPresent(String.self, forKey: .icon) ?? ""
        dueText = try container.decodeIfPresent(String.self, forKey: .dueText) ?? ""
        dueDays = try container.decodeIfPresent(Int.self, forKey: .dueDays)
        region = try container.decodeIfPresent(String.self, forKey: .region)
        note = try container.decodeIfPresent(String.self, forKey: .note)
        administeredAt = try container.decodeIfPresent(Date.self, forKey: .administeredAt)
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? .distantPast
    }
}
