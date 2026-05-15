variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "domain_name" {
  type = string
}

variable "certificate_arn" {
  type = string
}

variable "zone_id" {
  type = string
}

variable "dynamodb_table_name" {
  type = string
}

variable "dynamodb_table_arn" {
  type = string
}

variable "images_bucket_id" {
  type = string
}

variable "images_bucket_arn" {
  type = string
}

variable "alert_email" {
  type = string
}

variable "aws_region" {
  type = string
}
