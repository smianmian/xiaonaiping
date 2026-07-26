import Foundation
import UserNotifications

enum NotificationScheduleResult {
    case scheduled
    case removed
    case denied
    case failed
}

enum AppNotificationScheduler {
    /// - Parameter repeatIntervalMinutes: 自动提醒的重复间隔。传入后会按该间隔追加
    ///   后续几条“备份提醒”——父母睡过头没记录时，提醒链不会就此断掉。
    static func scheduleFeedingReminder(
        _ reminder: FeedingReminder,
        repeatIntervalMinutes: Int? = nil,
        completion: @escaping (NotificationScheduleResult) -> Void = { _ in }
    ) {
        guard reminder.remindAt > Date() else {
            removeFeedingReminder()
            complete(.removed, completion: completion)
            return
        }

        UNUserNotificationCenter.current().getNotificationSettings { settings in
            switch settings.authorizationStatus {
            case .authorized, .provisional, .ephemeral:
                addFeedingReminder(reminder, repeatIntervalMinutes: repeatIntervalMinutes, completion: completion)
            case .notDetermined:
                UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
                    if granted {
                        addFeedingReminder(reminder, repeatIntervalMinutes: repeatIntervalMinutes, completion: completion)
                    } else {
                        complete(.denied, completion: completion)
                    }
                }
            case .denied:
                complete(.denied, completion: completion)
            @unknown default:
                complete(.failed, completion: completion)
            }
        }
    }

    static func removeFeedingReminder() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: feedingReminderIdentifiers)
    }

    static func scheduleVaccineReminder(_ record: VaccineRecord, completion: @escaping (NotificationScheduleResult) -> Void = { _ in }) {
        guard !record.isAdministered,
              let dueDate = BabyRecordStore.date(fromDateString: record.dueText) else {
            removeVaccineReminder(record)
            complete(.removed, completion: completion)
            return
        }

        UNUserNotificationCenter.current().getNotificationSettings { settings in
            switch settings.authorizationStatus {
            case .authorized, .provisional, .ephemeral:
                addReminder(record: record, dueDate: dueDate, completion: completion)
            case .notDetermined:
                UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
                    if granted {
                        addReminder(record: record, dueDate: dueDate, completion: completion)
                    } else {
                        complete(.denied, completion: completion)
                    }
                }
            case .denied:
                complete(.denied, completion: completion)
            @unknown default:
                complete(.failed, completion: completion)
            }
        }
    }

    static func removeVaccineReminder(_ record: VaccineRecord) {
        UNUserNotificationCenter.current().removePendingNotificationRequests(
            withIdentifiers: [vaccineIdentifier(record), vaccineAdvanceIdentifier(record)]
        )
    }

    static func removeVaccineReminders(_ records: [VaccineRecord]) {
        let identifiers = records.map { vaccineIdentifier($0) } + records.map { vaccineAdvanceIdentifier($0) }
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: identifiers)
    }

    private static func addFeedingReminder(
        _ reminder: FeedingReminder,
        repeatIntervalMinutes: Int?,
        completion: @escaping (NotificationScheduleResult) -> Void
    ) {
        let reminderDates = feedingReminderDates(for: reminder, repeatIntervalMinutes: repeatIntervalMinutes)
        guard !reminderDates.isEmpty else {
            removeFeedingReminder()
            complete(.removed, completion: completion)
            return
        }

        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: feedingReminderIdentifiers)

        let group = DispatchGroup()
        let lock = NSLock()
        var didFail = false

        for (index, remindAt) in reminderDates.enumerated() {
            // “提前5分钟泡奶”只挂在第一条上；后续是错过后的备份提醒，不再翻倍打扰。
            if index == 0,
               let prepareAt = Calendar.current.date(byAdding: .minute, value: -feedingPrepareReminderLeadMinutes, to: remindAt),
               prepareAt > Date(),
               let request = notificationRequest(
                   identifier: feedingPrepareReminderIdentifier(index),
                   date: prepareAt,
                   title: "准备泡奶啦".localizedText,
                   body: "5分钟后到喝奶时间，先把奶准备好。".localizedText
               ) {
                add(request, group: group) {
                    lock.lock()
                    didFail = true
                    lock.unlock()
                }
            }

            let body: String
            if index == 0 {
                body = reminder.origin == .automatic
                    ? "到你设定的喝奶时间了。".localizedText
                    : "到你设置的喝奶时间了。".localizedText
            } else {
                body = "上一顿还没记录，到下一次喝奶时间了。".localizedText
            }

            if let request = notificationRequest(
                identifier: feedingReminderIdentifier(index),
                date: remindAt,
                title: "小奶瓶喝奶提醒".localizedText,
                body: body
            ) {
                add(request, group: group) {
                    lock.lock()
                    didFail = true
                    lock.unlock()
                }
            }
        }

        group.notify(queue: .main) {
            completion(didFail ? .failed : .scheduled)
        }
    }

    private static func addReminder(record: VaccineRecord, dueDate: Date, completion: @escaping (NotificationScheduleResult) -> Void) {
        removeVaccineReminder(record)

        // 到期当天 09:00 提醒。
        let dayOfRequest = vaccineRequest(
            identifier: vaccineIdentifier(record),
            date: dueDate,
            body: AppLocalization.format("%@ 今天有提醒，日期可按实际情况调整。", record.title.localizedText)
        )

        // 提前 3 天 09:00 再提醒一次，给预约留出时间。
        var advanceRequest: UNNotificationRequest?
        if let advanceDate = Calendar.current.date(byAdding: .day, value: -vaccineAdvanceLeadDays, to: dueDate),
           advanceDate > Date() {
            advanceRequest = vaccineRequest(
                identifier: vaccineAdvanceIdentifier(record),
                date: advanceDate,
                body: AppLocalization.format("%@ 还有%d天到期，可以先和接种点确认时间。", record.title.localizedText, vaccineAdvanceLeadDays)
            )
        }

        UNUserNotificationCenter.current().add(dayOfRequest) { error in
            if let advanceRequest {
                UNUserNotificationCenter.current().add(advanceRequest) { _ in }
            }
            complete(error == nil ? .scheduled : .failed, completion: completion)
        }
    }

    private static func vaccineRequest(identifier: String, date: Date, body: String) -> UNNotificationRequest {
        let content = UNMutableNotificationContent()
        content.title = "小奶瓶疫苗提醒".localizedText
        content.body = body
        content.sound = .default

        var components = Calendar.current.dateComponents([.year, .month, .day], from: date)
        components.hour = 9
        components.minute = 0

        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
        return UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)
    }

    // 喝奶提醒是“N 小时后”的相对时间，必须用时间间隔触发器：
    // 日历触发器会在跨时区时按新时区的墙钟漂移，且把秒截断成 0
    // 会让“30 秒后”的提醒落到过去、显示已安排实际永不触发。
    private static func notificationRequest(identifier: String, date: Date, title: String, body: String) -> UNNotificationRequest? {
        let interval = date.timeIntervalSinceNow
        guard interval > 1 else { return nil }

        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: interval, repeats: false)
        return UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)
    }

    private static func add(_ request: UNNotificationRequest, group: DispatchGroup, onFailure: @escaping () -> Void) {
        group.enter()
        UNUserNotificationCenter.current().add(request) { error in
            if error != nil {
                onFailure()
            }
            group.leave()
        }
    }

    private static func complete(_ result: NotificationScheduleResult, completion: @escaping (NotificationScheduleResult) -> Void) {
        DispatchQueue.main.async {
            completion(result)
        }
    }

    private static func vaccineIdentifier(_ record: VaccineRecord) -> String {
        "xiaonaiping.vaccine.\(record.id.uuidString)"
    }

    private static func vaccineAdvanceIdentifier(_ record: VaccineRecord) -> String {
        "xiaonaiping.vaccine.advance.\(record.id.uuidString)"
    }

    private static let vaccineAdvanceLeadDays = 3

    private static func feedingReminderDates(for reminder: FeedingReminder, repeatIntervalMinutes: Int?) -> [Date] {
        guard reminder.remindAt > Date() else { return [] }
        guard let repeatIntervalMinutes, repeatIntervalMinutes > 0 else {
            return [reminder.remindAt]
        }

        // 首条 + 按间隔追加的备份提醒，最多覆盖约 24 小时。
        var dates = [reminder.remindAt]
        var next = reminder.remindAt
        let horizon = Date().addingTimeInterval(24 * 60 * 60)
        while dates.count < feedingReminderChainCount,
              let candidate = Calendar.current.date(byAdding: .minute, value: repeatIntervalMinutes, to: next),
              candidate <= horizon {
            dates.append(candidate)
            next = candidate
        }
        return dates
    }

    private static func feedingReminderIdentifier(_ index: Int) -> String {
        "xiaonaiping.feeding.next.\(index)"
    }

    private static func feedingPrepareReminderIdentifier(_ index: Int) -> String {
        "xiaonaiping.feeding.prepare.\(index)"
    }

    private static var feedingReminderIdentifiers: [String] {
        [legacyFeedingReminderIdentifier] +
            (0..<feedingReminderScheduleLimit).map(feedingReminderIdentifier) +
            (0..<feedingReminderScheduleLimit).map(feedingPrepareReminderIdentifier)
    }

    private static let legacyFeedingReminderIdentifier = "xiaonaiping.feeding.next"
    private static let feedingReminderScheduleLimit = 24
    private static let feedingReminderChainCount = 8
    private static let feedingPrepareReminderLeadMinutes = 5
}
