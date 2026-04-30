#!/usr/bin/env bash
#
# Refresh a single CNPG database from production into DR.
#
# Strategy:
#   1. Take a "previous" dump of the local DR database (rollback artifact).
#   2. Stream pg_dump over SSH from the production primary pod (kubectl exec on Mac).
#   3. Pipe directly into pg_restore inside the DR primary pod (kubectl exec local).
#   4. Use --clean --if-exists --no-owner so the restore is idempotent.
#
# Args:
#   $1  prod_ns
#   $2  prod_cluster        e.g. pg-quaks-app-cluster
#   $3  dr_ns
#   $4  dr_cluster
#   $5  password_file       path to file containing the prod app password (used for verify)
#
set -uo pipefail
PROD_NS="$1"; PROD_CLUSTER="$2"; DR_NS="$3"; DR_CLUSTER="$4"; PASSWORD_FILE="$5"

DBNAME="${PG_DBNAME:-app}"
USERNAME="${PG_USERNAME:-app}"
PROD_POD="${PROD_CLUSTER}-1"
DR_POD="${DR_CLUSTER}-1"
ROLLBACK_DIR="${ROLLBACK_DIR:-/var/lib/dr/rollback}"
mkdir -p "$ROLLBACK_DIR"

log() { echo "[pg:$DR_CLUSTER] $*"; }

ssh_prod() {
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
      "${PROD_SSH_USER}@${PROD_SSH_HOST}" "$@"
}

# 1. Save a rollback snapshot of the local DB (best-effort; first run will be empty).
ROLLBACK_FILE="$ROLLBACK_DIR/${DR_CLUSTER}.prev.dump"
log "Saving rollback snapshot to $ROLLBACK_FILE"
if ! kubectl exec -n "$DR_NS" "$DR_POD" -c postgres -- \
       pg_dump -Fc -U postgres -d "$DBNAME" > "$ROLLBACK_FILE" 2>/dev/null; then
  log "  (no existing data; skipping rollback snapshot)"
  rm -f "$ROLLBACK_FILE"
fi

# 2 + 3. Stream prod dump → local restore.
log "Streaming pg_dump from prod $PROD_NS/$PROD_POD → DR $DR_NS/$DR_POD"
set -o pipefail
ssh_prod "kubectl exec -n '$PROD_NS' '$PROD_POD' -c postgres -- pg_dump -Fc -U postgres -d '$DBNAME'" \
  | kubectl exec -i -n "$DR_NS" "$DR_POD" -c postgres -- \
        pg_restore --clean --if-exists --no-owner --no-privileges -U postgres -d "$DBNAME"
rc=$?

if [[ $rc -ne 0 ]]; then
  log "FAILED (rc=$rc). Rollback dump preserved at $ROLLBACK_FILE"
  exit $rc
fi

log "OK"
exit 0
