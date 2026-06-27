import SwiftUI

struct ScreenScaffold<Content: View>: View {
    var title: String? = nil
    var trailingTitle: String? = nil
    var showBackButton: Bool = false
    var trailingAction: (() -> Void)?
    @ViewBuilder var content: Content

    var body: some View {
        ZStack {
            PaperBackgroundView()
            content
        }
        .modifier(ScreenNavigationModifier(
            title: title,
            trailingTitle: trailingTitle,
            showBackButton: showBackButton,
            trailingAction: trailingAction
        ))
    }
}

private struct ScreenNavigationModifier: ViewModifier {
    let title: String?
    let trailingTitle: String?
    let showBackButton: Bool
    let trailingAction: (() -> Void)?

    @ViewBuilder
    func body(content: Content) -> some View {
        if let title {
            content
                .navigationTitle(title)
                .navigationBarTitleDisplayMode(.inline)
                .navigationBarBackButtonHidden(!showBackButton)
                .toolbar {
                    if let trailingTitle, let trailingAction {
                        ToolbarItem(placement: .topBarTrailing) {
                            Button(trailingTitle) {
                                trailingAction()
                            }
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                        }
                    }
                }
                .tint(AppColors.coral)
                .toolbarBackground(AppColors.paper, for: .navigationBar)
                .toolbarBackground(.visible, for: .navigationBar)
        } else {
            content
                .toolbar(.hidden, for: .navigationBar)
        }
    }
}
