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
    /// 母乳哺乳侧："左侧" / "右侧"；nil 表示未记录（含旧数据）。
    var breastSide: String?
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
        breastSide: String? = nil,
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
        self.breastSide = breastSide
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
        breastSide = try container.decodeIfPresent(String.self, forKey: .breastSide)
        note = try container.decodeIfPresent(String.self, forKey: .note)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? occurredAt
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
        deletedAt = try container.decodeIfPresent(Date.self, forKey: .deletedAt)
        syncStatus = try container.decodeIfPresent(RecordSyncStatus.self, forKey: .syncStatus) ?? .localOnly
        serverId = try container.decodeIfPresent(String.self, forKey: .serverId)
    }
}

struct WaterRecord: Identifiable, Equatable, Codable {
    var id: UUID
    var babyId: UUID
    var occurredAt: Date
    var amountML: Int
    var note: String?
    var createdAt: Date
    var updatedAt: Date

    init(
        id: UUID = UUID(),
        babyId: UUID = RecordCodingDefaults.babyId,
        occurredAt: Date = Date(),
        amountML: Int,
        note: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.babyId = babyId
        self.occurredAt = occurredAt
        self.amountML = amountML
        self.note = note
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        babyId = try container.decodeIfPresent(UUID.self, forKey: .babyId) ?? RecordCodingDefaults.babyId
        occurredAt = try container.decodeIfPresent(Date.self, forKey: .occurredAt) ?? Date()
        amountML = try container.decodeIfPresent(Int.self, forKey: .amountML) ?? 0
        note = try container.decodeIfPresent(String.self, forKey: .note)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? occurredAt
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }
}

enum FeedingReminderOrigin: String, Codable {
    case manual
    case automatic
}

struct FeedingReminder: Identifiable, Equatable, Codable {
    var id: UUID
    var babyId: UUID
    var remindAt: Date
    var origin: FeedingReminderOrigin
    var title: String
    var note: String?
    var createdAt: Date
    var updatedAt: Date

    init(
        id: UUID = UUID(),
        babyId: UUID = RecordCodingDefaults.babyId,
        remindAt: Date,
        origin: FeedingReminderOrigin = .manual,
        title: String = "喝奶提醒",
        note: String? = nil,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.babyId = babyId
        self.remindAt = remindAt
        self.origin = origin
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
        origin = try container.decodeIfPresent(FeedingReminderOrigin.self, forKey: .origin) ?? .manual
        title = try container.decodeIfPresent(String.self, forKey: .title) ?? "喝奶提醒"
        note = try container.decodeIfPresent(String.self, forKey: .note)
        createdAt = try container.decodeIfPresent(Date.self, forKey: .createdAt) ?? Date()
        updatedAt = try container.decodeIfPresent(Date.self, forKey: .updatedAt) ?? createdAt
    }
}

struct FeedingReminderPreference: Equatable, Codable {
    static let supportedIntervalMinutes = [120, 150, 180, 210, 240]

    var babyId: UUID
    var isAutoReminderEnabled: Bool
    var intervalMinutes: Int?
    var updatedAt: Date

    init(
        babyId: UUID = RecordCodingDefaults.babyId,
        isAutoReminderEnabled: Bool = true,
        intervalMinutes: Int? = 180,
        updatedAt: Date = Date()
    ) {
        self.babyId = babyId
        self.isAutoReminderEnabled = isAutoReminderEnabled
        self.intervalMinutes = intervalMinutes
        self.updatedAt = updatedAt
    }

    var hasValidAutomaticInterval: Bool {
        guard let intervalMinutes else { return false }
        return Self.supportedIntervalMinutes.contains(intervalMinutes)
    }
}
