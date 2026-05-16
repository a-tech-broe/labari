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

# ── Data sources ─────────────────────────────────────────────────────────────

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
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

data "aws_eip" "labari" {
  id = var.eip_allocation_id
}

# ── ACM certificate (DNS-validated via Route 53) ──────────────────────────────

resource "aws_acm_certificate" "labari" {
  domain_name               = var.domain_name
  subject_alternative_names = ["www.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "labari"
    Environment = var.environment
  }
}

resource "aws_route53_record" "labari_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.labari.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.hosted_zone_id
}

resource "aws_acm_certificate_validation" "labari" {
  certificate_arn         = aws_acm_certificate.labari.arn
  validation_record_fqdns = [for r in aws_route53_record.labari_cert_validation : r.fqdn]
}

# ── Security groups ───────────────────────────────────────────────────────────

resource "aws_security_group" "alb" {
  name        = "labari-alb"
  description = "Labari ALB — internet-facing HTTP/HTTPS"
  vpc_id      = data.aws_vpc.default.id

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

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "labari-alb"
    Environment = var.environment
  }
}

resource "aws_security_group" "labari" {
  name        = "labari-ec2"
  description = "Labari EC2 — HTTP from ALB only, SSH from anywhere"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
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

# ── EC2 instance ──────────────────────────────────────────────────────────────

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
    set -e
    apt-get update -y
    apt-get install -y curl
  EOF

  tags = {
    Name        = "labari-prod"
    Environment = var.environment
    Project     = "labari"
  }
}

resource "aws_eip_association" "labari" {
  instance_id   = aws_instance.labari.id
  allocation_id = data.aws_eip.labari.id
}

# ── Application Load Balancer ─────────────────────────────────────────────────

resource "aws_lb" "labari" {
  name               = "labari"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids

  tags = {
    Name        = "labari"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "labari" {
  name     = "labari"
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 5
    interval            = 10
    matcher             = "200"
  }

  tags = {
    Name        = "labari"
    Environment = var.environment
  }
}

resource "aws_lb_target_group_attachment" "labari" {
  target_group_arn = aws_lb_target_group.labari.arn
  target_id        = aws_instance.labari.id
  port             = 80
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.labari.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.labari.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.labari.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.labari.arn
  }
}

# ── Route 53 — ALIAS to ALB ───────────────────────────────────────────────────

resource "aws_route53_record" "labari" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.labari.dns_name
    zone_id                = aws_lb.labari.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "labari_www" {
  zone_id = var.hosted_zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_lb.labari.dns_name
    zone_id                = aws_lb.labari.zone_id
    evaluate_target_health = true
  }
}
