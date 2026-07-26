import SwiftUI

struct FeedingRecordView: View {
    var autoPresentEditor = false

    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: FeedingRecord?
    @State private var deleteCandidate: FeedingRecord?
    @State private var isStatsPresented = false
    @State private var reminderDate = Date().addingTimeInterval(2 * 60 * 60)
    @State private var selectedAutoIntervalMinutes: Int?
    @State private var notificationMessage: String?
    @State private var isReminderExpanded = false
    @State private var didAutoPresentEditor = false
    @State private var selectedDay = Date()

    private var isViewingToday: Bool {
        Calendar.current.isDateInToday(selectedDay)
    }

    private var dayFeedingRecords: [FeedingRecord] {
        store.feedingRecords(on: selectedDay)
    }

    private var dayMilkAmountML: Int {
        dayFeedingRecords.compactMap(\.amountML).reduce(0, +)
    }

    var body: some View {
        ScreenScaffold(title: "喂养记录", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    recordFeedingButton

                    DaySwitcherBar(selectedDay: $selectedDay)

                    summaryCard

                    feedingReminderCard

                    VStack(alignment: .leading, spacing: AppSpacing.regular) {
                        SectionTitleView(title: "喂养历史")
                        if dayFeedingRecords.isEmpty {
                            EmptyRecordCard(
                                systemIcon: "bottle.fill",
                                title: isViewingToday ? "今天还没有喂养记录" : "这一天没有喂养记录",
                                actionTitle: isViewingToday ? "记录喂养" : "补记这一天"
                            ) {
                                openEditor()
                            }
                        } else {
                            historyCard
                        }
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            FeedingEditorSheet(
                record: editingRecord,
                automaticReminderIntervalMinutes: store.feedingReminderPreference.isAutoReminderEnabled
                    ? store.feedingReminderPreference.intervalMinutes
                    : nil,
                defaultOccurredAt: defaultEditorDate,
                onDelete: {
                    guard let editingRecord else { return }
                    deleteCandidate = editingRecord
                    isEditorPresented = false
                }
            ) { record, skipAutomaticReminder in
                saveFeedingRecord(record, skipAutomaticReminder: skipAutomaticReminder)
            }
            .presentationDetents([.medium, .large])
        }
        .sheet(isPresented: $isStatsPresented) {
            RecordStatsSheet(
                title: "今日喂养统计",
                rows: [
                    RecordStatsRow(label: "喂养次数", value: "\(store.feedingCount)次"),
                    RecordStatsRow(label: "总奶量", value: "\(store.milkAmountML)ml"),
                    RecordStatsRow(label: "最近一次", value: store.todayFeedingRecords.first?.time ?? "暂无"),
                    RecordStatsRow(label: "距上次", value: store.lastFeedingIntervalText)
                ]
            )
            .presentationDetents([.height(320)])
        }
        .onAppear {
            syncReminderDate()
            if autoPresentEditor && !didAutoPresentEditor {
                didAutoPresentEditor = true
                openEditor()
            }
        }
        .sheet(isPresented: $isReminderExpanded) {
            reminderSettingsSheet
                .presentationDetents([.medium, .large])
        }
        .alert("通知状态", isPresented: notificationAlertBinding) {
            Button("知道了") {
                notificationMessage = nil
            }
        } message: {
            Text(notificationMessage ?? "")
        }
        .alert("删除这条喂养记录？", isPresented: deleteAlertBinding) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteFeedingRecord(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text("删除后，今日首页的喂养次数和奶量会一起更新。")
        }
    }

    /// 「记录喂养」主按钮：珊瑚色实心大胶囊（页面级主操作，比水彩淡底按钮更醒目）。
    private var recordFeedingButton: some View {
        Button {
            openEditor()
        } label: {
            Text(isViewingToday ? "记录喂养" : "补记这一天")
                .font(AppTypography.bodyLarge.weight(.semibold))
                .foregroundStyle(AppColors.milk)
                .frame(maxWidth: .infinity)
                .frame(height: 52)
                .background(AppColors.coral, in: Capsule())
        }
        .buttonStyle(.plain)
    }

    /// 三列汇总卡：当日喂养 / 最近一次 / 距上次，列间细分隔线。
    private var summaryCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius) {
            HStack(spacing: 0) {
                summaryColumn(
                    title: isViewingToday ? "今日喂养" : "当日喂养",
                    value: "\(dayFeedingRecords.count)次 / \(dayMilkAmountML)ml"
                )
                summaryDivider
                summaryColumn(title: "最近一次", value: dayFeedingRecords.first?.time ?? "暂无")
                summaryDivider
                summaryColumn(
                    title: "距上次",
                    value: isViewingToday
                        ? (store.lastFeedingRecord == nil ? "暂无" : store.lastFeedingIntervalText)
                        : "—"
                )
            }
        }
    }

    private func summaryColumn(title: String, value: String) -> some View {
        VStack(spacing: AppSpacing.tiny) {
            Text(title.localizedText)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.ink)
                .lineLimit(1)
            Text(value.localizedText)
                .font(AppTypography.bodyLarge.weight(.semibold))
                .foregroundStyle(AppColors.coral)
                .lineLimit(1)
                .minimumScaleFactor(0.62)
        }
        .frame(maxWidth: .infinity)
    }

    private var summaryDivider: some View {
        Rectangle()
            .fill(AppColors.hairline)
            .frame(width: 1, height: 34)
    }

    /// 喂养历史：单卡分组，一张 milk 卡包全部行，行间细分隔线。
    private var historyCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: 0) {
            VStack(spacing: 0) {
                ForEach(Array(dayFeedingRecords.enumerated()), id: \.element.id) { index, record in
                    Button {
                        openEditor(record)
                    } label: {
                        historyRow(record)
                    }
                    .buttonStyle(.plain)
                    .accessibilityHint("打开编辑")
                    .contextMenu {
                        Button("编辑") {
                            openEditor(record)
                        }
                        Button("删除", role: .destructive) {
                            deleteCandidate = record
                        }
                    }
                    .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                        Button(role: .destructive) {
                            deleteCandidate = record
                        } label: {
                            Label("删除", systemImage: "trash")
                        }
                    }

                    if index < dayFeedingRecords.count - 1 {
                        Divider()
                            .padding(.leading)
                    }
                }
            }
        }
    }

    private func historyRow(_ record: FeedingRecord) -> some View {
        HStack(spacing: AppSpacing.small) {
            Text(record.time)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.inkGreen)
                .frame(width: 60, alignment: .leading)

            AssetWatercolorImage(name: "approvedFeedingBottle")
                .frame(width: 36, height: 36)

            Text(feedingTypeText(for: record))
                .font(AppTypography.body)
                .foregroundStyle(AppColors.ink)
                .lineLimit(1)
                .minimumScaleFactor(0.8)

            Spacer(minLength: AppSpacing.small)

            VStack(alignment: .trailing, spacing: 2) {
                Text(primaryValueText(for: record))
                    .font(AppTypography.bodyLarge.weight(.semibold))
                    .foregroundStyle(AppColors.coral)
                Text(intervalCaption(for: record))
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
            }

            Image(systemName: "chevron.right")
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(AppColors.inkSoft)
        }
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, 12)
        .contentShape(Rectangle())
    }

    /// 母乳且记录了哺乳侧时显示「母乳（右侧）」。
    private func feedingTypeText(for record: FeedingRecord) -> String {
        if record.type == "母乳", let side = record.breastSide, !side.isEmpty {
            return "母乳（\(side)）"
        }
        return record.type
    }

    private func primaryValueText(for record: FeedingRecord) -> String {
        if let amount = record.amountML {
            return "\(amount)ml"
        }
        if let duration = record.durationMinutes {
            return "\(duration)分钟"
        }
        return displayDetail(for: record)
    }

    private func intervalCaption(for record: FeedingRecord) -> String {
        let text = store.feedingIntervalText(before: record)
        return text == "首次记录".localizedText ? text : "距上次 \(text)"
    }

    /// 「下一次提醒」卡：铃铛 + 大号珊瑚色时间；点击仍打开提醒设置 sheet。
    private var feedingReminderCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            Button {
                isReminderExpanded = true
            } label: {
                HStack(spacing: AppSpacing.medium) {
                    Image(systemName: "bell.fill")
                        .font(.system(size: 24, weight: .semibold))
                        .foregroundStyle(AppColors.coral)
                        .frame(width: 48, height: 48)
                        .background {
                            Circle().fill(AppColors.butter.opacity(0.85))
                        }

                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("下一次提醒")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.ink)

                        if let reminder = store.nextFeedingReminder {
                            Text(BabyRecordStore.timeString(from: reminder.remindAt))
                                .font(AppTypography.largeNumber)
                                .foregroundStyle(AppColors.coral)
                        } else {
                            Text("未安排")
                                .font(AppTypography.sectionTitle)
                                .foregroundStyle(AppColors.coral)
                        }

                        if store.feedingReminderPreference.isAutoReminderEnabled,
                           let minutes = store.feedingReminderPreference.intervalMinutes {
                            Text("每\(feedingReminderIntervalText(minutes))提醒")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.inkSoft)
                        }
                    }

                    Spacer(minLength: 0)

                    HStack(spacing: AppSpacing.tiny) {
                        Text("修改")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                        Image(systemName: "chevron.right")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundStyle(AppColors.coral)
                    }
                }
            }
            .buttonStyle(.plain)
            .accessibilityHint("打开提醒设置")
        }
    }

    private var reminderSettingsSheet: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: AppSpacing.large) {
                    VStack(alignment: .leading, spacing: AppSpacing.small) {
                        Text("单次提醒")
                            .font(AppTypography.cardTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        DatePicker("提醒时间", selection: $reminderDate, in: Date()..., displayedComponents: [.date, .hourAndMinute])
                            .font(AppTypography.readableBody)
                            .tint(AppColors.coral)
                        PrimaryWatercolorButton(title: "保存本次提醒", tint: AppColors.cream, foreground: AppColors.blueInk) {
                            saveManualReminder()
                        }
                    }

                    VStack(alignment: .leading, spacing: AppSpacing.small) {
                        Toggle("保存喂养后自动提醒", isOn: automaticReminderEnabledBinding)
                            .font(AppTypography.body)
                            .tint(AppColors.coral)
                        Text("提醒间隔由你选择，不代表医疗建议。")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)

                        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: AppSpacing.small) {
                            ForEach(FeedingReminderIntervalOption.allCases) { option in
                                Button {
                                    selectAutomaticInterval(option.minutes)
                                } label: {
                                    Text(option.title)
                                        .font(AppTypography.caption)
                                        .foregroundStyle(selectedAutoIntervalMinutes == option.minutes ? AppColors.blueInk : AppColors.ink)
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 9)
                                        .background {
                                            Capsule()
                                                .fill(selectedAutoIntervalMinutes == option.minutes ? AppColors.cream : AppColors.milk.opacity(0.56))
                                                .overlay {
                                                    Capsule().stroke(AppColors.softStroke.opacity(0.28), lineWidth: 1)
                                                }
                                        }
                                }
                                .buttonStyle(.plain)
                            }
                        }

                        if store.feedingReminderPreference.isAutoReminderEnabled {
                            Button("暂停自动提醒") {
                                pauseAutomaticReminder()
                            }
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                        }
                    }

                    if store.nextFeedingReminder != nil {
                        Button("取消当前提醒", role: .destructive) {
                            cancelReminder()
                        }
                        .font(AppTypography.caption)
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle("提醒设置")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("完成") { isReminderExpanded = false }
                }
            }
        }
    }

    private var notificationAlertBinding: Binding<Bool> {
        Binding {
            notificationMessage != nil
        } set: { isPresented in
            if !isPresented {
                notificationMessage = nil
            }
        }
    }

    private var deleteAlertBinding: Binding<Bool> {
        Binding {
            deleteCandidate != nil
        } set: { isPresented in
            if !isPresented {
                deleteCandidate = nil
            }
        }
    }

    private func openEditor(_ record: FeedingRecord? = nil) {
        editingRecord = record
        isEditorPresented = true
    }

    /// 补记历史日期时，编辑器默认落在所选日期的中午，避免存成“今天”。
    private var defaultEditorDate: Date? {
        guard !isViewingToday else { return nil }
        return Calendar.current.date(bySettingHour: 12, minute: 0, second: 0, of: selectedDay)
    }

    private func displayDetail(for record: FeedingRecord) -> String {
        record.detail == "快速记录" ? "已记录" : record.detail
    }

    private var automaticReminderEnabledBinding: Binding<Bool> {
        Binding {
            store.feedingReminderPreference.isAutoReminderEnabled
        } set: { isEnabled in
            setAutomaticReminderEnabled(isEnabled)
        }
    }

    private func saveFeedingRecord(_ record: FeedingRecord, skipAutomaticReminder: Bool) -> Bool {
        notificationMessage = nil
        guard store.upsert(record) else { return false }
        // 成功路径保持安静：半夜每记一次奶都弹全屏 Alert 是负担。
        // 只有需要用户处理的情况（权限被拒、安排失败）才提示。
        switch store.updateAutomaticFeedingReminder(for: record, skipForThisRecord: skipAutomaticReminder) {
        case .scheduled(let reminder):
            reminderDate = reminder.remindAt
            syncLiveActivity()
            AppNotificationScheduler.scheduleFeedingReminder(
                reminder,
                repeatIntervalMinutes: store.feedingReminderPreference.intervalMinutes
            ) { result in
                if let message = failureMessage(for: result) {
                    notificationMessage = message
                }
            }
        case .skipped, .preservedManual:
            syncLiveActivity()
        case .disabled:
            break
        case .failed:
            notificationMessage = "喂养已保存；自动提醒更新失败，请稍后再试。"
        }
        return true
    }

    private func saveManualReminder() {
        notificationMessage = nil
        guard reminderDate > Date() else {
            notificationMessage = "提醒时间要晚于现在。"
            return
        }

        let reminder = FeedingReminder(
            babyId: store.baby.id,
            remindAt: reminderDate,
            origin: .manual
        )
        guard store.upsert(reminder) else {
            notificationMessage = "保存失败，请稍后再试。"
            return
        }

        syncLiveActivity()
        AppNotificationScheduler.scheduleFeedingReminder(reminder) { result in
            notificationMessage = notificationMessage(for: result)
        }
    }

    private func cancelReminder() {
        notificationMessage = nil
        guard store.cancelFeedingReminder() else {
            notificationMessage = "保存失败，请稍后再试。"
            return
        }

        AppNotificationScheduler.removeFeedingReminder()
        endLiveActivity()
        reminderDate = defaultReminderDate
        notificationMessage = "喝奶闹钟已取消。"
    }

    private func syncReminderDate() {
        let reminder = store.nextFeedingReminder
        reminderDate = reminder?.remindAt ?? defaultReminderDate
        selectedAutoIntervalMinutes = store.feedingReminderPreference.intervalMinutes
    }

    private func selectAutomaticInterval(_ minutes: Int) {
        selectedAutoIntervalMinutes = minutes
        guard store.feedingReminderPreference.isAutoReminderEnabled else { return }
        guard store.setAutomaticFeedingReminderEnabled(true, intervalMinutes: minutes) else {
            notificationMessage = "自动提醒设置未保存，请稍后再试。"
            return
        }
        notificationMessage = "自动提醒已改为每\(feedingReminderIntervalText(minutes))；保存下一条喂养后生效。"
    }

    private func setAutomaticReminderEnabled(_ isEnabled: Bool) {
        notificationMessage = nil
        guard !isEnabled || selectedAutoIntervalMinutes != nil else {
            notificationMessage = "请先选择 2 到 4 小时的提醒间隔。"
            return
        }

        let hadAutomaticReminder = store.feedingReminder?.origin == .automatic
        guard store.setAutomaticFeedingReminderEnabled(isEnabled, intervalMinutes: selectedAutoIntervalMinutes) else {
            notificationMessage = "自动提醒设置未保存，请稍后再试。"
            return
        }

        if !isEnabled, hadAutomaticReminder {
            AppNotificationScheduler.removeFeedingReminder()
            endLiveActivity()
        }
        notificationMessage = isEnabled
            ? "自动提醒已开启；保存下一条喂养后开始安排。"
            : "自动提醒已暂停。"
    }

    private func pauseAutomaticReminder() {
        setAutomaticReminderEnabled(false)
    }

    private var defaultReminderDate: Date {
        Date().addingTimeInterval(2 * 60 * 60)
    }

    private func notificationMessage(for result: NotificationScheduleResult) -> String {
        switch result {
        case .scheduled:
            return "喝奶闹钟已加入 iOS 系统通知，会提前5分钟提醒准备泡奶。"
        case .removed:
            return "提醒时间无效，未安排通知。"
        case .denied:
            return "通知权限未开启。喝奶时间已保留在喂养页，不会弹出系统提醒。"
        case .failed:
            return "通知安排失败。喝奶时间已保留在喂养页。"
        }
    }

    /// 只在需要用户处理时返回提示；成功与常规情况返回 nil 保持安静。
    private func failureMessage(for result: NotificationScheduleResult) -> String? {
        switch result {
        case .scheduled:
            return nil
        case .removed:
            return "提醒时间无效，未安排通知。"
        case .denied:
            return "通知权限未开启。喝奶时间已保留在喂养页，不会弹出系统提醒。"
        case .failed:
            return "通知安排失败。喝奶时间已保留在喂养页。"
        }
    }

    private func syncLiveActivity() {
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

    private func endLiveActivity() {
        #if canImport(ActivityKit)
        if #available(iOS 16.2, *) {
            FeedingReminderLiveActivityController.endAll()
        }
        #endif
    }

}

