import Foundation

struct DiaperRecord: Identifiable, Equatable, Codable {
    var id: UUID
    var babyId: UUID
    var occurredAt: Date
    var time: String
    var title: String
    var icon: String
    var kind: String
    var color: String?
    var texture: String?
    var note: String?
    var createdAt: Date
    var updatedAt: Date
    var deletedAt: Date?
    var syncStatus: RecordSyncStatus
    var serverId: String?

    init(
        id: UUID = UUID(),
        babyId: UUID = RecordCodingDefaults.babyId,
        occurredAt: Date? = nil,
        time: String,
        title: String,
        icon: String,
        kind: String = "大便",
        color: String? = nil,
        texture: String? = nil,
        note: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        deletedAt: Date? = nil,
        syncStatus: RecordSyncStatus = .localOnly,
        serverId: String? = nil
    ) {
        self.id = id
        self.babyId = babyId
        self.time = time
        self.occurredAt = occurredAt ?? RecordCodingDefaults.date(fromTimeString: time)
        self.title = title
        self.icon = icon
        self.kind = kind
        self.color = color
        self.texture = texture
        self.note = note
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.deletedAt = deletedAt
        self.syncStatus = syncStatus
        self.serverId = serverId
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        time = try container.decode(String.self, forKey: .time)
        occurredAt = try container.decodeIfPresent(Date.self, forKey: .occurredAt)
            ?? RecordCodingDefaults.date(fromTimeString: time)
        babyId = try container.decodeIfPresent(UUID.self, forKey: .babyId) ?? RecordCodingDefaults.babyId
        title = try container.decode(String.self, forKey: .title)
        icon = try container.decode(String.self, forKey: .icon)
        kind = try container.decodeIfPresent(String.self, forKey: .kind) ?? "大便"
        color = try container.decodeIfPresent(String.self, forKey: .color)
        texture = try container.decodeIfPresent(String.self, forKey: .texture)
        note = try container.decodeIfPresent(String.self, forKey: .note)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? occurredAt
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
        deletedAt = try container.decodeIfPresent(Date.self, forKey: .deletedAt)
        syncStatus = try container.decodeIfPresent(RecordSyncStatus.self, forKey: .syncStatus) ?? .localOnly
        serverId = try container.decodeIfPresent(String.self, forKey: .serverId)
    }
}
