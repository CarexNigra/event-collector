from pydantic import BaseModel, ConfigDict
import tomllib
from confluent_kafka import Producer
from functools import lru_cache


KAFKA_TOPIC = 'event-messages'
CONFIG_FILE_PATH = 'test_config.toml' 


def underscore_to_dot(string: str) -> str:
    string = string.replace('_', '.')
    return string


class KafkaProducerProperties(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    retries: int = 2147483647
    max_in_flight_requests_per_connection: int = 1 
    acks: str = 'all'
    batch_size: int = 16384
    enable_idempotence: bool = True
    delivery_timeout_ms: int = 120000
    linger_ms: int = 5
    request_timeout_ms: int = 30000

    model_config = ConfigDict(alias_generator=underscore_to_dot)


def parse_kafka_producer_config(file_path):
    with open(file_path, 'rb') as file:
        config = tomllib.load(file)
    producer_config = config.get("producer", None) # Outputs dict
    if not producer_config:
        raise Exception(f"No producer config found in the file, located at: {file_path}")
    return KafkaProducerProperties(**producer_config)


@lru_cache
def create_kafka_producer() -> Producer:
    kafka_producer_config = parse_kafka_producer_config(CONFIG_FILE_PATH)
    return Producer(kafka_producer_config.model_dump(by_alias=True))


def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
