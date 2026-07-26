import Foundation

struct Milestone: Identifiable, Equatable, Codable {
    var id = UUID()
    var title: String
    /// 兼容旧数据的显示字符串。真实日期以 occurredAt 为准；
    /// 旧版曾把“今天”“5月27日”这类相对/无年份文本存进来，导致日期无法还原。
    var date: String
    var icon: String
    var note: String? = nil
    /// 纪念日的真实日期。新保存的记录必填；旧数据由 store 尽力回填。
    var occurredAt: Date? = nil

    private enum CodingKeys: String, CodingKey {
        case id
        case title
        case date
        case icon
        case note
        case occurredAt
    }
}

extension Milestone {
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        title = try container.decodeIfPresent(String.self, forKey: .title) ?? ""
        date = try container.decodeIfPresent(String.self, forKey: .date) ?? ""
        icon = try container.decodeIfPresent(String.self, forKey: .icon) ?? ""
        note = try container.decodeIfPresent(String.self, forKey: .note)
        occurredAt = try container.decodeIfPresent(Date.self, forKey: .occurredAt)
    }
}

struct AutomaticMilestone: Identifiable {
    let title: String
    let dayNumber: Int
    let date: Date
    let daysRemaining: Int
    let isReached: Bool

    var id: Int { dayNumber }
}
