#############################################
# 🔐 Secrets Manager Configuration
#############################################

# Use the same random_password.db defined in rds_instance.tf
# (remove this block if it's already declared elsewhere)

resource "random_password" "db" {
  length           = 20
  special          = true
  override_special = "!#$%^&*()-_=+[]{}:,.?" # ✅ only safe for RDS
}

######################################################
# Secrets Manager Secret (Encrypted via Stable KMS)
######################################################
resource "aws_secretsmanager_secret" "db" {
  name        = "csye6225-db-credentials-${terraform.workspace}"
  description = "RDS credentials for ${terraform.workspace} environment"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = {
    Name    = "csye6225-db-secret"
    Project = "CSYE6225"
    Env     = terraform.workspace
  }

  depends_on = [aws_kms_key.secrets]
}

######################################################
# Secret Version (stores dynamic DB connection details)
######################################################
resource "aws_secretsmanager_secret_version" "db_value" {
  secret_id = aws_secretsmanager_secret.db.id

  secret_string = jsonencode({
    username = var.db_user
    password = random_password.db.result
    engine   = "mysql"
    host     = aws_db_instance.webapp_db.address
    port     = aws_db_instance.webapp_db.port
    dbname   = aws_db_instance.webapp_db.db_name
  })

  depends_on = [
    aws_kms_key.secrets,
    aws_db_instance.webapp_db
  ]
}

######################################################
# Output for reference (can be consumed by app module)
######################################################
output "db_secret_arn" {
  value       = aws_secretsmanager_secret.db.arn
  description = "ARN of the Secrets Manager secret storing RDS credentials"
}
