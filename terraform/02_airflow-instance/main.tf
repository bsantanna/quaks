
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

resource "kubernetes_namespace_v1" "airflow" {
  metadata {
    name = var.airflow_namespace
  }
}


resource "helm_release" "pg_quaks-dags" {
  name       = "pg-quaks-dags"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cluster"
  namespace  = var.airflow_namespace

  values = [
    yamlencode({
      cluster = {
        instances = 1
        imageName = var.pg_image
        storage = {
          size = "5Gi"
        }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.airflow
  ]

}

resource "time_sleep" "wait_for_pg_dags_secret" {
  create_duration = "15s"

  depends_on = [
    helm_release.pg_quaks-dags
  ]
}

data "kubernetes_secret_v1" "pg_quaks-dags-secret" {
  metadata {
    name      = "${helm_release.pg_quaks-dags.name}-cluster-app"
    namespace = var.airflow_namespace
  }

  depends_on = [time_sleep.wait_for_pg_dags_secret]
}

resource "helm_release" "redis_quaks_dags" {
  name       = "redis-quaks-dags"
  repository = "https://ot-container-kit.github.io/helm-charts/"
  chart      = "redis"
  namespace  = var.airflow_namespace

  set = [{
    name  = "featureGates.GenerateConfigInInitContainer"
    value = "true"
  }]

  depends_on = [
    kubernetes_namespace_v1.airflow
  ]

}

resource "time_sleep" "wait_for_redis_dags" {
  create_duration = "15s"

  depends_on = [
    helm_release.redis_quaks_dags
  ]
}


data "kubernetes_secret_v1" "quaks_elastic_api_secret" {
  metadata {
    name      = "quaks-elastic-api-secret"
    namespace = "quaks"
  }
}

resource "kubernetes_secret_v1" "quaks_dags_secrets" {
  metadata {
    name      = "quaks-dags-secrets"
    namespace = var.airflow_namespace
  }

  data = {
    ELASTICSEARCH_URL              = var.es_url
    ELASTICSEARCH_API_KEY          = data.kubernetes_secret_v1.quaks_elastic_api_secret.data["api-key"]
    "APCA-API-KEY-ID"              = var.alpaca_api_key_id
    "APCA-API-SECRET-KEY"          = var.alpaca_api_secret_key
    FINNHUB_API_KEY                = var.finnhub_api_key
    QUAKS_API_URL                  = "https://${var.quaks_fqdn}"
    QUAKS_SERVICE_ACCOUNT_USERNAME = var.auth_service_account_username
    QUAKS_SERVICE_ACCOUNT_SECRET   = var.auth_service_account_secret
    QUAKS_INTEGRATION_TYPE         = var.quaks_integration_type
    QUAKS_INTEGRATION_API_KEY      = var.quaks_integration_api_key
    KEYCLOAK_ADMIN_URL             = var.auth_url
    KEYCLOAK_ADMIN_USERNAME        = var.auth_admin_username
    KEYCLOAK_ADMIN_PASSWORD        = var.auth_admin_secret
    KEYCLOAK_REALM                 = var.keycloak_realm
    X_CONSUMER_KEY                 = var.x_consumer_key
    X_CONSUMER_SECRET              = var.x_consumer_secret
    X_ACCESS_TOKEN                 = var.x_access_token
    X_ACCESS_TOKEN_SECRET          = var.x_access_token_secret
    QUAKS_ARTICLE_URL_PATTERN      = "https://${var.quaks_fqdn}/insights/news/item"
  }

  type = "Opaque"

  depends_on = [
    kubernetes_namespace_v1.airflow
  ]
}

resource "helm_release" "airflow" {
  name       = "quaks-airflow"
  repository = "https://airflow.apache.org"
  chart      = "airflow"
  namespace  = var.airflow_namespace

  depends_on = [
    data.kubernetes_secret_v1.pg_quaks-dags-secret,
    time_sleep.wait_for_redis_dags
  ]

  values = [
    yamlencode({
      executor = "CeleryExecutor"

      defaultAirflowRepository = "bsantanna/quaks-dags"
      defaultAirflowTag        = "v${var.quaks_dags_image_tag}"

      createUserJob = {
        useHelmHooks = false
      }

      migrateDatabaseJob = {
        useHelmHooks = false
      }

      webserver = {
        defaultUser = {
          enabled   = true
          role      = "Admin"
          username  = var.airflow_admin_username
          password  = var.airflow_admin_password
          email     = var.airflow_admin_email
          firstName = "admin"
          lastName  = "user"
        }
      }

      postgresql = {
        enabled = false
      }

      data = {
        metadataConnection = {
          user     = data.kubernetes_secret_v1.pg_quaks-dags-secret.data["username"]
          pass     = data.kubernetes_secret_v1.pg_quaks-dags-secret.data["password"]
          protocol = "postgresql"
          host     = "${helm_release.pg_quaks-dags.name}-cluster-rw.${var.airflow_namespace}.svc.cluster.local"
          port     = 5432
          db       = "app"
        }
        brokerUrl = "redis://redis-quaks-dags.${var.airflow_namespace}.svc.cluster.local:6379/0"
      }

      redis = {
        enabled = false
      }

      ingress = {
        apiServer = {
          enabled          = true
          ingressClassName = "traefik"
          hosts = [{
            name = var.airflow_fqdn
            tls = {
              enabled    = true
              secretName = "quaks-dags-tls"
            }
          }]
          annotations = {
            "cert-manager.io/cluster-issuer" = "letsencrypt-prod"
          }
        }
      }
    })
  ]
}
