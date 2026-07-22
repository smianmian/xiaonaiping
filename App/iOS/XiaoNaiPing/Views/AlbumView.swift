import AVFoundation
import ImageIO
import Photos
import PhotosUI
import SwiftUI
import UIKit

struct AlbumView: View {
    @Environment(\.openURL) private var openURL
    @EnvironmentObject private var store: BabyRecordStore
    @EnvironmentObject private var cloudSync: CloudSyncController
    @State private var selectedFilter = "全部"
    @State private var selectedPhotoItems: [PhotosPickerItem] = []
    @State private var editingPhoto: BabyPhoto?
    @State private var deleteCandidate: BabyPhoto?
    @State private var importErrorMessage: String?
    @State private var importStatusMessage: String?
    @State private var isImportingPhotos = false
    @State private var isCameraPresented = false
    @State private var isPhotoPickerPresented = false
    @State private var permissionAlert: PhotoPermissionAlert?

    private let filters = ["全部", "本月"]
    private let columns = [
        GridItem(.flexible(), spacing: AppSpacing.regular),
        GridItem(.flexible(), spacing: AppSpacing.regular),
        GridItem(.flexible(), spacing: AppSpacing.regular)
    ]

    var body: some View {
        ScreenScaffold(title: "相册", showBackButton: true) {
            ZStack(alignment: .bottomTrailing) {
                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: AppSpacing.large) {
                        SegmentedPill(items: filters, selected: $selectedFilter)
                            .padding(.top, AppSpacing.small)

                        if store.babyPhotos.isEmpty {
                            emptyPhotoState
                        } else {
                            userPhotoSection
                        }

                        if let importErrorMessage {
                            Text(importErrorMessage)
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.coral)
                                .fixedSize(horizontal: false, vertical: true)
                        }

                        if isImportingPhotos || importStatusMessage != nil {
                            importStatusView
                        }
                    }
                    .padding(.horizontal, AppSpacing.page)
                    .padding(.bottom, AppSpacing.bottomBarSpace)
                }

                WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.small) {
                    HStack(spacing: AppSpacing.small) {
                        Button {
                            openCamera()
                        } label: {
                            Label("拍照", systemImage: "camera")
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.inkGreen)
                                .frame(minWidth: 84, minHeight: 44)
                                .background {
                                    RoundedRectangle(cornerRadius: AppShapes.smallRadius, style: .continuous)
                                        .fill(AppColors.milk.opacity(0.78))
                                }
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("打开相机添加照片")
                        .disabled(isImportingPhotos)

                        PrimaryWatercolorButton(title: "从相册添加", tint: AppColors.cream, foreground: AppColors.blueInk) {
                            openPhotoPicker()
                        }
                        .accessibilityLabel("从系统相册添加照片")
                        .disabled(isImportingPhotos)
                    }
                }
                .padding(.trailing, AppSpacing.page)
                .padding(.bottom, AppSpacing.bottomBarSpace - 22)
            }
        }
        .photosPicker(
            isPresented: $isPhotoPickerPresented,
            selection: $selectedPhotoItems,
            maxSelectionCount: 12,
            matching: .images
        )
        .onChange(of: selectedPhotoItems) { _, newItems in
            importPhotos(newItems)
        }
        .sheet(item: $editingPhoto) { photo in
            PhotoEditorSheet(photo: photo) { capturedAt, note in
                store.updatePhoto(photo, capturedAt: capturedAt, note: note)
            } onDelete: {
                deleteCandidate = photo
            }
            .presentationDetents([.medium])
        }
        .fullScreenCover(isPresented: $isCameraPresented) {
            CameraPicker { image in
                guard let data = image.jpegData(compressionQuality: 0.88) else {
                    importErrorMessage = "照片保存失败，请稍后再试。"
                    return
                }

                do {
                    try store.importPhoto(data: data, source: "camera")
                    importErrorMessage = nil
                    importStatusMessage = "已添加 1 张照片。"
                } catch {
                    importErrorMessage = "照片保存失败，请稍后再试。"
                }
            }
            .ignoresSafeArea()
        }
        .alert(permissionAlert?.title ?? "需要权限", isPresented: permissionAlertBinding, presenting: permissionAlert) { alert in
            if alert.showsSettingsButton {
                Button("去设置开启") {
                    openAppSettings()
                }
            }

            if alert == .cameraDenied {
                Button("从相册选择") {
                    isPhotoPickerPresented = true
                }
            }

            Button("稍后再说", role: .cancel) {}
        } message: { alert in
            Text(alert.message)
        }
        .alert("删除这张照片？", isPresented: deleteAlertBinding) {
            Button("删除", role: .destructive) {
                deleteSelectedPhoto()
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text(deleteAlertMessage)
        }
    }

    private var userPhotoSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.medium) {
            HStack(alignment: .firstTextBaseline, spacing: AppSpacing.medium) {
                Text("我的照片")
                    .font(AppTypography.navTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text("\(store.babyPhotos.count)张")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                AssetWatercolorImage(name: AppAssets.cloudBlue, mode: .multiply)
                    .frame(width: 46, height: 28)
            }

            syncStatusSummary

            if filteredPhotos.isEmpty {
                filteredEmptyState
            } else {
                VStack(alignment: .leading, spacing: AppSpacing.large) {
                    ForEach(photoDayGroups) { group in
                        PhotoTimelineDaySection(
                            title: timelineTitle(for: group.day),
                            subtitle: "\(group.photos.count)张",
                            photos: group.photos,
                            columns: columns,
                            photoURL: { store.photoURL(for: $0) },
                            onEdit: { editingPhoto = $0 }
                        )
                    }
                }
            }
        }
    }

    private var syncStatusSummary: some View {
        WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            HStack(alignment: .top, spacing: AppSpacing.medium) {
                Image(systemName: cloudSync.hasSession ? "checkmark.icloud" : "lock.icloud")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(AppColors.blueInk)
                    .frame(width: 28, height: 28)

                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                    Text(photoSyncTitle.localizedText)
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkGreen)
                    Text(photoSyncDetail.localizedText)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    private var photoSyncTitle: String {
        if cloudSync.hasSession {
            return "照片可随同步上传"
        }
        return cloudSync.isServiceConfigured ? "正在等待自动同步" : "正在连接同步服务"
    }

    private var photoSyncDetail: String {
        if cloudSync.hasSession {
            return "点击资料页的“立即同步”，会把主动加入小奶瓶的照片原图上传到私有账号空间。"
        }
        if cloudSync.isServiceConfigured {
            return "开启账号与同步前，照片只保存在 App 私有空间，不会自动上传。"
        }
        return "照片会在联网后自动同步到你的账号。"
    }

    private var filteredEmptyState: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
            Text("本月还没有添加到小奶瓶的照片。")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.inkSoft)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var importStatusView: some View {
        HStack(spacing: AppSpacing.small) {
            if isImportingPhotos {
                ProgressView()
                    .controlSize(.small)
            } else {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(AppColors.sage)
            }

            Text(importStatusMessage ?? "正在导入照片...")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.horizontal, AppSpacing.medium)
        .padding(.vertical, AppSpacing.small)
        .background {
            Capsule()
                .fill(AppColors.cream.opacity(0.68))
                .overlay {
                    Capsule()
                        .stroke(AppColors.softStroke.opacity(0.24), lineWidth: 1)
                }
        }
    }

    private var emptyPhotoState: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
            VStack(spacing: AppSpacing.medium) {
                AssetWatercolorImage(name: AppAssets.cameraIcon, mode: .multiply)
                    .frame(width: 72, height: 72)
                Text("还没有添加到小奶瓶的照片")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.inkGreen)
                Text("点击右下角添加照片，会复制到 App 私有空间；不会自动上传。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
        }
    }

    private var filteredPhotos: [BabyPhoto] {
        let photos: [BabyPhoto]
        switch selectedFilter {
        case "本月":
            let calendar = Calendar.current
            let currentComponents = calendar.dateComponents([.year, .month], from: Date())
            photos = store.babyPhotos.filter { photo in
                calendar.dateComponents([.year, .month], from: photo.capturedAt) == currentComponents
            }
        default:
            photos = store.babyPhotos
        }

        return photos.sorted { $0.capturedAt > $1.capturedAt }
    }

    private var photoDayGroups: [PhotoDayGroup] {
        let calendar = Calendar.current
        let groupedPhotos = Dictionary(grouping: filteredPhotos) { photo in
            calendar.startOfDay(for: photo.capturedAt)
        }

        return groupedPhotos
            .map { day, photos in
                PhotoDayGroup(day: day, photos: photos.sorted { $0.capturedAt > $1.capturedAt })
            }
            .sorted { $0.day > $1.day }
    }

    private var deleteAlertBinding: Binding<Bool> {
        Binding {
            deleteCandidate != nil
        } set: { isPresented in
            if !isPresented {
                deleteCandidate = nil
            }
        }
    }

    private var permissionAlertBinding: Binding<Bool> {
        Binding {
            permissionAlert != nil
        } set: { isPresented in
            if !isPresented {
                permissionAlert = nil
            }
        }
    }

    private var deleteAlertMessage: String {
        guard let deleteCandidate else {
            return "会删除 App 私有空间里的这张照片，不会删除系统相册原图。"
        }

        switch deleteCandidate.syncStatus {
        case .localOnly, .pending, .failed:
            return "会删除 App 私有空间里的这张照片，不会删除系统相册原图。"
        case .backedUp:
            return "会先删除私有账号空间里的云端原图，成功后再删除 App 私有空间照片；不会删除系统相册原图。"
        case .cloudDeletePending:
            return "会再次尝试删除私有账号空间里的云端原图；成功后再删除 App 私有空间照片。"
        }
    }

    private func deleteSelectedPhoto() {
        guard let photo = deleteCandidate else { return }
        deleteCandidate = nil

        switch photo.syncStatus {
        case .backedUp, .cloudDeletePending:
            Task {
                if await cloudSync.deleteCloudPhoto(photo) {
                    store.deletePhoto(photo)
                    editingPhoto = nil
                } else {
                    store.markCloudPhotoDeletePending(photo)
                    importErrorMessage = "照片删除同步失败，请稍后重试。"
                }
            }
        case .localOnly, .pending, .failed:
            store.deletePhoto(photo)
            editingPhoto = nil
        }
    }

    private func timelineTitle(for day: Date) -> String {
        let calendar = Calendar.current
        if calendar.isDateInToday(day) {
            return "今天"
        }

        if calendar.isDateInYesterday(day) {
            return "昨天"
        }

        return BabyRecordStore.displayDateString(from: day)
    }

    private func openCamera() {
        guard UIImagePickerController.isSourceTypeAvailable(.camera) else {
            importErrorMessage = "当前设备不可用相机，请从相册选择。"
            return
        }

        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            importErrorMessage = nil
            importStatusMessage = nil
            isCameraPresented = true
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { isGranted in
                DispatchQueue.main.async {
                    if isGranted {
                        importErrorMessage = nil
                        importStatusMessage = nil
                        isCameraPresented = true
                    } else {
                        permissionAlert = .cameraDenied
                    }
                }
            }
        case .denied, .restricted:
            permissionAlert = .cameraDenied
        @unknown default:
            permissionAlert = .cameraDenied
        }
    }

    private func openPhotoPicker() {
        switch PHPhotoLibrary.authorizationStatus(for: .readWrite) {
        case .authorized, .limited, .notDetermined:
            importErrorMessage = nil
            importStatusMessage = nil
            isPhotoPickerPresented = true
        case .denied, .restricted:
            permissionAlert = .photoLibraryDenied
        @unknown default:
            permissionAlert = .photoLibraryDenied
        }
    }

    private func openAppSettings() {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        openURL(url)
    }

    private func importPhotos(_ items: [PhotosPickerItem]) {
        guard !items.isEmpty else { return }
        importErrorMessage = nil
        importStatusMessage = "正在导入 \(items.count) 张照片..."
        isImportingPhotos = true

        Task {
            var importedCount = 0
            for (index, item) in items.enumerated() {
                await MainActor.run {
                    importStatusMessage = "正在导入第 \(index + 1) / \(items.count) 张照片..."
                }

                do {
                    if let data = try await item.loadTransferable(type: Data.self) {
                        let capturedAt = PhotoMetadataReader.capturedAt(from: data) ?? Date()
                        try await MainActor.run {
                            try store.importPhoto(data: data, capturedAt: capturedAt)
                            importedCount += 1
                        }
                    }
                } catch {
                    await MainActor.run {
                        importErrorMessage = "有照片导入失败，请稍后再试。"
                    }
                }
            }

            await MainActor.run {
                selectedPhotoItems = []
                isImportingPhotos = false
                if importedCount == 0 {
                    if importErrorMessage == nil {
                        importErrorMessage = "没有读取到可导入的照片。"
                    }
                    importStatusMessage = nil
                } else if importedCount > 0 {
                    importStatusMessage = "已添加 \(importedCount) 张照片。"
                }
            }
        }
    }
}

