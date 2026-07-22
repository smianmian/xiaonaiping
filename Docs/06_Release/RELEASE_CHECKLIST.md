# RELEASE_CHECKLIST.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：中国大陆发布清单实现进度更新
- 日期：2026-06-24
- 公司主体：深圳市闪现生活科技有限公司

## 已确认事实

1. 第一版目标是 App Store 可上线的真实 iOS App。
2. 第一版免费验证。
3. 第一版首发地区调整为中国大陆，香港第二批。
4. 第一版需要账号、同步恢复和照片原图云同步。
5. 涉及儿童、照片、成长记录和疫苗提醒，发布前必须完成隐私审查。
6. 疫苗模板覆盖中国大陆 + 香港，崩溃上报进入第一版并使用 Apple 原生渠道。
7. 当前最小后端和 iOS 云同步入口已实现，但未部署到华为云生产环境。

## 合理推断

1. 上线前必须准备隐私政策和用户协议。
2. 审核说明和隐私标签必须清楚说明账号、云同步、照片原图和删除路径。
3. 中国大陆 APP 备案、适用的 ICP 判断、生产后端和 App Store Connect 合规信息是首发阻断项。

## 待我确认的问题

1. App Store 展示名称最终是否为“小奶瓶”。
2. 隐私政策托管地址。
3. 中国大陆 APP 备案负责人和提交时间。
4. 付费 Apple Developer 账号开通时间。
5. Apple 原生崩溃上报脱敏验收方式。
6. 小奶瓶 API 正式域名。
7. 生产 `XNP_API_BASE_URL`。
8. 短信服务商、短信 webhook、签名、模板和发送区域。
9. 微信开放平台 AppID、AppSecret、iOS OpenSDK、URL Scheme / Universal Link。
10. 华为云中国大陆 ECS、正式域名、宝塔 MySQL 独立库和 OBS 资源。

## 不进入第一版的功能

1. 付费、订阅、内购。
2. macOS 上架。
3. 社区和分享审核材料。

## TestFlight

- [ ] 版本号正确。
- [ ] Apple Developer Team 已配置。
- [ ] App Store Distribution 签名归档成功。
- [x] Debug 模拟器构建成功。
- [x] iOS 26.5 Release 模拟器安装启动烟测通过，证据为 `Backend/proof/sim-launch-ios265-20260626.json`。
- [ ] 核心流程可跑通。
- [x] 隐私文案草案完整。
- [x] 审核登录路径草案准备完成：资料 -> 账号与同步 -> 创建账号并同步。
- [x] 生产同步恢复测试环境和生产环境边界清楚，证据见 `Backend/proof/remote-api.json`。
- [x] 华为云中国大陆生产 API 可通过 HTTPS 访问，当前过渡路径为 `https://api.mewpow.com/xiaonaiping`。
- [x] Release `XNP_API_BASE_URL` 指向公网 HTTPS 过渡路径；正式提交前建议切到小奶瓶专属子域名。
- [ ] 宝塔 MySQL migration 已通过；数据库同步和恢复演练待补。
- [ ] 私有 OBS 上传、下载和账号删除联动验证通过。
- [x] 对象存储验证脚本已完成并通过 disk 模式自测；正式 OBS 模式待生产凭证。
- [ ] 手机号登录真实短信验证码可用。
- [ ] 微信登录真实授权可用。
- [x] 手机号登录服务端生产 webhook 路径测试通过。
- [x] 微信登录服务端 code exchange 路径测试通过。
- [x] Release 包已禁止未配置时点击假微信登录；iOS 已接入 WechatOpenSDK 授权桥，真实微信 AppID、URL Scheme、Universal Link 后台绑定和 AppSecret 仍待私有配置。

## App Store

