import Foundation

#if canImport(ActivityKit)
import ActivityKit
import UIKit

@available(iOS 16.2, *)
enum FeedingReminderLiveActivityResult {
    case startedOrUpdated
    case ended
    case noReminder
    case activitiesDisabled
    case failed(message: String)
}

@available(iOS 16.2, *)
enum FeedingReminderLiveActivityController {
    static func sync(
        reminder: FeedingReminder?,
        repeatIntervalMinutes: Int? = nil,
        babyName: String,
        babyAvatarData: Data?,
        completion: @escaping (FeedingReminderLiveActivityResult) -> Void = { _ in }
    ) {
        Task {
            guard ActivityAuthorizationInfo().areActivitiesEnabled else {
                complete(.activitiesDisabled, completion: completion)
                return
            }

            guard let reminder else {
                await endAllActivities()
                complete(.noReminder, completion: completion)
                return
            }

            let state = FeedingReminderActivityAttributes.ContentState(
                babyName: babyName,
                nextReminderAt: reminder.remindAt,
                repeatIntervalMinutes: repeatIntervalMinutes,
                babyAvatarData: liveActivityAvatarData(from: babyAvatarData)
            )
            let content = ActivityContent(
                state: state,
                staleDate: Calendar.current.date(byAdding: .minute, value: 10, to: reminder.remindAt)
            )

            if let activity = Activity<FeedingReminderActivityAttributes>.activities.first {
                await activity.update(content)
                complete(.startedOrUpdated, completion: completion)
            } else {
                let attributes = FeedingReminderActivityAttributes(reminderID: reminder.id.uuidString)
                if await requestActivity(attributes: attributes, content: content) {
                    complete(.startedOrUpdated, completion: completion)
                } else {
                    complete(.failed(message: "系统刚刚还在处理上一条灵动岛提醒，请稍等几秒再试。"), completion: completion)
                }
            }
        }
    }

    static func endAll(completion: @escaping (FeedingReminderLiveActivityResult) -> Void = { _ in }) {
        Task {
            await endAllActivities()
            complete(.ended, completion: completion)
        }
    }

    private static func endAllActivities() async {
        for activity in Activity<FeedingReminderActivityAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
    }

    private static func requestActivity(
        attributes: FeedingReminderActivityAttributes,
        content: ActivityContent<FeedingReminderActivityAttributes.ContentState>
    ) async -> Bool {
        do {
            _ = try Activity.request(attributes: attributes, content: content, pushType: nil)
            return true
        } catch {
            try? await Task.sleep(nanoseconds: 700_000_000)
            if let activity = Activity<FeedingReminderActivityAttributes>.activities.first {
                await activity.update(content)
                return true
            }

            do {
                _ = try Activity.request(attributes: attributes, content: content, pushType: nil)
                return true
            } catch {
                return false
            }
        }
    }

    private static func liveActivityAvatarData(from data: Data?) -> Data? {
        guard let data,
              let image = UIImage(data: data) else {
            return nil
        }

        let side: CGFloat = 72
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        let renderer = UIGraphicsImageRenderer(size: CGSize(width: side, height: side), format: format)
        let thumbnail = renderer.image { _ in
            let sourceSize = image.size
            let scale = max(side / sourceSize.width, side / sourceSize.height)
            let drawSize = CGSize(width: sourceSize.width * scale, height: sourceSize.height * scale)
            let drawOrigin = CGPoint(x: (side - drawSize.width) / 2, y: (side - drawSize.height) / 2)
            image.draw(in: CGRect(origin: drawOrigin, size: drawSize))
        }
        return thumbnail.jpegData(compressionQuality: 0.72)
    }

    private static func complete(
        _ result: FeedingReminderLiveActivityResult,
        completion: @escaping (FeedingReminderLiveActivityResult) -> Void
    ) {
        DispatchQueue.main.async {
            completion(result)
        }
    }
}
#endif
