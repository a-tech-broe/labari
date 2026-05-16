# Labari

> **Labari** (Hausa: *stories / news*) — a production-grade blog platform built on AWS

A portfolio project demonstrating end-to-end DevOps ownership: dual deployment architectures (serverless and containerised), Infrastructure as Code, CI/CD pipelines, configuration management, and container orchestration.

---

## Features

**Public**

- Blog listing with live search and category filters
- Full post detail page with Markdown rendering
- Like and comment on stories
- Responsive dark-mode UI (Next.js + Tailwind CSS)

**Admin**

- Secure login with JWT authentication
- Create, edit, and delete posts with draft / publish toggle
- Direct-to-S3 image upload via presigned URLs
- Category tagging

---

## Architecture

Labari ships two fully working deployment targets. The EC2/Docker stack is the primary production architecture.

### EC2 / Docker (primary)

```text
                        Users
                          │
                          ▼
                    EC2  m5.xlarge
              ┌─── nginx :80 ─────────────────┐
              │  Static files  │  Reverse proxy │
              │                ▼                │
              │       FastAPI + Uvicorn         │
              │          :8000                  │
              │                │                │
              │                ▼                │
              │          PostgreSQL 16          │
              └────────────────────────────────┘
                    Elastic IP → Route 53
```

### Serverless (original, preserved)

```text
                        Users
                          │
                          ▼
              ┌─── CloudFront CDN ──────────────┐
              │                                  │
              ▼                                  │
        S3 (frontend)                            │
                                                 │
                     API Gateway HTTP v2         │
                          │                      │
                          ▼                      │
              Lambda (Python 3.12 · ARM64) ◄─────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
          DynamoDB               S3 (images)
        Single-table           Presigned URL upload
```

---

## Tech Stack

| Layer | EC2 / Docker | Serverless |
| ----- | ------------ | ---------- |
| IaC | Terraform (`infrastructure-ec2/`) | Terraform (`infrastructure/`) |
| Config management | Ansible | — |
| Compute | EC2 m5.xlarge | Lambda ARM64 |
| Backend | FastAPI + SQLAlchemy | Python Lambda handlers |
| Database | PostgreSQL 16 | DynamoDB single-table |
| Frontend | Next.js 14 static export served by nginx | S3 + CloudFront |
| Container registry | Docker Hub | — |
| Auth | JWT HS256 | JWT HS256 + SSM |
| CI/CD | GitHub Actions (`docker-deploy.yml`) | GitHub Actions (`deploy.yml`) |

---

## Project Structure

```text
labari/
├── backend-fastapi/              # FastAPI + SQLAlchemy (EC2 stack)
│   ├── main.py                   # App entry point, CORS, DB init
│   ├── core/                     # Config (pydantic-settings), JWT auth
│   ├── db/                       # SQLAlchemy models + session
│   ├── routers/                  # auth, posts, comments, images
│   └── Dockerfile
│
├── nginx/
│   ├── Dockerfile                # Multi-stage: Next.js build → nginx:alpine
│   └── nginx.conf                # Static files + reverse proxy to backend:8000
│
├── docker-compose.yml            # Local dev (postgres, backend, nginx on :3000)
├── docker-compose.prod.yml       # Production (Docker Hub images + env secrets)
│
├── infrastructure-ec2/           # Terraform: EC2, EIP association, Route 53
├── ansible/
│   ├── provision.yml             # Install Docker, start stack (first run)
│   └── deploy.yml                # Pull updated images, restart stack
│
├── backend/                      # Original Lambda handlers (preserved)
│   ├── handler.py
│   ├── handlers/                 # posts, auth, comments, images
│   ├── shared/                   # response helpers, DynamoDB, JWT
│   ├── seed/                     # Admin + story seed scripts
│   └── tests/                    # pytest + moto
│
├── frontend/
│   └── src/
│       ├── app/                  # Home, post detail, admin
│       ├── components/           # PostCard, LikeButton, CommentSection
│       └── lib/                  # API client, TypeScript types
│
├── infrastructure/               # Original serverless Terraform (preserved)
└── .github/workflows/
    ├── docker-deploy.yml         # EC2 stack: build images → provision → deploy
    └── deploy.yml                # Serverless stack: test → terraform → deploy
```

---

## Local Development

```bash
# Bring up the full stack locally (postgres + backend + nginx)
make docker-up        # http://localhost:3000

# Or run services individually
cd backend-fastapi
cp .env.example .env
uvicorn main:app --reload --port 8000

cd frontend
npm install && npm run dev   # http://localhost:3000

# Run serverless backend tests (moto mocks — no AWS needed)
make test-backend
```

---

## Deployment

### EC2 / Docker stack

#### Prerequisites

- AWS account + CLI configured
- Terraform ≥ 1.9
- An existing Elastic IP in your account
- A Route 53 hosted zone for your domain
- Docker Hub account with `labari-backend` and `labari-nginx` repos created

