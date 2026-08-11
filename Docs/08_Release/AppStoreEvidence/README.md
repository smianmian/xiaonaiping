# AppStoreEvidence

把全球 App Store 同轮提交证据放在本目录。文件不能包含密码、token、AK/SK、完整手机号、真实宝宝照片或未授权家庭资料。

详细采集要求见 `CAPTURE_GUIDE.md`。占位、待办、模板或 Markdown 文件不能冒充人工证据；模板统一放在 `_templates/` 或 `.template.*` 文件中。仓库不保存任何登录凭据、完整手机号、验证码、微信凭据或 token；认证证据只证明签名包展示并完成当前手机号验证码/微信生产流程。真机回归只能在签名 iOS 26.5 真机或 TestFlight 设备完成后，复制 `12-real-device-regression.template.md` 为 `12-real-device-regression.md`；登录、自动云同步、换机恢复、账号删除及每项 UI 证据均须来自同一 build。模板和待办状态不是完成证据，也不是提交许可。

需要的文件名和脱敏要求见 `CAPTURE_GUIDE.md`。自动门禁只覆盖可机器核对的部分，人工证据仍须逐项确认；可运行：

```bash
python3 Backend/scripts/check_app_store_assets.py --allow-incomplete
python3 Backend/scripts/check_review_notes.py --allow-incomplete
python3 Backend/scripts/check_production_readiness.py --allow-incomplete
```

## 当前已有

