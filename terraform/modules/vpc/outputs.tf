output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = var.enable_multi_az ? [aws_subnet.public_a.id, aws_subnet.public_b[0].id] : [aws_subnet.public_a.id]
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value = var.enable_multi_az ? [
    aws_subnet.private_1a.id,
    aws_subnet.private_2a.id,
    aws_subnet.private_1b[0].id,
    aws_subnet.private_2b[0].id
    ] : [
    aws_subnet.private_1a.id,
    aws_subnet.private_2a.id
  ]
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway in AZ A"
  value       = aws_nat_gateway.main_a.id
}

output "nat_gateway_public_ip" {
  description = "Public IP of the NAT Gateway in AZ A"
  value       = aws_eip.nat_a.public_ip
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "route_table_ids" {
  description = "IDs of all route tables"
  value = var.enable_multi_az ? [
    aws_route_table.public.id,
    aws_route_table.private_a.id,
    aws_route_table.private_b[0].id
    ] : [
    aws_route_table.public.id,
    aws_route_table.private_a.id
  ]
}

output "availability_zones" {
  description = "Availability zones used"
  value       = var.enable_multi_az ? ["${var.aws_region}a", "${var.aws_region}b"] : ["${var.aws_region}a"]
}
