variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "mwaa_environment_arn" {
  description = "ARN of MWAA environment"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "order_polling_rate" {
  description = "Polling frequency for orders (e.g., '5 minutes')"
  type        = string
  default     = "5 minutes"
}

variable "catalog_polling_rate" {
  description = "Polling frequency for catalog (products, SKUs, categories, brands) (e.g., '1 hour')"
  type        = string
  default     = "1 hour"
}

variable "stock_polling_rate" {
  description = "Polling frequency for stock (e.g., '10 minutes')"
  type        = string
  default     = "10 minutes"
}

variable "price_polling_rate" {
  description = "Polling frequency for prices (e.g., '30 minutes')"
  type        = string
  default     = "30 minutes"
}

variable "store_polling_rate" {
  description = "Polling frequency for stores (e.g., '1 day')"
  type        = string
  default     = "1 day"
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
