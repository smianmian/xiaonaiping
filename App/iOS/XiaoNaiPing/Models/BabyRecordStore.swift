import Foundation
import Combine
import UIKit
import WidgetKit

extension Notification.Name {
    static let babyRecordStoreDidSave = Notification.Name("babyRecordStoreDidSave")
}

private enum PhotoImportError: Error {
    case saveFailed
}

enum AutomaticFeedingReminderUpdate {
    case scheduled(FeedingReminder)
    case skipped
    case preservedManual
    case disabled
    case failed
}

final class BabyRecordStore: ObservableObject {
    static let mainlandVaccineRegion = "中国大陆"
    static let hongKongVaccineRegion = "香港"
    static let manualVaccineRegion = "手动"

    @Published var hasCompletedOnboarding = false
    @Published var baby = BabyRecordStore.emptyBaby
    @Published var feedingRecords: [FeedingRecord] = []
    @Published var waterRecords: [WaterRecord] = []
    @Published var feedingReminder: FeedingReminder?
    @Published private(set) var feedingReminderPreference = FeedingReminderPreference()
    @Published var sleepRecords: [SleepRecord] = []
    @Published var diaperRecords: [DiaperRecord] = []
    @Published var growthRecords: [GrowthRecord] = []
    @Published var vaccineRecords: [VaccineRecord] = []
    @Published var milestones: [Milestone] = []
    @Published var babyPhotos: [BabyPhoto] = []
    @Published var photoCount = 0
    @Published var quietCareModeEnabled = true
    @Published var feedingLiveActivityEnabled = true
    @Published var saveErrorMessage: String?
    @Published var loadErrorMessage: String?
    private(set) var isPersistenceBlocked = false

    private let fileManager = FileManager.default
    private let userDefaults = UserDefaults.standard
    private let stateFileName = "xiaonaiping-local-state.json"
    private let backupStateFileName = "xiaonaiping-local-state.backup.json"
    private let storageDirectoryOverride: URL?
    private static let mockDataSeededDefaultsKey = "xnp.debug.mock-data-seeded"

    init(seedMockData: Bool = false, storageDirectoryOverride: URL? = nil) {
        self.storageDirectoryOverride = storageDirectoryOverride
        loadState()
        if seedMockData {
            applyMockData()
        }

        loadFeedingReminderPreference()
        normalizeRecordsForCurrentBaby()
        removeLegacyBackupExclusionIfNeeded()
        writeSharedTodaySnapshot()
    }

    private func applyMockData() {
        userDefaults.set(true, forKey: Self.mockDataSeededDefaultsKey)
        hasCompletedOnboarding = true
        baby = MockData.baby
        feedingRecords = MockData.feedingRecords
        sleepRecords = MockData.sleepRecords
        diaperRecords = MockData.diaperRecords
        growthRecords = MockData.growthRecords
        vaccineRecords = MockData.vaccines
        milestones = MockData.milestones
        babyPhotos = []
        photoCount = 0
    }

    var automaticMilestones: [AutomaticMilestone] {
        Self.automaticMilestoneDefinitions.map { definition in
            let date = Calendar.current.date(
                byAdding: .day,
                value: max(0, definition.dayNumber - 1),
                to: baby.birthDate
            ) ?? baby.birthDate
            return AutomaticMilestone(
                title: definition.title,
                dayNumber: definition.dayNumber,
                date: date,
                daysRemaining: max(0, definition.dayNumber - currentBabyDaysSinceBirth),
                isReached: currentBabyDaysSinceBirth >= definition.dayNumber
            )
        }
    }

    var nextAutomaticMilestone: AutomaticMilestone? {
        automaticMilestones.first { !$0.isReached }
    }

    var feedingCount: Int {
        todayFeedingRecords.count
    }

    var milkAmountML: Int {
        todayFeedingRecords.compactMap(\.amountML).reduce(0, +)
    }

    var waterAmountML: Int {
        todayWaterRecords.map(\.amountML).reduce(0, +)
    }

    var todayWaterRecords: [WaterRecord] {
        waterRecords(on: Date())
    }

    var lastFeedingRecord: FeedingRecord? {
        todayFeedingRecords.first
    }

    var currentBabyDaysSinceBirth: Int {
        Self.daysSinceBirth(from: baby.birthDate)
    }

    var currentBabyAgeText: String {
        Self.ageText(from: baby.birthDate)
    }

    var lastFeedingIntervalText: String {
        guard let record = lastFeedingRecord else { return "暂无" }
        return Self.elapsedText(since: Self.feedingEndDate(record), now: Date())
    }

    var sleepDurationText: String {
        Self.durationText(from: totalSleepMinutes)
    }

    var totalSleepMinutes: Int {
        todaySleepRecords
            .map(Self.sleepMinutesDuringToday)
            .reduce(0, +)
    }

    var ongoingSleep: SleepRecord? {
        sleepRecords.first { $0.isOngoing }
    }

    var poopCount: Int {
        todayDiaperRecords.filter { $0.kind == "大便" }.count
    }

    var peeCount: Int {
        todayDiaperRecords.filter { $0.kind == "小便" }.count
    }

    var todayPhotoCount: Int {
        babyPhotos.filter { Calendar.current.isDateInToday($0.capturedAt) }.count
    }

    var hasTodayRecords: Bool {
        !todayFeedingRecords.isEmpty
            || !todayWaterRecords.isEmpty
            || !todaySleepRecords.isEmpty
            || !todayDiaperRecords.isEmpty
            || todayPhotoCount > 0
    }

    var todayFeedingRecords: [FeedingRecord] {
        feedingRecords(on: Date())
    }

    func feedingRecords(on day: Date) -> [FeedingRecord] {
        feedingRecords
            .filter { Calendar.current.isDate($0.occurredAt, inSameDayAs: day) }
            .sorted { $0.occurredAt > $1.occurredAt }
    }

    func waterRecords(on day: Date) -> [WaterRecord] {
        waterRecords
            .filter { Calendar.current.isDate($0.occurredAt, inSameDayAs: day) }
            .sorted { $0.occurredAt > $1.occurredAt }
    }

    func sleepRecords(on day: Date) -> [SleepRecord] {
        sleepRecords
            .filter { Self.isSleepRecord($0, on: day) }
            .sorted { Self.sleepSortDate($0) > Self.sleepSortDate($1) }
    }

    func diaperRecords(on day: Date) -> [DiaperRecord] {
        diaperRecords
            .filter { Calendar.current.isDate($0.occurredAt, inSameDayAs: day) }
            .sorted { $0.occurredAt > $1.occurredAt }
    }

    func sleepMinutes(on day: Date) -> Int {
        sleepRecords(on: day)
            .map { Self.sleepMinutes(of: $0, on: day) }
            .reduce(0, +)
    }

    var nextFeedingReminder: FeedingReminder? {
        guard let feedingReminder,
              feedingReminder.remindAt > Date() else {
            return nil
        }
        return feedingReminder
    }

    var todaySleepRecords: [SleepRecord] {
        sleepRecords(on: Date())
    }

    var todayDiaperRecords: [DiaperRecord] {
        diaperRecords(on: Date())
    }

    /// 最近一次喂养（不限日期），供“同上次”一键记录取默认值。
    var latestFeedingRecordEver: FeedingRecord? {
        feedingRecords.max { $0.occurredAt < $1.occurredAt }
    }

