# ============================================================================
# EventBridge Module - Variables
# ============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "mwaa_environment_arn" {
  description = "ARN of the MWAA environment to trigger"
  type        = string
}

variable "clients" {
  description = "List of client identifiers (metro, wongio, etc.)"
  type        = list(string)
}

variable "polling_rates" {
  description = "Polling rates per data type (in minutes for orders/stock/prices, in hours for products/stores)"
  type = object({
    orders   = number  # minutes
    stock    = number  # minutes
    prices   = number  # minutes
    products = number  # hours
    stores   = number  # hours
  })
  default = {
    orders   = 5      # cada 5 minutos
    stock    = 10     # cada 10 minutos
    prices   = 30     # cada 30 minutos
    products = 1      # cada 1 hora
    stores   = 24     # cada 24 horas
  }
}

variable "eventbridge_role_arn" {
  description = "ARN of existing IAM role for EventBridge to trigger MWAA"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
