#!/bin/bash

echo "🛑 Stopping Microservices System..."

# Stop all services
docker-compose down

echo "🧹 Cleaning up..."

# Optional: Remove volumes (uncomment if you want to clean all data)
# echo "⚠️  Removing all data volumes..."
# docker-compose down -v

# Optional: Remove images (uncomment if you want to clean all images)
# echo "🗑️  Removing built images..."
# docker-compose down --rmi all

echo "✅ System stopped successfully!"
echo ""
echo "💡 To start again: ./scripts/start-system.sh"
echo "🗑️  To clean all data: docker-compose down -v"
