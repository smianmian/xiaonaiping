# TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 日期：2026-06-30
- 用途：App Store 审核测试账号和真机回归记录
- 当前结论：恢复密钥测试账号已创建；iOS 26.5 本机模拟器安装启动烟测通过；当前可用真机为 iOS 27.0，按本项目规则未用于本机测试；手机号和微信测试号、TestFlight 真机回归尚未完成。

## 测试账号

| 项目 | 状态 |
|---|---|
| 恢复密钥测试账号 | 已创建 |
| 账号 ID | 见 `Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json` |
| 恢复密钥 | 只保存在本机 `.env.xnp-review-account`，不得提交到仓库 |
| 测试数据 | 已写入“审核测试宝宝”假数据和少量记录 |
| 恢复验证 | 已通过 `/v1/sessions/recover` 验证 |
| 手机号测试号 | 待真实短信服务商配置后补 |
| 微信测试号 | 待微信开放平台移动应用配置后补 |

### App Store Connect 填写方式

在 App Review Information 中填写，不写进仓库：

1. 登录路径：打开 App -> 设置 -> 账号与同步 -> 恢复密钥登录。
2. 恢复密钥：读取本机 `.env.xnp-review-account` 中的 `XNP_REVIEW_RECOVERY_KEY`。
3. 说明：该账号只含虚构宝宝资料，不含真实宝宝照片或家庭资料。
4. 手机号和微信测试信息：待短信和微信真实配置完成后补充。

### 审核员核心测试路径

1. 冷启动 App，进入“今日”页确认示例为空状态和快速记录入口可见。
2. 在“记录”页新增一条喂养、睡眠或排便记录，回到首页确认今日摘要更新。
3. 在“成长”页新增身高体重记录，确认趋势页可打开。
4. 在“资料 -> 账号与同步 -> 恢复密钥登录”使用 App Review Information 中的恢复密钥登录。
5. 触发“立即同步”，再使用恢复路径确认虚构测试数据可恢复。
6. 打开“数据与隐私”并验证云端账号删除路径可见。

### 审核时不得使用

1. 不使用 debug code、工程内部账号、真实宝宝照片或真实家庭数据。
2. 不使用未配置完成的微信登录替代恢复密钥审核路径。
3. 不把 `.env.xnp-review-account`、恢复密钥、手机号验证码或服务端 token 写入截图、录屏或仓库。

## 真机回归环境

| 项目 | 填写 |
|---|---|
| 设备 | 待填，当前本机模拟器只使用 iPhone 17 Pro / iOS 26.5 |
| iOS 版本 | iOS 26.5；本机测试不得改用旧 runtime |
| App 版本 | 待填 |
| Build 号 | 待填 |
| 安装方式 | TestFlight / Xcode 签名真机包 |
| 网络 | Wi-Fi + 蜂窝网络各一轮 |
| Apple ID 地区 | 中国大陆 |
| 证据文件 | `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md` |

## 同一 build 身份锁

`12-real-device-regression.md` 里的 App 版本和 Build 号必须同时对齐 `05-signed-archive.png`、`06-testflight.png`、`AppStoreConnect/ASC-07-build-testflight-link.png` 和 `APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md`。版本号和 build 号必须一致，证据只能来自同一 TestFlight build 或 Xcode 签名真机包，不能混用不同 build。

