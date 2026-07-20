import SwiftUI

struct VaccineView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: VaccineRecord?
    @State private var deleteCandidate: VaccineRecord?
    @State private var notificationMessage: String?
    @State private var selectedFilter = VaccineBookFilter.all
    @AppStorage("xiaonaiping.vaccineTemplateRegion") private var selectedTemplateRegion = BabyRecordStore.mainlandVaccineRegion

    private let templateRegions = [
        BabyRecordStore.mainlandVaccineRegion,
        BabyRecordStore.hongKongVaccineRegion
    ]

    var body: some View {
        ScreenScaffold(title: "宝宝疫苗本", trailingTitle: "新增", showBackButton: true, trailingAction: {
            openEditor()
        }) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    bookCover
                    templateSection
                    timelineSection
                    disclaimer
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            VaccineEditorSheet(record: editingRecord) { record in
                if store.upsert(record) {
                    AppNotificationScheduler.scheduleVaccineReminder(record) { result in
                        notificationMessage = notificationMessage(for: result)
                    }
                    return true
                }
                return false
            }
            .id(editingRecord?.id)
            .presentationDetents([.large])
        }
        .alert("删除这条接种记录？", isPresented: deleteAlertBinding) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteVaccineRecord(deleteCandidate)
                    AppNotificationScheduler.removeVaccineReminder(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text("只删除这条记录，不会删除宝宝档案或其他记录。")
        }
        .alert("通知状态", isPresented: notificationAlertBinding) {
            Button("知道了", role: .cancel) {
                notificationMessage = nil
            }
        } message: {
            Text(notificationMessage ?? "")
        }
    }

    private var bookCover: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.regular) {
                HStack(alignment: .top, spacing: AppSpacing.medium) {
                    VStack(alignment: .leading, spacing: AppSpacing.small) {
                        Text(AppLocalization.format("%@的疫苗本", store.baby.name))
                            .font(AppTypography.title)
                            .foregroundStyle(AppColors.inkGreen)
                        Text(AppLocalization.format("已接种 %d / %d 针", administeredCount, store.vaccineRecords.count))
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkSoft)
                    }
                    Spacer()
                    AssetWatercolorImage(name: AppAssets.vaccineHero, mode: .multiply)
                        .frame(width: 104, height: 82)
                }

                ProgressView(value: vaccinationProgress)
                    .tint(AppColors.coral)

                Divider()
                    .overlay(AppColors.inkGreen.opacity(0.12))

                if let next = store.nextVaccine {
                    HStack(alignment: .firstTextBaseline) {
                        VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                            Text("下一针")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.inkSoft)
                            Text(next.title.localizedText)
                                .font(AppTypography.bodyLarge)
                                .foregroundStyle(AppColors.inkGreen)
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: AppSpacing.tiny) {
                            Text(store.vaccineDueValue(next))
                                .font(AppTypography.largeNumber)
                                .foregroundStyle(AppColors.coral)
                            Text(store.vaccineDueUnit(next).localizedText)
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.inkSoft)
                        }
                    }
                } else {
                    Text(store.vaccineRecords.isEmpty ? "生成模板或新增记录，开始建立宝宝疫苗本。" : "当前没有待接种记录。")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.inkSoft)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    private var templateSection: some View {
        WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                HStack {
                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("接种模板")
                            .font(AppTypography.cardTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        Text("按宝宝生日生成可编辑的计划日期。")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                    }
                    Spacer()
                    Text("仅作记录")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.blueInk)
                }

                Picker("模板地区", selection: $selectedTemplateRegion) {
                    ForEach(templateRegions, id: \.self) { region in
                        Text(region.localizedText).tag(region)
                    }
                }
                .pickerStyle(.segmented)

                PrimaryWatercolorButton(
                    title: selectedTemplateRegion == BabyRecordStore.mainlandVaccineRegion ? "生成中国大陆模板" : "生成香港模板",
                    tint: AppColors.cream,
                    foreground: selectedTemplateRegion == BabyRecordStore.mainlandVaccineRegion ? AppColors.coral : AppColors.blueInk
                ) {
                    generateSelectedTemplate()
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var timelineSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.medium) {
            HStack {
                Text("月龄时间线")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Spacer()
                Text(AppLocalization.format("%d条记录", timelineRecords.count))
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
            }

            Picker("记录筛选", selection: $selectedFilter) {
                ForEach(VaccineBookFilter.allCases, id: \.self) { filter in
                    Text(filter.rawValue.localizedText).tag(filter)
                }
            }
            .pickerStyle(.segmented)

            if timelineRecords.isEmpty {
                WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
                    VStack(spacing: AppSpacing.medium) {
                        AssetWatercolorImage(name: AppAssets.vaccineTeddy, mode: .multiply)
                            .frame(width: 66, height: 72)
                        Text(emptyStateTitle)
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                        Text(emptyStateDetail)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                            .multilineTextAlignment(.center)
                            .fixedSize(horizontal: false, vertical: true)
                        if store.vaccineRecords.isEmpty {
                            PrimaryWatercolorButton(title: "新增接种记录") {
                                openEditor()
                            }
                        }
                    }
                    .frame(maxWidth: .infinity)
                }
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(timelineRecords.enumerated()), id: \.element.id) { index, vaccine in
                        VaccineTimelineRow(
                            vaccine: vaccine,
                            ageLabel: ageLabel(for: vaccine),
                            showsLineBelow: index < timelineRecords.count - 1,
                            onEdit: { openEditor(vaccine) },
                            onToggle: { toggleAdministered(vaccine) },
                            onDelete: { deleteCandidate = vaccine }
                        )
                    }
                }
            }
        }
    }

    private var disclaimer: some View {
        HStack(alignment: .bottom, spacing: AppSpacing.medium) {
            AssetWatercolorImage(name: AppAssets.vaccineTeddy, mode: .multiply)
                .frame(width: 68, height: 76)
            WatercolorCard(tint: AppColors.mistBlue, cornerRadius: 22, padding: AppSpacing.medium) {
                Text("疫苗本用于记录计划与实际接种日期；模板可编辑，实际安排请以医生或接种机构为准。")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.ink)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var administeredCount: Int {
        store.vaccineRecords.filter(\.isAdministered).count
    }

    private var vaccinationProgress: Double {
        guard !store.vaccineRecords.isEmpty else { return 0 }
        return Double(administeredCount) / Double(store.vaccineRecords.count)
    }

    private var timelineRecords: [VaccineRecord] {
        store.vaccineRecords
            .filter { record in
                switch selectedFilter {
                case .all:
                    true
                case .pending:
                    !record.isAdministered
                case .administered:
                    record.isAdministered
                }
            }
            .sorted { lhs, rhs in
                let leftDate = BabyRecordStore.date(fromDateString: lhs.dueText) ?? .distantFuture
                let rightDate = BabyRecordStore.date(fromDateString: rhs.dueText) ?? .distantFuture
                if leftDate == rightDate {
                    return lhs.title < rhs.title
                }
                return leftDate < rightDate
            }
    }

    private var emptyStateTitle: String {
        switch selectedFilter {
        case .all:
            "还没有接种记录".localizedText
        case .pending:
            "当前没有待接种记录".localizedText
        case .administered:
            "还没有已接种记录".localizedText
        }
    }

    private var emptyStateDetail: String {
        if store.vaccineRecords.isEmpty {
            return "可选择中国大陆或香港模板，也可以手动新增。".localizedText
        }
        return "可切换上方筛选查看其他记录。".localizedText
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

    private var notificationAlertBinding: Binding<Bool> {
        Binding {
            notificationMessage != nil
        } set: { isPresented in
            if !isPresented {
                notificationMessage = nil
            }
        }
    }

    private func openEditor(_ record: VaccineRecord? = nil) {
        editingRecord = record
        isEditorPresented = true
    }

    private func toggleAdministered(_ vaccine: VaccineRecord) {
        store.toggleVaccineCompleted(vaccine)
        guard let updated = store.vaccineRecords.first(where: { $0.id == vaccine.id }) else { return }
        if updated.isAdministered {
            AppNotificationScheduler.removeVaccineReminder(updated)
        } else {
            AppNotificationScheduler.scheduleVaccineReminder(updated) { result in
                notificationMessage = notificationMessage(for: result)
            }
        }
    }

    private func ageLabel(for vaccine: VaccineRecord) -> String {
        guard let dueDate = BabyRecordStore.date(fromDateString: vaccine.dueText) else {
            return "未设置月龄".localizedText
        }

        let birthDate = Calendar.current.startOfDay(for: store.baby.birthDate)
        let plannedDate = Calendar.current.startOfDay(for: dueDate)
        let totalDays = Calendar.current.dateComponents([.day], from: birthDate, to: plannedDate).day ?? 0
        if totalDays <= 14 {
            return "出生时".localizedText
        }

        let months = totalDays / 30
        let days = totalDays % 30
        if months == 0 {
            return AppLocalization.format("满%d周", max(1, totalDays / 7))
        }
        if days == 0 {
            return AppLocalization.format("满%d个月", months)
        }
        return AppLocalization.format("%d个月%d天", months, days)
    }

    private func generateSelectedTemplate() {
        let records = store.generateVaccineTemplate(region: selectedTemplateRegion)
        guard !records.isEmpty else {
            notificationMessage = "该模板记录已存在，可直接编辑日期或删除后重新生成。".localizedText
            return
        }

        selectedFilter = .all
        notificationMessage = AppLocalization.format(
            "已生成%d条%@疫苗记录，计划日期可逐条编辑。",
            records.count,
            selectedTemplateRegion.localizedText
        )
    }

    private func notificationMessage(for result: NotificationScheduleResult) -> String {
        switch result {
        case .scheduled:
            "提醒已加入 iOS 系统通知。".localizedText
        case .removed:
            "这条记录已接种或计划日期无效，未安排新通知。".localizedText
        case .denied:
            "通知权限未开启。可以去系统设置打开通知，接种记录本身已保存。".localizedText
        case .failed:
            "通知安排失败，接种记录本身已保存。".localizedText
        }
    }
}

private enum VaccineBookFilter: String, CaseIterable {
    case all = "全部"
    case pending = "待接种"
    case administered = "已接种"
}

private struct VaccineTimelineRow: View {
    let vaccine: VaccineRecord
    let ageLabel: String
    let showsLineBelow: Bool
    let onEdit: () -> Void
    let onToggle: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: AppSpacing.medium) {
            VStack(spacing: 0) {
                Circle()
                    .fill(vaccine.isAdministered ? AppColors.grass : AppColors.coral)
                    .frame(width: 14, height: 14)
                    .overlay {
                        Circle()
                            .stroke(AppColors.paper, lineWidth: 3)
                    }
                if showsLineBelow {
                    Rectangle()
                        .fill(AppColors.inkGreen.opacity(0.16))
                        .frame(width: 2, height: 116)
                }
            }
            .padding(.top, AppSpacing.regular)

            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Text(ageLabel)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)

                Button(action: onEdit) {
                    VaccineBookEntry(vaccine: vaccine)
                }
                .buttonStyle(.plain)

                HStack(spacing: AppSpacing.small) {
                    Button(action: onToggle) {
                        Label(
                            vaccine.isAdministered ? "改为待接种" : "记录已接种",
                            systemImage: vaccine.isAdministered ? "arrow.uturn.left" : "checkmark.circle"
                        )
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkGreen)
                        .padding(.horizontal, AppSpacing.medium)
                        .frame(height: 34)
                        .background {
                            Capsule().fill(AppColors.grass.opacity(0.56))
                        }
                    }
                    .buttonStyle(.plain)

                    Spacer()

                    Button(action: onDelete) {
                        Image(systemName: "trash")
                            .font(.system(size: 15, weight: .regular))
                            .foregroundStyle(AppColors.coral)
                            .frame(width: 34, height: 34)
                            .background {
                                Circle().fill(AppColors.blush.opacity(0.56))
                            }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("删除接种记录")
                }
            }
            .padding(.bottom, showsLineBelow ? AppSpacing.medium : 0)
        }
    }
}

