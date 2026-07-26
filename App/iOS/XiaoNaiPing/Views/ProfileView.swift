import PhotosUI
import SwiftUI
import UIKit
import UserNotifications

struct ProfileView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @EnvironmentObject private var cloudSync: CloudSyncController
    @State private var isAccountStatusPresented = false
    @State private var isPrivacyStatusPresented = false
    @State private var isBabyEditorPresented = false
    @State private var isProfileDeletePresented = false
    @State private var selectedAvatarItem: PhotosPickerItem?
    @State private var pendingAvatarImage: UIImage?
    @State private var avatarErrorMessage: String?
    @State private var liveActivityMessage: String?
    @State private var isFeedingLiveActivityUpdating = false
    @AppStorage("xnpNightModeEnabled") private var nightModeEnabled = false
    @AppStorage("xnpFeedbackSoundEnabled") private var feedbackSoundEnabled = true

    init() {
        #if DEBUG
        _isAccountStatusPresented = State(initialValue: ProcessInfo.processInfo.arguments.contains("-XNPScreenshotAccountSheet"))
        #endif
    }

    var body: some View {
        ScreenScaffold {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    Text("设置")
                        .font(AppTypography.heroTitle)
                        .foregroundStyle(AppColors.inkGreen)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    profileHeader
                    primarySettingsCard
                    globalSettingsCard
                    dangerSettingsCard
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.medium)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isAccountStatusPresented) {
            DataStatusSheet(kind: .account, cloudSync: cloudSync)
                .presentationDetents(accountPresentationDetents)
        }
        .sheet(isPresented: $isPrivacyStatusPresented) {
            DataStatusSheet(kind: .privacy, cloudSync: cloudSync)
                .presentationDetents([.medium, .large])
        }
        .alert("删除宝宝档案？", isPresented: $isProfileDeletePresented) {
            Button("删除", role: .destructive) {
                store.deleteBabyProfileAndLocalRecords()
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text("会清空当前宝宝档案、记录和照片。")
        }
        .sheet(isPresented: $isBabyEditorPresented) {
            BabyProfileEditorSheet(baby: store.baby) { name, birthDate, sex in
                store.updateBaby(name: name, birthDate: birthDate, sex: sex)
            }
            .presentationDetents([.medium])
        }
        .sheet(isPresented: avatarEditorBinding) {
            if let pendingAvatarImage {
                AvatarEditorSheet(image: pendingAvatarImage) { data in
                    saveEditedAvatar(data: data)
                }
                .presentationDetents([.large])
            }
        }
        .onChange(of: selectedAvatarItem) { _, newItem in
            updateAvatar(from: newItem)
        }
        .alert("头像保存失败", isPresented: avatarErrorBinding) {
            Button("知道了", role: .cancel) {
                avatarErrorMessage = nil
            }
        } message: {
            Text(avatarErrorMessage ?? "请稍后再试。")
        }
        .alert("灵动岛提醒", isPresented: liveActivityMessageBinding) {
            Button("知道了", role: .cancel) {
                liveActivityMessage = nil
            }
        } message: {
            Text(liveActivityMessage ?? "")
        }
    }

    private var profileHeader: some View {
        Button {
            isBabyEditorPresented = true
        } label: {
        HStack(spacing: AppSpacing.large) {
            PhotosPicker(selection: $selectedAvatarItem, matching: .images) {
                ZStack(alignment: .bottomTrailing) {
                    BabyAvatarView(
                        imageData: store.baby.avatarImageData,
                        fallbackAssetName: "approvedBabyAvatar",
                        size: 86
                    )

                    Image(systemName: "camera.fill")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.white)
                        .frame(width: 28, height: 28)
                        .background {
                            Circle()
                                .fill(AppColors.coral)
                                .shadow(color: AppColors.coral.opacity(0.20), radius: 8, y: 4)
                        }
                        .overlay {
                            Circle()
                                .stroke(AppColors.paper, lineWidth: 2)
                        }
                }
            }
            .buttonStyle(.plain)
            .accessibilityLabel("更换宝宝头像")

            VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                Text(store.baby.name)
                    .font(AppTypography.title)
                    .foregroundStyle(AppColors.inkGreen)
            }

            Spacer()
            Text("编辑资料")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.inkGreen)
            Image(systemName: "chevron.right")
                .foregroundStyle(AppColors.inkSoft)
        }
        .padding(AppSpacing.roomy)
        .background { CardBackground(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) }
        }
        .buttonStyle(.plain)
    }

    private var primarySettingsCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius, padding: 0) {
            VStack(spacing: 0) {
                Button { isBabyEditorPresented = true } label: {
                    ProfileMenuRow(icon: "face.smiling", title: "宝宝信息")
                }
                .buttonStyle(.plain)
                Button { isAccountStatusPresented = true } label: {
                    ProfileMenuRow(icon: "person.crop.circle", title: "账号管理")
                }
                .buttonStyle(.plain)
                Button { isPrivacyStatusPresented = true } label: {
                    ProfileMenuRow(icon: "lock.shield", title: "数据与隐私")
                }
                .buttonStyle(.plain)
            }
        }
    }

    private var globalSettingsCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius, padding: 0) {
            VStack(spacing: 0) {
                Toggle(isOn: $feedbackSoundEnabled) {
                    settingToggleLabel(icon: "speaker.wave.2", title: "操作提示音", detail: "记录成功时播放轻提示音", color: AppColors.inkGreen)
                }
                .toggleStyle(.switch)
                .tint(AppColors.sage)
                .padding(.horizontal, AppSpacing.roomy)
                .padding(.vertical, AppSpacing.regular)

                Divider().padding(.leading, 72).padding(.trailing, AppSpacing.roomy)

                Toggle(isOn: $nightModeEnabled) {
                    settingToggleLabel(icon: "moon.stars", title: "夜间外观", detail: "夜里记录时切换为柔和深色界面", color: AppColors.blueInk)
                }
                .toggleStyle(.switch)
                .tint(AppColors.blueInk)
                .padding(.horizontal, AppSpacing.roomy)
                .padding(.vertical, AppSpacing.regular)

                Divider().padding(.leading, 72).padding(.trailing, AppSpacing.roomy)

                Button { openNotificationSettings() } label: {
                    settingToggleLabel(icon: "bell", title: "通知权限", detail: "管理系统通知与提醒权限", color: AppColors.peach)
                        .overlay(alignment: .trailing) {
                            Image(systemName: "chevron.right")
                                .foregroundStyle(AppColors.inkSoft)
                                .padding(.trailing, 3)
                        }
                }
                .buttonStyle(.plain)
                .padding(.horizontal, AppSpacing.roomy)
                .padding(.vertical, AppSpacing.regular)

                Divider().padding(.leading, 72).padding(.trailing, AppSpacing.roomy)

                feedingLiveActivityRow
            }
        }
    }

    private var dangerSettingsCard: some View {
        Button { isProfileDeletePresented = true } label: {
            HStack(spacing: AppSpacing.medium) {
                Image(systemName: "trash")
                    .font(.system(size: 21, weight: .semibold))
                    .foregroundStyle(AppColors.coral)
                    .frame(width: 38, height: 38)
                Text("删除宝宝档案")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.coral)
                Spacer()
                Image(systemName: "chevron.right")
                    .foregroundStyle(AppColors.inkSoft)
            }
            .padding(AppSpacing.roomy)
            .background { CardBackground(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) }
        }
        .buttonStyle(.plain)
    }

    private func settingToggleLabel(icon: String, title: String, detail: String, color: Color) -> some View {
        HStack(spacing: AppSpacing.medium) {
            Image(systemName: icon)
                .font(.system(size: 22, weight: .regular))
                .foregroundStyle(color)
                .frame(width: 38, height: 38)
            VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                Text(title).font(AppTypography.bodyLarge).foregroundStyle(AppColors.inkGreen)
                Text(detail).font(AppTypography.caption).foregroundStyle(AppColors.inkSoft)
            }
            Spacer()
        }
    }

    private func openNotificationSettings() {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        UIApplication.shared.open(url)
    }

    private var quietCareModeRow: some View {
        Toggle(isOn: Binding(
            get: { store.quietCareModeEnabled },
            set: { store.setQuietCareModeEnabled($0) }
        )) {
            HStack(spacing: AppSpacing.regular) {
                Image(systemName: "speaker.slash")
                    .font(.system(size: 19, weight: .regular))
                    .foregroundStyle(AppColors.sage)
                    .frame(width: 30)
                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                    Text("安静育儿模式")
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkGreen)
                    Text("默认开启，半夜记录时不播放 App 内声音。")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                }
            }
        }
        .toggleStyle(.switch)
        .tint(AppColors.coral)
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, AppSpacing.small)
    }

    private var nightModeRow: some View {
        Toggle(isOn: $nightModeEnabled) {
            HStack(spacing: AppSpacing.regular) {
                Image(systemName: "moon.stars")
                    .font(.system(size: 19, weight: .regular))
                    .foregroundStyle(AppColors.blueInk)
                    .frame(width: 30)
                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                    Text("夜间模式")
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkGreen)
                    Text("夜里记录时切换为柔和深色界面。")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                }
            }
        }
        .toggleStyle(.switch)
        .tint(AppColors.blueInk)
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, AppSpacing.small)
    }

    private var feedingLiveActivityRow: some View {
        VStack(spacing: 0) {
            Toggle(isOn: Binding(
                get: { store.feedingLiveActivityEnabled },
                set: { setFeedingLiveActivityEnabled($0) }
            )) {
                HStack(spacing: AppSpacing.regular) {
                    Image(systemName: "sparkles")
                        .font(.system(size: 19, weight: .semibold))
                        .foregroundStyle(AppColors.coral)
                        .frame(width: 30)
                    VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                        Text("灵动岛喝奶提醒")
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                        Text("开启后，保存喝奶闹钟时会在灵动岛和锁屏上轻轻待着。")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                    }
                }
            }
            .toggleStyle(.switch)
            .tint(AppColors.coral)
            .disabled(isFeedingLiveActivityUpdating)
            .padding(.horizontal, AppSpacing.medium)
            .padding(.vertical, AppSpacing.small)
        }
    }

    private func setFeedingLiveActivityEnabled(_ isEnabled: Bool) {
        guard !isFeedingLiveActivityUpdating else { return }
        isFeedingLiveActivityUpdating = true
        store.setFeedingLiveActivityEnabled(isEnabled)
        #if canImport(ActivityKit)
        if #available(iOS 16.2, *) {
            if isEnabled {
                FeedingReminderLiveActivityController.sync(
                    reminder: store.nextFeedingReminder,
                    repeatIntervalMinutes: store.nextFeedingReminder?.origin == .automatic
                        ? store.feedingReminderPreference.intervalMinutes
                        : nil,
                    babyName: store.baby.name,
                    babyAvatarData: store.baby.avatarImageData
                ) { result in
                    handleFeedingLiveActivityResult(result)
                }
            } else {
                FeedingReminderLiveActivityController.endAll { result in
                    handleFeedingLiveActivityResult(result)
                }
            }
        } else {
            isFeedingLiveActivityUpdating = false
            store.setFeedingLiveActivityEnabled(false)
            liveActivityMessage = "当前系统版本不支持灵动岛实时活动。"
        }
        #else
        isFeedingLiveActivityUpdating = false
        store.setFeedingLiveActivityEnabled(false)
        liveActivityMessage = "当前系统版本不支持灵动岛实时活动。"
        #endif
    }

    @available(iOS 16.2, *)
    private func handleFeedingLiveActivityResult(_ result: FeedingReminderLiveActivityResult) {
        isFeedingLiveActivityUpdating = false
        switch result {
        case .startedOrUpdated:
            liveActivityMessage = "灵动岛喝奶提醒已开启。"
        case .ended:
            liveActivityMessage = "灵动岛喝奶提醒已关闭。"
        case .noReminder:
            liveActivityMessage = "已开启。先保存一个喝奶闹钟，灵动岛和锁屏提醒就会出现。"
        case .activitiesDisabled:
            store.setFeedingLiveActivityEnabled(false)
            liveActivityMessage = "系统没有允许实时活动。请到 iPhone 设置里允许小奶瓶实时活动。"
        case .failed(let message):
            liveActivityMessage = "灵动岛开关已打开。".localizedText + message.localizedText
        }
    }

    private var avatarErrorBinding: Binding<Bool> {
        Binding {
            avatarErrorMessage != nil
        } set: { isPresented in
            if !isPresented {
                avatarErrorMessage = nil
            }
        }
    }

    private var avatarEditorBinding: Binding<Bool> {
        Binding {
            pendingAvatarImage != nil
        } set: { isPresented in
            if !isPresented {
                pendingAvatarImage = nil
            }
        }
    }

    private var liveActivityMessageBinding: Binding<Bool> {
        Binding {
            liveActivityMessage != nil
        } set: { isPresented in
            if !isPresented {
                liveActivityMessage = nil
            }
        }
    }

    private func updateAvatar(from item: PhotosPickerItem?) {
        guard let item else { return }

        Task {
            do {
                guard let data = try await item.loadTransferable(type: Data.self) else {
                    await MainActor.run {
                        avatarErrorMessage = "没有读取到这张照片，请换一张再试。"
                        selectedAvatarItem = nil
                    }
                    return
                }

                await MainActor.run {
                    guard let image = UIImage(data: data), image.size.width > 0, image.size.height > 0 else {
                        avatarErrorMessage = "没有读取到这张照片，请换一张再试。"
                        selectedAvatarItem = nil
                        return
                    }
                    pendingAvatarImage = image
                    selectedAvatarItem = nil
                }
            } catch {
                await MainActor.run {
                    avatarErrorMessage = "没有读取到这张照片，请换一张再试。"
                    selectedAvatarItem = nil
                }
            }
        }
    }

    private func saveEditedAvatar(data: Data) -> String? {
        guard store.updateBabyAvatar(data: data) else {
            return store.saveErrorMessage ?? "头像保存失败，请换一张照片再试。"
        }

        pendingAvatarImage = nil
        refreshFeedingLiveActivityAvatar()
        return nil
    }

    private func refreshFeedingLiveActivityAvatar() {
        QuickLogService.syncLiveActivity(store: store)
    }

    private var accountPresentationDetents: Set<PresentationDetent> {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("-XNPScreenshotAccountSheet") {
            return [.large]
        }
        #endif
        return [.medium, .large]
    }
}

