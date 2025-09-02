#!/bin/bash

echo "🔥 EXTREME STRESS TEST - Service Killer"
echo "======================================="
echo "WARNING: This will attempt to completely overwhelm the orders service!"
echo "Use this to test alert system under extreme load."
echo ""

# Extreme parameters
REQUESTS=${1:-1000}
CONCURRENT=${2:-50}
BASE_URL="http://localhost"

echo "⚠️  DANGER ZONE PARAMETERS:"
echo "  - Requests: $REQUESTS"
echo "  - Concurrent: $CONCURRENT"
echo "  - This WILL likely cause service failures"
echo ""

read -p "Continue with extreme stress test? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled by user."
    exit 1
fi

echo ""
echo "🚨 Starting EXTREME stress test in 3 seconds..."
sleep 1 && echo "3..." 
sleep 1 && echo "2..." 
sleep 1 && echo "1..." 
echo "🔥 ATTACK!"

# Store initial stats
INITIAL_ALERTS=$(curl -s "$BASE_URL/monitor/api/monitor/dashboard" | grep -o '"total_alerts":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "0")
START_TIME=$(date +%s)

# Extreme attack function
extreme_attack() {
    local batch_id=$1
    
    for ((i=1; i<=20; i++)); do
        # Mix of different attack vectors
        case $((i % 4)) in
            0)
                # Memory bomb
                curl -s -X POST "$BASE_URL/api/orders/orders" \
                    -H "Content-Type: application/json" \
                    -d "{\"order_type\":\"sell\",\"customer_name\":\"$(printf 'X%.0s' {1..50000})\",\"items\":[{\"product_id\":\"bomb\",\"product_name\":\"$(printf 'Y%.0s' {1..10000})\",\"quantity\":\"overload\",\"unit_price\":\"crash\"}]}" > /dev/null 2>&1 &
                ;;
            1)
                # Type confusion attack
                curl -s -X POST "$BASE_URL/api/orders/orders" \
                    -H "Content-Type: application/json" \
                    -d "{\"order_type\":123,\"customer_name\":[\"array\",\"attack\"],\"items\":{\"not\":\"array\",\"product_id\":null,\"quantity\":\"∞\",\"unit_price\":\"💣\"}}" > /dev/null 2>&1 &
                ;;
            2)
                # Unicode and special chars bomb
                curl -s -X POST "$BASE_URL/api/orders/orders" \
                    -H "Content-Type: application/json" \
                    -d "{\"order_type\":\"💀💀💀\",\"customer_name\":\"🚀$(printf '🔥%.0s' {1..1000})🚀\",\"items\":[{\"product_id\":\"∞∞∞\",\"product_name\":\"$(printf '💣%.0s' {1..500})💥\",\"quantity\":\"🌪️\",\"unit_price\":\"💸💸💸\"}]}" > /dev/null 2>&1 &
                ;;
            3)
                # Nested chaos
                curl -s -X POST "$BASE_URL/api/orders/orders" \
                    -H "Content-Type: application/json" \
                    -d "{\"order_type\":\"sell\",\"customer_name\":\"ChaosTest$batch_id\",\"items\":[{\"product_id\":999999999999,\"quantity\":-999999999,\"unit_price\":99999999999.99,\"product_name\":\"$(date)\"}]}" > /dev/null 2>&1 &
                ;;
        esac
        
        # Super aggressive - no waiting
        if (( $(jobs -r | wc -l) > 200 )); then
            break
        fi
    done
}

# Launch extreme concurrent attacks
echo "🚀 Launching $CONCURRENT attack batches..."
for ((batch=1; batch<=CONCURRENT; batch++)); do
    extreme_attack $batch &
    
    # Progress
    if (( batch % 10 == 0 )); then
        echo "  Launched $batch attack batches..."
        CURRENT_JOBS=$(jobs -r | wc -l)
        echo "  Active processes: $CURRENT_JOBS"
    fi
    
    # Brief pause to not completely freeze system
    sleep 0.05
done

# Let it run for a bit
echo ""
echo "💀 Attack in progress... letting it run for 10 seconds"
for i in {10..1}; do
    ACTIVE_JOBS=$(jobs -r | wc -l)
    echo "  Time: ${i}s | Active attacks: $ACTIVE_JOBS"
    sleep 1
done

echo ""
echo "🛑 Stopping attack..."
jobs -p | xargs -r kill 2>/dev/null
wait 2>/dev/null

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "⏳ Waiting for system to recover and process alerts..."
sleep 10

# Check damage
FINAL_ALERTS=$(curl -s "$BASE_URL/monitor/api/monitor/dashboard" | grep -o '"total_alerts":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "0")
NEW_ALERTS=$((FINAL_ALERTS - INITIAL_ALERTS))

echo ""
echo "💀 EXTREME STRESS TEST RESULTS"
echo "==============================="
echo "Duration: ${DURATION} seconds"
echo "Initial alerts: $INITIAL_ALERTS"
echo "Final alerts: $FINAL_ALERTS"
echo "🚨 NEW ALERTS GENERATED: $NEW_ALERTS"
echo ""

if [ $NEW_ALERTS -gt 50 ]; then
    echo "🔥 MISSION ACCOMPLISHED: Service was severely stressed!"
    echo "   Generated $NEW_ALERTS alerts - Alert system is ROBUST!"
elif [ $NEW_ALERTS -gt 10 ]; then
    echo "⚡ GOOD DAMAGE: Service was stressed, alert system working!"
elif [ $NEW_ALERTS -gt 0 ]; then
    echo "⚠️  LIGHT DAMAGE: Some alerts generated, system is resilient"
else
    echo "🛡️  NO DAMAGE: Service survived the attack! Very robust!"
fi

echo ""
echo "🌐 Check the carnage:"
echo "  Dashboard: $BASE_URL/monitor/dashboard"
echo ""

# Check if service is still responding
echo "🔍 Service health check:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/orders/orders" 2>/dev/null)
if [ "$HTTP_CODE" = "405" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✅ Service is responding (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "500" ]; then
    echo "⚠️  Service is responding but with errors (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "000" ] || [ -z "$HTTP_CODE" ]; then
    echo "💀 Service appears to be DOWN!"
else
    echo "❓ Service status unclear (HTTP $HTTP_CODE)"
fi

echo ""
echo "🏁 Extreme stress test completed!"
echo "   The alert system has been thoroughly tested under extreme load."
