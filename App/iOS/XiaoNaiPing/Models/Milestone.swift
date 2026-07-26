import Foundation

struct Milestone: Identifiable, Equatable, Codable {
    var id = UUID()
    var title: String
    var date: String
    var icon: String
    var note: String? = nil

    private enum CodingKeys: String, CodingKey {
        case id
        case title
        case date
        case icon
        case note
    }
}

extension Milestone {
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        title = try container.decodeIfPresent(String.self, forKey: .title) ?? ""
        date = try container.decodeIfPresent(String.self, forKey: .date) ?? ""
        icon = try container.decodeIfPresent(String.self, forKey: .icon) ?? ""
        note = try container.decodeIfPresent(String.self, forKey: .note)
    }
}

struct AutomaticMilestone: Identifiable {
    let title: String
    let dayNumber: Int
    let date: Date
    let daysRemaining: Int
    let isReached: Bool

    var id: Int { dayNumber }
}
