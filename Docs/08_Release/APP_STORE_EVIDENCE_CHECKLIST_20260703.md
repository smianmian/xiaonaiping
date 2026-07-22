# 小奶瓶 App Store 人工证据清单

日期：2026-07-03

用途：把中国大陆 App Store 提交前必须补齐的人工截图、录屏、导出文件和真机回归证据集中到一个可执行清单。这个文件不是提交通过证明；只有 `Backend/scripts/check_app_store_evidence.py` 全绿后，人工证据才算齐。

## 当前已有证据

| 证据 | 文件 |
| --- | --- |
| App Store Connect 填表稿 | `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260703.md` |
| App Store 提交包 | `Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md` |
| 隐私标签 JSON | `Docs/08_Release/APP_STORE_PRIVACY_LABEL.json` |
| 截图计划 | `Docs/08_Release/SCREENSHOT_PLAN.md` |
| 人工证据采集指南 | `Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md` |
| 人工证据目录说明 | `Docs/08_Release/AppStoreEvidence/README.md` |
| 最终截图候选 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/` |
| 审核测试账号脱敏证据 | `Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json` |
| 真机回归模板 | `Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md` |
| 短信服务商采集模板 | `Docs/08_Release/AppStoreEvidence/_templates/sms-provider-evidence.template.json` |
| 微信开放平台采集模板 | `Docs/08_Release/AppStoreEvidence/_templates/wechat-open-platform-evidence.template.json` |
| OBS 策略采集模板 | `Docs/08_Release/AppStoreEvidence/_templates/obs-policy-evidence.template.json` |
| 备案/隐私/年龄分级采集模板 | `Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json` |
| App Store 截图资产 proof | `Backend/proof/app-store-assets.json` |
| App Store Connect 素材 proof | `Backend/proof/app-store-connect-materials.json` |
| App Store 人工证据 proof | `Backend/proof/app-store-evidence.json` |
| App Store 人工证据同轮执行包 | `Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260703.json` |

## 同轮人工证据索引模板

复制下面表格到当天的私有执行记录或工单中填写；所有证据必须来自同一天同一轮采集。不要把 Apple ID 邮箱、测试员邮箱、完整手机号、验证码、恢复密钥、token、AK/SK、AppSecret、证书私钥、对象 key、完整证件号或真实宝宝照片写进仓库。

| 项目 | 填写 |
| --- | --- |
| App 版本 | 待真实 TestFlight / Archive 后填写 |
| Build 号 | 待真实 TestFlight / Archive 后填写 |
| 安装方式 | `TestFlight` 或 `Xcode 签名真机包` |
| 证据范围 | 01-company-account.png 到 09-obs-policy.png、`08b-wechat-universal-link-aasa.png` 和 17-age-rating-result、`10-final-screenshots/`、`11-test-account-redacted.json`、`12-real-device-regression.md` |
| 同轮一致性 | App Store Connect 选中的 build 与 TestFlight / 12-real-device-regression.md 一致 |
| 文件体积 | 每个文件已确认单个文件不低于 10KB，最终截图和 RD 证据不使用空白图 |
| 最终截图来源 | `10-final-screenshots/UPLOAD_PROVENANCE.json` 已证明 `final-app-store-upload`、`iPhone 6.9` 槽位、iOS 26.5、TestFlight 或 Xcode 签名真机包最终截图和五张上传顺序图一致 |
| 脱敏 | 每个文件已脱敏，不含完整手机号、恢复密钥、token、AK/SK、AppSecret、验证码、证件号或真实宝宝照片 |
| 复跑 | `check_app_store_evidence.py --allow-incomplete`、`check_app_store_connect_materials.py`、`check_production_readiness.py` 已复跑 |
| 提交判断 | `production-readiness.json` 为 ready=true 后才进入 App Store Connect 提交审核 |

同轮执行包 `Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260703.json` 只用于现场逐项核对；它不是证据，不替代 `01-...`、`ASC-...`、`10-final-screenshots/UPLOAD_PROVENANCE.json` 或 `12-real-device-regression.md`，也不能把 `canSubmit` 改成 true。

## 仍需补齐的人工证据

所有文件放在 `Docs/08_Release/AppStoreEvidence/`。不要把桌面、下载目录、微信临时目录或聊天截图直接当成最终证据。

| 文件名建议 | 证明什么 | 截图/证据要求 | 当前状态 |
| --- | --- | --- | --- |
| `01-company-account.png` | App Store Connect 主体为深圳市闪现生活科技有限公司，且 D-U-N-S 后 Apple Developer Organization / Team ID 已确认 | 可见团队/法律主体、Apple Developer Organization、Team ID；遮邮箱、电话、付款信息、D-U-N-S 编码完整值 | 未完成 |
| `02-mainland-availability.png` | 首发只选择 China mainland / 中国大陆 | 可见 App 名称和可售地区选择状态；不要展示无关账号信息 | 未完成 |
| `03-app-filing.pdf` 或 `03-app-filing.png` | 中国大陆 APP 备案或适用判断 | 截图前参考 `_templates/mainland-filing-privacy-evidence.template.json`；可见 App 名称、主体、备案号或提交状态；遮证件细节、联系人完整电话 | 未完成 |
| `04-privacy-label.png` | App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写 | 截图前参考 `_templates/mainland-filing-privacy-evidence.template.json`；可见采集类别、用途、未 Tracking；遮账号邮箱 | 未完成 |
| `17-age-rating-result.png` 或 `17-age-rating-result.pdf` | App Store Connect 年龄分级结果已按答案表完成 | 截图前参考 `_templates/mainland-filing-privacy-evidence.template.json`；可见年龄分级结果、关键问答项，并与 `APP_STORE_AGE_RATING_ANSWERS_20260703.md` 一致；遮 Apple ID 邮箱、电话、付款信息 | 未完成 |
| `05-signed-archive.png` | App Store Distribution Archive 成功 | 可见 `com.mewpow.xiaonaiping`、版本、build、archive/upload 成功状态 | 未完成 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试 | 可见版本、build、处理完成或可测试状态；遮测试员邮箱 | 未完成 |
| `07-sms-provider.png` | 真实短信服务商、签名、模板和发送成功 | 截图前参考 `_templates/sms-provider-evidence.template.json`；可见服务商、签名、模板 ID/名称、模板审核状态、发送区域、发送成功；隐藏 AK/SK、验证码、完整手机号 | 未完成 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置完成 | 截图前参考 `_templates/wechat-open-platform-evidence.template.json`；可见 AppID、Bundle ID、URL Scheme、Universal Link、审核/配置状态；隐藏 AppSecret、管理员账号、完整手机号、验证码、token | 未完成 |
| `08b-wechat-universal-link-aasa.png` 或 `.pdf` | 微信 Universal Link / AASA / Associated Domains / Team ID 同轮核对 | 截图前参考 `_templates/wechat-open-platform-evidence.template.json`；可见 AASA endpoint、Team ID、Bundle ID、`applinks:api.mewpow.com`、`/xiaonaiping/wechat/`、`XNPWeChatUniversalLink`；隐藏 Apple ID 邮箱、完整手机号、AppSecret、验证码、token | 未完成 |
| `09-obs-policy.png` | 华为 OBS bucket 私有访问、加密、生命周期和删除策略 | 截图前参考 `_templates/obs-policy-evidence.template.json`；可见 bucket/prefix、区域、私有策略、加密/生命周期/删除状态；隐藏 AK/SK 和完整对象 key | 未完成 |
| `10-final-screenshots/01-home-iphone16pro.png` | App Store 上传顺序图 1 | 不能使用真实宝宝照片、完整手机号、debug 文案；必须为 iPhone 6.9" display 可上传尺寸 | 已有候选，缺最终上传 provenance |
| `10-final-screenshots/02-record-iphone16pro.png` | App Store 上传顺序图 2 | 记录页截图不写医疗承诺或喂养建议；必须为 iPhone 6.9" display 可上传尺寸 | 已有候选，缺最终上传 provenance |
| `10-final-screenshots/03-growth-iphone16pro.png` | App Store 上传顺序图 3 | 成长趋势只表达记录回看，不表达诊断或健康结论；必须为 iPhone 6.9" display 可上传尺寸 | 已有候选，缺最终上传 provenance |
| `10-final-screenshots/04-profile-iphone16pro.png` | App Store 上传顺序图 4 | 不展示恢复密钥、token、手机号明文；必须为 iPhone 6.9" display 可上传尺寸 | 已有候选，缺最终上传 provenance |
| `10-final-screenshots/05-profile-sync-iphone16pro.png` | App Store 上传顺序图 5 | 账号和同步路径只展示功能入口，不展示密钥；必须为 iPhone 6.9" display 可上传尺寸 | 已有候选，缺最终上传 provenance |
| `10-final-screenshots/UPLOAD_PROVENANCE.json` | 最终截图来源 | 必须写明 `final-app-store-upload`、`iPhone 6.9`、iOS 26.5、`TestFlight` 或 `Xcode 签名真机包最终截图`，并列出五张 finalFiles | 未完成 |
| `11-test-account-redacted.json` | App Review 恢复密钥测试账号脱敏证据 | 不能保存恢复密钥、验证码、token、完整手机号 | 已有 |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或 Xcode 签名真机包回归 | 复制模板后填写；RD-01 到 RD-24 必须全部通过并指向真实证据文件，单个 RD 文件不低于 10KB | 未完成 |
| `AppleDeveloper/13-organization-team-id.png` | D-U-N-S 后 Apple Developer 组织页确认主体、Membership 和 Team ID | 可见深圳市闪现生活科技有限公司、Team ID、Membership 状态；遮邮箱、电话、付款信息、D-U-N-S 编码完整值 | 未完成 |
| `AppleDeveloper/14-bundle-id-capabilities.png` | Bundle ID / Identifier 页确认 `com.mewpow.xiaonaiping`、App Groups、Associated Domains | 可见 Bundle ID、当前 Team、`group.com.mewpow.xiaonaiping`、`applinks:api.mewpow.com`；遮无关 App 和人员信息 | 未完成 |
| `AppleDeveloper/15-distribution-certificate-profile.png` | App Store Distribution 证书 / Profile 可用于 Archive | 可见类型、Bundle ID、Team ID、有效状态；遮证书私钥、下载链接、个人邮箱 | 未完成 |
| `AppleDeveloper/16-account-roles-access.png` | 当前 Apple ID 有证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限 | 可见当前 Apple ID 所属团队、角色列表、Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限、提交审核权限；遮 Apple ID 邮箱、联系人完整电话、付款信息、无关成员 | 未完成 |

## 真机回归必须覆盖

1. iOS 只能是 `26.5` 或 `iOS 26.5`。
2. 安装方式只能是 `TestFlight` 或 `Xcode 签名真机包`。
3. `RD-01` 到 `RD-24` 必须全部存在，状态列必须全部是“通过”。
4. 每个 RD 用例都必须填写证据文件路径，路径必须留在 `Docs/08_Release/AppStoreEvidence/` 内。
5. 证据文件后缀只能是 `.png`、`.jpg`、`.jpeg`、`.mp4`、`.mov` 或 `.pdf`，并且文件真实存在，单个文件不低于 10KB。
6. 环境字段必须填写：设备、iOS、安装方式、App 版本、Build、网络、证据截图/录屏。
7. 视觉结论必须填写：灵动岛紧凑态结论、灵动岛展开态结论、锁屏通知栈结论、锁屏小组件结论、桌面小组件结论。
8. RD-10、RD-13、RD-14、RD-15、RD-18、RD-22、RD-23、RD-24 不能复用总览图或同一份泛证据。
9. RD-10 恢复密钥登录必须使用独立证据文件：`RealDevice/RD-10-recovery-login.png`。
10. RD-13 手机号登录必须使用独立证据文件：`RealDevice/RD-13-phone-login.png`。
11. RD-14 微信登录必须使用独立证据文件：`RealDevice/RD-14-wechat-login.png`。
12. RD-15 账号删除必须使用独立证据文件：`RealDevice/RD-15-account-delete.png`。
13. RD-17 通知权限允许和拒绝必须使用独立证据文件：`RealDevice/RD-17-notification-allowed.png`、`RealDevice/RD-17-notification-denied.png`。
14. RD-22 灵动岛紧凑态和展开态必须使用独立证据文件：`RealDevice/RD-22-dynamic-island-compact.png`、`RealDevice/RD-22-dynamic-island-expanded.png`。
15. RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须使用独立证据文件：`RealDevice/RD-23-lock-screen-notification-stack.png`、`RealDevice/RD-23-lock-screen-widget-summary.png`、`RealDevice/RD-23-home-widget-summary.png`。
16. RD-10 路径必须体现 recovery 或恢复。
17. RD-13 路径必须体现 phone、sms、手机号或验证码。
18. RD-14 路径必须体现 wechat 或微信。
19. RD-15 路径必须体现 account / delete 或账号 / 删除。
20. RD-17 路径必须体现 notification、permission、通知或权限。
21. RD-18 路径必须同时体现 watch 和 mirror / notification。
22. RD-22 路径必须体现 live-activity、dynamic-island、island 或灵动岛。
23. RD-22 路径必须体现 switch、toggle、开关、compact 或 expanded。
24. RD-23 代表路径必须体现 widget / 小组件或 lock-screen / 锁屏。
25. 不能保留“待测”“待填”“待真实”“TODO”“TBD”“失败”“跳过”等状态。

## RD 用例列表

| ID | 必须证明 |
| --- | --- |
| `RD-01` | 冷启动进入首页 |
| `RD-02` | 创建宝宝档案 |
| `RD-03` | 记录喂养 |
| `RD-04` | 记录睡眠 |
| `RD-05` | 记录排便 |
| `RD-06` | 成长记录 |
| `RD-07` | 疫苗模板切换 |
| `RD-08` | 相册权限拒绝 |
| `RD-09` | 相册权限允许 |
| `RD-10` | 恢复密钥账号登录 |
| `RD-11` | 云同步 |
| `RD-12` | 云恢复 |
| `RD-13` | 手机号登录 |
| `RD-14` | 微信登录 |
| `RD-15` | 删除云端账号与同步 |
| `RD-16` | 断网保存 |
| `RD-17` | 通知权限 |
| `RD-18` | Apple Watch 镜像通知 |
| `RD-19` | 隐私政策/用户协议/支持 URL |
| `RD-20` | 崩溃/日志脱敏 |
| `RD-21` | Release 包体自检 |
| `RD-22` | 灵动岛喝奶提醒开关 |
| `RD-23` | 锁屏/桌面小组件 |
| `RD-24` | 审核边界文案 |

## 灵动岛 / 小组件 / Apple Watch 边界

1. 灵动岛和 Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔。
2. 灵动岛紧凑态头像和进度环不能右移压到岛中心。
3. 灵动岛展开态文字和数字不能贴边或被吞。
4. 锁屏通知栈上下相邻通知不能遮挡提醒卡片。
5. 锁屏/桌面小组件只读展示本机今日摘要。
6. 桌面小组件内容不能裁剪，不能展示隐私照片。
7. 灵动岛紧凑态、灵动岛展开态、锁屏通知栈、锁屏小组件和桌面小组件必须分别保留独立截图或录屏。
8. 通知权限允许和通知权限拒绝必须分别保留独立截图或录屏。
9. Apple Watch 只作为系统镜像通知，不在 App Store 文案中承诺 Watch App。
10. 状态展示只反映用户主动记录的数据。
11. 不生成健康建议、压力提醒、喂养建议或医疗判断。
12. 不接入 HealthKit、传感器、医院系统或第三方健康数据源。
13. 不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议。

## 遮挡与脱敏规则

- 手机号只保留前三后四。
- AppSecret、AK/SK、验证码、恢复密钥、Bearer token、session token、AI Key、数据库连接串必须全遮。
- 微信 AppID 可以展示，微信 AppSecret 必须隐藏。
- 不使用真实宝宝照片、真实家庭资料、未授权头像或聊天内容。
- 不展示对象存储完整 key、internal dashboard、debug code、`127.0.0.1`、localhost 或服务器私有路径。

## 当前不可替代项

以下不能用模拟器日志、模板文档或截图候选替代：

1. App Store Distribution Archive。
2. TestFlight 构建处理完成。
3. 真实短信服务商签名、模板和实发截图。
4. 微信开放平台移动应用配置。
5. 真机恢复密钥登录。
6. 真机手机号登录。
7. 真机微信登录。
8. 真机账号删除。
9. 通知权限弹窗。
10. iOS 26.5 TestFlight 或 Xcode 签名真机包回归。
11. 灵动岛、锁屏和桌面小组件视觉裁剪证据。
12. OBS 私有访问、加密、生命周期和删除策略截图。
13. `10-final-screenshots/UPLOAD_PROVENANCE.json`，证明最终截图不是 Debug simulator 候选，而是 iOS 26.5 TestFlight 或 Xcode 签名真机包的 iPhone 6.9" display 最终上传截图。

## 采集后必跑

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-07-03 --output Backend/proof/app-store-evidence-20260703T-current.json
python3 Backend/scripts/check_app_store_connect_materials.py --allow-incomplete --output Backend/proof/app-store-connect-materials.json
Backend/scripts/run_launch_readiness.sh \
  --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
  --app-path /private/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260703.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260703-device-current.log \
  --base-url https://api.mewpow.com/xiaonaiping \
  --live-check
```

如果 `app-store-evidence-20260703T-current.json` 或同步后的 `app-store-evidence.json` 仍有 `missingEvidence`，不能提交 App Store。
