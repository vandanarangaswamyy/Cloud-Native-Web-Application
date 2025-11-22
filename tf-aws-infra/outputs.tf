output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = [for s in aws_subnet.public : s.id]
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = [for s in aws_subnet.private : s.id]
}

output "public_route_table_id" {
  value = aws_route_table.public.id
}

output "private_route_table_id" {
  value = aws_route_table.private.id
}

output "igw_id" {
  value = aws_internet_gateway.this.id
}

# output "webapp_instance_public_ip" {
#   description = "Public IP of the Web Application EC2 instance"
#   value       = aws_instance.webapp_instance.public_ip
# }
#
# output "webapp_instance_id" {
#   description = "Instance ID of the Web Application EC2 instance"
#   value       = aws_instance.webapp_instance.id
# }

output "rds_endpoint" {
  description = "RDS endpoint for the web application"
  value       = aws_db_instance.webapp_db.address
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.images.bucket
  description = "The generated unique S3 bucket name."
}

output "lambda_function_name" {
  value = aws_lambda_function.email_verification_lambda.function_name
}

output "lambda_arn" {
  value = aws_lambda_function.email_verification_lambda.arn
}

output "email_track_table_name" {
  value = aws_dynamodb_table.email_track_table.name
}
