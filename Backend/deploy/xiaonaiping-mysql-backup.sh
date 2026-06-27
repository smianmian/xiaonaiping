#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=${XNP_ENV_FILE:-/srv/xiaonaiping/private/xiaonaiping-api.env}
BACKUP_DIR=${XNP_BACKUP_DIR:-/srv/xiaonaiping/backups/mysql}
RETENTION_DAYS=${XNP_BACKUP_RETENTION_DAYS:-14}

set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

cd /

if [ "${XNP_DATABASE_BACKEND:-}" != "mysql" ]; then
  echo "skip: XNP_DATABASE_BACKEND is not mysql"
  exit 0
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

timestamp=$(date -u +%Y%m%dT%H%M%SZ)
output="$BACKUP_DIR/${XNP_MYSQL_DATABASE}-${timestamp}.sql.gz"

MYSQL_PWD="$XNP_MYSQL_PASSWORD" mysqldump \
  --host="$XNP_MYSQL_HOST" \
  --port="${XNP_MYSQL_PORT:-3306}" \
  --user="$XNP_MYSQL_USER" \
  --single-transaction \
  --no-tablespaces \
  --routines \
  --triggers \
  --databases "$XNP_MYSQL_DATABASE" \
  | gzip -9 > "$output"

chmod 600 "$output"
find "$BACKUP_DIR" -type f -name "${XNP_MYSQL_DATABASE}-*.sql.gz" -mtime +"$RETENTION_DAYS" -delete

echo "created $output"
