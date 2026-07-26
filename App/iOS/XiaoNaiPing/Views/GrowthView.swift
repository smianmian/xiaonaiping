import SwiftUI
import Charts

struct GrowthView: View {
    var onOpenMonthlyReport: (() -> Void)?
    var onOpenVaccineBook: (() -> Void)?
    var autoPresentEditor = false

    @EnvironmentObject private var store: BabyRecordStore
    @State private var selectedMetric = "体重"
    @State private var isEditorPresented = false
    @State private var editingRecord: GrowthRecord?
    @State private var deleteCandidate: GrowthRecord?
    @State private var didAutoPresentEditor = false

    var body: some View {
        ScreenScaffold(title: "成长", trailingTitle: "记录", showBackButton: false, trailingAction: {
            openEditor()
        }) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    growthCard
                    vaccineBookEntry
                    healthObservationEntry
                    if !store.currentBabyGrowthRecords.isEmpty {
                        historySection
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            GrowthEditorSheet(record: editingRecord, latest: store.latestGrowthRecord) { record in
                store.upsert(record)
            }
            .presentationDetents([.medium, .large])
        }
        .onAppear {
            if autoPresentEditor && !didAutoPresentEditor {
                didAutoPresentEditor = true
                openEditor()
            }
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

    /// 身高体重主卡：空状态按参考稿（大插画 + 引导文案 + 珊瑚色胶囊按钮），
    /// 有数据时在同一张卡里展示指标切换、趋势图和最新数值。
    private var growthCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                HStack(spacing: AppSpacing.small) {
                    Image(systemName: "ruler.fill")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(AppColors.sage)
                    Text("身高体重")
                        .font(AppTypography.sectionTitle)
                        .foregroundStyle(AppColors.inkGreen)
                }

                if store.currentBabyGrowthRecords.isEmpty {
                    VStack(spacing: AppSpacing.medium) {
                        AssetWatercolorImage(name: "approvedGrowthMeasure")
                            .frame(width: 170, height: 170)
                            .padding(.top, AppSpacing.small)
                        Text("还没有身高体重记录")
                            .font(AppTypography.sectionTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        Text("记录第一次测量后，这里会生成成长趋势")
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkSoft)
                            .multilineTextAlignment(.center)
                        Button {
                            openEditor()
                        } label: {
                            Text("添加测量")
                                .font(AppTypography.bodyLarge.weight(.semibold))
                                .foregroundStyle(AppColors.milk)
                                .padding(.horizontal, 44)
                                .padding(.vertical, 13)
                                .background(AppColors.coral, in: Capsule())
                        }
                        .buttonStyle(.plain)
                        .padding(.bottom, AppSpacing.small)
                    }
                    .frame(maxWidth: .infinity)
                } else {
                    SegmentedPill(items: ["体重", "身高", "头围"], selected: $selectedMetric)
                        .padding(.horizontal, AppSpacing.small)

                    GrowthChartView(
                        records: store.currentBabyGrowthRecords,
                        metric: selectedMetric,
                        birthDate: store.baby.birthDate,
                        babySex: store.baby.sex
                    )
                    .frame(height: 248)

                    Text("阴影为 WHO 生长标准 P3–P97 参考带（\(store.baby.sex.contains("女") ? "女宝" : "男宝")），虚线为中位数；仅供参考，评估请咨询儿保医生。")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                        .fixedSize(horizontal: false, vertical: true)

                    HStack(spacing: AppSpacing.regular) {
                        metricCard(title: "体重", value: formatted(store.latestGrowthRecord?.weight), unit: "kg", icon: "heart.fill", tint: AppColors.blush, color: AppColors.coral)
                        metricCard(title: "身高", value: formatted(store.latestGrowthRecord?.height), unit: "cm", icon: "shield.fill", tint: AppColors.mistBlue, color: AppColors.blueInk)
                        metricCard(title: "头围", value: formatted(store.latestGrowthRecord?.head), unit: "cm", icon: "leaf.fill", tint: AppColors.grass, color: AppColors.inkGreen)
                    }

                    HStack {
                        Image(systemName: "clock")
                            .font(.system(size: 15, weight: .regular))
                            .foregroundStyle(AppColors.inkSoft)
                        Text("最近一次记录：\(store.latestGrowthRecord?.measuredAt ?? "")")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                        Spacer()
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var historySection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.regular) {
            SectionTitleView(title: "测量历史")
            ForEach(store.currentBabyGrowthRecords.reversed()) { record in
                Button {
                    openEditor(record)
                } label: {
                    GrowthHistoryRow(record: record)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.plain)
                .contextMenu {
                    Button("编辑") {
                        openEditor(record)
                    }
                    Button("删除", role: .destructive) {
                        deleteCandidate = record
                    }
                }
                .accessibilityHint("长按可编辑或删除")
            }
        }
    }

    /// 健康观察入口：黄疸/体温/用药，摘要显示最近一条。
    private var healthObservationEntry: some View {
        NavigationLink {
            HealthObservationView()
        } label: {
            WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) {
                HStack(spacing: AppSpacing.medium) {
                    Image(systemName: "stethoscope")
                        .font(.system(size: 26, weight: .regular))
                        .foregroundStyle(AppColors.coral)
                        .frame(width: 48, height: 48)
                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("健康观察")
                            .font(AppTypography.sectionTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        Text(healthEntrySubtitle)
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkSoft)
                            .lineLimit(1)
                    }
                    Spacer(minLength: 0)
                    Image(systemName: "chevron.right")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(AppColors.inkSoft)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .buttonStyle(.plain)
    }

    private var healthEntrySubtitle: String {
        guard let latest = store.healthObservations.first else {
            return "黄疸 · 体温 · 维D用药"
        }
        return "最近：\(latest.kind) \(latest.summaryText)"
    }

    @ViewBuilder
    private var vaccineBookEntry: some View {
        if let onOpenVaccineBook {
            Button {
                onOpenVaccineBook()
            } label: {
                vaccineBookCard
            }
            .buttonStyle(.plain)
        } else {
            NavigationLink {
                VaccineView()
            } label: {
                vaccineBookCard
            }
            .buttonStyle(.plain)
        }
    }

    private var vaccineBookCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                HStack(alignment: .center, spacing: AppSpacing.medium) {
                    ZStack {
                        Image(systemName: "shield.fill")
                            .font(.system(size: 34, weight: .regular))
                            .foregroundStyle(AppColors.sage)
                        Image(systemName: "plus")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundStyle(AppColors.milk)
                    }
                    .frame(width: 48, height: 48)

                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("宝宝疫苗本")
                            .font(AppTypography.sectionTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        vaccineSubtitleText
                            .font(AppTypography.body)
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    Spacer(minLength: 0)
                }

                if !store.vaccineRecords.isEmpty {
                    HStack(spacing: AppSpacing.regular) {
                        vaccineBookStat(
                            title: "已接种",
                            value: "\(administeredVaccineCount)",
                            icon: "checkmark.shield.fill",
                            tint: AppColors.grass,
                            color: AppColors.inkGreen
                        )
                        vaccineBookStat(
                            title: "待接种",
                            value: "\(pendingVaccineCount)",
                            icon: "syringe.fill",
                            tint: AppColors.blush,
                            color: AppColors.coral
                        )
                    }
                }

                Divider().opacity(0.35)

                HStack(spacing: AppSpacing.tiny) {
                    Text(store.vaccineRecords.isEmpty ? "创建疫苗本".localizedText : "打开疫苗本".localizedText)
                        .font(AppTypography.body.weight(.semibold))
                    Image(systemName: "chevron.right")
                        .font(.system(size: 13, weight: .semibold))
                }
                .foregroundStyle(AppColors.inkGreen)
                .frame(maxWidth: .infinity, alignment: .trailing)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(store.vaccineRecords.isEmpty ? "还没有建立宝宝疫苗本" : AppLocalization.format("宝宝疫苗本，已接种 %d 针，待接种 %d 针", administeredVaccineCount, pendingVaccineCount))
    }

    /// “下一针：脊灰疫苗 · 2026.08.30”——疫苗名用主题绿，其余淡墨。
    private var vaccineSubtitleText: Text {
        guard !store.vaccineRecords.isEmpty else {
            return Text("还没有建立宝宝疫苗本".localizedText)
                .foregroundColor(AppColors.inkSoft)
        }
        guard let nextVaccine = store.nextVaccine else {
            return Text("当前没有待接种记录。".localizedText)
                .foregroundColor(AppColors.inkSoft)
        }
        return Text("下一针：".localizedText).foregroundColor(AppColors.inkSoft)
            + Text(nextVaccine.title.localizedText).foregroundColor(AppColors.sage)
            + Text(" · " + vaccineDueText(nextVaccine)).foregroundColor(AppColors.inkSoft)
    }

    private func vaccineBookStat(title: String, value: String, icon: String, tint: Color, color: Color) -> some View {
        VStack(spacing: AppSpacing.small) {
            Image(systemName: icon)
                .font(.system(size: 24, weight: .regular))
                .foregroundStyle(color)
            Text(title.localizedText)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.ink)
            HStack(alignment: .firstTextBaseline, spacing: 2) {
                Text(value)
                    .font(AppTypography.largeNumber)
                    .foregroundStyle(color)
                Text("针".localizedText)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.ink)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, AppSpacing.regular)
        .background(tint.opacity(0.45), in: RoundedRectangle(cornerRadius: AppShapes.cardRadius, style: .continuous))
    }

    private var administeredVaccineCount: Int {
        store.vaccineRecords.filter(\.isAdministered).count
    }

    private var pendingVaccineCount: Int {
        store.vaccineRecords.filter { !$0.isAdministered }.count
    }

    private var vaccineBookSubtitle: String {
        guard !store.vaccineRecords.isEmpty else {
            return "还没有建立宝宝疫苗本".localizedText
        }

        guard let nextVaccine = store.nextVaccine else {
            return "当前没有待接种记录。".localizedText
        }

        return "下一针：".localizedText + nextVaccine.title.localizedText + " · " + vaccineDueText(nextVaccine)
    }

    private func vaccineDueText(_ record: VaccineRecord) -> String {
        // 参考稿显示具体日期（2026.08.30），有日期用日期，没有再退回“N天后”。
        if !record.dueText.isEmpty {
            return record.dueText
        }
        let unit = store.vaccineDueUnit(record)
        if unit == "今天" {
            return unit.localizedText
        }
        return store.vaccineDueValue(record) + unit.localizedText
    }

    private func openEditor(_ record: GrowthRecord? = nil) {
        editingRecord = record
        isEditorPresented = true
    }

    private func formatted(_ value: Double?) -> String {
        guard let value, value > 0 else { return "--" }
        return value.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(value)) : String(format: "%.1f", value)
    }

    private func metricCard(title: String, value: String, unit: String, icon: String, tint: Color, color: Color) -> some View {
        WatercolorCard(tint: tint, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.medium) {
            VStack(spacing: AppSpacing.small) {
                Label(title, systemImage: icon)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkGreen)
                    .lineLimit(1)
                HStack(alignment: .firstTextBaseline, spacing: 2) {
                    Text(value)
                        .font(AppTypography.largeNumber)
                        .foregroundStyle(color)
                        .lineLimit(1)
                        .minimumScaleFactor(0.55)
                    Text(unit)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.ink)
                        .layoutPriority(1)
                }
            }
            .frame(maxWidth: .infinity)
        }
    }
}

