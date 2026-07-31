import SwiftUI
import UIKit
import WidgetKit

#if canImport(ActivityKit)
import ActivityKit
#endif

struct TodayTimelineEntry: TimelineEntry {
    let date: Date
    let snapshot: SharedTodaySnapshot?
}

struct TodayProvider: TimelineProvider {
    func placeholder(in context: Context) -> TodayTimelineEntry {
        TodayTimelineEntry(date: Date(), snapshot: .empty)
    }

    func getSnapshot(in context: Context, completion: @escaping (TodayTimelineEntry) -> Void) {
        completion(TodayTimelineEntry(date: Date(), snapshot: XiaoNaiPingSharedStore.readSnapshot()))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<TodayTimelineEntry>) -> Void) {
        let now = Date()
        let snapshot = XiaoNaiPingSharedStore.readSnapshot()
        var entries = [TodayTimelineEntry(date: now, snapshot: snapshot)]
        // 跨零点补一个条目：让“今日”统计在午夜自动清零，而不是继续显示昨天的数字。
        if let nextMidnight = Calendar.current.date(byAdding: .day, value: 1, to: Calendar.current.startOfDay(for: now)) {
            entries.append(TodayTimelineEntry(date: nextMidnight, snapshot: snapshot))
        }
        let refreshDate = Calendar.current.date(byAdding: .minute, value: 15, to: now) ?? now
        completion(Timeline(entries: entries, policy: .after(refreshDate)))
    }
}

struct XiaoNaiPingTodayWidgetView: View {
    @Environment(\.widgetFamily) private var family

    let entry: TodayTimelineEntry

    var body: some View {
        // 深链一键记录：小尺寸/锁屏整体点按直达“记一次喂奶”，
        // 中尺寸在 mediumBody 里按区块分别链接喂奶/睡眠。
        switch family {
        case .systemMedium:
            mediumBody
        case .accessoryCircular:
            accessoryCircularBody
                .widgetURL(URL(string: "xnp://quicklog/feeding"))
        case .accessoryRectangular:
            accessoryRectangularBody
                .widgetURL(URL(string: "xnp://quicklog/feeding"))
        case .accessoryInline:
            Text(inlineText)
                .widgetURL(URL(string: "xnp://quicklog/feeding"))
        default:
            smallBody
                .widgetURL(URL(string: "xnp://quicklog/feeding"))
        }
    }

