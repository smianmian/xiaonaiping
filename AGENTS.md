# Agent 分工

本项目采用总控 Agent + 专项 Agent。所有 Agent 都必须服从“小奶瓶 / 宝宝成长记录”的第一版边界：只做 iOS 原生 App，先完成规格、后端决策、隐私审查和区域合规，再进入实现。

## 0. 总控 Agent / Project Director

负责流程闸门、任务拆解、验收推进。它不直接写代码。

硬规则：
- 没有 `PRODUCT_SPEC.md`，不允许写功能代码。
- 没有 `DATA_MODEL.md`，不允许实现存储逻辑。
- 没有 `UX_FLOW.md` / `UI_CONTRACT.md` / `UI_CONTRACT.json`，不允许实现正式页面。
- 没有 `ACCEPTANCE_CRITERIA.md`，不允许标记功能完成。
- 没有 `PRIVACY_REVIEW.md`，不允许接入照片、儿童、健康、家庭、账号、云同步或后端存储相关能力。
- 没有 `BACKEND_DECISION.md`，不允许创建后端、数据库、API 或管理后台。
- 没有 `REGIONAL_LAUNCH_STRATEGY.md`，不允许进入发布计划。
- 没有 `TEST_PLAN.md` 和 `RELEASE_CHECKLIST.md`，不允许发布。

## 1. Founder Translator Agent

把非技术创始人的输入翻译成产品、商业、体验、工程和合规都能执行的需求。

## 2. Product Agent

把创始人的模糊想法变成清晰需求，持续区分已确认事实、合理推断、待确认问题和不进入第一版的功能。

## 3. UX Agent

检查新手妈妈在半夜、单手、焦虑、赶时间时能否低负担完成记录。

## 4. UI Agent

检查页面结构、信息层级、组件布局，确保符合 `UI_CONTRACT.md` 和 `UI_CONTRACT.json`。

## 5. Visual Agent

建立温柔、干净、有纪念册感的视觉语言，避免复杂和压迫感。

## 6. Client Architect Agent

负责 iOS 原生技术方案。第一版不设计 macOS、Android、Web 实现。

## 7. Data & Sync Agent

负责数据模型、本地存储、服务器存储边界、迁移策略和删除策略。

## 8. Backend Architect Agent

只在 `BACKEND_DECISION.md` 证明后端必要后工作。负责后端部署原则、API、数据库、对象存储、备份和监控设计。

## 9. Analytics & Growth Agent

负责隐私安全的指标体系。不得采集宝宝照片、记录内容、生日、备注等敏感 payload。

## 10. Privacy & Security Agent

负责儿童信息、照片、健康成长记录、服务器存储、SDK 清单、App Store 隐私标签、区域合规和删除机制。

## 11. Monetization Agent

第一版不工作。只有当项目明确进入订阅、IAP 或付费功能时才启动。

## 12. QA Agent

负责功能测试、边界测试、兼容测试、回归测试，重点覆盖断网、空数据、误删、照片权限、账号删除和数据删除。

## 13. Release Agent

负责 TestFlight、App Store、版本、区域上线、审核材料和发布证据。

## 14. Post Launch Agent

负责上线后的留存、反馈、事故响应和迭代规划。

## 15. RCA Agent

负责问题复盘，防止同类问题反复发生。
