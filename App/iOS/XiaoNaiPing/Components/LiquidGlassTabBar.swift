import SwiftUI

enum AppTab: String, CaseIterable, Identifiable {
    case home = "今天"
    case growth = "成长"
    case record = "记录"
    case profile = "设置"

    var id: String { rawValue }

    var iconAsset: String {
        switch self {
        case .home:
            AppAssets.tabHomeDrawing
        case .growth:
            AppAssets.quickGrowthIcon
        case .record:
            AppAssets.tabRecordDrawing
        case .profile:
            AppAssets.tabProfileDrawing
        }
    }

    var systemImage: String {
        switch self {
        case .home:
            "house"
        case .growth:
            "chart.line.uptrend.xyaxis"
        case .record:
            "square.and.pencil"
        case .profile:
            "person"
        }
    }
}

struct LiquidGlassTabBar: View {
    let selectedTab: AppTab
    let onSelect: (AppTab) -> Void

    var body: some View {
        HStack(spacing: 0) {
            ForEach(AppTab.allCases) { tab in
                tabButton(tab)
            }
        }
        .padding(6)
        .frame(height: 72)
        .background {
            Capsule()
                .fill(AppColors.milk.opacity(0.72))
                .overlay {
                    Capsule()
                        .stroke(.white.opacity(0.72), lineWidth: 1.5)
                }
                .shadow(color: .brown.opacity(0.07), radius: 6, y: 3)
        }
        .padding(.horizontal, 16)
        .padding(.bottom, 10)
    }

    private func tabButton(_ tab: AppTab) -> some View {
        let isSelected = selectedTab == tab

        return Button {
            onSelect(tab)
        } label: {
            VStack(spacing: 3) {
                AssetWatercolorImage(name: tab.iconAsset, mode: .multiply)
                    .frame(width: tab == .profile ? 34 : 31, height: 29)
                    .opacity(isSelected ? 1 : 0.78)

                Text(tab.rawValue.localizedText)
                    .font(AppTypography.tab)
                    .foregroundStyle(isSelected ? AppColors.coral : AppColors.tabMuted)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 56)
            .background {
                if isSelected {
                    Capsule()
                        .fill((tab == .record ? AppColors.blush : AppColors.blush).opacity(0.66))
                        .overlay {
                            Capsule()
                                .stroke(.white.opacity(0.62), lineWidth: 1)
                        }
                }
            }
            .offset(y: isSelected && tab == .record ? -3 : 0)
        }
        .buttonStyle(.plain)
    }
}
