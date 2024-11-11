import os
import tomllib
from functools import lru_cache
from typing import Any

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


class ConfigParser:
    """
    Class responsible for loading and parsing the configuration file.
    """

    def __init__(self, path_to_config_toml: str) -> None:
        """
        Initializes the ConfigParser with the path to the TOML configuration file.
        Input:
            path_to_config_toml (str): Path to the configuration TOML file.
        """
        self._path_to_config_toml: str = path_to_config_toml
        with open(self._path_to_config_toml, "rb") as file:
            self._config: Any = tomllib.load(file)

    def _get_section(self, name: str) -> dict:
        """
        Retrieves a specific section from the configuration.
        Input:
            name (str): The section name to retrieve.
        Output:
            dict[str, Any]: The configuration data for the specified section.
        """
        section = self._config.get(name, None)  # Outputs dict
        if not section:
            raise Exception(f"No `{name}` config found in the file, located at: {self._path_to_config_toml}")
        return section

    def get_all_configs_dict(self) -> dict[str, dict[str, Any]]:
        """
        Retrieve all configuration sections.
        Output:
            dict[str, dict[str, Any]]: A dictionary of all configuration sections and their contents.
        """
        all_configs_dict = {}
        for section_name in self._config.keys():
            all_configs_dict[section_name] = self._get_section(section_name)
        return all_configs_dict


class MinioProperties(BaseSettings):
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool
    """
    Model representing configuration properties for MinIO.
    Args:
        endpoint (str): MinIO server endpoint.
        access_key (str): Access key for authentication (username).
        secret_key (str): Secret key for authentication (password).
        secure (bool): Flag indicating whether to use a secure connection.
    """

    class Config:
        env_prefix = "MINIO_"


@lru_cache
def get_config() -> dict[str, dict[str, Any]]:
    """
    Retrieve the application configuration, cached for improved performance.
    Output:
        dict[str, dict[str, Any]]: A dictionary containing all configuration sections.
    """
    CONFIG_FILE_PATH = get_config_path()
    config_parser = ConfigParser(CONFIG_FILE_PATH)
    all_configs_dict = config_parser.get_all_configs_dict()

    if not all_configs_dict:
        all_configs_dict = {}

    return all_configs_dict
