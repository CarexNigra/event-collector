import os
import abc 
from datetime import datetime, timedelta
from typing import List, Any, Optional
import uuid

import threading
import queue

import glob
import json

from io import BytesIO
from minio import Minio
from minio.error import S3Error

from confluent_kafka import Consumer
from google.protobuf.json_format import MessageToJson

from config.config import KafkaConsumerProperties, MinioProperties, get_config
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

from common.logger import get_logger

logger = get_logger()

# ==================================== #
# (1) Create consumer instance
# ==================================== #

def create_kafka_consumer(config: Optional[dict[str, Any]] = None) -> Consumer:
    if not config:
        config = get_config()['consumer']
    kafka_consumer_config = KafkaConsumerProperties(**config)

    logger.info(f"Kafka consumer config: {kafka_consumer_config}")
    return Consumer(kafka_consumer_config.model_dump(by_alias=True))


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
        logger.info(f"(2) Parsing. Event class data type: {type(event_json_data)}, data: \n{event_json_data}")
        return event_json_data


# ==================================== #
# (3) Set up stuff for Minio
# ==================================== #

def create_minio_client(config: Optional[dict[str, Any]] = None) -> Minio: 
    if not config:
        config = get_config()['minio']
    minio_config = MinioProperties(**config)

    logger.info(f"Minio config: {minio_config}, {type(minio_config)}")
    minio_config_dict = minio_config.model_dump(by_alias=True)
    # logger.info(f"Minio config: {minio_config_dict}, {type(minio_config_dict)}")
    minio_client = Minio(**minio_config_dict)
    return minio_client


def create_bucket(bucket_name: str, minio_client: Minio) -> None:
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' created successfully")
        else:
            logger.info(f"Bucket '{bucket_name}' already exists")
    except S3Error as exc:
        logger.info(f"Error occurred: {exc}")

# ==================================== #
# (4) Set up FileWriters
# ==================================== #

class FileWriterBase(abc.ABC):
    # NOTE: This is an abstract class to make file writing env agnostic

    def __init__(self, max_output_file_size):
        self._max_output_file_size = max_output_file_size
    
    def parse_received_at_date(self, message):
        # NOTE: The date is taken from the first message
        received_at_timestamp = datetime.fromtimestamp(int(message["context"]["receivedAt"]))
        date_dict = {
            "year": str(received_at_timestamp.year),
            "day": str(received_at_timestamp.day),
            "month": str(received_at_timestamp.month),
            "hour": str(received_at_timestamp.hour),
            "int_timestamp": str(message["context"]["receivedAt"]),
        }
        return date_dict
    
    def get_or_create_file_path(self, json_files: List[str], folder_path: str, date_dict: dict, messages_size: int, unique_consumer_id: str) -> str:
        # (1) Check existing files
        if json_files:
            # Select "most recent" file (by its event-timestamp name),
            most_recent_file_path = max(json_files, key=lambda f: int(os.path.splitext(os.path.basename(f).split('_')[-1])[0]))
            # Check its size in bytes
            # This needs to be overridden by subclasses because they handle file sizes differently
            file_size = self.get_file_size(most_recent_file_path)

            # Define the path file will be written to
            if file_size + messages_size < self._max_output_file_size:
                file_path = most_recent_file_path
            else:
                file_name = f"{unique_consumer_id}_{date_dict['int_timestamp']}.json"
                file_path = os.path.join(folder_path, file_name)

        # (2) Create file if there are no files
        if not json_files:
            file_name = f"{unique_consumer_id}_{date_dict['int_timestamp']}.json"
            file_path = os.path.join(folder_path, file_name)

        return file_path

    @abc.abstractmethod
    def get_file_size(self, file_path: str) -> int:
        pass

    @abc.abstractmethod
    def get_full_path(self, messages: List[dict], unique_consumer_id: str) -> str:
        pass

    @abc.abstractmethod
    def write_file(self, messages: List[dict], unique_consumer_id: str):
        pass


