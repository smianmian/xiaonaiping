import Foundation

/// 0-3 月核心健康观察：黄疸、体温、用药/补剂。
/// 黄疸和维生素 D 是新生儿父母最高频的两个焦虑点，
/// 记录本身不做任何医学判断，仅供就诊时出示趋势。
struct HealthObservation: Identifiable, Equatable, Codable {
    static let jaundiceKind = "黄疸"
    static let temperatureKind = "体温"
    static let medicationKind = "用药"

    static let jaundiceZones = ["面部", "胸腹", "四肢", "手足心"]
    static let medicationPresets = ["维生素D", "维生素AD", "铁剂", "益生菌", "退烧药", "其他"]

    var id: UUID
    var babyId: UUID
    var kind: String
    var occurredAt: Date
    /// 黄疸经皮值（mg/dL）或体温（℃）；用药不使用。
    var value: Double?
    /// 黄疸目测部位。
    var zone: String?
    var medicationName: String?
    var dose: String?
    var note: String?
    var createdAt: Date
    var updatedAt: Date

    init(
        id: UUID = UUID(),
        babyId: UUID = RecordCodingDefaults.babyId,
        kind: String,
        occurredAt: Date = Date(),
        value: Double? = nil,
        zone: String? = nil,
        medicationName: String? = nil,
        dose: String? = nil,
        note: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.babyId = babyId
        self.kind = kind
        self.occurredAt = occurredAt
        self.value = value
        self.zone = zone
        self.medicationName = medicationName
        self.dose = dose
        self.note = note
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    private enum CodingKeys: String, CodingKey {
        case id, babyId, kind, occurredAt, value, zone, medicationName, dose, note, createdAt, updatedAt
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        babyId = try container.decodeIfPresent(UUID.self, forKey: .babyId) ?? RecordCodingDefaults.babyId
        kind = try container.decodeIfPresent(String.self, forKey: .kind) ?? Self.medicationKind
        occurredAt = try container.decodeIfPresent(Date.self, forKey: .occurredAt) ?? Date()
        value = try container.decodeIfPresent(Double.self, forKey: .value)
        zone = try container.decodeIfPresent(String.self, forKey: .zone)
        medicationName = try container.decodeIfPresent(String.self, forKey: .medicationName)
        dose = try container.decodeIfPresent(String.self, forKey: .dose)
        note = try container.decodeIfPresent(String.self, forKey: .note)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? occurredAt
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? .distantPast
    }

    /// 列表行摘要，如“经皮 8.5 · 胸腹”“38.2℃”“维生素D 400IU”。
    var summaryText: String {
        switch kind {
        case Self.jaundiceKind:
            var parts: [String] = []
            if let value {
                parts.append(String(format: "经皮 %.1f", value))
            }
            if let zone {
                parts.append(zone)
            }
            return parts.isEmpty ? "目测记录" : parts.joined(separator: " · ")
        case Self.temperatureKind:
            if let value {
                return String(format: "%.1f℃", value)
            }
            return "已测量"
        default:
            var parts: [String] = []
            if let medicationName {
                parts.append(medicationName)
            }
            if let dose, !dose.isEmpty {
                parts.append(dose)
            }
            return parts.isEmpty ? "已服用" : parts.joined(separator: " ")
        }
    }
}
