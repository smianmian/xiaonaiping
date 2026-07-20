import SwiftUI
import UIKit

enum AppRoute: Hashable {
    case album
    case feeding
    case water
    case sleep
    case diaper
    case milestone
    case growth
    case vaccine
    case monthlyReport
}

struct RootTabView: View {
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var store: BabyRecordStore
    @StateObject private var cloudBackup = CloudBackupController()
    @State private var selectedTab: AppTab
    @State private var homePath: [AppRoute] = []
    @State private var growthPath: [AppRoute] = []
    @State private var recordPath: [AppRoute] = []
    @AppStorage("xnpNightModeEnabled") private var nightModeEnabled = false

    init() {
        Self.configureTabBarAppearance()
#if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        let seedMockData = arguments.contains("-XNPScreenshotData")
        _store = StateObject(wrappedValue: BabyRecordStore(seedMockData: seedMockData))
        _selectedTab = State(initialValue: Self.initialTab(from: arguments))
#else
        _store = StateObject(wrappedValue: BabyRecordStore())
        _selectedTab = State(initialValue: .home)
#endif
    }

    var body: some View {
        ZStack {
            if shouldShowLaunchLogin {
                LaunchLoginView(cloudBackup: cloudBackup, store: store)
            } else if store.hasCompletedOnboarding {
                tabContent
            } else {
                OnboardingView { name, birthDate, sex in
                    store.createBabyProfile(name: name, birthDate: birthDate, sex: sex)
                }
            }
        }
        .ignoresSafeArea(.keyboard)
        .preferredColorScheme(nightModeEnabled ? .dark : nil)
        .environmentObject(store)
        .environmentObject(cloudBackup)
        .onAppear(perform: syncFeedingReminderLiveActivity)
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                syncFeedingReminderLiveActivity()
                Task {
                    await cloudBackup.syncIfNeeded(store: store)
                }
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .babyRecordStoreDidSave)) { _ in
            cloudBackup.scheduleAutomaticSync(store: store)
        }
        .alert("保存失败", isPresented: saveErrorAlertBinding) {
            Button("知道了") {
                store.clearSaveError()
            }
        } message: {
            Text(store.saveErrorMessage ?? "请稍后再试。")
        }
    }

    private var shouldShowLaunchLogin: Bool {
        guard !cloudBackup.hasSession else {
            return false
        }

        #if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        if arguments.contains("-XNPScreenshotData")
            || arguments.contains("-XNPScreenshotTab")
            || arguments.contains("-XNPScreenshotBackupSheet") {
            return false
        }
        return cloudBackup.isServiceConfigured
        #else
        return true
        #endif
    }

    private var tabContent: some View {
        ZStack {
            TabView(selection: $selectedTab) {
                NavigationStack(path: $homePath) {
                    HomeView(
                        onRoute: { homePath.append($0) },
                        onOpenAlbum: {
                            homePath.append(.album)
                        }
                    )
                    .navigationDestination(for: AppRoute.self) { route in
                        routeView(route) {
                            homePath.append(.monthlyReport)
                        }
                    }
                }
                .tabItem {
                    tabLabel(.home)
                }
                .tag(AppTab.home)

                NavigationStack(path: $growthPath) {
                    GrowthView(
                        onOpenMonthlyReport: {
                            growthPath.append(.monthlyReport)
                        },
                        onOpenVaccineBook: {
                            growthPath.append(.vaccine)
                        }
                    )
                    .navigationDestination(for: AppRoute.self) { route in
                        routeView(route) {
                            growthPath.append(.monthlyReport)
                        }
                    }
                }
                .tabItem {
                    tabLabel(.growth)
                }
                .tag(AppTab.growth)

                NavigationStack(path: $recordPath) {
                    RecordHomeView { route in
                        recordPath.append(route)
                    }
                    .navigationDestination(for: AppRoute.self) { route in
                        routeView(route) {
                            recordPath.append(.monthlyReport)
                        }
                    }
                }
                .tabItem {
                    tabLabel(.record)
                }
                .tag(AppTab.record)

                NavigationStack {
                    ProfileView()
                }
                .tabItem {
                    tabLabel(.profile)
                }
                .tag(AppTab.profile)
            }
            .tint(AppColors.coral)
            .toolbarBackground(AppColors.milk.opacity(0.94), for: .tabBar)
            .toolbarBackground(.visible, for: .tabBar)
        }
    }

    private var saveErrorAlertBinding: Binding<Bool> {
        Binding {
            store.saveErrorMessage != nil
        } set: { isPresented in
            if !isPresented {
                store.clearSaveError()
            }
        }
    }

    private func syncFeedingReminderLiveActivity() {
        #if canImport(ActivityKit)
        if #available(iOS 16.2, *) {
            guard store.feedingLiveActivityEnabled else {
                FeedingReminderLiveActivityController.endAll()
                return
            }
            FeedingReminderLiveActivityController.sync(
                reminder: store.nextFeedingReminder,
                babyName: store.baby.name,
                babyAvatarData: store.baby.avatarImageData
            )
        }
        #endif
    }

    @ViewBuilder
    private func tabLabel(_ tab: AppTab) -> some View {
        Image(systemName: tab.systemImage)
        Text(tab.rawValue.localizedText)
    }

    @ViewBuilder
    private func routeView(_ route: AppRoute, onMonthlyReport: @escaping () -> Void) -> some View {
        switch route {
        case .album:
            AlbumView()
        case .feeding:
            FeedingRecordView()
        case .water:
            WaterRecordView()
        case .sleep:
            SleepRecordView()
        case .diaper:
            DiaperRecordView()
        case .milestone:
            MilestoneView()
        case .growth:
            GrowthView(onOpenMonthlyReport: onMonthlyReport)
        case .vaccine:
            VaccineView()
        case .monthlyReport:
            MonthlyReportDetailView()
        }
    }

    private static func configureTabBarAppearance() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor(red: 1.000, green: 0.988, blue: 0.960, alpha: 1)
        appearance.shadowColor = UIColor(red: 0.790, green: 0.715, blue: 0.620, alpha: 0.28)

        let itemAppearance = UITabBarItemAppearance()
        itemAppearance.normal.titleTextAttributes = [
            .foregroundColor: UIColor(red: 0.440, green: 0.515, blue: 0.410, alpha: 1)
        ]
        itemAppearance.selected.titleTextAttributes = [
            .foregroundColor: UIColor(red: 0.875, green: 0.360, blue: 0.290, alpha: 1)
        ]
        itemAppearance.normal.iconColor = UIColor(red: 0.440, green: 0.515, blue: 0.410, alpha: 1)
        itemAppearance.selected.iconColor = UIColor(red: 0.875, green: 0.360, blue: 0.290, alpha: 1)

        appearance.stackedLayoutAppearance = itemAppearance
        appearance.inlineLayoutAppearance = itemAppearance
        appearance.compactInlineLayoutAppearance = itemAppearance

        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance
        UITabBar.appearance().tintColor = UIColor(red: 0.875, green: 0.360, blue: 0.290, alpha: 1)
        UITabBar.appearance().unselectedItemTintColor = UIColor(red: 0.440, green: 0.515, blue: 0.410, alpha: 1)
    }

