# Cloud Native Web Application – CSYE 6225

## Project Overview

This project implements a Cloud Native Web Application using Django + Django REST Framework (DRF) with user authentication, product management, and integrated email verification via AWS SNS + Lambda.

The application is fully deployed on AWS using Terraform Infrastructure as Code, Packer, and GitHub Actions CI/CD pipelines, supporting both Dev and Demo environments.

## Architecture Overview

### Core Components

| Component | Technology | Description |
|-----------|-----------|-------------|
| Application | Django + DRF | RESTful web API for users and products |
| Database | Amazon RDS (MySQL) | Managed MySQL database |
| Storage | Amazon S3 | Stores static and media files |
| Secrets | AWS Secrets Manager | Stores MySQL and SendGrid credentials |
| Email | AWS SNS + Lambda + SendGrid | Triggers verification emails |
| Encryption | AWS KMS | Custom keys for EC2, RDS, S3, and Secrets Manager |
| SSL | AWS ACM (Dev) / ZeroSSL (Demo) | Secure HTTPS for both environments |
| Monitoring | AWS CloudWatch | Logs, metrics, and alarms |
| IaC | Terraform | Infrastructure provisioning and teardown |
| CI/CD | GitHub Actions | Automated testing, AMI build, and deployment |

## Infrastructure Deployment (Terraform)

### Prerequisites

- AWS CLI configured with dev and demo profiles
- Terraform v1.8+
- Packer v1.10+
- GitHub repository secrets configured for both accounts:
    - `AWS_ACCESS_KEY_ID_DEV`, `AWS_SECRET_ACCESS_KEY_DEV`
    - `AWS_ACCESS_KEY_ID_DEMO`, `AWS_SECRET_ACCESS_KEY_DEMO`

### Commands
```bash
# Initialize
terraform init

# Validate
terraform validate

# Plan (Dev)
terraform plan --var-file=terraform.tfvars --profile=dev

# Apply (Dev)
terraform apply --var-file=terraform.tfvars --profile=dev

# Plan (Demo)
terraform plan --var-file=terraform.tfvars --profile=demo

# Apply (Demo)
terraform apply --var-file=terraform.tfvars --profile=demo
```

### Key Terraform Modules

- `vpc.tf` → VPC, subnets, IGW, route tables
- `alb.tf` → Application Load Balancer (IPv4-only)
- `asg.tf` → Auto Scaling Group + Launch Template
- `kms.tf` → Custom KMS keys for each resource
- `secrets.tf` → Secrets Manager for database and email credentials
- `lambda.tf` → Email verification Lambda + DynamoDB tracker
- `sns.tf` → SNS topic + Lambda subscription
- `rds.tf` → MySQL instance (KMS-encrypted)

## SSL Certificates

### Dev Environment (ACM)

Uses AWS Certificate Manager to automatically issue and validate `dev.vandanarangaswamy.com`.

### Demo Environment (ZeroSSL)

Using a manually imported certificate for `demo.vandanarangaswamy.com`.

**Import Command** (documented per requirement):
```bash
aws acm import-certificate \
  --certificate fileb://certificate.crt \
  --certificate-chain fileb://ca_bundle.crt \
  --private-key fileb://private.key \
  --region us-east-2 \
  --profile demo
```

## CI/CD Pipelines

### Web Application – packer-build.yml

Runs on every pull request merge.

**Executes:**
1. Unit tests (pytest)
2. Packer validation and build
3. AMI creation in Dev account
4. AMI sharing to Demo account
5. AWS CLI profile switch to Demo
6. Launch Template version update
7. Auto Scaling Group instance refresh
8. Waits for instance refresh completion

**Tools Used:**
- GitHub Actions
- Packer
- AWS EC2 AMIs
- Terraform-managed networking

### Lambda CI/CD – ci-cd.yml

Triggered on every push to any branch in the serverless repository.

**Steps:**
1. Build Lambda ZIP (sendgrid included)
2. Configure AWS credentials (Dev)
3. Verify function existence
4. Update function code
5. Wait for deployment completion
6. Log summary (version, size, timestamp)

## Email Verification Flow

1. User registers via `POST /v1/user/`
2. Django publishes event to SNS topic
3. SNS invokes Lambda
4. Lambda:
    - Sends a SendGrid email with a verification link:
```
     https://<domain>/validateEmail?email=<user>&token=<uuid>
```
- Stores email+UUID in DynamoDB for deduplication
5. User clicks link → `validateEmail` endpoint:
    - Token expires after 1 minute
    - Invalid or reused tokens are rejected
    - Success response marks the user as verified

## Security Overview

| Resource | Encryption | Key Type |
|----------|-----------|----------|
| EC2 | AES-256 | Custom KMS Key |
| RDS | AES-256 | Custom KMS Key |
| S3 | AES-256 | Custom KMS Key |
| Secrets Manager | AES-256 | Custom KMS Key |
| Lambda | IAM-based Access | Role-bound Permissions |

## Networking (IPv4 Only)

All infrastructure is IPv4-only — consistent with CSYE 6225 guidelines.

- ALB uses `ip_address_type = "ipv4"`
- No IPv6 CIDR assigned to subnets or VPC
- Route53 has only A records (no AAAA)
- Ensures compatibility with AWS load balancer and grading scripts

## Testing

### Unit Tests
```bash
pytest -v
```

### Integration Tests
```bash
pytest "api/tests/integration tests/" -v
```

### Coverage
```bash
pytest --cov=api --cov-report=term-missing
```

## Validation Commands

### Check ALB DNS
```bash
dig <dev/demo>.vandanarangaswamy.com +short
```

### Health Check
```bash
curl -v https://<dev/demo>.vandanarangaswamy.com/healthz 
```

### Create User
```bash
curl -i -X POST https://<dev/demo>.vandanarangaswamy.com/v1/user/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"v","last_name":"r","email":"<mail>","password":"Pass@12345"}'
```

**Expected response:**
```json
{"message": "Verification email sent"}
```
