import Foundation

struct DiaperRecord: Identifiable, Equatable {
    var id = UUID()
    var time: String
    var title: String
    var icon: String
    var kind: String = "大便"
    var color: String? = nil
    var texture: String? = nil
    var note: String? = nil
}
