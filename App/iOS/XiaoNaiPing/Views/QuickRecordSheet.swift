import SwiftUI

enum QuickRecordAction: CaseIterable, Identifiable {
    case feeding, water, sleep, diaper, photo, growth, milestone

    var id: String { title }

    var title: String {
        switch self {
        case .feeding: "喂养"
        case .water: "喝水"
        case .sleep: "睡眠"
        case .diaper: "排便"
        case .photo: "照片"
        case .growth: "身高体重"
        case .milestone: "纪念日"
        }
    }

    var asset: String? {
        switch self {
        case .feeding: "feedingBottle"
        case .sleep: "sleepMoon"
        case .diaper: "diaperPoop"
        case .water: "waterDrop"
        case .photo: "cameraPink"
        case .growth: "rulerScale"
        case .milestone: nil
        }
    }

    // Natural artwork heights in points, taken from the approved mockup so the
    // six illustrations keep their relative scale instead of filling one slot.
    var artHeight: CGFloat {
        switch self {
        case .feeding: 81
        case .sleep: 69
        case .diaper: 68
        case .water: 70
        case .photo: 63
        case .growth: 65
        case .milestone: 44
        }
    }

    var systemIcon: String? {
        switch self {
        case .milestone: "rosette"
        default: nil
        }
    }

    var tint: Color {
        switch self {
        case .feeding: AppColors.blush
        case .sleep: Color(red: 0.90, green: 0.88, blue: 0.98)
        case .diaper: AppColors.grass
        case .water: AppColors.mistBlue
        case .photo: AppColors.cream
        case .growth: Color(red: 0.87, green: 0.94, blue: 0.94)
        case .milestone: AppColors.cream
        }
    }
}

struct QuickRecordSheet: View {
    let onSelect: (QuickRecordAction) -> Void
    @Environment(\.dismiss) private var dismiss

    private let primaryActions: [QuickRecordAction] = [.feeding, .sleep, .diaper, .water, .photo, .growth]

    // Geometry measured on the approved mockup (863px wide ≈ 2.2px/pt).
    private enum Metrics {
        static let pageMargin: CGFloat = 25
        static let columnGap: CGFloat = 11
        static let rowGap: CGFloat = 8
        static let cardHeight: CGFloat = 94
        static let cardRadius: CGFloat = 14
        static let iconSlot: CGFloat = 87
        static let chevronInset: CGFloat = 14
        static let titleTopGap: CGFloat = 37
        static let titleToGrid: CGFloat = 19
        static let cancelTopGap: CGFloat = 16
    }

    var body: some View {
        VStack(spacing: 0) {
            header
                .padding(.top, Metrics.titleTopGap)
            grid
                .padding(.top, Metrics.titleToGrid)
            cancelButton
                .padding(.top, Metrics.cancelTopGap)
            Spacer(minLength: 0)
        }
        .padding(.horizontal, Metrics.pageMargin)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        .background(AppColors.porcelain.ignoresSafeArea())
    }

    private var header: some View {
        HStack(spacing: 12) {
            AssetWatercolorImage(name: "decoSprigLeft")
                .frame(height: 13)
            Text("快速记录")
                .font(AppTypography.quickSheetTitle)
                .foregroundStyle(AppColors.inkGreen)
            AssetWatercolorImage(name: "decoSprigRight")
                .frame(height: 13)
        }
        .frame(maxWidth: .infinity)
    }

    private var grid: some View {
        LazyVGrid(
            columns: [GridItem(.flexible(), spacing: Metrics.columnGap), GridItem(.flexible())],
            spacing: Metrics.rowGap
        ) {
            ForEach(primaryActions) { action in
                quickCard(action)
            }
        }
    }

    private var cancelButton: some View {
        Button("取消") { dismiss() }
            .font(AppTypography.quickSheetCancel)
            .foregroundStyle(AppColors.inkSoft)
            .frame(maxWidth: .infinity)
            .frame(height: 34)
    }

    private func quickCard(_ action: QuickRecordAction) -> some View {
        Button {
            onSelect(action)
            dismiss()
        } label: {
            HStack(spacing: 0) {
                actionArtwork(action)
                    .frame(width: Metrics.iconSlot)
                Text(action.title)
                    .font(AppTypography.homeCardTitle)
                    .foregroundStyle(AppColors.ink)
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)
                    .layoutPriority(1)
                Spacer(minLength: AppSpacing.tiny)
                Image(systemName: "chevron.right")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(AppColors.inkGreen.opacity(0.72))
                    .padding(.trailing, Metrics.chevronInset)
            }
            .frame(maxWidth: .infinity)
            .frame(height: Metrics.cardHeight)
            .background(AppColors.porcelain, in: RoundedRectangle(cornerRadius: Metrics.cardRadius, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: Metrics.cardRadius, style: .continuous)
                    .stroke(AppColors.hairline, lineWidth: 1)
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel("记录\(action.title)")
    }

    @ViewBuilder
    private func actionArtwork(_ action: QuickRecordAction) -> some View {
        if let asset = action.asset {
            AssetWatercolorImage(name: asset)
                .frame(height: action.artHeight)
        } else if let systemIcon = action.systemIcon {
            Image(systemName: systemIcon)
                .font(.system(size: 30, weight: .semibold))
                .foregroundStyle(AppColors.coral.opacity(0.82))
                .frame(width: 56, height: 56)
                .background(AppColors.milk, in: Circle())
        }
    }
}
