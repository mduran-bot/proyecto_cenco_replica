#!/bin/bash
# backup-state.sh
# Automate Terraform state file backups
# Usage: ./backup-state.sh [environment] [--all]

set -e

ENVIRONMENT=$1
BACKUP_ALL=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENTS_DIR="$TERRAFORM_ROOT/environments"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${BLUE}[SUCCESS]${NC} $1"
}

# Parse arguments
if [ "$1" == "--all" ] || [ "$2" == "--all" ]; then
    BACKUP_ALL=true
    ENVIRONMENT=""
fi

# Function to backup a single environment
backup_environment() {
    local env=$1
    local env_dir="$ENVIRONMENTS_DIR/$env"
    local state_file="$env_dir/terraform.tfstate"
    local backup_dir="$env_dir/backups"
    
    if [ ! -d "$env_dir" ]; then
        print_warning "Environment directory does not exist: $env_dir"
        return 1
    fi
    
    if [ ! -f "$state_file" ]; then
        print_warning "No state file found for environment: $env"
        return 1
    fi
    
    # Create backup directory if it doesn't exist
    mkdir -p "$backup_dir"
    
    # Generate backup filename with timestamp
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$backup_dir/terraform.tfstate.backup.$timestamp"
    
    # Copy state file to backup
    cp "$state_file" "$backup_file"
    
    # Get file size
    local file_size=$(du -h "$backup_file" | cut -f1)
    
    print_success "Backed up $env: $backup_file ($file_size)"
    
    # Also backup the backup file if it exists
    if [ -f "$env_dir/terraform.tfstate.backup" ]; then
        local auto_backup_file="$backup_dir/terraform.tfstate.auto-backup.$timestamp"
        cp "$env_dir/terraform.tfstate.backup" "$auto_backup_file"
        print_info "Also backed up auto-backup file for $env"
    fi
    
    return 0
}

# Function to list backups for an environment
list_backups() {
    local env=$1
    local backup_dir="$ENVIRONMENTS_DIR/$env/backups"
    
    if [ ! -d "$backup_dir" ]; then
        print_warning "No backups found for environment: $env"
        return
    fi
    
    echo ""
    print_info "Backups for $env:"
    ls -lh "$backup_dir" | grep -E "terraform.tfstate.backup|terraform.tfstate.auto-backup" | awk '{print "  " $9 " (" $5 ")"}'
}

# Function to clean old backups (keep last N backups)
clean_old_backups() {
    local env=$1
    local keep_count=${2:-10}  # Default: keep last 10 backups
    local backup_dir="$ENVIRONMENTS_DIR/$env/backups"
    
    if [ ! -d "$backup_dir" ]; then
        return
    fi
    
    # Count backups
    local backup_count=$(ls -1 "$backup_dir" | grep -c "terraform.tfstate.backup" || true)
    
    if [ "$backup_count" -le "$keep_count" ]; then
        print_info "No cleanup needed for $env (found $backup_count backups, keeping $keep_count)"
        return
    fi
    
    print_info "Cleaning old backups for $env (keeping last $keep_count)..."
    
    # Remove old backups (keep last N)
    ls -t "$backup_dir"/terraform.tfstate.backup.* | tail -n +$((keep_count + 1)) | xargs -r rm -f
    
    local removed_count=$((backup_count - keep_count))
    print_success "Removed $removed_count old backup(s) from $env"
}

# Function to restore from backup
restore_backup() {
    local env=$1
    local backup_file=$2
    local env_dir="$ENVIRONMENTS_DIR/$env"
    local state_file="$env_dir/terraform.tfstate"
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        return 1
    fi
    
    print_warning "This will replace the current state file with the backup!"
    echo "Environment: $env"
    echo "Backup file: $backup_file"
    echo ""
    read -p "Are you sure you want to restore? (yes/NO): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Restore cancelled"
        return 0
    fi
    
    # Backup current state before restoring
    if [ -f "$state_file" ]; then
        local safety_backup="$env_dir/terraform.tfstate.before-restore.$(date +%Y%m%d_%H%M%S)"
        cp "$state_file" "$safety_backup"
        print_info "Current state backed up to: $safety_backup"
    fi
    
    # Restore from backup
    cp "$backup_file" "$state_file"
    print_success "State restored from backup: $backup_file"
}

# Show usage
show_usage() {
    echo "Usage: ./backup-state.sh [environment] [options]"
    echo ""
    echo "Arguments:"
    echo "  environment    - Specific environment to backup (dev, staging, prod)"
    echo "  --all          - Backup all environments"
    echo ""
    echo "Options:"
    echo "  --list         - List all backups for the environment"
    echo "  --clean [N]    - Clean old backups, keeping last N (default: 10)"
    echo "  --restore FILE - Restore state from a specific backup file"
    echo ""
    echo "Examples:"
    echo "  ./backup-state.sh dev                    # Backup dev environment"
    echo "  ./backup-state.sh --all                  # Backup all environments"
    echo "  ./backup-state.sh dev --list             # List backups for dev"
    echo "  ./backup-state.sh dev --clean 5          # Keep only last 5 backups"
    echo "  ./backup-state.sh dev --restore FILE     # Restore from backup"
}

# Main logic
if [ -z "$ENVIRONMENT" ] && [ "$BACKUP_ALL" = false ]; then
    show_usage
    exit 1
fi

# Handle --list option
if [ "$2" == "--list" ] || [ "$3" == "--list" ]; then
    if [ -n "$ENVIRONMENT" ]; then
        list_backups "$ENVIRONMENT"
    else
        for env in dev staging prod; do
            list_backups "$env"
        done
    fi
    exit 0
fi

# Handle --clean option
if [ "$2" == "--clean" ] || [ "$3" == "--clean" ]; then
    KEEP_COUNT=${3:-10}
    if [ "$3" == "--clean" ]; then
        KEEP_COUNT=${4:-10}
    fi
    
    if [ -n "$ENVIRONMENT" ]; then
        clean_old_backups "$ENVIRONMENT" "$KEEP_COUNT"
    else
        for env in dev staging prod; do
            clean_old_backups "$env" "$KEEP_COUNT"
        done
    fi
    exit 0
fi

# Handle --restore option
if [ "$2" == "--restore" ]; then
    if [ -z "$3" ]; then
        print_error "Please specify the backup file to restore"
        exit 1
    fi
    restore_backup "$ENVIRONMENT" "$3"
    exit 0
fi

# Perform backup
print_info "Starting Terraform state backup..."
echo ""

if [ "$BACKUP_ALL" = true ]; then
    print_info "Backing up all environments..."
    success_count=0
    fail_count=0
    
    for env in dev staging prod; do
        if backup_environment "$env"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    done
    
    echo ""
    print_info "=== Backup Summary ==="
    echo "Successful: $success_count"
    echo "Failed/Skipped: $fail_count"
    
else
    # Validate environment name
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        print_error "Invalid environment: $ENVIRONMENT"
        echo "Valid environments are: dev, staging, prod"
        exit 1
    fi
    
    if backup_environment "$ENVIRONMENT"; then
        echo ""
        print_info "Backup completed successfully!"
        list_backups "$ENVIRONMENT"
    else
        print_error "Backup failed for environment: $ENVIRONMENT"
        exit 1
    fi
fi

echo ""
print_info "Backup location: $ENVIRONMENTS_DIR/<environment>/backups/"
print_warning "Remember to clean old backups periodically using --clean option"
