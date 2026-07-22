#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: run_launch_readiness.sh [options]

Run XiaoNaiPing launch-readiness checks and regenerate proof files in one pass.

Options:
  --repo-root PATH            Repository root (default: script directory's parent)
  --base-url URL              Public API base URL for remote checks
                              (default: https://api.mewpow.com/xiaonaiping)
  --env-file PATH             Private production .env (optional, loaded into env)
  --deployment-proof PATH     Existing deployment proof to reuse instead of refreshing
  --storage-proof PATH        Existing storage proof to reuse instead of refreshing
  --auth-providers-proof PATH Existing auth proof to reuse instead of refreshing
  --app-path PATH             XiaoNaiPing.app for iOS bundle and TestFlight client checks
  --ios-simulator-log PATH    iOS 26.5 simulator xcodebuild log for build proof
  --ios-device-log PATH       iOS 26.5 generic device xcodebuild log for build proof
  --sim-launch-proof PATH     iOS 26.5 simulator install/launch proof
                              (default: latest Backend/proof/sim-launch-ios265-*.json)
  --live-check                Enable live auth-provider checks that hit production APIs
  --skip-ios-bundle            Skip iOS .app bundle check
  --help                      Show help

Examples:
  Backend/scripts/run_launch_readiness.sh \
    --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
    --base-url https://api.mewpow.com/xiaonaiping \
    --live-check
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BASE_URL="https://api.mewpow.com/xiaonaiping"
ENV_FILE=""
DEPLOYMENT_PROOF=""
STORAGE_PROOF_INPUT=""
AUTH_PROOF_INPUT=""
APP_PATH=""
IOS_SIMULATOR_LOG=""
IOS_DEVICE_LOG=""
SIM_LAUNCH_PROOF=""
LIVE_CHECK=0
SKIP_IOS_BUNDLE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --deployment-proof)
      DEPLOYMENT_PROOF="$2"
      shift 2
      ;;
    --storage-proof)
      STORAGE_PROOF_INPUT="$2"
      shift 2
      ;;
    --auth-providers-proof)
      AUTH_PROOF_INPUT="$2"
      shift 2
      ;;
    --app-path)
      APP_PATH="$2"
      shift 2
      ;;
    --ios-simulator-log)
      IOS_SIMULATOR_LOG="$2"
      shift 2
      ;;
    --ios-device-log)
      IOS_DEVICE_LOG="$2"
      shift 2
      ;;
    --sim-launch-proof)
      SIM_LAUNCH_PROOF="$2"
      shift 2
      ;;
    --live-check)
      LIVE_CHECK=1
      shift
      ;;
    --skip-ios-bundle)
      SKIP_IOS_BUNDLE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

cd "$REPO_ROOT"

if [[ -z "$SIM_LAUNCH_PROOF" ]]; then
  SIM_LAUNCH_PROOF="$(find Backend/proof -maxdepth 1 -name 'sim-launch-ios265-*.json' -print 2>/dev/null | sort | tail -n 1 || true)"
fi
if [[ -z "$SIM_LAUNCH_PROOF" ]]; then
  SIM_LAUNCH_PROOF="Backend/proof/sim-launch-ios265-20260626.json"
fi

if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "env file not found: $ENV_FILE" >&2
    exit 1
  fi

  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

run_or_fail() {
  local name="$1"
  shift
  if "$@" >/tmp/xnp-launch-step.log 2>&1; then
    echo "[ok] $name"
  else
    echo "[warn] $name (failed). tail:"
    echo "---"
    cat /tmp/xnp-launch-step.log
    echo "---"
    FAILED=1
  fi
}

proof_status() {
  local proof="$1"
  local key="$2"
  python3 - "$proof" "$key" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
key = sys.argv[2]
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception as error:
    print(f"cannot read {path}: {error}")
    raise SystemExit(2)

value = data.get(key)
failed = data.get("failedRequiredChecks")
missing = data.get("missingEvidence")

if value is True:
    print(f"{key}=true")
    raise SystemExit(0)

def format_value(value):
    if isinstance(value, bool):
        return str(value).lower()
    return repr(value)

parts = [f"{key}={format_value(value)}"]
if failed:
    parts.append("failedRequiredChecks=" + ", ".join(str(item) for item in failed))
if missing:
    parts.append("missingEvidence=" + ", ".join(str(item) for item in missing))
print("; ".join(parts))
raise SystemExit(1)
PY
}

