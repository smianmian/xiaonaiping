from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_app_store_connect_materials.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def dashed_date(path_date: str) -> str:
    return f"{path_date[:4]}-{path_date[4:6]}-{path_date[6:8]}"


def extract_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    start = text.find("\n", start)
    if start < 0:
        return ""
    next_heading = text.find("\n## ", start + 1)
    return text[start:next_heading if next_heading >= 0 else len(text)].strip()


def extract_first_code_block(section: str) -> str:
    start = section.find("```text")
    if start < 0:
        return ""
    start = section.find("\n", start)
    end = section.find("```", start + 1)
    return section[start:end].strip() if start >= 0 and end >= 0 else ""


def valid_fill_sheet() -> str:
    return """
# 小奶瓶 App Store Connect 填表版

状态：可用于准备 App Store Connect 草稿，不可直接提交审核。正式提交仍需 `Backend/proof/production-readiness.json` 为 `ready: true`。

## App 信息

| 字段 | 填写内容 |
| --- | --- |
| App 名称 | 小奶瓶 |
| Bundle ID | `com.mewpow.xiaonaiping` |
| SKU | `xiaonaiping-ios-1` |
| 副标题 | 温柔记录宝宝每一天 |
| 主类别 | 生活 |
| 第二类别 | 留空，推荐不要选择健康健美，降低被误判为医疗/健康建议 App 的风险 |
| 价格 | 免费 |
| 首发地区 | Specific Countries or Regions -> China mainland |
| 第二批地区 | Hong Kong |
| 版权 | `© 2026 深圳市闪现生活科技有限公司` |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` |
| 技术支持 URL | `https://api.mewpow.com/xiaonaiping/support` |
| 用户协议 URL | `https://api.mewpow.com/xiaonaiping/terms` |

## 字段预算

关键词按 UTF-8 bytes 计算；其他字段按 App Store Connect 字符数口径复核。人工粘贴前如果改字，一个字段改完必须重跑 `check_app_store_connect_materials.py`。

| 字段 | 限制 | 当前 | 余量 |
| --- | --- | --- | --- |
| App 名称 | 30 字符 | 3 字符 | 剩余 27 字符 |
| 副标题 | 30 字符 | 9 字符 | 剩余 21 字符 |
| 关键词 | 100 UTF-8 bytes | 73 bytes | 剩余 27 bytes |
| 宣传文本 | 170 字符 | 31 字符 | 剩余 139 字符 |
| 描述 | 4000 字符 | 184 字符 | 剩余 3816 字符 |
| 新版本说明 | 4000 字符 | 58 字符 | 剩余 3942 字符 |
| 审核备注 | 4000 字符 | 524 字符 | 剩余 3476 字符 |

## 关键词

```text
宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册
```

## 宣传文本

```text
用低负担的方式记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片。
```

## 新版本说明

```text
第一版：宝宝档案、日常记录、喝奶提醒与手动顺延、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。
```

## 描述

```text
小奶瓶是一款宝宝成长记录 App。数据默认本地优先保存，可使用恢复密钥登录账号，并同步用户主动加入 App 的照片原图。喝奶提醒可按 5 分钟一档手动顺延；小奶瓶不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。小奶瓶不提供医疗诊断。疫苗模板仅用于记录和提醒，不构成医疗建议，不作为医疗建议，实际接种安排请以医生和当地官方信息为准，不替代医生建议。
```

## 年龄分级建议

- 不选择 Kids 类目。
- 预期年龄分级：4+。
- 目标用户为父母和照护者，不面向儿童直接使用。
- 不接入 HealthKit、传感器、医院系统或第三方健康数据源；不提供压力评估、心理健康判断或压力提醒。

## 截图文案

| 序号 | 截图 | 标题 | 辅助文案 |
| --- | --- | --- | --- |
| 1 | `01-home-iphone16pro.png` | 记录宝宝今天的小变化 | 今日摘要。 |
| 2 | `02-record-iphone16pro.png` | 半夜也能低负担记录 | 快速记录。 |
| 3 | `03-growth-iphone16pro.png` | 一个月的成长，轻轻回看 | 成长变化。 |
| 4 | `04-profile-iphone16pro.png` | 设置、隐私和资料都在这里 | 管理资料。 |
| 5 | `05-profile-sync-iphone16pro.png` | 主动同步，也能主动删除 | 同步删除。 |

当前 5 张候选图不展示灵动岛/锁屏 Live Activity 或小组件。若后续新增截图，不得写成健康建议、喂养推荐或医疗判断。

截图禁区：

1. 不使用真实宝宝照片，除非另有明确授权。
2. 不展示真实手机号、恢复密钥、token、账号 ID、对象存储 key 或内部路径。
3. 不展示 `127.0.0.1`、debug code、internal dashboard 或工程文档。
4. 不写医疗诊断、治疗、疫苗建议、医生替代或专业健康结论。
5. 微信登录未完成开放平台配置前，不截图暗示微信登录已经可用。

## App Store Connect 截图上传矩阵

官方规格：https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/ 。App Store Connect 截图上传每个设备槽位为一到十张，格式只能使用 `.jpeg`、`.jpg`、`.png`。当前草稿先用 5 张候选图排顺序；正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图。

| 槽位 | 当前口径 | 上传/证据要求 |
| --- | --- | --- |
| iPhone 6.9" display | 官方可接受竖图尺寸包含 1260 x 2736、1290 x 2796、1320 x 2868 | 最终提交优先补这一槽位；上传后在 `AppStoreConnect/ASC-02-version-information.png` 保留截图上传顺序和选中 build |
| 当前候选图 | 当前候选为 iPhone 17 Pro Max / iPhone 6.9" display / 1320 x 2868 | 只作为 App Store Connect 文案、画面顺序和尺寸候选；不能把 Debug simulator 候选图声称为 TestFlight、签名真机或 App Store Connect 上传最终证据 |
| 候选来源 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json` | 来源必须显示 iOS 26.5、截图 seed data、生产 API URL injection，并注明不是 TestFlight 或签名真机包最终证据 |
| iPad 槽位 | 工程目标为 iPhone only，`TARGETED_DEVICE_FAMILY=1` | 如果 App Store Connect 要求 iPad 截图，先复核工程 target family、Bundle ID capabilities 和 App Store Connect 平台设置，不临时上传拉伸图 |

## 审核备注可粘贴文本

```text
灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。小奶瓶不是医疗器械。正式提交包不得依赖 debug code。

审核测试登录请优先使用 App Review Information 中提供的恢复密钥测试账号。手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充；正式提交包不提供、不依赖 debug code。
```

## 审核测试账号填写说明

- App Review Information 中填写恢复密钥测试账号。
- 脱敏证据文件：`Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json`。
- 真机回归与测试账号操作表：`Docs/08_Release/TEST_ACCOUNT_AND_REAL_DEVICE_REGRESSION.md`。
- 真实恢复密钥只保存在本地 ignored 文件 `.env.xnp-review-account`，只允许复制到 App Review Information 安全字段。
- 真实恢复密钥不得写入 App Store Connect 文案、审核备注、截图或仓库文档。
- 手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充。

## 当前不可提交原因

- `Backend/proof/production-readiness.json` 当前 `ready=false`
- `Backend/proof/auth-providers.json` 当前 `passed=false`，微信 provider 未配置；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充
- `Backend/proof/ios-release-readiness.json` 当前 `passed=false`，缺真实微信 Release build setting
- `Backend/proof/ios-app-bundle.json` 当前 `passed=false`，缺真实 `wx...` URL Scheme
- `Backend/proof/app-store-evidence.json` 当前 `ready=false`，缺人工证据和 iOS 26.5 真机回归记录
""".lstrip()


def valid_metadata() -> str:
    return """
# APP_STORE_METADATA.md

- 日期：2026-06-27

## 当前填表来源

| 材料 | 路径 |
|---|---|
| App Store Connect 填表版 | `Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md` |
| D-U-N-S 后续动作 | `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md` |
| 外部平台证据交接 | `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260627.md` |
| App Store Connect 终填审计表 | `Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md` |
| 年龄分级与医疗器械答案表 | `Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md` |

## 当前不可提交原因

以 `Backend/proof/launch-objective-audit.json` 和 `Backend/proof/production-readiness.json` 为准。

1. D-U-N-S 后仍需完成 Apple Developer Organization enrollment，并确认组织 Team ID。
2. 未归档 iOS 26.5 TestFlight / 签名真机回归证据。

| 字段 | 草案 |
|---|---|
| App 名称 | 小奶瓶 |
| 分类 | 生活；第二分类留空 |
| 隐私政策 | https://api.mewpow.com/xiaonaiping/privacy |
| 技术支持 | https://api.mewpow.com/xiaonaiping/support |
| 用户协议 | https://api.mewpow.com/xiaonaiping/terms |
| 描述 | 也可以在新增喂养后按 5 分钟一档手动顺延下一次提醒；不根据奶量、月龄、传感器或健康数据自动推算喂养时间。也可以在新增餵養後按 5 分鐘一檔手動順延下一次提醒；不會根據奶量、月齡、感測器或健康資料自動推算餵養時間。You can manually defer it in 5-minute steps after adding a feeding; Xiao Nai Ping does not infer feeding times from volume, age, sensors, or health data. |

Phone and WeChat sign-in will be added as account-recovery paths only after real SMS provider, WeChat Open Platform, live-send, and real-device evidence are complete.

Bundle ID: com.mewpow.xiaonaiping
""".lstrip()


def valid_app_store_connect_draft_json(path_date: str = "20260627") -> str:
    fill_sheet = valid_fill_sheet()
    draft = {
        "artifactType": "app-store-connect-draft",
        "status": "draft-only-not-submission",
        "date": dashed_date(path_date),
        "sourceFiles": {
            "fillSheet": f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
            "copyPastePacket": f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
            "metadata": "Docs/08_Release/APP_STORE_METADATA.md",
            "privacyLabel": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
            "privacyAnswers": f"Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_{path_date}.md",
            "ageRatingAnswers": f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
            "reviewInformation": f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md",
            "versionReleaseSettings": f"Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_{path_date}.md",
            "finalEntryAudit": f"Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_{path_date}.md",
        },
        "appInformation": {
            "appName": "小奶瓶",
            "bundleId": "com.mewpow.xiaonaiping",
            "sku": "xiaonaiping-ios-1",
            "subtitle": "温柔记录宝宝每一天",
            "primaryCategory": "生活",
            "secondaryCategory": "留空",
            "price": "免费",
            "firstReleaseRegion": "China mainland",
            "secondReleaseRegion": "Hong Kong",
            "copyright": "© 2026 深圳市闪现生活科技有限公司",
            "privacyPolicyUrl": "https://api.mewpow.com/xiaonaiping/privacy",
            "supportUrl": "https://api.mewpow.com/xiaonaiping/support",
            "termsUrl": "https://api.mewpow.com/xiaonaiping/terms",
        },
        "versionInformation": {
            "keywords": extract_first_code_block(extract_section(fill_sheet, "关键词")),
            "promotionalText": extract_first_code_block(extract_section(fill_sheet, "宣传文本")),
            "description": extract_first_code_block(extract_section(fill_sheet, "描述")),
            "whatsNew": extract_first_code_block(extract_section(fill_sheet, "新版本说明")),
        },
        "ageRating": {
            "answerSheet": f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
            "expectedRating": "4+",
            "kidsCategory": "No",
            "ageCategoriesAndOverride": "Not Applicable",
            "regulatedMedicalDevice": "No",
            "boundaries": [
                "not a medical device",
                "no diagnosis",
                "no treatment",
                "no disease prediction",
                "no HealthKit",
                "no sensors",
                "no hospital records",
                "no automatic feeding inference",
            ],
        },
        "appPrivacy": {
            "privacyLabel": "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
            "privacyAnswers": f"Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_{path_date}.md",
            "usesTracking": False,
            "thirdPartyAdvertising": False,
            "thirdPartyAnalytics": False,
            "dataCategories": [
                "Identifiers",
                "Contact Info",
                "User Content",
                "Photos or Videos",
                "Health and Fitness",
                "Usage Data",
                "Diagnostics",
            ],
        },
        "reviewNotes": {
            "reviewInformation": f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md",
            "signInRequired": True,
            "preferredTestAccount": "recovery-key",
            "debugCodeAllowed": False,
            "realSmsWechatAccountsPending": True,
            "boundaryChecklist": {
                "liveActivityAndWidgetsStatusOnly": True,
                "manualDeferralOptions": [
                    "不顺延",
                    "+5 分钟",
                    "+10 分钟",
                    "+15 分钟",
                    "+20 分钟",
                    "+25 分钟",
                    "+30 分钟",
                ],
                "deferralCalculation": "本顿结束时间 + 固定间隔 + 顺延分钟；本顿无喂养时长时按本顿发生时间计算",
                "deferralPersistenceBoundary": "只写入下一次 remindAt；不新增持久化字段",
                "noAutomaticFeedingInference": True,
                "noFeedingAdvice": True,
                "noHealthDataSource": True,
                "reviewLoginBoundary": "优先使用恢复密钥测试账号；手机号和微信测试号等待真实服务证据；不依赖 debug code",
            },
            "text": extract_first_code_block(extract_section(fill_sheet, "审核备注可粘贴文本")),
        },
        "pageEvidenceMap": {
            "directory": "Docs/08_Release/AppStoreEvidence/AppStoreConnect/",
            "status": "post-fill-page-evidence-only",
            "doesNotReplace": [
                "01-company-account.png",
                "02-mainland-availability.png",
                "04-privacy-label.png",
                "05-signed-archive.png",
                "06-testflight.png",
                "12-real-device-regression.md",
                "17-age-rating-result",
            ],
            "items": [
                {
                    "file": "AppStoreConnect/ASC-01-app-information.png",
                    "captures": [
                        "App 名称",
                        "副标题",
                        "Bundle ID",
                        "SKU",
                        "主类别生活",
                        "第二类别留空",
                        "版权",
                        "隐私政策 URL",
                        "技术支持 URL",
                        "用户协议 URL",
                    ],
                    "redact": ["Apple ID 邮箱", "电话", "付款信息", "D-U-N-S 编码完整值"],
                    "crossCheck": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
                        "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
                    ],
                },
                {
                    "file": "AppStoreConnect/ASC-02-version-information.png",
                    "captures": ["Version 1.0", "选中 build", "描述", "关键词", "新版本说明", "截图上传顺序"],
                    "redact": ["测试员邮箱", "Apple ID 邮箱", "恢复密钥", "验证码"],
                    "crossCheck": [
                        f"Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_{path_date}.md",
                        "Docs/08_Release/AppStoreEvidence/10-final-screenshots/",
                        "06-testflight.png",
                    ],
                },
                {
                    "file": "AppStoreConnect/ASC-03-pricing-availability-release.png",
                    "captures": [
                        "Free",
                        "Specific Countries or Regions -> China mainland",
                        "手动发布",
                        "Phased release off",
                    ],
                    "redact": ["付款信息", "税务信息", "无关地区账号资料"],
                    "crossCheck": [
                        "02-mainland-availability.png",
                        f"Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_{path_date}.md",
                    ],
                },
                {
                    "file": "AppStoreConnect/ASC-04-app-privacy.png",
                    "captures": [
                        "Tracking 为 No",
                        "Data Linked to You",
                        "Data Not Linked to You",
                        "Health and Fitness",
                        "Usage Data",
                        "Diagnostics",
                    ],
                    "redact": ["Apple ID 邮箱", "账号私密信息"],
                    "crossCheck": [
                        f"Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_{path_date}.md",
                        "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
                        "04-privacy-label.png",
                    ],
                },
                {
                    "file": "AppStoreConnect/ASC-05-age-rating.png",
                    "captures": [
                        "4+ 或 App Store Connect 自动计算结果",
                        "Kids Category 未选择",
                        "Regulated Medical Device 为 No",
                    ],
                    "redact": ["Apple ID 邮箱", "电话", "付款信息"],
                    "crossCheck": [
                        f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
                        "17-age-rating-result",
                    ],
                },
                {
                    "file": "AppStoreConnect/ASC-06-review-information.png",
                    "captures": ["Sign-in required", "恢复密钥测试账号说明", "审核备注", "联系人字段已填"],
                    "redact": ["恢复密钥", "验证码", "完整手机号", "Apple ID 邮箱", "联系人完整电话"],
                    "crossCheck": [
                        f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md",
                        "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
                    ],
                },
                {
                    "file": "AppStoreConnect/ASC-07-build-testflight-link.png",
                    "captures": ["选中 build", "TestFlight 构建状态", "版本和 build 与真机回归一致"],
                    "redact": ["测试员邮箱", "Apple ID 邮箱", "内部备注"],
                    "crossCheck": ["06-testflight.png", "12-real-device-regression.md"],
                },
                {
                    "file": "AppStoreConnect/ASC-08-submit-review-precheck.png",
                    "captures": ["Submit for Review 前页面无未处理警告", "所有字段与本审计表一致"],
                    "redact": ["恢复密钥", "验证码", "完整手机号", "AppSecret", "证书私钥", "Apple ID 邮箱"],
                    "crossCheck": [
                        "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
                        f"python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date {path_date[:4]}-{path_date[4:6]}-{path_date[6:8]} --output Backend/proof/app-store-evidence-{path_date}T-current.json",
                        "python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
                    ],
                },
            ],
        },
        "fieldAuditMatrix": {
            "status": "source-locked-before-submit",
            "rules": [
                "人工填写 App Store Connect 时只能从本矩阵列出的源文件复制。",
                "不得只改 App Store Connect 页面而不回写源文件。",
                "页面截图只证明字段已回填，不替代外部平台、TestFlight、签名归档、备案、隐私标签或 iOS 26.5 真机回归证据。",
                "任一字段改字后必须重跑 check_app_store_connect_materials.py、check_app_store_submission_packet.py 和 check_app_store_evidence.py --allow-incomplete。",
            ],
            "rows": [
                {
                    "id": "appName",
                    "field": "App 名称",
                    "value": "小奶瓶",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
                    "blockerProofs": ["01-company-account.png", "D-U-N-S delivered", "Apple Developer Organization enrollment"],
                    "redact": ["Apple ID 邮箱", "D-U-N-S 编码完整值"],
                },
                {
                    "id": "subtitle",
                    "field": "副标题",
                    "value": "温柔记录宝宝每一天",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
                    "blockerProofs": ["Backend/proof/app-store-connect-materials.json"],
                    "redact": ["Apple ID 邮箱"],
                },
                {
                    "id": "description",
                    "field": "描述",
                    "valueSource": "versionInformation.description",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-02-version-information.png"],
                    "blockerProofs": [
                        "Docs/08_Release/AppStoreEvidence/10-final-screenshots/UPLOAD_PROVENANCE.json",
                        "Backend/proof/app-store-evidence.json",
                    ],
                    "mustKeepBoundary": [
                        "本地优先",
                        "不提供医疗诊断",
                        "疫苗模板仅用于记录和提醒",
                        "手动顺延下一次提醒",
                        "不根据奶量、月龄、传感器或健康数据自动推算喂养时间",
                    ],
                    "redact": ["恢复密钥", "验证码", "完整手机号"],
                },
                {
                    "id": "keywords",
                    "field": "关键词",
                    "value": "宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-02-version-information.png"],
                    "blockerProofs": ["Backend/proof/app-store-connect-materials.json"],
                    "mustKeepBoundary": ["100 UTF-8 bytes", "73 bytes"],
                    "redact": ["Apple ID 邮箱"],
                },
                {
                    "id": "promotionalText",
                    "field": "宣传文本",
                    "valueSource": "versionInformation.promotionalText",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-02-version-information.png"],
                    "blockerProofs": ["Backend/proof/app-store-connect-materials.json"],
                    "mustKeepBoundary": [
                        "低负担",
                        "记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片",
                        "不写医疗诊断",
                        "不写喂养建议",
                    ],
                    "redact": ["Apple ID 邮箱"],
                },
                {
                    "id": "whatsNew",
                    "field": "新版本说明",
                    "valueSource": "versionInformation.whatsNew",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-02-version-information.png"],
                    "mustKeepBoundary": [
                        "喝奶提醒与手动顺延",
                        "恢复密钥账号同步恢复",
                        "云端账号删除",
                    ],
                    "redact": ["Apple ID 邮箱"],
                },
                {
                    "id": "category",
                    "field": "分类",
                    "value": "主类别：生活；第二类别：留空",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
                    "blockerProofs": ["Backend/proof/app-store-connect-materials.json"],
                    "mustKeepBoundary": ["不选择健康健美", "不选择 Kids 类目"],
                    "redact": ["Apple ID 邮箱"],
                },
                {
                    "id": "ageRating",
                    "field": "年龄分级",
                    "value": "预期 4+；以 App Store Connect 自动计算结果为准",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-05-age-rating.png", "17-age-rating-result.png 或 .pdf"],
                    "blockerProofs": ["17-age-rating-result"],
                    "mustKeepBoundary": ["Kids Category 未选择", "Regulated Medical Device 为 No", "not a medical device"],
                    "redact": ["Apple ID 邮箱", "电话"],
                },
                {
                    "id": "privacyPolicyUrl",
                    "field": "隐私政策 URL",
                    "value": "https://api.mewpow.com/xiaonaiping/privacy",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
                        "Backend/static/privacy.html",
                    ],
                    "ascEvidence": [
                        "AppStoreConnect/ASC-01-app-information.png",
                        "AppStoreConnect/ASC-04-app-privacy.png",
                    ],
                    "blockerProofs": ["04-privacy-label.png", "Backend/proof/public-pages.json"],
                    "redact": ["Apple ID 邮箱", "账号私密信息"],
                },
                {
                    "id": "supportUrl",
                    "field": "技术支持 URL",
                    "value": "https://api.mewpow.com/xiaonaiping/support",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
                        "Backend/static/support.html",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
                    "blockerProofs": ["Backend/proof/public-pages.json"],
                    "redact": ["Apple ID 邮箱"],
                },
                {
                    "id": "termsUrl",
                    "field": "用户协议 URL",
                    "value": "https://api.mewpow.com/xiaonaiping/terms",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        "Backend/static/terms.html",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-01-app-information.png"],
                    "blockerProofs": ["Backend/proof/public-pages.json"],
                    "redact": ["Apple ID 邮箱"],
                },
                {
                    "id": "reviewNotes",
                    "field": "审核备注",
                    "valueSource": "reviewNotes.text",
                    "sourceFiles": [
                        f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
                        f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md",
                    ],
                    "ascEvidence": ["AppStoreConnect/ASC-06-review-information.png"],
                    "blockerProofs": [
                        "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
                        "Docs/08_Release/AppStoreEvidence/12-real-device-regression.md",
                        "Backend/proof/app-store-evidence.json",
                    ],
                    "mustKeepBoundary": [
                        "不提供医疗诊断",
                        "不构成喂养建议",
                        "手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充",
                        "正式提交包不提供、不依赖 debug code",
                    ],
                    "redact": ["恢复密钥", "验证码", "完整手机号", "AppSecret", "Apple ID 邮箱"],
                },
            ],
        },
        "submissionBoundary": {
            "canSubmitFromThisDraft": False,
            "requiresBeforeSubmit": [
                "production-readiness.json ready=true",
                "launch-objective-audit.json ready=true",
                "D-U-N-S delivered and Apple Developer Organization enrollment resumed",
                "Apple Developer Team ID confirmed",
                "App Store Distribution Archive created",
                "TestFlight build processed",
                "微信开放平台 AppID/AppSecret/Universal Link configured",
                "短信服务商截图 and real send proof archived",
                "OBS private bucket policy and deletion proof archived",
                "APP 备案 / ICP applicability evidence archived",
                "iOS 26.5 TestFlight or signed real-device regression completed",
            ],
        },
    }
    return json.dumps(draft, ensure_ascii=False, indent=2) + "\n"


