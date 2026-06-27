import Foundation

#if canImport(ActivityKit)
import ActivityKit
#endif

struct SharedTodaySnapshot: Codable, Equatable {
    var hasCompletedOnboarding: Bool
    var babyName: String
    var daysSinceBirth: Int
    var feedingCount: Int
    var milkAmountML: Int
    var lastFeedingAt: Date?
    var ongoingSleepStartAt: Date?
    var nextFeedingReminderAt: Date?
    var feedingReminderRepeatIntervalMinutes: Int?
    var poopCount: Int
    var peeCount: Int
    var generatedAt: Date

    static let empty = SharedTodaySnapshot(
        hasCompletedOnboarding: false,
        babyName: "宝宝",
        daysSinceBirth: 0,
        feedingCount: 0,
        milkAmountML: 0,
        lastFeedingAt: nil,
        ongoingSleepStartAt: nil,
        nextFeedingReminderAt: nil,
        feedingReminderRepeatIntervalMinutes: nil,
        poopCount: 0,
        peeCount: 0,
        generatedAt: Date()
    )
}

#if canImport(ActivityKit)
@available(iOS 16.2, *)
struct FeedingReminderActivityAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var babyName: String
        var nextReminderAt: Date
        var repeatIntervalMinutes: Int?
        var babyAvatarData: Data?
    }

    var reminderID: String
}
#endif

enum XiaoNaiPingSharedStore {
    static let appGroupIdentifier = "group.com.mewpow.xiaonaiping"

    static func readSnapshot() -> SharedTodaySnapshot? {
        guard let data = try? Data(contentsOf: snapshotURL()) else {
            return nil
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try? decoder.decode(SharedTodaySnapshot.self, from: data)
    }

    static func writeSnapshot(_ snapshot: SharedTodaySnapshot) throws {
        let url = snapshotURL()
        try FileManager.default.createDirectory(
            at: url.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(snapshot)
        try data.write(to: url, options: [.atomic])
    }

    private static func snapshotURL() -> URL {
        let baseURL = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupIdentifier)
            ?? FileManager.default.temporaryDirectory
        return baseURL.appendingPathComponent("xiaonaiping-today-snapshot.json")
    }
}