mark_proof_status() {
  local name="$1"
  local proof="$2"
  local key="$3"
  local status

  if status="$(proof_status "$proof" "$key" 2>&1)"; then
    echo "[proof-ok] $name (${status})"
  else
    echo "[incomplete] $name (${status})"
    FAILED=1
  fi
}

publish_latest_proof() {
  local source="$1"
  local target="$2"
  if [[ -f "$source" ]]; then
    cp "$source" "$target"
  fi
}

latest_current_proof() {
  local prefix="$1"
  local date_compact="$2"
  local same_day="Backend/proof/${prefix}-${date_compact}T-current.json"
  if [[ -f "$same_day" ]]; then
    echo "$same_day"
    return
  fi
  find Backend/proof -maxdepth 1 -name "${prefix}-*T-current.json" -print 2>/dev/null | sort | tail -n 1 || true
}

FAILED=0
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PROOF_DATE="$(date +%Y-%m-%d)"
PROOF_DATE_COMPACT="${PROOF_DATE//-/}"
REMOTE_PROOF="Backend/proof/remote-api-${TIMESTAMP}.json"
STORAGE_PROOF="Backend/proof/storage-backend-${TIMESTAMP}.json"
AUTH_PROOF="Backend/proof/auth-providers-${TIMESTAMP}.json"
DIAG_PROOF="Backend/proof/diagnostics-redaction-${TIMESTAMP}.json"
PUBLIC_PAGES_PROOF="Backend/proof/public-pages-${TIMESTAMP}.json"
REVIEW_NOTES_PROOF="Backend/proof/review-notes-${TIMESTAMP}.json"
LEGAL_DRAFTS_PROOF="Backend/proof/legal-drafts-${TIMESTAMP}.json"
UNIVERSAL_LINKS_PROOF="Backend/proof/universal-links-${TIMESTAMP}.json"
WECHAT_CLIENT_CONFIG="Backend/proof/wechat-client-configuration-${TIMESTAMP}.json"
MAINLAND_FILING_MATERIALS="Backend/proof/mainland-filing-materials-${TIMESTAMP}.json"
PROVIDER_EVIDENCE_MATERIALS="Backend/proof/provider-evidence-materials-${TIMESTAMP}.json"
APP_STORE_EVIDENCE="Backend/proof/app-store-evidence-${TIMESTAMP}.json"
IOS_RELEASE_PROOF="Backend/proof/ios-release-readiness-${TIMESTAMP}.json"
IOS_APP_BUNDLE_PROOF="Backend/proof/ios-app-bundle-${TIMESTAMP}.json"
IOS_265_BUILD_PROOF="Backend/proof/ios-265-build-${TIMESTAMP}.json"
IOS_265_DEVICE_AVAILABILITY="Backend/proof/ios265-device-availability-${TIMESTAMP}.json"
TESTFLIGHT_PRECHECK_PROOF="Backend/proof/testflight-precheck-${TIMESTAMP}.json"
TESTFLIGHT_REGRESSION_PLAN="Backend/proof/testflight-regression-plan-${TIMESTAMP}.json"
APP_STORE_ASSETS="Backend/proof/app-store-assets-${TIMESTAMP}.json"
APP_STORE_CONNECT_MATERIALS="Backend/proof/app-store-connect-materials-${TIMESTAMP}.json"
APP_STORE_CONNECT_EVIDENCE_MATERIALS="Backend/proof/app-store-connect-evidence-materials-${TIMESTAMP}.json"
APP_STORE_SUBMISSION_PACKET="Backend/proof/app-store-submission-packet-${TIMESTAMP}.json"
LAUNCH_DAY_ROLLOVER="Backend/proof/launch-day-rollover-${TIMESTAMP}.json"
LAUNCH_OPERATOR_WORKBENCH="Backend/proof/launch-operator-workbench-${TIMESTAMP}.json"
SIGNED_ARCHIVE_TESTFLIGHT_MATERIALS="Backend/proof/signed-archive-testflight-materials-${TIMESTAMP}.json"
DEPLOY_PROOF="Backend/proof/huawei-baota-deploy-${TIMESTAMP}.json"
PRODUCTION_PROOF="Backend/proof/production-readiness-${TIMESTAMP}.json"
LAUNCH_BLOCKER_SCOPE="Backend/proof/launch-blocker-scope-${TIMESTAMP}.json"
LAUNCH_OBJECTIVE_AUDIT="Backend/proof/launch-objective-audit-${TIMESTAMP}.json"
LAUNCH_BLOCKER_ACTION_PACKET="Backend/proof/launch-blocker-action-packet-${TIMESTAMP}.json"

