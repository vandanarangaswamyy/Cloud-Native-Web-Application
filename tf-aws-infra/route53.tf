# --- Look up the hosted zone you manually created in your Dev AWS account ---
data "aws_route53_zone" "dev_zone" {
  name         = "dev.vandanarangaswamy.com."
  private_zone = false
}

# --- Use the existing issued ACM certificate ---
data "aws_acm_certificate" "dev_cert" {
  domain      = "dev.vandanarangaswamy.com"
  statuses    = ["ISSUED"]
  most_recent = true
}

# --- Point dev.vandanarangaswamy.com to the ALB ---
resource "aws_route53_record" "dev_webapp" {
  zone_id = data.aws_route53_zone.dev_zone.zone_id
  name    = "dev.vandanarangaswamy.com"
  type    = "A"

  alias {
    name                   = aws_lb.webapp_alb.dns_name
    zone_id                = aws_lb.webapp_alb.zone_id
    evaluate_target_health = true
  }

  # ✅ Prevent Terraform from recreating existing A record
  lifecycle {
    ignore_changes = all
  }
}

##########################################################
# Route53 - DEMO Environment
##########################################################
# data "aws_route53_zone" "demo_zone" {
#   name         = "demo.vandanarangaswamy.com."
#   private_zone = false
# }

# You no longer use data source for ACM here since it's imported manually,
# but we keep the flexibility if you ever reimport or refresh it later.
# data "aws_acm_certificate" "demo_cert" {
#   domain      = "demo.vandanarangaswamy.com"
#   statuses    = ["ISSUED"]
#   most_recent = true
# }
#
# resource "aws_route53_record" "demo_webapp" {
#   zone_id = data.aws_route53_zone.demo_zone.zone_id
#   name    = "demo.vandanarangaswamy.com"
#   type    = "A"
#
#   alias {
#     name                   = aws_lb.webapp_alb.dns_name
#     zone_id                = aws_lb.webapp_alb.zone_id
#     evaluate_target_health = true
#   }
#
#   lifecycle {
#     ignore_changes = all
#   }
# }