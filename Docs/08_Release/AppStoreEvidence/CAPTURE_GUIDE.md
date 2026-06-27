# App Store Evidence Capture Guide

## 使用规则

本目录只归档真实提交证据。占位、待办、模板或聊天记录不要命名成 `01-...` 到 `09-...`，否则容易混入发布包。`check_app_store_evidence.py` 对 `01-...` 到 `09-...` 只接受 `.png`、`.jpg`、`.jpeg`、`.pdf`、`.json` 作为人工证据，普通人工证据和 RD 真机证据文件都必须至少 10KB，截图建议统一使用 `.png`。真机回归使用 `12-real-device-regression.md`，且必须勾选核心真机项；RD-01 到 RD-24 的状态列必须全部等于“通过”，不能保留“待测”“失败”“跳过”或其他状态。

## 通用脱敏

保留能证明审核状态的字段，遮掉无关个人或密钥信息：

1. 遮邮箱、手机号、证件号、付款资料、验证码、恢复密钥、session token、AK/SK、AppSecret。
2. 保留 App 名称、Bundle ID、版本号、构建号、状态、地区、URL、服务商名称和必要配置项。
3. 不使用真实宝宝照片、真实家庭资料、完整手机号或未授权头像。
4. 不保存后台入口、internal dashboard、服务器私有路径或对象存储完整 key。

## 采集清单

| 文件 | 必须能证明 | 保留字段 | 必须遮挡 |
|---|---|---|---|
| `01-company-account.png` | App Store Connect 账号主体为深圳市闪现生活科技有限公司 | 团队/法律主体名称、账号页标题 | 邮箱、电话、付款信息 |
| `02-mainland-availability.png` | 首发只选 China mainland / 中国大陆 | App 名称、可售地区选择状态 | 无关账号信息 |
| `03-app-filing.pdf` 或 `.png` | App 备案/ICP/适用判断进度或结果 | App 名称、主体、备案号或提交状态 | 遮个人证件细节、证件号、联系人完整电话 |
| `04-privacy-label.png` 或 `.pdf` | App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写 | 已采集类别、未追踪、用途 | 账号邮箱 |
| `05-signed-archive.png` | App Store Distribution archive 成功 | Bundle ID、版本、build、archive success / uploaded status | Apple ID 邮箱 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试 | Build 号、版本、处理状态、测试状态 | 测试员邮箱 |
| `07-sms-provider.png` | 真实短信签名、模板和发送成功 | 服务商、签名、模板 ID/名称、发送成功状态 | AccessKey、Secret、完整手机号、验证码 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置完成 | AppID、Bundle ID、URL Scheme、Universal Link | AppSecret、管理员账号 |
| `09-obs-policy.png` | OBS bucket 私有访问、加密、生命周期、删除验证 | bucket/prefix、区域、加密/生命周期/删除策略状态 | AK/SK、完整对象 key |
| `10-final-screenshots/*.png` | 最终 App Store 截图 | 必须包含 `01-home-iphone16pro.png` 到 `05-profile-backup-iphone16pro.png` 这五张上传顺序图，尺寸通过 `app-store-assets.json` | 真实宝宝照片、手机号、debug 文案 |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归结论 | 设备、iOS 26.5、build、安装方式 `TestFlight` 或 `Xcode 签名真机包`、证据截图/录屏路径、灵动岛紧凑态/展开态、锁屏通知栈、桌面小组件视觉结论、RD-01 到 RD-24 全部通过、账号/通知/灵动岛/小组件/审核边界核心项 `- [x]` 勾选 | 恢复密钥、验证码、完整手机号、token、debug code |

`12-real-device-regression.md` 中每个真机回归项的证据截图/录屏路径必须填写，路径必须指向 `.png`、`.jpg`、`.jpeg`、`.mp4`、`.mov` 或 `.pdf` 文件，不能只写目录。每个路径都必须是 `Docs/08_Release/AppStoreEvidence/` 内真实存在且不低于 10KB 的文件；不要填写桌面、下载目录、微信临时目录或其他绝对路径。建议把真机截图和录屏放在 `Docs/08_Release/AppStoreEvidence/RealDevice/` 后再填写相对路径，例如 `RealDevice/RD-01-cold-launch.png`。

灵动岛和锁屏证据要按视觉边界拍：紧凑态要能看出图标和进度环没有右移压到岛中心；展开态要能看出文字、数字和边缘留白没有被吞；锁屏要在有上下相邻通知的通知栈里证明提醒卡片不被遮挡；桌面小组件要证明小尺寸和中尺寸都没有裁剪、没有展示隐私照片。`12-real-device-regression.md` 的视觉结论不能只写“正常”，必须明确写“无裁剪 / 边缘完整 / 未右移压到岛中心 / 未贴边或未被吞 / 不遮挡 / 无溢出 / 不展示隐私照片”等机器可查结论。

RD-17、RD-18、RD-22、RD-23、RD-24 不能复用总览图。文件名也必须能识别场景：RD-17 要体现 notification / permission / 通知 / 权限；RD-18 要同时体现 watch 和 mirror / notification；RD-22 要同时体现 live-activity / dynamic-island / 灵动岛 和 switch / toggle / 开关；RD-23 要同时体现 widget / 小组件 和 lock-screen / 锁屏；RD-24 要体现 review / boundary / 审核 / 边界。

## 采集后必跑

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --output Backend/proof/app-store-evidence-20260627T-current.json
Backend/scripts/run_launch_readiness.sh \
  --deployment-proof Backend/proof/huawei-baota-deploy-20260625T080412Z.json \
  --storage-proof Backend/proof/storage-backend-20260625T080039Z.json \
  --app-path /private/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app \
  --ios-simulator-log Backend/proof/xcodebuild-release-ios265-20260627-sim-current.log \
  --ios-device-log Backend/proof/xcodebuild-release-ios265-20260627-device-current.log \
  --base-url https://api.mewpow.com/xiaonaiping
```

如果 `app-store-evidence-20260627T-current.json` 仍有 `missingEvidence`，不能提交 App Store。
