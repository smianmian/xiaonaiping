import XCTest
@testable import XiaoNaiPing

/// 数据安全防回归用例：这些测试对应真实的“全损”故障链，
/// 任何一条失败都意味着用户可能永久丢失育儿记录。
@MainActor
final class BabyRecordStorePersistenceTests: XCTestCase {
    private var tempDirectory: URL!
    private let mockSeededKey = "xnp.debug.mock-data-seeded"
    private let legacyMockBabyID = "11111111-1111-1111-1111-111111111111"

    private var stateURL: URL {
        tempDirectory.appendingPathComponent("xiaonaiping-local-state.json")
    }

    private var backupURL: URL {
        tempDirectory.appendingPathComponent("xiaonaiping-local-state.backup.json")
    }

    override func setUpWithError() throws {
        tempDirectory = FileManager.default.temporaryDirectory
            .appendingPathComponent("xnp-tests-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
        UserDefaults.standard.removeObject(forKey: mockSeededKey)
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: tempDirectory)
        UserDefaults.standard.removeObject(forKey: mockSeededKey)
    }

    private func makeStore() -> BabyRecordStore {
        BabyRecordStore(storageDirectoryOverride: tempDirectory)
    }

    @discardableResult
    private func makeSeededStore(feedingCount: Int = 1) -> BabyRecordStore {
        let store = makeStore()
        store.createBabyProfile(name: "测试宝宝", birthDate: Date(), sex: "男宝")
        for index in 0..<feedingCount {
            _ = store.upsert(
                FeedingRecord(time: "0\(index + 1):30", type: "奶粉", detail: "120ml", icon: "", amountML: 120)
            )
        }
        // 写盘是后台队列异步的，测试断言磁盘状态前必须先等待落盘。
        store.flushPersistence()
        return store
    }

    private func readStateJSON() throws -> [String: Any] {
        let data = try Data(contentsOf: stateURL)
        return try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
    }

    private func writeStateJSON(_ object: [String: Any]) throws {
        let data = try JSONSerialization.data(withJSONObject: object)
        try data.write(to: stateURL, options: [.atomic])
    }

    // MARK: - 损坏文件绝不清库、绝不覆盖

    func testCorruptStateEntersSafeModeAndNeverOverwrites() throws {
        makeSeededStore()
        try Data("not-json-at-all".utf8).write(to: stateURL, options: [.atomic])
        try? FileManager.default.removeItem(at: backupURL)

        let store = makeStore()
        XCTAssertTrue(store.isPersistenceBlocked, "损坏文件必须进入安全模式")
        XCTAssertNotNil(store.loadErrorMessage)

        let bytesBefore = try Data(contentsOf: stateURL)
        let saved = store.upsert(FeedingRecord(time: "09:00", type: "奶粉", detail: "90ml", icon: "", amountML: 90))
        XCTAssertFalse(saved, "安全模式下必须拒绝写入")
        let bytesAfter = try Data(contentsOf: stateURL)
        XCTAssertEqual(bytesBefore, bytesAfter, "损坏的原文件不允许被覆盖")

        let corruptCopies = try FileManager.default
            .contentsOfDirectory(at: tempDirectory, includingPropertiesForKeys: nil)
            .filter { $0.lastPathComponent.contains(".corrupt-") }
        XCTAssertFalse(corruptCopies.isEmpty, "损坏文件必须另存保留以便人工恢复")
    }

    func testBackupIsUsedWhenPrimaryCorrupt() throws {
        makeSeededStore()
        XCTAssertTrue(FileManager.default.fileExists(atPath: backupURL.path), "第二次保存后必须存在备份文件")
        try Data("garbage".utf8).write(to: stateURL, options: [.atomic])

        let store = makeStore()
        XCTAssertFalse(store.isPersistenceBlocked, "备份可用时不应进入安全模式")
        XCTAssertTrue(store.hasCompletedOnboarding)
        XCTAssertEqual(store.baby.name, "测试宝宝")
    }

