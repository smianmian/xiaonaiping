from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_mainland_filing_materials.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_materials() -> str:
    return """
# MAINLAND_FILING_MATERIALS.md

## 当前判断

1. 小奶瓶计划在中国大陆 App Store 首发，并通过中国大陆云资源提供联网服务，应按 App 备案路径准备材料。
2. 当前公网过渡路径为 `https://api.mewpow.com/xiaonaiping`，正式提交前建议改为小奶瓶专属子域名。
3. App Store Connect 公司主体证据依赖 D-U-N-S 后继续完成 Apple Developer Organization enrollment，并确认 Team ID；见 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md`。
4. 微信开放平台、短信服务商、OBS 策略、生产 proof 和 iOS 26.5 真机/TestFlight 证据按 `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md` 归档。
5. App 备案完成后，需要在 App 显著位置展示备案编号并链接工信部备案系统；拿到备案号后再实现 UI / 静态页展示。
6. 公安联网备案通常在 ICP / App 备案完成并开通服务后继续办理，证据也要归档。

## 拟填信息

| 项目 | 当前填写稿 | 状态 |
|---|---|---|
| 主办单位 | 深圳市闪现生活科技有限公司 | 待营业执照和备案主体确认 |
| App 名称 | 小奶瓶 | 待 App Store Connect 最终名称确认 |
| App 类型 | iOS 原生 App | 已确认 |
| Bundle ID | `com.mewpow.xiaonaiping` | 已在 iOS release gate 通过 |
| SKU | `xiaonaiping-ios-1` | 可用于 App Store Connect |
| 服务内容 | 父母/照护者记录宝宝喂养、睡眠、排便、成长、疫苗提醒和照片时间线 | 待按备案系统选项映射 |
| 是否面向儿童直接使用 | 否，面向父母和照护者 | 已确认 |
| 是否医疗服务 | 否，不提供诊断、治疗、处方或专业疫苗建议 | 待法务复核 |
| 首发地区 | 中国大陆 App Store | 已确认 |
| 第二批地区 | 香港 App Store | 已确认 |
| 隐私政策 URL | `https://api.mewpow.com/xiaonaiping/privacy` | 当前过渡 URL |
| 用户协议 URL | `https://api.mewpow.com/xiaonaiping/terms` | 当前过渡 URL |
| 支持 URL | `https://api.mewpow.com/xiaonaiping/support` | 当前过渡 URL |
| API URL | `https://api.mewpow.com/xiaonaiping` | 当前过渡 URL，建议换专属子域名 |
| 云服务 | 华为云中国大陆 ECS、宝塔 MySQL、华为云 OBS | 待控制台证据 |
| 生产数据库 | `xiaonaiping_prod` | 已有部署 proof，仍需同步/恢复演练 |
| 账号方式 | 恢复密钥、手机号验证码、微信授权 | 手机短信和微信开放平台仍待最终配置 |

## 需要向公司/后台拿到的材料

1. 营业执照电子版。
2. 法定代表人、App 负责人、网站/网络安全负责人证件材料。
3. 域名证书、域名实名认证信息、DNS 解析截图。
4. 云服务器公网 IP、地域、接入商、实例/备案服务号等信息。
5. App 图标、Bundle ID、版本号、应用简介、应用截图。
6. 隐私政策 URL、用户协议 URL、支持 URL 可访问证明。
7. App Store Connect 公司主体截图。
8. D-U-N-S 后继续完成 Apple Developer Organization enrollment、Team ID、App Store Connect 公司主体绑定证明。
9. 中国大陆只选择可售地区截图。
10. 短信服务商签名、模板、发送成功证明。
11. 微信开放平台移动应用、Bundle ID、URL Scheme、Universal Link 绑定证明。
12. OBS bucket、私有访问、服务端访问、加密、生命周期、删除验证证明。
13. `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md` 中列出的微信、短信、OBS、生产 proof、iOS 26.5 真机/TestFlight 证据。
14. 拿到备案号后的备案编号、备案查询页截图和 App 内展示位置截图。
15. 公安联网备案提交/通过证明。

## 证据归档文件名

| 证据 | 文件名 |
|---|---|
| 公司主体 | `Docs/08_Release/AppStoreEvidence/01-company-account.png` |
| 中国大陆可售地区 | `Docs/08_Release/AppStoreEvidence/02-mainland-availability.png` |
| App 备案 / ICP 备案 | `Docs/08_Release/AppStoreEvidence/03-app-filing.pdf` 或 `.png` |
| 隐私标签 | `Docs/08_Release/AppStoreEvidence/04-privacy-label.png` |
| 签名归档 | `Docs/08_Release/AppStoreEvidence/05-signed-archive.png` |
| TestFlight | `Docs/08_Release/AppStoreEvidence/06-testflight.png` |
| 短信服务商 | `Docs/08_Release/AppStoreEvidence/07-sms-provider.png` |
| 微信开放平台 | `Docs/08_Release/AppStoreEvidence/08-wechat-open-platform.png` |
| OBS 策略 | `Docs/08_Release/AppStoreEvidence/09-obs-policy.png` |
| 最终截图 | `Docs/08_Release/AppStoreEvidence/10-final-screenshots/` |
| 测试账号 redacted 证据 | `Docs/08_Release/AppStoreEvidence/11-test-account-redacted.json` |

## 上线前需要改代码的备案项

拿到备案编号后再做，不提前写占位号：

1. 隐私政策、用户协议、支持页底部展示备案编号。
2. App 内“数据与隐私”或“关于小奶瓶”展示备案编号和备案系统链接。
3. App Store Review Notes 补充备案编号。
4. 重新跑 `Backend/scripts/check_public_pages.py`、`Backend/scripts/check_review_notes.py` 和 `Backend/scripts/check_production_readiness.py`。

## 提交顺序

1. 确认专属域名或决定继续使用过渡路径。
2. 按 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md` 完成 D-U-N-S 后的 Apple Developer 公司主体、Team ID、签名归档前置确认。
3. 按 `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md` 补齐微信、短信、OBS、生产 proof 和 iOS 26.5 真机/TestFlight 证据。
4. 在华为云/接入商备案系统提交 App 备案和适用 ICP 信息。
5. 备案通过后补 App 内/网页备案编号展示。
6. 完成公安联网备案并归档证明。
7. 再提交 App Store Connect 中国大陆审核。

## 备案 / ICP / 公安联网备案当天执行记录模板

复制下面清单到当天的私有执行记录或工单中填写；所有项必须来自同一天同一轮操作。
结构化执行包见 `Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260630.json`；它不是备案证据，不能作为提交许可，只用于锁定源文件、证据文件名、停止条件、脱敏清单和复跑 gate。

- [ ] 营业执照电子版、法定代表人、App 负责人、网络安全负责人材料已确认。
- [ ] 域名证书、域名实名认证、DNS 解析、云服务器公网 IP、接入商信息已确认。
- [ ] Apple Developer Organization enrollment / Team ID 和 App Store Connect 公司主体截图已归档。
- [ ] 03-app-filing.pdf 或 03-app-filing.png 已归档。
- [ ] 备案系统提交状态、备案号或适用判断结果可见。
- [ ] 备案通过前不在公开页、App 内或 Review Notes 写占位备案号。
- [ ] 备案通过后再更新 Backend/static/privacy.html、terms.html、support.html。
- [ ] App 内“数据与隐私”或“关于小奶瓶”展示备案编号和工信部备案系统链接。
- [ ] 公安联网备案提交/通过证明已归档。
- [ ] check_public_pages.py、check_review_notes.py、check_mainland_filing_materials.py、check_production_readiness.py 已复跑。
- [ ] 不记录完整证件号、联系人完整电话、验证码、AK/SK、AppSecret、恢复密钥或 token。
- [ ] 如果任一项未通过，不提交中国大陆 App Store 审核。
""".lstrip()


