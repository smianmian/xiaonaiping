import SwiftUI

struct HomeView: View {
    let onRoute: (AppRoute) -> Void
    let onOpenAlbum: () -> Void
    let onQuickRecord: () -> Void
    @EnvironmentObject private var store: BabyRecordStore
    @State private var quickOutcome: QuickLogOutcome?
    @State private var quickFeedbackTrigger = 0
    @State private var undoDismissTask: Task<Void, Never>?

    var body: some View {
        ScreenScaffold {
            ScrollView(showsIndicators: false) {
                // 每 30 秒重算一次，让“距上次”和进行中睡眠的时长自己走。
                TimelineView(.periodic(from: .now, by: 30)) { _ in
                    VStack(alignment: .leading, spacing: AppLayout.sectionSpacing) {
                        header
                        currentState
                        quickActionsSection
                        overviewSection
                        recentRecords
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppLayout.homeTopAdjustment)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sensoryFeedback(.success, trigger: quickFeedbackTrigger)
    }

    private var header: some View {
        Button(action: onOpenAlbum) {
            HStack(spacing: AppSpacing.medium) {
                BabyAvatarView(
                    imageData: store.baby.avatarImageData,
                    fallbackAssetName: "approvedBabyAvatar",
                    size: AppLayout.headerAvatar
                )
                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                    Text(store.baby.name)
                        .font(AppTypography.homeBabyName)
                        .foregroundStyle(AppColors.inkGreen)
                    Text("第\(store.currentBabyDaysSinceBirth)天")
                        .font(AppTypography.homeDay)
                        .foregroundStyle(AppColors.coral)
                }
                Spacer(minLength: 0)
                Image(systemName: "chevron.right")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(AppColors.inkSoft)
            }
            .frame(height: 90)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(store.baby.name)，第\(store.currentBabyDaysSinceBirth)天，打开相册")
    }

    private var currentState: some View {
        Button { onRoute(.feeding) } label: {
            HStack(spacing: 0) {
                stateColumn(label: "最近喂养", value: latestFeedingText, artwork: "approvedFeedingBottle")
                stateDivider
                stateColumn(label: "距上次", value: store.lastFeedingRecord == nil ? "暂无" : store.lastFeedingIntervalText, systemIcon: "clock")
                stateDivider
                stateColumn(
                    label: "下一次提醒",
                    value: nextReminderText,
                    systemIcon: "bell",
                    subValue: nextReminderSubText,
                    valueFont: AppTypography.homePrimaryData
                )
            }
            .frame(maxWidth: .infinity)
            .frame(minHeight: AppLayout.stateCardHeight)
            .background { CardBackground(tint: AppColors.milk, cornerRadius: AppLayout.statusCardRadius) }
        }
        .buttonStyle(.plain)
    }

    private var stateDivider: some View {
        Rectangle()
            .fill(AppColors.softStroke.opacity(0.26))
            .frame(width: 1, height: 74)
    }

    @ViewBuilder
    private func stateColumn(
        label: String,
        value: String,
        artwork: String? = nil,
        systemIcon: String? = nil,
        subValue: String? = nil,
        valueFont: Font = AppTypography.stateValue
    ) -> some View {
        VStack(spacing: AppSpacing.small) {
            Group {
                if let artwork {
                    AssetWatercolorImage(name: artwork)
                } else if let systemIcon {
                    Image(systemName: systemIcon)
                        .font(.system(size: 25, weight: .regular))
                        .foregroundStyle(AppColors.inkGreen)
                        .padding(11)
                        .background(AppColors.cream, in: Circle())
                }
            }
            .frame(width: AppLayout.stateArtworkWidth, height: AppLayout.stateArtworkHeight)

            Text(label)
                .font(AppTypography.stateLabel)
                .foregroundStyle(AppColors.ink)
                .lineLimit(1)
            Text(value)
                .font(valueFont)
                .foregroundStyle(AppColors.coral)
                .lineLimit(1)
                .minimumScaleFactor(0.70)
                .multilineTextAlignment(.center)
            if let subValue {
                Text(subValue)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, AppSpacing.small)
    }

    private var quickActionsSection: some View {
        VStack(spacing: AppSpacing.small) {
            HStack(spacing: AppSpacing.medium) {
                QuickActionButton(
                    title: "喂奶",
                    subtitle: feedingQuickSubtitle,
                    assetName: "approvedFeedingBottle"
                ) {
                    performQuick(QuickLogService.logFeedingLikeLast(store: store))
                }
                QuickActionButton(
                    title: "大便",
                    subtitle: "记一次 · 刚刚",
                    assetName: "approvedDiaper"
                ) {
                    performQuick(QuickLogService.logDiaper(store: store))
                }
                QuickActionButton(
                    title: store.ongoingSleep == nil ? "睡觉" : "醒了",
                    subtitle: sleepQuickSubtitle,
                    assetName: "approvedSleepMoon"
                ) {
                    performQuick(QuickLogService.toggleSleep(store: store))
                }
            }
            if let quickOutcome {
                quickUndoStrip(for: quickOutcome)
                    .transition(.opacity.combined(with: .move(edge: .top)))
            }
        }
    }

    private var feedingQuickSubtitle: String {
        guard let last = store.latestFeedingRecordEver else { return "去记录" }
        if let amount = last.amountML, amount > 0 {
            return "同上次 · \(amount)ml"
        }
        if let duration = last.durationMinutes, duration > 0 {
            return "同上次 · \(duration)分钟"
        }
        return "同上次 · \(last.type)"
    }

    private var sleepQuickSubtitle: String {
        guard let ongoing = store.ongoingSleep else { return "开始计时" }
        let minutes = max(0, Calendar.current.dateComponents([.minute], from: ongoing.startAt, to: Date()).minute ?? 0)
        return "已睡 \(BabyRecordStore.durationText(from: minutes))"
    }

    private func performQuick(_ outcome: QuickLogOutcome) {
        switch outcome {
        case .needsFeedingEditor:
            onRoute(.feedingForm)
        case .failed:
            break
        default:
            quickFeedbackTrigger += 1
            withAnimation(.easeOut(duration: 0.2)) {
                quickOutcome = outcome
            }
            undoDismissTask?.cancel()
            undoDismissTask = Task {
                try? await Task.sleep(nanoseconds: 6_000_000_000)
                guard !Task.isCancelled else { return }
                withAnimation(.easeIn(duration: 0.2)) {
                    quickOutcome = nil
                }
            }
        }
    }

    private func quickUndoStrip(for outcome: QuickLogOutcome) -> some View {
        HStack(spacing: AppSpacing.small) {
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(AppColors.inkGreen)
            Text(quickOutcomeText(outcome))
                .font(AppTypography.homeSecondary)
                .foregroundStyle(AppColors.ink)
                .lineLimit(1)
            Spacer(minLength: 0)
            if quickOutcomeSupportsUndo(outcome) {
                Button("撤销") {
                    QuickLogService.undo(outcome, store: store)
                    undoDismissTask?.cancel()
                    withAnimation(.easeIn(duration: 0.2)) {
                        quickOutcome = nil
                    }
                }
                .font(AppTypography.homeSecondary.weight(.semibold))
                .foregroundStyle(AppColors.coral)
            }
        }
        .padding(.horizontal, AppSpacing.medium)
        .frame(height: 44)
        .frame(maxWidth: .infinity)
        .background { CardBackground(tint: AppColors.cream, cornerRadius: AppLayout.cardRadius) }
    }

    private func quickOutcomeText(_ outcome: QuickLogOutcome) -> String {
        switch outcome {
        case .feedingSaved(let record):
            return "已记喂奶 · \(record.type)\(record.detail.isEmpty ? "" : " \(record.detail)")"
        case .diaperSaved:
            return "已记大便 · 刚刚"
        case .sleepStarted:
            return "睡眠计时已开始"
        case .sleepEnded(let minutes):
            return "已记睡眠 · \(BabyRecordStore.durationText(from: minutes))"
        case .needsFeedingEditor, .failed:
            return ""
        }
    }

    private func quickOutcomeSupportsUndo(_ outcome: QuickLogOutcome) -> Bool {
        switch outcome {
        case .feedingSaved, .diaperSaved, .sleepStarted:
            return true
        case .sleepEnded, .needsFeedingEditor, .failed:
            return false
        }
    }

    private var overviewSection: some View {
        VStack(alignment: .leading, spacing: AppLayout.titleToContentSpacing) {
            Text("今日概览")
                .font(AppTypography.homeSectionTitle)
                .foregroundStyle(AppColors.inkGreen)
            LazyVGrid(columns: [GridItem(.flexible(), spacing: AppSpacing.medium), GridItem(.flexible())], spacing: AppSpacing.medium) {
                HomeStatCard(title: "喂养", value: "\(store.feedingCount)次 / \(store.milkAmountML)ml", assetName: "approvedFeedingBottle", valueColor: AppColors.coral) { onRoute(.feeding) }
                HomeStatCard(title: "睡眠", value: store.sleepDurationText, assetName: "approvedSleepMoon", valueColor: AppColors.blueInk) { onRoute(.sleep) }
                HomeStatCard(title: "排便", value: "\(store.poopCount)次", assetName: "approvedDiaper", valueColor: AppColors.inkGreen) { onRoute(.diaper) }
                HomeStatCard(title: "喝水", value: "\(store.todayWaterRecords.count)次 / \(store.waterAmountML)ml", assetName: "approvedWaterDrop", valueColor: AppColors.blueInk) { onRoute(.water) }
            }
        }
    }

    private var recentRecords: some View {
        VStack(alignment: .leading, spacing: AppLayout.titleToContentSpacing) {
            Text("最近记录")
                .font(AppTypography.homeSectionTitle)
                .foregroundStyle(AppColors.inkGreen)
            if store.recentHomeRecords.isEmpty {
                WatercolorCard(tint: AppColors.milk, cornerRadius: AppLayout.cardRadius, padding: AppSpacing.roomy) {
                    Text("还没有记录")
                        .font(AppTypography.homeSecondary)
                        .foregroundStyle(AppColors.inkSoft)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            } else {
                HomeRecentListCard(records: Array(store.recentHomeRecords.prefix(3))) {
                    onRoute(.feeding)
                }
            }
        }
    }

    /// 参考稿规格：时间 + 奶量/时长，不带类型名。奶量优先，
    /// 无奶量用时长，都没有只显示时间。
    private var latestFeedingText: String {
        guard let record = store.lastFeedingRecord else { return "暂无记录" }
        if let amount = record.amountML, amount > 0 {
            return "\(record.time) · \(amount)ml"
        }
        if let duration = record.durationMinutes, duration > 0 {
            return "\(record.time) · \(duration)分钟"
        }
        return record.time
    }

    private var nextReminderText: String {
        guard let reminder = store.nextFeedingReminder else { return "未安排" }
        return BabyRecordStore.timeString(from: reminder.remindAt)
    }

    /// 仅当提醒来自自动间隔且自动提醒开启时，显示“每N小时提醒”副行；
    /// 非整小时显示一位小数（如“每2.5小时提醒”）。
    private var nextReminderSubText: String? {
        guard let reminder = store.nextFeedingReminder,
              reminder.origin == .automatic,
              store.feedingReminderPreference.isAutoReminderEnabled,
              let intervalMinutes = store.feedingReminderPreference.intervalMinutes else {
            return nil
        }
        let hours = Double(intervalMinutes) / 60
        let hoursText = intervalMinutes % 60 == 0
            ? "\(intervalMinutes / 60)"
            : String(format: "%.1f", hours)
        return "每\(hoursText)小时提醒"
    }
}

private struct QuickActionButton: View {
    let title: String
    let subtitle: String
    let assetName: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: AppSpacing.tiny) {
                AssetWatercolorImage(name: assetName)
                    .frame(width: 40, height: 40)
                Text(title)
                    .font(AppTypography.homeCardTitle)
                    .foregroundStyle(AppColors.inkGreen)
                    .lineLimit(1)
                Text(subtitle)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            .padding(.vertical, AppSpacing.medium)
            .padding(.horizontal, AppSpacing.tiny)
            .frame(maxWidth: .infinity, minHeight: 96)
            .background { CardBackground(tint: AppColors.cream, cornerRadius: AppLayout.cardRadius) }
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(title)，\(subtitle)")
        .accessibilityHint("一键记录，无需填表")
    }
}

private struct HomeStatCard: View {
    let title: String
    let value: String
    let assetName: String
    let valueColor: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: -2) {
                AssetWatercolorImage(name: assetName)
                    .frame(width: AppLayout.overviewArtwork, height: AppLayout.overviewArtwork)
                VStack(alignment: .leading, spacing: AppSpacing.small) {
                    Text(title)
                        .font(AppTypography.homeCardTitle)
                        .foregroundStyle(AppColors.inkGreen)
                    Text(value)
                        .font(AppTypography.homePrimaryData)
                        .foregroundStyle(valueColor)
                        .lineLimit(1)
                        .minimumScaleFactor(0.60)
                        .layoutPriority(1)
                }
                Spacer(minLength: 0)
            }
            .padding(.horizontal, AppSpacing.regular)
            .padding(.vertical, AppSpacing.medium)
            .frame(maxWidth: .infinity, minHeight: AppLayout.overviewCardHeight, alignment: .leading)
            .background { CardBackground(tint: AppColors.milk, cornerRadius: AppLayout.cardRadius) }
        }
        .buttonStyle(.plain)
    }
}

private struct HomeRecentListCard: View {
    let records: [HomeRecentRecord]
    let onSeeMore: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            ForEach(Array(records.enumerated()), id: \.element.id) { index, record in
                recentRow(record)
                if index < records.count - 1 {
                    Divider().padding(.leading, 16)
                }
            }
            Button(action: onSeeMore) {
                HStack {
                    Spacer()
                    Text("查看更多记录")
                    Image(systemName: "chevron.right")
                        .font(.system(size: 13, weight: .semibold))
                }
                .font(AppTypography.homeSecondary)
                .foregroundStyle(AppColors.inkGreen)
                .frame(height: 44)
                .padding(.horizontal, AppSpacing.medium)
            }
            .buttonStyle(.plain)
        }
        .background { CardBackground(tint: AppColors.milk, cornerRadius: AppLayout.cardRadius) }
    }

    private func recentRow(_ record: HomeRecentRecord) -> some View {
        HStack(spacing: AppSpacing.small) {
            Text(record.time)
                .font(AppTypography.homeListText)
                .foregroundStyle(AppColors.inkGreen)
                .lineLimit(1)
                .layoutPriority(1)
                .frame(minWidth: 78, alignment: .leading)
            recordArtwork(for: record.title)
                .frame(width: AppLayout.recentArtwork, height: AppLayout.recentArtwork)
            Text(record.title)
                .font(AppTypography.homeListText)
                .foregroundStyle(AppColors.ink)
                .lineLimit(1)
                .minimumScaleFactor(0.85)
            Spacer(minLength: AppSpacing.tiny)
            Text(record.detail == "快速记录" ? "已记录" : record.detail)
                .font(AppTypography.homeListText)
                .foregroundStyle(AppColors.ink)
                .lineLimit(1)
                .minimumScaleFactor(0.72)
        }
        .padding(.horizontal, AppSpacing.medium)
        .frame(minHeight: 58)
    }

    @ViewBuilder
    private func recordArtwork(for title: String) -> some View {
        if title.contains("喂养") {
            AssetWatercolorImage(name: "approvedFeedingBottle")
        } else if title.contains("睡眠") {
            AssetWatercolorImage(name: "approvedSleepMoon")
        } else if title.contains("大便") || title.contains("排便") {
            AssetWatercolorImage(name: "approvedDiaper")
        } else if title.contains("喝水") {
            AssetWatercolorImage(name: "approvedWaterDrop")
        } else {
            Image(systemName: "circle.fill").foregroundStyle(AppColors.inkSoft)
        }
    }
}
