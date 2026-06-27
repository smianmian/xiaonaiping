#if !canImport(WechatOpenSDK)
import AuthenticationServices
import Foundation
import UIKit

public class BaseReq {}

public class BaseResp {
    public var errCode: Int32 = 0

    public init() {}
}

public class SendAuthReq: BaseReq {
    public var scope: String?
    public var state: String?

    public override init() {
        super.init()
    }
}

public class SendAuthResp: BaseResp {
    public var code: String?
    public var state: String?

    public override init() {
        super.init()
    }
}

public protocol WXApiDelegate: AnyObject {
    func onReq(_ req: BaseReq)
    func onResp(_ resp: BaseResp)
}

@MainActor
private final class WeChatOpenSDKWebAuthCoordinator: NSObject, ASWebAuthenticationPresentationContextProviding {
    private struct ActiveAuth {
        weak var delegate: WXApiDelegate?
        let expectedState: String
        let completion: (Bool) -> Void
    }

    static let shared = WeChatOpenSDKWebAuthCoordinator()

    private var activeAuth: ActiveAuth?
    private var webSession: ASWebAuthenticationSession?

    private var callbackScheme: String? {
        guard let raw = (Bundle.main.object(forInfoDictionaryKey: "XNPWeChatURLScheme") as? String)?
            .trimmingCharacters(in: .whitespacesAndNewlines),
              !raw.isEmpty,
              !raw.contains("$("),
              raw.hasPrefix("wx") else {
            return nil
        }
        return raw
    }

    func register(appID: String, universalLink: String) -> Bool {
        appID.hasPrefix("wx")
        && !appID.contains("$(")
        && universalLink.hasPrefix("https://")
        && !universalLink.contains("$(")
    }

    func startSendAuthRequest(
        _ request: SendAuthReq,
        delegate: WXApiDelegate
    ) -> Bool {
        guard activeAuth == nil else {
            return false
        }

        guard let callbackScheme = callbackScheme?.trimmingCharacters(in: .whitespacesAndNewlines),
              !callbackScheme.isEmpty else {
            return false
        }

        let state = request.state?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        guard !state.isEmpty else {
            return false
        }

        let redirect = URL(string: "\(callbackScheme)://wechat/auth")
        guard let redirect else {
            return false
        }

        var components = URLComponents(string: "https://open.weixin.qq.com/connect/oauth2/authorize")
        let appID = (Bundle.main.object(forInfoDictionaryKey: "XNPWeChatAppID") as? String ?? "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard appID.hasPrefix("wx"), !appID.contains("$(") else {
            return false
        }

        components?.queryItems = [
            URLQueryItem(name: "appid", value: appID),
            URLQueryItem(name: "redirect_uri", value: redirect.absoluteString),
            URLQueryItem(name: "response_type", value: "code"),
            URLQueryItem(name: "scope", value: request.scope ?? "snsapi_userinfo"),
            URLQueryItem(name: "state", value: state),
        ]
        guard let url = components?.url else {
            return false
        }

        let session = ASWebAuthenticationSession(url: url, callbackURLScheme: callbackScheme) { [weak self] callbackURL, error in
            Task { @MainActor in
                guard let self else { return }
                if let callbackURL {
                    self.finishWithCallbackURL(callbackURL)
                    return
                }

                if let nsError = error as NSError?, nsError.domain == ASWebAuthenticationSessionError.errorDomain {
                    let canceled = nsError.code == ASWebAuthenticationSessionError.canceledLogin.rawValue
                    self.finish(error: canceled ? -2 : -1)
                } else {
                    self.finish(error: -1)
                }
            }
        }

        session.presentationContextProvider = self
        webSession = session
        activeAuth = ActiveAuth(delegate: delegate, expectedState: state) { [weak self] success in
            if !success {
                self?.finish(error: -1)
            }
        }

        guard session.start() else {
            activeAuth = nil
            webSession = nil
            return false
        }
        return true
    }

    func handleOpen(_ url: URL, delegate: WXApiDelegate) -> Bool {
        guard let callbackScheme = callbackScheme?.trimmingCharacters(in: .whitespacesAndNewlines),
              !callbackScheme.isEmpty,
              let scheme = url.scheme,
              scheme.hasPrefix(callbackScheme) else {
            return false
        }

        WXApiDelegateWrapper.shared.delegate = delegate
        finishWithCallbackURL(url)
        return true
    }

    func handleUniversalLink(_ userActivity: NSUserActivity, delegate: WXApiDelegate) -> Bool {
        guard let url = userActivity.webpageURL else {
            return false
        }
        return handleOpen(url, delegate: delegate)
    }

    private func finishWithCallbackURL(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            return
        }

        let queryItems = components.queryItems ?? []
        let values: [String: String] = Dictionary(uniqueKeysWithValues: queryItems.compactMap { item in
            guard let value = item.value else { return nil }
            return (item.name, value)
        })

        let code = values["code"]
        let state = values["state"]

        if values["errmsg"] != nil {
            finish(error: -4)
            return
        }

        if let activeAuth {
            guard state == activeAuth.expectedState else {
                finish(error: -3, state: state)
                return
            }
            finish(code: code, state: state)
            return
        }

        activeAuth = nil
        webSession?.cancel()
        webSession = nil
    }

