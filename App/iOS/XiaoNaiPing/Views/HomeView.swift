import SwiftUI

struct HomeView: View {
    let onRoute: (AppRoute) -> Void
    let onOpenAlbum: () -> Void
    @EnvironmentObject private var store: BabyRecordStore

    var body: some View {
        ScreenScaffold {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    homeHeader
                    hero
                    reminderCards
                    SectionTitleView(title: "今日记录")
                    todayGrid
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.medium)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
    }

    private var homeHeader: some View {
        HStack(spacing: AppSpacing.regular) {
            Image(AppAssets.babyAvatar)
                .resizable()
                .scaledToFill()
                .frame(width: 64, height: 64)
                .clipShape(Circle())

            Text(store.baby.name)
                .font(AppTypography.title)
                .foregroundStyle(AppColors.inkGreen)

            Image(systemName: "chevron.down")
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(AppColors.inkGreen)

            Spacer()

            Button {
                onRoute(.vaccine)
            } label: {
                AssetWatercolorImage(name: AppAssets.bellIcon, mode: .multiply)
                    .frame(width: 42, height: 42)
            }
            .buttonStyle(.plain)
        }
    }

    private var hero: some View {
        ZStack {
            HStack(alignment: .bottom) {
                AssetWatercolorImage(name: AppAssets.homeBottleHero, mode: .multiply)
                    .frame(width: 105, height: 165)
                Spacer()
                AssetWatercolorImage(name: AppAssets.teddyHero, mode: .multiply)
                    .frame(width: 140, height: 160)
            }
            .padding(.horizontal, 10)
            .padding(.top, 24)

            AssetWatercolorImage(name: AppAssets.cloudBlue, mode: .multiply)
                .frame(width: 110, height: 64)
                .offset(x: 108, y: -82)

            VStack(spacing: AppSpacing.tiny) {
                Text("宝宝今天")
                    .font(AppTypography.heroTitle)
                    .foregroundStyle(AppColors.inkGreen)
                HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                    Text("第")
                        .font(AppTypography.heroUnit)
                    Text("\(store.baby.daysSinceBirth)")
                        .font(AppTypography.heroNumber)
                        .foregroundStyle(AppColors.coral)
                    Text("天")
                        .font(AppTypography.heroUnit)
                }
                .foregroundStyle(AppColors.inkGreen)
            }
            .padding(.top, 20)
        }
        .frame(height: 300)
    }

    private var reminderCards: some View {
        HStack(spacing: AppSpacing.medium) {
            Button {
                onRoute(.milestone)
            } label: {
                WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.medium) {
                    VStack(alignment: .leading, spacing: AppSpacing.small) {
                        Text("距离百天还有")
                            .font(AppTypography.cardTitle)
                        HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                            Text("\(store.hundredDaysRemaining)")
                                .font(AppTypography.largeNumber)
                                .foregroundStyle(AppColors.coral)
                            Text("天")
                                .font(AppTypography.bodyLarge)
                        }
                    }
                    .foregroundStyle(AppColors.ink)
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .buttonStyle(.plain)

            Button {
                onRoute(.vaccine)
            } label: {
                WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.medium) {
                    VStack(alignment: .leading, spacing: AppSpacing.small) {
                        Text(store.nextVaccine?.title ?? "下一次疫苗")
                            .font(AppTypography.cardTitle)
                        HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                            Text("\(store.nextVaccine?.dueDays ?? 0)")
                                .font(AppTypography.largeNumber)
                                .foregroundStyle(AppColors.blueInk)
                            Text(store.nextVaccine == nil ? "暂无" : "天后")
                                .font(AppTypography.bodyLarge)
                        }
                    }
                    .foregroundStyle(AppColors.ink)
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .buttonStyle(.plain)
        }
    }

    private var todayGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: AppSpacing.medium) {
            HomeStatCard(
                icon: AppAssets.bottleIcon,
                title: "喂养",
                value: "\(store.feedingCount)次 / \(store.milkAmountML)ml",
                tint: AppColors.cream
            ) { onRoute(.feeding) }

            HomeStatCard(
                icon: AppAssets.moonIcon,
                title: "睡眠",
                value: store.ongoingSleep == nil ? store.sleepDurationText : "进行中",
                tint: AppColors.mistBlue
            ) { onRoute(.sleep) }

            HomeStatCard(
                icon: AppAssets.diaperIcon,
                title: "排便",
                value: "\(store.poopCount)次",
                tint: AppColors.grass
            ) { onRoute(.diaper) }

            HomeStatCard(
                icon: AppAssets.cameraIcon,
                title: "照片",
                value: "\(store.photoCount)张",
                tint: AppColors.cream
            ) { onOpenAlbum() }
        }
    }
}

private struct HomeStatCard: View {
    let icon: String
    let title: String
    let value: String
    let tint: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            WatercolorCard(tint: tint, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
                HStack(spacing: AppSpacing.regular) {
                    AssetWatercolorImage(name: icon, mode: .multiply)
                        .frame(width: 62, height: 62)
                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text(title)
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.ink)
                        Text(value)
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(title == "睡眠" ? AppColors.blueInk : AppColors.coral)
                            .lineLimit(2)
                            .minimumScaleFactor(0.78)
                    }
                    Spacer(minLength: 0)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .frame(height: 74)
            }
        }
        .buttonStyle(.plain)
    }
}
