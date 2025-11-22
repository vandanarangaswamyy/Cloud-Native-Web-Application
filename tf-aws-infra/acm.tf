resource "aws_acm_certificate" "dev_cert" {
  domain_name       = "dev.vandanarangaswamy.com"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "csye6225-dev-cert"
  }
}
