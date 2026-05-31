import SwiftUI

enum AppRoute: Hashable {
    case feeding
    case sleep
    case diaper
    case milestone
    case growth
    case vaccine
}

struct RootTabView: View {
    @StateObject private var store = BabyRecordStore()
    @State private var selectedTab: AppTab = .home
    @State private var path: [AppRoute] = []
    @State private var isQuickRecordPresented = false

    private var visualTab: AppTab {
        if isQuickRecordPresented { return .record }
        if let last = path.last {
            switch last {
            case .feeding, .sleep, .diaper, .milestone, .growth, .vaccine:
                return .record
            }
        }
        return selectedTab
    }

    var body: some View {
        ZStack(alignment: .bottom) {
            NavigationStack(path: $path) {
                currentTabContent
                    .navigationDestination(for: AppRoute.self) { route in
                        routeView(route)
                    }
            }
            .blur(radius: isQuickRecordPresented ? 4 : 0)
            .animation(.easeOut(duration: 0.18), value: isQuickRecordPresented)

            if isQuickRecordPresented {
                Color.black.opacity(0.18)
                    .ignoresSafeArea()
                    .transition(.opacity)
                    .onTapGesture {
                        isQuickRecordPresented = false
                    }

                QuickRecordSheet { action in
                    handleQuickAction(action)
                } onClose: {
                    isQuickRecordPresented = false
                }
                .transition(.move(edge: .bottom).combined(with: .opacity))
                .padding(.bottom, 98)
            }

            LiquidGlassTabBar(selectedTab: visualTab) { tab in
                handleTabSelection(tab)
            }
        }
        .ignoresSafeArea(.keyboard)
        .environmentObject(store)
    }

    @ViewBuilder
    private var currentTabContent: some View {
        switch selectedTab {
        case .home, .record:
            HomeView(
                onRoute: { path.append($0) },
                onOpenAlbum: {
                    path.removeAll()
                    selectedTab = .album
                }
            )
        case .album:
            AlbumView()
        case .profile:
            ProfileView()
        }
    }

    @ViewBuilder
    private func routeView(_ route: AppRoute) -> some View {
        switch route {
        case .feeding:
            FeedingRecordView()
        case .sleep:
            SleepRecordView()
        case .diaper:
            DiaperRecordView()
        case .milestone:
            MilestoneView()
        case .growth:
            GrowthView()
        case .vaccine:
            VaccineView()
        }
    }

    private func handleTabSelection(_ tab: AppTab) {
        if tab == .record {
            isQuickRecordPresented = true
            return
        }

        isQuickRecordPresented = false
        path.removeAll()
        selectedTab = tab
    }

    private func handleQuickAction(_ action: QuickRecordAction) {
        isQuickRecordPresented = false

        switch action {
        case .feeding:
            path.append(.feeding)
        case .sleep:
            path.append(.sleep)
        case .diaper:
            path.append(.diaper)
        case .photo:
            path.removeAll()
            selectedTab = .album
        case .growth:
            path.append(.growth)
        case .milestone:
            path.append(.milestone)
        }
    }
}

#Preview {
    RootTabView()
}
