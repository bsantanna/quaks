variable "quaks_namespace" {
  description = "Kubernetes namespace for Quaks deployment"
  type        = string
  default     = "quaks"
}

variable "auth_url" {
  type        = string
  description = "Auth Host URL"
}

variable "auth_realm" {
  type        = string
  description = "Auth Realm"
  default     = "quaks"
}

variable "auth_admin_username" {
  type        = string
  description = "Auth Admin Username"
  sensitive   = true
}

variable "auth_admin_secret" {
  type        = string
  description = "Auth Admin Secret"
  sensitive   = true
}

variable "auth_service_account_username" {
  type        = string
  description = "Auth Service Account Username"
  default     = "quaks-service-account"
  sensitive   = true
}

variable "auth_service_account_secret" {
  type        = string
  description = "Auth Service Account Secret"
  sensitive   = true
}

variable "auth_client_id" {
  type        = string
  description = "Auth Client ID"
  default     = "quaks-client"
}

variable "auth_client_redirect_uris" {
  type        = list(string)
  description = "Auth Client Redirect URIs"
  default     = ["*"]
}

variable "smtp_host" {
  type        = string
  description = "SMTP server address"
}

variable "smtp_port" {
  type        = number
  description = "SMTP server port"
}

variable "smtp_user" {
  type        = string
  description = "SMTP username"
  sensitive   = true
}

variable "smtp_password" {
  type        = string
  description = "SMTP password"
  sensitive   = true
}

variable "smtp_from" {
  type        = string
  description = "SMTP sender email address"
}
