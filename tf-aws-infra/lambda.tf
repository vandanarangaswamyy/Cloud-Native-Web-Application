######################################################
# Lambda Function for Email Verification (Skeleton)
######################################################

resource "aws_lambda_function" "email_verification_lambda" {
  function_name = "csye6225-email-verification-lambda"
  description   = "Lambda to send verification emails via SendGrid when a user registers"

  # ✅ Create a placeholder ZIP just once — GitHub Actions will later update it
  filename         = "${path.module}/lambda_function_placeholder.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_function_placeholder.zip")

  handler = "lambda_function.lambda_handler"
  runtime = "python3.12"
  role    = aws_iam_role.lambda_exec_role.arn

  environment {
    variables = {
      REGION            = var.aws_region
      SNS_TOPIC_ARN     = var.sns_topic_arn
      SENDER_EMAIL      = var.sender_email
      APP_DOMAIN        = var.verification_url
      SENDGRID_API_KEY  = var.sendgrid_api_key
      EMAIL_TRACK_TABLE = aws_dynamodb_table.email_track_table.name
      FROM_EMAIL        = "no-reply@vandanarangaswamy.com"
    }
  }

  timeout = 10

  # ✅ Ignore future code changes made by CI/CD
  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash
    ]
  }
}

######################################################
# DynamoDB Table to Track Sent Emails
######################################################

resource "aws_dynamodb_table" "email_track_table" {
  name         = "csye6225-email-tracker"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email"

  attribute {
    name = "email"
    type = "S"
  }

  tags = {
    Name = "email-tracker"
  }
}

######################################################
# Lambda Permissions for SNS Invocation
######################################################

resource "aws_lambda_permission" "allow_sns_invoke" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.email_verification_lambda.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = var.sns_topic_arn
}

######################################################
# Subscribe Lambda to SNS Topic
######################################################

resource "aws_sns_topic_subscription" "lambda_subscription" {
  topic_arn = var.sns_topic_arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.email_verification_lambda.arn
}

######################################################
# Output SNS ARN (for reference/debug)
######################################################

output "sns_topic_arn_used" {
  value = var.sns_topic_arn
}