#### CI/CD pipeline overview

```
dev push (infrastructure-ec2/** changed)
  └── changes job (dorny/paths-filter)
        └── provision job
              ├── terraform apply   → EC2 + EIP association + Route 53
              └── ansible provision.yml → Docker install + stack start

any push (backend-fastapi/**, frontend/**, nginx/**)
  └── build job
        ├── docker build + push labari-backend → Docker Hub
        └── docker build + push labari-nginx   → Docker Hub

main push
  └── build job → deploy job
                    └── ansible deploy.yml → pull updated images + restart
```

#### 1. Provision infrastructure (first time only)

Add all secrets listed below, then push any file change inside `infrastructure-ec2/` to the `dev` branch. The `changes` job detects the modified path and automatically triggers `terraform apply` followed by the Ansible provisioning playbook.

To run manually instead:

```bash
cp infrastructure-ec2/terraform.tfvars.example infrastructure-ec2/terraform.tfvars
# Fill in: aws_region, key_name, domain_name, hosted_zone_id, eip_allocation_id

make ec2-init
make ec2-apply

pip install ansible
ansible-playbook ansible/provision.yml \
  -i "<ec2-ip>," \
  -u ubuntu --private-key ~/.ssh/labari.pem \
  -e "dockerhub_username=<user>" \
  -e "dockerhub_token=<token>" \
  -e "image_tag=latest" \
  -e "db_password=<pass>" \
  -e "jwt_secret=<secret>" \
  -e "aws_region=us-east-1" \
  -e "images_bucket="
```

#### 2. Deploy (every push to main)

CI builds both Docker images, pushes them to Docker Hub tagged with the commit SHA, then Ansible SSH-es into EC2 and runs `docker compose pull && up -d`. Nothing to run manually.

#### GitHub Actions secrets

| Secret | Required | Value |
| ------ | -------- | ----- |
| `AWS_ACCESS_KEY_ID` | ✅ | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | ✅ | IAM secret |
| `AWS_REGION` | ✅ | e.g. `us-east-1` |
| `TF_STATE_BUCKET` | ✅ | S3 bucket for Terraform state |
| `TF_LOCK_TABLE` | ✅ | DynamoDB table for state locking |
| `DOMAIN_NAME` | ✅ | e.g. `mailabari.com` |
| `HOSTED_ZONE_ID` | ✅ | Route 53 hosted zone ID |
| `EIP_ALLOCATION_ID` | ✅ | Allocation ID of an existing Elastic IP — find it with `aws ec2 describe-addresses` |
| `EC2_KEY_NAME` | ✅ | EC2 key pair name |
| `EC2_SSH_PRIVATE_KEY` | ✅ | Full contents of the `.pem` file |
| `DOCKERHUB_USERNAME` | ✅ | Docker Hub username |
| `DOCKERHUB_TOKEN` | ✅ | Docker Hub access token (Account Settings → Security) |
| `DB_PASSWORD` | ✅ | Strong password for PostgreSQL |
| `JWT_SECRET` | ✅ | Random string for JWT signing (e.g. `openssl rand -hex 32`) |
| `IMAGES_BUCKET` | ➖ | S3 bucket name for image uploads — leave blank to disable |

> **Tip:** Find your EIP allocation ID with:
> ```bash
> aws ec2 describe-addresses --query 'Addresses[*].[AllocationId,PublicIp]' --output table
> ```

---

### Serverless stack (original)

```bash
cp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars
cp infrastructure/backend.hcl.example infrastructure/backend.hcl

make tf-init && make tf-apply
make build-simple
make deploy-frontend
```

Additional secrets needed for the serverless CI pipeline: `LAMBDA_FUNCTION_NAME`, `FRONTEND_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`, `NEXT_PUBLIC_API_URL`, `ALERT_EMAIL`, `ADMIN_PASSWORD`.

---

## API Reference

All routes are identical between the EC2 (FastAPI) and serverless (Lambda) stacks.

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| GET | `/posts` | — | List published posts; optional `?category=aws` |
| GET | `/posts/{id}` | — | Get single post |
| GET | `/search?q=...` | — | Full-text search across title, excerpt, content |
| POST | `/posts` | JWT | Create post |
| PUT | `/posts/{id}` | JWT | Update post |
| DELETE | `/posts/{id}` | JWT | Delete post |
| POST | `/posts/{id}/like` | — | Increment like count |
| GET | `/posts/{id}/comments` | — | List comments |
| POST | `/posts/{id}/comments` | — | Add comment |
| DELETE | `/posts/{id}/comments/{comment_id}` | JWT | Delete comment |
| POST | `/auth/register` | — | Register — body: `email`, `password`, `name` |
| POST | `/auth/login` | — | Login — returns `token` + `user` |
| POST | `/images/upload` | JWT | Get presigned S3 URL |