private struct VaccineBookEntry: View {
    let vaccine: VaccineRecord

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.medium) {
            HStack(alignment: .top, spacing: AppSpacing.medium) {
                AssetWatercolorImage(name: vaccine.icon, mode: .multiply)
                    .frame(width: 42, height: 42)
                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                    Text(vaccine.title.localizedText)
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkGreen)
                        .multilineTextAlignment(.leading)
                    Text(BabyRecordStore.normalizedVaccineRegion(vaccine.region).localizedText)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                }
                Spacer()
                Text(vaccine.displayStatus.localizedText)
                    .font(AppTypography.caption)
                    .foregroundStyle(statusColor)
                    .padding(.horizontal, AppSpacing.medium)
                    .padding(.vertical, AppSpacing.small)
                    .background {
                        Capsule().fill(statusTint.opacity(0.72))
                    }
            }

            HStack(alignment: .top, spacing: AppSpacing.large) {
                dateColumn(title: "计划日期", value: vaccine.dueText.isEmpty ? "未设置" : vaccine.dueText)
                if vaccine.isAdministered {
                    dateColumn(
                        title: "实际接种",
                        value: vaccine.administeredAt.map { BabyRecordStore.displayDateString(from: $0) } ?? "未记录"
                    )
                }
            }

            if let note = vaccine.note, !note.isEmpty {
                Text(note)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)
            }
        }
        .padding(AppSpacing.regular)
        .background {
            CardBackground(tint: rowTint, cornerRadius: 22)
        }
    }

    private func dateColumn(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: AppSpacing.tiny) {
            Text(title.localizedText)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
            Text(value.localizedText)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.inkGreen)
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
        switch vaccine.displayStatus {
        case VaccineRecord.bookedStatus: AppColors.mistBlue
        case VaccineRecord.administeredStatus: AppColors.grass
        default: Color(red: 1.0, green: 0.900, blue: 0.760)
        }
    }

    private var statusColor: Color {
        switch vaccine.displayStatus {
        case VaccineRecord.bookedStatus: AppColors.blueInk
        case VaccineRecord.administeredStatus: AppColors.inkGreen
        default: Color(red: 0.735, green: 0.365, blue: 0.180)
        }
    }
}

