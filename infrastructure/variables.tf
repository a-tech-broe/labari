variable "domain_name" {
  description = "Root domain name (e.g., labari.com). A Route53 hosted zone must already exist."
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod"
  }
}

variable "aws_region" {
  description = "Primary AWS region. ACM certs for CloudFront are always created in us-east-1 via a provider alias regardless of this value."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as a prefix for all resource names"
  type        = string
  default     = "labari"
}

variable "alert_email" {
  description = "Email address to receive CloudWatch alarm notifications"
  type        = string
}
