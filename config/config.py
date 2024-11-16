import os
import tomllib
from functools import lru_cache

from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic_settings import BaseSettings


def get_config_path() -> str:
    """
    Determines the path to the configuration file based on the environment.
    Output:
        str: The path to the configuration file.
    """
    environmnet_type: str = os.environ.get("ENVIRONMENT", "dev")
    configs_path = os.path.abspath(os.path.dirname(__file__))
    config_fpath = f"{configs_path}/{environmnet_type}.toml"
    if os.path.exists(config_fpath):
        return config_fpath
    else:
        raise Exception(f"There is no config file for {environmnet_type} environment")


def underscore_to_dot(string: str) -> str:
    """
    Converts underscores in a string to dots.
    Input:
        string (str): The input string (with underscores).
    Output:
        str: The modified string with underscores replaced by dots.
    """
    string = string.replace("_", ".")
    return string


class KafkaProducerProperties(BaseModel):
    bootstrap_servers: str
    retries: int
    max_in_flight_requests_per_connection: int
    acks: str
    batch_size: int
    enable_idempotence: bool
    delivery_timeout_ms: int
    linger_ms: int
    request_timeout_ms: int
    """
    Model representing configuration properties for a Kafka producer.
    Args:
        bootstrap_servers (str): Comma-separated Kafka server addresses (brokers).
        retries (int): Number of retries for sending a message.
        max_in_flight_requests_per_connection (int): Max inflight requests per connection.
        acks (str): Acknowledgment policy for message delivery.
        batch_size (int): Size of each message batch in bytes.
        enable_idempotence (bool): Enable idempotence for the producer.
        delivery_timeout_ms (int): Timeout in milliseconds for message delivery.
        linger_ms (int): Time in milliseconds for batching messages.
        request_timeout_ms (int): Timeout for producer requests.
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            serialization_alias=underscore_to_dot,
        )
    )


class ProducerAppConfig(BaseModel):
    kafka_topic: str


class ProducerConfig(BaseModel):
    kafka: KafkaProducerProperties
    app: ProducerAppConfig


class KafkaConsumerProperties(BaseModel):
    bootstrap_servers: str
    group_id: str
    auto_offset_reset: str
    partition_assignment_strategy: str
    """
    Model representing configuration properties for a Kafka consumer.
    Args:
        bootstrap_servers (str): Comma-separated Kafka server addresses (brokers).
        group_id (str): Consumer group ID for Kafka.
        auto_offset_reset (str): Policy for resetting offsets.
        partition_assignment_strategy (str): Strategy for partition assignment.
    """

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            serialization_alias=underscore_to_dot,
        )
    )


class MinioProperties(BaseSettings):
    endpoint: str
    secure: bool
    access_key: str | None = None
    secret_key: str | None = None
    """
    Model representing configuration properties for MinIO.
    Args:
        endpoint (str): MinIO server endpoint.
        access_key (str): Access key for authentication (username).
        secret_key (str): Secret key for authentication (password).
        secure (bool): Flag indicating whether to use a secure connection.
    """

    model_config = ConfigDict(env_prefix="MINIO_") # type: ignore


class ConsumerAppConfig(BaseModel):
    kafka_topic: str
    max_output_file_size: int
    flush_interval: int
    root_path: str


class ConsumerConfig(BaseModel):
    kafka: KafkaConsumerProperties
    minio: MinioProperties
    app: ConsumerAppConfig


@lru_cache
def get_producer_config() -> ProducerConfig:
    config_fpath = get_config_path()
    with open(config_fpath, "rb") as file:
        raw_config = tomllib.load(file)
    raw_producer_config = raw_config.get("producer")
    if not raw_producer_config:
        raise Exception("Can't open producer config file")
    config = ProducerConfig(**raw_producer_config)
    return config


@lru_cache
def get_consumer_config() -> ConsumerConfig:
    config_fpath = get_config_path()
    with open(config_fpath, "rb") as file:
        raw_config = tomllib.load(file)
    raw_consumer_config = raw_config.get("consumer")
    if not raw_consumer_config:
        raise Exception("Can't open consumer config file")
    config = ConsumerConfig(**raw_consumer_config)
    return config
