# Target group for the Django app
resource "aws_lb_target_group" "webapp_tg" {
  name        = "webapp-tg"
  port        = 8000
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = aws_vpc.this.id

  health_check {
    path                = "/healthz" # your app MUST return 200 here
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name    = "webapp-tg"
    Project = "CSYE6225"
  }
}

# Application Load Balancer (public)
resource "aws_lb" "webapp_alb" {
  name               = "webapp-alb"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    aws_security_group.alb_sg.id
  ]

  # ALB must live in public subnets
  subnets = [
    values(aws_subnet.public)[0].id,
    values(aws_subnet.public)[1].id
  ]

  enable_deletion_protection = false

  tags = {
    Name    = "webapp-alb"
    Project = "CSYE6225"
  }
}

# =======================================================
# HTTPS Listener - DEV environment
# =======================================================
resource "aws_lb_listener" "https_listener_dev" {
  load_balancer_arn = aws_lb.webapp_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = data.aws_acm_certificate.dev_cert.arn # from ACM (dev account)

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.webapp_tg.arn
  }
}

# Redirect root (/) to /healthz for DEV
resource "aws_lb_listener_rule" "root_to_healthz_dev" {
  listener_arn = aws_lb_listener.https_listener_dev.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.webapp_tg.arn
  }

  condition {
    path_pattern {
      values = ["/"]
    }
  }
}

# # =======================================================
# # HTTPS Listener - DEMO environment (ZeroSSL Certificate)
# # =======================================================
# resource "aws_lb_listener" "https_listener_demo" {
#   load_balancer_arn = aws_lb.webapp_alb.arn
#   port              = "443"
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-2016-08"
#   certificate_arn   = "arn:aws:acm:us-east-2:021730294097:certificate/52e56e3b-9f1c-4799-99a4-6f4360611379"
#
#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.webapp_tg.arn
#   }
# }
# # Redirect root (/) to /healthz for DEMO
# resource "aws_lb_listener_rule" "root_to_healthz_demo" {
#   listener_arn = aws_lb_listener.https_listener_demo.arn
#   priority     = 10
#
#   action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.webapp_tg.arn
#   }
#
#   condition {
#     path_pattern {
#       values = ["/"]
#     }
#   }
# }