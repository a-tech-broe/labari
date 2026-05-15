# Labari

> **Labari** (Hausa: *stories / news*) — a production-grade serverless blog platform on AWS

A portfolio project demonstrating AWS architecture, Infrastructure as Code, CI/CD, and serverless engineering.

---

## Architecture

```text
Users
  │
  ▼
CloudFront CDN  ──────────────────────────────────────────────┐
  │  (HTTPS, custom domain, SPA routing)                       │
  ▼                                                            │
S3 (frontend)                                                  │
Next.js static export                                         │
                                                               │
      api.yourdomain.com                                       │
              │                                                │
              ▼                                                │
      API Gateway HTTP v2  ─────────────────────────────────  │
              │  (CORS, custom domain, access logs)            │
              ▼                                                │
        Lambda (Python 3.12, ARM64)  ◄────────────────────────┘
              │
      ┌───────┴────────┐
      ▼                ▼
  DynamoDB          S3 (images)
(single-table)   (presigned URL upload)
      │
  SSM Parameter Store
  (JWT secret, encrypted)
```

**Estimated cost at zero traffic:** ~$0.00/month (everything is pay-per-use)  
**Estimated cost at 10k requests/month:** <$1.00/month

---

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| IaC | Terraform ≥1.9, modular |
| Frontend | Next.js 14 (static export), TypeScript, Tailwind CSS |
| Backend | Python 3.12 Lambda (ARM64), single-function monolith |
| Database | DynamoDB (single-table, PAY_PER_REQUEST) |
| Auth | JWT (HS256), secret in SSM Parameter Store |
| CDN | CloudFront with Origin Access Control (OAC) |
| DNS + TLS | Route53 + ACM (wildcard cert) |
| CI/CD | GitHub Actions (3 separate pipelines) |
| Observability | CloudWatch Logs + Metric Alarms → SNS → Email |

---

## Project Structure

```text
labari/
├── infrastructure/          # Terraform
│   ├── main.tf              # Root module — orchestrates all modules
│   ├── modules/
│   │   ├── dns/             # Route53 + ACM wildcard cert (us-east-1)
│   │   ├── storage/         # S3: frontend + images buckets
│   │   ├── cdn/             # CloudFront distribution + OAC
│   │   ├── database/        # DynamoDB single-table with GSI
│   │   └── api/             # API Gateway + Lambda + IAM + SSM + CloudWatch
├── backend/                 # Python Lambda
│   ├── handler.py           # Entry point — routes by routeKey
│   ├── handlers/            # posts.py, auth.py, images.py
│   ├── shared/              # response.py, auth.py, db.py
│   └── tests/               # pytest + moto (no AWS required)
├── frontend/                # Next.js
│   └── src/
│       ├── app/             # Home, post page, admin dashboard
│       ├── components/      # Header, Footer, PostCard
│       └── lib/             # API client, TypeScript types
└── .github/workflows/       # CI/CD: terraform, backend, frontend
```

---

## Getting Started

### Prerequisites

- AWS account with CLI configured (`aws configure`)
- Terraform ≥1.9
- Python 3.12 + pip
- Node.js 20 + npm
- A Route53 hosted zone for your domain

### 1. Infrastructure

```bash
cp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars
# Edit terraform.tfvars with your domain, email, etc.

make tf-init
make tf-plan
make tf-apply
```

> **First run:** ACM certificate validation via DNS can take up to 5 minutes.

### 2. Build & Deploy Backend

```bash
make build           # Creates dist/lambda.zip
# Then re-run terraform apply, or:
aws lambda update-function-code \
  --function-name labari-prod-api \
  --zip-file fileb://dist/lambda.zip
```

### 3. Deploy Frontend

```bash
cp frontend/.env.local.example frontend/.env.local
# Edit NEXT_PUBLIC_API_URL=https://api.yourdomain.com

make deploy-frontend FRONTEND_BUCKET=<bucket> CLOUDFRONT_ID=<dist-id>
```

### 4. Create your first account

```bash
curl -X POST https://api.yourdomain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword","name":"Your Name"}'
```

Then log in at `https://yourdomain.com/admin/`.

---

## CI/CD (GitHub Actions)

Set these repository secrets:

| Secret | Description |
| ------ | ----------- |
| `AWS_ACCESS_KEY_ID` | IAM user for deployments |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret |
| `DOMAIN_NAME` | e.g., `labari.com` |
| `ALERT_EMAIL` | CloudWatch alarm email |
| `LAMBDA_FUNCTION_NAME` | From `terraform output lambda_function_name` |
| `FRONTEND_BUCKET` | From `terraform output frontend_bucket` |
| `CLOUDFRONT_DISTRIBUTION_ID` | From `terraform output cloudfront_distribution_id` |
| `NEXT_PUBLIC_API_URL` | e.g., `https://api.labari.com` |

Pipelines trigger automatically on `main` branch pushes when relevant paths change.

---

## API Reference

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| GET | `/posts` | — | List published posts (optional `?category=aws`) |
| GET | `/posts/{id}` | — | Get single post |
| GET | `/search?q=...` | — | Full-text search across title/excerpt/content/categories |
| POST | `/posts` | JWT | Create post (supports `categories` array) |
| PUT | `/posts/{id}` | JWT | Update post |
| DELETE | `/posts/{id}` | JWT | Delete post |
| POST | `/auth/register` | — | Register account |
| POST | `/auth/login` | — | Login, returns JWT |
| POST | `/images/upload` | JWT | Get S3 presigned URL for direct browser upload |

---

## Local Development

```bash
# Backend tests (no AWS needed — uses moto mocks)
cd backend && pip install -r requirements-dev.txt
python -m pytest tests/ -v

# Frontend dev server
cd frontend && npm install && npm run dev
```
