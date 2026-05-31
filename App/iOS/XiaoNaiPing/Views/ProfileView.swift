import SwiftUI

struct ProfileView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var isPrivacyNoticePresented = false
    @State private var isLocalDeletePresented = false

    var body: some View {
        ScreenScaffold {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    profileHeader

                    WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius, padding: 0) {
                        VStack(spacing: 0) {
                            ProfileMenuRow(icon: "list.clipboard", title: "宝宝信息", value: "本地原型")
                            ProfileMenuRow(icon: "bell", title: "提醒设置", value: "疫苗")
                            Button {
                                isPrivacyNoticePresented = true
                            } label: {
                                ProfileMenuRow(icon: "icloud.and.arrow.up", title: "账号与备份", value: "待审查")
                            }
                            .buttonStyle(.plain)
                            Button {
                                isPrivacyNoticePresented = true
                            } label: {
                                ProfileMenuRow(icon: "shield", title: "隐私与安全", value: "必做")
                            }
                            .buttonStyle(.plain)
                            Button {
                                isLocalDeletePresented = true
                            } label: {
                                ProfileMenuRow(icon: "trash", title: "清空本地演示数据", value: nil)
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    AssetWatercolorImage(name: AppAssets.profileBirdBottle, mode: .multiply)
                        .frame(height: 120)
                        .padding(.top, AppSpacing.medium)
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.large)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .alert("账号与备份暂不接入", isPresented: $isPrivacyNoticePresented) {
            Button("知道了", role: .cancel) {}
        } message: {
            Text("账号、备份恢复、照片原图云备份和服务器存储需要先补齐删除 SLA、隐私政策、日志脱敏和 App Store 隐私标签。当前只做本地原型。")
        }
        .alert("清空本地演示数据？", isPresented: $isLocalDeletePresented) {
            Button("清空", role: .destructive) {
                store.clearLocalDemoRecords()
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text("这只会清空当前运行中的本地演示数据，不会连接服务器。")
        }
    }

    private var profileHeader: some View {
        HStack(spacing: AppSpacing.large) {
            Image(AppAssets.profileBaby)
                .resizable()
                .scaledToFill()
                .frame(width: 104, height: 104)
                .clipShape(Circle())

            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Text(MockData.baby.name)
                    .font(AppTypography.title)
                    .foregroundStyle(AppColors.inkGreen)
                HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                    Text("68天")
                        .font(AppTypography.largeNumber)
                        .foregroundStyle(AppColors.coral)
                    Text("/ \(MockData.baby.ageText)")
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.ink)
                }
            }

            Spacer()
            AssetWatercolorImage(name: AppAssets.cloudBlue, mode: .multiply)
                .frame(width: 78, height: 48)
        }
    }
}

private struct ProfileMenuRow: View {
    let icon: String
    let title: String
    var value: String? = nil

    var body: some View {
        HStack(spacing: AppSpacing.medium) {
            Image(systemName: icon)
                .font(.system(size: 24, weight: .regular))
                .foregroundStyle(AppColors.sage)
                .frame(width: 44, height: 44)
            Text(title)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.ink)
            Spacer()
            if let value {
                Text(value)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
            }
            Image(systemName: "chevron.right")
                .font(.system(size: 18, weight: .regular))
                .foregroundStyle(AppColors.inkSoft.opacity(0.72))
        }
        .padding(.horizontal, AppSpacing.large)
        .padding(.vertical, AppSpacing.medium)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(AppColors.softStroke.opacity(0.18))
                .frame(height: 1)
                .padding(.leading, 88)
                .padding(.trailing, AppSpacing.large)
        }
    }
}
