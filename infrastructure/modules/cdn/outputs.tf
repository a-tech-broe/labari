output "distribution_arn" {
  value = aws_cloudfront_distribution.main.arn
}

output "distribution_id" {
  value = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.main.domain_name
}

output "oac_id" {
  value = aws_cloudfront_origin_access_control.main.id
}
