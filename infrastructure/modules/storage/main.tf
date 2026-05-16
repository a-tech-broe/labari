locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# --- Frontend bucket (served via CloudFront OAC, not public) ---

resource "aws_s3_bucket" "frontend" {
  bucket        = "${local.name_prefix}-frontend-${var.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket policy is created in the root module to avoid a circular dependency
# with CloudFront (CloudFront ARN is needed here but isn't known until CDN module runs)

# --- Images bucket (private; accessed via presigned URLs) ---

resource "aws_s3_bucket" "images" {
  bucket        = "${local.name_prefix}-images-${var.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket                  = aws_s3_bucket.images.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  cors_rule {
    allowed_headers = ["Content-Type", "Content-Length", "Authorization"]
    allowed_methods = ["PUT", "GET"]
    allowed_origins = ["https://${var.domain_name}", "https://www.${var.domain_name}"]
    max_age_seconds = 3000
  }
}
