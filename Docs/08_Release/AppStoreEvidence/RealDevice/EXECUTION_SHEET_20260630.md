# 小奶瓶真机证据现场执行单

日期：2026-06-30

状态：现场拍摄和填表用，不是已完成证据。正式提交仍以 `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md`、`Backend/proof/testflight-regression-plan.json` 和 `Backend/proof/app-store-evidence-20260630T-current.json` 为准。重点截图结构化清单见 `FOCUSED_CAPTURE_PACKET_20260630.json`，它只用于现场逐项核对，不替代真实 iOS 26.5 TestFlight / 签名真机证据。

## 0. 硬门槛

- 只接受 iOS 26.5。
- 构建来源只能是 `TestFlight` 或 `Xcode 签名真机包`。
- TestFlight 或 Xcode 签名真机包必须能对应最终提交前的签名构建。
- RD 编号、用例名称和目标文件必须与 `Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`、`Docs/08_Release/AppStoreEvidence/12-real-device-regression.template.md` 保持一致。
- 所有 RD 文件都放在 `Docs/08_Release/AppStoreEvidence/RealDevice/`。
- 每个证据文件不低于 10KB。
- 所有截图/录屏必须记录采集开始时间、采集结束时间和同一测试时间窗口。
- 不能复用跨天、旧版本、聊天转发或无法证明拍摄时间的素材。
- 补拍必须写补拍时间、补拍原因和对应 RD 编号，并继续使用同一 build 复测。
- 不能写桌面、下载目录、微信临时目录或绝对路径。
- 完整手机号、验证码、AccessKey、Secret、AppSecret 全遮。
- 不保存恢复密钥、token、对象 key、真实宝宝照片或未授权家庭资料。
- 不写喂养建议、健康建议、压力提醒、心理健康判断或医疗诊断。

## 1. 开始前

| 项 | 填写 |
| --- | --- |
| 设备 |  |
| iOS | 26.5 |
| 安装方式 | TestFlight / Xcode 签名真机包 |
| App 版本 / Build |  |
| 网络 | Wi-Fi / 蜂窝网络 |
| 测试时间 |  |
| 采集开始时间 |  |
| 采集结束时间 |  |
| 补拍记录 | 无 / 有，见失败复测与阻断清单 |
| 前置 build 证据 | `05-signed-archive.png`、`06-testflight.png` |
| 结构化结果模板 | `RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json` |
| 结构化结果文件 | `RealDevice/REAL-DEVICE-CAPTURE-RESULT.json` |

## 同一 build 身份锁

现场填写的 App 版本和 Build 号必须同时对齐 `05-signed-archive.png`、`06-testflight.png`、`AppStoreConnect/ASC-07-build-testflight-link.png`、`APP_STORE_VERSION_RELEASE_SETTINGS_20260630.md` 和 `12-real-device-regression.md`。版本号和 build 号必须一致，证据只能来自同一 TestFlight build 或 Xcode 签名真机包，不能混用不同 build。

如果同一测试时间窗口内无法完成全部 RD，必须拆成新的执行单并重新证明版本号、Build、安装来源和采集时间；不能把跨窗口素材合并成同一轮通过结论。

如果任一截图、表格或 App Store Connect 选中 build 对不上，先重新归档、上传或重跑真机回归；随后复跑 `check_ios_app_bundle.py`、`check_testflight_precheck.py`、`check_testflight_regression_plan.py` 和 `check_app_store_evidence.py --allow-incomplete`，再把结果填回正式文件。

## 2. 核心 App 流程

| RD | 目标文件 | 通过结论 |
| --- | --- | --- |
| RD-01 冷启动进入首页 | `RealDevice/RD-01-cold-start.png` | 首页首屏可见，不崩溃，不展示 debug 文案 |
| RD-02 创建宝宝档案 | `RealDevice/RD-02-baby-profile.png` | 宝宝档案可新建、编辑、切换，使用虚构宝宝资料 |
| RD-03 记录喂养 | `RealDevice/RD-03-feeding-record.png` | 喂养记录可保存；已有固定喝奶间隔时，顺延滚轮只提供不顺延、+5、+10、+15、+20、+25、+30 分钟 |
| RD-04 记录睡眠 | `RealDevice/RD-04-sleep-record.png` | 睡眠记录可添加、编辑、删除 |
| RD-05 记录排便 | `RealDevice/RD-05-diaper-record.png` | 尿布记录可添加、编辑、删除 |
| RD-06 成长记录 | `RealDevice/RD-06-growth-record.png` | 身高体重记录可保存，成长页可见 |
| RD-07 疫苗模板切换 | `RealDevice/RD-07-vaccine-template.png` | 中国大陆 / 香港模板可切换，文案不构成医疗建议 |
| RD-08 相册权限拒绝 | `RealDevice/RD-08-photo-denied.png` | 拒绝权限后 App 不崩溃，有可理解状态 |
| RD-09 相册权限允许 | `RealDevice/RD-09-photo-allowed.png` | 可主动加入示例照片，不自动扫描系统相册 |
| RD-10 恢复密钥账号登录 | `RealDevice/RD-10-recovery-login.png` | 恢复密钥登录成功，恢复密钥不入镜 |
| RD-11 云同步 | `RealDevice/RD-11-cloud-sync.png` | 云同步成功，不展示对象 key、AK/SK 或 token |
| RD-12 云恢复 | `RealDevice/RD-12-cloud-restore.png` | 云恢复成功，恢复密钥和 token 脱敏 |
| RD-13 手机号登录 | `RealDevice/RD-13-phone-login.png` | 真实短信验证码可发送和校验，完整手机号和验证码脱敏 |
| RD-14 微信登录 | `RealDevice/RD-14-wechat-login.png` | 微信登录拉起授权并回到 App，不使用 debug code，AppSecret 不入镜 |
| RD-15 删除云端账号与同步 / 账号删除 | `RealDevice/RD-15-account-delete.png` | 删除前测试账号已完成云同步且云端照片对象存在可删除 proof；删除后旧 token 失效，重新打开 App 不自动恢复旧账号，本地缓存身份清理完成，云端同步和照片对象删除，本机资料默认保留边界清楚，删除后不展示真实宝宝照片 |
| RD-16 断网保存 | `RealDevice/RD-16-offline-save.png` | 断网时本地记录可保存，云操作给出失败状态 |