    private func finish(code: String?, state: String?) {
        guard let activeAuth else {
            return
        }

        let response = SendAuthResp()
        response.code = code
        response.state = state
        response.errCode = code == nil ? -6 : 0

        let delegate = activeAuth.delegate
        activeAuth.completion(true)
        self.activeAuth = nil
        webSession?.cancel()
        webSession = nil

        delegate?.onResp(response)
    }

    private func finish(error: Int32, state: String? = nil) {
        guard let activeAuth else {
            return
        }

        let response = SendAuthResp()
        response.errCode = error
        response.state = state
        let delegate = activeAuth.delegate
        activeAuth.completion(true)
        self.activeAuth = nil
        webSession?.cancel()
        webSession = nil

        delegate?.onResp(response)
    }

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        let scenes = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first { $0.activationState == .foregroundActive }

        return scenes?.windows.first(where: { $0.isKeyWindow }) ?? UIWindow()
    }
}

public enum WXApi {
    @MainActor
    public static func setDelegate(_ delegate: WXApiDelegate?) {
        WXApiDelegateWrapper.shared.delegate = delegate
    }

    @MainActor
    public static func registerApp(_ appID: String, universalLink: String) -> Bool {
        WeChatOpenSDKWebAuthCoordinator.shared.register(appID: appID, universalLink: universalLink)
    }

    @MainActor
    public static func sendReq(_ req: BaseReq, completion: ((Bool) -> Void)? = nil) {
        guard let request = req as? SendAuthReq,
              let delegate = WXApiDelegateWrapper.shared.delegate else {
            completion?(false)
            return
        }

        let sent = WeChatOpenSDKWebAuthCoordinator.shared.startSendAuthRequest(request, delegate: delegate)
        if !sent {
            completion?(false)
            return
        }
        completion?(true)
    }

    @MainActor
    public static func handleOpen(_ url: URL, delegate: WXApiDelegate) -> Bool {
        WXApiDelegateWrapper.shared.delegate = delegate
        return WeChatOpenSDKWebAuthCoordinator.shared.handleOpen(url, delegate: delegate)
    }

    @MainActor
    public static func handleOpenUniversalLink(_ userActivity: NSUserActivity, delegate: WXApiDelegate) -> Bool {
        WXApiDelegateWrapper.shared.delegate = delegate
        return WeChatOpenSDKWebAuthCoordinator.shared.handleUniversalLink(userActivity, delegate: delegate)
    }
}

private final class WXApiDelegateWrapper {
    static let shared = WXApiDelegateWrapper()
    weak var delegate: WXApiDelegate?
}
#endif
