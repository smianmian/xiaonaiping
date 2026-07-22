import SwiftUI

struct HomeView: View {
    let onRoute: (AppRoute) -> Void
    let onOpenAlbum: () -> Void
    @EnvironmentObject private var store: BabyRecordStore
    @StateObject private var whiteNoisePlayer = WhiteNoisePlayer()

    var body: some View {
        ScreenScaffold {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    homeHeader
                    hero
                    SectionTitleView(title: "今日记录")
                    todayGrid
                    if !store.hasTodayRecords {
                        todayEmptyState
                    }
                    recentRecordsSection
                    reminderCards
                    whiteNoiseModule
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.medium)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
    }

    private var homeHeader: some View {
        HStack(spacing: AppSpacing.regular) {
            BabyAvatarView(
                imageData: store.baby.avatarImageData,
                fallbackAssetName: AppAssets.babyAvatar,
                size: 54
            )

            Text(store.baby.name)
                .font(AppTypography.title)
                .foregroundStyle(AppColors.inkGreen)

            Spacer()

            Button {
                onRoute(.vaccine)
            } label: {
                AssetWatercolorImage(name: AppAssets.bellIcon, mode: .multiply)
                    .frame(width: 36, height: 36)
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.plain)
        }
    }

    private var hero: some View {
        ZStack {
            HStack(alignment: .bottom) {
                AssetWatercolorImage(name: AppAssets.homeBottleHero, mode: .multiply)
                    .frame(width: 62, height: 98)
                Spacer()
                AssetWatercolorImage(name: AppAssets.teddyHero, mode: .multiply)
                    .frame(width: 84, height: 96)
            }
            .padding(.horizontal, 10)
            .padding(.top, 8)

            AssetWatercolorImage(name: AppAssets.cloudBlue, mode: .multiply)
                .frame(width: 76, height: 44)
                .offset(x: 84, y: -46)

            VStack(spacing: AppSpacing.tiny) {
                Text("宝宝今天")
                    .font(AppTypography.sectionTitle)
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
            .padding(.top, 4)
        }
        .frame(height: 166)
    }

    private var reminderCards: some View {
        HStack(spacing: AppSpacing.medium) {
            Button {
                onRoute(.milestone)
            } label: {
                WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.medium) {
                    VStack(alignment: .leading, spacing: AppSpacing.small) {
                        Text((store.nextAutomaticMilestone?.title ?? "成长纪念日").localizedText)
                            .font(AppTypography.cardTitle)
                        HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                            Text(store.nextAutomaticMilestone.map { "\($0.daysRemaining)" } ?? "\(store.baby.daysSinceBirth)")
                                .font(AppTypography.largeNumber)
                                .foregroundStyle(AppColors.coral)
                            Text((store.nextAutomaticMilestone == nil ? "成长天数" : "天后").localizedText)
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
                            Text(store.nextVaccine.map(store.vaccineDueValue) ?? "--")
                                .font(AppTypography.largeNumber)
                                .foregroundStyle(AppColors.blueInk)
                            Text((store.nextVaccine.map(store.vaccineDueUnit) ?? "暂无").localizedText)
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
                title: "记喂养",
                value: feedingCardValue,
                tint: AppColors.cream,
                isQuietMode: store.quietCareModeEnabled
            ) { onRoute(.feeding) }

            HomeStatCard(
                systemIcon: "drop.fill",
                title: "记喝水",
                value: "\(store.todayWaterRecords.count)次 / \(store.waterAmountML)ml",
                tint: AppColors.mistBlue,
                isQuietMode: store.quietCareModeEnabled
            ) { onRoute(.water) }

            HomeStatCard(
                icon: AppAssets.moonIcon,
                title: "睡眠记录",
                value: sleepCardValue,
                tint: AppColors.mistBlue,
                isQuietMode: store.quietCareModeEnabled
            ) { onRoute(.sleep) }

            HomeStatCard(
                icon: AppAssets.diaperIcon,
                title: "记排便",
                value: "\(store.poopCount)次",
                tint: AppColors.grass,
                isQuietMode: store.quietCareModeEnabled
            ) { onRoute(.diaper) }

            HomeStatCard(
                icon: AppAssets.cameraIcon,
                title: "加照片",
                value: "\(store.todayPhotoCount)张",
                tint: AppColors.cream,
                isQuietMode: store.quietCareModeEnabled
            ) { onOpenAlbum() }
        }
    }

    private var feedingCardValue: String {
        guard store.feedingCount > 0 else {
            return "\(store.feedingCount)次 / \(store.milkAmountML)ml"
        }
        return "\(store.feedingCount)次 / \(store.milkAmountML)ml\n距上次 \(store.lastFeedingIntervalText)"
    }

    private var sleepCardValue: String {
        guard let ongoing = store.ongoingSleep else {
            return store.sleepDurationText
        }

        return "从 \(ongoing.start) 开始"
    }

    private var todayEmptyState: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Text("今天还没有记录")
                    .font(AppTypography.cardTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text("先记一件小事吧，喂养、睡眠、排便或照片都可以。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityElement(children: .combine)
    }

    private var recentRecordsSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.regular) {
            SectionTitleView(title: "最近记录")

            if store.recentHomeRecords.isEmpty {
                WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
                    Text("记录后会在这里慢慢排成一条小时间线。")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            } else {
                VStack(spacing: AppSpacing.small) {
                    ForEach(store.recentHomeRecords.prefix(3)) { record in
                        RecordRowView(
                            icon: record.icon,
                            systemIcon: record.systemIcon,
                            time: record.time,
                            title: record.title,
                            detail: record.detail,
                            tint: AppColors.cream
                        )
                        .accessibilityElement(children: .combine)
                        .accessibilityLabel("\(record.time)，\(record.title)，\(record.detail)")
                    }
                }
            }
        }
    }

    private var whiteNoiseModule: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.regular) {
                HStack(alignment: .center, spacing: AppSpacing.medium) {
                    ZStack {
                        AssetWatercolorImage(name: AppAssets.cloudBlue, mode: .multiply)
                            .frame(width: 72, height: 46)
                            .offset(x: 12, y: -8)
                        AssetWatercolorImage(name: AppAssets.moonIcon, mode: .multiply)
                            .frame(width: 54, height: 54)
                            .offset(x: -12, y: 8)
                    }
                    .frame(width: 82, height: 64)

                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("睡前小声音")
                            .font(AppTypography.sectionTitle)
                            .foregroundStyle(AppColors.inkGreen)
                        Text(whiteNoiseStatusText)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    Spacer(minLength: AppSpacing.small)

                    Button {
                        if !store.quietCareModeEnabled {
                            whiteNoisePlayer.toggle()
                        }
                    } label: {
                        ZStack {
                            Circle()
                                .fill((whiteNoisePlayer.isPlaying ? AppColors.blush : AppColors.mistBlue).opacity(0.9))
                                .overlay {
                                    Circle()
                                        .stroke(.white.opacity(0.72), lineWidth: 1)
                                }
                                .shadow(color: AppColors.softStroke.opacity(0.24), radius: 10, y: 5)
                            Image(systemName: whiteNoisePlayer.isPreparing ? "hourglass" : (whiteNoisePlayer.isPlaying ? "pause.fill" : "play.fill"))
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundStyle(whiteNoisePlayer.isPlaying ? AppColors.coral : AppColors.blueInk)
                                .offset(x: whiteNoisePlayer.isPlaying ? 0 : 1)
                        }
                        .frame(width: 46, height: 46)
                    }
                    .buttonStyle(.plain)
                    .disabled(store.quietCareModeEnabled)
                    .accessibilityLabel(whiteNoisePlayer.isPlaying || whiteNoisePlayer.isPreparing ? "暂停白噪音" : "播放白噪音")
                }

                HStack(spacing: AppSpacing.regular) {
                    Menu {
                        ForEach(WhiteNoiseSound.allCases) { sound in
                            Button {
                                whiteNoisePlayer.selectedSound = sound
                            } label: {
                                Label(sound.title, systemImage: sound.systemImage)
                            }
                        }
                    } label: {
                        HStack(spacing: AppSpacing.small) {
                            Image(systemName: whiteNoisePlayer.selectedSound.systemImage)
                                .font(.system(size: 14, weight: .semibold))
                            Text(whiteNoisePlayer.selectedSound.title)
                                .font(AppTypography.body)
                            Spacer(minLength: 0)
                            Image(systemName: "chevron.down")
                                .font(.system(size: 12, weight: .semibold))
                        }
                        .foregroundStyle(AppColors.inkGreen)
                        .padding(.horizontal, AppSpacing.regular)
                        .frame(height: 44)
                        .background {
                            RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                                .fill(AppColors.milk.opacity(0.56))
                                .overlay {
                                    RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                                        .stroke(AppColors.softStroke.opacity(0.24), lineWidth: 1)
                                }
                        }
                    }
                    .buttonStyle(.plain)
                    .disabled(store.quietCareModeEnabled)

                    WhiteNoiseVolumeDots(volume: $whiteNoisePlayer.volume)
                        .opacity(store.quietCareModeEnabled ? 0.46 : 1)
                }
            }
        }
        .onChange(of: store.quietCareModeEnabled) { _, isEnabled in
            if isEnabled {
                whiteNoisePlayer.stop()
            }
        }
    }

    private var whiteNoiseStatusText: String {
        if store.quietCareModeEnabled {
            return "安静育儿模式已开启，不会播放声音"
        }

        if whiteNoisePlayer.isPreparing {
            return "\(whiteNoisePlayer.selectedSound.title)准备中"
        }

        if whiteNoisePlayer.isPlaying {
            return "\(whiteNoisePlayer.selectedSound.title)轻轻播放中"
        }

        return "点一下，慢慢安静下来"
    }
}

