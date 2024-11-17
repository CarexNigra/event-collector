import os
import tomllib
from functools import lru_cache

from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.logger import get_logger

logger = get_logger("config-parser")


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
        logger.error(f"There is no config file for {environmnet_type} environment")
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


########################################
# (1) Producer config classes
########################################


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
    """
    Model representing configuration properties for the producer app.
    Args:
        kafka_topic (str): topic which producer app would send messages to
    """


class ProducerConfig(BaseModel):
    kafka: KafkaProducerProperties
    app: ProducerAppConfig
    """
    Model representing configuration properties for a Kafka producer and producer app.
    Args:
        kafka (KafkaProducerProperties): model representing configuration properties for a Kafka producer.
        app (ProducerAppConfig): model representing configuration properties for the producer app.
    """


########################################
# (2) Consumer config classes
########################################


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


class ConsumerAppConfig(BaseModel):
    kafka_topic: str
    max_output_file_size: int
    flush_interval: int
    root_path: str
    """
    Model representing configuration properties for the producer app.
    Args:
        kafka_topic (str): topic which producer app would send messages to
        max_output_file_size (int): file size (in bytes) not to be exceeded when flushing messages into a file
        flush_interval (int): the interval (in seconds) for consumed message queue to be flushed to a new file
        root_path (str): path to local folder where files with events will be saved 
    """


class MinioProperties(BaseSettings):
    endpoint: str
    access_key: str | None
    secret_key: str | None
    secure: bool
    """
    Model representing configuration properties for MinIO.
    Args:
        endpoint (str): MinIO server endpoint.
        access_key (str): Access key for authentication (username). NOTE: Should be fetched from env vars
        secret_key (str): Secret key for authentication (password). NOTE: Should be fetched from env vars
        secure (bool): Flag indicating whether to use a secure connection.
    """

    model_config = SettingsConfigDict(env_prefix="MINIO_")

    # NOTE: This is a hack that allows to overcome pydantic args checks errors related to env vars
    # (access_key and secret_key) when we istantiate MinioProperties class from ConsumerConfig class
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ConsumerConfig(BaseModel):
    kafka: KafkaConsumerProperties
    app: ConsumerAppConfig
    minio: MinioProperties
    """
    Model representing configuration properties for a Kafka producer and producer app.
    Args:
        kafka (KafkaConsumerProperties): model representing configuration properties for a Kafka consumer.
        app (ConsumerAppConfig): model representing configuration properties for the consumer app.
        minio (ProducerAppConfig): model representing configuration properties for MinIO.
    """


########################################
# (3) Functions to get configs
########################################


@lru_cache
def get_producer_config() -> ProducerConfig:
    """
    Retrieves and parses the Kafka producer configuration from a configuration file. 
    It uses lru_cache to cache the configuration, ensuring that subsequent calls to this function 
    do not re-read the file but instead return the cached configuration.
    """
    config_fpath = get_config_path()
    with open(config_fpath, "rb") as file:
        raw_config = tomllib.load(file)
    raw_producer_config = raw_config.get("producer")
    if not raw_producer_config:
        logger.error("Can't open producer config file")
        raise Exception("Can't open producer config file")
    config = ProducerConfig(**raw_producer_config)
    return config


@lru_cache
def get_consumer_config() -> ConsumerConfig:
    """
    This function retrieves and parses the Kafka consumer configuration from a configuration file. 
    It uses lru_cache to cache the configuration, ensuring that subsequent calls to this function 
    do not re-read the file but instead return the cached configuration.
    """
    config_fpath = get_config_path()
    with open(config_fpath, "rb") as file:
        raw_config = tomllib.load(file)
    raw_consumer_config = raw_config.get("consumer")
    if not raw_consumer_config:
        logger.error("Can't open consumer config file")
        raise Exception("Can't open consumer config file")
    config = ConsumerConfig(**raw_consumer_config)
    return config
