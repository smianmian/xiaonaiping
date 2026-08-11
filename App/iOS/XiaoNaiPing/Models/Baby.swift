import Foundation

struct Baby: Identifiable, Equatable, Codable {
    var id: UUID
    var name: String
    var daysSinceBirth: Int
    var ageText: String
    var birthDate: Date = Date()
    var sex: String = "未设置"
    var avatarImageData: Data? = nil
    var updatedAt: Date = Date()

    private enum CodingKeys: String, CodingKey {
        case id
        case name
        case daysSinceBirth
        case ageText
        case birthDate
        case sex
        case avatarImageData
        case updatedAt
    }
}

extension Baby {
    // 逐字段容错：单个字段缺失/损坏不应让整份档案（乃至整份本地状态）解码失败。
    // id 兜底必须是全新 UUID，绝不能复用 RecordCodingDefaults.babyId 之类的哨兵值。
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        name = try container.decodeIfPresent(String.self, forKey: .name) ?? "宝宝"
        daysSinceBirth = try container.decodeIfPresent(Int.self, forKey: .daysSinceBirth) ?? 0
        ageText = try container.decodeIfPresent(String.self, forKey: .ageText) ?? ""
        birthDate = try container.decodeIfPresent(Date.self, forKey: .birthDate) ?? Date()
        sex = try container.decodeIfPresent(String.self, forKey: .sex) ?? "未设置"
        avatarImageData = try container.decodeIfPresent(Data.self, forKey: .avatarImageData)
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? Date()
    }
}
