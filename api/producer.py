from pydantic import BaseModel, ConfigDict
from confluent_kafka import Producer
from functools import lru_cache

from config.config import ConfigParser


KAFKA_TOPIC = 'event-messages'
CONFIG_FILE_PATH = 'config/dev.toml' 


# # TODO: Move to lib
# def underscore_to_dot(string: str) -> str:
#     string = string.replace('_', '.')
#     return string


# class KafkaProducerProperties(BaseModel):
#     bootstrap_servers: str = "localhost:9092"
#     retries: int = 2147483647
#     max_in_flight_requests_per_connection: int = 1 
#     acks: str = 'all'
#     batch_size: int = 16384
#     enable_idempotence: bool = True
#     delivery_timeout_ms: int = 120000
#     linger_ms: int = 5
#     request_timeout_ms: int = 30000

#     model_config = ConfigDict(alias_generator=underscore_to_dot)


@lru_cache
def create_kafka_producer() -> Producer:
    config_parser = ConfigParser(CONFIG_FILE_PATH)
    kafka_producer_config_dict = config_parser.get_producer_config()
    kafka_producer_config = KafkaProducerProperties(**kafka_producer_config_dict)
    print("Kafka producer config:", kafka_producer_config)
    return Producer(kafka_producer_config.model_dump(by_alias=True))


def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


# if __name__=="__main__":
#     producer = create_kafka_producer()
#     print("\n", producer)