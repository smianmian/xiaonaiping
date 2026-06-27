import SwiftUI

struct WatercolorCard<Content: View>: View {
    let tint: Color
    var cornerRadius: CGFloat = AppShapes.cardRadius
    var padding: CGFloat = AppSpacing.roomy
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(padding)
            .background {
                CardBackground(tint: tint, cornerRadius: cornerRadius)
            }
    }
}

struct CardBackground: View {
    let tint: Color
    var cornerRadius: CGFloat = AppShapes.cardRadius

    var body: some View {
        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
            .fill(tint.opacity(0.62))
            .overlay {
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .stroke(AppColors.softStroke.opacity(0.33), lineWidth: 1)
            }
            .shadow(color: .brown.opacity(0.045), radius: 4, y: 2)
    }
}
