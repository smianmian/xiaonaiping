import Foundation

struct Milestone: Identifiable, Equatable {
    var id = UUID()
    var title: String
    var date: String
    var icon: String
    var note: String? = nil
}
