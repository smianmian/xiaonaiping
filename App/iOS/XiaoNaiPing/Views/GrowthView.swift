import SwiftUI

struct GrowthView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var selectedMetric = "体重"
    @State private var isEditorPresented = false
    @State private var editingRecord: GrowthRecord?
    @State private var deleteCandidate: GrowthRecord?

    var body: some View {
        ScreenScaffold(title: "身高体重", trailingTitle: "记录", showBackButton: true, trailingAction: {
            openEditor()
        }) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    SegmentedPill(items: ["体重", "身高", "头围"], selected: $selectedMetric)
                        .padding(.horizontal, 42)

                    GrowthChartView(records: store.growthRecords, metric: selectedMetric)
                        .frame(height: 360)

                    HStack(spacing: AppSpacing.regular) {
                        metricCard(title: "体重", value: formatted(store.latestGrowthRecord?.weight), unit: "kg", icon: "heart.fill", tint: AppColors.blush, color: AppColors.coral)
                        metricCard(title: "身高", value: formatted(store.latestGrowthRecord?.height), unit: "cm", icon: "shield.fill", tint: AppColors.mistBlue, color: AppColors.blueInk)
                        metricCard(title: "头围", value: formatted(store.latestGrowthRecord?.head), unit: "cm", icon: "leaf.fill", tint: AppColors.grass, color: AppColors.inkGreen)
                    }

                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.smallRadius, padding: AppSpacing.medium) {
                        HStack {
                            AssetWatercolorImage(name: AppAssets.teddyHero, mode: .multiply)
                                .frame(width: 42, height: 38)
                            Text("最近一次记录：\(store.latestGrowthRecord?.measuredAt.isEmpty == false ? store.latestGrowthRecord?.measuredAt ?? "暂无" : "暂无")")
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.inkGreen)
                            Spacer()
                        }
                    }

                    MonthlyReportCard(report: store.monthlyReport)

                    VStack(spacing: AppSpacing.regular) {
                        if store.growthRecords.isEmpty {
                            growthEmptyState
                        } else {
                            ForEach(store.growthRecords.reversed()) { record in
                                HStack(spacing: AppSpacing.small) {
                                    Button {
                                        openEditor(record)
                                    } label: {
                                        GrowthHistoryRow(record: record)
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
                                    .accessibilityLabel("删除成长记录")
                                }
                            }
                        }
                    }

                    PrimaryWatercolorButton(title: "+ 添加记录") {
                        openEditor()
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            GrowthEditorSheet(record: editingRecord) { record in
                store.upsert(record)
            }
            .presentationDetents([.medium, .large])
        }
        .alert("删除这条成长记录？", isPresented: deleteAlertBinding) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteGrowthRecord(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text("删除后，图表和最近一次记录会一起更新。")
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

    private var growthEmptyState: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
            VStack(spacing: AppSpacing.medium) {
                AssetWatercolorImage(name: AppAssets.quickGrowthIcon, mode: .multiply)
                    .frame(width: 64, height: 64)
                Text("还没有身高体重记录")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                PrimaryWatercolorButton(title: "添加记录") {
                    openEditor()
                }
            }
            .frame(maxWidth: .infinity)
        }
    }

    private func openEditor(_ record: GrowthRecord? = nil) {
        editingRecord = record
        isEditorPresented = true
    }

    private func formatted(_ value: Double?) -> String {
        guard let value else { return "--" }
        return value.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(value)) : String(format: "%.1f", value)
    }

    private func metricCard(title: String, value: String, unit: String, icon: String, tint: Color, color: Color) -> some View {
        WatercolorCard(tint: tint, cornerRadius: 24, padding: AppSpacing.medium) {
            VStack(spacing: AppSpacing.small) {
                Label(title, systemImage: icon)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkGreen)
                    .lineLimit(1)
                HStack(alignment: .firstTextBaseline, spacing: 2) {
                    Text(value)
                        .font(AppTypography.largeNumber)
                        .foregroundStyle(color)
                    Text(unit)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.ink)
                }
            }
            .frame(maxWidth: .infinity)
        }
    }
}

private struct GrowthChartView: View {
    let records: [GrowthRecord]
    let metric: String

