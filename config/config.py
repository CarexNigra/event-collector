import os
import tomllib

from pydantic import BaseModel, ConfigDict


def get_config_path():
    environmnet_type: str = os.environ.get("ENVIRONMENT", "dev")
    configs_path = os.path.abspath(os.path.dirname(__file__))
    config_fpath = f"{configs_path}/{environmnet_type}.toml"
    if os.path.exists(config_fpath):
        return config_fpath
    else:
        raise Exception(f"There is no config file for {environmnet_type} environment")


def underscore_to_dot(string: str) -> str:
    string = string.replace("_", ".")
    return string


# TODO: To figure out which properties should be here
class KafkaConsumerProperties(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    group_id: str = "foo"
    auto_offset_reset: str = "smallest"

    model_config = ConfigDict(alias_generator=underscore_to_dot)


class KafkaProducerProperties(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    retries: int = 2147483647
    max_in_flight_requests_per_connection: int = 1
    acks: str = "all"
    batch_size: int = 16384
    enable_idempotence: bool = True
    delivery_timeout_ms: int = 120000
    linger_ms: int = 5
    request_timeout_ms: int = 30000

    model_config = ConfigDict(alias_generator=underscore_to_dot)


class ConfigParser:
    def __init__(self, path_to_config_toml):
        self._path_to_config_toml = path_to_config_toml
        with open(self._path_to_config_toml, "rb") as file:
            self._config = tomllib.load(file)

    def _get_section(self, name: str) -> dict:
        section = self._config.get(name, None)  # Outputs dict
        if not section:
            raise Exception(f"No `{name}` config found in the file, located at: {self._path_to_config_toml}")
        return section

    def get_consumer_config(self):
        config_dict = self._get_section("consumer")
        return config_dict

    def get_producer_config(self):
        config_dict = self._get_section("producer")
        return config_dict

    def get_general_config(self):
        config_dict = self._get_section("general")
        return config_dict
