#!/bin/bash

# Covibe Deployment Script
# This script handles deployment of Covibe to various environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_ENV="development"
DEFAULT_COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Covibe Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    start       Start the application
    stop        Stop the application
    restart     Restart the application
    build       Build Docker images
    deploy      Deploy to production
    status      Show service status
    logs        Show service logs
    backup      Create configuration backup
    restore     Restore from backup
    health      Check service health

Options:
    -e, --env ENV           Environment (development, staging, production)
    -f, --file FILE         Docker compose file to use
    -m, --monitoring        Include monitoring services
    -h, --help              Show this help message

Examples:
    $0 start                           # Start development environment
    $0 -e production deploy            # Deploy to production
    $0 -m start                        # Start with monitoring
    $0 -f docker-compose.prod.yml build   # Build production images

EOF
}

# Parse command line arguments
ENVIRONMENT="$DEFAULT_ENV"
COMPOSE_FILE="$DEFAULT_COMPOSE_FILE"
INCLUDE_MONITORING=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -m|--monitoring)
            INCLUDE_MONITORING=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        start|stop|restart|build|deploy|status|logs|backup|restore|health)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate command
if [[ -z "$COMMAND" ]]; then
    log_error "No command specified"
    show_help
    exit 1
fi

# Set compose files based on environment and options
COMPOSE_FILES="-f $COMPOSE_FILE"
if [[ "$INCLUDE_MONITORING" == true ]]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.monitoring.yml"
fi

# Environment-specific configurations
case $ENVIRONMENT in
    development)
        export LOG_LEVEL=debug
        export DATABASE_URL=sqlite:///./data/covibe.db
        ;;
    staging)
        export LOG_LEVEL=info
        export DATABASE_URL=postgresql://covibe:password@db:5432/covibe_staging
        ;;
    production)
        export LOG_LEVEL=warning
        export DATABASE_URL=postgresql://covibe:${DB_PASSWORD}@db:5432/covibe
        COMPOSE_FILES="-f docker-compose.prod.yml"
        if [[ "$INCLUDE_MONITORING" == true ]]; then
            COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.monitoring.yml"
        fi
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Change to project root
cd "$PROJECT_ROOT"

# Pre-deployment checks
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check required files
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Create required directories
    mkdir -p data logs monitoring/grafana/dashboards
    
    log_success "Prerequisites check passed"
}

# Build images
build_images() {
    log_info "Building Docker images..."
    docker-compose $COMPOSE_FILES build --no-cache
    log_success "Images built successfully"
}

# Start services
start_services() {
    log_info "Starting Covibe services..."
    check_prerequisites
    
    # Create network if it doesn't exist
    docker network create covibe-network 2>/dev/null || true
    
    # Start services
    docker-compose $COMPOSE_FILES up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    if check_health; then
        log_success "Covibe started successfully"
        show_service_info
    else
        log_error "Some services are not healthy"
        docker-compose $COMPOSE_FILES logs
        exit 1
    fi
}

# Stop services
stop_services() {
    log_info "Stopping Covibe services..."
    docker-compose $COMPOSE_FILES down
    log_success "Covibe stopped successfully"
}

# Restart services
restart_services() {
    log_info "Restarting Covibe services..."
    stop_services
    start_services
}

# Show service status
show_status() {
    log_info "Service status:"
    docker-compose $COMPOSE_FILES ps
}

# Show service logs
show_logs() {
    docker-compose $COMPOSE_FILES logs -f
}

# Check service health
check_health() {
    local healthy=true
    
    log_info "Checking service health..."
    
    # Check backend health
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "Backend is healthy"
    else
        log_error "Backend is not healthy"
        healthy=false
    fi
    
    # Check frontend (if not using nginx proxy)
    if [[ "$ENVIRONMENT" == "development" ]]; then
        if curl -f http://localhost:3000 &>/dev/null; then
            log_success "Frontend is healthy"
        else
            log_error "Frontend is not healthy"
            healthy=false
        fi
    fi
    
    # Check monitoring services if enabled
    if [[ "$INCLUDE_MONITORING" == true ]]; then
        if curl -f http://localhost:9090 &>/dev/null; then
            log_success "Prometheus is healthy"
        else
            log_warning "Prometheus is not healthy"
        fi
        
        if curl -f http://localhost:3000 &>/dev/null; then
            log_success "Grafana is healthy"
        else
            log_warning "Grafana is not healthy"
        fi
    fi
    
    $healthy
}

# Show service information
show_service_info() {
    log_info "Service URLs:"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    echo "  Frontend: http://localhost:3000"
    
    if [[ "$INCLUDE_MONITORING" == true ]]; then
        echo "  Prometheus: http://localhost:9090"
        echo "  Grafana: http://localhost:3000 (admin/admin)"
        echo "  Jaeger: http://localhost:16686"
        echo "  Kibana: http://localhost:5601"
    fi
}

# Create backup
create_backup() {
    local backup_name="covibe_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_dir="./backups/$backup_name"
    
    log_info "Creating backup: $backup_name"
    
    mkdir -p "$backup_dir"
    
    # Backup database
    if [[ -f "./data/covibe.db" ]]; then
        cp "./data/covibe.db" "$backup_dir/"
        log_success "Database backed up"
    fi
    
    # Backup configuration files
    cp -r ./monitoring "$backup_dir/" 2>/dev/null || true
    cp docker-compose*.yml "$backup_dir/" 2>/dev/null || true
    cp .env "$backup_dir/" 2>/dev/null || true
    
    # Create archive
    tar -czf "${backup_dir}.tar.gz" -C ./backups "$backup_name"
    rm -rf "$backup_dir"
    
    log_success "Backup created: ${backup_dir}.tar.gz"
}

# Restore from backup
restore_backup() {
    log_warning "Restore functionality not implemented yet"
    log_info "To restore manually:"
    echo "  1. Stop services: $0 stop"
    echo "  2. Extract backup: tar -xzf backup.tar.gz"
    echo "  3. Copy files to appropriate locations"
    echo "  4. Start services: $0 start"
}

# Production deployment
deploy_production() {
    log_info "Deploying to production..."
    
    if [[ "$ENVIRONMENT" != "production" ]]; then
        log_error "This command should only be used with -e production"
        exit 1
    fi
    
    # Additional production checks
    if [[ -z "$DB_PASSWORD" ]]; then
        log_error "DB_PASSWORD environment variable is required for production"
        exit 1
    fi
    
    # Build and deploy
    build_images
    start_services
    
    # Run production health checks
    sleep 30
    if check_health; then
        log_success "Production deployment successful"
    else
        log_error "Production deployment failed"
        exit 1
    fi
}

# Main command execution
case $COMMAND in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    build)
        build_images
        ;;
    deploy)
        if [[ "$ENVIRONMENT" == "production" ]]; then
            deploy_production
        else
            start_services
        fi
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backup)
        create_backup
        ;;
    restore)
        restore_backup
        ;;
    health)
        check_health
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac