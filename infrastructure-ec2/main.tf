terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}

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

resource "aws_security_group" "labari" {
  name        = "labari-ec2"
  description = "Labari application security group"

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "labari-ec2"
    Environment = var.environment
  }
}

resource "aws_instance" "labari" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.labari.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y curl
  EOF

  tags = {
    Name        = "labari-prod"
    Environment = var.environment
    Project     = "labari"
  }
}

data "aws_eip" "labari" {
  id = var.eip_allocation_id
}

resource "aws_eip_association" "labari" {
  instance_id   = aws_instance.labari.id
  allocation_id = data.aws_eip.labari.id
}

resource "aws_route53_record" "labari" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 60
  records = [data.aws_eip.labari.public_ip]
}

resource "aws_route53_record" "labari_www" {
  zone_id = var.hosted_zone_id
  name    = "www.${var.domain_name}"
  type    = "A"
  ttl     = 60
  records = [data.aws_eip.labari.public_ip]
}