def rewrite_packet_dates(value, path_date: str):
    if isinstance(value, str):
        return (
            value.replace("20260628", path_date)
            .replace("2026-06-28", dashed_date(path_date))
            .replace("20260629", path_date)
            .replace("2026-06-29", dashed_date(path_date))
            .replace("20260630", path_date)
            .replace("2026-06-30", dashed_date(path_date))
            .replace("20260704", path_date)
            .replace("2026-07-04", dashed_date(path_date))
        )
    if isinstance(value, list):
        return [rewrite_packet_dates(item, path_date) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_packet_dates(item, path_date) for key, item in value.items()}
    return value


def valid_app_store_connect_field_freeze_packet(path_date: str = "20260627") -> str:
    draft = json.loads(valid_app_store_connect_draft_json(path_date))
    budgets = [
        ("appName", "App 名称", "characters", 30, "appInformation.appName", draft["appInformation"]["appName"]),
        ("subtitle", "副标题", "characters", 30, "appInformation.subtitle", draft["appInformation"]["subtitle"]),
        ("keywords", "关键词", "utf8Bytes", 100, "versionInformation.keywords", draft["versionInformation"]["keywords"]),
        ("promotionalText", "宣传文本", "characters", 170, "versionInformation.promotionalText", draft["versionInformation"]["promotionalText"]),
        ("description", "描述", "characters", 4000, "versionInformation.description", draft["versionInformation"]["description"]),
        ("whatsNew", "新版本说明", "characters", 4000, "versionInformation.whatsNew", draft["versionInformation"]["whatsNew"]),
        ("reviewNotes", "审核备注", "characters", 4000, "reviewNotes.text", draft["reviewNotes"]["text"]),
    ]
    field_budget_matrix = []
    for row_id, field, metric, limit, value_source, value in budgets:
        used = len(value.encode("utf-8")) if metric == "utf8Bytes" else len(value)
        field_budget_matrix.append(
            {
                "id": row_id,
                "field": field,
                "valueSource": value_source,
                "metric": metric,
                "limit": limit,
                "used": used,
                "remaining": limit - used,
                "withinLimit": used <= limit,
                "sourceValuePresent": bool(value),
            }
        )
    fields = []
    for row in draft["fieldAuditMatrix"]["rows"]:
        field = dict(row)
        field["freezeAction"] = "如需改字段，先回写源文件，再更新 App Store Connect 页面并重跑 gate。"
        fields.append(field)
    source_lock_match_keys = (
        "field",
        "value",
        "valueSource",
        "sourceFiles",
        "ascEvidence",
        "blockerProofs",
        "mustKeepBoundary",
        "redact",
    )
    field_source_lock_matrix = []
    for row in draft["fieldAuditMatrix"]["rows"]:
        field_source_lock_matrix.append(
            {
                "id": row["id"],
                "draftRowId": row["id"],
                "freezeFieldId": row["id"],
                "sourceObject": (
                    f"Docs/08_Release/APP_STORE_CONNECT_DRAFT_{path_date}.json:"
                    f"fieldAuditMatrix.rows.{row['id']}"
                ),
                "requiredMatches": [
                    key
                    for key in source_lock_match_keys
                    if key in row
                ],
                "matchesDraftRow": True,
                "matchesFreezeField": True,
                "status": "locked-from-draft-not-live-evidence",
            }
        )
    paste_post_gate = "check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json"
    paste_sequence_specs = [
        (
            "appName",
            1,
            "ASC-01 App Information",
            "App Name",
            "text",
            "appInformation.appName",
            f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
            ["AppStoreConnect/ASC-01-app-information.png"],
            "fieldSourceLockMatrix.appName.matchesDraftRow=true",
        ),
        (
            "subtitle",
            2,
            "ASC-01 App Information",
            "Subtitle",
            "text",
            "appInformation.subtitle",
            f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
            ["AppStoreConnect/ASC-01-app-information.png"],
            "fieldSourceLockMatrix.subtitle.matchesDraftRow=true",
        ),
        (
            "description",
            3,
            "ASC-02 Version Information",
            "Description",
            "textarea",
            "versionInformation.description",
            f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
            ["AppStoreConnect/ASC-02-version-information.png"],
            "fieldBudgetMatrix.description.withinLimit=true",
        ),
        (
            "keywords",
            4,
            "ASC-02 Version Information",
            "Keywords",
            "keyword-list",
            "versionInformation.keywords",
            f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
            ["AppStoreConnect/ASC-02-version-information.png"],
            "fieldBudgetMatrix.keywords.withinLimit=true",
        ),
        (
            "promotionalText",
            5,
            "ASC-02 Version Information",
            "Promotional Text",
            "textarea",
            "versionInformation.promotionalText",
            f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
            ["AppStoreConnect/ASC-02-version-information.png"],
            "fieldBudgetMatrix.promotionalText.withinLimit=true",
        ),
        (
            "whatsNew",
            6,
            "ASC-02 Version Information",
            "What's New",
            "textarea",
            "versionInformation.whatsNew",
            f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
            ["AppStoreConnect/ASC-02-version-information.png"],
            "fieldBudgetMatrix.whatsNew.withinLimit=true",
        ),
        (
            "category",
            7,
            "ASC-01 App Information",
            "Primary Category / Secondary Category",
            "category-selector",
            "appInformation.primaryCategory + appInformation.secondaryCategory",
            f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
            ["AppStoreConnect/ASC-01-app-information.png"],
            "fieldSourceLockMatrix.category.matchesDraftRow=true",
        ),
        (
            "ageRating",
            8,
            "ASC-05 Age Rating",
            "Age Rating questionnaire",
            "questionnaire",
            "ageRating.answerSheet",
            f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
            ["AppStoreConnect/ASC-05-age-rating.png", "17-age-rating-result.png 或 .pdf"],
            "fieldSourceLockMatrix.ageRating.matchesDraftRow=true",
        ),
        (
            "privacyPolicyUrl",
            9,
            "ASC-01 App Information / ASC-04 App Privacy",
            "Privacy Policy URL",
            "url",
            "appInformation.privacyPolicyUrl",
            f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
            ["AppStoreConnect/ASC-01-app-information.png", "AppStoreConnect/ASC-04-app-privacy.png"],
            "fieldSourceLockMatrix.privacyPolicyUrl.matchesDraftRow=true",
        ),
        (
            "supportUrl",
            10,
            "ASC-01 App Information",
            "Support URL",
            "url",
            "appInformation.supportUrl",
            f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
            ["AppStoreConnect/ASC-01-app-information.png"],
            "fieldSourceLockMatrix.supportUrl.matchesDraftRow=true",
        ),
        (
            "termsUrl",
            11,
            "ASC-01 App Information",
            "License Agreement URL",
            "url",
            "appInformation.termsUrl",
            f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
            ["AppStoreConnect/ASC-01-app-information.png"],
            "fieldSourceLockMatrix.termsUrl.matchesDraftRow=true",
        ),
        (
            "reviewNotes",
            12,
            "ASC-06 App Review Information",
            "Review Notes",
            "review-notes-textarea",
            "reviewNotes.text",
            f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
            ["AppStoreConnect/ASC-06-review-information.png"],
            "fieldBudgetMatrix.reviewNotes.withinLimit=true",
        ),
    ]
    paste_sequence_matrix = [
        {
            "id": row_id,
            "order": order,
            "ascPage": asc_page,
            "ascField": asc_field,
            "inputType": input_type,
            "sourceValuePath": source_value_path,
            "copySource": copy_source,
            "ascEvidence": asc_evidence,
            "prePasteCheck": pre_paste_check,
            "postPasteGate": paste_post_gate,
            "pasteRequired": True,
            "initialStatus": "pending",
        }
        for (
            row_id,
            order,
            asc_page,
            asc_field,
            input_type,
            source_value_path,
            copy_source,
            asc_evidence,
            pre_paste_check,
        ) in paste_sequence_specs
    ]
    packet = {
        "artifactType": "app-store-connect-field-freeze-packet",
        "status": "field-freeze-plan-not-evidence",
        "date": dashed_date(path_date),
        "project": "XiaoNaiPing",
        "appName": "小奶瓶",
        "bundleId": "com.mewpow.xiaonaiping",
        "canSubmitFromThisPacket": False,
        "sourceFiles": {
            "draftJson": f"Docs/08_Release/APP_STORE_CONNECT_DRAFT_{path_date}.json",
            "fillSheet": f"Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_{path_date}.md",
            "copyPastePacket": f"Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_{path_date}.md",
            "finalEntryAudit": f"Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_{path_date}.md",
            "privacyAnswers": f"Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_{path_date}.md",
            "ageRatingAnswers": f"Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_{path_date}.md",
            "reviewInformation": f"Docs/08_Release/APP_STORE_REVIEW_INFORMATION_{path_date}.md",
            "entrySessionPacket": f"Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_{path_date}.json",
            "appStoreSubmissionPacket": "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
        },
        "fieldFreezeRules": [
            "field-freeze-plan-not-evidence; this is an App Store Connect 草稿字段冻结 packet.",
            "只能从 sourceFiles 复制，不得现场改字后只改 App Store Connect 页面。",
            "任一字段改字必须回写源文件，并重跑 postFreezeGates。",
            "ASC 页面截图只证明回填，不能替代 D-U-N-S、Archive、TestFlight、短信、微信、OBS、备案、隐私标签、最终截图或 iOS 26.5 真机回归证据。",
        ],
        "fields": fields,
        "fieldSourceLockMatrix": field_source_lock_matrix,
        "pasteSequenceMatrix": paste_sequence_matrix,
        "fieldBudgetMatrix": field_budget_matrix,
        "postFreezeGates": [
            "check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json",
            "check_app_store_submission_packet.py --output Backend/proof/app-store-submission-packet.json",
            f"check_app_store_evidence.py --allow-incomplete --date {dashed_date(path_date)} --output Backend/proof/app-store-evidence-{path_date}T-current.json",
            "check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json",
        ],
        "completionRule": "field-freeze-plan-not-evidence; not App Store Connect live evidence; not submission permission; canSubmitFromThisPacket=false. Submit for Review still requires app-store-evidence.json ready=true, production-readiness.json ready=true, and launch-objective-audit.json ready=true.",
    }
    return json.dumps(packet, ensure_ascii=False, indent=2) + "\n"


