# App Store Evidence Capture Guide

## 使用规则

本目录只归档真实提交证据。现场先按 `Docs/08_Release/APP_STORE_MANUAL_EVIDENCE_PACKET_20260704.json` 核对同轮目标文件、脱敏、iOS 26.5 和复跑命令；这个执行包不是证据，也不是提交许可。占位、待办、模板或聊天记录不要命名成 `01-...` 到 `09-...` 或 `17-...`，否则容易混入发布包。模板只能放在 `_templates/` 或使用 `.template.*` 文件名，真实证据名留给截图、导出 PDF 或脱敏 JSON。`check_app_store_evidence.py` 对 `01-...` 到 `09-...` 和 `17-...` 只接受 `.png`、`.jpg`、`.jpeg`、`.pdf`、`.json` 作为人工证据，普通人工证据和 RD 真机证据文件都必须至少 10KB，截图建议统一使用 `.png`。真机回归使用 `12-real-device-regression.md`，且必须勾选核心真机项；RD-01 到 RD-24 的状态列必须全部等于“通过”，不能保留“待测”“失败”“跳过”或其他状态。

## 通用脱敏

保留能证明审核状态的字段，遮掉无关个人或密钥信息：

1. 遮邮箱、手机号、证件号、付款资料、验证码、恢复密钥、session token、AK/SK、AppSecret。
2. 保留 App 名称、Bundle ID、版本号、构建号、状态、地区、URL、服务商名称和必要配置项。
3. 不使用真实宝宝照片、真实家庭资料、完整手机号或未授权头像。
4. 不保存后台入口、internal dashboard、服务器私有路径或对象存储完整 key。

## 采集清单

| 文件 | 必须能证明 | 保留字段 | 必须遮挡 |
|---|---|---|---|
| `01-company-account.png` | App Store Connect 账号主体为深圳市闪现生活科技有限公司，且 D-U-N-S 后 Apple Developer Organization / Team ID 已确认 | 团队/法律主体名称、账号页标题、Apple Developer Organization、Team ID | 邮箱、电话、付款信息、D-U-N-S 编码完整值 |
| `02-mainland-availability.png` | 首发只选 China mainland / 中国大陆 | App 名称、可售地区选择状态 | 无关账号信息 |
| `03-app-filing.pdf` 或 `.png` | App 备案/ICP/适用判断进度或结果；采集前可参考 `_templates/mainland-filing-privacy-evidence.template.json` | App 名称、主体、备案号或提交状态 | 遮个人证件细节、证件号、联系人完整电话 |
| `04-privacy-label.png` 或 `.pdf` | App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写；采集前可参考 `_templates/mainland-filing-privacy-evidence.template.json` | 已采集类别、未追踪、用途 | 账号邮箱 |
| `17-age-rating-result.png` 或 `.pdf` | App Store Connect 年龄分级结果已按答案表完成；采集前可参考 `_templates/mainland-filing-privacy-evidence.template.json` | 年龄分级结果、关键问答项、与 `APP_STORE_AGE_RATING_ANSWERS_20260704.md` 一致 | Apple ID 邮箱、电话、付款信息 |
| `05-signed-archive.png` | App Store Distribution archive 成功；采集前可参考 `_templates/apple-developer-team-signing-evidence.template.json` | Bundle ID、版本、build、archive success / uploaded status | Apple ID 邮箱 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试；采集前可参考 `_templates/apple-developer-team-signing-evidence.template.json` | Build 号、版本、处理状态、测试状态 | 测试员邮箱 |
| `07-sms-provider.png` | 真实短信签名、账号登录/验证验证码模板和发送成功；模板不含营销、不含医疗、不含育儿建议；采集前可参考 `_templates/sms-provider-evidence.template.json` | 服务商、签名、模板 ID/名称、模板审核状态、发送区域、发送成功状态 | AccessKey、Secret、完整手机号、验证码 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置完成；采集前可参考 `_templates/wechat-open-platform-evidence.template.json` | AppID、Bundle ID、URL Scheme、Universal Link、审核/配置状态 | AppSecret、管理员账号、完整手机号、验证码、token |
| `08b-wechat-universal-link-aasa.png` 或 `.pdf` | AASA、Team ID、Associated Domains、微信 Universal Link 同轮核对 | AASA endpoint、Team ID、Bundle ID、`applinks:api.mewpow.com`、`/xiaonaiping/wechat/`、`XNPWeChatUniversalLink` | Apple ID 邮箱、完整手机号、AppSecret、验证码、token |
| `09-obs-policy.png` | OBS bucket 私有访问、加密、生命周期、删除验证；采集前可参考 `_templates/obs-policy-evidence.template.json` | bucket/prefix、区域、加密/生命周期/删除策略状态 | AK/SK、完整对象 key |
| `10-final-screenshots/*.png` + `10-final-screenshots/UPLOAD_PROVENANCE.json` | 最终 App Store 截图 | 必须包含 `01-home-iphone16pro.png` 到 `05-profile-sync-iphone16pro.png` 这五张上传顺序图；截图必须为 iPhone 6.9" display 可上传尺寸；先复制 `10-final-screenshots/UPLOAD_PROVENANCE.template.json`，填入同一 iOS 26.5 TestFlight 或 Xcode 签名真机包的版本、build、设备和安装来源，再另存为 `UPLOAD_PROVENANCE.json`；最终 JSON 必须写明 `evidenceType: final-app-store-upload`、iOS 26.5、安装来源 `TestFlight` 或 `Xcode 签名真机包`，并列出五张 finalFiles | 真实宝宝照片、手机号、debug 文案、候选或模拟器最终截图声明 |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归结论 | 设备、iOS 26.5、build、安装方式 `TestFlight` 或 `Xcode 签名真机包`、证据截图/录屏路径、灵动岛紧凑态/展开态、锁屏通知栈、锁屏/桌面小组件视觉结论、RD-01 到 RD-24 全部通过、喂养顺延滚轮只提供不顺延和 +5、+10、+15、+20、+25、+30 分钟、下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排、账号/通知/灵动岛/小组件/审核边界核心项 `- [x]` 勾选 | 恢复密钥、验证码、完整手机号、token、debug code |
| `AppleDeveloper/13-organization-team-id.png` | Apple Developer 组织页确认主体、Membership 和 Team ID；采集前可参考 `_templates/apple-developer-team-signing-evidence.template.json` | 深圳市闪现生活科技有限公司、Team ID、Membership 状态 | Apple ID 邮箱、联系人电话、付款信息、D-U-N-S 编码完整值 |
| `AppleDeveloper/14-bundle-id-capabilities.png` | Bundle ID / Identifier 页确认 `com.mewpow.xiaonaiping`、App Groups、Associated Domains；采集前可参考 `_templates/apple-developer-team-signing-evidence.template.json` | Bundle ID、Team、`group.com.mewpow.xiaonaiping.shared`、`applinks:api.mewpow.com` | 无关 App、人员信息 |
| `AppleDeveloper/15-distribution-certificate-profile.png` | App Store Distribution 证书 / Profile 可用于 Archive；采集前可参考 `_templates/apple-developer-team-signing-evidence.template.json` | 类型、Bundle ID、Team ID、有效状态 | 证书私钥、下载链接、个人邮箱 |
| `AppleDeveloper/16-account-roles-access.png` | 当前 Apple ID 有证书/Profile、App 管理、构建上传、TestFlight 管理和提交审核权限；采集前可参考 `_templates/apple-developer-team-signing-evidence.template.json` | 当前 Apple ID 所属团队、角色列表、Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限、提交审核权限 | Apple ID 邮箱、联系人完整电话、付款信息、无关成员 |

