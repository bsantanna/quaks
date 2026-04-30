# Disaster Recovery (Module 07)

Hourly pull-based replication from the production Quaks cluster (Mac, Docker
Desktop K8s) to a separate Linux box running k3s. The production cluster is
not modified — all replication is initiated from the DR side over SSH.

## Topology

```
   Production (Mac)                   DR (Linux, k3s)
   ───────────────                   ─────────────────
   pg-quaks-app          ──┐
   pg-quaks-vectors        │  SSH +
   pg-quaks-checkpoints    │  kubectl exec  ─►  pg-quaks-* (CNPG)
   pg-keycloak             │  pg_dump | pg_restore
                           │
   Vault (file backend)  ──┤  SSH + kubectl exec
                           │  tar /vault/data ─►  /var/lib/dr/vault/*.tar.gz
                           │                       (24 hourly + 7 daily)
   Elasticsearch         ──┘  SSH port-forward + scroll/bulk
                              quaks_*  ─►  ES (DR) ─► snapshot repo
```

Cron lives **inside the DR cluster** as a `CronJob` (namespace `dr-cron`),
running hourly at `:00`.

## What gets mirrored

| Source                           | Mode                       | Restore artifact                 |
|----------------------------------|----------------------------|----------------------------------|
| `pg-quaks-app-cluster`           | hot replica (drop+restore) | live DR cluster + rollback dump  |
| `pg-quaks-vectors-cluster`       | hot replica                | live DR cluster + rollback dump  |
| `pg-quaks-checkpoints-cluster`   | hot replica                | live DR cluster + rollback dump  |
| `pg-keycloak-cluster`            | hot replica                | live DR cluster + rollback dump  |
| Vault (`/vault/data` tarball)    | point-in-time backup       | `vault-<ts>.tar.gz` (retained)   |
| Elasticsearch `quaks_*` indices  | hot replica + snapshot     | live DR ES + `dr_repo` snapshots |
| ES schema (templates, ILM, scripts, aliases) | mirrored        | live DR ES                       |

## Bootstrap

On a fresh Ubuntu host with SSH already authorized to the Mac:

```bash
sudo PROD_SSH_USER=bsantanna \
     PROD_SSH_HOST=<mac.local-or-ip> \
     PROD_VAULT_UNSEAL_KEY=<key>     \
     PROD_VAULT_ROOT_TOKEN=<token>   \
     TFVARS_FILE=/root/dr.tfvars     \
     ./bootstrap_backup_node.sh
```

The bootstrap script:
1. Installs k3s, helm, terraform, jq.
2. Pulls production CNPG and ECK secrets via SSH.
3. Generates `dr.tfvars`.
4. `terraform init && apply` for module 07.
5. Triggers one immediate cron run for verification.

The Vault unseal key and root token are **not stored on production** — supply
them as environment variables when running bootstrap.

## Operations

```bash
# Status
kubectl -n dr-cron get cronjob dr-backup
kubectl -n dr-cron get jobs

# Tail the latest run
kubectl -n dr-cron logs -l job-name=$(kubectl -n dr-cron get jobs -o jsonpath='{.items[-1:].metadata.name}')

# Trigger a manual run
kubectl -n dr-cron create job --from=cronjob/dr-backup dr-backup-manual-$(date +%s)

# Inspect persistent logs (last 168 runs ≈ 7 days)
kubectl -n dr-cron exec deploy/...  # there's no deploy; use a shell pod against the PVC if needed
```

Logs are written to `/var/lib/dr/logs/run-<ts>.log` on the `dr-backup` PVC.

## Manual restore procedures

### Postgres (already live)

The DR clusters are continuously refreshed; just point your apps at them.
If a cron run corrupts a DR DB, replay the rollback dump from the previous
cycle:

```bash
kubectl exec -n quaks pg-quaks-app-cluster-1 -c postgres -- \
  pg_restore --clean --if-exists --no-owner -U postgres -d app \
    < /var/lib/dr/rollback/pg-quaks-app-cluster.prev.dump
```

### Vault

DR Vault runs uninitialized; bring it up by extracting a tarball into its PVC:

```bash
# Stop DR Vault
kubectl scale -n vault statefulset/vault --replicas=0

# Mount the data PVC into a helper pod and untar
kubectl -n vault run dr-restore --rm -it --restart=Never \
  --image=debian:bookworm-slim \
  --overrides='{"spec":{"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"data-vault-0"}},{"name":"backup","persistentVolumeClaim":{"claimName":"dr-backup"}}],"containers":[{"name":"dr-restore","image":"debian:bookworm-slim","command":["bash","-c","tar xzf /backup/vault/$(ls -1t /backup/vault/vault-*.tar.gz | head -1) -C /vault/"],"volumeMounts":[{"name":"data","mountPath":"/vault/data"},{"name":"backup","mountPath":"/backup"}]}]}}'

# Start DR Vault and unseal with the production key
kubectl scale -n vault statefulset/vault --replicas=1
kubectl -n vault wait --for=condition=Ready pod/vault-0 --timeout=120s
kubectl -n vault exec vault-0 -- vault operator unseal "$PROD_VAULT_UNSEAL_KEY"
```

### Elasticsearch

DR ES is already live with the most recent hour of data. For point-in-time
recovery:

```bash
# List snapshots
curl -sk -u "elastic:$DR_ES_PW" \
  https://elasticsearch-es-http.elastic-system.svc:9200/_snapshot/dr_repo/_all

# Restore a specific snapshot (closes target indices first)
curl -sk -u "elastic:$DR_ES_PW" -X POST \
  "https://elasticsearch-es-http.elastic-system.svc:9200/_snapshot/dr_repo/quaks-<ts>/_restore" \
  -H 'Content-Type: application/json' \
  -d '{"indices":"quaks_*","rename_pattern":"quaks_(.+)","rename_replacement":"quaks_$1_restored"}'
```

## Verification

`scripts/verify.sh` runs at the end of every cron cycle and asserts:

- DR row counts ≥ 95% of prod for each Postgres cluster.
- DR doc counts ≥ 95% of prod for `quaks_*` indices.
- Latest vault tarball is < 2 hours old.

Failures are logged and the cron job exits non-zero (visible in
`kubectl -n dr-cron get jobs`), but data is *not* rolled back — the
intention is to surface the issue, not to mask drift.

## Limitations

- **Vault file backend is not crash-consistent.** Hot tar of a running
  Vault has a small inconsistency window. For our usage (low-write KV
  storage), worst case is losing the last few writes.
- **No PITR for Postgres.** We rebuild the DR DB from a logical dump each
  hour; restore granularity is one hour. WAL-shipping (pgBackRest) would
  give finer recovery but requires production-side config.
- **No alerting.** Failures only surface in `kubectl get jobs` / `kubectl logs`.
  Wire to Slack/email externally if needed.
- **DR cluster is single-node.** k3s on one host has no HA — this is a
  *recovery* target, not a high-availability replica.
