#############################################
# EC2 IAM Role — S3 + CloudWatch + RDS + SNS
#############################################

resource "aws_iam_role" "webapp_ec2_role" {
  name = "csye6225-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# --------------------------
# Inline IAM policy for S3
# --------------------------
resource "aws_iam_policy" "webapp_s3_policy" {
  name        = "csye6225-s3-policy"
  description = "Allow EC2 instance to access S3 bucket for image upload"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.images.bucket}",
          "arn:aws:s3:::${aws_s3_bucket.images.bucket}/*"
        ]
      }
    ]
  })
}

# --------------------------
# Inline IAM policy for RDS
# --------------------------
resource "aws_iam_policy" "webapp_rds_policy" {
  name        = "csye6225-rds-policy"
  description = "Allow EC2 instance to connect and describe RDS"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ],
        Resource = "*"
      }
    ]
  })
}

# --------------------------
# Inline IAM policy for CloudWatch Agent + Logs
# --------------------------
resource "aws_iam_policy" "webapp_cloudwatch_policy" {
  name        = "csye6225-cloudwatch-policy"
  description = "Allow EC2 instance to publish logs and metrics to CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "cloudwatch:PutMetricData",
          "ec2:DescribeTags"
        ],
        Resource = "*"
      }
    ]
  })
}

# --------------------------
# Attach policies to the EC2 Role
# --------------------------
resource "aws_iam_role_policy_attachment" "attach_s3_policy" {
  role       = aws_iam_role.webapp_ec2_role.name
  policy_arn = aws_iam_policy.webapp_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "attach_rds_policy" {
  role       = aws_iam_role.webapp_ec2_role.name
  policy_arn = aws_iam_policy.webapp_rds_policy.arn
}

resource "aws_iam_role_policy_attachment" "attach_cloudwatch_policy" {
  role       = aws_iam_role.webapp_ec2_role.name
  policy_arn = aws_iam_policy.webapp_cloudwatch_policy.arn
}

# --------------------------
# Instance Profile
# --------------------------
resource "aws_iam_instance_profile" "webapp_instance_profile" {
  name = "csye6225-ec2-instance-profile"
  role = aws_iam_role.webapp_ec2_role.name
}

#############################################
# Data Source: Current AWS Account
#############################################
data "aws_caller_identity" "current" {}

#############################################
# SNS Topic — user signup notifications
# (Added placeholder so terraform destroy works)
#############################################
resource "aws_sns_topic" "user_signup" {
  name = "user-signup-topic"
}

#############################################
# IAM Policy — Secrets Manager + KMS + SNS
#############################################
resource "aws_iam_policy" "webapp_extra_policy" {
  name        = "csye6225-ec2-extra-policy"
  description = "Allow EC2 to read Secrets Manager values, decrypt via KMS, and publish SNS messages"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      # --- Secrets Manager + KMS access ---
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
          "kms:Decrypt"
        ],
        Resource = [
          "arn:aws:secretsmanager:us-east-2:${data.aws_caller_identity.current.account_id}:secret:csye6225-db-credentials*",
          aws_kms_key.secrets.arn
        ]
      },
      # --- SNS publish permission ---
      {
        Effect = "Allow",
        Action = [
          "sns:Publish"
        ],
        Resource = [
          aws_sns_topic.user_signup.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_extra_policy" {
  role       = aws_iam_role.webapp_ec2_role.name
  policy_arn = aws_iam_policy.webapp_extra_policy.arn
}

#############################################
# Cross-account SNS publish policy
#############################################
resource "aws_iam_role_policy" "sns_crossaccount_publish" {
  name = "csye6225-sns-crossaccount-policy"
  role = aws_iam_role.webapp_ec2_role.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid      = "AllowPublishToRootSNS",
        Effect   = "Allow",
        Action   = "sns:Publish",
        Resource = var.root_sns_topic_arn
      }
    ]
  })
}
