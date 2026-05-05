terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ====================== ENVIRONMENT ======================
variable "environment" {
  description = "Environment name: dev or prod"
  type        = string
  default     = "prod"
}

locals {
  common_tags = {
    Project     = "tayyib"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ====================== VPC ======================
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = merge(local.common_tags, {
    Name = "tayyib-vpc-${var.environment}"
  })
}

# ====================== SUBNETS ======================
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags = merge(local.common_tags, {
    Name = "tayyib-public-subnet-${var.environment}"
  })
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}a"
  tags = merge(local.common_tags, {
    Name = "tayyib-private-subnet-a-${var.environment}"
  })
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "${var.aws_region}b"
  tags = merge(local.common_tags, {
    Name = "tayyib-private-subnet-b-${var.environment}"
  })
}

# ====================== INTERNET GATEWAY ======================
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = merge(local.common_tags, {
    Name = "tayyib-igw-${var.environment}"
  })
}

# ====================== ROUTE TABLE ======================
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = merge(local.common_tags, {
    Name = "tayyib-public-rt-${var.environment}"
  })
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ====================== SECURITY GROUPS ======================
resource "aws_security_group" "ec2" {
  name   = "tayyib-ec2-sg-${var.environment}"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "tayyib-ec2-sg-${var.environment}"
  })
}

resource "aws_security_group" "rds" {
  name   = "tayyib-rds-sg-${var.environment}"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "tayyib-rds-sg-${var.environment}"
  })
}

# ====================== KEY PAIR ======================
resource "aws_key_pair" "tayyib" {
  key_name   = "tayyib-key-${var.environment}"
  public_key = file(var.ssh_public_key_path)
  tags       = local.common_tags
}

# ====================== EC2 INSTANCE ======================
resource "aws_instance" "app" {
  ami                    = var.ec2_ami
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name               = aws_key_pair.tayyib.key_name

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y docker.io docker-compose-plugin git
    systemctl start docker
    systemctl enable docker
    usermod -aG docker ubuntu
  EOF

  tags = merge(local.common_tags, {
    Name = "tayyib-app-server-${var.environment}"
  })
}

# ====================== ELASTIC IP ======================
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"
  tags = merge(local.common_tags, {
    Name = "tayyib-eip-${var.environment}"
  })
}

# ====================== RDS ======================
resource "aws_db_subnet_group" "main" {
  name       = "tayyib-db-subnet-group-${var.environment}"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  tags = merge(local.common_tags, {
    Name = "tayyib-db-subnet-group-${var.environment}"
  })
}

resource "aws_db_instance" "postgres" {
  identifier             = "tayyib-db-${var.environment}"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_type           = "gp2"
  db_name                = var.db_name
  username               = var.db_user
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true
  publicly_accessible    = false

  tags = merge(local.common_tags, {
    Name = "tayyib-db-${var.environment}"
  })
}