    var recentHomeRecords: [HomeRecentRecord] {
        let feeding = todayFeedingRecords.map { record in
            HomeRecentRecord(
                id: "feeding-\(record.id.uuidString)",
                sortDate: Self.sortableDate(record.occurredAt, timeString: record.time),
                time: record.time,
                icon: record.icon,
                title: "喂养 · \(record.type)",
                detail: feedingResultText(for: record)
            )
        }
        let sleep = todaySleepRecords.map { record in
            HomeRecentRecord(
                id: "sleep-\(record.id.uuidString)",
                sortDate: Self.sortableDate(record.startAt, timeString: record.start),
                time: record.start,
                icon: record.icon,
                title: record.isOngoing ? "睡眠进行中" : "睡眠 · \(record.type)",
                detail: record.isOngoing ? "从 \(record.start) 开始" : record.duration
            )
        }
        let water = todayWaterRecords.map { record in
            HomeRecentRecord(
                id: "water-\(record.id.uuidString)",
                sortDate: record.occurredAt,
                time: Self.timeString(from: record.occurredAt),
                icon: nil,
                systemIcon: "drop.fill",
                title: "喝水",
                detail: "\(record.amountML)ml"
            )
        }
        let diaper = todayDiaperRecords.map { record in
            HomeRecentRecord(
                id: "diaper-\(record.id.uuidString)",
                sortDate: Self.sortableDate(record.occurredAt, timeString: record.time),
                time: record.time,
                icon: record.icon,
                title: record.kind,
                detail: record.title
            )
        }
        let photos = babyPhotos.filter { Calendar.current.isDateInToday($0.capturedAt) }.map { photo in
            HomeRecentRecord(
                id: "photo-\(photo.id.uuidString)",
                sortDate: photo.capturedAt,
                time: Self.timeString(from: photo.capturedAt),
                icon: AppAssets.cameraIcon,
                title: "照片",
                detail: photo.note.isEmpty ? "成长照片" : photo.note
            )
        }

        return (feeding + water + sleep + diaper + photos)
            .sorted { $0.sortDate > $1.sortDate }
    }

    var nextVaccine: VaccineRecord? {
        vaccineRecords
            .filter { !$0.isAdministered }
            .sorted(by: isVaccineEarlier)
            .first
    }

    private func feedingResultText(for record: FeedingRecord) -> String {
        if let amount = record.amountML, amount > 0 {
            return "\(amount)ml"
        }
        if let duration = record.durationMinutes, duration > 0 {
            return "\(duration)分钟"
        }
        return record.detail == "快速记录" ? "已记录" : record.detail
    }

    /// Growth records are legacy data without a babyId. Keep only dated records
    /// that can belong to the current baby's lifetime so stale demo/history
    /// entries cannot appear on the formal growth page.
    var currentBabyGrowthRecords: [GrowthRecord] {
        let birthDate = Calendar.current.startOfDay(for: baby.birthDate)
        let today = Calendar.current.startOfDay(for: Date())
        return growthRecords
            .filter { record in
                guard let measuredAt = Self.date(fromDateString: record.measuredAt) else {
                    return false
                }
                let date = Calendar.current.startOfDay(for: measuredAt)
                return date >= birthDate && date <= today
            }
            .sorted {
                (Self.date(fromDateString: $0.measuredAt) ?? .distantPast)
                    < (Self.date(fromDateString: $1.measuredAt) ?? .distantPast)
            }
    }

    func vaccineDaysUntil(_ record: VaccineRecord) -> Int {
        guard let dueDate = Self.date(fromDateString: record.dueText) else {
            return Int.max
        }
        return Calendar.current.dateComponents(
            [.day],
            from: Calendar.current.startOfDay(for: Date()),
            to: Calendar.current.startOfDay(for: dueDate)
        ).day ?? Int.max
    }

    func vaccineDueValue(_ record: VaccineRecord) -> String {
        let days = vaccineDaysUntil(record)
        guard days != Int.max else { return "未设置" }
        // A pending item with a past plan date is not "N days ago". Show the
        // concrete plan date so the user can decide whether to edit or mark it.
        return days < 0 ? (record.dueText.isEmpty ? "--" : record.dueText) : "\(days)"
    }

    func vaccineDueUnit(_ record: VaccineRecord) -> String {
        let days = vaccineDaysUntil(record)
        if days == Int.max {
            return ""
        }
        if days < 0 {
            return ""
        }
        if days == 0 {
            return "今天"
        }
        return "天后"
    }

    private func isVaccineEarlier(_ lhs: VaccineRecord, _ rhs: VaccineRecord) -> Bool {
        let lhsDays = vaccineDaysUntil(lhs)
        let rhsDays = vaccineDaysUntil(rhs)

        if lhsDays == Int.max { return false }
        if rhsDays == Int.max { return true }
        if lhsDays >= 0, rhsDays < 0 { return true }
        if lhsDays < 0, rhsDays >= 0 { return false }
        if lhsDays >= 0 {
            return lhsDays < rhsDays
        }
        return lhsDays > rhsDays
    }

    var latestGrowthRecord: GrowthRecord? {
        currentBabyGrowthRecords.last
    }

    var monthlyReport: MonthlyReportSnapshot {
        monthlyReport(for: Date())
    }

    func monthlyReport(for monthDate: Date) -> MonthlyReportSnapshot {
        let monthlyFeedings = feedingRecords.filter { Self.isSameMonth($0.occurredAt, monthDate: monthDate) }
        let monthlySleep = sleepRecords.filter { Self.isSameMonthSleepRecord($0, monthDate: monthDate) }
        let monthlyDiapers = diaperRecords.filter { Self.isSameMonth($0.occurredAt, monthDate: monthDate) }
        let monthlyPhotos = babyPhotos.filter { Calendar.current.isDate($0.capturedAt, equalTo: monthDate, toGranularity: .month) }
        let monthlyGrowth = currentBabyGrowthRecords.filter { record in
            guard let measuredAt = Self.date(fromDateString: record.measuredAt) else {
                return Calendar.current.isDate(monthDate, equalTo: Date(), toGranularity: .month)
            }
            return Calendar.current.isDate(measuredAt, equalTo: monthDate, toGranularity: .month)
        }
        let monthlyMilestones = milestones.filter { milestone in
            guard let date = Self.date(fromDisplayDateString: milestone.date) else { return false }
            return Calendar.current.isDate(date, equalTo: monthDate, toGranularity: .month)
        }
        let monthlyVaccines = vaccineRecords.filter { record in
            guard let dueDate = Self.date(fromDateString: record.dueText) else { return false }
            return Calendar.current.isDate(dueDate, equalTo: monthDate, toGranularity: .month)
        }
        let latest = monthlyGrowth.last
        let previous = monthlyGrowth.dropLast().last
        let sleepMinutes = monthlySleep.compactMap(\.durationMinutes).reduce(0, +)

        return MonthlyReportSnapshot(
            monthTitle: Self.reportMonthString(from: monthDate),
            feedingCount: monthlyFeedings.count,
            milkAmountML: monthlyFeedings.compactMap(\.amountML).reduce(0, +),
            sleepDurationText: Self.durationText(from: sleepMinutes),
            diaperCount: monthlyDiapers.count,
            photoCount: monthlyPhotos.count,
            latestWeight: latest?.weight == 0 ? nil : latest?.weight,
            latestHeight: latest?.height == 0 ? nil : latest?.height,
            weightDelta: Self.delta(latest?.weight == 0 ? nil : latest?.weight, previous?.weight == 0 ? nil : previous?.weight),
            heightDelta: Self.delta(latest?.height == 0 ? nil : latest?.height, previous?.height == 0 ? nil : previous?.height),
            milestoneCount: monthlyMilestones.count,
            vaccineOpenCount: monthlyVaccines.filter { !$0.isAdministered }.count,
            recordCount: monthlyFeedings.count + waterRecords.filter { Self.isSameMonth($0.occurredAt, monthDate: monthDate) }.count + monthlySleep.count + monthlyDiapers.count + monthlyPhotos.count + monthlyGrowth.count + monthlyMilestones.count + monthlyVaccines.count
        )
    }

    func createBabyProfile(name: String, birthDate: Date, sex: String) {
        baby = Baby(
            id: UUID(),
            name: name,
            daysSinceBirth: Self.daysSinceBirth(from: birthDate),
            ageText: Self.ageText(from: birthDate),
            birthDate: birthDate,
            sex: sex
        )
        removeAllLocalRecords()
        loadFeedingReminderPreference()
        hasCompletedOnboarding = true
        saveState()
    }