private struct WhiteNoiseVolumeDots: View {
    @Binding var volume: Double

    private let levels: [Double] = [0.14, 0.26, 0.38, 0.52, 0.66]

    var body: some View {
        HStack(spacing: AppSpacing.regular) {
            Text("音量")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkGreen)

            HStack(spacing: AppSpacing.small) {
                ForEach(levels.indices, id: \.self) { index in
                    Button {
                        volume = levels[index]
                    } label: {
                        ZStack {
                            Circle()
                                .fill(index <= selectedIndex ? AppColors.blueInk.opacity(0.72) : AppColors.milk.opacity(0.72))
                                .frame(width: CGFloat(9 + index * 2), height: CGFloat(9 + index * 2))
                                .overlay {
                                    Circle()
                                        .stroke(AppColors.softStroke.opacity(0.28), lineWidth: 1)
                                }
                        }
                        .frame(width: 30, height: 34)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("白噪音音量 \(index + 1)")
                }
            }

            Spacer()

            Text(volumeLabel)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
        }
        .padding(.horizontal, AppSpacing.regular)
        .padding(.vertical, AppSpacing.small)
        .background {
            RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                .fill(AppColors.mistBlue.opacity(0.30))
        }
    }

    private var selectedIndex: Int {
        levels.enumerated().min { abs($0.element - volume) < abs($1.element - volume) }?.offset ?? 2
    }

