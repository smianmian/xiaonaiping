import SwiftUI

struct PrimaryWatercolorButton: View {
    let title: String
    var tint: Color = AppColors.blush
    var foreground: Color = AppColors.coral
    var action: () -> Void = {}

    var body: some View {
        Button(action: action) {
            Text(title.localizedText)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(foreground)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 13)
                .background {
                    RoundedRectangle(cornerRadius: AppShapes.largeCardRadius, style: .continuous)
                        .fill(tint.opacity(0.70))
                        .overlay {
                            RoundedRectangle(cornerRadius: AppShapes.largeCardRadius, style: .continuous)
                                .stroke(foreground.opacity(0.24), lineWidth: 1)
                        }
                }
        }
        .buttonStyle(.plain)
    }
}