private struct AvatarEditorSheet: View {
    let image: UIImage
    let onSave: (Data) -> String?

    @Environment(\.dismiss) private var dismiss
    @State private var scale = 1.0
    @State private var rotationDegrees = 0.0
    @State private var offset = CGSize.zero
    @State private var dragStartOffset = CGSize.zero
    @State private var errorMessage: String?

    private let previewSize: CGFloat = 258
    private let outputSide: CGFloat = 512

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    VStack(spacing: AppSpacing.small) {
                        avatarPreview
                        Text("拖动圆里的照片，下面可以调大小和角度。".localizedText)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                    }

                    VStack(spacing: AppSpacing.medium) {
                        editorSlider(
                            title: "大小",
                            value: $scale,
                            range: 0.80...3.00,
                            valueText: "\(Int(scale * 100))%"
                        )
                        editorSlider(
                            title: "角度",
                            value: $rotationDegrees,
                            range: -180.00...180.00,
                            valueText: "\(Int(rotationDegrees))°"
                        )
                    }
                    .padding(AppSpacing.roomy)
                    .background {
                        RoundedRectangle(cornerRadius: AppShapes.largeCardRadius, style: .continuous)
                            .fill(AppColors.cream.opacity(0.86))
                            .overlay {
                                RoundedRectangle(cornerRadius: AppShapes.largeCardRadius, style: .continuous)
                                    .stroke(AppColors.softStroke.opacity(0.30), lineWidth: 1)
                            }
                    }

