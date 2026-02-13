
terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = ">= 3.0.0"
    }
  }
}

provider "helm" {
  kubernetes = {
    config_path = "~/.kube/config"
  }
}

resource "helm_release" "quaks" {
  name       = "quaks"
  repository = "https://bsantanna.github.io/agent-lab"
  chart      = "agent-lab"
  version    = var.agent_lab_chart_version
  namespace  = var.quaks_namespace

  values = [
    yamlencode({
      config = {
        telemetry_endpoint = var.telemetry_endpoint
      }

      ingress = {
        enabled   = true
        className = "traefik"
        hosts = [{
          host = var.quaks_fqdn
          paths = [{
            path     = "/"
            pathType = "Prefix"
          }]
        }]
        tls = [{
          hosts      = [var.quaks_fqdn]
          secretName = "quaks-tls"
        }]
        annotations = {
          "cert-manager.io/cluster-issuer" = "letsencrypt-prod"
        }
      }

      livenessProbe = {
        timeoutSeconds = 60
      }

      readinessProbe = {
        timeoutSeconds = 60
      }

      image = {
        repository = var.quaks_image_repository
        tag = var.quaks_image_tag
      }

      secretName = "quaks-secret"
    })
  ]
}
