resource "aws_launch_template" "webapp_lt" {
  name_prefix   = "csye6225_lt-"
  image_id      = var.ami_id
  instance_type = "t2.micro"

  key_name = var.key_pair_name

  # Network configuration for instances launched by ASG
  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.app_sg.id]
  }

  iam_instance_profile {
    name = aws_iam_instance_profile.webapp_instance_profile.name
  }

  # Same user-data you used in aws_instance.webapp_instance
  # We just reuse the same templatefile call
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    APP_NAME       = "csye6225"
    APP_DIR        = "/opt/csye6225"
    APP_PORT       = 8000
    db_name        = var.db_name
    db_user        = var.db_user
    db_host        = aws_db_instance.webapp_db.address
    s3_bucket_name = aws_s3_bucket.images.bucket
    region         = var.region
    db_secret_arn  = aws_secretsmanager_secret.db.arn
    sns_topic_arn  = aws_sns_topic.user_verification_topic.arn
  }))

  # Copy root_block_device config from your instance
  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = 25
      volume_type           = "gp2"
      delete_on_termination = true
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name    = "csye6225-webapp-instance"
      Project = "CSYE6225"
    }
  }
}
