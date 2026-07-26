import Foundation

struct GrowthRecord: Identifiable, Equatable, Codable {
    var id = UUID()
    var month: String
    var weight: Double
    var height: Double
    var head: Double
    var measuredAt: String = ""
    var note: String? = nil
    /// 家人共享 LWW 用的最后修改时间；旧数据缺省回退到 distantPast。
    var updatedAt: Date = Date()

    private enum CodingKeys: String, CodingKey {
        case id
        case month
        case weight
        case height
        case head
        case measuredAt
        case note
        case updatedAt
    }
}

extension GrowthRecord {
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        month = try container.decodeIfPresent(String.self, forKey: .month) ?? ""
        weight = try container.decodeIfPresent(Double.self, forKey: .weight) ?? 0
        height = try container.decodeIfPresent(Double.self, forKey: .height) ?? 0
        head = try container.decodeIfPresent(Double.self, forKey: .head) ?? 0
        measuredAt = try container.decodeIfPresent(String.self, forKey: .measuredAt) ?? ""
        note = try container.decodeIfPresent(String.self, forKey: .note)
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? .distantPast
    }
}
