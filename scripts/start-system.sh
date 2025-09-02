#!/bin/bash

echo "🚀 Starting Microservices System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start all services
echo "📦 Starting all services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 45

# Setup Kafka topics
echo "📨 Setting up Kafka topics..."
./scripts/setup-kafka-topics.sh

# Check services health
echo "🔍 Checking services health..."
sleep 10

echo "Checking Inventory Service..."
curl -f http://localhost:5001/health || echo "❌ Inventory service not ready"

echo "Checking Orders Service..."
curl -f http://localhost:5002/health || echo "❌ Orders service not ready"

echo "Checking Monitor Service..."
curl -f http://localhost:5003/health || echo "❌ Monitor service not ready"

echo ""
echo "✅ System startup completed!"
echo ""
echo "🌐 Access points:"
echo "  - Main Dashboard: http://localhost"
echo "  - Inventory API: http://localhost:5001"
echo "  - Orders API: http://localhost:5002"
echo "  - Monitor API: http://localhost:5003"
echo "  - Kafka UI: http://localhost:8080"
echo ""
echo "📊 API Examples:"
echo "  - GET http://localhost/api/inventory/products"
echo "  - GET http://localhost/api/orders/orders"
echo "  - GET http://localhost/api/monitor/dashboard"
echo ""
echo "🛑 To stop the system: ./scripts/stop-system.sh"
