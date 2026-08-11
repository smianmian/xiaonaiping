# AUTH_AND_ACCOUNT.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：账号方案更新
- 日期：2026-06-24
- 当前结论：第一版需要账号；手机号登录、阿里云短信 webhook adapter 和微信登录的服务端路径已补齐，iOS 已接入 WechatOpenSDK 授权桥，Release 包已禁止未配置时点击假微信登录；正式上架前仍必须完成阿里云短信签名/模板/RAM 密钥私有配置、微信开放平台 AppID/AppSecret、真实 URL Scheme / Universal Link 后台绑定、隐私政策、App Store 隐私标签和账号删除联动验证

## 已确认事实

1. 第一版支持多宝宝档案和私密家庭协作；每位照护者使用自己的账号。
2. 第一版需要同步恢复。
3. 第一版需要服务器存储照片原图。
4. 第一版需要稳定账号身份。
5. 第一版全球同步首发，不采用地区分批上线。
6. 开发期账号先用当前可用方案；后续开通付费 Apple Developer 账号。

## 合理推断

1. 手机号登录会增加短信服务商、验证码、客服和隐私标签成本。
2. 微信登录会增加微信开放平台配置、SDK/URL Scheme、第三方账号标识和审核材料成本。
3. 有账号就必须有账号删除。
4. 账号只用于私密家庭组成员资格，不应变成公开社交身份系统。

## 待我确认的问题

1. 付费 Apple Developer 账号开通时间。
2. 阿里云短信签名、模板、RAM 子账号和 adapter 私有 env。
3. 微信开放平台 AppID、AppSecret、Universal Link / URL Scheme 后台绑定。
4. 删除账号后云端数据是否立即硬删除，还是短期保留恢复窗口。

## 当前实现边界

1. 手机号登录 UI、服务端 API 和阿里云 webhook adapter 已存在；生产阿里云短信签名/模板/RAM 密钥未配置时不能作为正式登录能力提交。
2. 微信登录服务端 code exchange 已存在；iOS 端已接入 WechatOpenSDK 和 `WeChatLoginService` 授权桥，配置齐全后会拉起微信授权并把返回 code 交给后端。Release 未配置真实 AppID、URL Scheme、Universal Link 时按钮会被禁用。
3. `CFBundleURLTypes` 已接到 `XNP_WECHAT_URL_SCHEME` build setting；拿到微信开放平台真实 `wx...` scheme 后不需要再手改 Info.plist。
4. `Backend/scripts/verify_auth_providers.py` 会阻断未配置短信 webhook、微信 AppID/AppSecret 或线上接受 `debug_wechat_*` 的后端；脚本默认不发送真实短信，最终服务商测试需显式传 `--send-test-sms --phone-env XNP_SMS_TEST_PHONE`。
5. `Backend/scripts/check_ios_release_readiness.py` 和 `Backend/scripts/check_ios_app_bundle.py` 会分别阻断未接 WeChat OpenSDK、未配置真实 build setting、缺少授权桥或构建产物缺少真实 `wx...` URL Type 的包，避免把假微信登录提交到 App Store。

## 不进入第一版的功能

1. 邮箱登录。
2. Google / Facebook 等第三方社交登录。
3. 复杂权限角色系统。
4. 账号公开主页。

## 推荐账号方案

第一版推荐：

1. 手机号验证码登录：服务端通过短信 webhook 发送验证码，阿里云 adapter 可独立调用 Dysmsapi `SendSms`；验证后绑定到账号，账号身份表只保存 HMAC 后的手机号标识。
2. 微信登录：客户端拿到微信授权 code，服务端使用微信开放平台换取 openid/unionid 后绑定到账号；账号身份表只保存 HMAC 后的微信标识。
3. 本地数据可以先创建，不登录时保持完整离线可用。
4. 登录成功后将本地数据绑定到账号并自动进入云同步队列。
5. 退出登录不删除本地数据，删除账号才触发云端删除流程。
6. 家庭协作中，账号可创建或加入一个最多 6 人的家庭组；邀请不读取通讯录，不存储关系标签，照片原图不在成员间共享。成员退出、创建者移除成员和旧邀请码失效属于上线前必须补齐的访问撤销能力。

## 账号删除要求

账号进入第一版，必须同步完成：

1. `Docs/05_BusinessOperations/ACCOUNT_DELETION_PLAN.md`
2. App 内删除账号入口。
3. 云端宝宝档案、记录、照片原图删除机制。
4. 手机号和微信身份绑定删除。
5. 微信授权解绑说明，如微信开放平台要求。
6. App Store Review Notes 删除路径说明。
