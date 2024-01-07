
from confluent_kafka import Producer
from functools import lru_cache


    
KAFKA_TOPIC = 'event_messages'


@lru_cache
def create_kafka_producer():
    kafka_producer_config = {"bootstrap.servers": "localhost:9092"} 
    # TODO: I cannot figure out how to get rid of this dependency from config and fake in
    return Producer(kafka_producer_config)
