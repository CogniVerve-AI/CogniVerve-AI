#!/bin/bash

# CogniVerve-AI Deployment Setup Script
# This script sets up the deployment infrastructure and secrets

set -e

echo "🚀 Setting up CogniVerve-AI deployment infrastructure..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v flyctl &> /dev/null; then
        print_error "flyctl is not installed. Please install it from https://fly.io/docs/hands-on/install-flyctl/"
        exit 1
    fi
    
    if ! command -v vercel &> /dev/null; then
        print_warning "Vercel CLI not found. Installing..."
        npm install -g vercel
    fi
    
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI not found. Please install it from https://cli.github.com/"
    fi
    
    print_status "Dependencies check completed!"
}

# Setup Fly.io applications
setup_flyio() {
    print_status "Setting up Fly.io applications..."
    
    cd backend
    
    # Create production app
    print_status "Creating production backend app..."
    flyctl apps create cogniverve-backend-prod --org personal || true
    
    # Create staging app
    print_status "Creating staging backend app..."
    flyctl apps create cogniverve-backend-staging --org personal || true
    
    # Set up secrets for production
    print_status "Setting up production secrets..."
    echo "Please enter your production environment variables:"
    
    read -p "Database URL: " DATABASE_URL
    read -p "Redis URL: " REDIS_URL
    read -s -p "Secret Key: " SECRET_KEY
    echo
    read -p "Stripe Secret Key: " STRIPE_SECRET_KEY
    read -p "Stripe Webhook Secret: " STRIPE_WEBHOOK_SECRET
    
    flyctl secrets set \
        DATABASE_URL="$DATABASE_URL" \
        REDIS_URL="$REDIS_URL" \
        SECRET_KEY="$SECRET_KEY" \
        STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY" \
        STRIPE_WEBHOOK_SECRET="$STRIPE_WEBHOOK_SECRET" \
        --app cogniverve-backend-prod
    
    # Set up secrets for staging (with test values)
    print_status "Setting up staging secrets..."
    flyctl secrets set \
        DATABASE_URL="postgresql://test:test@localhost:5432/test_db" \
        REDIS_URL="redis://localhost:6379/0" \
        SECRET_KEY="staging-secret-key" \
        STRIPE_SECRET_KEY="sk_test_staging" \
        STRIPE_WEBHOOK_SECRET="whsec_staging" \
        --app cogniverve-backend-staging
    
    cd ..
    print_status "Fly.io setup completed!"
}

# Setup Vercel project
setup_vercel() {
    print_status "Setting up Vercel project..."
    
    cd frontend
    
    # Link to Vercel project
    vercel link --yes || true
    
    # Set environment variables
    print_status "Setting up Vercel environment variables..."
    vercel env add VITE_API_URL production
    echo "https://api.cogniverve.ai" | vercel env add VITE_API_URL production
    
    vercel env add VITE_API_URL preview
    echo "https://api-staging.cogniverve.ai" | vercel env add VITE_API_URL preview
    
    cd ..
    print_status "Vercel setup completed!"
}

# Setup GitHub secrets
setup_github_secrets() {
    print_status "Setting up GitHub secrets..."
    
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI not found. Please manually add the following secrets to your GitHub repository:"
        echo "- FLY_API_TOKEN: Your Fly.io API token"
        echo "- VERCEL_TOKEN: Your Vercel token"
        echo "- VERCEL_ORG_ID: Your Vercel organization ID"
        echo "- VERCEL_PROJECT_ID: Your Vercel project ID"
        echo "- SLACK_WEBHOOK_URL: Your Slack webhook URL (optional)"
        return
    fi
    
    print_status "Please provide the following tokens:"
    
    read -s -p "Fly.io API Token: " FLY_API_TOKEN
    echo
    read -s -p "Vercel Token: " VERCEL_TOKEN
    echo
    read -p "Vercel Org ID: " VERCEL_ORG_ID
    read -p "Vercel Project ID: " VERCEL_PROJECT_ID
    read -p "Slack Webhook URL (optional): " SLACK_WEBHOOK_URL
    
    # Set GitHub secrets
    gh secret set FLY_API_TOKEN --body "$FLY_API_TOKEN"
    gh secret set VERCEL_TOKEN --body "$VERCEL_TOKEN"
    gh secret set VERCEL_ORG_ID --body "$VERCEL_ORG_ID"
    gh secret set VERCEL_PROJECT_ID --body "$VERCEL_PROJECT_ID"
    
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        gh secret set SLACK_WEBHOOK_URL --body "$SLACK_WEBHOOK_URL"
    fi
    
    print_status "GitHub secrets setup completed!"
}

# Setup databases
setup_databases() {
    print_status "Setting up databases..."
    
    print_status "Please set up the following external services:"
    echo "1. Supabase PostgreSQL database: https://supabase.com"
    echo "2. Upstash Redis: https://upstash.com"
    echo "3. Qdrant Cloud: https://cloud.qdrant.io"
    echo ""
    echo "After setting up these services, update the secrets in Fly.io with the connection strings."
    
    print_status "Database setup instructions provided!"
}

# Main execution
main() {
    print_status "Starting CogniVerve-AI deployment setup..."
    
    check_dependencies
    setup_flyio
    setup_vercel
    setup_github_secrets
    setup_databases
    
    print_status "🎉 Deployment setup completed!"
    print_status "You can now push to the main branch to trigger a deployment."
    print_status "Monitor your deployments at:"
    echo "  - Fly.io: https://fly.io/apps/cogniverve-backend-prod"
    echo "  - Vercel: https://vercel.com/dashboard"
    echo "  - GitHub Actions: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"
}

# Run main function
main "$@"