private enum PhotoMetadataReader {
    static func capturedAt(from data: Data) -> Date? {
        guard let source = CGImageSourceCreateWithData(data as CFData, nil),
              let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any] else {
            return nil
        }

        let exif = properties[kCGImagePropertyExifDictionary] as? [CFString: Any]
        let tiff = properties[kCGImagePropertyTIFFDictionary] as? [CFString: Any]
        let rawDate = exif?[kCGImagePropertyExifDateTimeOriginal] as? String
            ?? exif?[kCGImagePropertyExifDateTimeDigitized] as? String
            ?? tiff?[kCGImagePropertyTIFFDateTime] as? String

        guard let rawDate else { return nil }
        return exifDateFormatter.date(from: rawDate)
    }

    private static let exifDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy:MM:dd HH:mm:ss"
        return formatter
    }()
}

private enum PhotoPermissionAlert: Identifiable, Equatable {
    case cameraDenied
    case photoLibraryDenied

    var id: String { title }

    var title: String {
        switch self {
        case .cameraDenied:
            "需要相机权限"
        case .photoLibraryDenied:
            "需要相册权限"
        }
    }

    var message: String {
        switch self {
        case .cameraDenied:
            "开启相机权限后，才能拍摄并保存宝宝照片。也可以先从相册选择。"
        case .photoLibraryDenied:
            "开启相册权限后，才能选择照片并复制到小奶瓶私有空间。"
        }
    }

