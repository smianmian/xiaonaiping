import XCTest
@testable import XiaoNaiPing

/// 多宝宝：档案数组、活跃切换、按宝宝过滤与旧格式迁移。
@MainActor
final class MultiBabyTests: XCTestCase {
    private var storageURL: URL!

    override func setUp() {
        super.setUp()
        storageURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("multi-baby-tests-\(UUID().uuidString)", isDirectory: true)
        try? FileManager.default.createDirectory(at: storageURL, withIntermediateDirectories: true)
    }

    override func tearDown() {
        try? FileManager.default.removeItem(at: storageURL)
        super.tearDown()
    }

    private func makeStore() -> BabyRecordStore {
        BabyRecordStore(storageDirectoryOverride: storageURL)
    }

    private func waitForPersistence() {
        // 写盘在串行后台队列；用一个新的期望短暂等待落盘完成。
        let expectation = expectation(description: "persistence")
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.3) {
            expectation.fulfill()
        }
        wait(for: [expectation], timeout: 2)
    }

    func testAddBabyKeepsExistingRecordsAndSwitchesActive() {
        let store = makeStore()
        store.createBabyProfile(name: "大宝", birthDate: Date().addingTimeInterval(-86400 * 60), sex: "男宝")
        let firstID = store.baby.id

        XCTAssertTrue(store.upsert(FeedingRecord(
            babyId: firstID,
            time: "08:00",
            type: "奶粉",
            detail: "120ml",
            icon: "icon",
            amountML: 120
        )))
        XCTAssertEqual(store.todayFeedingRecords.count, 1)

        XCTAssertTrue(store.addBaby(name: "二宝", birthDate: Date().addingTimeInterval(-86400 * 60), sex: "女宝"))
        XCTAssertEqual(store.babies.count, 2)
        XCTAssertEqual(store.baby.name, "二宝", "添加后自动切换到新宝宝")
        XCTAssertEqual(store.todayFeedingRecords.count, 0, "二宝看不到大宝的记录")
        XCTAssertEqual(store.feedingRecords.count, 1, "底层数据不丢")

        store.switchActiveBaby(firstID)
        XCTAssertEqual(store.baby.name, "大宝")
        XCTAssertEqual(store.todayFeedingRecords.count, 1, "切回大宝记录仍在")
    }

    func testOngoingSleepIsPerBaby() {
        let store = makeStore()
        store.createBabyProfile(name: "大宝", birthDate: Date().addingTimeInterval(-86400 * 60), sex: "男宝")
        XCTAssertTrue(store.startSleepNow())
        XCTAssertNotNil(store.ongoingSleep)

        XCTAssertTrue(store.addBaby(name: "二宝", birthDate: Date().addingTimeInterval(-86400 * 60), sex: "女宝"))
        XCTAssertNil(store.ongoingSleep, "大宝在睡不挡二宝")
        XCTAssertTrue(store.startSleepNow(), "二宝可以独立开始睡眠")
        XCTAssertNotNil(store.ongoingSleep)
    }

    func testVaccineTemplatePerBaby() {
        let store = makeStore()
        store.createBabyProfile(name: "大宝", birthDate: Date().addingTimeInterval(-86400 * 30), sex: "男宝")
        let firstCount = store.generateVaccineTemplate(region: "中国大陆").count
        XCTAssertGreaterThan(firstCount, 0)
        XCTAssertEqual(store.activeVaccineRecords.count, firstCount)

        XCTAssertTrue(store.addBaby(name: "二宝", birthDate: Date().addingTimeInterval(-86400 * 30), sex: "女宝"))
        XCTAssertEqual(store.activeVaccineRecords.count, 0, "二宝的疫苗本是空的")
        let secondCount = store.generateVaccineTemplate(region: "中国大陆").count
        XCTAssertEqual(secondCount, firstCount, "二宝可以生成同样完整的模板")
        XCTAssertEqual(store.activeVaccineRecords.count, firstCount)
    }

    func testPersistenceRoundTripKeepsBabies() {
        let store = makeStore()
        store.createBabyProfile(name: "大宝", birthDate: Date().addingTimeInterval(-86400 * 60), sex: "男宝")
        XCTAssertTrue(store.addBaby(name: "二宝", birthDate: Date().addingTimeInterval(-86400 * 30), sex: "女宝"))
        let activeID = store.baby.id
        waitForPersistence()

        let reloaded = makeStore()
        XCTAssertEqual(reloaded.babies.count, 2)
        XCTAssertEqual(reloaded.baby.id, activeID, "活跃宝宝跨启动保持")
        XCTAssertEqual(reloaded.babies.map(\.name).sorted(), ["二宝", "大宝"])
    }

    func testDeleteBabyRemovesOnlyItsRecords() {
        let store = makeStore()
        store.createBabyProfile(name: "大宝", birthDate: Date().addingTimeInterval(-86400 * 60), sex: "男宝")
        let firstID = store.baby.id
        XCTAssertTrue(store.upsert(FeedingRecord(
            babyId: firstID, time: "08:00", type: "奶粉", detail: "120ml", icon: "icon", amountML: 120
        )))

        XCTAssertTrue(store.addBaby(name: "二宝", birthDate: Date().addingTimeInterval(-86400 * 30), sex: "女宝"))
        let secondID = store.baby.id
        XCTAssertTrue(store.upsert(FeedingRecord(
            babyId: secondID, time: "09:00", type: "奶粉", detail: "90ml", icon: "icon", amountML: 90
        )))

        XCTAssertFalse(store.deleteBaby(firstID) && store.babies.count > 1 && store.deleteBaby(secondID), "不能删到一个不剩")
        XCTAssertTrue(store.babies.count == 1)
        XCTAssertEqual(store.feedingRecords.count, 1, "只删除被删宝宝的记录")
        XCTAssertEqual(store.feedingRecords.first?.babyId, secondID)
    }
}
