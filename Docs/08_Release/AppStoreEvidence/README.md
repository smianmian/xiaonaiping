# AppStoreEvidence

把中国大陆 App Store 提交证据放在本目录。文件不能包含密码、token、AK/SK、完整手机号、真实宝宝照片或未授权家庭资料。

详细采集要求见 `CAPTURE_GUIDE.md`。占位、待办、模板或 Markdown 文件不能作为 `01-...` 到 `09-...` 人工证据通过 gate；当前检查器只接受 `.png`、`.jpg`、`.jpeg`、`.pdf`、`.json` 这类真实证据文件，普通人工证据和 RD 真机证据文件都必须至少 10KB。文字型证据会扫描恢复密钥、Bearer token、debug 微信 code、API key 和完整手机号，命中会被拒绝。审核测试账号证据必须使用 `11-test-account-redacted.json`，且只能保存脱敏账号状态，不能保存恢复密钥、token、验证码或完整手机号。真机回归是例外：只能在签名 iOS 26.5 真机或 TestFlight 设备跑完后，复制 `12-real-device-regression.template.md` 为 `12-real-device-regression.md`，填完环境、灵动岛紧凑态/展开态、锁屏通知栈和桌面小组件视觉结论，勾选账号、通知、灵动岛、小组件和审核边界核心真机项，并把 RD-01 到 RD-24 全部改成已通过。视觉结论不能只写“正常”，必须明确写出无裁剪、边缘完整、未右移压到岛中心、未贴边或未被吞、不遮挡、无溢出、不展示隐私照片等可复核结论。TestFlight 或签名真机包证据不替代 TestFlight / 签名真机回归清单，本地模拟器证据也不替代 TestFlight / 签名真机回归。

需要的文件名见 `Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md`，也可以运行：

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence-20260627T-current.json
```

## 当前已有

- `10-final-screenshots/`：当前 iPhone 17 Pro / iOS 26.5 Debug simulator 候选截图；`PROVENANCE.json` 证明截图来源，但不替代 TestFlight、签名真机或 Release build 最终证据。
- `11-test-account-redacted.json`：审核测试账号 redacted 证据；恢复密钥只保存在本机忽略文件，不提交到仓库。

## 仍需补齐

| 文件名 | 证明什么 | 脱敏要求 | 当前状态 |
| --- | --- | --- | --- |
| `01-company-account.png` | App Store Connect 主体为深圳市闪现生活科技有限公司 | 遮邮箱、电话、付款信息 | 未完成 |
| `02-mainland-availability.png` | 只选择 China mainland 首发 | 不展示无关账号信息 | 未完成 |
| `03-app-filing.pdf` 或 `03-app-filing.png` | 中国大陆 APP 备案或适用判断 | 遮个人证件细节 | 未完成 |
| `04-privacy-label.png` | App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写 | 不展示账号隐私信息 | 未完成 |
| `05-signed-archive.png` | App Store Distribution Archive 成功 | 可见 bundle id、版本和 archive 成功 | 未完成 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试 | 可见构建号和状态 | 未完成 |
| `07-sms-provider.png` | 真实短信服务商、签名、模板和发送成功 | 手机号中段打码，隐藏密钥 | 未完成 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置 | 可见 AppID、Bundle ID、URL Scheme / Universal Link；隐藏 AppSecret | 未完成 |
| `09-obs-policy.png` | 华为 OBS bucket、生命周期、加密、删除策略 | 隐藏 AK/SK 和完整对象路径 | 未完成 |
| `10-final-screenshots/*.png` | 最终 App Store 截图候选 | 必须包含五张上传顺序图，尺寸和 iOS 26.5 provenance 通过 `app-store-assets.json` | 当前 iOS 26.5 候选已归档 |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归 | 不保存完整手机号、验证码、恢复密钥或宝宝真实照片 | 未完成 |

## 真机回归必须覆盖

1. 启动：iOS 26.5 签名包或 TestFlight 冷启动不崩溃。
2. 手机号登录：真实验证码可收、可登录。
3. 微信登录：微信授权可拉起并回到 App，登录态正确。
4. 恢复密钥登录：审核测试账号可恢复。
5. 云备份：宝宝记录和主动加入 App 的照片可上传。
6. 云恢复：换设备或重装后可恢复。
7. 账号删除：删除云端账号与备份后旧 token 失效。
8. 通知权限：授权、拒绝、设置入口都可理解。
9. 灵动岛喝奶提醒开关：开启只展示下一次喝奶提醒和固定间隔，关闭会结束 Live Activity。
10. 灵动岛视觉边界：紧凑态头像和进度环不右移压到岛中心，展开态文字和数字不贴边、不被吞；机器检查要求视觉结论中出现这些明确结果。
11. 锁屏通知栈：有上下相邻通知时提醒卡片不被遮挡。
12. 锁屏/桌面小组件：只读展示本机今日摘要，不展示照片原图、备注、token 或对象 key，内容不裁剪。
13. Apple Watch：只验证系统镜像通知，不在 App Store 文案中承诺 Watch App。
14. 审核边界文案：不暗示 HealthKit、传感器、压力评估、心理健康判断、医疗诊断或喂养建议。
15. RD-01 到 RD-24 的状态列必须全部填写为“通过”，不保留“待测”“待填”“待真实”“失败”“跳过”等状态。
16. 安装方式必须明确二选一：`TestFlight` 或 `Xcode 签名真机包`。
17. RD-01 到 RD-24 每一行的证据/备注必须填写截图或录屏文件路径，路径必须以 `.png`、`.jpg`、`.jpeg`、`.mp4`、`.mov` 或 `.pdf` 结尾，不能只写目录。
18. RD-01 到 RD-24 每一行的证据文件必须真实存在、单个文件不低于 10KB，并且路径必须留在 `Docs/08_Release/AppStoreEvidence/` 目录内；不要填写桌面、下载目录、微信临时目录或其他绝对路径。
19. 证据截图/录屏路径不能包含完整手机号、恢复密钥、token、debug code 或真实宝宝照片。
20. `12-real-device-regression.md` 的“审核边界确认”必须全部勾选；机器会检查 Live Activity / 小组件只做状态展示、只反映用户主动记录数据、不生成健康建议/压力提醒/喂养建议/医疗判断、无 HealthKit/传感器/医院系统/第三方健康数据源。

## 最终截图命名

`10-final-screenshots/` 必须包含以下五张上传顺序图，不能用任意 5 张图替代：

1. `01-home-iphone16pro.png`
2. `02-record-iphone16pro.png`
3. `03-growth-iphone16pro.png`
4. `04-profile-iphone16pro.png`
5. `05-profile-backup-iphone16pro.png`

## 截图禁区

1. 不使用真实宝宝照片，除非另有明确授权。
2. 不展示完整手机号、恢复密钥、token、账号 ID、对象存储 key 或内部路径。
3. 不展示 `127.0.0.1`、debug code、internal dashboard 或工程文档。
4. 不写医疗诊断、治疗、疫苗建议、医生替代或专业健康结论。
5. 微信登录未完成开放平台配置前，不截图暗示微信登录已经可用。
