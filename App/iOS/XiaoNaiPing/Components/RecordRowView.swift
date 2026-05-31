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
                .frame(width: 42, height: 42)
            Text(time)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.inkGreen)
                .frame(width: 76, alignment: .leading)
            Text(title)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.ink)
            Spacer(minLength: AppSpacing.small)
            Text(detail)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.ink)
                .multilineTextAlignment(.trailing)
        }
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, 13)
        .background {
            CardBackground(tint: tint, cornerRadius: 22)
        }
    }
}
