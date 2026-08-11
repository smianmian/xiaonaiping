#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  XNP_DEPLOY_HOST=root@YOUR_SERVER XNP_REMOTE_TEST_PHONE=+8613800000000 Backend/deploy/deploy-huawei-baota.sh

Required env:
  XNP_DEPLOY_HOST=root@YOUR_SERVER
  XNP_REMOTE_TEST_PHONE=+8613800000000

Optional env:
  XNP_API_BASE_URL=https://api.mewpow.com/xiaonaiping
  XNP_REMOTE_ROOT=/srv/xiaonaiping
  XNP_SERVICE_NAME=xiaonaiping-api.service
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ -z "${XNP_DEPLOY_HOST:-}" ]]; then
  usage >&2
  echo "error: XNP_DEPLOY_HOST is required" >&2
  exit 64
fi

if [[ -z "${XNP_REMOTE_TEST_PHONE:-}" ]]; then
  usage >&2
  echo "error: XNP_REMOTE_TEST_PHONE is required for interactive production SMS verification" >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REMOTE_HOST="$XNP_DEPLOY_HOST"
REMOTE_ROOT="${XNP_REMOTE_ROOT:-/srv/xiaonaiping}"
SERVICE_NAME="${XNP_SERVICE_NAME:-xiaonaiping-api.service}"
BASE_URL="${XNP_API_BASE_URL:-https://api.mewpow.com/xiaonaiping}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BUNDLE_DIR="$REPO_ROOT/Backend/proof/deploy-bundles"

if [[ "$REMOTE_ROOT" != *xiaonaiping* ]]; then
  echo "error: refusing to deploy to non-xiaonaiping root: $REMOTE_ROOT" >&2
  exit 65
fi

if [[ "$SERVICE_NAME" != "xiaonaiping-api.service" ]]; then
  echo "error: refusing to restart non-xiaonaiping service: $SERVICE_NAME" >&2
  exit 65
fi

python3 "$REPO_ROOT/Backend/scripts/build_deploy_bundle.py" \
  --repo-root "$REPO_ROOT" \
  --output-dir "$BUNDLE_DIR"

BUNDLE_PATH="$(find "$BUNDLE_DIR" -maxdepth 1 -name 'xiaonaiping-backend-*.tar.gz' -type f -print | sort | tail -n 1)"
if [[ -z "$BUNDLE_PATH" ]]; then
  echo "error: deploy bundle was not created" >&2
  exit 66
fi

REMOTE_BUNDLE="/tmp/$(basename "$BUNDLE_PATH")"
REMOTE_STORAGE_PROOF="$REMOTE_ROOT/current/Backend/proof/storage-backend-$TIMESTAMP.json"
REMOTE_DEPLOY_PROOF="$REMOTE_ROOT/current/Backend/proof/huawei-baota-deploy-$TIMESTAMP.json"

scp "$BUNDLE_PATH" "$REMOTE_HOST:$REMOTE_BUNDLE"

ssh "$REMOTE_HOST" bash -s -- "$REMOTE_ROOT" "$SERVICE_NAME" "$REMOTE_BUNDLE" "$TIMESTAMP" <<'REMOTE'
set -euo pipefail

REMOTE_ROOT="$1"
SERVICE_NAME="$2"
REMOTE_BUNDLE="$3"
TIMESTAMP="$4"
REMOTE_USER="xiaonaiping"
ENV_FILE="$REMOTE_ROOT/private/xiaonaiping-api.env"
SMS_ADAPTER_ENV_FILE="$REMOTE_ROOT/private/xiaonaiping-aliyun-sms-adapter.env"
SMS_ADAPTER_SERVICE="xiaonaiping-aliyun-sms-adapter.service"
RELEASE="$REMOTE_ROOT/releases/$TIMESTAMP"

case "$REMOTE_ROOT" in
  *xiaonaiping*) ;;
  *) echo "refusing non-xiaonaiping root: $REMOTE_ROOT" >&2; exit 65 ;;
esac

