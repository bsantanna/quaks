# reference https://www.elastic.co/blog/how-to-embed-kibana-dashboards#basic-embedding-with-html-iframe

terraform {
  required_providers {
    elasticstack = {
      source  = "elastic/elasticstack"
      version = "~> 0.12"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 3.0.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.0.0"
    }
  }
}

data "kubernetes_secret_v1" "quaks_elastic_api_secret" {
  metadata {
    name      = "quaks-elastic-api-secret"
    namespace = var.quaks_namespace
  }
}

provider "elasticstack" {
  elasticsearch {
    endpoints = [var.es_url]
    api_key   = data.kubernetes_secret_v1.quaks_elastic_api_secret.data["api-key"]
  }

  kibana {
    endpoints = [var.kb_url]
    api_key   = data.kubernetes_secret_v1.quaks_elastic_api_secret.data["api-key"]
  }
}

provider "helm" {
  kubernetes = {
    config_path = "~/.kube/config"
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "helm_release" "kibana" {
  name       = "kibana"
  repository = "https://helm.elastic.co"
  chart      = "eck-kibana"
  namespace  = var.quaks_namespace

  values = [
    yamlencode({
      fullnameOverride = "kibana"

      version = var.kb_version

      elasticsearchRef = {
        name      = var.es_cluster_name
        namespace = var.es_namespace
      }

      config = {

        server = {
          publicBaseUrl   = "https://${var.quaks_fqdn}/dashboards"
          basePath        = "/dashboards"
          rewriteBasePath = true
        }
        xpack = {
          security = {
            # sameSiteCookies = "None"
            authc = {
              providers = {
                basic = {
                  basic1 = {
                    order = 0
                  }
                }
                anonymous = {
                  anonymous1 = {
                    order = 1
                    credentials = {
                      username = var.kb_anonymous_username
                      password = var.kb_anonymous_password
                    }
                  }
                }
              }
            }
          }
          fleet = {
            packages = [{
              name    = "apm"
              version = "latest"
            }]
          }
        }
      }

      http = {
        tls = {
          selfSignedCertificate = {
            disabled = true
          }
        }
      }

      ingress = {
        enabled   = true
        className = "traefik"
        pathType  = "Prefix"
        annotations = {}
        hosts = [{
          host = var.quaks_fqdn
          path = "/dashboards"
        }]
        tls = {
          enabled    = true
          secretName = "quaks-tls"
        }
      }
    })
  ]
}

resource "elasticstack_elasticsearch_security_role" "anonymous_dashboard_role" {
  name = "anonymous_dashboard_role"

  indices {
    names      = ["quaks_*"]
    privileges = ["read", "view_index_metadata"]
  }

  applications {
    application = "kibana-.kibana"
    privileges  = ["feature_dashboard.minimal_read"]
    resources   = ["space:default"]
  }

}

resource "elasticstack_elasticsearch_security_user" "anonymous_user" {
  username    = var.kb_anonymous_username
  password_wo = var.kb_anonymous_password
  roles       = [elasticstack_elasticsearch_security_role.anonymous_dashboard_role.name]

  depends_on = [elasticstack_elasticsearch_security_role.anonymous_dashboard_role]
}

data "local_file" "stocks_eod_data_view_ndjson" {
  filename = "${path.module}/stocks_eod_data_view.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "data_view" {
  file_contents = data.local_file.stocks_eod_data_view_ndjson.content
  space_id      = "default"
  overwrite     = true
}

data "local_file" "stocks_eod_visualizations_ndjson" {
  filename = "${path.module}/stocks_eod_visualizations.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "visualizations" {
  file_contents = data.local_file.stocks_eod_visualizations_ndjson.content
  space_id      = "default"
  overwrite     = true
  depends_on    = [elasticstack_kibana_import_saved_objects.data_view]
}

data "local_file" "stocks_eod_dashboard_ndjson" {
  filename = "${path.module}/stocks_eod_dashboard.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "dashboard" {
  file_contents = data.local_file.stocks_eod_dashboard_ndjson.content
  space_id      = "default"
  overwrite     = true
  depends_on    = [elasticstack_kibana_import_saved_objects.visualizations]
}
