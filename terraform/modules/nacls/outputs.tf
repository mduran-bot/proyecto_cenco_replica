output "public_nacl_id" {
  description = "ID of public subnet NACL"
  value       = aws_network_acl.public.id
}

output "private_nacl_id" {
  description = "ID of private subnet NACL"
  value       = aws_network_acl.private.id
}
