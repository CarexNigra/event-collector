import abc
import json
import os
from datetime import datetime
from io import BytesIO
from typing import Any, Optional

from minio import Minio
from minio.error import S3Error

from common.logger import get_logger
from config.config import MinioProperties, get_config

logger = get_logger()

# ==================================== #
# (1) Set up stuff for Minio
# ==================================== #


def create_minio_client(config: Optional[dict[str, Any]] = None) -> Minio:
    """
    Creates and returns a Minio client using the provided configuration or
    default configuration if none is provided.

    Args:
        config (Optional[dict[str, Any]]): Configuration dictionary for Minio client.
                                           Uses default if None.
    Returns:
        Minio: An initialized Minio client.
    """
    if not config:
        config = get_config()["minio"]
    minio_config = MinioProperties(**config)
    minio_config_dict = minio_config.model_dump(by_alias=True)
    logger.debug(f"Minio config raw type: {type(minio_config_dict)}, data: {minio_config_dict}")
    
    minio_client = Minio(**minio_config_dict)
    return minio_client


def create_bucket(bucket_name: str, minio_client: Minio) -> None:
    """
    Creates a bucket in Minio if it does not already exist.

    Args:
        bucket_name (str): The name of the bucket to create.
        minio_client (Minio): The Minio client used to create the bucket.
    Logs:
        Loggs success or error messages based on the creation status.
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' created successfully")
        else:
            logger.info(f"Bucket '{bucket_name}' already exists")
    except S3Error as exc:
        logger.error(f"Error occurred: {exc}")


# ==================================== #
# (2) Set up FileWriters
# ==================================== #


class FileWriterBase(abc.ABC):
    """
    Abstract base class for file writers, providing environment-agnostic
    methods to parse date information and create file paths.
    """

    def parse_received_at_date(self, message: str) -> dict[str, str]:
        """
        Parses a message to extract date information as a dictionary.
        NOTE: The date is taken from the first message

        Args:
            message (str): JSON-encoded message containing timestamp information.
        Returns:
            dict[str, str]: Dictionary with parsed date and time components.
        """
        msg_decoded = json.loads(message)
        received_at_timestamp = datetime.fromtimestamp(int(msg_decoded["context"]["receivedAt"]))
        date_dict = {
            "year": str(received_at_timestamp.year),
            "day": str(received_at_timestamp.day),
            "month": str(received_at_timestamp.month),
            "hour": str(received_at_timestamp.hour),
            "int_timestamp": str(msg_decoded["context"]["receivedAt"]),
        }
        return date_dict

    def create_file_path(self, folder_path: str, date_dict: dict, unique_consumer_id: str) -> str:
        """
        Generates a file path using the folder path, date dictionary, and a unique identifier.

        Args:
            folder_path (str): Base folder path (folder for local storage in dev, minio bucket for stg)
            date_dict (dict): Dictionary containing parsed date components.
            unique_consumer_id (str): Unique identifier for the consumer.
        Returns:
            str: Full file path including filename.
        """
        file_name = f"{unique_consumer_id}_{date_dict['int_timestamp']}.json"
        file_path = os.path.join(folder_path, file_name)
        return file_path

    @abc.abstractmethod
    def get_full_path(self, messages: list[str], unique_consumer_id: str) -> str:
        """
        Abstract method to get the full file path. Must be implemented by subclasses.
        Args:
            messages (list[str]): List of messages.
            unique_consumer_id (str): Unique identifier for the consumer.
        Returns:
            str: Full file path.
        """
        pass

    @abc.abstractmethod
    def write_file(self, messages: list[str], unique_consumer_id: str) -> None:
        """
        Abstract method to write messages to file. Must be implemented by subclasses.
        Args:
            messages (list[str]): List of messages to write.
            unique_consumer_id (str): Unique identifier for the consumer. Needed to be added
                to the file name (to force different consumers' writing to different files)
        """
        pass


class MinioFileWriter(FileWriterBase):
    """
    A file writer that saves messages to MinIO storage.

    Args:
        root_path (str): MinIO bucket name.
        minio_client (Minio): Minio client instance.
        NOTE: password and login should be stored as environment vars (see Readme)
    """

    def __init__(self, root_path, minio_client) -> None:
        self._root_path = root_path  # This is minio bucket_name 
        self._minio_client = minio_client

    def get_full_path(self, messages: list[str], unique_consumer_id: str) -> str:
        """
        Generates the full path for the file based on first message recieved_at date and minio bucket path.

        Args:
            messages (list[str]): List of messages.
            unique_consumer_id (str): Unique identifier for the consumer. Needed to be added
                to the file name (to force different consumers' writing to different files)
        Returns:
            str: Full path for the file.
        """
        first_message = messages[0]
        date_dict = self.parse_received_at_date(first_message)

        # (1) Define folder path
        folder_path = os.path.join(date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"])

        # (2) Create file path
        file_path = self.create_file_path(folder_path, date_dict, unique_consumer_id)

        return file_path

    def write_file(self, messages: list[str], unique_consumer_id: str) -> None:
        """
        Writes the provided messages to a file in MinIO storage.

        Args:
            messages (list[str]): List of messages to write.
            unique_consumer_id (str): Unique identifier for the consumer. Needed to be added
                to the file name (to force different consumers' writing to different files)
        """
        if not messages:
            return

        # (1) Get path
        file_path = self.get_full_path(messages, unique_consumer_id)

        # (2) Convert updated data back to JSON string
        json_data = "\n".join(messages)

        # (3) Write the updated data back to MinIO
        self._minio_client.put_object(
            bucket_name=self._root_path,
            object_name=file_path,
            data=BytesIO(json_data.encode("utf-8")),
            length=len(json_data),
            content_type="application/json",
        )
        logger.debug(f"(4) Saving. JSON file saved to MinIO at: {file_path}")
