import Foundation

struct VaccineRecord: Identifiable, Equatable {
    var id = UUID()
    var title: String
    var status: String
    var tintName: String
    var icon: String
    var dueText: String = ""
    var dueDays: Int? = nil
    var region: String? = nil
    var note: String? = nil
}
