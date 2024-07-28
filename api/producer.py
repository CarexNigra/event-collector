from functools import lru_cache

from confluent_kafka import Producer

from config.config import ConfigParser, KafkaProducerProperties, get_config_path

CONFIG_FILE_PATH = get_config_path()

# ==================================== #
# (1) Create producer instance
# ==================================== #


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


# ==================================== #
# (2) Test that it works
# ==================================== #

if __name__ == "__main__":
    producer = create_kafka_producer()
    print("\nProducer:", producer)
