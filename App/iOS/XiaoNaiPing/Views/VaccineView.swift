import SwiftUI

struct VaccineView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: VaccineRecord?
    @State private var deleteCandidate: VaccineRecord?

    var body: some View {
        ScreenScaffold(title: "疫苗提醒", trailingTitle: "新增", showBackButton: true, trailingAction: {
            openEditor()
        }) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    heroCard
                    reminderList
                    disclaimer
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            VaccineEditorSheet(record: editingRecord) { record in
                store.upsert(record)
            }
            .presentationDetents([.medium, .large])
        }
        .alert("删除这条疫苗提醒？", isPresented: deleteAlertBinding) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteVaccineRecord(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text("只删除这条提醒，不会删除宝宝档案或其他记录。")
        }
    }

    private var heroCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: AppSpacing.regular) {
                    Text("下一针：")
                        .font(AppTypography.bodyLarge)
                    Text(store.nextVaccine?.title ?? "暂无待办提醒")
                        .font(AppTypography.title)
                    HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                        Text("\(store.nextVaccine?.dueDays ?? 0)")
                            .font(AppTypography.largeNumber)
                            .foregroundStyle(AppColors.coral)
                        Text(store.nextVaccine == nil ? "待添加" : "天后")
                            .font(AppTypography.bodyLarge)
                    }
                }
                .foregroundStyle(AppColors.inkGreen)
                Spacer()
                AssetWatercolorImage(name: AppAssets.vaccineHero, mode: .multiply)
                    .frame(width: 158, height: 126)
            }
        }
    }

    private var reminderList: some View {
        VStack(spacing: AppSpacing.medium) {
            if store.vaccineRecords.isEmpty {
                WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
                    VStack(spacing: AppSpacing.medium) {
                        AssetWatercolorImage(name: AppAssets.vaccineHero, mode: .multiply)
                            .frame(width: 90, height: 76)
                        Text("还没有疫苗提醒")
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                        PrimaryWatercolorButton(title: "添加提醒") {
                            openEditor()
                        }
                    }
                    .frame(maxWidth: .infinity)
                }
            } else {
                ForEach(store.vaccineRecords) { vaccine in
                    HStack(spacing: AppSpacing.small) {
                        Button {
                            openEditor(vaccine)
                        } label: {
                            VaccineRow(vaccine: vaccine)
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.plain)

                        VStack(spacing: AppSpacing.small) {
                            Button {
                                store.toggleVaccineCompleted(vaccine)
                            } label: {
                                Image(systemName: vaccine.status == "已完成" ? "arrow.uturn.left" : "checkmark")
                                    .font(.system(size: 16, weight: .semibold))
                                    .foregroundStyle(AppColors.inkGreen)
                                    .frame(width: 38, height: 38)
                                    .background {
                                        Circle().fill(AppColors.grass.opacity(0.62))
                                    }
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel(vaccine.status == "已完成" ? "标记为待接种" : "标记完成")

                            Button {
                                deleteCandidate = vaccine
                            } label: {
                                Image(systemName: "trash")
                                    .font(.system(size: 16, weight: .regular))
                                    .foregroundStyle(AppColors.coral)
                                    .frame(width: 38, height: 38)
                                    .background {
                                        Circle().fill(AppColors.blush.opacity(0.56))
                                    }
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("删除疫苗提醒")
                        }
                    }
                }
            }
        }
    }

    private var disclaimer: some View {
        HStack(alignment: .bottom, spacing: AppSpacing.medium) {
            AssetWatercolorImage(name: AppAssets.vaccineTeddy, mode: .multiply)
                .frame(width: 86, height: 96)
            WatercolorCard(tint: AppColors.mistBlue, cornerRadius: 24, padding: AppSpacing.medium) {
                Text("疫苗模块仅做日程提醒；模板日期可编辑，不替代医生建议。")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.ink)
                    .fixedSize(horizontal: false, vertical: true)
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

    private func openEditor(_ record: VaccineRecord? = nil) {
        editingRecord = record
        isEditorPresented = true
    }
}

private struct VaccineRow: View {
    let vaccine: VaccineRecord

    var body: some View {
        HStack(spacing: AppSpacing.medium) {
            AssetWatercolorImage(name: vaccine.icon, mode: .multiply)
                .frame(width: 50, height: 50)
            Text(vaccine.title)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.inkGreen)
                .lineLimit(2)
            Spacer()
            VStack(alignment: .trailing, spacing: AppSpacing.tiny) {
                Text(vaccine.status)
                    .font(AppTypography.body)
                    .foregroundStyle(statusColor)
                    .padding(.horizontal, AppSpacing.medium)
                    .padding(.vertical, AppSpacing.small)
                    .background {
                        Capsule()
                            .fill(statusTint.opacity(0.72))
                    }
                if !vaccine.dueText.isEmpty {
                    Text(vaccine.dueText)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkGreen)
                }
            }
        }
        .padding(AppSpacing.medium)
        .background {
            CardBackground(tint: rowTint, cornerRadius: 24)
        }
    }

    private var rowTint: Color {
        switch vaccine.tintName {
        case "blue": AppColors.mistBlue
        case "green": AppColors.grass
        default: AppColors.cream
        }
    }

    private var statusTint: Color {
        switch vaccine.status {
        case "已预约": AppColors.mistBlue
        case "已完成": AppColors.grass
        default: Color(red: 1.0, green: 0.900, blue: 0.760)
        }
    }

    private var statusColor: Color {
        switch vaccine.status {
        case "已预约": AppColors.blueInk
        case "已完成": AppColors.inkGreen
        default: Color(red: 0.735, green: 0.365, blue: 0.180)
        }
    }
}

