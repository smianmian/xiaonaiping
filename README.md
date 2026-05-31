# 小奶瓶 / 宝宝成长记录

这是“小奶瓶 / 宝宝成长记录”的 AppLaunchOS 项目治理层和 iOS 客户端工作区。当前已创建 iOS SwiftUI 工程骨架，第一阶段只允许做高保真 SwiftUI UI 和本地 mock 数据，不允许接入后端、账号、照片权限、CloudKit、第三方 SDK 或真实用户数据。

## 项目定位

小奶瓶是一款面向新手妈妈的 iOS 原生宝宝成长记录工具，覆盖宝宝 0-3 岁阶段，帮助用户低负担记录喂养、睡眠、排便、身高体重、照片、疫苗、纪念日和月度成长报告。

第一版只做 iOS 原生 App。macOS、Android、Web 不进入第一版。

## 第一版目标

让真实新手妈妈愿意每天多次打开，并连续记录 30 天。

## iOS 工程

- 工程路径：`App/iOS/XiaoNaiPing.xcodeproj`
- Scheme：`XiaoNaiPing`
- App 显示名：小奶瓶
- 当前实现：SwiftUI App 骨架、4 个底部 Tab、本地 mock 首页占位、DesignSystem 初始 token
- 当前验证：iOS Simulator generic build 已通过

命令行编译：

```bash
cd /Users/smianmian/Downloads/小奶瓶/App/iOS
xcodebuild -project XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -destination 'generic/platform=iOS Simulator' build
```

## 当前基础设施等级

当前更新为 **Level 2.5：本地优先 + 账号 + 备份恢复 + 原图文件存储**。

- 已确认：本地优先、单人记录、照片可复制进 App 私有空间、需要账号、需要备份恢复、服务器需要存照片原图。
- 已确认首发地区：香港和美国。
- 已确认：疫苗提醒模板覆盖国内 + 香港，崩溃上报进入第一版。
- 已确认：API 服务和对象存储区域必须在发布前按合规策略确认。
- 已确认：崩溃上报使用 Apple 原生渠道。
- 默认后端基线：如果后端被证明第一版必须做，只在公开仓库保留架构原则；具体云厂商、区域、域名、端口、目录和进程名放在私有部署文档。
- 当前禁令：没有后端实现计划、API 设计、数据库/对象存储设计、账号删除方案、隐私审查和发布合规确认前，不允许实现上传、账号或服务器存储。

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
- `Docs/08_Release/APP_STORE_COMPLIANCE_TIMELINE.md`

## 明确不在当前阶段做

- 不安装第三方依赖。
- 不接入照片、健康、账号、云同步或后端接口。
- 不开始 macOS、Android、Web。
- 不创建后台、管理端或数据库。
- 不把设计整图铺成背景冒充页面。