RD-15 删除后必须单独确认：旧 token 失效，云端同步和照片对象删除；OBS 控制台截图、服务端日志或后台 proof 只能作为辅助，不替代 iOS 26.5 TestFlight / Xcode 签名真机包里的账号删除结果。

## 3. 通知、公开 URL 和审核边界

| RD | 目标文件 | 通过结论 |
| --- | --- | --- |
| RD-17 通知权限 | `RealDevice/RD-17-notification-allowed.png`、`RealDevice/RD-17-notification-denied.png` | 允许后可创建下一次喝奶提醒；拒绝后有可理解状态和系统设置入口 |
| RD-18 Apple Watch 镜像通知 | `RealDevice/RD-18-watch-mirror.png` | 只证明 iPhone 本地通知可按系统设置镜像，不承诺独立 Watch App |
| RD-19 隐私政策/用户协议/支持 URL | `RealDevice/RD-19-public-urls.png` | 隐私政策、用户协议、技术支持 URL 可打开，无 404 |
| RD-20 崩溃/日志脱敏 | `RealDevice/RD-20-diagnostics-redaction.png` | 不输出宝宝内容、照片对象 key、手机号明文或 token |
| RD-21 Release 包体自检 | `RealDevice/RD-21-release-bundle.png` | `ios-app-bundle.json` 结果可见，不含内部文档、本地地址、debug 文案或 API key 标记 |
| RD-22 灵动岛喝奶提醒开关 / 灵动岛 / 锁屏提醒 | `RealDevice/RD-22-dynamic-island-compact.png`、`RealDevice/RD-22-dynamic-island-expanded.png` | 紧凑态无裁剪；展开态下一次喝奶时间、固定间隔、手动顺延后的提醒时间可读 |
| RD-23 锁屏/桌面小组件 / 桌面/锁屏小组件 | `RealDevice/RD-23-lock-screen-notification-stack.png`、`RealDevice/RD-23-lock-screen-widget-summary.png`、`RealDevice/RD-23-home-widget-summary.png` | 锁屏通知栈不遮挡；锁屏小组件和桌面小组件只读展示今日摘要，不展示备注、真实照片、token 或对象 key |
| RD-24 审核边界文案 | `RealDevice/RD-24-review-boundary.png` | App 内和审核说明不暗示 HealthKit、传感器、健康建议、压力评估、心理健康判断、医疗诊断或喂养建议 |

## 通知权限双路径重置锁

RD-17 必须分别验证允许和拒绝两条路径。由于 iOS 通知授权状态会保留，拍 `RD-17-notification-allowed.png` 和 `RD-17-notification-denied.png` 前，必须先把 App 回到干净通知授权状态：删除 App 后重新安装同一 TestFlight build / Xcode 签名真机包，或在系统设置中重置小奶瓶通知授权并确认首次弹窗会重新出现。不能在已经允许通知的安装状态下拍拒绝路径，也不能在已经拒绝通知的安装状态下拍允许路径。

| RD-17 路径 | 前置状态 | 必须观察 | 证据 |
|---|---|---|---|
| 通知权限允许 | 干净通知授权状态，首次弹窗可见 | 点击允许后可创建下一次喝奶提醒，并能看到 pending reminder 生效 | `RealDevice/RD-17-notification-allowed.png` |
| 通知权限拒绝 | 重新回到干净通知授权状态，首次弹窗可见 | 点击拒绝后有可理解状态和系统设置入口，不崩溃，不继续假装已创建提醒 | `RealDevice/RD-17-notification-denied.png` |

两张证据必须来自同一 App 版本 / Build 的独立安装或独立重置回合；不能复用同一次授权状态、不能复用同一张截图、不能用系统设置页单独替代 App 内状态。

