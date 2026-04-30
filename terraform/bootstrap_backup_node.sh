#!/usr/bin/env bash
#
# One-shot bootstrap of a fresh Ubuntu host into the Quaks DR backup node.
# Idempotent — safe to re-run.
#
# Steps:
#   1. Install k3s (single-node Kubernetes), kubectl, helm, terraform.
#   2. Pull the production credentials over SSH from the Mac (kubectl get secret).
#   3. Write a partial tfvars file with the values terraform/07_disaster-recovery needs.
#   4. terraform init && terraform apply for module 07.
#   5. Trigger one immediate cron run to verify the pipeline works end-to-end.
#
# Usage:
#   sudo PROD_SSH_USER=bsantanna PROD_SSH_HOST=mac.local TFVARS_FILE=/path/to/dr.tfvars \
#        ./bootstrap_backup_node.sh
#
# Required env:
#   PROD_SSH_USER          SSH user on the Mac (kubeconfig owner)
#   PROD_SSH_HOST          Hostname/IP of the Mac
#   TFVARS_FILE            Where to write the generated tfvars (will be filled in)
#   PROD_VAULT_UNSEAL_KEY  Production Vault unseal key (file backend, must be supplied manually)
#   PROD_VAULT_ROOT_TOKEN  Production Vault root token (must be supplied manually)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$SCRIPT_DIR/07_disaster-recovery"

: "${PROD_SSH_USER:?must be set}"
: "${PROD_SSH_HOST:?must be set}"
: "${TFVARS_FILE:?must be set (path to dr tfvars file)}"
: "${PROD_VAULT_UNSEAL_KEY:?must be set}"
: "${PROD_VAULT_ROOT_TOKEN:?must be set}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()     { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()     { echo -e "${RED}[ERROR]${NC} $*"; }
section() { echo -e "\n${CYAN}=== $* ===${NC}"; }

if [[ "$(id -u)" -ne 0 ]]; then
  err "This script must be run as root (or via sudo)."
  exit 1
fi

# Resolve the unprivileged user that should own kubeconfig + tfvars.
TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"

ssh_prod() {
  sudo -u "$TARGET_USER" \
    ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
        "${PROD_SSH_USER}@${PROD_SSH_HOST}" "$@"
}

# ── 1. Install dependencies ────────────────────────────────────────────────

section "Installing dependencies"

if ! command -v k3s &>/dev/null; then
  log "Installing k3s"
  curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--write-kubeconfig-mode=644" sh -
else
  log "k3s already installed"
fi

# Make k3s kubeconfig usable by the unprivileged user.
mkdir -p "$TARGET_HOME/.kube"
cp /etc/rancher/k3s/k3s.yaml "$TARGET_HOME/.kube/config"
chown -R "$TARGET_USER":"$TARGET_USER" "$TARGET_HOME/.kube"
chmod 600 "$TARGET_HOME/.kube/config"
export KUBECONFIG="$TARGET_HOME/.kube/config"

if ! command -v helm &>/dev/null; then
  log "Installing helm"
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

if ! command -v terraform &>/dev/null; then
  log "Installing terraform"
  apt-get update -y
  apt-get install -y --no-install-recommends gnupg software-properties-common curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /etc/apt/keyrings/hashicorp.gpg
  echo "deb [signed-by=/etc/apt/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/hashicorp.list
  apt-get update -y
  apt-get install -y --no-install-recommends terraform jq
fi

# ── 2. Generate / locate the SSH key authorized on prod ───────────────────

section "Verifying SSH access to production"

SSH_KEY="$TARGET_HOME/.ssh/id_rsa"
if [[ ! -f "$SSH_KEY" ]]; then
  err "Expected SSH key at $SSH_KEY (already authorized on $PROD_SSH_HOST per requirements)."
  exit 1
fi

if ! ssh_prod true; then
  err "SSH to ${PROD_SSH_USER}@${PROD_SSH_HOST} failed."
  exit 1
fi
log "SSH OK"

# ── 3. Pull production credentials ────────────────────────────────────────

section "Fetching production credentials"

get_pg_pw() {
  local ns="$1" cluster="$2"
  ssh_prod "kubectl get secret ${cluster}-app -n $ns -o jsonpath='{.data.password}' | base64 -d"
}

PROD_PG_QUAKS_APP_PASSWORD=$(get_pg_pw quaks    pg-quaks-app-cluster)
PROD_PG_QUAKS_VECTORS_PASSWORD=$(get_pg_pw quaks    pg-quaks-vectors-cluster)
PROD_PG_QUAKS_CHECKPOINTS_PASSWORD=$(get_pg_pw quaks pg-quaks-checkpoints-cluster)
PROD_PG_KEYCLOAK_PASSWORD=$(get_pg_pw keycloak pg-keycloak-cluster)
PROD_ES_ELASTIC_PASSWORD=$(ssh_prod "kubectl get secret elasticsearch-es-elastic-user -n elastic -o jsonpath='{.data.elastic}' | base64 -d")

log "All credentials fetched"

# ── 4. Write tfvars ───────────────────────────────────────────────────────

section "Writing tfvars to $TFVARS_FILE"

PROD_SSH_PRIVATE_KEY="$(cat "$SSH_KEY")"

cat > "$TFVARS_FILE" <<EOF
prod_ssh_user                       = "${PROD_SSH_USER}"
prod_ssh_host                       = "${PROD_SSH_HOST}"
prod_ssh_private_key                = <<KEY
${PROD_SSH_PRIVATE_KEY}
KEY

prod_pg_quaks_app_password         = "${PROD_PG_QUAKS_APP_PASSWORD}"
prod_pg_quaks_vectors_password     = "${PROD_PG_QUAKS_VECTORS_PASSWORD}"
prod_pg_quaks_checkpoints_password = "${PROD_PG_QUAKS_CHECKPOINTS_PASSWORD}"
prod_pg_keycloak_password          = "${PROD_PG_KEYCLOAK_PASSWORD}"

prod_es_elastic_password           = "${PROD_ES_ELASTIC_PASSWORD}"

prod_vault_unseal_key              = "${PROD_VAULT_UNSEAL_KEY}"
prod_vault_root_token              = "${PROD_VAULT_ROOT_TOKEN}"
EOF
chown "$TARGET_USER":"$TARGET_USER" "$TFVARS_FILE"
chmod 600 "$TFVARS_FILE"

log "tfvars written ($(wc -l < "$TFVARS_FILE") lines)"

# ── 5. Terraform init + apply ─────────────────────────────────────────────

section "Running terraform init && apply"

sudo -u "$TARGET_USER" -E bash -c "
  cd '$MODULE_DIR'
  terraform init -input=false
  terraform apply -input=false -auto-approve -var-file='$TFVARS_FILE'
"

# ── 6. Trigger one immediate run ──────────────────────────────────────────

section "Triggering an immediate DR run for verification"

sudo -u "$TARGET_USER" -E kubectl create job --from=cronjob/dr-backup \
  -n dr-cron "dr-backup-bootstrap-$(date +%s)" || warn "Bootstrap job creation failed (non-fatal)"

log "Bootstrap complete. Tail logs with:"
log "  kubectl -n dr-cron logs -f -l job-name=dr-backup-bootstrap-..."
log "Cron schedule: hourly at :00. Verify status: kubectl -n dr-cron get cronjob dr-backup"
