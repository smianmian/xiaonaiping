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
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [feedingReminderIdentifier])
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
        let content = UNMutableNotificationContent()
        content.title = "小奶瓶喝奶提醒".localizedText
        content.body = "到你设置的喝奶时间了。".localizedText
        content.sound = .default

        var components = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: reminder.remindAt)
        components.second = 0

        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: false)
        let request = UNNotificationRequest(
            identifier: feedingReminderIdentifier,
            content: content,
            trigger: trigger
        )

        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [feedingReminderIdentifier])
        UNUserNotificationCenter.current().add(request) { error in
            complete(error == nil ? .scheduled : .failed, completion: completion)
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

    private static func complete(_ result: NotificationScheduleResult, completion: @escaping (NotificationScheduleResult) -> Void) {
        DispatchQueue.main.async {
            completion(result)
        }
    }

    private static func vaccineIdentifier(_ record: VaccineRecord) -> String {
        "xiaonaiping.vaccine.\(record.id.uuidString)"
    }

    private static let feedingReminderIdentifier = "xiaonaiping.feeding.next"
}
