variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "rate_limit" {
  description = "Rate limit (requests per IP in 5 minutes)"
  type        = number
}

variable "allowed_countries" {
  description = "List of country codes allowed by geo-blocking"
  type        = list(string)
}

variable "nat_gateway_id" {
  description = "NAT Gateway ID for monitoring"
  type        = string
  default     = ""
}