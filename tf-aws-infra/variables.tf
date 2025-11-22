variable "target_account" {
  description = "AWS CLI profile to use (dev or demo)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "vpc_name" {
  description = "Name tag for the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC (e.g., 10.0.0.0/16)"
  type        = string
}

variable "subnet_newbits" {
  description = "How many extra bits to add when carving subnets from VPC CIDR"
  type        = number
  default     = 8
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "key_pair_name" {
  description = "Name of the existing AWS key pair for SSH"
  type        = string
}


variable "ami_id" {
  description = "Custom AMI ID built via Packer"
  type        = string
}

# variable "s3_bucket_name" {
#   description = "S3 bucket name for image uploads"
#   type        = string
# }

variable "db_name" {
  description = "RDS database name-csye6225"
  type        = string
  default     = "csye6225"
}

variable "db_user" {
  description = "RDS master username-csye6225"
  type        = string
  default     = "csye6225"
}

variable "root_sns_topic_arn" {
  description = "SNS topic ARN in the root account for email verification"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
}

variable "webapp_domain" {
  description = "Base domain for verification links"
  type        = string
}

variable "lambda_name" {
  description = "Lambda function name"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for verification emails"
  type        = string
}

variable "sender_email" {
  description = "Verified SES sender email address"
  type        = string
}

variable "verification_url" {
  description = "Base URL for email verification links"
  type        = string
}

variable "sendgrid_api_key" {
  type = string
}