                    if let errorMessage {
                        Text(errorMessage.localizedText)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    HStack(spacing: AppSpacing.medium) {
                        Button {
                            reset()
                        } label: {
                            Text("重置".localizedText)
                                .font(AppTypography.bodyLarge)
                                .foregroundStyle(AppColors.blueInk)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 13)
                                .background {
                                    Capsule()
                                        .fill(AppColors.mistBlue.opacity(0.72))
                                        .overlay {
                                            Capsule()
                                                .stroke(AppColors.blueInk.opacity(0.22), lineWidth: 1)
                                        }
                                }
                        }
                        .buttonStyle(.plain)

                        PrimaryWatercolorButton(title: "保存头像") {
                            save()
                        }
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle("头像编辑".localizedText)
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(AppColors.paper, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                    .foregroundStyle(AppColors.coral)
                }
            }
        }
        .preferredColorScheme(.light)
    }

    private var avatarPreview: some View {
        ZStack {
            Circle()
                .fill(AppColors.milk)

            Image(uiImage: image)
                .resizable()
                .scaledToFill()
                .frame(width: previewSize, height: previewSize)
                .scaleEffect(CGFloat(scale))
                .rotationEffect(.degrees(rotationDegrees))
                .offset(offset)

            Circle()
                .stroke(AppColors.paper.opacity(0.95), lineWidth: 7)
            Circle()
                .stroke(AppColors.coral.opacity(0.18), lineWidth: 1)
                .padding(7)
        }
        .frame(width: previewSize, height: previewSize)
        .clipShape(Circle())
        .shadow(color: AppColors.inkGreen.opacity(0.12), radius: 18, y: 9)
        .gesture(
            DragGesture()
                .onChanged { value in
                    offset = clampedOffset(CGSize(
                        width: dragStartOffset.width + value.translation.width,
                        height: dragStartOffset.height + value.translation.height
                    ))
                }
                .onEnded { _ in
                    dragStartOffset = offset
                }
        )
        .accessibilityLabel("头像预览")
    }

    private func editorSlider(
        title: String,
        value: Binding<Double>,
        range: ClosedRange<Double>,
        valueText: String
    ) -> some View {
        VStack(alignment: .leading, spacing: AppSpacing.small) {
            HStack {
                Text(title.localizedText)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                Spacer()
                Text(valueText)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
            }
            Slider(value: value, in: range)
                .tint(AppColors.coral)
        }
    }

    private func reset() {
        scale = 1
        rotationDegrees = 0
        offset = .zero
        dragStartOffset = .zero
        errorMessage = nil
    }

    private func save() {
        guard let data = renderedAvatarData() else {
            errorMessage = "头像保存失败，请换一张照片再试。"
            return
        }

        if let message = onSave(data) {
            errorMessage = message
        } else {
            dismiss()
        }
    }

    private func renderedAvatarData() -> Data? {
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        format.opaque = true
        let size = CGSize(width: outputSide, height: outputSide)
        let renderer = UIGraphicsImageRenderer(size: size, format: format)
        let rendered = renderer.image { context in
            UIColor(red: 1.000, green: 0.988, blue: 0.960, alpha: 1).setFill()
            UIBezierPath(rect: CGRect(origin: .zero, size: size)).fill()

            let outputOffset = CGSize(
                width: offset.width / previewSize * outputSide,
                height: offset.height / previewSize * outputSide
            )
            let imageSize = image.size
            let baseScale = max(outputSide / imageSize.width, outputSide / imageSize.height)
            let finalScale = baseScale * CGFloat(scale)
            let drawSize = CGSize(width: imageSize.width * finalScale, height: imageSize.height * finalScale)
            let drawRect = CGRect(
                x: -drawSize.width / 2,
                y: -drawSize.height / 2,
                width: drawSize.width,
                height: drawSize.height
            )

            let cgContext = context.cgContext
            cgContext.saveGState()
            cgContext.translateBy(x: outputSide / 2 + outputOffset.width, y: outputSide / 2 + outputOffset.height)
            cgContext.rotate(by: CGFloat(rotationDegrees * .pi / 180))
            image.draw(in: drawRect)
            cgContext.restoreGState()
        }
        return rendered.jpegData(compressionQuality: 0.86)
    }

    private func clampedOffset(_ value: CGSize) -> CGSize {
        let maxOffset = previewSize * 0.44
        return CGSize(
            width: min(max(value.width, -maxOffset), maxOffset),
            height: min(max(value.height, -maxOffset), maxOffset)
        )
    }
}

