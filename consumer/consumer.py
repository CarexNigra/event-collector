from confluent_kafka import Consumer

from events_registry.key_manager import ProducerKeyManager
from events_registry.events_registry import events_mapping
from config.config import ConfigParser, KafkaConsumerProperties

import json
from google.protobuf.json_format import MessageToJson
from datetime import datetime
import os

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

# TODO: Do we need message received report? (by analogy with message delivery for producer)


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

# TODO: 
#  1. Event files:
#       - make path to be structured as folows: /YEAR/MONTH/DAY/HOUR/timestamp.json
#       - write file until it exceeds certain size (let's say 4mb, like at miro), then create a new file named as a timestamp of the next event
#  2. Logic:
#       - write a class that abstracts file writing (name parsing, folders creation, etc) and use in the consumer
#  3. Write test that checks consumer writes file to disk:
#       - mock consumer
#       - add check that event file written on disk

def save_message_to_json_locally(event_json_data, save_to_path):
    received_at_timestamp = datetime.fromtimestamp(int(event_json_data['context']['receivedAt']))
    received_at_formatted = received_at_timestamp.strftime('%Y-%m-%dT%H:%M:%S%z')
    print(received_at_formatted)

    folder_name = received_at_formatted[:13].replace('-', '_').replace(':', '')
    print(folder_name)

    # Check if the subfolder exists in the consumer_output folder
    folder_path = os.path.join(save_to_path, folder_name)

    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Save the dict as a JSON file with the name consisting of receivedAt timestamp + underscore + messageId
    file_name = f"{received_at_formatted.replace(':', '_')}_{event_json_data['context']['messageId']}.json"
    file_path = os.path.join(folder_path, file_name)

    with open(file_path, 'w') as json_file:
        json.dump(event_json_data, json_file)

    print(f"JSON file saved: {file_path}")



running = True # TODO: Should it be here?

def basic_consume_loop(consumer, topics, min_commit_count, save_to_path):
    try:
        consumer.subscribe(topics)
        msg_count = 0
        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue

            if msg.error():
                print("Kafka message error") # TODO: Implement logging here
            else:
                message_dict = parse_message(msg)
                save_message_to_json_locally(message_dict, save_to_path)
                
                msg_count += 1
                if msg_count % min_commit_count == 0:
                    consumer.commit(asynchronous=True)
    finally:
        # Close down consumer to commit final offsets.
        consumer.close()


def shutdown():
    running = False

# ==================================== #
# (3) Test that it works
# ==================================== #

if __name__=="__main__":
    # (1) Get general properties
    config_parser = ConfigParser(CONFIG_FILE_PATH)
    general_config_dict = config_parser.get_general_config()
    print("\nGeneral config dict:", general_config_dict)

    # (2) Launch consumer
    consumer = create_kafka_consumer()
    print("\nConsumer:", consumer)
    basic_consume_loop(consumer, [general_config_dict['kafka_topic']], general_config_dict['min_commit_count'], general_config_dict['save_to_path'])
    # shutdown()
    
    




    
