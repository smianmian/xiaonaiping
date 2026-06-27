import Foundation

struct Milestone: Identifiable, Equatable, Codable {
    var id = UUID()
    var title: String
    var date: String
    var icon: String
    var note: String? = nil
}

struct AutomaticMilestone: Identifiable {
    let title: String
    let dayNumber: Int
    let date: Date
    let daysRemaining: Int
    let isReached: Bool

    var id: Int { dayNumber }
}
