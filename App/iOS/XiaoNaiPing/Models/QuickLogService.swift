import Foundation

/// 首页一键记录的结果，用于内联反馈与撤销。
enum QuickLogOutcome: Equatable {
    case feedingSaved(FeedingRecord)
    case diaperSaved(DiaperRecord)
    case sleepStarted
    case sleepEnded(minutes: Int)
    /// 没有历史喂养可复制，需要打开完整表单。
    case needsFeedingEditor
    case failed
}

/// 单手一键落库：不弹表单、不弹 Alert，副作用（自动提醒、灵动岛）静默完成。
@MainActor
enum QuickLogService {
    static func logFeedingLikeLast(store: BabyRecordStore) -> QuickLogOutcome {
        guard let last = store.latestFeedingRecordEver else { return .needsFeedingEditor }
        let now = Date()
        let record = FeedingRecord(
            babyId: store.baby.id,
            occurredAt: now,
            time: BabyRecordStore.timeString(from: now),
            type: last.type,
            detail: detailText(from: last),
            icon: AppAssets.bottleIcon,
            amountML: last.amountML,
            durationMinutes: last.durationMinutes
        )
        guard store.upsert(record) else { return .failed }
        scheduleReminderSilently(for: record, store: store)
        return .feedingSaved(record)
    }

    static func logDiaper(store: BabyRecordStore) -> QuickLogOutcome {
        let now = Date()
        let record = DiaperRecord(
            babyId: store.baby.id,
            occurredAt: now,
            time: BabyRecordStore.timeString(from: now),
            title: "大便",
            icon: AppAssets.diaperIcon,
            kind: "大便"
        )
        guard store.upsert(record) else { return .failed }
        return .diaperSaved(record)
    }

    static func toggleSleep(store: BabyRecordStore) -> QuickLogOutcome {
        if let ongoing = store.ongoingSleep {
            let minutes = max(1, Calendar.current.dateComponents([.minute], from: ongoing.startAt, to: Date()).minute ?? 1)
            guard store.finishOngoingSleepNow() else { return .failed }
            return .sleepEnded(minutes: minutes)
        }
        guard store.startSleepNow() else { return .failed }
        return .sleepStarted
    }

    static func undo(_ outcome: QuickLogOutcome, store: BabyRecordStore) {
        switch outcome {
        case .feedingSaved(let record):
            _ = store.deleteFeedingRecord(record)
        case .diaperSaved(let record):
            _ = store.deleteDiaperRecord(record)
        case .sleepStarted:
            if let ongoing = store.ongoingSleep {
                _ = store.deleteSleepRecord(ongoing)
            }
        case .sleepEnded, .needsFeedingEditor, .failed:
            break
        }
    }

    /// 保存喂养后的自动提醒与灵动岛同步（静默版：成功不打扰用户）。
    static func scheduleReminderSilently(for record: FeedingRecord, store: BabyRecordStore) {
        switch store.updateAutomaticFeedingReminder(for: record, skipForThisRecord: false) {
        case .scheduled(let reminder):
            AppNotificationScheduler.scheduleFeedingReminder(
                reminder,
                repeatIntervalMinutes: store.feedingReminderPreference.intervalMinutes
            ) { _ in }
            syncLiveActivity(store: store)
        case .skipped, .preservedManual:
            syncLiveActivity(store: store)
        case .disabled, .failed:
            break
        }
    }

    /// 统一的灵动岛同步入口：所有调用点都带上正确的重复间隔，
    /// 避免“切个后台就从每3小时降级成只提醒一次”。
    static func syncLiveActivity(store: BabyRecordStore) {
        #if canImport(ActivityKit)
        if #available(iOS 16.2, *) {
            guard store.feedingLiveActivityEnabled else {
                FeedingReminderLiveActivityController.endAll()
                return
            }
            FeedingReminderLiveActivityController.sync(
                reminder: store.nextFeedingReminder,
                repeatIntervalMinutes: store.nextFeedingReminder?.origin == .automatic
                    ? store.feedingReminderPreference.intervalMinutes
                    : nil,
                babyName: store.baby.name,
                babyAvatarData: store.baby.avatarImageData
            )
        }
        #endif
    }

    private static func detailText(from last: FeedingRecord) -> String {
        if let amount = last.amountML, amount > 0 {
            return "\(amount)ml"
        }
        if let duration = last.durationMinutes, duration > 0 {
            return "\(duration)分钟"
        }
        return last.detail.isEmpty ? "快速记录" : last.detail
    }
}
