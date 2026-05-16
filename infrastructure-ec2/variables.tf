variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "m5.xlarge"
}

variable "key_name" {
  description = "Name of the EC2 key pair for SSH access"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the application (e.g. mailabari.com)"
  type        = string
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID for the domain"
  type        = string
}

variable "eip_allocation_id" {
  description = "Allocation ID of the existing Elastic IP to associate with the instance (e.g. eipalloc-0123456789abcdef0)"
  type        = string
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "production"
}

variable "alb_ssl_policy" {
  description = "ALB HTTPS listener SSL policy"
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}
