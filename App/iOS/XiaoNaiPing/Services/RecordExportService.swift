import Foundation

/// 把账号内全部记录导出为一份 CSV 文本：
/// 既是给儿保医生看的问诊材料，也是用户唯一的自助数据备份通道（可携带权）。
@MainActor
enum RecordExportService {
    enum ExportError: LocalizedError {
        case writeFailed

        var errorDescription: String? {
            "导出文件写入失败，请检查设备存储空间。"
        }
    }

    /// 生成 CSV 文件并返回临时 URL，调用方负责弹分享面板。
    static func exportCSV(store: BabyRecordStore) throws -> URL {
        var sections: [String] = []

        sections.append(csvSection(
            title: "宝宝档案",
            header: ["昵称", "出生日期", "性别"],
            rows: [[
                store.baby.name,
                BabyRecordStore.dateString(from: store.baby.birthDate),
                store.baby.sex
            ]]
        ))

        sections.append(csvSection(
            title: "喂养记录",
            header: ["日期", "时间", "类型", "奶量ml", "时长分钟", "哺乳侧", "备注"],
            rows: store.feedingRecords
                .sorted { $0.occurredAt < $1.occurredAt }
                .map { record in
                    [
                        BabyRecordStore.dateString(from: record.occurredAt),
                        BabyRecordStore.timeString(from: record.occurredAt),
                        record.type,
                        record.amountML.map(String.init) ?? "",
                        record.durationMinutes.map(String.init) ?? "",
                        record.breastSide ?? "",
                        record.note ?? ""
                    ]
                }
        ))

        sections.append(csvSection(
            title: "睡眠记录",
            header: ["开始日期", "开始时间", "结束时间", "类型", "时长分钟", "备注"],
            rows: store.sleepRecords
                .sorted { $0.startAt < $1.startAt }
                .map { record in
                    [
                        BabyRecordStore.dateString(from: record.startAt),
                        BabyRecordStore.timeString(from: record.startAt),
                        record.endAt.map(BabyRecordStore.timeString(from:)) ?? "进行中",
                        record.type,
                        record.durationMinutes.map(String.init) ?? "",
                        record.note ?? ""
                    ]
                }
        ))

        sections.append(csvSection(
            title: "排便记录",
            header: ["日期", "时间", "种类", "颜色", "性状", "备注"],
            rows: store.diaperRecords
                .sorted { $0.occurredAt < $1.occurredAt }
                .map { record in
                    [
                        BabyRecordStore.dateString(from: record.occurredAt),
                        BabyRecordStore.timeString(from: record.occurredAt),
                        record.kind,
                        record.color ?? "",
                        record.texture ?? "",
                        record.note ?? ""
                    ]
                }
        ))

        sections.append(csvSection(
            title: "喝水记录",
            header: ["日期", "时间", "水量ml", "备注"],
            rows: store.waterRecords
                .sorted { $0.occurredAt < $1.occurredAt }
                .map { record in
                    [
                        BabyRecordStore.dateString(from: record.occurredAt),
                        BabyRecordStore.timeString(from: record.occurredAt),
                        String(record.amountML),
                        record.note ?? ""
                    ]
                }
        ))

        sections.append(csvSection(
            title: "成长记录",
            header: ["测量日期", "体重kg", "身高cm", "头围cm", "备注"],
            rows: store.growthRecords
                .sorted { $0.measuredAt < $1.measuredAt }
                .map { record in
                    [
                        record.measuredAt,
                        record.weight > 0 ? String(format: "%.1f", record.weight) : "",
                        record.height > 0 ? String(format: "%.1f", record.height) : "",
                        record.head > 0 ? String(format: "%.1f", record.head) : "",
                        record.note ?? ""
                    ]
                }
        ))

        sections.append(csvSection(
            title: "疫苗记录",
            header: ["名称", "状态", "计划日期", "实际接种日期", "地区", "备注"],
            rows: store.vaccineRecords.map { record in
                [
                    record.title,
                    record.displayStatus,
                    record.dueText,
                    record.administeredAt.map(BabyRecordStore.dateString(from:)) ?? "",
                    record.region ?? "",
                    record.note ?? ""
                ]
            }
        ))

        sections.append(csvSection(
            title: "健康观察",
            header: ["日期", "时间", "类型", "数值", "部位", "药品", "剂量", "备注"],
            rows: store.healthObservations
                .sorted { $0.occurredAt < $1.occurredAt }
                .map { record in
                    [
                        BabyRecordStore.dateString(from: record.occurredAt),
                        BabyRecordStore.timeString(from: record.occurredAt),
                        record.kind,
                        record.value.map { String(format: "%.1f", $0) } ?? "",
                        record.zone ?? "",
                        record.medicationName ?? "",
                        record.dose ?? "",
                        record.note ?? ""
                    ]
                }
        ))

        sections.append(csvSection(
            title: "纪念日",
            header: ["名称", "日期", "备注"],
            rows: store.milestones.map { milestone in
                [
                    milestone.title,
                    BabyRecordStore.milestoneDate(milestone).map(BabyRecordStore.dateString(from:)) ?? milestone.date,
                    milestone.note ?? ""
                ]
            }
        ))

        // BOM 让 Excel/Numbers 正确识别 UTF-8 中文。
        let content = "\u{FEFF}" + sections.joined(separator: "\n\n")

        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyyMMdd-HHmm"
        let fileName = "小奶瓶记录导出-\(formatter.string(from: Date())).csv"
        let url = FileManager.default.temporaryDirectory.appendingPathComponent(fileName)

        do {
            try content.write(to: url, atomically: true, encoding: .utf8)
        } catch {
            throw ExportError.writeFailed
        }
        return url
    }

    private static func csvSection(title: String, header: [String], rows: [[String]]) -> String {
        var lines = ["# \(title)"]
        lines.append(header.map(escaped).joined(separator: ","))
        if rows.isEmpty {
            lines.append("（暂无记录）")
        } else {
            lines.append(contentsOf: rows.map { row in
                row.map(escaped).joined(separator: ",")
            })
        }
        return lines.joined(separator: "\n")
    }

    private static func escaped(_ field: String) -> String {
        guard field.contains(",") || field.contains("\"") || field.contains("\n") else {
            return field
        }
        return "\"\(field.replacingOccurrences(of: "\"", with: "\"\""))\""
    }
}
