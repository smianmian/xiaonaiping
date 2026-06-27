# 12-real-device-regression.md Template

> 复制本文件为 `12-real-device-regression.md` 后再填写，并删除本模板提示。不要把恢复密钥、验证码、完整手机号、token、真实宝宝照片或对象存储 key 写进来。
> 本项目真机回归只接受 iOS 26.5；iOS 27.0 不能作为本项目真机回归证据。

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
- 桌面小组件结论：

> 视觉结论不能只写“正常”。紧凑态要写无裁剪、边缘完整、未右移或未压到岛中心；展开态要写无裁剪、未贴边或未被吞；锁屏通知栈要写不遮挡；桌面小组件要写无裁剪、无溢出或不展示隐私照片。

## 必填勾选

- [ ] iOS 26.5
- [ ] 冷启动
- [ ] 手机号登录
- [ ] 微信登录
- [ ] 恢复密钥登录
- [ ] 云备份
- [ ] 云恢复
- [ ] 账号删除
- [ ] 通知权限
- [ ] 灵动岛喝奶提醒开关
- [ ] 灵动岛紧凑态头像和进度环未压到岛中心
- [ ] 灵动岛展开态文字和数字未贴边或被吞
- [ ] 锁屏通知栈上下相邻通知不遮挡提醒卡片
- [ ] 锁屏/桌面小组件
- [ ] 桌面小组件内容不裁剪不展示隐私照片
- [ ] 审核边界文案

## RD-01 到 RD-24 结果

> 最终提交前每一行都必须改成“通过”，并填写截图或录屏文件路径；路径必须指向 `Docs/08_Release/AppStoreEvidence/` 内真实存在且不低于 10KB 的 `.png`、`.jpg`、`.jpeg`、`.mp4`、`.mov` 或 `.pdf` 文件，不能只写目录，也不能写桌面、下载目录、微信临时目录或其他绝对路径。建议放在 `RealDevice/` 子目录。不能保留“待测”“待真实短信配置”或“待微信开放平台配置”。安装方式只能填写 `TestFlight` 或 `Xcode 签名真机包` 其中一个，不要保留斜杠选项。
> `RD-17`、`RD-18`、`RD-22`、`RD-23`、`RD-24` 必须使用各自独立的证据文件，不能复用 `RealDevice/00-overview.png` 或同一份泛证据。`RD-17` 文件名必须体现通知或权限；`RD-18` 文件名必须同时体现 watch 和 mirror / notification；`RD-22` 文件名必须同时体现 live-activity / dynamic-island / 灵动岛 和 switch / toggle / 开关；`RD-23` 文件名必须同时体现 widget / 小组件 和 lock-screen / 锁屏。

| 编号 | 结果 | 证据/备注 |
|---|---|---|
| RD-01 冷启动进入首页 | 待测 | RealDevice/RD-01-cold-start.png |
| RD-02 创建宝宝档案 | 待测 | RealDevice/RD-02-baby-profile.png |
| RD-03 记录喂养 | 待测 | RealDevice/RD-03-feeding-record.png |
| RD-04 记录睡眠 | 待测 | RealDevice/RD-04-sleep-record.png |
| RD-05 记录排便 | 待测 | RealDevice/RD-05-diaper-record.png |
| RD-06 成长记录 | 待测 | RealDevice/RD-06-growth-record.png |
| RD-07 疫苗模板切换 | 待测 | RealDevice/RD-07-vaccine-template.png |
| RD-08 相册权限拒绝 | 待测 | RealDevice/RD-08-photo-denied.png |
| RD-09 相册权限允许 | 待测 | RealDevice/RD-09-photo-allowed.png |
| RD-10 恢复密钥账号登录 | 待测 | RealDevice/RD-10-recovery-login.png |
| RD-11 云备份 | 待测 | RealDevice/RD-11-cloud-backup.png |
| RD-12 云恢复 | 待测 | RealDevice/RD-12-cloud-restore.png |
| RD-13 手机号登录 | 待真实短信配置 | RealDevice/RD-13-phone-login.png |
| RD-14 微信登录 | 待微信开放平台配置 | RealDevice/RD-14-wechat-login.png |
| RD-15 删除云端账号与备份 | 待测 | RealDevice/RD-15-account-delete.png |
| RD-16 断网保存 | 待测 | RealDevice/RD-16-offline-save.png |
| RD-17 通知权限 | 待测 | RealDevice/RD-17-notification-permission.png |
| RD-18 Apple Watch 镜像通知 | 待测 | RealDevice/RD-18-watch-mirror.png |
| RD-19 隐私政策/用户协议/支持 URL | 待测 | RealDevice/RD-19-public-urls.png |
| RD-20 崩溃/日志脱敏 | 待测 | RealDevice/RD-20-diagnostics-redaction.png |
| RD-21 Release 包体自检 | 待测 | RealDevice/RD-21-release-bundle.png |
| RD-22 灵动岛喝奶提醒开关 | 待测 | RealDevice/RD-22-live-activity-switch.png |
| RD-23 锁屏/桌面小组件 | 待测 | RealDevice/RD-23-lock-screen-widget-summary.png |
| RD-24 审核边界文案 | 待测 | RealDevice/RD-24-review-boundary.png |

## 审核边界确认

- [ ] Live Activity 只展示用户设置的下一次喝奶提醒和固定间隔。
- [ ] 小组件只读展示本机今日摘要，不展示照片原图、备注、token 或对象 key。
- [ ] Apple Watch 只作为系统镜像通知，不在 App Store 文案中承诺 Watch App。
- [ ] 状态展示只反映用户主动记录的数据。
- [ ] 不生成健康建议、压力提醒、喂养建议或医疗判断。
- [ ] 不接入 HealthKit、传感器、医院系统或第三方健康数据源。
- [ ] 不提供压力评估、心理健康判断、医疗诊断、治疗建议或专业疫苗建议。
