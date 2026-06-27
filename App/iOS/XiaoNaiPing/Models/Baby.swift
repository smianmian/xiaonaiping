import Foundation

struct Baby: Identifiable, Equatable, Codable {
    var id: UUID
    var name: String
    var daysSinceBirth: Int
    var ageText: String
    var birthDate: Date = Calendar.current.date(byAdding: .day, value: -68, to: Date()) ?? Date()
    var sex: String = "未设置"
    var avatarImageData: Data? = nil
}
