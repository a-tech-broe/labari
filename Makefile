.PHONY: docker-up docker-down docker-build dev-frontend ec2-init ec2-plan ec2-apply

EC2_TF_DIR = infrastructure-ec2

# --- Docker (local dev) ---

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

docker-build:
	docker compose build

# --- Frontend dev server ---

dev-frontend:
	cd frontend && npm run dev

# --- EC2 Terraform ---

ec2-init:
	cd $(EC2_TF_DIR) && terraform init \
		-backend-config="key=labari-ec2/terraform.tfstate"

ec2-plan:
	cd $(EC2_TF_DIR) && terraform plan

ec2-apply:
	cd $(EC2_TF_DIR) && terraform apply
