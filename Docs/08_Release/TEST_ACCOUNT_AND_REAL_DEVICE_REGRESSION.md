# TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 日期：2026-06-26
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

1. 登录路径：打开 App -> 设置 -> 账号与备份 -> 恢复密钥登录。
2. 恢复密钥：读取本机 `.env.xnp-review-account` 中的 `XNP_REVIEW_RECOVERY_KEY`。
3. 说明：该账号只含虚构宝宝资料，不含真实宝宝照片或家庭资料。
4. 手机号和微信测试信息：待短信和微信真实配置完成后补充。

### 审核员核心测试路径

1. 冷启动 App，进入“今日”页确认示例为空状态和快速记录入口可见。
2. 在“记录”页新增一条喂养、睡眠或排便记录，回到首页确认今日摘要更新。
3. 在“成长”页新增身高体重记录，确认趋势页可打开。
4. 在“资料 -> 账号与备份 -> 恢复密钥登录”使用 App Review Information 中的恢复密钥登录。
5. 触发“立即备份”，再使用恢复路径确认虚构测试数据可恢复。
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

### 当前本机真机可用性

| 设备 | 系统 | 状态 | 本轮处理 |
|---|---|---|---|
| 蓝蓝 / iPhone 16 Pro Max | iOS 26.5 | unavailable | 符合版本但当前不可用，未测试 |
| 面面 / iPhone 16 Plus | iOS 27.0 | available (paired) | 不符合本项目 iOS 26.5 本机测试规则，未测试 |

机器证据：`Backend/proof/ios265-device-availability.json`。该证据只证明本机设备版本策略已检查，不替代 TestFlight / 签名真机回归。

## 本机 iOS 26.5 烟测证据

| 项目 | 结果 |
|---|---|
| Release 模拟器包 | `/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app` |
| 设备 | iPhone 17 Pro / iOS 26.5 |
| 安装 | 通过 |
| 启动 | 通过，输出 `com.mewpow.xiaonaiping: 92544` |
| 证据 | `Backend/proof/sim-launch-ios265-20260626.json` |
| 注意 | 该证据只证明本机 iOS 26.5 安装启动，不替代 TestFlight / 签名真机回归 |

## 必测用例

| 编号 | 用例 | 期望 | 结果 |
|---|---|---|---|
| RD-01 | 冷启动进入首页 | 不崩溃，首页可见 | 待测 |
| RD-02 | 创建宝宝档案 | 本地保存成功，重启后仍存在 | 待测 |
| RD-03 | 记录喂养 | 首页今日摘要和最近记录更新 | 待测 |
| RD-04 | 记录睡眠 | 睡眠记录可保存、可回看 | 待测 |
| RD-05 | 记录排便 | 排便记录可保存、可回看 | 待测 |
| RD-06 | 成长记录 | 身高体重可保存，成长页可见 | 待测 |
| RD-07 | 疫苗模板切换 | 中国大陆 / 香港模板可切换；文案不构成医疗建议 | 待测 |
| RD-08 | 相册权限拒绝 | 拒绝权限后 App 不崩溃，有可理解状态 | 待测 |
| RD-09 | 相册权限允许 | 可主动加入照片；不自动扫描系统相册 | 待测 |
| RD-10 | 恢复密钥账号登录 | 可用测试恢复密钥连接账号 | 待测 |
| RD-11 | 云备份 | 备份成功，服务端无真实宝宝照片或手机号明文证据外泄 | 待测 |
| RD-12 | 云恢复 | 清空/换装后可恢复测试数据 | 待测 |
| RD-13 | 手机号登录 | 真实验证码可发送、可校验、频控正常 | 待真实短信配置 |
| RD-14 | 微信登录 | 可拉起微信授权并回到 App | 待微信开放平台配置 |
| RD-15 | 删除云端账号与备份 | 云端备份、照片对象、账号失效 | 待测 |
| RD-16 | 断网保存 | 本地记录可保存；云操作给出失败状态 | 待测 |
| RD-17 | 通知权限 | 喂养提醒权限请求、提醒创建、关闭均正常 | 待测 |
| RD-18 | Apple Watch 镜像通知 | iPhone 本地通知可按系统设置镜像到 Apple Watch | 待测 |
| RD-19 | 隐私政策/用户协议/支持 URL | App Store Connect URL 可打开，无 404 | 待测 |
| RD-20 | 崩溃/日志脱敏 | 不输出宝宝内容、照片对象 key、手机号明文 | 待测 |
| RD-21 | Release 包体自检 | `ios-app-bundle.json` 不含内部文档、本地地址、debug 文案或 API key 标记 | 当前通过；微信配置仍阻断 |
| RD-22 | 灵动岛喝奶提醒开关 | 开关打开后仅在保存喝奶闹钟时展示下一次喝奶时间和固定间隔；关闭后结束 Live Activity | 待测 |
| RD-23 | 锁屏/桌面小组件 | 只读展示本机今日摘要、下一次喝奶提醒、进行中睡眠等，不展示照片原图、备注、token 或云端对象 key | 待测 |
| RD-24 | 审核边界文案 | App 内和审核说明明确灵动岛/Live Activity/小组件只是状态展示，不暗示 HealthKit、传感器、健康建议、压力评估、压力提醒、心理健康判断、医疗诊断或喂养建议 | 待测 |

## 通过标准

1. RD-01 到 RD-12、RD-15 到 RD-24 必须通过。
2. RD-13 和 RD-14 必须在真实短信和微信配置完成后通过；不能用 debug code 代替。
3. 每轮真机回归必须附截图或录屏证据；同时填写 `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md`，并把核心项勾选为完成。
4. 每个 RD 用例的证据路径必须指向 `Docs/08_Release/AppStoreEvidence/` 内真实存在的非空文件，不能填写桌面、下载目录、微信临时目录或其他绝对路径。
5. `12-real-device-regression.md` 的“审核边界确认”必须全部勾选，尤其是 Live Activity / 小组件只做状态展示、只反映用户主动记录数据、不生成健康建议/压力提醒/喂养建议/医疗判断、无 HealthKit/传感器/医院系统/第三方健康数据源。
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
| RD-11 云备份 | `RealDevice/RD-11-cloud-backup.png` |
| RD-12 云恢复 | `RealDevice/RD-12-cloud-restore.png` |
| RD-13 手机号登录 | `RealDevice/RD-13-phone-login.png` |
| RD-14 微信登录 | `RealDevice/RD-14-wechat-login.png` |
| RD-15 删除云端账号与备份 | `RealDevice/RD-15-account-delete.png` |
| RD-16 断网保存 | `RealDevice/RD-16-offline-save.png` |
| RD-17 通知权限 | `RealDevice/RD-17-notification-permission.png` |
| RD-18 Apple Watch 镜像通知 | `RealDevice/RD-18-watch-mirror.png` |
| RD-19 隐私政策/用户协议/支持 URL | `RealDevice/RD-19-public-urls.png` |
| RD-20 崩溃/日志脱敏 | `RealDevice/RD-20-diagnostics-redaction.png` |
| RD-21 Release 包体自检 | `RealDevice/RD-21-release-bundle.png` |
| RD-22 灵动岛喝奶提醒开关 | `RealDevice/RD-22-live-activity-switch.png` |
| RD-23 锁屏/桌面小组件 | `RealDevice/RD-23-widget-summary.png` |
| RD-24 审核边界文案 | `RealDevice/RD-24-review-boundary.png` |
