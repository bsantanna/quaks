terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = ">= 3.0.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.9.0"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

provider "helm" {
  kubernetes = {
    config_path = "~/.kube/config"
  }
}

# ── Namespaces ─────────────────────────────────────────────────────────────

resource "kubernetes_namespace_v1" "dr_quaks" {
  metadata { name = var.dr_namespace }
}

resource "kubernetes_namespace_v1" "dr_keycloak" {
  metadata { name = var.dr_keycloak_namespace }
}

resource "kubernetes_namespace_v1" "dr_vault" {
  metadata { name = var.dr_vault_namespace }
}

resource "kubernetes_namespace_v1" "dr_es" {
  metadata { name = var.dr_es_namespace }
}

resource "kubernetes_namespace_v1" "dr_cron" {
  metadata { name = var.dr_cron_namespace }
}

# ── Operators ─────────────────────────────────────────────────────────────

resource "helm_release" "cnpg_operator" {
  name             = "cnpg"
  repository       = "https://cloudnative-pg.github.io/charts"
  chart            = "cloudnative-pg"
  version          = var.cnpg_chart_version
  namespace        = "cnpg-system"
  create_namespace = true
}

resource "helm_release" "eck_operator" {
  name       = "elastic-operator"
  repository = "https://helm.elastic.co"
  chart      = "eck-operator"
  version    = var.eck_chart_version
  namespace  = var.dr_es_namespace

  depends_on = [kubernetes_namespace_v1.dr_es]
}

resource "time_sleep" "wait_for_operators" {
  create_duration = "30s"

  depends_on = [
    helm_release.cnpg_operator,
    helm_release.eck_operator,
  ]
}

# ── PG replicas (CNPG cluster CRs, deployed via the cluster chart so the
#    spec mirrors terraform/02 and terraform/04) ─────────────────────────────

