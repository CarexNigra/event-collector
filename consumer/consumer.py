import os
import abc 
from datetime import datetime
from typing import List

import glob
import json

from io import BytesIO
from minio import Minio
from minio.error import S3Error

from confluent_kafka import Consumer
from google.protobuf.json_format import MessageToJson

from config.config import ConfigParser, KafkaConsumerProperties, get_config_path
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

CONFIG_FILE_PATH = get_config_path()

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
# (2) Parse messages from kafka
# ==================================== #

def parse_message(message):
    event_type = ProducerKeyManager(producer_key=message.key().decode("utf-8")).get_event_type_from_key()
    # print("\nEvent type: ", event_type)

    binary_value = message.value()
    # print("\nValue:", binary_value)

    if event_type in events_mapping:
        event_class = events_mapping.get(event_type)
        event = event_class()
        event.ParseFromString(binary_value)
        event_json_string = MessageToJson(event)
        event_json_data = json.loads(event_json_string)
        print(f"Event class data type: {type(event_json_data)}, data: \n{event_json_data}")
        return event_json_data


# ==================================== #
# (3) Set up stuff for Minio
# ==================================== #

def create_minio_client() -> Minio: 
    # TODO: Move credentials from here to stg config
    minio_client = Minio(
                "localhost:9000", 
                # following keys are from the environment variables in docker-compose.yaml 
                access_key="minio_user",  
                secret_key="minio_password",  
                secure=False  # Set to True if using HTTPS
            )
    return minio_client

def create_bucket(bucket_name: str, minio_client: Minio) -> None:
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created successfully.")
        else:
            print(f"Bucket '{bucket_name}' already exists.")
    except S3Error as exc:
        print("Error occurred: ", exc)

# ==================================== #
# (3) Set up FileWriters
# ==================================== #

class FileWriter(abc.ABC):
    # NOTE: This is an abstract class to make file writing env agnostic

    def __init__(self, event_json_data, max_output_file_size):
        self._event_json_data = event_json_data
        self._max_output_file_size = max_output_file_size
    
    def parse_received_at_date(self):
        received_at_timestamp = datetime.fromtimestamp(int(self._event_json_data["context"]["receivedAt"]))
        date_dict = {
            "year": str(received_at_timestamp.year),
            "day": str(received_at_timestamp.day),
            "month": str(received_at_timestamp.month),
            "hour": str(received_at_timestamp.hour),
            "int_timestamp": str(self._event_json_data["context"]["receivedAt"]),
        }
        return date_dict
    
    def get_or_create_file_path(self, json_files: List[str], folder_path: str, date_dict: dict) -> str:
        # (1) Check existing files
        if json_files:
            # Select "most recent" file (by its event-timestamp name),
            most_recent_file_path = max(json_files, key=lambda f: int(os.path.splitext(os.path.basename(f))[0]))
            # Check its size in bytes
            # This needs to be overridden by subclasses because they handle file sizes differently
            file_size = self.get_file_size(most_recent_file_path)

            # Define the path file will be written to
            if file_size < self._max_output_file_size:
                file_path = most_recent_file_path
            else:
                file_name = f"{date_dict['int_timestamp']}.json"
                file_path = os.path.join(folder_path, file_name)

        # (2) Create file if there are no files
        if not json_files:
            file_name = f"{date_dict['int_timestamp']}.json"
            file_path = os.path.join(folder_path, file_name)

        return file_path

    @abc.abstractmethod
    def get_file_size(self, file_path: str) -> int:
        pass

    @abc.abstractmethod
    def get_full_path(self) -> str:
        pass

    @abc.abstractmethod
    def write_file(self):
        pass


