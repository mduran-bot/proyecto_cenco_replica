#!/bin/bash
# ============================================================================
# EventBridge Configuration Validation Script
# ============================================================================
# This script validates that EventBridge rules are properly configured
# for the API polling system

set -e

echo "=========================================="
echo "EventBridge Configuration Validation"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAME_PREFIX="janis-cencosud"
EXPECTED_RULES=5

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
    exit 1
fi
print_success "AWS CLI is installed"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials are not configured"
    exit 1
fi
print_success "AWS credentials are configured"

echo ""
echo "Checking EventBridge Rules..."
echo "------------------------------"

# List all polling rules
RULES=$(aws events list-rules --name-prefix "${NAME_PREFIX}-poll" --query 'Rules[].Name' --output text)

if [ -z "$RULES" ]; then
    print_error "No EventBridge rules found with prefix ${NAME_PREFIX}-poll"
    exit 1
fi

RULE_COUNT=$(echo "$RULES" | wc -w)
if [ "$RULE_COUNT" -eq "$EXPECTED_RULES" ]; then
    print_success "Found $RULE_COUNT EventBridge rules (expected $EXPECTED_RULES)"
else
    print_warning "Found $RULE_COUNT EventBridge rules (expected $EXPECTED_RULES)"
fi

# Check each rule
DATA_TYPES=("orders" "products" "stock" "prices" "stores")
EXPECTED_SCHEDULES=("rate(5 minutes)" "rate(1 hour)" "rate(10 minutes)" "rate(30 minutes)" "rate(1 day)")

for i in "${!DATA_TYPES[@]}"; do
    DATA_TYPE="${DATA_TYPES[$i]}"
    EXPECTED_SCHEDULE="${EXPECTED_SCHEDULES[$i]}"
    RULE_NAME="${NAME_PREFIX}-poll-${DATA_TYPE}-schedule"
    
    echo ""
    echo "Checking rule: $RULE_NAME"
    
    # Check if rule exists
    RULE_INFO=$(aws events describe-rule --name "$RULE_NAME" 2>/dev/null || echo "")
    
    if [ -z "$RULE_INFO" ]; then
        print_error "Rule $RULE_NAME not found"
        continue
    fi
    print_success "Rule exists"
    
    # Check schedule expression
    SCHEDULE=$(echo "$RULE_INFO" | jq -r '.ScheduleExpression')
    if [ "$SCHEDULE" == "$EXPECTED_SCHEDULE" ]; then
        print_success "Schedule is correct: $SCHEDULE"
    else
        print_error "Schedule is incorrect. Expected: $EXPECTED_SCHEDULE, Got: $SCHEDULE"
    fi
    
    # Check rule state
    STATE=$(echo "$RULE_INFO" | jq -r '.State')
    if [ "$STATE" == "ENABLED" ]; then
        print_success "Rule is enabled"
    else
        print_warning "Rule is disabled"
    fi
    
    # Check targets
    TARGETS=$(aws events list-targets-by-rule --rule "$RULE_NAME" --query 'Targets[].Arn' --output text)
    if [ -n "$TARGETS" ]; then
        print_success "Rule has targets configured"
        
        # Check target input
        TARGET_INPUT=$(aws events list-targets-by-rule --rule "$RULE_NAME" --query 'Targets[0].Input' --output text)
        if echo "$TARGET_INPUT" | jq -e ".dag_id == \"poll_${DATA_TYPE}\"" &> /dev/null; then
            print_success "Target input has correct dag_id"
        else
            print_error "Target input dag_id is incorrect"
        fi
        
        if echo "$TARGET_INPUT" | jq -e ".conf.data_type == \"${DATA_TYPE}\"" &> /dev/null; then
            print_success "Target input has correct data_type in conf"
        else
            print_error "Target input data_type is incorrect"
        fi
    else
        print_error "Rule has no targets configured"
    fi
done

echo ""
echo "Checking IAM Role..."
echo "--------------------"

# Check IAM role
ROLE_NAME="${NAME_PREFIX}-eventbridge-mwaa-role"
ROLE_INFO=$(aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null || echo "")

if [ -n "$ROLE_INFO" ]; then
    print_success "IAM role exists: $ROLE_NAME"
    
    # Check assume role policy
    ASSUME_ROLE_POLICY=$(echo "$ROLE_INFO" | jq -r '.Role.AssumeRolePolicyDocument')
    if echo "$ASSUME_ROLE_POLICY" | jq -e '.Statement[].Principal.Service | contains("events.amazonaws.com")' &> /dev/null; then
        print_success "IAM role has correct trust policy for EventBridge"
    else
        print_error "IAM role trust policy is incorrect"
    fi
    
    # Check inline policies
    POLICY_NAME="${NAME_PREFIX}-eventbridge-mwaa-policy"
    POLICY_INFO=$(aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME" 2>/dev/null || echo "")
    
    if [ -n "$POLICY_INFO" ]; then
        print_success "IAM policy exists: $POLICY_NAME"
        
        # Check for airflow:CreateCliToken permission
        if echo "$POLICY_INFO" | jq -e '.PolicyDocument.Statement[].Action | contains(["airflow:CreateCliToken"])' &> /dev/null; then
            print_success "IAM policy has airflow:CreateCliToken permission"
        else
            print_error "IAM policy missing airflow:CreateCliToken permission"
        fi
    else
        print_error "IAM policy not found: $POLICY_NAME"
    fi
else
    print_error "IAM role not found: $ROLE_NAME"
fi

echo ""
echo "Checking Dead Letter Queue..."
echo "------------------------------"

# Check DLQ
DLQ_NAME="${NAME_PREFIX}-eventbridge-dlq"
DLQ_URL=$(aws sqs get-queue-url --queue-name "$DLQ_NAME" --query 'QueueUrl' --output text 2>/dev/null || echo "")

if [ -n "$DLQ_URL" ]; then
    print_success "Dead Letter Queue exists: $DLQ_NAME"
    
    # Check message count
    MSG_COUNT=$(aws sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names ApproximateNumberOfMessages --query 'Attributes.ApproximateNumberOfMessages' --output text)
    if [ "$MSG_COUNT" -eq 0 ]; then
        print_success "DLQ is empty (no failed invocations)"
    else
        print_warning "DLQ has $MSG_COUNT messages (failed invocations detected)"
    fi
else
    print_error "Dead Letter Queue not found: $DLQ_NAME"
fi

echo ""
echo "Checking CloudWatch Log Group..."
echo "---------------------------------"

# Check log group
LOG_GROUP_NAME="/aws/events/${NAME_PREFIX}-polling"
LOG_GROUP_INFO=$(aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP_NAME" --query 'logGroups[0]' 2>/dev/null || echo "")

if [ -n "$LOG_GROUP_INFO" ]; then
    print_success "CloudWatch Log Group exists: $LOG_GROUP_NAME"
    
    RETENTION=$(echo "$LOG_GROUP_INFO" | jq -r '.retentionInDays')
    if [ "$RETENTION" == "90" ]; then
        print_success "Log retention is set to 90 days"
    else
        print_warning "Log retention is $RETENTION days (expected 90)"
    fi
else
    print_error "CloudWatch Log Group not found: $LOG_GROUP_NAME"
fi

echo ""
echo "=========================================="
echo "Validation Complete"
echo "=========================================="
