import SwiftUI

/// 健康观察：黄疸 / 体温 / 用药补剂。
/// 只做记录与趋势出示，不做任何医学判断。
struct HealthObservationView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var selectedKind = HealthObservation.jaundiceKind
    @State private var isEditorPresented = false
    @State private var editingRecord: HealthObservation?
    @State private var deleteCandidate: HealthObservation?

    private let kinds = [HealthObservation.jaundiceKind, HealthObservation.temperatureKind, HealthObservation.medicationKind]

    private var filteredRecords: [HealthObservation] {
        store.healthObservations.filter { $0.kind == selectedKind }
    }

    var body: some View {
        ScreenScaffold(title: "健康观察", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    PrimaryWatercolorButton(title: "记录\(selectedKind)") {
                        openEditor()
                    }

                    SegmentedPill(items: kinds, selected: $selectedKind)
                        .padding(.horizontal, AppSpacing.small)

                    if selectedKind == HealthObservation.medicationKind, let lastDose = lastMedicationText {
                        WatercolorCard(tint: AppColors.butter.opacity(0.55), cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
                            Label(lastDose, systemImage: "pills")
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.inkGreen)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }

                    VStack(alignment: .leading, spacing: AppSpacing.regular) {
                        SectionTitleView(title: "\(selectedKind)记录")
                        if filteredRecords.isEmpty {
                            emptyState
                        } else {
                            ForEach(filteredRecords) { record in
                                recordRow(record)
                            }
                        }
                    }

                    Text("记录仅供就诊时出示参考，不构成医疗建议；黄疸、发热等异常请及时就医。")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            HealthObservationEditorSheet(record: editingRecord, kind: selectedKind) { record in
                store.upsert(record)
            }
            .presentationDetents([.medium, .large])
        }
        .alert("删除这条记录？", isPresented: Binding {
            deleteCandidate != nil
        } set: { isPresented in
            if !isPresented { deleteCandidate = nil }
        }) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteHealthObservation(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        }
    }

    private var lastMedicationText: String? {
        guard let last = store.healthObservations.first(where: { $0.kind == HealthObservation.medicationKind }) else {
            return nil
        }
        let elapsed = BabyRecordStore.displayDateString(from: last.occurredAt)
        return "上次：\(last.summaryText) · \(elapsed) \(BabyRecordStore.timeString(from: last.occurredAt))"
    }

    private var emptyState: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
            VStack(spacing: AppSpacing.medium) {
                Image(systemName: emptyIcon)
                    .font(.system(size: 34, weight: .regular))
                    .foregroundStyle(AppColors.inkSoft)
                Text("还没有\(selectedKind)记录")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, AppSpacing.medium)
        }
    }

    private var emptyIcon: String {
        switch selectedKind {
        case HealthObservation.jaundiceKind: "sun.max"
        case HealthObservation.temperatureKind: "thermometer.medium"
        default: "pills"
        }
    }

    private func recordRow(_ record: HealthObservation) -> some View {
        Button {
            openEditor(record)
        } label: {
            RecordRowView(
                icon: nil,
                systemIcon: emptyIcon,
                time: "\(BabyRecordStore.displayDateString(from: record.occurredAt)) \(BabyRecordStore.timeString(from: record.occurredAt))",
                title: record.summaryText,
                detail: record.note ?? "",
                tint: AppColors.cream
            )
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(.plain)
        .contextMenu {
            Button {
                openEditor(record)
            } label: {
                Label("编辑", systemImage: "pencil")
            }
            Button(role: .destructive) {
                deleteCandidate = record
            } label: {
                Label("删除", systemImage: "trash")
            }
        }
    }

    private func openEditor(_ record: HealthObservation? = nil) {
        editingRecord = record
        isEditorPresented = true
    }
}

private struct HealthObservationEditorSheet: View {
    let record: HealthObservation?
    let onSave: (HealthObservation) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var kind: String
    @State private var occurredAt: Date
    @State private var valueText: String
    @State private var zone: String
    @State private var medicationName: String
    @State private var dose: String
    @State private var note: String
    @State private var errorMessage: String?

