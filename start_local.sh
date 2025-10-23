#!/bin/bash

# Sales Engagement Platform - Local Development Startup Script
set -e

echo "🚀 Starting Sales Engagement Platform Locally"
echo "=" * 50

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing docker-compose..."
    sudo apt update && sudo apt install -y docker-compose
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
sudo docker-compose -f docker-compose.local.yml down --remove-orphans

# Build and start services
echo "🔨 Building and starting services..."
sudo docker-compose -f docker-compose.local.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
sudo docker-compose -f docker-compose.local.yml ps

# Run database migrations
echo "🔄 Running database migrations..."
sudo docker-compose -f docker-compose.local.yml exec -T api alembic upgrade head

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install aiohttp

# Run tests
echo "🧪 Running comprehensive tests..."
python test_local_deployment.py

echo ""
echo "🎉 Local deployment complete!"
echo "🌐 API URL: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "📋 Useful commands:"
echo "  View logs: sudo docker-compose -f docker-compose.local.yml logs -f"
echo "  Stop services: sudo docker-compose -f docker-compose.local.yml down"
echo "  Restart API: sudo docker-compose -f docker-compose.local.yml restart api"