import SwiftUI

enum AppTab: String, CaseIterable, Identifiable {
    case home = "今天"
    case growth = "成长"
    case record = "记录"
    case profile = "设置"

    var id: String { rawValue }

    var iconAsset: String {
        switch self {
        case .home:
            AppAssets.tabHomeDrawing
        case .growth:
            AppAssets.quickGrowthIcon
        case .record:
            AppAssets.tabRecordDrawing
        case .profile:
            AppAssets.tabProfileDrawing
        }
    }

    var systemImage: String {
        switch self {
        case .home:
            "house"
        case .growth:
            "chart.line.uptrend.xyaxis"
        case .record:
            "square.and.pencil"
        case .profile:
            "person"
        }
    }
}

