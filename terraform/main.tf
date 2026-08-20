# ============================================================
# CHAOS TYPE ZERO — Terraform Main (AWS)
# ============================================================
# Deploy CTZ on AWS EC2 with VPC, Security Group, and Storage

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "ctz-terraform-state"
    key    = "chaos-type-zero/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# ============================================================
# DATA SOURCES
# ============================================================
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ============================================================
# VPC
# ============================================================
resource "aws_vpc" "ctz_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "ctz_igw" {
  vpc_id = aws_vpc.ctz_vpc.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "ctz_public" {
  vpc_id                  = aws_vpc.ctz_vpc.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public"
  }
}

resource "aws_route_table" "ctz_public" {
  vpc_id = aws_vpc.ctz_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ctz_igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "ctz_public" {
  subnet_id      = aws_subnet.ctz_public.id
  route_table_id = aws_route_table.ctz_public.id
}

# ============================================================
# SECURITY GROUP
# ============================================================
resource "aws_security_group" "ctz_sg" {
  name        = "${var.project_name}-sg"
  description = "CTZ Security Group"
  vpc_id      = aws_vpc.ctz_vpc.id

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  # Dashboard
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # API
  ingress {
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Slack Bot
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Grafana
  ingress {
    from_port   = 3001
    to_port     = 3001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# ============================================================
# EC2 INSTANCE
# ============================================================
resource "aws_instance" "ctz_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.ctz_sg.id]
  subnet_id              = aws_subnet.ctz_public.id

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = templatefile("${path.module}/user_data.sh", {
    db_password = var.db_password
  })

  tags = {
    Name = "${var.project_name}-server"
  }
}

# ============================================================
# EBS VOLUME (Data)
# ============================================================
resource "aws_ebs_volume" "ctz_data" {
  availability_zone = "${var.aws_region}a"
  size              = 100
  type              = "gp3"
  encrypted         = true

  tags = {
    Name = "${var.project_name}-data"
  }
}

resource "aws_volume_attachment" "ctz_data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.ctz_data.id
  instance_id = aws_instance.ctz_server.id
}

# ============================================================
# S3 BUCKET (Backups)
# ============================================================
resource "aws_s3_bucket" "ctz_backups" {
  bucket = "${var.project_name}-backups-${var.environment}"

  tags = {
    Name = "${var.project_name}-backups"
  }
}

resource "aws_s3_bucket_versioning" "ctz_backups" {
  bucket = aws_s3_bucket.ctz_backups.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ctz_backups" {
  bucket = aws_s3_bucket.ctz_backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ============================================================
# CLOUDWATCH
# ============================================================
resource "aws_cloudwatch_metric_alarm" "ctz_cpu" {
  alarm_name          = "${var.project_name}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CTZ CPU utilization > 80%"
  alarm_actions       = []

  dimensions = {
    InstanceId = aws_instance.ctz_server.id
  }
}

# ============================================================
# OUTPUTS
# ============================================================
output "instance_public_ip" {
  description = "CTZ server public IP"
  value       = aws_instance.ctz_server.public_ip
}

output "instance_public_dns" {
  description = "CTZ server public DNS"
  value       = aws_instance.ctz_server.public_dns
}

output "dashboard_url" {
  description = "CTZ Dashboard URL"
  value       = "http://${aws_instance.ctz_server.public_ip}:8080"
}

output "api_url" {
  description = "CTZ API URL"
  value       = "http://${aws_instance.ctz_server.public_ip}:8081"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://${aws_instance.ctz_server.public_ip}:9090"
}

output "s3_bucket_name" {
  description = "Backup S3 bucket"
  value       = aws_s3_bucket.ctz_backups.id
}
