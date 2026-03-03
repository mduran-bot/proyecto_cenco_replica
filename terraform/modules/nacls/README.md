# Network ACLs (NACLs) Module

## Overview

This module creates Network Access Control Lists (NACLs) for public and private subnets in the VPC. NACLs provide stateless, subnet-level network filtering as an additional layer of security beyond Security Groups.

## Architecture

### Design Pattern

The module uses **explicit NACL associations** rather than inline `subnet_ids` to provide better control and avoid Terraform state conflicts:

```hcl
# NACL resource (without subnet_ids)
resource "aws_network_acl" "public" {
  vpc_id = var.vpc_id
  tags   = merge(var.tags, {...})
}

# Explicit associations (one per subnet)
resource "aws_network_acl_association" "public" {
  count          = length(var.public_subnet_ids)
  network_acl_id = aws_network_acl.public.id
  subnet_id      = var.public_subnet_ids[count.index]
}
```

### Why Explicit Associations?

**Benefits:**
- ✅ **Cleaner state management**: Each association is a separate resource
- ✅ **Better change tracking**: Terraform can track individual subnet associations
- ✅ **Reduced conflicts**: Avoids race conditions when multiple subnets are modified
- ✅ **Easier debugging**: Clear visibility of which subnets are associated
- ✅ **AWS best practice**: Aligns with AWS recommended patterns

**Previous Approach (Deprecated):**
```hcl
# Old pattern - can cause state conflicts
resource "aws_network_acl" "public" {
  vpc_id     = var.vpc_id
  subnet_ids = var.public_subnet_ids  # Inline - harder to manage
}
```

## Resources Created

### Public Subnet NACL

**Purpose**: Controls traffic for public subnets (NAT Gateway, future load balancers)

**Inbound Rules:**
- Rule 100: HTTPS (443) from 0.0.0.0/0
- Rule 110: Ephemeral ports (1024-65535) from 0.0.0.0/0

**Outbound Rules:**
- Rule 100: All traffic to 0.0.0.0/0

**Resources:**
- `aws_network_acl.public` - The NACL resource
- `aws_network_acl_association.public[*]` - One association per public subnet

### Private Subnet NACL

**Purpose**: Controls traffic for private subnets (Lambda, Glue, MWAA, Redshift)

**Inbound Rules:**
- Rule 100: All traffic from VPC CIDR (10.0.0.0/16)
- Rule 110: HTTPS (443) from 0.0.0.0/0 (for VPC endpoints)
- Rule 120: Ephemeral ports (1024-65535) from 0.0.0.0/0

**Outbound Rules:**
- Rule 100: All traffic to VPC CIDR (10.0.0.0/16)
- Rule 110: HTTPS (443) to 0.0.0.0/0 (for VPC endpoints)

**Resources:**
- `aws_network_acl.private` - The NACL resource
- `aws_network_acl_association.private[*]` - One association per private subnet

## Usage

```hcl
module "nacls" {
  source = "./modules/nacls"

  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = var.vpc_cidr
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  name_prefix        = local.name_prefix

  tags = local.all_tags
}
```

## Variables

| Name | Type | Description | Required |
|------|------|-------------|----------|
| `vpc_id` | string | ID of the VPC | Yes |
| `vpc_cidr` | string | CIDR block of the VPC | Yes |
| `public_subnet_ids` | list(string) | List of public subnet IDs | Yes |
| `private_subnet_ids` | list(string) | List of private subnet IDs | Yes |
| `name_prefix` | string | Prefix for resource names | Yes |
| `tags` | map(string) | Common tags to apply to all resources | Yes |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| `public_nacl_id` | string | ID of the public subnet NACL |
| `private_nacl_id` | string | ID of the private subnet NACL |

## NACL Rules Explained

### Stateless Nature

Unlike Security Groups, NACLs are **stateless**:
- Return traffic must be explicitly allowed
- Both inbound and outbound rules are required
- Ephemeral ports (1024-65535) must be allowed for return traffic

### Rule Numbering

Rules are evaluated in order from lowest to highest:
- Lower numbers = higher priority
- First matching rule is applied
- Default rule (32767) denies all traffic

### Public Subnet Rules

**Why allow HTTPS inbound?**
- NAT Gateway needs to receive return traffic from internet
- Future load balancers may need to accept HTTPS connections

**Why allow ephemeral ports inbound?**
- Return traffic from internet connections initiated by NAT Gateway
- Required for stateless NACL operation

**Why allow all outbound?**
- NAT Gateway needs to forward traffic to internet
- Simplifies configuration while maintaining security