- [x] App 名称草案。
- [x] 副标题草案。
- [x] 描述草案。
- [x] 关键词草案。
- [x] 中国大陆简体中文元数据草案。
- [x] App 内跟随系统语言，并已加入 `zh-Hant-HK` 繁中香港资源。
- [ ] 中国大陆简体中文元数据和截图最终校对。
- [ ] 香港第二批繁中高频文案人工校对。
- [x] 香港区 App Store runbook。
- [x] 中国大陆 App Store runbook。
- [ ] 深圳市闪现生活科技有限公司 Apple Developer / App Store Connect 主体验证。
- [ ] 中国大陆 APP 备案完成并留存备案信息。
- [ ] 大陆域名和联网服务完成适用的 ICP / 公安联网 / 等保判断。
- [x] iPhone 截图候选已归档到 App Store 证据目录。
- [x] 5 张 iPhone 模拟器实现截图证据，包括账号与同步登录面板。
- [x] 截图已重截，避免本地 API、token、真实宝宝照片和 Debug 文案进入候选图。
- [x] 隐私政策草案和 `/privacy` 页面。
- [x] 用户协议草案和 `/terms` 页面。
- [x] Support URL 草案和 `/support` 页面。
- [x] App 隐私标签草案。
- [x] App Store 可填写提交包。
- [x] App Store 隐私标签 JSON 草案。
- [x] App Store Connect 文案材料预检脚本，当前证据为 `Backend/proof/app-store-connect-materials.json`。
- [x] 中国大陆上线执行包。
- [x] ICP / App 备案材料包。
- [x] 测试账号与真机回归清单。
- [x] TestFlight / 真机回归清单预检脚本，当前证据为 `Backend/proof/testflight-regression-plan.json`。
- [x] iOS Release 包体自检文档。
- [x] 微信客户端配置交接文档。
- [x] 2026-06-26 上线闸门复跑报告。
- [x] iOS 26.5 构建预检脚本，当前证据为 `Backend/proof/ios-265-build.json`。
- [x] iOS Privacy Manifest 已加入 app bundle，并由 iOS 发布预检校验。
- [x] SDK 清单草案。
- [x] 审核说明草案。
- [x] 儿童/家庭数据处理说明草案。
- [x] 照片原图云同步说明草案。
- [x] 疫苗模板说明：中国大陆 + 香港，非医疗建议。
- [x] App 内可切换中国大陆 / 香港疫苗模板；安装后不按用户所在地封锁模板。
- [x] 崩溃上报说明草案。
- [x] 账号删除和服务器数据删除说明草案。
- [x] 地区上线策略：中国大陆第一批，香港第二批。
- [x] 生产发布预检脚本。
- [x] 无密钥部署证明采集脚本。
- [x] App Store 资源预检脚本，当前证据为 `Backend/proof/app-store-assets.json`。
- [x] iOS 发布预检脚本，当前证据为 `Backend/proof/ios-release-readiness.json`。
- [x] iOS Release 产物预检脚本，当前证据为 `Backend/proof/ios-app-bundle.json`；已新增 README / Markdown / HTML / env / 本地地址 / debug / API key 标记扫描。
- [x] TestFlight 客户端预检脚本，当前证据为 `Backend/proof/testflight-precheck.json`；Widget extension、Live Activity、本地通知、App Group、共享 payload 和无 HealthKit / 压力评估源码面均通过。
- [x] App Store 人工证据门禁脚本。
- [x] 恢复密钥审核测试账号已创建；密钥保存在本机忽略文件 `.env.xnp-review-account`，redacted 证据已归档。
- [x] 认证服务商预检脚本，当前证据为 `Backend/proof/auth-providers.json`。
- [x] 无密钥后端部署包脚本。
- [ ] 短信服务商人工截图、微信开放平台和 iOS OpenSDK 生产证据。
- [x] 不含宝宝内容的私有运维看板本地实现和权限测试通过。
- [x] 公网 `/xiaonaiping/internal` 已由 Nginx 封禁，服务器本机看板仍可用于 SSH/内网运维。
- [ ] 生产运维看板完成正式 VPN/内网访问和管理员审计验证。

## 新版框架门禁

- [ ] `Docs/08_Release/REGIONAL_LAUNCH_STRATEGY.md` 已确认。
- [ ] `Docs/08_Release/APP_STORE_COMPLIANCE_TIMELINE.md` 已确认。
- [ ] `Docs/08_Release/APP_STORE_METADATA.md` 已确认。
- [ ] `Docs/07_PrivacySecurity/SDK_DATA_INVENTORY.md` 已确认。
- [ ] `Docs/07_PrivacySecurity/PRIVACY_REVIEW.md` 已确认。
- [ ] `Docs/05_BusinessOperations/ACCOUNT_DELETION_PLAN.md` 已确认。

## 交付证据

