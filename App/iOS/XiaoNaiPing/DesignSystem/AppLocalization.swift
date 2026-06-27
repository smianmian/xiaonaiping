import Foundation

enum AppLocalization {
    static func text(_ key: String) -> String {
        NSLocalizedString(key, bundle: .main, value: key, comment: "")
    }

    static func format(_ key: String, _ arguments: CVarArg...) -> String {
        let format = text(key)
        return String(format: format, locale: Locale.autoupdatingCurrent, arguments: arguments)
    }
}

extension String {
    var localizedText: String {
        AppLocalization.text(self)
    }
}
