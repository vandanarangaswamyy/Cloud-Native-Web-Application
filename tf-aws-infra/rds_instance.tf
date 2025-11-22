######################################################
# Random password for RDS (Terraform-managed)
######################################################
# resource "random_password" "db" {
#   length  = 16
#   special = true
# }

######################################################
# DB Subnet Group
######################################################
resource "aws_db_subnet_group" "webapp_subnets" {
  name       = "csye6225-db-subnet-group"
  subnet_ids = [for s in aws_subnet.private : s.id]

  tags = {
    Name = "csye6225-db-subnet-group"
  }
}

######################################################
# Optional: Custom Parameter Group (if needed)
######################################################
# Uncomment if you want to customize DB parameters.
# resource "aws_db_parameter_group" "webapp_param_group" {
#   name        = "csye6225-db-param-group"
#   family      = "mysql8.0"
#   description = "Custom parameter group for webapp DB"
# }

######################################################
# RDS Instance
######################################################
resource "aws_db_instance" "webapp_db" {
  identifier             = "csye6225-db"
  allocated_storage      = 20
  db_name                = var.db_name
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"
  username               = var.db_user
  password               = random_password.db.result
  parameter_group_name   = try(aws_db_parameter_group.webapp_param_group.name, null)
  db_subnet_group_name   = aws_db_subnet_group.webapp_subnets.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  skip_final_snapshot    = true
  publicly_accessible    = false
  multi_az               = false
  storage_encrypted      = true

  # Optional: use your permanent KMS key for encryption
  kms_key_id = aws_kms_key.secrets.arn

  tags = {
    Name = "csye6225-db"
  }
}
