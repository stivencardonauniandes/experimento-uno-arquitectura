#!/bin/bash

echo "🚀 Starting Kafka infrastructure..."

# Start only infrastructure services first
echo "📦 Starting Zookeeper and Kafka..."
docker-compose up -d zookeeper postgres redis

echo "⏳ Waiting for Zookeeper to be ready..."
sleep 15

# Start Kafka
docker-compose up -d kafka

echo "⏳ Waiting for Kafka to be ready..."
max_attempts=60
attempt=0
kafka_ready=false

while [ $attempt -lt $max_attempts ] && [ "$kafka_ready" = false ]; do
    if docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
        kafka_ready=true
        echo "✅ Kafka is ready!"
        break
    else
        echo "⏳ Kafka not ready yet, waiting... (attempt $((attempt + 1))/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
        
        # Check if Kafka container is still running
        if ! docker ps | grep -q kafka; then
            echo "❌ Kafka container stopped, checking logs..."
            docker-compose logs kafka --tail=10
            echo "🔄 Restarting Kafka..."
            docker-compose restart kafka
            sleep 10
        fi
    fi
done

if [ "$kafka_ready" = false ]; then
    echo "❌ Kafka failed to start after $max_attempts attempts"
    echo "Checking final logs..."
    docker-compose logs kafka --tail=20
    exit 1
fi

# Setup Kafka topics
echo "📨 Setting up Kafka topics..."
./scripts/setup-kafka-topics.sh

echo "✅ Kafka infrastructure is ready!"
