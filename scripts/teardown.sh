#!/usr/bin/env bash
# Destroys all Labari AWS resources (Terraform) and optionally cleans up
# Docker Hub images and the Terraform state backend (S3 + DynamoDB).
#
# Usage:
#   ./scripts/teardown.sh                  # interactive prompts
#   ./scripts/teardown.sh --yes            # skip confirmation (CI-safe)
#
# Required env vars (or will be prompted):
#   TF_STATE_BUCKET      S3 bucket holding terraform.tfstate
#   TF_LOCK_TABLE        DynamoDB table for state locking
#   AWS_REGION           e.g. us-east-1
#   TF_VAR_key_name      EC2 key pair name
#   TF_VAR_domain_name   e.g. mailabari.com
#   TF_VAR_hosted_zone_id
#   TF_VAR_eip_allocation_id
#
# Optional (for Docker Hub cleanup):
#   DOCKERHUB_USERNAME
#   DOCKERHUB_TOKEN      Docker Hub access token

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$REPO_ROOT/infrastructure-ec2"
AUTO_YES=false

# ── Argument parsing ──────────────────────────────────────────────────────────

for arg in "$@"; do
  case $arg in
    --yes|-y) AUTO_YES=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────

red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
bold()   { printf '\033[1m%s\033[0m\n' "$*"; }

prompt_var() {
  local var="$1" label="$2" secret="${3:-false}"
  if [ -z "${!var:-}" ]; then
    if [ "$secret" = "true" ]; then
      read -rsp "$label: " value; echo
    else
      read -rp "$label: " value
    fi
    export "$var=$value"
  fi
}

confirm() {
  if $AUTO_YES; then return 0; fi
  local answer
  read -rp "$1 [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]]
}

# ── Prerequisites ─────────────────────────────────────────────────────────────

for cmd in terraform aws; do
  if ! command -v "$cmd" &>/dev/null; then
    red "Required tool not found: $cmd"
    exit 1
  fi
done

bold "=== Labari Teardown ==="
echo
yellow "This will PERMANENTLY destroy all AWS resources for this project:"
echo "  • EC2 instance (labari-prod)"
echo "  • Application Load Balancer + target group + listeners"
echo "  • ACM certificate"
echo "  • Security groups (labari-alb, labari-ec2)"
echo "  • Route 53 A records (domain + www)"
echo "  • EIP association (the Elastic IP itself is NOT deleted)"
echo

# ── Collect required config ───────────────────────────────────────────────────

bold "--- Terraform backend config ---"
prompt_var AWS_REGION           "AWS region (e.g. us-east-1)"
prompt_var TF_STATE_BUCKET      "S3 bucket for Terraform state"
prompt_var TF_LOCK_TABLE        "DynamoDB lock table name"

bold "--- Terraform variables ---"
prompt_var TF_VAR_key_name           "EC2 key pair name"
prompt_var TF_VAR_domain_name        "Domain name (e.g. mailabari.com)"
prompt_var TF_VAR_hosted_zone_id     "Route 53 hosted zone ID"
prompt_var TF_VAR_eip_allocation_id  "EIP allocation ID (eipalloc-...)"

export TF_VAR_aws_region="$AWS_REGION"

echo
if ! confirm "Proceed with terraform destroy?"; then
  echo "Aborted."
  exit 0
fi

# ── Terraform destroy ─────────────────────────────────────────────────────────

bold "--- Initialising Terraform ---"
terraform -chdir="$TF_DIR" init -reconfigure \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=labari-ec2/terraform.tfstate" \
  -backend-config="dynamodb_table=$TF_LOCK_TABLE" \
  -backend-config="region=$AWS_REGION" \
  -input=false

bold "--- Destroying AWS resources ---"
terraform -chdir="$TF_DIR" destroy -auto-approve

green "Terraform destroy complete."

# ── Optional: Docker Hub cleanup ─────────────────────────────────────────────

echo
if confirm "Delete Docker Hub repositories (labari-backend, labari-nginx)?"; then
  prompt_var DOCKERHUB_USERNAME "Docker Hub username"
  prompt_var DOCKERHUB_TOKEN    "Docker Hub access token" true

  bold "--- Authenticating with Docker Hub ---"
  HUB_JWT=$(curl -sf -X POST "https://hub.docker.com/v2/users/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$DOCKERHUB_USERNAME\",\"password\":\"$DOCKERHUB_TOKEN\"}" \
    | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

  if [ -z "$HUB_JWT" ]; then
    red "Docker Hub login failed — skipping image cleanup."
  else
    for repo in labari-backend labari-nginx; do
      STATUS=$(curl -sf -o /dev/null -w "%{http_code}" -X DELETE \
        "https://hub.docker.com/v2/repositories/$DOCKERHUB_USERNAME/$repo/" \
        -H "Authorization: JWT $HUB_JWT" || true)
      if [ "$STATUS" = "202" ] || [ "$STATUS" = "204" ]; then
        green "  Deleted: $DOCKERHUB_USERNAME/$repo"
      else
        yellow "  Could not delete $DOCKERHUB_USERNAME/$repo (HTTP $STATUS) — delete manually at hub.docker.com"
      fi
    done
  fi
fi

# ── Optional: Terraform state backend ────────────────────────────────────────

echo
yellow "The Terraform state backend (S3 bucket '$TF_STATE_BUCKET' and DynamoDB table '$TF_LOCK_TABLE') was NOT deleted."
if confirm "Delete the state backend too? (irreversible — only do this if you are done with the project entirely)"; then
  bold "--- Deleting Terraform state ---"

  # Empty and delete the S3 bucket (versioned buckets need object version purge)
  aws s3 rm "s3://$TF_STATE_BUCKET" --recursive --region "$AWS_REGION" || true
  # Delete all object versions (required before deleting a versioned bucket)
  aws s3api list-object-versions --bucket "$TF_STATE_BUCKET" --region "$AWS_REGION" \
    --query '{Objects: Versions[].{Key: Key, VersionId: VersionId}}' \
    --output json 2>/dev/null \
  | grep -v "^null" \
  | xargs -I{} aws s3api delete-objects --bucket "$TF_STATE_BUCKET" --region "$AWS_REGION" --delete '{}' 2>/dev/null || true

  aws s3api delete-bucket --bucket "$TF_STATE_BUCKET" --region "$AWS_REGION" \
    && green "  Deleted S3 bucket: $TF_STATE_BUCKET" \
    || yellow "  Could not delete S3 bucket — remove manually"

  aws dynamodb delete-table --table-name "$TF_LOCK_TABLE" --region "$AWS_REGION" \
    && green "  Deleted DynamoDB table: $TF_LOCK_TABLE" \
    || yellow "  Could not delete DynamoDB table — remove manually"
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo
green "=== Teardown complete ==="
echo "Note: the Elastic IP ($TF_VAR_eip_allocation_id) was disassociated but NOT released."
echo "Release it manually to stop incurring charges:"
echo "  aws ec2 release-address --allocation-id $TF_VAR_eip_allocation_id --region $AWS_REGION"
