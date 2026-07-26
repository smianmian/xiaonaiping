import SwiftUI

/// 高频记录页共用的日期切换条：左右切天 + 点中间日历任选日期。
/// 让父母能回看/补录任意一天，而不是只有“今天”。
struct DaySwitcherBar: View {
    @Binding var selectedDay: Date

    private var isToday: Bool {
        Calendar.current.isDateInToday(selectedDay)
    }

    var body: some View {
        HStack(spacing: AppSpacing.small) {
            Button {
                shift(by: -1)
            } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(AppColors.inkGreen)
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("前一天")

            Spacer(minLength: 0)

            HStack(spacing: AppSpacing.tiny) {
                Image(systemName: "calendar")
                    .font(.system(size: 14, weight: .regular))
                    .foregroundStyle(AppColors.inkSoft)
                Text(displayTitle)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.inkGreen)
            }
            .overlay {
                // 透明的原生 DatePicker 盖在标题上：外观自定义，点击弹系统日历。
                DatePicker(
                    "选择日期",
                    selection: $selectedDay,
                    in: ...Date(),
                    displayedComponents: .date
                )
                .labelsHidden()
                .datePickerStyle(.compact)
                .colorMultiply(.clear)
            }

            Spacer(minLength: 0)

            Button {
                shift(by: 1)
            } label: {
                Image(systemName: "chevron.right")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(isToday ? AppColors.inkSoft.opacity(0.4) : AppColors.inkGreen)
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.plain)
            .disabled(isToday)
            .accessibilityLabel("后一天")

            if !isToday {
                Button("回今天") {
                    selectedDay = Date()
                }
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.coral)
                .padding(.horizontal, 10)
                .padding(.vertical, 7)
                .background(AppColors.cream, in: Capsule())
            }
        }
        .padding(.horizontal, AppSpacing.small)
        .frame(maxWidth: .infinity)
        .background { CardBackground(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius) }
    }

    private var displayTitle: String {
        if isToday {
            return "今天"
        }
        if Calendar.current.isDateInYesterday(selectedDay) {
            return "昨天"
        }
        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = Calendar.current.isDate(selectedDay, equalTo: Date(), toGranularity: .year)
            ? "M月d日"
            : "yyyy年M月d日"
        return formatter.string(from: selectedDay)
    }

    private func shift(by days: Int) {
        guard let newDay = Calendar.current.date(byAdding: .day, value: days, to: selectedDay) else { return }
        guard newDay <= Date() || Calendar.current.isDateInToday(newDay) else { return }
        selectedDay = newDay
    }
}
