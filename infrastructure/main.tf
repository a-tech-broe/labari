module "dns" {
  source = "./modules/dns"

  domain_name  = var.domain_name
  project_name = var.project_name
  environment  = var.environment

  providers = {
    aws = aws.us_east_1
  }
}

module "storage" {
  source = "./modules/storage"

  project_name = var.project_name
  environment  = var.environment
  account_id   = data.aws_caller_identity.current.account_id
  domain_name  = var.domain_name
}

module "database" {
  source = "./modules/database"

  project_name = var.project_name
  environment  = var.environment
}

module "cdn" {
  source = "./modules/cdn"

  project_name                         = var.project_name
  environment                          = var.environment
  domain_name                          = var.domain_name
  certificate_arn                      = module.dns.certificate_arn
  zone_id                              = module.dns.zone_id
  frontend_bucket_id                   = module.storage.frontend_bucket_id
  frontend_bucket_regional_domain_name = "${module.storage.frontend_bucket_id}.s3.${var.aws_region}.amazonaws.com"
}

module "api" {
  source = "./modules/api"

  project_name        = var.project_name
  environment         = var.environment
  domain_name         = var.domain_name
  certificate_arn     = module.dns.certificate_arn
  zone_id             = module.dns.zone_id
  dynamodb_table_name = module.database.table_name
  dynamodb_table_arn  = module.database.table_arn
  images_bucket_id    = module.storage.images_bucket_id
  images_bucket_arn   = module.storage.images_bucket_arn
  alert_email         = var.alert_email
  aws_region          = var.aws_region
}

# Frontend S3 bucket policy: grants CloudFront OAC access.
# Lives here (not in storage module) to break the circular dependency between
# storage (needs CloudFront ARN) and cdn (needs bucket ID).
resource "aws_s3_bucket_policy" "frontend" {
  bucket = module.storage.frontend_bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowCloudFrontOAC"
      Effect = "Allow"
      Principal = {
        Service = "cloudfront.amazonaws.com"
      }
      Action   = "s3:GetObject"
      Resource = "${module.storage.frontend_bucket_arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = module.cdn.distribution_arn
        }
      }
    }]
  })
}