struct MonthlyReportDetailView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var selectedMonth = Date()

    private var report: MonthlyReportSnapshot {
        store.monthlyReport(for: selectedMonth)
    }

    var body: some View {
        ScreenScaffold(title: "月度报告", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    monthSwitcher
                    MonthlyReportCard(report: report)
                    sourceSummary
                    if report.recordCount == 0 {
                        emptyState
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
    }

    private var monthSwitcher: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            HStack(spacing: AppSpacing.medium) {
                monthArrowButton(symbol: "chevron.left", enabled: true) {
                    shiftMonth(-1)
                }
                .accessibilityLabel("上个月")

                VStack(spacing: AppSpacing.tiny) {
                    Text(report.monthTitle)
                        .font(AppTypography.sectionTitle)
                        .foregroundStyle(AppColors.inkGreen)
                    Text("汇总账号中的真实记录")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                }
                .frame(maxWidth: .infinity)

                monthArrowButton(symbol: "chevron.right", enabled: canMoveToNextMonth) {
                    shiftMonth(1)
                }
                .disabled(!canMoveToNextMonth)
                .accessibilityLabel("下个月")
            }
        }
    }

    /// 月份切换箭头：cream 圆底次按钮，与 GrowthEditorSheet 的 stepper 按钮同款。
    private func monthArrowButton(symbol: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: symbol)
                .font(.system(size: 16, weight: .bold))
                .foregroundStyle(AppColors.coral.opacity(enabled ? 1 : 0.35))
                .frame(width: 44, height: 44)
                .background {
                    Circle()
                        .fill(AppColors.cream)
                        .overlay {
                            Circle().stroke(AppColors.softStroke.opacity(0.4), lineWidth: 1)
                        }
                        .frame(width: 38, height: 38)
                }
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    private var sourceSummary: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                HStack(spacing: AppSpacing.small) {
                    Image(systemName: "info.circle")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(AppColors.inkSoft)
                    Text("原始记录来源")
                        .font(AppTypography.cardTitle)
                        .foregroundStyle(AppColors.inkGreen)
                }
                Text("喂养、喝水、睡眠、排便、照片、成长指标、纪念日和疫苗提醒都来自原始记录。要修改内容，请回到对应页面编辑原始记录。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var emptyState: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(spacing: AppSpacing.small) {
                AssetWatercolorImage(name: AppAssets.cakeIcon, mode: .multiply)
                    .frame(width: 54, height: 48)
                Text("这个月记录还不多")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                Text("报告不会补写不存在的数据。等多记几次后，这里会慢慢长出月度回顾。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity)
        }
    }

    private var canMoveToNextMonth: Bool {
        let currentMonth = Calendar.current.dateComponents([.year, .month], from: Date())
        let selected = Calendar.current.dateComponents([.year, .month], from: selectedMonth)
        return selected.year != currentMonth.year || selected.month != currentMonth.month
    }

    private func shiftMonth(_ value: Int) {
        guard value < 0 || canMoveToNextMonth else { return }
        selectedMonth = Calendar.current.date(byAdding: .month, value: value, to: selectedMonth) ?? selectedMonth
    }
}