    init(record: HealthObservation?, kind: String, onSave: @escaping (HealthObservation) -> Bool) {
        self.record = record
        self.onSave = onSave
        _kind = State(initialValue: record?.kind ?? kind)
        _occurredAt = State(initialValue: record?.occurredAt ?? Date())
        _valueText = State(initialValue: record?.value.map { String(format: "%.1f", $0) } ?? "")
        _zone = State(initialValue: record?.zone ?? "面部")
        _medicationName = State(initialValue: record?.medicationName ?? "维生素D")
        _dose = State(initialValue: record?.dose ?? "")
        _note = State(initialValue: record?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            Picker("类型", selection: $kind) {
                                ForEach([HealthObservation.jaundiceKind, HealthObservation.temperatureKind, HealthObservation.medicationKind], id: \.self) { item in
                                    Text(item).tag(item)
                                }
                            }
                            .pickerStyle(.segmented)
                            .tint(AppColors.peach)

                            QuickTimeField(date: $occurredAt)

                            kindFields
                        }
                    }

                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
                        TextField("备注，可不填", text: $note, axis: .vertical)
                            .lineLimit(2...4)
                            .textFieldStyle(.roundedBorder)
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .safeAreaInset(edge: .bottom, spacing: 0) {
                PrimaryWatercolorButton(title: "保存记录") {
                    save()
                }
                .padding(.horizontal, AppSpacing.large)
                .padding(.vertical, AppSpacing.small)
                .background(.ultraThinMaterial)
            }
            .navigationTitle(record == nil ? "记录健康观察" : "编辑记录")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") { dismiss() }
                }
            }
        }
    }

    @ViewBuilder
    private var kindFields: some View {
        switch kind {
        case HealthObservation.jaundiceKind:
            TextField("经皮值 mg/dL，可不填", text: $valueText)
                .keyboardType(.decimalPad)
                .textFieldStyle(.roundedBorder)
            Picker("部位", selection: $zone) {
                ForEach(HealthObservation.jaundiceZones, id: \.self) { item in
                    Text(item).tag(item)
                }
            }
            .pickerStyle(.segmented)
        case HealthObservation.temperatureKind:
            TextField("体温 ℃（必填）", text: $valueText)
                .keyboardType(.decimalPad)
                .textFieldStyle(.roundedBorder)
        default:
            Picker("药品", selection: $medicationName) {
                ForEach(HealthObservation.medicationPresets, id: \.self) { item in
                    Text(item).tag(item)
                }
            }
            .pickerStyle(.menu)
            .tint(AppColors.inkGreen)
            TextField("剂量，如 400IU / 5ml，可不填", text: $dose)
                .textFieldStyle(.roundedBorder)
        }
    }

    private func save() {
        errorMessage = nil
        let trimmedValue = valueText.trimmingCharacters(in: .whitespacesAndNewlines)
        var value: Double?
        if !trimmedValue.isEmpty {
            guard let parsed = Double(trimmedValue), parsed > 0 else {
                errorMessage = "数值请填写大于 0 的数字，或留空。"
                return
            }
            value = parsed
        }
        if kind == HealthObservation.temperatureKind {
            guard let temperature = value, (30...45).contains(temperature) else {
                errorMessage = "体温请填写 30–45℃ 之间的数值。"
                return
            }
        }

        var saved = record ?? HealthObservation(kind: kind, occurredAt: occurredAt)
        saved.kind = kind
        saved.occurredAt = occurredAt
        saved.value = value
        saved.zone = kind == HealthObservation.jaundiceKind ? zone : nil
        saved.medicationName = kind == HealthObservation.medicationKind ? medicationName : nil
        saved.dose = kind == HealthObservation.medicationKind && !dose.isEmpty ? dose : nil
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        if onSave(saved) {
            dismiss()
        } else {
            errorMessage = "保存失败，请稍后再试。输入已保留。"
        }
    }
}