    func clearSaveError() {
        saveErrorMessage = nil
    }

    func setQuietCareModeEnabled(_ isEnabled: Bool) {
        quietCareModeEnabled = isEnabled
        saveState()
    }

    func setFeedingLiveActivityEnabled(_ isEnabled: Bool) {
        feedingLiveActivityEnabled = isEnabled
        saveState()
    }

    func feedingIntervalText(before record: FeedingRecord) -> String {
        let records = feedingRecords.sorted { $0.occurredAt > $1.occurredAt }
        guard let index = records.firstIndex(where: { $0.id == record.id }),
              records.indices.contains(index + 1) else {
            return "首次记录".localizedText
        }

        let previous = records[index + 1]
        let minutes = Calendar.current.dateComponents(
            [.minute],
            from: Self.feedingEndDate(previous),
            to: record.occurredAt
        ).minute ?? 0

        guard minutes > 0 else { return "间隔很近".localizedText }
        return Self.durationText(from: minutes)
    }

    @discardableResult
    func upsert(_ record: FeedingRecord) -> Bool {
        if record.type == "奶粉" || record.type == "瓶喂" {
            guard let amount = record.amountML, amount > 0 else {
                saveErrorMessage = "奶量必须填写大于 0 的数字。"
                return false
            }
        }
        let previous = feedingRecords
        let saved = prepared(record)
        if let index = feedingRecords.firstIndex(where: { $0.id == saved.id }) {
            feedingRecords[index] = saved
        } else {
            feedingRecords.insert(saved, at: 0)
        }
        guard saveState() else {
            feedingRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func deleteFeedingRecord(_ record: FeedingRecord) -> Bool {
        let previous = feedingRecords
        feedingRecords.removeAll { $0.id == record.id }
        guard saveState() else {
            feedingRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func upsert(_ record: WaterRecord) -> Bool {
        let previous = waterRecords
        var saved = record
        saved.babyId = baby.id
        saved.updatedAt = Date()
        if let index = waterRecords.firstIndex(where: { $0.id == saved.id }) {
            waterRecords[index] = saved
        } else {
            waterRecords.insert(saved, at: 0)
        }
        guard saveState() else {
            waterRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func deleteWaterRecord(_ record: WaterRecord) -> Bool {
        let previous = waterRecords
        waterRecords.removeAll { $0.id == record.id }
        guard saveState() else {
            waterRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func upsert(_ reminder: FeedingReminder) -> Bool {
        let previous = feedingReminder
        var saved = reminder
        saved.babyId = baby.id
        saved.updatedAt = Date()
        feedingReminder = saved
        guard saveState() else {
            feedingReminder = previous
            return false
        }
        return true
    }

    @discardableResult
    func cancelFeedingReminder() -> Bool {
        let previous = feedingReminder
        feedingReminder = nil
        guard saveState() else {
            feedingReminder = previous
            return false
        }
        return true
    }

    @discardableResult
    func setAutomaticFeedingReminderEnabled(_ isEnabled: Bool, intervalMinutes: Int?) -> Bool {
        guard !isEnabled || FeedingReminderPreference.supportedIntervalMinutes.contains(intervalMinutes ?? -1) else {
            return false
        }

        let preference = FeedingReminderPreference(
            babyId: baby.id,
            isAutoReminderEnabled: isEnabled,
            intervalMinutes: isEnabled ? intervalMinutes : nil
        )
        guard saveFeedingReminderPreference(preference) else { return false }

        feedingReminderPreference = preference
        if !isEnabled, feedingReminder?.origin == .automatic {
            return cancelFeedingReminder()
        }
        return true
    }

    @discardableResult
    func updateAutomaticFeedingReminder(for record: FeedingRecord, skipForThisRecord: Bool) -> AutomaticFeedingReminderUpdate {
        if let reminder = feedingReminder, reminder.origin == .manual {
            guard reminder.remindAt <= Date() else {
                return .preservedManual
            }
            guard cancelFeedingReminder() else { return .failed }
        }

        if skipForThisRecord {
            if feedingReminder?.origin == .automatic, !cancelFeedingReminder() {
                return .failed
            }
            return .skipped
        }

        guard feedingReminderPreference.isAutoReminderEnabled,
              let intervalMinutes = feedingReminderPreference.intervalMinutes,
              feedingReminderPreference.hasValidAutomaticInterval else {
            return .disabled
        }

        let baseDate = Self.feedingEndDate(record)
        let remindAt = Calendar.current.date(byAdding: .minute, value: intervalMinutes, to: baseDate)
            ?? baseDate.addingTimeInterval(TimeInterval(intervalMinutes * 60))
        let reminder = FeedingReminder(
            babyId: baby.id,
            remindAt: remindAt,
            origin: .automatic
        )
        guard upsert(reminder) else { return .failed }
        return .scheduled(reminder)
    }

    @discardableResult
    func upsert(_ record: SleepRecord) -> Bool {
        let previous = sleepRecords
        let saved = prepared(record)
        if let index = sleepRecords.firstIndex(where: { $0.id == saved.id }) {
            sleepRecords[index] = saved
        } else {
            sleepRecords.insert(saved, at: 0)
        }
        guard saveState() else {
            sleepRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func deleteSleepRecord(_ record: SleepRecord) -> Bool {
        let previous = sleepRecords
        sleepRecords.removeAll { $0.id == record.id }
        guard saveState() else {
            sleepRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func startSleepNow() -> Bool {
        guard ongoingSleep == nil else { return true }
        let previous = sleepRecords
        let now = Date()
        let record = SleepRecord(
            babyId: baby.id,
            startAt: now,
            endAt: nil,
            start: Self.timeString(from: now),
            end: "进行中",
            type: "小睡",
            duration: "进行中",
            icon: AppAssets.moonIcon,
            isOngoing: true
        )
        sleepRecords.insert(record, at: 0)
        guard saveState() else {
            sleepRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func finishOngoingSleepNow() -> Bool {
        guard let ongoing = ongoingSleep,
              let index = sleepRecords.firstIndex(where: { $0.id == ongoing.id }) else { return true }

        let previous = sleepRecords
        let endDate = Date()
        let startDate = ongoing.startAt
        let minutes = max(1, Calendar.current.dateComponents([.minute], from: startDate, to: endDate).minute ?? 1)
        sleepRecords[index].end = Self.timeString(from: endDate)
        sleepRecords[index].endAt = endDate
        sleepRecords[index].durationMinutes = minutes
        sleepRecords[index].duration = Self.durationText(from: minutes)
        sleepRecords[index].isOngoing = false
        sleepRecords[index].updatedAt = endDate
        sleepRecords[index].syncStatus = .localOnly
        guard saveState() else {
            sleepRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func upsert(_ record: DiaperRecord) -> Bool {
        let previous = diaperRecords
        let saved = prepared(record)
        if let index = diaperRecords.firstIndex(where: { $0.id == saved.id }) {
            diaperRecords[index] = saved
        } else {
            diaperRecords.insert(saved, at: 0)
        }
        guard saveState() else {
            diaperRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func deleteDiaperRecord(_ record: DiaperRecord) -> Bool {
        let previous = diaperRecords
        diaperRecords.removeAll { $0.id == record.id }
        guard saveState() else {
            diaperRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func upsert(_ record: GrowthRecord) -> Bool {
        let previous = growthRecords
        if let index = growthRecords.firstIndex(where: { $0.id == record.id }) {
            growthRecords[index] = record
        } else {
            growthRecords.append(record)
        }
        guard saveState() else {
            growthRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func deleteGrowthRecord(_ record: GrowthRecord) -> Bool {
        let previous = growthRecords
        growthRecords.removeAll { $0.id == record.id }
        guard saveState() else {
            growthRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func upsert(_ record: VaccineRecord) -> Bool {
        let previous = vaccineRecords
        var saved = record
        saved.region = Self.normalizedVaccineRegion(record.region)
        if saved.status == VaccineRecord.legacyCompletedStatus {
            saved.status = VaccineRecord.administeredStatus
        }
        if let index = vaccineRecords.firstIndex(where: { $0.id == saved.id }) {
            vaccineRecords[index] = saved
        } else {
            vaccineRecords.insert(saved, at: 0)
        }
        guard saveState() else {
            vaccineRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func deleteVaccineRecord(_ record: VaccineRecord) -> Bool {
        let previous = vaccineRecords
        vaccineRecords.removeAll { $0.id == record.id }
        guard saveState() else {
            vaccineRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func toggleVaccineCompleted(_ record: VaccineRecord) -> Bool {
        guard let index = vaccineRecords.firstIndex(where: { $0.id == record.id }) else { return false }
        let previous = vaccineRecords
        if vaccineRecords[index].isAdministered {
            vaccineRecords[index].status = VaccineRecord.pendingStatus
            vaccineRecords[index].tintName = "orange"
            vaccineRecords[index].icon = AppAssets.bottleIcon
            vaccineRecords[index].administeredAt = nil
        } else {
            vaccineRecords[index].status = VaccineRecord.administeredStatus
            vaccineRecords[index].tintName = "green"
            vaccineRecords[index].icon = AppAssets.cameraIcon
            vaccineRecords[index].administeredAt = Date()
        }
        guard saveState() else {
            vaccineRecords = previous
            return false
        }
        return true
    }

    @discardableResult
    func upsert(_ milestone: Milestone) -> Bool {
        let previous = milestones
        if let index = milestones.firstIndex(where: { $0.id == milestone.id }) {
            milestones[index] = milestone
        } else {
            milestones.insert(milestone, at: 0)
        }
        guard saveState() else {
            milestones = previous
            return false
        }
        return true
    }

    @discardableResult
    func deleteMilestone(_ milestone: Milestone) -> Bool {
        let previous = milestones
        milestones.removeAll { $0.id == milestone.id }
        guard saveState() else {
            milestones = previous
            return false
        }
        return true
    }

    func updateBaby(name: String, birthDate: Date, sex: String) {
        baby.name = name
        baby.birthDate = birthDate
        baby.sex = sex
        baby.daysSinceBirth = Self.daysSinceBirth(from: birthDate)
        baby.ageText = Self.ageText(from: birthDate)
        saveState()
    }

    @discardableResult
    func updateBabyAvatar(data: Data) -> Bool {
        let previousAvatar = baby.avatarImageData
        guard let avatarData = sanitizedAvatarJPEGData(from: data) else {
            saveErrorMessage = "头像保存失败，请换一张照片再试。"
            return false
        }

        baby.avatarImageData = avatarData
        guard saveState() else {
            baby.avatarImageData = previousAvatar
            return false
        }
        return true
    }

    @discardableResult
    func clearBabyAvatar() -> Bool {
        let previousAvatar = baby.avatarImageData
        baby.avatarImageData = nil
        guard saveState() else {
            baby.avatarImageData = previousAvatar
            return false
        }
        return true
    }

    func deleteBabyProfileAndLocalRecords() {
        removeFeedingReminderPreference(for: baby.id)
        baby = Baby(
            id: UUID(),
            name: "宝宝",
            daysSinceBirth: 0,
            ageText: "第1天",
            birthDate: Date(),
            sex: "未设置"
        )
        removeAllLocalRecords()
        loadFeedingReminderPreference()
        hasCompletedOnboarding = false
        saveState()
    }

    func clearLocalDemoRecords() {
        removeAllLocalRecords()
        saveState()
    }

    private func removeAllLocalRecords() {
        AppNotificationScheduler.removeFeedingReminder()
        AppNotificationScheduler.removeVaccineReminders(vaccineRecords)
        feedingReminder = nil
        feedingRecords.removeAll()
        waterRecords.removeAll()
        sleepRecords.removeAll()
        diaperRecords.removeAll()
        growthRecords.removeAll()
        vaccineRecords.removeAll()
        milestones.removeAll()
        for photo in babyPhotos {
            try? fileManager.removeItem(at: photoURL(for: photo))
        }
        babyPhotos.removeAll()
        photoCount = 0
    }

    @discardableResult
    func generateVaccineTemplate(region: String) -> [VaccineRecord] {
        let normalizedRegion = Self.normalizedVaccineRegion(region)
        let templates = VaccineTemplate.templates(for: normalizedRegion)
        let existingKeys = Set(vaccineRecords.map { "\(Self.normalizedVaccineRegion($0.region))-\($0.title)" })
        let today = Calendar.current.startOfDay(for: Date())
        let newRecords = templates.compactMap { template -> VaccineRecord? in
            let key = "\(normalizedRegion)-\(template.title)"
            guard !existingKeys.contains(key),
                  let dueDate = Calendar.current.date(byAdding: .day, value: template.dayOffset, to: baby.birthDate) else {
                return nil
            }

            let dueDays = Calendar.current.dateComponents([.day], from: today, to: Calendar.current.startOfDay(for: dueDate)).day
            return VaccineRecord(
                title: template.title,
                status: VaccineRecord.pendingStatus,
                tintName: "orange",
                icon: AppAssets.bottleIcon,
                dueText: Self.dateString(from: dueDate),
                dueDays: dueDays,
                region: normalizedRegion,
                note: AppLocalization.format("由%@模板生成，日期可按实际接种安排修改。", normalizedRegion.localizedText)
            )
        }

        guard !newRecords.isEmpty else { return [] }
        let previous = vaccineRecords
        vaccineRecords.append(contentsOf: newRecords)
        vaccineRecords.sort { ($0.dueDays ?? Int.max) < ($1.dueDays ?? Int.max) }
        guard saveState() else {
            vaccineRecords = previous
            return []
        }
        return newRecords
    }

    static func normalizedVaccineRegion(_ region: String?) -> String {
        switch region?.trimmingCharacters(in: .whitespacesAndNewlines) {
        case mainlandVaccineRegion, "大陆", "国内", "Mainland China":
            mainlandVaccineRegion
        case hongKongVaccineRegion, "Hong Kong":
            hongKongVaccineRegion
        default:
            manualVaccineRegion
        }
    }

    func importPhoto(data: Data, capturedAt: Date = Date(), source: String = "photoLibrary") throws {
        let photosDirectory = try ensurePhotosDirectory()
        let fileName = "\(UUID().uuidString).jpg"
        let destinationURL = photosDirectory.appendingPathComponent(fileName)
        try sanitizedJPEGData(from: data).write(to: destinationURL, options: [.atomic])
        try markIncludedInBackup(destinationURL)

        let photo = BabyPhoto(
            capturedAt: capturedAt,
            localFileName: fileName,
            source: source
        )
        let previous = babyPhotos
        babyPhotos.insert(photo, at: 0)
        photoCount = babyPhotos.count
        guard saveState() else {
            babyPhotos = previous
            photoCount = previous.count
            try? fileManager.removeItem(at: destinationURL)
            throw PhotoImportError.saveFailed
        }
    }

    func updatePhoto(_ photo: BabyPhoto, capturedAt: Date, note: String) {
        guard let index = babyPhotos.firstIndex(where: { $0.id == photo.id }) else { return }
        babyPhotos[index].capturedAt = capturedAt
        babyPhotos[index].note = note
        saveState()
    }

    @discardableResult
    func deletePhoto(_ photo: BabyPhoto) -> Bool {
        let previous = babyPhotos
        babyPhotos.removeAll { $0.id == photo.id }
        photoCount = babyPhotos.count
        guard saveState() else {
            babyPhotos = previous
            photoCount = previous.count
            return false
        }
        try? fileManager.removeItem(at: photoURL(for: photo))
        return true
    }

    func photoURL(for photo: BabyPhoto) -> URL {
        photosDirectory.appendingPathComponent(photo.localFileName)
    }

    func encodedCloudSyncData() throws -> Data {
        let payload = CloudSyncPayload(
            schemaVersion: 1,
            generatedAt: Date(),
            hasCompletedOnboarding: hasCompletedOnboarding,
            baby: baby,
            feedingRecords: feedingRecords,
            waterRecords: waterRecords,
            sleepRecords: sleepRecords,
            diaperRecords: diaperRecords,
            growthRecords: growthRecords,
            vaccineRecords: vaccineRecords,
            milestones: milestones,
            babyPhotos: babyPhotos
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys]
        return try encoder.encode(payload)
    }

    func restoreCloudSyncData(_ data: Data) throws {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let payload = try decoder.decode(CloudSyncPayload.self, from: data)
        baby = payload.baby
        hasCompletedOnboarding = payload.hasCompletedOnboarding
        feedingRecords = payload.feedingRecords
        waterRecords = payload.waterRecords
        sleepRecords = payload.sleepRecords
        diaperRecords = payload.diaperRecords
        growthRecords = payload.growthRecords
        vaccineRecords = payload.vaccineRecords
        milestones = payload.milestones
        babyPhotos = payload.babyPhotos
        photoCount = babyPhotos.count
        AppNotificationScheduler.removeFeedingReminder()
        feedingReminder = nil
        loadFeedingReminderPreference()
        normalizeRecordsForCurrentBaby()
        // 云端恢复成功意味着我们重新拿到了一份完整可信的状态，
        // 可以解除因本地文件损坏而进入的安全模式（损坏文件已另存保留）。
        isPersistenceBlocked = false
        loadErrorMessage = nil
        saveState()
    }

    func localPhotoSyncAssets() -> [LocalPhotoSyncAsset] {
        babyPhotos.compactMap { photo in
            // 只上传还没备份成功的照片，已备份/待删除的不重复传。
            switch photo.syncStatus {
            case .backedUp, .cloudDeletePending:
                return nil
            case .localOnly, .pending, .failed:
                break
            }
            let url = photoURL(for: photo)
            guard fileManager.fileExists(atPath: url.path) else { return nil }
            return LocalPhotoSyncAsset(photo: photo, fileURL: url)
        }
    }

    /// 供同步覆盖保护使用：本地记录总量（不含宝宝档案本身）。
    var localSyncableRecordCount: Int {
        feedingRecords.count
            + waterRecords.count
            + sleepRecords.count
            + diaperRecords.count
            + growthRecords.count
            + vaccineRecords.count
            + milestones.count
            + babyPhotos.count
    }

    /// 云端恢复会整体覆盖本地状态；恢复前把当前状态文件另存一份快照，
    /// 让“恢复选错了”永远有退路。
    func snapshotStateFileBeforeRestore() {
        guard fileManager.fileExists(atPath: stateURL.path) else { return }
        let stamp = Int(Date().timeIntervalSince1970)
        let snapshotURL = applicationSupportDirectory.appendingPathComponent("\(stateFileName).pre-restore-\(stamp)")
        try? fileManager.copyItem(at: stateURL, to: snapshotURL)
    }

    func restoreCloudPhotoData(for photo: BabyPhoto, data: Data) throws {
        let destinationURL = try ensurePhotosDirectory().appendingPathComponent(photo.localFileName)
        try data.write(to: destinationURL, options: [.atomic])
        try markIncludedInBackup(destinationURL)
        markCloudPhotoSynced(photo)
    }

    func markCloudPhotoSynced(_ photo: BabyPhoto) {
        guard let index = babyPhotos.firstIndex(where: { $0.id == photo.id }),
              babyPhotos[index].syncStatus != .backedUp else { return }
        babyPhotos[index].syncStatus = .backedUp
        saveState()
    }

    func markCloudPhotoDeletePending(_ photo: BabyPhoto) {
        guard let index = babyPhotos.firstIndex(where: { $0.id == photo.id }) else { return }
        babyPhotos[index].syncStatus = .cloudDeletePending
        saveState()
    }

    /// 返回是否有任何状态被更新。没有变化时不落盘、不发保存通知，
    /// 避免“同步完成→保存→通知→再同步”的自激循环。
    @discardableResult
    func markCloudSyncCompleted() -> Bool {
        let updatedFeeding = feedingRecords.map { record in
            var updated = record
            updated.syncStatus = .synced
            return updated
        }
        let updatedWater = waterRecords.map { record in
            var normalized = record
            normalized.babyId = baby.id
            return normalized
        }
        let updatedSleep = sleepRecords.map { record in
            var updated = record
            updated.syncStatus = .synced
            return updated
        }
        let updatedDiaper = diaperRecords.map { record in
            var updated = record
            updated.syncStatus = .synced
            return updated
        }
        let updatedPhotos = babyPhotos.map { photo in
            var updated = photo
            updated.syncStatus = .backedUp
            return updated
        }

        let changed = updatedFeeding != feedingRecords
            || updatedWater != waterRecords
            || updatedSleep != sleepRecords
            || updatedDiaper != diaperRecords
            || updatedPhotos != babyPhotos
        guard changed else { return false }

        feedingRecords = updatedFeeding
        waterRecords = updatedWater
        sleepRecords = updatedSleep
        diaperRecords = updatedDiaper
        babyPhotos = updatedPhotos
        saveState()
        return true
    }

    func markCloudAccountDeletedLocally() {
        feedingRecords = feedingRecords.map { record in
            var updated = record
            updated.syncStatus = .localOnly
            return updated
        }
        sleepRecords = sleepRecords.map { record in
            var updated = record
            updated.syncStatus = .localOnly
            return updated
        }
        diaperRecords = diaperRecords.map { record in
            var updated = record
            updated.syncStatus = .localOnly
            return updated
        }
        babyPhotos = babyPhotos.map { photo in
            var updated = photo
            updated.syncStatus = .localOnly
            return updated
        }
        saveState()
    }

    private func prepared(_ record: FeedingRecord) -> FeedingRecord {
        var saved = record
        let now = Date()
        saved.babyId = baby.id
        saved.updatedAt = now
        saved.deletedAt = nil
        saved.syncStatus = .localOnly
        return saved
    }

    private func prepared(_ record: SleepRecord) -> SleepRecord {
        var saved = record
        let now = Date()
        saved.babyId = baby.id
        saved.updatedAt = now
        saved.deletedAt = nil
        saved.syncStatus = .localOnly
        return saved
    }

    private func prepared(_ record: DiaperRecord) -> DiaperRecord {
        var saved = record
        let now = Date()
        saved.babyId = baby.id
        saved.updatedAt = now
        saved.deletedAt = nil
        saved.syncStatus = .localOnly
        return saved
    }

    private func normalizeRecordsForCurrentBaby() {
        feedingRecords = feedingRecords.map { record in
            var normalized = record
            normalized.babyId = baby.id
            return normalized
        }
        sleepRecords = sleepRecords.map { record in
            var normalized = record
            normalized.babyId = baby.id
            return normalized
        }
        diaperRecords = diaperRecords.map { record in
            var normalized = record
            normalized.babyId = baby.id
            return normalized
        }
        vaccineRecords = vaccineRecords.map { record in
            var normalized = record
            if normalized.status == VaccineRecord.legacyCompletedStatus {
                normalized.status = VaccineRecord.administeredStatus
            }
            return normalized
        }
        if let reminder = feedingReminder {
            guard reminder.remindAt > Date() else {
                feedingReminder = nil
                return
            }

            var normalized = reminder
            normalized.babyId = baby.id
            feedingReminder = normalized
        }
    }

    private func loadState() {
        let stateFileExists = fileManager.fileExists(atPath: stateURL.path)
        let backupFileExists = fileManager.fileExists(atPath: backupStateURL.path)
        guard stateFileExists || backupFileExists else {
            photoCount = babyPhotos.count
            return
        }

        if let state = decodeState(at: stateURL) {
            apply(state)
        } else if let backupState = decodeState(at: backupStateURL) {
            preserveCorruptStateFile()
            apply(backupState)
            loadErrorMessage = "上次的数据文件读取异常，已从最近一次备份恢复。请检查记录是否完整。"
        } else {
            // 文件存在但两份都无法解码：进入安全模式。保留原文件，禁止任何写入，
            // 绝不能以“空状态”覆盖用户已有的记录。
            preserveCorruptStateFile()
            isPersistenceBlocked = true
            loadErrorMessage = "本地数据文件读取异常。为保护已有记录，本次已暂停保存功能，请不要新增记录并尝试重启 App；若持续出现请联系我们协助恢复。"
            photoCount = babyPhotos.count
            return
        }

        // 仅当本机曾注入过截图用 mock 数据时才清理遗留 mock 档案。
        // 绝不允许仅凭 UUID 命中就删除用户数据。
        if baby.id == Self.legacyMockBabyID, userDefaults.bool(forKey: Self.mockDataSeededDefaultsKey) {
            resetToEmptyProfile()
            userDefaults.removeObject(forKey: Self.mockDataSeededDefaultsKey)
        }
    }

    private func apply(_ state: LocalAppState) {
        baby = state.baby ?? Self.emptyBaby
        hasCompletedOnboarding = state.hasCompletedOnboarding
        feedingRecords = state.feedingRecords
        waterRecords = state.waterRecords
        feedingReminder = state.feedingReminder
        sleepRecords = state.sleepRecords
        diaperRecords = state.diaperRecords
        growthRecords = state.growthRecords
        vaccineRecords = state.vaccineRecords
        milestones = state.milestones
        babyPhotos = state.babyPhotos
        quietCareModeEnabled = state.quietCareModeEnabled
        feedingLiveActivityEnabled = state.feedingLiveActivityEnabled
        photoCount = babyPhotos.count
    }

    private func decodeState(at url: URL) -> LocalAppState? {
        guard let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(LocalAppState.self, from: data)
    }

    private func preserveCorruptStateFile() {
        guard fileManager.fileExists(atPath: stateURL.path) else { return }
        let stamp = Int(Date().timeIntervalSince1970)
        let corruptURL = applicationSupportDirectory.appendingPathComponent("\(stateFileName).corrupt-\(stamp)")
        try? fileManager.copyItem(at: stateURL, to: corruptURL)
    }

    private func loadFeedingReminderPreference() {
        guard let data = userDefaults.data(forKey: feedingReminderPreferenceKey(for: baby.id)),
              let preference = try? JSONDecoder().decode(FeedingReminderPreference.self, from: data),
              preference.babyId == baby.id else {
            feedingReminderPreference = FeedingReminderPreference(babyId: baby.id)
            return
        }
        feedingReminderPreference = preference
    }

    private func saveFeedingReminderPreference(_ preference: FeedingReminderPreference) -> Bool {
        guard let data = try? JSONEncoder().encode(preference) else { return false }
        userDefaults.set(data, forKey: feedingReminderPreferenceKey(for: preference.babyId))
        return true
    }

    private func removeFeedingReminderPreference(for babyID: UUID) {
        userDefaults.removeObject(forKey: feedingReminderPreferenceKey(for: babyID))
    }

    private func feedingReminderPreferenceKey(for babyID: UUID) -> String {
        "xiaonaiping.feeding-reminder-preference.\(babyID.uuidString)"
    }

    @discardableResult
    private func saveState() -> Bool {
        let state = LocalAppState(
            hasCompletedOnboarding: hasCompletedOnboarding,
            baby: baby,
            feedingRecords: feedingRecords,
            waterRecords: waterRecords,
            feedingReminder: feedingReminder,
            sleepRecords: sleepRecords,
            diaperRecords: diaperRecords,
            growthRecords: growthRecords,
            vaccineRecords: vaccineRecords,
            milestones: milestones,
            babyPhotos: babyPhotos,
            quietCareModeEnabled: quietCareModeEnabled,
            feedingLiveActivityEnabled: feedingLiveActivityEnabled
        )

        guard !isPersistenceBlocked else {
            saveErrorMessage = "本地数据文件读取异常，为保护已有记录已暂停保存。请重启 App；若持续出现请联系我们。"
            return false
        }

        do {
            let data = try JSONEncoder().encode(state)
            try ensureApplicationSupportDirectory()
            // 三段式写入：先写临时文件，替换时把上一版轮转为备份，
            // 任意一步失败都不会破坏当前生效的状态文件。
            let stagingURL = applicationSupportDirectory.appendingPathComponent("\(stateFileName).new")
            try data.write(to: stagingURL, options: [.atomic])
            if fileManager.fileExists(atPath: stateURL.path) {
                try? fileManager.removeItem(at: backupStateURL)
                _ = try fileManager.replaceItemAt(
                    stateURL,
                    withItemAt: stagingURL,
                    backupItemName: backupStateFileName,
                    options: .withoutDeletingBackupItem
                )
            } else {
                try fileManager.moveItem(at: stagingURL, to: stateURL)
            }
            try? markIncludedInBackup(stateURL)
            try? markIncludedInBackup(backupStateURL)
            writeSharedTodaySnapshot()
            saveErrorMessage = nil
            NotificationCenter.default.post(name: .babyRecordStoreDidSave, object: self)
            return true
        } catch {
            saveErrorMessage = "保存失败，请检查网络或设备存储空间后重试。"
            return false
        }
    }

    private var stateURL: URL {
        applicationSupportDirectory.appendingPathComponent(stateFileName)
    }

    private var backupStateURL: URL {
        applicationSupportDirectory.appendingPathComponent(backupStateFileName)
    }

    private var applicationSupportDirectory: URL {
        if let storageDirectoryOverride {
            return storageDirectoryOverride
        }
        let baseURL = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return baseURL.appendingPathComponent("XiaoNaiPing", isDirectory: true)
    }

    private var photosDirectory: URL {
        applicationSupportDirectory.appendingPathComponent("Photos", isDirectory: true)
    }

    private func ensureApplicationSupportDirectory() throws {
        try fileManager.createDirectory(at: applicationSupportDirectory, withIntermediateDirectories: true)
        try markIncludedInBackup(applicationSupportDirectory)
    }

    private func ensurePhotosDirectory() throws -> URL {
        try ensureApplicationSupportDirectory()
        try fileManager.createDirectory(at: photosDirectory, withIntermediateDirectories: true)
        try markIncludedInBackup(photosDirectory)
        return photosDirectory
    }

    private func sanitizedJPEGData(from data: Data) -> Data {
        guard let image = UIImage(data: data),
              let sanitizedData = image.jpegData(compressionQuality: 0.88) else {
            return data
        }

        return sanitizedData
    }

    private func sanitizedAvatarJPEGData(from data: Data) -> Data? {
        guard let image = UIImage(data: data) else { return nil }
        let maxSide: CGFloat = 512
        let longestSide = max(image.size.width, image.size.height)
        let scale = longestSide > maxSide ? maxSide / longestSide : 1
        let targetSize = CGSize(width: image.size.width * scale, height: image.size.height * scale)
        let renderer = UIGraphicsImageRenderer(size: targetSize)
        let resized = renderer.image { _ in
            image.draw(in: CGRect(origin: .zero, size: targetSize))
        }
        return resized.jpegData(compressionQuality: 0.84)
    }

    // 婴儿记录是不可重建数据，必须允许随 iCloud/整机备份迁移。
    // 该方法同时会清掉历史版本设置过的排除标记。
    private func markIncludedInBackup(_ url: URL) throws {
        guard fileManager.fileExists(atPath: url.path) else { return }
        var resourceValues = URLResourceValues()
        resourceValues.isExcludedFromBackup = false
        var mutableURL = url
        try mutableURL.setResourceValues(resourceValues)
    }

    /// 历史版本曾把状态文件、照片目录和每张照片都排除在备份之外；
    /// 这里做一次性迁移，把已存在文件的排除标记全部清掉。
    private func removeLegacyBackupExclusionIfNeeded() {
        let migrationKey = "xnp.migration.backup-exclusion-removed"
        guard !userDefaults.bool(forKey: migrationKey) else { return }
        try? markIncludedInBackup(applicationSupportDirectory)
        try? markIncludedInBackup(stateURL)
        try? markIncludedInBackup(backupStateURL)
        try? markIncludedInBackup(photosDirectory)
        if let files = try? fileManager.contentsOfDirectory(at: photosDirectory, includingPropertiesForKeys: nil) {
            for file in files {
                try? markIncludedInBackup(file)
            }
        }
        userDefaults.set(true, forKey: migrationKey)
    }

    private static func delta(_ latest: Double?, _ previous: Double?) -> Double? {
        guard let latest, let previous else { return nil }
        return latest - previous
    }

    static func timeString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }

    static func dateString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy.MM.dd"
        return formatter.string(from: date)
    }

    static func date(fromDateString value: String) -> Date? {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy.MM.dd"
        return formatter.date(from: value)
    }

    static func reminderDateTimeString(from date: Date) -> String {
        "\(displayDateString(from: date)) \(timeString(from: date))"
    }

    static func displayDateString(from date: Date) -> String {
        if Calendar.current.isDateInToday(date) {
            return "今天".localizedText
        }

        if Calendar.current.isDateInTomorrow(date) {
            return "明天".localizedText
        }

        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = Calendar.current.isDate(date, equalTo: Date(), toGranularity: .year)
            ? "M月d日"
            : "yyyy年M月d日"
        return formatter.string(from: date)
    }

    static func monthString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = "M月"
        return formatter.string(from: date)
    }

    static func reportMonthString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = "yyyy年M月"
        return formatter.string(from: date)
    }

    static func durationText(from minutes: Int) -> String {
        guard minutes > 0 else { return AppLocalization.format("%d分钟", 0) }
        let hours = minutes / 60
        let remainingMinutes = minutes % 60

        if hours == 0 {
            return AppLocalization.format("%d分钟", remainingMinutes)
        }

        if remainingMinutes == 0 {
            return AppLocalization.format("%d小时", hours)
        }

        return AppLocalization.format("%d小时%d分", hours, remainingMinutes)
    }

    private static func feedingEndDate(_ record: FeedingRecord) -> Date {
        guard let durationMinutes = record.durationMinutes, durationMinutes > 0,
              let endDate = Calendar.current.date(byAdding: .minute, value: durationMinutes, to: record.occurredAt) else {
            return record.occurredAt
        }

        return endDate
    }

    private static func elapsedText(since date: Date, now: Date) -> String {
        let minutes = max(0, Calendar.current.dateComponents([.minute], from: date, to: now).minute ?? 0)
        if minutes < 1 {
            return "刚刚".localizedText
        }
        if minutes < 60 {
            return AppLocalization.format("%d分钟前", minutes)
        }
        let hours = minutes / 60
        let remainingMinutes = minutes % 60
        if remainingMinutes == 0 {
            return AppLocalization.format("%d小时前", hours)
        }
        return AppLocalization.format("%d小时%d分前", hours, remainingMinutes)
    }

    private func makeSharedTodaySnapshot() -> SharedTodaySnapshot {
        SharedTodaySnapshot(
            hasCompletedOnboarding: hasCompletedOnboarding,
            babyName: baby.name,
            daysSinceBirth: currentBabyDaysSinceBirth,
            feedingCount: feedingCount,
            milkAmountML: milkAmountML,
            lastFeedingAt: lastFeedingRecord.map(Self.feedingEndDate),
            ongoingSleepStartAt: ongoingSleep?.startAt,
            nextFeedingReminderAt: nextFeedingReminder?.remindAt,
            feedingReminderRepeatIntervalMinutes: nextFeedingReminder?.origin == .automatic
                ? feedingReminderPreference.intervalMinutes
                : nil,
            poopCount: poopCount,
            peeCount: peeCount,
            generatedAt: Date()
        )
    }

    private func writeSharedTodaySnapshot() {
        try? XiaoNaiPingSharedStore.writeSnapshot(makeSharedTodaySnapshot())
        // 主动通知 WidgetKit 刷新，否则桌面小组件最长要等 15 分钟
        // 才会显示刚记完的这一笔——而“距上次喂奶”正是它的核心价值。
        WidgetCenter.shared.reloadAllTimelines()
    }

    static func date(fromTimeString time: String) -> Date {
        var components = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        let parts = time.split(separator: ":").compactMap { Int($0) }
        components.hour = parts.first ?? 0
        components.minute = parts.dropFirst().first ?? 0
        return Calendar.current.date(from: components) ?? Date()
    }

    private static func isTodaySleepRecord(_ record: SleepRecord) -> Bool {
        isSleepRecord(record, on: Date())
    }

    static func isSleepRecord(_ record: SleepRecord, on day: Date) -> Bool {
        let dayStart = Calendar.current.startOfDay(for: day)
        let dayEnd = Calendar.current.date(byAdding: .day, value: 1, to: dayStart) ?? day
        let endAt = record.endAt ?? Date()

        if record.isOngoing {
            return record.startAt < dayEnd
        }

        return record.startAt < dayEnd && endAt >= dayStart
    }

    private static func sleepMinutesDuringToday(_ record: SleepRecord) -> Int {
        sleepMinutes(of: record, on: Date())
    }

    static func sleepMinutes(of record: SleepRecord, on day: Date) -> Int {
        let dayStart = Calendar.current.startOfDay(for: day)
        let dayEnd = Calendar.current.date(byAdding: .day, value: 1, to: dayStart) ?? day
        let recordEnd = record.endAt ?? min(Date(), dayEnd)
        let overlapStart = max(record.startAt, dayStart)
        let overlapEnd = min(recordEnd, dayEnd)
        return max(0, Calendar.current.dateComponents([.minute], from: overlapStart, to: overlapEnd).minute ?? 0)
    }

    private static func isSameMonth(_ date: Date, monthDate: Date) -> Bool {
        return Calendar.current.isDate(date, equalTo: monthDate, toGranularity: .month)
    }

    private static func isSameMonthSleepRecord(_ record: SleepRecord, monthDate: Date) -> Bool {
        let monthStart = Calendar.current.date(from: Calendar.current.dateComponents([.year, .month], from: monthDate)) ?? monthDate
        let nextMonthStart = Calendar.current.date(byAdding: .month, value: 1, to: monthStart) ?? monthDate
        let endAt = record.endAt ?? Date()
        return record.startAt < nextMonthStart && endAt >= monthStart
    }

    private static func sleepSortDate(_ record: SleepRecord) -> Date {
        record.endAt ?? record.startAt
    }

    private static func sortableDate(_ value: Date?, timeString: String) -> Date {
        value ?? date(fromTimeString: timeString)
    }

    static func daysSinceBirth(from birthDate: Date) -> Int {
        let start = Calendar.current.startOfDay(for: birthDate)
        let today = Calendar.current.startOfDay(for: Date())
        return max(0, (Calendar.current.dateComponents([.day], from: start, to: today).day ?? 0) + 1)
    }

    static func ageText(from birthDate: Date) -> String {
        let days = daysSinceBirth(from: birthDate)
        if days <= 31 {
            return AppLocalization.format("第%d天", days)
        }

        let months = max(1, days / 30)
        let remainingDays = days % 30
        return AppLocalization.format("%d个月%d天", months, remainingDays)
    }

    static func date(fromDisplayDateString value: String) -> Date? {
        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = "yyyy年M月d日"
        if let date = formatter.date(from: value) {
            return date
        }

        formatter.locale = Locale(identifier: "zh_Hans_CN")
        return formatter.date(from: value)
    }

    private static let emptyBaby = Baby(
        id: UUID(),
        name: "宝宝",
        daysSinceBirth: 0,
        ageText: "第1天",
        birthDate: Date(),
        sex: "未设置"
    )

    private static let automaticMilestoneDefinitions: [(title: String, dayNumber: Int)] = [
        ("满月", 30),
        ("百天", 100),
        ("半岁", 183),
        ("一周岁", 365),
        ("两周岁", 730),
        ("三周岁", 1095)
    ]

    private static let legacyMockBabyID = UUID(uuidString: "11111111-1111-1111-1111-111111111111")!

    private func resetToEmptyProfile() {
        baby = Self.emptyBaby
        hasCompletedOnboarding = false
        removeAllLocalRecords()
    }
}

/// 单个元素解码失败时跳过该元素而不是让整个数组（乃至整份状态）解码失败。
/// 婴儿记录不可重建：一条坏记录绝不能导致全部数据被视为不存在。
struct FailableDecodable<T: Decodable>: Decodable {
    let value: T?

    init(from decoder: Decoder) {
        value = try? T(from: decoder)
    }
}

private struct LocalAppState: Codable {
    var hasCompletedOnboarding: Bool
    var baby: Baby?
    var feedingRecords: [FeedingRecord]
    var waterRecords: [WaterRecord]
    var feedingReminder: FeedingReminder?
    var sleepRecords: [SleepRecord]
    var diaperRecords: [DiaperRecord]
    var growthRecords: [GrowthRecord]
    var vaccineRecords: [VaccineRecord]
    var milestones: [Milestone]
    var babyPhotos: [BabyPhoto]
    var quietCareModeEnabled: Bool
    var feedingLiveActivityEnabled: Bool

    private enum CodingKeys: String, CodingKey {
        case hasCompletedOnboarding
        case baby
        case feedingRecords
        case waterRecords
        case feedingReminder
        case sleepRecords
        case diaperRecords
        case growthRecords
        case vaccineRecords
        case milestones
        case babyPhotos
        case quietCareModeEnabled
        case feedingLiveActivityEnabled
    }

    init(
        hasCompletedOnboarding: Bool,
        baby: Baby,
        feedingRecords: [FeedingRecord],
        waterRecords: [WaterRecord] = [],
        feedingReminder: FeedingReminder? = nil,
        sleepRecords: [SleepRecord],
        diaperRecords: [DiaperRecord],
        growthRecords: [GrowthRecord],
        vaccineRecords: [VaccineRecord],
        milestones: [Milestone],
        babyPhotos: [BabyPhoto],
        quietCareModeEnabled: Bool = true,
        feedingLiveActivityEnabled: Bool = true
    ) {
        self.hasCompletedOnboarding = hasCompletedOnboarding
        self.baby = baby
        self.feedingRecords = feedingRecords
        self.waterRecords = waterRecords
        self.feedingReminder = feedingReminder
        self.sleepRecords = sleepRecords
        self.diaperRecords = diaperRecords
        self.growthRecords = growthRecords
        self.vaccineRecords = vaccineRecords
        self.milestones = milestones
        self.babyPhotos = babyPhotos
        self.quietCareModeEnabled = quietCareModeEnabled
        self.feedingLiveActivityEnabled = feedingLiveActivityEnabled
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        hasCompletedOnboarding = try container.decodeIfPresent(Bool.self, forKey: .hasCompletedOnboarding) ?? false
        baby = Self.tolerantValue(Baby.self, in: container, forKey: .baby)
        feedingRecords = Self.tolerantArray(FeedingRecord.self, in: container, forKey: .feedingRecords)
        waterRecords = Self.tolerantArray(WaterRecord.self, in: container, forKey: .waterRecords)
        feedingReminder = Self.tolerantValue(FeedingReminder.self, in: container, forKey: .feedingReminder)
        sleepRecords = Self.tolerantArray(SleepRecord.self, in: container, forKey: .sleepRecords)
        diaperRecords = Self.tolerantArray(DiaperRecord.self, in: container, forKey: .diaperRecords)
        growthRecords = Self.tolerantArray(GrowthRecord.self, in: container, forKey: .growthRecords)
        vaccineRecords = Self.tolerantArray(VaccineRecord.self, in: container, forKey: .vaccineRecords)
        milestones = Self.tolerantArray(Milestone.self, in: container, forKey: .milestones)
        babyPhotos = Self.tolerantArray(BabyPhoto.self, in: container, forKey: .babyPhotos)
        quietCareModeEnabled = try container.decodeIfPresent(Bool.self, forKey: .quietCareModeEnabled) ?? true
        feedingLiveActivityEnabled = try container.decodeIfPresent(Bool.self, forKey: .feedingLiveActivityEnabled) ?? true
    }

    private static func tolerantArray<T: Decodable>(
        _ type: T.Type,
        in container: KeyedDecodingContainer<CodingKeys>,
        forKey key: CodingKeys
    ) -> [T] {
        let wrapped = (try? container.decodeIfPresent([FailableDecodable<T>].self, forKey: key)) ?? nil
        return wrapped?.compactMap(\.value) ?? []
    }

    private static func tolerantValue<T: Decodable>(
        _ type: T.Type,
        in container: KeyedDecodingContainer<CodingKeys>,
        forKey key: CodingKeys
    ) -> T? {
        ((try? container.decodeIfPresent(FailableDecodable<T>.self, forKey: key)) ?? nil)?.value
    }
}

struct MonthlyReportSnapshot: Equatable {
    var monthTitle: String = ""
    var feedingCount: Int
    var milkAmountML: Int
    var sleepDurationText: String
    var diaperCount: Int
    var photoCount: Int
    var latestWeight: Double?
    var latestHeight: Double?
    var weightDelta: Double?
    var heightDelta: Double?
    var milestoneCount: Int
    var vaccineOpenCount: Int
    var recordCount: Int = 0
}

struct HomeRecentRecord: Identifiable, Equatable {
    var id: String
    var sortDate: Date
    var time: String
    var icon: String?
    var systemIcon: String? = nil
    var title: String
    var detail: String
}

private struct VaccineTemplate {
    var title: String
    var dayOffset: Int

    static func templates(for region: String) -> [VaccineTemplate] {
        switch region {
        case BabyRecordStore.hongKongVaccineRegion:
            [
                VaccineTemplate(title: "乙肝疫苗 第1针", dayOffset: 0),
                VaccineTemplate(title: "乙肝疫苗 第2针", dayOffset: 30),
                VaccineTemplate(title: "六联疫苗 第1针", dayOffset: 60),
                VaccineTemplate(title: "肺炎球菌疫苗 第1针", dayOffset: 60),
                VaccineTemplate(title: "轮状病毒疫苗 第1剂", dayOffset: 60),
                VaccineTemplate(title: "六联疫苗 第2针", dayOffset: 120),
                VaccineTemplate(title: "肺炎球菌疫苗 第2针", dayOffset: 120),
                VaccineTemplate(title: "麻疹腮腺炎风疹疫苗 第1针", dayOffset: 365)
            ]
        default:
            [
                VaccineTemplate(title: "乙肝疫苗 第1针", dayOffset: 0),
                VaccineTemplate(title: "卡介苗", dayOffset: 0),
                VaccineTemplate(title: "乙肝疫苗 第2针", dayOffset: 30),
                VaccineTemplate(title: "脊灰疫苗 第1剂", dayOffset: 60),
                VaccineTemplate(title: "百白破疫苗 第1针", dayOffset: 90),
                VaccineTemplate(title: "脊灰疫苗 第2剂", dayOffset: 90),
                VaccineTemplate(title: "百白破疫苗 第2针", dayOffset: 120),
                VaccineTemplate(title: "麻腮风疫苗 第1针", dayOffset: 240)
            ]
        }
    }

}
