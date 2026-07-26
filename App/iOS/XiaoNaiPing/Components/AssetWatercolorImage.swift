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
            // 水彩插画全部是装饰性的：不让 VoiceOver 朗读
            // "approvedFeedingBottle" 这类资源名。语义由所在控件的 label 承担。
            .accessibilityHidden(true)
    }
}
