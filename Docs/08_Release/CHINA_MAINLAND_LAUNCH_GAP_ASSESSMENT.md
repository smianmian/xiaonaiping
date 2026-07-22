# CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 公司主体：深圳市闪现生活科技有限公司
- 日期：2026-07-04
- 发布决策：中国大陆 App Store 第一批，香港 App Store 第二批
- 说明：本文件是工程与发布差距评估，不构成法律意见；备案、儿童个人信息和 App Store 中国大陆合规要求必须在提交前按最新规则复核

## 当前结论

1. **已有华为云 ECS / 宝塔 MySQL / 公网 HTTPS 过渡路径证据，远端 API proof 也已通过。**
2. **当前仍不得提交中国大陆 App Store。** 以 `Backend/proof/production-readiness.json` 和 `Backend/proof/launch-objective-audit.json` 为准，当前仍是 `ready=false`。
3. **材料包不是提交证据。** `Backend/proof/provider-evidence-materials.json`、`Backend/proof/mainland-filing-materials.json`、App Store Connect 文案和备案材料 gate 已通过，但只能证明填写口径和采集清单完整。
4. **真实阻断项仍在外部证据和真机链路。** 当前红项包括 `deploymentProofCurrent`、`storageBackendProofCurrent`、`wechatLoginProviderConfigured`、`ios265PhysicalDeviceAvailabilityReady`、`appStoreManualEvidenceReady`。
5. **提交前必须按 `XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md` 刷新 `20260704T-current` proof。** 不能用旧 proof、模拟器或模板文档替代当天真实部署、OBS、微信、短信、App Store 人工证据和 iOS 26.5 真机/TestFlight 证据。
6. App 已保留中国大陆 / 香港疫苗模板切换；这解决的是 App 内功能选择，不等于完成中国大陆上架和联网服务合规。

## 证据

| 检查项 | 仓库现状 | 结论 |
|---|---|---|
| 后端 API | `Backend/api/` 已实现账号、手机号、微信、同步、照片和删除接口 | 本地最小实现已存在 |
| 华为云部署 | `Backend/proof/huawei-baota-deploy-20260625T080412Z.json` 记录独立 ECS 目录、systemd 服务、宝塔 MySQL 和公网 HTTPS 过渡路径；提交前需刷新 `Backend/proof/huawei-baota-deploy-20260704T-current.json` | 已有部署证据；`deploymentProofCurrent` 仍需当天 current proof |
| 远端 API | `Backend/proof/remote-api.json` 当前通过；提交前需刷新 `Backend/proof/remote-api-20260704T-current.json` | API 最小闭环有证据；提交前仍需同轮 current proof |
| iOS Release API | Release `XNP_API_BASE_URL` 已配置为 `https://api.mewpow.com/xiaonaiping` | Release 包可连接当前公网 HTTPS 过渡路径 |
| 数据库 | 已支持本地 SQLite 和 `XNP_DATABASE_BACKEND=mysql`；远端迁移已在 `xiaonaiping_prod` 执行 | 宝塔 MySQL 已连通；仍需同步/恢复演练证据 |
| 对象存储 | 支持 `huawei_obs`；`Backend/proof/storage-backend-20260625T080039Z.json` 已通过；提交前需刷新 `Backend/proof/storage-backend-20260704T-current.json` | `storageBackendProofCurrent` 仍需当天 current proof 和 `09-obs-policy` 人工证据 |
| 手机号登录 | 支持 webhook 服务商接口，材料包要求 `07-sms-provider.png` 和真实实发验证 | 真实短信服务商截图和实发截图未归档 |
| 微信登录 | 支持微信 code exchange，iOS 已接入 WechatOpenSDK 授权桥和 Universal Link / AASA 基础配置 | 微信开放平台凭据、真实 `wx...` URL Scheme 和开放平台后台绑定未完成 |
| 数据看板 | `/internal/dashboard` + 管理员令牌保护的 `/internal/metrics` | 公网 `/xiaonaiping/internal` 已由 Nginx 封禁；服务器本机路径仍可用于 SSH/内网运维，后续补正式 VPN/内网访问审计 |
| 供应商/备案材料 | `Backend/proof/provider-evidence-materials.json`、`Backend/proof/mainland-filing-materials.json` 均通过 | 只证明材料清单完整，不替代真实 `07-sms-provider`、`08-wechat-open-platform`、`09-obs-policy`、`03-app-filing` 等人工证据 |
| 生产预检 | `Backend/proof/production-readiness.json` 为 `ready: false` | 不能作为上架生产证据；以 `failedRequiredChecks` 追踪剩余阻断项 |
| 上线目标总审计 | `Backend/proof/launch-objective-audit.json` 为 `ready: false` | iOS 26.5 真机可用性、微信配置、TestFlight/真机回归、App Store 人工证据和 production readiness 仍阻断 |

## 与“一根呆毛 / 情绪 App”的差异

| 能力 | 一根呆毛 | 小奶瓶 |
|---|---|---|
| 华为云发布 | 有固定部署脚本、SSH 发布、迁移和 PM2 重载流程 | 已有独立 ECS 目录、systemd 服务、宝塔 MySQL、Nginx 过渡路径和远程验证证据；仍需专属子域名、OBS、短信和微信 |
| 生产数据库 | MySQL 连接池和连续 migration | 已补 MySQL 连接与迁移，真实宝塔 MySQL 待验证 |
| 数据分析 | 有分析事件表、分析 API 和管理端统计 | 无分析采集、无管理端 |
| 数据看板 | 有管理后台，并有 Metabase 私有部署方案 | 已有聚合运维看板，无用户内容后台 |
| 运维证据 | 有部署域名、迁移流程和 `Backend/proof/remote-api.json` | 提交前仍需同一天 `20260704T-current` 部署、远端 API、storage、auth provider 和 production readiness proof |

