#!/bin/bash

# Quick stress test for orders service
# Usage: ./quick-stress-test.sh [requests] [concurrent]

REQUESTS=${1:-50}
CONCURRENT=${2:-10}
BASE_URL="http://localhost"

echo "🚀 Quick Stress Test"
echo "==================="
echo "Requests: $REQUESTS | Concurrent: $CONCURRENT"
echo ""

# Function to send invalid order
send_invalid_order() {
    local id=$1
    curl -s -X POST "$BASE_URL/api/orders/orders" \
        -H "Content-Type: application/json" \
        -d "{
            \"order_type\": \"sell\",
            \"customer_name\": \"QuickTest$id\",
            \"items\": [{
                \"product_id\": \"invalid$id\",
                \"product_name\": \"Test Product $id\",
                \"quantity\": \"not_a_number\",
                \"unit_price\": 10.0
            }]
        }" > /dev/null 2>&1 &
}

echo "📊 Baseline alerts: $(curl -s "$BASE_URL/monitor/api/monitor/dashboard" | grep -o '"total_alerts":[0-9]*' | cut -d':' -f2)"
echo ""
echo "🔥 Sending $REQUESTS requests..."

# Send requests
for ((i=1; i<=REQUESTS; i++)); do
    send_invalid_order $i
    
    # Limit concurrent requests
    while (( $(jobs -r | wc -l) >= CONCURRENT )); do
        sleep 0.1
    done
    
    # Progress indicator
    if (( i % 10 == 0 )); then
        echo "  Sent $i requests..."
    fi
done

wait # Wait for all requests
echo ""
echo "⏳ Waiting for processing..."
sleep 3

echo "📊 Final alerts: $(curl -s "$BASE_URL/monitor/api/monitor/dashboard" | grep -o '"total_alerts":[0-9]*' | cut -d':' -f2)"
echo "✅ Quick stress test completed!"
echo ""
echo "🌐 Check dashboard: $BASE_URL/monitor/dashboard"
