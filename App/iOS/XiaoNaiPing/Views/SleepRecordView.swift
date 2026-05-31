import SwiftUI

struct SleepRecordView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: SleepRecord?
    @State private var deleteCandidate: SleepRecord?

    var body: some View {
        ScreenScaffold(title: "睡眠记录", trailingTitle: "统计", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    AssetWatercolorImage(name: AppAssets.sleepHero, mode: .multiply)
                        .frame(height: 130)

                    WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(spacing: AppSpacing.medium) {
                            Text("今日总睡眠")
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.ink)
                            HStack(alignment: .firstTextBaseline, spacing: 4) {
                                Text(totalSleepHours)
                                Text("小时")
                                    .font(AppTypography.body)
                                Text(totalSleepMinutes)
                                Text("分")
                                    .font(AppTypography.body)
                            }
                            .font(AppTypography.largeNumber)
                            .foregroundStyle(AppColors.blueInk)

                            Divider().opacity(0.35)

                            HStack {
                                sleepMiniStat("小睡", "\(store.sleepRecords.filter { $0.type == "小睡" }.count)次", icon: AppAssets.cloudBlue)
                                Divider().frame(height: 58)
                                sleepMiniStat("状态", store.ongoingSleep == nil ? "已记录" : "进行中", icon: AppAssets.moonIcon)
                            }
                        }
                    }

                    SectionTitleView(title: "今日睡眠时段")

                    VStack(spacing: AppSpacing.regular) {
                        if store.sleepRecords.isEmpty {
                            sleepEmptyState
                        } else {
                            ForEach(store.sleepRecords) { record in
                                HStack(spacing: AppSpacing.small) {
                                    Button {
                                        if !record.isOngoing {
                                            openEditor(record)
                                        }
                                    } label: {
                                        HStack(spacing: AppSpacing.medium) {
                                            AssetWatercolorImage(name: record.icon, mode: .multiply)
                                                .frame(width: 42, height: 42)
                                            Text("\(record.start) → \(record.end)")
                                                .font(AppTypography.bodyLarge)
                                                .foregroundStyle(AppColors.ink)
                                            Spacer()
                                            Text("\(record.type) \(record.duration)")
                                                .font(AppTypography.body)
                                                .foregroundStyle(record.isOngoing ? AppColors.coral : AppColors.ink)
                                        }
                                        .padding(.horizontal, AppSpacing.medium)
                                        .padding(.vertical, 14)
                                        .background {
                                            CardBackground(tint: record.isOngoing ? AppColors.blush : AppColors.cream, cornerRadius: 22)
                                        }
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
                                    .accessibilityLabel("删除睡眠记录")
                                }
                            }
                        }
                    }

                    HStack(spacing: AppSpacing.medium) {
                        PrimaryWatercolorButton(
                            title: store.ongoingSleep == nil ? "开始睡觉" : "结束睡眠",
                            tint: AppColors.mistBlue,
                            foreground: AppColors.blueInk
                        ) {
                            if store.ongoingSleep == nil {
                                store.startSleepNow()
                            } else {
                                store.finishOngoingSleepNow()
                            }
                        }
                        PrimaryWatercolorButton(title: "补记", tint: AppColors.mistBlue.opacity(0.7), foreground: AppColors.blueInk) {
                            openEditor()
                        }
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            SleepEditorSheet(record: editingRecord) { record in
                store.upsert(record)
            }
            .presentationDetents([.medium, .large])
        }
        .alert("删除这段睡眠？", isPresented: deleteAlertBinding) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteSleepRecord(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text("删除后，今日睡眠总时长会一起更新。")
        }
    }

    private var totalSleepHours: String {
        "\(store.totalSleepMinutes / 60)"
    }

    private var totalSleepMinutes: String {
        "\(store.totalSleepMinutes % 60)"
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

    private var sleepEmptyState: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
            VStack(spacing: AppSpacing.medium) {
                AssetWatercolorImage(name: AppAssets.moonIcon, mode: .multiply)
                    .frame(width: 64, height: 64)
                Text("今天还没有睡眠记录")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                PrimaryWatercolorButton(title: "开始睡觉", tint: AppColors.mistBlue, foreground: AppColors.blueInk) {
                    store.startSleepNow()
                }
            }
            .frame(maxWidth: .infinity)
        }
    }

    private func openEditor(_ record: SleepRecord? = nil) {
        editingRecord = record
        isEditorPresented = true
    }

    private func sleepMiniStat(_ title: String, _ value: String, icon: String) -> some View {
        HStack(spacing: AppSpacing.small) {
            AssetWatercolorImage(name: icon, mode: .multiply)
                .frame(width: 42, height: 42)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(AppTypography.caption)
                Text(value)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.blueInk)
            }
            .foregroundStyle(AppColors.ink)
        }
        .frame(maxWidth: .infinity)
    }
}