def valid_app_store_connect_entry_session_packet(path_date: str = "20260627") -> str:
    packet_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260630.json"
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet = rewrite_packet_dates(packet, path_date)
    packet.setdefault("sourceFiles", {})[
        "submitReviewPreflight"
    ] = f"Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_{path_date}.json"
    return json.dumps(packet, ensure_ascii=False, indent=2) + "\n"


def valid_app_store_connect_submit_review_preflight_packet(path_date: str = "20260627") -> str:
    packet_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260630.json"
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet = rewrite_packet_dates(packet, path_date)
    return json.dumps(packet, ensure_ascii=False, indent=2) + "\n"


def valid_asc_backfill_result_template(path_date: str = "20260627") -> str:
    template_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-BACKFILL-RESULT.template.json"
    )
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template = rewrite_packet_dates(template, path_date)
    return json.dumps(template, ensure_ascii=False, indent=2) + "\n"


def valid_asc_privacy_age_review_result_template(path_date: str = "20260627") -> str:
    template_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-PRIVACY-AGE-REVIEW-RESULT.template.json"
    )
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template = rewrite_packet_dates(template, path_date)
    return json.dumps(template, ensure_ascii=False, indent=2) + "\n"


def valid_app_review_test_account_packet(path_date: str = "20260627") -> str:
    packet_path = (
        Path(__file__).resolve().parents[2]
        / "Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260630.json"
    )
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet = rewrite_packet_dates(packet, path_date)
    return json.dumps(packet, ensure_ascii=False, indent=2) + "\n"


def valid_age_rating_answers() -> str:
    return """
# 小奶瓶 App Store 年龄分级与医疗器械答案表

日期：2026-06-27

## 官方核对入口

1. https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating
2. https://developer.apple.com/help/app-store-connect/manage-app-information/declare-regulated-medical-device-status
3. Kids Category https://developer.apple.com/app-store/review/guidelines/#kids-category

## 产品事实边界

小奶瓶面向父母和照护者，不面向儿童直接使用。第一版免费，无 IAP、无广告、无第三方分析 SDK。第一版没有公开 UGC、社区、聊天、社交匹配、赌博、成人内容或内置开放网页浏览器。用户可以手动顺延下一次提醒，但不根据奶量、月龄、传感器或健康数据自动推算喂养时间。

## App Store Connect 年龄分级问卷口径

| 项目 | 填写口径 |
|---|---|
| 预期年龄分级 | 4+，以 App Store Connect 问卷自动计算结果为准 |
| Age Categories and Override | Not Applicable |
| Made for Kids / Kids Category | 不选择 |
| Web access | 无内置开放网页浏览器 |
| User-generated public content | 无 |
| Messaging / chat | 无 |
| Purchases | 无 |
| Advertising / tracking | 无 |
| Gambling / contests | 无 |
| Mature or objectionable content | 无 |
| Health-related records | 用户主动输入，只用于记录和提醒 |
| Medical advice | 不提供 |

## 受监管医疗器械声明口径

| 项目 | 填写口径 |
|---|---|
| Regulated Medical Device | `No` |
| 解释 | Xiao Nai Ping is not a medical device. It does not provide diagnosis, prevention, monitoring, treatment, disease prediction, or professional medical advice. |
| 外部监管状态 | 无 FDA cleared / approved、无 CE mark、无 UKCA mark |
| 数据来源 | 不接入 HealthKit、传感器、医院系统 |

## 提交前重检项

功能变化后必须重新复核。
""".lstrip()


def valid_copy_paste_packet() -> str:
    return """
# 小奶瓶 App Store Connect 可复制字段包

日期：2026-06-27

源文件：`Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md`

App Privacy 逐项答案表另见：`Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md`

版本页和发布设置另见：`Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md`

最终人工粘贴和同轮证据核对另见：`Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md`

## App 信息

```text
App 名称：小奶瓶
Bundle ID：com.mewpow.xiaonaiping
SKU：xiaonaiping-ios-1
副标题：温柔记录宝宝每一天
主类别：生活
第二类别：留空
价格：免费
首发地区：Specific Countries or Regions -> China mainland
第二批地区：Hong Kong
版权：© 2026 深圳市闪现生活科技有限公司
隐私政策 URL：https://api.mewpow.com/xiaonaiping/privacy
技术支持 URL：https://api.mewpow.com/xiaonaiping/support
用户协议 URL：https://api.mewpow.com/xiaonaiping/terms
```

## 字段预算

关键词按 UTF-8 bytes 计算；其他字段按 App Store Connect 字符数口径复核。人工粘贴前如果改字，一个字段改完必须重跑 `check_app_store_connect_materials.py`。

| 字段 | 限制 | 当前 | 余量 |
| --- | --- | --- | --- |
| App 名称 | 30 字符 | 3 字符 | 剩余 27 字符 |
| 副标题 | 30 字符 | 9 字符 | 剩余 21 字符 |
| 关键词 | 100 UTF-8 bytes | 73 bytes | 剩余 27 bytes |
| 宣传文本 | 170 字符 | 31 字符 | 剩余 139 字符 |
| 描述 | 4000 字符 | 184 字符 | 剩余 3816 字符 |
| 新版本说明 | 4000 字符 | 58 字符 | 剩余 3942 字符 |
| 审核备注 | 4000 字符 | 524 字符 | 剩余 3476 字符 |

## 关键词

```text
宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册
```

## 宣传文本

```text
用低负担的方式记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片。
```

## 描述

```text
小奶瓶是一款宝宝成长记录 App。数据默认本地优先保存，可使用恢复密钥登录账号，并同步用户主动加入 App 的照片原图。喝奶提醒可按 5 分钟一档手动顺延；小奶瓶不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。小奶瓶不提供医疗诊断。疫苗模板仅用于记录和提醒，不构成医疗建议，不作为医疗建议，实际接种安排请以医生和当地官方信息为准，不替代医生建议。
```

## 新版本说明

```text
第一版：宝宝档案、日常记录、喝奶提醒与手动顺延、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。
```

## 年龄分级填写口径

```text
逐项答案表：Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md

不选择 Kids 类目。预期年龄分级为 4+。
```

## 隐私标签来源

Docs/08_Release/APP_STORE_PRIVACY_LABEL.json
用于追踪：否

## 审核备注

```text
灵动岛和锁屏 Live Activity 只显示用户设置的下一次喝奶提醒、固定间隔和宝宝昵称/头像缩略图；桌面/锁屏小组件只读展示今日摘要。用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。所有摘要都来自用户在 App 内输入并保存在本机记录的数据，不接入 HealthKit、传感器、医院系统或第三方健康数据源，不提供压力评估、心理健康判断或医疗诊断。小奶瓶不是医疗器械。正式提交包不得依赖 debug code。

审核测试登录请优先使用 App Review Information 中提供的恢复密钥测试账号。手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充；正式提交包不提供、不依赖 debug code。
```

用户保存新喂养时可以手动顺延下一次提醒。顺延使用 5 分钟一档，不新增持久化字段。正式提交包不提供、不依赖 debug code。

## 提交前不可跳过

D-U-N-S 交付后必须回 Apple Developer 继续 Organization enrollment。
iOS 26.5 TestFlight 或 Xcode 签名真机包回归必须完成，模拟器和 iOS 27 不能替代。
""".lstrip()


def valid_review_information_packet() -> str:
    return """
# 小奶瓶 App Review Information 私密字段包

日期：2026-06-27

结构化审核测试账号执行包：`Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260627.json`。该包状态为 `review-test-account-packet-not-evidence`；只约束 App Review 私密 Sign-In Information 的填写、脱敏证据、RD-10/RD-13/RD-14/RD-15 真机采集、账号删除和复跑 gate，不保存恢复密钥，不能作为提交许可。

## 官方核对入口

1. https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information/
2. https://developer.apple.com/distribute/app-review

## Contact Information

| 字段 | 填写要求 | 仓库状态 |
|---|---|---|
| First Name / Last Name | 使用公司联系人 | 不写入仓库 |
| Email | 使用公司邮箱 | 不写入仓库 |
| Phone Number | 使用公司电话 | 不写入仓库 |

## Sign-In Information

Sign-in required: Yes. Username: review-recovery-key-account. Password 从 .env.xnp-review-account 的 XNP_REVIEW_RECOVERY_KEY 读取，只能填入 App Review Information 私密字段。手机号测试号和微信测试号必须等真实短信服务商和微信开放平台配置完成后再补。

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

请使用恢复密钥登录。账号只包含虚构宝宝资料。登录后可测试立即同步、云端恢复、删除云端账号与同步。正式提交包不得依赖 debug code。状态展示不生成健康建议、压力提醒、喂养建议或医疗判断。

## 证据

11-test-account-redacted.json
12-real-device-regression.md
05-signed-archive.png
06-testflight.png
07-sms-provider.png
08-wechat-open-platform.png

## 提交前阻断项

Review Information 可以先保存草稿，但点击 Submit for Review 前必须逐项确认；不能只保存草稿后提交审核，也不能把恢复密钥测试账号当成上线完成证据。

| 阻断项 | 必须核对的证据 |
|---|---|
| 总上线闸门 | `Backend/proof/production-readiness.json` ready=true；`Backend/proof/launch-objective-audit.json` ready=true |
| D-U-N-S / Apple Developer | `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md`：D-U-N-S、Apple Developer Organization enrollment、Team ID、`AppleDeveloper/16-account-roles-access.png`、App Store Distribution Archive、TestFlight |
| 中国大陆 / App Store 人工项 | `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260627.md`：`03-app-filing`、`04-privacy-label`、`17-age-rating-result` |
| 外部平台 | `07-sms-provider.png`、`08-wechat-open-platform.png`、`09-obs-policy.png` |
| Archive / TestFlight / 真机回归 | `05-signed-archive.png`、`06-testflight.png`、`12-real-device-regression.md` |
| 最终截图 | `10-final-screenshots/UPLOAD_PROVENANCE.json` |

## 不得填写或提交

不得填写或提交 debug_wechat_*、127.0.0.1、localhost。不得声称手机号登录、微信登录、TestFlight、备案或 App Store 人工证据已完成。
""".lstrip()


def valid_privacy_answers() -> str:
    return """
# 小奶瓶 App Store Privacy 逐项答案表

日期：2026-06-27

源文件：Docs/08_Release/APP_STORE_PRIVACY_LABEL.json

官方入口：
- https://developer.apple.com/app-store/app-privacy-details/
- https://developer.apple.com/help/app-store-connect/manage-app-privacy/overview-of-app-privacy-details/

Data Used to Track You: No.
Tracking Domains: None. PrivacyInfo.xcprivacy disables tracking.
Third-Party Advertising: No.
Third-Party Analytics: No.
Kids Category: No.
Privacy Policy URL: https://api.mewpow.com/xiaonaiping/privacy

Data Linked to You: Identifiers, Contact Info, User Content, Photos or Videos, Health and Fitness, Usage Data.
Data Not Linked to You: Diagnostics.
Not Collected: Location, Contacts, Purchases, Advertising Data.

Health and Fitness 边界：用户主动输入；不接入 HealthKit、传感器、医院系统或第三方健康数据源；status display only；不生成健康建议、压力提醒、喂养建议或医疗判断；不根据奶量、月龄、传感器或健康数据自动推算喂养时间。

Usage Data 边界：no baby content, photos, photo keys, phone numbers, WeChat identifiers, advertising ID, device fingerprint.

提交前重跑 check_ios_release_readiness.py 和 check_diagnostics_redaction.py，并归档 04-privacy-label.png。
""".lstrip()


def valid_version_release_settings() -> str:
    return """
# 小奶瓶 App Store Version 与发布设置表

日期：2026-06-27

## Version Information

| 字段 | 当前填写 |
|---|---|
| Version | `1.0` |
| Build | 等 TestFlight 构建处理完成后选择对应 build；当前工程 CURRENT_PROJECT_VERSION=1 |
| What's New | 第一版：宝宝档案、日常记录、喝奶提醒与手动顺延、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。 |
| Promotional Text | 用低负担的方式记录喂养、睡眠、排便、成长、疫苗提醒和珍贵照片。 |
| Description | 复制填表版的描述 |
| Keywords | 宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册 |
| Support URL | `https://api.mewpow.com/xiaonaiping/support` |
| Marketing URL | 留空 |

## Pricing and Availability

Price: Free. Availability: Specific Countries or Regions -> China mainland. First batch: China mainland only. Do not select Hong Kong, United States, all other regions. Evidence: 02-mainland-availability.png.

## Version Release

Release option: Manually release this version after App Review approval. Phased release: Off. 审核通过不等于可以自动上线.

## Export Compliance

Uses encryption: Yes, Apple 平台安全、Keychain、HTTPS 和标准系统/网络加密. Custom cryptography: No. VPN: No. DRM: No. End-to-end encrypted messaging: No.

## Advertising Identifier / Tracking

Uses IDFA: No. Tracking: No. Third-party advertising: No. Third-party analytics SDK: No.

## Content Rights

User-added photos are private. 不使用真实宝宝照片.

## 提交前重检

Require 05-signed-archive.png, 06-testflight.png, 12-real-device-regression.md and check_signed_archive_testflight_materials.py before claiming completion.
""".lstrip()


