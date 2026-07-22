# 12-real-device-regression.md Template

> 复制本文件为 `12-real-device-regression.md` 后再填写，并删除本模板提示。不要把恢复密钥、验证码、完整手机号、token、真实宝宝照片或对象存储 key 写进来。
> 本项目真机回归只接受 iOS 26.5；iOS 27.0 不能作为本项目真机回归证据。
> 重点截图现场核对另见 `RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json`；该 JSON 只是采集清单，不替代真实 TestFlight / 签名真机回归证据。

## 环境

- 设备：
- iOS：26.5
- 安装方式：TestFlight
- App 版本：
- Build：
- 网络：Wi-Fi / 蜂窝网络
- 证据截图/录屏：RealDevice/00-overview.png
- 灵动岛紧凑态结论：
- 灵动岛展开态结论：
- 锁屏通知栈结论：
- 锁屏小组件结论：
- 桌面小组件结论：

> 视觉结论不能只写“正常”。紧凑态要写无裁剪、边缘完整、未右移或未压到岛中心；展开态要写无裁剪、未贴边或未被吞；锁屏通知栈要写不遮挡；锁屏小组件和桌面小组件都要写无裁剪、无溢出或不展示隐私照片。

## 同一 build 身份锁

本文件的 App 版本和 Build 号必须同时对齐 `05-signed-archive.png`、`06-testflight.png`、`AppStoreConnect/ASC-07-build-testflight-link.png` 和 `APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md`。版本号和 build 号必须一致，证据只能来自同一 TestFlight build 或 Xcode 签名真机包，不能混用不同 build。

