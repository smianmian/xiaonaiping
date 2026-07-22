import Foundation

enum PhotoSyncStatus: String, Codable, Equatable {
    case localOnly
    case pending
    case backedUp
    case failed
    case cloudDeletePending
}

struct BabyPhoto: Identifiable, Equatable, Codable {
    var id = UUID()
    var capturedAt: Date
    var localFileName: String
    var source: String
    var note: String = ""
    var syncStatus: PhotoSyncStatus = .localOnly

    var displayMonth: String {
        BabyRecordStore.monthString(from: capturedAt)
    }

    init(
        id: UUID = UUID(),
        capturedAt: Date,
        localFileName: String,
        source: String,
        note: String = "",
        syncStatus: PhotoSyncStatus = .localOnly
    ) {
        self.id = id
        self.capturedAt = capturedAt
        self.localFileName = localFileName
        self.source = source
        self.note = note
        self.syncStatus = syncStatus
    }

    private enum CodingKeys: String, CodingKey {
        case id
        case capturedAt
        case localFileName
        case source
        case note
        case syncStatus
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        capturedAt = try container.decode(Date.self, forKey: .capturedAt)
        localFileName = try container.decode(String.self, forKey: .localFileName)
        source = try container.decode(String.self, forKey: .source)
        note = try container.decodeIfPresent(String.self, forKey: .note) ?? ""
        syncStatus = try container.decodeIfPresent(PhotoSyncStatus.self, forKey: .syncStatus) ?? .localOnly
    }
}
