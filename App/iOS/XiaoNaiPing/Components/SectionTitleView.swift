import SwiftUI

struct SectionTitleView: View {
    let title: String

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.tiny) {
            Text(title)
                .font(AppTypography.sectionTitle)
                .foregroundStyle(AppColors.inkGreen)
            Capsule()
                .fill(AppColors.blushDeep.opacity(0.55))
                .frame(width: 58, height: 3)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