class LocalFileWriter(FileWriter):
    def __init__(self, event_json_data, root_path, max_output_file_size):
        super().__init__(event_json_data, max_output_file_size)
        self._root_path = root_path

    def get_file_size(self, file_path: str) -> int:
        return os.path.getsize(file_path)

    def get_full_path(self) -> str:
        date_dict = self.parse_received_at_date(self._event_json_data)

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
        file_path = self.get_or_create_file_path(json_files, folder_path, date_dict)
        
        return file_path


    def write_file(self, event_json_data):
        file_path = self.get_full_path()
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
            print("The existing data is not a list. Cannot append new data.")
            return

        # Append the new event data to existing data
        existing_data.append(self._event_json_data)

        # Write back the updated data
        with open(file_path, "w") as json_file:
            json.dump(existing_data, json_file)
        print(f"JSON file saved to: {file_path}")
        



class MinioFileWriter(FileWriter):
    def __init__(self, event_json_data, root_path, max_output_file_size, minio_client):
        super().__init__(event_json_data, max_output_file_size)
        self._root_path = root_path # = bucket_name TODO: should we rename it for comprehensibility?
        self._minio_client = minio_client

    def get_file_size(self, file_path: str) -> int:
        object_stat = self._minio_client.stat_object(self._root_path, file_path)
        return object_stat.size

    def get_full_path(self):
        date_dict = self.parse_received_at_date()

        # (1) Define folder path
        folder_path = os.path.join(
            date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"]
        )
        # (2) Get all json files in the dir
        objects = self._minio_client.list_objects(self._root_path, prefix=folder_path, recursive=False)
        json_files = [obj.object_name for obj in objects if obj.object_name.endswith('.json')]

        # (3) Check existing files
        file_path = self.get_or_create_file_path(json_files, folder_path, date_dict)

        return file_path

    def write_file(self):
        # (1) Get path
        file_path = self.get_full_path()

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
            print("The existing data is not a list. Cannot append new data.")
            return
        
        # Append the new event data to existing data
        existing_data.append(self._event_json_data)

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

        print(f"JSON file saved to MinIO at: {file_path}")


# ==================================== #
# (4) Set up EventConsumer
# ==================================== #

class EventConsumer:
    def __init__(self, file_writer: FileWriter, consumer: Consumer, topics: List[str], min_commit_count: int):
        self._file_writer = file_writer
        self._consumer = consumer
        self._topics = topics
        self._min_commit_count = min_commit_count
        

    def run_consume_loop(self):
        try:
            self._consumer.subscribe(self._topics)
            msg_count = 0
            while True:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    print("Kafka message error")  # TODO: Implement logging here
                else:
                    message_dict = parse_message(msg)
                    print("\n>>>>message_dict: ", message_dict)
                    self._file_writer._event_json_data = message_dict
                    self._file_writer.write_file()
                
                    msg_count += 1
                    if msg_count % self._min_commit_count == 0:
                        self._consumer.commit(asynchronous=True)
        
        finally:
            # Close down consumer to commit final offsets.
            self._consumer.close()



# ==================================== #
# (5) Test that it works
# ==================================== #


if __name__ == "__main__":
    # (1) Get general properties
    config_parser = ConfigParser(CONFIG_FILE_PATH)
    general_config_dict = config_parser.get_general_config()

    # (2 Option 1) Instantiate Locacl file writer
    # file_writer = LocalFileWriter(
    #     event_json_data={},
    #     root_path=general_config_dict["root_path"],
    #     max_output_file_size=general_config_dict["max_output_file_size"]
    # )

    # (2 Option 2) Instantiate Minio file writer
    minio_client = create_minio_client()
    create_bucket(general_config_dict["root_path"], minio_client)
    file_writer = MinioFileWriter(
        event_json_data={},
        root_path=general_config_dict["root_path"],
        minio_client=minio_client,
        max_output_file_size=general_config_dict["max_output_file_size"]
    )

    # (3) Instantiate consumer
    consumer = create_kafka_consumer()
    event_consumer = EventConsumer(
        file_writer=file_writer,
        consumer=consumer,
        topics=[general_config_dict["kafka_topic"]],
        min_commit_count=general_config_dict["min_commit_count"]
    )

    # (4) Write
    event_consumer.run_consume_loop()


