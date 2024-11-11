from functools import lru_cache
from typing import Any, Optional

from confluent_kafka import Producer

from common.logger import get_logger
from config.config import KafkaProducerProperties, get_config

logger = get_logger()


# ==================================== #
# (1) Create producer instance
# ==================================== #


@lru_cache
def create_kafka_producer() -> Producer:
    """
    Creates and returns a Kafka producer instance configured with application-specific settings.
    This function uses a cached instance to ensure that the producer is created only once
    per session, leveraging `lru_cache` to improve performance and avoid repeated setup.

    Returns:
        Producer: A configured Kafka producer instance for publishing events.
    """
    kafka_producer_config_dict = get_config()["producer"]
    kafka_producer_config = KafkaProducerProperties(**kafka_producer_config_dict)

    logger.info(f"Kafka producer config: {kafka_producer_config}")
    return Producer(kafka_producer_config.model_dump(by_alias=True))


def delivery_report(err: Optional[BaseException], msg: Any) -> None:
    """
    Callback function invoked by the Kafka producer to report whether a message
    was successfully delivered to a topic or if an error occurred during delivery.

    Args:
        err (Optional[BaseException]): An error instance if message delivery failed;
                                       None if successful.
        msg (Any): The Kafka message that was attempted to be delivered.
    """
    if err is not None:
        logger.info(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
