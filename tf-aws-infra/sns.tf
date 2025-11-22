#############################################
# 🔔 SNS Topic & Unified Policy
#############################################
resource "aws_sns_topic" "user_verification_topic" {
  name = "user-verification-topic"
}

resource "aws_sns_topic_policy" "user_verification_policy" {
  arn = aws_sns_topic.user_verification_topic.arn

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      # 1️⃣ Allow the SNS service (Lambda etc.)
      {
        Sid    = "AllowLambdaInvoke",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action   = "sns:Publish",
        Resource = aws_sns_topic.user_verification_topic.arn
      },

      # 2️⃣ Allow the root account (498048454096) to subscribe or receive
      {
        Sid    = "AllowRootSubscribe",
        Effect = "Allow",
        Principal = {
          AWS = "arn:aws:iam::498048454096:root"
        },
        Action = [
          "SNS:Subscribe",
          "SNS:Receive"
        ],
        Resource = aws_sns_topic.user_verification_topic.arn
      },

      # 3️⃣ Allow anyone (Lambda, services) to publish (optional legacy)
      {
        Sid       = "AllowGenericPublish",
        Effect    = "Allow",
        Principal = "*",
        Action    = "sns:Publish",
        Resource  = aws_sns_topic.user_verification_topic.arn
      },

      # 4️⃣ ✅ Allow Dev Account (268604531924) to publish cross-account
      {
        Sid    = "AllowDevAccountToPublish",
        Effect = "Allow",
        Principal = {
          AWS = "arn:aws:iam::268604531924:root"
        },
        Action   = "sns:Publish",
        Resource = aws_sns_topic.user_verification_topic.arn
      }
    ]
  })
}

# Outputs
output "verification_sns_topic_arn" {
  value = aws_sns_topic.user_verification_topic.arn
}
#############################################
# 🔔 SNS Cross-Account Publish Permission
#############################################
# resource "aws_iam_role_policy" "sns_crossaccount_publish" {
#   name = "csye6225-sns-crossaccount-policy"
#   role = aws_iam_role.webapp_ec2_role.name   # Same EC2 role already attached to instance
#
#   policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Sid      = "AllowPublishToRootSNS",
#         Effect   = "Allow",
#         Action   = "sns:Publish",
#         Resource = "arn:aws:sns:us-east-2:498048454096:user-verification-topic"  # root account SNS topic
#       }
#     ]
#   })
# }

