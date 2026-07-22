# CHINA_MAINLAND_COMPLIANCE.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：中国大陆上线合规更新
- 日期：2026-07-04
- 公司主体：深圳市闪现生活科技有限公司
- 说明：项目管理用途，不构成正式法律意见；中国大陆首发提交前必须按最新规则复核

## 已确认事实

1. 小奶瓶涉及儿童、宝宝照片、家庭和成长记录。
2. 第一版需要账号、同步恢复和服务器存储照片原图。
3. 第一版改为中国大陆 App Store 首发，香港第二批。
4. 当前已有华为云部署、远端 API 和材料 gate 证据，但 `Backend/proof/production-readiness.json` 和 `Backend/proof/launch-objective-audit.json` 仍为未就绪。
5. 疫苗模板覆盖国内 + 香港。
6. 第一版不做社区、公开分享、AI 诊断、订阅、电商。

## 当前证据口径

1. 中国大陆提交判断以 `Backend/proof/production-readiness.json` 和 `Backend/proof/launch-objective-audit.json` 为准；任一不是 ready 都不得直接提交。
2. 备案材料按 `Docs/08_Release/MAINLAND_FILING_MATERIALS.md` 执行，外部平台和生产证据按 `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md` 执行。
3. D-U-N-S 交付后的 Apple Developer Organization enrollment、Team ID、证书、Archive 和 TestFlight 动作按 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md` 执行。
4. 当前仍缺 APP 备案 / ICP / 公安联网备案证据、微信开放平台、短信服务商、OBS、App Store Connect 人工证据、iOS 26.5 TestFlight 或签名真机回归证据。
5. `Docs/08_Release/CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md` 是当前差距总览，不能用旧 proof、模拟器、模板文档或未归档截图替代真实证据。

## 合理推断

1. 中国大陆首发需要立即启动 APP 备案和 ICP 判断。
2. 使用华为云中国大陆区域时，域名、隐私政策、用户协议、API 和接入信息都要进入备案路径判断。
3. 儿童和敏感个人信息需要更严格的告知和单独同意。
4. 照片原图云同步会提高个人信息保护和数据安全要求。
5. 国内疫苗模板后续如面向中国大陆发布，需要重新核对数据来源、文案和医疗边界。

## 待我确认的问题

1. 公司 Apple Developer 账号和 D-U-N-S 状态。
2. 正式域名和华为云中国大陆区域资源。
3. APP 备案接入信息和负责人。
4. 国内 + 香港疫苗模板的数据来源、复核负责人和更新周期。

## 不进入第一版的功能

1. UGC 社区。
2. AI 生成或 AI 诊断。
3. 电商交易。
4. 直播/音视频平台。
5. 医疗建议。

## 中国大陆首发检查

| 项 | 当前结论 |
|---|---|
| APP 备案 | 首发阻断项，立即启动 |
| ICP 备案 | 大陆域名/服务器路径必须判断并完成适用手续 |
| ICP 许可证 | 当前免费工具大概率暂不触发，但需按最终形态复核 |
| 公安联网备案 | 若有网站/后台/联网服务需判断 |
| 等保 | 若有后端和用户数据存储需判断 |
| 个人信息保护 | 首发前必须完成 |
| 儿童/未成年人条款 | 首发前必须完成适用判断与告知同意 |
| SDK 披露 | 首发前必须完成并与实际网络行为一致 |
| 内容安全 | 无公开 UGC，低风险；私有照片不公开 |
| 医疗资质 | 不做医疗诊断或建议 |

## 当前建议

当前不得直接提交。先按 `Docs/08_Release/CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md`、`Docs/08_Release/MAINLAND_FILING_MATERIALS.md`、`Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260704.md` 和 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md` 补齐主体、D-U-N-S / Apple Developer Organization enrollment / Team ID、备案、域名、当天生产 proof、OBS、微信开放平台、短信服务商、App Store Connect 人工证据、儿童与敏感个人信息、照片原图云同步和 iOS 26.5 真机/TestFlight 证据，再开放中国大陆 App Store。