if [[ "$SERVICE_NAME" != "xiaonaiping-api.service" ]]; then
  echo "refusing non-xiaonaiping service: $SERVICE_NAME" >&2
  exit 65
fi

if [[ -e "$RELEASE" ]]; then
  echo "release already exists: $RELEASE" >&2
  exit 66
fi

test -f "$ENV_FILE"
set -a
. "$ENV_FILE"
set +a
SMS_ADAPTER_REQUIRED=0
if [[ "${XNP_SMS_PROVIDER:-}" == "webhook" ]]; then
  case "${XNP_SMS_WEBHOOK_URL:-}" in
    http://127.0.0.1:8791/send|http://localhost:8791/send)
      SMS_ADAPTER_REQUIRED=1
      ;;
  esac
fi
install -d -o "$REMOTE_USER" -g "$REMOTE_USER" -m 750 "$REMOTE_ROOT/releases" "$REMOTE_ROOT/data" "$REMOTE_ROOT/syncs" "$REMOTE_ROOT/logs"
install -d -o "$REMOTE_USER" -g "$REMOTE_USER" -m 750 "$RELEASE"
tar -xzf "$REMOTE_BUNDLE" -C "$RELEASE"
chown -R "$REMOTE_USER:$REMOTE_USER" "$RELEASE"

sudo -u "$REMOTE_USER" python3 -m venv "$RELEASE/Backend/.venv"
sudo -u "$REMOTE_USER" env PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1 PIP_DEFAULT_TIMEOUT=60 \
  timeout 240 "$RELEASE/Backend/.venv/bin/pip" install -r "$RELEASE/Backend/requirements-production.txt"
if [[ -f "$RELEASE/Backend/requirements-obs.txt" ]]; then
  sudo -u "$REMOTE_USER" env PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1 PIP_DEFAULT_TIMEOUT=60 \
    timeout 240 "$RELEASE/Backend/.venv/bin/pip" install -r "$RELEASE/Backend/requirements-obs.txt"
fi
SMS_ADAPTER_DIR="$RELEASE/Backend/sms/aliyun-webhook-adapter"
if [[ -f "$SMS_ADAPTER_DIR/package.json" ]]; then
  if command -v npm >/dev/null 2>&1; then
    sudo -u "$REMOTE_USER" env NPM_CONFIG_AUDIT=false NPM_CONFIG_FUND=false bash -lc '
      set -euo pipefail
      cd "$1"
      if [[ -f package-lock.json ]]; then
        npm ci --omit=dev
      else
        npm install --omit=dev
      fi
    ' bash "$SMS_ADAPTER_DIR"
  else
    echo "warning: npm not found; Aliyun SMS adapter dependencies were not installed" >&2
  fi
fi
if [[ "$SMS_ADAPTER_REQUIRED" == "1" ]]; then
  test -f "$SMS_ADAPTER_ENV_FILE"
  install -m 644 "$RELEASE/Backend/deploy/xiaonaiping-aliyun-sms-adapter.service.example" \
    "/etc/systemd/system/$SMS_ADAPTER_SERVICE"
  systemctl daemon-reload
  systemctl enable "$SMS_ADAPTER_SERVICE" >/dev/null
fi

sudo -u "$REMOTE_USER" -E env XNP_RELEASE_BACKEND="$RELEASE/Backend" bash -lc '
  set -euo pipefail
  cd "$XNP_RELEASE_BACKEND"
  "$XNP_RELEASE_BACKEND/.venv/bin/python" scripts/migrate_database.py
'

ln -sfn "$RELEASE" "$REMOTE_ROOT/current"
systemctl restart "$SERVICE_NAME"
systemctl is-active "$SERVICE_NAME" >/dev/null
if [[ "$SMS_ADAPTER_REQUIRED" == "1" ]]; then
  systemctl restart "$SMS_ADAPTER_SERVICE"
  systemctl is-active "$SMS_ADAPTER_SERVICE" >/dev/null
  for attempt in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:8791/healthz" >/dev/null 2>&1; then
      break
    fi
    if [[ "$attempt" == "30" ]]; then
      echo "SMS adapter did not answer /healthz after restart" >&2
      exit 69
    fi
    sleep 1
  done