if [[ -n "$DEPLOYMENT_PROOF" ]]; then
  if [[ ! -f "$DEPLOYMENT_PROOF" ]]; then
    echo "deployment proof not found: $DEPLOYMENT_PROOF" >&2
    exit 1
  fi
  DEPLOY_PROOF_FOR_PROD="$DEPLOYMENT_PROOF"
  echo "[skip] collect deployment proof (using --deployment-proof ${DEPLOYMENT_PROOF})"
elif [[ -n "$ENV_FILE" ]]; then
  DEPLOY_PROOF_ARGS=(
    --env-file "$ENV_FILE"
    --output "$DEPLOY_PROOF"
    --base-url "$BASE_URL"
    --service-active
    --public-internal-blocked
  )

  run_or_fail "collect deployment proof" \
    python3 Backend/scripts/collect_deployment_proof.py \
    "${DEPLOY_PROOF_ARGS[@]}"
  publish_latest_proof "$DEPLOY_PROOF" "Backend/proof/huawei-baota-deploy.json"
  DEPLOY_PROOF_FOR_PROD="$DEPLOY_PROOF"
else
  DEPLOY_PROOF_FOR_PROD="$(latest_current_proof "huawei-baota-deploy" "$PROOF_DATE_COMPACT")"
  if [[ -n "$DEPLOY_PROOF_FOR_PROD" ]]; then
    echo "[skip] collect deployment proof (no --env-file; using current ${DEPLOY_PROOF_FOR_PROD})"
  else
    DEPLOY_PROOF_FOR_PROD="Backend/proof/huawei-baota-deploy.json"
  fi
  if [[ -f "$DEPLOY_PROOF_FOR_PROD" ]]; then
    if [[ "$DEPLOY_PROOF_FOR_PROD" == "Backend/proof/huawei-baota-deploy.json" ]]; then
      echo "[skip] collect deployment proof (no --env-file; using ${DEPLOY_PROOF_FOR_PROD})"
    fi
  else
    echo "[warn] no --env-file or existing deployment proof; production readiness will fail this gate"
    FAILED=1
  fi
fi

run_or_fail "verify remote API" \
  python3 Backend/scripts/verify_remote_api.py \
  --base-url "$BASE_URL" \
  --output "$REMOTE_PROOF"
publish_latest_proof "$REMOTE_PROOF" "Backend/proof/remote-api.json"

if [[ -n "$STORAGE_PROOF_INPUT" ]]; then
  if [[ ! -f "$STORAGE_PROOF_INPUT" ]]; then
    echo "storage proof not found: $STORAGE_PROOF_INPUT" >&2
    exit 1
  fi
  STORAGE_PROOF_FOR_PROD="$STORAGE_PROOF_INPUT"
  echo "[skip] verify storage backend (using --storage-proof ${STORAGE_PROOF_INPUT})"
elif [[ -n "$ENV_FILE" ]]; then
  run_or_fail "verify storage backend" \
    python3 Backend/scripts/verify_storage_backend.py \
    --output "$STORAGE_PROOF"
  publish_latest_proof "$STORAGE_PROOF" "Backend/proof/storage-backend.json"
  STORAGE_PROOF_FOR_PROD="$STORAGE_PROOF"