/// 生长曲线：真实月龄横轴 + WHO P3–P97 参考带 + P50 中位线。
/// 回答“我娃在什么水平”，而不是只画自身数值的孤立折线。
private struct GrowthChartView: View {
    let records: [GrowthRecord]
    let metric: String
    let birthDate: Date
    let babySex: String

    private struct DataPoint: Identifiable {
        let id: UUID
        let ageMonths: Double
        let value: Double
    }

    var body: some View {
        if dataPoints.isEmpty {
            Text("添加\(metric)记录后会在这里看到变化")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.inkGreen)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else {
            Chart {
                ForEach(referencePoints, id: \.month) { point in
                    AreaMark(
                        x: .value("月龄", Double(point.month)),
                        yStart: .value("P3", point.p3),
                        yEnd: .value("P97", point.p97)
                    )
                    .foregroundStyle(lineColor.opacity(0.14))

                    LineMark(
                        x: .value("月龄", Double(point.month)),
                        y: .value("P50", point.p50),
                        series: .value("曲线", "P50")
                    )
                    .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [5, 6]))
                    .foregroundStyle(lineColor.opacity(0.45))
                }

                ForEach(dataPoints) { point in
                    LineMark(
                        x: .value("月龄", point.ageMonths),
                        y: .value(metric, point.value),
                        series: .value("曲线", "宝宝")
                    )
                    .lineStyle(StrokeStyle(lineWidth: 3, lineCap: .round, lineJoin: .round))
                    .foregroundStyle(lineColor)

                    PointMark(
                        x: .value("月龄", point.ageMonths),
                        y: .value(metric, point.value)
                    )
                    .symbolSize(70)
                    .foregroundStyle(lineColor)
                }
            }
            .chartXScale(domain: 0...windowMaxMonth)
            .chartYScale(domain: yDomain)
            .chartXAxis {
                AxisMarks(values: xAxisTicks) { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4, 6]))
                        .foregroundStyle(AppColors.softStroke.opacity(0.4))
                    AxisValueLabel {
                        if let month = value.as(Double.self) {
                            Text("\(Int(month))月")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.inkSoft)
                        }
                    }
                }
            }
            .chartYAxis {
                AxisMarks(position: .leading) { value in
                    AxisGridLine(stroke: StrokeStyle(lineWidth: 0.5, dash: [4, 6]))
                        .foregroundStyle(AppColors.softStroke.opacity(0.4))
                    AxisValueLabel {
                        if let number = value.as(Double.self) {
                            Text(number.formatted(.number.precision(.fractionLength(0...1))))
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.inkSoft)
                        }
                    }
                }
            }
            .accessibilityLabel("\(metric)生长曲线，含 WHO 参考带")
        }
    }

    private var whoMetric: WHOGrowthReference.Metric {
        switch metric {
        case "身高": .height
        case "头围": .head
        default: .weight
        }
    }

    private var referencePoints: [WHOGrowthReference.Point] {
        WHOGrowthReference.points(metric: whoMetric, sex: .init(babySex: babySex))
            .filter { Double($0.month) <= windowMaxMonth }
    }

    private var dataPoints: [DataPoint] {
        records.compactMap { record in
            let value = value(for: record)
            guard value > 0,
                  let measuredDate = BabyRecordStore.date(fromDateString: record.measuredAt) else {
                return nil
            }
            let days = Calendar.current.dateComponents([.day], from: birthDate, to: measuredDate).day ?? 0
            return DataPoint(id: record.id, ageMonths: max(0, Double(days) / 30.4375), value: value)
        }
        .sorted { $0.ageMonths < $1.ageMonths }
    }

    /// 横轴窗口：至少看到 6 个月，随宝宝月龄扩展，上限 24 个月。
    private var windowMaxMonth: Double {
        let maxDataAge = dataPoints.map(\.ageMonths).max() ?? 0
        return min(24, max(6, (maxDataAge + 1.5).rounded(.up)))
    }

    private var xAxisTicks: [Double] {
        let step: Double = windowMaxMonth > 12 ? 6 : 2
        return Array(stride(from: 0, through: windowMaxMonth, by: step))
    }

    private var yDomain: ClosedRange<Double> {
        let referenceValues = referencePoints.flatMap { [$0.p3, $0.p97] }
        let dataValues = dataPoints.map(\.value)
        let allValues = referenceValues + dataValues
        guard let minValue = allValues.min(), let maxValue = allValues.max() else {
            return 0...10
        }
        let padding = max((maxValue - minValue) * 0.08, 0.5)
        return (minValue - padding)...(maxValue + padding)
    }

    private func value(for record: GrowthRecord) -> Double {
        switch metric {
        case "身高":
            record.height
        case "头围":
            record.head
        default:
            record.weight
        }
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
}