fi
for attempt in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:8787/healthz" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "service did not answer /healthz after restart" >&2
    exit 68
  fi
  sleep 1
done
rm -f "$REMOTE_BUNDLE"
REMOTE

check_internal_blocked() {
  local path status
  for path in /internal /internal/ /internal/dashboard /internal/metrics; do
    status="$(curl -sS -o /dev/null -w '%{http_code}' "$BASE_URL$path")"
    case "$status" in
      401|403|404) ;;
      *)
        echo "error: public internal path is not blocked: $BASE_URL$path returned $status" >&2
        exit 67
        ;;
    esac
  done
}

check_internal_blocked

python3 "$REPO_ROOT/Backend/scripts/verify_remote_api.py" \
  --base-url "$BASE_URL" \
  --phone "$XNP_REMOTE_TEST_PHONE" \
  --output "$REPO_ROOT/Backend/proof/remote-api-$TIMESTAMP.json"
cp "$REPO_ROOT/Backend/proof/remote-api-$TIMESTAMP.json" "$REPO_ROOT/Backend/proof/remote-api.json"

ssh "$REMOTE_HOST" bash -s -- "$REMOTE_ROOT" "$REMOTE_STORAGE_PROOF" "$REMOTE_DEPLOY_PROOF" "$BASE_URL" <<'REMOTE'
set -euo pipefail

REMOTE_ROOT="$1"
REMOTE_STORAGE_PROOF="$2"
REMOTE_DEPLOY_PROOF="$3"
BASE_URL="$4"
REMOTE_USER="xiaonaiping"
ENV_FILE="$REMOTE_ROOT/private/xiaonaiping-api.env"
BACKEND="$REMOTE_ROOT/current/Backend"

test -f "$ENV_FILE"
set -a
. "$ENV_FILE"
set +a
install -d -o "$REMOTE_USER" -g "$REMOTE_USER" -m 750 "$BACKEND/proof"

sudo -u "$REMOTE_USER" -E env XNP_RELEASE_BACKEND="$BACKEND" XNP_STORAGE_PROOF="$REMOTE_STORAGE_PROOF" bash -lc '
  set -euo pipefail
  cd "$XNP_RELEASE_BACKEND"
  PYTHONPATH="$XNP_RELEASE_BACKEND" "$XNP_RELEASE_BACKEND/.venv/bin/python" scripts/verify_storage_backend.py \
    --data-dir "$XNP_DATA_DIR" \
    --output "$XNP_STORAGE_PROOF"
'

/usr/bin/python3 "$BACKEND/scripts/collect_deployment_proof.py" \
  --env-file "$ENV_FILE" \
  --base-url "$BASE_URL" \
  --service-active \
  --public-internal-blocked \
  --output "$REMOTE_DEPLOY_PROOF"

chown "$REMOTE_USER:$REMOTE_USER" "$REMOTE_STORAGE_PROOF" "$REMOTE_DEPLOY_PROOF"
REMOTE

scp "$REMOTE_HOST:$REMOTE_STORAGE_PROOF" "$REPO_ROOT/Backend/proof/storage-backend-$TIMESTAMP.json"
scp "$REMOTE_HOST:$REMOTE_DEPLOY_PROOF" "$REPO_ROOT/Backend/proof/huawei-baota-deploy-$TIMESTAMP.json"
cp "$REPO_ROOT/Backend/proof/storage-backend-$TIMESTAMP.json" "$REPO_ROOT/Backend/proof/storage-backend.json"
cp "$REPO_ROOT/Backend/proof/huawei-baota-deploy-$TIMESTAMP.json" "$REPO_ROOT/Backend/proof/huawei-baota-deploy.json"

echo "deploy completed: $BASE_URL"
echo "proof:"
echo "  Backend/proof/remote-api-$TIMESTAMP.json"
echo "  Backend/proof/storage-backend-$TIMESTAMP.json"
echo "  Backend/proof/huawei-baota-deploy-$TIMESTAMP.json"
