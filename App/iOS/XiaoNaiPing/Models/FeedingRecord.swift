import Foundation

enum RecordSyncStatus: String, Codable {
    case notSynced
    case pending
    case synced
    case failed
    case localOnly
}

enum RecordCodingDefaults {
    static let babyId = UUID(uuidString: "11111111-1111-1111-1111-111111111111")!

    static func date(fromTimeString time: String) -> Date {
        var components = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        let parts = time.split(separator: ":").compactMap { Int($0) }
        components.hour = parts.first ?? 0
        components.minute = parts.dropFirst().first ?? 0
        return Calendar.current.date(from: components) ?? Date()
    }
}

struct FeedingRecord: Identifiable, Equatable, Codable {
    var id: UUID
    var babyId: UUID
    var occurredAt: Date
    var time: String
    var type: String
    var detail: String
    var icon: String
    var amountML: Int?
    var durationMinutes: Int?
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
        type: String,
        detail: String,
        icon: String,
        amountML: Int? = nil,
        durationMinutes: Int? = nil,
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
        self.type = type
        self.detail = detail
        self.icon = icon
        self.amountML = amountML
        self.durationMinutes = durationMinutes
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
        type = try container.decode(String.self, forKey: .type)
        detail = try container.decode(String.self, forKey: .detail)
        icon = try container.decode(String.self, forKey: .icon)
        amountML = try container.decodeIfPresent(Int.self, forKey: .amountML)
        durationMinutes = try container.decodeIfPresent(Int.self, forKey: .durationMinutes)
        note = try container.decodeIfPresent(String.self, forKey: .note)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? occurredAt
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
        deletedAt = try container.decodeIfPresent(Date.self, forKey: .deletedAt)
        syncStatus = try container.decodeIfPresent(RecordSyncStatus.self, forKey: .syncStatus) ?? .localOnly
        serverId = try container.decodeIfPresent(String.self, forKey: .serverId)
    }
}

struct FeedingReminder: Identifiable, Equatable, Codable {
    var id: UUID
    var babyId: UUID
    var remindAt: Date
    var repeatIntervalMinutes: Int?
    var title: String
    var note: String?
    var createdAt: Date
    var updatedAt: Date

    init(
        id: UUID = UUID(),
        babyId: UUID = RecordCodingDefaults.babyId,
        remindAt: Date,
        repeatIntervalMinutes: Int? = nil,
        title: String = "喝奶提醒",
        note: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.babyId = babyId
        self.remindAt = remindAt
        self.repeatIntervalMinutes = repeatIntervalMinutes
        self.title = title
        self.note = note
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        babyId = try container.decodeIfPresent(UUID.self, forKey: .babyId) ?? RecordCodingDefaults.babyId
        remindAt = try container.decode(Date.self, forKey: .remindAt)
        repeatIntervalMinutes = try container.decodeIfPresent(Int.self, forKey: .repeatIntervalMinutes)
        title = try container.decodeIfPresent(String.self, forKey: .title) ?? "喝奶提醒"
        note = try container.decodeIfPresent(String.self, forKey: .note)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? Date()
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }

    var repeatIntervalText: String? {
        guard let repeatIntervalMinutes, repeatIntervalMinutes > 0 else { return nil }
        let hours = repeatIntervalMinutes / 60
        let minutes = repeatIntervalMinutes % 60
        if minutes == 0 {
            return "\(hours)小时"
        }
        if hours == 0 {
            return "\(minutes)分钟"
        }
        return "\(hours)小时\(minutes)分"
    }

    func nextRemindAt(after referenceDate: Date = Date()) -> Date? {
        guard let repeatIntervalMinutes, repeatIntervalMinutes > 0 else {
            return remindAt > referenceDate ? remindAt : nil
        }

        let interval = TimeInterval(repeatIntervalMinutes * 60)
        guard remindAt <= referenceDate else { return remindAt }

        let elapsed = referenceDate.timeIntervalSince(remindAt)
        let steps = floor(elapsed / interval) + 1
        return remindAt.addingTimeInterval(steps * interval)
    }
}
