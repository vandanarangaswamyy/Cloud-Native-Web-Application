# Cloud Native Web Application – End-to-End Deployment on AWS

**Technologies:** Django · DRF · MySQL · AWS · Terraform · Packer · EC2 · ALB · ASG · Route 53 · ACM · Lambda · DynamoDB · SNS · SendGrid

This project implements a fully automated, production-grade cloud-native application deployed on AWS using Infrastructure as Code, scalable architecture, secure networking and a serverless email verification workflow.

The implementation is split across three repositories:
- **WebApp** – Django + DRF backend service
- **tf-aws-infra** – Terraform IaC for AWS
- **serverless** – Lambda-based email verification system

---

## Overview

### 1. WebApp (Django + DRF)

A RESTful backend with:

#### Core Features
- User signup/login with secure password hashing
- Email verification with token workflow
- Protected endpoints via Basic Auth
- MySQL database integration
- Health check endpoint for ALB
- Systemd-based deployment for EC2 instances

#### Environment
App secrets are injected via:
- AWS Secrets Manager
- Accessed at boot by the systemd service

---

### 2. tf-aws-infra (Terraform AWS Infrastructure)

This repo defines the complete cloud architecture.

#### VPC & Networking
- 1 VPC
- Public & private subnets (multi-AZ)
- Internet Gateway + NAT Gateway
- Route tables for proper routing
- Security Groups for ALB, EC2, DB with principle of least access

**Custom AMI (Packer)**
- Python runtime
- Django app & dependencies
- Systemd service to start app on boot

**Auto Scaling Group + Launch Template**
- Launches EC2s using the custom AMI
- Health-check based scaling
- Auto-replacement of unhealthy instances

**Application Load Balancer**
- Routes public traffic to EC2s
- Health checks at `/healthz`
- Target group monitoring
- SSL/TLS termination enabled with AWS Certificate Manager (ACM)
- Protects all client–server communication

#### Database Layer

**MySQL RDS**
- Multi-AZ configuration
- Lives in private subnets
- Only accessible from EC2 app servers
- Password stored securely in Secrets Manager

#### Security

**IAM Roles & Policies (Least Privilege)**
- Lambda execution role → only DynamoDB/SES/Logs
- EC2 instance role → access only to Secrets Manager and S3 logs
- Terraform-created roles follow least privilege:
  - No wildcard (*) policies
  - Fine-grained permissions for each service
  - Separation of duties between components

**KMS**
- Encrypted Secrets Manager values
- Keys deleted safely after project completion

#### DNS & Domain Management

**Custom Domain**
- Domain purchased from Namecheap
- Connected to AWS via Route 53 hosted zone
- A/AAAA records → ALB
- CNAME for email verification

**SSL/TLS**
- ACM certificate attached to ALB
- Enforces HTTPS for all traffic

---

### 3. Serverless Email Verification (serverless repo)

**AWS Lambda**
- Python 3.12 runtime
- Reads SNS messages for email verification events
- Sends emails via SendGrid
- Stores tokens in DynamoDB (`csye6225-email-tracker`)

**DynamoDB**
- Stores email verification tokens
- Ensures idempotency + expiry logic

**SNS**
- SNS topic → triggers Lambda
- SNS also used for operational notifications (below)

---

## Monitoring, Logging & Notifications

**CloudWatch Logs**
- Lambda logs
- Application logs (via EC2 instance role)

**CloudWatch Alarms**

Terraform provisions alarms for:
- EC2 instance health
- ALB 5xx errors
- High CPU usage
- Unhealthy target count

**SNS Notifications**

Alarms trigger SNS alerts

Email notifications for:
- High CPU
- Unhealthy EC2
- Lambda failures
- RDS storage warnings

---

## DevOps & IaC Highlights

**Infrastructure as Code (Terraform)**
- Modularized folder structure
- Remote state backend
- Multi-account deployment (dev/demo)
- Automated provisioning of:
  - VPC
  - ALB
  - ASG/EC2
  - RDS
  - ACM
  - CloudWatch alarms
  - IAM roles/policies
  - Lambda + DynamoDB + SNS

**CI/CD (GitHub Actions)**
- Validates Terraform
- Builds & uploads AMIs (manual or automated)
- Deploys application to EC2 via AMI refresh


## How to Run Locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```



