import Foundation
import Combine
import UIKit

extension Notification.Name {
    static let babyRecordStoreDidSave = Notification.Name("babyRecordStoreDidSave")
}

private enum PhotoImportError: Error {
    case saveFailed
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

    private let fileManager = FileManager.default
    private let stateFileName = "xiaonaiping-local-state.json"

    init(seedMockData: Bool = false) {
        loadState()
        if seedMockData {
            applyMockData()
        }

        normalizeRecordsForCurrentBaby()
        writeSharedTodaySnapshot()
    }

    private func applyMockData() {
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
                daysRemaining: max(0, definition.dayNumber - baby.daysSinceBirth),
                isReached: baby.daysSinceBirth >= definition.dayNumber
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
        waterRecords
            .filter { Calendar.current.isDateInToday($0.occurredAt) }
            .sorted { $0.occurredAt > $1.occurredAt }
    }

    var lastFeedingRecord: FeedingRecord? {
        todayFeedingRecords.first
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
            .filter { !$0.isOngoing }
            .compactMap(\.durationMinutes)
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
        feedingRecords
            .filter { Calendar.current.isDateInToday($0.occurredAt) }
            .sorted { $0.occurredAt > $1.occurredAt }
    }

    var nextFeedingReminder: FeedingReminder? {
        guard var feedingReminder,
              let nextRemindAt = feedingReminder.nextRemindAt(after: Date()) else {
            return nil
        }
        feedingReminder.remindAt = nextRemindAt
        return feedingReminder
    }

    var todaySleepRecords: [SleepRecord] {
        sleepRecords
            .filter(Self.isTodaySleepRecord)
            .sorted { Self.sleepSortDate($0) > Self.sleepSortDate($1) }
    }

    var todayDiaperRecords: [DiaperRecord] {
        diaperRecords
            .filter { Calendar.current.isDateInToday($0.occurredAt) }
            .sorted { $0.occurredAt > $1.occurredAt }
    }

