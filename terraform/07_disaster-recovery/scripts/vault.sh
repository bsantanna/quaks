#!/usr/bin/env bash
#
# Backup HashiCorp Vault (file backend) from production. The vault data dir is
# tarred from inside the prod vault pod over SSH+kubectl exec and saved as a
# timestamped artifact on the DR backup volume with retention.
#
# Restore is a manual procedure — see README.md.
#
# Required env: PROD_SSH_USER PROD_SSH_HOST PROD_VAULT_NS
#
set -uo pipefail

VAULT_POD="${VAULT_POD:-vault-0}"
BACKUP_DIR="${BACKUP_DIR:-/var/lib/dr/vault}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
ARTIFACT="$BACKUP_DIR/vault-$TS.tar.gz"

mkdir -p "$BACKUP_DIR"

log() { echo "[vault] $*"; }

ssh_prod() {
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
      "${PROD_SSH_USER}@${PROD_SSH_HOST}" "$@"
}

log "Streaming /vault/data from prod $PROD_VAULT_NS/$VAULT_POD → $ARTIFACT"
set -o pipefail
ssh_prod "kubectl exec -n '$PROD_VAULT_NS' '$VAULT_POD' -- tar czf - -C /vault data" \
  > "$ARTIFACT"
rc=$?

if [[ $rc -ne 0 || ! -s "$ARTIFACT" ]]; then
  log "FAILED (rc=$rc, size=$(stat -c%s "$ARTIFACT" 2>/dev/null || echo 0))"
  rm -f "$ARTIFACT"
  exit 1
fi

# Retention: 24 hourly (last 24 unique hours) + 7 daily (one per day for 7 days).
# Implementation: keep the most recent 24 hourly artifacts, plus the most recent
# artifact for each of the previous 7 days.
log "Applying retention policy (24 hourly + 7 daily)"

cd "$BACKUP_DIR"
mapfile -t all < <(ls -1t vault-*.tar.gz 2>/dev/null)

declare -A keep
# Keep the 24 most recent (hourly).
for f in "${all[@]:0:24}"; do keep[$f]=1; done
# Keep one per day for the last 7 days.
declare -A by_day
for f in "${all[@]}"; do
  day="${f:6:8}"  # vault-YYYYMMDD...
  [[ -z "${by_day[$day]:-}" ]] && by_day[$day]=$f
done
i=0
for d in $(printf '%s\n' "${!by_day[@]}" | sort -r); do
  keep[${by_day[$d]}]=1
  ((i++))
  [[ $i -ge 7 ]] && break
done

removed=0
for f in "${all[@]}"; do
  if [[ -z "${keep[$f]:-}" ]]; then
    rm -f "$f"
    ((removed++))
  fi
done
log "Retention removed $removed old artifact(s); kept ${#keep[@]}"

log "OK ($(du -h "$ARTIFACT" | cut -f1))"
exit 0