可以参考一根呆毛的部署、迁移、只读看板和验证流程，但不能直接复制它的社区、用户标签、内容查询和完整运营后台。小奶瓶包含宝宝照片、成长记录、疫苗与家庭数据，管理端默认不得查看用户内容。

## 中国大陆首发 P0 阻断项

### 公司与商店

- [ ] Apple Developer / App Store Connect 账号使用深圳市闪现生活科技有限公司主体，并完成所需企业资料验证。
- [ ] App Store Connect 选择中国大陆可售地区，补齐中国大陆适用的合规信息与证明，并归档 `02-mainland-availability.png`。
- [ ] 确认 App 名称、Bundle ID、主体名称、隐私政策、用户协议和备案主体一致。
- [ ] 使用简体中文主元数据和大陆审核截图；`zh-Hant-HK` 继续保留给香港用户。

### 备案与合规

- [ ] 以公司主体启动 APP 备案，并核对域名、云资源、接入商和应用信息，归档 `03-app-filing.pdf` 或 `.png`。
- [ ] 若 API/网页使用中国大陆服务器和域名，完成适用的 ICP 备案及其他联网服务备案判断。
- [ ] 对儿童个人信息、敏感个人信息、照片原图、手机号、微信标识、跨设备同步分别完成告知和同意设计。
- [ ] 隐私政策、App Privacy Label、SDK 清单和实际网络行为保持一致，并归档 `04-privacy-label.png`。
- [ ] 疫苗模板只作为记录和提醒，正式发布前复核来源、更新时间和非医疗建议文案。

### 生产基础设施

- [x] 在华为云中国大陆区域建立独立生产环境：ECS、HTTPS/Nginx 过渡路径、独立进程和日志。
- [ ] 将生产数据库定为华为云 ECS 上宝塔管理的独立 MySQL，并建立 migration、同步、恢复演练和最小权限账号。当前已完成独立 MySQL 与 migration，同步/恢复演练证据待补。
- [ ] 使用私有 OBS 保存照片原图，配置服务端访问、加密、生命周期、同步和删除验证，并归档 `09-obs-policy.png`。
- [ ] 配置正式 API 域名，并写入 Release `XNP_API_BASE_URL`。当前 Release 已写入公网 HTTPS 过渡路径，专属 API 子域名待补。
- [ ] 使用私密配置保存密钥，禁止把 AK/SK、AppSecret、短信密钥写入仓库。
- [ ] 配置监控、告警、日志脱敏、容量阈值和回滚流程。

### 登录

- [ ] 接入可在中国大陆稳定使用的短信服务，完成签名、模板、频控、验证码过期、反滥用验证、真实实发验证、`Backend/proof/auth-providers.json` 和 `07-sms-provider.png`。
- [ ] 完成微信开放平台移动应用配置、真实 `wx...` URL Scheme、开放平台 Universal Link 绑定、真机登录、`Backend/proof/auth-providers.json` / `ios-release-readiness.json` 和 `08-wechat-open-platform.png`。
- [ ] iOS 发布构建使用外部环境变量注入微信配置：`XNP_WECHAT_APP_ID`、`XNP_WECHAT_URL_SCHEME`、`XNP_WECHAT_UNIVERSAL_LINK`。严禁将真实微信密钥写入源码仓库。
- [ ] 验证手机号、微信和恢复密钥能落到同一账号身份模型，并覆盖账号删除。

## 最小数据看板

第一版已实现**私有运维看板**，不是用户运营后台。当前展示：

- 注册账号数、日活账号数和 App 版本分布。
- 同步成功率、恢复成功率、照片上传成功率和删除任务结果。
- 手机验证码发送/验证失败率、微信登录失败率。
- API 可用率、延迟、5xx、存储容量和数据库同步状态。
- 账号删除数量、删除耗时和超过 SLA 的任务数。

看板禁止展示或检索：

- 宝宝姓名、生日、头像或照片。
- 喂养、睡眠、排便、成长、疫苗记录和备注正文。
- OBS 对象地址、恢复密钥、手机号明文、微信 token。

当前入口为 `/internal/dashboard`，数据接口为 `/internal/metrics`，必须配置 `XNP_ADMIN_TOKEN`。公网过渡路径已封禁 `/xiaonaiping/internal`，生产后续仍需补正式公司内部网络/VPN访问和管理员审计，不直接照搬一根呆毛的 Basic Auth。

## 推荐执行顺序

1. 确认 Apple 公司账号、域名和华为云中国大陆区域资源。
2. 启动 APP 备案，同时建立独立 ECS、宝塔 MySQL、OBS 和正式 HTTPS API。
3. 在真实宝塔 MySQL 执行现有 migration，完成生产数据同步和恢复演练。
4. 接通真实短信与微信登录，完成真机验证。
5. 将现有私有运维看板接入生产内网/VPN，并补充云监控告警。
6. 按 `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md` 刷新 `20260704T-current` 部署、远端 API、storage、auth provider 和 production readiness proof。
7. 跑通 iOS 26.5 TestFlight / 签名真机回归、Archive、App Store Connect 人工证据和中国大陆备案证据。
8. 所有 P0 证据通过后再提交中国大陆 App Store；香港作为第二批复用 `zh-Hant-HK` 资源。