struct BabyAvatarView: View {
    let imageData: Data?
    let fallbackAssetName: String
    let size: CGFloat

    var body: some View {
        ZStack {
            if let imageData, let image = UIImage(data: imageData) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
            } else {
                Image(fallbackAssetName)
                    .renderingMode(.original)
                    .resizable()
                    .scaledToFit()
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
        .overlay {
            Circle()
                .stroke(AppColors.paper.opacity(0.92), lineWidth: max(2, size * 0.035))
        }
        .shadow(color: AppColors.inkGreen.opacity(0.10), radius: 10, y: 5)
    }
}

private struct ExportFileItem: Identifiable {
    let url: URL
    var id: String { url.absoluteString }
}

private struct ShareSheet: UIViewControllerRepresentable {
    let activityItems: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: activityItems, applicationActivities: nil)
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

private enum DataStatusKind {
    case account
    case privacy

    var title: String {
        switch self {
        case .account:
            "账号管理"
        case .privacy:
            "数据与隐私"
        }
    }
}

private struct DataStatusSheet: View {
    private enum PhoneLoginField {
        case phoneNumber
        case verificationCode
    }

    let kind: DataStatusKind
    @ObservedObject var cloudSync: CloudSyncController
    @EnvironmentObject private var store: BabyRecordStore
    @Environment(\.dismiss) private var dismiss
    @State private var isCloudDeletePresented = false
    @State private var isSignOutPresented = false
    @State private var isRestorePresented = false
    @State private var phoneNumber = "+86"
    @State private var phoneCode = ""
    @State private var isPhoneCodeRequested = false
    @State private var exportFileURL: ExportFileItem?
    @State private var exportErrorMessage: String?
    @FocusState private var focusedPhoneLoginField: PhoneLoginField?

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    headerCard
                    if kind == .account {
                        if cloudSync.isServiceConfigured {
                            accountContent
                        } else {
                            serviceUnavailableCard
                        }
                    } else {
                        privacyContent
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .navigationTitle(kind.title.localizedText)
            .navigationBarTitleDisplayMode(.inline)
            .alert("删除云端账号？", isPresented: $isCloudDeletePresented) {
                Button("删除", role: .destructive) {
                    Task {
                        await cloudSync.deleteCloudAccount(store: store)
                    }
                }
                Button("取消", role: .cancel) {}
            } message: {
                Text("会删除账号、云端记录和照片原图。")
            }
            .alert("退出当前账号？", isPresented: $isSignOutPresented) {
                Button("退出", role: .destructive) {
                    cloudSync.signOut()
                }
                Button("取消", role: .cancel) {}
            } message: {
                Text("只会移除此设备上的登录会话，不会删除账号中的记录。")
            }
            .alert("从云端恢复？", isPresented: $isRestorePresented) {
                Button("恢复", role: .destructive) {
                    Task {
                        await cloudSync.restoreFromCloud(store: store)
                    }
                }
                Button("取消", role: .cancel) {}
            } message: {
                Text("会用云端备份覆盖本机当前的记录和照片。恢复前会自动保留一份本机快照。")
            }
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("关闭") {
                        dismiss()
                    }
                    .foregroundStyle(AppColors.coral)
                }
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("完成") {
                        focusedPhoneLoginField = nil
                    }
                }
            }
        }
    }

    private var headerCard: some View {
        WatercolorCard(tint: kind == .account ? AppColors.mistBlue : AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Label((kind == .account ? "账号管理" : "数据与隐私").localizedText, systemImage: kind == .account ? "person.crop.circle" : "shield")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text(kind == .account ? "使用手机号或微信登录，并在这里管理账号。" : "宝宝昵称、生日、记录、照片和疫苗提醒都属于高敏感家庭数据，可在这里查看保存范围和管理删除。")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.ink)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var accountContent: some View {
        VStack(spacing: AppSpacing.regular) {
            statusRow(icon: "person.crop.circle", title: "账号", value: cloudSync.accountSummary, detail: "使用手机号或微信登录；云端只保存必要账号标识。")
            if !cloudSync.hasSession {
                phoneLoginSection
                if cloudSync.isWeChatLoginConfigured {
                    weChatLoginSection
                }
            }
            statusRow(icon: "arrow.clockwise", title: "换机恢复", value: "同一账号", detail: "在新手机用同一个手机号或微信登录后，可恢复服务器中的资料。")
            statusRow(icon: "trash", title: "删除账号", value: "App 内可用", detail: "删除账号会删除云端记录、照片和账号信息。")
            actionButtons
        }
    }

    private var phoneLoginSection: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Label("手机号登录", systemImage: "iphone")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                Text("使用 E.164 格式，例如 +8613800138000 或 +85251234567。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .fixedSize(horizontal: false, vertical: true)
                TextField("手机号", text: $phoneNumber)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.phonePad)
                    .textFieldStyle(.roundedBorder)
                    .focused($focusedPhoneLoginField, equals: .phoneNumber)
                    .onChange(of: phoneNumber) { _, _ in
                        guard isPhoneCodeRequested else { return }
                        isPhoneCodeRequested = false
                        phoneCode = ""
                    }
                if let phoneValidationMessage {
                    Text(phoneValidationMessage)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.coral)
                }
                Button("获取验证码") {
                    focusedPhoneLoginField = nil
                    isPhoneCodeRequested = true
                    Task {
                        await cloudSync.requestPhoneCode(phoneNumber: normalizedPhoneNumber)
                    }
                }
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.coral)
                .frame(maxWidth: .infinity)
                .frame(minHeight: 44)
                .overlay {
                    Capsule()
                        .stroke(AppColors.coral.opacity(0.35), lineWidth: 1)
                }
                .buttonStyle(.plain)
                .disabled(cloudSync.isWorking || !canRequestPhoneCode)

                if isPhoneCodeRequested {
                    TextField("6 位验证码", text: $phoneCode)
                        .keyboardType(.numberPad)
                        .textFieldStyle(.roundedBorder)
                        .focused($focusedPhoneLoginField, equals: .verificationCode)
                        .onChange(of: phoneCode) { _, code in
                            if CloudSyncController.validateSmsCode(code) {
                                focusedPhoneLoginField = nil
                            }
                        }

                    if let codeValidationMessage {
                        Text(codeValidationMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                    }

                    Button("手机号登录") {
                        focusedPhoneLoginField = nil
                        Task {
                            await cloudSync.verifyPhoneCode(phoneNumber: normalizedPhoneNumber, code: normalizedPhoneCode, store: store)
                        }
                    }
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.coral)
                    .disabled(cloudSync.isWorking || !canVerifyPhoneCode)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var normalizedPhoneNumber: String {
        phoneNumber.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var normalizedPhoneCode: String {
        phoneCode.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canRequestPhoneCode: Bool {
        CloudSyncController.validateE164PhoneNumber(normalizedPhoneNumber)
        && !cloudSync.isWorking
    }

    private var canVerifyPhoneCode: Bool {
        CloudSyncController.validateE164PhoneNumber(normalizedPhoneNumber)
        && CloudSyncController.validateSmsCode(normalizedPhoneCode)
        && !cloudSync.isWorking
    }

    private var phoneValidationMessage: String? {
        if normalizedPhoneNumber.isEmpty || normalizedPhoneNumber == "+86" {
            return nil
        }
        return CloudSyncController.validateE164PhoneNumber(normalizedPhoneNumber) ? nil : "手机号格式不正确，需以 + 开头，且为 E.164 数字位数。"
    }

    private var codeValidationMessage: String? {
        if normalizedPhoneCode.isEmpty {
            return nil
        }
        return CloudSyncController.validateSmsCode(normalizedPhoneCode) ? nil : "验证码格式不正确，需 6 位数字。"
    }

    private var weChatLoginSection: some View {
        WatercolorCard(tint: AppColors.grass, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Label("微信登录", systemImage: "message")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                Text(weChatLoginDetail)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .fixedSize(horizontal: false, vertical: true)
                Button("微信登录") {
                    Task {
                        await cloudSync.loginWithWeChat(store: store)
                    }
                }
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.inkGreen)
                .disabled(cloudSync.isWorking || !cloudSync.isWeChatLoginConfigured)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var weChatLoginDetail: String {
        if cloudSync.isNativeWeChatLoginAvailable {
            return "微信开放平台已配置；登录会通过微信授权 code 换取私有账号。".localizedText
        }
        #if DEBUG
        if cloudSync.isDebugWeChatLoginAvailable {
            return "微信开放平台配置完成后，可通过微信授权连接同一个私有账号。".localizedText
        }
        #endif
        return "微信登录未启用：请先完成微信 OpenSDK、AppID、URL Scheme、Universal Link 和服务端凭证配置。".localizedText
    }

    private var serviceUnavailableCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Label("云端服务尚未配置", systemImage: "icloud.slash")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text("账号服务暂不可用，请检查网络后重试。手机号和微信登录会在服务恢复后继续可用。")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.inkSoft)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var actionButtons: some View {
        VStack(spacing: AppSpacing.small) {
            PrimaryWatercolorButton(title: "从云端恢复", tint: AppColors.cream, foreground: AppColors.inkGreen) {
                isRestorePresented = true
            }
            .disabled(cloudSync.isWorking || !cloudSync.hasSession)

            PrimaryWatercolorButton(title: "退出当前账号", tint: AppColors.mistBlue, foreground: AppColors.inkGreen) {
                isSignOutPresented = true
            }
            .disabled(cloudSync.isWorking || !cloudSync.hasSession)

            PrimaryWatercolorButton(title: "删除云端账号", tint: AppColors.cream, foreground: AppColors.coral) {
                isCloudDeletePresented = true
            }
            .disabled(cloudSync.isWorking || !cloudSync.hasSession)
        }
    }

    private var privacyContent: some View {
        VStack(spacing: AppSpacing.regular) {
            statusRow(icon: "lock", title: "数据保存", value: "私有服务", detail: "喂养、喝水、睡眠、排便、成长、照片和疫苗记录保存在小奶瓶私有服务中。")
            statusRow(icon: "photo", title: "照片", value: "私有空间", detail: "从相册选择或拍照后复制到 App 私有目录。")
            statusRow(icon: "bell", title: "通知", value: "系统权限", detail: "疫苗提醒使用 iOS 系统通知；拒绝后需要去系统设置开启。")
            statusRow(icon: "waveform.path.ecg", title: "崩溃日志", value: "Apple 原生", detail: "不得包含宝宝照片、生日、备注、对象 key 或记录明细。")
            statusRow(icon: "xmark.octagon", title: "未接入", value: "无第三方分析", detail: "第一版不接广告、社区或第三方数据分析 SDK。")

            PrimaryWatercolorButton(title: "导出全部记录（CSV）", tint: AppColors.grass, foreground: AppColors.inkGreen) {
                exportRecords()
            }
            Text("导出为表格文件，可以直接发给医生或自己留档。照片请在相册中单独保存。")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
                .frame(maxWidth: .infinity, alignment: .leading)

            if let exportErrorMessage {
                Text(exportErrorMessage)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.coral)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .sheet(item: $exportFileURL) { exportItem in
            ShareSheet(activityItems: [exportItem.url])
        }
    }

    private func exportRecords() {
        exportErrorMessage = nil
        do {
            let url = try RecordExportService.exportCSV(store: store)
            exportFileURL = ExportFileItem(url: url)
        } catch {
            exportErrorMessage = error.localizedDescription
        }
    }

    private func statusRow(icon: String, title: String, value: String, detail: String) -> some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            HStack(alignment: .top, spacing: AppSpacing.medium) {
                Image(systemName: icon)
                    .font(.system(size: 20, weight: .regular))
                    .foregroundStyle(AppColors.sage)
                    .frame(width: 30)
                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(title.localizedText)
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                        Spacer()
                        Text(value.localizedText)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                    }
                    Text(detail.localizedText)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }
}

private struct BabyProfileEditorSheet: View {
    let baby: Baby
    let onSave: (String, Date, String) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var name: String
    @State private var birthDate: Date
    @State private var sex: String
    @State private var errorMessage: String?

    private let sexOptions = ["未设置", "女宝", "男宝"]

    init(baby: Baby, onSave: @escaping (String, Date, String) -> Void) {
        self.baby = baby
        self.onSave = onSave
        _name = State(initialValue: baby.name)
        _birthDate = State(initialValue: baby.birthDate)
        _sex = State(initialValue: baby.sex)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: AppSpacing.large) {
                VStack(alignment: .leading, spacing: AppSpacing.medium) {
                    Text("昵称")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                    TextField("宝宝昵称", text: $name)
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.ink)
                        .textInputAutocapitalization(.never)
                        .padding(.horizontal, AppSpacing.medium)
                        .frame(height: 48)
                        .background {
                            RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                                .fill(AppColors.milk)
                                .overlay {
                                    RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                                        .stroke(AppColors.softStroke.opacity(0.28), lineWidth: 1)
                                }
                        }

                    DatePicker("出生日期", selection: $birthDate, in: ...Date(), displayedComponents: [.date])
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.ink)
                        .tint(AppColors.coral)

                    Picker("性别", selection: $sex) {
                        ForEach(sexOptions, id: \.self) { option in
                            Text(option.localizedText).tag(option)
                        }
                    }
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.ink)
                    .tint(AppColors.coral)
                }
                .padding(AppSpacing.roomy)
                .background {
                    RoundedRectangle(cornerRadius: AppShapes.largeCardRadius, style: .continuous)
                        .fill(AppColors.cream.opacity(0.86))
                        .overlay {
                            RoundedRectangle(cornerRadius: AppShapes.largeCardRadius, style: .continuous)
                                .stroke(AppColors.softStroke.opacity(0.30), lineWidth: 1)
                        }
                }

                if let errorMessage {
                        Text(errorMessage.localizedText)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.coral)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }

                PrimaryWatercolorButton(title: "保存宝宝信息") {
                    save()
                }
                Spacer()
            }
            .padding(AppSpacing.large)
            .background(PaperBackgroundView())
            .navigationTitle("宝宝信息".localizedText)
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(AppColors.paper, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                    .foregroundStyle(AppColors.coral)
                }
            }
        }
        .preferredColorScheme(.light)
    }

    private func save() {
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedName.isEmpty else {
            errorMessage = "请填写宝宝昵称。"
            return
        }

        onSave(trimmedName, birthDate, sex)
        dismiss()
    }
}

private struct ProfileMenuRow: View {
    let icon: String
    let title: String
    var value: String? = nil

    var body: some View {
        HStack(spacing: AppSpacing.medium) {
            Image(systemName: icon)
                .font(.system(size: 20, weight: .regular))
                .foregroundStyle(AppColors.sage)
                .frame(width: 38, height: 38)
            Text(title.localizedText)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.ink)
            Spacer()
            if let value {
                Text(value.localizedText)
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
            }
            Image(systemName: "chevron.right")
                .font(.system(size: 15, weight: .regular))
                .foregroundStyle(AppColors.inkSoft.opacity(0.72))
        }
        .padding(.horizontal, AppSpacing.roomy)
        .padding(.vertical, AppSpacing.regular)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(AppColors.softStroke.opacity(0.18))
                .frame(height: 1)
                .padding(.leading, 72)
                .padding(.trailing, AppSpacing.roomy)
        }
    }
}