else
  STORAGE_PROOF_FOR_PROD="$(latest_current_proof "storage-backend" "$PROOF_DATE_COMPACT")"
  if [[ -n "$STORAGE_PROOF_FOR_PROD" ]]; then
    echo "[skip] verify storage backend (no --env-file; using current ${STORAGE_PROOF_FOR_PROD})"
  else
    STORAGE_PROOF_FOR_PROD="Backend/proof/storage-backend.json"
  fi
  if [[ -f "$STORAGE_PROOF_FOR_PROD" ]]; then
    if [[ "$STORAGE_PROOF_FOR_PROD" == "Backend/proof/storage-backend.json" ]]; then
      echo "[skip] verify storage backend (no --env-file; using ${STORAGE_PROOF_FOR_PROD})"
    fi
  else
    echo "[warn] no --env-file or existing storage proof; production readiness will fail this gate"
    FAILED=1
  fi
fi

if [[ -n "$AUTH_PROOF_INPUT" ]]; then
  if [[ ! -f "$AUTH_PROOF_INPUT" ]]; then
    echo "auth providers proof not found: $AUTH_PROOF_INPUT" >&2
    exit 1
  fi
  AUTH_PROOF_FOR_PROD="$AUTH_PROOF_INPUT"
  echo "[skip] verify auth providers (using --auth-providers-proof ${AUTH_PROOF_INPUT})"
else
  AUTH_ARGS=(
    --deployment-proof "$DEPLOY_PROOF_FOR_PROD"
    --base-url "$BASE_URL"
    --output "$AUTH_PROOF"
  )
  if [[ $LIVE_CHECK -eq 1 ]]; then
    AUTH_ARGS+=(--live-check)
  fi

  run_or_fail "verify auth providers" \
    python3 Backend/scripts/verify_auth_providers.py \
    "${AUTH_ARGS[@]}"
  publish_latest_proof "$AUTH_PROOF" "Backend/proof/auth-providers.json"
  AUTH_PROOF_FOR_PROD="$AUTH_PROOF"
fi

run_or_fail "check diagnostics redaction" \
  python3 Backend/scripts/check_diagnostics_redaction.py \
  --output "$DIAG_PROOF"
publish_latest_proof "$DIAG_PROOF" "Backend/proof/diagnostics-redaction.json"

run_or_fail "check public pages" \
  python3 Backend/scripts/check_public_pages.py \
  --output "$PUBLIC_PAGES_PROOF"
publish_latest_proof "$PUBLIC_PAGES_PROOF" "Backend/proof/public-pages.json"

run_or_fail "check review notes" \
  python3 Backend/scripts/check_review_notes.py \
  --output "$REVIEW_NOTES_PROOF"
publish_latest_proof "$REVIEW_NOTES_PROOF" "Backend/proof/review-notes.json"

run_or_fail "check legal drafts" \
  python3 Backend/scripts/check_legal_drafts.py \
  --output "$LEGAL_DRAFTS_PROOF"
publish_latest_proof "$LEGAL_DRAFTS_PROOF" "Backend/proof/legal-drafts.json"

run_or_fail "check universal links" \
  python3 Backend/scripts/check_universal_links.py \
  --output "$UNIVERSAL_LINKS_PROOF"
publish_latest_proof "$UNIVERSAL_LINKS_PROOF" "Backend/proof/universal-links.json"

run_or_fail "check WeChat client configuration handoff" \
  python3 Backend/scripts/check_wechat_client_configuration.py \
  --output "$WECHAT_CLIENT_CONFIG"
publish_latest_proof "$WECHAT_CLIENT_CONFIG" "Backend/proof/wechat-client-configuration.json"
mark_proof_status "check WeChat client configuration handoff" "$WECHAT_CLIENT_CONFIG" "passed"

run_or_fail "check mainland filing materials" \
  python3 Backend/scripts/check_mainland_filing_materials.py \
  --output "$MAINLAND_FILING_MATERIALS"
publish_latest_proof "$MAINLAND_FILING_MATERIALS" "Backend/proof/mainland-filing-materials.json"
mark_proof_status "check mainland filing materials" "$MAINLAND_FILING_MATERIALS" "passed"

run_or_fail "generate app store evidence proof" \
  python3 Backend/scripts/check_app_store_evidence.py \
  --allow-incomplete \
  --date "$PROOF_DATE" \
  --output "$APP_STORE_EVIDENCE"
