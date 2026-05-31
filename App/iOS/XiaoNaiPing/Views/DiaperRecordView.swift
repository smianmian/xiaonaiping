import SwiftUI

struct DiaperRecordView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingRecord: DiaperRecord?
    @State private var deleteCandidate: DiaperRecord?

    var body: some View {
        ScreenScaffold(title: "排便记录", trailingTitle: "统计", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    AssetWatercolorImage(name: AppAssets.diaperHero, mode: .multiply)
                        .frame(height: 150)

                    WatercolorCard(tint: AppColors.grass, cornerRadius: AppShapes.largeCardRadius) {
                        HStack {
                            diaperSummary("今日便便", "\(store.poopCount)", "次", icon: AppAssets.diaperSmallIcon, color: AppColors.coral)
                            Divider().frame(height: 92)
                            diaperSummary("小便", "\(store.peeCount)", "次", icon: AppAssets.peeDropIcon, color: AppColors.blueInk)
                            Divider().frame(height: 92)
                            diaperSummary("最近一次", store.diaperRecords.first?.time ?? "--", "", icon: AppAssets.quickGrowthIcon, color: AppColors.sage)
                        }
                    }

                    VStack(spacing: AppSpacing.regular) {
                        if store.diaperRecords.isEmpty {
                            diaperEmptyState
                        } else {
                            ForEach(store.diaperRecords) { record in
                                HStack(spacing: AppSpacing.small) {
                                    Button {
                                        openEditor(record)
                                    } label: {
                                        RecordRowView(
                                            icon: record.icon,
                                            time: record.time,
                                            title: record.title,
                                            detail: record.note ?? "",
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
                                    .accessibilityLabel("删除排便记录")
                                }
                            }
                        }
                    }

                    PrimaryWatercolorButton(title: "+ 记录一次", tint: AppColors.grass, foreground: AppColors.inkGreen) {
                        openEditor()
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            DiaperEditorSheet(record: editingRecord) { record in
                store.upsert(record)
            }
            .presentationDetents([.medium, .large])
        }
        .alert("删除这条排便记录？", isPresented: deleteAlertBinding) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteDiaperRecord(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text("删除后，今日排便摘要会一起更新。")
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

    private var diaperEmptyState: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
            VStack(spacing: AppSpacing.medium) {
                AssetWatercolorImage(name: AppAssets.diaperIcon, mode: .multiply)
                    .frame(width: 64, height: 64)
                Text("今天还没有排便记录")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                PrimaryWatercolorButton(title: "记录一次", tint: AppColors.grass, foreground: AppColors.inkGreen) {
                    openEditor()
                }
            }
            .frame(maxWidth: .infinity)
        }
    }

    private func openEditor(_ record: DiaperRecord? = nil) {
        editingRecord = record
        isEditorPresented = true
    }

    private func diaperSummary(_ title: String, _ value: String, _ unit: String, icon: String, color: Color) -> some View {
        VStack(spacing: AppSpacing.small) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.ink)
                .multilineTextAlignment(.center)
            HStack(alignment: .firstTextBaseline, spacing: 2) {
                Text(value)
                    .font(AppTypography.largeNumber)
                    .foregroundStyle(color)
                Text(unit)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.ink)
            }
            AssetWatercolorImage(name: icon, mode: .multiply)
                .frame(width: 48, height: 48)
        }
        .frame(maxWidth: .infinity)
    }
}

private struct DiaperEditorSheet: View {
    let record: DiaperRecord?
    let onSave: (DiaperRecord) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var occurredAt: Date
    @State private var kind: String
    @State private var color: String
    @State private var texture: String
    @State private var note: String

    private let kinds = ["大便", "小便"]
    private let colors = ["未选择", "金黄色", "黄色", "绿色", "棕色"]
    private let textures = ["未选择", "糊状", "软便", "水样", "颗粒"]

    init(record: DiaperRecord?, onSave: @escaping (DiaperRecord) -> Void) {
        self.record = record
        self.onSave = onSave
        _occurredAt = State(initialValue: BabyRecordStore.date(fromTimeString: record?.time ?? BabyRecordStore.timeString(from: Date())))
        _kind = State(initialValue: record?.kind ?? "大便")
        _color = State(initialValue: record?.color ?? "未选择")
        _texture = State(initialValue: record?.texture ?? "未选择")
        _note = State(initialValue: record?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.grass, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            DatePicker("时间", selection: $occurredAt, displayedComponents: [.hourAndMinute])
                                .font(AppTypography.readableBody)
                            Picker("类型", selection: $kind) {
                                ForEach(kinds, id: \.self) { item in
                                    Text(item).tag(item)
                                }
                            }
                            .pickerStyle(.segmented)
                        }
                    }

                    if kind == "大便" {
                        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
                            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                                Text("可选细节")
                                    .font(AppTypography.cardTitle)
                                    .foregroundStyle(AppColors.inkGreen)
                                Picker("颜色", selection: $color) {
                                    ForEach(colors, id: \.self) { item in
                                        Text(item).tag(item)
                                    }
                                }
                                Picker("形态", selection: $texture) {
                                    ForEach(textures, id: \.self) { item in
                                        Text(item).tag(item)
                                    }
                                }
                                TextField("备注，可不填", text: $note, axis: .vertical)
                                    .lineLimit(2...4)
                                    .textFieldStyle(.roundedBorder)
                            }
                        }
                    } else {
                        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
                            TextField("备注，可不填", text: $note, axis: .vertical)
                                .lineLimit(2...4)
                                .textFieldStyle(.roundedBorder)
                        }
                    }

                    PrimaryWatercolorButton(title: "保存排便记录", tint: AppColors.grass, foreground: AppColors.inkGreen) {
                        save()
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle(record == nil ? "记录排便" : "编辑排便")
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
        let savedColor = color == "未选择" || kind == "小便" ? nil : color
        let savedTexture = texture == "未选择" || kind == "小便" ? nil : texture
        let title = titleText(kind: kind, color: savedColor, texture: savedTexture)
        var saved = record ?? DiaperRecord(
            time: BabyRecordStore.timeString(from: occurredAt),
            title: title,
            icon: kind == "小便" ? AppAssets.peeDropIcon : AppAssets.diaperIcon
        )
        saved.time = BabyRecordStore.timeString(from: occurredAt)
        saved.title = title
        saved.kind = kind
        saved.color = savedColor
        saved.texture = savedTexture
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        saved.icon = kind == "小便" ? AppAssets.peeDropIcon : AppAssets.diaperIcon
        onSave(saved)
        dismiss()
    }

    private func titleText(kind: String, color: String?, texture: String?) -> String {
        var parts = [kind]
        if let color {
            parts.append(color)
        }
        if let texture {
            parts.append(texture)
        }
        return parts.joined(separator: "-")
    }
}
