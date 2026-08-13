# 小奶瓶华为云 APP 备案执行表 - 2026-07-05

> 历史说明：这是 2026-07-05 的受阻现场记录，后续流程已经完成。小奶瓶 APP 备案现已完成，主体 ICP 备案号为 `粤ICP备2025379333号`；本表中的“暂不可新建”“阻断”不代表当前状态。

## 当前结论

- 状态：暂不可新建 / 提交小奶瓶 APP 备案。
- 原因：华为云同一主体当前已有进行中的备案订单，页面提示“您有正在进行中的订单，请完成或放弃后再操作”，`新增互联网信息` 按钮置灰。
- 当前进行中订单：`1220260705000319`，备案类型 `新增互联网信息 (1APP)`，状态 `等待初审`，内容为一根呆毛，不是小奶瓶。
- 操作边界：不放弃一根呆毛订单；等该订单完成初审/流转后，再新增小奶瓶 APP 备案。
- 阻断截图：`Docs/08_Release/AppStoreEvidence/FilingAssets/huawei-existing-app-order-blocker-20260705.png`
- 阻断截图 SHA-256：`61c08ac0005073a7c567b1235f3f8238ea4b9f04fe00a539e090134a7ecacb43`

本文件是复跑填写表，不是备案完成证明。小奶瓶备案成功前，不得在 App、公开页、App Store Review Notes 中写占位备案号。

## 华为云官方流程依据

- 华为云 ICP / APP 备案流程：`https://support.huaweicloud.com/usermanual-icp/zh-cn_topic_0000002127712329.html`
- 华为云新增 APP 信息填写说明：`https://support.huaweicloud.com/usermanual-icp/zh-cn_topic_0000002127792641.html`
- 华为云 APP 特征信息说明：`https://support.huaweicloud.com/usermanual-icp/zh-cn_topic_0000002085120221.html`
- 华为云 APP 备案准备：`https://support.huaweicloud.com/prepare-icp/icp_02_0049.html`
- 华为云服务内容目录：`https://support.huaweicloud.com/prepare-icp/zh-cn_topic_0000002049126804.html`

## 主体与服务

| 字段 | 建议填写 |
|---|---|
| 主办单位 | 深圳市闪现生活科技有限公司 |
| 主体备案号 | `粤ICP备2025379333号` |
| 备案类型 | 新增互联网信息 / APP |
| APP 名称 | 小奶瓶 |
| APP 显示名称 | 小奶瓶 |
| APP 类型 | iOS 原生 App |
| 服务内容 | 父母和照护者记录宝宝喂养、睡眠、排便、成长、疫苗提醒和照片时间线 |
| 分类优先级 | 优先选 `生活服务 -> 母婴`；若无母婴，选 `生活服务 -> 工具` |
| 不选分类 | 不选医疗服务、宠物、新闻、教育培训、出版、宗教 |
| 医疗边界备注 | 本 App 不提供医疗诊断、治疗、处方、在线问诊或专业疫苗建议，仅提供家庭成长记录和本地/账号提醒工具。 |
| 是否提供 SDK 服务 | 否 |
| 是否应用第三方 SDK 服务 | 是 |
| 负责人 | 使用华为云主体中已认证的负责人信息；仓库不记录完整手机号、身份证号或短信验证码。 |

## 公开 URL

| 用途 | URL | 当前验证 |
|---|---|---|
| 官网首页 | `https://www.mewpow.com/xiaonaiping/` | 2026-07-05 可访问 |
| 隐私政策 | `https://api.mewpow.com/xiaonaiping/privacy` | 2026-07-05 HTTP 200 |
| 用户协议 | `https://api.mewpow.com/xiaonaiping/terms` | 2026-07-05 HTTP 200 |
| 支持页 | `https://api.mewpow.com/xiaonaiping/support` | 2026-07-05 HTTP 200 |
| API 前缀 | `https://api.mewpow.com/xiaonaiping` | 过渡路径，当前线上使用 |
| 健康检查 | `https://api.mewpow.com/xiaonaiping/healthz` | 2026-07-05 返回 `status=ok` |

域名填写建议：

- APP / API 域名：`api.mewpow.com`
- 官网域名：`www.mewpow.com`
- 主域名：`mewpow.com`
- 域名证书：使用华为云域名证书 / 实名认证页面截图或证书文件。
- 注意：本机 DNS 查询到的 `198.18.0.83` 属保留测试网段，不可作为公网备案 IP 提交。备案时以华为云备案系统识别到的云资源 / EIP / 接入商信息为准；一根呆毛同轮流程曾在华为云页面选择过 `113.45.236.95`，小奶瓶提交时仍必须在控制台重新确认。

## iOS 特征信息

