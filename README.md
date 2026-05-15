# Labari

> **Labari** (Hausa: *stories / news*) — a production-grade serverless blog platform built on AWS

A portfolio project demonstrating end-to-end AWS ownership: architecture design, Infrastructure as Code, CI/CD pipelines, serverless engineering, security best practices, observability, and cost optimisation — all at near-zero monthly cost.

---

## Features

**Public**

- Blog listing with live search and category filters
- Full post detail page with Markdown rendering
- Responsive dark-mode UI (Next.js + Tailwind CSS)

**Admin**

- Secure login with JWT authentication
- Create, edit, delete posts with draft / publish mode
- Direct-to-S3 image upload via presigned URLs
- Category tagging

---

## Architecture

```text
                        Users
                          │
                          ▼
              ┌─── CloudFront CDN ───────────────────────┐
              │   HTTPS · Custom domain · SPA routing     │
              ▼                                           │
        S3 (frontend)                                     │
      Next.js static export                               │
                                                          │
                   api.yourdomain.com                     │
                          │                               │
                          ▼                               │
              API Gateway HTTP v2                         │
              CORS · Custom domain · Access logs          │
                          │                               │
                          ▼                               │
             Lambda  (Python 3.12 · ARM64) ◄─────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
          DynamoDB               S3 (images)
        Single-table           Presigned URL upload
        GSI for sorting
              │
      SSM Parameter Store
      JWT secret · Encrypted
```

**Estimated cost at zero traffic:** ~$0.00 / month — everything is pay-per-use  
**Estimated cost at 10 000 requests / month:** < $1.00 / month

---

## AWS Services

| Layer | Service | Why |
| ----- | ------- | --- |
| Frontend Hosting | Amazon S3 | Cheapest static hosting — no server needed |
| CDN + HTTPS | CloudFront | Global CDN, free SSL, SPA routing via error pages |
| Backend API | API Gateway HTTP v2 | Serverless APIs — cheaper and faster than REST API |
| Compute | Lambda (ARM64) | No EC2 costs — Graviton2 is 20 % cheaper than x86 |
| Database | DynamoDB | Pay-per-request — free tier eligible, scales to zero |
| Auth | JWT + SSM Parameter Store | No Cognito cost — secret rotated via SSM |
| DNS | Route 53 | Custom domain + ACM cert validation |
| CI/CD | GitHub Actions | Free for public repos |
| Monitoring | CloudWatch | Native Lambda + API Gateway logs + metric alarms |
| Secrets | SSM Parameter Store | Free-tier SecureString — no Secrets Manager cost |

---

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| IaC | Terraform ≥ 1.9, modular (5 reusable modules) |
| Frontend | Next.js 14 static export, TypeScript, Tailwind CSS |
| Backend | Python 3.12 Lambda, single-monolith handler |
| Database | DynamoDB single-table design with GSI |
| Auth | JWT HS256, secret stored in SSM Parameter Store |
| CDN | CloudFront with Origin Access Control (OAC) |
| DNS + TLS | Route 53 + ACM wildcard certificate |
| CI/CD | GitHub Actions — 3 independent pipelines |
| Observability | CloudWatch Logs + Metric Alarms → SNS → Email |

---

## Project Structure

```text
labari/
├── infrastructure/
│   ├── main.tf                   # Root module — wires all modules together
│   ├── modules/
│   │   ├── dns/                  # Route 53 zone lookup + ACM wildcard cert
│   │   ├── storage/              # S3 buckets: frontend (OAC) + images (CORS)
│   │   ├── cdn/                  # CloudFront distribution + OAC + DNS records
│   │   ├── database/             # DynamoDB PAY_PER_REQUEST + GSI1
│   │   └── api/                  # API Gateway + Lambda + IAM + SSM + CloudWatch
├── backend/
│   ├── handler.py                # Entry point — routes on event['routeKey']
│   ├── handlers/
│   │   ├── posts.py              # CRUD, categories, search
│   │   ├── auth.py               # Register / login, bcrypt + JWT
│   │   └── images.py             # S3 presigned URL generation
│   ├── shared/
│   │   ├── response.py           # HTTP response helpers + CORS headers
│   │   ├── auth.py               # JWT verification, SSM secret (lru_cache)
│   │   └── db.py                 # DynamoDB singleton
│   └── tests/                    # pytest + moto — no AWS account needed
├── frontend/
│   └── src/
│       ├── app/                  # Home, post detail, admin dashboard
│       ├── components/           # Header, Footer, PostCard
│       └── lib/                  # API client, TypeScript types
└── .github/workflows/
    ├── terraform.yml             # Plan on PR · Apply on merge
    ├── deploy-backend.yml        # Test → build zip → update Lambda
    └── deploy-frontend.yml       # Typecheck → build → S3 sync → CF invalidation
```

