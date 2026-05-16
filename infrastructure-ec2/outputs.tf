output "public_ip" {
  description = "Elastic IP of the Labari EC2 instance (SSH access)"
  value       = data.aws_eip.labari.public_ip
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.labari.id
}

output "alb_dns_name" {
  description = "ALB DNS name (used for health checks and debugging)"
  value       = aws_lb.labari.dns_name
}

output "domain" {
  description = "Application domain"
  value       = "https://${var.domain_name}"
}
