# -------------------------------
# S3 Bucket for Image Storage
# -------------------------------
resource "aws_s3_bucket" "images" {
  bucket        = local.s3_bucket_name
  force_destroy = true # allows terraform destroy even if not empty

  tags = {
    Name    = local.s3_bucket_name
    Project = "CSYE6225"
  }
}

# -------------------------------
# Block All Public Access
# -------------------------------
resource "aws_s3_bucket_public_access_block" "images" {
  bucket                  = aws_s3_bucket.images.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -------------------------------
# Default Encryption (AES256)
# -------------------------------
resource "aws_s3_bucket_server_side_encryption_configuration" "images" {
  bucket = aws_s3_bucket.images.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}

# -------------------------------
# Lifecycle Policy (STANDARD → STANDARD_IA after 30 days)
# -------------------------------
resource "aws_s3_bucket_lifecycle_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
  }
}
