variable "dr_namespace" {
  description = "DR namespace mirroring production 'quaks' (CNPG clusters land here)"
  type        = string
  default     = "quaks"
}

variable "dr_keycloak_namespace" {
  description = "DR namespace mirroring production 'keycloak'"
  type        = string
  default     = "keycloak"
}

variable "dr_vault_namespace" {
  description = "DR namespace for the Vault helm release"
  type        = string
  default     = "vault"
}

variable "dr_es_namespace" {
  description = "DR namespace for the ECK operator and Elasticsearch CR"
  type        = string
  default     = "elastic-system"
}

variable "dr_cron_namespace" {
  description = "DR namespace for the disaster-recovery CronJob and its config"
  type        = string
  default     = "dr-cron"
}

variable "prod_ssh_user" {
  description = "SSH user on the production (Mac) host"
  type        = string
}

variable "prod_ssh_host" {
  description = "SSH host or IP of the production (Mac) host (must be reachable from the Linux DR host)"
  type        = string
}

variable "prod_ssh_private_key" {
  description = "SSH private key (PEM) authorized to log into the production host"
  type        = string
  sensitive   = true
}

variable "prod_namespace" {
  description = "Production namespace hosting the 3 quaks CNPG clusters and Elasticsearch (defaults match terraform/04)"
  type        = string
  default     = "quaks"
}

variable "prod_keycloak_namespace" {
  description = "Production namespace hosting the keycloak CNPG cluster"
  type        = string
  default     = "keycloak"
}

variable "prod_vault_namespace" {
  description = "Production namespace hosting Vault"
  type        = string
  default     = "vault"
}

variable "prod_es_namespace" {
  description = "Production namespace hosting Elasticsearch (ECK)"
  type        = string
  default     = "elastic"
}

variable "prod_pg_quaks_app_password" {
  description = "App-user password of the prod pg-quaks-app cluster (used by verify.sh)"
  type        = string
  sensitive   = true
}

variable "prod_pg_quaks_vectors_password" {
  description = "App-user password of the prod pg-quaks-vectors cluster"
  type        = string
  sensitive   = true
}

variable "prod_pg_quaks_checkpoints_password" {
  description = "App-user password of the prod pg-quaks-checkpoints cluster"
  type        = string
  sensitive   = true
}

variable "prod_pg_keycloak_password" {
  description = "App-user password of the prod pg-keycloak cluster"
  type        = string
  sensitive   = true
}

variable "prod_es_elastic_password" {
  description = "Production Elasticsearch elastic-user password (for verify and snapshot mirror)"
  type        = string
  sensitive   = true
}

variable "prod_vault_unseal_key" {
  description = "Production Vault unseal key (file backend) — needed for manual DR vault unseal"
  type        = string
  sensitive   = true
}

variable "prod_vault_root_token" {
  description = "Production Vault root token — needed for manual DR vault administration"
  type        = string
  sensitive   = true
}

variable "pg_image" {
  description = "PostgreSQL image with pgvector — must match production"
  type        = string
  default     = "bsantanna/cloudnative-pg-vector:17.4"
}

variable "es_version" {
  description = "Elasticsearch version — must match production"
  type        = string
  default     = "9.3.1"
}

variable "vault_chart_version" {
  description = "HashiCorp Vault helm chart version"
  type        = string
  default     = "0.32.0"
}

variable "cnpg_chart_version" {
  description = "CloudNativePG operator helm chart version"
  type        = string
  default     = "0.22.1"
}

variable "eck_chart_version" {
  description = "ECK (Elastic Cloud on Kubernetes) operator helm chart version"
  type        = string
  default     = "3.0.0"
}

variable "dr_tools_image" {
  description = "Image used by the DR cron job"
  type        = string
  default     = "bsantanna/quaks-dr-tools"
}

variable "dr_tools_image_tag" {
  description = "Tag for the DR tools image (matches the project semver release tag)"
  type        = string
  default     = "1.5.26"
}

variable "cron_schedule" {
  description = "Crontab expression for the DR backup job"
  type        = string
  default     = "0 * * * *"
}

variable "backup_volume_size" {
  description = "Size of the PVC backing /var/lib/dr (vault tarballs, rollback dumps, logs)"
  type        = string
  default     = "20Gi"
}

variable "snapshots_volume_size" {
  description = "Size of the PVC backing the DR ES snapshot repo (path.repo)"
  type        = string
  default     = "20Gi"
}
