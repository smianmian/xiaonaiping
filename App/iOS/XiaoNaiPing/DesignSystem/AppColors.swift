import SwiftUI
import UIKit

enum AppColors {
    static let paper = adaptive(light: (0.992, 0.965, 0.918), dark: (0.075, 0.083, 0.090))
    static let paperDeep = adaptive(light: (0.955, 0.915, 0.852), dark: (0.105, 0.115, 0.120))
    static let cream = adaptive(light: (1.000, 0.980, 0.940), dark: (0.115, 0.123, 0.130))
    static let milk = adaptive(light: (1.000, 0.988, 0.960), dark: (0.135, 0.145, 0.152))
    static let blush = adaptive(light: (1.000, 0.905, 0.895), dark: (0.190, 0.125, 0.132))
    static let blushDeep = Color(red: 0.948, green: 0.455, blue: 0.388)
    static let mistBlue = adaptive(light: (0.875, 0.925, 0.985), dark: (0.105, 0.155, 0.205))
    static let grass = adaptive(light: (0.882, 0.925, 0.820), dark: (0.120, 0.180, 0.125))
    static let sage = Color(red: 0.580, green: 0.665, blue: 0.505)
    static let butter = Color(red: 1.000, green: 0.935, blue: 0.690)
    static let peach = Color(red: 0.988, green: 0.760, blue: 0.620)
    static let coral = Color(red: 0.875, green: 0.360, blue: 0.290)
    static let blueInk = Color(red: 0.270, green: 0.505, blue: 0.760)
    static let ink = adaptive(light: (0.235, 0.225, 0.205), dark: (0.930, 0.925, 0.900))
    static let inkSoft = adaptive(light: (0.410, 0.390, 0.340), dark: (0.720, 0.725, 0.700))
    static let inkGreen = adaptive(light: (0.220, 0.350, 0.230), dark: (0.730, 0.860, 0.740))
    static let tabMuted = adaptive(light: (0.440, 0.515, 0.410), dark: (0.690, 0.760, 0.680))
    static let softStroke = adaptive(light: (0.790, 0.715, 0.620), dark: (0.310, 0.330, 0.330))
    static let porcelain = adaptive(light: (0.988, 0.976, 0.957), dark: (0.110, 0.118, 0.125))
    static let hairline = adaptive(light: (0.922, 0.878, 0.831), dark: (0.280, 0.295, 0.300))

    private static func adaptive(light: (CGFloat, CGFloat, CGFloat), dark: (CGFloat, CGFloat, CGFloat)) -> Color {
        Color(UIColor { trait in
            let value = trait.userInterfaceStyle == .dark ? dark : light
            return UIColor(red: value.0, green: value.1, blue: value.2, alpha: 1)
        })
    }
}
