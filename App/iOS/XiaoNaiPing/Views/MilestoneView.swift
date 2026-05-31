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
                    WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.largeCardRadius) {
                        HStack {
                            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                                Text("即将到来的纪念日：百天")
                                    .font(AppTypography.bodyLarge)
                                    .foregroundStyle(AppColors.inkGreen)
                                HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                                    Text("还剩")
                                        .font(AppTypography.bodyLarge)
                                    Text("\(store.hundredDaysRemaining)")
                                        .font(AppTypography.largeNumber)
                                        .foregroundStyle(AppColors.coral)
                                    Text("天")
                                        .font(AppTypography.bodyLarge)
                                }
                                .foregroundStyle(AppColors.inkGreen)
                                Text("按宝宝出生第 \(store.baby.daysSinceBirth) 天计算")
                                    .font(AppTypography.body)
                                    .foregroundStyle(AppColors.inkGreen)
                            }
                            Spacer()
                            AssetWatercolorImage(name: AppAssets.cakeIcon, mode: .multiply)
                                .frame(width: 126, height: 110)
                        }
                    }

                    HStack(alignment: .top, spacing: AppSpacing.medium) {
                        AssetWatercolorImage(name: AppAssets.plantTimeline, mode: .multiply)
                            .frame(width: 55)
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
                                                    .frame(width: 58, height: 52)
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
                                                .frame(width: 36, height: 36)
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
    let onSave: (Milestone) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var title: String
    @State private var date: Date
    @State private var note: String
    @State private var errorMessage: String?

    init(milestone: Milestone?, onSave: @escaping (Milestone) -> Void) {
        self.milestone = milestone
        self.onSave = onSave
        _title = State(initialValue: milestone?.title ?? "")
        _date = State(initialValue: Date())
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
        onSave(saved)
        dismiss()
    }
}
