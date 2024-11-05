from functools import lru_cache

from confluent_kafka import Producer

from config.config import KafkaProducerProperties, get_config

from common.logger import get_logger

logger = get_logger()


# ==================================== #
# (1) Create producer instance
# ==================================== #


@lru_cache
def create_kafka_producer() -> Producer:
    kafka_producer_config_dict = get_config()['producer']
    # print(">>>", kafka_producer_config_dict) # TODO: fix why properties not being initialized with config values
    kafka_producer_config = KafkaProducerProperties(**kafka_producer_config_dict)
    
    logger.info(f"Kafka producer config: {kafka_producer_config}")
    return Producer(kafka_producer_config.model_dump(by_alias=True))


def delivery_report(err, msg):
    if err is not None:
        logger.info(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


# ==================================== #
# (2) Test that it works
# ==================================== #

if __name__ == "__main__":
    producer = create_kafka_producer()
    logger.info(f"\nProducer: {producer}")