private struct MonthlyReportCard: View {
    let report: MonthlyReportSnapshot

    var body: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                HStack {
                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        HStack(spacing: AppSpacing.small) {
                            Image(systemName: "chart.bar.fill")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundStyle(AppColors.sage)
                            Text("本月成长小报")
                                .font(AppTypography.sectionTitle)
                                .foregroundStyle(AppColors.inkGreen)
                        }
                        Text("\(report.monthTitle.isEmpty ? "本月" : report.monthTitle) · 基于当前记录生成")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                    }
                    Spacer()
                    AssetWatercolorImage(name: AppAssets.cakeIcon, mode: .multiply)
                        .frame(width: 46, height: 40)
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: AppSpacing.regular) {
                    reportMetric(title: "喂养", value: "\(report.feedingCount)次 / \(report.milkAmountML)ml", icon: "drop.fill", tint: AppColors.blush, color: AppColors.coral)
                    reportMetric(title: "睡眠", value: report.sleepDurationText, icon: "moon.fill", tint: AppColors.mistBlue, color: AppColors.blueInk)
                    reportMetric(title: "排便", value: "\(report.diaperCount)次", icon: "leaf.fill", tint: AppColors.grass, color: AppColors.inkGreen)
                    reportMetric(title: "照片", value: "\(report.photoCount)张", icon: "photo.fill", tint: AppColors.cream, color: AppColors.coral)
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

    /// 指标小瓦片：与 growthCard 的 metricCard / vaccineBookStat 同一族（低饱和 tint 底 + 主题色数值）。
    private func reportMetric(title: String, value: String, icon: String, tint: Color, color: Color) -> some View {
        VStack(alignment: .leading, spacing: AppSpacing.tiny) {
            Label(title, systemImage: icon)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkGreen)
                .lineLimit(1)
            Text(value)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(color)
                .lineLimit(2)
                .minimumScaleFactor(0.78)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AppSpacing.regular)
        .background(tint.opacity(0.45), in: RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous))
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
            Image(systemName: "ruler.fill")
                .font(.system(size: 20, weight: .semibold))
                .foregroundStyle(AppColors.blueInk)
                .frame(width: 36, height: 36)
            VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                Text(record.measuredAt.isEmpty ? record.month : record.measuredAt)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                Text(measurementSummary)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.ink)
            }
            Spacer()
            if let headSummary {
                Text(headSummary)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.ink)
            }
        }
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, 11)
        .background {
            CardBackground(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius)
        }
    }

    private var measurementSummary: String {
        let parts = [
            record.weight > 0 ? "体重 \(display(record.weight))kg" : nil,
            record.height > 0 ? "身高 \(display(record.height))cm" : nil
        ].compactMap { $0 }

        return parts.isEmpty ? "这次只记录了日期" : parts.joined(separator: "  ")
    }

    private var headSummary: String? {
        record.head > 0 ? "头围 \(display(record.head))cm" : nil
    }

    private func display(_ value: Double) -> String {
        value.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(value)) : String(format: "%.1f", value)
    }
}

