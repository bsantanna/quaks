variable "airflow_namespace" {
  description = "Kubernetes namespace for Airflow deployment"
  type        = string
  default     = "airflow"
}

variable "airflow_fqdn" {
  description = "Fully qualified domain name for Airflow ingress"
  type        = string
}

variable "quaks_dags_image_tag" {
  description = "Docker image tag for quaks-dags"
  type        = string
  default     = "v1.3.14"
}

variable "airflow_admin_username" {
  description = "Username for the Airflow admin user"
  type        = string
  sensitive   = true
}

variable "airflow_admin_password" {
  description = "Password for the Airflow admin user"
  type        = string
  sensitive   = true
}

variable "pg_image" {
  type        = string
  default     = "bsantanna/cloudnative-pg-vector:17.4"
  description = "PostgreSQL image with pgvector (adjust if needed)"
}