class LocalFileWriter(FileWriterBase):
    def __init__(self, root_path, max_output_file_size): # event_json_data
        super().__init__(max_output_file_size) 
        self._root_path = root_path

    def get_file_size(self, file_path: str) -> int:
        return os.path.getsize(file_path)

    def get_full_path(self, messages: List[dict], unique_consumer_id: str) -> str:
        first_message = messages[0]
        date_dict = self.parse_received_at_date(first_message)

        # (1) Check if the subfolder exists in the consumer_output folder
        folder_path = os.path.join(
            self._root_path, date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"]
        )

        # (2) Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

        # (3) Get all json files in the dir
        json_files = glob.glob(os.path.join(folder_path, "*.json"))

        # (4) Get file path
        serialized_messages = json.dumps(messages)
        messages_size = len(serialized_messages.encode('utf-8'))
        file_path = self.get_or_create_file_path(json_files, folder_path, date_dict, messages_size, unique_consumer_id)
        
        return file_path


    def write_file(self, messages: List[dict], unique_consumer_id: str):
        
        if not messages:
            return
        
        file_path = self.get_full_path(messages, unique_consumer_id)
        if file_path is None:
            return

        # Read existing data if file exists
        if os.path.exists(file_path):
            with open(file_path, "r") as json_file:
                try:
                    existing_data = json.load(json_file)
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []

        # Ensure existing data is a list (assuming the JSON data structure is a list of events)
        if not isinstance(existing_data, list):
            logger.info("The existing data is not a list. Cannot append new data")
            return

        # Append the new event data to existing data
        existing_data.extend(messages)

        # Write back the updated data
        with open(file_path, "w") as json_file:
            json.dump(existing_data, json_file)
        logger.info(f"(4) Saving. JSON file saved to: {file_path}")
        



class MinioFileWriter(FileWriterBase):
    def __init__(self, root_path, max_output_file_size, minio_client): 
        super().__init__(max_output_file_size) 
        self._root_path = root_path # = minio bucket_name TODO: should we rename it for comprehensibility?
        self._minio_client = minio_client

    def get_file_size(self, file_path: str) -> int:
        object_stat = self._minio_client.stat_object(self._root_path, file_path)
        return object_stat.size

    def get_full_path(self, messages: List[dict], unique_consumer_id: str):
        first_message = messages[0]
        date_dict = self.parse_received_at_date(first_message)

        # (1) Define folder path
        folder_path = os.path.join(
            date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"]
        )
        # (2) Get all json files in the dir
        objects = self._minio_client.list_objects(self._root_path, prefix=folder_path, recursive=False)
        json_files = [obj.object_name for obj in objects if obj.object_name.endswith('.json')]

        # (3) Check existing files
        serialized_messages = json.dumps(messages)
        messages_size = len(serialized_messages.encode('utf-8'))
        file_path = self.get_or_create_file_path(json_files, folder_path, date_dict, messages_size, unique_consumer_id)

        return file_path

    def write_file(self, messages: List[dict], unique_consumer_id: str):
        if not messages:
            return
        
        # (1) Get path
        file_path = self.get_full_path(messages, unique_consumer_id)

        # (2) Write
        # (2.1) Read existing data if the file exists
        try:
            response = self._minio_client.get_object(self._root_path, file_path)
            existing_data = json.load(response)
            response.close()
            response.release_conn()  # Important to close the response to avoid connection issues
        except S3Error as exc:
            if exc.code == 'NoSuchKey':
                existing_data = []
            else:
                raise  # Re-raise any other exceptions
    
        # Ensure existing data is a list (assuming the JSON data structure is a list of events)
        if not isinstance(existing_data, list):
            logger.info("The existing data is not a list. Cannot append new data.")
            return
        
        # Append the new event data to existing data
        existing_data.extend(messages)

        # Convert updated data back to JSON string
        json_data = json.dumps(existing_data)

        # Write the updated data back to MinIO
        self._minio_client.put_object(
            bucket_name=self._root_path,
            object_name=file_path,
            data=BytesIO(json_data.encode("utf-8")),
            length=len(json_data),
            content_type="application/json"
        )
        logger.info(f"(4) Saving. JSON file saved to MinIO at: {file_path}")


# ==================================== #
# (5) Set up EventConsumer
# ==================================== #

