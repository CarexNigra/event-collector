from datetime import datetime, timedelta
from typing import List, Any, Optional
import uuid

import json

from confluent_kafka import Consumer
from google.protobuf.json_format import MessageToJson

from config.config import KafkaConsumerProperties, get_config
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

# import consumer
from consumer.file_writers import FileWriterBase 
# from consumer import file_writers as fw

import traceback
from common.logger import get_logger

logger = get_logger()

# ==================================== #
# (1) Create consumer instance
# ==================================== #

def create_kafka_consumer(config: Optional[dict[str, Any]] = None) -> Consumer:
    if not config:
        config = get_config()['consumer']
    logger.info(f"Kafka consumer raw config: {config}")
    kafka_consumer_config = KafkaConsumerProperties(**config)
    kafka_consumer_config_dict = kafka_consumer_config.model_dump(by_alias=True)
    logger.info(f"Kafka consumer config dict: {kafka_consumer_config_dict}")
    return Consumer(**kafka_consumer_config_dict)


# TODO: Do we need message received report? (by analogy with message delivery for producer). Can be done with Prometheus

# ==================================== #
# (2) Parse messages from kafka
# ==================================== #

def parse_message(message):
    event_type = ProducerKeyManager(producer_key=message.key().decode("utf-8")).get_event_type_from_key()
    # logger.debug(f"Event type: {event_type}")

    binary_value = message.value()
    # logger.debug(f"Value: {binary_value}")

    if event_type in events_mapping:
        event_class = events_mapping.get(event_type)
        event = event_class()
        event.ParseFromString(binary_value)
        event_json_string = MessageToJson(event)
        event_json_data = json.loads(event_json_string)
        logger.info(f"(2) Parsing. Event class data type: {type(event_json_data)}, data: {event_json_data}")
        return event_json_data


# ==================================== #
# (3) Set up EventConsumer
# ==================================== #

class EventConsumer:
    def __init__(self, 
                 file_writer: FileWriterBase, 
                 consumer: Consumer, 
                 consumer_group_id: str,
                 topics: List[str], 
                 max_output_file_size: int, 
                 flush_interval: int
                 ):
        self._file_writer = file_writer
        self._consumer = consumer
        self._topics = topics
        self._max_output_file_size = max_output_file_size  # max size of messages batch (in bytes) to collect before writing
        self._flush_interval = timedelta(seconds=flush_interval)  # interval to write in-memory messages to storage, even if max_output_file_size is not reached; in seconds
        self._message_queue = []  # in-memory queue for buffering raw messages
        self._last_flush_time = datetime.now()
        self._running = True  # Added this flag to control the loop

        # unique_consumer_id is needed to be added to the file name (to force different consumers' writing to different files)
        consumer_id = consumer.memberid()
        if not consumer_group_id or not consumer_id:
            self._unique_consumer_id = str(uuid.uuid4())
        else:
            self._unique_consumer_id = f"{consumer_group_id}_{consumer_id}"

    def stop(self):
        """Stop consumption loop"""
        self._running = False  # Added a method to stop the loop
        self._flush_messages()  # Ensure remaining messages are written when stopping
    
    def _flush_messages(self):
        """Flush messages in the buffer to storage"""
        logger.info(f"(3) Flushing {len(self._message_queue)} parsed messages.")
        self._file_writer.write_file(self._message_queue, self._unique_consumer_id)  # Write batch of parsed messages
        self._consumer.commit(asynchronous=True)  # Commit offsets after writing
        self._message_queue = []

    def run_consume_loop(self):
        queue_size_bytes = 0
        unqiue_msgs = set()
        
        try:
            self._consumer.subscribe(self._topics)
            
            while self._running: # Added to stop the loop
                raw_msg = self._consumer.poll(timeout=1.0) 
                # Waits for up to 1 second before returning None if no message is available.
                logger.info(f"(1) Consumption. Message: {raw_msg}")

                if raw_msg is None:
                    continue

                if raw_msg.error():
                    logger.info("(1) Consumption. Kafka message error")
                
                try:
                    if raw_msg not in unqiue_msgs:
                        # Parse message
                        msg_dict = parse_message(raw_msg)
                        msg_str = json.dumps(msg_dict)
                        msg_size = len((msg_str + "\n").encode("utf-8")) 
                        
                        # No flushing conditions, message is added to queue    
                        if queue_size_bytes + msg_size <= self._max_output_file_size:
                            self._message_queue.append(msg_str)
                            queue_size_bytes += msg_size
                            unqiue_msgs.add(raw_msg)
                        
                        # Flushing option by queue size, message added to empty queue after flushing
                        else:
                            self._flush_messages()
                            self._message_queue.append(msg_str)
                            queue_size_bytes = msg_size
                            unqiue_msgs = set([raw_msg])

                        # Flushing option by time 
                        current_time = datetime.now()
                        if current_time - self._last_flush_time >= self._flush_interval:
                            self._flush_messages()
                            self._last_flush_time = current_time
                            queue_size_bytes = 0
                            unqiue_msgs = set()
                
                except Exception as e:
                    stack_trace = traceback.format_exc()
                    # print(stack_trace)
                    logger.error(f"(2) Parsing. Error parsing message: {raw_msg}. Exception: {stack_trace}")
                    # Continue with next message, do not stop processing

        finally:
            # Close down consumer to commit final offsets.
            self._flush_messages()
            self._consumer.close()



# ==================================== #
# (6) Test that it works
# ==================================== #

# ENVIRONMENT=dev PYTHONPATH=. poetry run python ./consumer/event_consumer.py
# ENVIRONMENT=stg PYTHONPATH=. poetry run python ./consumer/event_consumer.py

# if __name__ == "__main__":

#     from file_writers import LocalFileWriter, MinioFileWriter, create_bucket, create_minio_client
#     # (1) Get general properties
#     general_config_dict = get_config()['general']
#     consumer_config_dict = get_config()['consumer']

#     # (2 Option 1) Instantiate Locacl file writer
#     file_writer = LocalFileWriter(
#         root_path=general_config_dict["root_path"],
#     )

#     # # (2 Option 2) Instantiate Minio file writer
#     # minio_client = create_minio_client()
#     # create_bucket(general_config_dict["root_path"], minio_client)
#     # file_writer = MinioFileWriter(
#     #     root_path=general_config_dict["root_path"],
#     #     minio_client=minio_client,
#     # )

#     # (3) Instantiate consumer
#     consumer = create_kafka_consumer()
#     event_consumer = EventConsumer(
#         file_writer=file_writer,
#         consumer=consumer,
#         consumer_group_id=consumer_config_dict['group_id'],
#         topics=[general_config_dict["kafka_topic"]],
#         max_output_file_size = general_config_dict["max_output_file_size"], 
#         flush_interval = general_config_dict["flush_interval"],
#     )

#     # (4) Write
#     event_consumer.run_consume_loop()