    private var smallBody: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
                .foregroundStyle(.primary)
                .lineLimit(1)
            Text(primaryLine)
                .font(.title3.weight(.semibold))
                .foregroundStyle(Color(red: 0.86, green: 0.36, blue: 0.30))
                .lineLimit(2)
                .minimumScaleFactor(0.72)
            Text(secondaryLine)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .containerBackground(Color(red: 1.0, green: 0.97, blue: 0.90), for: .widget)
    }

    private var mediumBody: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title)
                    .font(.headline)
                Spacer()
                Text(daysText)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(.secondary)
            }
            HStack(spacing: 14) {
                // 每个区块深链到对应的一键记录：点喂养直接记一次奶。
                Link(destination: URL(string: "xnp://quicklog/feeding")!) {
                    metric("喂养", "\(snapshot?.feedingCount ?? 0)次", "\(snapshot?.milkAmountML ?? 0)ml")
                }
                Link(destination: URL(string: "xnp://quicklog/sleep")!) {
                    metric("睡眠", sleepStatus, sleepDetail)
                }
                Link(destination: URL(string: "xnp://quicklog/diaper")!) {
                    metric("排便", "\(diaperCount)次", reminderText)
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .containerBackground(Color(red: 1.0, green: 0.97, blue: 0.90), for: .widget)
    }

    private var accessoryCircularBody: some View {
        Gauge(value: Double(snapshot?.feedingCount ?? 0), in: 0...8) {
            Image(systemName: "drop.fill")
        } currentValueLabel: {
            Text("\(snapshot?.feedingCount ?? 0)")
        }
        .gaugeStyle(.accessoryCircular)
    }

    private var accessoryRectangularBody: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("小奶瓶")
                .font(.caption2)
            Text(primaryLine)
                .font(.headline)
                .lineLimit(1)
            Text(secondaryLine)
                .font(.caption2)
                .lineLimit(1)
        }
    }

    private func metric(_ title: String, _ value: String, _ detail: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.title3.weight(.semibold))
                .foregroundStyle(.primary)
                .lineLimit(1)
                .minimumScaleFactor(0.75)
            Text(detail)
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var snapshot: SharedTodaySnapshot? {
        guard let raw = entry.snapshot else { return nil }
        // 快照还是当天生成的才显示“今日”数字；跨天后清零计数，
        // 但保留上次喂奶时间等仍然有意义的信息。
        guard !Calendar.current.isDate(raw.generatedAt, inSameDayAs: entry.date) else {
            return raw
        }
        var reset = raw
        reset.feedingCount = 0
        reset.milkAmountML = 0
        reset.poopCount = 0
        reset.peeCount = 0
        return reset
    }

    private var title: String {
        guard let snapshot, snapshot.hasCompletedOnboarding else {
            return "小奶瓶"
        }
        return snapshot.babyName
    }

    private var primaryLine: String {
        guard let snapshot, snapshot.hasCompletedOnboarding else {
            return "先建宝宝档案"
        }
        if let reminderAt = snapshot.nextFeedingReminderAt, reminderAt > Date() {
            return "喝奶 \(relativeText(until: reminderAt))"
        }
        if let lastFeedingAt = snapshot.lastFeedingAt {
            return "上次 \(relativeText(since: lastFeedingAt))"
        }
        return "今天 \(snapshot.feedingCount) 次喂养"
    }

    private var secondaryLine: String {
        guard let snapshot, snapshot.hasCompletedOnboarding else {
            return "打开 App 后会显示今日摘要"
        }
        if snapshot.ongoingSleepStartAt != nil {
            return "睡眠进行中"
        }
        if snapshot.nextFeedingReminderAt != nil, let repeatText = repeatIntervalText(snapshot.feedingReminderRepeatIntervalMinutes) {
            return "按 \(repeatText) 节奏提醒"
        }
        return "奶量 \(snapshot.milkAmountML)ml · 排便 \(diaperCount)次"
    }

    private var inlineText: String {
        "\(title)：\(primaryLine)"
    }

    private var daysText: String {
        guard let snapshot, snapshot.hasCompletedOnboarding else {
            return "未建档"
        }
        return "第 \(snapshot.daysSinceBirth) 天"
    }

    private var diaperCount: Int {
        (snapshot?.poopCount ?? 0) + (snapshot?.peeCount ?? 0)
    }

    private var sleepStatus: String {
        snapshot?.ongoingSleepStartAt == nil ? "已记录" : "进行中"
    }

    private var sleepDetail: String {
        guard let startAt = snapshot?.ongoingSleepStartAt else {
            return "今日摘要"
        }
        return relativeText(since: startAt)
    }

    private var reminderText: String {
        guard let reminderAt = snapshot?.nextFeedingReminderAt, reminderAt > Date() else {
            return "无闹钟"
        }
        if let repeatText = repeatIntervalText(snapshot?.feedingReminderRepeatIntervalMinutes) {
            return "每\(repeatText)"
        }
        return relativeText(until: reminderAt)
    }

    private func relativeText(since date: Date) -> String {
        let minutes = max(0, Calendar.current.dateComponents([.minute], from: date, to: Date()).minute ?? 0)
        if minutes < 1 { return "刚刚" }
        if minutes < 60 { return "\(minutes)分钟前" }
        let hours = minutes / 60
        let remainingMinutes = minutes % 60
        return remainingMinutes == 0 ? "\(hours)小时前" : "\(hours)小时\(remainingMinutes)分前"
    }

    private func relativeText(until date: Date) -> String {
        let minutes = max(0, Calendar.current.dateComponents([.minute], from: Date(), to: date).minute ?? 0)
        if minutes < 1 { return "快到了" }
        if minutes < 60 { return "\(minutes)分钟后" }
        let hours = minutes / 60
        let remainingMinutes = minutes % 60
        return remainingMinutes == 0 ? "\(hours)小时后" : "\(hours)小时\(remainingMinutes)分后"
    }

    private func repeatIntervalText(_ minutes: Int?) -> String? {
        guard let minutes, minutes > 0 else { return nil }
        let hours = minutes / 60
        let remainingMinutes = minutes % 60
        if remainingMinutes == 0 {
            return "\(hours)小时"
        }
        return "\(hours)小时\(remainingMinutes)分"
    }
}