---

## Getting Started

### Prerequisites

- AWS account with CLI configured (`aws configure`)
- Terraform ≥ 1.9
- Python 3.12 + pip
- Node.js 20 + npm
- A Route 53 hosted zone for your domain

### 1. Deploy infrastructure

```bash
cp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars
# Fill in domain_name, alert_email, etc.

make tf-init
make tf-plan
make tf-apply
```

> ACM certificate DNS validation takes up to 5 minutes on first run.

### 2. Build and deploy backend

```bash
make build-simple    # pip install deps + zip → dist/lambda.zip

aws lambda update-function-code \
  --function-name $(cd infrastructure && terraform output -raw lambda_function_name) \
  --zip-file fileb://dist/lambda.zip
```

### 3. Deploy frontend

```bash
cp frontend/.env.local.example frontend/.env.local
# Set NEXT_PUBLIC_API_URL=https://api.yourdomain.com

make deploy-frontend \
  FRONTEND_BUCKET=$(cd infrastructure && terraform output -raw frontend_bucket) \
  CLOUDFRONT_ID=$(cd infrastructure && terraform output -raw cloudfront_distribution_id)
```

### 4. Create your first account

```bash
curl -X POST https://api.yourdomain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword","name":"Your Name"}'
```

Then go to `https://yourdomain.com/admin/` to log in and start writing.

---

## CI/CD (GitHub Actions)

Three pipelines — each triggers only when its own files change.

| Pipeline | Trigger path | What it does |
| -------- | ------------ | ------------ |
| `terraform.yml` | `infrastructure/**` | Plan on PR (posts comment), apply on merge |
| `deploy-backend.yml` | `backend/**` | Run tests → build zip → update Lambda |
| `deploy-frontend.yml` | `frontend/**` | Typecheck → build → S3 sync → CF invalidation |

Set these repository secrets (`Settings → Secrets → Actions`):

| Secret | Value |
| ------ | ----- |
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret |
| `DOMAIN_NAME` | e.g. `labari.com` |
| `ALERT_EMAIL` | CloudWatch alarm recipient |
| `LAMBDA_FUNCTION_NAME` | `terraform output lambda_function_name` |
| `FRONTEND_BUCKET` | `terraform output frontend_bucket` |
| `CLOUDFRONT_DISTRIBUTION_ID` | `terraform output cloudfront_distribution_id` |
| `NEXT_PUBLIC_API_URL` | e.g. `https://api.labari.com` |

---

## API Reference

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| GET | `/posts` | — | List published posts; optional `?category=aws` |
| GET | `/posts/{id}` | — | Get single post |
| GET | `/search?q=...` | — | Search title, excerpt, content, and categories |
| POST | `/posts` | JWT | Create post — body: `title`, `content`, `categories[]`, `published` |
| PUT | `/posts/{id}` | JWT | Update post fields |
| DELETE | `/posts/{id}` | JWT | Delete post |
| POST | `/auth/register` | — | Register — body: `email`, `password`, `name` |
| POST | `/auth/login` | — | Login — returns `token` + `user` |
| POST | `/images/upload` | JWT | Get presigned S3 URL — body: `file_type` |

---

## Local Development

```bash
# Backend — runs tests with moto mocks, no AWS account required
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -v

# Frontend — dev server with hot reload
cd frontend
npm install
npm run dev
```
