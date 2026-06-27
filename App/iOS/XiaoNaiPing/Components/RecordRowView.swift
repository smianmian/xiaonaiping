import SwiftUI

struct RecordRowView: View {
    let icon: String
    let time: String
    let title: String
    let detail: String
    var tint: Color = AppColors.cream

    var body: some View {
        HStack(spacing: AppSpacing.medium) {
            AssetWatercolorImage(name: icon, mode: .multiply)
                .frame(width: 36, height: 36)
            Text(time)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.inkGreen)
                .frame(width: 76, alignment: .leading)
            Text(title.localizedText)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.ink)
            Spacer(minLength: AppSpacing.small)
            Text(detail.localizedText)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.ink)
                .multilineTextAlignment(.trailing)
        }
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, 11)
        .background {
            CardBackground(tint: tint, cornerRadius: 20)
        }
    }
}
