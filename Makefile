.PHONY: build build-simple build-layer tf-init tf-plan tf-apply tf-destroy deploy-frontend dev-frontend test-backend

ENVIRONMENT  ?= prod
TF_DIR        = infrastructure
TF_VARS       = TF_VAR_environment=$(ENVIRONMENT)

# Pull deployment targets from terraform output (requires prior tf-apply)
FRONTEND_BUCKET    ?= $(shell cd $(TF_DIR) && terraform output -raw frontend_bucket 2>/dev/null)
CLOUDFRONT_ID      ?= $(shell cd $(TF_DIR) && terraform output -raw cloudfront_distribution_id 2>/dev/null)
LAMBDA_FUNCTION    ?= $(shell cd $(TF_DIR) && terraform output -raw lambda_function_name 2>/dev/null)

# --- Lambda build ---

build-layer:
	pip install -r backend/requirements.txt -t dist/layer/python/
	cp -r backend/shared dist/layer/python/

build: build-layer
	cp -r backend/handler.py backend/handlers backend/shared dist/layer/
	cd dist/layer && zip -r ../../dist/lambda.zip .

# Faster dev build: single pip install + zip (no layer separation)
build-simple:
	mkdir -p dist/packages
	pip install -r backend/requirements.txt -t dist/packages/ --quiet
	cp -r backend/handler.py backend/handlers backend/shared dist/packages/
	cd dist/packages && zip -r ../../dist/lambda.zip . \
		-x "**/__pycache__/*" -x "*.pyc" -x "*.dist-info/*"

# --- Terraform ---

tf-init:
	cd $(TF_DIR) && terraform init -backend-config=backend.hcl

tf-plan:
	cd $(TF_DIR) && $(TF_VARS) terraform plan

tf-apply:
	cd $(TF_DIR) && $(TF_VARS) terraform apply

tf-destroy:
	cd $(TF_DIR) && $(TF_VARS) terraform destroy

# --- Frontend ---

deploy-frontend:
	cd frontend && npm run build
	@test -n "$(FRONTEND_BUCKET)"  || (echo "ERROR: could not read frontend_bucket from terraform output"; exit 1)
	@test -n "$(CLOUDFRONT_ID)"    || (echo "ERROR: could not read cloudfront_distribution_id from terraform output"; exit 1)
	aws s3 sync frontend/out/ s3://$(FRONTEND_BUCKET)/ --delete \
		--cache-control "public,max-age=31536000,immutable" --exclude "*.html"
	aws s3 sync frontend/out/ s3://$(FRONTEND_BUCKET)/ --delete \
		--cache-control "public,max-age=0,must-revalidate" --include "*.html"
	aws cloudfront create-invalidation --distribution-id $(CLOUDFRONT_ID) --paths "/*"

dev-frontend:
	cd frontend && npm run dev

# --- Backend ---

deploy-backend: build-simple
	@test -n "$(LAMBDA_FUNCTION)" || (echo "ERROR: could not read lambda_function_name from terraform output"; exit 1)
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION) \
		--zip-file fileb://dist/lambda.zip \
		--architectures arm64
	aws lambda wait function-updated --function-name $(LAMBDA_FUNCTION)

test-backend:
	cd backend && python -m pytest tests/ -v
