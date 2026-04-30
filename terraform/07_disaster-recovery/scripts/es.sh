#!/usr/bin/env bash
#
# Mirror all quaks_* Elasticsearch indices from production into DR ES, then
# snapshot DR ES locally for point-in-time recovery.
#
# Approach:
#   1. Open an SSH tunnel that exposes prod ES at https://localhost:19200
#      via `kubectl port-forward` running on the production (Mac) host.
#   2. Discover quaks_* indices on prod, plus index templates / aliases / ILM
#      policies / search templates (schema mirror).
#   3. For each index, scroll docs from prod and bulk-index into DR ES.
#   4. Trigger a snapshot on DR ES into the local fs repo "dr_repo".
#   5. Tear down the tunnel.
#
# Required env:
#   PROD_SSH_USER PROD_SSH_HOST PROD_ES_NS ES_REMOTE_USER
#   DR_ES_URL                  e.g. https://elasticsearch-es-http.elastic-system.svc:9200
#   DR_ES_USER                 typically "elastic"
#
# Required secret-mounted files:
#   /secrets/prod/es-elastic-password   prod elastic-user password
#   /secrets/dr/es-elastic-password     DR elastic-user password
#
set -uo pipefail

PROD_ES_LOCAL="https://localhost:19200"
DR_ES_URL="${DR_ES_URL:-https://elasticsearch-es-http.elastic-system.svc:9200}"
DR_ES_USER="${DR_ES_USER:-elastic}"
PROD_PASS="$(cat /secrets/prod/es-elastic-password)"
DR_PASS="$(cat /secrets/dr/es-elastic-password)"
PROD_SVC="${PROD_ES_SVC:-svc/elasticsearch-es-http}"
SCROLL_SIZE="${ES_SCROLL_SIZE:-1000}"
SCROLL_KEEPALIVE="${ES_SCROLL_KEEPALIVE:-5m}"
SNAPSHOT_REPO="${ES_SNAPSHOT_REPO:-dr_repo}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

log() { echo "[es] $*"; }

# Curl helpers (-k accepts the eck self-signed cert chain on both sides).
prod_curl() { curl -sk -u "${ES_REMOTE_USER}:${PROD_PASS}" -H 'Content-Type: application/json' "$@"; }
dr_curl()   { curl -sk -u "${DR_ES_USER}:${DR_PASS}"      -H 'Content-Type: application/json' "$@"; }

# 1. Open SSH tunnel: cron-pod:19200 → mac:9200 → (via kubectl pf) prod ES.
#    The remote command keeps the SSH session alive while kubectl pf is running.
log "Opening SSH tunnel to prod ES"
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
    -L 19200:localhost:9200 \
    "${PROD_SSH_USER}@${PROD_SSH_HOST}" \
    "kubectl port-forward -n '$PROD_ES_NS' $PROD_SVC 9200:9200" &
TUNNEL_PID=$!
trap 'kill $TUNNEL_PID 2>/dev/null || true' EXIT

# Wait for tunnel readiness (retry up to 30s).
for i in $(seq 1 30); do
  if prod_curl -o /dev/null -w '%{http_code}' "$PROD_ES_LOCAL" 2>/dev/null | grep -q '^200$'; then
    log "Tunnel ready after ${i}s"
    break
  fi
  sleep 1
  if [[ $i -eq 30 ]]; then
    log "FAILED: tunnel did not become ready"
    exit 1
  fi
done

# 2. Mirror schema: ILM policies, index templates, search templates, then aliases.
log "Mirroring ILM policies"
for pol in quaks_policy quaks_ephemeral_policy; do
  body=$(prod_curl "$PROD_ES_LOCAL/_ilm/policy/$pol" | jq -c ".\"$pol\"")
  if [[ -n "$body" && "$body" != "null" ]]; then
    dr_curl -X PUT "$DR_ES_URL/_ilm/policy/$pol" -d "$body" >/dev/null
  fi
done

log "Mirroring composable index templates"
prod_curl "$PROD_ES_LOCAL/_index_template/quaks_*" \
  | jq -c '.index_templates[]' \
  | while read -r entry; do
      name=$(echo "$entry" | jq -r '.name')
      body=$(echo "$entry" | jq -c '.index_template')
      dr_curl -X PUT "$DR_ES_URL/_index_template/$name" -d "$body" >/dev/null
    done

log "Mirroring stored scripts (search templates)"
prod_curl "$PROD_ES_LOCAL/_cluster/state/metadata?filter_path=metadata.stored_scripts" \
  | jq -c '.metadata.stored_scripts // {} | to_entries[]' \
  | while read -r entry; do
      name=$(echo "$entry" | jq -r '.key')
      [[ "$name" != get_* ]] && continue
      body=$(echo "$entry" | jq -c '{script: .value}')
      dr_curl -X PUT "$DR_ES_URL/_scripts/$name" -d "$body" >/dev/null
    done

