import SwiftUI

struct MilestoneView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var editingMilestone: Milestone?
    @State private var deleteCandidate: Milestone?

    var body: some View {
        ScreenScaffold(title: "纪念日", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    nextMilestoneCard
                    automaticMilestoneSection
                    manualMilestoneSection
                    addMilestoneButton
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            MilestoneEditorSheet(milestone: editingMilestone) { milestone in
                store.upsert(milestone)
            }
            .presentationDetents([.medium, .large])
        }
        .alert("删除这个纪念日？", isPresented: deleteAlertBinding) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteMilestone(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text("只会删除这个手动纪念日，不影响宝宝档案。")
        }
    }

    /// 倒计时主卡：低饱和奶白底 + 珊瑚色大数字，与成长页 growthCard 同一张“皮”。
    private var nextMilestoneCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                HStack(spacing: AppSpacing.small) {
                    Image(systemName: "gift.fill")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(AppColors.coral)
                    Text("下一个纪念日")
                        .font(AppTypography.sectionTitle)
                        .foregroundStyle(AppColors.inkGreen)
                }

                HStack(alignment: .center, spacing: AppSpacing.medium) {
                    VStack(alignment: .leading, spacing: AppSpacing.small) {
                        Text(nextMilestoneTitle)
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                            .fixedSize(horizontal: false, vertical: true)
                        HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                            Text(store.nextAutomaticMilestone == nil ? "成长" : "还剩")
                                .font(AppTypography.bodyLarge)
                            Text("\(store.nextAutomaticMilestone?.daysRemaining ?? store.currentBabyDaysSinceBirth)")
                                .font(AppTypography.largeNumber)
                                .foregroundStyle(AppColors.coral)
                            Text("天")
                                .font(AppTypography.bodyLarge)
                        }
                        .foregroundStyle(AppColors.inkGreen)
                        Text("按宝宝出生第 \(store.currentBabyDaysSinceBirth) 天计算")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                    }
                    Spacer(minLength: 0)
                    AssetWatercolorImage(name: AppAssets.cakeIcon, mode: .multiply)
                        .frame(width: 96, height: 84)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    /// 自动纪念节点：行卡样式与成长页测量历史一致（cream 行卡 + 名称主、日期辅）。
    private var automaticMilestoneSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.regular) {
            SectionTitleView(title: "自动纪念节点")
            ForEach(store.automaticMilestones) { milestone in
                HStack(spacing: AppSpacing.medium) {
                    Image(systemName: milestone.isReached ? "checkmark.circle.fill" : "calendar")
                        .font(.system(size: 20, weight: .semibold))
                        .foregroundStyle(milestone.isReached ? AppColors.sage : AppColors.coral)
                        .frame(width: 36, height: 36)
                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text(milestone.title.localizedText)
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                        Text(BabyRecordStore.displayDateString(from: milestone.date))
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                    }
                    Spacer()
                    Text(milestone.isReached ? "已到达".localizedText : AppLocalization.format("%d天后", milestone.daysRemaining))
                        .font(AppTypography.caption)
                        .foregroundStyle(milestone.isReached ? AppColors.sage : AppColors.coral)
                }
                .padding(.horizontal, AppSpacing.medium)
                .padding(.vertical, 11)
                .background {
                    CardBackground(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius)
                }
            }
        }
    }

    /// 手动纪念日列表：行卡样式与成长页测量历史一致；
    /// 点击行进入编辑，长按行弹出“编辑/删除”菜单（与喂养历史行同款，删除仍走确认弹窗）。
    private var manualMilestoneSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.regular) {
            SectionTitleView(title: "我的纪念日")
            if store.activeMilestones.isEmpty {
                WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius) {
                    VStack(spacing: AppSpacing.small) {
                        Text("还没有手动添加的纪念日")
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                        Text("第一次翻身、第一次叫妈妈，都值得记下来")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                }
            } else {
                ForEach(store.activeMilestones) { item in
                    Button {
                        openEditor(item)
                    } label: {
                        milestoneRow(item)
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.plain)
                    .accessibilityHint("打开编辑，长按可删除")
                    .contextMenu {
                        Button("编辑") {
                            openEditor(item)
                        }
                        Button("删除", role: .destructive) {
                            deleteCandidate = item
                        }
                    }
                }
            }
        }
    }

    private func milestoneRow(_ item: Milestone) -> some View {
        HStack(spacing: AppSpacing.medium) {
            AssetWatercolorImage(name: item.icon, mode: .multiply)
                .frame(width: 40, height: 36)
            VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                Text(item.title)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                    .lineLimit(1)
                Text(displayDate(for: item))
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
            }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, 11)
        .background {
            CardBackground(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius)
        }
    }

    /// 主按钮：实心珊瑚胶囊 + 奶白字，与成长页“添加测量”同款。
    private var addMilestoneButton: some View {
        Button {
            openEditor()
        } label: {
            HStack(spacing: AppSpacing.small) {
                Image(systemName: "plus")
                    .font(.system(size: 16, weight: .bold))
                Text("添加纪念日")
                    .font(AppTypography.bodyLarge.weight(.semibold))
            }
            .foregroundStyle(AppColors.milk)
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .background(AppColors.coral, in: Capsule())
        }
        .buttonStyle(.plain)
    }

    private var nextMilestoneTitle: String {
        guard let milestone = store.nextAutomaticMilestone else {
            return "已经走过三周岁".localizedText
        }
        return AppLocalization.format("即将到来：%@", milestone.title.localizedText)
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

    private func openEditor(_ milestone: Milestone? = nil) {
        editingMilestone = milestone
        isEditorPresented = true
    }

    /// 相对文案（今天/昨天）在渲染时实时计算，绝不落盘。
    private func displayDate(for milestone: Milestone) -> String {
        guard let date = BabyRecordStore.milestoneDate(milestone) else {
            return milestone.date
        }
        return BabyRecordStore.displayDateString(from: date)
    }
}

