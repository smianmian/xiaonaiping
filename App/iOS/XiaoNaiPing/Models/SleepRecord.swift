import Foundation

struct SleepRecord: Identifiable, Equatable {
    var id = UUID()
    var start: String
    var end: String
    var type: String
    var duration: String
    var icon: String
    var durationMinutes: Int? = nil
    var isOngoing: Bool = false
    var note: String? = nil
}