## 4. 证据索引与脱敏复核

拍完后先填这个表，再填回 `12-real-device-regression.md`。所有截图/录屏必须来自同一 TestFlight build 或 Xcode 签名真机包，文件大小不低于 10KB，并逐项确认是独立证据、已脱敏。

| 证据 | 来源 build | 文件大小 | 独立证据 | 脱敏复核 |
| --- | --- | --- | --- | --- |
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

## 5. 失败复测与阻断清单

任一 RD 失败时，不要覆盖失败证据；先保留失败截图或录屏，再用同一 iOS 26.5 TestFlight build 或 Xcode 签名真机包复测。失败仍存在时，不得提交 App Store Connect 审核，并把阻断写入 `RELEASE_CHECKLIST.md`、`LAUNCH_GATE_RERUN_20260626.md`、`production-readiness.json` 和 `launch-objective-audit.json` 的当前结论。

| 失败 RD | 失败现象 | 失败证据 | 复测证据 | 复测结果 | 阻断结论 |
|---|---|---|---|---|---|
| RD-13 手机号登录 | 真实短信服务商验证码未收到、校验失败或完整手机号/验证码入镜 | RealDevice/RD-13-phone-login-fail.png | RealDevice/RD-13-phone-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-14 微信登录 | 微信开放平台授权未拉起、未回到 App、AppSecret / debug code 入镜 | RealDevice/RD-14-wechat-login-fail.png | RealDevice/RD-14-wechat-login-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-17 通知权限 | 允许或拒绝路径不可理解，或拒绝后仍假装已创建提醒 | RealDevice/RD-17-notification-fail.png | RealDevice/RD-17-notification-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-22 灵动岛 | 紧凑态裁剪、压到岛中心，或展开态提醒时间/固定间隔/顺延结果不可读 | RealDevice/RD-22-dynamic-island-fail.png | RealDevice/RD-22-dynamic-island-retest.png | 待填 | 未通过前不得提交 App Store Connect |
| RD-23 锁屏/小组件 | 锁屏通知栈遮挡，或锁屏/桌面小组件裁剪、展示隐私照片、备注、token、对象存储 key | RealDevice/RD-23-widget-fail.png | RealDevice/RD-23-widget-retest.png | 待填 | 未通过前不得提交 App Store Connect |

## 6. 外部后台证据不能互相替代

- 不能用后台截图替代真机截图。
- 不能用真机截图替代短信服务商、微信开放平台、OBS、APP 备案或 App Store Connect 后台 proof。
- 外部后台证据按以下文件归档，不占用 RD 编号：
  - `03-app-filing.png` 或 `.pdf`
  - `07-sms-provider.png`
  - `08-wechat-open-platform.png`
  - `08b-wechat-universal-link-aasa.png`
  - `09-obs-policy.png`（OBS / 对象存储）
  - `17-age-rating-result.png` 或 `.pdf`

## 7. 填回正式文件

把本执行单结果填入 `12-real-device-regression.md`。必须全部改为“通过”，并写明：

- 灵动岛紧凑态结论：无裁剪、边缘完整、未右移或未压到岛中心。
- 灵动岛展开态结论：无裁剪、未贴边、文字和数字未被吞。
- 锁屏通知栈结论：上下相邻通知不遮挡提醒卡片。
- 锁屏小组件结论：无裁剪、无溢出、不展示隐私照片。
- 桌面小组件结论：无裁剪、无溢出、不展示隐私照片。
- Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔。
- 手动顺延只改变下一次提醒时间，不新增持久化字段，不根据奶量、月龄、传感器或健康数据自动推算。
- 小组件只读展示本机今日摘要。
- Apple Watch 只作为系统镜像通知，不承诺独立 Watch App。

同时从 `RealDevice/REAL-DEVICE-CAPTURE-RESULT.template.json` 复制生成 `RealDevice/REAL-DEVICE-CAPTURE-RESULT.json`。结果文件必须填写 `status: captured-live-real-device`、`iOS 26.5`、`TestFlight` 或 `Xcode 签名真机包`、`sameBuildAsSignedArchiveAndTestFlight`、`canSubmitAtCapture`、`redactionReviewed`、`rdResults.feedingReminderDeferral`、`rdResults.login`、`rdResults.accountDelete`、`rdResults.notificationPermission`、`rdResults.dynamicIsland.visualQA`、`rdResults.lockScreen.visualQA` 和 `rdResults.homeWidget.visualQA`。模板不是证据；只要结构化结果没有填完，就不能把 RD-03、RD-22、RD-23 或任何登录/账号删除/通知权限截图当作最终提交证据。

## 8. 拍完后立刻跑

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-30 --output Backend/proof/app-store-evidence-20260630T-current.json
python3 Backend/scripts/check_testflight_regression_plan.py --output Backend/proof/testflight-regression-plan.json --allow-incomplete
python3 Backend/scripts/check_production_readiness.py --allow-incomplete --output Backend/proof/production-readiness-20260630T-current.json
```
