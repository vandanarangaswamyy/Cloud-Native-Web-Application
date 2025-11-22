# ---------------------------------------------
# Security Groups Configuration
# ---------------------------------------------

# -------------------------------
#   Application Security Group
# -------------------------------
resource "aws_security_group" "app_sg" {
  name        = "csye6225-app-sg"
  description = "Security group for web application"
  vpc_id      = aws_vpc.this.id

  # Allow SSH (grader still needs to be able to get in)
  # ingress {
  #   description = "Allow SSH"
  #   from_port   = 22
  #   to_port     = 22
  #   protocol    = "tcp"
  #   cidr_blocks = ["0.0.0.0/0"]
  # }

  # Allow app traffic on port 8000 -- BUT ONLY from the ALB SG
  ingress {
    description     = "App port from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  # IMPORTANT:
  # We are REMOVING direct 80/443/8000 from 0.0.0.0/0.
  # No more public web access to instances.

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "csye6225-app-sg"
    Project = "CSYE6225"
  }
}


# -------------------------------
#  Database Security Group
# -------------------------------
resource "aws_security_group" "db_sg" {
  name        = "csye6225-db-sg"
  description = "Security group for RDS (MySQL) - only from app SG"
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "MySQL from app SG"
    protocol        = "tcp"
    from_port       = 3306
    to_port         = 3306
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    description = "All egress"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "csye6225-db-sg"
    Project = "CSYE6225"
  }
}

# -------------------------------
# Outputs for reuse
# -------------------------------
output "app_security_group_id" {
  description = "Security Group ID for web application"
  value       = aws_security_group.app_sg.id
}

output "db_security_group_id" {
  description = "Security Group ID for RDS"
  value       = aws_security_group.db_sg.id
}

# ---------------------------------------------
# Load Balancer Security Group (public entrypoint)
# ---------------------------------------------
resource "aws_security_group" "alb_sg" {
  name        = "csye6225-alb-sg"
  description = "Security group for the public-facing ALB"
  vpc_id      = aws_vpc.this.id

  # Allow HTTP from anywhere
  ingress {
    description = "Allow HTTP from world"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTPS from anywhere (future-proof: you might add TLS later)
  ingress {
    description = "Allow HTTPS from world"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound allowed (ALB -> targets)
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "csye6225-alb-sg"
    Project = "CSYE6225"
  }
}
