# Labari

> **Labari** (Hausa: *stories / news*) — a production-grade blog platform built on AWS

A portfolio project demonstrating end-to-end DevOps ownership: containerised application deployment, Infrastructure as Code, CI/CD pipelines, and configuration management on EC2.

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

```text
                        Users
                          │
                     DNS (Route 53)
                          │
                    Elastic IP (static)
                          │
                    EC2  m5.xlarge
              ┌─── nginx :80 ──────────────────┐
              │                                 │
              │  /            → static files    │
              │  /posts       → FastAPI :8000   │
              │  /auth/       → FastAPI :8000   │
              │  /search      → FastAPI :8000   │
              │  /images/     → FastAPI :8000   │
              │                                 │
              │         FastAPI + Uvicorn        │
              │              :8000               │
              │                │                 │
              │                ▼                 │
              │          PostgreSQL 16           │
              └─────────────────────────────────┘
```

All three services run as Docker containers managed by Docker Compose. nginx handles TLS termination, static file serving, and reverse proxying to the FastAPI backend.

---

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| IaC | Terraform ≥ 1.9 |
| Config management | Ansible |
| Compute | EC2 m5.xlarge (Ubuntu 22.04) |
| Backend | FastAPI + SQLAlchemy + Uvicorn |
| Database | PostgreSQL 16 |
| Frontend | Next.js 14 static export |
| Web server | nginx (reverse proxy + static files) |
| Containers | Docker + Docker Compose |
| Registry | Docker Hub |
| Auth | JWT HS256 |
| DNS | Route 53 (A record → Elastic IP) |
| CI/CD | GitHub Actions |

---

## Project Structure

```text
labari/
├── backend-fastapi/              # FastAPI application
│   ├── main.py                   # App entry point — CORS, DB init, router wiring
│   ├── core/
│   │   ├── config.py             # pydantic-settings (reads .env)
│   │   └── auth.py               # JWT create/decode, get_current_user dependency
│   ├── db/
│   │   ├── models.py             # SQLAlchemy ORM: User, Post, Comment
│   │   └── session.py            # Engine + get_db dependency
│   ├── routers/
│   │   ├── auth.py               # POST /auth/register, /auth/login
│   │   ├── posts.py              # CRUD + search + like
│   │   ├── comments.py           # List / create / delete comments
│   │   └── images.py             # S3 presigned URL
│   └── Dockerfile
│
├── nginx/
│   ├── Dockerfile                # Multi-stage: npm build → nginx:alpine
│   └── nginx.conf                # Static files + proxy_pass to backend:8000
│
├── infrastructure-ec2/
│   ├── main.tf                   # EC2, security group, EIP association, Route 53
│   ├── variables.tf
│   └── outputs.tf
│
├── ansible/
│   ├── provision.yml             # Install Docker, pull images, start stack (first run)
│   └── deploy.yml                # Pull updated images, restart stack
│
├── frontend/
│   └── src/
│       ├── app/                  # Home, post detail, admin pages
│       ├── components/           # PostCard, LikeButton, CommentSection
│       └── lib/                  # API client, TypeScript types
│
├── docker-compose.yml            # Local dev (postgres, backend, nginx on :3000)
├── docker-compose.prod.yml       # Production (Docker Hub images)
└── .github/workflows/
    └── docker-deploy.yml         # CI/CD pipeline
```

---

## Local Development

```bash
# Full stack (postgres + backend + nginx)
make docker-up            # http://localhost:3000

# Frontend only (hot reload)
make dev-frontend         # http://localhost:3000

# Tear down and remove volumes
make docker-down
```

Backend environment variables (copy and edit before running locally):

```bash
cp backend-fastapi/.env.example backend-fastapi/.env
```

---

## CI/CD Pipeline

**File:** `.github/workflows/docker-deploy.yml`

```
dev push  (infrastructure-ec2/** changed)
  └── changes  →  provision
                    ├── terraform apply   (EC2 + EIP + Route 53)
                    └── ansible provision.yml  (Docker install + first deploy)

any push  (backend-fastapi/**, frontend/**, nginx/**)
  └── build
        ├── docker build + push  labari-backend → Docker Hub
        └── docker build + push  labari-nginx   → Docker Hub

main push
  └── build  →  deploy
                  └── ansible deploy.yml  (pull updated images + restart)
```

---

## Deployment

### Prerequisites

- AWS account with CLI configured
- Terraform ≥ 1.9
- An existing Elastic IP (`eipalloc-…`) in your AWS account
- A Route 53 hosted zone for your domain
- EC2 key pair created in AWS
- Docker Hub account — create two public repos: `labari-backend` and `labari-nginx`

### First-time provisioning

Add all secrets (table below), then push any file change inside `infrastructure-ec2/` to the `dev` branch. The pipeline detects the changed path and runs `terraform apply` + `ansible/provision.yml` automatically.

To run manually:

```bash
cp infrastructure-ec2/terraform.tfvars.example infrastructure-ec2/terraform.tfvars
# Edit: aws_region, key_name, domain_name, hosted_zone_id, eip_allocation_id

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

### Ongoing deploys

Push to `main`. The pipeline builds updated images and Ansible restarts the stack on EC2.

### GitHub Actions secrets

| Secret | Required | Value |
| ------ | :------: | ----- |
| `AWS_ACCESS_KEY_ID` | ✅ | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | ✅ | IAM secret |
| `AWS_REGION` | ✅ | e.g. `us-east-1` |
| `TF_STATE_BUCKET` | ✅ | S3 bucket for Terraform state |
| `TF_LOCK_TABLE` | ✅ | DynamoDB table for state locking |
| `DOMAIN_NAME` | ✅ | e.g. `mailabari.com` |
| `HOSTED_ZONE_ID` | ✅ | Route 53 hosted zone ID |
| `EIP_ALLOCATION_ID` | ✅ | Find with `aws ec2 describe-addresses --query 'Addresses[*].[AllocationId,PublicIp]' --output table` |
| `EC2_KEY_NAME` | ✅ | EC2 key pair name |
| `EC2_SSH_PRIVATE_KEY` | ✅ | Full contents of the `.pem` file |
| `DOCKERHUB_USERNAME` | ✅ | Docker Hub username |
| `DOCKERHUB_TOKEN` | ✅ | Docker Hub access token (hub.docker.com → Account Settings → Security) |
| `DB_PASSWORD` | ✅ | Strong password for PostgreSQL |
| `JWT_SECRET` | ✅ | `openssl rand -hex 32` |
| `IMAGES_BUCKET` | ➖ | S3 bucket for image uploads — leave blank to disable |

---

## API Reference

| Method | Path | Auth | Description |
| ------ | ---- | :--: | ----------- |
| GET | `/posts` | | List published posts; optional `?category=aws` |
| GET | `/posts/{id}` | | Get single post |
| GET | `/search?q=…` | | Full-text search across title, excerpt, and content |
| POST | `/posts` | JWT | Create post |
| PUT | `/posts/{id}` | JWT | Update post |
| DELETE | `/posts/{id}` | JWT | Delete post |
| POST | `/posts/{id}/like` | | Increment like count |
| GET | `/posts/{id}/comments` | | List comments |
| POST | `/posts/{id}/comments` | | Add a comment |
| DELETE | `/posts/{id}/comments/{comment_id}` | JWT | Delete comment |
| POST | `/auth/register` | | Register — body: `email`, `password`, `name` |
| POST | `/auth/login` | | Login — returns `token` + `user` |
| POST | `/images/upload` | JWT | Get presigned S3 upload URL |