private func feedingReminderIntervalText(_ minutes: Int) -> String {
    let hours = minutes / 60
    let remainingMinutes = minutes % 60
    if remainingMinutes == 0 {
        return "\(hours)小时"
    }
    if hours == 0 {
        return "\(remainingMinutes)分钟"
    }
    return "\(hours)小时\(remainingMinutes)分"
}

private struct FeedingReminderIntervalOption: Identifiable, CaseIterable {
    let id: String
    let title: String
    let minutes: Int

    static let allCases = [
        FeedingReminderIntervalOption(id: "120", title: "2小时", minutes: 120),
        FeedingReminderIntervalOption(id: "150", title: "2.5小时", minutes: 150),
        FeedingReminderIntervalOption(id: "180", title: "3小时", minutes: 180),
        FeedingReminderIntervalOption(id: "210", title: "3.5小时", minutes: 210),
        FeedingReminderIntervalOption(id: "240", title: "4小时", minutes: 240)
    ]
}

private struct FeedingEditorSheet: View {
    let record: FeedingRecord?
    let automaticReminderIntervalMinutes: Int?
    let onDelete: () -> Void
    let onSave: (FeedingRecord, Bool) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var occurredAt: Date
    @State private var type: String
    @State private var amountText: String
    @State private var durationText: String
    @State private var breastSide: String?
    @State private var note: String
    @State private var skipsAutomaticReminder = false
    @State private var errorMessage: String?
    @State private var showsTimePicker = false
    @State private var showsMoreDetails = false
    @State private var isSaving = false

