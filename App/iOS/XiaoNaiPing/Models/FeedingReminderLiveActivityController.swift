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

            XiaoNaiPingSharedStore.writeLiveActivityAvatar(
                liveActivityAvatarData(from: babyAvatarData)
            )

            let state = FeedingReminderActivityAttributes.ContentState(
                babyName: babyName,
                nextReminderAt: reminder.remindAt,
                repeatIntervalMinutes: repeatIntervalMinutes
            )
            let content = ActivityContent(
                state: state,
                staleDate: Calendar.current.date(byAdding: .minute, value: 10, to: reminder.remindAt)
            )

            // attributes 不可变：换了提醒就必须结束旧活动重新请求，
            // 否则活动身上挂着旧 reminderID，后续对不上号。
            if let activity = Activity<FeedingReminderActivityAttributes>.activities.first,
               activity.attributes.reminderID == reminder.id.uuidString {
                await activity.update(content)
                complete(.startedOrUpdated, completion: completion)
            } else {
                await endAllActivities(clearAvatar: false)
                let attributes = FeedingReminderActivityAttributes(reminderID: reminder.id.uuidString)
                if let failureMessage = await requestActivity(attributes: attributes, content: content) {
                    complete(.failed(message: failureMessage), completion: completion)
                } else {
                    complete(.startedOrUpdated, completion: completion)
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

    private static func endAllActivities(clearAvatar: Bool = true) async {
        for activity in Activity<FeedingReminderActivityAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
        if clearAvatar {
            XiaoNaiPingSharedStore.clearLiveActivityAvatar()
        }
    }

    private static func requestActivity(
        attributes: FeedingReminderActivityAttributes,
        content: ActivityContent<FeedingReminderActivityAttributes.ContentState>
    ) async -> String? {
        do {
            _ = try Activity.request(attributes: attributes, content: content, pushType: nil)
            return nil
        } catch {
            print("Live Activity request failed: \(error)")
            return activityRequestFailureMessage(for: error)
        }
    }

    private static func activityRequestFailureMessage(for error: Error) -> String {
        guard let authorizationError = error as? ActivityAuthorizationError else {
            return "系统未能启动实时活动，请检查 iPhone 的实时活动设置后再试。"
        }

        switch authorizationError {
        case .attributesTooLarge:
            return "灵动岛内容超过系统限制，请重新打开后再试。"
        case .globalMaximumExceeded, .targetMaximumExceeded:
            return "系统当前的实时活动数量已达上限，请先结束其他实时活动。"
        case .denied:
            return "系统没有允许小奶瓶显示实时活动。"
        case .unsupported, .unsupportedTarget:
            return "当前设备暂不支持小奶瓶的实时活动。"
        case .unentitled:
            return "当前安装包缺少实时活动授权。"
        case .visibility:
            return "系统当前不允许显示实时活动。"
        case .persistenceFailure, .missingProcessIdentifier, .malformedActivityIdentifier, .reconnectNotPermitted:
            return "系统未能启动实时活动，请关闭后重新打开再试。"
        @unknown default:
            return "系统未能启动实时活动，请检查 iPhone 的实时活动设置后再试。"
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
