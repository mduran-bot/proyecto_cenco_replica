# ============================================================================
# EventBridge Module - Scheduled Triggers for MWAA DAGs
# ============================================================================
# NOTA: Este módulo NO crea roles IAM, usa un rol existente proporcionado

# ============================================================================
# EventBridge Rules - One per client per data type
# ============================================================================

# Orders Polling Rules (one per client) - Every 5 minutes
resource "aws_cloudwatch_event_rule" "poll_orders" {
  for_each = toset(var.clients)
  
  name                = "${var.name_prefix}-poll-orders-${each.key}"
  description         = "Trigger orders polling DAG for ${each.key} every ${var.polling_rates.orders} minutes"
  schedule_expression = "rate(${var.polling_rates.orders} minutes)"
  
  tags = merge(var.tags, {
    Client   = each.key
    DataType = "orders"
  })
}

resource "aws_cloudwatch_event_target" "poll_orders" {
  for_each = toset(var.clients)
  
  rule      = aws_cloudwatch_event_rule.poll_orders[each.key].name
  target_id = "TriggerMWAADAG"
  arn       = var.mwaa_environment_arn
  role_arn  = var.eventbridge_role_arn  # Usar rol existente
  
  input = jsonencode({
    dag_name = "poll_orders_${each.key}"
    conf     = {
      client    = each.key
      data_type = "orders"
    }
  })
}

# Products Polling Rules (one per client) - Every 1 hour
resource "aws_cloudwatch_event_rule" "poll_products" {
  for_each = toset(var.clients)
  
  name                = "${var.name_prefix}-poll-products-${each.key}"
  description         = "Trigger products polling DAG for ${each.key} every ${var.polling_rates.products} hour(s)"
  schedule_expression = "rate(${var.polling_rates.products} hour${var.polling_rates.products > 1 ? "s" : ""})"
  
  tags = merge(var.tags, {
    Client   = each.key
    DataType = "products"
  })
}

resource "aws_cloudwatch_event_target" "poll_products" {
  for_each = toset(var.clients)
  
  rule      = aws_cloudwatch_event_rule.poll_products[each.key].name
  target_id = "TriggerMWAADAG"
  arn       = var.mwaa_environment_arn
  role_arn  = var.eventbridge_role_arn  # Usar rol existente
  
  input = jsonencode({
    dag_name = "poll_products_${each.key}"
    conf     = {
      client    = each.key
      data_type = "products"
    }
  })
}

# Stock Polling Rules (one per client) - Every 10 minutes
resource "aws_cloudwatch_event_rule" "poll_stock" {
  for_each = toset(var.clients)
  
  name                = "${var.name_prefix}-poll-stock-${each.key}"
  description         = "Trigger stock polling DAG for ${each.key} every ${var.polling_rates.stock} minutes"
  schedule_expression = "rate(${var.polling_rates.stock} minutes)"
  
  tags = merge(var.tags, {
    Client   = each.key
    DataType = "stock"
  })
}

resource "aws_cloudwatch_event_target" "poll_stock" {
  for_each = toset(var.clients)
  
  rule      = aws_cloudwatch_event_rule.poll_stock[each.key].name
  target_id = "TriggerMWAADAG"
  arn       = var.mwaa_environment_arn
  role_arn  = var.eventbridge_role_arn  # Usar rol existente
  
  input = jsonencode({
    dag_name = "poll_stock_${each.key}"
    conf     = {
      client    = each.key
      data_type = "stock"
    }
  })
}

# Prices Polling Rules (one per client) - Every 30 minutes
resource "aws_cloudwatch_event_rule" "poll_prices" {
  for_each = toset(var.clients)
  
  name                = "${var.name_prefix}-poll-prices-${each.key}"
  description         = "Trigger prices polling DAG for ${each.key} every ${var.polling_rates.prices} minutes"
  schedule_expression = "rate(${var.polling_rates.prices} minutes)"
  
  tags = merge(var.tags, {
    Client   = each.key
    DataType = "prices"
  })
}

resource "aws_cloudwatch_event_target" "poll_prices" {
  for_each = toset(var.clients)
  
  rule      = aws_cloudwatch_event_rule.poll_prices[each.key].name
  target_id = "TriggerMWAADAG"
  arn       = var.mwaa_environment_arn
  role_arn  = var.eventbridge_role_arn  # Usar rol existente
  
  input = jsonencode({
    dag_name = "poll_prices_${each.key}"
    conf     = {
      client    = each.key
      data_type = "prices"
    }
  })
}

# Stores Polling Rules (one per client) - Every 24 hours
resource "aws_cloudwatch_event_rule" "poll_stores" {
  for_each = toset(var.clients)
  
  name                = "${var.name_prefix}-poll-stores-${each.key}"
  description         = "Trigger stores polling DAG for ${each.key} every ${var.polling_rates.stores} hour(s)"
  schedule_expression = "rate(${var.polling_rates.stores} hour${var.polling_rates.stores > 1 ? "s" : ""})"
  
  tags = merge(var.tags, {
    Client   = each.key
    DataType = "stores"
  })
}

resource "aws_cloudwatch_event_target" "poll_stores" {
  for_each = toset(var.clients)
  
  rule      = aws_cloudwatch_event_rule.poll_stores[each.key].name
  target_id = "TriggerMWAADAG"
  arn       = var.mwaa_environment_arn
  role_arn  = var.eventbridge_role_arn  # Usar rol existente
  
  input = jsonencode({
    dag_name = "poll_stores_${each.key}"
    conf     = {
      client    = each.key
      data_type = "stores"
    }
  })
}
