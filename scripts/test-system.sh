#!/bin/bash

echo "🧪 Testing Microservices System..."

BASE_URL="http://localhost"

# Test health endpoints
echo "🔍 Testing health endpoints..."

echo "Testing Inventory Service health..."
curl -s "$BASE_URL/api/inventory/health" | grep -q "healthy" && echo "✅ Inventory service is healthy" || echo "❌ Inventory service failed"

echo "Testing Orders Service health..."
curl -s "$BASE_URL/api/orders/health" | grep -q "healthy" && echo "✅ Orders service is healthy" || echo "❌ Orders service failed"

echo "Testing Monitor Service health..."
curl -s "$BASE_URL/api/monitor/health" | grep -q "healthy" && echo "✅ Monitor service is healthy" || echo "❌ Monitor service failed"

# Test basic API endpoints
echo ""
echo "📡 Testing API endpoints..."

echo "Testing products endpoint..."
curl -s "$BASE_URL/api/inventory/products" > /dev/null && echo "✅ Products API working" || echo "❌ Products API failed"

echo "Testing orders endpoint..."
curl -s "$BASE_URL/api/orders/orders" > /dev/null && echo "✅ Orders API working" || echo "❌ Orders API failed"

echo "Testing monitor dashboard..."
curl -s "$BASE_URL/api/monitor/dashboard" > /dev/null && echo "✅ Monitor dashboard working" || echo "❌ Monitor dashboard failed"

# Test Kafka UI
echo ""
echo "📊 Testing external services..."
curl -s "http://localhost:8080" > /dev/null && echo "✅ Kafka UI accessible" || echo "❌ Kafka UI not accessible"

echo ""
echo "🎯 System test completed!"
echo ""
echo "📊 For detailed monitoring, visit:"
echo "  - Dashboard: $BASE_URL"
echo "  - Monitor API: $BASE_URL/api/monitor/dashboard"
echo "  - Kafka UI: http://localhost:8080"
