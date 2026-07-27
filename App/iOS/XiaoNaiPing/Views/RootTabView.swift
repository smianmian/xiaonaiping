import SwiftUI
import UIKit

enum AppRoute: Hashable {
    case album
    case feeding
    case feedingForm
    case water
    case waterForm
    case sleep
    case sleepForm
    case diaper
    case diaperForm
    case milestone
    case growth
    case growthForm
    case vaccine
    case health
    case monthlyReport
}

struct RootTabView: View {
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var store: BabyRecordStore
    @StateObject private var cloudSync = CloudSyncController()
    @StateObject private var familySync = FamilySyncEngine()
    @State private var selectedTab: AppTab
    @State private var homePath: [AppRoute] = []
    @State private var growthPath: [AppRoute] = []
    @State private var recordPath: [AppRoute] = []
    @State private var isQuickRecordPresented = false
    @State private var pendingQuickRecordRoute: AppRoute?
    @State private var isRegistering = false
    @State private var isReadyToCreateProfile = false
    @AppStorage("xnpNightModeEnabled") private var nightModeEnabled = false

    init() {
        Self.configureTabBarAppearance()
#if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        let seedMockData = arguments.contains("-XNPScreenshotData")
        _store = StateObject(wrappedValue: BabyRecordStore(seedMockData: seedMockData))
        _selectedTab = State(initialValue: Self.initialTab(from: arguments))
        _isQuickRecordPresented = State(initialValue: arguments.contains("-XNPScreenshotQuickRecord"))
#else
        _store = StateObject(wrappedValue: BabyRecordStore())
        _selectedTab = State(initialValue: .home)
#endif
    }

