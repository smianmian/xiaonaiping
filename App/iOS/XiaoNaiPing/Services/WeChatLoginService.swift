import Foundation
#if canImport(UIKit)
import UIKit
#endif
#if canImport(WechatOpenSDK)
import WechatOpenSDK
#endif

// Fallback implementations are provided in WeChatOpenSDKShim.swift when official module is unavailable.
enum WeChatLoginError: LocalizedError {
    case notConfigured
    case alreadyInProgress
    case registrationFailed
    case sendFailed
    case cancelled
    case denied
    case stateMismatch
    case missingAuthorizationCode
    case unsupportedResponse
    case failed(Int32)

    var errorDescription: String? {
        switch self {
        case .notConfigured:
            return "微信登录未启用：请先完成微信 OpenSDK、AppID、URL Scheme、Universal Link 和服务端凭证配置。"
        case .alreadyInProgress:
            return "已有一次微信授权正在进行，请稍后再试。"
        case .registrationFailed:
            return "微信 OpenSDK 注册失败，请检查 AppID 和 Universal Link。"
        case .sendFailed:
            return "未能拉起微信授权，请确认设备已安装微信并完成开放平台配置。"
        case .cancelled:
            return "已取消微信授权。"
        case .denied:
            return "微信授权被拒绝。"
        case .stateMismatch:
            return "微信授权校验失败，请重新登录。"
        case .missingAuthorizationCode:
            return "微信未返回授权 code，请重新登录。"
        case .unsupportedResponse:
            return "收到不支持的微信回调。"
        case .failed(let code):
            return "微信授权失败：错误码 \(code)。"
        }
    }
}

@MainActor
final class WeChatLoginService: NSObject {
    static let shared = WeChatLoginService()

    private var continuation: CheckedContinuation<String, Error>?
    private var expectedState: String?

    func requestAuthorizationCode() async throws -> String {
        guard CloudBackupConfiguration.isWeChatLoginConfigured else {
            throw WeChatLoginError.notConfigured
        }

        guard let appID = CloudBackupConfiguration.weChatAppID,
              let universalLink = CloudBackupConfiguration.weChatUniversalLink else {
            throw WeChatLoginError.notConfigured
        }
        guard continuation == nil else {
            throw WeChatLoginError.alreadyInProgress
        }
        guard WXApi.registerApp(appID, universalLink: universalLink.absoluteString) else {
            throw WeChatLoginError.registrationFailed
        }

        let state = UUID().uuidString.replacingOccurrences(of: "-", with: "")
        expectedState = state

        return try await withTaskCancellationHandler(
            operation: {
                try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<String, Error>) in
                    self.continuation = continuation
                    let request = SendAuthReq()
                    request.scope = "snsapi_userinfo"
                    request.state = state
                    #if canImport(WechatOpenSDK)
                    guard let viewController = Self.activeViewController() else {
                        self.finish(.failure(WeChatLoginError.sendFailed))
                        return
                    }
                    WXApi.sendAuthReq(request, viewController: viewController, delegate: self) { [weak self] sent in
                        guard !sent else { return }
                        Task { @MainActor in
                            self?.finish(.failure(WeChatLoginError.sendFailed))
                        }
                    }
                    #else
                    WXApi.setDelegate(self)
                    WXApi.sendReq(request) { [weak self] sent in
                        guard !sent else { return }
                        Task { @MainActor in
                            self?.finish(.failure(WeChatLoginError.sendFailed))
                        }
                    }
                    #endif
                }
            },
            onCancel: {
                Task { @MainActor in
                    self.finish(.failure(CancellationError()))
                }
            }
        )
    }

    func handleOpenURL(_ url: URL) -> Bool {
        WXApi.handleOpen(url, delegate: self)
    }

    func handleUniversalLink(_ userActivity: NSUserActivity) -> Bool {
        WXApi.handleOpenUniversalLink(userActivity, delegate: self)
    }

    #if canImport(WechatOpenSDK)
    private static func activeViewController() -> UIViewController? {
        let scene = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first { $0.activationState == .foregroundActive }
        let root = scene?.windows.first { $0.isKeyWindow }?.rootViewController
        return topViewController(from: root)
    }

    private static func topViewController(from viewController: UIViewController?) -> UIViewController? {
        if let navigationController = viewController as? UINavigationController {
            return topViewController(from: navigationController.visibleViewController)
        }
        if let tabBarController = viewController as? UITabBarController {
            return topViewController(from: tabBarController.selectedViewController)
        }
        if let presented = viewController?.presentedViewController {
            return topViewController(from: presented)
        }
        return viewController
    }
    #endif

    private func finish(_ result: Result<String, Error>) {
        guard let continuation else { return }
        self.continuation = nil
        expectedState = nil

        switch result {
        case .success(let code):
            continuation.resume(returning: code)
        case .failure(let error):
            continuation.resume(throwing: error)
        }
    }

    private func handle(response: BaseResp) {
        guard let response = response as? SendAuthResp else {
            finish(.failure(WeChatLoginError.unsupportedResponse))
            return
        }

        switch response.errCode {
        case 0:
            break
        case -2:
            finish(.failure(WeChatLoginError.cancelled))
            return
        case -4:
            finish(.failure(WeChatLoginError.denied))
            return
        default:
            finish(.failure(WeChatLoginError.failed(response.errCode)))
            return
        }

        guard response.state == expectedState else {
            finish(.failure(WeChatLoginError.stateMismatch))
            return
        }
        guard let code = response.code?.trimmingCharacters(in: .whitespacesAndNewlines), !code.isEmpty else {
            finish(.failure(WeChatLoginError.missingAuthorizationCode))
            return
        }
        finish(.success(code))
    }
}

#if !canImport(WechatOpenSDK)
extension WeChatLoginService: WXApiDelegate {
    nonisolated func onReq(_ req: BaseReq) {}

    nonisolated func onResp(_ resp: BaseResp) {
        Task { @MainActor in
            WeChatLoginService.shared.handle(response: resp)
        }
    }
}
#endif

#if canImport(WechatOpenSDK)
extension WeChatLoginService: WXApiDelegate {
    nonisolated func onReq(_ req: BaseReq) {}

    nonisolated func onResp(_ resp: BaseResp) {
        Task { @MainActor in
            WeChatLoginService.shared.handle(response: resp)
        }
    }
}
#endif
