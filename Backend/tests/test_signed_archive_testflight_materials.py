from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_signed_archive_testflight_materials.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def valid_submission_packet() -> str:
    return """
# APP_STORE_SUBMISSION_PACKET.md

## Signing and Archive Status

Current archive command:

```bash
xcodebuild -project App/iOS/XiaoNaiPing.xcodeproj -scheme XiaoNaiPing -configuration Release -destination 'generic/platform=iOS' -archivePath /tmp/XiaoNaiPing-CN.xcarchive archive
```

Current result: failed because Xcode signing has no Development Team configured. Configure the Apple Developer Team and App Store Distribution signing before uploading a build to App Store Connect.

## Screenshot Status

Final screenshots require TestFlight or signed-device final screenshots. No real baby photos. Copy review for medical and privacy claims. 本地模拟器和候选截图不替代 TestFlight / 签名真机回归；最终证据必须来自 iOS 26.5 TestFlight 或签名真机包。

## Pre-Submit Commands

```bash
python3 Backend/scripts/check_signed_archive_testflight_materials.py
python3 Backend/scripts/check_ios_app_bundle.py
python3 Backend/scripts/check_testflight_precheck.py
python3 Backend/scripts/check_testflight_regression_plan.py
python3 Backend/scripts/check_app_store_evidence.py
```
""".lstrip()


def valid_bundle_verification() -> str:
    return """
# IOS_RELEASE_BUNDLE_VERIFICATION.md

Current iOS 26.5 bundle evidence is captured by `Backend/proof/ios-265-build.json` and `Backend/proof/ios-app-bundle.json`.
Release iPhoneOS artifact uses `iphoneos26.5`.

## 仍需补齐

1. App Store Distribution 签名归档。
2. TestFlight 上传后的同一套包体扫描和真机回归证据。
""".lstrip()


def valid_runbook() -> str:
    return """
# CHINA_MAINLAND_APP_STORE_RUNBOOK.md

Archive 命令必须在配置 Apple Developer Team 和 App Store Distribution 签名后成功；archive 后还要用导出的 `.app` 重新跑 `check_ios_app_bundle.py`。

## 证据归档

5. `05-signed-archive.png`：App Store Distribution Archive 成功截图。
6. `06-testflight.png`：TestFlight 构建和测试状态截图。
""".lstrip()


def valid_evidence_readme() -> str:
    return """
# AppStoreEvidence

| 文件名 | 证明什么 |
| --- | --- |
| `05-signed-archive.png` | App Store Distribution Archive 成功 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试 |
| `12-real-device-regression.md` | iOS 26.5 TestFlight 或签名真机回归；TestFlight 或签名真机包；不替代 TestFlight / 签名真机回归 |
""".lstrip()


def valid_capture_guide() -> str:
    return """
# CAPTURE_GUIDE.md

| 文件 | 必须能证明 | 保留字段 | 必须遮挡 |
|---|---|---|---|
| `05-signed-archive.png` | App Store Distribution archive 成功 | Bundle ID、版本、build、archive success / uploaded status | Apple ID 邮箱 |
| `06-testflight.png` | TestFlight 构建已处理完成并可测试 | Build 号、版本、处理状态、测试状态 | 测试员邮箱 |
""".lstrip()


def write_valid_docs(root: Path) -> None:
    write(root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md", valid_submission_packet())
    write(root / "Docs/08_Release/IOS_RELEASE_BUNDLE_VERIFICATION.md", valid_bundle_verification())
    write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook())
    write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_evidence_readme())
    write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide())


class SignedArchiveTestFlightMaterialsTest(unittest.TestCase):
    def run_checker(self, root: Path) -> dict:
        output = root / "Backend/proof/signed-archive-testflight-materials.json"
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
        self.assertIn("signed archive/TestFlight materials", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_valid_materials_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)

            report = self.run_checker(root)

            self.assertTrue(report["passed"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_missing_evidence_names_and_redaction_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(root / "Docs/08_Release/CHINA_MAINLAND_APP_STORE_RUNBOOK.md", valid_runbook().replace("06-testflight.png", "06-build.png"))
            write(root / "Docs/08_Release/AppStoreEvidence/README.md", valid_evidence_readme().replace("06-testflight.png", "06-build.png"))
            write(root / "Docs/08_Release/AppStoreEvidence/CAPTURE_GUIDE.md", valid_capture_guide().replace("06-testflight.png", "06-build.png").replace("Apple ID 邮箱", ""))

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("signedArchiveAndTestFlightEvidenceFilenamesPresent", report["failedRequiredChecks"])
            self.assertIn("signedArchiveAndTestFlightEvidenceRedactionCovered", report["failedRequiredChecks"])

    def test_completion_claim_without_archived_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_valid_docs(root)
            write(
                root / "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
                valid_submission_packet() + "\nArchive 已完成。TestFlight 已完成。\n",
            )

            report = self.run_checker(root)

            self.assertFalse(report["passed"])
            self.assertIn("doesNotPretendArchiveOrTestFlightCompleteBeforeEvidence", report["failedRequiredChecks"])
            evidence = report["checks"]["doesNotPretendArchiveOrTestFlightCompleteBeforeEvidence"]["evidence"]
            self.assertIn("Archive 已完成", evidence)
            self.assertIn("TestFlight 已完成", evidence)


if __name__ == "__main__":
    unittest.main()