/// 「记录身高体重」编辑表单：分行卡片式布局。
/// 时间行（内联日期选择）＋ 体重/身高/头围三个 stepper 行 ＋ 备注卡 ＋ 底部珊瑚色保存胶囊。
/// 三项数值都随 stepper 保存（有默认值即有效值），不再有“至少填一项”的报错分支。
private struct GrowthEditorSheet: View {
    let record: GrowthRecord?
    let onSave: (GrowthRecord) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var measuredAt: Date
    @State private var weight: Double
    @State private var height: Double
    @State private var head: Double
    @State private var note: String
    @State private var errorMessage: String?
    @State private var showsDatePicker = false

    private static let weightRange: ClosedRange<Double> = 1.0...30.0
    private static let heightRange: ClosedRange<Double> = 30.0...130.0
    private static let headRange: ClosedRange<Double> = 25.0...60.0
    private static let noteLimit = 100

    private static let displayDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "yyyy年M月d日"
        return formatter
    }()

    /// 新建时用 `latest`（store 最近一条成长记录）的对应值当默认值；没有历史则退回固定默认。
    init(record: GrowthRecord?, latest: GrowthRecord? = nil, onSave: @escaping (GrowthRecord) -> Bool) {
        self.record = record
        self.onSave = onSave
        _measuredAt = State(initialValue: record.flatMap { BabyRecordStore.date(fromDateString: $0.measuredAt) } ?? Date())
        _weight = State(initialValue: Self.initialValue(record?.weight, latest: latest?.weight, fallback: 4.0, in: Self.weightRange))
        _height = State(initialValue: Self.initialValue(record?.height, latest: latest?.height, fallback: 55.0, in: Self.heightRange))
        _head = State(initialValue: Self.initialValue(record?.head, latest: latest?.head, fallback: 37.0, in: Self.headRange))
        _note = State(initialValue: record?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.medium) {
                    dateCard
                    stepperRow(icon: "scalemass", iconColor: AppColors.inkGreen, title: "体重", value: $weight, step: 0.1, range: Self.weightRange, unit: "kg")
                    stepperRow(icon: "ruler", iconColor: AppColors.inkGreen, title: "身高", value: $height, step: 0.5, range: Self.heightRange, unit: "cm")
                    stepperRow(icon: "face.smiling", iconColor: AppColors.peach, title: "头围", value: $head, step: 0.5, range: Self.headRange, unit: "cm")
                    noteCard

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
                Button {
                    save()
                } label: {
                    Text("保存记录")
                        .font(AppTypography.bodyLarge.weight(.semibold))
                        .foregroundStyle(AppColors.milk)
                        .frame(maxWidth: .infinity)
                        .frame(height: 52)
                        .background(AppColors.coral, in: Capsule())
                }
                .buttonStyle(.plain)
                .padding(.horizontal, AppSpacing.large)
                .padding(.vertical, AppSpacing.small)
                .background(.ultraThinMaterial)
            }
            .navigationTitle(record == nil ? "记录身高体重" : "编辑测量")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("保存") {
                        save()
                    }
                    .foregroundStyle(AppColors.coral)
                }
            }
        }
    }

    // MARK: - 行卡

    private var dateCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: 0) {
            VStack(spacing: 0) {
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        showsDatePicker.toggle()
                    }
                } label: {
                    HStack(spacing: AppSpacing.small) {
                        Image(systemName: "calendar")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundStyle(AppColors.inkGreen)
                            .frame(width: 26)
                        Text("时间")
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkGreen)
                        Spacer(minLength: AppSpacing.small)
                        Text(Self.displayDateFormatter.string(from: measuredAt))
                            .font(AppTypography.readableBody)
                            .foregroundStyle(AppColors.ink)
                        Image(systemName: "chevron.down")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(AppColors.inkSoft)
                            .rotationEffect(.degrees(showsDatePicker ? 180 : 0))
                    }
                    .padding(AppSpacing.medium)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("测量时间")
                .accessibilityValue(Self.displayDateFormatter.string(from: measuredAt))

                if showsDatePicker {
                    DatePicker("测量时间", selection: $measuredAt, in: ...Date(), displayedComponents: [.date])
                        .datePickerStyle(.graphical)
                        .labelsHidden()
                        .tint(AppColors.coral)
                        .padding(.horizontal, AppSpacing.small)
                        .padding(.bottom, AppSpacing.small)
                }
            }
        }
    }

    private func stepperRow(icon: String, iconColor: Color, title: String, value: Binding<Double>, step: Double, range: ClosedRange<Double>, unit: String) -> some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            HStack(spacing: AppSpacing.small) {
                Image(systemName: icon)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(iconColor)
                    .frame(width: 26)
                Text(title)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.inkGreen)

                Spacer(minLength: AppSpacing.small)

                stepButton(symbol: "minus", enabled: value.wrappedValue > range.lowerBound + 0.001) {
                    adjust(value, by: -step, in: range)
                }
                .accessibilityLabel("减少\(title)")

                HStack(alignment: .firstTextBaseline, spacing: 3) {
                    Text(String(format: "%.1f", value.wrappedValue))
                        .font(AppTypography.largeNumber)
                        .foregroundStyle(AppColors.ink)
                        .lineLimit(1)
                        .minimumScaleFactor(0.55)
                    Text(unit)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                }
                .frame(minWidth: 88)
                .accessibilityElement(children: .combine)
                .accessibilityLabel(title)
                .accessibilityValue("\(String(format: "%.1f", value.wrappedValue)) \(unit)")

                stepButton(symbol: "plus", enabled: value.wrappedValue < range.upperBound - 0.001) {
                    adjust(value, by: step, in: range)
                }
                .accessibilityLabel("增加\(title)")
            }
            .frame(maxWidth: .infinity)
        }
    }

    private func stepButton(symbol: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: symbol)
                .font(.system(size: 16, weight: .bold))
                .foregroundStyle(AppColors.coral.opacity(enabled ? 1 : 0.35))
                .frame(width: 44, height: 44)
                .background {
                    Circle()
                        .fill(AppColors.cream)
                        .overlay {
                            Circle().stroke(AppColors.softStroke.opacity(0.4), lineWidth: 1)
                        }
                        .frame(width: 38, height: 38)
                }
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(!enabled)
    }

    private var noteCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                HStack(spacing: AppSpacing.small) {
                    Image(systemName: "pencil")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundStyle(AppColors.inkGreen)
                        .frame(width: 26)
                    Text("备注（可选）")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.inkGreen)
                }
                TextField("如：宝宝状态等", text: $note, axis: .vertical)
                    .lineLimit(2...4)
                    .font(AppTypography.readableBody)
                    .foregroundStyle(AppColors.ink)
                    .onChange(of: note) { _, newValue in
                        if newValue.count > Self.noteLimit {
                            note = String(newValue.prefix(Self.noteLimit))
                        }
                    }
                Text("\(note.count)/\(Self.noteLimit)")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .frame(maxWidth: .infinity, alignment: .trailing)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    // MARK: - 数值与保存

    private func adjust(_ value: Binding<Double>, by step: Double, in range: ClosedRange<Double>) {
        let next = ((value.wrappedValue + step) * 10).rounded() / 10
        value.wrappedValue = min(max(next, range.lowerBound), range.upperBound)
    }

    /// 编辑时用记录值（>0 才算有效）；新建时用最近一条记录的对应值；再退回固定默认，并夹进合法范围。
    private static func initialValue(_ recordValue: Double?, latest: Double?, fallback: Double, in range: ClosedRange<Double>) -> Double {
        let base = [recordValue, latest].compactMap { $0 }.first { $0 > 0 } ?? fallback
        let clamped = min(max(base, range.lowerBound), range.upperBound)
        return (clamped * 10).rounded() / 10
    }

    private func save() {
        errorMessage = nil
        var saved = record ?? GrowthRecord(
            month: BabyRecordStore.monthString(from: measuredAt),
            weight: weight,
            height: height,
            head: head,
            measuredAt: BabyRecordStore.dateString(from: measuredAt)
        )
        saved.month = BabyRecordStore.monthString(from: measuredAt)
        saved.weight = weight
        saved.height = height
        saved.head = head
        saved.measuredAt = BabyRecordStore.dateString(from: measuredAt)
        let trimmedNote = note.trimmingCharacters(in: .whitespacesAndNewlines)
        saved.note = trimmedNote.isEmpty ? nil : trimmedNote
        if onSave(saved) {
            dismiss()
        } else {
            errorMessage = "保存失败，请稍后再试。输入已保留。"
        }
    }
}
