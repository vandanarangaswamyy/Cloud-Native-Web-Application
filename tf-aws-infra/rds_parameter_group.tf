# ---------------------------------------------
# RDS Parameter Group
# ---------------------------------------------
resource "aws_db_parameter_group" "webapp_param_group" {
  name        = "csye6225-mysql-parameter-group"
  family      = "mysql8.0"
  description = "Custom parameter group for csye6225 webapp"

  parameter {
    name  = "max_connections"
    value = "200"
  }

  parameter {
    name  = "slow_query_log"
    value = "1"
  }

  tags = {
    Name = "csye6225-mysql-param-group"
  }
}