def valid_final_entry_audit() -> str:
    return """
# 小奶瓶 App Store Connect 终填审计表

日期：2026-06-27

状态：用于 App Store Connect 草稿最后一次人工粘贴和截图前核对。同一天同一轮只记录字段、证据路径和复跑命令。

结构化人工填写执行包：`Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json`。该包状态为 `entry-session-plan-not-evidence`；不是 App Store Connect 人工证据，不能作为提交许可。

## 同一天同一轮环境

App 版本 `1.0`。Build 号和 App Store Connect 选中的 build 必须与 `06-testflight.png`、`12-real-device-regression.md` 一致。D-U-N-S 交付后完成 Apple Developer Organization enrollment，并确认 Team ID。

## 终填字段核对

| 字段 | 值 |
|---|---|
| App 名称 | 小奶瓶 |
| 副标题 | 温柔记录宝宝每一天 |
| 主类别：生活 | APP_STORE_CONNECT_FILL_SHEET_20260627.md |
| 第二类别：留空 | APP_STORE_CONNECT_FILL_SHEET_20260627.md |
| 隐私政策 URL | https://api.mewpow.com/xiaonaiping/privacy |
| 技术支持 URL | https://api.mewpow.com/xiaonaiping/support |
| 关键词 | APP_STORE_CONNECT_COPY_PASTE_20260627.md |
| 描述 | APP_STORE_CONNECT_COPY_PASTE_20260627.md |
| 审核备注 | APP_STORE_CONNECT_COPY_PASTE_20260627.md |
| Sign-In Information | APP_STORE_REVIEW_INFORMATION_20260627.md |
| App Privacy | APP_STORE_PRIVACY_ANSWERS_20260627.md |
| 年龄分级 | APP_STORE_AGE_RATING_ANSWERS_20260627.md |
| 版本发布设置 | APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md |
| 截图 | 10-final-screenshots/ |

## 终填字段源文件一致性锁

App Store Connect 页面值不能成为唯一来源。人工粘贴时只允许从下表源文件复制；如果页面值和源文件不一致，先修正 App Store Connect 或源文件，再重跑 `check_app_store_connect_materials.py` 和 `check_app_store_submission_packet.py`，不提交审核。

| 字段 | 唯一来源 | 回填证据 |
| --- | --- | --- |
| App 名称 / 副标题 / 主类别 / 第二类别 | `APP_STORE_CONNECT_FILL_SHEET_20260627.md`、`APP_STORE_CONNECT_COPY_PASTE_20260627.md` | `AppStoreConnect/ASC-01-app-information.png` |
| 关键词 / 描述 / 审核备注 | `APP_STORE_CONNECT_FILL_SHEET_20260627.md`、`APP_STORE_CONNECT_COPY_PASTE_20260627.md` | `AppStoreConnect/ASC-02-version-information.png`、`AppStoreConnect/ASC-06-review-information.png` |
| 年龄分级 | `APP_STORE_AGE_RATING_ANSWERS_20260627.md` | `AppStoreConnect/ASC-05-age-rating.png`、`17-age-rating-result.png` 或 `.pdf` |
| 隐私政策 URL / 技术支持 URL / 用户协议 URL | `APP_STORE_CONNECT_FILL_SHEET_20260627.md`、`APP_STORE_PRIVACY_LABEL.json`、`Backend/static/privacy.html`、`Backend/static/support.html`、`Backend/static/terms.html` | `AppStoreConnect/ASC-01-app-information.png`、公开 URL proof |
| App Privacy | `APP_STORE_PRIVACY_ANSWERS_20260627.md`、`APP_STORE_PRIVACY_LABEL.json` | `AppStoreConnect/ASC-04-app-privacy.png`、`04-privacy-label.png` |
| Sign-In Information | `APP_STORE_REVIEW_INFORMATION_20260627.md`、`11-test-account-redacted.json` | `AppStoreConnect/ASC-06-review-information.png` |
| 版本发布设置 | `APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md` | `AppStoreConnect/ASC-03-pricing-availability-release.png`、`AppStoreConnect/ASC-07-build-testflight-link.png` |
| 截图上传顺序 | `SCREENSHOT_PLAN.md`、`APP_STORE_EVIDENCE_CHECKLIST_20260627.md`、`10-final-screenshots/PROVENANCE.json` | `AppStoreConnect/ASC-02-version-information.png` |

- [ ] 不得只改 App Store Connect 页面而不回写源文件。
- [ ] 任一字段改字后，先同步填表版、可复制字段包、终填审计表和对应答案表，再重跑材料 gate。
- [ ] 回填截图只证明页面已经填入，不替代源文件、外部后台证据、TestFlight 或真机回归。

## 字段预算

关键词按 UTF-8 bytes 计算；其他字段按 App Store Connect 字符数口径复核。人工粘贴前如果改字，一个字段改完必须重跑 `check_app_store_connect_materials.py`。

| 字段 | 限制 | 当前 | 余量 |
| --- | --- | --- | --- |
| App 名称 | 30 字符 | 3 字符 | 剩余 27 字符 |
| 副标题 | 30 字符 | 9 字符 | 剩余 21 字符 |
| 关键词 | 100 UTF-8 bytes | 73 bytes | 剩余 27 bytes |
| 宣传文本 | 170 字符 | 31 字符 | 剩余 139 字符 |
| 描述 | 4000 字符 | 184 字符 | 剩余 3816 字符 |
| 新版本说明 | 4000 字符 | 58 字符 | 剩余 3942 字符 |
| 审核备注 | 4000 字符 | 524 字符 | 剩余 3476 字符 |

## 外部证据同轮索引

01-company-account.png
02-mainland-availability.png
03-app-filing
04-privacy-label.png
05-signed-archive.png
06-testflight.png
07-sms-provider.png
08-wechat-open-platform.png
09-obs-policy.png
10-final-screenshots/
11-test-account-redacted.json
12-real-device-regression.md
17-age-rating-result

## App Store Connect 截图上传矩阵

官方规格：https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/ 。App Store Connect 截图上传每个设备槽位为一到十张，格式只能使用 `.jpeg`、`.jpg`、`.png`。当前 5 张候选图已固定文案顺序，但正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图。

| 槽位 | 当前口径 | 回填证据 |
| --- | --- | --- |
| iPhone 6.9" display | 官方可接受竖图尺寸包含 1260 x 2736、1290 x 2796、1320 x 2868 | `AppStoreConnect/ASC-02-version-information.png` 必须保留截图上传顺序、选中 build 和上传后的 5 张图 |
| 当前候选图 | 当前候选为 iPhone 17 Pro Max / iPhone 6.9" display / 1320 x 2868 | 只作为画面、文案和尺寸候选；不能把 Debug simulator 候选图声称为 TestFlight、签名真机或 App Store Connect 上传最终证据 |
| 候选来源 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json` | 候选来源必须说明 iOS 26.5 Debug simulator、截图 seed data、生产 API URL injection，且不替代 TestFlight 或签名真机包最终证据 |
| iPad 槽位 | 工程目标为 iPhone only，`TARGETED_DEVICE_FAMILY=1` | 如果 App Store Connect 要求 iPad 截图，先复核工程 target family、Bundle ID capabilities 和 App Store Connect 平台设置，不临时上传拉伸图 |

## App Store Connect 页面回填证据索引

页面截图或 PDF 放进 `Docs/08_Release/AppStoreEvidence/AppStoreConnect/`。这些文件不替代 `01-company-account.png`、`02-mainland-availability.png`、`04-privacy-label.png`、`05-signed-archive.png`、`06-testflight.png`、`12-real-device-regression.md` 或 `17-age-rating-result`。

| 文件名 | 必须保留 | 必须遮挡 | 回填核对 |
|---|---|---|---|
| `AppStoreConnect/ASC-01-app-information.png` | App 名称、副标题、Bundle ID、SKU、主类别生活、第二类别留空、版权、隐私政策 URL、技术支持 URL、用户协议 URL | Apple ID 邮箱、电话、付款信息、D-U-N-S 编码完整值 | APP_STORE_CONNECT_FILL_SHEET_20260627.md |
| `AppStoreConnect/ASC-02-version-information.png` | Version `1.0`、选中 build、描述、关键词、新版本说明、截图上传顺序 | 测试员邮箱、Apple ID 邮箱、任何恢复密钥或验证码 | 10-final-screenshots/ |
| `AppStoreConnect/ASC-03-pricing-availability-release.png` | Free、Specific Countries or Regions -> China mainland、手动发布、Phased release off | 付款信息、税务信息、无关地区账号资料 | 02-mainland-availability.png |
| `AppStoreConnect/ASC-04-app-privacy.png` | Tracking 为 No、Data Linked to You / Data Not Linked to You、Health and Fitness / Usage Data / Diagnostics 填写结果 | Apple ID 邮箱、账号私密信息 | 04-privacy-label.png |
| `AppStoreConnect/ASC-05-age-rating.png` | 4+ 或 App Store Connect 自动计算结果、Kids Category 未选择、Regulated Medical Device 为 No | Apple ID 邮箱、电话、付款信息 | 17-age-rating-result |
| `AppStoreConnect/ASC-06-review-information.png` | Sign-in required、恢复密钥测试账号说明、审核备注、联系人字段已填 | 恢复密钥、验证码、完整手机号、Apple ID 邮箱、联系人完整电话 | 11-test-account-redacted.json |
| `AppStoreConnect/ASC-07-build-testflight-link.png` | 选中 build、TestFlight 构建状态、版本和 build 与真机回归一致 | 测试员邮箱、Apple ID 邮箱、内部备注 | 06-testflight.png 和 12-real-device-regression.md |
| `AppStoreConnect/ASC-08-submit-review-precheck.png` | Submit for Review 前页面无未处理警告 | 恢复密钥、验证码、完整手机号、AppSecret、证书私钥、Apple ID 邮箱 | check_app_store_connect_materials.py、check_app_store_evidence.py --allow-incomplete、check_launch_objective_audit.py --allow-incomplete |

## Submit for Review 总守卫

点击 Submit for Review 前必须先在本机生成同一天同一轮的小奶瓶提交 proof 组。只有下面 proof 全部为真，才允许点击提交审核；任一项为红时，只能保存草稿和归档页面回填证据。

```bash
python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json
python3 Backend/scripts/check_launch_objective_audit.py --allow-incomplete --output Backend/proof/launch-objective-audit.json
python3 Backend/scripts/check_production_readiness.py --require-huawei-obs --require-screenshots --require-app-store-evidence --allow-incomplete --output Backend/proof/production-readiness.json
python3 Backend/scripts/check_testflight_regression_plan.py --allow-incomplete --output Backend/proof/testflight-regression-plan.json
python3 Backend/scripts/check_provider_evidence_materials.py --output Backend/proof/provider-evidence-materials.json
python3 Backend/scripts/check_mainland_filing_materials.py --output Backend/proof/mainland-filing-materials.json
python3 Backend/scripts/check_signed_archive_testflight_materials.py --output Backend/proof/signed-archive-testflight-materials.json
```

- [ ] `Backend/proof/launch-objective-audit.json` 的 `ready=true`。
- [ ] `Backend/proof/production-readiness.json` 的 `ready=true`。
- [ ] `Backend/proof/app-store-evidence.json` 的 `ready=true`，且真实 App Store / 外部平台 / TestFlight / iOS 26.5 真机证据均已归档。
- [ ] `Backend/proof/testflight-regression-plan.json` 的 `passed=true`。
- [ ] `Backend/proof/provider-evidence-materials.json` 的 `passed=true`。
- [ ] `Backend/proof/mainland-filing-materials.json` 的 `passed=true`。
- [ ] `Backend/proof/signed-archive-testflight-materials.json` 的 `passed=true`。
- [ ] 如果 `ready=false`、`passed=false` 或仍有 `failedRequiredChecks` / `missingEvidence`，不点击 Submit for Review。

## 人工填写后回填验收模板

- [ ] App Store Connect 页面值已逐项对照。
- [ ] `AppStoreConnect/ASC-01-app-information.png` 到 `AppStoreConnect/ASC-08-submit-review-precheck.png` 已按页面回填证据索引归档并脱敏。
- [ ] App 名称 / 副标题 / 描述 / 关键词 / 主类别 / 第二类别 与源文件一致。
- [ ] 隐私政策 URL / 技术支持 URL / 用户协议 URL 与源文件一致。
- [ ] App Privacy / 年龄分级 / 审核备注 与答案表一致。
- [ ] App Store Connect 选中 build 与 `06-testflight.png`、`12-real-device-regression.md` 和 `APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md` 一致。
- [ ] 截图上传顺序与 `10-final-screenshots/`、`APP_STORE_EVIDENCE_CHECKLIST_20260627.md` 和 `SCREENSHOT_PLAN.md` 一致。
- [ ] 价格、首发地区和手动发布设置与 `APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md` 和 `02-mainland-availability.png` 一致。
- [ ] `production-readiness.json`、`launch-objective-audit.json`、`app-store-evidence.json` 均为 ready=true。
- [ ] `testflight-regression-plan.json`、`provider-evidence-materials.json`、`mainland-filing-materials.json`、`signed-archive-testflight-materials.json` 均为 passed=true。
- [ ] 若任一页面值与源文件不一致，先修正 App Store Connect 或源文件，再重跑本页复跑命令；不提交审核。
- [ ] 回填记录不得写入恢复密钥、验证码、AppSecret、D-U-N-S 编码完整值、Apple ID 邮箱、完整手机号或测试员邮箱。

## 复跑命令

check_app_store_connect_materials.py
check_app_store_evidence.py --allow-incomplete
check_testflight_regression_plan.py --allow-incomplete
check_provider_evidence_materials.py
check_mainland_filing_materials.py
check_signed_archive_testflight_materials.py
check_launch_objective_audit.py --allow-incomplete
production-readiness.json
launch-objective-audit.json

## 禁写和提交边界

不得写入恢复密钥。
不得写入验证码。
不得写入 AppSecret。
不得写入 D-U-N-S 编码完整值。
不得写入证书私钥。
不得声称完成，除非对应真实文件已归档并通过 gate。
不得在小奶瓶提交 proof 组存在 `ready=false` 或 `passed=false` 时点击 Submit for Review。
""".lstrip()


def valid_privacy_label() -> dict:
    return {
        "app": {
            "name": "小奶瓶",
            "bundleId": "com.mewpow.xiaonaiping",
            "targetsChildrenDirectly": False,
            "containsThirdPartyAdvertising": False,
            "containsThirdPartyAnalytics": False,
            "usesTracking": False,
        },
        "privacyPolicyUrl": "https://api.mewpow.com/xiaonaiping/privacy",
        "supportUrl": "https://api.mewpow.com/xiaonaiping/support",
        "dataCategories": [
            {
                "category": "Identifiers",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
            },
            {
                "category": "Contact Info",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
            },
            {
                "category": "User Content",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
            },
            {
                "category": "Photos or Videos",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
            },
            {
                "category": "Health and Fitness",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["App Functionality"],
                "notes": "User-entered baby care records only. No HealthKit, sensors, hospital records, stress detection, medical interpretation, health advice, pressure reminders, feeding advice, or medical diagnosis. Live Activity and widgets are status display only.",
            },
            {
                "category": "Usage Data",
                "collected": True,
                "linkedToUser": True,
                "usedForTracking": False,
                "purposes": ["Analytics"],
                "notes": "No baby content, photos, phone numbers, WeChat identifiers, advertising ID, or device fingerprint.",
            },
            {
                "category": "Diagnostics",
                "collected": True,
                "linkedToUser": False,
                "usedForTracking": False,
                "purposes": ["App Functionality", "Analytics"],
            },
        ],
    }


def valid_screenshot_plan() -> str:
    return """
# SCREENSHOT_PLAN.md

## 当前截图命令

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Debug -sdk iphonesimulator26.5 -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -derivedDataPath /tmp/XiaoNaiPing-DebugScreenshots-26_5 CODE_SIGNING_ALLOWED=NO build
SIMCTL_CHILD_XNP_API_BASE_URL=https://api.mewpow.com/xiaonaiping python3 Backend/scripts/capture_ios_screenshots.py --device IOS_26_5_SIMULATOR_UDID --app /tmp/XiaoNaiPing-DebugScreenshots-26_5/Build/Products/Debug-iphonesimulator/XiaoNaiPing.app --output-dir /tmp/xnp-debug-prod-screenshots-26_5 --tabs home record growth profile profile-sync --settle-seconds 2.5 --shutdown
```

## 仍需补齐

1. TestFlight 或签名真机包最终截图。
2. 正式提交前仍需用 iOS 26.5 TestFlight 或签名真机包归档最终截图。

## App Store Connect 截图上传矩阵

官方规格：https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/ 。App Store Connect 截图上传每个设备槽位为一到十张，格式只能使用 `.jpeg`、`.jpg`、`.png`。

| 槽位 | 当前状态 | 下一步 |
|---|---|---|
| iPhone 6.9" display | 官方可接受竖图尺寸包含 1260 x 2736、1290 x 2796、1320 x 2868 | 用 iOS 26.5 TestFlight 或签名真机包补最终截图，上传后归档 `AppStoreConnect/ASC-02-version-information.png` |
| 当前候选图 | 当前候选为 iPhone 17 Pro Max / iPhone 6.9" display / 1320 x 2868 | 只作为画面顺序、文案和尺寸候选；不能把 Debug simulator 候选图声称为 TestFlight、签名真机或 App Store Connect 上传最终证据 |
| 候选来源 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/PROVENANCE.json` | 保留 iOS 26.5、截图 seed data 和生产 API URL injection 证明，但不替代 TestFlight 或签名真机包最终证据 |
| iPad 槽位 | 工程目标为 iPhone only，`TARGETED_DEVICE_FAMILY=1` | 如果 App Store Connect 要求 iPad 截图，先复核工程 target family、Bundle ID capabilities 和 App Store Connect 平台设置，不临时上传拉伸图 |
""".lstrip()


