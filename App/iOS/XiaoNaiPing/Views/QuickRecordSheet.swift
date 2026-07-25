import SwiftUI

enum QuickRecordAction: CaseIterable, Identifiable {
    case feeding
    case water
    case sleep
    case diaper
    case photo
    case growth
    case milestone

    var id: String { title }

    var title: String {
        switch self {
        case .feeding: "喂养"
        case .water: "喝水"
        case .sleep: "睡眠"
        case .diaper: "排便"
        case .photo: "照片"
        case .growth: "身高体重"
        case .milestone: "纪念日"
        }
    }

    var asset: String? {
        switch self {
        case .feeding: AppAssets.bottleIcon
        case .water: nil
        case .sleep: AppAssets.moonIcon
        case .diaper: AppAssets.diaperIcon
        case .photo: AppAssets.cameraIcon
        case .growth: AppAssets.quickGrowthIcon
        case .milestone: AppAssets.milestoneMedalIcon
        }
    }

    var systemIcon: String? {
        switch self {
        case .water: "drop.fill"
        default: nil
        }
    }

    var tint: Color {
        switch self {
        case .feeding: AppColors.cream
        case .water: AppColors.mistBlue
        case .sleep: AppColors.mistBlue
        case .diaper: AppColors.grass
        case .photo: AppColors.blush
        case .growth: Color(red: 0.925, green: 0.885, blue: 0.955)
        case .milestone: Color(red: 1.0, green: 0.925, blue: 0.840)
        }
    }
}

struct QuickRecordSheet: View {
    let onSelect: (QuickRecordAction) -> Void

    @Environment(\.dismiss) private var dismiss

    private let primaryActions: [QuickRecordAction] = [
        .feeding, .sleep, .diaper, .water, .photo, .growth
    ]

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: AppSpacing.medium) {
                    Text("记下刚刚发生的事")
                        .font(AppTypography.sectionTitle)
                        .foregroundStyle(AppColors.inkGreen)

                    Text("选择记录类型后继续填写。")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)

                    ForEach(primaryActions) { action in
                        Button {
                            onSelect(action)
                            dismiss()
                        } label: {
                            HStack(spacing: AppSpacing.regular) {
                                actionIcon(for: action)
                                    .frame(width: 32, height: 32)

                                Text(action.title)
                                    .font(AppTypography.bodyLarge)
                                    .foregroundStyle(AppColors.inkGreen)

                                Spacer(minLength: 0)

                                Image(systemName: "chevron.right")
                                    .font(.system(size: 13, weight: .semibold))
                                    .foregroundStyle(AppColors.inkSoft)
                            }
                            .padding(.horizontal, AppSpacing.medium)
                            .frame(maxWidth: .infinity, minHeight: 56)
                            .background {
                                RoundedRectangle(cornerRadius: AppShapes.cardRadius, style: .continuous)
                                    .fill(action.tint)
                            }
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("记录\(action.title)")
                        .accessibilityHint("打开\(action.title)表单")
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle("记录")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("关闭") {
                        dismiss()
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func actionIcon(for action: QuickRecordAction) -> some View {
        if let asset = action.asset {
            AssetWatercolorImage(name: asset, mode: .multiply)
        } else if let systemIcon = action.systemIcon {
            Image(systemName: systemIcon)
                .font(.system(size: 20, weight: .semibold))
                .foregroundStyle(AppColors.blueInk)
        }
    }
}
