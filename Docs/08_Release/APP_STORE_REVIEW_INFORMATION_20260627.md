# 小奶瓶 App Review Information 私密字段包

日期：2026-06-27

状态：用于 App Store Connect 的 App Review Information 区块。该区块不展示给用户，但仍不得写入仓库中的真实恢复密钥、完整手机号、验证码、Apple ID 邮箱、联系人完整电话、token、AppSecret 或其他密钥。

## 官方核对入口

1. App Review 信息说明：https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information/
2. App Review 准备说明：https://developer.apple.com/distribute/app-review/

## Contact Information

在 App Store Connect 私密字段填写，由公司确认后再填；不要写入仓库：

| 字段 | 填写要求 | 仓库状态 |
|---|---|---|
| First Name / Last Name | 使用公司指定审核联系人 | 不写入仓库 |
| Email | 使用公司指定审核联系邮箱 | 不写入仓库 |
| Phone Number | 使用公司指定可接通电话 | 不写入仓库 |

## Sign-In Information

当前审核主路径使用恢复密钥测试账号。真实值只从本机 ignored 文件 `.env.xnp-review-account` 读取，只能填入 App Store Connect 的 App Review Information 私密字段。

| 字段 | 填写口径 |
|---|---|
| Sign-in required | Yes |
| Username | `review-recovery-key-account`，仅作为账号标签；App 内实际使用恢复密钥登录 |
| Password | 粘贴 `.env.xnp-review-account` 中的 `XNP_REVIEW_RECOVERY_KEY`，不得写入仓库 |
| Additional demo accounts | 手机号测试号和微信测试号必须等真实短信服务商和微信开放平台配置完成后再补 |

## 审核测试账号脱敏证据一致性锁

`Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json` 只保存可审核的脱敏状态，不保存恢复密钥本身。提交前必须能从该 JSON 反向核对 App Review Information 的 Sign-In Information：

| JSON 字段 | 必须值或要求 |
|---|---|
| `accountId` | 非空；仅用于证明测试账号已创建 |
| `baseUrl` | `https://api.mewpow.com/xiaonaiping` |
| `recoveryKeyStored` | `.env.xnp-review-account` |
| `recoveryVerified` | `true` |
| `syncSeeded` | `true` |
| `containsSecret` | `false` |

- [ ] Username 仍使用 `review-recovery-key-account`，不要写真实恢复密钥。
- [ ] Password 只从 `.env.xnp-review-account` 的 `XNP_REVIEW_RECOVERY_KEY` 复制到 App Store Connect 私密字段。
- [ ] 重新生成测试账号证据后，必须重跑 `check_app_store_evidence.py --allow-incomplete` 和 `check_app_store_connect_materials.py`。
- [ ] JSON 不得新增 `secret`、`token`、`password`、`code` 字段，不得包含恢复密钥、验证码、bearer 凭证、完整手机号或 API key。

## Notes 可粘贴文本

```text
请使用恢复密钥测试账号审核：

1. 打开 App -> 资料 -> 账号与同步 -> 恢复密钥登录。
2. 使用本 App Review Information 的 Sign-In Information 中提供的恢复密钥登录。
3. 该账号只包含虚构宝宝资料和虚构记录，不含真实宝宝照片或真实家庭资料。
4. 登录后可测试立即同步、云端恢复和删除云端账号与同步。
5. 手机号登录和微信登录会在真实短信服务商、微信开放平台、Release 包 `wx...` URL Scheme、Universal Link 和相关人工证据全部完成后补充测试号；正式提交包不得依赖 debug code。
6. 灵动岛、锁屏 Live Activity 和小组件仅展示用户设置或用户主动记录的状态，不生成健康建议、压力提醒、喂养建议或医疗判断。若已设置固定喝奶间隔，新增喂养时的顺延选项为不顺延或 +5、+10、+15、+20、+25、+30 分钟；下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排，本顿无喂养时长时按本顿发生时间计算。
```

## 需要随提交归档或核对的证据

| 证据 | 路径 | 状态 |
|---|---|---|
| 审核测试账号脱敏证明 | `Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json` | 已有 |
| 真机/TestFlight 回归记录 | `Docs/08_Release/AppStoreEvidence/12-real-device-regression.md` | 待 iOS 26.5 TestFlight 或签名真机包完成 |
| 签名归档截图 | `Docs/08_Release/AppStoreEvidence/05-signed-archive.png` | 待 D-U-N-S / Apple Developer / Archive 完成 |
| TestFlight 截图 | `Docs/08_Release/AppStoreEvidence/06-testflight.png` | 待 TestFlight 构建处理完成 |
| 短信服务商截图 | `Docs/08_Release/AppStoreEvidence/07-sms-provider.png` | 待真实服务商后台完成 |
| 微信开放平台截图 | `Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png` | 待真实开放平台配置完成 |

## 不得填写或提交

1. 不得把恢复密钥写入 Review Notes 文案源文件、截图、录屏、Markdown 或 JSON proof。
2. 不得提供 debug code、`debug_wechat_*`、本地 API、`127.0.0.1`、`localhost` 或 internal dashboard。
3. 不得提供完整手机号、验证码、联系人完整电话、Apple ID 邮箱、token、API key、AppSecret 或对象存储 key。
4. 不得声称手机号登录、微信登录、TestFlight、备案或 App Store 人工证据已完成，除非对应 proof 和 `AppStoreEvidence/` 文件已归档。
5. 不得把灵动岛、锁屏 Live Activity、小组件或喝奶提醒描述成健康建议、喂养建议、压力提醒、心理健康判断或医疗诊断。
