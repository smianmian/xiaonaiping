import SwiftUI

struct FeedingRecordView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: FeedingRecord?
    @State private var deleteCandidate: FeedingRecord?

    var body: some View {
        ScreenScaffold(title: "喂养记录", trailingTitle: "统计", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    DateStripView(selected: "今天\n5/15")

                    WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.largeCardRadius) {
                        HStack(spacing: AppSpacing.medium) {
                            AssetWatercolorImage(name: AppAssets.bottleIcon, mode: .multiply)
                                .frame(width: 82, height: 108)

                            VStack(spacing: AppSpacing.medium) {
                                HStack(spacing: AppSpacing.small) {
                                    summaryMetric(title: "今日喂养", value: "\(store.feedingCount)次")
                                    summaryMetric(title: "总奶量", value: "\(store.milkAmountML)ml")
                                }

                                summaryMetric(title: "最近一次", value: store.feedingRecords.first?.time ?? "暂无")
                            }
                        }
                    }

                    VStack(spacing: AppSpacing.regular) {
                        if store.feedingRecords.isEmpty {
                            EmptyRecordCard(
                                icon: AppAssets.bottleIcon,
                                title: "今天还没有喂养记录",
                                actionTitle: "记录喂养"
                            ) {
                                openEditor()
                            }
                        } else {
                            ForEach(store.feedingRecords) { record in
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

                    PrimaryWatercolorButton(title: "+ 记录喂养") {
                        openEditor()
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
    let onSave: (FeedingRecord) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var occurredAt: Date
    @State private var type: String
    @State private var amountText: String
    @State private var durationText: String
    @State private var note: String
    @State private var errorMessage: String?

    private let types = ["母乳", "瓶喂", "奶粉", "辅食"]

    init(record: FeedingRecord?, onSave: @escaping (FeedingRecord) -> Void) {
        self.record = record
        self.onSave = onSave
        _occurredAt = State(initialValue: BabyRecordStore.date(fromTimeString: record?.time ?? BabyRecordStore.timeString(from: Date())))
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
        saved.time = BabyRecordStore.timeString(from: occurredAt)
        saved.type = type
        saved.amountML = amount
        saved.durationMinutes = duration
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        saved.detail = detailText(amount: amount, duration: duration)
        onSave(saved)
        dismiss()
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

private struct EmptyRecordCard: View {
    let icon: String
    let title: String
    let actionTitle: String
    let action: () -> Void

    var body: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
            VStack(spacing: AppSpacing.medium) {
                AssetWatercolorImage(name: icon, mode: .multiply)
                    .frame(width: 64, height: 64)
                Text(title)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                PrimaryWatercolorButton(title: actionTitle, action: action)
            }
            .frame(maxWidth: .infinity)
        }
    }
}

private struct DateStripView: View {
    let selected: String

    private let days = ["一\n5/12", "二\n5/13", "三\n5/14", "今天\n5/15", "五\n5/16", "六\n5/17", "日\n5/18"]

    var body: some View {
        HStack(spacing: AppSpacing.small) {
            ForEach(days, id: \.self) { day in
                Text(day)
                    .font(AppTypography.caption)
                    .foregroundStyle(day == selected ? AppColors.coral : AppColors.ink)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, AppSpacing.small)
                    .background {
                        if day == selected {
                            Circle()
                                .fill(AppColors.blush.opacity(0.62))
                                .frame(width: 72, height: 72)
                        }
                    }
            }
        }
        .padding(.top, AppSpacing.small)
    }
}
