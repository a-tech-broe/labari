# Labari

> **Labari** (Hausa: *stories / news*) — a production-grade blog platform built on AWS

A portfolio project demonstrating end-to-end DevOps ownership: containerised application deployment, Infrastructure as Code, CI/CD pipelines, database migrations, and security hardening on EC2.

---

## Features

- Blog listing with live search and category filters
- Full post detail with Markdown rendering, likes, and comments
- Responsive dark-mode UI (Next.js 14 + Tailwind CSS)
- Admin dashboard — create, edit, publish posts with image uploads
- JWT authentication

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
              │  /health      → FastAPI :8000   │
              │                                 │
              │      FastAPI + Uvicorn (x2)     │
              │              :8000              │
              │                │                │
              │                ▼                │
              │         PostgreSQL 16           │
              └─────────────────────────────────┘
```

All three services run as Docker containers managed by Compose. nginx handles static file serving, reverse proxying, security headers, and request size limits. The backend runs as a non-root user and applies Alembic migrations before startup.

---

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| IaC | Terraform ≥ 1.9 |
| Config management | Ansible |
| Compute | EC2 m5.xlarge (Ubuntu 22.04) |
| Backend | FastAPI + SQLAlchemy + Uvicorn |
| Migrations | Alembic (runs on container startup) |
| Database | PostgreSQL 16 |
| Frontend | Next.js 14 static export |
| Web server | nginx (security headers, reverse proxy, static files) |
| Containers | Docker + Docker Compose |
| Registry | Docker Hub |
| Auth | JWT HS256 |
| DNS | Route 53 (A record → Elastic IP) |
| CI/CD | GitHub Actions |

---

## Project Structure

```text
labari/
├── backend-fastapi/
│   ├── main.py                   # CORS (env-scoped), health check with DB probe
│   ├── entrypoint.sh             # Runs migrations then starts uvicorn
│   ├── core/
│   │   ├── config.py             # pydantic-settings — JWT_SECRET validated at startup
│   │   └── auth.py               # JWT create/decode, get_current_user dependency
│   ├── db/
│   │   ├── models.py             # SQLAlchemy ORM: User, Post, Comment (with indexes)
│   │   └── session.py            # Connection pool (size=10, overflow=20, recycle=1800s)
│   ├── routers/
│   │   ├── auth.py               # POST /auth/register, /auth/login
│   │   ├── posts.py              # CRUD, paginated search, atomic like increment
│   │   ├── comments.py           # List / create / delete comments
│   │   └── images.py             # S3 presigned URL
│   ├── alembic/                  # Versioned schema migrations
│   │   ├── env.py
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   ├── alembic.ini
│   ├── Dockerfile                # Non-root appuser, entrypoint.sh
│   └── .env.example
│
├── nginx/
│   ├── Dockerfile                # Multi-stage: npm build → nginx:alpine
│   └── nginx.conf                # Security headers, 10 MB body limit, cache rules
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
│   ├── package-lock.json         # Lockfile — ensures reproducible Docker builds
│   └── src/
│       ├── app/                  # Home, post detail, admin pages
│       ├── components/           # PostCard, LikeButton, CommentSection
│       └── lib/                  # API client, TypeScript types
│
├── docker-compose.yml            # Local dev — health checks, env defaults
├── docker-compose.prod.yml       # Production — Docker Hub images, restart policies
└── .github/workflows/
    └── docker-deploy.yml         # CI/CD pipeline
```

---

## Local Development

```bash
# Start the full stack (postgres + backend + nginx)
make docker-up        # → http://localhost:3000

# Frontend hot-reload only
make dev-frontend     # → http://localhost:3000