    var recentHomeRecords: [HomeRecentRecord] {
        let feeding = todayFeedingRecords.map { record in
            HomeRecentRecord(
                id: "feeding-\(record.id.uuidString)",
                sortDate: Self.sortableDate(record.occurredAt, timeString: record.time),
                time: record.time,
                icon: record.icon,
                title: "喂养 · \(record.type)",
                detail: record.detail
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
                icon: AppAssets.peeDropIcon,
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
        guard days != Int.max else { return "--" }
        return "\(abs(days))"
    }

    func vaccineDueUnit(_ record: VaccineRecord) -> String {
        let days = vaccineDaysUntil(record)
        if days < 0 {
            return "天前"
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
        growthRecords.last
    }

    var monthlyReport: MonthlyReportSnapshot {
        monthlyReport(for: Date())
    }

    func monthlyReport(for monthDate: Date) -> MonthlyReportSnapshot {
        let monthlyFeedings = feedingRecords.filter { Self.isSameMonth($0.occurredAt, monthDate: monthDate) }
        let monthlySleep = sleepRecords.filter { Self.isSameMonthSleepRecord($0, monthDate: monthDate) }
        let monthlyDiapers = diaperRecords.filter { Self.isSameMonth($0.occurredAt, monthDate: monthDate) }
        let monthlyPhotos = babyPhotos.filter { Calendar.current.isDate($0.capturedAt, equalTo: monthDate, toGranularity: .month) }
        let monthlyGrowth = growthRecords.filter { record in
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
        baby = Baby(
            id: UUID(),
            name: "宝宝",
            daysSinceBirth: 0,
            ageText: "第1天",
            birthDate: Date(),
            sex: "未设置"
        )
        removeAllLocalRecords()
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
        try markExcludedFromBackup(destinationURL)

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

    func encodedCloudBackupData() throws -> Data {
        let payload = CloudBackupPayload(
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

    func restoreCloudBackupData(_ data: Data) throws {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let payload = try decoder.decode(CloudBackupPayload.self, from: data)
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
        normalizeRecordsForCurrentBaby()
        saveState()
    }

    func localPhotoBackupAssets() -> [LocalPhotoBackupAsset] {
        babyPhotos.compactMap { photo in
            let url = photoURL(for: photo)
            guard fileManager.fileExists(atPath: url.path) else { return nil }
            return LocalPhotoBackupAsset(photo: photo, fileURL: url)
        }
    }

    func restoreCloudPhotoData(for photo: BabyPhoto, data: Data) throws {
        let destinationURL = try ensurePhotosDirectory().appendingPathComponent(photo.localFileName)
        try data.write(to: destinationURL, options: [.atomic])
        try markExcludedFromBackup(destinationURL)
        markCloudPhotoBackedUp(photo)
    }

    func markCloudPhotoBackedUp(_ photo: BabyPhoto) {
        guard let index = babyPhotos.firstIndex(where: { $0.id == photo.id }) else { return }
        babyPhotos[index].backupStatus = .backedUp
        saveState()
    }

    func markCloudPhotoDeletePending(_ photo: BabyPhoto) {
        guard let index = babyPhotos.firstIndex(where: { $0.id == photo.id }) else { return }
        babyPhotos[index].backupStatus = .cloudDeletePending
        saveState()
    }

    func markCloudBackupCompleted() {
        feedingRecords = feedingRecords.map { record in
            var updated = record
            updated.syncStatus = .synced
            return updated
        }
        waterRecords = waterRecords.map { record in
            var normalized = record
            normalized.babyId = baby.id
            return normalized
        }
        sleepRecords = sleepRecords.map { record in
            var updated = record
            updated.syncStatus = .synced
            return updated
        }
        diaperRecords = diaperRecords.map { record in
            var updated = record
            updated.syncStatus = .synced
            return updated
        }
        babyPhotos = babyPhotos.map { photo in
            var updated = photo
            updated.backupStatus = .backedUp
            return updated
        }
        saveState()
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
            updated.backupStatus = .localOnly
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
                if reminder.nextRemindAt(after: Date()) != nil {
                    var normalized = reminder
                    normalized.babyId = baby.id
                    feedingReminder = normalized
                    return
                }
                feedingReminder = nil
                return
            }

            var normalized = reminder
            normalized.babyId = baby.id
            feedingReminder = normalized
        }
    }

    private func loadState() {
        guard let data = try? Data(contentsOf: stateURL),
              let state = try? JSONDecoder().decode(LocalAppState.self, from: data) else {
            photoCount = babyPhotos.count
            return
        }

        baby = state.baby
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

        if baby.id == Self.legacyMockBabyID {
            resetToEmptyProfile()
        }
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

        do {
            let data = try JSONEncoder().encode(state)
            try ensureApplicationSupportDirectory()
            try data.write(to: stateURL, options: [.atomic])
            try markExcludedFromBackup(stateURL)
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

    private var applicationSupportDirectory: URL {
        let baseURL = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
        return baseURL.appendingPathComponent("XiaoNaiPing", isDirectory: true)
    }

    private var photosDirectory: URL {
        applicationSupportDirectory.appendingPathComponent("Photos", isDirectory: true)
    }

    private func ensureApplicationSupportDirectory() throws {
        try fileManager.createDirectory(at: applicationSupportDirectory, withIntermediateDirectories: true)
        try markExcludedFromBackup(applicationSupportDirectory)
    }

    private func ensurePhotosDirectory() throws -> URL {
        try ensureApplicationSupportDirectory()
        try fileManager.createDirectory(at: photosDirectory, withIntermediateDirectories: true)
        try markExcludedFromBackup(photosDirectory)
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

    private func markExcludedFromBackup(_ url: URL) throws {
        var resourceValues = URLResourceValues()
        resourceValues.isExcludedFromBackup = true
        var mutableURL = url
        try mutableURL.setResourceValues(resourceValues)
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
        if Calendar.current.isDateInToday(date) {
            return AppLocalization.format("今天 %@", timeString(from: date))
        }

        if Calendar.current.isDateInTomorrow(date) {
            return AppLocalization.format("明天 %@", timeString(from: date))
        }

        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = "M月d日 HH:mm"
        return formatter.string(from: date)
    }

    static func displayDateString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = "yyyy年M月d日"
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
            daysSinceBirth: baby.daysSinceBirth,
            feedingCount: feedingCount,
            milkAmountML: milkAmountML,
            lastFeedingAt: lastFeedingRecord.map(Self.feedingEndDate),
            ongoingSleepStartAt: ongoingSleep?.startAt,
            nextFeedingReminderAt: nextFeedingReminder?.remindAt,
            feedingReminderRepeatIntervalMinutes: nextFeedingReminder?.repeatIntervalMinutes,
            poopCount: poopCount,
            peeCount: peeCount,
            generatedAt: Date()
        )
    }

    private func writeSharedTodaySnapshot() {
        try? XiaoNaiPingSharedStore.writeSnapshot(makeSharedTodaySnapshot())
    }

    static func date(fromTimeString time: String) -> Date {
        var components = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        let parts = time.split(separator: ":").compactMap { Int($0) }
        components.hour = parts.first ?? 0
        components.minute = parts.dropFirst().first ?? 0
        return Calendar.current.date(from: components) ?? Date()
    }

    private static func isTodaySleepRecord(_ record: SleepRecord) -> Bool {
        let startOfToday = Calendar.current.startOfDay(for: Date())
        let startOfTomorrow = Calendar.current.date(byAdding: .day, value: 1, to: startOfToday) ?? Date()
        let endAt = record.endAt ?? Date()

        if record.isOngoing {
            return record.startAt < startOfTomorrow
        }

        return record.startAt < startOfTomorrow && endAt >= startOfToday
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

private struct LocalAppState: Codable {
    var hasCompletedOnboarding: Bool
    var baby: Baby
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
        baby = try container.decode(Baby.self, forKey: .baby)
        feedingRecords = try container.decode([FeedingRecord].self, forKey: .feedingRecords)
        waterRecords = try container.decodeIfPresent([WaterRecord].self, forKey: .waterRecords) ?? []
        feedingReminder = try container.decodeIfPresent(FeedingReminder.self, forKey: .feedingReminder)
        sleepRecords = try container.decode([SleepRecord].self, forKey: .sleepRecords)
        diaperRecords = try container.decode([DiaperRecord].self, forKey: .diaperRecords)
        growthRecords = try container.decode([GrowthRecord].self, forKey: .growthRecords)
        vaccineRecords = try container.decode([VaccineRecord].self, forKey: .vaccineRecords)
        milestones = try container.decode([Milestone].self, forKey: .milestones)
        babyPhotos = try container.decode([BabyPhoto].self, forKey: .babyPhotos)
        quietCareModeEnabled = try container.decodeIfPresent(Bool.self, forKey: .quietCareModeEnabled) ?? true
        feedingLiveActivityEnabled = try container.decodeIfPresent(Bool.self, forKey: .feedingLiveActivityEnabled) ?? true
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
    var icon: String
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
