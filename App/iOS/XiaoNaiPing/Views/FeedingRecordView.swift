import SwiftUI

struct FeedingRecordView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: FeedingRecord?
    @State private var deleteCandidate: FeedingRecord?
    @State private var isStatsPresented = false
    @State private var reminderDate = Date().addingTimeInterval(2 * 60 * 60)
    @State private var selectedAutoIntervalMinutes: Int?
    @State private var notificationMessage: String?
    @State private var isReminderExpanded = false

    var body: some View {
        ScreenScaffold(title: "喂养记录", trailingTitle: "统计", showBackButton: true, trailingAction: {
            isStatsPresented = true
        }) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    PrimaryWatercolorButton(title: "记录喂养") {
                        openEditor()
                    }

                    WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.largeCardRadius) {
                        HStack(spacing: AppSpacing.medium) {
                            AssetWatercolorImage(name: AppAssets.bottleIcon, mode: .multiply)
                                .frame(width: 66, height: 86)

                            VStack(spacing: AppSpacing.medium) {
                                HStack(spacing: AppSpacing.small) {
                                    summaryMetric(title: "今日喂养", value: "\(store.feedingCount)次")
                                    summaryMetric(title: "总奶量", value: "\(store.milkAmountML)ml")
                                }

                                HStack(spacing: AppSpacing.small) {
                                    summaryMetric(title: "最近一次", value: store.todayFeedingRecords.first?.time ?? "暂无")
                                    summaryMetric(title: "距上次", value: store.lastFeedingIntervalText)
                                }
                            }
                        }
                    }

                    feedingReminderCard

                    VStack(alignment: .leading, spacing: AppSpacing.regular) {
                        SectionTitleView(title: "喂养历史")
                        if store.todayFeedingRecords.isEmpty {
                            EmptyRecordCard(
                                icon: AppAssets.bottleIcon,
                                title: "今天还没有喂养记录",
                                actionTitle: "记录喂养"
                            ) {
                                openEditor()
                            }
                        } else {
                            ForEach(store.todayFeedingRecords) { record in
                                Button {
                                    openEditor(record)
                                } label: {
                                    RecordRowView(
                                        icon: record.icon,
                                        time: record.time,
                                        title: record.type,
                                        detail: "\(record.detail) · 距上次 \(store.feedingIntervalText(before: record))",
                                        tint: AppColors.cream
                                    )
                                    .frame(maxWidth: .infinity)
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
                            }
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
        .onAppear(perform: syncReminderDate)
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

    private var feedingReminderCard: some View {
        WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            DisclosureGroup(isExpanded: $isReminderExpanded) {
                VStack(alignment: .leading, spacing: AppSpacing.medium) {
                    VStack(alignment: .leading, spacing: AppSpacing.small) {
                        Text("单次手动提醒")
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
                        Text("由你选择固定间隔；不会根据月龄、奶量或历史记录推断。")
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

                    HStack(alignment: .top, spacing: AppSpacing.tiny) {
                        Image(systemName: "applewatch.radiowaves.left.and.right")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(AppColors.coral)
                            .frame(width: 18, height: 18)
                        Text("会提前5分钟提醒准备泡奶；通知未开启时仍会保留提醒意图。")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    if store.nextFeedingReminder != nil {
                        Button("取消当前提醒", role: .destructive) {
                            cancelReminder()
                        }
                        .font(AppTypography.caption)
                    }
                }
            } label: {
                HStack(alignment: .top, spacing: AppSpacing.medium) {
                    Image(systemName: "bell.badge")
                        .font(.system(size: 19, weight: .semibold))
                        .foregroundStyle(AppColors.blueInk)
                        .frame(width: 34, height: 34)
                        .background {
                            Circle().fill(AppColors.milk.opacity(0.72))
                        }

                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("喝奶提醒")
                            .font(AppTypography.cardTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        Text(reminderStatusText)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
        }
    }

    private var reminderStatusText: String {
        if let reminder = store.nextFeedingReminder {
            let source = reminder.origin == .automatic ? "自动" : "手动"
            return "下一次：\(BabyRecordStore.reminderDateTimeString(from: reminder.remindAt)) · \(source)提醒"
        }

        if store.feedingReminderPreference.isAutoReminderEnabled,
           let minutes = store.feedingReminderPreference.intervalMinutes {
            return "自动提醒已开启；保存下一条喂养后，按\(feedingReminderIntervalText(minutes))安排。"
        }
        return "还没有设置下一次喝奶提醒。"
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
        switch store.updateAutomaticFeedingReminder(for: record, skipForThisRecord: skipAutomaticReminder) {
        case .scheduled(let reminder):
            reminderDate = reminder.remindAt
            syncLiveActivity()
            AppNotificationScheduler.scheduleFeedingReminder(reminder) { result in
                notificationMessage = notificationMessage(for: result)
            }
        case .skipped:
            syncLiveActivity()
            notificationMessage = "喂养已保存；本次不会自动提醒。"
        case .preservedManual:
            notificationMessage = "喂养已保存；你手动指定的提醒保持不变。"
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

    private func summaryMetric(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: AppSpacing.tiny) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkGreen)
                .lineLimit(1)

            Text(value)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.coral)
                .lineLimit(1)
                .minimumScaleFactor(0.78)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, AppSpacing.small)
        .padding(.vertical, AppSpacing.small)
        .background {
            RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                .fill(AppColors.milk.opacity(0.46))
        }
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
        onDelete: @escaping () -> Void,
        onSave: @escaping (FeedingRecord, Bool) -> Bool
    ) {
        self.record = record
        self.automaticReminderIntervalMinutes = automaticReminderIntervalMinutes
        self.onDelete = onDelete
        self.onSave = onSave
        _occurredAt = State(initialValue: record?.occurredAt ?? BabyRecordStore.date(fromTimeString: record?.time ?? BabyRecordStore.timeString(from: Date())))
        _type = State(initialValue: record?.type ?? "奶粉")
        _amountText = State(initialValue: record?.amountML.map(String.init) ?? "")
        _durationText = State(initialValue: record?.durationMinutes.map(String.init) ?? "")
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
                                AssetWatercolorImage(name: AppAssets.bottleIcon, mode: .multiply)
                                    .frame(width: 34, height: 40)

                                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                                    Text(record == nil && !showsTimePicker ? "刚刚" : BabyRecordStore.reminderDateTimeString(from: occurredAt))
                                        .font(AppTypography.cardTitle)
                                        .foregroundStyle(AppColors.inkGreen)
                                    Text(record == nil && !showsTimePicker ? "会按现在的时间保存" : "记录时间")
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
                        }
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

                    PrimaryWatercolorButton(title: record == nil ? "刚喂完，记录一下" : "保存修改") {
                        save()
                    }
                    .disabled(isSaving)
                    .opacity(isSaving ? 0.55 : 1)
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
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

    private var optionalDetails: some View {
        WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.cardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                if type == "瓶喂" || type == "奶粉" {
                    TextField("奶量 ml，可不填", text: $amountText)
                        .keyboardType(.numberPad)
                        .textFieldStyle(.roundedBorder)
                }

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

        var saved = record ?? FeedingRecord(
            time: BabyRecordStore.timeString(from: occurredAt),
            type: type,
            detail: "快速记录",
            icon: AppAssets.bottleIcon
        )
        saved.occurredAt = occurredAt
        saved.time = BabyRecordStore.timeString(from: occurredAt)
        saved.type = type
        saved.amountML = amount
        saved.durationMinutes = duration
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

        if let duration {
            return "\(duration)分钟"
        }

        return "快速记录"
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
    let icon: String
    let title: String
    let actionTitle: String
    let action: () -> Void

    var body: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
            VStack(spacing: AppSpacing.medium) {
                AssetWatercolorImage(name: icon, mode: .multiply)
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
