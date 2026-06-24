import SwiftUI

struct FeedingRecordView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: FeedingRecord?
    @State private var deleteCandidate: FeedingRecord?
    @State private var isStatsPresented = false
    @State private var reminderDate = Date().addingTimeInterval(2 * 60 * 60)
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

                                summaryMetric(title: "最近一次", value: store.todayFeedingRecords.first?.time ?? "暂无")
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
                                            detail: record.detail,
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
            FeedingEditorSheet(record: editingRecord) { record in
                store.upsert(record)
            }
            .presentationDetents([.medium, .large])
        }
        .sheet(isPresented: $isStatsPresented) {
            RecordStatsSheet(
                title: "今日喂养统计",
                rows: [
                    RecordStatsRow(label: "喂养次数", value: "\(store.feedingCount)次"),
                    RecordStatsRow(label: "总奶量", value: "\(store.milkAmountML)ml"),
                    RecordStatsRow(label: "最近一次", value: store.todayFeedingRecords.first?.time ?? "暂无")
                ]
            )
            .presentationDetents([.height(260)])
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

        return "下一次：\(BabyRecordStore.reminderDateTimeString(from: reminder.remindAt))"
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

    private func saveReminder() {
        notificationMessage = nil
        guard reminderDate > Date() else {
            notificationMessage = "提醒时间要晚于现在。"
            return
        }

        let reminder = FeedingReminder(babyId: store.baby.id, remindAt: reminderDate)
        guard store.upsert(reminder) else {
            notificationMessage = "本地保存失败，请稍后再试。"
            return
        }

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
        reminderDate = defaultReminderDate
        notificationMessage = "喝奶闹钟已取消。"
    }

    private func syncReminderDate() {
        reminderDate = store.nextFeedingReminder?.remindAt ?? defaultReminderDate
    }

    private var defaultReminderDate: Date {
        Date().addingTimeInterval(2 * 60 * 60)
    }

    private func notificationMessage(for result: NotificationScheduleResult) -> String {
        switch result {
        case .scheduled:
            return "喝奶闹钟已加入 iOS 本地通知。"
        case .removed:
            return "提醒时间无效，未安排通知。"
        case .denied:
            return "通知权限未开启。喝奶时间已保留在喂养页，不会弹出系统提醒。"
        case .failed:
            return "通知安排失败。喝奶时间已保留在喂养页。"
        }
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

private struct FeedingEditorSheet: View {
    let record: FeedingRecord?
    let onSave: (FeedingRecord) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var occurredAt: Date
    @State private var type: String
    @State private var amountText: String
    @State private var durationText: String
    @State private var note: String
    @State private var errorMessage: String?

    private let types = ["母乳", "瓶喂", "奶粉", "辅食"]

    init(record: FeedingRecord?, onSave: @escaping (FeedingRecord) -> Bool) {
        self.record = record
        self.onSave = onSave
        _occurredAt = State(initialValue: record?.occurredAt ?? BabyRecordStore.date(fromTimeString: record?.time ?? BabyRecordStore.timeString(from: Date())))
        _type = State(initialValue: record?.type ?? "母乳")
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
                            DatePicker("时间", selection: $occurredAt, displayedComponents: [.hourAndMinute])
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
        if onSave(saved) {
            dismiss()
        } else {
            errorMessage = "本地保存失败，请稍后再试。输入已保留。"
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