# 3. Sync data per index.
log "Listing prod quaks_* indices"
mapfile -t indices < <(prod_curl "$PROD_ES_LOCAL/_cat/indices/quaks_*?h=index" | sort -u)

if [[ ${#indices[@]} -eq 0 ]]; then
  log "No quaks_* indices found on prod"
fi

# Emit NDJSON bulk-index pairs (action line, source line) from a search response.
to_bulk() {
  jq -c '
    .hits.hits[]
    | (
        {"index": {"_index": ._index, "_id": ._id}},
        ._source
      )
  ' "$1"
}

for idx in "${indices[@]}"; do
  [[ -z "$idx" ]] && continue
  log "Syncing index $idx"

  # Drop+recreate the DR index so settings/mappings/aliases stay aligned.
  meta=$(prod_curl "$PROD_ES_LOCAL/$idx" | jq -c ".[\"$idx\"]")
  create_body=$(echo "$meta" | jq -c '{
      settings: (.settings.index | del(.creation_date,.uuid,.version,.provided_name)),
      mappings: .mappings,
      aliases:  .aliases
  }')
  dr_curl -X DELETE "$DR_ES_URL/$idx" >/dev/null
  dr_curl -X PUT    "$DR_ES_URL/$idx" -d "$create_body" >/dev/null

  # Scroll + bulk-index in chunks.
  prod_curl -X POST "$PROD_ES_LOCAL/$idx/_search?scroll=$SCROLL_KEEPALIVE" \
            -d "{\"size\":$SCROLL_SIZE,\"sort\":[\"_doc\"]}" > /tmp/page.json
  scroll_id=$(jq -r '._scroll_id' /tmp/page.json)
  count=0

  while :; do
    n=$(jq '.hits.hits | length' /tmp/page.json)
    [[ "$n" -eq 0 ]] && break
    to_bulk /tmp/page.json > /tmp/bulk.ndjson
    count=$((count + n))
    dr_curl -X POST "$DR_ES_URL/_bulk" -H 'Content-Type: application/x-ndjson' \
            --data-binary "@/tmp/bulk.ndjson" >/dev/null
    prod_curl -X POST "$PROD_ES_LOCAL/_search/scroll" \
              -d "{\"scroll\":\"$SCROLL_KEEPALIVE\",\"scroll_id\":\"$scroll_id\"}" > /tmp/page.json
    scroll_id=$(jq -r '._scroll_id' /tmp/page.json)
  done

  prod_curl -X DELETE "$PROD_ES_LOCAL/_search/scroll" -d "{\"scroll_id\":\"$scroll_id\"}" >/dev/null
  log "  $idx: $count docs"
done

# 4. Ensure the local snapshot repo exists, then snapshot for PITR.
dr_curl -X PUT "$DR_ES_URL/_snapshot/$SNAPSHOT_REPO" -d '{
  "type": "fs",
  "settings": { "location": "/usr/share/elasticsearch/snapshots" }
}' >/dev/null

log "Triggering DR snapshot"
snap_name="quaks-$TS"
dr_curl -X PUT "$DR_ES_URL/_snapshot/$SNAPSHOT_REPO/$snap_name?wait_for_completion=true" \
  -d "{\"indices\":\"quaks_*\",\"include_global_state\":true}" >/dev/null
log "  snapshot: $snap_name"

# Snapshot retention: keep 24 hourly + 7 daily snapshots (matches vault).
all_snaps=$(dr_curl "$DR_ES_URL/_snapshot/$SNAPSHOT_REPO/_all" | jq -r '.snapshots[].snapshot' | sort -r)
declare -A keep_snap
i=0
for s in $all_snaps; do
  ((i < 24)) && keep_snap[$s]=1
  ((i++))
done
declare -A by_day_snap
for s in $all_snaps; do
  day="${s:6:8}"
  [[ -z "${by_day_snap[$day]:-}" ]] && by_day_snap[$day]=$s
done
i=0
for d in $(printf '%s\n' "${!by_day_snap[@]}" | sort -r); do
  keep_snap[${by_day_snap[$d]}]=1
  ((i++))
  [[ $i -ge 7 ]] && break
done
for s in $all_snaps; do
  if [[ -z "${keep_snap[$s]:-}" ]]; then
    dr_curl -X DELETE "$DR_ES_URL/_snapshot/$SNAPSHOT_REPO/$s" >/dev/null
  fi
done

# 5. Tunnel teardown is handled by the EXIT trap.
log "OK"
exit 0
