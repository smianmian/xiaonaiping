import Foundation

enum AppSpacing {
    static let tiny: CGFloat = 4
    static let small: CGFloat = 8
    static let regular: CGFloat = 10
    static let medium: CGFloat = 14
    static let roomy: CGFloat = 18
    static let large: CGFloat = 20
    static let xlarge: CGFloat = 28
    static let page: CGFloat = 20
    // Leave enough room for the tab bar and the home indicator when a scroll
    // view is hosted inside a tab. Detail pages use the same spacing so their
    // last row remains reachable without relying on a page-specific tweak.
    static let bottomBarSpace: CGFloat = 88
}

enum AppLayout {
    static let homeTopAdjustment: CGFloat = -8
    static let sectionSpacing: CGFloat = 18
    static let titleToContentSpacing: CGFloat = 12
    static let cardRadius: CGFloat = 24
    static let statusCardRadius: CGFloat = 28
    static let headerAvatar: CGFloat = 92
    static let stateCardHeight: CGFloat = 150
    static let overviewCardHeight: CGFloat = 100
    static let stateArtworkWidth: CGFloat = 96
    static let stateArtworkHeight: CGFloat = 72
    static let overviewArtwork: CGFloat = 84
    static let quickArtwork: CGFloat = 96
    static let quickCardHeight: CGFloat = 112
    static let recentArtwork: CGFloat = 32
}