publish_latest_proof "$APP_STORE_EVIDENCE" "Backend/proof/app-store-evidence.json"
mark_proof_status "check app store evidence" "$APP_STORE_EVIDENCE" "ready"

run_or_fail "generate iOS release readiness proof" \
  python3 Backend/scripts/check_ios_release_readiness.py \
  --allow-incomplete \
  --output "$IOS_RELEASE_PROOF"
publish_latest_proof "$IOS_RELEASE_PROOF" "Backend/proof/ios-release-readiness.json"
mark_proof_status "check iOS release readiness" "$IOS_RELEASE_PROOF" "passed"

IOS_265_BUILD_ARGS=(
  --allow-incomplete
  --output "$IOS_265_BUILD_PROOF"
)
if [[ -n "$IOS_SIMULATOR_LOG" ]]; then
  IOS_265_BUILD_ARGS+=(--simulator-log "$IOS_SIMULATOR_LOG")
fi
if [[ -n "$IOS_DEVICE_LOG" ]]; then
  IOS_265_BUILD_ARGS+=(--device-log "$IOS_DEVICE_LOG")
fi

run_or_fail "generate iOS 26.5 build proof" \
  python3 Backend/scripts/check_ios_265_build_proof.py \
  "${IOS_265_BUILD_ARGS[@]}"
publish_latest_proof "$IOS_265_BUILD_PROOF" "Backend/proof/ios-265-build.json"
mark_proof_status "check iOS 26.5 build proof" "$IOS_265_BUILD_PROOF" "passed"

run_or_fail "check iOS 26.5 device availability" \
  python3 Backend/scripts/check_ios265_device_availability.py \
  --output "$IOS_265_DEVICE_AVAILABILITY" \
  --allow-incomplete
publish_latest_proof "$IOS_265_DEVICE_AVAILABILITY" "Backend/proof/ios265-device-availability.json"
mark_proof_status "check iOS 26.5 device availability proof" "$IOS_265_DEVICE_AVAILABILITY" "passed"

if [[ $SKIP_IOS_BUNDLE -eq 0 && -n "$APP_PATH" ]]; then
  run_or_fail "generate iOS app bundle proof" \
    python3 Backend/scripts/check_ios_app_bundle.py \
    --app "$APP_PATH" \
    --allow-incomplete \
    --output "$IOS_APP_BUNDLE_PROOF"
  publish_latest_proof "$IOS_APP_BUNDLE_PROOF" "Backend/proof/ios-app-bundle.json"
  mark_proof_status "check iOS app bundle" "$IOS_APP_BUNDLE_PROOF" "passed"

  run_or_fail "generate TestFlight client precheck proof" \
    python3 Backend/scripts/check_testflight_precheck.py \
    --app "$APP_PATH" \
    --allow-incomplete \
    --output "$TESTFLIGHT_PRECHECK_PROOF"
  publish_latest_proof "$TESTFLIGHT_PRECHECK_PROOF" "Backend/proof/testflight-precheck.json"
  mark_proof_status "check TestFlight client precheck" "$TESTFLIGHT_PRECHECK_PROOF" "passed"
elif [[ $SKIP_IOS_BUNDLE -eq 1 ]]; then
  echo "[skip] iOS app bundle check and TestFlight client precheck"
else
  echo "[skip] iOS app bundle check and TestFlight client precheck (pass --app-path to include)"
fi

IOS_APP_BUNDLE_PROOF_FOR_PROD="$IOS_APP_BUNDLE_PROOF"
if [[ ! -f "$IOS_APP_BUNDLE_PROOF_FOR_PROD" ]]; then
  IOS_APP_BUNDLE_PROOF_FOR_PROD="Backend/proof/ios-app-bundle.json"
fi
TESTFLIGHT_PRECHECK_PROOF_FOR_PROD="$TESTFLIGHT_PRECHECK_PROOF"
if [[ ! -f "$TESTFLIGHT_PRECHECK_PROOF_FOR_PROD" ]]; then
  TESTFLIGHT_PRECHECK_PROOF_FOR_PROD="Backend/proof/testflight-precheck.json"
fi

run_or_fail "check App Store assets" \
  python3 Backend/scripts/check_app_store_assets.py \
  --output "$APP_STORE_ASSETS"
