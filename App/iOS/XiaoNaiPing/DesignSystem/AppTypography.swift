import SwiftUI

enum AppTypography {
    private static let handRegular = "DFWaWaSC-W5"
    private static let handMedium = "DFWaWaSC-W5"
    private static let numberHand = "HanziPenSC-W3"
    private static let readableRegular = "PingFangSC-Regular"
    private static let readableMedium = "PingFangSC-Medium"

    static let navTitle = Font.custom(handMedium, size: 26, relativeTo: .title)
    static let title = Font.custom(handMedium, size: 24, relativeTo: .title)
    static let sectionTitle = Font.custom(handMedium, size: 21, relativeTo: .title2)
    static let cardTitle = Font.custom(handRegular, size: 17, relativeTo: .headline)
    static let body = Font.custom(handRegular, size: 16, relativeTo: .body)
    static let bodyLarge = Font.custom(handRegular, size: 18, relativeTo: .title3)
    static let quietBody = Font.custom(handRegular, size: 17, relativeTo: .body)
    static let quietBodyLarge = Font.custom(handRegular, size: 20, relativeTo: .title3)
    static let caption = Font.custom(readableRegular, size: 12, relativeTo: .caption)
    static let tab = Font.custom(handMedium, size: 12, relativeTo: .caption)
    static let largeNumber = Font.custom(numberHand, size: 38, relativeTo: .largeTitle)
    static let heroTitle = Font.custom(handMedium, size: 32, relativeTo: .largeTitle)
    static let heroUnit = Font.custom(handMedium, size: 28, relativeTo: .title)
    static let heroNumber = Font.custom(numberHand, size: 58, relativeTo: .largeTitle)
    static let readableBody = Font.custom(readableRegular, size: 16, relativeTo: .body)
    static let readableBodyMedium = Font.custom(readableMedium, size: 16, relativeTo: .body)
}
