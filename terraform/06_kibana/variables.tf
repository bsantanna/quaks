variable "es_url" {
  description = "The endpoint URL for the Elasticsearch cluster"
  type        = string
}

variable "kb_url" {
  description = "The endpoint URL for the Kibana UI"
  type        = string
}

variable "kb_anonymous_username" {
  description = "The username for the anonymous access in Kibana"
  type        = string
  sensitive   = true
}

variable "kb_anonymous_password" {
  description = "The password for the anonymous access in Kibana"
  type        = string
  sensitive   = true
}

variable "quaks_namespace" {
  description = "Kubernetes namespace for Kibana deployment"
  type        = string
  default     = "quaks"
}

variable "es_namespace" {
  description = "Kubernetes namespace where Elasticsearch is deployed"
  type        = string
  default     = "elastic"
}

variable "es_cluster_name" {
  description = "Name of the ECK Elasticsearch cluster resource"
  type        = string
  default     = "elasticsearch"
}

variable "kb_version" {
  description = "Kibana version to deploy"
  type        = string
  default     = "9.3.1"
}

variable "quaks_fqdn" {
  description = "Fully qualified domain name for Quaks ingress (shared with Kibana)"
  type        = string
  default     = "quaks.ai"
}
