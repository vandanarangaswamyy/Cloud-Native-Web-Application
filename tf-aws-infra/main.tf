########################################
# Data Sources
########################################

# Get 3 usable AZs in the region
data "aws_availability_zones" "this" {
  state = "available"
}

########################################
# VPC
########################################

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = var.vpc_name
  })
}

########################################
# Internet Gateway
########################################

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.vpc_name}-igw" })
}

########################################
# Local Variables
########################################

locals {
  # We’ll use the first 3 AZs
  azs = slice(data.aws_availability_zones.this.names, 0, 3)
}

########################################
# Public Subnets (3)
########################################

resource "aws_subnet" "public" {
  for_each          = toset(local.azs)
  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  # carve unique /24s (or as per subnet_newbits) for public subnets
  cidr_block              = cidrsubnet(var.vpc_cidr, var.subnet_newbits, index(local.azs, each.key))
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-public-${each.key}"
    Tier = "public"
  })
}

########################################
# Private Subnets (3)
########################################

resource "aws_subnet" "private" {
  for_each          = toset(local.azs)
  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  # offset the index by +10 for private blocks to avoid overlap with public
  cidr_block = cidrsubnet(var.vpc_cidr, var.subnet_newbits, index(local.azs, each.key) + 10)

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-private-${each.key}"
    Tier = "private"
  })
}

########################################
# Route Tables
########################################

# Public route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.vpc_name}-public-rt" })
}

# Default internet route for public RT
resource "aws_route" "public_inet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

# Private route table
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
  tags   = merge(var.tags, { Name = "${var.vpc_name}-private-rt" })
}

########################################
# Route Table Associations
########################################

# Public subnets -> public route table
resource "aws_route_table_association" "public_assoc" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# Private subnets -> private route table
resource "aws_route_table_association" "private_assoc" {
  for_each       = aws_subnet.private
  subnet_id      = each.value.id
  route_table_id = aws_route_table.private.id
}

resource "random_uuid" "s3_suffix" {}

locals {
  # Generate a unique S3 bucket name
  s3_bucket_name = "csye6225-images-${random_uuid.s3_suffix.result}"
}