# Tear down (removes volumes)
make docker-down
```

Set up backend environment before first run:

```bash
cp backend-fastapi/.env.example backend-fastapi/.env
# Edit JWT_SECRET — must be a strong random value:
# openssl rand -hex 32
```

The `docker-compose.yml` dev stack uses a built-in `JWT_SECRET` so you don't need to set one for local dev. For any standalone `uvicorn` run, the `.env` file is required.

---

## CI/CD Pipeline

**File:** `.github/workflows/docker-deploy.yml`

A `changes` job runs first on every push to detect which paths changed. Subsequent jobs only run when relevant paths are affected.

```text
push to dev  (infrastructure-ec2/** changed)
  └── changes → provision
                  ├── terraform apply        EC2 + EIP association + Route 53
                  └── ansible provision.yml  Docker install + first stack deploy

push to any branch  (backend-fastapi/**, frontend/**, nginx/**)
  └── changes → build
                  ├── docker build + push  labari-backend → Docker Hub :<sha> + :latest
                  └── docker build + push  labari-nginx   → Docker Hub :<sha> + :latest

push to main  (app files changed + build succeeded)
  └── build → deploy
                └── ansible deploy.yml  pull updated images + docker compose up -d

workflow_dispatch on main  (manual re-deploy, no code change needed)
  └── deploy → ansible deploy.yml  pull :latest images + docker compose up -d
```

SSH keys are written to a unique temp file (`mktemp`) and deleted with `if: always()` after each Ansible run.

### Manual re-deploy

If you need to redeploy without a code change (e.g., after first provisioning), go to **GitHub → Actions → Docker Deploy → Run workflow**, select `main`, and leave the image tag as `latest`. The deploy job runs immediately without rebuilding images.

---

## Deployment

### Prerequisites

- AWS account + CLI configured
- Terraform ≥ 1.9
- An existing Elastic IP in your AWS account
- A Route 53 hosted zone for your domain
- An EC2 key pair
- Docker Hub account with two repos: `labari-backend` and `labari-nginx`

### First-time provisioning

Add all secrets (table below), then push any file inside `infrastructure-ec2/` to the `dev` branch. CI runs `terraform apply` then `ansible/provision.yml` automatically.

To provision manually instead:

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
  -e "jwt_secret=$(openssl rand -hex 32)" \
  -e "domain_name=mailabari.com" \
  -e "aws_region=us-east-1" \
  -e "images_bucket="
```

### Ongoing deploys

Push to `main`. The pipeline builds new images (tagged with the commit SHA and `:latest`), then Ansible pulls them and restarts the stack with zero-downtime Compose recreation.

To redeploy without a code change, use the manual workflow dispatch described in the CI/CD section above.

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
| `EIP_ALLOCATION_ID` | ✅ | `aws ec2 describe-addresses --query 'Addresses[*].[AllocationId,PublicIp]' --output table` |
| `EC2_KEY_NAME` | ✅ | EC2 key pair name |
| `EC2_SSH_PRIVATE_KEY` | ✅ | Full contents of the `.pem` file |
| `DOCKERHUB_USERNAME` | ✅ | Docker Hub username |
| `DOCKERHUB_TOKEN` | ✅ | Docker Hub access token (hub.docker.com → Account Settings → Security) |
| `DB_PASSWORD` | ✅ | Strong password for PostgreSQL |
| `JWT_SECRET` | ✅ | `openssl rand -hex 32` — app refuses to start if this is not set |
| `IMAGES_BUCKET` | ➖ | S3 bucket for image uploads — leave blank to disable |

---

## Security

| Control | Implementation |
| ------- | -------------- |
| JWT secret validation | App fails at startup if `JWT_SECRET` is not overridden from the default |
| CORS | Locked to `DOMAIN_NAME` in production; localhost in dev |
| Security headers | `X-Frame-Options`, `X-Content-Type-Options`, `HSTS`, `Referrer-Policy`, `Permissions-Policy` via nginx |
| Request size | `client_max_body_size 10M` in nginx |
| Container user | Backend runs as non-root `appuser` |
| Atomic counters | Like increment uses `UPDATE … RETURNING` — no read-modify-write race |
| Schema migrations | Alembic — versioned, rollback-capable, runs before server starts |
| Connection pool | `pool_size=10`, `max_overflow=20`, `pool_recycle=1800s` |
| Health check | `/health` probes the database; returns `503` if DB is unreachable |
| SSH key hygiene | Written to `mktemp`, deleted with `if: always()` after Ansible run |
| Docs | Swagger UI disabled in production (`ENVIRONMENT=production`) |

---

## API Reference

All endpoints are proxied through nginx on port 80. No separate API subdomain needed.

| Method | Path | Auth | Description |
| ------ | ---- | :--: | ----------- |
| GET | `/posts?category=&limit=&offset=` | | Paginated list of published posts |
| GET | `/posts/{id}` | | Single post |
| GET | `/search?q=&limit=&offset=` | | Search title, excerpt, and content |
| POST | `/posts` | JWT | Create post |
| PUT | `/posts/{id}` | JWT | Update post |
| DELETE | `/posts/{id}` | JWT | Delete post |
| POST | `/posts/{id}/like` | | Atomic like increment |
| GET | `/posts/{id}/comments` | | List comments |
| POST | `/posts/{id}/comments` | | Add comment |
| DELETE | `/posts/{id}/comments/{comment_id}` | JWT | Delete comment |
| POST | `/auth/register` | | Register — `email`, `password`, `name` |
| POST | `/auth/login` | | Login — returns `token` + `user` |
| POST | `/images/upload` | JWT | Presigned S3 upload URL |
| GET | `/health` | | DB-aware health check — `200 ok` or `503 degraded` |
