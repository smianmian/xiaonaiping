import SwiftUI

struct PrimaryWatercolorButton: View {
    let title: String
    var tint: Color = AppColors.blush
    var foreground: Color = AppColors.coral
    var action: () -> Void = {}

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(foreground)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 15)
                .background {
                    Capsule()
                        .fill(tint.opacity(0.70))
                        .overlay {
                            Capsule()
                                .stroke(foreground.opacity(0.24), lineWidth: 1)
                        }
                }
        }
        .buttonStyle(.plain)
    }
}

