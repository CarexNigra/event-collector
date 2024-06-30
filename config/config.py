import tomllib
from pydantic import BaseModel, ConfigDict


# Write function get_config_path which would construct the path to the config file depending on the environment name: dev, stage, etc
# 

# TODO: Move to lib
def underscore_to_dot(string: str) -> str:
    string = string.replace('_', '.')
    return string


# TODO: To figure out which properties should be here
class KafkaConsumerProperties(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    group_id: str = 'foo'
    auto_offset_reset: str = 'smallest'
    
    model_config = ConfigDict(alias_generator=underscore_to_dot)


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



class ConfigParser:
    def __init__(self, path_to_config_toml):
        self._path_to_config_toml = path_to_config_toml
        with open(self._path_to_config_toml, 'rb') as file:
            self._config = tomllib.load(file)

    def _get_section(self, name: str) -> dict:
        section = self._config.get(name, None) # Outputs dict
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
