output "public_ip" {
  description = "Elastic IP of the Labari EC2 instance"
  value       = aws_eip.labari.public_ip
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.labari.id
}

output "domain" {
  description = "Application domain"
  value       = var.domain_name
}
