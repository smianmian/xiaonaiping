import Foundation
import Combine

final class BabyRecordStore: ObservableObject {
    @Published var baby = MockData.baby
    @Published var feedingRecords = MockData.feedingRecords
    @Published var sleepRecords = MockData.sleepRecords
    @Published var diaperRecords = MockData.diaperRecords
    @Published var growthRecords = MockData.growthRecords
    @Published var vaccineRecords = MockData.vaccines
    @Published var milestones = MockData.milestones
    @Published var photoCount = MockData.summary.photoCount

    var hundredDaysRemaining: Int {
        max(0, 100 - baby.daysSinceBirth)
    }

    var feedingCount: Int {
        feedingRecords.count
    }

    var milkAmountML: Int {
        feedingRecords.compactMap(\.amountML).reduce(0, +)
    }

    var sleepDurationText: String {
        Self.durationText(from: totalSleepMinutes)
    }

    var totalSleepMinutes: Int {
        sleepRecords.compactMap(\.durationMinutes).reduce(0, +)
    }

    var ongoingSleep: SleepRecord? {
        sleepRecords.first { $0.isOngoing }
    }

    var poopCount: Int {
        diaperRecords.filter { $0.kind == "大便" }.count
    }

    var peeCount: Int {
        diaperRecords.filter { $0.kind == "小便" }.count
    }

    var nextVaccine: VaccineRecord? {
        vaccineRecords
            .filter { $0.status != "已完成" }
            .sorted { ($0.dueDays ?? Int.max) < ($1.dueDays ?? Int.max) }
            .first
    }

    var latestGrowthRecord: GrowthRecord? {
        growthRecords.last
    }

    var monthlyReport: MonthlyReportSnapshot {
        let latest = latestGrowthRecord
        let previous = growthRecords.dropLast().last
        return MonthlyReportSnapshot(
            feedingCount: feedingCount,
            milkAmountML: milkAmountML,
            sleepDurationText: sleepDurationText,
            diaperCount: diaperRecords.count,
            photoCount: photoCount,
            latestWeight: latest?.weight,
            latestHeight: latest?.height,
            weightDelta: Self.delta(latest?.weight, previous?.weight),
            heightDelta: Self.delta(latest?.height, previous?.height),
            milestoneCount: milestones.count,
            vaccineOpenCount: vaccineRecords.filter { $0.status != "已完成" }.count
        )
    }

    func upsert(_ record: FeedingRecord) {
        if let index = feedingRecords.firstIndex(where: { $0.id == record.id }) {
            feedingRecords[index] = record
        } else {
            feedingRecords.insert(record, at: 0)
        }
    }

    func deleteFeedingRecord(_ record: FeedingRecord) {
        feedingRecords.removeAll { $0.id == record.id }
    }

    func upsert(_ record: SleepRecord) {
        if let index = sleepRecords.firstIndex(where: { $0.id == record.id }) {
            sleepRecords[index] = record
        } else {
            sleepRecords.insert(record, at: 0)
        }
    }

    func deleteSleepRecord(_ record: SleepRecord) {
        sleepRecords.removeAll { $0.id == record.id }
    }

    func startSleepNow() {
        guard ongoingSleep == nil else { return }
        let now = Date()
        let record = SleepRecord(
            start: Self.timeString(from: now),
            end: "进行中",
            type: "小睡",
            duration: "进行中",
            icon: AppAssets.moonIcon,
            isOngoing: true
        )
        sleepRecords.insert(record, at: 0)
    }

    func finishOngoingSleepNow() {
        guard let ongoing = ongoingSleep,
              let index = sleepRecords.firstIndex(where: { $0.id == ongoing.id }) else { return }

        let endDate = Date()
        let startDate = Self.date(fromTimeString: ongoing.start)
        let minutes = max(1, Calendar.current.dateComponents([.minute], from: startDate, to: endDate).minute ?? 1)
        sleepRecords[index].end = Self.timeString(from: endDate)
        sleepRecords[index].durationMinutes = minutes
        sleepRecords[index].duration = Self.durationText(from: minutes)
        sleepRecords[index].isOngoing = false
    }

    func upsert(_ record: DiaperRecord) {
        if let index = diaperRecords.firstIndex(where: { $0.id == record.id }) {
            diaperRecords[index] = record
        } else {
            diaperRecords.insert(record, at: 0)
        }
    }

    func deleteDiaperRecord(_ record: DiaperRecord) {
        diaperRecords.removeAll { $0.id == record.id }
    }

    func upsert(_ record: GrowthRecord) {
        if let index = growthRecords.firstIndex(where: { $0.id == record.id }) {
            growthRecords[index] = record
        } else {
            growthRecords.append(record)
        }
    }

    func deleteGrowthRecord(_ record: GrowthRecord) {
        growthRecords.removeAll { $0.id == record.id }
    }

    func upsert(_ record: VaccineRecord) {
        if let index = vaccineRecords.firstIndex(where: { $0.id == record.id }) {
            vaccineRecords[index] = record
        } else {
            vaccineRecords.insert(record, at: 0)
        }
    }

    func deleteVaccineRecord(_ record: VaccineRecord) {
        vaccineRecords.removeAll { $0.id == record.id }
    }

    func toggleVaccineCompleted(_ record: VaccineRecord) {
        guard let index = vaccineRecords.firstIndex(where: { $0.id == record.id }) else { return }
        if vaccineRecords[index].status == "已完成" {
            vaccineRecords[index].status = "待接种"
            vaccineRecords[index].tintName = "orange"
        } else {
            vaccineRecords[index].status = "已完成"
            vaccineRecords[index].tintName = "green"
        }
    }

    func upsert(_ milestone: Milestone) {
        if let index = milestones.firstIndex(where: { $0.id == milestone.id }) {
            milestones[index] = milestone
        } else {
            milestones.insert(milestone, at: 0)
        }
    }

    func deleteMilestone(_ milestone: Milestone) {
        milestones.removeAll { $0.id == milestone.id }
    }

    func clearLocalDemoRecords() {
        feedingRecords.removeAll()
        sleepRecords.removeAll()
        diaperRecords.removeAll()
        growthRecords.removeAll()
        vaccineRecords.removeAll()
        milestones.removeAll()
        photoCount = 0
    }

    private static func delta(_ latest: Double?, _ previous: Double?) -> Double? {
        guard let latest, let previous else { return nil }
        return latest - previous
    }

    static func timeString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_Hans_CN")
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }

    static func dateString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_Hans_CN")
        formatter.dateFormat = "yyyy.MM.dd"
        return formatter.string(from: date)
    }

    static func displayDateString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_Hans_CN")
        formatter.dateFormat = "yyyy年M月d日"
        return formatter.string(from: date)
    }

    static func monthString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_Hans_CN")
        formatter.dateFormat = "M月"
        return formatter.string(from: date)
    }

    static func durationText(from minutes: Int) -> String {
        guard minutes > 0 else { return "0分钟" }
        let hours = minutes / 60
        let remainingMinutes = minutes % 60

        if hours == 0 {
            return "\(remainingMinutes)分钟"
        }

        if remainingMinutes == 0 {
            return "\(hours)小时"
        }

        return "\(hours)小时\(remainingMinutes)分"
    }

    static func date(fromTimeString time: String) -> Date {
        var components = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        let parts = time.split(separator: ":").compactMap { Int($0) }
        components.hour = parts.first ?? 0
        components.minute = parts.dropFirst().first ?? 0
        return Calendar.current.date(from: components) ?? Date()
    }
}

struct MonthlyReportSnapshot: Equatable {
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
}