/// 纪念日编辑表单：分行卡片式布局，与成长页 GrowthEditorSheet 同一套语言。
/// 名称行 ＋ 日期行（收起显示日期文本，点击展开 .graphical 日历，仅日期无时间）＋ 备注卡 ＋ 底部珊瑚色保存胶囊。
private struct MilestoneEditorSheet: View {
    let milestone: Milestone?
    let onSave: (Milestone) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var title: String
    @State private var date: Date
    @State private var note: String
    @State private var errorMessage: String?
    @State private var showsDatePicker = false

    private static let displayDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "yyyy年M月d日"
        return formatter
    }()

    init(milestone: Milestone?, onSave: @escaping (Milestone) -> Bool) {
        self.milestone = milestone
        self.onSave = onSave
        _title = State(initialValue: milestone?.title ?? "")
        _date = State(initialValue: milestone.flatMap(BabyRecordStore.milestoneDate) ?? Date())
        _note = State(initialValue: milestone?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.medium) {
                    titleCard
                    dateCard
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
                    Text("保存纪念日")
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
            .navigationTitle(milestone == nil ? "添加纪念日" : "编辑纪念日")
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

    private var titleCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            HStack(spacing: AppSpacing.small) {
                Image(systemName: "star.fill")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(AppColors.inkGreen)
                    .frame(width: 26)
                Text("名称")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.inkGreen)
                TextField("如：第一次翻身", text: $title)
                    .font(AppTypography.readableBody)
                    .foregroundStyle(AppColors.ink)
                    .multilineTextAlignment(.trailing)
                    .submitLabel(.done)
            }
            .frame(maxWidth: .infinity)
        }
    }

    /// 日期行卡：收起时显示日期文本＋chevron，点击内联展开 .graphical 日历；纪念日只需日期。
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
                        Text("日期")
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkGreen)
                        Spacer(minLength: AppSpacing.small)
                        Text(Self.displayDateFormatter.string(from: date))
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
                .accessibilityLabel("纪念日日期")
                .accessibilityValue(Self.displayDateFormatter.string(from: date))

                if showsDatePicker {
                    DatePicker("纪念日日期", selection: $date, displayedComponents: [.date])
                        .datePickerStyle(.graphical)
                        .labelsHidden()
                        .tint(AppColors.coral)
                        .padding(.horizontal, AppSpacing.small)
                        .padding(.bottom, AppSpacing.small)
                }
            }
        }
    }

    private var noteCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                HStack(spacing: AppSpacing.small) {
                    Image(systemName: "pencil")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundStyle(AppColors.inkGreen)
                        .frame(width: 26)
                    Text("备注（可不填）")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.inkGreen)
                }
                TextField("如：当时的小故事", text: $note, axis: .vertical)
                    .lineLimit(2...4)
                    .font(AppTypography.readableBody)
                    .foregroundStyle(AppColors.ink)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    // MARK: - 保存

    private func save() {
        let trimmedTitle = title.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedTitle.isEmpty else {
            errorMessage = "请填写纪念日名称。"
            return
        }

        var saved = milestone ?? Milestone(
            title: trimmedTitle,
            date: BabyRecordStore.fullDisplayDateString(from: date),
            icon: AppAssets.milestoneMedalIcon
        )
        saved.title = trimmedTitle
        saved.date = BabyRecordStore.fullDisplayDateString(from: date)
        saved.occurredAt = date
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        if onSave(saved) {
            dismiss()
        } else {
            errorMessage = "保存失败，请稍后再试。输入已保留。"
        }
    }
}