def valid_capture_guide() -> str:
    return """
| 文件名 | 说明 | 必须包含 | 不得包含 |
|---|---|---|---|
| `03-app-filing.pdf` 或 `.png` | App 备案/ICP/适用判断进度或结果 | App 名称、主体、备案号或提交状态 | 遮个人证件细节 |
""".lstrip()


def valid_gap_assessment() -> str:
    return """
# CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md

- 日期：2026-06-30

当前以 `Backend/proof/production-readiness.json` 和 `Backend/proof/launch-objective-audit.json` 为准，仍不得提交中国大陆 App Store。
已有 `Backend/proof/remote-api.json`、`Backend/proof/provider-evidence-materials.json` 和 `Backend/proof/mainland-filing-materials.json`，但提交前仍必须按 `XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md` 刷新 `20260630T-current` proof。

当前红项包括 `deploymentProofCurrent`、`storageBackendProofCurrent`、`wechatLoginProviderConfigured`、`ios265PhysicalDeviceAvailabilityReady` 和 `appStoreManualEvidenceReady`。
不能用旧 proof、模拟器或模板文档替代。
""".lstrip()


def valid_compliance() -> str:
    return """
# CHINA_MAINLAND_COMPLIANCE.md

## 文档状态

- 日期：2026-06-30

## 当前证据口径

1. 中国大陆提交判断以 `Backend/proof/production-readiness.json` 和 `Backend/proof/launch-objective-audit.json` 为准；任一不是 ready 都不得直接提交。
2. 备案材料按 `Docs/08_Release/MAINLAND_FILING_MATERIALS.md` 执行，外部平台和生产证据按 `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md` 执行。
3. D-U-N-S 交付后的 Apple Developer Organization enrollment、Team ID、证书、Archive 和 TestFlight 动作按 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md` 执行。
4. 当前仍缺 APP 备案 / ICP / 公安联网备案证据、微信开放平台、短信服务商、OBS、App Store Connect 人工证据、iOS 26.5 TestFlight 或签名真机回归证据。
5. `Docs/08_Release/CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md` 是当前差距总览。
""".lstrip()