publish_latest_proof "$APP_STORE_ASSETS" "Backend/proof/app-store-assets.json"

run_or_fail "check App Store Connect materials" \
  python3 Backend/scripts/check_app_store_connect_materials.py \
  --expected-material-date "$PROOF_DATE_COMPACT" \
  --output "$APP_STORE_CONNECT_MATERIALS"
publish_latest_proof "$APP_STORE_CONNECT_MATERIALS" "Backend/proof/app-store-connect-materials.json"

run_or_fail "check App Store Connect evidence materials" \
  python3 Backend/scripts/check_app_store_connect_evidence_materials.py \
  --expected-material-date "$PROOF_DATE_COMPACT" \
  --output "$APP_STORE_CONNECT_EVIDENCE_MATERIALS"
publish_latest_proof "$APP_STORE_CONNECT_EVIDENCE_MATERIALS" "Backend/proof/app-store-connect-evidence-materials.json"
mark_proof_status "check App Store Connect evidence materials" "$APP_STORE_CONNECT_EVIDENCE_MATERIALS" "passed"

run_or_fail "check App Store submission packet" \
  python3 Backend/scripts/check_app_store_submission_packet.py \
  --output "$APP_STORE_SUBMISSION_PACKET"
publish_latest_proof "$APP_STORE_SUBMISSION_PACKET" "Backend/proof/app-store-submission-packet.json"

run_or_fail "check launch day rollover" \
  python3 Backend/scripts/check_launch_day_rollover.py \
  --output "$LAUNCH_DAY_ROLLOVER"
publish_latest_proof "$LAUNCH_DAY_ROLLOVER" "Backend/proof/launch-day-rollover.json"
mark_proof_status "check launch day rollover" "$LAUNCH_DAY_ROLLOVER" "passed"

run_or_fail "check launch operator workbench" \
  python3 Backend/scripts/check_launch_operator_workbench.py \
  --output "$LAUNCH_OPERATOR_WORKBENCH"
publish_latest_proof "$LAUNCH_OPERATOR_WORKBENCH" "Backend/proof/launch-operator-workbench.json"
mark_proof_status "check launch operator workbench" "$LAUNCH_OPERATOR_WORKBENCH" "passed"

run_or_fail "check signed archive and TestFlight materials" \
  python3 Backend/scripts/check_signed_archive_testflight_materials.py \
  --output "$SIGNED_ARCHIVE_TESTFLIGHT_MATERIALS"
publish_latest_proof "$SIGNED_ARCHIVE_TESTFLIGHT_MATERIALS" "Backend/proof/signed-archive-testflight-materials.json"
mark_proof_status "check signed archive and TestFlight materials" "$SIGNED_ARCHIVE_TESTFLIGHT_MATERIALS" "passed"

run_or_fail "check provider evidence materials" \
  python3 Backend/scripts/check_provider_evidence_materials.py \
  --output "$PROVIDER_EVIDENCE_MATERIALS"
publish_latest_proof "$PROVIDER_EVIDENCE_MATERIALS" "Backend/proof/provider-evidence-materials.json"
mark_proof_status "check provider evidence materials" "$PROVIDER_EVIDENCE_MATERIALS" "passed"

run_or_fail "check TestFlight regression plan" \
  python3 Backend/scripts/check_testflight_regression_plan.py \
  --app-store-evidence-proof "$APP_STORE_EVIDENCE" \
  --output "$TESTFLIGHT_REGRESSION_PLAN"
publish_latest_proof "$TESTFLIGHT_REGRESSION_PLAN" "Backend/proof/testflight-regression-plan.json"

