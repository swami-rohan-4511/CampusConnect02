#!/bin/bash

# Campus Connect Deployment Script
# This script helps deploy the application to various platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup environment
setup_environment() {
    print_status "Setting up deployment environment..."

    # Check if .env.production exists
    if [ ! -f ".env.production" ]; then
        print_error ".env.production file not found!"
        print_status "Copying from .env.example..."
        cp .env.example .env.production
        print_warning "Please update .env.production with your production values!"
    fi

    # Check if Docker is installed
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_success "Environment setup complete"
}

# Function to deploy locally with Docker
deploy_local() {
    print_status "Deploying locally with Docker Compose..."

    # Copy production environment
    cp .env.production .env

    # Build and start services
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d

    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 30

    # Run health checks
    print_status "Running health checks..."
    if python test_integration.py; then
        print_success "Local deployment successful!"
        print_status "Access your application at:"
        echo "  Frontend: http://localhost:3000"
        echo "  API Gateway: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
    else
        print_error "Health checks failed. Check the logs:"
        echo "  docker-compose logs"
    fi
}

# Function to deploy to Render
deploy_render() {
    print_status "Deploying to Render..."

    # Check if Render CLI is installed
    if ! command_exists render; then
        print_error "Render CLI is not installed."
        print_status "Install it with: npm install -g render-cli"
        exit 1
    fi

    # Check if render.yaml exists
    if [ ! -f "render.yaml" ]; then
        print_error "render.yaml not found!"
        exit 1
    fi

    # Deploy using Render CLI
    print_status "Deploying services to Render..."
    render deploy render.yaml

    print_success "Render deployment initiated!"
    print_status "Monitor deployment status in your Render dashboard"
}

# Function to deploy frontend to Vercel
deploy_vercel() {
    print_status "Deploying frontend to Vercel..."

    # Check if Vercel CLI is installed
    if ! command_exists vercel; then
        print_error "Vercel CLI is not installed."
        print_status "Install it with: npm install -g vercel"
        exit 1
    fi

    # Navigate to frontend directory
    cd frontend

    # Deploy to Vercel
    print_status "Deploying frontend..."
    vercel --prod

    print_success "Frontend deployed to Vercel!"
    cd ..
}

# Function to setup production database
setup_database() {
    print_status "Setting up production database..."

    # This would typically involve:
    # 1. Creating database instances on your cloud provider
    # 2. Running migrations
    # 3. Setting up backups

    print_status "Database setup steps:"
    echo "1. Create MySQL database on your cloud provider (AWS RDS, Google Cloud SQL, etc.)"
    echo "2. Update .env.production with database credentials"
    echo "3. Run database migrations:"
    echo "   docker-compose exec mysql mysql -u root -p < database/init.sql"
    echo "4. Setup automated backups"
    echo "5. Configure database monitoring"

    print_success "Database setup guidelines provided"
}

# Function to setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring and logging..."

    print_status "Recommended monitoring setup:"
    echo "1. Error Tracking: Sentry"
    echo "   - Sign up at sentry.io"
    echo "   - Add SENTRY_DSN to .env.production"
    echo ""
    echo "2. Performance Monitoring: New Relic"
    echo "   - Sign up at newrelic.com"
    echo "   - Add NEW_RELIC_LICENSE_KEY to .env.production"
    echo ""
    echo "3. Application Metrics: Prometheus + Grafana"
    echo "   - Deploy Prometheus and Grafana containers"
    echo "   - Configure exporters for each service"
    echo ""
    echo "4. Log Aggregation: ELK Stack or CloudWatch"
    echo "   - Setup centralized logging"
    echo "   - Configure log rotation"

    print_success "Monitoring setup guidelines provided"
}

# Function to show deployment status
show_status() {
    print_status "Checking deployment status..."

    # Check if services are running locally
    if docker-compose ps | grep -q "Up"; then
        print_success "Local services are running"
        docker-compose ps
    else
        print_warning "No local services running"
    fi

    print_status "Service URLs (update with your actual deployed URLs):"
    echo "Frontend: https://campus-connect.vercel.app"
    echo "API Gateway: https://campus-connect-api-gateway.onrender.com"
    echo "WebSocket: wss://campus-connect-websocket.onrender.com"
}

# Function to cleanup deployment
cleanup() {
    print_status "Cleaning up deployment..."

    # Stop local services
    docker-compose down -v

    # Remove unused Docker images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    print_success "Cleanup complete"
}

# Main menu
show_menu() {
    echo "========================================"
    echo "  Campus Connect Deployment Manager"
    echo "========================================"
    echo "1. Setup Environment"
    echo "2. Deploy Locally (Docker)"
    echo "3. Deploy to Render (Backend)"
    echo "4. Deploy to Vercel (Frontend)"
    echo "5. Setup Production Database"
    echo "6. Setup Monitoring"
    echo "7. Show Deployment Status"
    echo "8. Cleanup Deployment"
    echo "9. Exit"
    echo "========================================"
}

# Main script logic
main() {
    while true; do
        show_menu
        read -p "Choose an option (1-9): " choice

        case $choice in
            1)
                setup_environment
                ;;
            2)
                deploy_local
                ;;
            3)
                deploy_render
                ;;
            4)
                deploy_vercel
                ;;
            5)
                setup_database
                ;;
            6)
                setup_monitoring
                ;;
            7)
                show_status
                ;;
            8)
                cleanup
                ;;
            9)
                print_success "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-9."
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main