#!/usr/bin/env bash
# Cron-friendly SQLite backup wrapper.
# Schedules: e.g. every 6 hours via crontab:
#   0 */6 * * * /path/to/cno/scripts/backup_db.sh >> /var/log/cno-backup.log 2>&1
#
# Honors:
#   CNO_DB_PATH         — defaults to ./cno_audit.db
#   CNO_BACKUP_DIR      — defaults to ./backups
#   CNO_BACKUP_RETAIN   — keep N most recent backups (default 30)

set -euo pipefail

DB_PATH="${CNO_DB_PATH:-./cno_audit.db}"
BACKUP_DIR="${CNO_BACKUP_DIR:-$(dirname "$DB_PATH")/backups}"
RETAIN="${CNO_BACKUP_RETAIN:-30}"

if [ ! -f "$DB_PATH" ]; then
    echo "[backup_db] live DB not found: $DB_PATH" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
TARGET="$BACKUP_DIR/$(basename "${DB_PATH%.db}")-$STAMP.db"

# Use sqlite's .backup command — atomic, safe under concurrent writes.
sqlite3 "$DB_PATH" ".backup '$TARGET'"
echo "[backup_db] wrote $TARGET ($(stat -c %s "$TARGET" 2>/dev/null || stat -f %z "$TARGET") bytes)"

# Retention: keep newest $RETAIN, drop the rest.
if [ -n "$RETAIN" ] && [ "$RETAIN" -gt 0 ]; then
    cd "$BACKUP_DIR"
    # shellcheck disable=SC2012
    ls -1t "$(basename "${DB_PATH%.db}")"-*.db 2>/dev/null | tail -n +$((RETAIN + 1)) | while read -r old; do
        echo "[backup_db] pruning $old"
        rm -f "$old"
    done
fi