### Private Subnet Rules

**Why allow all traffic from VPC CIDR?**
- Inter-subnet communication (Lambda ↔ Redshift, Glue ↔ S3 endpoints)
- Simplifies internal networking

**Why allow HTTPS from 0.0.0.0/0?**
- VPC Interface Endpoints receive traffic from AWS services
- Required for Glue, Secrets Manager, CloudWatch Logs endpoints

**Why allow ephemeral ports inbound?**
- Return traffic from VPC endpoints and internet (via NAT)
- Required for stateless NACL operation

**Why restrict outbound to VPC + HTTPS?**
- Private subnets should only communicate within VPC or via VPC endpoints
- HTTPS allows access to VPC endpoints and internet via NAT

## Security Considerations

### Defense in Depth

NACLs provide an additional security layer:
1. **Security Groups** (stateful, instance-level)
2. **NACLs** (stateless, subnet-level) ← This module
3. **WAF** (application-level, managed by client)

### Best Practices

✅ **Do:**
- Use NACLs for subnet-level filtering
- Keep rules simple and well-documented
- Use explicit associations for better state management
- Test rule changes in development first

❌ **Don't:**
- Use NACLs as primary security mechanism (use Security Groups)
- Create overly complex rule sets
- Forget to allow ephemeral ports for return traffic
- Use inline `subnet_ids` (causes state conflicts)

## Multi-AZ Support

The module automatically supports Multi-AZ deployments:
- Associations are created dynamically based on subnet count
- Works with 1-N subnets per NACL
- No code changes needed when expanding to Multi-AZ

```hcl
# Single-AZ (3 subnets)
public_subnet_ids  = [subnet_a]
private_subnet_ids = [subnet_1a, subnet_2a]

# Multi-AZ (6 subnets)
public_subnet_ids  = [subnet_a, subnet_b]
private_subnet_ids = [subnet_1a, subnet_2a, subnet_1b, subnet_2b]
```

## Testing

### Property-Based Test

**Property 9: NACL Stateless Bidirectionality**
- Validates that for every inbound rule, there's a corresponding outbound rule
- Ensures ephemeral ports are allowed for return traffic
- Verifies stateless nature is properly handled

**Test File:** `terraform/test/nacl_property_test.go`

### Validation Script

**Script:** `terraform/test/validate_nacl.ps1`

Validates:
- NACL resources exist
- Subnet associations are correct
- Rules are properly configured
- Tags are applied

## Troubleshooting

### Issue: Subnet not associated with NACL

**Symptom:** Subnet uses default NACL instead of custom NACL

**Solution:**
```bash
# Check associations
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=<vpc-id>"

# Verify in Terraform state
terraform state list | grep nacl_association
```

### Issue: Traffic blocked unexpectedly

**Symptom:** Legitimate traffic is denied

**Solution:**
1. Check NACL rules are in correct order
2. Verify ephemeral ports are allowed
3. Ensure both inbound and outbound rules exist
4. Check VPC Flow Logs for denied traffic

### Issue: State conflicts during apply

**Symptom:** Terraform reports conflicts with subnet associations

**Solution:**
- This module uses explicit associations to avoid this issue
- If using old inline pattern, migrate to explicit associations
- Run `terraform refresh` to sync state

## Migration from Inline Pattern

If migrating from inline `subnet_ids` to explicit associations:

```bash
# 1. Remove inline subnet_ids from NACL resource
# 2. Add explicit association resources
# 3. Import existing associations
terraform import 'module.nacls.aws_network_acl_association.public[0]' <association-id>

# 4. Apply changes
terraform apply
```

## Compliance

### Corporate Tagging Policy

All resources include mandatory tags:
- `Application` - Application name
- `Environment` - Environment (dev/qa/prod)
- `Owner` - Team responsible
- `CostCenter` - Cost allocation
- `BusinessUnit` - Business unit
- `Country` - Country code
- `Criticality` - Criticality level

### AWS Well-Architected

Aligns with:
- **Security Pillar**: Defense in depth with subnet-level filtering
- **Reliability Pillar**: Explicit associations for better state management
- **Operational Excellence**: Clear documentation and testing

## References

- [AWS Network ACLs Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html)
- [Terraform aws_network_acl Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/network_acl)
- [Terraform aws_network_acl_association Resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/network_acl_association)
- [VPC Security Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html)

---

**Last Updated:** January 29, 2026  
**Module Version:** 1.1.0  
**Status:** ✅ Production Ready
