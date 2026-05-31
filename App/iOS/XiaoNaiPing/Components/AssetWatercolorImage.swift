import SwiftUI

struct AssetWatercolorImage: View {
    let name: String
    var mode: BlendMode = .normal

    var body: some View {
        Image(name)
            .resizable()
            .scaledToFit()
            .blendMode(mode)
            .allowsHitTesting(false)
    }
}