def valid_regional_strategy() -> str:
    return """
# REGIONAL_LAUNCH_STRATEGY.md

## 文档状态

- 日期：2026-06-30
- 当前结论：中国大陆 App Store 为第一批，香港 App Store 为第二批；完成当天生产 proof、备案、App Store 人工证据、微信/短信/OBS 和 iOS 26.5 真机/TestFlight 证据前不得提交

## 当前证据口径

1. 中国大陆首发判断以 `Backend/proof/production-readiness.json` 和 `Backend/proof/launch-objective-audit.json` 为准；任一不是 ready 都不得提交。
2. 2026-06-30 当天生产 proof、外部平台证据和稳定 alias 同步按 `Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md` 执行。
3. 当前仍缺 APP 备案、微信/短信/OBS 真实证据和 iOS 26.5 真机/TestFlight 回归。

## 发布要求

按 `CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md` 和 `XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md` 完成 APP 备案、正式域名、当天 `20260630T-current` 生产 proof、微信/短信/OBS、App Store 人工证据和 iOS 26.5 真机/TestFlight 验证。
""".lstrip()


def valid_app_store_compliance_timeline() -> str:
    return """
# APP_STORE_COMPLIANCE_TIMELINE.md

## 文档状态

- 项目：小奶瓶 / 宝宝成长记录
- 阶段：App Store 合规时间线当前版
- 日期：2026-06-30
- 公司主体：深圳市闪现生活科技有限公司
- 当前总闸门：`Backend/proof/production-readiness.json` 和 `Backend/proof/launch-objective-audit.json` 任一不是 ready=true 时，不得提交 App Store Connect 审核。

## 当前材料状态

1. App Store Connect 草稿字段已经整理到 `Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260630.json`。
2. 字段冻结和现场粘贴顺序由 `Docs/08_Release/APP_STORE_CONNECT_FIELD_FREEZE_PACKET_20260630.json` 约束。
3. Submit for Review 前置检查由 `Docs/08_Release/APP_STORE_CONNECT_SUBMIT_REVIEW_PREFLIGHT_20260630.json` 约束。
4. App Store submission packet 由 `Backend/proof/app-store-submission-packet.json` 证明当前材料包可机检，但不是提交许可。

## D-U-N-S 到 TestFlight 时间线

1. D-U-N-S 交付后按 `Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md` 继续 Apple Developer Organization enrollment。
2. 结构化动作包为 `Docs/08_Release/APPLE_DEVELOPER_DUNS_POST_DELIVERY_ACTIONS.json`。
3. 完成后确认 Team ID、App Store Distribution Archive 和 TestFlight。

## 隐私、年龄分级和审核信息

1. 隐私标签答案表：`Docs/08_Release/APP_STORE_PRIVACY_ANSWERS_20260630.md`。
2. 年龄分级答案表：`Docs/08_Release/APP_STORE_AGE_RATING_ANSWERS_20260630.md`。
3. 审核信息：`Docs/08_Release/APP_STORE_REVIEW_INFORMATION_20260630.md`。

## 生产、备案和外部平台

1. 生产/隐私证据入库工作台：`Docs/08_Release/XNP_PRODUCTION_PRIVACY_EVIDENCE_WORKBENCH_20260630.md`。
2. APP/ICP/公安联网备案执行包：`Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260630.json`。
3. 微信 Release 配置：`Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json`。
4. 短信实发：`Docs/08_Release/SMS_PROVIDER_LIVE_SEND_PACKET_20260630.json`。
5. OBS proof：`Docs/08_Release/OBS_STORAGE_PROOF_PACKET_20260630.json`。
6. 当前生产 proof refresh status 仍为 `stableAliasSyncAllowed=false`。

## 真机/TestFlight

1. 只接受 iOS 26.5。
2. 真机采集预检：`Docs/08_Release/AppStoreEvidence/RealDevice/REAL_DEVICE_CAPTURE_PREFLIGHT_20260630.json`。
3. 重点采集包：`Docs/08_Release/AppStoreEvidence/RealDevice/FOCUSED_CAPTURE_PACKET_20260630.json`。

## 当前提交结论

当前不得提交 App Store Connect 审核。必须先补齐 D-U-N-S 后 Apple Developer Organization enrollment、Team ID、Archive、TestFlight、微信/短信/OBS、备案、App Store 人工证据、最终截图上传 provenance、iOS 26.5 真机回归，并让 production readiness 和 launch objective audit 都变绿。
""".lstrip()


