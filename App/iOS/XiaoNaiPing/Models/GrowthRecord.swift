import Foundation

struct GrowthRecord: Identifiable, Equatable {
    var id = UUID()
    var month: String
    var weight: Double
    var height: Double
    var head: Double
    var measuredAt: String = ""
    var note: String? = nil
}
