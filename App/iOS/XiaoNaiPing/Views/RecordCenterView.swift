import SwiftUI

/// 「记录」tab 的真实落地页：全部记录类别的常驻大卡入口。
/// 之前这个 tab 只弹快速记录浮层，点取消就哪儿也去不了。
struct RecordCenterView: View {
    let onRoute: (AppRoute) -> Void
    @EnvironmentObject private var store: BabyRecordStore

    private struct Entry: Identifiable {
        let title: String
        let asset: String?
        let systemIcon: String?
        let artHeight: CGFloat
        let route: AppRoute
        var id: String { title }
    }

    private let entries: [Entry] = [
        Entry(title: "喂养", asset: "feedingBottle", systemIcon: nil, artHeight: 66, route: .feeding),
        Entry(title: "睡眠", asset: "sleepMoon", systemIcon: nil, artHeight: 56, route: .sleep),
        Entry(title: "排便", asset: "diaperPoop", systemIcon: nil, artHeight: 56, route: .diaper),
        Entry(title: "喝水", asset: "waterDrop", systemIcon: nil, artHeight: 58, route: .water),
        Entry(title: "照片", asset: "cameraPink", systemIcon: nil, artHeight: 52, route: .album),
        Entry(title: "身高体重", asset: "rulerScale", systemIcon: nil, artHeight: 54, route: .growth),
        Entry(title: "健康观察", asset: "recordHealthStethoscope", systemIcon: nil, artHeight: 58, route: .health),
        Entry(title: "纪念日", asset: "recordMilestoneMedal", systemIcon: nil, artHeight: 58, route: .milestone)
    ]

    var body: some View {
        ScreenScaffold(title: "记录") {
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: AppSpacing.large) {
                    Text(todaySummaryText)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.inkSoft)

                    LazyVGrid(
                        columns: [
                            GridItem(.flexible(), spacing: AppSpacing.medium),
                            GridItem(.flexible(), spacing: AppSpacing.medium)
                        ],
                        spacing: AppSpacing.medium
                    ) {
                        ForEach(entries) { entry in
                            entryCard(entry)
                        }
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.medium)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
    }

    private var todaySummaryText: String {
        let count = store.todayFeedingRecords.count
            + store.todaySleepRecords.count
            + store.todayDiaperRecords.count
            + store.todayWaterRecords.count
        return count == 0 ? "今天还没有记录，从下面选一类开始。" : "今天已记 \(count) 条，继续保持。"
    }

    private func entryCard(_ entry: Entry) -> some View {
        Button {
            onRoute(entry.route)
        } label: {
            VStack(spacing: AppSpacing.small) {
                Group {
                    if let asset = entry.asset {
                        AssetWatercolorImage(name: asset)
                            .frame(height: entry.artHeight)
                    } else if let systemIcon = entry.systemIcon {
                        Image(systemName: systemIcon)
                            .font(.system(size: 30, weight: .regular))
                            .foregroundStyle(AppColors.coral.opacity(0.82))
                    }
                }
                .frame(height: 70)

                Text(entry.title)
                    .font(AppTypography.homeCardTitle)
                    .foregroundStyle(AppColors.ink)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            .padding(.vertical, AppSpacing.regular)
            .frame(maxWidth: .infinity, minHeight: 128)
            .background {
                CardBackground(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius)
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel("打开\(entry.title)")
    }
}
