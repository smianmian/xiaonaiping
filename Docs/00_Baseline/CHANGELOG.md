# Changelog

## 2026-05-29

- 在 `App/iOS` 创建正式 iOS SwiftUI 工程骨架：`XiaoNaiPing.xcodeproj`。
- App 可见显示名保持“小奶瓶”，工程/target 使用 `XiaoNaiPing` 以保证构建稳定。
- 新增第一批客户端目录：`DesignSystem`、`Components`、`Models`、`Mock`、`Views`、`Assets.xcassets`。
- 新增最小可运行 SwiftUI App 入口、4 Tab 骨架和本地 mock 首页占位。
- 当前未接入后端、账号、照片权限、CloudKit、第三方 SDK 或真实用户数据。
- 通过 iOS Simulator generic build 验证：`xcodebuild -project XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' build`。
- 修复 Debug 构建在未配置 Apple Developer Team 时的签名报错：Debug 关闭 code signing，Release/上架签名后续再接正式开发者账号。
- 调整 Debug 签名策略：模拟器关闭签名，真机 Debug 使用 Apple Development Team `TNF9B47CJ2` 自动签名；当前真机仍需要在 Xcode Accounts 中登录对应 Apple ID 以生成 provisioning profile。
- 修复运行后白屏问题：移除 XcodeGen 自动生成的空 `UIApplicationSceneManifest`，SwiftUI `WindowGroup` 现在能正常显示根视图；已在 iPhone 16 Plus Simulator 截图验证首页和 4 个 Tab 可见。
- 移除工程中硬编码的 `DEVELOPMENT_TEAM`，避免 Xcode 在未登录 `TNF9B47CJ2` 时强制报错；真机运行改为在 Xcode `Signing & Capabilities` 中手动选择当前可用 Team。
- 按 `xiaonaiping_app_ui_svg_hybrid_package` / `xiaonaiping_app_ui_psd_layers` 的水彩纸张风格重做第一阶段 SwiftUI UI：保留真实 SwiftUI 组件，素材只作为纸张纹理、手绘图标、插画和 mock 照片资源。
- 新增并接入 10 个高保真 mock 页面：首页、快速记录浮层、喂养、睡眠、排便、相册、纪念日、身高体重、疫苗提醒、我的。
- 修正资源裁切问题：移除错误的整图残片纸张纹理，重新生成干净纸张纹理；从分层包裁切透明插画/图标，避免 UI 背景残字和明显方块底。
- 修正喂养记录汇总卡数字换行问题；修正“我的”页装饰图误带第二个“会员中心”行的问题。
- 通过 iOS Simulator generic build 验证，并在 iPhone 16 Plus Simulator 交互验证：首页、快速记录浮层、喂养页、相册页、我的页可访问；底部 Tab 保持 4 个：首页、相册、记录、我的。

## 2026-05-28

- 初始化“小奶瓶 / 宝宝成长记录”项目治理层。
- 将 Apple 客户端启动模板改为 iOS-only 第一版边界。
- 生成产品、MVP、用户故事、验收、UX、UI、数据、同步和隐私审查文档。
- 合并 AppLaunchOS v2 框架：后端决策、后端部署方案基线、区域上线合规、SDK 清单、隐私安全指标、账号删除和 App Store 合规时间线。
- 确认首发地区为香港和美国，第一版需要账号、备份恢复和服务器照片原图备份。
- 将后端从“是否需要”推进为“需要做最小账号 + 备份恢复 + 原图文件存储方案”；未完成实现计划前仍不允许创建后端、数据库、API 或管理后台。
- 确认疫苗提醒模板范围为国内 + 香港，崩溃上报进入第一版。
- 增加同机部署隔离要求：小奶瓶使用独立目录、端口、进程和 反向代理站点，禁止影响 同机已有服务。
- 明确当前阶段不创建 Xcode 工程、不写 Swift 代码、不安装依赖。
