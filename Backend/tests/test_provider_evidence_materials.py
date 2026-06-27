from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_provider_evidence_materials.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_submission_packet() -> str:
    return """
# APP_STORE_SUBMISSION_PACKET.md

## Pre-Submit Commands

```bash
python3 Backend/scripts/verify_auth_providers.py
python3 Backend/scripts/verify_storage_backend.py
python3 Backend/scripts/check_wechat_client_configuration.py
python3 Backend/scripts/check_provider_evidence_materials.py
python3 Backend/scripts/check_app_store_evidence.py
```
""".lstrip()


def valid_runbook() -> str:
    return """
# CHINA_MAINLAND_APP_STORE_RUNBOOK.md

7. `07-sms-provider.png`：短信签名、模板、验证码发送成功证据，隐藏密钥和手机号中段。
8. `08-wechat-open-platform.png`：微信开放平台移动应用、Bundle ID、URL Scheme / Universal Link 配置证据。
9. `09-obs-policy.png`：OBS bucket、生命周期、加密、删除验证证据，隐藏 AK/SK 和完整对象 key。
""".lstrip()


def valid_evidence_readme() -> str:
    return """
# AppStoreEvidence

| 文件名 | 证明什么 | 脱敏要求 | 当前状态 |
| --- | --- | --- | --- |
| `07-sms-provider.png` | 真实短信服务商、签名、模板和发送成功 | 手机号中段打码，隐藏密钥 | 未完成 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置 | 可见 AppID、Bundle ID、URL Scheme / Universal Link；隐藏 AppSecret | 未完成 |
| `09-obs-policy.png` | 华为 OBS bucket、生命周期、加密、删除策略 | 隐藏 AK/SK 和完整对象路径 | 未完成 |
""".lstrip()


def valid_capture_guide() -> str:
    return """
# CAPTURE_GUIDE.md

| 文件 | 必须能证明 | 保留字段 | 必须遮挡 |
|---|---|---|---|
| `07-sms-provider.png` | 真实短信签名、模板和发送成功 | 服务商、签名、模板 ID/名称、发送成功状态 | AccessKey、Secret、完整手机号、验证码 |
| `08-wechat-open-platform.png` | 微信开放平台移动应用配置完成 | AppID、Bundle ID、URL Scheme、Universal Link | AppSecret、管理员账号 |
| `09-obs-policy.png` | OBS bucket 私有访问、加密、生命周期、删除验证 | bucket/prefix、区域、加密/生命周期/删除策略状态 | AK/SK、完整对象 key |
""".lstrip()


def valid_sms_doc() -> str:
    return """
# Aliyun SMS Webhook Adapter

小奶瓶 API 用 `XNP_SMS_SECRET` 对 webhook body 做 HMAC-SHA256。adapter 使用阿里云 Dysmsapi `SendSms` 发送验证码。
建议使用只允许 `dysms:SendSms` 的 RAM 子账号。
App Store 证据归档到 `07-sms-provider.png`，必须能看到短信签名、模板和发送成功；必须遮挡 AccessKey、Secret、完整手机号、验证码和 `XNP_SMS_SECRET`。
""".lstrip()


def valid_wechat_doc() -> str:
    return """
# WECHAT_CLIENT_CONFIGURATION.md

微信开放平台移动应用 AppID：格式为 `wx + 16 hex`。归档到 `08-wechat-open-platform.png`。
截图要能看到 AppID、Bundle ID、URL Scheme、Universal Link。AppSecret 只配置在服务端，不能写进 iOS 工程或仓库。
""".lstrip()


def valid_obs_doc() -> str:
    return """
# Huawei Cloud OBS Handoff

Use a private bucket. Keep server-side AK/SK only on the backend host.
App Store 证据归档到 `09-obs-policy.png`，必须能看到 bucket、prefix、区域、加密、生命周期和删除验证；必须遮挡 AK/SK 和完整对象 key。
""".lstrip()


def write_valid_docs(root: Path) -> None:
    write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", valid_submission_packet())
    write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook())
    write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_evidence_readme())
    write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide())
    write(root / "Docs/08_Release/WECHAT_CLIENT_CONFIGURATION.md", valid_wechat_doc())
    write(root / "Backend/deploy/aliyun-sms-webhook-adapter.md", valid_sms_doc())
    write(root / "Backend/deploy/huawei-obs.md", valid_obs_doc())


class ProviderEvidenceMaterialsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/provider-evidence-materials.json"
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
        self.assertIn("provider evidence materials", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_materials_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_provider_rows_and_redaction_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_evidence_readme().replace("09-obs-policy.png", "09-storage.png"))
            write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook().replace("09-obs-policy.png", "09-storage.png"))
            write(
                root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md",
                valid_capture_guide().replace("09-obs-policy.png", "09-storage.png").replace("完整手机号、验证码", "手机号"),
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("providerEvidenceFilenamesPresent", report["failedRequiredChecks"])
            self.assertIn("providerEvidenceRedactionCovered", report["failedRequiredChecks"])

    def test_completion_claim_without_archived_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
                valid_submission_packet() + "\n短信服务商证据已完成。OBS 策略证据已完成。\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("doesNotPretendProviderEvidenceCompleteBeforeFiles", report["failedRequiredChecks"])
            evidence = report["checks"]["doesNotPretendProviderEvidenceCompleteBeforeFiles"]["evidence"]
            self.assertIn("短信服务商证据已完成", evidence)
            self.assertIn("OBS 策略证据已完成", evidence)


if __name__ == "__main__":
    unittest.main()