resource "helm_release" "pg_quaks_app" {
  name       = "pg-quaks-app"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = var.dr_namespace

  values = [
    yamlencode({
      cluster = {
        instances = 1
        imageName = var.pg_image
        storage   = { size = "5Gi" }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.dr_quaks,
    time_sleep.wait_for_operators,
  ]
}

resource "helm_release" "pg_quaks_vectors" {
  name       = "pg-quaks-vectors"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = var.dr_namespace

  values = [
    yamlencode({
      cluster = {
        instances = 1
        imageName = var.pg_image
        storage   = { size = "5Gi" }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.dr_quaks,
    time_sleep.wait_for_operators,
  ]
}

resource "helm_release" "pg_quaks_checkpoints" {
  name       = "pg-quaks-checkpoints"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = var.dr_namespace

  values = [
    yamlencode({
      cluster = {
        instances = 1
        imageName = var.pg_image
        storage   = { size = "5Gi" }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.dr_quaks,
    time_sleep.wait_for_operators,
  ]
}

resource "helm_release" "pg_keycloak" {
  name       = "pg-keycloak"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = var.dr_keycloak_namespace

  values = [
    yamlencode({
      cluster = {
        instances = 1
        imageName = var.pg_image
        storage   = { size = "1Gi" }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.dr_keycloak,
    time_sleep.wait_for_operators,
  ]
}

# ── Elasticsearch (data-only, single node, snapshot repo enabled) ──────────

resource "kubernetes_persistent_volume_claim_v1" "es_snapshots" {
  metadata {
    name      = "es-snapshots"
    namespace = var.dr_es_namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = var.snapshots_volume_size
      }
    }
  }
  wait_until_bound = false

  depends_on = [kubernetes_namespace_v1.dr_es]
}

resource "kubernetes_manifest" "elasticsearch" {
  manifest = {
    apiVersion = "elasticsearch.k8s.elastic.co/v1"
    kind       = "Elasticsearch"
    metadata = {
      name      = "elasticsearch"
      namespace = var.dr_es_namespace
    }
    spec = {
      version = var.es_version
      nodeSets = [
        {
          name  = "default"
          count = 1
          config = {
            "node.store.allow_mmap"    = false
            "path.repo"                = ["/usr/share/elasticsearch/snapshots"]
            "reindex.remote.whitelist" = ["localhost:*"]
          }
          podTemplate = {
            spec = {
              containers = [
                {
                  name = "elasticsearch"
                  volumeMounts = [
                    {
                      name      = "snapshots"
                      mountPath = "/usr/share/elasticsearch/snapshots"
                    }
                  ]
                }
              ]
              volumes = [
                {
                  name = "snapshots"
                  persistentVolumeClaim = {
                    claimName = kubernetes_persistent_volume_claim_v1.es_snapshots.metadata[0].name
                  }
                }
              ]
            }
          }
          volumeClaimTemplates = [
            {
              metadata = { name = "elasticsearch-data" }
              spec = {
                accessModes = ["ReadWriteOnce"]
                resources   = { requests = { storage = "5Gi" } }
              }
            }
          ]
        }
      ]
    }
  }

  depends_on = [
    helm_release.eck_operator,
    time_sleep.wait_for_operators,
  ]
}

# ── Vault (file backend, single replica, mirrors prod) ─────────────────────

resource "helm_release" "vault" {
  name       = "vault"
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  version    = var.vault_chart_version
  namespace  = var.dr_vault_namespace

  values = [
    yamlencode({
      server = {
        ha = { enabled = false }
        standalone = { enabled = true, config = <<-EOT
          ui = true
          listener "tcp" {
            tls_disable = 1
            address     = "[::]:8200"
            cluster_address = "[::]:8201"
          }
          storage "file" {
            path = "/vault/data"
          }
          disable_mlock = true
        EOT
        }
        dataStorage = {
          enabled      = true
          size         = "10Gi"
          mountPath    = "/vault/data"
          storageClass = null
        }
      }
      injector = { enabled = false }
    })
  ]

  depends_on = [kubernetes_namespace_v1.dr_vault]
}

# ── DR cron infrastructure ────────────────────────────────────────────────

resource "kubernetes_persistent_volume_claim_v1" "backup" {
  metadata {
    name      = "dr-backup"
    namespace = var.dr_cron_namespace
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = var.backup_volume_size
      }
    }
  }
  wait_until_bound = false

  depends_on = [kubernetes_namespace_v1.dr_cron]
}

resource "kubernetes_secret_v1" "ssh" {
  metadata {
    name      = "dr-ssh"
    namespace = var.dr_cron_namespace
  }
  data = {
    id_rsa = file(var.prod_ssh_private_key_path)
  }
  type = "Opaque"

  depends_on = [kubernetes_namespace_v1.dr_cron]
}

resource "kubernetes_secret_v1" "prod_creds" {
  metadata {
    name      = "dr-prod-creds"
    namespace = var.dr_cron_namespace
  }
  data = {
    "pg-quaks-app-password"         = var.prod_pg_quaks_app_password
    "pg-quaks-vectors-password"     = var.prod_pg_quaks_vectors_password
    "pg-quaks-checkpoints-password" = var.prod_pg_quaks_checkpoints_password
    "pg-keycloak-password"          = var.prod_pg_keycloak_password
    "es-elastic-password"           = var.prod_es_elastic_password
    "vault-unseal-key"              = var.prod_vault_unseal_key
    "vault-root-token"              = var.prod_vault_root_token
  }
  type = "Opaque"

  depends_on = [kubernetes_namespace_v1.dr_cron]
}

# DR-side credentials (fetched at bootstrap from the local ECK secret)
data "kubernetes_secret_v1" "dr_es_elastic_user" {
  metadata {
    name      = "elasticsearch-es-elastic-user"
    namespace = var.dr_es_namespace
  }

  depends_on = [kubernetes_manifest.elasticsearch]
}

resource "kubernetes_secret_v1" "dr_creds" {
  metadata {
    name      = "dr-local-creds"
    namespace = var.dr_cron_namespace
  }
  data = {
    "es-elastic-password" = data.kubernetes_secret_v1.dr_es_elastic_user.data["elastic"]
  }
  type = "Opaque"

  depends_on = [kubernetes_namespace_v1.dr_cron]
}

resource "kubernetes_config_map_v1" "scripts" {
  metadata {
    name      = "dr-scripts"
    namespace = var.dr_cron_namespace
  }
  data = {
    "orchestrator.sh" = file("${path.module}/scripts/orchestrator.sh")
    "pg.sh"           = file("${path.module}/scripts/pg.sh")
    "vault.sh"        = file("${path.module}/scripts/vault.sh")
    "es.sh"           = file("${path.module}/scripts/es.sh")
    "verify.sh"       = file("${path.module}/scripts/verify.sh")
  }

  depends_on = [kubernetes_namespace_v1.dr_cron]
}

resource "kubernetes_service_account_v1" "cron" {
  metadata {
    name      = "dr-cron"
    namespace = var.dr_cron_namespace
  }

  depends_on = [kubernetes_namespace_v1.dr_cron]
}

resource "kubernetes_cluster_role_v1" "cron" {
  metadata { name = "dr-cron" }

  rule {
    api_groups = [""]
    resources  = ["pods", "pods/exec", "services"]
    verbs      = ["get", "list", "create"]
  }
  rule {
    api_groups = [""]
    resources  = ["secrets"]
    verbs      = ["get", "list"]
  }
}

resource "kubernetes_cluster_role_binding_v1" "cron" {
  metadata { name = "dr-cron" }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role_v1.cron.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.cron.metadata[0].name
    namespace = var.dr_cron_namespace
  }
}

resource "kubernetes_cron_job_v1" "backup" {
  metadata {
    name      = "dr-backup"
    namespace = var.dr_cron_namespace
  }

  spec {
    schedule                      = var.cron_schedule
    concurrency_policy            = "Forbid"
    successful_jobs_history_limit = 3
    failed_jobs_history_limit     = 5
    starting_deadline_seconds     = 600

    job_template {
      metadata {}
      spec {
        backoff_limit           = 0
        active_deadline_seconds = 1800

        template {
          metadata {}
          spec {
            service_account_name = kubernetes_service_account_v1.cron.metadata[0].name
            restart_policy       = "Never"

            container {
              name              = "dr"
              image             = "${var.dr_tools_image}:${var.dr_tools_image_tag}"
              image_pull_policy = "IfNotPresent"
              command           = ["/bin/bash", "/scripts/orchestrator.sh"]

              env {
                name  = "PROD_SSH_USER"
                value = var.prod_ssh_user
              }
              env {
                name  = "PROD_SSH_HOST"
                value = var.prod_ssh_host
              }
              env {
                name  = "PROD_NAMESPACE"
                value = var.prod_namespace
              }
              env {
                name  = "PROD_KEYCLOAK_NS"
                value = var.prod_keycloak_namespace
              }
              env {
                name  = "PROD_VAULT_NS"
                value = var.prod_vault_namespace
              }
              env {
                name  = "PROD_ES_NS"
                value = var.prod_es_namespace
              }
              env {
                name  = "DR_NAMESPACE"
                value = var.dr_namespace
              }
              env {
                name  = "DR_ES_URL"
                value = "https://elasticsearch-es-http.${var.dr_es_namespace}.svc:9200"
              }
              env {
                name  = "ES_REMOTE_USER"
                value = "elastic"
              }
              env {
                name  = "DR_ES_USER"
                value = "elastic"
              }
              env {
                name  = "LOG_DIR"
                value = "/var/lib/dr/logs"
              }
              env {
                name  = "BACKUP_DIR"
                value = "/var/lib/dr/vault"
              }
              env {
                name  = "ROLLBACK_DIR"
                value = "/var/lib/dr/rollback"
              }

              volume_mount {
                name       = "scripts"
                mount_path = "/scripts"
              }
              volume_mount {
                name       = "ssh"
                mount_path = "/secrets/ssh"
                read_only  = true
              }
              volume_mount {
                name       = "prod-creds"
                mount_path = "/secrets/prod"
                read_only  = true
              }
              volume_mount {
                name       = "dr-creds"
                mount_path = "/secrets/dr"
                read_only  = true
              }
              volume_mount {
                name       = "backup"
                mount_path = "/var/lib/dr"
              }
            }

            volume {
              name = "scripts"
              config_map {
                name         = kubernetes_config_map_v1.scripts.metadata[0].name
                default_mode = "0755"
              }
            }
            volume {
              name = "ssh"
              secret {
                secret_name  = kubernetes_secret_v1.ssh.metadata[0].name
                default_mode = "0400"
              }
            }
            volume {
              name = "prod-creds"
              secret {
                secret_name = kubernetes_secret_v1.prod_creds.metadata[0].name
              }
            }
            volume {
              name = "dr-creds"
              secret {
                secret_name = kubernetes_secret_v1.dr_creds.metadata[0].name
              }
            }
            volume {
              name = "backup"
              persistent_volume_claim {
                claim_name = kubernetes_persistent_volume_claim_v1.backup.metadata[0].name
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    kubernetes_config_map_v1.scripts,
    kubernetes_secret_v1.ssh,
    kubernetes_secret_v1.prod_creds,
    kubernetes_secret_v1.dr_creds,
  ]
}
