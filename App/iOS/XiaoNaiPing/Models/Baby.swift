import Foundation

struct Baby: Identifiable, Equatable {
    let id: UUID
    var name: String
    var daysSinceBirth: Int
    var ageText: String
}