    private let types = ["奶粉", "母乳", "瓶喂", "辅食"]
    init(
        record: FeedingRecord?,
        automaticReminderIntervalMinutes: Int?,
        defaultOccurredAt: Date? = nil,
        onDelete: @escaping () -> Void,
        onSave: @escaping (FeedingRecord, Bool) -> Bool
    ) {
        self.record = record
        self.automaticReminderIntervalMinutes = automaticReminderIntervalMinutes
        self.onDelete = onDelete
        self.onSave = onSave
        _occurredAt = State(initialValue: record?.occurredAt
            ?? defaultOccurredAt
            ?? BabyRecordStore.date(fromTimeString: record?.time ?? BabyRecordStore.timeString(from: Date())))
        _type = State(initialValue: record?.type ?? "奶粉")
        _amountText = State(initialValue: record?.amountML.map(String.init) ?? "")
        _durationText = State(initialValue: record?.durationMinutes.map(String.init) ?? "")
        _breastSide = State(initialValue: record?.breastSide)
        _note = State(initialValue: record?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            Text("这一次")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.inkSoft)

                            Picker("类型", selection: $type) {
                                ForEach(types, id: \.self) { type in
                                    Text(type).tag(type)
                                }
                            }
                            .pickerStyle(.segmented)
                            .tint(AppColors.peach)

                            HStack {
                                AssetWatercolorImage(name: "approvedFeedingBottle")
                                    .frame(width: 34, height: 40)

                                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                                    Text(BabyRecordStore.reminderDateTimeString(from: occurredAt))
                                        .font(AppTypography.cardTitle)
                                        .foregroundStyle(AppColors.inkGreen)
                                    Text("记录时间")
                                        .font(AppTypography.caption)
                                        .foregroundStyle(AppColors.inkSoft)
                                }

                                Spacer(minLength: 0)

                                Button(showsTimePicker ? "收起" : "修改时间") {
                                    withAnimation {
                                        showsTimePicker.toggle()
                                    }
                                }
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.blueInk)
                            }

                            if showsTimePicker {
                                DatePicker("时间", selection: $occurredAt, displayedComponents: [.date, .hourAndMinute])
                                    .font(AppTypography.readableBody)
                                    .tint(AppColors.coral)
                            }

                            HStack(spacing: AppSpacing.small) {
                                ForEach([("现在", 0), ("-5分钟", -5), ("-10分钟", -10), ("-30分钟", -30)], id: \.1) { item in
                                    Button(item.0) {
                                        occurredAt = Date().addingTimeInterval(TimeInterval(item.1 * 60))
                                    }
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.blueInk)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 7)
                                    .background(AppColors.milk, in: Capsule())
                                }
                            }
                        }
                    }

                    if type == "瓶喂" || type == "奶粉" {
                        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius) {
                            VStack(alignment: .leading, spacing: AppSpacing.small) {
                                TextField("奶量 ml（必填）", text: $amountText)
                                    .keyboardType(.numberPad)
                                    .textFieldStyle(.roundedBorder)
                                HStack(spacing: AppSpacing.small) {
                                    ForEach([60, 90, 120, 150, 180], id: \.self) { preset in
                                        Button("\(preset)") {
                                            amountText = "\(preset)"
                                        }
                                        .font(AppTypography.caption)
                                        .foregroundStyle(amountText == "\(preset)" ? AppColors.milk : AppColors.blueInk)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 7)
                                        .background(
                                            amountText == "\(preset)" ? AppColors.blueInk : AppColors.cream,
                                            in: Capsule()
                                        )
                                    }
                                }
                            }
                        }
                    }

                    if type == "母乳" {
                        breastSideCard
                    }

                    WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius, padding: 0) {
                        Button {
                            withAnimation {
                                showsMoreDetails.toggle()
                            }
                        } label: {
                            HStack(spacing: AppSpacing.small) {
                                Image(systemName: showsMoreDetails ? "chevron.up" : "chevron.down")
                                Text("更多详情（可不填）")
                                Spacer(minLength: 0)
                                Text(showsMoreDetails ? "收起" : "按需填写")
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.inkSoft)
                            }
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkGreen)
                            .padding(.horizontal, AppSpacing.medium)
                            .padding(.vertical, AppSpacing.regular)
                        }
                        .buttonStyle(.plain)
                    }

                    if showsMoreDetails {
                        optionalDetails
                    }

                    if let automaticReminderIntervalMinutes {
                        automaticReminderChoice(intervalMinutes: automaticReminderIntervalMinutes)
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    if !canSave && (type == "奶粉" || type == "瓶喂") {
                        Text("奶量必须填写大于 0 的数字")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .safeAreaInset(edge: .bottom, spacing: 0) {
                PrimaryWatercolorButton(title: record == nil ? "保存喂养记录" : "保存修改") {
                    save()
                }
                .disabled(isSaving || !canSave)
                .opacity(isSaving || !canSave ? 0.55 : 1)
                .padding(.horizontal, AppSpacing.large)
                .padding(.vertical, AppSpacing.small)
                .background(.ultraThinMaterial)
            }
            .navigationTitle(record == nil ? "记录喂养" : "编辑喂养")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                }
                if record != nil {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button("删除", role: .destructive) {
                            onDelete()
                            dismiss()
                        }
                    }
                }
            }
        }
    }

    /// 哺乳侧选择：左侧 / 右侧 / 不记录。「不记录」存 nil，保持旧数据与云端包兼容。
    private var breastSideCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Text("哺乳侧")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                HStack(spacing: AppSpacing.small) {
                    ForEach(["左侧", "右侧", "不记录"], id: \.self) { option in
                        let isSelected = (breastSide ?? "不记录") == option
                        Button(option) {
                            breastSide = option == "不记录" ? nil : option
                        }
                        .font(AppTypography.caption)
                        .foregroundStyle(isSelected ? AppColors.milk : AppColors.blueInk)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 7)
                        .background(
                            isSelected ? AppColors.blueInk : AppColors.cream,
                            in: Capsule()
                        )
                    }
                }
            }
        }
    }

    private var optionalDetails: some View {
        WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.cardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                if type == "母乳" {
                    TextField("时长 分钟，可不填", text: $durationText)
                        .keyboardType(.numberPad)
                        .textFieldStyle(.roundedBorder)
                }

                TextField("备注，可不填", text: $note, axis: .vertical)
                    .lineLimit(2...4)
                    .textFieldStyle(.roundedBorder)
            }
        }
    }

    private func automaticReminderChoice(intervalMinutes: Int) -> some View {
        WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Text("本次喂养后的提醒")
                    .font(AppTypography.cardTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text("默认会在结束时间后 \(feedingReminderIntervalText(intervalMinutes)) 安排下一次提醒。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                Toggle("本次不提醒", isOn: $skipsAutomaticReminder)
                    .font(AppTypography.body)
                    .tint(AppColors.coral)
            }
        }
    }

    private func save() {
        guard !isSaving else { return }
        errorMessage = nil
        guard let amount = validatedNumber(amountText, fieldName: "奶量") else { return }
        guard let duration = validatedNumber(durationText, fieldName: "时长") else { return }

        if (type == "奶粉" || type == "瓶喂") && amount == nil {
            errorMessage = "奶量必须填写大于 0 的数字。"
            return
        }

        var saved = record ?? FeedingRecord(
            time: BabyRecordStore.timeString(from: occurredAt),
            type: type,
            detail: type,
            icon: AppAssets.bottleIcon
        )
        saved.occurredAt = occurredAt
        saved.time = BabyRecordStore.timeString(from: occurredAt)
        saved.type = type
        saved.amountML = amount
        saved.durationMinutes = duration
        saved.breastSide = type == "母乳" ? breastSide : nil
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        saved.detail = detailText(amount: amount, duration: duration)
        isSaving = true
        if onSave(saved, skipsAutomaticReminder) {
            dismiss()
        } else {
            isSaving = false
            errorMessage = "保存失败，请稍后再试。输入已保留。"
        }
    }

    private var canSave: Bool {
        guard type == "奶粉" || type == "瓶喂" else { return true }
        guard let amount = Int(amountText.trimmingCharacters(in: .whitespacesAndNewlines)) else { return false }
        return amount > 0
    }

    private func validatedNumber(_ value: String, fieldName: String) -> Int?? {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return .some(nil)
        }

        guard let number = Int(trimmed), number > 0 else {
            errorMessage = "\(fieldName)请填写大于 0 的数字，或留空。"
            return nil
        }

        return .some(number)
    }

    private func detailText(amount: Int?, duration: Int?) -> String {
        if let amount {
            return "\(amount)ml"
        }

        // 母乳的 detail 与 MockData 既有文案格式一致："右侧15分钟" / "右侧" / "15分钟"。
        let sideText = type == "母乳" ? (breastSide ?? "") : ""

        if let duration {
            return "\(sideText)\(duration)分钟"
        }

        if !sideText.isEmpty {
            return sideText
        }

        return type
    }
}

