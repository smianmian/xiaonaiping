import SwiftUI

enum QuickRecordAction: CaseIterable, Identifiable {
    case feeding
    case sleep
    case diaper
    case photo
    case growth
    case milestone

    var id: String { title }

    var title: String {
        switch self {
        case .feeding: "喂养"
        case .sleep: "睡眠"
        case .diaper: "排便"
        case .photo: "照片"
        case .growth: "身高体重"
        case .milestone: "纪念日"
        }
    }

    var asset: String {
        switch self {
        case .feeding: AppAssets.bottleIcon
        case .sleep: AppAssets.moonIcon
        case .diaper: AppAssets.diaperIcon
        case .photo: AppAssets.cameraIcon
        case .growth: AppAssets.quickGrowthIcon
        case .milestone: AppAssets.milestoneMedalIcon
        }
    }

    var tint: Color {
        switch self {
        case .feeding: AppColors.cream
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
    let onClose: () -> Void

    private let columns = [
        GridItem(.flexible(), spacing: AppSpacing.medium),
        GridItem(.flexible(), spacing: AppSpacing.medium),
        GridItem(.flexible(), spacing: AppSpacing.medium)
    ]

    var body: some View {
        VStack(spacing: AppSpacing.large) {
            HStack {
                Spacer()
                Text("快速记录")
                    .font(AppTypography.navTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Spacer()
                Button(action: onClose) {
                    Image(systemName: "xmark")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(AppColors.inkGreen)
                        .frame(width: 42, height: 42)
                        .background {
                            Circle()
                                .fill(AppColors.milk.opacity(0.72))
                                .overlay {
                                    Circle().stroke(.white.opacity(0.65), lineWidth: 1)
                                }
                        }
                }
                .buttonStyle(.plain)
            }

            LazyVGrid(columns: columns, spacing: AppSpacing.medium) {
                ForEach(QuickRecordAction.allCases) { action in
                    Button {
                        onSelect(action)
                    } label: {
                        VStack(spacing: AppSpacing.regular) {
                            AssetWatercolorImage(name: action.asset, mode: .multiply)
                                .frame(width: 78, height: 76)
                            Text(action.title)
                                .font(AppTypography.bodyLarge)
                                .foregroundStyle(AppColors.ink)
                                .lineLimit(1)
                                .minimumScaleFactor(0.78)
                        }
                        .frame(maxWidth: .infinity)
                        .frame(height: 140)
                        .background {
                            CardBackground(tint: action.tint, cornerRadius: AppShapes.cardRadius)
                        }
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(.horizontal, AppSpacing.large)
        .padding(.top, AppSpacing.large)
        .padding(.bottom, AppSpacing.large)
        .background {
            UnevenRoundedRectangle(
                topLeadingRadius: AppShapes.sheetRadius,
                bottomLeadingRadius: AppShapes.sheetRadius,
                bottomTrailingRadius: AppShapes.sheetRadius,
                topTrailingRadius: AppShapes.sheetRadius,
                style: .continuous
            )
            .fill(AppColors.milk.opacity(0.86))
            .background {
                UnevenRoundedRectangle(
                    topLeadingRadius: AppShapes.sheetRadius,
                    bottomLeadingRadius: AppShapes.sheetRadius,
                    bottomTrailingRadius: AppShapes.sheetRadius,
                    topTrailingRadius: AppShapes.sheetRadius,
                    style: .continuous
                )
                .fill(.ultraThinMaterial)
            }
            .overlay {
                RoundedRectangle(cornerRadius: AppShapes.sheetRadius, style: .continuous)
                    .stroke(.white.opacity(0.72), lineWidth: 1)
            }
            .shadow(color: .black.opacity(0.16), radius: 28, y: -8)
        }
        .padding(.horizontal, AppSpacing.small)
    }
}