如果任一截图、表格或 App Store Connect 选中 build 对不上，先重新归档、上传或重跑真机回归；随后复跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_testflight_regression_plan.py` 和 `check_app_store_evidence.py --allow-incomplete`，再更新本表。

### 当前本机真机可用性

| 设备 | 系统 | 状态 | 本轮处理 |
|---|---|---|---|
| 蓝蓝 / iPhone 16 Pro Max | iOS 26.5 | unavailable | 符合版本但当前不可用，未测试 |
| 面面 / iPhone 16 Plus | iOS 27.0 | available (paired) | 不符合本项目 iOS 26.5 本机测试规则，未测试 |

机器证据：`Backend/proof/ios265-device-availability.json`。该证据只证明本机设备版本策略已检查，不替代 TestFlight / 签名真机回归。

结构化重点采集包：`Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json`。它只用于现场逐张核对 RD-10 / RD-13 / RD-14 / RD-15 / RD-17 / RD-22 / RD-23 的目标文件、前置条件、观察点和脱敏项，不替代 `12-real-device-regression.md` 或真实 iOS 26.5 TestFlight / 签名真机证据。

结构化审核测试账号执行包：`Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260630.json`。它只用于锁定 App Review 私密 Sign-In Information 的恢复密钥来源、脱敏账号证据、RD-10/RD-13/RD-14/RD-15 账号链路采集、账号删除和复跑 gate；状态为 `review-test-account-packet-not-evidence`，不保存恢复密钥，不能替代真实 iOS 26.5 TestFlight / 签名真机证据，也不能作为提交许可。

## 上线当天执行顺序

同一天同一轮执行时，先完成外部和包体前置证明，再跑真机回归；不能先跑真机回归再补服务商证据。

1. 确认 `ios265-device-availability.json` 证明可用 physical iPhone 为 iOS 26.5。
2. 完成 D-U-N-S 后 Apple Developer Organization enrollment、Team ID、App Store Distribution certificate / provisioning profile，并归档 `05-signed-archive.png`。
3. 上传同一 build 到 TestFlight，处理完成并可测试后归档 `06-testflight.png`。
4. 完成短信服务商真实实发验证，命令包含 `verify_auth_providers.py --send-test-sms --require-sms-live-send`，并归档 `07-sms-provider.png`。
5. 完成微信开放平台 AppID、Bundle ID、URL Scheme、Universal Link 后台绑定和服务端 AppSecret 私有配置，并归档 `08-wechat-open-platform.png`。
6. 完成 OBS bucket、区域、加密、生命周期和删除验证，并归档 `09-obs-policy.png`。
7. 复跑 `check_production_readiness.py`，确认 production proof 变绿或把红项写入阻断清单。
8. 只在上述前置完成后，使用同一 TestFlight build 或 Xcode 签名真机包填写 `12-real-device-regression.md`。
9. 先跑账号和服务端链路：`RD-11-cloud-sync.png`、`RD-12-cloud-restore.png`、`RD-13-phone-login.png`、`RD-14-wechat-login.png`、`RD-15-account-delete.png`。
10. 再跑视觉和通知链路：`RD-22-dynamic-island-compact.png`、`RD-22-dynamic-island-expanded.png`、`RD-23-lock-screen-notification-stack.png`、`RD-23-lock-screen-widget-summary.png`、`RD-23-home-widget-summary.png`。

## 本机 iOS 26.5 烟测证据

| 项目 | 结果 |
|---|---|
| Release 模拟器包 | `/Users/smianmian/Downloads/小奶瓶/build/Run-20260630-xnp-ios265-release/Build/Products/Release-iphonesimulator/XiaoNaiPing.app` |
| 设备 | iPhone 17 Pro / iOS 26.5 |
| 安装 | 通过 |
| 启动 | 通过，输出 `com.mewpow.xiaonaiping: 43802` |
| 证据 | `Backend/proof/sim-launch-ios265-20260630-current.json` |
| launchOutput | `com.mewpow.xiaonaiping: 43802` |
| 注意 | 该证据只证明本机 iOS 26.5 安装启动，不替代 TestFlight / 签名真机回归 |

## 必测用例

| 编号 | 用例 | 期望 | 结果 |
|---|---|---|---|
| RD-01 | 冷启动进入首页 | 不崩溃，首页可见 | 待测 |
| RD-02 | 创建宝宝档案 | 本地保存成功，重启后仍存在 | 待测 |
| RD-03 | 记录喂养 | 首页今日摘要和最近记录更新；已有固定喝奶间隔时，顺延滚轮提供不顺延、+5、+10、+15、+20、+25、+30 分钟，保存后下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算 | 待测 |
| RD-04 | 记录睡眠 | 睡眠记录可保存、可回看 | 待测 |
| RD-05 | 记录排便 | 排便记录可保存、可回看 | 待测 |
| RD-06 | 成长记录 | 身高体重可保存，成长页可见 | 待测 |
| RD-07 | 疫苗模板切换 | 中国大陆 / 香港模板可切换；文案不构成医疗建议 | 待测 |
| RD-08 | 相册权限拒绝 | 拒绝权限后 App 不崩溃，有可理解状态 | 待测 |
| RD-09 | 相册权限允许 | 可主动加入照片；不自动扫描系统相册 | 待测 |
| RD-10 | 恢复密钥账号登录 | 可用测试恢复密钥连接账号 | 待测 |
| RD-11 | 云同步 | 同步成功，服务端无真实宝宝照片或手机号明文证据外泄 | 待测 |
| RD-12 | 云恢复 | 清空/换装后可恢复测试数据 | 待测 |
| RD-13 | 手机号登录 | 真实验证码可发送、可校验、频控正常 | 待真实短信配置 |
| RD-14 | 微信登录 | 可拉起微信授权并回到 App | 待微信开放平台配置 |
| RD-15 | 删除云端账号与同步 | 云端同步、照片对象、账号失效 | 待测 |
| RD-16 | 断网保存 | 本地记录可保存；云操作给出失败状态 | 待测 |
| RD-17 | 通知权限 | 允许后可创建下一次喝奶提醒；拒绝后有可理解状态和系统设置入口；关闭提醒会移除 pending notification | 待测 |
| RD-18 | Apple Watch 镜像通知 | iPhone 本地通知可按系统设置镜像到 Apple Watch | 待测 |
| RD-19 | 隐私政策/用户协议/支持 URL | App Store Connect URL 可打开，无 404 | 待测 |
| RD-20 | 崩溃/日志脱敏 | 不输出宝宝内容、照片对象 key、手机号明文 | 待测 |
| RD-21 | Release 包体自检 | `ios-app-bundle.json` 不含内部文档、本地地址、debug 文案或 API key 标记 | 当前通过；微信配置仍阻断 |
| RD-22 | 灵动岛喝奶提醒开关 | 开关打开后仅在保存喝奶闹钟时展示下一次喝奶时间、固定间隔和手动顺延后的提醒时间；顺延只改变下一次提醒时间、不新增持久化字段；关闭后结束 Live Activity | 待测 |
| RD-23 | 锁屏/桌面小组件 | 锁屏通知栈不遮挡；锁屏小组件和桌面小组件只读展示本机今日摘要、下一次喝奶提醒、进行中睡眠等，不展示照片原图、备注、token 或云端对象 key | 待测 |
| RD-24 | 审核边界文案 | App 内和审核说明明确灵动岛/Live Activity/小组件只是状态展示，不暗示 HealthKit、传感器、健康建议、压力评估、压力提醒、心理健康判断、医疗诊断或喂养建议 | 待测 |

## 重点采集清单

以下证据必须来自 iOS 26.5 TestFlight 或 Xcode 签名真机包；模拟器、iOS 27、模板截图、空白图或口头结论不能替代。截图/录屏不得出现恢复密钥、验证码、完整手机号、真实宝宝照片、token、对象存储 key、debug code 或内部后台。

| 场景 | 必拍内容 | 建议证据 |
|---|---|---|
| 灵动岛紧凑态 | 开启喝奶提醒后，灵动岛紧凑态头像/进度环完整，无裁剪、未压到岛中心；每项必须使用独立证据文件 | `RealDevice/RD-22-dynamic-island-compact.png` |
| 灵动岛展开态 | 长按展开 Live Activity，下一次喝奶时间、固定间隔、手动顺延后的提醒时间可读；顺延选项来自不顺延、+5、+10、+15、+20、+25、+30 分钟，文案不构成喂养建议；每项必须使用独立证据文件 | `RealDevice/RD-22-dynamic-island-expanded.png` |
| 锁屏通知栈 | 下一次喝奶提醒在锁屏通知栈内不被上下相邻通知遮挡，锁屏卡片不展示备注、token 或照片原图；每项必须使用独立证据文件 | `RealDevice/RD-23-lock-screen-notification-stack.png` |
| 锁屏小组件 | 锁屏 accessoryCircular / accessoryRectangular / accessoryInline 小组件只读展示本机今日摘要或下一次提醒，不裁剪、不展示隐私照片、备注、token 或云端对象 key；每项必须使用独立证据文件 | `RealDevice/RD-23-lock-screen-widget-summary.png` |
| 桌面小组件 | 桌面小组件只读展示本机今日摘要/下一次提醒，不裁剪、不展示隐私照片或云端对象 key；每项必须使用独立证据文件 | `RealDevice/RD-23-home-widget-summary.png` |
| 恢复密钥登录 | 使用 App Review Information 中的恢复密钥登录，截图只展示登录成功状态，不展示密钥全文 | `RealDevice/RD-10-recovery-login.png` |
| 手机号登录 | 真实短信验证码可发送和校验，截图遮挡完整手机号和验证码 | `RealDevice/RD-13-phone-login.png` |
| 微信登录 | 微信开放平台配置完成后，可拉起微信授权并回到 App；不使用 debug code | `RealDevice/RD-14-wechat-login.png` |
| 账号删除 | 删除云端账号与同步后，账号失效、云端 JSON 同步和照片对象删除，本机资料保留边界清楚 | `RealDevice/RD-15-account-delete.png` |
| 通知权限允许 | 首次允许通知后，可创建下一次喝奶提醒，并能看到 pending reminder 生效；每项必须使用独立证据文件 | `RealDevice/RD-17-notification-allowed.png` |
| 通知权限拒绝 | 拒绝通知后有可理解状态和系统设置入口，不崩溃，不继续假装已创建提醒；每项必须使用独立证据文件 | `RealDevice/RD-17-notification-denied.png` |

## 通知权限双路径重置锁

RD-17 必须分别验证允许和拒绝两条路径。由于 iOS 通知授权状态会保留，拍 `RD-17-notification-allowed.png` 和 `RD-17-notification-denied.png` 前，必须先把 App 回到干净通知授权状态：删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包，或在系统设置中重置小奶瓶通知授权并确认首次弹窗会重新出现。不能在已经允许通知的安装状态下拍拒绝路径，也不能在已经拒绝通知的安装状态下拍允许路径。

| RD-17 路径 | 前置状态 | 必须观察 | 证据 |
|---|---|---|---|
| 通知权限允许 | 干净通知授权状态，首次弹窗可见 | 点击允许后可创建下一次喝奶提醒，并能看到 pending reminder 生效 | `RealDevice/RD-17-notification-allowed.png` |
| 通知权限拒绝 | 重新回到干净通知授权状态，首次弹窗可见 | 点击拒绝后有可理解状态和系统设置入口，不崩溃，不继续假装已创建提醒 | `RealDevice/RD-17-notification-denied.png` |

两张证据必须来自同一 App 版本 / Build 的独立安装或独立重置回合；不能复用同一次授权状态、不能复用同一张截图、不能用系统设置页单独替代 App 内状态。

## 证据索引与脱敏复核

填写 `12-real-device-regression.md` 时，必须把每个核心证据文件登记到索引表。所有截图/录屏必须来自同一 TestFlight build 或 Xcode 签名真机包，文件大小不低于 10KB，并逐项确认是独立证据、已脱敏。

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

任一 RD 失败时，不要覆盖失败证据；先保留失败截图或录屏，再用同一 iOS 26.5 TestFlight build 或 Xcode 签名真机包复测。失败仍存在时，不得提交 App Store Connect 审核，并把阻断写入 `RELEASE_CHECKLIST.md`、`LAUNCH_GATE_RERUN_20260626.md`、`production-readiness.json` 和 `launch-objective-audit.json` 的当前结论。

| 失败 RD | 失败现象 | 失败证据 | 复测证据 | 复测结果 | 阻断结论 |
|---|---|---|---|---|---|
| RD-13 手机号登录 | 真实短信服务商验证码未收到、校验失败或完整手机号/验证码入镜 | RealDevice/RD-13-phone-login-fail.png | RealDevice/RD-13-phone-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-14 微信登录 | 微信开放平台授权未拉起、未回到 App、AppSecret / debug code 入镜 | RealDevice/RD-14-wechat-login-fail.png | RealDevice/RD-14-wechat-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-17 通知权限 | 允许或拒绝路径不可理解，或拒绝后仍假装已创建提醒 | RealDevice/RD-17-notification-fail.png | RealDevice/RD-17-notification-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-22 灵动岛 | 紧凑态裁剪、压到岛中心，或展开态提醒时间/固定间隔/顺延结果不可读 | RealDevice/RD-22-dynamic-island-fail.png | RealDevice/RD-22-dynamic-island-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-23 锁屏/小组件 | 锁屏通知栈遮挡，或锁屏/桌面小组件裁剪、展示隐私照片、备注、token、对象存储 key | RealDevice/RD-23-widget-fail.png | RealDevice/RD-23-widget-retest.png | 待填 | 未通过前不得提交 App Store Connect |

## 通过标准

1. RD-01 到 RD-12、RD-15 到 RD-24 必须通过。
2. RD-13 和 RD-14 必须在真实短信和微信配置完成后通过；不能用 debug code 代替。
3. 每轮真机回归必须附截图或录屏证据；同时填写 `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md`，并把核心项勾选为完成。
4. 每个 RD 用例的证据路径必须指向 `Docs/08_Release/AppStoreEvidence/` 内真实存在的非空文件，不能填写桌面、下载目录、微信临时目录或其他绝对路径。
5. `12-real-device-regression.md` 的“审核边界确认”必须全部勾选，尤其是 Live Activity / 小组件只做状态展示、手动顺延只改变下一次提醒时间、不新增持久化字段、只反映用户主动记录数据、不生成健康建议/压力提醒/喂养建议/医疗判断、无 HealthKit/传感器/医院系统/第三方健康数据源。
6. 失败项必须进入阻断清单，不允许在 `RELEASE_CHECKLIST.md` 中打勾。

## 建议证据文件名

把真机截图和录屏统一放在 `Docs/08_Release/AppStoreEvidence/RealDevice/`。下面是建议文件名；复制模板后可以直接使用这些相对路径，最终文件必须真实存在且非空。

| 证据 | 建议路径 |
|---|---|
| 环境总览 | `RealDevice/00-overview.png` |
| RD-01 冷启动进入首页 | `RealDevice/RD-01-cold-start.png` |
| RD-02 创建宝宝档案 | `RealDevice/RD-02-baby-profile.png` |
| RD-03 记录喂养 | `RealDevice/RD-03-feeding-record.png` |
| RD-04 记录睡眠 | `RealDevice/RD-04-sleep-record.png` |
| RD-05 记录排便 | `RealDevice/RD-05-diaper-record.png` |
| RD-06 成长记录 | `RealDevice/RD-06-growth-record.png` |
| RD-07 疫苗模板切换 | `RealDevice/RD-07-vaccine-template.png` |
| RD-08 相册权限拒绝 | `RealDevice/RD-08-photo-denied.png` |
| RD-09 相册权限允许 | `RealDevice/RD-09-photo-allowed.png` |
| RD-10 恢复密钥账号登录 | `RealDevice/RD-10-recovery-login.png` |
| RD-11 云同步 | `RealDevice/RD-11-cloud-sync.png` |
| RD-12 云恢复 | `RealDevice/RD-12-cloud-restore.png` |
| RD-13 手机号登录 | `RealDevice/RD-13-phone-login.png` |
| RD-14 微信登录 | `RealDevice/RD-14-wechat-login.png` |
| RD-15 删除云端账号与同步 | `RealDevice/RD-15-account-delete.png` |
| RD-16 断网保存 | `RealDevice/RD-16-offline-save.png` |
| RD-17 通知权限允许 | `RealDevice/RD-17-notification-allowed.png` |
| RD-17 通知权限拒绝 | `RealDevice/RD-17-notification-denied.png` |
| RD-18 Apple Watch 镜像通知 | `RealDevice/RD-18-watch-mirror.png` |
| RD-19 隐私政策/用户协议/支持 URL | `RealDevice/RD-19-public-urls.png` |
| RD-20 崩溃/日志脱敏 | `RealDevice/RD-20-diagnostics-redaction.png` |
| RD-21 Release 包体自检 | `RealDevice/RD-21-release-bundle.png` |
| RD-22 灵动岛紧凑态 | `RealDevice/RD-22-dynamic-island-compact.png` |
| RD-22 灵动岛展开态 | `RealDevice/RD-22-dynamic-island-expanded.png` |
| RD-23 锁屏通知栈 | `RealDevice/RD-23-lock-screen-notification-stack.png` |
| RD-23 锁屏小组件 | `RealDevice/RD-23-lock-screen-widget-summary.png` |
| RD-23 桌面小组件 | `RealDevice/RD-23-home-widget-summary.png` |
| RD-24 审核边界文案 | `RealDevice/RD-24-review-boundary.png` |
