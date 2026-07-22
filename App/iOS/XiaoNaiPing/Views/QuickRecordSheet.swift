import SwiftUI

enum QuickRecordAction: CaseIterable, Identifiable {
    case feeding
    case water
    case sleep
    case diaper
    case photo
    case growth
    case milestone

    var id: String { title }

    var title: String {
        switch self {
        case .feeding: "喂养"
        case .water: "喝水"
        case .sleep: "睡眠"
        case .diaper: "排便"
        case .photo: "照片"
        case .growth: "身高体重"
        case .milestone: "纪念日"
        }
    }

    var asset: String? {
        switch self {
        case .feeding: AppAssets.bottleIcon
        case .water: nil
        case .sleep: AppAssets.moonIcon
        case .diaper: AppAssets.diaperIcon
        case .photo: AppAssets.cameraIcon
        case .growth: AppAssets.quickGrowthIcon
        case .milestone: AppAssets.milestoneMedalIcon
        }
    }

    var systemIcon: String? {
        switch self {
        case .water: "drop.fill"
        default: nil
        }
    }

    var tint: Color {
        switch self {
        case .feeding: AppColors.cream
        case .water: AppColors.mistBlue
        case .sleep: AppColors.mistBlue
        case .diaper: AppColors.grass
        case .photo: AppColors.blush
        case .growth: Color(red: 0.925, green: 0.885, blue: 0.955)
        case .milestone: Color(red: 1.0, green: 0.925, blue: 0.840)
        }
    }
}
