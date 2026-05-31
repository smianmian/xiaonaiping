import SwiftUI

struct PaperBackgroundView: View {
    var body: some View {
        AppColors.paper
            .ignoresSafeArea()
            .overlay {
                Image(AppAssets.paperTexture)
                    .resizable(resizingMode: .tile)
                    .opacity(0.13)
                    .ignoresSafeArea()
            }
            .overlay {
                Canvas { context, size in
                    for index in 0..<46 {
                        let x = CGFloat((index * 53) % 997) / 997 * size.width
                        let y = CGFloat((index * 97) % 1543) / 1543 * size.height
                        let opacity = Double((index % 4) + 1) * 0.004
                        let rect = CGRect(x: x, y: y, width: 1.2, height: 14)
                        context.opacity = opacity
                        context.fill(Path(ellipseIn: rect), with: .color(.brown))
                    }
                }
                .blendMode(.multiply)
            }
    }
}
