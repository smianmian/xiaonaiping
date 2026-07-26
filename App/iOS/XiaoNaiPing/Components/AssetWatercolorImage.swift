import SwiftUI

struct AssetWatercolorImage: View {
    let name: String
    var mode: BlendMode = .normal

    var body: some View {
        Image(name)
            .renderingMode(.original)
            .resizable()
            .scaledToFit()
            .allowsHitTesting(false)
    }
}
