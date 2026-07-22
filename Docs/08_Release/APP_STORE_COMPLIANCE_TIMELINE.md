# APP_STORE_COMPLIANCE_TIMELINE.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：App Store 合规时间线当前版
- 日期：2026-07-04
- 公司主体：深圳市闪现生活科技有限公司
- 当前总闸门：`Backend/proof/production-readiness.json` 和 `Backend/proof/launch-objective-audit.json` 任一不是 `ready=true` 时，不得提交 App Store Connect 审核。

## 当前材料状态

1. App Store Connect 草稿字段已经整理到 `Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260704.json`。
2. 字段冻结和现场粘贴顺序由 `Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260704.json` 约束。
3. Submit for Review 前置检查由 `Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260704.json` 约束。
4. App Store submission packet 由 `Backend/proof/app-store-submission-packet.json` 证明当前材料包可机检，但不是提交许可。

## D-U-N-S 到 TestFlight 时间线

1. D-U-N-S 交付后按 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md` 继续 Apple Developer Organization enrollment。
2. 结构化动作包为 `Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json`。
3. 完成后确认 Team ID、App Store Distribution Archive 和 TestFlight。
4. 如果 Apple Developer 显示 Team ID 与当前工程值不一致，先同步 project、ExportOptions、AASA、微信 Universal Link 和提交材料，再 Archive / TestFlight。

## 隐私、年龄分级和审核信息

1. 隐私标签答案表：`Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260704.md`。
2. 年龄分级答案表：`Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260704.md`。
3. 审核信息：`Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260704.md`。
4. 这些材料只证明草稿和现场填写依据，不替代 App Store Connect 人工页面证据。

## 生产、备案和外部平台

1. 生产/隐私证据入库工作台：`Docs/08_Release/XNP_PRODUCTION_PRIVACY_EVIDENCE_WORKBENCH_20260704.md`。
2. APP/ICP/公安联网备案执行包：`Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260704.json`。
3. 微信 Release 配置：`Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260704.json`。
4. 短信实发：`Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260704.json`。
5. OBS proof：`Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260704.json`。
6. 当前生产 proof refresh status 仍为 `stableAliasSyncAllowed=false`；不能同步 stable aliases，也不能把 current proof 模板当真实证据。

## 真机/TestFlight

1. 只接受 iOS 26.5。
2. 真机采集预检：`Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260704.json`。
3. 重点采集包：`Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260704.json`。
4. 模拟器、iOS 27、Debug candidate、模板截图、空白图或口头结论不能替代 iOS 26.5 TestFlight / 签名真机证据。

## 当前提交结论

当前不得提交 App Store Connect 审核。必须先补齐 D-U-N-S 后 Apple Developer Organization enrollment、Team ID、Archive、TestFlight、微信/短信/OBS、备案、App Store 人工证据、最终截图上传 provenance、iOS 26.5 真机回归，并让 production readiness 和 launch objective audit 都变绿。
