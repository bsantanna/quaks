#!/usr/bin/env bash
#
# Smoke-test the DR replicas. Compares prod vs DR row counts (PG) and doc
# counts (ES). Threshold: DR must be at least 95% of prod (allows for the
# ~1h gap between cron runs). Also asserts the latest vault artifact is
# < 2h old.
#
set -uo pipefail

THRESHOLD="${VERIFY_THRESHOLD:-0.95}"
DR_ES_URL="${DR_ES_URL:-https://elasticsearch-es-http.elastic-system.svc:9200}"
PROD_ES_LOCAL="https://localhost:19200"
DR_PASS="$(cat /secrets/dr/es-elastic-password)"
PROD_PASS="$(cat /secrets/prod/es-elastic-password)"
DR_ES_USER="${DR_ES_USER:-elastic}"

log() { echo "[verify] $*"; }
fail=0

ssh_prod() {
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
      "${PROD_SSH_USER}@${PROD_SSH_HOST}" "$@"
}

# ── Postgres counts ─────────────────────────────────────────────────────────
verify_pg() {
  local prod_ns="$1" prod_cluster="$2" dr_ns="$3" dr_cluster="$4"
  local prod_pod="${prod_cluster}-1"
  local dr_pod="${dr_cluster}-1"
  local q="SELECT sum(reltuples)::bigint FROM pg_class WHERE relkind='r' AND relnamespace IN (SELECT oid FROM pg_namespace WHERE nspname NOT IN ('pg_catalog','information_schema'));"

  local prod_count dr_count
  prod_count=$(ssh_prod "kubectl exec -n '$prod_ns' '$prod_pod' -c postgres -- psql -U postgres -d app -tAc \"$q\"" 2>/dev/null | tr -d ' ' || echo 0)
  dr_count=$(kubectl exec -n "$dr_ns" "$dr_pod" -c postgres -- psql -U postgres -d app -tAc "$q" 2>/dev/null | tr -d ' ' || echo 0)
  prod_count=${prod_count:-0}
  dr_count=${dr_count:-0}

  if (( prod_count == 0 )); then
    log "  $dr_cluster: prod=0 dr=$dr_count (skipping ratio)"
    return 0
  fi

  ratio=$(awk -v p="$prod_count" -v d="$dr_count" 'BEGIN { printf "%.4f", d/p }')
  ok=$(awk -v r="$ratio" -v t="$THRESHOLD" 'BEGIN { print (r >= t) ? 1 : 0 }')
  if [[ "$ok" == "1" ]]; then
    log "  $dr_cluster: prod=$prod_count dr=$dr_count ratio=$ratio OK"
  else
    log "  $dr_cluster: prod=$prod_count dr=$dr_count ratio=$ratio BELOW $THRESHOLD"
    fail=1
  fi
}

log "Postgres counts"
verify_pg "$PROD_NAMESPACE"   pg-quaks-app-cluster         "$DR_NAMESPACE" pg-quaks-app-cluster
verify_pg "$PROD_NAMESPACE"   pg-quaks-vectors-cluster     "$DR_NAMESPACE" pg-quaks-vectors-cluster
verify_pg "$PROD_NAMESPACE"   pg-quaks-checkpoints-cluster "$DR_NAMESPACE" pg-quaks-checkpoints-cluster
verify_pg "$PROD_KEYCLOAK_NS" pg-keycloak-cluster          keycloak        pg-keycloak-cluster

# ── Elasticsearch doc counts ────────────────────────────────────────────────
log "Elasticsearch doc counts"
prod_total=$(curl -sk -u "${ES_REMOTE_USER}:${PROD_PASS}" \
  "$PROD_ES_LOCAL/quaks_*/_count" 2>/dev/null | jq -r '.count // 0')
dr_total=$(curl -sk -u "${DR_ES_USER}:${DR_PASS}" \
  "$DR_ES_URL/quaks_*/_count" 2>/dev/null | jq -r '.count // 0')

if (( prod_total == 0 )); then
  log "  prod=0 dr=$dr_total (skipping ratio)"
else
  ratio=$(awk -v p="$prod_total" -v d="$dr_total" 'BEGIN { printf "%.4f", d/p }')
  ok=$(awk -v r="$ratio" -v t="$THRESHOLD" 'BEGIN { print (r >= t) ? 1 : 0 }')
  if [[ "$ok" == "1" ]]; then
    log "  ES: prod=$prod_total dr=$dr_total ratio=$ratio OK"
  else
    log "  ES: prod=$prod_total dr=$dr_total ratio=$ratio BELOW $THRESHOLD"
    fail=1
  fi
fi

# ── Vault artifact freshness ────────────────────────────────────────────────
log "Vault artifact freshness"
latest=$(ls -1t /var/lib/dr/vault/vault-*.tar.gz 2>/dev/null | head -1 || true)
if [[ -z "$latest" ]]; then
  log "  no vault artifact found"
  fail=1
else
  age_s=$(( $(date +%s) - $(stat -c %Y "$latest") ))
  if (( age_s > 7200 )); then
    log "  $latest age=${age_s}s STALE (>2h)"
    fail=1
  else
    log "  $latest age=${age_s}s OK"
  fi
fi

exit $fail
