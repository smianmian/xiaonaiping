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
                    SectionTitleView(title: "我的纪念日")

                    HStack(alignment: .top, spacing: AppSpacing.medium) {
                        AssetWatercolorImage(name: AppAssets.plantTimeline, mode: .multiply)
                            .frame(width: 44)
                        VStack(spacing: AppSpacing.medium) {
                            if store.milestones.isEmpty {
                                WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
                                    Text("还没有手动添加的纪念日")
                                        .font(AppTypography.bodyLarge)
                                        .foregroundStyle(AppColors.inkGreen)
                                        .frame(maxWidth: .infinity)
                                }
                            } else {
                                ForEach(store.milestones) { item in
                                    HStack(spacing: AppSpacing.small) {
                                        Button {
                                            openEditor(item)
                                        } label: {
                                            HStack(spacing: AppSpacing.medium) {
                                                AssetWatercolorImage(name: item.icon, mode: .multiply)
                                                    .frame(width: 46, height: 42)
                                                Text(item.title)
                                                    .font(AppTypography.bodyLarge)
                                                    .foregroundStyle(AppColors.inkGreen)
                                                Spacer()
                                                Text(item.date)
                                                    .font(AppTypography.caption)
                                                    .foregroundStyle(AppColors.inkGreen)
                                            }
                                        }
                                        .buttonStyle(.plain)

                                        Button {
                                            deleteCandidate = item
                                        } label: {
                                            Image(systemName: "trash")
                                                .font(.system(size: 16, weight: .regular))
                                                .foregroundStyle(AppColors.coral)
                                                .frame(width: 44, height: 44)
                                                .background {
                                                    Circle().fill(AppColors.blush.opacity(0.5))
                                                }
                                        }
                                        .buttonStyle(.plain)
                                        .accessibilityLabel("删除纪念日")
                                    }
                                    .padding(.vertical, 6)
                                    Divider().opacity(0.28)
                                }
                            }
                        }
                    }

                    PrimaryWatercolorButton(title: "+ 添加纪念日") {
                        openEditor()
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            MilestoneEditorSheet(milestone: editingMilestone) { milestone in
                store.upsert(milestone)
            }
            .presentationDetents([.medium])
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

    private var nextMilestoneCard: some View {
        WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.largeCardRadius) {
            HStack {
                VStack(alignment: .leading, spacing: AppSpacing.medium) {
                    Text(nextMilestoneTitle)
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkGreen)
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
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.inkGreen)
                }
                Spacer()
                AssetWatercolorImage(name: AppAssets.cakeIcon, mode: .multiply)
                    .frame(width: 100, height: 88)
            }
        }
    }

    private var automaticMilestoneSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.regular) {
            SectionTitleView(title: "自动纪念节点")
            ForEach(store.automaticMilestones) { milestone in
                HStack(spacing: AppSpacing.medium) {
                    Image(systemName: milestone.isReached ? "checkmark.circle.fill" : "calendar")
                        .foregroundStyle(milestone.isReached ? AppColors.sage : AppColors.coral)
                        .frame(width: 28)
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
                .padding(.vertical, AppSpacing.regular)
                .background {
                    CardBackground(tint: AppColors.cream, cornerRadius: AppShapes.smallRadius)
                }
            }
        }
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
}

private struct MilestoneEditorSheet: View {
    let milestone: Milestone?
    let onSave: (Milestone) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var title: String
    @State private var date: Date
    @State private var note: String
    @State private var errorMessage: String?
    @State private var showsMoreDetails = false

    init(milestone: Milestone?, onSave: @escaping (Milestone) -> Bool) {
        self.milestone = milestone
        self.onSave = onSave
        _title = State(initialValue: milestone?.title ?? "")
        _date = State(initialValue: milestone.flatMap { BabyRecordStore.date(fromDisplayDateString: $0.date) } ?? Date())
        _note = State(initialValue: milestone?.note ?? "")
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: AppSpacing.large) {
                WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            TextField("纪念日名称", text: $title)
                                .textFieldStyle(.roundedBorder)
                            DatePicker("日期", selection: $date, displayedComponents: [.date])
                        }
                    }

                    WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius, padding: 0) {
                        Button {
                            withAnimation {
                                showsMoreDetails.toggle()
                            }
                        } label: {
                            HStack(spacing: AppSpacing.small) {
                                Image(systemName: showsMoreDetails ? "chevron.up" : "chevron.down")
                                Text("更多详情（可不填）")
                                Spacer(minLength: 0)
                                Text(showsMoreDetails ? "收起" : "添加备注")
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.inkSoft)
                            }
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkGreen)
                            .padding(.horizontal, AppSpacing.medium)
                            .padding(.vertical, AppSpacing.regular)
                        }
                        .buttonStyle(.plain)
                    }

                    if showsMoreDetails {
                        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
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

                PrimaryWatercolorButton(title: "保存纪念日") {
                    save()
                }
                Spacer()
            }
            .padding(AppSpacing.large)
            .background(PaperBackgroundView())
            .navigationTitle(milestone == nil ? "添加纪念日" : "编辑纪念日")
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
            errorMessage = "请填写纪念日名称。"
            return
        }

        var saved = milestone ?? Milestone(
            title: trimmedTitle,
            date: BabyRecordStore.displayDateString(from: date),
            icon: AppAssets.milestoneMedalIcon
        )
        saved.title = trimmedTitle
        saved.date = BabyRecordStore.displayDateString(from: date)
        saved.note = note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : note
        if onSave(saved) {
            dismiss()
        } else {
            errorMessage = "保存失败，请稍后再试。输入已保留。"
        }
    }
}