def valid_filing_execution_packet() -> str:
    return (SCRIPT.parents[2] / "Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260630.json").read_text(
        encoding="utf-8",
    )


def valid_mainland_filing_privacy_template() -> str:
    return (
        SCRIPT.parents[2]
        / "Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json"
    ).read_text(encoding="utf-8")


def write_valid_context(
    root: Path,
    *,
    materials: str | None = None,
    capture_guide: str | None = None,
    gap_assessment: str | None = None,
    compliance: str | None = None,
    regional_strategy: str | None = None,
    app_store_compliance_timeline: str | None = None,
    filing_execution_packet: str | None = None,
) -> None:
    write(root / "Docs/08_Release/MAINLAND_FILING_MATERIALS.md", materials or valid_materials())
    write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", capture_guide or valid_capture_guide())
    write(root / "Docs/08_Release/CHINA_MAINLAND_LAUNCH_GAP_ASSESSMENT.md", gap_assessment or valid_gap_assessment())
    write(root / "Docs/07_PrivacySecurity/CHINA_MAINLAND_COMPLIANCE.md", compliance or valid_compliance())
    write(root / "Docs/08_Release/REGIONAL_LAUNCH_STRATEGY.md", regional_strategy or valid_regional_strategy())
    write(
        root / "Docs/08_Release/APP_STORE_COMPLIANCE_TIMELINE.md",
        app_store_compliance_timeline or valid_app_store_compliance_timeline(),
    )
    write(
        root / "Docs/08_Release/MAINLAND_FILING_EXECUTION_PACKET_20260630.json",
        filing_execution_packet or valid_filing_execution_packet(),
    )
    write(
        root / "Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json",
        valid_mainland_filing_privacy_template(),
    )


class MainlandFilingMaterialsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/mainland-filing-materials.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(root),
                "--output",
                str(output),
                "--allow-incomplete",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("mainland filing materials", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_materials_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_archive_names_and_redaction_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(
                root,
                materials=valid_materials()
                .replace("03-app-filing.pdf", "03-filing-proof.pdf")
                .replace("拿到备案编号后再做，不提前写占位号", ""),
                capture_guide="| bad | bad |\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("evidenceArchiveFilenamesMatchGate", report["failedRequiredChecks"])
            self.assertIn("postFilingCodeChangesDeferredUntilRealNumber", report["failedRequiredChecks"])
            self.assertIn("captureGuideCoversFilingEvidenceRedaction", report["failedRequiredChecks"])

    def test_missing_developer_and_external_handoffs_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            outdated = valid_materials()
            for marker in (
                "D-U-N-S",
                "Apple Developer Organization enrollment",
                "Team ID",
                "Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md",
                "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md",
                "生产 proof",
                "iOS 26.5 真机/TestFlight",
            ):
                outdated = outdated.replace(marker, "")
            write_valid_context(root, materials=outdated)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("dunsAppleDeveloperDependencyDocumented", report["failedRequiredChecks"])
            self.assertIn("externalPlatformEvidenceHandoffDocumented", report["failedRequiredChecks"])
            self.assertIn("currentJudgmentCoversLaunchAndFilingPath", report["failedRequiredChecks"])
            self.assertIn("externalMaterialCollectionListComplete", report["failedRequiredChecks"])
            self.assertIn("submissionSequenceKeepsFilingBeforeChinaReview", report["failedRequiredChecks"])

    def test_completion_claim_without_archived_filing_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root, materials=valid_materials() + "\n备案已完成。APP备案号：待填\n")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("doesNotPretendFilingCompleteBeforeEvidence", report["failedRequiredChecks"])
            evidence = report["checks"]["doesNotPretendFilingCompleteBeforeEvidence"]["evidence"]
            self.assertIn("备案已完成", evidence)
            self.assertIn("placeholderAppFilingNumber", evidence)

    def test_stale_gap_assessment_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(
                root,
                gap_assessment=valid_gap_assessment()
                .replace("日期：2026-06-30", "日期：2026-06-18")
                .replace("Backend/proof/launch-objective-audit.json", "")
                .replace("deploymentProofCurrent", "")
                .replace("不得提交中国大陆 App Store", ""),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("chinaMainlandGapAssessmentCurrent", report["failedRequiredChecks"])
            evidence = report["checks"]["chinaMainlandGapAssessmentCurrent"]["evidence"]
            self.assertIn("日期：2026-06-30", evidence)
            self.assertIn("Backend/proof/launch-objective-audit.json", evidence)
            self.assertIn("deploymentProofCurrent", evidence)

    def test_old_external_handoff_and_current_proofs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(
                root,
                materials=valid_materials()
                + "\n历史误填：Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260628.md\n",
                gap_assessment=valid_gap_assessment() + "\n历史误填：20260628T-current，日期：2026-06-28\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("mainlandMaterialsUseCurrentDayHandoff", report["failedRequiredChecks"])
            evidence = report["checks"]["mainlandMaterialsUseCurrentDayHandoff"]["evidence"]
            self.assertIn("XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260628.md", evidence)
            self.assertIn("20260628T-current", evidence)
            self.assertIn("日期：2026-06-28", evidence)

    def test_filing_same_day_execution_template_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            broken = valid_materials()
            broken = broken.replace("## 备案 / ICP / 公安联网备案当天执行记录模板", "## 备案当天记录")
            broken = broken.replace("03-app-filing.pdf 或 03-app-filing.png 已归档。", "")
            broken = broken.replace("备案通过前不在公开页、App 内或 Review Notes 写占位备案号。", "")
            broken = broken.replace("如果任一项未通过，不提交中国大陆 App Store 审核。", "")
            write_valid_context(root, materials=broken)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("filingSameDayExecutionTemplatePresent", report["failedRequiredChecks"])
            evidence = report["checks"]["filingSameDayExecutionTemplatePresent"]["evidence"]
            self.assertIn("## 备案 / ICP / 公安联网备案当天执行记录模板", evidence)
            self.assertIn("03-app-filing.pdf 或 03-app-filing.png 已归档", evidence)
            self.assertIn("备案通过前不在公开页、App 内或 Review Notes 写占位备案号", evidence)
            self.assertIn("如果任一项未通过，不提交中国大陆 App Store 审核", evidence)

    def test_filing_execution_packet_is_required_and_structured(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            broken_packet = json.loads(valid_filing_execution_packet())
            broken_packet.pop("canSubmitFromThisPacket")
            broken_packet["targetEvidenceFiles"].pop("appFilingPdf")
            broken_packet["stopConditions"] = [
                item
                for item in broken_packet["stopConditions"]
                if item["id"] != "noRealFilingNumber"
            ]
            broken_packet["postExecutionGates"] = [
                gate
                for gate in broken_packet["postExecutionGates"]
                if "check_public_pages.py" not in gate
            ]
            broken_packet["completionRule"] = broken_packet["completionRule"].replace("not submission permission", "")
            write_valid_context(
                root,
                filing_execution_packet=json.dumps(broken_packet, ensure_ascii=False, indent=2),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("filingExecutionPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["filingExecutionPacketValid"]["evidence"]
            self.assertIn("canSubmitFromThisPacket must be false", evidence)
            self.assertIn("targetEvidenceFiles.appFilingPdf", evidence)
            self.assertIn("stopConditions missing noRealFilingNumber", evidence)
            self.assertIn("postExecutionGates missing check_public_pages.py", evidence)
            self.assertIn("completionRule missing not submission permission", evidence)

    def test_filing_execution_packet_rejects_reordered_or_extra_items(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            broken_packet = json.loads(valid_filing_execution_packet())
            source_files = broken_packet["sourceFiles"]
            source_files["extraTemplate"] = "Docs/08_Release/template-only.md"
            target_files = broken_packet["targetEvidenceFiles"]
            first_target = next(iter(target_files))
            target_files[first_target] = target_files.pop(first_target)
            stop_conditions = broken_packet["stopConditions"]
            stop_conditions.append(stop_conditions.pop(0))
            write_valid_context(
                root,
                filing_execution_packet=json.dumps(broken_packet, ensure_ascii=False, indent=2),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("filingExecutionPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["filingExecutionPacketValid"]["evidence"]
            self.assertIn("sourceFiles order must be", evidence)
            self.assertIn("targetEvidenceFiles order must be", evidence)
            self.assertIn("stopConditions order must be", evidence)

    def test_filing_execution_packet_requires_evidence_file_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            broken_packet = json.loads(valid_filing_execution_packet())
            broken_packet["evidenceFileChecks"] = [
                item for item in broken_packet["evidenceFileChecks"] if item["artifactId"] != "companyAccount"
            ]
            broken_packet["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/02-wrong.png"
            broken_packet["evidenceFileChecks"][0]["sha256"] = "already-filled"
            broken_packet["evidenceFileChecks"][0]["sameRoundAsFilingExecution"] = True
            broken_packet["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            write_valid_context(
                root,
                filing_execution_packet=json.dumps(broken_packet, ensure_ascii=False, indent=2),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("filingExecutionPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["filingExecutionPacketValid"]["evidence"]
            self.assertIn("evidenceFileChecks.companyAccount missing object", evidence)
            self.assertIn(
                "evidenceFileChecks.mainlandAvailability.target must be "
                "Docs/08_Release/AppStoreEvidence/02-mainland-availability.png",
                evidence,
            )
            self.assertIn(
                "evidenceFileChecks.mainlandAvailability.sha256 must be 'FILL_AFTER_CAPTURE'",
                evidence,
            )
            self.assertIn(
                "evidenceFileChecks.mainlandAvailability.sameRoundAsFilingExecution must be False",
                evidence,
            )
            self.assertIn(
                "evidenceFileChecks.mainlandAvailability.secretValuesNotRecorded must be False",
                evidence,
            )

    def test_filing_execution_packet_requires_dependency_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            broken_packet = json.loads(valid_filing_execution_packet())
            broken_packet["evidenceDependencyMatrix"] = [
                item
                for item in broken_packet["evidenceDependencyMatrix"]
                if item["artifactId"] != "appFilingPdf"
            ]
            broken_packet["evidenceDependencyMatrix"][0]["target"] = (
                "Docs/08_Release/AppStoreEvidence/01-company-copy.png"
            )
            broken_packet["evidenceDependencyMatrix"][4]["proves"] = ["privacy visible"]
            broken_packet["evidenceDependencyMatrix"][9]["requiredBeforeMainlandSubmit"] = False
            broken_packet["evidenceDependencyMatrix"][9]["initialStatus"] = "captured"
            write_valid_context(
                root,
                filing_execution_packet=json.dumps(broken_packet, ensure_ascii=False, indent=2),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("filingExecutionPacketValid", report["failedRequiredChecks"])
            evidence = report["checks"]["filingExecutionPacketValid"]["evidence"]
            self.assertIn("evidenceDependencyMatrix order must be", evidence)
            self.assertIn("evidenceDependencyMatrix.appFilingPdf missing object", evidence)
            self.assertIn(
                "evidenceDependencyMatrix.companyAccount.target must be "
                "Docs/08_Release/AppStoreEvidence/01-company-account.png",
                evidence,
            )
            self.assertIn(
                "evidenceDependencyMatrix.privacyLabel.proves must be "
                "['App Store Connect App Privacy label result is archived', "
                "'privacy label is available for China mainland review materials']",
                evidence,
            )
            self.assertIn(
                "evidenceDependencyMatrix.productionReadinessCurrent.requiredBeforeMainlandSubmit must be True",
                evidence,
            )
            self.assertIn(
                "evidenceDependencyMatrix.productionReadinessCurrent.initialStatus must be pending",
                evidence,
            )

    def test_mainland_filing_privacy_template_is_directly_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_context(root)
            template = json.loads(valid_mainland_filing_privacy_template())
            template["status"] = "captured-live-filing-privacy"
            targets = template["targetEvidenceFiles"]
            template["targetEvidenceFiles"] = {
                "privacyLabel": targets["privacyLabel"],
                "companyAccount": targets["companyAccount"],
                "mainlandAvailability": targets["mainlandAvailability"],
                "mainlandFiling": "Docs/08_Release/AppStoreEvidence/03-filing.png",
                "ageRatingResult": targets["ageRatingResult"],
            }
            template["evidenceFileChecks"] = [
                check for check in template["evidenceFileChecks"] if check["artifactId"] != "companyAccount"
            ]
            template["evidenceFileChecks"][0]["target"] = "Docs/08_Release/AppStoreEvidence/02-wrong.png"
            template["evidenceFileChecks"][0]["sha256"] = "already-filled"
            template["evidenceFileChecks"][0]["sameRoundAsTemplateCapture"] = True
            template["evidenceFileChecks"][0]["secretValuesNotRecorded"] = True
            template["fieldsToVerify"]["privacyPolicyUrl"] = "https://example.com/privacy"
            template["fieldsToVerify"].pop("medicalBoundary")
            template["redactionChecklist"] = ["Hide Apple ID email"]
            template["postCaptureChecks"] = ["python3 Backend/scripts/check_mainland_filing_materials.py"]
            template["completionRule"] = "Evidence is done."
            write(
                root / "Docs/08_Release/AppStoreEvidence/_templates/mainland-filing-privacy-evidence.template.json",
                json.dumps(template, ensure_ascii=False, indent=2),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("mainlandFilingPrivacyEvidenceTemplateValid", report["failedRequiredChecks"])
            evidence = report["checks"]["mainlandFilingPrivacyEvidenceTemplateValid"]["evidence"]
            self.assertIn("mainlandFilingPrivacyTemplate.status must be template-only-not-evidence", evidence)
            self.assertIn("mainlandFilingPrivacyTemplate.targetEvidenceFiles order must be", evidence)
            self.assertIn("mainlandFilingPrivacyTemplate.targetEvidenceFiles.mainlandFiling", evidence)
            self.assertIn("mainlandFilingPrivacyTemplate.evidenceFileChecks.companyAccount missing object", evidence)
            self.assertIn(
                "mainlandFilingPrivacyTemplate.evidenceFileChecks.mainlandAvailability.target must be "
                "Docs/08_Release/AppStoreEvidence/02-mainland-availability.png",
                evidence,
            )
            self.assertIn(
                "mainlandFilingPrivacyTemplate.evidenceFileChecks.mainlandAvailability.sha256 must be 'FILL_AFTER_CAPTURE'",
                evidence,
            )
            self.assertIn(
                "mainlandFilingPrivacyTemplate.evidenceFileChecks.mainlandAvailability.sameRoundAsTemplateCapture must be False",
                evidence,
            )
            self.assertIn(
                "mainlandFilingPrivacyTemplate.evidenceFileChecks.mainlandAvailability.secretValuesNotRecorded must be False",
                evidence,
            )
            self.assertIn("mainlandFilingPrivacyTemplate.fieldsToVerify.privacyPolicyUrl", evidence)
            self.assertIn("mainlandFilingPrivacyTemplate.fieldsToVerify.medicalBoundary", evidence)
            self.assertIn("mainlandFilingPrivacyTemplate.redactionChecklist missing Hide complete phone numbers", evidence)
            self.assertIn("mainlandFilingPrivacyTemplate.postCaptureChecks missing app-store-evidence-20260630T-current.json", evidence)
            self.assertIn("mainlandFilingPrivacyTemplate.completionRule missing template is only a capture worksheet", evidence)

    def test_regional_launch_strategy_must_use_current_proof_context(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stale = (
                valid_regional_strategy()
                .replace("日期：2026-06-30", "日期：2026-06-28")
                .replace("Backend/proof/launch-objective-audit.json", "")
                .replace("XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md", "XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260628.md")
                .replace("20260630T-current", "20260628T-current")
                .replace("不得提交", "可以提交")
            )
            write_valid_context(root, regional_strategy=stale)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("regionalLaunchStrategyCurrent", report["failedRequiredChecks"])
            self.assertIn("mainlandMaterialsUseCurrentDayHandoff", report["failedRequiredChecks"])
            evidence = report["checks"]["regionalLaunchStrategyCurrent"]["evidence"]
            self.assertIn("日期：2026-06-30", evidence)
            self.assertIn("Backend/proof/launch-objective-audit.json", evidence)
            self.assertIn("XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md", evidence)
            self.assertIn("20260630T-current", evidence)
            self.assertIn("不得提交", evidence)

    def test_app_store_compliance_timeline_must_use_current_gate_context(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stale = (
                valid_app_store_compliance_timeline()
                .replace("日期：2026-06-30", "日期：2026-06-18")
                .replace("Backend/proof/launch-objective-audit.json", "")
                .replace("Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260630.json", "Docs/08_Release/APP_STORE_CONNECT_DRAFT.md")
                .replace("Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json", "Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET.json")
                .replace("stableAliasSyncAllowed=false", "stableAliasSyncAllowed=true")
                .replace("不得提交 App Store Connect 审核", "可以提交 App Store Connect 审核")
            )
            write_valid_context(root, app_store_compliance_timeline=stale)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("appStoreComplianceTimelineCurrent", report["failedRequiredChecks"])
            self.assertIn("mainlandMaterialsUseCurrentDayHandoff", report["failedRequiredChecks"])
            evidence = report["checks"]["appStoreComplianceTimelineCurrent"]["evidence"]
            self.assertIn("日期：2026-06-30", evidence)
            self.assertIn("Backend/proof/launch-objective-audit.json", evidence)
            self.assertIn("Docs/08_Release/APP_STORE_CONNECT_DRAFT_20260630.json", evidence)
            self.assertIn("Docs/08_Release/WECHAT_RELEASE_CONFIGURATION_PACKET_20260630.json", evidence)
            self.assertIn("stableAliasSyncAllowed=false", evidence)
            self.assertIn("不得提交 App Store Connect 审核", evidence)

    def test_china_mainland_compliance_must_use_current_proof_context(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            stale = (
                valid_compliance()
                .replace("日期：2026-06-30", "日期：2026-06-28")
                .replace("Backend/proof/launch-objective-audit.json", "")
                .replace("Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md", "Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260628.md")
                .replace("Docs/08_Release/APPLE_DEVELOPER_DUNS_HANDOFF.md", "")
                .replace("iOS 26.5 TestFlight", "TestFlight")
                .replace("不得直接提交", "可以提交")
            )
            write_valid_context(root, compliance=stale)

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("chinaMainlandComplianceCurrent", report["failedRequiredChecks"])
            evidence = report["checks"]["chinaMainlandComplianceCurrent"]["evidence"]
            self.assertIn("日期：2026-06-30", evidence)
            self.assertIn("Backend/proof/launch-objective-audit.json", evidence)
            self.assertIn("Docs/08_Release/XNP_EXTERNAL_PLATFORM_EVIDENCE_HANDOFF_20260630.md", evidence)
            self.assertIn("不得直接提交", evidence)


if __name__ == "__main__":
    unittest.main()
