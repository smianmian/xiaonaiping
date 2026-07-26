import Foundation

enum MockData {
    private static let babyBirthDate = Calendar.current.date(byAdding: .day, value: -67, to: Date()) ?? Date()

    static let baby = Baby(
        id: UUID(uuidString: "11111111-1111-1111-1111-111111111111")!,
        name: "小奶瓶",
        daysSinceBirth: 68,
        ageText: "2个月7天",
        birthDate: babyBirthDate
    )

    static let feedingRecords = [
        FeedingRecord(time: "08:30", type: "母乳", detail: "右侧15分钟", icon: AppAssets.bottleIcon, durationMinutes: 15, breastSide: "右侧"),
        FeedingRecord(time: "11:20", type: "奶粉", detail: "120ml", icon: AppAssets.bottleIcon, amountML: 120),
        FeedingRecord(time: "14:10", type: "母乳", detail: "左侧18分钟", icon: AppAssets.bottleIcon, durationMinutes: 18, breastSide: "左侧"),
        FeedingRecord(time: "16:30", type: "奶粉", detail: "150ml", icon: AppAssets.bottleIcon, amountML: 150),
        FeedingRecord(time: "19:20", type: "母乳", detail: "右侧12分钟", icon: AppAssets.bottleIcon, durationMinutes: 12, breastSide: "右侧"),
        FeedingRecord(time: "22:00", type: "奶粉", detail: "150ml", icon: AppAssets.bottleIcon, amountML: 150)
    ]

    static let sleepRecords = [
        SleepRecord(start: "09:15", end: "10:05", type: "小睡", duration: "50分钟", icon: AppAssets.cloudBlue, durationMinutes: 50),
        SleepRecord(start: "12:30", end: "13:20", type: "小睡", duration: "50分钟", icon: AppAssets.cloudBlue, durationMinutes: 50),
        SleepRecord(start: "16:00", end: "16:40", type: "小睡", duration: "40分钟", icon: AppAssets.cloudBlue, durationMinutes: 40),
        SleepRecord(start: "20:30", end: "06:40", type: "夜睡", duration: "10小时10分钟", icon: AppAssets.moonIcon, durationMinutes: 610)
    ]

    static let diaperRecords = [
        DiaperRecord(time: "10:30", title: "大便-金黄色-糊状", icon: AppAssets.diaperIcon, kind: "大便", color: "金黄色", texture: "糊状"),
        DiaperRecord(time: "08:15", title: "小便", icon: AppAssets.peeDropIcon, kind: "小便"),
        DiaperRecord(time: "06:45", title: "大便-金黄色-软便", icon: AppAssets.diaperIcon, kind: "大便", color: "金黄色", texture: "软便"),
        DiaperRecord(time: "03:20", title: "小便", icon: AppAssets.peeDropIcon, kind: "小便"),
        DiaperRecord(time: "01:10", title: "大便-金黄色-糊状", icon: AppAssets.diaperIcon, kind: "大便", color: "金黄色", texture: "糊状")
    ]

    static let milestones = [
        Milestone(title: "满月", date: "2025年5月27日", icon: AppAssets.bottleIcon),
        Milestone(title: "第一次洗澡", date: "2025年4月28日", icon: AppAssets.cloudBlue),
        Milestone(title: "第一次笑", date: "2025年4月15日", icon: AppAssets.babyAvatar),
        Milestone(title: "第一次出门", date: "2025年4月8日", icon: AppAssets.cameraIcon),
        Milestone(title: "第一次回家", date: "2025年4月8日", icon: AppAssets.homeBottleHero)
    ]

    static let vaccines = [
        VaccineRecord(title: "乙肝第2针", status: "待接种", tintName: "orange", icon: AppAssets.bottleIcon, dueText: "2025.05.18", dueDays: 3, region: "国内"),
        VaccineRecord(title: "五联疫苗第2针", status: "已预约", tintName: "blue", icon: AppAssets.milestoneMedalIcon, dueText: "2025.05.22", dueDays: 7, region: "香港"),
        VaccineRecord(title: "脊灰 IPV", status: "待接种", tintName: "orange", icon: AppAssets.bottleIcon, dueText: "2025.05.30", dueDays: 15, region: "国内"),
        VaccineRecord(title: "乙肝第3针", status: "已完成", tintName: "green", icon: AppAssets.cameraIcon, dueText: "2025.05.01", dueDays: nil, region: "国内")
    ]

    // 相对生日生成日期，避免写死年份后被 currentBabyGrowthRecords 的
    // “出生日～今天”过滤条件淘汰（宝宝生日是相对今天推算的）。
    private static func growthMeasuredAt(daysAfterBirth: Int) -> String {
        let date = Calendar.current.date(byAdding: .day, value: daysAfterBirth, to: babyBirthDate) ?? babyBirthDate
        return BabyRecordStore.dateString(from: date)
    }

    static let growthRecords = [
        GrowthRecord(month: "出生", weight: 3.2, height: 50, head: 34.0, measuredAt: growthMeasuredAt(daysAfterBirth: 0)),
        GrowthRecord(month: "满月", weight: 4.2, height: 54.5, head: 37.0, measuredAt: growthMeasuredAt(daysAfterBirth: 30)),
        GrowthRecord(month: "2月", weight: 5.1, height: 58, head: 38.5, measuredAt: growthMeasuredAt(daysAfterBirth: 60))
    ]
}