struct RecordStatsRow: Identifiable {
    let id = UUID()
    let label: String
    let value: String
}

struct RecordStatsSheet: View {
    let title: String
    let rows: [RecordStatsRow]

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: AppSpacing.regular) {
                ForEach(rows) { row in
                    HStack {
                        Text(row.label)
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkGreen)
                        Spacer()
                        Text(row.value)
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.coral)
                    }
                    .padding(.horizontal, AppSpacing.medium)
                    .padding(.vertical, AppSpacing.small)
                    .background {
                        RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                            .fill(AppColors.milk.opacity(0.56))
                    }
                }
                Spacer(minLength: 0)
            }
            .padding(AppSpacing.large)
            .background(PaperBackgroundView())
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("完成") {
                        dismiss()
                    }
                }
            }
        }
    }
}

private struct EmptyRecordCard: View {
    let systemIcon: String
    let title: String
    let actionTitle: String
    let action: () -> Void

    var body: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
            VStack(spacing: AppSpacing.medium) {
                Image(systemName: systemIcon)
                    .font(.system(size: 38, weight: .semibold))
                    .foregroundStyle(AppColors.coral)
                    .frame(width: 54, height: 54)
                Text(title)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                PrimaryWatercolorButton(title: actionTitle, action: action)
            }
            .frame(maxWidth: .infinity)
        }
    }
}