    var showsSettingsButton: Bool {
        true
    }
}

private struct PhotoDayGroup: Identifiable {
    let day: Date
    let photos: [BabyPhoto]

    var id: Date { day }
}

private struct PhotoTimelineDaySection: View {
    let title: String
    let subtitle: String
    let photos: [BabyPhoto]
    let columns: [GridItem]
    let photoURL: (BabyPhoto) -> URL
    let onEdit: (BabyPhoto) -> Void

    var body: some View {
        HStack(alignment: .top, spacing: AppSpacing.medium) {
            VStack(spacing: AppSpacing.tiny) {
                Circle()
                    .fill(AppColors.coral.opacity(0.72))
                    .frame(width: 9, height: 9)
                Rectangle()
                    .fill(AppColors.softStroke.opacity(0.36))
                    .frame(width: 1)
                    .frame(minHeight: 108)
            }
            .padding(.top, 7)

            VStack(alignment: .leading, spacing: AppSpacing.regular) {
                HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
                    Text(title)
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkGreen)
                    Text(subtitle)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                }

                LazyVGrid(columns: columns, spacing: AppSpacing.regular) {
                    ForEach(photos) { photo in
                        Button {
                            onEdit(photo)
                        } label: {
                            ZStack(alignment: .bottomLeading) {
                                LocalPhotoCell(url: photoURL(photo))
                                PhotoSyncStatusBadge(status: photo.syncStatus)
                                    .padding(6)
                            }
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("编辑\(title)的照片，\(photo.syncStatus.accessibilityText)")
                    }
                }
            }
        }
    }
}

private struct PhotoSyncStatusBadge: View {
    let status: PhotoSyncStatus

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: status.systemImage)
                .font(.system(size: 10, weight: .semibold))
            Text(status.title)
                .font(.caption2)
        }
        .foregroundStyle(status.foreground)
        .padding(.horizontal, 7)
        .padding(.vertical, 4)
        .background {
            Capsule()
                .fill(status.tint.opacity(0.88))
        }
    }
}

private extension PhotoSyncStatus {
    var title: String {
        switch self {
        case .localOnly:
            "等待同步"
        case .pending:
            "待同步"
        case .backedUp:
            "已同步"
        case .failed:
            "同步失败"
        case .cloudDeletePending:
            "待删云端"
        }
    }

    var accessibilityText: String {
        switch self {
        case .localOnly:
            "联网后会自动同步"
        case .pending:
            "等待云同步"
        case .backedUp:
            "已经完成云同步"
        case .failed:
            "云同步失败"
        case .cloudDeletePending:
            "云端删除待完成"
        }
    }

    var systemImage: String {
        switch self {
        case .localOnly:
            "lock.fill"
        case .pending:
            "icloud.and.arrow.up"
        case .backedUp:
            "checkmark.icloud"
        case .failed:
            "exclamationmark.icloud"
        case .cloudDeletePending:
            "icloud.slash"
        }
    }

    var tint: Color {
        switch self {
        case .localOnly:
            AppColors.inkGreen
        case .pending:
            AppColors.blueInk
        case .backedUp:
            AppColors.sage
        case .failed:
            AppColors.coral
        case .cloudDeletePending:
            AppColors.inkSoft
        }
    }

