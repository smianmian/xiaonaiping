import SwiftUI

@main
struct XiaoNaiPingApp: App {
    var body: some Scene {
        WindowGroup {
            RootTabView()
                .onOpenURL { url in
                    _ = WeChatLoginService.shared.handleOpenURL(url)
                }
                .onContinueUserActivity(NSUserActivityTypeBrowsingWeb) { userActivity in
                    _ = WeChatLoginService.shared.handleUniversalLink(userActivity)
                }
        }
    }
}