    func testSaveRotatesDecodableBackup() throws {
        makeSeededStore(feedingCount: 2)
        XCTAssertTrue(FileManager.default.fileExists(atPath: stateURL.path))
        XCTAssertTrue(FileManager.default.fileExists(atPath: backupURL.path))
        let backupData = try Data(contentsOf: backupURL)
        XCTAssertNoThrow(try JSONSerialization.jsonObject(with: backupData), "备份文件必须是可解析的 JSON")
    }

    // MARK: - 单条坏记录只跳过自身

    func testSingleCorruptRecordIsSkippedNotFatal() throws {
        makeSeededStore(feedingCount: 2)

        var json = try readStateJSON()
        var feedings = try XCTUnwrap(json["feedingRecords"] as? [[String: Any]])
        XCTAssertEqual(feedings.count, 2)
        feedings[0]["occurredAt"] = ["corrupted": true]
        json["feedingRecords"] = feedings
        try writeStateJSON(json)

        let store = makeStore()
        XCTAssertFalse(store.isPersistenceBlocked)
        XCTAssertEqual(store.feedingRecords.count, 1, "坏记录跳过，其余记录必须保留")
    }

    func testMissingModelFieldsDecodeWithDefaults() throws {
        makeSeededStore()

        var json = try readStateJSON()
        var baby = try XCTUnwrap(json["baby"] as? [String: Any])
        baby.removeValue(forKey: "birthDate")
        baby.removeValue(forKey: "sex")
        json["baby"] = baby
        json.removeValue(forKey: "milestones")
        try writeStateJSON(json)

        let store = makeStore()
        XCTAssertFalse(store.isPersistenceBlocked)
        XCTAssertEqual(store.baby.name, "测试宝宝")
        XCTAssertEqual(store.baby.sex, "未设置")
        XCTAssertEqual(store.feedingRecords.count, 1)
    }

    // MARK: - legacyMockBabyID 不再是删库开关

    func testLegacyMockBabyIdDoesNotWipeWithoutDebugMarker() throws {
        makeSeededStore()

        var json = try readStateJSON()
        var baby = try XCTUnwrap(json["baby"] as? [String: Any])
        baby["id"] = legacyMockBabyID
        json["baby"] = baby
        try writeStateJSON(json)

        let store = makeStore()
        XCTAssertTrue(store.hasCompletedOnboarding, "仅凭 UUID 命中绝不允许重置档案")
        XCTAssertEqual(store.feedingRecords.count, 1, "仅凭 UUID 命中绝不允许删除记录")
    }

    func testLegacyMockBabyIdCleansUpOnlyWithDebugMarker() throws {
        makeSeededStore()

        var json = try readStateJSON()
        var baby = try XCTUnwrap(json["baby"] as? [String: Any])
        baby["id"] = legacyMockBabyID
        json["baby"] = baby
        try writeStateJSON(json)
        UserDefaults.standard.set(true, forKey: mockSeededKey)

        let store = makeStore()
        XCTAssertFalse(store.hasCompletedOnboarding, "本机注入过 mock 数据时才允许清理遗留 mock 档案")
        XCTAssertTrue(store.feedingRecords.isEmpty)
        XCTAssertFalse(UserDefaults.standard.bool(forKey: mockSeededKey), "清理后应移除标记")
    }

    // MARK: - 跨午夜睡眠裁剪

    func testCrossMidnightSleepClipsToToday() throws {
        let store = makeSeededStore(feedingCount: 0)
        let startOfToday = Calendar.current.startOfDay(for: Date())
        let record = SleepRecord(
            startAt: startOfToday.addingTimeInterval(-3600),
            endAt: startOfToday.addingTimeInterval(3600),
            start: "23:00",
            end: "01:00",
            type: "夜睡",
            duration: "2小时",
            icon: "",
            durationMinutes: 120
        )
        _ = store.upsert(record)
        XCTAssertEqual(store.totalSleepMinutes, 60, "跨午夜睡眠只应计入与今天重叠的部分")
    }
}

