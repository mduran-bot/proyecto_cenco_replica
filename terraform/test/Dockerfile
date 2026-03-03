# Dockerfile for running Terraform property-based tests
# This provides a containerized environment with Go and Terraform

FROM golang:1.21-alpine

# Install Terraform and other dependencies
RUN apk add --no-cache \
    terraform \
    git \
    bash \
    curl

# Set working directory
WORKDIR /workspace

# Copy go module files
COPY go.mod go.sum* ./

# Download dependencies
RUN go mod download

# Copy test files
COPY . .

# Default command runs all tests
CMD ["go", "test", "-v", "-timeout", "30m"]
