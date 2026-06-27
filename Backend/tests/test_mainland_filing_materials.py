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
3. App 备案完成后，需要在 App 显著位置展示备案编号并链接工信部备案系统；拿到备案号后再实现 UI / 静态页展示。
4. 公安联网备案通常在 ICP / App 备案完成并开通服务后继续办理，证据也要归档。

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
| 生产数据库 | `xiaonaiping_prod` | 已有部署 proof，仍需备份/恢复演练 |
| 账号方式 | 恢复密钥、手机号验证码、微信授权 | 手机短信和微信开放平台仍待最终配置 |

## 需要向公司/后台拿到的材料

1. 营业执照电子版。
2. 法定代表人、App 负责人、网站/网络安全负责人证件材料。
3. 域名证书、域名实名认证信息、DNS 解析截图。
4. 云服务器公网 IP、地域、接入商、实例/备案服务号等信息。
5. App 图标、Bundle ID、版本号、应用简介、应用截图。
6. 隐私政策 URL、用户协议 URL、支持 URL 可访问证明。
7. App Store Connect 公司主体截图。
8. 中国大陆只选择可售地区截图。
9. 短信服务商签名、模板、发送成功证明。
10. 微信开放平台移动应用、Bundle ID、URL Scheme、Universal Link 绑定证明。
11. OBS bucket、私有访问、服务端访问、加密、生命周期、删除验证证明。
12. 拿到备案号后的备案编号、备案查询页截图和 App 内展示位置截图。
13. 公安联网备案提交/通过证明。

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
2. 在华为云/接入商备案系统提交 App 备案和适用 ICP 信息。
3. 备案通过后补 App 内/网页备案编号展示。
4. 完成公安联网备案并归档证明。
5. 再提交 App Store Connect 中国大陆审核。
""".lstrip()


def valid_capture_guide() -> str:
    return """
| 文件名 | 说明 | 必须包含 | 不得包含 |
|---|---|---|---|
| `03-app-filing.pdf` 或 `.png` | App 备案/ICP/适用判断进度或结果 | App 名称、主体、备案号或提交状态 | 遮个人证件细节 |
""".lstrip()


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
            write(root / "Docs/08_Release/MAINLAND_FILING_MATERIALS.md", valid_materials())
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide())

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_archive_names_and_redaction_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write(
                root / "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
                valid_materials().replace("03-app-filing.pdf", "03-filing-proof.pdf").replace("拿到备案编号后再做，不提前写占位号", ""),
            )
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", "| bad | bad |\n")

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("evidenceArchiveFilenamesMatchGate", report["failedRequiredChecks"])
            self.assertIn("postFilingCodeChangesDeferredUntilRealNumber", report["failedRequiredChecks"])
            self.assertIn("captureGuideCoversFilingEvidenceRedaction", report["failedRequiredChecks"])

    def test_completion_claim_without_archived_filing_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write(
                root / "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
                valid_materials() + "\n备案已完成。APP备案号：待填\n",
            )
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide())

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("doesNotPretendFilingCompleteBeforeEvidence", report["failedRequiredChecks"])
            evidence = report["checks"]["doesNotPretendFilingCompleteBeforeEvidence"]["evidence"]
            self.assertIn("备案已完成", evidence)
            self.assertIn("placeholderAppFilingNumber", evidence)


if __name__ == "__main__":
    unittest.main()
