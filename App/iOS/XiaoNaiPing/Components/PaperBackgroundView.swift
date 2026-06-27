import SwiftUI

struct PaperBackgroundView: View {
    var body: some View {
        AppColors.paper
            .ignoresSafeArea()
            .overlay {
                Image(AppAssets.paperTexture)
                    .resizable(resizingMode: .tile)
                    .opacity(0.08)
                    .ignoresSafeArea()
            }
    }
}
