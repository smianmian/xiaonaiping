import Foundation

struct VaccineRecord: Identifiable, Equatable, Codable {
    static let pendingStatus = "待接种"
    static let bookedStatus = "已预约"
    static let administeredStatus = "已接种"
    static let legacyCompletedStatus = "已完成"

    var id = UUID()
    var title: String
    var status: String
    var tintName: String
    var icon: String
    var dueText: String = ""
    var dueDays: Int? = nil
    var region: String? = nil
    var note: String? = nil
    var administeredAt: Date? = nil

    var isAdministered: Bool {
        status == Self.administeredStatus || status == Self.legacyCompletedStatus
    }

    var displayStatus: String {
        isAdministered ? Self.administeredStatus : status
    }
}