#if DEBUG
    private static func initialTab(from arguments: [String]) -> AppTab {
        guard let index = arguments.firstIndex(of: "-XNPScreenshotTab"),
              arguments.indices.contains(index + 1) else {
            return .home
        }

        switch arguments[index + 1].lowercased() {
        case "growth":
            return .growth
        case "record":
            return .record
        case "profile":
            return .profile
        default:
            return .home
        }
    }
#endif
}

private struct LaunchLoginView: View {
    private enum PhoneLoginField {
        case phoneNumber
        case verificationCode
    }

    @ObservedObject var cloudBackup: CloudBackupController
    @ObservedObject var store: BabyRecordStore

    @State private var phoneNumber = "+86"
    @State private var phoneCode = ""
    @State private var isPhoneCodeRequested = false
    @FocusState private var focusedPhoneLoginField: PhoneLoginField?

    var body: some View {
        ScreenScaffold {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.roomy) {
                    hero

                    if cloudBackup.isServiceConfigured {
                        phoneLoginCard
                        if shouldShowStatusLine {
                            statusLine
                        }

                        if cloudBackup.isWeChatLoginConfigured {
                            weChatLoginButton
                        }
                    } else {
                        serviceUnavailableCard
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.large)
                .padding(.bottom, AppSpacing.xlarge)
            }
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("完成") {
                        focusedPhoneLoginField = nil
                    }
                }
            }
        }
    }

    private var hero: some View {
        VStack(spacing: AppSpacing.small) {
            AssetWatercolorImage(name: AppAssets.homeBottleHero, mode: .multiply)
                .frame(width: 72, height: 94)

            VStack(spacing: AppSpacing.tiny) {
                Text("登录小奶瓶")
                    .font(AppTypography.title)
                    .foregroundStyle(AppColors.inkGreen)
                    .multilineTextAlignment(.center)
                Text("登录后可备份宝宝的每一次成长记录。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var phoneLoginCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Label("手机号登录", systemImage: "iphone")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)

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
                        await cloudBackup.requestPhoneCode(phoneNumber: normalizedPhoneNumber)
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
                .disabled(cloudBackup.isWorking || !canRequestPhoneCode)

                if isPhoneCodeRequested {
                    TextField("6 位验证码", text: $phoneCode)
                        .keyboardType(.numberPad)
                        .textFieldStyle(.roundedBorder)
                        .focused($focusedPhoneLoginField, equals: .verificationCode)
                        .onChange(of: phoneCode) { _, code in
                            if CloudBackupController.validateSmsCode(code) {
                                focusedPhoneLoginField = nil
                            }
                        }

                    if let codeValidationMessage {
                        Text(codeValidationMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                    }

                    PrimaryWatercolorButton(title: "手机号登录", tint: AppColors.blush, foreground: AppColors.coral) {
                        focusedPhoneLoginField = nil
                        Task {
                            await cloudBackup.verifyPhoneCode(phoneNumber: normalizedPhoneNumber, code: normalizedPhoneCode, store: store)
                        }
                    }
                    .disabled(cloudBackup.isWorking || !canVerifyPhoneCode)
                    .opacity(cloudBackup.isWorking || !canVerifyPhoneCode ? 0.55 : 1)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var statusLine: some View {
        HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
            Image(systemName: cloudBackup.isWorking ? "arrow.triangle.2.circlepath" : "info.circle")
                .foregroundStyle(AppColors.blueInk)
            Text("\(cloudBackup.statusTitle.localizedText)：\(cloudBackup.statusDetail.localizedText)")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var shouldShowStatusLine: Bool {
        cloudBackup.isWorking || cloudBackup.statusTitle != "未开启"
    }

    private var weChatLoginButton: some View {
        Button {
            Task {
                await cloudBackup.loginWithWeChat(store: store)
            }
        } label: {
            Label("微信登录", systemImage: "message")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.inkGreen)
                .frame(maxWidth: .infinity)
                .frame(minHeight: 44)
                .overlay {
                    Capsule()
                        .stroke(AppColors.sage.opacity(0.42), lineWidth: 1)
                }
        }
        .buttonStyle(.plain)
        .disabled(cloudBackup.isWorking || !cloudBackup.isWeChatLoginConfigured)
        .opacity(cloudBackup.isWorking || !cloudBackup.isWeChatLoginConfigured ? 0.55 : 1)
        .accessibilityHint(weChatLoginDetail)
    }

    private var serviceUnavailableCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Label("账号服务暂未配置", systemImage: "icloud.slash")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text("需要配置正式 API、短信验证码和微信开放平台后才能登录。")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.inkSoft)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var weChatLoginDetail: String {
        if cloudBackup.isNativeWeChatLoginAvailable {
            return "微信开放平台已配置；授权后会连接到小奶瓶私有账号。".localizedText
        }
        return "微信登录未启用：请先完成微信 OpenSDK、AppID、URL Scheme、Universal Link 和服务端凭证配置。".localizedText
    }

    private var normalizedPhoneNumber: String {
        phoneNumber.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var normalizedPhoneCode: String {
        phoneCode.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canRequestPhoneCode: Bool {
        CloudBackupController.validateE164PhoneNumber(normalizedPhoneNumber)
        && !cloudBackup.isWorking
    }

    private var canVerifyPhoneCode: Bool {
        CloudBackupController.validateE164PhoneNumber(normalizedPhoneNumber)
        && CloudBackupController.validateSmsCode(normalizedPhoneCode)
        && !cloudBackup.isWorking
    }

    private var phoneValidationMessage: String? {
        if normalizedPhoneNumber.isEmpty || normalizedPhoneNumber == "+86" {
            return nil
        }
        return CloudBackupController.validateE164PhoneNumber(normalizedPhoneNumber) ? nil : "手机号格式不正确，需以 + 开头。"
    }

    private var codeValidationMessage: String? {
        if normalizedPhoneCode.isEmpty {
            return nil
        }
        return CloudBackupController.validateSmsCode(normalizedPhoneCode) ? nil : "验证码格式不正确，需 6 位数字。"
    }
}

private struct WaterRecordView: View {
    @EnvironmentObject private var store: BabyRecordStore
    @State private var occurredAt = Date()
    @State private var amountML = 60

    var body: some View {
        ScreenScaffold(title: "喝水记录", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.largeCardRadius) {
                        VStack(alignment: .leading, spacing: AppSpacing.medium) {
                            Label("记录喝水", systemImage: "drop.fill")
                                .font(AppTypography.sectionTitle)
                                .foregroundStyle(AppColors.inkGreen)
                            DatePicker("时间", selection: $occurredAt, in: ...Date(), displayedComponents: [.date, .hourAndMinute])
                                .tint(AppColors.blueInk)
                            Stepper(value: $amountML, in: 10...600, step: 10) {
                                HStack {
                                    Text("饮水量")
                                    Spacer()
                                    Text("\(amountML)ml")
                                        .foregroundStyle(AppColors.blueInk)
                                }
                                .font(AppTypography.bodyLarge)
                                .foregroundStyle(AppColors.ink)
                            }
                            PrimaryWatercolorButton(title: "保存喝水记录", tint: AppColors.mistBlue, foreground: AppColors.blueInk) {
                                guard store.upsert(WaterRecord(occurredAt: occurredAt, amountML: amountML)) else { return }
                                occurredAt = Date()
                                amountML = 60
                            }
                        }
                    }

                    VStack(alignment: .leading, spacing: AppSpacing.regular) {
                        SectionTitleView(title: "今天喝水")
                        if store.todayWaterRecords.isEmpty {
                            WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
                                Text("今天还没有喝水记录。")
                                    .font(AppTypography.body)
                                    .foregroundStyle(AppColors.inkSoft)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        } else {
                            ForEach(store.todayWaterRecords) { record in
                                HStack {
                                    Label("\(record.amountML)ml", systemImage: "drop.fill")
                                        .font(AppTypography.bodyLarge)
                                        .foregroundStyle(AppColors.inkGreen)
                                    Spacer()
                                    Text(BabyRecordStore.timeString(from: record.occurredAt))
                                        .font(AppTypography.body)
                                        .foregroundStyle(AppColors.inkSoft)
                                    Button(role: .destructive) {
                                        store.deleteWaterRecord(record)
                                    } label: {
                                        Image(systemName: "trash")
                                    }
                                    .buttonStyle(.plain)
                                }
                                .padding(AppSpacing.medium)
                                .background(AppColors.cream, in: RoundedRectangle(cornerRadius: AppShapes.cardRadius, style: .continuous))
                            }
                        }
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.vertical, AppSpacing.medium)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
    }
}

private struct RecordHomeView: View {
    @EnvironmentObject private var store: BabyRecordStore

    let onRoute: (AppRoute) -> Void

    private let columns = [
        GridItem(.flexible(), spacing: AppSpacing.medium),
        GridItem(.flexible(), spacing: AppSpacing.medium)
    ]

    var body: some View {
        ScreenScaffold(title: "记录") {
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: AppSpacing.large) {
                    headerCard
                    SectionTitleView(title: "快速记录")
                    actionGrid
                    SectionTitleView(title: "今日概览")
                    todaySummary
                    recentRecords
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.medium)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
    }

    private var headerCard: some View {
        WatercolorCard(tint: AppColors.blush, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.large) {
            HStack(spacing: AppSpacing.medium) {
                AssetWatercolorImage(name: AppAssets.tabRecordDrawing, mode: .multiply)
                    .frame(width: 76, height: 70)

                VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                    Text("今天记了 \(todayRecordCount) 件")
                        .font(AppTypography.sectionTitle)
                        .foregroundStyle(AppColors.inkGreen)
                    Text(headerDetailText)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                        .fixedSize(horizontal: false, vertical: true)
                }

                Spacer(minLength: 0)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityElement(children: .combine)
    }

    private var actionGrid: some View {
        LazyVGrid(columns: columns, spacing: AppSpacing.medium) {
            ForEach(QuickRecordAction.allCases) { action in
                Button {
                    onRoute(route(for: action))
                } label: {
                    WatercolorCard(tint: action.tint, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
                        HStack(spacing: AppSpacing.regular) {
                            AssetWatercolorImage(name: action.asset, mode: .multiply)
                                .frame(width: 44, height: 44)

                            Text(title(for: action))
                                .font(AppTypography.bodyLarge)
                                .foregroundStyle(AppColors.ink)
                                .lineLimit(2)
                                .minimumScaleFactor(0.82)

                            Spacer(minLength: 0)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .frame(height: 50)
                    }
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("record_action_\(action.id)")
            }
        }
    }

    private var todaySummary: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            LazyVGrid(columns: columns, spacing: AppSpacing.medium) {
                RecordSummaryMetric(title: "喂养", value: "\(store.feedingCount)次", detail: "\(store.milkAmountML)ml")
                RecordSummaryMetric(title: "喝水", value: "\(store.todayWaterRecords.count)次", detail: "\(store.waterAmountML)ml")
                RecordSummaryMetric(title: "睡眠", value: store.sleepDurationText, detail: store.ongoingSleep == nil ? "今日累计" : "进行中")
                RecordSummaryMetric(title: "排便", value: "\(store.poopCount)次", detail: "小便 \(store.peeCount)次")
                RecordSummaryMetric(title: "照片", value: "\(store.todayPhotoCount)张", detail: "今日新增")
            }
        }
    }

    private var recentRecords: some View {
        VStack(alignment: .leading, spacing: AppSpacing.regular) {
            SectionTitleView(title: "最近记录")

            if store.recentHomeRecords.isEmpty {
                WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
                    Text("今天还没有记录。")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.inkSoft)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            } else {
                VStack(spacing: AppSpacing.small) {
                    ForEach(store.recentHomeRecords.prefix(5)) { record in
                        RecordRowView(
                            icon: record.icon,
                            time: record.time,
                            title: record.title,
                            detail: record.detail,
                            tint: AppColors.cream
                        )
                        .accessibilityElement(children: .combine)
                    }
                }
            }
        }
    }

    private var todayRecordCount: Int {
        store.feedingCount + store.todayWaterRecords.count + store.todaySleepRecords.count + store.todayDiaperRecords.count + store.todayPhotoCount
    }

    private var headerDetailText: String {
        if store.ongoingSleep != nil {
            return "睡眠正在进行中，醒来后记得结束。"
        }

        guard store.hasTodayRecords else {
            return "喂养、喝水、睡眠、排便和照片都在这里。"
        }

        return "喂养 \(store.feedingCount) 次，喝水 \(store.waterAmountML)ml，睡眠 \(store.sleepDurationText)。"
    }

    private func title(for action: QuickRecordAction) -> String {
        switch action {
        case .feeding:
            return "喂养"
        case .water:
            return "喝水"
        case .sleep:
            return store.ongoingSleep == nil ? "睡眠" : "结束睡眠"
        case .diaper:
            return "排便"
        case .photo:
            return "照片"
        case .growth:
            return "身高体重"
        case .milestone:
            return "纪念日"
        }
    }

    private func route(for action: QuickRecordAction) -> AppRoute {
        switch action {
        case .feeding:
            return .feeding
        case .water:
            return .water
        case .sleep:
            return .sleep
        case .diaper:
            return .diaper
        case .photo:
            return .album
        case .growth:
            return .growth
        case .milestone:
            return .milestone
        }
    }
}

private struct RecordSummaryMetric: View {
    let title: String
    let value: String
    let detail: String

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.tiny) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
            Text(value)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.inkGreen)
                .lineLimit(1)
                .minimumScaleFactor(0.75)
            Text(detail)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
                .lineLimit(1)
                .minimumScaleFactor(0.75)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct OnboardingView: View {
    let onCreate: (String, Date, String) -> Void

    @State private var name = "宝宝"
    @State private var birthDate = Date()
    @State private var sex = "未设置"
    @State private var errorMessage: String?

    private let sexOptions = ["未设置", "女宝", "男宝"]

    var body: some View {
        ScreenScaffold {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    hero
                    formCard
                    privacyCard

                    if let errorMessage {
                        Text(errorMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    PrimaryWatercolorButton(title: "创建宝宝档案") {
                        create()
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.roomy)
                .padding(.bottom, AppSpacing.roomy)
            }
        }
    }

    private var hero: some View {
        VStack(spacing: AppSpacing.medium) {
            AssetWatercolorImage(name: AppAssets.homeBottleHero, mode: .multiply)
                .frame(width: 96, height: 132)
            VStack(spacing: AppSpacing.tiny) {
                Text("先为宝宝建一个小档案")
                    .font(AppTypography.heroTitle)
                    .foregroundStyle(AppColors.inkGreen)
                    .multilineTextAlignment(.center)
                Text("之后每一次喂养、睡眠、排便和照片，都会归到这个档案里。")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.inkSoft)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var formCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                Text("宝宝信息")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)

                TextField("宝宝昵称", text: $name)
                    .font(AppTypography.bodyLarge)
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
                    .font(AppTypography.readableBody)
                    .tint(AppColors.coral)

                Picker("性别", selection: $sex) {
                    ForEach(sexOptions, id: \.self) { option in
                        Text(option).tag(option)
                    }
                }
                .font(AppTypography.readableBody)
                .tint(AppColors.coral)
            }
        }
    }

    private var privacyCard: some View {
        WatercolorCard(tint: AppColors.mistBlue, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Label("隐私提示", systemImage: "shield")
                    .font(AppTypography.cardTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text("登录后，宝宝资料、记录和主动加入 App 的照片原图会自动同步，并可在资料页管理账号与备份。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func create() {
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedName.isEmpty else {
            errorMessage = "请填写宝宝昵称。"
            return
        }

        errorMessage = nil
        onCreate(trimmedName, birthDate, sex)
    }

}