private struct VaccineEditorSheet: View {
    let record: VaccineRecord?
    let onSave: (VaccineRecord) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var title: String
    @State private var dueAt: Date
    @State private var status: String
    @State private var region: String
    @State private var hasAdministeredDate: Bool
    @State private var administeredAt: Date
    @State private var note: String
    @State private var errorMessage: String?

    private let statuses = [
        VaccineRecord.pendingStatus,
        VaccineRecord.bookedStatus,
        VaccineRecord.administeredStatus
    ]
    private let regions = [
        BabyRecordStore.mainlandVaccineRegion,
        BabyRecordStore.hongKongVaccineRegion,
        BabyRecordStore.manualVaccineRegion
    ]

    init(record: VaccineRecord?, onSave: @escaping (VaccineRecord) -> Bool) {
        self.record = record
        self.onSave = onSave
        _title = State(initialValue: record?.title ?? "")
        _dueAt = State(initialValue: record.flatMap { BabyRecordStore.date(fromDateString: $0.dueText) } ?? Date())
        _status = State(initialValue: record?.displayStatus ?? VaccineRecord.pendingStatus)
        _region = State(initialValue: BabyRecordStore.normalizedVaccineRegion(record?.region))
        _hasAdministeredDate = State(initialValue: record?.isAdministered == true ? record?.administeredAt != nil : true)
        _administeredAt = State(initialValue: record?.administeredAt ?? Date())
        _note = State(initialValue: record?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            TextField("疫苗或事项名称", text: $title)
                                .textFieldStyle(.roundedBorder)
                            DatePicker("计划接种日期", selection: $dueAt, displayedComponents: [.date])

                            VStack(alignment: .leading, spacing: AppSpacing.small) {
                                Text("接种状态")
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.inkSoft)
                                Picker("接种状态", selection: $status) {
                                    ForEach(statuses, id: \.self) { item in
                                        Text(item.localizedText).tag(item)
                                    }
                                }
                                .pickerStyle(.segmented)
                            }

                            if status == VaccineRecord.administeredStatus {
                                Toggle("记录实际接种日期", isOn: $hasAdministeredDate)
                                if hasAdministeredDate {
                                    DatePicker("实际接种日期", selection: $administeredAt, in: ...Date(), displayedComponents: [.date])
                                }
                            }

                            Picker("模板来源", selection: $region) {
                                ForEach(regions, id: \.self) { item in
                                    Text(item.localizedText).tag(item)
                                }
                            }
                        }
                    }

                    WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            Text("接种备注")
                                .font(AppTypography.cardTitle)
                                .foregroundStyle(AppColors.inkGreen)
                            TextField("可记录接种点、批次或其他信息", text: $note, axis: .vertical)
                                .lineLimit(2...4)
                                .textFieldStyle(.roundedBorder)
                        }
                    }

                    if let errorMessage {
                        Text(errorMessage.localizedText)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    PrimaryWatercolorButton(title: "保存记录") {
                        save()
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle((record == nil ? "新增接种记录" : "编辑接种记录").localizedText)
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
            errorMessage = "请填写疫苗或事项名称。"
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
            icon: status == VaccineRecord.administeredStatus ? AppAssets.cameraIcon : AppAssets.bottleIcon
        )
        saved.title = trimmedTitle
        saved.status = status
        saved.tintName = tintName(for: status)
        saved.icon = status == VaccineRecord.administeredStatus ? AppAssets.cameraIcon : AppAssets.bottleIcon
        saved.dueText = BabyRecordStore.dateString(from: dueAt)
        saved.dueDays = days
        saved.region = region
        saved.administeredAt = status == VaccineRecord.administeredStatus && hasAdministeredDate ? administeredAt : nil
        let trimmedNote = note.trimmingCharacters(in: .whitespacesAndNewlines)
        saved.note = trimmedNote.isEmpty ? nil : trimmedNote
        if onSave(saved) {
            dismiss()
        } else {
            errorMessage = "保存失败，请稍后再试。输入已保留。"
        }
    }

    private func tintName(for status: String) -> String {
        switch status {
        case VaccineRecord.bookedStatus:
            "blue"
        case VaccineRecord.administeredStatus:
            "green"
        default:
            "orange"
        }
    }
}
