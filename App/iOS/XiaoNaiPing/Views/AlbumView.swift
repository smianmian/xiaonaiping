import SwiftUI

struct AlbumView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var selectedFilter = "全部"
    @State private var isPhotoBoundaryPresented = false
    private let filters = ["全部", "本月", "纪念日", "月报"]
    private let columns = [
        GridItem(.flexible(), spacing: AppSpacing.regular),
        GridItem(.flexible(), spacing: AppSpacing.regular),
        GridItem(.flexible(), spacing: AppSpacing.regular)
    ]

    var body: some View {
        ScreenScaffold(title: "相册") {
            ZStack(alignment: .bottomTrailing) {
                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: AppSpacing.large) {
                        SegmentedPill(items: filters, selected: $selectedFilter)
                            .padding(.top, AppSpacing.small)

                        monthSection(title: "5月", year: "2025", photos: Array(AppAssets.albumPhotos.prefix(6)))
                        monthSection(title: "4月", year: "2025", photos: Array(AppAssets.albumPhotos.dropFirst(6)))
                    }
                    .padding(.horizontal, AppSpacing.page)
                    .padding(.bottom, AppSpacing.bottomBarSpace)
                }

                Button {
                    isPhotoBoundaryPresented = true
                } label: {
                    HStack(spacing: AppSpacing.small) {
                        Image(systemName: "photo.badge.plus")
                            .font(.system(size: 24, weight: .regular))
                        Text("添加照片")
                            .font(AppTypography.body)
                    }
                    .foregroundStyle(.white)
                    .padding(.horizontal, AppSpacing.medium)
                    .padding(.vertical, AppSpacing.regular)
                    .background {
                        Capsule()
                            .fill(AppColors.blueInk.opacity(0.76))
                            .shadow(color: AppColors.blueInk.opacity(0.24), radius: 16, y: 8)
                    }
                }
                .buttonStyle(.plain)
                .padding(.trailing, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace - 26)
            }
        }
        .alert("照片功能待接入", isPresented: $isPhotoBoundaryPresented) {
            Button("知道了", role: .cancel) {}
        } message: {
            Text("第一版会让用户主动选择照片，并复制到 App 私有空间；接入相册/相机权限前需要完成隐私说明和删除机制。当前仅保留本地相册原型。")
        }
    }

    private func monthSection(title: String, year: String, photos: [String]) -> some View {
        VStack(alignment: .leading, spacing: AppSpacing.medium) {
            HStack(alignment: .firstTextBaseline, spacing: AppSpacing.medium) {
                Text(title)
                    .font(AppTypography.navTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text(year)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                AssetWatercolorImage(name: AppAssets.cloudBlue, mode: .multiply)
                    .frame(width: 54, height: 34)
                Spacer()
                Text("\(store.photoCount)张")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkGreen)
            }

            LazyVGrid(columns: columns, spacing: AppSpacing.regular) {
                ForEach(photos, id: \.self) { photo in
                    Image(photo)
                        .resizable()
                        .scaledToFill()
                        .frame(height: 116)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                }
            }
        }
    }
}
