import Foundation
import UserNotifications

enum NotificationScheduleResult {
    case scheduled
    case removed
    case denied
    case failed
}

enum AppNotificationScheduler {
    static func scheduleFeedingReminder(_ reminder: FeedingReminder, completion: @escaping (NotificationScheduleResult) -> Void = { _ in }) {
        guard reminder.remindAt > Date() else {
            removeFeedingReminder()
            complete(.removed, completion: completion)
            return
        }

        UNUserNotificationCenter.current().getNotificationSettings { settings in
            switch settings.authorizationStatus {
            case .authorized, .provisional, .ephemeral:
                addFeedingReminder(reminder, completion: completion)
            case .notDetermined:
                UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
                    if granted {
                        addFeedingReminder(reminder, completion: completion)
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
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [vaccineIdentifier(record)])
    }

    static func removeVaccineReminders(_ records: [VaccineRecord]) {
        let identifiers = records.map { vaccineIdentifier($0) }
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: identifiers)
    }

    private static func addFeedingReminder(_ reminder: FeedingReminder, completion: @escaping (NotificationScheduleResult) -> Void) {
        let reminderDates = feedingReminderDates(for: reminder)
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
            if let prepareAt = Calendar.current.date(byAdding: .minute, value: -feedingPrepareReminderLeadMinutes, to: remindAt),
               prepareAt > Date() {
                let request = notificationRequest(
                    identifier: feedingPrepareReminderIdentifier(index),
                    date: prepareAt,
                    title: "准备泡奶啦".localizedText,
                    body: "5分钟后到喝奶时间，先把奶准备好。".localizedText
                )
                add(request, group: group) {
                    lock.lock()
                    didFail = true
                    lock.unlock()
                }
            }

            let body = reminder.origin == .automatic
                ? "到你设定的喝奶时间了。".localizedText
                : "到你设置的喝奶时间了。".localizedText

            let request = notificationRequest(
                identifier: feedingReminderIdentifier(index),
                date: remindAt,
                title: "小奶瓶喝奶提醒".localizedText,
                body: body
            )
            add(request, group: group) {
                lock.lock()
                didFail = true
                lock.unlock()
            }
        }

        group.notify(queue: .main) {
            completion(didFail ? .failed : .scheduled)
        }
    }

    private static func addReminder(record: VaccineRecord, dueDate: Date, completion: @escaping (NotificationScheduleResult) -> Void) {
        let content = UNMutableNotificationContent()
        content.title = "小奶瓶疫苗提醒".localizedText
        content.body = AppLocalization.format("%@ 今天有提醒，日期可按实际情况调整。", record.title.localizedText)
        content.sound = .default

        var components = Calendar.current.dateComponents([.year, .month, .day], from: dueDate)
        components.hour = 9
        components.minute = 0

        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
        let request = UNNotificationRequest(
            identifier: vaccineIdentifier(record),
            content: content,
            trigger: trigger
        )

        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [vaccineIdentifier(record)])
        UNUserNotificationCenter.current().add(request) { error in
            complete(error == nil ? .scheduled : .failed, completion: completion)
        }
    }

    private static func notificationRequest(identifier: String, date: Date, title: String, body: String) -> UNNotificationRequest {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default

        var components = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: date)
        components.second = 0

        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
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

    private static func feedingReminderDates(for reminder: FeedingReminder) -> [Date] {
        reminder.remindAt > Date() ? [reminder.remindAt] : []
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
    private static let feedingPrepareReminderLeadMinutes = 5
}
