# MAINLAND_FILING_MATERIALS.md

> 当前状态：小奶瓶 APP 备案已完成；主体 ICP 备案号为 `粤ICP备2025379333号`。本文其余未勾选项目是备案执行过程记录，不得再解释为“APP 备案未完成”。当前发布状态见 `CURRENT_RELEASE_STATUS.md`。

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 日期：2026-07-04
- 公司主体：深圳市闪现生活科技有限公司
- 用途：中国大陆 App 备案、适用 ICP / 公安联网备案材料准备
- 说明：本文件是提交材料清单，不构成法律意见；最终字段以接入商备案系统、通信管理局和公安联网备案平台要求为准。

## 当前判断

1. 小奶瓶计划在中国大陆 App Store 首发，并通过中国大陆云资源提供联网服务，应按 App 备案路径准备材料。
2. 当前公网过渡路径为 `https://api.mewpow.com/xiaonaiping`，正式提交前建议改为小奶瓶专属子域名，避免多个产品共用路径导致备案和审核材料混乱。
3. App Store Connect 公司主体证据依赖 D-U-N-S 后继续完成 Apple Developer Organization enrollment，并确认 Team ID；见 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md`。
4. 微信开放平台、短信服务商、OBS 策略、生产 proof 和 iOS 26.5 真机/TestFlight 证据必须按同一轮真实操作归档，不用截图模板或占位配置替代。
5. App 备案完成后，需要在 App 显著位置展示备案编号并链接工信部备案系统；拿到备案号后再实现 UI / 静态页展示。
6. 公安联网备案通常在 ICP / App 备案完成并开通服务后继续办理，证据也要归档。

## 拟填信息

| 项目 | 当前填写稿 | 状态 |
|---|---|---|
| 主办单位 | 深圳市闪现生活科技有限公司 | 待营业执照和备案主体确认 |
| App 名称 | 小奶瓶 | 待 App Store Connect 最终名称确认 |
| App 类型 | iOS 原生 App | 已确认 |
| Bundle ID | `com.mewpow.xiaonaiping` | 已在 iOS release gate 通过 |
| SKU | `xiaonaiping-ios-1` | 可用于 App Store Connect |
| 服务内容 | 父母/照护者记录宝宝喂养、睡眠、排便、成长、疫苗提醒和照片时间线 | 待按备案系统选项映射 |
| 是否面向儿童直接使用 | 否，面向父母和照护者 | 已确认 |
| 是否医疗服务 | 否，不提供诊断、治疗、处方或专业疫苗建议 | 待法务复核 |
| 是否新闻/出版/教育/影视/宗教 | 否 | 待法务复核 |
| 首发地区 | 中国大陆 App Store | 已确认 |
| 第二批地区 | 香港 App Store | 已确认 |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` | 当前过渡 URL |
| 用户协议 URL | `https://api.mewpow.com/xiaonaiping/terms` | 当前过渡 URL |
| 支持 URL | `https://api.mewpow.com/xiaonaiping/support` | 当前过渡 URL |
| API URL | `https://api.mewpow.com/xiaonaiping` | 当前过渡 URL，建议换专属子域名 |
| 云服务 | 华为云中国大陆 ECS、宝塔 MySQL、华为云 OBS | 待控制台证据 |
| 生产数据库 | `xiaonaiping_prod` | 已有部署 proof，仍需同步/恢复演练 |
| 对象存储 | 华为云 OBS 私有 bucket / prefix | 待 bucket、加密、生命周期和删除验证证据 |
| 账号方式 | 手机号验证码、微信授权 | 手机短信和微信开放平台仍待最终配置；登录后自动云同步 |

## 需要向公司/后台拿到的材料

1. 营业执照电子版。
2. 法定代表人、App 负责人、网站/网络安全负责人证件材料。
3. 域名证书、域名实名认证信息、DNS 解析截图。
4. 云服务器公网 IP、地域、接入商、实例/备案服务号等信息。
5. App 图标、Bundle ID、版本号、应用简介、应用截图。
6. 隐私政策 URL、用户协议 URL、支持 URL 可访问证明。
7. App Store Connect 公司主体截图。
8. D-U-N-S 后继续完成 Apple Developer Organization enrollment、Team ID、App Store Connect 公司主体绑定证明。
9. 中国大陆只选择可售地区截图。
10. 短信服务商签名、模板、发送成功证明。
11. 微信开放平台移动应用、Bundle ID、URL Scheme、Universal Link 绑定证明。
12. OBS bucket、私有访问、服务端访问、加密、生命周期、删除验证证明。
13. 微信、短信、OBS、生产 proof 和 iOS 26.5 真机/TestFlight 同轮真实证据。
14. 拿到备案号后的备案编号、备案查询页截图和 App 内展示位置截图。
15. 公安联网备案提交/通过证明。

