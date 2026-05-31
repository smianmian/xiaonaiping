import SwiftUI

struct ScreenScaffold<Content: View>: View {
    var title: String? = nil
    var trailingTitle: String? = nil
    var showBackButton: Bool = false
    var trailingAction: (() -> Void)?
    @Environment(\.dismiss) private var dismiss
    @ViewBuilder var content: Content

    var body: some View {
        ZStack {
            PaperBackgroundView()

            VStack(spacing: 0) {
                if title != nil || showBackButton || trailingTitle != nil {
                    HStack {
                        if showBackButton {
                            Button {
                                dismiss()
                            } label: {
                                Image(systemName: "chevron.left")
                                    .font(.system(size: 24, weight: .regular))
                                    .foregroundStyle(AppColors.inkGreen)
                                    .frame(width: 44, height: 44)
                            }
                        } else {
                            Color.clear.frame(width: 44, height: 44)
                        }

                        Spacer()

                        if let title {
                            Text(title)
                                .font(AppTypography.navTitle)
                                .foregroundStyle(AppColors.inkGreen)
                        }

                        Spacer()

                        if let trailingTitle {
                            Button {
                                trailingAction?()
                            } label: {
                                Text(trailingTitle)
                                    .font(AppTypography.bodyLarge)
                                    .foregroundStyle(AppColors.inkGreen)
                                    .frame(width: 64, height: 44, alignment: .trailing)
                            }
                        } else {
                            Color.clear.frame(width: 44, height: 44)
                        }
                    }
                    .padding(.horizontal, AppSpacing.medium)
                    .padding(.top, AppSpacing.medium)
                    .padding(.bottom, AppSpacing.small)
                }

                content
            }
        }
        .navigationBarBackButtonHidden(true)
        .toolbar(.hidden, for: .navigationBar)
    }
}