private struct VaccineEditorSheet: View {
    let record: VaccineRecord?
    let onSave: (VaccineRecord) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var title: String
    @State private var dueAt: Date
    @State private var status: String
    @State private var region: String
    @State private var note: String
    @State private var errorMessage: String?

    private let statuses = ["待接种", "已预约", "已完成"]
    private let regions = ["国内", "香港", "手动"]

    init(record: VaccineRecord?, onSave: @escaping (VaccineRecord) -> Void) {
        self.record = record
        self.onSave = onSave
        _title = State(initialValue: record?.title ?? "")
        _dueAt = State(initialValue: Date())
        _status = State(initialValue: record?.status ?? "待接种")
        _region = State(initialValue: record?.region ?? "手动")
        _note = State(initialValue: record?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            TextField("提醒名称", text: $title)
                                .textFieldStyle(.roundedBorder)
                            DatePicker("提醒日期", selection: $dueAt, displayedComponents: [.date])
                            Picker("状态", selection: $status) {
                                ForEach(statuses, id: \.self) { item in
                                    Text(item).tag(item)
                                }
                            }
                            Picker("模板来源", selection: $region) {
                                ForEach(regions, id: \.self) { item in
                                    Text(item).tag(item)
                                }
                            }
                        }
                    }

                    WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            Text("提醒说明")
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

                    PrimaryWatercolorButton(title: "保存提醒") {
                        save()
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle(record == nil ? "新增提醒" : "编辑提醒")
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
        let trimmedTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedTitle.isEmpty else {
            errorMessage = "请填写提醒名称。"
            return
        }

        let days = Calendar.current.dateComponents(
            [.day],
            from: Calendar.current.startOfDay(for: Date()),
            to: Calendar.current.startOfDay(for: dueAt)
        ).day
        var saved = record ?? VaccineRecord(
            title: trimmedTitle,
            status: status,
            tintName: tintName(for: status),
            icon: status == "已完成" ? AppAssets.cameraIcon : AppAssets.bottleIcon
        )
        saved.title = trimmedTitle
        saved.status = status
        saved.tintName = tintName(for: status)
        saved.icon = status == "已完成" ? AppAssets.cameraIcon : AppAssets.bottleIcon
        saved.dueText = BabyRecordStore.dateString(from: dueAt)
        saved.dueDays = days
        saved.region = region
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        onSave(saved)
        dismiss()
    }

    private func tintName(for status: String) -> String {
        switch status {
        case "已预约":
            "blue"
        case "已完成":
            "green"
        default:
            "orange"
        }
    }
}