private struct SleepEditorSheet: View {
    let record: SleepRecord?
    let onSave: (SleepRecord) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var startAt: Date
    @State private var endAt: Date
    @State private var type: String
    @State private var note: String
    @State private var errorMessage: String?

    private let types = ["小睡", "夜睡"]

    init(record: SleepRecord?, onSave: @escaping (SleepRecord) -> Void) {
        self.record = record
        self.onSave = onSave
        let startDate = BabyRecordStore.date(fromTimeString: record?.start ?? BabyRecordStore.timeString(from: Date()))
        _startAt = State(initialValue: startDate)
        _endAt = State(initialValue: Self.endDate(for: record, startDate: startDate))
        _type = State(initialValue: record?.type ?? "小睡")
        _note = State(initialValue: record?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            DatePicker("开始", selection: $startAt, displayedComponents: [.date, .hourAndMinute])
                                .font(AppTypography.readableBody)
                            DatePicker("结束", selection: $endAt, displayedComponents: [.date, .hourAndMinute])
                                .font(AppTypography.readableBody)
                            Picker("类型", selection: $type) {
                                ForEach(types, id: \.self) { type in
                                    Text(type).tag(type)
                                }
                            }
                            .pickerStyle(.segmented)
                        }
                    }

                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            Text("备注")
                                .font(AppTypography.cardTitle)
                                .foregroundStyle(AppColors.inkGreen)
                            TextField("可不填", text: $note, axis: .vertical)
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

                    PrimaryWatercolorButton(title: "保存睡眠记录", tint: AppColors.mistBlue, foreground: AppColors.blueInk) {
                        save()
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle(record == nil ? "补记睡眠" : "编辑睡眠")
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
        let minutes = Calendar.current.dateComponents([.minute], from: startAt, to: endAt).minute ?? 0
        guard minutes > 0 else {
            errorMessage = "结束时间需要晚于开始时间。"
            return
        }

        var saved = record ?? SleepRecord(
            start: BabyRecordStore.timeString(from: startAt),
            end: BabyRecordStore.timeString(from: endAt),
            type: type,
            duration: BabyRecordStore.durationText(from: minutes),
            icon: type == "夜睡" ? AppAssets.moonIcon : AppAssets.cloudBlue
        )
        saved.start = BabyRecordStore.timeString(from: startAt)
        saved.end = BabyRecordStore.timeString(from: endAt)
        saved.type = type
        saved.durationMinutes = minutes
        saved.duration = BabyRecordStore.durationText(from: minutes)
        saved.icon = type == "夜睡" ? AppAssets.moonIcon : AppAssets.cloudBlue
        saved.isOngoing = false
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        onSave(saved)
        dismiss()
    }

    private static func endDate(for record: SleepRecord?, startDate: Date) -> Date {
        guard let record, !record.isOngoing else {
            return Calendar.current.date(byAdding: .minute, value: 45, to: startDate) ?? Date()
        }

        var endDate = BabyRecordStore.date(fromTimeString: record.end)
        if endDate <= startDate {
            endDate = Calendar.current.date(byAdding: .day, value: 1, to: endDate) ?? endDate
        }
        return endDate
    }
}
