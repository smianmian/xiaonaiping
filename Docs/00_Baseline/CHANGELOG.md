# Changelog

## 2026-08-11

- 首发范围统一为全球同步上线，不再采用中国大陆、香港、美国或其他地区的分批顺序。
- 各目标地区适用的备案、商店、隐私和儿童数据要求改为同一轮发布门禁。

## 2026-06-24

- 新增喝奶闹钟边界：用户手动设置一个本机下一次喂养提醒，使用 iOS 本地通知；第一版不根据月龄、上一顿时间或奶量自动推荐喂养间隔，不上传服务器。
- 新增第一轮体验升级：安静育儿模式默认开启；喂养支持日期 + 分钟级时间输入和距上次喂养展示；睡眠进行中与已结束睡眠统计分开展示；新增 App Group 今日快照和只读桌面/锁屏小组件。
- 喝奶闹钟升级为“下一次提醒 + 可选固定间隔继续提醒”，支持 2/2.5/3/3.5/4 小时节奏；本地通知会预排多次提醒，Widget 与灵动岛/锁屏 Live Activity 展示下一次喝奶和提醒节奏。

## 2026-06-19

- 确认中国大陆生产目标改为华为云 ECS + 宝塔 MySQL 独立库，不与情绪 App / 一根呆毛共享数据库、目录、端口、进程、对象桶或反向代理站点。
- 新增 `Backend/deploy/huawei-baota-production.md` 生产部署交接文档，并把生产配置样例切到 `xiaonaiping_prod` / `xiaonaiping_app`。
- 生产预检新增小奶瓶命名空间和情绪 App 命名空间拦截，避免误连共享服务资源。

## 2026-06-18

- 公司主体确认为深圳市闪现生活科技有限公司。
- 当时的地区发布顺序已由 2026-08-11 全球同步首发决策覆盖。
- 完成现状审计：本地最小后端和 SQLite 已存在，但华为云生产、生产 MySQL、私有 OBS、正式短信/微信登录、远程 API 证据和最小运维看板仍未完成。
- 同步当时的产品、架构、隐私、部署和发布门禁；旧地区差距产物现已退役。
- 后端新增 SQLite/MySQL 双数据库支持、MySQL schema 迁移脚本和生产数据库门禁。
- 新增 `/internal/dashboard` 与受 `XNP_ADMIN_TOKEN` 保护的聚合运维指标，不展示宝宝内容。
- 后端 17 项测试通过；生产预检继续阻断未配置的真实 MySQL、OBS、短信、微信、域名和远程验证。

## 2026-05-29

- 在 `App/iOS` 创建正式 iOS SwiftUI 工程骨架：`XiaoNaiPing.xcodeproj`。
- App 可见显示名保持“小奶瓶”，工程/target 使用 `XiaoNaiPing` 以保证构建稳定。
- 新增第一批客户端目录：`DesignSystem`、`Components`、`Models`、`Mock`、`Views`、`Assets.xcassets`。
- 新增最小可运行 SwiftUI App 入口、4 Tab 骨架和本地 mock 首页占位。
- 当前已接入最小第一方后端、手机号验证码/微信登录、登录后自动云同步、照片原图云同步和账号删除；未接入 CloudKit、第三方 SDK 或真实生产用户数据。
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
- 第一版确认需要账号、同步恢复和服务器照片原图同步；旧地区顺序已由全球同步首发决策覆盖。
- 将后端从“是否需要”推进为“需要做最小账号 + 同步恢复 + 原图文件存储方案”；后续已按该边界实现最小后端，不包含管理后台或 BI。
- 确认疫苗提醒模板范围为国内 + 香港，崩溃上报进入第一版。
- 增加同机部署隔离要求：小奶瓶使用独立目录、端口、进程和 反向代理站点，禁止影响 同机已有服务。
- 明确当前阶段不创建 Xcode 工程、不写 Swift 代码、不安装依赖。

## 2026-06-14

- 新增 `Backend/api/server.py` 最小第一方后端，覆盖手机号验证码/微信登录、自动云同步、照片原图上传/下载/删除和账号删除。
- iOS 资料页接入账号与同步操作，会话存入 Keychain，Debug 默认连接本机 API，Release 需要配置真实 `XNP_API_BASE_URL`。
- 新增隐私政策草案、用户协议草案、App Store 元数据草案和当前发布证据包。
- 当前仍不允许正式提交 App Store：缺真实 HTTPS API 域名、生产部署、App Store Connect、截图、公开隐私政策 URL、生产删除 SLA 和崩溃脱敏证据。