    var body: some View {
        ZStack {
            if store.hasCompletedOnboarding {
                if shouldShowLaunchLogin {
                    LaunchLoginView(cloudSync: cloudSync, store: store, onContinueToProfile: {})
                } else {
                    tabContent
                }
            } else if isReadyToCreateProfile {
                OnboardingView { name, birthDate, sex in
                    store.createBabyProfile(name: name, birthDate: birthDate, sex: sex)
                }
            } else if isRegistering {
                LaunchLoginView(cloudSync: cloudSync, store: store) {
                    isReadyToCreateProfile = true
                }
            } else {
                WelcomeIntroView(
                    onStart: {
                        isRegistering = true
                    }
                )
            }
        }
        .ignoresSafeArea(.keyboard)
        .preferredColorScheme(nightModeEnabled ? .dark : nil)
        .environmentObject(store)
        .environmentObject(cloudSync)
        .environmentObject(familySync)
        .onAppear(perform: syncFeedingReminderLiveActivity)
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                syncFeedingReminderLiveActivity()
                Task {
                    await cloudSync.syncIfNeeded(store: store)
                }
                Task {
                    await familySync.refreshMembership()
                    await familySync.syncNow(store: store)
                }
            }
            if phase == .background {
                // 写盘是后台队列异步的；退后台前同步等待，保证已保存的记录都落盘。
                store.flushPersistence()
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .babyRecordStoreDidSave)) { _ in
            cloudSync.scheduleAutomaticSync(store: store)
            familySync.scheduleAutomaticSync(store: store)
        }
        .onOpenURL { url in
            handleQuickLogURL(url)
        }
        .alert("保存失败", isPresented: saveErrorAlertBinding) {
            Button("知道了") {
                store.clearSaveError()
            }
        } message: {
            Text(store.saveErrorMessage ?? "请稍后再试。")
        }
        .alert("数据读取异常", isPresented: loadErrorAlertBinding) {
            Button("知道了") {
                store.loadErrorMessage = nil
            }
        } message: {
            Text(store.loadErrorMessage ?? "")
        }
    }

    private var shouldShowLaunchLogin: Bool {
        guard store.hasCompletedOnboarding, !cloudSync.hasSession else {
            return false
        }

        #if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        if arguments.contains("-XNPScreenshotData")
            || arguments.contains("-XNPScreenshotTab")
            || arguments.contains("-XNPScreenshotAccountSheet") {
            return false
        }
        return cloudSync.isServiceConfigured
        #else
        return true
        #endif
    }

    private var tabContent: some View {
        ZStack {
            TabView(selection: tabSelection) {
                NavigationStack(path: $homePath) {
                    HomeView(
                        onRoute: { homePath.append($0) },
                        onOpenAlbum: {
                            homePath.append(.album)
                        },
                        onQuickRecord: {
                            isQuickRecordPresented = true
                        }
                    )
                    .navigationDestination(for: AppRoute.self) { route in
                        routeView(route) {
                            homePath.append(.monthlyReport)
                        }
                        .toolbar(.hidden, for: .tabBar)
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
                        .toolbar(.hidden, for: .tabBar)
                    }
                }
                .tabItem {
                    tabLabel(.growth)
                }
                .tag(AppTab.growth)

                NavigationStack(path: $recordPath) {
                    RecordCenterView(onRoute: { recordPath.append($0) })
                        .navigationDestination(for: AppRoute.self) { route in
                            routeView(route) {
                                recordPath.append(.monthlyReport)
                            }
                            .toolbar(.hidden, for: .tabBar)
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
        .sheet(isPresented: $isQuickRecordPresented, onDismiss: openPendingQuickRecord) {
            QuickRecordSheet { action in
                openQuickRecord(action)
            }
            .presentationDetents([.fraction(0.61)])
            .presentationDragIndicator(.visible)
            .presentationCornerRadius(24)
        }
    }

    /// Widget/锁屏深链：xnp://quicklog/feeding|diaper|sleep
    /// 点击即落库（复用首页一键记录的静默路径），并回到首页看到结果与撤销条。
    private func handleQuickLogURL(_ url: URL) {
        guard url.scheme == "xnp", url.host == "quicklog",
              store.hasCompletedOnboarding else { return }
        selectedTab = .home
        homePath = []
        switch url.pathComponents.dropFirst().first {
        case "feeding":
            _ = QuickLogService.logFeedingLikeLast(store: store)
        case "diaper":
            _ = QuickLogService.logDiaper(store: store)
        case "sleep":
            _ = QuickLogService.toggleSleep(store: store)
        default:
            break
        }
    }

    // 「记录」tab 现在是真实页面，不再拦截成弹层；
    // 快速记录浮层保留给首页入口与截图流程。
    private var tabSelection: Binding<AppTab> {
        Binding {
            selectedTab
        } set: { tab in
            selectedTab = tab
        }
    }

    private func openQuickRecord(_ action: QuickRecordAction) {
        let route: AppRoute
        switch action {
        case .feeding: route = .feedingForm
        case .water: route = .waterForm
        case .sleep: route = .sleepForm
        case .diaper: route = .diaperForm
        case .photo: route = .album
        case .growth: route = .growthForm
        case .milestone: route = .milestone
        }

        pendingQuickRecordRoute = route
    }

    private func openPendingQuickRecord() {
        guard let route = pendingQuickRecordRoute else { return }
        pendingQuickRecordRoute = nil
        selectedTab = .home
        homePath.append(route)
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

    private var loadErrorAlertBinding: Binding<Bool> {
        Binding {
            store.loadErrorMessage != nil
        } set: { isPresented in
            if !isPresented {
                store.loadErrorMessage = nil
            }
        }
    }

    private func syncFeedingReminderLiveActivity() {
        QuickLogService.syncLiveActivity(store: store)
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
        case .feedingForm:
            FeedingRecordView(autoPresentEditor: true)
        case .water:
            WaterRecordView()
        case .waterForm:
            WaterRecordView(autoPresentEditor: true)
        case .sleep:
            SleepRecordView()
        case .sleepForm:
            SleepRecordView(autoPresentEditor: true)
        case .diaper:
            DiaperRecordView()
        case .diaperForm:
            DiaperRecordView(autoPresentEditor: true)
        case .milestone:
            MilestoneView()
        case .growth:
            GrowthView(onOpenMonthlyReport: onMonthlyReport)
        case .growthForm:
            GrowthView(onOpenMonthlyReport: onMonthlyReport, autoPresentEditor: true)
        case .vaccine:
            VaccineView()
        case .health:
            HealthObservationView()
        case .monthlyReport:
            MonthlyReportDetailView()
        }
    }

    private static func configureTabBarAppearance() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = AppColors.milkUIColor
        appearance.shadowColor = AppColors.softStrokeUIColor.withAlphaComponent(0.28)

        let itemAppearance = UITabBarItemAppearance()
        itemAppearance.normal.titleTextAttributes = [
            .foregroundColor: AppColors.tabMutedUIColor
        ]
        itemAppearance.selected.titleTextAttributes = [
            .foregroundColor: AppColors.coralUIColor
        ]
        itemAppearance.normal.iconColor = AppColors.tabMutedUIColor
        itemAppearance.selected.iconColor = AppColors.coralUIColor

        appearance.stackedLayoutAppearance = itemAppearance
        appearance.inlineLayoutAppearance = itemAppearance
        appearance.compactInlineLayoutAppearance = itemAppearance

        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance
        UITabBar.appearance().tintColor = AppColors.coralUIColor
        UITabBar.appearance().unselectedItemTintColor = AppColors.tabMutedUIColor
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

    @ObservedObject var cloudSync: CloudSyncController
    @ObservedObject var store: BabyRecordStore
    let onContinueToProfile: () -> Void

    @State private var phoneNumber = "+86"
    @State private var phoneCode = ""
    @State private var isPhoneCodeRequested = false
    @FocusState private var focusedPhoneLoginField: PhoneLoginField?

    var body: some View {
        ScreenScaffold {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    hero

                    if cloudSync.hasSession {
                        signedInCard
                    } else if cloudSync.isServiceConfigured {
                        phoneLoginCard

                        orDivider

                        if cloudSync.isWeChatLoginConfigured {
                            weChatLoginButton
                        }

                        if shouldShowStatusLine {
                            statusLine
                        }

                        termsLine
                            .padding(.top, AppSpacing.small)
                    } else {
                        serviceUnavailableCard
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.top, AppSpacing.roomy)
                .padding(.bottom, AppSpacing.xlarge)
            }
            .onChange(of: cloudSync.hasSession) { _, hasSession in
                if hasSession {
                    onContinueToProfile()
                }
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
        VStack(spacing: AppSpacing.regular) {
            AssetWatercolorImage(name: AppAssets.homeBottleHero, mode: .multiply)
                .frame(width: 108, height: 140)

            VStack(spacing: AppSpacing.small) {
                Text("欢迎来到小奶瓶")
                    .font(AppTypography.title)
                    .foregroundStyle(AppColors.inkGreen)
                    .multilineTextAlignment(.center)
                Text("登录后，宝宝的记录和照片会安全保存在你的账号里")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.inkSoft)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(.bottom, AppSpacing.small)
    }

    /// 替代系统默认描边样式的自绘输入框，与水彩卡片风格统一。
    private func loginField(
        icon: String,
        placeholder: String,
        text: Binding<String>,
        keyboard: UIKeyboardType,
        field: PhoneLoginField
    ) -> some View {
        HStack(spacing: AppSpacing.small) {
            Image(systemName: icon)
                .font(.system(size: 17, weight: .regular))
                .foregroundStyle(AppColors.sage)
                .frame(width: 24)
            TextField(placeholder, text: text)
                .textInputAutocapitalization(.never)
                .keyboardType(keyboard)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(AppColors.ink)
                .focused($focusedPhoneLoginField, equals: field)
        }
        .padding(.horizontal, AppSpacing.regular)
        .frame(height: 52)
        .background(AppColors.cream, in: RoundedRectangle(cornerRadius: AppShapes.cardRadius, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: AppShapes.cardRadius, style: .continuous)
                .stroke(
                    focusedPhoneLoginField == field ? AppColors.coral.opacity(0.55) : AppColors.softStroke.opacity(0.30),
                    lineWidth: 1.5
                )
        }
    }

    private var orDivider: some View {
        HStack(spacing: AppSpacing.regular) {
            Rectangle()
                .fill(AppColors.softStroke.opacity(0.35))
                .frame(height: 1)
            Text("或")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
            Rectangle()
                .fill(AppColors.softStroke.opacity(0.35))
                .frame(height: 1)
        }
        .padding(.horizontal, AppSpacing.small)
    }

    private var termsLine: some View {
        HStack(spacing: 0) {
            Text("登录即代表同意")
                .foregroundStyle(AppColors.inkSoft)
            Link("《用户协议》", destination: URL(string: "https://api.mewpow.com/xiaonaiping/terms")!)
                .foregroundStyle(AppColors.inkGreen)
            Text("与")
                .foregroundStyle(AppColors.inkSoft)
            Link("《隐私政策》", destination: URL(string: "https://api.mewpow.com/xiaonaiping/privacy")!)
                .foregroundStyle(AppColors.inkGreen)
        }
        .font(AppTypography.caption)
        .frame(maxWidth: .infinity)
    }

    private var signedInCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.largeCardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.medium) {
                Label("已登录", systemImage: "checkmark.circle.fill")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)
                Text("确认账号后，继续创建宝宝资料。")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                PrimaryWatercolorButton(title: "继续创建宝宝资料", action: onContinueToProfile)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var phoneLoginCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.regular) {
                loginField(
                    icon: "iphone",
                    placeholder: "手机号",
                    text: $phoneNumber,
                    keyboard: .phonePad,
                    field: .phoneNumber
                )
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

                if isPhoneCodeRequested {
                    loginField(
                        icon: "key",
                        placeholder: "6 位验证码",
                        text: $phoneCode,
                        keyboard: .numberPad,
                        field: .verificationCode
                    )
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

                    HStack {
                        Text("验证码已发送")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                        Spacer()
                        Button("重新获取") {
                            requestPhoneCode()
                        }
                        .font(AppTypography.caption.weight(.semibold))
                        .foregroundStyle(AppColors.inkGreen)
                        .disabled(cloudSync.isWorking || !canRequestPhoneCode)
                    }

                    solidActionButton(
                        title: "验证并登录",
                        enabled: !cloudSync.isWorking && canVerifyPhoneCode
                    ) {
                        focusedPhoneLoginField = nil
                        Task {
                            await cloudSync.verifyPhoneCode(phoneNumber: normalizedPhoneNumber, code: normalizedPhoneCode, store: store)
                        }
                    }
                } else {
                    solidActionButton(
                        title: "获取验证码",
                        enabled: !cloudSync.isWorking && canRequestPhoneCode
                    ) {
                        requestPhoneCode()
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    /// 与成长页“添加测量”一致的珊瑚色实心主按钮。
    private func solidActionButton(title: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title.localizedText)
                .font(AppTypography.bodyLarge.weight(.semibold))
                .foregroundStyle(AppColors.milk)
                .frame(maxWidth: .infinity)
                .frame(height: 52)
                .background(AppColors.coral.opacity(enabled ? 1 : 0.35), in: Capsule())
        }
        .buttonStyle(.plain)
        .disabled(!enabled)
    }

    private func requestPhoneCode() {
        focusedPhoneLoginField = nil
        isPhoneCodeRequested = true
        Task {
            await cloudSync.requestPhoneCode(phoneNumber: normalizedPhoneNumber)
        }
    }

    private var statusLine: some View {
        HStack(alignment: .firstTextBaseline, spacing: AppSpacing.small) {
            Image(systemName: cloudSync.isWorking ? "arrow.triangle.2.circlepath" : "info.circle")
                .font(.system(size: 13, weight: .regular))
                .foregroundStyle(AppColors.inkSoft)
            Text("\(cloudSync.statusTitle.localizedText)：\(cloudSync.statusDetail.localizedText)")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.inkSoft)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity)
        .multilineTextAlignment(.center)
    }

    // 空闲态（未登录/已登录）不显示状态行——好处已在页头说明；
    // 只有进行中或异常状态（发送验证码、等待连接、失败）才值得占一行。
    private var shouldShowStatusLine: Bool {
        cloudSync.isWorking || !["未登录", "已登录"].contains(cloudSync.statusTitle)
    }

    private static let weChatGreen = Color(red: 0.027, green: 0.757, blue: 0.376)

    private var weChatLoginButton: some View {
        Button {
            Task {
                await cloudSync.loginWithWeChat(store: store)
            }
        } label: {
            HStack(spacing: AppSpacing.small) {
                Image(systemName: "message.fill")
                    .font(.system(size: 18, weight: .semibold))
                Text("微信登录")
                    .font(AppTypography.bodyLarge.weight(.semibold))
            }
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .background(Self.weChatGreen, in: Capsule())
        }
        .buttonStyle(.plain)
        .disabled(cloudSync.isWorking || !cloudSync.isWeChatLoginConfigured)
        .opacity(cloudSync.isWorking || !cloudSync.isWeChatLoginConfigured ? 0.5 : 1)
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
        if cloudSync.isNativeWeChatLoginAvailable {
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
        return CloudSyncController.validateE164PhoneNumber(normalizedPhoneNumber) ? nil : "手机号格式不正确，需以 + 开头。"
    }

    private var codeValidationMessage: String? {
        if normalizedPhoneCode.isEmpty {
            return nil
        }
        return CloudSyncController.validateSmsCode(normalizedPhoneCode) ? nil : "验证码格式不正确，需 6 位数字。"
    }
}

private struct WaterRecordView: View {
    var autoPresentEditor = false

    @EnvironmentObject private var store: BabyRecordStore
    @State private var isEditorPresented = false
    @State private var didAutoPresentEditor = false
    @State private var selectedDay = Date()
    @State private var deleteCandidate: WaterRecord?

    private var isViewingToday: Bool {
        Calendar.current.isDateInToday(selectedDay)
    }

    private var dayWaterRecords: [WaterRecord] {
        store.waterRecords(on: selectedDay)
    }

    private var dayWaterAmountML: Int {
        dayWaterRecords.reduce(0) { $0 + $1.amountML }
    }

    var body: some View {
        ScreenScaffold(title: "喝水记录", showBackButton: true) {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.large) {
                    recordWaterButton

                    DaySwitcherBar(selectedDay: $selectedDay)

                    daySummaryCard

                    historyCard
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.vertical, AppSpacing.medium)
                .padding(.bottom, AppSpacing.bottomBarSpace)
            }
        }
        .sheet(isPresented: $isEditorPresented) {
            WaterEditorSheet(defaultDay: isViewingToday ? nil : selectedDay) { record in
                store.upsert(record)
            }
            .presentationDetents([.medium, .large])
        }
        .alert("删除这条喝水记录？", isPresented: Binding {
            deleteCandidate != nil
        } set: { isPresented in
            if !isPresented { deleteCandidate = nil }
        }) {
            Button("删除", role: .destructive) {
                if let deleteCandidate {
                    store.deleteWaterRecord(deleteCandidate)
                }
                deleteCandidate = nil
            }
            Button("取消", role: .cancel) {
                deleteCandidate = nil
            }
        } message: {
            Text("删除后，当日喝水次数和总量会一起更新。")
        }
        .onAppear {
            if autoPresentEditor && !didAutoPresentEditor {
                didAutoPresentEditor = true
                isEditorPresented = true
            }
        }
    }

    /// 顶部主按钮：蓝色实心胶囊 + 白色水滴，是本页唯一的“开始记录”入口。
    private var recordWaterButton: some View {
        Button {
            isEditorPresented = true
        } label: {
            HStack(spacing: AppSpacing.small) {
                Image(systemName: "drop.fill")
                    .font(.system(size: 17, weight: .semibold))
                Text(isViewingToday ? "记录喝水" : "补记这一天")
                    .font(AppTypography.bodyLarge.weight(.semibold))
            }
            .foregroundStyle(AppColors.milk)
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .background(AppColors.blueInk, in: Capsule())
        }
        .buttonStyle(.plain)
        .accessibilityHint(isViewingToday ? "记录一次今天的喝水" : "为当前选中的日期补记喝水")
    }

    /// 今日/当日喝水汇总大卡：水彩水滴插画 + 大号次数与总量。
    private var daySummaryCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) {
            VStack(spacing: AppSpacing.medium) {
                Text(isViewingToday ? "今日喝水" : "当日喝水")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)
                    .frame(maxWidth: .infinity, alignment: .leading)

                AssetWatercolorImage(name: "approvedWaterDrop")
                    .frame(
                        width: dayWaterRecords.isEmpty ? 130 : 90,
                        height: dayWaterRecords.isEmpty ? 130 : 90
                    )

                HStack(alignment: .firstTextBaseline, spacing: AppSpacing.tiny) {
                    Text("\(dayWaterRecords.count)")
                        .font(AppTypography.largeNumber)
                        .foregroundStyle(AppColors.blueInk)
                    Text("次")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.ink)
                    Text("/")
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkSoft)
                        .padding(.horizontal, AppSpacing.tiny)
                    Text("\(dayWaterAmountML)")
                        .font(AppTypography.largeNumber)
                        .foregroundStyle(AppColors.blueInk)
                    Text("ml")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.ink)
                }

                if dayWaterRecords.isEmpty {
                    VStack(spacing: AppSpacing.tiny) {
                        Text(isViewingToday ? "今天还没有喝水记录" : "这一天没有喝水记录")
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.inkGreen)
                        Text("点击上方按钮，记录第一次喝水")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.inkSoft)
                    }
                    .padding(.bottom, AppSpacing.small)
                }
            }
            .frame(maxWidth: .infinity)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(
            AppLocalization.format(
                isViewingToday ? "今日喝水 %d 次，共 %d 毫升" : "当日喝水 %d 次，共 %d 毫升",
                dayWaterRecords.count,
                dayWaterAmountML
            )
        )
    }

    /// 喝水历史卡：空状态给淡色剪贴板占位，有记录时逐行展示时间、水量和删除入口。
    private var historyCard: some View {
        WatercolorCard(tint: AppColors.milk, cornerRadius: AppShapes.largeCardRadius) {
            VStack(alignment: .leading, spacing: AppSpacing.regular) {
                Text("喝水历史")
                    .font(AppTypography.sectionTitle)
                    .foregroundStyle(AppColors.inkGreen)

                if dayWaterRecords.isEmpty {
                    VStack(spacing: AppSpacing.regular) {
                        Image(systemName: "list.clipboard")
                            .font(.system(size: 42, weight: .light))
                            .foregroundStyle(AppColors.inkSoft.opacity(0.55))
                            .padding(.top, AppSpacing.small)
                        Text("暂无记录")
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.inkSoft)
                            .padding(.bottom, AppSpacing.small)
                    }
                    .frame(maxWidth: .infinity)
                } else {
                    VStack(spacing: 0) {
                        ForEach(dayWaterRecords) { record in
                            historyRow(record)
                            if record.id != dayWaterRecords.last?.id {
                                Divider().opacity(0.4)
                            }
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func historyRow(_ record: WaterRecord) -> some View {
        HStack(alignment: .center, spacing: AppSpacing.regular) {
            VStack(alignment: .leading, spacing: AppSpacing.tiny) {
                HStack(spacing: AppSpacing.regular) {
                    Text(BabyRecordStore.timeString(from: record.occurredAt))
                        .font(AppTypography.bodyLarge)
                        .foregroundStyle(AppColors.inkGreen)
                    HStack(spacing: AppSpacing.tiny) {
                        Image(systemName: "drop.fill")
                            .font(.system(size: 14, weight: .regular))
                            .foregroundStyle(AppColors.blueInk.opacity(0.82))
                        Text("\(record.amountML)ml")
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.blueInk)
                    }
                }
                if let note = record.note, !note.isEmpty {
                    Text(note)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.inkSoft)
                        .lineLimit(2)
                }
            }

            Spacer(minLength: 0)
        }
        .padding(.vertical, AppSpacing.tiny)
        .contentShape(Rectangle())
        // 删除入口收进长按菜单，列表不再常驻垃圾桶。
        .contextMenu {
            Button("删除", role: .destructive) {
                deleteCandidate = record
            }
        }
        .accessibilityHint("长按可删除")
    }
}

private struct WaterEditorSheet: View {
    let onSave: (WaterRecord) -> Bool

    @Environment(\.dismiss) private var dismiss
    @State private var occurredAt: Date
    @State private var amountML = 60
    @State private var note = ""
    @State private var isTimePickerExpanded = false
    @State private var errorMessage: String?

    private static let noteLimit = 100
    private static let amountRange = 10...600
    private static let amountStep = 10

    private static let occurredAtFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = .autoupdatingCurrent
        formatter.dateFormat = "yyyy年M月d日 HH:mm"
        return formatter
    }()

    init(defaultDay: Date? = nil, onSave: @escaping (WaterRecord) -> Bool) {
        self.onSave = onSave
        let fallback = defaultDay.flatMap {
            Calendar.current.date(bySettingHour: 12, minute: 0, second: 0, of: $0)
        }
        _occurredAt = State(initialValue: fallback ?? Date())
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: AppSpacing.medium) {
                    timeCard
                    amountCard
                    noteCard

                    if let errorMessage {
                        Text(errorMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.coral)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(AppSpacing.large)
            }
            .background(PaperBackgroundView())
            .safeAreaInset(edge: .bottom, spacing: 0) {
                saveButton
                    .padding(.horizontal, AppSpacing.large)
                    .padding(.vertical, AppSpacing.small)
                    .background(.ultraThinMaterial)
            }
            .navigationTitle("记录喝水")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("保存") { save() }
                        .font(AppTypography.body.weight(.semibold))
                        .foregroundStyle(AppColors.blueInk)
                }
            }
        }
    }

    /// 「时间」行卡：默认收起只显示格式化时间，点击展开内联选择器。
    private var timeCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(spacing: AppSpacing.small) {
                Button {
                    withAnimation(.easeInOut(duration: 0.22)) {
                        isTimePickerExpanded.toggle()
                    }
                } label: {
                    HStack(spacing: AppSpacing.small) {
                        Text("时间")
                            .font(AppTypography.bodyLarge)
                            .foregroundStyle(AppColors.ink)
                        Spacer(minLength: 0)
                        Text(Self.occurredAtFormatter.string(from: occurredAt))
                            .font(AppTypography.readableBody)
                            .foregroundStyle(AppColors.blueInk)
                        Image(systemName: isTimePickerExpanded ? "chevron.up" : "chevron.down")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(AppColors.inkSoft)
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityHint(isTimePickerExpanded ? "收起时间选择器" : "展开时间选择器")

                if isTimePickerExpanded {
                    Divider().opacity(0.4)
                    DatePicker(
                        "喝水时间",
                        selection: $occurredAt,
                        in: ...Date(),
                        displayedComponents: [.date, .hourAndMinute]
                    )
                    .datePickerStyle(.graphical)
                    .labelsHidden()
                    .tint(AppColors.blueInk)
                }
            }
            .frame(maxWidth: .infinity)
        }
    }

    /// 「饮水量」行卡：自绘 − / ＋ 圆形按钮，中间大号数字。
    private var amountCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            HStack(spacing: AppSpacing.small) {
                Text("饮水量")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.ink)

                Spacer(minLength: 0)

                stepButton(systemName: "minus", enabled: amountML > Self.amountRange.lowerBound) {
                    amountML = max(Self.amountRange.lowerBound, amountML - Self.amountStep)
                }
                .accessibilityLabel("减少 10 毫升")

                HStack(alignment: .firstTextBaseline, spacing: 3) {
                    Text("\(amountML)")
                        .font(AppTypography.largeNumber)
                        .foregroundStyle(AppColors.blueInk)
                        .lineLimit(1)
                    Text("ml")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.ink)
                }
                .frame(minWidth: 92)
                .accessibilityLabel(AppLocalization.format("饮水量 %d 毫升", amountML))

                stepButton(systemName: "plus", enabled: amountML < Self.amountRange.upperBound) {
                    amountML = min(Self.amountRange.upperBound, amountML + Self.amountStep)
                }
                .accessibilityLabel("增加 10 毫升")
            }
            .frame(maxWidth: .infinity)
        }
    }

    private func stepButton(systemName: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: 17, weight: .semibold))
                .foregroundStyle(enabled ? AppColors.blueInk : AppColors.inkSoft.opacity(0.35))
                .frame(width: 44, height: 44)
                .background {
                    Circle()
                        .fill(AppColors.mistBlue.opacity(enabled ? 0.6 : 0.3))
                        .overlay {
                            Circle()
                                .stroke(AppColors.blueInk.opacity(enabled ? 0.26 : 0.1), lineWidth: 1)
                        }
                }
        }
        .buttonStyle(.plain)
        .disabled(!enabled)
    }

    /// 「备注（可选）」卡：多行输入 + 右下角字数，超过 100 字自动截断。
    private var noteCard: some View {
        WatercolorCard(tint: AppColors.cream, cornerRadius: AppShapes.cardRadius, padding: AppSpacing.medium) {
            VStack(alignment: .leading, spacing: AppSpacing.small) {
                Text("备注（可选）")
                    .font(AppTypography.bodyLarge)
                    .foregroundStyle(AppColors.ink)
                TextField("如：温水、奶中等", text: $note, axis: .vertical)
                    .lineLimit(2...4)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.ink)
                    .onChange(of: note) { _, newValue in
                        if newValue.count > Self.noteLimit {
                            note = String(newValue.prefix(Self.noteLimit))
                        }
                    }
                Text("\(note.count)/\(Self.noteLimit)")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.inkSoft)
                    .frame(maxWidth: .infinity, alignment: .trailing)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    /// 底部主按钮：与列表页「记录喝水」同款的蓝色实心胶囊。
    private var saveButton: some View {
        Button {
            save()
        } label: {
            Text("保存记录")
                .font(AppTypography.bodyLarge.weight(.semibold))
                .foregroundStyle(AppColors.milk)
                .frame(maxWidth: .infinity)
                .frame(height: 52)
                .background(AppColors.blueInk, in: Capsule())
        }
        .buttonStyle(.plain)
    }

    private func save() {
        let trimmedNote = note.trimmingCharacters(in: .whitespacesAndNewlines)
        let saved = WaterRecord(
            occurredAt: occurredAt,
            amountML: amountML,
            note: trimmedNote.isEmpty ? nil : String(trimmedNote.prefix(Self.noteLimit))
        )
        if onSave(saved) {
            dismiss()
        } else {
            errorMessage = "保存失败，请稍后再试。"
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

private struct WelcomeIntroView: View {
    let onStart: () -> Void

    @State private var page = 0

    private let pages = [
        (
            title: "欢迎来到\n小奶瓶",
            detail: "记录宝宝的每一次成长，\n贴心守护，陪伴每个珍贵瞬间。",
            image: AppAssets.homeBottleHero,
            imageSize: CGSize(width: 232, height: 290)
        ),
        (
            title: "轻轻记一下",
            detail: "喝奶、睡觉、换尿布，\n忙着照顾宝宝时也能快速完成。",
            image: AppAssets.sleepHero,
            imageSize: CGSize(width: 238, height: 260)
        ),
        (
            title: "留住小小成长",
            detail: "照片、纪念日和每一件小事，\n慢慢变成专属于宝宝的小册子。",
            image: AppAssets.plantTimeline,
            imageSize: CGSize(width: 250, height: 270)
        )
    ]

    var body: some View {
        ZStack {
            PaperBackgroundView()

            VStack(spacing: 0) {
                illustration
                    .frame(maxWidth: .infinity)
                    .frame(height: 410)

                Text(pages[page].title)
                    .font(AppTypography.heroTitle)
                    .foregroundStyle(AppColors.blushDeep)
                    .multilineTextAlignment(.center)
                    .lineSpacing(8)
                    .minimumScaleFactor(0.82)
                    .padding(.horizontal, AppSpacing.page)

                Text(pages[page].detail)
                    .font(AppTypography.quietBody)
                    .foregroundStyle(AppColors.inkSoft)
                    .multilineTextAlignment(.center)
                    .lineSpacing(6)
                    .padding(.top, AppSpacing.medium)
                    .padding(.horizontal, AppSpacing.page)

                pageIndicator
                    .padding(.top, AppSpacing.large)

                Spacer(minLength: AppSpacing.large)

                VStack(spacing: AppSpacing.small) {
                    welcomeButton(
                        title: page == pages.count - 1 ? "注册或登录" : "下一步",
                        filled: true,
                        action: page == pages.count - 1 ? onStart : advance
                    )

                    if page == pages.count - 1 {
                        welcomeButton(title: "已有账号，登录", filled: false, action: onStart)
                    }
                }
                .padding(.horizontal, AppSpacing.page)
                .padding(.bottom, AppSpacing.xlarge)
            }
        }
        .accessibilityElement(children: .contain)
    }

    @ViewBuilder
    private var illustration: some View {
        ZStack {
            AssetWatercolorImage(name: AppAssets.cloudBlue, mode: .multiply)
                .frame(width: 104, height: 58)
                .offset(x: -118, y: -132)

            AssetWatercolorImage(name: AppAssets.cloudBlue, mode: .multiply)
                .frame(width: 88, height: 50)
                .scaleEffect(x: -1, y: 1)
                .offset(x: 118, y: -86)

            Capsule()
                .fill(AppColors.butter.opacity(0.62))
                .frame(width: 235, height: 20)
                .blur(radius: 5)
                .offset(y: 120)

            AssetWatercolorImage(name: pages[page].image, mode: .multiply)
                .frame(width: pages[page].imageSize.width, height: pages[page].imageSize.height)
                .offset(y: 8)
                .id(page)
                .transition(.opacity.combined(with: .scale(scale: 0.96)))
        }
        .animation(.easeInOut(duration: 0.28), value: page)
        .padding(.top, AppSpacing.xlarge)
        .accessibilityHidden(true)
    }

    private var pageIndicator: some View {
        HStack(spacing: AppSpacing.small) {
            ForEach(pages.indices, id: \.self) { index in
                Capsule()
                    .fill(index == page ? AppColors.peach : AppColors.paperDeep)
                    .frame(width: index == page ? 22 : 11, height: 7)
            }
        }
        .accessibilityLabel("欢迎引导第 \(page + 1) 页，共 \(pages.count) 页")
    }

    private func welcomeButton(title: String, filled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(AppTypography.bodyLarge)
                .foregroundStyle(filled ? AppColors.milk : AppColors.blueInk)
                .frame(maxWidth: .infinity)
                .frame(height: 54)
                .background {
                    Capsule()
                        .fill(filled ? AppColors.peach.opacity(0.88) : AppColors.milk.opacity(0.56))
                        .overlay {
                            Capsule()
                                .stroke(filled ? AppColors.coral.opacity(0.36) : AppColors.blueInk.opacity(0.72), lineWidth: filled ? 1 : 2)
                        }
                }
        }
        .buttonStyle(.plain)
        .accessibilityHint(
            filled
                ? "先完成注册或登录，再创建宝宝档案"
                : page == pages.count - 1 ? "登录已有账号" : "查看下一页欢迎引导"
        )
    }

    private func advance() {
        withAnimation(.easeInOut(duration: 0.28)) {
            page += 1
        }
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
                Text("登录后，宝宝资料、记录和主动加入 App 的照片原图会安全保存到私有服务中，并可在资料页管理账号。")
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
