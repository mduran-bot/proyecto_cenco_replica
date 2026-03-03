# ============================================================================
# VPC Module
# Creates VPC, Subnets, Internet Gateway, NAT Gateway, and Route Tables
# ============================================================================

# ============================================================================
# VPC
# ============================================================================

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-vpc"
    Component = "vpc"
  })
}

# ============================================================================
# Subnets - Availability Zone A (us-east-1a)
# ============================================================================

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-public-subnet-a"
    Component = "subnet"
    Tier      = "public"
    Purpose   = "nat-gateway-api-gateway"
  })
}

resource "aws_subnet" "private_1a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_1a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = false

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-private-subnet-1a"
    Component = "subnet"
    Tier      = "private"
    Purpose   = "lambda-mwaa-redshift"
  })
}

resource "aws_subnet" "private_2a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_2a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = false

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-private-subnet-2a"
    Component = "subnet"
    Tier      = "private"
    Purpose   = "glue-enis"
  })
}

# ============================================================================
# Subnets - Availability Zone B (us-east-1b) - Only if Multi-AZ enabled
# ============================================================================
#
# RESERVED CIDR BLOCKS FOR FUTURE MULTI-AZ EXPANSION:
# - Public Subnet B: 10.0.2.0/24 (us-east-1b) - RESERVED
# - Private Subnet 1B: 10.0.11.0/24 (us-east-1b) - RESERVED
# - Private Subnet 2B: 10.0.21.0/24 (us-east-1b) - RESERVED
#
# These subnets are created ONLY when enable_multi_az = true
# DO NOT use these CIDR blocks for any other purpose
#
# For migration instructions, see: terraform/MULTI_AZ_EXPANSION.md
# ============================================================================

resource "aws_subnet" "public_b" {
  count = var.enable_multi_az ? 1 : 0

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_b_cidr
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-public-subnet-b"
    Component = "subnet"
    Tier      = "public"
    Purpose   = "nat-gateway-api-gateway"
  })
}

resource "aws_subnet" "private_1b" {
  count = var.enable_multi_az ? 1 : 0

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_1b_cidr
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = false

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-private-subnet-1b"
    Component = "subnet"
    Tier      = "private"
    Purpose   = "lambda-mwaa-redshift"
  })
}

resource "aws_subnet" "private_2b" {
  count = var.enable_multi_az ? 1 : 0

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_2b_cidr
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = false

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-private-subnet-2b"
    Component = "subnet"
    Tier      = "private"
    Purpose   = "glue-enis"
  })
}

# ============================================================================
# Internet Gateway
# ============================================================================

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-igw"
    Component = "internet-gateway"
  })
}

# ============================================================================
# Elastic IPs for NAT Gateways
# ============================================================================

resource "aws_eip" "nat_a" {
  domain = "vpc"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-nat-eip-a"
    Component = "elastic-ip"
  })

  depends_on = [aws_internet_gateway.main]
}

resource "aws_eip" "nat_b" {
  count = var.enable_multi_az ? 1 : 0

  domain = "vpc"

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-nat-eip-b"
    Component = "elastic-ip"
  })

  depends_on = [aws_internet_gateway.main]
}

# ============================================================================
# NAT Gateways
# ============================================================================

resource "aws_nat_gateway" "main_a" {
  allocation_id = aws_eip.nat_a.id
  subnet_id     = aws_subnet.public_a.id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-nat-gateway-a"
    Component = "nat-gateway"
  })

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main_b" {
  count = var.enable_multi_az ? 1 : 0

  allocation_id = aws_eip.nat_b[0].id
  subnet_id     = aws_subnet.public_b[0].id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-nat-gateway-b"
    Component = "nat-gateway"
  })

  depends_on = [aws_internet_gateway.main]
}

# ============================================================================
# Route Tables
# ============================================================================

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-public-rt"
    Component = "route-table"
    Tier      = "public"
  })
}

# Private Route Table for AZ A
resource "aws_route_table" "private_a" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main_a.id
  }

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-private-rt-a"
    Component = "route-table"
    Tier      = "private"
  })
}

# Private Route Table for AZ B (Multi-AZ only)
resource "aws_route_table" "private_b" {
  count = var.enable_multi_az ? 1 : 0

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main_b[0].id
  }

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-private-rt-b"
    Component = "route-table"
    Tier      = "private"
  })
}

# ============================================================================
# Route Table Associations
# ============================================================================

# Public Subnet A
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

# Public Subnet B (Multi-AZ only)
resource "aws_route_table_association" "public_b" {
  count = var.enable_multi_az ? 1 : 0

  subnet_id      = aws_subnet.public_b[0].id
  route_table_id = aws_route_table.public.id
}

# Private Subnet 1A
resource "aws_route_table_association" "private_1a" {
  subnet_id      = aws_subnet.private_1a.id
  route_table_id = aws_route_table.private_a.id
}

# Private Subnet 2A
resource "aws_route_table_association" "private_2a" {
  subnet_id      = aws_subnet.private_2a.id
  route_table_id = aws_route_table.private_a.id
}

# Private Subnet 1B (Multi-AZ only)
resource "aws_route_table_association" "private_1b" {
  count = var.enable_multi_az ? 1 : 0

  subnet_id      = aws_subnet.private_1b[0].id
  route_table_id = aws_route_table.private_b[0].id
}

# Private Subnet 2B (Multi-AZ only)
resource "aws_route_table_association" "private_2b" {
  count = var.enable_multi_az ? 1 : 0

  subnet_id      = aws_subnet.private_2b[0].id
  route_table_id = aws_route_table.private_b[0].id
}
