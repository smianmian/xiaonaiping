import XCTest
@testable import XiaoNaiPing

/// 数据安全防回归用例：这些测试对应真实的“全损”故障链，
/// 任何一条失败都意味着用户可能永久丢失育儿记录。
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
