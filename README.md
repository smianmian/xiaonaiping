# 小奶瓶 / 宝宝成长记录

这是“小奶瓶 / 宝宝成长记录”的 AppLaunchOS 项目治理层和 iOS 客户端工作区。iOS 客户端已进入功能完整阶段：真实本地持久化（JSON 状态文件 + 备份轮转 + 容错解码）、手机号/微信账号、云端同步与照片原图备份（自有后端）、本地通知与灵动岛提醒、Widget、白噪音、WHO 生长参考曲线、CSV 数据导出。早期“仅 mock 数据”的禁令已随 Level 2.5 基线解除，仅 DEBUG 截图流程仍会用 `-XNPScreenshotData` 注入演示数据。

## 当前发布状态

- iOS 1.3.4（构建 15）已于 2026-08-13 前通过审核并正式发布。
- App Store 已按全球同步上线策略开放，不再处于“准备提交”“等待审核”或“备案阻断”阶段。
- 中国大陆 APP 备案已完成；主体 ICP 备案号为 `粤ICP备2025379333号`。
- 当前阶段为发布后生产巡检、用户反馈和 1.3.5 稳定性维护，详见 `Docs/08_Release/CURRENT_RELEASE_STATUS.md`。

## 项目定位

小奶瓶是一款面向新手妈妈的 iOS 原生宝宝成长记录工具，覆盖宝宝 0-3 岁阶段，帮助用户低负担记录喂养、睡眠、排便、身高体重、照片、疫苗、纪念日和月度成长报告。

第一版只做 iOS 原生 App。macOS、Android、Web 不进入第一版。

## 第一版目标

让真实新手妈妈愿意每天多次打开，并连续记录 30 天。

## iOS 工程

- 工程路径：`App/iOS/XiaoNaiPing.xcodeproj`（XcodeGen 生成，源为 `project.yml`；新增文件后运行 `xcodegen generate`）
- Scheme：`XiaoNaiPing`；测试 target：`XiaoNaiPingTests`
- App 显示名：小奶瓶
- 当前实现：喂养/喝水/睡眠/排便/成长/疫苗/纪念日/相册/月报全量记录，
  首页一键记录 + 撤销，历史日期回看与补录，喝奶自动提醒链 + 灵动岛，
  WHO 百分位生长曲线，白噪音哄睡，CSV 导出，深浅色适配
- 当前验证：模拟器构建 + 单元测试通过（数据安全防回归用例见 `App/iOS/XiaoNaiPingTests/`）

命令行编译：

```bash
cd /Users/smianmian/Downloads/小奶瓶/App/iOS
xcodebuild -project XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' build
```

## 当前基础设施等级

当前更新为 **Level 2.5：本地优先 + 账号 + 自动云端同步 + 原图文件存储**。

- 已确认：本地优先、单人记录、照片可复制进 App 私有空间、需要账号、需要自动云端同步、服务器需要存照片原图。
- 已确认第一版全球同步首发，不采用地区分批上线。
- 已确认：疫苗提醒模板覆盖国内 + 香港，崩溃上报进入第一版。
- 已确认：API 服务和对象存储区域必须在发布前按合规策略确认。
- 已确认：崩溃上报使用 Apple 原生渠道。
- 后端现状：自有 API 服务已实现（手机验证码/微信登录、整包同步 + 服务端版本历史、照片原图上传/下载/删除、账号删除），代码在 `Backend/`；具体云厂商、区域、域名、端口、目录和进程名仍只放私有部署文档。
- 客户端通过构建变量 `XNP_API_BASE_URL` 指向服务；未配置时账号功能降级为"暂未配置"。

## 公开仓库部署边界

如果小奶瓶后端部署到共享服务器，必须与已有服务完全隔离：

- 使用独立部署目录、内部端口、进程名、反向代理站点和 API 域名。
- 禁止覆盖、重启、迁移或复用同机已有服务。
- 禁止在公开仓库写真实服务器地址、面板地址、端口、目录、账号、密钥或对象存储桶名。
- 具体部署参数只允许保存在私有运维文档或服务器环境配置中。

## 数据区域原则

区域就是服务器和照片仓库放在哪个数据中心。公开仓库只记录原则：数据区域必须匹配首发地区、隐私政策、儿童数据保护和 App Store 披露要求；具体云厂商和数据中心在发布前由私有合规/运维文档确认。

## 核心原则

1. 先文档，后设计，后开发。
2. 第一版优先高频记录，不追求大而全。
3. 儿童、照片、健康、家庭数据必须先过隐私审查。
4. 默认本地优先，任何服务器存储必须说明用途、边界、删除机制、地区合规和 App Store 隐私披露。
5. 没有验收标准，不允许标记功能完成。
6. 没有测试与发布证据，不允许上线。
7. 不默认接入第三方 SDK、广告、归因或分析。

## 当前核心文档

- `Docs/01_Product/PRODUCT_SPEC.md`
- `Docs/01_Product/MVP_SCOPE.md`
- `Docs/01_Product/USER_STORIES.md`
- `Docs/01_Product/ACCEPTANCE_CRITERIA.md`
- `Docs/02_Design/UX_FLOW.md`
- `Docs/02_Design/UI_CONTRACT.md`
- `Docs/02_Design/UI_CONTRACT.json`
- `Docs/03_Architecture/DATA_MODEL.md`
- `Docs/03_Architecture/SYNC_RULES.md`
- `Docs/04_BackendInfrastructure/BACKEND_DECISION.md`
- `Docs/04_BackendInfrastructure/CLOUD_HOSTING_GUIDE.md`
- `Docs/06_AnalyticsGrowth/PRIVACY_SAFE_TRACKING.md`
- `Docs/07_PrivacySecurity/PRIVACY_REVIEW.md`
- `Docs/07_PrivacySecurity/SDK_DATA_INVENTORY.md`
- `Docs/07_PrivacySecurity/CHINA_MAINLAND_COMPLIANCE.md`
- `Docs/07_PrivacySecurity/US_HK_COMPLIANCE.md`
- `Docs/08_Release/REGIONAL_LAUNCH_STRATEGY.md`

## 明确不在当前阶段做

- 不接入 HealthKit、Apple Watch。
- 不开始 macOS、Android、Web。
- 不接广告、社区或第三方数据分析 SDK（唯一第三方依赖：微信 OpenSDK，仅登录用途，用户点击登录时才初始化）。
- 不做多看护人共享（需先把整包同步改为逐条增量，见任务队列）。
- 不把设计整图铺成背景冒充页面。
