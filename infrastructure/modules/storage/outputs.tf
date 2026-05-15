output "frontend_bucket_id" {
  value = aws_s3_bucket.frontend.id
}

output "frontend_bucket_regional_domain_name" {
  value = aws_s3_bucket.frontend.bucket_regional_domain_name
}

output "frontend_bucket_arn" {
  value = aws_s3_bucket.frontend.arn
}

output "images_bucket_id" {
  value = aws_s3_bucket.images.id
}

output "images_bucket_arn" {
  value = aws_s3_bucket.images.arn
}

output "images_bucket_domain_name" {
  value = aws_s3_bucket.images.bucket_regional_domain_name
}
