.PHONY: build build-layer tf-init tf-plan tf-apply tf-destroy deploy-frontend dev-frontend

ENVIRONMENT ?= prod
TF_DIR = infrastructure

build-layer:
	pip install -r backend/requirements.txt -t dist/layer/python/
	cp -r backend/shared dist/layer/python/

build: build-layer
	cp -r backend/handler.py backend/handlers dist/
	cd dist && zip -r lambda.zip handler.py handlers/ layer/python/shared/
	cd dist && zip -r lambda.zip $(shell find dist/layer/python -mindepth 1 -maxdepth 1 -not -name shared -printf "%P\n" | sed 's|^|dist/layer/python/|')

# Simpler build: zip entire backend dir (faster for dev)
build-simple:
	pip install -r backend/requirements.txt -t dist/packages/
	cp -r backend/* dist/packages/
	cd dist/packages && zip -r ../../dist/lambda.zip .

tf-init:
	cd $(TF_DIR) && terraform init

tf-plan:
	cd $(TF_DIR) && terraform plan -var-file=terraform.tfvars

tf-apply:
	cd $(TF_DIR) && terraform apply -var-file=terraform.tfvars

tf-destroy:
	cd $(TF_DIR) && terraform destroy -var-file=terraform.tfvars

deploy-frontend:
	cd frontend && npm run build
	aws s3 sync frontend/out/ s3://$(FRONTEND_BUCKET)/ --delete
	aws cloudfront create-invalidation --distribution-id $(CLOUDFRONT_ID) --paths "/*"

dev-frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && python -m pytest tests/ -v
