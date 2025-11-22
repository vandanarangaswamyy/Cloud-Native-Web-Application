######################################################
# IAM Role for Lambda Execution
######################################################

resource "aws_iam_role" "lambda_exec_role" {
  name = "csye6225-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

######################################################
# IAM Policy for Lambda (CloudWatch, SNS, SES)
######################################################
resource "aws_iam_policy" "lambda_policy" {
  name        = "csye6225-lambda-policy"
  description = "Allow Lambda to write logs, access SNS, and send email via SES"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },

      # SES Send Email
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      },

      # SNS (in case Lambda republish or log to SNS)
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "sns:Subscribe"
        ]
        Resource = "*"
      }
    ]
  })
}

######################################################
# Attach Policy to Role
######################################################
resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name        = "csye6225-lambda-dynamodb-policy"
  description = "Allow Lambda to access DynamoDB email tracker table"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DescribeTable"
        ]
        Resource = "arn:aws:dynamodb:us-east-2:${data.aws_caller_identity.current.account_id}:table/csye6225-email-tracker"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_dynamodb_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}