# LAUNCH_EXECUTION_PACKET.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 日期：2026-06-25
- 公司主体：深圳市闪现生活科技有限公司
- 首发目标：中国大陆 App Store
- 当前结论：上线材料已进入可填写包，但仍不得提交审核，直到生产预检、微信、备案、签名、TestFlight 和真机回归证据全部通过。

## 本轮已完成

1. App Store Connect 文案
   - 填写源文件：`Docs/08_Release/APP_STORE_METADATA.md`
   - 提交包：`Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md`
   - 当前版本覆盖 App 名称、副标题、关键词、宣传文本、描述、新版本说明、审核说明、隐私标签和 URL 草案。

2. 隐私政策和公开页面
   - 隐私政策草案：`Docs/08_Release/PRIVACY_POLICY_DRAFT.md`
   - 用户协议草案：`Docs/08_Release/TERMS_OF_USE_DRAFT.md`
   - 当前公开 URL 草案：`https://api.mewpow.com/xiaonaiping/privacy`、`/terms`、`/support`
   - 公开页面预检证据：`Backend/proof/public-pages.json`

3. ICP / App 备案材料
   - 材料包：`Docs/08_Release/MAINLAND_FILING_MATERIALS.md`
   - 结论：备案材料表已准备；备案编号、接入商受理截图、域名/IP 信息和公安联网备案证据仍需从后台取得。

4. 截图
   - 候选截图目录：`Docs/08_Release/AppStoreEvidence/10-final-screenshots/`
   - 当前截图尺寸：iPhone 17 Pro Max / iPhone 6.9" display，`1320 x 2868`
   - 本轮已重截，避免本地 API、token、真实宝宝照片和 Debug 字样进入候选图；仍需 `UPLOAD_PROVENANCE.json` 证明最终截图来自 iOS 26.5 TestFlight 或 Xcode 签名真机包。
   - 截图资源预检证据：`Backend/proof/app-store-assets.json`

5. 测试账号
   - 已创建恢复密钥测试账号，并写入一份假宝宝记录用于审核恢复验证。
   - 密钥只保存在本机忽略文件：`.env.xnp-review-account`
   - 可提交证据只保留 redacted 版本：`Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json`
   - 手机号测试号和微信测试号仍待真实短信/微信开放平台配置完成后补齐。

6. 真机回归
   - 回归清单：`Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`
   - 当前状态：清单已准备，未执行真机回归；必须在 TestFlight 或签名真机包上执行后才能打勾。

7. 从一根呆毛复用的发布材料结构
   - 已复用审核说明结构、不得提交/不得截图清单、测试路径、包体自检和 release rehearsal 证据格式。
   - 已新增小奶瓶专属包体自检：`Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md`。
   - 已把 README / Markdown / HTML / env / 本地地址 / debug / API key 标记扫描固化进 `Backend/scripts/check_ios_app_bundle.py`。
   - 已修正 `Audio/README.md` 被打入 Release `.app` 的问题。

8. 微信客户端配置
   - 配置交接文档：`Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md`。
   - 当前客户端槽位、URL 回调、Universal Link 回调和按钮禁用态已具备。
   - 仍需微信开放平台真实 `wx...` AppID / URL Scheme 和服务端 AppSecret，不能用占位值替代审核证据。

## 仍然不能提交的原因

1. `Backend/proof/production-readiness.json` 必须为 `ready: true`。
2. `Backend/proof/auth-providers.json` 仍需微信开放平台 AppID/AppSecret 和真机授权证据。
3. `Backend/proof/ios-release-readiness.json` 仍需真实 `XNP_WECHAT_APP_ID` 和 `XNP_WECHAT_URL_SCHEME`。
4. `Backend/proof/app-store-evidence.json` 仍缺公司主体、可售地区、备案、隐私标签、签名归档、TestFlight、短信、微信、OBS 证据和 iOS 26.5 真机回归记录。
5. 中国大陆 App 备案号、适用 ICP / 公安联网备案证据未归档。
6. App Store Distribution Archive 和 TestFlight 未完成。
7. 真机回归未执行；`Docs/08_Release/AppStoreEvidence/12-real-device-regression.md` 尚未生成并勾选。
8. `Backend/proof/ios-app-bundle.json` 虽已通过包体内容扫描，但仍因微信原生配置缺失未通过。
9. `Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md` 中的真实 `wx...` 注入命令还不能执行，因为微信开放平台移动应用值未取得。

## App Store Connect 直接填写稿

| 字段 | 填写 |
|---|---|
| App 名称 | 小奶瓶 |
| 副标题 | 温柔记录宝宝每一天 |
| 主类别 | 生活 |
| 价格 | 免费 |
| 首发地区 | Specific Countries or Regions -> China mainland |
| 关键词 | 宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册 |
| 宣传文本 | 用低负担的方式记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片。 |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` |
| Support URL | `https://api.mewpow.com/xiaonaiping/support` |
| 用户协议 URL | `https://api.mewpow.com/xiaonaiping/terms` |

## 审核说明可粘贴稿

小奶瓶用于父母或照护者记录宝宝成长，不面向儿童直接使用。第一版免费，无 IAP、无广告、无第三方分析 SDK，不提供医疗诊断、治疗建议或专业疫苗建议。产品交互分析只使用自有后端第一方白名单事件，不采集宝宝内容、照片、照片 key、手机号、微信标识、定位、广告标识或设备指纹。

数据默认本地优先保存。用户可以在“资料 -> 账号与同步”中使用恢复密钥、手机号或微信登录并主动同步。同步会上传宝宝记录、照片元数据，以及用户主动加入 App 的照片原图。手机号和微信登录仅用于账号识别和恢复；服务端保存哈希后的账号标识，不采集邮箱。

账号删除路径为：“资料 -> 账号与同步 -> 删除云端账号与同步”。该操作会删除账号、云端 JSON 同步和云端照片原图，本机资料默认保留，用户可以另行清空本地记录或删除宝宝档案。

疫苗模板仅用于记录和提醒，App 内文案不构成医疗建议。

审核测试登录请使用 App Review Information 中提供的恢复密钥测试账号；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充。正式提交包不得提供或依赖 debug code。

## 不得提交或截图

1. 真实宝宝照片、真实手机号、恢复密钥、token、账号 ID、对象存储 key 或 API key。
2. Debug 登录、工程说明、本地 API、`127.0.0.1`、`localhost`、internal dashboard 路径。
3. 医疗诊断、治疗建议、专业疫苗建议或替代医生判断的表述。
4. 付费、订阅、会员、广告、社区、公开分享或 UGC 相关表述。
5. 未配置完成的微信登录成功画面或任何无法在审核包中真实复现的功能。