| 字段 | 值 |
|---|---|
| 平台 | iOS |
| Bundle ID / 包名 | `com.mewpow.xiaonaiping` |
| 版本号 | `1.0` |
| Build | `2` |
| Team ID | `L2TYJNDTJK` |
| 签名主体 | `Apple Distribution: Shenzhen Flash Life Technology Co., Ltd (L2TYJNDTJK)` |
| 证书 SHA-1 指纹 | `33:2D:58:D0:9E:E0:F9:0D:7D:D6:25:CD:B0:7A:05:C9:7C:3D:8D:69` |
| 华为云 iOS “MD5 签名值”字段 | 按华为云 iOS 说明填写 SHA-1 十六进制：`332D58D09EE0F90D7DD625CDB07A05C97C3D8D69` |
| 已签名归档 | `/tmp/XiaoNaiPing-CN-L2TYJNDTJK-20260704-appstore-build2.xcarchive` |

证书公钥：

```text
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAorok/q67euUtkXmAJZ5b
4jNY1/boSJduuNbpqlFZGP40KWCZTy7+/KcIyitozcCUNK5Vh3SeMShLxUZd3oNM
2RKWvKYZ6P/qbmuHaYVd6VOKrUP8yFwYgNWLEIQERqGyY1LqpNvaio3+fXsacQZY
zRp80ydXjvZWp6+fo3bPv6LRz7zDVMn314orSYk5AzKp/RPlvtDyttIKRpb6BN5g
7krC43HgHYkmYY4YuSXF6rBuxHjeJuCzao/sUatofRN/mdeViqfoI1UoPE+g1e6v
G9ELUghgZC5LWT+W3ZrDA7zH1W1SKBiNfCKJ0Pcvl4S2/J6KLe5pFqrDilO21T83
AwIDAQAB
-----END PUBLIC KEY-----
```

## 图标与截图

| 用途 | 文件 | 大小 | SHA-256 |
|---|---|---:|---|
| 华为云推荐图标 | `Docs/08_Release/AppStoreEvidence/FilingAssets/xiaonaiping-app-icon-256.png` | 81,781 bytes | `dd6ea97d9f31a40dac782d59dd0e7d2102a360a29bfa25c3111f42c27dee300d` |
| 备用高清图标 | `Docs/08_Release/AppStoreEvidence/FilingAssets/xiaonaiping-app-icon-512.png` | 332,708 bytes | `81e52a4a11c8febf2859f8be2ef20287819374cf65c5ae06936838cdac9fa125` |
| 运行流程截图 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/` | 已存在 | 用于备案“应用运行流程”或 App Store 材料 |

华为云推荐图标小于 100KB，优先上传 256x256 版本。

## SDK 信息

| SDK / 服务 | 厂商 | 用途 | 备注 |
|---|---|---|---|
| WeChat OpenSDK / 微信开放平台 | 深圳市腾讯计算机系统有限公司 | 微信登录 / 授权 | iOS 已接入 OpenSDK；后台 AppID、URL Scheme、Universal Link、AppSecret 需以私有配置和开放平台截图为准。 |
| 阿里云 Dysmsapi / 短信服务 API | 阿里云计算有限公司 | 手机号验证码 | 服务端 webhook adapter；App 不直连短信 SDK。 |
| 华为云 OBS | 华为云计算技术有限公司 | 服务端对象存储，存储用户主动同步的照片原图 | 客户端不直连 OBS SDK，通过自有 API 上传。 |
| 自有后端 API / 第一方埋点 | 深圳市闪现生活科技有限公司 | 账号、同步恢复、合规聚合行为统计 | 无第三方分析 SDK、无广告 SDK、无第三方崩溃 SDK。 |
| Apple 原生框架 / crash reports | Apple Inc. | iOS 系统能力、崩溃报告 | 不作为第三方广告或分析 SDK 填报；如平台要求 SDK 清单，可按系统框架说明。 |

## 当前缺口

- 不能新建小奶瓶备案单：需等待一根呆毛订单 `1220260705000319` 完成或明确放弃。
- 营业执照、负责人身份证正反面、域名证书、域名实名认证截图仍需在华为云上传环节使用。
- 云资源公网 IP、接入商、备案服务号必须在华为云备案系统中重新确认，不使用本机 DNS 的 `198.18.0.83`。
- 微信开放平台移动应用截图、OBS 控制台策略截图、公安联网备案证明仍未作为小奶瓶证据归档。
- 小奶瓶备案成功后 30 日内继续办理公安联网备案。

## 下次复跑步骤

1. 打开华为云备案系统，进入 `我的备案`。
2. 确认一根呆毛订单 `1220260705000319` 不再阻挡新增互联网信息。
3. 点击 `新增互联网信息`，选择 APP / iOS。
4. 使用本表填写 App 名称、分类、域名、Bundle ID、公钥、SHA-1。
5. 上传 `xiaonaiping-app-icon-256.png`、运行流程截图、域名证书、营业执照、负责人材料。
6. 由负责人完成扫码活体核验。
7. 在最终提交初审按钮前再次确认；提交后截图归档为 `Docs/08_Release/AppStoreEvidence/03-app-filing.png` 或 `.pdf`。
8. 初审通过后 24 小时内完成工信部短信核验。
9. 管局审核通过后再补备案号展示和公安联网备案。
