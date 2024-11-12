#!/bin/sh

KAFKA_BROKER_LIST="kafka-broker-1:9092,kafka-broker-2:9094,kafka-broker-3:9095"

echo "Waiting for Kafka brokers to be reachable..."
for i in {1..10}; do
  kafka-topics --bootstrap-server "$KAFKA_BROKER_LIST" --list && break || sleep 5;
done

echo "Creating Kafka topics"
kafka-topics --bootstrap-server "$KAFKA_BROKER_LIST" \
  --create --if-not-exists --topic "${KAFKA_TOPIC}" --replication-factor 3 --partitions 3

echo "Successfully created the following topics:"
kafka-topics --bootstrap-server "$KAFKA_BROKER_LIST" --list
