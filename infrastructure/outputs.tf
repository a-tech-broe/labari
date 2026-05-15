output "frontend_url" {
  description = "Blog frontend URL"
  value       = "https://${var.domain_name}"
}

output "api_url" {
  description = "API base URL"
  value       = module.api.api_endpoint
}

output "cloudfront_distribution_id" {
  description = "Used for cache invalidation in CI/CD"
  value       = module.cdn.distribution_id
}

output "frontend_bucket" {
  description = "S3 bucket name for frontend deployment"
  value       = module.storage.frontend_bucket_id
}

output "lambda_function_name" {
  description = "Lambda function name for manual invocations"
  value       = module.api.lambda_function_name
}