    var foreground: Color {
        .white
    }
}

private struct CameraPicker: UIViewControllerRepresentable {
    let onImage: (UIImage) -> Void
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.allowsEditing = false
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(onImage: onImage, dismiss: dismiss)
    }

    final class Coordinator: NSObject, UINavigationControllerDelegate, UIImagePickerControllerDelegate {
        let onImage: (UIImage) -> Void
        let dismiss: DismissAction

        init(onImage: @escaping (UIImage) -> Void, dismiss: DismissAction) {
            self.onImage = onImage
            self.dismiss = dismiss
        }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            if let image = info[.originalImage] as? UIImage {
                onImage(image)
            }
            dismiss()
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            dismiss()
        }
    }
}

private struct LocalPhotoCell: View {
    let url: URL
    @State private var thumbnail: UIImage?

    var body: some View {
        ZStack {
            if let thumbnail {
                Image(uiImage: thumbnail)
                    .resizable()
                    .scaledToFill()
            } else {
                AppColors.cream.opacity(0.72)
                Image(systemName: "photo")
                    .foregroundStyle(AppColors.inkSoft)
            }
        }
        .frame(height: 104)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        .task(id: url) {
            thumbnail = await LocalPhotoThumbnailer.thumbnail(for: url, maxPixelSize: 360)
        }
    }
}

private enum LocalPhotoThumbnailer {
    static func thumbnail(for url: URL, maxPixelSize: Int) async -> UIImage? {
        await Task.detached(priority: .utility) {
            let sourceOptions: [CFString: Any] = [
                kCGImageSourceShouldCache: false
            ]

            guard let source = CGImageSourceCreateWithURL(url as CFURL, sourceOptions as CFDictionary) else {
                return nil
            }

            let thumbnailOptions: [CFString: Any] = [
                kCGImageSourceCreateThumbnailFromImageAlways: true,
                kCGImageSourceCreateThumbnailWithTransform: true,
                kCGImageSourceShouldCacheImmediately: true,
                kCGImageSourceThumbnailMaxPixelSize: maxPixelSize
            ]

            guard let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, thumbnailOptions as CFDictionary) else {
                return nil
            }

            return UIImage(cgImage: cgImage)
        }.value
    }
}

private struct PhotoEditorSheet: View {
    let photo: BabyPhoto
    let onSave: (Date, String) -> Void
    let onDelete: () -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var capturedAt: Date
    @State private var note: String
    @State private var showsMoreDetails = false

    init(photo: BabyPhoto, onSave: @escaping (Date, String) -> Void, onDelete: @escaping () -> Void) {
        self.photo = photo
        self.onSave = onSave
        self.onDelete = onDelete
        _capturedAt = State(initialValue: photo.capturedAt)
        _note = State(initialValue: photo.note)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: AppSpacing.large) {
                WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            PhotoSyncStatusBadge(status: photo.syncStatus)
                            DatePicker("照片日期", selection: $capturedAt, displayedComponents: [.date])
                        }
                    }

                    WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius, padding: 0) {
                        Button {
                            withAnimation {
                                showsMoreDetails.toggle()
                            }
                        } label: {
                            HStack(spacing: AppSpacing.small) {
                                Image(systemName: showsMoreDetails ? "chevron.up" : "chevron.down")
                                Text("更多详情（可不填）")
                                Spacer(minLength: 0)
                                Text(showsMoreDetails ? "收起" : "添加备注")
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.inkSoft)
                            }
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkGreen)
                            .padding(.horizontal, AppSpacing.medium)
                            .padding(.vertical, AppSpacing.regular)
                        }
                        .buttonStyle(.plain)
                    }

                    if showsMoreDetails {
                        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius) {
                            TextField("备注，可不填", text: $note, axis: .vertical)
                                .lineLimit(2...4)
                                .textFieldStyle(.roundedBorder)
                        }
                    }

                PrimaryWatercolorButton(title: "保存照片信息") {
                    onSave(capturedAt, note)
                    dismiss()
                }

                Button(role: .destructive) {
                    onDelete()
                } label: {
                    Text("删除这张照片")
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.coral)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                }

                Spacer()
            }
            .padding(AppSpacing.large)
            .background(PaperBackgroundView())
            .navigationTitle("照片信息")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") {
                        dismiss()
                    }
                }
            }
        }
    }
}