PROD_ARGS=(
  --base-url "$BASE_URL"
  --deployment-proof "$DEPLOY_PROOF_FOR_PROD"
  --remote-proof "$REMOTE_PROOF"
  --storage-proof "$STORAGE_PROOF_FOR_PROD"
  --ios-release-proof "$IOS_RELEASE_PROOF"
  --ios-265-build-proof "$IOS_265_BUILD_PROOF"
  --app-store-assets-proof "$APP_STORE_ASSETS"
  --app-store-connect-materials-proof "$APP_STORE_CONNECT_MATERIALS"
  --app-store-connect-evidence-materials-proof "$APP_STORE_CONNECT_EVIDENCE_MATERIALS"
  --app-store-submission-packet-proof "$APP_STORE_SUBMISSION_PACKET"
  --mainland-filing-materials-proof "$MAINLAND_FILING_MATERIALS"
  --signed-archive-testflight-materials-proof "$SIGNED_ARCHIVE_TESTFLIGHT_MATERIALS"
  --provider-evidence-materials-proof "$PROVIDER_EVIDENCE_MATERIALS"
  --testflight-precheck-proof "$TESTFLIGHT_PRECHECK_PROOF_FOR_PROD"
  --testflight-regression-plan-proof "$TESTFLIGHT_REGRESSION_PLAN"
  --sim-launch-proof "$SIM_LAUNCH_PROOF"
  --auth-providers-proof "$AUTH_PROOF_FOR_PROD"
  --diagnostics-redaction-proof "$DIAG_PROOF"
  --public-pages-proof "$PUBLIC_PAGES_PROOF"
  --review-notes-proof "$REVIEW_NOTES_PROOF"
  --legal-drafts-proof "$LEGAL_DRAFTS_PROOF"
  --universal-links-proof "$UNIVERSAL_LINKS_PROOF"
  --app-store-evidence "$APP_STORE_EVIDENCE"
  --require-huawei-obs
  --require-screenshots
  --require-app-store-evidence
  --expected-proof-date "$PROOF_DATE"
  --output "$PRODUCTION_PROOF"
  --allow-incomplete
)
if [[ $LIVE_CHECK -eq 1 ]]; then
  PROD_ARGS+=(--live-check)
fi

if [[ -f "$IOS_APP_BUNDLE_PROOF_FOR_PROD" ]]; then
  PROD_ARGS+=(--ios-app-bundle-proof "$IOS_APP_BUNDLE_PROOF_FOR_PROD")
fi

run_or_fail "generate production readiness proof" \
  python3 Backend/scripts/check_production_readiness.py "${PROD_ARGS[@]}"
publish_latest_proof "$PRODUCTION_PROOF" "Backend/proof/production-readiness.json"
mark_proof_status "check production readiness" "$PRODUCTION_PROOF" "ready"

run_or_fail "check launch blocker scope" \
  python3 Backend/scripts/check_launch_blocker_scope.py \
  --production-proof "$PRODUCTION_PROOF" \
  --app-store-evidence "$APP_STORE_EVIDENCE" \
  --auth-providers-proof "$AUTH_PROOF_FOR_PROD" \
  --ios-release-proof "$IOS_RELEASE_PROOF" \
  --ios-app-bundle-proof "$IOS_APP_BUNDLE_PROOF_FOR_PROD" \
  --output "$LAUNCH_BLOCKER_SCOPE"
publish_latest_proof "$LAUNCH_BLOCKER_SCOPE" "Backend/proof/launch-blocker-scope.json"

run_or_fail "generate launch objective audit proof" \
  python3 Backend/scripts/check_launch_objective_audit.py \
  --production-readiness "$PRODUCTION_PROOF" \
  --ios-265-build "$IOS_265_BUILD_PROOF" \
  --ios-release "$IOS_RELEASE_PROOF" \
  --ios-app-bundle "$IOS_APP_BUNDLE_PROOF_FOR_PROD" \
  --auth-providers "$AUTH_PROOF_FOR_PROD" \
  --app-store-assets "$APP_STORE_ASSETS" \
  --app-store-connect-materials "$APP_STORE_CONNECT_MATERIALS" \
  --app-store-connect-evidence-materials "$APP_STORE_CONNECT_EVIDENCE_MATERIALS" \
  --app-store-submission-packet "$APP_STORE_SUBMISSION_PACKET" \
  --launch-day-rollover "$LAUNCH_DAY_ROLLOVER" \
  --launch-operator-workbench "$LAUNCH_OPERATOR_WORKBENCH" \
  --mainland-filing-materials "$MAINLAND_FILING_MATERIALS" \
  --signed-archive-testflight-materials "$SIGNED_ARCHIVE_TESTFLIGHT_MATERIALS" \
  --provider-evidence-materials "$PROVIDER_EVIDENCE_MATERIALS" \
  --testflight-precheck "$TESTFLIGHT_PRECHECK_PROOF_FOR_PROD" \
  --testflight-regression-plan "$TESTFLIGHT_REGRESSION_PLAN" \
  --app-store-evidence "$APP_STORE_EVIDENCE" \
  --review-notes "$REVIEW_NOTES_PROOF" \
  --remote-api "$REMOTE_PROOF" \
  --public-pages "$PUBLIC_PAGES_PROOF" \
  --legal-drafts "$LEGAL_DRAFTS_PROOF" \
  --diagnostics-redaction "$DIAG_PROOF" \
  --universal-links "$UNIVERSAL_LINKS_PROOF" \
  --wechat-client-configuration "$WECHAT_CLIENT_CONFIG" \
  --storage-backend "$STORAGE_PROOF_FOR_PROD" \
  --output "$LAUNCH_OBJECTIVE_AUDIT" \
  --allow-incomplete