/// 纪念日日期修复（P0-4）防回归：真实日期必须可往返，旧显示字符串尽力回填。
@MainActor
final class MilestoneDateTests: XCTestCase {
    func testMilestoneDatePrefersOccurredAt() {
        let realDate = Calendar.current.date(byAdding: .day, value: -40, to: Date())!
        let milestone = Milestone(title: "第一次笑", date: "今天", icon: "x", occurredAt: realDate)
        XCTAssertEqual(BabyRecordStore.milestoneDate(milestone), realDate)
    }

    func testLegacyFullStringBackfills() {
        let milestone = Milestone(title: "满月", date: "2025年5月27日", icon: "x")
        let resolved = BabyRecordStore.milestoneDate(milestone)
        XCTAssertNotNil(resolved)
        let components = Calendar.current.dateComponents([.year, .month, .day], from: resolved!)
        XCTAssertEqual(components.year, 2025)
        XCTAssertEqual(components.month, 5)
        XCTAssertEqual(components.day, 27)
    }

    func testLegacyYearlessStringResolvesToPast() {
        // 旧版“当年格式”无年份：应回填为今年；若在未来则视为去年，绝不能落在未来。
        let milestone = Milestone(title: "百天", date: "12月31日", icon: "x")
        guard let resolved = BabyRecordStore.milestoneDate(milestone) else {
            return XCTFail("无年份日期应能回填")
        }
        XCTAssertLessThanOrEqual(resolved, Date())
    }

    func testFrozenRelativeTextStaysNilButDisplayFallsBack() {
        // “今天”这类冻结文本无法还原真实日期——必须返回 nil，而不是错误地当成今天。
        let milestone = Milestone(title: "第一次抬头", date: "今天", icon: "x")
        XCTAssertNil(BabyRecordStore.milestoneDate(milestone))
    }

    func testFullDisplayStringRoundTrips() {
        let date = Calendar.current.date(from: DateComponents(year: 2026, month: 7, day: 26))!
        let text = BabyRecordStore.fullDisplayDateString(from: date)
        XCTAssertEqual(BabyRecordStore.date(fromDisplayDateString: text).map {
            Calendar.current.startOfDay(for: $0)
        }, Calendar.current.startOfDay(for: date))
    }
}

/// 睡眠口径统一防回归：跨月/跨午夜按重叠裁剪，不双计。
@MainActor
final class SleepClippingTests: XCTestCase {
    func testCrossMonthSleepIsClippedPerMonth() {
        // 6月30日 23:00 → 7月1日 07:00：6月只算 60 分钟，7月只算 420 分钟。
        var june = DateComponents(); june.year = 2026; june.month = 6; june.day = 30; june.hour = 23
        var july = DateComponents(); july.year = 2026; july.month = 7; july.day = 1; july.hour = 7
        let start = Calendar.current.date(from: june)!
        let end = Calendar.current.date(from: july)!
        let record = SleepRecord(
            startAt: start, endAt: end,
            start: "23:00", end: "07:00",
            type: "夜睡", duration: "8小时", icon: "x",
            durationMinutes: 480
        )
        let juneMinutes = BabyRecordStore.sleepMinutes(of: record, inMonthOf: start)
        let julyMinutes = BabyRecordStore.sleepMinutes(of: record, inMonthOf: end)
        XCTAssertEqual(juneMinutes, 60)
        XCTAssertEqual(julyMinutes, 420)
        XCTAssertEqual(juneMinutes + julyMinutes, 480)
    }

    func testStaleOngoingSleepCappedInStats() {
        // 3 天前开始、忘了结束的记录：当天统计按 12 小时封顶，今天不计入。
        let start = Calendar.current.date(byAdding: .day, value: -3, to: Date())!
        let record = SleepRecord(
            startAt: start, endAt: nil,
            start: "21:00", end: "进行中",
            type: "夜睡", duration: "进行中", icon: "x",
            isOngoing: true
        )
        XCTAssertFalse(BabyRecordStore.isSleepRecord(record, on: Date()))
        let startDayMinutes = BabyRecordStore.sleepMinutes(of: record, on: start)
        XCTAssertLessThanOrEqual(startDayMinutes, BabyRecordStore.staleOngoingSleepHours * 60)
    }
}
