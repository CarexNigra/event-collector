import os
import tomllib
from functools import lru_cache

from pydantic import AliasGenerator, BaseModel, ConfigDict 
from pydantic_settings import BaseSettings


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
    bootstrap_servers: str
    group_id: str 
    auto_offset_reset: str 
    partition_assignment_strategy: str

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

    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            serialization_alias=underscore_to_dot,
        )
    )


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
    
    def get_all_configs_dict(self):
        all_configs_dict = {}
        for section_name in self._config.keys():
            all_configs_dict[section_name] = self._get_section(section_name)
        return all_configs_dict
    

class MinioProperties(BaseSettings):
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool 

    class Config:
        env_prefix = "MINIO_"


@lru_cache
def get_config():
    CONFIG_FILE_PATH = get_config_path()
    config_parser = ConfigParser(CONFIG_FILE_PATH)
    all_configs_dict = config_parser.get_all_configs_dict()
    return all_configs_dict
