#!/bin/sh

KAFKA_BROKER_LIST="localhost:9092,localhost:9094,localhost:9095"

echo "Waiting for Kafka brokers to be reachable..."
for i in {1..10}; do
  kafka-topics --bootstrap-server "$KAFKA_BROKER_LIST" --list && break || sleep 5;
done

echo "Creating Kafka topics"
kafka-topics --bootstrap-server "$KAFKA_BROKER_LIST" \
  --create --if-not-exists --topic event-messages --replication-factor 3 --partitions 3

echo "Successfully created the following topics:"
kafka-topics --bootstrap-server "$KAFKA_BROKER_LIST" --list
