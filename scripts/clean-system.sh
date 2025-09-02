#!/bin/bash

echo "🧹 Cleaning Microservices System..."

# Stop all services and remove volumes
echo "🛑 Stopping services and removing volumes..."
docker-compose down -v

# Remove any dangling containers
echo "🗑️  Removing dangling containers..."
docker container prune -f

# Remove any dangling images
echo "🗑️  Removing dangling images..."
docker image prune -f

# Remove any dangling volumes
echo "🗑️  Removing dangling volumes..."
docker volume prune -f

# Remove any dangling networks
echo "🗑️  Removing dangling networks..."
docker network prune -f

echo "✅ System cleaned successfully!"
echo ""
echo "💡 To start fresh: ./scripts/start-system.sh"