publish_latest_proof "$LAUNCH_OBJECTIVE_AUDIT" "Backend/proof/launch-objective-audit.json"
mark_proof_status "check launch objective audit" "$LAUNCH_OBJECTIVE_AUDIT" "ready"

run_or_fail "check launch blocker action packet" \
  python3 Backend/scripts/check_launch_blocker_action_packet.py \
  --launch-objective-audit "$LAUNCH_OBJECTIVE_AUDIT" \
  --app-store-evidence "$APP_STORE_EVIDENCE" \
  --output "$LAUNCH_BLOCKER_ACTION_PACKET" \
  --allow-incomplete
publish_latest_proof "$LAUNCH_BLOCKER_ACTION_PACKET" "Backend/proof/launch-blocker-action-packet.json"
mark_proof_status "check launch blocker action packet" "$LAUNCH_BLOCKER_ACTION_PACKET" "passed"

cat <<SUMMARY

Launch readiness checks complete. Proof outputs refreshed:
  production: ${PRODUCTION_PROOF}
  launch-blocker-scope: ${LAUNCH_BLOCKER_SCOPE}
  launch-objective-audit: ${LAUNCH_OBJECTIVE_AUDIT}
  launch-blocker-action-packet: ${LAUNCH_BLOCKER_ACTION_PACKET}
  wechat-client-configuration: ${WECHAT_CLIENT_CONFIG}
  mainland-filing-materials: ${MAINLAND_FILING_MATERIALS}
  signed-archive-testflight-materials: ${SIGNED_ARCHIVE_TESTFLIGHT_MATERIALS}
  provider-evidence-materials: ${PROVIDER_EVIDENCE_MATERIALS}
  ios-release: ${IOS_RELEASE_PROOF}
  ios-265-build: ${IOS_265_BUILD_PROOF}
  sim-launch-proof: ${SIM_LAUNCH_PROOF}
  ios265-device-availability: ${IOS_265_DEVICE_AVAILABILITY}
  app-store-connect-materials: ${APP_STORE_CONNECT_MATERIALS}
  app-store-connect-evidence-materials: ${APP_STORE_CONNECT_EVIDENCE_MATERIALS}
  app-store-submission-packet: ${APP_STORE_SUBMISSION_PACKET}
  launch-day-rollover: ${LAUNCH_DAY_ROLLOVER}
  launch-operator-workbench: ${LAUNCH_OPERATOR_WORKBENCH}
  testflight-precheck: ${TESTFLIGHT_PRECHECK_PROOF_FOR_PROD}
  testflight-regression-plan: ${TESTFLIGHT_REGRESSION_PLAN}
  auth-providers: ${AUTH_PROOF_FOR_PROD}
  app-store-evidence: ${APP_STORE_EVIDENCE}
  evidence-date: ${PROOF_DATE}
  deployment: ${DEPLOY_PROOF_FOR_PROD}
  storage: ${STORAGE_PROOF_FOR_PROD}
  remote-api: ${REMOTE_PROOF}
SUMMARY

if [[ $FAILED -eq 1 ]]; then
  echo "Some checks failed; do not treat this as submission-ready yet."
  exit 1
fi

echo "All checks command steps ran successfully."