    private var volumeLabel: String {
        switch selectedIndex {
        case 0...1:
            "轻轻的"
        case 2:
            "刚刚好"
        default:
            "稍明显"
        }
    }
}

private struct HomeStatCard: View {
    var icon: String? = nil
    var systemIcon: String? = nil
    let title: String
    let value: String
    let tint: Color
    var isQuietMode = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            WatercolorCard(tint: tint, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
                HStack(spacing: AppSpacing.regular) {
                    Group {
                        if let icon {
                            AssetWatercolorImage(name: icon, mode: .multiply)
                        } else if let systemIcon {
                            Image(systemName: systemIcon)
                                .resizable()
                                .scaledToFit()
                                .foregroundStyle(AppColors.blueInk)
                        }
                    }
                    .frame(width: 50, height: 50)
                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text(title)
                            .font(isQuietMode ? AppTypography.quietBody : AppTypography.body)
                            .foregroundStyle(AppColors.ink)
                        Text(value)
                            .font(isQuietMode ? AppTypography.quietBodyLarge : AppTypography.bodyLarge)
                            .foregroundStyle(title.contains("睡眠") ? AppColors.blueInk : AppColors.coral)
                            .lineLimit(2)
                            .minimumScaleFactor(0.78)
                    }
                    Spacer(minLength: 0)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .frame(height: 62)
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(title)，\(value)")
        .accessibilityIdentifier("home_stat_\(title)")
    }
}
