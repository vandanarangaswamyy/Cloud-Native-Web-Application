resource "aws_autoscaling_group" "webapp_asg" {
  name                      = "csye6225_asg"
  min_size                  = 3
  max_size                  = 5
  desired_capacity          = 3
  default_cooldown          = 60
  health_check_grace_period = 60
  health_check_type         = "EC2"

  launch_template {
    id      = aws_launch_template.webapp_lt.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    values(aws_subnet.public)[0].id,
    values(aws_subnet.public)[1].id
  ]

  target_group_arns = [aws_lb_target_group.webapp_tg.arn]

  tag {
    key                 = "Name"
    value               = "csye6225-webapp"
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = "CSYE6225"
    propagate_at_launch = true
  }
}


# Policy: scale UP by +1
resource "aws_autoscaling_policy" "scale_up" {
  name                   = "cpu-scale-up"
  autoscaling_group_name = aws_autoscaling_group.webapp_asg.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = 1
  cooldown               = 60
}

# Policy: scale DOWN by -1
resource "aws_autoscaling_policy" "scale_down" {
  name                   = "cpu-scale-down"
  autoscaling_group_name = aws_autoscaling_group.webapp_asg.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = -1
  cooldown               = 60
}

# CloudWatch alarm to trigger scale UP (>5% avg CPU)
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 8
  alarm_description   = "Scale up when CPU > 5% avg"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.webapp_asg.name
  }

  alarm_actions = [aws_autoscaling_policy.scale_up.arn]
}

# CloudWatch alarm to trigger scale DOWN (<3% avg CPU)
resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 4
  alarm_description   = "Scale down when CPU < 3% avg"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.webapp_asg.name
  }

  alarm_actions = [aws_autoscaling_policy.scale_down.arn]
}
