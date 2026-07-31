import SwiftUI

struct SegmentedPill: View {
    let items: [String]
    @Binding var selected: String

    var body: some View {
        HStack(spacing: 0) {
            ForEach(items, id: \.self) { item in
                Button {
                    selected = item
                } label: {
                    Text(item.localizedText)
                        .font(AppTypography.readableBodyMedium)
                        .foregroundStyle(selected == item ? AppColors.coral : AppColors.inkGreen)
                        .frame(maxWidth: .infinity)
                        .frame(minHeight: 48)
                        .background {
                            if selected == item {
                                Capsule()
                                    .fill(AppColors.blush.opacity(0.65))
                            }
                        }
                }
                .buttonStyle(.plain)
            }
        }
        .padding(4)
        .background {
            Capsule()
                .fill(AppColors.cream.opacity(0.62))
                .overlay {
                    Capsule()
                        .stroke(AppColors.softStroke.opacity(0.30), lineWidth: 1)
                }
        }
    }
}