如果任一截图、表格或 App Store Connect 选中 build 对不上，先重新归档、上传或重跑真机回归；随后复跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_testflight_regression_plan.py` 和 `check_app_store_evidence.py --allow-incomplete`，再更新 `12-real-device-regression.md`。

## 上线当天执行顺序

同一天同一轮执行时，先完成外部和包体前置证明，再跑真机回归；不能先跑真机回归再补服务商证据。

1. 确认 `ios265-device-availability.json` 证明可用 physical iPhone 为 iOS 26.5。
2. 归档 `05-signed-archive.png` 和 `06-testflight.png`。
3. 完成 `verify_auth_providers.py --send-test-sms --require-sms-live-send`，并归档 `07-sms-provider.png`。
4. 归档 `08-wechat-open-platform.png` 和 `09-obs-policy.png`。
5. 复跑 `check_production_readiness.py`，确认 production proof 变绿或把红项写入阻断清单。
6. 使用同一 TestFlight build 或 Xcode 签名真机包填写 `12-real-device-regression.md`。
7. 先跑 `RD-11-cloud-sync.png`、`RD-12-cloud-restore.png`、`RD-13-phone-login.png`、`RD-14-wechat-login.png`、`RD-15-account-delete.png`。
8. 再跑 `RD-22-dynamic-island-compact.png`、`RD-22-dynamic-island-expanded.png`、`RD-23-lock-screen-notification-stack.png`、`RD-23-lock-screen-widget-summary.png`、`RD-23-home-widget-summary.png`。

## 必填勾选

- [ ] iOS 26.5
- [ ] 冷启动
- [ ] 手机号登录
- [ ] 微信登录
- [ ] 恢复密钥登录
- [ ] 云同步
- [ ] 云恢复
- [ ] 账号删除
- [ ] 通知权限
- [ ] 通知权限允许后可创建下一次喝奶提醒
- [ ] 通知权限拒绝后有可理解状态和系统设置入口
- [ ] 通知权限允许独立截图
- [ ] 通知权限拒绝独立截图
- [ ] 灵动岛喝奶提醒开关
- [ ] 灵动岛紧凑态头像和进度环未压到岛中心
- [ ] 灵动岛展开态文字和数字未贴边或被吞
- [ ] 灵动岛展开态展示手动顺延后的提醒时间
- [ ] 喂养顺延滚轮只提供不顺延和 +5、+10、+15、+20、+25、+30 分钟
- [ ] 下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算
- [ ] 锁屏通知栈上下相邻通知不遮挡提醒卡片
- [ ] 锁屏/桌面小组件
- [ ] 灵动岛紧凑态独立截图
- [ ] 灵动岛展开态独立截图
- [ ] 锁屏通知栈独立截图
- [ ] 锁屏小组件独立截图
- [ ] 桌面小组件独立截图
- [ ] 锁屏小组件内容不裁剪不展示隐私照片
- [ ] 桌面小组件内容不裁剪不展示隐私照片
- [ ] 审核边界文案

## 重点采集清单

> 每项必须填写实际观察结论和证据文件。证据必须来自 iOS 26.5 TestFlight 或 Xcode 签名真机包；模拟器、iOS 27、模板截图、空白图或口头结论不能替代。每项必须使用独立证据文件，不能用总览图或同一张截图同时替代多个视觉/权限结论。

| 场景 | 实际观察结论 | 证据 |
|---|---|---|
| 灵动岛紧凑态 |  | RealDevice/RD-22-dynamic-island-compact.png |
| 灵动岛展开态 | 必须确认下一次喝奶时间、固定间隔、手动顺延后的提醒时间都可读；顺延选项来自不顺延、+5、+10、+15、+20、+25、+30 分钟；文案不构成喂养建议 | RealDevice/RD-22-dynamic-island-expanded.png |
| 锁屏通知栈 |  | RealDevice/RD-23-lock-screen-notification-stack.png |
| 锁屏小组件 | 必须确认 accessoryCircular / accessoryRectangular / accessoryInline 至少一种锁屏小组件可读、无裁剪、不展示隐私照片、备注、token 或对象存储 key | RealDevice/RD-23-lock-screen-widget-summary.png |
| 桌面小组件 |  | RealDevice/RD-23-home-widget-summary.png |
| 恢复密钥登录 |  | RealDevice/RD-10-recovery-login.png |
| 手机号登录 |  | RealDevice/RD-13-phone-login.png |
| 微信登录 |  | RealDevice/RD-14-wechat-login.png |
| 账号删除 |  | RealDevice/RD-15-account-delete.png |
| 通知权限允许 |  | RealDevice/RD-17-notification-allowed.png |
| 通知权限拒绝 |  | RealDevice/RD-17-notification-denied.png |

## 通知权限双路径重置锁

RD-17 必须分别验证允许和拒绝两条路径。由于 iOS 通知授权状态会保留，拍 `RD-17-notification-allowed.png` 和 `RD-17-notification-denied.png` 前，必须先把 App 回到干净通知授权状态：删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包，或在系统设置中重置小奶瓶通知授权并确认首次弹窗会重新出现。不能在已经允许通知的安装状态下拍拒绝路径，也不能在已经拒绝通知的安装状态下拍允许路径。

| RD-17 路径 | 前置状态 | 必须观察 | 证据 |
|---|---|---|---|
| 通知权限允许 | 干净通知授权状态，首次弹窗可见 | 点击允许后可创建下一次喝奶提醒，并能看到 pending reminder 生效 | `RealDevice/RD-17-notification-allowed.png` |
| 通知权限拒绝 | 重新回到干净通知授权状态，首次弹窗可见 | 点击拒绝后有可理解状态和系统设置入口，不崩溃，不继续假装已创建提醒 | `RealDevice/RD-17-notification-denied.png` |

两张证据必须来自同一 App 版本 / Build 的独立安装或独立重置回合；不能复用同一次授权状态、不能复用同一张截图、不能用系统设置页单独替代 App 内状态。

## 证据索引与脱敏复核

> 每个核心证据文件都要填来源 build、文件大小、是否独立证据和脱敏复核。所有截图/录屏必须来自同一 TestFlight build 或 Xcode 签名真机包；文件大小不低于 10KB；不得复用总览图替代独立截图。

| 证据 | 来源 build | 文件大小 | 独立证据 | 脱敏复核 |
|---|---|---|---|---|
| `RealDevice/00-overview.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片已遮挡或未出现 |
| `RealDevice/RD-10-recovery-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥全文、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-13-phone-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 完整手机号和验证码已遮挡，不展示 token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-14-wechat-login.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示 AppSecret、debug code、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-15-account-delete.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-17-notification-allowed.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-17-notification-denied.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-22-dynamic-island-compact.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-22-dynamic-island-expanded.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-lock-screen-notification-stack.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-lock-screen-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |
| `RealDevice/RD-23-home-widget-summary.png` | TestFlight / Xcode 签名真机包 | 待填；不低于 10KB | 是 | 不展示恢复密钥、验证码、完整手机号、token、对象存储 key、真实宝宝照片 |

## 失败复测与阻断清单

> 任一 RD 失败时，不要覆盖失败证据；先保留失败截图或录屏，再用同一 iOS 26.5 TestFlight build 或 Xcode 签名真机包复测。失败仍存在时，不得提交 App Store Connect 审核，并把阻断写入 `RELEASE_CHECKLIST.md`、`LAUNCH_GATE_RERUN_20260626.md`、`production-readiness.json` 和 `launch-objective-audit.json` 的当前结论。

| 失败 RD | 失败现象 | 失败证据 | 复测证据 | 复测结果 | 阻断结论 |
|---|---|---|---|---|---|
| RD-13 手机号登录 | 真实短信服务商验证码未收到、校验失败或完整手机号/验证码入镜 | RealDevice/RD-13-phone-login-fail.png | RealDevice/RD-13-phone-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-14 微信登录 | 微信开放平台授权未拉起、未回到 App、AppSecret / debug code 入镜 | RealDevice/RD-14-wechat-login-fail.png | RealDevice/RD-14-wechat-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-17 通知权限 | 允许或拒绝路径不可理解，或拒绝后仍假装已创建提醒 | RealDevice/RD-17-notification-fail.png | RealDevice/RD-17-notification-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-22 灵动岛 | 紧凑态裁剪、压到岛中心，或展开态提醒时间/固定间隔/顺延结果不可读 | RealDevice/RD-22-dynamic-island-fail.png | RealDevice/RD-22-dynamic-island-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-23 锁屏/小组件 | 锁屏通知栈遮挡，或锁屏/桌面小组件裁剪、展示隐私照片、备注、token、对象存储 key | RealDevice/RD-23-widget-fail.png | RealDevice/RD-23-widget-retest.png | 待填 | 未通过前不得提交 App Store Connect |

## RD-01 到 RD-24 结果

> 最终提交前每一行都必须改成“通过”，并填写截图或录屏文件路径；路径必须指向 `Docs/08_Release/AppStoreEvidence/` 内真实存在且不低于 10KB 的 `.png`、`.jpg`、`.jpeg`、`.mp4`、`.mov` 或 `.pdf` 文件，不能只写目录，也不能写桌面、下载目录、微信临时目录或其他绝对路径。建议放在 `RealDevice/` 子目录。不能保留“待测”“待真实短信配置”或“待微信开放平台配置”。安装方式只能填写 `TestFlight` 或 `Xcode 签名真机包` 其中一个，不要保留斜杠选项。
> `RD-10`、`RD-13`、`RD-14`、`RD-15`、`RD-17`、`RD-18`、`RD-22`、`RD-23`、`RD-24` 必须使用各自独立的证据文件，不能复用 `RealDevice/00-overview.png` 或同一份泛证据。`RD-10` 文件名必须体现 recovery / 恢复；`RD-13` 文件名必须体现 phone / sms / 手机号 / 验证码；`RD-14` 文件名必须体现 wechat / 微信；`RD-15` 文件名必须体现 account / delete / 账号 / 删除；`RD-17` 文件名必须体现通知或权限；`RD-18` 文件名必须同时体现 watch 和 mirror / notification；`RD-22` 代表路径必须体现 live-activity / dynamic-island / 灵动岛 和 switch / toggle / 开关 / compact / expanded；`RD-23` 代表路径必须体现 widget / 小组件或 lock-screen / 锁屏。

| 编号 | 结果 | 证据/备注 |
|---|---|---|
| RD-01 冷启动进入首页 | 待测 | RealDevice/RD-01-cold-start.png |
| RD-02 创建宝宝档案 | 待测 | RealDevice/RD-02-baby-profile.png |
| RD-03 记录喂养 | 待测 | RealDevice/RD-03-feeding-record.png；需验证已有固定喝奶间隔时，顺延滚轮只提供不顺延、+5、+10、+15、+20、+25、+30 分钟 |
| RD-04 记录睡眠 | 待测 | RealDevice/RD-04-sleep-record.png |
| RD-05 记录排便 | 待测 | RealDevice/RD-05-diaper-record.png |
| RD-06 成长记录 | 待测 | RealDevice/RD-06-growth-record.png |
| RD-07 疫苗模板切换 | 待测 | RealDevice/RD-07-vaccine-template.png |
| RD-08 相册权限拒绝 | 待测 | RealDevice/RD-08-photo-denied.png |
| RD-09 相册权限允许 | 待测 | RealDevice/RD-09-photo-allowed.png |
| RD-10 恢复密钥账号登录 | 待测 | RealDevice/RD-10-recovery-login.png |
| RD-11 云同步 | 待测 | RealDevice/RD-11-cloud-sync.png |
| RD-12 云恢复 | 待测 | RealDevice/RD-12-cloud-restore.png |
| RD-13 手机号登录 | 待真实短信配置 | RealDevice/RD-13-phone-login.png |
| RD-14 微信登录 | 待微信开放平台配置 | RealDevice/RD-14-wechat-login.png |
| RD-15 删除云端账号与同步 | 待测 | RealDevice/RD-15-account-delete.png |
| RD-16 断网保存 | 待测 | RealDevice/RD-16-offline-save.png |
| RD-17 通知权限 | 待测 | RealDevice/RD-17-notification-allowed.png；RealDevice/RD-17-notification-denied.png |
| RD-18 Apple Watch 镜像通知 | 待测 | RealDevice/RD-18-watch-mirror.png |
| RD-19 隐私政策/用户协议/支持 URL | 待测 | RealDevice/RD-19-public-urls.png |
| RD-20 崩溃/日志脱敏 | 待测 | RealDevice/RD-20-diagnostics-redaction.png |
| RD-21 Release 包体自检 | 待测 | RealDevice/RD-21-release-bundle.png |
| RD-22 灵动岛喝奶提醒开关 | 待测 | RealDevice/RD-22-dynamic-island-compact.png；RealDevice/RD-22-dynamic-island-expanded.png |
| RD-23 锁屏/桌面小组件 | 待测 | RealDevice/RD-23-lock-screen-notification-stack.png；RealDevice/RD-23-lock-screen-widget-summary.png；RealDevice/RD-23-home-widget-summary.png |
| RD-24 审核边界文案 | 待测 | RealDevice/RD-24-review-boundary.png |

## 审核边界确认

- [ ] Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔。
- [ ] 手动顺延只改变下一次提醒时间，不新增持久化字段，不根据奶量、月龄、传感器或健康数据自动推算。
- [ ] 下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。
- [ ] 小组件只读展示本机今日摘要，不展示照片原图、备注、token 或对象 key。
- [ ] Apple Watch 只作为系统镜像通知，不在 App Store 文案中承诺 Watch App。
- [ ] 状态展示只反映用户主动记录的数据。
- [ ] 不生成健康建议、压力提醒、喂养建议或医疗判断。
- [ ] 不接入 HealthKit、传感器、医院系统或第三方健康数据源。
- [ ] 不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议。