`12-real-device-regression.md` 中每个真机回归项的证据截图/录屏路径必须填写，路径必须指向 `.png`、`.jpg`、`.jpeg`、`.mp4`、`.mov` 或 `.pdf` 文件，不能只写目录。每个路径都必须是 `Docs/08_Release/AppStoreEvidence/` 内真实存在且不低于 10KB 的文件；不要填写桌面、下载目录、微信临时目录或其他绝对路径。建议把真机截图和录屏放在 `Docs/08_Release/AppStoreEvidence/RealDevice/` 后再填写相对路径，例如 `RealDevice/RD-01-cold-launch.png`。

灵动岛和锁屏证据要按视觉边界拍：紧凑态要能看出图标和进度环没有右移压到岛中心；展开态要能看出文字、数字和边缘留白没有被吞，并能证明手动顺延后的下一次提醒时间可读；锁屏要在有上下相邻通知的通知栈里证明提醒卡片不被遮挡；锁屏小组件要证明 accessoryCircular / accessoryRectangular / accessoryInline 至少一种可读、没有裁剪、没有展示隐私照片；桌面小组件要证明小尺寸和中尺寸都没有裁剪、没有展示隐私照片。`12-real-device-regression.md` 的锁屏小组件视觉结论不能只写“正常”，必须明确写“无裁剪 / 边缘完整 / 未右移压到岛中心 / 未贴边或未被吞 / 不遮挡 / 无溢出 / 不展示隐私照片”等机器可查结论。

RD-10、RD-13、RD-14、RD-15、RD-17、RD-18、RD-22、RD-23、RD-24 不能复用总览图。RD-10 恢复密钥登录、RD-13 手机号登录、RD-14 微信登录、RD-15 账号删除必须分别拆成 `RealDevice/RD-10-recovery-login.png`、`RealDevice/RD-13-phone-login.png`、`RealDevice/RD-14-wechat-login.png`、`RealDevice/RD-15-account-delete.png`；RD-17 通知权限允许和拒绝必须拆成 `RealDevice/RD-17-notification-allowed.png`、`RealDevice/RD-17-notification-denied.png`；RD-22 灵动岛紧凑态和展开态必须拆成 `RealDevice/RD-22-dynamic-island-compact.png`、`RealDevice/RD-22-dynamic-island-expanded.png`；RD-23 锁屏通知栈、锁屏小组件和桌面小组件必须拆成 `RealDevice/RD-23-lock-screen-notification-stack.png`、`RealDevice/RD-23-lock-screen-widget-summary.png`、`RealDevice/RD-23-home-widget-summary.png`。文件名也必须能识别场景：RD-10 要体现 recovery / 恢复；RD-13 要体现 phone / sms / 手机号 / 验证码；RD-14 要体现 wechat / 微信；RD-15 要体现 account / delete / 账号 / 删除；RD-17 要体现 notification / permission / 通知 / 权限；RD-18 要同时体现 watch 和 mirror / notification；RD-22 代表路径要体现 live-activity / dynamic-island / 灵动岛 和 switch / toggle / 开关 / compact / expanded；RD-23 代表路径要体现 widget / 小组件或 lock-screen / 锁屏；RD-24 要体现 review / boundary / 审核 / 边界。

## 采集后必跑

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-07-04 --output Backend/proof/app-store-evidence-20260704T-current.json
Backend/scripts/run_launch_readiness.sh \
  --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
  --app-path /tmp/XiaoNaiPing-WeChat-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260704-wechat-sim.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260704-wechat-device.log \
  --base-url https://api.mewpow.com/xiaonaiping \
  --live-check
```

如果 `app-store-evidence-20260704T-current.json` 或同步后的 `app-store-evidence.json` 仍有 `missingEvidence`，不能提交 App Store。
