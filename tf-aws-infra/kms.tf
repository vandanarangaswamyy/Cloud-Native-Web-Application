######################################################
# Caller identity (for dynamic ARN reference)
######################################################

######################################################
# KMS Key for RDS
######################################################
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS storage encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}

resource "aws_kms_alias" "rds" {
  name          = "alias/csye6225-rds"
  target_key_id = aws_kms_key.rds.id
}

######################################################
# KMS Key for S3
######################################################
resource "aws_kms_key" "s3" {
  description             = "KMS key for S3 object encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}

resource "aws_kms_alias" "s3" {
  name          = "alias/csye6225-s3"
  target_key_id = aws_kms_key.s3.id
}

######################################################
# KMS Key for EBS
######################################################
resource "aws_kms_key" "ebs" {
  description             = "KMS key for EBS volume encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}

resource "aws_kms_alias" "ebs" {
  name          = "alias/csye6225-ebs"
  target_key_id = aws_kms_key.ebs.id
}

######################################################
# Stable KMS Key for Secrets Manager (Permanent)
######################################################
resource "aws_kms_key" "secrets" {
  description             = "Permanent KMS key for encrypting Secrets Manager values (e.g. RDS credentials)"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "EnableRootPermissions",
        Effect = "Allow",
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        },
        Action   = "kms:*",
        Resource = "*"
      },
      {
        Sid    = "AllowSecretsManagerUse",
        Effect = "Allow",
        Principal = {
          Service = "secretsmanager.amazonaws.com"
        },
        Action = [
          "kms:GenerateDataKey",
          "kms:Decrypt"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/csye6225-secrets"
  target_key_id = aws_kms_key.secrets.id
}
