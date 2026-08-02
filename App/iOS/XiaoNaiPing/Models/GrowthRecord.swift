import Foundation

enum GrowthWeightUnit: String, CaseIterable, Codable {
    case kilograms
    case jin

    var label: String {
        switch self {
        case .kilograms: "kg"
        case .jin: "斤"
        }
    }

    private var kilogramsPerUnit: Double {
        switch self {
        case .kilograms: 1
        case .jin: 0.5
        }
    }

    func value(fromKilograms kilograms: Double) -> Double {
        kilograms / kilogramsPerUnit
    }

    func kilograms(from value: Double) -> Double {
        value * kilogramsPerUnit
    }
}

struct GrowthRecord: Identifiable, Equatable, Codable {
    var id = UUID()
    /// 多宝宝：记录归属；旧数据缺省用 legacy 默认值，迁移时归到首个宝宝。
    var babyId: UUID = RecordCodingDefaults.babyId
    var month: String
    /// 始终以 kg 保存，保证 WHO 曲线和跨设备数据的口径一致。
    var weight: Double
    /// 用户录入时选择的显示单位；旧记录缺省为 kg。
    var weightUnit: GrowthWeightUnit = .kilograms
    var height: Double
    var head: Double
    var measuredAt: String = ""
    var note: String? = nil
    /// 家人共享 LWW 用的最后修改时间；旧数据缺省回退到 distantPast。
    var updatedAt: Date = Date()

    private enum CodingKeys: String, CodingKey {
        case id
        case babyId
        case month
        case weight
        case weightUnit
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
        babyId = try container.decodeIfPresent(UUID.self, forKey: .babyId) ?? RecordCodingDefaults.babyId
        month = try container.decodeIfPresent(String.self, forKey: .month) ?? ""
        weight = try container.decodeIfPresent(Double.self, forKey: .weight) ?? 0
        weightUnit = try container.decodeIfPresent(GrowthWeightUnit.self, forKey: .weightUnit) ?? .kilograms
        height = try container.decodeIfPresent(Double.self, forKey: .height) ?? 0
        head = try container.decodeIfPresent(Double.self, forKey: .head) ?? 0
        measuredAt = try container.decodeIfPresent(String.self, forKey: .measuredAt) ?? ""
        note = try container.decodeIfPresent(String.self, forKey: .note)
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? .distantPast
    }
}
