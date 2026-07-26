import SwiftUI

/// 全 App 统一的“单个时间”录入：默认刚刚，快捷 chip 一步到位，
/// 精确调整才展开内联滚轮——绝不弹系统日历弹层。
/// 解决“记录时选时间很难选很浪费时间”。
struct QuickTimeField: View {
    @Binding var date: Date
    /// 快捷偏移（分钟，负值表示过去）。
    var offsets: [Int] = [0, -15, -30, -60]
    @State private var isExpanded = false
    /// 只有用户主动点过 chip 才高亮；编辑旧记录时不能一进来就亮着“刚刚”。
    @State private var selectedOffset: Int?

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.small) {
            HStack {
                Image(systemName: "clock")
                    .font(.system(size: 15, weight: .regular))
                    .foregroundStyle(AppColors.inkSoft)
                Text(displayText)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                Spacer(minLength: 0)
                Button(isExpanded ? "收起" : "精确调整") {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        isExpanded.toggle()
                    }
                }
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.blueInk)
            }

            HStack(spacing: AppSpacing.small) {
                ForEach(offsets, id: \.self) { offset in
                    chip(
                        title: chipTitle(for: offset),
                        isSelected: selectedOffset == offset && !isExpanded
                    ) {
                        selectedOffset = offset
                        isExpanded = false
                        date = Date().addingTimeInterval(TimeInterval(offset * 60))
                    }
                }
            }

            if isExpanded {
                DatePicker(
                    "时间",
                    selection: Binding(
                        get: { date },
                        set: { newValue in
                            date = newValue
                            selectedOffset = nil
                        }
                    ),
                    in: ...Date(),
                    displayedComponents: [.date, .hourAndMinute]
                )
                .datePickerStyle(.wheel)
                .labelsHidden()
                .frame(maxHeight: 170)
                .frame(maxWidth: .infinity)
            }
        }
    }

    private var displayText: String {
        if Calendar.current.isDateInToday(date), abs(date.timeIntervalSinceNow) < 90 {
            return "刚刚 · \(BabyRecordStore.timeString(from: date))"
        }
        return BabyRecordStore.reminderDateTimeString(from: date)
    }

    private func chipTitle(for offset: Int) -> String {
        switch offset {
        case 0: "刚刚"
        case let minutes where minutes > -60: "\(minutes)分钟"
        default: "\(offset / 60)小时"
        }
    }

    private func chip(title: String, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(title, action: action)
            .font(AppTypography.caption)
            .foregroundStyle(isSelected ? AppColors.milk : AppColors.blueInk)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(isSelected ? AppColors.blueInk : AppColors.cream, in: Capsule())
            .buttonStyle(.plain)
    }
}

/// 睡眠补录专用：结束时间 + 睡了多久，两步选完一段睡眠。
/// 替代原先“开始/结束各弹两个系统弹层”的四步操作。
struct SleepSpanField: View {
    @Binding var startAt: Date
    @Binding var endAt: Date
    @State private var isExpanded = false
    @State private var selectedDurationMinutes: Int? = 60
    @State private var selectedEndOffset: Int? = 0

    private let endOffsets: [Int] = [0, -15, -30]
    private let durationOptions: [Int] = [30, 60, 90, 120, 180]

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Text("什么时候醒的？")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                HStack(spacing: AppSpacing.small) {
                    ForEach(endOffsets, id: \.self) { offset in
                        chip(
                            title: offset == 0 ? "刚刚" : "\(offset)分钟",
                            isSelected: selectedEndOffset == offset && !isExpanded
                        ) {
                            selectedEndOffset = offset
                            isExpanded = false
                            setEnd(Date().addingTimeInterval(TimeInterval(offset * 60)))
                        }
                    }
                    Spacer(minLength: 0)
                    Text(BabyRecordStore.timeString(from: endAt))
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkGreen)
                }
            }

            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Text("睡了多久？")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                HStack(spacing: AppSpacing.small) {
                    ForEach(durationOptions, id: \.self) { minutes in
                        chip(
                            title: durationTitle(minutes),
                            isSelected: selectedDurationMinutes == minutes && !isExpanded
                        ) {
                            selectedDurationMinutes = minutes
                            isExpanded = false
                            startAt = endAt.addingTimeInterval(TimeInterval(-minutes * 60))
                        }
                    }
                }
            }

            HStack {
                Text(summaryText)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                Spacer(minLength: 0)
                Button(isExpanded ? "收起" : "精确调整") {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        isExpanded.toggle()
                    }
                }
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.blueInk)
            }

            if isExpanded {
                VStack(alignment: .leading, spacing: AppSpacing.small) {
                    DatePicker("开始", selection: Binding(
                        get: { startAt },
                        set: { newValue in
                            startAt = newValue
                            selectedDurationMinutes = nil
                            selectedEndOffset = nil
                        }
                    ), in: ...Date(), displayedComponents: [.date, .hourAndMinute])
                        .font(AppTypography.readableBody)
                        .tint(AppColors.blueInk)
                    DatePicker("结束", selection: Binding(
                        get: { endAt },
                        set: { newValue in
                            setEnd(newValue)
                            selectedDurationMinutes = nil
                            selectedEndOffset = nil
                        }
                    ), in: ...Date(), displayedComponents: [.date, .hourAndMinute])
                        .font(AppTypography.readableBody)
                        .tint(AppColors.blueInk)
                }
            }
        }
        .onAppear {
            // 默认：刚醒，睡了 1 小时。
            if abs(endAt.timeIntervalSince(startAt)) < 60 {
                endAt = Date()
                startAt = endAt.addingTimeInterval(-3600)
            }
        }
    }

    /// 结束时间变化时保持时长不变（有选中时长时）。
    private func setEnd(_ newEnd: Date) {
        let duration = selectedDurationMinutes.map { TimeInterval($0 * 60) }
            ?? endAt.timeIntervalSince(startAt)
        endAt = newEnd
        if duration > 0 {
            startAt = newEnd.addingTimeInterval(-duration)
        }
    }

    private func durationTitle(_ minutes: Int) -> String {
        if minutes < 60 {
            return "\(minutes)分"
        }
        if minutes % 60 == 0 {
            return "\(minutes / 60)小时"
        }
        return String(format: "%.1f小时", Double(minutes) / 60)
    }

    private var summaryText: String {
        let minutes = max(0, Int(endAt.timeIntervalSince(startAt) / 60))
        let sameDayPrefix = Calendar.current.isDate(startAt, inSameDayAs: endAt) ? "" : "昨天"
        return "\(sameDayPrefix)\(BabyRecordStore.timeString(from: startAt)) → \(BabyRecordStore.timeString(from: endAt)) · \(BabyRecordStore.durationText(from: minutes))"
    }

    private func chip(title: String, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(title, action: action)
            .font(AppTypography.caption)
            .foregroundStyle(isSelected ? AppColors.milk : AppColors.blueInk)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(isSelected ? AppColors.blueInk : AppColors.cream, in: Capsule())
            .buttonStyle(.plain)
    }
}
