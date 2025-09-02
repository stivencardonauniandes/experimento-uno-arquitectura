#!/bin/bash

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
sleep 30

# Kafka container name
KAFKA_CONTAINER="kafka"

# Create topics
echo "Creating Kafka topics..."

docker exec $KAFKA_CONTAINER kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic stock-update \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

docker exec $KAFKA_CONTAINER kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic order-created \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

docker exec $KAFKA_CONTAINER kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic order-processed \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

docker exec $KAFKA_CONTAINER kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic health-check \
    --partitions 1 \
    --replication-factor 1 \
    --if-not-exists

docker exec $KAFKA_CONTAINER kafka-topics --create \
    --bootstrap-server localhost:9092 \
    --topic system-error \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

# List topics
echo "Created topics:"
docker exec $KAFKA_CONTAINER kafka-topics --list --bootstrap-server localhost:9092

echo "Kafka topics setup completed!"
