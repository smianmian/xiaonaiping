# SCREENSHOT_PLAN.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：App Store 截图计划
- 日期：2026-06-25

## 原则

1. 不使用真实宝宝照片，除非另有明确授权。
2. 截图必须展示产品本身，不做夸大营销页。
3. 不写医疗诊断、治疗、疫苗建议或健康结论。
4. 展示账号备份时，必须说明是用户主动开启，且照片原图只用于私有备份恢复。
5. 香港区最终 App Store 截图使用跟随系统的繁体中文香港 `zh-Hant-HK`，截图前必须完成高频文案人工校对。
6. 不展示未完成外部配置的成功态，尤其是微信登录未完成前不能截图暗示已可用。
7. 本机截图候选和本机测试只使用 iOS 26.5；旧 runtime 截图不能作为当前测试证据。

## iPhone 截图组草案

| 序号 | 页面 | 画面重点 | 标题草案 |
|---:|---|---|---|
| 1 | 今日首页 | 出生天数、今日摘要、快速记录 | 记录宝宝今天的小变化 |
| 2 | 快速记录 | 喂养、睡眠、排便入口 | 半夜也能低负担记录 |
| 3 | 照片时间线 | 私密照片整理，不用真实宝宝照片 | 把珍贵瞬间放进私密时间线 |
| 4 | 成长/月报 | 月度回看、成长趋势 | 一个月的成长，轻轻回看 |
| 5 | 疫苗提醒 | 中国大陆 + 香港模板，非医疗建议 | 提醒和记录，不替代医生建议 |
| 6 | 账号与备份 | 恢复密钥账号、备份、删除云端数据 | 主动备份，也能主动删除 |

## 截图前检查

1. 使用最终 App 名称和图标。
2. 使用非真实宝宝照片或授权素材。
3. 不出现真实 token、恢复密钥、服务器域名或账号 ID。
4. 账号与备份截图必须使用测试账号，并在截图后删除云端账号。
5. 所有截图文字与 App Store 隐私标签、Review Notes 一致。
6. 设备或 App 语言设置为繁体中文香港，确认截图里不混入未预期简体文案。
7. 不出现 debug 文案、本地地址、internal 路径、工程说明或不可审核复现的功能状态。

## 已生成实现证据

1. `Docs/08_Release/AppStoreEvidence/10-final-screenshots/01-home-iphone16pro.png`
2. `Docs/08_Release/AppStoreEvidence/10-final-screenshots/02-record-iphone16pro.png`
3. `Docs/08_Release/AppStoreEvidence/10-final-screenshots/03-growth-iphone16pro.png`
4. `Docs/08_Release/AppStoreEvidence/10-final-screenshots/04-profile-iphone16pro.png`
5. `Docs/08_Release/AppStoreEvidence/10-final-screenshots/05-profile-backup-iphone16pro.png`

这些文件已于 2026-06-27 使用 iPhone 17 Pro / iOS 26.5 Debug simulator、截图 seed data 和生产 API URL injection 重截为当前 App Store 截图候选，尺寸均为 `1206 x 2622`。来源证明见 `Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json`。本轮修正点：

1. 不再使用带 `http://127.0.0.1:8787` 的账号截图。
2. 不出现 token、真实手机号、真实宝宝照片或 Debug 字样。
3. 账号截图使用样例手机号和未登录状态。
4. `Backend/proof/app-store-assets.json` 已通过，并强制校验 iOS 26.5 screenshot provenance。

这些文件是当前 App Store 截图候选；不是 TestFlight、签名真机或 Release build 最终证据。正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图。

## 当前截图命令

```bash
# iOS 26.5 simulator: iPhone 17 Pro, OS=26.5, UDID=07D2E9B8-B283-4F62-88D7-AFF7B7E82ED4
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -sdk iphonesimulator26.5 -destination 'platform=iOS Simulator,id=07D2E9B8-B283-4F62-88D7-AFF7B7E82ED4' -derivedDataPath /tmp/XiaoNaiPing-DebugScreenshots-26_5 CODE_SIGNING_ALLOWED=NO build
SIMCTL_CHILD_XNP_API_BASE_URL=https://api.mewpow.com/xiaonaiping python3 Backend/scripts/capture_ios_screenshots.py --device 07D2E9B8-B283-4F62-88D7-AFF7B7E82ED4 --app /tmp/XiaoNaiPing-DebugScreenshots-26_5/Build/Products/Debug-iphonesimulator/XiaoNaiPing.app --output-dir Docs/08_Release/Screenshots --tabs home record growth profile profile-backup --settle-seconds 2.5
python3 Backend/scripts/check_app_store_assets.py --output Backend/proof/app-store-assets.json
```

## 仍需补齐

1. TestFlight 或签名真机包最终截图。
2. App Store Connect 上传后截图证据。
3. 香港区繁中最终截图。
4. English (U.K.) 备用截图是否需要。
