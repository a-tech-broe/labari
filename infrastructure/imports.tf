# Use this file to import existing AWS resources into Terraform state instead
# of letting Terraform try to create them (which fails if they already exist).
#
# Uncomment the relevant block, run `terraform plan` to verify, then
# `terraform apply`. After import, re-comment or delete the block — import
# blocks are one-shot operations.
#
# Find the resource addresses with: terraform state list
# Find AWS resource IDs in the AWS Console or CLI.

# --- ACM Certificate ---
# If the cert already exists and Terraform tries to create a duplicate:
#
# import {
#   to = module.dns.aws_acm_certificate.main
#   id = "arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/CERTIFICATE_ID"
# }

# --- Route53 Validation Records ---
# If the CNAME records already exist (allow_overwrite=true handles this
# automatically, but import is available if you need explicit state tracking):
#
# import {
#   to = module.dns.aws_route53_record.cert_validation["*.yourdomain.com"]
#   id = "ZONE_ID_VALIDATION_RECORD_NAME_CNAME"
# }

# --- DynamoDB Table ---
# If the table already exists from a previous manual deployment:
#
# import {
#   to = module.database.aws_dynamodb_table.main
#   id = "labari-prod"
# }

# --- S3 Buckets ---
# import {
#   to = module.storage.aws_s3_bucket.frontend
#   id = "labari-prod-frontend-ACCOUNT_ID"
# }
#
# import {
#   to = module.storage.aws_s3_bucket.images
#   id = "labari-prod-images-ACCOUNT_ID"
# }

# --- Lambda Function ---
# import {
#   to = module.api.aws_lambda_function.api
#   id = "labari-prod-api"
# }