class EventConsumer:
    def __init__(self, 
                 file_writer: FileWriterBase, 
                 consumer: Consumer, 
                 consumer_group_id: str,
                 topics: List[str], 
                 batch_size: int, 
                 flush_interval: int
                 ):
        self._file_writer = file_writer
        self._consumer = consumer
        self._topics = topics
        self._batch_size = batch_size  # max number of messages to batch before writing
        self._flush_interval = timedelta(seconds=flush_interval)  # interval to write in-memory messages to storage, even if batch_size is not reached; in seconds
        self._message_queue = queue.Queue()  # in-memory queue for buffering raw messages
        self._lock = threading.Lock()  # to safely modify the message buffer
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
        parsed_messages = []
        unqiue_msgs = set() # To deduplicate messages having the same content (even if msg_ids are the same)
        self._lock.acquire()  # Manually acquire the lock (instead of with self._lock)
        try:
            while not self._message_queue.empty() and len(parsed_messages) < self._batch_size:
                raw_msg = self._message_queue.get()
                try:
                    # Attempt to parse the raw message
                    if raw_msg is not None and raw_msg not in unqiue_msgs:
                        message_dict: dict = parse_message(raw_msg)
                        parsed_messages.append(message_dict)
                        unqiue_msgs.add(raw_msg)
                except Exception as e:
                    logger.error(f"(2) Parsing. Error parsing message: {raw_msg}. Exception: {e}")
                    # Continue with next message, do not stop processing
            if parsed_messages:
                logger.info(f"(3) Flushing {len(parsed_messages)} parsed messages.")
                self._file_writer.write_file(parsed_messages, self._unique_consumer_id)  # Write batch of parsed messages
                self._consumer.commit(asynchronous=True)  # Commit offsets after writing
                # TODO: Figure out what is the best practice to commit, to avoid duplications when there are several replicas of the consumer
        finally:
            self._lock.release()  # Manually release the lock even if there's an error
        

    def run_consume_loop(self):
        try:
            self._consumer.subscribe(self._topics)
            
            while self._running: # Added to stop the loop
                msg = self._consumer.poll(timeout=1.0) # Waits for up to 1 second before returning None if no message is available.
                logger.info(f"(1) Consumption. Message: {msg}")
                if msg is None:
                    continue
                if msg.error():
                    logger.info("(1) Consumption. Kafka message error")
                else:
                    self._message_queue.put(msg) 

                    # Flushing option by batch size
                    if self._message_queue.qsize() >= self._batch_size:
                        self._flush_messages()

                    # Flushing option by time
                    current_time = datetime.now()
                    if current_time - self._last_flush_time >= self._flush_interval:
                        self._flush_messages()
                        self._last_flush_time = current_time
            
        finally:
            # Close down consumer to commit final offsets.
            self._flush_messages()
            self._consumer.close()



# ==================================== #
# (6) Test that it works
# ==================================== #

# ENVIRONMENT=dev PYTHONPATH=. poetry run python ./consumer/consumer.py
# ENVIRONMENT=stg PYTHONPATH=. poetry run python ./consumer/consumer.py

if __name__ == "__main__":
    # (1) Get general properties
    general_config_dict = get_config()['general']
    consumer_config_dict = get_config()['consumer']

    # # (2 Option 1) Instantiate Locacl file writer
    # file_writer = LocalFileWriter(
    #     root_path=general_config_dict["root_path"],
    #     max_output_file_size=general_config_dict["max_output_file_size"]
    # )

    # (2 Option 2) Instantiate Minio file writer
    minio_client = create_minio_client()
    create_bucket(general_config_dict["root_path"], minio_client)
    file_writer = MinioFileWriter(
        root_path=general_config_dict["root_path"],
        minio_client=minio_client,
        max_output_file_size=general_config_dict["max_output_file_size"]
    )

    # (3) Instantiate consumer
    consumer = create_kafka_consumer()
    event_consumer = EventConsumer(
        file_writer=file_writer,
        consumer=consumer,
        consumer_group_id=consumer_config_dict['group_id'],
        topics=[general_config_dict["kafka_topic"]],
        batch_size = general_config_dict["consumer_batch_size"], 
        flush_interval = general_config_dict["flush_interval"],
    )

    # (4) Write
    event_consumer.run_consume_loop()