#if canImport(ActivityKit)
@available(iOS 16.2, *)
struct FeedingReminderLiveActivityWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: FeedingReminderActivityAttributes.self) { context in
            liveActivityBody(context)
                .activityBackgroundTint(.black.opacity(0.82))
                .activitySystemActionForegroundColor(.white)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    HStack(spacing: 7) {
                        avatarOrMark(size: 26)
                        Text(context.state.babyName)
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.white.opacity(0.86))
                            .lineLimit(1)
                            .frame(maxWidth: 90, alignment: .leading)
                    }
                        .padding(.leading, 8)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    repeatPill(context.state)
                        .padding(.trailing, 8)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack(alignment: .center, spacing: 14) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(reminderHeadline(context.state))
                                    .font(.headline.weight(.semibold))
                                    .foregroundStyle(.white)
                                    .lineLimit(1)
                                    .minimumScaleFactor(0.82)

                                Text(context.state.nextReminderAt, style: .time)
                                    .font(.caption2.weight(.medium))
                                    .foregroundStyle(.white.opacity(0.68))
                                    .lineLimit(1)
                            }
                            Spacer(minLength: 12)
                            VStack(alignment: .trailing, spacing: 2) {
                                if context.state.nextReminderAt > Date() {
                                    Text(String(localized: "还有"))
                                        .font(.caption2.weight(.medium))
                                        .foregroundStyle(.white.opacity(0.62))
                                    Text(context.state.nextReminderAt, style: .timer)
                                        .font(.title3.weight(.semibold))
                                        .monospacedDigit()
                                        .foregroundStyle(.white)
                                } else {
                                    Text(String(localized: "现在"))
                                        .font(.title3.weight(.semibold))
                                        .foregroundStyle(Self.milk)
                                }
                            }
                            .frame(minWidth: 74, alignment: .trailing)
                        }

                        progressBar(context.state)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 6)
                }
            } compactLeading: {
                avatarOrMark(size: 20)
            } compactTrailing: {
                compactCountdown(context.state, foreground: .white.opacity(0.94))
            } minimal: {
                avatarOrMark(size: 16)
            }
            .keylineTint(Self.coral)
        }
    }

    private func liveActivityBody(_ context: ActivityViewContext<FeedingReminderActivityAttributes>) -> some View {
        HStack(spacing: 12) {
            avatarOrMark(size: 38)
            VStack(alignment: .leading, spacing: 5) {
                Text(reminderHeadline(context.state))
                    .font(.headline.weight(.semibold))
                    .foregroundStyle(.white)
                    .lineLimit(1)
            }
            Spacer(minLength: 0)
            VStack(alignment: .trailing, spacing: 3) {
                Text(context.state.nextReminderAt, style: .time)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(.white.opacity(0.70))
                compactCountdown(context.state, foreground: .white)
                    .font(.title3.weight(.semibold))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }

    private func reminderMark(size: CGFloat) -> some View {
        ZStack {
            Circle()
                .fill(Self.milk.opacity(0.95))
            Circle()
                .stroke(Self.coral.opacity(0.34), lineWidth: 1)
            Image(systemName: "waterbottle.fill")
                .font(.system(size: size * 0.50, weight: .semibold))
                .foregroundStyle(Self.coral)
            if size >= 24 {
                Image(systemName: "heart.fill")
                    .font(.system(size: size * 0.18, weight: .bold))
                    .foregroundStyle(Self.coral.opacity(0.86))
                    .offset(x: size * 0.25, y: -size * 0.24)
            }
        }
        .frame(width: size, height: size)
    }

    @ViewBuilder
    private func avatarOrMark(size: CGFloat) -> some View {
        if let avatarData = XiaoNaiPingSharedStore.readLiveActivityAvatarData(),
           let image = UIImage(data: avatarData) {
            Image(uiImage: image)
                .resizable()
                .scaledToFill()
                .frame(width: size, height: size)
                .clipShape(Circle())
                .overlay {
                    Circle().stroke(Self.milk.opacity(0.96), lineWidth: 1.4)
                }
        } else {
            reminderMark(size: size)
        }
    }

    @ViewBuilder
    private func compactCountdown(_ state: FeedingReminderActivityAttributes.ContentState, foreground: Color) -> some View {
        if reminderPhase(state) == .waiting {
            Text(state.nextReminderAt, style: .timer)
                .font(.caption2.weight(.semibold))
                .monospacedDigit()
                .foregroundStyle(foreground)
                .lineLimit(1)
                .minimumScaleFactor(0.78)
                .frame(maxWidth: 52, alignment: .trailing)
        } else {
            Text(compactStatusText(state))
                .font(.caption2.weight(.semibold))
                .monospacedDigit()
                .foregroundStyle(Self.milk)
                .lineLimit(1)
                .minimumScaleFactor(0.78)
                .frame(maxWidth: 52, alignment: .trailing)
        }
    }

    private func repeatPill(_ state: FeedingReminderActivityAttributes.ContentState) -> some View {
        Text(repeatPillText(state.repeatIntervalMinutes))
            .font(.caption2.weight(.semibold))
            .foregroundStyle(.white.opacity(0.92))
            .lineLimit(1)
            .padding(.horizontal, 9)
            .padding(.vertical, 5)
            .background(Self.coral.opacity(0.34), in: Capsule())
            .overlay {
                Capsule().stroke(.white.opacity(0.10), lineWidth: 1)
            }
    }

    private func reminderHeadline(_ state: FeedingReminderActivityAttributes.ContentState) -> String {
        switch reminderPhase(state) {
        case .due:
            return String(localized: "该喝奶啦")
        case .preparing:
            return String(localized: "准备泡奶啦")
        case .waiting:
            return String(localized: "下次喝奶")
        }
    }

    private func repeatPillText(_ minutes: Int?) -> String {
        guard let repeatText = repeatIntervalText(minutes) else {
            return String(localized: "一次")
        }
        return String(format: String(localized: "每%@"), repeatText)
    }

    private func compactStatusText(_ state: FeedingReminderActivityAttributes.ContentState) -> String {
        switch reminderPhase(state) {
        case .due:
            return String(localized: "喝奶")
        case .preparing:
            return String(localized: "泡奶")
        case .waiting:
            return shortCountdownText(until: state.nextReminderAt)
        }
    }

    private func shortCountdownText(until date: Date) -> String {
        let seconds = max(0, date.timeIntervalSinceNow)
        let minutes = max(1, Int(ceil(seconds / 60)))
        if minutes >= 60 {
            let hours = max(1, Int(ceil(Double(minutes) / 60.0)))
            return "\(hours)h"
        }
        return "\(minutes)m"
    }

    private func reminderPhase(_ state: FeedingReminderActivityAttributes.ContentState) -> ReminderPhase {
        let now = Date()
        if state.nextReminderAt <= now {
            return .due
        }
        let prepareAt = Calendar.current.date(
            byAdding: .minute,
            value: -Self.prepareReminderLeadMinutes,
            to: state.nextReminderAt
        ) ?? state.nextReminderAt
        return prepareAt <= now ? .preparing : .waiting
    }

    private func progressBar(_ state: FeedingReminderActivityAttributes.ContentState) -> some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                Capsule()
                    .fill(.white.opacity(0.14))
                Capsule()
                    .fill(Self.milk.opacity(0.86))
                    .frame(width: geometry.size.width * reminderProgress(state))
            }
        }
        .frame(maxWidth: .infinity)
        .frame(height: 4)
    }

    private func reminderProgress(_ state: FeedingReminderActivityAttributes.ContentState) -> CGFloat {
        if state.nextReminderAt <= Date() {
            return 1
        }

        let totalSeconds: TimeInterval
        if let repeatIntervalMinutes = state.repeatIntervalMinutes, repeatIntervalMinutes > 0 {
            totalSeconds = TimeInterval(repeatIntervalMinutes * 60)
        } else {
            totalSeconds = TimeInterval(Self.prepareReminderLeadMinutes * 60)
        }

        let startAt = state.nextReminderAt.addingTimeInterval(-totalSeconds)
        let elapsed = Date().timeIntervalSince(startAt)
        let progress = elapsed / totalSeconds
        return min(max(CGFloat(progress), 0.08), 1)
    }

    private func repeatIntervalText(_ minutes: Int?) -> String? {
        guard let minutes, minutes > 0 else { return nil }
        let hours = minutes / 60
        let remainingMinutes = minutes % 60
        if remainingMinutes == 0 {
            return String(format: String(localized: "%d小时"), hours)
        }
        return String(format: String(localized: "%d小时%d分"), hours, remainingMinutes)
    }

    private static let milk = Color(red: 1.0, green: 0.972, blue: 0.925)
    private static let coral = Color(red: 0.875, green: 0.360, blue: 0.290)
    private static let ink = Color(red: 0.235, green: 0.225, blue: 0.205)
    private static let inkSoft = Color(red: 0.410, green: 0.390, blue: 0.340)
    private static let inkGreen = Color(red: 0.220, green: 0.350, blue: 0.230)
    private static let prepareReminderLeadMinutes = 5

    private enum ReminderPhase {
        case waiting
        case preparing
        case due
    }
}
#endif

struct XiaoNaiPingTodayWidget: Widget {
    let kind = "XiaoNaiPingTodayWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: TodayProvider()) { entry in
            XiaoNaiPingTodayWidgetView(entry: entry)
        }
        .configurationDisplayName("小奶瓶今日")
        .description("查看今日喂养、睡眠、排便和下一次喝奶提醒。")
        .supportedFamilies([.systemSmall, .systemMedium, .accessoryCircular, .accessoryRectangular, .accessoryInline])
    }
}

@main
struct XiaoNaiPingWidgetsBundle: WidgetBundle {
    var body: some Widget {
        XiaoNaiPingTodayWidget()
        if #available(iOS 16.2, *) {
            FeedingReminderLiveActivityWidget()
        }
    }
}
