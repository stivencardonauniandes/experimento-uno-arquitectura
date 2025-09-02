#!/bin/bash

echo "🚀 STRESS TEST - Orders Service Alert System"
echo "=============================================="
echo "This script will attempt to overwhelm the orders service"
echo "to test the Kafka alert system under load"
echo ""

BASE_URL="http://localhost"
TOTAL_REQUESTS=200
CONCURRENT_REQUESTS=20
ERROR_TYPES=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
SUCCESSFUL_REQUESTS=0
FAILED_REQUESTS=0
ERROR_500_COUNT=0
ERROR_400_COUNT=0

echo "📊 Test Configuration:"
echo "  - Total requests: $TOTAL_REQUESTS"
echo "  - Concurrent requests: $CONCURRENT_REQUESTS"
echo "  - Error types: $ERROR_TYPES different scenarios"
echo "  - Target: $BASE_URL/api/orders/orders"
echo ""

# Function to send a problematic order request
send_problematic_order() {
    local test_type=$1
    local request_id=$2
    
    case $test_type in
        1)
            # Invalid data types (should cause 500 errors and Kafka alerts)
            RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/orders/orders" \
                -H "Content-Type: application/json" \
                -d "{
                    \"order_type\": \"sell\",
                    \"customer_name\": \"StressTest$request_id\",
                    \"items\": [{
                        \"product_id\": \"invalid_string_id\",
                        \"product_name\": \"Stress Product $request_id\",
                        \"quantity\": \"not_a_number\",
                        \"unit_price\": \"also_not_a_number\"
                    }]
                }" 2>/dev/null)
            ;;
        2)
            # Extremely large data (memory stress)
            LARGE_STRING=$(printf 'A%.0s' {1..10000})
            RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/orders/orders" \
                -H "Content-Type: application/json" \
                -d "{
                    \"order_type\": \"buy\",
                    \"customer_name\": \"$LARGE_STRING\",
                    \"customer_email\": \"${LARGE_STRING}@test.com\",
                    \"items\": [{
                        \"product_id\": 1,
                        \"product_name\": \"$LARGE_STRING\",
                        \"quantity\": 999999999,
                        \"unit_price\": 999999999.99
                    }]
                }" 2>/dev/null)
            ;;
        3)
            # Negative values and edge cases
            RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/orders/orders" \
                -H "Content-Type: application/json" \
                -d "{
                    \"order_type\": \"sell\",
                    \"customer_name\": \"NegativeTest$request_id\",
                    \"items\": [{
                        \"product_id\": -999,
                        \"product_name\": \"Negative Product\",
                        \"quantity\": -1,
                        \"unit_price\": -100.50
                    }]
                }" 2>/dev/null)
            ;;
        4)
            # Malformed JSON and SQL injection attempts
            RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/orders/orders" \
                -H "Content-Type: application/json" \
                -d "{
                    \"order_type\": \"'; DROP TABLE orders; --\",
                    \"customer_name\": \"<script>alert('xss')</script>\",
                    \"items\": [{
                        \"product_id\": \"1 UNION SELECT * FROM users\",
                        \"product_name\": \"'; DELETE FROM products; --\",
                        \"quantity\": null,
                        \"unit_price\": undefined
                    }
                }" 2>/dev/null)
            ;;
        5)
            # Valid but problematic orders (high volume)
            RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/orders/orders" \
                -H "Content-Type: application/json" \
                -d "{
                    \"order_type\": \"buy\",
                    \"customer_name\": \"HighVolumeTest$request_id\",
                    \"customer_email\": \"test$request_id@stress.com\",
                    \"items\": [
                        {\"product_id\": 1, \"product_name\": \"Product A\", \"quantity\": 1000000, \"unit_price\": 0.01},
                        {\"product_id\": 2, \"product_name\": \"Product B\", \"quantity\": 500000, \"unit_price\": 0.02},
                        {\"product_id\": 3, \"product_name\": \"Product C\", \"quantity\": 750000, \"unit_price\": 0.03}
                    ]
                }" 2>/dev/null)
            ;;
    esac
    
    # Extract HTTP code from response
    HTTP_CODE="${RESPONSE: -3}"
    RESPONSE_BODY="${RESPONSE%???}"
    
    # Count responses
    if [[ "$HTTP_CODE" == "500" ]]; then
        ((ERROR_500_COUNT++))
        echo -e "${RED}[ERROR 500]${NC} Request $request_id (Type $test_type): Internal Server Error"
    elif [[ "$HTTP_CODE" == "400" ]]; then
        ((ERROR_400_COUNT++))
        echo -e "${YELLOW}[ERROR 400]${NC} Request $request_id (Type $test_type): Bad Request"
    elif [[ "$HTTP_CODE" == "201" ]]; then
        ((SUCCESSFUL_REQUESTS++))
        echo -e "${GREEN}[SUCCESS]${NC} Request $request_id (Type $test_type): Order created"
    else
        ((FAILED_REQUESTS++))
        echo -e "${BLUE}[OTHER $HTTP_CODE]${NC} Request $request_id (Type $test_type): $RESPONSE_BODY"
    fi
}

# Function to run concurrent requests
run_batch() {
    local batch_start=$1
    local batch_size=$2
    
    echo ""
    echo "🔥 Starting batch $((batch_start / batch_size + 1)) - Requests $((batch_start + 1)) to $((batch_start + batch_size))"
    
    # Run concurrent requests
    for ((i=0; i<batch_size; i++)); do
        local request_id=$((batch_start + i + 1))
        local test_type=$(((request_id - 1) % ERROR_TYPES + 1))
        
        # Run in background for concurrency
        send_problematic_order $test_type $request_id &
        
        # Limit concurrent processes
        while (( $(jobs -r | wc -l) >= CONCURRENT_REQUESTS )); do
            sleep 0.1
        done
    done
    
    # Wait for all background jobs in this batch
    wait
}

# Get baseline alerts count
echo "📊 Getting baseline alert count..."
INITIAL_ALERTS=$(curl -s "$BASE_URL/monitor/api/monitor/dashboard" | grep -o '"total_alerts":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "0")
echo "Initial alerts: $INITIAL_ALERTS"

echo ""
echo "🚀 Starting stress test..."
START_TIME=$(date +%s)

# Run stress test in batches
for ((batch_start=0; batch_start<TOTAL_REQUESTS; batch_start+=CONCURRENT_REQUESTS)); do
    remaining=$((TOTAL_REQUESTS - batch_start))
    batch_size=$((remaining < CONCURRENT_REQUESTS ? remaining : CONCURRENT_REQUESTS))
    
    run_batch $batch_start $batch_size
    
    # Brief pause between batches to avoid completely overwhelming the system
    sleep 1
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "⏱️  Stress test completed in ${DURATION} seconds"
echo ""

# Wait a moment for alerts to be processed
echo "⏳ Waiting for alerts to be processed..."
sleep 5

# Get final stats
echo "📈 Final Results:"
echo "=================="
echo -e "Total Requests: $TOTAL_REQUESTS"
echo -e "${GREEN}Successful (201): $SUCCESSFUL_REQUESTS${NC}"
echo -e "${RED}Server Errors (500): $ERROR_500_COUNT${NC}"
echo -e "${YELLOW}Client Errors (400): $ERROR_400_COUNT${NC}"
echo -e "${BLUE}Other Errors: $FAILED_REQUESTS${NC}"
echo ""

# Check final alert count
FINAL_ALERTS=$(curl -s "$BASE_URL/monitor/api/monitor/dashboard" | grep -o '"total_alerts":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "0")
NEW_ALERTS=$((FINAL_ALERTS - INITIAL_ALERTS))

echo "🚨 Alert System Results:"
echo "========================"
echo "Initial alerts: $INITIAL_ALERTS"
echo "Final alerts: $FINAL_ALERTS"
echo -e "${RED}New alerts generated: $NEW_ALERTS${NC}"
echo ""

if [ $NEW_ALERTS -gt 0 ]; then
    echo -e "${GREEN}✅ SUCCESS: Alert system is working! Generated $NEW_ALERTS new alerts.${NC}"
    echo ""
    echo "🎯 Recent alerts from stress test:"
    curl -s "$BASE_URL/monitor/api/monitor/dashboard" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    alerts = data.get('recent_alerts', [])[-5:]  # Show last 5 alerts
    for alert in reversed(alerts):
        severity = alert.get('severity', 'unknown').upper()
        message = alert.get('message', 'No message')
        timestamp = alert.get('timestamp', 'N/A')[:19]
        service = alert.get('service', 'unknown')
        print(f'- {severity}: {message} ({service}) - {timestamp}')
except Exception as e:
    print('Error parsing alerts:', e)
" 2>/dev/null
else
    echo -e "${YELLOW}⚠️  WARNING: No new alerts generated. Check if the alert system is working properly.${NC}"
fi

echo ""
echo "🌐 View detailed results in dashboard:"
echo "  Dashboard: $BASE_URL/monitor/dashboard"
echo "  API: $BASE_URL/monitor/api/monitor/dashboard"
echo ""

# Performance summary
REQUESTS_PER_SECOND=$((TOTAL_REQUESTS / (DURATION > 0 ? DURATION : 1)))
ERROR_RATE=$(((ERROR_500_COUNT + ERROR_400_COUNT + FAILED_REQUESTS) * 100 / TOTAL_REQUESTS))

echo "📊 Performance Summary:"
echo "======================="
echo "Duration: ${DURATION}s"
echo "Requests/second: $REQUESTS_PER_SECOND"
echo "Error rate: ${ERROR_RATE}%"
echo ""

if [ $ERROR_500_COUNT -gt $((TOTAL_REQUESTS / 4)) ]; then
    echo -e "${RED}🔥 HIGH LOAD ACHIEVED: Service is under significant stress (${ERROR_500_COUNT} server errors)${NC}"
else
    echo -e "${YELLOW}💡 Consider increasing load parameters for more stress${NC}"
fi

echo ""
echo "✅ Stress test completed! Check the dashboard for real-time alerts."
