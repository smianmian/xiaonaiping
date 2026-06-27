import Foundation

struct SleepRecord: Identifiable, Equatable, Codable {
    var id: UUID
    var babyId: UUID
    var startAt: Date
    var endAt: Date?
    var start: String
    var end: String
    var type: String
    var duration: String
    var icon: String
    var durationMinutes: Int?
    var isOngoing: Bool
    var note: String?
    var createdAt: Date
    var updatedAt: Date
    var deletedAt: Date?
    var syncStatus: RecordSyncStatus
    var serverId: String?

    init(
        id: UUID = UUID(),
        babyId: UUID = RecordCodingDefaults.babyId,
        startAt: Date? = nil,
        endAt: Date? = nil,
        start: String,
        end: String,
        type: String,
        duration: String,
        icon: String,
        durationMinutes: Int? = nil,
        isOngoing: Bool = false,
        note: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        deletedAt: Date? = nil,
        syncStatus: RecordSyncStatus = .localOnly,
        serverId: String? = nil
    ) {
        self.id = id
        self.babyId = babyId
        self.start = start
        self.end = end
        self.startAt = startAt ?? RecordCodingDefaults.date(fromTimeString: start)
        self.endAt = endAt ?? Self.legacyEndDate(end, startAt: self.startAt)
        self.type = type
        self.duration = duration
        self.icon = icon
        self.durationMinutes = durationMinutes
        self.isOngoing = isOngoing
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
        start = try container.decode(String.self, forKey: .start)
        end = try container.decode(String.self, forKey: .end)
        startAt = try container.decodeIfPresent(Date.self, forKey: .startAt)
            ?? RecordCodingDefaults.date(fromTimeString: start)
        endAt = try container.decodeIfPresent(Date.self, forKey: .endAt)
            ?? Self.legacyEndDate(end, startAt: startAt)
        babyId = try container.decodeIfPresent(UUID.self, forKey: .babyId) ?? RecordCodingDefaults.babyId
        type = try container.decode(String.self, forKey: .type)
        duration = try container.decode(String.self, forKey: .duration)
        icon = try container.decode(String.self, forKey: .icon)
        durationMinutes = try container.decodeIfPresent(Int.self, forKey: .durationMinutes)
        let decodedIsOngoing = try container.decodeIfPresent(Bool.self, forKey: .isOngoing)
        isOngoing = decodedIsOngoing ?? (endAt == nil)
        note = try container.decodeIfPresent(String.self, forKey: .note)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? startAt
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
        deletedAt = try container.decodeIfPresent(Date.self, forKey: .deletedAt)
        syncStatus = try container.decodeIfPresent(RecordSyncStatus.self, forKey: .syncStatus) ?? .localOnly
        serverId = try container.decodeIfPresent(String.self, forKey: .serverId)
    }

    private static func legacyEndDate(_ value: String, startAt: Date) -> Date? {
        guard value != "进行中" else { return nil }
        var endDate = RecordCodingDefaults.date(fromTimeString: value)
        if endDate <= startAt {
            endDate = Calendar.current.date(byAdding: .day, value: 1, to: endDate) ?? endDate
        }
        return endDate
    }
}