- `10-final-screenshots/`：当前 iPhone 17 Pro Max / iOS 26.5 Debug simulator / iPhone 6.9" display 候选截图；`PROVENANCE.json` 证明候选来源，但不替代 TestFlight、签名真机或 Release build 最终证据。最终上传前按 `10-final-screenshots/UPLOAD_PROVENANCE.template.json` 填写并另存为 `UPLOAD_PROVENANCE.json`，证明 `final-app-store-upload`、`iPhone 6.9" display`、iOS 26.5、`TestFlight` 或 `Xcode 签名真机包`、同一版本/build 和五张上传顺序图一致。
- `_templates/sms-provider-evidence.template.json`：短信服务商签名、验证码模板、真实实发和脱敏清单；它不是人工证据，不能改名成 `07-sms-provider.*`。
- `_templates/obs-policy-evidence.template.json`：华为 OBS 私有访问、加密/生命周期/删除验证和脱敏清单；它不是人工证据，不能改名成 `09-obs-policy.*`。
- `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md`：D-U-N-S 交付后继续 Apple Developer 企业注册、确认 Team ID、配证书、Archive 和 TestFlight 的动作清单；它不是 App Store 人工证据，不替代 `01-company-account.png`、`05-signed-archive.png` 或 `06-testflight.png`。

## 仍需补齐

| 文件名 | 证明什么 | 脱敏要求 | 当前状态 |
| --- | --- | --- | --- |
| `01-company-account.png` | App Store Connect 主体为深圳市闪现生活科技有限公司，且 D-U-N-S 后 Apple Developer Organization / Team ID 已确认 | 遮邮箱、电话、付款信息、D-U-N-S 编码完整值 | 未完成 |
| `02-mainland-availability.png` | 只选择 China mainland 首发 | 不展示无关账号信息 | 未完成 |
| `03-app-filing.pdf` 或 `03-app-filing.png` | 中国大陆 APP 备案或适用判断 | 遮个人证件细节；按当前备案状态现场重新取证 | 未完成 |
| `04-privacy-label.png` | App Privacy 已按 `APP_STORE_PRIVACY_LABEL.json` 填写 | 不展示账号隐私信息；按当前 App Privacy 填写结果现场重新取证 | 未完成 |
| `17-age-rating-result.png` 或 `17-age-rating-result.pdf` | App Store Connect 年龄分级结果已按答案表完成 | 遮 Apple ID 邮箱、电话、付款信息；按当前年龄分级结果现场重新取证 | 未完成 |
| `05-signed-archive.png` | App Store Distribution Archive 成功 | 可见 bundle id、版本和 archive 成功；按当前签名构建现场重新取证 | 未完成 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试 | 可见构建号和状态；按当前 TestFlight 构建现场重新取证 | 未完成 |
| `07-sms-provider.png` | 真实短信服务商、签名、账号登录/验证验证码模板、模板审核状态、发送区域和发送成功；模板不含营销、不含医疗、不含育儿建议 | 手机号中段打码，隐藏密钥；截图前可参考 `_templates/sms-provider-evidence.template.json`，但模板本身不是证据 | 未完成 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置 | 可见 AppID、Bundle ID、URL Scheme / Universal Link；隐藏 AppSecret；按当前微信登录配置现场重新取证 | 未完成 |
| `08b-wechat-universal-link-aasa.png` 或 `.pdf` | 微信 Universal Link / AASA / Associated Domains 同轮核对 | 可见 AASA endpoint、Team ID、Bundle ID、Associated Domains、微信 Universal Link；遮 Apple ID 邮箱、完整手机号、AppSecret | 未完成 |
| `09-obs-policy.png` | 华为 OBS bucket、生命周期、加密、删除策略 | 隐藏 AK/SK 和完整对象路径；截图前可参考 `_templates/obs-policy-evidence.template.json`，但模板本身不是证据 | 未完成 |
| `10-final-screenshots/*.png` + `10-final-screenshots/UPLOAD_PROVENANCE.json` | 最终 App Store 截图 | 必须包含五张上传顺序图；截图必须为 iPhone 6.9" display 可上传尺寸；先用 `UPLOAD_PROVENANCE.template.json` 填写同一版本/build、安装来源和脱敏检查，再另存为 `UPLOAD_PROVENANCE.json`；最终 JSON 必须证明 `final-app-store-upload`、iOS 26.5、`TestFlight` 或 `Xcode 签名真机包`；尺寸和 provenance 通过 `app-store-assets.json` | 已有 iOS 26.5 候选，缺最终上传 provenance |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归 | 不保存完整手机号、验证码、微信凭证或宝宝真实照片 | 未完成 |

### D-U-N-S 后 Apple Developer 归档证据

这些文件只在 D-U-N-S 交付并继续完成 Apple Developer Organization enrollment 后归档，不作为当前已完成证据：

| 文件名 | 证明什么 | 脱敏要求 | 当前状态 |
| --- | --- | --- | --- |
| `AppleDeveloper/13-organization-team-id.png` | Apple Developer 组织页确认深圳市闪现生活科技有限公司、Membership 和 Team ID | 遮 Apple ID 邮箱、联系人电话、付款信息、D-U-N-S 编码完整值；按当前组织状态现场重新取证 | 未完成 |
| `AppleDeveloper/14-bundle-id-capabilities.png` | Bundle ID / Identifier 页确认 `com.mewpow.xiaonaiping`、App Groups、Associated Domains 归属当前组织 Team | 遮无关 App、人员信息；按当前 Bundle ID 配置现场重新取证 | 未完成 |
| `AppleDeveloper/15-distribution-certificate-profile.png` | App Store Distribution 证书 / Profile 可用于 `com.mewpow.xiaonaiping` Archive | 遮证书私钥、下载链接、个人邮箱；按当前证书与 Profile 状态现场重新取证 | 未完成 |
| `AppleDeveloper/16-account-roles-access.png` | 账号权限 / Roles and Access 确认当前 Apple ID 有 Certificates, Identifiers & Profiles、App 管理权限、构建上传权限、TestFlight 管理权限和提交审核权限 | 遮 Apple ID 邮箱、联系人完整电话、付款信息、无关成员；按当前账号权限现场重新取证 | 未完成 |

## 真机回归必须覆盖

1. 启动：iOS 26.5 签名包或 TestFlight 冷启动不崩溃。
2. 手机号登录：真实验证码可收、可登录。
3. 微信登录：微信授权可拉起并回到 App，登录态正确。
4. 当前认证入口：签名包只展示并完成手机号验证码或微信授权，不出现历史认证入口、静态账号或 debug code。
5. 云同步：宝宝记录和主动加入 App 的照片可上传。
6. 云恢复：换设备或重装后可恢复。
7. 账号删除：删除云端账号与同步后旧 token 失效。
8. 通知权限：授权、拒绝、设置入口都可理解。
9. 灵动岛喝奶提醒开关：开启只展示下一次喝奶提醒和固定间隔，关闭会结束 Live Activity。
10. 灵动岛视觉边界：紧凑态头像和进度环不右移压到岛中心，展开态文字和数字不贴边、不被吞；机器检查要求视觉结论中出现这些明确结果。
11. 锁屏通知栈：有上下相邻通知时提醒卡片不被遮挡。
12. 锁屏小组件和桌面小组件：只读展示本机今日摘要，不展示照片原图、备注、token 或对象 key；锁屏小组件内容不裁剪不展示隐私照片，桌面小组件内容不裁剪不展示隐私照片。
13. Apple Watch：只验证系统镜像通知，不在 App Store 文案中承诺 Watch App。
14. 通知权限：分别记录允许、拒绝后状态和去系统设置入口是否可理解；不能只写“通知正常”。
15. 登录和删除：当前认证入口、手机号登录、微信登录、账号删除必须分别使用独立证据文件，不能复用总览图或同一份泛证据。
16. 审核边界文案：不暗示 HealthKit、传感器、压力评估、心理健康判断、医疗诊断或喂养建议。
17. RD-01 到 RD-24 的状态列必须全部填写为“通过”，不保留“待测”“待填”“待真实”“失败”“跳过”等状态。
18. 安装方式必须明确二选一：`TestFlight` 或 `Xcode 签名真机包`。
19. RD-01 到 RD-24 每一行的证据/备注必须填写截图或录屏文件路径，路径必须以 `.png`、`.jpg`、`.jpeg`、`.mp4`、`.mov` 或 `.pdf` 结尾，不能只写目录。
20. RD-01 到 RD-24 每一行的证据文件必须真实存在、单个文件不低于 10KB，并且路径必须留在 `Docs/08_Release/AppStoreEvidence/` 目录内；不要填写桌面、下载目录、微信临时目录或其他绝对路径。
21. 证据截图/录屏路径不能包含完整手机号、验证码、微信凭证、token、debug code 或真实宝宝照片。
22. `12-real-device-regression.md` 的“审核边界确认”必须全部勾选；机器会检查 Live Activity / 小组件只做状态展示、只反映用户主动记录数据、不生成健康建议/压力提醒/喂养建议/医疗判断、无 HealthKit/传感器/医院系统/第三方健康数据源。

## 最终截图命名

`10-final-screenshots/` 必须包含以下五张上传顺序图，不能用任意 5 张图替代：

1. `01-home-iphone16pro.png`
2. `02-record-iphone16pro.png`
3. `03-growth-iphone16pro.png`
4. `04-profile-iphone16pro.png`
5. `05-profile-sync-iphone16pro.png`

`UPLOAD_PROVENANCE.json` 也必须同目录存在，并写明 `evidenceType` 为 `final-app-store-upload`、`appStoreDeviceSlot` 为 `iPhone 6.9" display`、安装来源为 `TestFlight` 或 `Xcode 签名真机包`。填写时先复制 `UPLOAD_PROVENANCE.template.json`，把版本、build、设备和安装来源改为同一轮 TestFlight 或签名真机证据。只有 `PROVENANCE.json` 的 Debug simulator 候选来源时，不能把最终截图标为完成。

## 截图禁区

1. 不使用真实宝宝照片，除非另有明确授权。
2. 不展示完整手机号、验证码、微信凭证、token、账号 ID、对象存储 key 或内部路径。
3. 不展示 `127.0.0.1`、debug code、internal dashboard 或工程文档。
4. 不写医疗诊断、治疗、疫苗建议、医生替代或专业健康结论。
5. 微信登录未完成开放平台配置前，不截图暗示微信登录已经可用。
