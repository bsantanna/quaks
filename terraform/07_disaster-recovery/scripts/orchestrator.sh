#!/usr/bin/env bash
#
# Disaster recovery orchestrator. Runs each per-source backup script, captures
# its exit code, continues on individual failures, and exits non-zero if any
# source failed. Designed to run as the entrypoint of a hourly Kubernetes CronJob.
#
# Required environment variables (provided via CronJob env / mounted secrets):
#   PROD_SSH_USER       SSH user for the production (Mac) host
#   PROD_SSH_HOST       SSH host or IP of the production host
#   PROD_KUBECONTEXT    kubectl context name on the production host (optional)
#   DR_NAMESPACE        Namespace on the DR cluster hosting CNPG clusters
#   PROD_NAMESPACE      Namespace on production hosting CNPG clusters (quaks)
#   PROD_KEYCLOAK_NS    Namespace on production hosting keycloak CNPG cluster
#   PROD_VAULT_NS       Namespace on production hosting Vault
#   PROD_ES_NS          Namespace on production hosting Elasticsearch
#   ES_REMOTE_URL       Production Elasticsearch URL (https://elasticsearch-es-http.elastic:9200)
#   ES_REMOTE_USER      Production Elasticsearch username (typically "elastic")
#   VAULT_UNSEAL_KEY    Production Vault unseal key (used to unseal DR vault after restore)
#   LOG_DIR             Directory where logs are persisted (mounted hostPath PV)
#
# Required secret-mounted files:
#   /secrets/ssh/id_rsa                    SSH private key authorized on production host
#   /secrets/prod/es-api-key               Elasticsearch API key (read-only against quaks_*)
#   /secrets/prod/es-elastic-password      Elasticsearch elastic-user password (cluster-wide ops)
#   /secrets/prod/pg-<cluster>-password    Per-cluster app password
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_DIR="${LOG_DIR:-/var/log/dr}"
mkdir -p "$LOG_DIR"
RUN_LOG="$LOG_DIR/run-$RUN_TS.log"

# Tee all output to both stdout (for kubectl logs) and the persistent log file.
exec > >(tee -a "$RUN_LOG") 2>&1

log()  { echo "[$(date -u +%FT%TZ)] $*"; }
fail() { log "FAIL: $*"; }

log "DR run starting (run id: $RUN_TS)"

# Ensure SSH key has correct permissions and known_hosts is set up.
install -m 0600 /secrets/ssh/id_rsa /root/.ssh/id_rsa
ssh-keyscan -H "$PROD_SSH_HOST" >> /root/.ssh/known_hosts 2>/dev/null

declare -A RESULT
SOURCES=(pg-quaks-app pg-quaks-vectors pg-quaks-checkpoints pg-keycloak vault elasticsearch)

run_source() {
  local name="$1"
  local script="$2"
  shift 2
  log "=== START $name ==="
  if "$SCRIPT_DIR/$script" "$@"; then
    RESULT[$name]="ok"
    log "=== OK    $name ==="
  else
    RESULT[$name]="failed"
    fail "=== FAIL  $name (exit $?) ==="
  fi
}

# CNPG clusters: pg.sh <prod-namespace> <prod-cluster> <dr-namespace> <dr-cluster> <password-file>
run_source "pg-quaks-app"          pg.sh "$PROD_NAMESPACE"  pg-quaks-app-cluster         "$DR_NAMESPACE" pg-quaks-app-cluster         /secrets/prod/pg-quaks-app-password
run_source "pg-quaks-vectors"      pg.sh "$PROD_NAMESPACE"  pg-quaks-vectors-cluster     "$DR_NAMESPACE" pg-quaks-vectors-cluster     /secrets/prod/pg-quaks-vectors-password
run_source "pg-quaks-checkpoints"  pg.sh "$PROD_NAMESPACE"  pg-quaks-checkpoints-cluster "$DR_NAMESPACE" pg-quaks-checkpoints-cluster /secrets/prod/pg-quaks-checkpoints-password
run_source "pg-keycloak"           pg.sh "$PROD_KEYCLOAK_NS" pg-keycloak-cluster         keycloak        pg-keycloak-cluster          /secrets/prod/pg-keycloak-password

run_source "vault"                 vault.sh
run_source "elasticsearch"         es.sh

log "=== START verify ==="
if "$SCRIPT_DIR/verify.sh"; then
  RESULT[verify]="ok"
  log "=== OK    verify ==="
else
  RESULT[verify]="failed"
  fail "=== FAIL  verify ==="
fi

log ""
log "Summary for run $RUN_TS:"
overall=0
for s in "${SOURCES[@]}" verify; do
  status="${RESULT[$s]:-skipped}"
  log "  $s: $status"
  [[ "$status" != "ok" ]] && overall=1
done

# Retention: keep last 168 logs (7 days at hourly cadence).
ls -1t "$LOG_DIR"/run-*.log 2>/dev/null | tail -n +169 | xargs -r rm -f

log "DR run finished (exit $overall)"
exit $overall
