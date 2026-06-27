import SwiftUI

struct FeedingRecordView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: FeedingRecord?
    @State private var deleteCandidate: FeedingRecord?
    @State private var isStatsPresented = false
    @State private var reminderDate = Date().addingTimeInterval(2 * 60 * 60)
    @State private var repeatIntervalMinutes: Int?
    @State private var notificationMessage: String?

    var body: some View {
        ScreenScaffold(title: "喂养记录", trailingTitle: "统计", showBackButton: true, trailingAction: {
            isStatsPresented = true
        }) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
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

                    VStack(spacing: AppSpacing.regular) {
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
                                HStack(spacing: AppSpacing.small) {
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

                                    Button {
                                        deleteCandidate = record
                                    } label: {
                                        Image(systemName: "trash")
                                            .font(.system(size: 18, weight: .regular))
                                            .foregroundStyle(AppColors.coral)
                                            .frame(width: 44, height: 44)
                                            .background {
                                                Circle().fill(AppColors.blush.opacity(0.56))
                                            }
                                    }
                                    .buttonStyle(.plain)
                                    .accessibilityLabel("删除喂养记录")
                                }
                            }
                        }
                    }

                    if !store.todayFeedingRecords.isEmpty {
                        PrimaryWatercolorButton(title: "+ 记录喂养") {
                            openEditor()
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
                reminderRepeatIntervalMinutes: store.nextFeedingReminder?.repeatIntervalMinutes
            ) { record, reminderDeferralMinutes in
                saveFeedingRecord(record, reminderDeferralMinutes: reminderDeferralMinutes)
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
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                HStack(alignment: .top, spacing: AppSpacing.medium) {
                    Image(systemName: "bell.badge")
                        .font(.system(size: 19, weight: .semibold))
                        .foregroundStyle(AppColors.blueInk)
                        .frame(width: 34, height: 34)
                        .background {
                            Circle().fill(AppColors.milk.opacity(0.72))
                        }

                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("喝奶闹钟")
                            .font(AppTypography.cardTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        Text(reminderStatusText)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    Spacer(minLength: 0)
                }

                DatePicker("提醒时间", selection: $reminderDate, in: Date()..., displayedComponents: [.date, .hourAndMinute])
                    .font(AppTypography.readableBody)
                    .tint(AppColors.coral)

                HStack(alignment: .top, spacing: AppSpacing.tiny) {
                    Image(systemName: "applewatch.radiowaves.left.and.right")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(AppColors.coral)
                        .frame(width: 18, height: 18)
                    Text("会提前5分钟提醒准备泡奶，Apple Watch 可跟随系统通知震动。")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                        .fixedSize(horizontal: false, vertical: true)
                }

                VStack(alignment: .leading, spacing: AppSpacing.small) {
                    Text("之后继续提醒")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkGreen)
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: AppSpacing.small) {
                        ForEach(FeedingReminderRepeatOption.allCases) { option in
                            Button {
                                repeatIntervalMinutes = option.minutes
                            } label: {
                                Text(option.title)
                                    .font(AppTypography.caption)
                                    .foregroundStyle(repeatIntervalMinutes == option.minutes ? AppColors.blueInk : AppColors.ink)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 9)
                                    .background {
                                        Capsule()
                                            .fill(repeatIntervalMinutes == option.minutes ? AppColors.cream : AppColors.milk.opacity(0.56))
                                            .overlay {
                                                Capsule().stroke(AppColors.softStroke.opacity(0.28), lineWidth: 1)
                                            }
                                    }
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                HStack(spacing: AppSpacing.small) {
                    PrimaryWatercolorButton(title: "保存闹钟", tint: AppColors.cream, foreground: AppColors.blueInk) {
                        saveReminder()
                    }

                    if store.nextFeedingReminder != nil {
                        Button {
                            cancelReminder()
                        } label: {
                            Text("取消闹钟")
                                .font(AppTypography.bodyLarge)
                                .foregroundStyle(AppColors.coral)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 13)
                                .background {
                                    Capsule()
                                        .fill(AppColors.blush.opacity(0.62))
                                        .overlay {
                                            Capsule().stroke(AppColors.coral.opacity(0.22), lineWidth: 1)
                                        }
                                }
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }

    private var reminderStatusText: String {
        guard let reminder = store.nextFeedingReminder else {
            return "还没有设置下一次喝奶提醒。"
        }

        if let repeatIntervalText = reminder.repeatIntervalText {
            return "下一次：\(BabyRecordStore.reminderDateTimeString(from: reminder.remindAt)) · 之后每\(repeatIntervalText)"
        }

        return "下一次：\(BabyRecordStore.reminderDateTimeString(from: reminder.remindAt)) · 只提醒一次"
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

    private func saveFeedingRecord(_ record: FeedingRecord, reminderDeferralMinutes: Int?) -> Bool {
        notificationMessage = nil
        guard store.upsert(record) else { return false }
        guard let reminderDeferralMinutes,
              let currentReminder = store.feedingReminder,
              let repeatIntervalMinutes = currentReminder.repeatIntervalMinutes,
              repeatIntervalMinutes > 0 else {
            return true
        }

        let nextRemindAt = feedingReminderDate(
            occurredAt: record.occurredAt,
            durationMinutes: record.durationMinutes,
            repeatIntervalMinutes: repeatIntervalMinutes,
            deferralMinutes: reminderDeferralMinutes
        )
        guard nextRemindAt > Date() else {
            notificationMessage = "喂养已保存；顺延后的提醒时间已早于现在，闹钟未调整。"
            return true
        }

        let reminder = FeedingReminder(
            id: currentReminder.id,
            babyId: store.baby.id,
            remindAt: nextRemindAt,
            repeatIntervalMinutes: repeatIntervalMinutes,
            title: currentReminder.title,
            note: currentReminder.note,
            createdAt: currentReminder.createdAt
        )
        guard store.upsert(reminder) else {
            notificationMessage = "喂养已保存；喝奶闹钟更新失败，请稍后再试。"
            return true
        }

        reminderDate = nextRemindAt
        self.repeatIntervalMinutes = repeatIntervalMinutes
        syncLiveActivity()
        AppNotificationScheduler.scheduleFeedingReminder(reminder) { result in
            notificationMessage = notificationMessage(for: result)
        }
        return true
    }

    private func saveReminder() {
        notificationMessage = nil
        guard reminderDate > Date() else {
            notificationMessage = "提醒时间要晚于现在。"
            return
        }

        let reminder = FeedingReminder(
            babyId: store.baby.id,
            remindAt: reminderDate,
            repeatIntervalMinutes: repeatIntervalMinutes
        )
        guard store.upsert(reminder) else {
            notificationMessage = "本地保存失败，请稍后再试。"
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
            notificationMessage = "本地保存失败，请稍后再试。"
            return
        }

        AppNotificationScheduler.removeFeedingReminder()
        endLiveActivity()
        reminderDate = defaultReminderDate
        repeatIntervalMinutes = nil
        notificationMessage = "喝奶闹钟已取消。"
    }

    private func syncReminderDate() {
        let reminder = store.nextFeedingReminder
        reminderDate = reminder?.remindAt ?? defaultReminderDate
        repeatIntervalMinutes = reminder?.repeatIntervalMinutes
    }

    private var defaultReminderDate: Date {
        Date().addingTimeInterval(2 * 60 * 60)
    }

    private func notificationMessage(for result: NotificationScheduleResult) -> String {
        switch result {
        case .scheduled:
            return "喝奶闹钟已加入 iOS 本地通知，会提前5分钟提醒准备泡奶。"
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

private func feedingReminderDate(
    occurredAt: Date,
    durationMinutes: Int?,
    repeatIntervalMinutes: Int,
    deferralMinutes: Int
) -> Date {
    let baseDate: Date
    if let durationMinutes, durationMinutes > 0,
       let finishedAt = Calendar.current.date(byAdding: .minute, value: durationMinutes, to: occurredAt) {
        baseDate = finishedAt
    } else {
        baseDate = occurredAt
    }

    return Calendar.current.date(
        byAdding: .minute,
        value: repeatIntervalMinutes + deferralMinutes,
        to: baseDate
    ) ?? baseDate.addingTimeInterval(TimeInterval((repeatIntervalMinutes + deferralMinutes) * 60))
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

private struct FeedingReminderRepeatOption: Identifiable, CaseIterable {
    let id: String
    let title: String
    let minutes: Int?

    static let allCases = [
        FeedingReminderRepeatOption(id: "once", title: "只一次", minutes: nil),
        FeedingReminderRepeatOption(id: "120", title: "2小时", minutes: 120),
        FeedingReminderRepeatOption(id: "150", title: "2.5小时", minutes: 150),
        FeedingReminderRepeatOption(id: "180", title: "3小时", minutes: 180),
        FeedingReminderRepeatOption(id: "210", title: "3.5小时", minutes: 210),
        FeedingReminderRepeatOption(id: "240", title: "4小时", minutes: 240)
    ]
}

private struct FeedingEditorSheet: View {
    let record: FeedingRecord?
    let reminderRepeatIntervalMinutes: Int?
    let onSave: (FeedingRecord, Int?) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var occurredAt: Date
    @State private var type: String
    @State private var amountText: String
    @State private var durationText: String
    @State private var note: String
    @State private var reminderDeferralMinutes: Int
    @State private var errorMessage: String?

    private let types = ["母乳", "瓶喂", "奶粉", "辅食"]
    private let reminderDeferralOptions = Array(stride(from: 0, through: 30, by: 5))

    init(
        record: FeedingRecord?,
        reminderRepeatIntervalMinutes: Int?,
        onSave: @escaping (FeedingRecord, Int?) -> Bool
    ) {
        self.record = record
        self.reminderRepeatIntervalMinutes = reminderRepeatIntervalMinutes
        self.onSave = onSave
        _occurredAt = State(initialValue: record?.occurredAt ?? BabyRecordStore.date(fromTimeString: record?.time ?? BabyRecordStore.timeString(from: Date())))
        _type = State(initialValue: record?.type ?? "母乳")
        _amountText = State(initialValue: record?.amountML.map(String.init) ?? "")
        _durationText = State(initialValue: record?.durationMinutes.map(String.init) ?? "")
        _note = State(initialValue: record?.note ?? "")
        _reminderDeferralMinutes = State(initialValue: 0)
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            DatePicker("时间", selection: $occurredAt, displayedComponents: [.date, .hourAndMinute])
                                .font(AppTypography.readableBody)
                            Picker("类型", selection: $type) {
                                ForEach(types, id: \.self) { type in
                                    Text(type).tag(type)
                                }
                            }
                            .pickerStyle(.segmented)
                        }
                    }

                    WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.cardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            Text("可选细节")
                                .font(AppTypography.cardTitle)
                                .foregroundStyle(AppColors.inkGreen)

                            TextField("奶量 ml，可不填", text: $amountText)
                                .keyboardType(.numberPad)
                                .textFieldStyle(.roundedBorder)

                            TextField("时长 分钟，可不填", text: $durationText)
                                .keyboardType(.numberPad)
                                .textFieldStyle(.roundedBorder)

                            TextField("备注，可不填", text: $note, axis: .vertical)
                                .lineLimit(2...4)
                                .textFieldStyle(.roundedBorder)
                        }
                    }

                    if shouldShowReminderDeferral {
                        WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius) {
                            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                                HStack(alignment: .top, spacing: AppSpacing.medium) {
                                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                                        Text("下一次提醒")
                                            .font(AppTypography.cardTitle)
                                            .foregroundStyle(AppColors.inkGreen)
                                        if let reminderRepeatIntervalMinutes {
                                            Text("固定间隔 \(feedingReminderIntervalText(reminderRepeatIntervalMinutes))")
                                                .font(AppTypography.caption)
                                                .foregroundStyle(AppColors.inkSoft)
                                        }
                                    }

                                    Spacer(minLength: 0)

                                    Text(nextReminderPreviewText)
                                        .font(AppTypography.caption)
                                        .foregroundStyle(AppColors.blueInk)
                                        .multilineTextAlignment(.trailing)
                                        .fixedSize(horizontal: false, vertical: true)
                                }

                                Picker("顺延", selection: $reminderDeferralMinutes) {
                                    ForEach(reminderDeferralOptions, id: \.self) { minutes in
                                        Text(reminderDeferralTitle(minutes)).tag(minutes)
                                    }
                                }
                                .pickerStyle(.wheel)
                                .frame(height: 94)
                                .clipped()
                            }
                        }
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    PrimaryWatercolorButton(title: "保存喂养记录") {
                        save()
                    }
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
            }
        }
    }

    private func save() {
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
        if onSave(saved, shouldShowReminderDeferral ? reminderDeferralMinutes : nil) {
            dismiss()
        } else {
            errorMessage = "本地保存失败，请稍后再试。输入已保留。"
        }
    }

    private var shouldShowReminderDeferral: Bool {
        record == nil && (reminderRepeatIntervalMinutes ?? 0) > 0
    }

    private var nextReminderPreviewText: String {
        guard let reminderRepeatIntervalMinutes else {
            return "未设置"
        }

        let remindAt = feedingReminderDate(
            occurredAt: occurredAt,
            durationMinutes: previewDurationMinutes,
            repeatIntervalMinutes: reminderRepeatIntervalMinutes,
            deferralMinutes: reminderDeferralMinutes
        )
        return BabyRecordStore.reminderDateTimeString(from: remindAt)
    }

    private var previewDurationMinutes: Int? {
        let trimmed = durationText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let value = Int(trimmed), value > 0 else { return nil }
        return value
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

    private func reminderDeferralTitle(_ minutes: Int) -> String {
        minutes == 0 ? "不顺延" : "+\(minutes)分钟"
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