def write_valid_materials(root: Path) -> None:
    write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md", valid_fill_sheet())
    write(root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md", valid_copy_paste_packet())
    write(root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json", valid_app_store_connect_draft_json())
    write(
        root / "Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260627.json",
        valid_app_store_connect_field_freeze_packet(),
    )
    write(
        root / "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
        valid_app_store_connect_entry_session_packet(),
    )
    write(
        root / "Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260627.json",
        valid_app_store_connect_submit_review_preflight_packet(),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-BACKFILL-RESULT.template.json",
        valid_asc_backfill_result_template(),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-PRIVACY-AGE-REVIEW-RESULT.template.json",
        valid_asc_privacy_age_review_result_template(),
    )
    write(root / "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md", valid_review_information_packet())
    write(
        root / "Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260627.json",
        valid_app_review_test_account_packet(),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
        json.dumps(
            {
                "createdAt": "2026-06-25T12:28:11+00:00",
                "baseUrl": "https://api.mewpow.com/xiaonaiping",
                "accountId": "9704886c-58cb-4b5d-9cb2-d97a0dfaa515",
                "recoveryKeyStored": ".env.xnp-review-account",
                "recoveryVerified": True,
                "syncSeeded": True,
                "containsSecret": False,
            },
            ensure_ascii=False,
        ),
    )
    write(root / "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md", valid_privacy_answers())
    write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md", valid_age_rating_answers())
    write(root / "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md", valid_version_release_settings())
    write(root / "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md", valid_final_entry_audit())
    write(root / "Docs/08_Release/APP_STORE_METADATA.md", valid_metadata())
    write(
        root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        json.dumps(valid_privacy_label(), ensure_ascii=False),
    )
    write(root / "Docs/08_Release/SCREENSHOT_PLAN.md", valid_screenshot_plan())
    write(
        root / "App/iOS/XiaoNaiPing/Views/FeedingRecordView.swift",
        'Text("会提前5分钟提醒准备泡奶，Apple Watch 可跟随系统通知震动。")\n',
    )
    write(
        root / "App/iOS/XiaoNaiPing/zh-Hant-HK.lproj/Localizable.strings",
        '"会提前5分钟提醒准备泡奶，Apple Watch 可跟随系统通知震动。" = "會提前5分鐘提醒準備泡奶，Apple Watch 可跟隨系統通知震動。";\n',
    )


class AppStoreConnectMaterialsTest(unittest.TestCase):
    def run_checker(self, root: Path, expected_material_date: str | None = "20260627") -> dict:
        output = root / "Backend/proof/app-store-connect-materials.json"
        command = [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(root),
            "--output",
            str(output),
            "--allow-incomplete",
        ]
        if expected_material_date is not None:
            command.extend(["--expected-material-date", expected_material_date])
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("App Store Connect materials", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_default_run_requires_current_material_date(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)

            report = self.run_checker(root, expected_material_date=None)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectMaterialDateCurrent", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectMaterialDateCurrent"]["evidence"]
            self.assertIn("selected material date 20260627", evidence)
            self.assertIn("expected 20260704", evidence)

    def test_valid_materials_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_app_store_connect_draft_json_must_match_fill_sheet_and_submission_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            draft = json.loads(valid_app_store_connect_draft_json())
            draft["appInformation"]["subtitle"] = "宝宝健康助手"
            draft["versionInformation"]["keywords"] = "宝宝,健康,医疗"
            draft["ageRating"]["boundaries"].remove("no automatic feeding inference")
            draft["appPrivacy"]["usesTracking"] = True
            draft["reviewNotes"]["debugCodeAllowed"] = True
            draft["reviewNotes"]["boundaryChecklist"]["manualDeferralOptions"] = ["+5 分钟"]
            draft["reviewNotes"]["boundaryChecklist"]["deferralPersistenceBoundary"] = "新增持久化顺延字段"
            draft["submissionBoundary"]["canSubmitFromThisDraft"] = True
            draft["submissionBoundary"]["requiresBeforeSubmit"] = ["production-readiness.json ready=true"]
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
                json.dumps(draft, ensure_ascii=False),
            )

            report = self.run_checker(root, expected_material_date="20260628")

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectDraftJsonMatchesFillSheet", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectDraftJsonMatchesFillSheet"]["evidence"]
            self.assertIn("appInformation.subtitle must be 温柔记录宝宝每一天", evidence)
            self.assertIn("versionInformation.keywords differs from fill sheet", evidence)
            self.assertIn("ageRating boundary missing no automatic feeding inference", evidence)
            self.assertIn("appPrivacy.usesTracking must be false", evidence)
            self.assertIn("reviewNotes.debugCodeAllowed must be false", evidence)
            self.assertIn("reviewNotes.boundaryChecklist.manualDeferralOptions must be", evidence)
            self.assertIn("reviewNotes.boundaryChecklist.deferralPersistenceBoundary must be", evidence)
            self.assertIn("submissionBoundary.canSubmitFromThisDraft must be false", evidence)
            self.assertIn("submissionBoundary missing D-U-N-S", evidence)

    def test_app_store_connect_draft_json_field_limits_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            draft = json.loads(valid_app_store_connect_draft_json())
            draft["appInformation"]["appName"] = "a" * 31
            draft["appInformation"]["subtitle"] = "a" * 31
            draft["versionInformation"]["keywords"] = "宝宝记录," + ("育儿" * 40)
            draft["versionInformation"]["promotionalText"] = "a" * 171
            draft["versionInformation"]["description"] = "a" * 4001
            draft["versionInformation"]["whatsNew"] = "a" * 4001
            draft["reviewNotes"]["text"] = {"pasteText": ["a" * 4001]}
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
                json.dumps(draft, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectDraftJsonMatchesFillSheet", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectDraftJsonMatchesFillSheet"]["evidence"]
            self.assertIn("appInformation.appName exceeds 30 characters", evidence)
            self.assertIn("appInformation.subtitle exceeds 30 characters", evidence)
            self.assertIn("versionInformation.keywords exceeds 100 UTF-8 bytes", evidence)
            self.assertIn("versionInformation.promotionalText exceeds 170 characters", evidence)
            self.assertIn("versionInformation.description exceeds 4000 characters", evidence)
            self.assertIn("versionInformation.whatsNew exceeds 4000 characters", evidence)
            self.assertIn("reviewNotes.text exceeds 4000 characters", evidence)

    def test_app_store_connect_draft_rejects_reordered_submission_boundary_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            draft = json.loads(valid_app_store_connect_draft_json())
            requirements = draft["submissionBoundary"]["requiresBeforeSubmit"]
            draft["submissionBoundary"]["requiresBeforeSubmit"] = [
                requirements[1],
                requirements[0],
                *requirements[2:],
                requirements[-1],
            ]
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
                json.dumps(draft, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectDraftJsonMatchesFillSheet", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectDraftJsonMatchesFillSheet"]["evidence"]
            self.assertIn(
                "submissionBoundary.requiresBeforeSubmit duplicate iOS 26.5 TestFlight or signed real-device regression completed",
                evidence,
            )
            self.assertIn(
                "submissionBoundary.requiresBeforeSubmit order must match launch submission blocker order",
                evidence,
            )

    def test_app_store_connect_materials_reject_placeholder_filing_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet() + "\n备案号：ICP备000000号\n",
            )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
                valid_copy_paste_packet() + "\nplaceholder filing\n",
            )
            draft = json.loads(valid_app_store_connect_draft_json())
            draft["reviewNotes"]["text"] += "\n备案号：ICP备000000号"
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
                json.dumps(draft, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("copyPastePacketCompleteAndRedacted", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectDraftJsonMatchesFillSheet", report["failedRequiredChecks"])
            self.assertIn("reviewAccountInstructionsRedacted", report["failedRequiredChecks"])
            self.assertIn(
                "placeholderFilingNumber",
                report["checks"]["copyPastePacketCompleteAndRedacted"]["evidence"],
            )
            self.assertIn(
                "placeholderFilingNumber",
                report["checks"]["appStoreConnectDraftJsonMatchesFillSheet"]["evidence"],
            )
            self.assertIn(
                "placeholderFilingNumber",
                report["checks"]["reviewAccountInstructionsRedacted"]["evidence"],
            )

    def test_copy_paste_app_information_must_match_fill_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            copy_paste = valid_copy_paste_packet()
            copy_paste = copy_paste.replace("价格：免费\n", "")
            copy_paste = copy_paste.replace(
                "技术支持 URL：https://api.mewpow.com/xiaonaiping/support",
                "技术支持 URL：https://example.com/support",
            )
            write(root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md", copy_paste)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("copyPasteAppInformationMatchesFillSheet", report["failedRequiredChecks"])
            evidence = report["checks"]["copyPasteAppInformationMatchesFillSheet"]["evidence"]
            self.assertIn("App 信息 copy-paste field order must match fill sheet entry order", evidence)
            self.assertIn("App 信息.价格 missing from copy-paste packet", evidence)
            self.assertIn(
                "App 信息.技术支持 URL copy value must be https://api.mewpow.com/xiaonaiping/support",
                evidence,
            )

    def test_app_store_connect_draft_page_evidence_map_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            draft = json.loads(valid_app_store_connect_draft_json())
            page_map = draft["pageEvidenceMap"]
            page_map["status"] = "submission-evidence"
            page_map["doesNotReplace"].remove("05-signed-archive.png")
            page_map["items"][0]["redact"].remove("D-U-N-S 编码完整值")
            page_map["items"] = [
                item
                for item in page_map["items"]
                if item["file"] != "AppStoreConnect/ASC-06-review-information.png"
            ]
            page_map["items"][-1]["crossCheck"] = [
                "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json"
            ]
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
                json.dumps(draft, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectDraftPageEvidenceMapComplete", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectDraftPageEvidenceMapComplete"]["evidence"]
            self.assertIn("pageEvidenceMap.status must be post-fill-page-evidence-only", evidence)
            self.assertIn("pageEvidenceMap.doesNotReplace missing 05-signed-archive.png", evidence)
            self.assertIn("ASC-01-app-information.png.redact missing D-U-N-S 编码完整值", evidence)
            self.assertIn("pageEvidenceMap.items missing AppStoreConnect/ASC-06-review-information.png", evidence)
            self.assertIn("ASC-08-submit-review-precheck.png.crossCheck missing", evidence)

    def test_app_store_connect_draft_field_audit_matrix_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            draft = json.loads(valid_app_store_connect_draft_json())
            matrix = draft["fieldAuditMatrix"]
            matrix["rules"] = ["人工填写 App Store Connect 时只能从本矩阵列出的源文件复制。"]
            matrix["rows"] = [
                row
                for row in matrix["rows"]
                if row["id"] not in {"reviewNotes", "termsUrl"}
            ]
            matrix["rows"][0]["blockerProofs"].remove("D-U-N-S delivered")
            matrix["rows"][2]["mustKeepBoundary"].remove("手动顺延下一次提醒")
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
                json.dumps(draft, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectDraftFieldAuditMatrixComplete", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectDraftFieldAuditMatrixComplete"]["evidence"]
            self.assertIn("fieldAuditMatrix rule missing 不得只改 App Store Connect 页面而不回写源文件", evidence)
            self.assertIn("fieldAuditMatrix.appName missing D-U-N-S delivered", evidence)
            self.assertIn("fieldAuditMatrix.description missing 手动顺延下一次提醒", evidence)
            self.assertIn("fieldAuditMatrix.rows missing termsUrl", evidence)
            self.assertIn("fieldAuditMatrix.rows missing reviewNotes", evidence)

    def test_app_store_connect_draft_field_audit_matrix_rejects_mismatched_values(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            draft = json.loads(valid_app_store_connect_draft_json())
            rows = {row["id"]: row for row in draft["fieldAuditMatrix"]["rows"]}
            rows["category"]["value"] = "主类别：健康健美；第二类别：生活"
            rows["privacyPolicyUrl"]["field"] = "隐私网址"
            rows["supportUrl"]["value"] = "https://example.com/support"
            rows["reviewNotes"]["valueSource"] = "reviewInformation.notes"
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
                json.dumps(draft, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectDraftFieldAuditMatrixComplete", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectDraftFieldAuditMatrixComplete"]["evidence"]
            self.assertIn("fieldAuditMatrix.category.value must be 主类别：生活；第二类别：留空", evidence)
            self.assertIn("fieldAuditMatrix.privacyPolicyUrl.field must be 隐私政策 URL", evidence)
            self.assertIn("fieldAuditMatrix.supportUrl.value must be https://api.mewpow.com/xiaonaiping/support", evidence)
            self.assertIn("fieldAuditMatrix.reviewNotes.valueSource must be reviewNotes.text", evidence)

    def test_app_store_connect_field_freeze_packet_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            packet = json.loads(valid_app_store_connect_field_freeze_packet())
            packet["canSubmitFromThisPacket"] = True
            packet["sourceFiles"]["copyPastePacket"] = "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE.md"
            packet["fieldFreezeRules"] = ["field-freeze-plan-not-evidence"]
            packet["fields"] = [
                field
                for field in packet["fields"]
                if field["id"] != "reviewNotes"
            ]
            next(field for field in packet["fields"] if field["id"] == "category")[
                "value"
            ] = "主类别：健康健美；第二类别：生活"
            next(field for field in packet["fields"] if field["id"] == "category").pop(
                "freezeAction"
            )
            next(field for field in packet["fields"] if field["id"] == "supportUrl")[
                "sourceFiles"
            ] = ["Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md"]
            packet["fieldSourceLockMatrix"] = [
                row
                for row in packet["fieldSourceLockMatrix"]
                if row["id"] != "reviewNotes"
            ]
            packet["fieldSourceLockMatrix"][0]["sourceObject"] = "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json"
            packet["fieldSourceLockMatrix"][1]["requiredMatches"] = ["field", "value"]
            packet["fieldSourceLockMatrix"][2]["matchesDraftRow"] = False
            packet["pasteSequenceMatrix"] = [
                row
                for row in packet["pasteSequenceMatrix"]
                if row["id"] != "reviewNotes"
            ]
            packet["pasteSequenceMatrix"][0]["initialStatus"] = "captured"
            next(row for row in packet["pasteSequenceMatrix"] if row["id"] == "category")[
                "ascPage"
            ] = "ASC-03 Pricing and Availability"
            next(row for row in packet["pasteSequenceMatrix"] if row["id"] == "ageRating")[
                "inputType"
            ] = "text"
            next(row for row in packet["pasteSequenceMatrix"] if row["id"] == "privacyPolicyUrl")[
                "copySource"
            ] = "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json"
            packet["fieldBudgetMatrix"] = [
                row
                for row in packet["fieldBudgetMatrix"]
                if row["id"] != "reviewNotes"
            ]
            packet["fieldBudgetMatrix"][2]["used"] = 101
            packet["fieldBudgetMatrix"][2]["remaining"] = -1
            packet["fieldBudgetMatrix"][2]["withinLimit"] = False
            packet["postFreezeGates"] = [
                gate for gate in packet["postFreezeGates"] if "check_app_store_submission_packet.py" not in gate
            ]
            packet["completionRule"] = "done"
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260627.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectFieldFreezePacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectFieldFreezePacketValid"]["evidence"]
            self.assertIn("canSubmitFromThisPacket must be False", evidence)
            self.assertIn("sourceFiles.copyPastePacket must be Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md", evidence)
            self.assertIn("fieldFreezeRules missing 不得现场改字后只改 App Store Connect 页面", evidence)
            self.assertIn("fields.category.value must be 主类别：生活；第二类别：留空", evidence)
            self.assertIn("fields.category missing freezeAction source-file rewrite boundary", evidence)
            self.assertIn("fields missing reviewNotes", evidence)
            self.assertIn("fieldSourceLockMatrix order must match App Store Connect field order", evidence)
            self.assertIn(
                "fieldSourceLockMatrix.appName.sourceObject must be "
                "'Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json:fieldAuditMatrix.rows.appName'",
                evidence,
            )
            self.assertIn(
                "fieldSourceLockMatrix.subtitle.requiredMatches must be "
                "['field', 'value', 'sourceFiles', 'ascEvidence', 'blockerProofs', 'redact']",
                evidence,
            )
            self.assertIn("fieldSourceLockMatrix.description.matchesDraftRow must be True", evidence)
            self.assertIn(
                "fieldSourceLockMatrix.supportUrl.sourceFiles must match draft fieldAuditMatrix row",
                evidence,
            )
            self.assertIn("fieldSourceLockMatrix missing reviewNotes", evidence)
            self.assertIn("pasteSequenceMatrix order must match App Store Connect field order", evidence)
            self.assertIn("pasteSequenceMatrix.appName.initialStatus must be 'pending'", evidence)
            self.assertIn("pasteSequenceMatrix.category.ascPage must be 'ASC-01 App Information'", evidence)
            self.assertIn("pasteSequenceMatrix.ageRating.inputType must be 'questionnaire'", evidence)
            self.assertIn(
                "pasteSequenceMatrix.privacyPolicyUrl.copySource must be 'Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md'",
                evidence,
            )
            self.assertIn("pasteSequenceMatrix missing reviewNotes", evidence)
            self.assertIn("fieldBudgetMatrix order must match App Store Connect text budget order", evidence)
            self.assertIn("fieldBudgetMatrix.keywords.used must be 73", evidence)
            self.assertIn("fieldBudgetMatrix missing reviewNotes", evidence)
            self.assertIn("postFreezeGates missing check_app_store_submission_packet.py", evidence)
            self.assertIn("completionRule missing not submission permission", evidence)

    def test_app_store_connect_draft_field_audit_matrix_rejects_duplicate_or_reordered_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            draft = json.loads(valid_app_store_connect_draft_json())
            rows = draft["fieldAuditMatrix"]["rows"]
            draft["fieldAuditMatrix"]["rows"] = [
                rows[1],
                rows[0],
                *rows[2:],
                dict(rows[-1]),
            ]
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260627.json",
                json.dumps(draft, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectDraftFieldAuditMatrixComplete", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectDraftFieldAuditMatrixComplete"]["evidence"]
            self.assertIn("fieldAuditMatrix.rows duplicate reviewNotes", evidence)
            self.assertIn("fieldAuditMatrix.rows order must match App Store Connect field order", evidence)

    def test_app_store_connect_entry_session_packet_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            packet = json.loads(valid_app_store_connect_entry_session_packet())
            packet["canSubmitFromThisPacket"] = True
            del packet["sourceFiles"]["executionSheet"]
            del packet["targetPageEvidenceFiles"]["reviewInformation"]
            packet["pageEvidenceFileChecks"] = [
                item
                for item in packet["pageEvidenceFileChecks"]
                if item["artifactId"] != "reviewInformation"
            ]
            packet["pageEvidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-01-app-info-copy.png"
            packet["pageEvidenceFileChecks"][0]["sha256"] = "already-filled"
            packet["pageEvidenceFileChecks"][0]["redactionChecked"] = True
            packet["pageEvidenceFileChecks"][0]["sameRoundAsEntrySession"] = True
            packet["pageEvidenceFileChecks"][0]["matchesFieldSourceLocks"] = True
            packet["pageEvidenceFileChecks"][0]["realPageEvidenceNotTemplate"] = True
            packet["fieldSourceLocks"] = [
                lock for lock in packet["fieldSourceLocks"] if lock["id"] != "keywords"
            ]
            packet["entrySequence"] = [
                step for step in packet["entrySequence"] if step["id"] != "capturePostFillPages"
            ]
            packet["stopConditions"].remove("productionReadinessStillRed")
            packet["postEntryGates"] = [
                gate
                for gate in packet["postEntryGates"]
                if "check_launch_objective_audit.py" not in gate["command"]
            ]
            packet["completionRule"] = "done"
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
                json.dumps(packet, ensure_ascii=False),
            )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
                valid_final_entry_audit().replace("APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectEntrySessionPacketReferenced", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectEntrySessionPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectEntrySessionPacketValid"]["evidence"]
            self.assertIn("canSubmitFromThisPacket must be False", evidence)
            self.assertIn("sourceFiles.executionSheet must be", evidence)
            self.assertIn("targetPageEvidenceFiles.reviewInformation must be", evidence)
            self.assertIn("pageEvidenceFileChecks order must match targetPageEvidenceFiles", evidence)
            self.assertIn("pageEvidenceFileChecks.reviewInformation missing object", evidence)
            self.assertIn(
                "pageEvidenceFileChecks.appInformation.target must be Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-01-app-information.png",
                evidence,
            )
            self.assertIn("pageEvidenceFileChecks.appInformation.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("pageEvidenceFileChecks.appInformation.redactionChecked must be False", evidence)
            self.assertIn("pageEvidenceFileChecks.appInformation.sameRoundAsEntrySession must be False", evidence)
            self.assertIn("pageEvidenceFileChecks.appInformation.matchesFieldSourceLocks must be False", evidence)
            self.assertIn("pageEvidenceFileChecks.appInformation.realPageEvidenceNotTemplate must be False", evidence)
            self.assertIn("fieldSourceLocks missing keywords", evidence)
            self.assertIn("entrySequence missing capturePostFillPages", evidence)
            self.assertIn("stopConditions missing productionReadinessStillRed", evidence)
            self.assertIn("postEntryGates missing", evidence)
            self.assertIn("completion boundary missing entry-session-plan-not-evidence", evidence)

    def test_asc_backfill_result_template_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            template = json.loads(valid_asc_backfill_result_template())
            template["status"] = "captured-live-backfill"
            template["canSubmitAtCapture"] = True
            template["redactionReviewed"] = True
            template["sourceDocuments"] = [
                "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md"
            ]
            template["xiaonaipingSubmissionProofs"].pop("productionReadiness")
            template["fieldFreeze"]["sourceSnapshot"] = [
                "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md"
            ]
            template["fieldFreeze"]["screenshotsRefreshed"] = True
            template["fieldFreeze"]["rerunProofs"] = {
                "checkAppStoreConnectMaterials": "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json"
            }
            template["backfillSessionIntegrity"]["sessionFlags"]["allFieldsMatchFieldFreezePacket"] = True
            template["backfillSessionIntegrity"]["pageGroups"]["appInformation"] = [
                "appName",
                "subtitle",
                "category",
            ]
            template["backfillSessionIntegrity"]["pageEvidence"]["reviewInformation"] = (
                "AppStoreConnect/ASC-06-review-info-copy.png"
            )
            template["backfillSessionIntegrity"]["stopConditions"] = [
                item
                for item in template["backfillSessionIntegrity"]["stopConditions"]
                if item["id"] != "fieldChangedOnlyInAsc"
            ]
            template["appReviewInformationPrivateFieldChecks"]["targetPrivateEvidence"] = (
                "Docs/08_Release/AppStoreEvidence/16-private-copy.png"
            )
            template["appReviewInformationPrivateFieldChecks"]["recoveryKeyOnlyInPrivateField"] = True
            template["appReviewInformationPrivateFieldChecks"].pop("secretValuesNotRecorded")
            template["fieldEntryChecks"] = [
                entry
                for entry in template["fieldEntryChecks"]
                if entry["id"] != "reviewNotes"
            ]
            template["fieldEntryChecks"][3]["targetPage"] = "AppStoreConnect/ASC-01-app-information.png"
            template["fieldEntryChecks"][3]["sourceMatchesFieldFreeze"] = True
            template["evidenceFileChecks"] = [
                check
                for check in template["evidenceFileChecks"]
                if check["artifactId"] != "appPrivacy"
            ]
            template["evidenceFileChecks"][0]["target"] = (
                "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-01-copy.png"
            )
            template["evidenceFileChecks"][0]["sha256"] = "already-filled"
            template["evidenceFileChecks"][0]["sameSessionAsBackfill"] = True
            template["evidenceFileChecks"][0]["sourceIsAppStoreConnectEvidenceRoot"] = True
            template["evidenceFileChecks"][0]["fieldFreezeConfirmed"] = True
            template["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            template["screenshots"]["reviewInformation"]["screenshotFiles"] = [
                "ASC-06-review-info-copy.png"
            ]
            template["screenshots"]["submitReviewPrecheck"]["canSubmitTrueVisible"] = True
            write(
                root / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-BACKFILL-RESULT.template.json",
                json.dumps(template, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ascBackfillResultTemplateValid", report["failedRequiredChecks"])
            evidence = report["checks"]["ascBackfillResultTemplateValid"]["evidence"]
            self.assertIn("status must be template-not-evidence", evidence)
            self.assertIn("canSubmitAtCapture must be False", evidence)
            self.assertIn("redactionReviewed must be False", evidence)
            self.assertIn("sourceDocuments must match ASC copy, final audit, and XiaoNaiPing proofs", evidence)
            self.assertIn(
                "xiaonaipingSubmissionProofs must lock XiaoNaiPing App Store, production, audit, TestFlight, provider, filing, and signing proofs",
                evidence,
            )
            self.assertIn("fieldFreeze.sourceSnapshot must match sourceDocuments", evidence)
            self.assertIn("fieldFreeze.screenshotsRefreshed must be False", evidence)
            self.assertIn("fieldFreeze.rerunProofs must include XiaoNaiPing proof reruns", evidence)
            self.assertIn(
                "backfillSessionIntegrity.sessionFlags.allFieldsMatchFieldFreezePacket must be False",
                evidence,
            )
            self.assertIn(
                "backfillSessionIntegrity.pageGroups.appInformation must be appName, subtitle, category, privacyPolicyUrl, supportUrl, termsUrl",
                evidence,
            )
            self.assertIn(
                "backfillSessionIntegrity.pageEvidence must map ASC-01/02/05/06 to draft field evidence",
                evidence,
            )
            self.assertIn(
                "backfillSessionIntegrity.stopConditions missing fieldChangedOnlyInAsc",
                evidence,
            )
            self.assertIn(
                "appReviewInformationPrivateFieldChecks.targetPrivateEvidence must be Docs/08_Release/AppStoreEvidence/16-app-review-information-private.png",
                evidence,
            )
            self.assertIn(
                "appReviewInformationPrivateFieldChecks.recoveryKeyOnlyInPrivateField must be False",
                evidence,
            )
            self.assertIn(
                "appReviewInformationPrivateFieldChecks.secretValuesNotRecorded must be False",
                evidence,
            )
            self.assertIn("fieldEntryChecks order must match App Store Connect field order", evidence)
            self.assertIn("fieldEntryChecks.reviewNotes missing object", evidence)
            self.assertIn(
                "fieldEntryChecks.keywords.targetPage must be AppStoreConnect/ASC-02-version-information.png",
                evidence,
            )
            self.assertIn("fieldEntryChecks.keywords.sourceMatchesFieldFreeze must be False", evidence)
            self.assertIn("evidenceFileChecks order must match App Store Connect backfill workflow", evidence)
            self.assertIn("evidenceFileChecks.appPrivacy missing object", evidence)
            self.assertIn(
                "evidenceFileChecks.appInformation.target missing Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-01-app-information.png",
                evidence,
            )
            self.assertIn("evidenceFileChecks.appInformation.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("evidenceFileChecks.appInformation.sameSessionAsBackfill must be False", evidence)
            self.assertIn(
                "evidenceFileChecks.appInformation.sourceIsAppStoreConnectEvidenceRoot must be False",
                evidence,
            )
            self.assertIn("evidenceFileChecks.appInformation.fieldFreezeConfirmed must be False", evidence)
            self.assertIn("evidenceFileChecks.appInformation.secretValuesNotRecorded must be False", evidence)
            self.assertIn(
                "screenshots.reviewInformation.screenshotFiles must be ASC-06-review-information.png",
                evidence,
            )
            self.assertIn("screenshots.submitReviewPrecheck.canSubmitTrueVisible must be False", evidence)

    def test_asc_privacy_age_review_result_template_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            template = json.loads(valid_asc_privacy_age_review_result_template())
            template["status"] = "captured-live-privacy-age-review"
            template["canSubmitFromThisTemplate"] = True
            template["redactionReviewed"] = True
            template["sourceFiles"]["privacyAnswers"] = "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS.md"
            del template["targetEvidenceFiles"]["ageRatingResult"]
            template["evidenceFileChecks"] = [
                check
                for check in template["evidenceFileChecks"]
                if check["artifactId"] != "reviewAccountRedacted"
            ]
            template["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/ASC-04.png"
            template["evidenceFileChecks"][0]["sha256"] = "already-filled"
            template["evidenceFileChecks"][0]["sameSessionAsAscBackfill"] = True
            template["evidenceFileChecks"][0]["sourceMatchesAnswerSheet"] = True
            template["evidenceDependencyMatrix"] = [
                entry
                for entry in template["evidenceDependencyMatrix"]
                if entry["artifactId"] != "privacyLabelEvidence"
            ]
            template["evidenceDependencyMatrix"][1]["proves"] = ["age rating page visible"]
            template["evidenceDependencyMatrix"][3]["requiredBeforeCapturedLiveStatus"] = False
            template["evidenceDependencyMatrix"][3]["initialStatus"] = "captured"
            template["resultSections"] = [
                section for section in template["resultSections"] if section["id"] != "ageRating"
            ]
            template["resultSections"][0]["mustVerify"] = []
            template["stopConditions"].remove("reviewInformationSecretLeak")
            template["postResultGates"] = [
                gate for gate in template["postResultGates"] if "check_review_notes.py" not in gate
            ]
            template["completionRule"] = "done"
            write(
                root / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-PRIVACY-AGE-REVIEW-RESULT.template.json",
                json.dumps(template, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ascPrivacyAgeReviewResultTemplateValid", report["failedRequiredChecks"])
            evidence = report["checks"]["ascPrivacyAgeReviewResultTemplateValid"]["evidence"]
            self.assertIn("status must be template-not-evidence", evidence)
            self.assertIn("canSubmitFromThisTemplate must be False", evidence)
            self.assertIn("redactionReviewed must be False", evidence)
            self.assertIn(
                "sourceFiles.privacyAnswers must be Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md",
                evidence,
            )
            self.assertIn("targetEvidenceFiles.ageRatingResult must be Docs/08_Release/AppStoreEvidence/17-age-rating-result.png", evidence)
            self.assertIn("evidenceFileChecks order must match privacy/age/review target evidence workflow", evidence)
            self.assertIn("evidenceFileChecks.reviewAccountRedacted missing object", evidence)
            self.assertIn(
                "evidenceFileChecks.appPrivacyPage.target must be Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-04-app-privacy.png",
                evidence,
            )
            self.assertIn("evidenceFileChecks.appPrivacyPage.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("evidenceFileChecks.appPrivacyPage.sameSessionAsAscBackfill must be False", evidence)
            self.assertIn("evidenceFileChecks.appPrivacyPage.sourceMatchesAnswerSheet must be False", evidence)
            self.assertIn(
                "evidenceDependencyMatrix order must match privacy/age/review target evidence workflow",
                evidence,
            )
            self.assertIn("evidenceDependencyMatrix.privacyLabelEvidence missing object", evidence)
            self.assertIn(
                "evidenceDependencyMatrix.ageRatingPage.proves must be App Store Connect age rating answers page is visible, Kids Category is not selected, regulated medical device answer is No",
                evidence,
            )
            self.assertIn(
                "evidenceDependencyMatrix.reviewInformationPage.requiredBeforeCapturedLiveStatus must be True",
                evidence,
            )
            self.assertIn(
                "evidenceDependencyMatrix.reviewInformationPage.initialStatus must be pending",
                evidence,
            )
            self.assertIn("resultSections order must be appPrivacy, ageRating, reviewInformation", evidence)
            self.assertIn("resultSections.appPrivacy missing Tracking 为 No", evidence)
            self.assertIn("resultSections.ageRating missing object", evidence)
            self.assertIn("stopConditions missing reviewInformationSecretLeak", evidence)
            self.assertIn("postResultGates missing check_review_notes.py", evidence)
            self.assertIn("template missing privacy-age-review-result-template-not-evidence", evidence)

    def test_app_store_connect_entry_session_packet_rejects_duplicate_or_reordered_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            packet = json.loads(valid_app_store_connect_entry_session_packet())
            packet["entrySequence"] = [
                packet["entrySequence"][1],
                packet["entrySequence"][0],
                *packet["entrySequence"][2:],
                dict(packet["entrySequence"][-1]),
            ]
            packet["stopConditions"].append("privacyUrlMismatch")
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
                json.dumps(packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectEntrySessionPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectEntrySessionPacketValid"]["evidence"]
            self.assertIn("entrySequence duplicate id runPostEntryGates", evidence)
            self.assertIn("entrySequence order must match App Store Connect entry-session order", evidence)
            self.assertIn("stopConditions duplicate privacyUrlMismatch", evidence)

    def test_app_store_connect_submit_review_preflight_packet_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            packet = json.loads(valid_app_store_connect_submit_review_preflight_packet())
            packet["canSubmitFromThisPacket"] = True
            packet["sourceFiles"]["entrySessionPacket"] = "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET.json"
            del packet["targetPageEvidence"]["submitReviewPrecheck"]
            packet["mustBeGreenBeforeSubmit"] = [
                item
                for item in packet["mustBeGreenBeforeSubmit"]
                if item["id"] != "launchObjectiveAuditGreen"
            ]
            packet["mustBeGreenBeforeSubmit"][0]["requiredState"] = "ready=false"
            packet["mustBeGreenBeforeSubmit"][0]["redIfMissing"] = ["companyAccount"]
            packet["submissionDependencyMatrix"] = [
                item
                for item in packet["submissionDependencyMatrix"]
                if item["id"] != "launchObjectiveAuditGreen"
            ]
            packet["submissionDependencyMatrix"][0]["proves"] = ["ASC-08 page looks clean"]
            packet["submissionDependencyMatrix"][-2]["requiredBeforeSubmit"] = False
            packet["submissionDependencyMatrix"][-2]["initialStatus"] = "captured"
            packet["submitButtonDecision"]["expectedBeforeAllGreen"] = "click-submit-for-review"
            packet["submitButtonDecision"]["mustNotUseAsSubstituteFor"] = []
            packet["postPreflightGates"] = [
                gate for gate in packet["postPreflightGates"] if "check_launch_objective_audit.py" not in gate["command"]
            ]
            packet["completionRule"] = "done"
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260627.json",
                json.dumps(packet, ensure_ascii=False),
            )
            entry_packet = json.loads(valid_app_store_connect_entry_session_packet())
            del entry_packet["sourceFiles"]["submitReviewPreflight"]
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json",
                json.dumps(entry_packet, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectEntrySessionPacketValid", report["failedRequiredChecks"])
            self.assertIn("appStoreConnectSubmitReviewPreflightValid", report["failedRequiredChecks"])
            entry_evidence = report["checks"]["appStoreConnectEntrySessionPacketValid"]["evidence"]
            self.assertIn("sourceFiles.submitReviewPreflight must be", entry_evidence)
            evidence = report["checks"]["appStoreConnectSubmitReviewPreflightValid"]["evidence"]
            self.assertIn("canSubmitFromThisPacket must be False", evidence)
            self.assertIn("sourceFiles.entrySessionPacket must be Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260627.json", evidence)
            self.assertIn("targetPageEvidence.submitReviewPrecheck must be", evidence)
            self.assertIn("mustBeGreenBeforeSubmit order must match Submit for Review blocker order", evidence)
            self.assertIn("mustBeGreenBeforeSubmit missing launchObjectiveAuditGreen", evidence)
            self.assertIn("mustBeGreenBeforeSubmit.appStoreEvidenceReady.requiredState must be ready=true", evidence)
            self.assertIn("mustBeGreenBeforeSubmit.appStoreEvidenceReady missing realDeviceRegression", evidence)
            self.assertIn("submissionDependencyMatrix order must match Submit for Review dependency order", evidence)
            self.assertIn("submissionDependencyMatrix missing launchObjectiveAuditGreen", evidence)
            self.assertIn(
                "submissionDependencyMatrix.appStoreEvidenceReady.proves must be "
                "all required XiaoNaiPing App Store manual evidence files are archived and redaction-reviewed, "
                "company account, mainland availability, filing, privacy label, age rating result, signed archive, "
                "TestFlight, providers, final screenshots, and real-device evidence are indexed",
                evidence,
            )
            self.assertIn(
                "submissionDependencyMatrix.signedArchiveAndTestFlightReady.requiredBeforeSubmit must be True",
                evidence,
            )
            self.assertIn(
                "submissionDependencyMatrix.signedArchiveAndTestFlightReady.initialStatus must be pending",
                evidence,
            )
            self.assertIn("submitButtonDecision missing do-not-click-submit-for-review", evidence)
            self.assertIn("submitButtonDecision missing 08-wechat-open-platform.png", evidence)
            self.assertIn("postPreflightGates missing check_launch_objective_audit.py", evidence)
            self.assertIn("completion boundary missing not submission permission", evidence)

    def test_latest_dated_fill_sheet_is_used_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260626.md", "stale draft")
            write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md", valid_fill_sheet())

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertIn(
                "APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                report["checks"]["fillSheetPresent"]["evidence"],
            )

    def test_latest_fill_sheet_uses_same_dated_peer_materials_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)

            def current_day(text: str) -> str:
                return text.replace("20260627", "20260628").replace("2026-06-27", "2026-06-28")

            write(root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260628.md", valid_fill_sheet())
            write(root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260628.md", current_day(valid_copy_paste_packet()))
            write(root / "Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260628.json", valid_app_store_connect_draft_json("20260628"))
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260628.json",
                valid_app_store_connect_field_freeze_packet("20260628"),
            )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_ENTRY_SESSION_PACKET_20260628.json",
                valid_app_store_connect_entry_session_packet("20260628"),
            )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260628.json",
                valid_app_store_connect_submit_review_preflight_packet("20260628"),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-BACKFILL-RESULT.template.json",
                valid_asc_backfill_result_template("20260628"),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/AppStoreConnect/ASC-PRIVACY-AGE-REVIEW-RESULT.template.json",
                valid_asc_privacy_age_review_result_template("20260628"),
            )
            write(root / "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260628.md", current_day(valid_review_information_packet()))
            write(
                root / "Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260628.json",
                valid_app_review_test_account_packet("20260628"),
            )
            write(root / "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260628.md", current_day(valid_privacy_answers()))
            write(root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260628.md", current_day(valid_age_rating_answers()))
            write(root / "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260628.md", current_day(valid_version_release_settings()))
            write(root / "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260628.md", current_day(valid_final_entry_audit()))
            write(root / "Docs/08_Release/APP_STORE_METADATA.md", current_day(valid_metadata()))

            report = self.run_checker(root, expected_material_date="20260628")

            self.assertTrue(report["passed"])
            self.assertIn(
                "APP_STORE_CONNECT_FILL_SHEET_20260628.md",
                report["checks"]["fillSheetPresent"]["evidence"],
            )
            self.assertIn(
                "APP_STORE_CONNECT_COPY_PASTE_20260628.md",
                report["checks"]["copyPastePacketPresent"]["evidence"],
            )

    def test_metadata_must_reference_current_handoffs_and_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_METADATA.md",
                valid_metadata()
                .replace("日期：2026-06-27", "日期：2026-06-18")
                .replace("Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md", "")
                .replace("Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260627.md", "")
                .replace("Backend/proof/launch-objective-audit.json", "")
                .replace("iOS 26.5 TestFlight / 签名真机回归证据", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("metadataCurrentLaunchHandoffPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["metadataCurrentLaunchHandoffPresent"]["evidence"]
            self.assertIn("日期：2026-06-27", evidence)
            self.assertIn("Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md", evidence)
            self.assertIn("iOS 26.5 TestFlight / 签名真机回归证据", evidence)

    def test_metadata_description_must_cover_current_feeding_reminder_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_METADATA.md",
                valid_metadata()
                .replace("也可以在新增喂养后按 5 分钟一档手动顺延下一次提醒；", "")
                .replace("不會根據奶量、月齡、感測器或健康資料自動推算餵養時間。", "")
                .replace("manually defer it in 5-minute steps after adding a feeding", "defer reminders"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("metadataDraftDescriptionCoversCurrentReminderBehavior", report["failedRequiredChecks"])
            evidence = report["checks"]["metadataDraftDescriptionCoversCurrentReminderBehavior"]["evidence"]
            self.assertIn("也可以在新增喂养后按 5 分钟一档手动顺延下一次提醒", evidence)
            self.assertIn("不會根據奶量、月齡、感測器或健康資料自動推算餵養時間", evidence)
            self.assertIn("manually defer it in 5-minute steps after adding a feeding", evidence)

    def test_app_store_description_must_cover_current_feeding_reminder_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet()
                .replace("喝奶提醒可按 5 分钟一档手动顺延；", "")
                .replace("不根据奶量、月龄、传感器或健康数据自动推算喂养时间", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("descriptionCompleteAndWithinLimit", report["failedRequiredChecks"])
            evidence = report["checks"]["descriptionCompleteAndWithinLimit"]["evidence"]
            self.assertIn("5 分钟一档", evidence)
            self.assertIn("不根据奶量、月龄、传感器或健康数据自动推算喂养时间", evidence)

    def test_copy_paste_packet_must_cover_fields_and_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
                valid_copy_paste_packet()
                .replace("App 名称：小奶瓶", "")
                .replace("D-U-N-S 交付后必须回 Apple Developer 继续 Organization enrollment。", "")
                .replace("iOS 26.5 TestFlight 或 Xcode 签名真机包回归必须完成，模拟器和 iOS 27 不能替代。", "")
                + "\nXNP_REVIEW_RECOVERY_KEY=secret\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("copyPastePacketCompleteAndRedacted", report["failedRequiredChecks"])
            evidence = report["checks"]["copyPastePacketCompleteAndRedacted"]["evidence"]
            self.assertIn("App 名称：小奶瓶", evidence)
            self.assertIn("D-U-N-S 交付后必须回 Apple Developer 继续 Organization enrollment", evidence)
            self.assertIn("iOS 26.5 TestFlight 或 Xcode 签名真机包回归必须完成", evidence)
            self.assertIn("recoveryKeyAssignment", evidence)

    def test_copy_paste_packet_must_match_fill_sheet_draft_text(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
                valid_copy_paste_packet()
                .replace("小奶瓶是一款宝宝成长记录 App。", "小奶瓶是一款宝宝成长记录工具。")
                .replace("第一版：宝宝档案、日常记录、喝奶提醒与手动顺延、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。", "第一版：宝宝档案和日常记录。"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("copyPastePacketMatchesFillSheetDraft", report["failedRequiredChecks"])
            evidence = report["checks"]["copyPastePacketMatchesFillSheetDraft"]["evidence"]
            self.assertIn("描述: differs from fill sheet 描述", evidence)
            self.assertIn("新版本说明: differs from fill sheet 新版本说明", evidence)

    def test_review_information_packet_must_cover_private_fields_and_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
                valid_review_information_packet()
                .replace("Contact Information", "")
                .replace("review-recovery-key-account", "")
                .replace("不得声称手机号登录、微信登录、TestFlight、备案或 App Store 人工证据已完成", "")
                + "\nXNP_REVIEW_RECOVERY_KEY=secret\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("reviewInformationPacketCompleteAndRedacted", report["failedRequiredChecks"])
            evidence = report["checks"]["reviewInformationPacketCompleteAndRedacted"]["evidence"]
            self.assertIn("Contact Information", evidence)
            self.assertIn("review-recovery-key-account", evidence)
            self.assertIn("不得声称手机号登录、微信登录、TestFlight、备案或 App Store 人工证据已完成", evidence)
            self.assertIn("recoveryKeyAssignment", evidence)

    def test_review_information_must_keep_submission_blockers_separate_from_test_account_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
                valid_review_information_packet()
                .replace("## 提交前阻断项", "## 提交前重检")
                .replace("Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md", "")
                .replace("不能把恢复密钥测试账号当成上线完成证据", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("reviewInformationSubmissionBlockersPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["reviewInformationSubmissionBlockersPresent"]["evidence"]
            self.assertIn("## 提交前阻断项", evidence)
            self.assertIn("Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md", evidence)
            self.assertIn("不能把恢复密钥测试账号当成上线完成证据", evidence)

    def test_privacy_answers_must_map_app_store_privacy_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260627.md",
                valid_privacy_answers()
                .replace("Data Used to Track You", "")
                .replace("Health and Fitness 边界", "")
                .replace("04-privacy-label.png", "")
                + "\n13800138000\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyAnswersCompleteAndRedacted", report["failedRequiredChecks"])
            evidence = report["checks"]["privacyAnswersCompleteAndRedacted"]["evidence"]
            self.assertIn("Data Used to Track You", evidence)
            self.assertIn("Health and Fitness 边界", evidence)
            self.assertIn("04-privacy-label.png", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)

    def test_age_rating_answers_must_cover_kids_content_and_medical_device_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
                valid_age_rating_answers()
                .replace("Kids Category", "")
                .replace("User-generated public content", "")
                .replace("Regulated Medical Device", "")
                .replace("does not provide diagnosis, prevention, monitoring, treatment, disease prediction", "")
                + "\n13800138000\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ageRatingAnswersCompleteAndRedacted", report["failedRequiredChecks"])
            evidence = report["checks"]["ageRatingAnswersCompleteAndRedacted"]["evidence"]
            self.assertIn("Kids Category", evidence)
            self.assertIn("User-generated public content", evidence)
            self.assertIn("Regulated Medical Device", evidence)
            self.assertIn("does not provide diagnosis, prevention, monitoring, treatment, disease prediction", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)

    def test_age_rating_answer_sheet_must_be_referenced_by_app_store_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
                valid_copy_paste_packet().replace("Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md", ""),
            )
            write(
                root / "Docs/08_Release/APP_STORE_METADATA.md",
                valid_metadata().replace("Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("ageRatingAnswerSheetReferencedByDraft", report["failedRequiredChecks"])
            self.assertIn(
                "Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260627.md",
                report["checks"]["ageRatingAnswerSheetReferencedByDraft"]["evidence"],
            )

    def test_version_release_settings_must_cover_release_mode_and_compliance(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
                valid_version_release_settings()
                .replace("Manually release this version after App Review approval", "")
                .replace("Uses IDFA: No", "")
                .replace("02-mainland-availability.png", "")
                + "\n13800138000\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("versionReleaseSettingsCompleteAndRedacted", report["failedRequiredChecks"])
            evidence = report["checks"]["versionReleaseSettingsCompleteAndRedacted"]["evidence"]
            self.assertIn("Manually release this version after App Review approval", evidence)
            self.assertIn("Uses IDFA", evidence)
            self.assertIn("02-mainland-availability.png", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)

    def test_version_release_settings_whats_new_must_match_fill_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_VERSION_RELEASE_SETTINGS_20260627.md",
                valid_version_release_settings().replace(
                    "第一版：宝宝档案、日常记录、喝奶提醒与手动顺延、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。",
                    "第一版：宝宝档案、日常记录、成长记录、疫苗提醒、照片时间线、恢复密钥账号同步恢复和云端账号删除。",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("versionReleaseSettingsMatchesFillSheetWhatsNew", report["failedRequiredChecks"])
            evidence = report["checks"]["versionReleaseSettingsMatchesFillSheetWhatsNew"]["evidence"]
            self.assertIn("What's New differs from fill sheet 新版本说明", evidence)

    def test_final_entry_audit_must_map_fields_evidence_and_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
                valid_final_entry_audit()
                .replace("App Store Connect 选中的 build", "")
                .replace("APP_STORE_AGE_RATING_ANSWERS_20260627.md", "")
                .replace("https://api.mewpow.com/xiaonaiping/privacy", "")
                .replace("17-age-rating-result", "")
                .replace("## 人工填写后回填验收模板", "")
                .replace("App Store Connect 页面值已逐项对照", "")
                .replace("若任一页面值与源文件不一致，先修正 App Store Connect 或源文件，再重跑本页复跑命令；不提交审核", "")
                .replace("不得写入恢复密钥", "")
                + "\nXNP_REVIEW_RECOVERY_KEY=secret\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalEntryAuditCompleteAndRedacted", report["failedRequiredChecks"])
            evidence = report["checks"]["finalEntryAuditCompleteAndRedacted"]["evidence"]
            self.assertIn("App Store Connect 选中的 build", evidence)
            self.assertIn("APP_STORE_AGE_RATING_ANSWERS_20260627.md", evidence)
            self.assertIn("https://api.mewpow.com/xiaonaiping/privacy", evidence)
            self.assertIn("17-age-rating-result", evidence)
            self.assertIn("## 人工填写后回填验收模板", evidence)
            self.assertIn("App Store Connect 页面值已逐项对照", evidence)
            self.assertIn("若任一页面值与源文件不一致", evidence)
            self.assertIn("不得写入恢复密钥", evidence)
            self.assertIn("recoveryKeyAssignment", evidence)

    def test_final_entry_page_evidence_index_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
                valid_final_entry_audit()
                .replace("## App Store Connect 页面回填证据索引", "## 页面证据")
                .replace("AppStoreConnect/ASC-06-review-information.png", "AppStoreConnect/review-info.png")
                .replace("恢复密钥、验证码、完整手机号、Apple ID 邮箱、联系人完整电话", "账号信息")
                .replace("check_app_store_evidence.py --allow-incomplete", "check_app_store_evidence.py")
                .replace("`AppStoreConnect/ASC-01-app-information.png` 到 `AppStoreConnect/ASC-08-submit-review-precheck.png` 已按页面回填证据索引归档并脱敏。", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalEntryPageEvidenceIndexPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["finalEntryPageEvidenceIndexPresent"]["evidence"]
            self.assertIn("## App Store Connect 页面回填证据索引", evidence)
            self.assertIn("AppStoreConnect/ASC-06-review-information.png", evidence)
            self.assertIn("check_app_store_evidence.py --allow-incomplete", evidence)
            self.assertIn("已按页面回填证据索引归档并脱敏", evidence)

    def test_final_submit_review_guard_requires_xiaonaiping_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
                valid_final_entry_audit()
                .replace("## Submit for Review 总守卫", "## Submit 前检查")
                .replace("python3 Backend/scripts/check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json", "")
                .replace("`Backend/proof/testflight-regression-plan.json` 的 `passed=true`。", "")
                .replace("`Backend/proof/provider-evidence-materials.json` 的 `passed=true`。", "")
                .replace("`Backend/proof/mainland-filing-materials.json` 的 `passed=true`。", "")
                .replace("`Backend/proof/signed-archive-testflight-materials.json` 的 `passed=true`。", "")
                .replace("`passed=false`", "")
                .replace("`failedRequiredChecks` / `missingEvidence`", "")
                .replace("不点击 Submit for Review", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalSubmitReviewGuardRequiresXiaoNaiPingProofs", report["failedRequiredChecks"])
            evidence = report["checks"]["finalSubmitReviewGuardRequiresXiaoNaiPingProofs"]["evidence"]
            self.assertIn("## Submit for Review 总守卫", evidence)
            self.assertIn("`passed=true`", evidence)
            self.assertIn("不点击 Submit for Review", evidence)

    def test_final_field_source_consistency_lock_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
                valid_final_entry_audit()
                .replace("## 终填字段源文件一致性锁", "## 终填字段清单")
                .replace("App Store Connect 页面值不能成为唯一来源", "")
                .replace("关键词 / 描述 / 审核备注", "关键词")
                .replace("隐私政策 URL / 技术支持 URL / 用户协议 URL", "公开 URL")
                .replace("Backend/static/privacy.html", "")
                .replace("AppStoreConnect/ASC-05-age-rating.png", "AppStoreConnect/age-rating.png")
                .replace("不得只改 App Store Connect 页面而不回写源文件", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("finalFieldSourceConsistencyLockPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["finalFieldSourceConsistencyLockPresent"]["evidence"]
            self.assertIn("## 终填字段源文件一致性锁", evidence)
            self.assertIn("App Store Connect 页面值不能成为唯一来源", evidence)
            self.assertIn("关键词 / 描述 / 审核备注", evidence)
            self.assertIn("Backend/static/privacy.html", evidence)
            self.assertIn("不得只改 App Store Connect 页面而不回写源文件", evidence)

    def test_category_url_keywords_and_screenshots_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_METADATA.md",
                valid_metadata() + "\n| Category | Lifestyle or Health & Fitness; choose one before submission |\n",
            )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet()
                .replace("https://api.mewpow.com/xiaonaiping/support", "https://api.example.com/support")
                .replace("宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册", "宝宝记录," + "育儿" * 60)
                .replace("| 5 | `05-profile-sync-iphone16pro.png` | 主动同步，也能主动删除 | 同步删除。 |", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("metadataNoHealthFitnessCategoryAlternative", report["failedRequiredChecks"])
            self.assertIn("publicUrlsMatch", report["failedRequiredChecks"])
            self.assertIn("keywordsCompleteAndWithinLimit", report["failedRequiredChecks"])
            self.assertIn("screenshotCopyComplete", report["failedRequiredChecks"])

    def test_keywords_limit_counts_utf8_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet().replace(
                    "宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册",
                    "宝宝记录,育儿,喂奶,睡眠,尿布,成长记录,疫苗提醒,相册,轻柔记录记录记录记录记录记录",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("keywordsCompleteAndWithinLimit", report["failedRequiredChecks"])
            evidence = report["checks"]["keywordsCompleteAndWithinLimit"]["evidence"]
            self.assertIn("bytes=", evidence)

    def test_field_budget_tables_must_match_current_draft_lengths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            copy_paste = root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md"
            copy_paste.write_text(
                copy_paste.read_text(encoding="utf-8").replace("剩余 27 bytes", "剩余 99 bytes"),
                encoding="utf-8",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreConnectFieldBudgetTablesCurrent", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreConnectFieldBudgetTablesCurrent"]["evidence"]
            self.assertIn("copy paste packet", evidence)
            self.assertIn("| 关键词 | 100 UTF-8 bytes | 73 bytes | 剩余 27 bytes |", evidence)

    def test_screenshot_copy_rejects_medical_or_unavailable_login_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet()
                .replace("主动同步，也能主动删除", "微信登录成功，同步恢复")
                .replace("半夜也能低负担记录", "半夜喂养推荐")
                .replace("5. 微信登录未完成开放平台配置前，不截图暗示微信登录已经可用。\n", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("screenshotCopyAvoidsUnavailableOrMedicalClaims", report["failedRequiredChecks"])
            evidence = report["checks"]["screenshotCopyAvoidsUnavailableOrMedicalClaims"]["evidence"]
            self.assertIn("微信登录成功", evidence)
            self.assertIn("喂养推荐", evidence)
            self.assertIn("微信登录未完成开放平台配置前", evidence)

    def test_stale_current_proof_references_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet()
                .replace("Backend/proof/production-readiness.json", "Backend/proof/production-readiness-20260627T-current.json")
                .replace("Backend/proof/ios-app-bundle.json", "Backend/proof/ios-app-bundle-20260627T-current-ios265.json"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("blockingProofReferencesUseLatestSnapshots", report["failedRequiredChecks"])

    def test_screenshot_plan_must_use_ios265_only(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/SCREENSHOT_PLAN.md",
                valid_screenshot_plan()
                .replace("-sdk iphonesimulator26.5", "")
                .replace("OS=26.5", "OS=18.5")
                .replace("XiaoNaiPing-DebugScreenshots-26_5", "XiaoNaiPing-DebugScreenshots"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("screenshotPlanUsesIOS265Only", report["failedRequiredChecks"])
            self.assertIn("OS=18.5", report["checks"]["screenshotPlanUsesIOS265Only"]["evidence"])

    def test_screenshot_upload_matrix_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            def remove_matrix_markers(text: str) -> str:
                return (
                    text.replace("## App Store Connect 截图上传矩阵", "## 截图上传")
                    .replace("iPhone 6.9\" display", "iPhone display")
                    .replace("1260 x 2736", "")
                    .replace("1290 x 2796", "")
                    .replace("1320 x 2868", "")
                    .replace("当前候选为 iPhone 17 Pro Max / iPhone 6.9\" display / 1320 x 2868", "")
                    .replace("不能把 Debug simulator 候选图声称为 TestFlight、签名真机或 App Store Connect 上传最终证据", "")
                    .replace("TARGETED_DEVICE_FAMILY=1", "TARGETED_DEVICE_FAMILY")
                    .replace("如果 App Store Connect 要求 iPad 截图，先复核工程 target family", "如果需要 iPad 截图")
                )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                remove_matrix_markers(valid_fill_sheet()),
            )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FINAL_ENTRY_AUDIT_20260627.md",
                remove_matrix_markers(valid_final_entry_audit()),
            )
            write(
                root / "Docs/08_Release/SCREENSHOT_PLAN.md",
                remove_matrix_markers(valid_screenshot_plan()).replace("`.jpeg`、`.jpg`、`.png`", "png"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreScreenshotUploadMatrixPresent", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreScreenshotUploadMatrixPresent"]["evidence"]
            self.assertIn("## App Store Connect 截图上传矩阵", evidence)
            self.assertIn("iPhone 6.9\" display", evidence)
            self.assertIn("不能把 Debug simulator 候选图声称为 TestFlight、签名真机或 App Store Connect 上传最终证据", evidence)
            self.assertIn("TARGETED_DEVICE_FAMILY=1", evidence)

    def test_in_app_companion_copy_rejects_unbounded_watch_app_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "App/iOS/XiaoNaiPing/Views/FeedingRecordView.swift",
                'Text("支持 Apple Watch App 和 watchOS 手表体验。")\n',
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("inAppCompanionCopyBounded", report["failedRequiredChecks"])
            evidence = report["checks"]["inAppCompanionCopyBounded"]["evidence"]
            self.assertIn("Watch App", evidence)
            self.assertIn("watchOS", evidence)

    def test_external_auth_submission_boundaries_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet()
                .replace("，微信 provider 未配置；手机号和微信测试号会在真实短信服务与微信开放平台配置完成后补充", "")
                .replace("，缺真实微信 Release build setting", "")
                .replace("，缺真实 `wx...` URL Scheme", "")
                .replace("，缺人工证据和 iOS 26.5 真机回归记录", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("externalAuthSubmissionBoundaryPresent", report["failedRequiredChecks"])

    def test_public_copy_defers_sms_wechat_until_provider_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet()
                .replace(
                    "小奶瓶是一款宝宝成长记录 App。数据默认本地优先保存，可使用恢复密钥登录账号，并同步用户主动加入 App 的照片原图。",
                    "小奶瓶是一款宝宝成长记录 App。数据默认本地优先保存，可通过恢复密钥、手机号或微信登录账号，并同步用户主动加入 App 的照片原图。",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("deferredSmsWechatPublicCopyBounded", report["failedRequiredChecks"])
            evidence = report["checks"]["deferredSmsWechatPublicCopyBounded"]["evidence"]
            self.assertIn("prematureClaims", evidence)
            self.assertIn("可通过恢复密钥、手机号或微信登录", evidence)

    def test_traditional_public_copy_defers_sms_wechat_until_provider_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_METADATA.md",
                valid_metadata()
                + "\n可透過恢復密鑰、手機號碼或微信登入私有帳號。\n"
                + "第一版：手機號碼/微信/恢復密鑰帳號同步恢復。\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("deferredSmsWechatPublicCopyBounded", report["failedRequiredChecks"])
            evidence = report["checks"]["deferredSmsWechatPublicCopyBounded"]["evidence"]
            self.assertIn("可透過恢復密鑰、手機號碼或微信登入", evidence)
            self.assertIn("手機號碼/微信/恢復密鑰帳號同步恢復", evidence)

    def test_review_paste_text_requires_status_and_advice_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet().replace(
                    "这些状态展示只反映用户主动记录的数据，不生成健康建议、压力提醒、喂养建议或医疗判断。",
                    "",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("reviewNotesPasteTextHasBoundary", report["failedRequiredChecks"])

    def test_manual_feeding_reminder_deferral_boundary_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet().replace(
                    "用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。",
                    "",
                ),
            )
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_COPY_PASTE_20260627.md",
                valid_copy_paste_packet().replace(
                    "用户可以手动顺延下一次提醒：保存新喂养时，如果已设置固定喝奶间隔，可以用 5 分钟一档的滚轮选择不顺延或顺延 +5、+10、+15、+20、+25、+30 分钟。保存后，下一次提醒按本顿结束时间 + 固定间隔 + 顺延分钟重排；本顿无喂养时长时按本顿发生时间计算。顺延只改变下一次提醒时间，不新增持久化字段；App 不根据奶量、月龄、传感器或健康数据自动推算喂养时间，也不构成喂养建议。",
                    "",
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("feedingReminderDeferralBoundarySpecific", report["failedRequiredChecks"])
            self.assertIn("reviewNotesPasteTextHasBoundary", report["failedRequiredChecks"])

    def test_review_account_instructions_must_be_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet()
                .replace(
                    "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
                    "Docs/08_Release/AppStoreEvidence/missing.json",
                )
                + "\nXNP_REVIEW_RECOVERY_KEY=secret\nBearer abc.def_123\n13800138000\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("reviewAccountInstructionsRedacted", report["failedRequiredChecks"])
            evidence = report["checks"]["reviewAccountInstructionsRedacted"]["evidence"]
            self.assertIn("Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json", evidence)
            self.assertIn("recoveryKeyAssignment", evidence)
            self.assertIn("bearerToken", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)

    def test_review_account_redacted_evidence_must_match_review_info(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
                valid_review_information_packet()
                .replace("## 审核测试账号脱敏证据一致性锁", "## 测试账号证据")
                .replace("只保存可审核的脱敏状态，不保存恢复密钥本身", "")
                .replace("Password 只从 `.env.xnp-review-account` 的 `XNP_REVIEW_RECOVERY_KEY` 复制到 App Store Connect 私密字段", "")
                .replace("JSON 不得新增 `secret`、`token`、`password`、`code` 字段", ""),
            )
            write(
                root / "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
                json.dumps(
                    {
                        "baseUrl": "https://example.com/xiaonaiping",
                        "accountId": "",
                        "recoveryKeyStored": "Docs/recovery-key.txt",
                        "recoveryVerified": False,
                        "syncSeeded": False,
                        "containsSecret": True,
                        "sessionToken": "Bearer abc.def_123",
                        "phone": "13800138000",
                    },
                    ensure_ascii=False,
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("reviewAccountRedactedEvidenceMatchesReviewInfo", report["failedRequiredChecks"])
            evidence = report["checks"]["reviewAccountRedactedEvidenceMatchesReviewInfo"]["evidence"]
            self.assertIn("## 审核测试账号脱敏证据一致性锁", evidence)
            self.assertIn("只保存可审核的脱敏状态", evidence)
            self.assertIn("accountId missing", evidence)
            self.assertIn("baseUrl mismatch", evidence)
            self.assertIn("recoveryVerified must be true", evidence)
            self.assertIn("forbidden fields: sessionToken", evidence)
            self.assertIn("bearerToken", evidence)
            self.assertIn("mainlandPhoneNumber", evidence)

    def test_app_review_test_account_packet_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            packet = json.loads(valid_app_review_test_account_packet())
            packet.pop("evidenceRoot", None)
            packet["canSubmitFromThisPacket"] = True
            packet["appReviewSignInFields"]["debugCodeAllowed"] = True
            packet["redactedEvidenceRequired"]["baseUrl"] = "https://example.com/xiaonaiping"
            packet["evidenceFileChecks"] = [
                item
                for item in packet["evidenceFileChecks"]
                if item["artifactId"] != "RD-15"
            ]
            packet["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/11-test-account.json"
            packet["evidenceFileChecks"][0]["sha256"] = "already-filled"
            packet["evidenceFileChecks"][0]["sameRoundAsAppReviewFill"] = True
            packet["evidenceFileChecks"][0]["sameBuildAsReviewBuild"] = True
            packet["evidenceFileChecks"][0]["runtimeIsIos265"] = True
            packet["evidenceFileChecks"][0]["realEvidenceNotTemplate"] = True
            packet["evidenceDependencyMatrix"] = [
                item
                for item in packet["evidenceDependencyMatrix"]
                if item["artifactId"] != "RD-10"
            ]
            packet["evidenceDependencyMatrix"][0]["target"] = "Docs/08_Release/AppStoreEvidence/11-test-account-copy.json"
            packet["evidenceDependencyMatrix"][0]["proves"] = ["review account exists"]
            packet["evidenceDependencyMatrix"][0]["requiredBeforeSubmit"] = False
            packet["evidenceDependencyMatrix"][0]["initialStatus"] = "captured"
            packet["evidenceDependencyMatrix"][0]["extra"] = "unexpected"
            packet["realDeviceEvidenceTargets"] = [
                target for target in packet["realDeviceEvidenceTargets"] if target["id"] != "RD-15"
            ]
            packet["stopConditions"] = [
                condition
                for condition in packet["stopConditions"]
                if condition["id"] != "ios265RealDeviceEvidenceMissing"
            ]
            packet["redactionChecklist"] = ["token"]
            packet["postFillGates"] = [
                "python3 Backend/scripts/check_app_store_connect_materials.py --output Backend/proof/app-store-connect-materials.json"
            ]
            packet["completionRule"] = "done"
            write(
                root / "Docs/08_Release/APP_REVIEW_TEST_ACCOUNT_PACKET_20260627.json",
                json.dumps(packet, ensure_ascii=False),
            )
            write(
                root / "Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260627.md",
                valid_review_information_packet().replace("APP_REVIEW_TEST_ACCOUNT_PACKET_20260627.json", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appReviewTestAccountPacketReferenced", report["failedRequiredChecks"])
            self.assertIn("appReviewTestAccountPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["appReviewTestAccountPacketValid"]["evidence"]
            self.assertIn("canSubmitFromThisPacket must be false", evidence)
            self.assertIn("appReviewSignInFields.debugCodeAllowed must be false", evidence)
            self.assertIn("redactedEvidenceRequired.baseUrl must be https://api.mewpow.com/xiaonaiping", evidence)
            self.assertIn("redactedEvidenceRequired.baseUrl must match review account evidence", evidence)
            self.assertIn("evidenceFileChecks order must match App Review test-account evidence workflow", evidence)
            self.assertIn("evidenceFileChecks.RD-15 missing object", evidence)
            self.assertIn(
                "evidenceFileChecks.reviewAccountRedacted.target must be Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
                evidence,
            )
            self.assertIn("evidenceFileChecks.reviewAccountRedacted.sha256 must be 'FILL_AFTER_CAPTURE'", evidence)
            self.assertIn("evidenceFileChecks.reviewAccountRedacted.sameRoundAsAppReviewFill must be False", evidence)
            self.assertIn("evidenceFileChecks.reviewAccountRedacted.sameBuildAsReviewBuild must be False", evidence)
            self.assertIn("evidenceFileChecks.reviewAccountRedacted.runtimeIsIos265 must be False", evidence)
            self.assertIn("evidenceFileChecks.reviewAccountRedacted.realEvidenceNotTemplate must be False", evidence)
            self.assertIn("evidenceDependencyMatrix order must match App Review test-account evidence workflow", evidence)
            self.assertIn("evidenceDependencyMatrix.RD-10 missing object", evidence)
            self.assertIn(
                "evidenceDependencyMatrix.reviewAccountRedacted.fields must be "
                "artifactId -> target -> proves -> doesNotProve -> requiredBeforeSubmit -> initialStatus",
                evidence,
            )
            self.assertIn(
                "evidenceDependencyMatrix.reviewAccountRedacted.target must be "
                "Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json",
                evidence,
            )
            self.assertIn(
                "evidenceDependencyMatrix.reviewAccountRedacted.proves must be "
                "['redacted App Review recovery-key account evidence exists without storing the recovery key', "
                "'recovery-key login account is prepared, verified, sync-seeded, and tied to the production base URL']",
                evidence,
            )
            self.assertIn("evidenceDependencyMatrix.reviewAccountRedacted.requiredBeforeSubmit must be True", evidence)
            self.assertIn("evidenceDependencyMatrix.reviewAccountRedacted.initialStatus must be pending", evidence)
            self.assertIn("realDeviceEvidenceTargets missing RD-15", evidence)
            self.assertIn("stopConditions missing ios265RealDeviceEvidenceMissing", evidence)
            self.assertIn("redactionChecklist missing recovery key", evidence)
            self.assertIn(
                "postFillGates missing check_app_store_evidence.py --allow-incomplete --date 2026-06-27 --output Backend/proof/app-store-evidence-20260627T-current.json",
                evidence,
            )
            self.assertIn("completionRule missing review-test-account-packet-not-evidence", evidence)

    def test_release_notes_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            write(
                root / "Docs/08_Release/APP_STORE_CONNECT_FILL_SHEET_20260627.md",
                valid_fill_sheet().replace("、照片时间线、恢复密钥账号同步恢复和云端账号删除", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("releaseNotesCompleteAndWithinLimit", report["failedRequiredChecks"])

    def test_privacy_label_app_flags_and_usage_boundaries_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            privacy_label = valid_privacy_label()
            privacy_label["app"]["containsThirdPartyAnalytics"] = True
            privacy_label["dataCategories"][5]["linkedToUser"] = False
            privacy_label["dataCategories"][5]["notes"] = "First-party product interaction only."
            privacy_label["dataCategories"].append(
                {
                    "category": "Location",
                    "collected": True,
                    "linkedToUser": True,
                    "usedForTracking": False,
                    "purposes": ["Analytics"],
                }
            )
            write(
                root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
                json.dumps(privacy_label, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyLabelMatchesAppStoreDraft", report["failedRequiredChecks"])
            evidence = report["checks"]["privacyLabelMatchesAppStoreDraft"]["evidence"]
            self.assertIn("app.containsThirdPartyAnalytics must be false", evidence)
            self.assertIn("unexpected collected categories: Location", evidence)
            self.assertIn("Usage Data.linkedToUser must be true", evidence)
            self.assertIn("Usage Data boundary missing", evidence)

    def test_privacy_label_health_boundaries_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_materials(root)
            privacy_label = valid_privacy_label()
            privacy_label["dataCategories"][4]["notes"] = "The app is not a medical device."
            write(
                root / "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
                json.dumps(privacy_label, ensure_ascii=False),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("privacyLabelMatchesAppStoreDraft", report["failedRequiredChecks"])
            evidence = report["checks"]["privacyLabelMatchesAppStoreDraft"]["evidence"]
            self.assertIn("Health and Fitness boundary missing", evidence)


if __name__ == "__main__":
    unittest.main()