    var body: some View {
        GeometryReader { proxy in
            let size = proxy.size
            ZStack {
                ForEach(0..<7, id: \.self) { index in
                    Path { path in
                        let y = CGFloat(index) / 6 * (size.height - 52) + 16
                        path.move(to: CGPoint(x: 52, y: y))
                        path.addLine(to: CGPoint(x: size.width - 14, y: y))
                    }
                    .stroke(AppColors.softStroke.opacity(0.32), style: StrokeStyle(lineWidth: 1, dash: [6, 8]))
                }

                if records.isEmpty {
                    Text("添加记录后会在这里看到变化")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.inkGreen)
                } else {
                    chartLine(values: values, range: chartRange, size: size, color: lineColor)
                }

                VStack {
                    Spacer()
                    HStack {
                        ForEach(records) { record in
                            Text(record.month)
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.inkGreen)
                                .frame(maxWidth: .infinity)
                        }
                    }
                    .padding(.leading, 52)
                    .padding(.trailing, 10)
                }
            }
        }
    }

    private var values: [Double] {
        switch metric {
        case "身高":
            records.map(\.height)
        case "头围":
            records.map(\.head)
        default:
            records.map(\.weight)
        }
    }

    private var chartRange: ClosedRange<Double> {
        let fallback: ClosedRange<Double>
        switch metric {
        case "身高":
            fallback = 45...75
        case "头围":
            fallback = 32...48
        default:
            fallback = 2...8
        }

        guard let minValue = values.min(), let maxValue = values.max(), minValue != maxValue else {
            return fallback
        }

        let padding = Swift.max((maxValue - minValue) * 0.25, 1)
        return (minValue - padding)...(maxValue + padding)
    }

    private var lineColor: Color {
        switch metric {
        case "身高":
            AppColors.blueInk
        case "头围":
            AppColors.sage
        default:
            AppColors.coral
        }
    }

    private func chartLine(values: [Double], range: ClosedRange<Double>, size: CGSize, color: Color) -> some View {
        let points = values.enumerated().map { index, value in
            let availableWidth = size.width - 76
            let x = 52 + CGFloat(index) / CGFloat(max(values.count - 1, 1)) * availableWidth
            let normalized = (value - range.lowerBound) / (range.upperBound - range.lowerBound)
            let y = (size.height - 58) - CGFloat(normalized) * (size.height - 90) + 14
            return CGPoint(x: x, y: y)
        }

        return ZStack {
            Path { path in
                guard let first = points.first else { return }
                path.move(to: first)
                for point in points.dropFirst() {
                    path.addLine(to: point)
                }
            }
            .stroke(color, style: StrokeStyle(lineWidth: 3, lineCap: .round, lineJoin: .round))

            ForEach(points.indices, id: \.self) { index in
                Circle()
                    .fill(color.opacity(0.78))
                    .frame(width: 12, height: 12)
                    .position(points[index])
            }
        }
    }
}

private struct MonthlyReportCard: View {
    let report: MonthlyReportSnapshot

    var body: some View {
        WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                HStack {
                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("本月成长小报")
                            .font(AppTypography.sectionTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        Text("基于当前本地记录生成")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                    }
                    Spacer()
                    AssetWatercolorImage(name: AppAssets.cakeIcon, mode: .multiply)
                        .frame(width: 54, height: 48)
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: AppSpacing.regular) {
                    reportMetric(title: "喂养", value: "\(report.feedingCount)次 / \(report.milkAmountML)ml", tint: AppColors.cream)
                    reportMetric(title: "睡眠", value: report.sleepDurationText, tint: AppColors.mistBlue)
                    reportMetric(title: "排便", value: "\(report.diaperCount)次", tint: AppColors.grass)
                    reportMetric(title: "照片", value: "\(report.photoCount)张", tint: AppColors.cream)
                }

                Divider().opacity(0.25)

                VStack(alignment: .leading, spacing: AppSpacing.small) {
                    Text(growthSentence)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.ink)
                        .fixedSize(horizontal: false, vertical: true)
                    Text("纪念日 \(report.milestoneCount) 个，待完成疫苗提醒 \(report.vaccineOpenCount) 条。")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.ink)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    private var growthSentence: String {
        guard let weight = report.latestWeight, let height = report.latestHeight else {
            return "添加身高或体重后，这里会自动生成成长变化摘要。"
        }

        let weightDelta = report.weightDelta.map { "，较上次\(deltaText($0, unit: "kg"))" } ?? ""
        let heightDelta = report.heightDelta.map { "，较上次\(deltaText($0, unit: "cm"))" } ?? ""
        return "最近记录：体重 \(display(weight))kg\(weightDelta)，身高 \(display(height))cm\(heightDelta)。"
    }

