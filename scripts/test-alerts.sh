 #!/bin/bash

echo "🚨 Testing Error Alert System..."
echo "This script will intentionally generate errors to test the Kafka alert system"
echo ""

BASE_URL="http://localhost"

echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "📧 Test 1: Invalid order data (will trigger order_creation_failed alert)"
echo "Sending order with invalid quantity type..."

RESPONSE1=$(curl -s -X POST "$BASE_URL/api/orders/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "sell",
    "customer_name": "Test Error User 1",
    "items": [{
      "product_id": 1,
      "product_name": "Test Product",
      "quantity": "not_a_number",
      "unit_price": 10.0
    }]
  }')

echo "Response: $RESPONSE1"
echo ""

echo "📧 Test 2: Missing required fields (will trigger validation error)"
echo "Sending order with missing order_type and items..."

RESPONSE2=$(curl -s -X POST "$BASE_URL/api/orders/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Error User 2",
    "customer_email": "test@error.com"
  }')

echo "Response: $RESPONSE2"
echo ""

echo "📧 Test 3: Invalid product data (database constraint error)"
echo "Sending order with negative product_id..."

RESPONSE3=$(curl -s -X POST "$BASE_URL/api/orders/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "sell",
    "customer_name": "Test Error User 3",
    "items": [{
      "product_id": -1,
      "product_name": "Invalid Product",
      "quantity": 1,
      "unit_price": -50.0
    }]
  }')

echo "Response: $RESPONSE3"
echo ""

echo "⏳ Waiting for alerts to be processed..."
sleep 3

echo ""
echo "📊 Checking alerts in dashboard API..."
DASHBOARD_DATA=$(curl -s "$BASE_URL/monitor/api/monitor/dashboard")
ALERTS=$(echo "$DASHBOARD_DATA" | grep -o '"total_alerts":[0-9]*' | cut -d':' -f2)
echo "Total alerts in system: $ALERTS"

echo ""
echo "🎯 Recent alerts:"
echo "$DASHBOARD_DATA" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    alerts = data.get('recent_alerts', [])
    if alerts:
        for alert in alerts[-3:]:  # Show last 3 alerts
            timestamp = alert.get('timestamp', 'N/A')[:19]  # Show only date and time part
            print(f'- {alert.get(\"severity\", \"unknown\").upper()}: {alert.get(\"message\", \"No message\")} ({timestamp})')
    else:
        print('- No recent alerts found')
except Exception as e:
    print(f'- Error parsing dashboard data: {e}')
" 2>/dev/null

echo ""
echo "✅ Error alert testing completed!"
echo ""
echo "🌐 View all alerts in the dashboard:"
echo "  Dashboard: $BASE_URL/monitor/dashboard"
echo "  API: $BASE_URL/monitor/api/monitor/dashboard"
echo ""
echo "📊 The alerts should appear in the 'Alertas Recientes' section"
echo "   and will auto-refresh every second for real-time monitoring"