## 证据归档文件名

| 证据 | 文件名 |
|---|---|
| 公司主体 | `Docs/08_Release/AppStoreEvidence/01-company-account.png` |
| 中国大陆可售地区 | `Docs/08_Release/AppStoreEvidence/02-mainland-availability.png` |
| App 备案 / ICP 备案 | `Docs/08_Release/AppStoreEvidence/03-app-filing.pdf` 或 `.png` |
| 隐私标签 | `Docs/08_Release/AppStoreEvidence/04-privacy-label.png` |
| 签名归档 | `Docs/08_Release/AppStoreEvidence/05-signed-archive.png` |
| TestFlight | `Docs/08_Release/AppStoreEvidence/06-testflight.png` |
| 短信服务商 | `Docs/08_Release/AppStoreEvidence/07-sms-provider.png` |
| 微信开放平台 | `Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png` |
| OBS 策略 | `Docs/08_Release/AppStoreEvidence/09-obs-policy.png` |
| 最终截图 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/` |

## 上线前需要改代码的备案项

拿到备案编号后再做，不提前写占位号：

1. 隐私政策、用户协议、支持页底部展示备案编号。
2. App 内“数据与隐私”或“关于小奶瓶”展示备案编号和备案系统链接。
3. App Store Review Notes 补充备案编号。
4. 重新跑 `Backend/scripts/check_public_pages.py`、`Backend/scripts/check_review_notes.py` 和 `Backend/scripts/check_production_readiness.py`。

## 提交顺序

1. 确认专属域名或决定继续使用过渡路径。
2. 按 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md` 完成 D-U-N-S 后的 Apple Developer 公司主体、Team ID、签名归档前置确认。
3. 按本文件和 `REGIONAL_LAUNCH_STRATEGY.md` 补齐微信、短信、对象存储、生产 proof 和签名真机/TestFlight 证据。
4. 在华为云/接入商备案系统提交 App 备案和适用 ICP 信息。
5. 备案通过后补 App 内/网页备案编号展示。
6. 完成公安联网备案并归档证明。
7. 中国大陆门禁与其他目标地区门禁全部通过后，再提交同一轮全球 App Store 审核。

## 备案 / ICP / 公安联网备案当天执行记录模板

复制下面清单到当天的私有执行记录或工单中填写；所有项必须来自同一天同一轮操作。不要把完整证件号、联系人完整电话、验证码、AK/SK、AppSecret、token、服务器密码或真实宝宝照片写进仓库。
旧日期结构化执行包已移除；新的备案执行记录必须从真实后台同轮采集，且不能作为备案通过或提交许可的替代证据。

- [ ] 营业执照电子版、法定代表人、App 负责人、网络安全负责人材料已确认。
- [ ] 域名证书、域名实名认证、DNS 解析、云服务器公网 IP、接入商信息已确认。
- [ ] Apple Developer Organization enrollment / Team ID 和 App Store Connect 公司主体截图已归档。
- [ ] 03-app-filing.pdf 或 03-app-filing.png 已归档。
- [ ] 备案系统提交状态、备案号或适用判断结果可见。
- [ ] 备案通过前不在公开页、App 内或 Review Notes 写占位备案号。
- [ ] 备案通过后再更新 Backend/static/privacy.html、terms.html、support.html。
- [ ] App 内“数据与隐私”或“关于小奶瓶”展示备案编号和工信部备案系统链接。
- [ ] 公安联网备案提交/通过证明已归档。
- [ ] 备案材料已人工核对，且 check_public_pages.py、check_review_notes.py、check_production_readiness.py 已复跑。
- [ ] 不记录完整证件号、联系人完整电话、验证码、AK/SK、AppSecret 或 token。
- [ ] 如果任一项未通过，不提交中国大陆 App Store 审核。
