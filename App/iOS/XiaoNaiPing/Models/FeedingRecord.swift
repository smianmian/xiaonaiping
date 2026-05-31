import Foundation

struct FeedingRecord: Identifiable, Equatable {
    var id = UUID()
    var time: String
    var type: String
    var detail: String
    var icon: String
    var amountML: Int? = nil
    var durationMinutes: Int? = nil
    var note: String? = nil
}
