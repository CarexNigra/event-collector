from confluent_kafka import Consumer

from events_registry.key_manager import ProducerKeyManager
from events_registry.events_registry import events_mapping
from config.config import ConfigParser, KafkaConsumerProperties

from datetime import datetime
import os
import json
from google.protobuf.json_format import MessageToJson


CONFIG_FILE_PATH = 'config/dev.toml' 

# ==================================== #
# (1) Create consumer instance
# ==================================== #

def create_kafka_consumer() -> Consumer:
    config_parser = ConfigParser(CONFIG_FILE_PATH)
    kafka_consumer_config_dict = config_parser.get_consumer_config()
    kafka_consumer_config = KafkaConsumerProperties(**kafka_consumer_config_dict)
    print("Kafka consumer config:", kafka_consumer_config)
    return Consumer(kafka_consumer_config.model_dump(by_alias=True))

# TODO: Do we need message received report? (by analogy with message delivery for producer). Can be done with Prometheus 


# ==================================== #
# (2) Consume messages from kafka
# ==================================== #

def parse_message(message):

    event_type = ProducerKeyManager(producer_key=message.key().decode("utf-8")).get_event_type_from_key()
    # print("\nEvent type: ", event_type)

    binary_value =  message.value()
    # print("\nValue:", binary_value)

    if event_type in events_mapping:

        event_class = events_mapping.get(event_type)
        event = event_class()
        event.ParseFromString(binary_value)
        event_json_string = MessageToJson(event)
        event_json_data = json.loads(event_json_string)
        print(f"Event class data type: {type(event_json_data)}, data: \n{event_json_data}")
        return event_json_data

# TODO: write file until it exceeds certain size (let's say 4mb, like at miro), then create a new file named as a timestamp of the next event

class LocalFileWriter:
    def __init__(self, event_json_data, environment, root_path):
        self._event_json_data = event_json_data
        self._environment = environment
        self._root_path = root_path

    def parse_received_at_date(self):
        received_at_timestamp = datetime.fromtimestamp(int(self._event_json_data['context']['receivedAt']))
        date_dict = {
            "year": str(received_at_timestamp.year),
            "day": str(received_at_timestamp.day),
            "month": str(received_at_timestamp.month),
            "hour": str(received_at_timestamp.hour),
            "int_timestamp": str(self._event_json_data['context']['receivedAt'])
        }
        return date_dict
    
    def get_full_path(self):
        if self._environment == 'dev':
            date_dict = self.parse_received_at_date()
            # Check if the subfolder exists in the consumer_output folder
            folder_path = os.path.join(self._root_path, 
                                       date_dict['year'], 
                                       date_dict['month'], 
                                       date_dict['day'], 
                                       date_dict['hour'])

            # Create the folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Save the dict as a JSON file with the name consisting of receivedAt timestamp + underscore + messageId
            file_name = f"{date_dict['int_timestamp']}.json"
            file_path = os.path.join(folder_path, file_name)
            return file_path
        else:
            print(f"No path defined for {self._environment} environment")
    
    def write_file(self):
        if self._environment == 'dev':
            file_path = self.get_full_path()
            with open(file_path, 'w') as json_file:
                json.dump(self._event_json_data, json_file)
            print(f"JSON file saved for {self._environment} saved to: {file_path}")
        else:
            print(f"No saving function defined for {self._environment} environment")


def basic_consume_loop(consumer, topics, min_commit_count, save_to_path):
    try:
        consumer.subscribe(topics)
        msg_count = 0
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None: 
                continue

            if msg.error():
                print("Kafka message error") # TODO: Implement logging here
            else:
                message_dict = parse_message(msg)
                file_writer = LocalFileWriter(
                    event_json_data = message_dict, 
                    environment = 'dev', 
                    root_path = save_to_path
                )
                file_writer.write_file()
                
                msg_count += 1
                if msg_count % min_commit_count == 0:
                    consumer.commit(asynchronous=True)
    finally:
        # Close down consumer to commit final offsets.
        consumer.close()




# ==================================== #
# (3) Test that it works
# ==================================== #

if __name__=="__main__":
    # (1) Get general properties
    config_parser = ConfigParser(CONFIG_FILE_PATH)
    general_config_dict = config_parser.get_general_config()
    # print("\nGeneral config dict:", general_config_dict)
    

    # (2) Launch consumer
    consumer = create_kafka_consumer()
    # print("\nConsumer:", consumer)    
    basic_consume_loop(
        consumer, 
        [general_config_dict['kafka_topic']], 
        general_config_dict['min_commit_count'], 
        general_config_dict['save_to_path'],
    )

