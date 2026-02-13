variable "quaks_namespace" {
  description = "Kubernetes namespace for Quaks deployment"
  type        = string
  default     = "quaks"
}

variable "agent_lab_chart_version" {
  description = "Helm chart version for Quaks"
  type        = string
  default     = "1.3.13"
}

variable "quaks_image_tag" {
  description = "Docker image tag for Quaks application"
  type        = string
  default     = "v1.3.12"
}

variable "quaks_image_repository" {
  description = "Docker image repository for Quaks application"
  type        = string
  default     = "bsantanna/quaks-app"
}

variable "quaks_fqdn" {
  description = "Fully qualified domain name for Quaks ingress"
  type        = string
}

variable "telemetry_endpoint" {
  description = "OpenTelemetry collector endpoint URL"
  type        = string
  default     = "http://otel-collector-opentelemetry-collector.otel.svc.cluster.local:4318"
}