    private func reportMetric(title: String, value: String, tint: Color) -> some View {
        VStack(alignment: .leading, spacing: AppSpacing.tiny) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkGreen)
            Text(value)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(title == "睡眠" ? AppColors.blueInk : AppColors.coral)
                .lineLimit(2)
                .minimumScaleFactor(0.78)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AppSpacing.regular)
        .background {
            RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                .fill(tint.opacity(0.62))
        }
    }

    private func deltaText(_ value: Double, unit: String) -> String {
        if value > 0 {
            return "+\(display(value))\(unit)"
        }
        if value < 0 {
            return "\(display(value))\(unit)"
        }
        return "无变化"
    }

    private func display(_ value: Double) -> String {
        value.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(value)) : String(format: "%.1f", value)
    }
}

private struct GrowthHistoryRow: View {
    let record: GrowthRecord

    var body: some View {
        HStack(spacing: AppSpacing.medium) {
            AssetWatercolorImage(name: AppAssets.quickGrowthIcon, mode: .multiply)
                .frame(width: 42, height: 42)
            VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                Text(record.measuredAt.isEmpty ? record.month : record.measuredAt)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                Text("体重 \(display(record.weight))kg  身高 \(display(record.height))cm")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.ink)
            }
            Spacer()
            Text("头围 \(display(record.head))cm")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.ink)
        }
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, 13)
        .background {
            CardBackground(tint: AppColors.cream, cornerRadius: 22)
        }
    }

    private func display(_ value: Double) -> String {
        value.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(value)) : String(format: "%.1f", value)
    }
}

private struct GrowthEditorSheet: View {
    let record: GrowthRecord?
    let onSave: (GrowthRecord) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var measuredAt: Date
    @State private var weightText: String
    @State private var heightText: String
    @State private var headText: String
    @State private var note: String
    @State private var errorMessage: String?

    init(record: GrowthRecord?, onSave: @escaping (GrowthRecord) -> Void) {
        self.record = record
        self.onSave = onSave
        _measuredAt = State(initialValue: Date())
        _weightText = State(initialValue: record.map { String($0.weight) } ?? "")
        _heightText = State(initialValue: record.map { String($0.height) } ?? "")
        _headText = State(initialValue: record.map { String($0.head) } ?? "")
        _note = State(initialValue: record?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            DatePicker("日期", selection: $measuredAt, displayedComponents: [.date])
                                .font(AppTypography.readableBody)
                            TextField("体重 kg，可不填", text: $weightText)
                                .keyboardType(.decimalPad)
                                .textFieldStyle(.roundedBorder)
                            TextField("身高 cm，可不填", text: $heightText)
                                .keyboardType(.decimalPad)
                                .textFieldStyle(.roundedBorder)
                            TextField("头围 cm，可不填", text: $headText)
                                .keyboardType(.decimalPad)
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

                    PrimaryWatercolorButton(title: "保存成长记录") {
                        save()
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle(record == nil ? "添加记录" : "编辑记录")
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
        let weight = decimalValue(weightText)
        let height = decimalValue(heightText)
        let head = decimalValue(headText)

        guard errorMessage == nil else { return }
        guard weight != nil || height != nil else {
            errorMessage = "至少填写体重或身高其中一项。"
            return
        }

        var saved = record ?? GrowthRecord(
            month: BabyRecordStore.monthString(from: measuredAt),
            weight: weight ?? 0,
            height: height ?? 0,
            head: head ?? 0,
            measuredAt: BabyRecordStore.dateString(from: measuredAt)
        )
        saved.month = BabyRecordStore.monthString(from: measuredAt)
        saved.weight = weight ?? saved.weight
        saved.height = height ?? saved.height
        saved.head = head ?? saved.head
        saved.measuredAt = BabyRecordStore.dateString(from: measuredAt)
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        onSave(saved)
        dismiss()
    }

    private func decimalValue(_ text: String) -> Double? {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        guard let value = Double(trimmed), value > 0 else {
            errorMessage = "数值请填写大于 0 的数字，或留空。"
            return nil
        }
        errorMessage = nil
        return value
    }
}
