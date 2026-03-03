# ============================================================================
# SNS Module Outputs
# ============================================================================

output "topic_arn" {
  description = "ARN of the SNS topic"
  value       = aws_sns_topic.error_notifications.arn
}

output "topic_id" {
  description = "ID of the SNS topic"
  value       = aws_sns_topic.error_notifications.id
}

output "topic_name" {
  description = "Name of the SNS topic"
  value       = aws_sns_topic.error_notifications.name
}

output "topic_owner" {
  description = "AWS account ID of the SNS topic owner"
  value       = aws_sns_topic.error_notifications.owner
}

output "email_subscription_arns" {
  description = "ARNs of email subscriptions"
  value       = aws_sns_topic_subscription.email[*].arn
}

output "sqs_subscription_arns" {
  description = "ARNs of SQS subscriptions"
  value       = aws_sns_topic_subscription.sqs[*].arn
}

output "lambda_subscription_arns" {
  description = "ARNs of Lambda subscriptions"
  value       = aws_sns_topic_subscription.lambda[*].arn
}
