import SwiftUI

enum AppTab: String, CaseIterable, Identifiable {
    case home = "首页"
    case album = "相册"
    case record = "记录"
    case profile = "我的"

    var id: String { rawValue }

    var iconAsset: String {
        switch self {
        case .home:
            AppAssets.tabHomeDrawing
        case .album:
            AppAssets.tabAlbumDrawing
        case .record:
            AppAssets.tabRecordDrawing
        case .profile:
            AppAssets.tabProfileDrawing
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
        .padding(8)
        .frame(height: 84)
        .background {
            Capsule()
                .fill(AppColors.milk.opacity(0.72))
                .background {
                    Capsule()
                        .fill(.ultraThinMaterial)
                }
                .overlay {
                    Capsule()
                        .stroke(.white.opacity(0.72), lineWidth: 1.5)
                }
                .shadow(color: .brown.opacity(0.14), radius: 18, y: 8)
        }
        .padding(.horizontal, 18)
        .padding(.bottom, 14)
    }

    private func tabButton(_ tab: AppTab) -> some View {
        let isSelected = selectedTab == tab

        return Button {
            onSelect(tab)
        } label: {
            VStack(spacing: 3) {
                AssetWatercolorImage(name: tab.iconAsset, mode: .multiply)
                    .frame(width: tab == .profile ? 40 : 37, height: 34)
                    .opacity(isSelected ? 1 : 0.78)

                Text(tab.rawValue)
                    .font(AppTypography.tab)
                    .foregroundStyle(isSelected ? AppColors.coral : AppColors.tabMuted)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 66)
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
            .offset(y: isSelected && tab == .record ? -5 : 0)
        }
        .buttonStyle(.plain)
    }
}
