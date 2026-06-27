from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_production_readiness.py"


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_png_header(path: Path, width: int, height: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + (13).to_bytes(4, "big")
        + b"IHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )


def write_minimal_repo(root: Path, release_url: str, app_metadata_url: str, remote_proof: bool) -> None:
    write(
        root / "App/iOS/project.yml",
        f"""
settings:
  configs:
    Release:
      XNP_API_BASE_URL: "{release_url}"
""".lstrip(),
    )
    for relative in [
        "Docs/07_PrivacySecurity/PRIVACY_REVIEW.md",
        "Docs/07_PrivacySecurity/SDK_DATA_INVENTORY.md",
        "Docs/05_QA/TEST_PLAN.md",
        "Docs/06_Release/RELEASE_CHECKLIST.md",
        "Docs/06_Release/PROOF_PACK.md",
        "Docs/08_Release/REGIONAL_LAUNCH_STRATEGY.md",
        "Docs/08_Release/APP_STORE_PRIVACY_LABEL.json",
        "Docs/08_Release/APP_STORE_SUBMISSION_PACKET.md",
        "Docs/08_Release/MAINLAND_FILING_MATERIALS.md",
        "Docs/08_Release/PRIVACY_POLICY_DRAFT.md",
        "Docs/08_Release/TERMS_OF_USE_DRAFT.md",
        "Docs/08_Release/SCREENSHOT_PLAN.md",
        "Docs/06_Release/ROLLBACK_PLAN.md",
    ]:
        write(root / relative, "# ok\n")
    write(root / "Docs/08_Release/APP_STORE_METADATA.md", f"Privacy URL: {app_metadata_url}\n")
    write(
        root / "Backend/proof/release-flow.json",
        json.dumps({"passed": True, "checks": {"accountCreated": True}, "failedChecks": []}),
    )
    if remote_proof:
        write(
            root / "Backend/proof/remote-api.json",
            json.dumps(
                {
                    "passed": True,
                    "apiBaseUrl": release_url,
                    "checks": {"healthz": True, "accountCreated": True},
                    "failedChecks": [],
                }
            ),
        )
    deployment_proof = json.dumps(
        {
            "remotePaths": {"dataDir": "/srv/xiaonaiping/data"},
            "isolation": {
                "mysqlUser": "xiaonaiping_app",
                "mysqlDatabase": "xiaonaiping_prod",
            },
            "runtime": {},
            "publicRoute": {
                "publicInternalPathsBlocked": True,
                "blockedPaths": ["/xiaonaiping/internal", "/xiaonaiping/internal/"],
            },
            "privateEnvStatus": {"set": [], "empty": []},
        }
    )
    write(root / "Backend/proof/huawei-baota-deploy.json", deployment_proof)
    write(root / "Backend/proof/huawei-baota-deploy-20260620.json", deployment_proof)
    write(
        root / "Backend/proof/storage-backend.json",
        json.dumps(
            {
                "passed": True,
                "storageBackend": "huawei_obs",
                "checks": {
                    "photoUploaded": True,
                    "photoDownloaded": True,
                    "photoDeleted": True,
                    "accountDeleteRemovedPhotos": True,
                },
                "failedChecks": [],
            }
        ),
    )
    write(
        root / "Backend/proof/ios-release-readiness.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "releaseApiBaseURLConfigured": {"passed": True},
                    "weChatOpenSDKLinked": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/ios-app-bundle.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "appPath": "/tmp/XiaoNaiPing.app",
                "checks": {
                    "releaseApiBaseURLMatches": {"passed": True},
                    "privacyManifestBundled": {"passed": True},
                    "debugWeChatCodeAbsent": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/ios-265-build.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "simulatorAppPath": "/tmp/XiaoNaiPing-Gate-ReleaseSim-26_5/Build/Products/Release-iphonesimulator/XiaoNaiPing.app",
                "deviceAppPath": "/tmp/XiaoNaiPing-Gate-ReleaseDevice-26_5/Build/Products/Release-iphoneos/XiaoNaiPing.app",
                "checks": {
                    "simulatorBuiltWithIOS265": {"passed": True},
                    "deviceBuiltWithIOS265": {"passed": True},
                    "simulatorBundleIdentifierMatches": {"passed": True},
                    "deviceBundleIdentifierMatches": {"passed": True},
                    "simulatorPrivacyManifestBundled": {"passed": True},
                    "devicePrivacyManifestBundled": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/testflight-precheck.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "appPath": "/tmp/XiaoNaiPing.app",
                "checks": {
                    "widgetExtensionBundled": {"passed": True},
                    "widgetBundleIncludesTodayAndLiveActivity": {"passed": True},
                    "localNotificationSchedulerPresent": {"passed": True},
                    "noHealthKitOrPressureSourceSurface": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/testflight-regression-plan.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "reviewAccountRedactedProofPresent": {"passed": True},
                    "regressionCaseIdsComplete": {"passed": True},
                    "regressionCoverageComplete": {"passed": True},
                    "externalAuthCasesMarkedPending": {"passed": True},
                    "passCriteriaSeparateExternalAuthAndEvidence": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/sim-launch-ios265-20260626.json",
        json.dumps(
            {
                "passed": True,
                "simulator": {
                    "name": "iPhone 17 Pro",
                    "runtime": "iOS 26.5",
                },
                "app": {
                    "dtPlatformVersion": "26.5",
                    "dtSdkName": "iphonesimulator26.5",
                },
                "launchOutput": "com.mewpow.xiaonaiping: 15975",
            }
        ),
    )
    write(
        root / "Backend/proof/app-store-assets.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "appIcon1024PngValid": {"passed": True},
                    "appIconHasNoAlpha": {"passed": True},
                    "finalScreenshotsAcceptedSizes": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/app-store-connect-materials.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "appNameMatches": {"passed": True},
                    "subtitleWithinLimit": {"passed": True},
                    "primaryCategoryLifestyle": {"passed": True},
                    "secondaryCategoryBlank": {"passed": True},
                    "publicUrlsMatch": {"passed": True},
                    "screenshotCopyComplete": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/app-store-connect-evidence-materials.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "appStoreConnectEvidenceFilenamesPresent": {"passed": True},
                    "appStoreConnectEvidenceRedactionCovered": {"passed": True},
                    "privacyLabelJsonMatchesEvidenceChecklist": {"passed": True},
                    "doesNotPretendAppStoreConnectEvidenceCompleteBeforeFiles": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/app-store-submission-packet.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "officialAppleCheckpointsPresent": {"passed": True},
                    "reviewNotesPresent": {"passed": True},
                    "privacyLabelSourcesComplete": {"passed": True},
                    "preSubmitCommandsComplete": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/mainland-filing-materials.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "materialsDocumentPresent": {"passed": True},
                    "currentJudgmentCoversLaunchAndFilingPath": {"passed": True},
                    "draftFilingFieldsComplete": {"passed": True},
                    "evidenceArchiveFilenamesMatchGate": {"passed": True},
                    "doesNotPretendFilingCompleteBeforeEvidence": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/signed-archive-testflight-materials.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "signingArchiveStatusDocumentsCurrentBlocker": {"passed": True},
                    "postArchiveBundleVerificationRequired": {"passed": True},
                    "signedArchiveAndTestFlightEvidenceFilenamesPresent": {"passed": True},
                    "signedArchiveAndTestFlightEvidenceRedactionCovered": {"passed": True},
                    "testFlightEvidenceBoundaryPresent": {"passed": True},
                    "doesNotPretendArchiveOrTestFlightCompleteBeforeEvidence": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/provider-evidence-materials.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "providerEvidenceFilenamesPresent": {"passed": True},
                    "providerEvidenceRedactionCovered": {"passed": True},
                    "smsProviderMaterialCoversSignatureTemplateSendAndSecrets": {"passed": True},
                    "wechatOpenPlatformMaterialCoversClientServerSecretBoundary": {"passed": True},
                    "huaweiObsMaterialCoversBucketEncryptionLifecycleDeletion": {"passed": True},
                    "doesNotPretendProviderEvidenceCompleteBeforeFiles": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/auth-providers.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "authDebugModeDisabled": {"passed": True},
                    "smsProviderConfigured": {"passed": True},
                    "wechatProviderConfigured": {"passed": True},
                    "wechatDebugLoginRejected": {"passed": True},
                    "smsLiveSendVerified": {"passed": False, "required": False},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/diagnostics-redaction.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "iosNoThirdPartyCrashOrAnalyticsSDK": {"passed": True},
                    "iosNoClientLoggingCalls": {"passed": True},
                    "privacyManifestDiagnosticsDeclared": {"passed": True},
                    "backendPhotoLogPathRedacted": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/public-pages.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "privacyPageMainlandFirst": {"passed": True},
                    "privacyPageHongKongSecond": {"passed": True},
                    "privacyPageCompanyEntity": {"passed": True},
                    "termsPagePhoneAndWeChatLogin": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/review-notes.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "submissionReviewNotesFree": {"passed": True},
                    "submissionReviewNotesNoMedicalAdvice": {"passed": True},
                    "submissionReviewNotesDeletionPath": {"passed": True},
                    "metadataReviewNotesNoDebugCode": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/legal-drafts.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "privacyCurrentDate": {"passed": True},
                    "privacyCompanyEntity": {"passed": True},
                    "privacyMainlandFirst": {"passed": True},
                    "termsCurrentDate": {"passed": True},
                    "termsAccountMethods": {"passed": True},
                    "termsOutdatedRecoveryOnly": {"passed": True},
                },
            }
        ),
    )
    write(
        root / "Backend/proof/universal-links.json",
        json.dumps(
            {
                "passed": True,
                "failedRequiredChecks": [],
                "checks": {
                    "aasaFilePresent": {"passed": True},
                    "aasaExpectedAppIDPresent": {"passed": True},
                    "iosAssociatedDomainsEntitlementPresent": {"passed": True},
                    "universalLinkPathCoveredByAASA": {"passed": True},
                },
            }
        ),
    )


class ProductionReadinessTest(unittest.TestCase):
    def run_checker(self, root: Path, env: dict[str, str] | None = None, *extra_args: str) -> dict:
        output = root / "Backend/proof/production-readiness.json"
        process_env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("XNP_") and not key.startswith("HUAWEI_OBS_")
        }
        process_env.update(env or {})
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(root),
                "--output",
                str(output),
                "--allow-incomplete",
                *extra_args,
            ],
            env=process_env,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("production readiness", completed.stderr + completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_placeholder_release_url_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            write_minimal_repo(root, "", "https://api.example.com/privacy", remote_proof=False)

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["productionApiBaseUrlPresent"]["passed"])
            self.assertFalse(report["checks"]["remoteReleaseFlowProofPassed"]["passed"])
            self.assertFalse(report["checks"]["appStoreUrlsFinalized"]["passed"])

    def test_full_offline_gate_can_pass_with_production_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write_png_header(root / "Docs/08_Release/Screenshots/home.png", 1206, 2622)
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs", "--require-screenshots")

            self.assertTrue(report["ready"])
            self.assertEqual(report["failedRequiredChecks"], [])

    def test_sample_wechat_app_id_blocks_production_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write_png_header(root / "Docs/08_Release/Screenshots/home.png", 1206, 2622)
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wx1234567890abcdef",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs", "--require-screenshots")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["wechatLoginProviderConfigured"]["passed"])
            self.assertIn("wechatLoginProviderConfigured", report["failedRequiredChecks"])

    def test_emotion_app_namespace_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write_png_header(root / "Docs/08_Release/Screenshots/home.png", 1206, 2622)
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/emotion-isle/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "127.0.0.1",
                "XNP_MYSQL_USER": "ydm_user",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "emotion_isle",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "ydm-prod",
                "HUAWEI_OBS_PREFIX": "ydm",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs", "--require-screenshots")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["xiaonaipingProductionNamespaceConfigured"]["passed"])
            self.assertFalse(report["checks"]["sharedServiceNamespaceRejected"]["passed"])

    def test_deployment_proof_can_supply_remote_private_provider_state(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write_png_header(root / "Docs/08_Release/Screenshots/home.png", 1206, 2622)
            deployment_proof = json.dumps(
                {
                    "remotePaths": {"dataDir": "/srv/xiaonaiping/data"},
                    "isolation": {
                        "mysqlUser": "xiaonaiping_app",
                        "mysqlDatabase": "xiaonaiping_prod",
                    },
                    "runtime": {
                        "databaseBackend": "mysql",
                        "storageBackend": "huawei_obs",
                    },
                    "publicEnvValues": {
                        "XNP_STORAGE_BACKEND": "huawei_obs",
                        "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                        "HUAWEI_OBS_PREFIX": "xiaonaiping",
                        "XNP_SMS_PROVIDER": "webhook",
                    },
                    "providerChecks": {
                        "authDebugModeDisabled": True,
                        "storageBackendIsHuaweiOBS": True,
                        "obsBucketHasXiaoNaiPingNamespace": True,
                        "smsProviderIsWebhook": True,
                        "wechatAppIDConfigured": True,
                    },
                    "publicRoute": {
                        "publicInternalPathsBlocked": True,
                        "blockedPaths": ["/xiaonaiping/internal", "/xiaonaiping/internal/"],
                    },
                    "privateEnvStatus": {
                        "set": [
                            "XNP_SECRET_KEY",
                            "XNP_ADMIN_TOKEN",
                            "XNP_MYSQL_HOST",
                            "XNP_MYSQL_USER",
                            "XNP_MYSQL_PASSWORD",
                            "XNP_MYSQL_DATABASE",
                            "HUAWEI_OBS_ACCESS_KEY_ID",
                            "HUAWEI_OBS_SECRET_ACCESS_KEY",
                            "HUAWEI_OBS_ENDPOINT",
                            "HUAWEI_OBS_BUCKET",
                            "XNP_SMS_SECRET",
                            "XNP_SMS_WEBHOOK_URL",
                            "XNP_WECHAT_APP_ID",
                            "XNP_WECHAT_APP_SECRET",
                        ],
                        "empty": [],
                    },
                }
            )
            write(root / "Backend/proof/huawei-baota-deploy.json", deployment_proof)
            write(root / "Backend/proof/huawei-baota-deploy-20260620.json", deployment_proof)

            report = self.run_checker(root, None, "--require-huawei-obs", "--require-screenshots")

            self.assertTrue(report["ready"])
            self.assertTrue(report["checks"]["phoneLoginProviderConfigured"]["passed"])
            self.assertTrue(report["checks"]["wechatLoginProviderConfigured"]["passed"])

    def test_auth_debug_mode_is_rejected_for_production(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write_png_header(root / "Docs/08_Release/Screenshots/home.png", 1206, 2622)
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_AUTH_DEBUG_MODE": "1",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs", "--require-screenshots")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["authDebugModeDisabled"]["passed"])

    def test_app_store_manual_evidence_can_be_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write_png_header(root / "Docs/08_Release/Screenshots/home.png", 1206, 2622)
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(
                root,
                env,
                "--require-huawei-obs",
                "--require-screenshots",
                "--require-app-store-evidence",
            )

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["appStoreManualEvidenceReady"]["passed"])

    def test_app_store_connect_materials_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/app-store-connect-materials.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["metadataNoHealthFitnessCategoryAlternative"],
                        "checks": {
                            "metadataNoHealthFitnessCategoryAlternative": {
                                "passed": False,
                                "required": True,
                                "evidence": "Health & Fitness alternate category remains",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["appStoreConnectMaterialsProofPassed"]["passed"])

    def test_app_store_submission_packet_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/app-store-submission-packet.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["officialAppleCheckpointsPresent"],
                        "checks": {
                            "officialAppleCheckpointsPresent": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing App Review Guidelines URL",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["appStoreSubmissionPacketProofPassed"]["passed"])

    def test_app_store_connect_evidence_materials_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/app-store-connect-evidence-materials.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["privacyLabelJsonMatchesEvidenceChecklist"],
                        "checks": {
                            "privacyLabelJsonMatchesEvidenceChecklist": {
                                "passed": False,
                                "required": True,
                                "evidence": "usesTracking=true",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["appStoreConnectEvidenceMaterialsProofPassed"]["passed"])

    def test_mainland_filing_materials_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/mainland-filing-materials.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["evidenceArchiveFilenamesMatchGate"],
                        "checks": {
                            "evidenceArchiveFilenamesMatchGate": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing 03-app-filing.pdf",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["mainlandFilingMaterialsProofPassed"]["passed"])

    def test_signed_archive_testflight_materials_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/signed-archive-testflight-materials.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["preSubmitCommandsIncludeArchiveTestFlightGate"],
                        "checks": {
                            "preSubmitCommandsIncludeArchiveTestFlightGate": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing check_signed_archive_testflight_materials.py",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["signedArchiveTestFlightMaterialsProofPassed"]["passed"])

    def test_provider_evidence_materials_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/provider-evidence-materials.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["providerEvidenceRedactionCovered"],
                        "checks": {
                            "providerEvidenceRedactionCovered": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing AppSecret redaction",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["providerEvidenceMaterialsProofPassed"]["passed"])

    def test_testflight_regression_plan_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/testflight-regression-plan.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["regressionCoverageComplete"],
                        "checks": {
                            "regressionCoverageComplete": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing widget regression case",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["testFlightRegressionPlanProofPassed"]["passed"])

    def test_ios_release_readiness_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/ios-release-readiness.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["weChatOpenSDKLinked"],
                        "checks": {
                            "weChatOpenSDKLinked": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing SDK",
                            }
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["iosReleaseReadinessProofPassed"]["passed"])

    def test_ios_265_build_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/ios-265-build.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["deviceBuiltWithIOS265"],
                        "checks": {
                            "deviceBuiltWithIOS265": {
                                "passed": False,
                                "required": True,
                                "evidence": "DTSDKName=iphoneos18.5",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["ios265BuildProofPassed"]["passed"])

    def test_testflight_client_precheck_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/testflight-precheck.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["widgetBundleIncludesTodayAndLiveActivity"],
                        "checks": {
                            "widgetBundleIncludesTodayAndLiveActivity": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing Live Activity widget",
                            }
                        },
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["testFlightClientPrecheckProofPassed"]["passed"])

    def test_ios_265_simulator_launch_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/sim-launch-ios265-20260626.json",
                json.dumps(
                    {
                        "passed": True,
                        "simulator": {"runtime": "iOS 18.5"},
                        "app": {
                            "dtPlatformVersion": "18.5",
                            "dtSdkName": "iphonesimulator18.5",
                        },
                        "launchOutput": "com.mewpow.xiaonaiping: 123",
                    }
                ),
            )

            report = self.run_checker(root)

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["ios265SimulatorLaunchProofPassed"]["passed"])

    def test_ios_app_bundle_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/ios-app-bundle.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["privacyManifestBundled"],
                        "checks": {
                            "privacyManifestBundled": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing bundle manifest",
                            }
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["iosAppBundleProofPassed"]["passed"])

    def test_app_store_assets_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/app-store-assets.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["appIconHasNoAlpha"],
                        "checks": {
                            "appIconHasNoAlpha": {
                                "passed": False,
                                "required": True,
                                "evidence": "icon has alpha",
                            }
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["appStoreAssetsProofPassed"]["passed"])

    def test_auth_provider_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/auth-providers.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["smsProviderConfigured", "wechatProviderConfigured"],
                        "checks": {
                            "smsProviderConfigured": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing SMS provider",
                            },
                            "wechatProviderConfigured": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing WeChat provider",
                            },
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["authProvidersProofPassed"]["passed"])

    def test_diagnostics_redaction_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/diagnostics-redaction.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["backendPhotoLogPathRedacted"],
                        "checks": {
                            "backendPhotoLogPathRedacted": {
                                "passed": False,
                                "required": True,
                                "evidence": "photo object key can appear in logs",
                            }
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["diagnosticsRedactionProofPassed"]["passed"])

    def test_public_pages_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/public-pages.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["privacyOutdatedHongKongUsFirst"],
                        "checks": {
                            "privacyOutdatedHongKongUsFirst": {
                                "passed": False,
                                "required": True,
                                "evidence": "privacy.html contains old region strategy",
                            }
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["publicPagesProofPassed"]["passed"])

    def test_review_notes_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/review-notes.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["submissionReviewNotesDeletionPath"],
                        "checks": {
                            "submissionReviewNotesDeletionPath": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing deletion path",
                            }
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["reviewNotesProofPassed"]["passed"])

    def test_legal_drafts_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/legal-drafts.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["termsOutdatedRecoveryOnly"],
                        "checks": {
                            "termsOutdatedRecoveryOnly": {
                                "passed": False,
                                "required": True,
                                "evidence": "old recovery-only account copy",
                            }
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["legalDraftsProofPassed"]["passed"])

    def test_universal_links_proof_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            release_url = "https://api.xiaonaiping.test"
            write_minimal_repo(root, release_url, release_url + "/privacy", remote_proof=True)
            write(
                root / "Backend/proof/universal-links.json",
                json.dumps(
                    {
                        "passed": False,
                        "failedRequiredChecks": ["universalLinkPathCoveredByAASA"],
                        "checks": {
                            "universalLinkPathCoveredByAASA": {
                                "passed": False,
                                "required": True,
                                "evidence": "missing WeChat callback path",
                            }
                        },
                    }
                ),
            )
            env = {
                "XNP_SECRET_KEY": "production-secret-key-with-enough-length",
                "XNP_DATA_DIR": "/srv/xiaonaiping/data",
                "XNP_DATABASE_BACKEND": "mysql",
                "XNP_MYSQL_HOST": "rds.internal",
                "XNP_MYSQL_USER": "xiaonaiping",
                "XNP_MYSQL_PASSWORD": "configured",
                "XNP_MYSQL_DATABASE": "xiaonaiping",
                "XNP_STORAGE_BACKEND": "huawei_obs",
                "HUAWEI_OBS_ACCESS_KEY_ID": "set",
                "HUAWEI_OBS_SECRET_ACCESS_KEY": "set",
                "HUAWEI_OBS_ENDPOINT": "https://obs.example.test",
                "HUAWEI_OBS_BUCKET": "xiaonaiping-prod",
                "HUAWEI_OBS_PREFIX": "xiaonaiping",
                "XNP_SMS_PROVIDER": "webhook",
                "XNP_SMS_SECRET": "configured",
                "XNP_SMS_WEBHOOK_URL": "https://sms.example.test/send",
                "XNP_WECHAT_APP_ID": "wxa4f19c3e802b7d65",
                "XNP_WECHAT_APP_SECRET": "configured",
                "XNP_ADMIN_TOKEN": "production-admin-token-with-enough-length",
            }

            report = self.run_checker(root, env, "--require-huawei-obs")

            self.assertFalse(report["ready"])
            self.assertFalse(report["checks"]["universalLinksProofPassed"]["passed"])


if __name__ == "__main__":
    unittest.main()
