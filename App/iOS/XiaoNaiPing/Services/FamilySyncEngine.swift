import Foundation

/// 家人共享同步引擎：与整包 blob 备份并存的第二条通道。
/// blob 备份是单账号灾备；这里按记录逐条推拉（LWW），
/// 让妈妈/爸爸/家人各自登录自己的账号也能看到同一份记录。
@MainActor
final class FamilySyncEngine: ObservableObject {
    @Published private(set) var familyInfo: FamilyInfo?
    @Published private(set) var isSyncing = false
    @Published private(set) var statusText: String?
    @Published var errorMessage: String?

    private let sessionStore: CloudAccountSessionStore
    private var scheduledSyncTask: Task<Void, Never>?

    init(sessionStore: CloudAccountSessionStore = CloudAccountSessionStore()) {
        self.sessionStore = sessionStore
    }

    var isAvailable: Bool {
        CloudSyncConfiguration.apiBaseURL != nil && sessionStore.session != nil
    }

    var isInFamily: Bool {
        familyInfo != nil
    }

    // MARK: 家庭生命周期

    func refreshMembership() async {
        guard let token = sessionStore.session?.sessionToken,
              let client = makeClient() else { return }
        familyInfo = (try? await client.fetchFamily(token: token)) ?? familyInfo
    }

    func createFamily() async {
        guard let token = sessionStore.session?.sessionToken,
              let client = makeClient() else { return }
        errorMessage = nil
        do {
            familyInfo = try await client.createFamily(token: token)
            statusText = "家庭已创建，把邀请码发给家人即可加入。"
        } catch {
            errorMessage = "创建家庭失败，请稍后再试。"
        }
    }

    func joinFamily(inviteCode: String, store: BabyRecordStore) async {
        guard let token = sessionStore.session?.sessionToken,
              let client = makeClient() else { return }
        errorMessage = nil
        do {
            familyInfo = try await client.joinFamily(inviteCode: inviteCode, token: token)
            statusText = "已加入家庭，正在同步记录…"
            // 新成员从 0 拉全量。
            resetCursor()
            await syncNow(store: store)
        } catch {
            errorMessage = "加入失败：请确认邀请码正确，且家庭未满员。"
        }
    }

    // MARK: 同步

    /// 保存后 2 秒合并触发一次；不在家庭里则完全静默。
    func scheduleAutomaticSync(store: BabyRecordStore) {
        guard isInFamily else { return }
        scheduledSyncTask?.cancel()
        scheduledSyncTask = Task { [weak self, weak store] in
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            guard !Task.isCancelled, let self, let store else { return }
            await self.syncNow(store: store)
        }
    }

    func syncNow(store: BabyRecordStore) async {
        guard !isSyncing, isInFamily,
              let token = sessionStore.session?.sessionToken,
              let client = makeClient() else { return }
        isSyncing = true
        defer { isSyncing = false }

        let syncStart = Date()
        do {
            // 1) 推送本地水位线之后的变更（含墓碑）。
            let watermark = lastSyncedAt
            let dirty = store.familyDirtyEnvelopes(since: watermark)
            if !dirty.isEmpty {
                for batch in stride(from: 0, to: dirty.count, by: 200).map({ Array(dirty[$0..<min($0 + 200, dirty.count)]) }) {
                    _ = try await client.pushFamilyRecords(batch, token: token)
                }
            }

            // 2) 从游标增量拉取并合并（hasMore 分页循环）。
            var cursor = pullCursor
            var applied = 0
            while true {
                let page = try await client.pullFamilyRecords(since: cursor, token: token)
                applied += store.applyFamilyChanges(page.records.filter { $0.mine != true })
                cursor = page.cursor
                if !page.hasMore { break }
            }

            pullCursor = cursor
            lastSyncedAt = syncStart
            statusText = applied > 0
                ? "已同步：合并了 \(applied) 条家人更新。"
                : "已同步。"
            errorMessage = nil
        } catch {
            statusText = "同步未完成，会在下次打开或保存后重试。"
        }
    }

    // MARK: 游标与水位线

    private var cursorKey: String {
        "xnp.family.pull-cursor.\(familyInfo?.familyId ?? "none")"
    }

    private var watermarkKey: String {
        "xnp.family.push-watermark.\(familyInfo?.familyId ?? "none")"
    }

    private var pullCursor: Int {
        get { UserDefaults.standard.integer(forKey: cursorKey) }
        set { UserDefaults.standard.set(newValue, forKey: cursorKey) }
    }

    /// 推送水位线：这个时间之前的本地变更都已推送过。
    private var lastSyncedAt: Date {
        get {
            let interval = UserDefaults.standard.double(forKey: watermarkKey)
            return interval > 0 ? Date(timeIntervalSince1970: interval) : .distantPast
        }
        set { UserDefaults.standard.set(newValue.timeIntervalSince1970, forKey: watermarkKey) }
    }

    private func resetCursor() {
        UserDefaults.standard.removeObject(forKey: cursorKey)
        UserDefaults.standard.removeObject(forKey: watermarkKey)
    }

    private func makeClient() -> CloudSyncAPIClient? {
        guard let baseURL = CloudSyncConfiguration.apiBaseURL else { return nil }
        return CloudSyncAPIClient(baseURL: baseURL)
    }
}