- [x] 需求对应关系。
- [x] 测试结果。
- [x] 截图计划。
- [x] 隐私审查结果。
- [x] SDK 清单。
- [x] 地区上线结论。
- [x] 账号删除后端测试。
- [x] 云端照片删除后端测试。
- [x] 手机号和微信登录后端 debug 流测试。
- [x] 手机号短信 webhook 和微信 code exchange 后端生产替身测试。
- [x] 无密钥部署证明采集测试，确认不会输出密码、token、AK/SK。
- [x] 认证服务商预检报告，当前结论未就绪，阻断于微信开放平台凭证；短信 webhook 和发送探测已通过，线上 `debug_wechat_*` 探测已被拒绝。
- [x] 代码层诊断/日志脱敏预检报告，当前结论已通过；后端照片对象路径已脱敏为 `/v1/photos/<redacted>`。
- [x] 公开审核页面预检报告，当前结论已通过；隐私政策、用户协议、支持页已改为中国大陆首发、香港第二批和深圳市闪现生活科技有限公司主体。
- [x] Review Notes 预检报告，当前结论已通过；审核说明覆盖免费、无广告、无医疗建议、账号方式、照片原图同步、删除路径、疫苗边界和不依赖 debug code。
- [x] 法务草案预检报告，当前结论已通过；隐私政策和用户协议草案已同步中国大陆首发、香港第二批、深圳市闪现生活科技有限公司主体和恢复密钥/手机号/微信账号方式。
- [x] Universal Links / AASA 预检报告，当前结论已通过；后端 AASA、iOS Associated Domains entitlement、Release 微信 Universal Link 和过渡路径 `/xiaonaiping/wechat/` 已对齐。
- [x] App Store 资源预检报告，当前结论已通过。
- [x] App Store Connect 文案材料预检报告，当前结论已通过；名称、副标题、分类、年龄分级、URL、关键词、隐私标签采集/关联身份/用途/追踪/App flags 和截图文案均通过。
- [x] iOS 发布预检报告，当前结论未就绪，阻断于微信客户端 OpenSDK / Release build settings；`CFBundleURLTypes` 已接入 `XNP_WECHAT_URL_SCHEME` 插槽，`WeChatLoginService` 授权桥已通过预检。
- [x] iOS Release 产物预检报告，当前结论未就绪，阻断于构建产物缺少微信原生 AppID / URL Type。
- [x] Release 包体内容扫描报告，当前不含内部文档、本地地址、debug 文案或 API key 标记。
- [x] 微信客户端配置交接清单，当前明确不能用假 `wx...` 替代真实开放平台配置。
- [x] 微信客户端配置本地干跑已通过，证明真实 `wx...` 到位后可由 build setting 注入 Release 包；干跑值不是提交证据。
- [x] iOS 26.5 Release Simulator 和 iPhoneOS Release 构建已复跑通过；当前阻断仍是微信真实配置、App Store 人工证据、签名/TestFlight 和中国大陆备案。
- [x] iOS 26.5 构建预检报告，当前结论已通过；Release Simulator 和 Release iPhoneOS 产物均为 26.5 SDK。
- [x] iOS 26.5 Release Simulator 安装启动烟测已通过；这不是 TestFlight / 签名真机回归证据。
- [x] TestFlight 客户端预检报告，当前结论已通过；Widget、Live Activity、Dynamic Island、本地通知、App Group、Associated Domains 和共享数据边界均通过。
- [x] TestFlight / 真机回归清单预检报告，当前结论已通过；RD-01 到 RD-24、恢复密钥账号、iOS 26.5 烟测、外部短信/微信待配置边界和证据路径均通过。
- [x] Privacy Manifest 与 App Store 隐私标签草案的当前数据类别对齐，并强制包含 ProductInteraction。
- [x] 生产发布预检报告，当前结论未就绪。
- [x] 后端部署包 manifest。
- [x] App Store archive 检查已执行，当前因未配置 Development Team 失败。
- [x] 代码层崩溃/诊断脱敏测试。
- [ ] TestFlight / App Store Connect 真实崩溃样本脱敏截图或导出。
- [ ] 真机回归证据 `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md`。
- [x] 已知问题。
- [x] 生产回滚方案草案。

## 发布阻断项

- [ ] 未完成 `PRIVACY_REVIEW.md`。
- [ ] 未完成 `TEST_PLAN.md`。
- [ ] 未完成 `REGIONAL_LAUNCH_STRATEGY.md`。
- [x] 没有账号删除机制。当前最小实现已解决，生产验证待补。
- [x] 没有云端照片删除机制。当前最小实现已解决，生产验证待补。
- [ ] App Store 隐私标签与实际行为不一致。
- [ ] 未说明服务器存储和照片原图云同步。
- [ ] `Backend/proof/production-readiness.json` 仍为 `ready: false`。
- [ ] `Backend/proof/auth-providers.json` 仍为 `passed: false`。
- [ ] `Backend/proof/ios-release-readiness.json` 仍为 `passed: false`。
- [ ] `Backend/proof/ios-app-bundle.json` 仍为 `passed: false`。
- [x] 没有华为云远程 API 通过报告。当前 `Backend/proof/remote-api.json` 已通过。
- [x] 没有宝塔 MySQL 生产证据。当前 `Backend/proof/huawei-baota-deploy-20260620.json` 已记录独立宝塔 MySQL。
- [ ] 没有 OBS 策略截图、短信服务商截图和微信登录完整人工证据。
- [ ] 没有中国大陆 APP 备案和 App Store Connect 大陆合规证明。
- [ ] 没有真机回归通过证据。
