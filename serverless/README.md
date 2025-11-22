# 📦 Serverless Lambda Deployment (CI/CD)

This repository contains the AWS Lambda function that powers the email verification service for the CSYE 6225 web application.

---

## 🧩 Prerequisites

- **Python 3.12+**
- **AWS CLI** installed and configured
- **Terraform** for initial infrastructure setup
- **SendGrid API Key** (stored in AWS Secrets Manager)
- Access to an IAM role with `lambda:UpdateFunctionCode`

---

## ⚙️ Local Build & Deploy (Manual)

```bash
# Install dependencies
pip install -r requirements.txt -t package

# Package the Lambda
cp lambda_function.py package/
cd package && zip -r ../lambda_function.zip . && cd ..

# Deploy to AWS Lambda
aws lambda update-function-code \
  --function-name csye6225-email-verification-lambda \
  --zip-file fileb://lambda_function.zip \
  --publish
