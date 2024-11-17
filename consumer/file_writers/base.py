import abc
import json
import os
from datetime import datetime

import xxhash


def get_list_hash(objs: list[str]) -> str:
    objs_str = "".join(objs)
    return xxhash.xxh64(objs_str).hexdigest()


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

    def create_file_path(self, folder_path: str, msg_hash: str, unique_consumer_id: str) -> str:
        """
        Generates a file path using the folder path, date dictionary, and a unique identifier.

        Args:
            folder_path (str): Base folder path (folder for local storage in dev, minio bucket for stg)
            date_dict (dict): Dictionary containing parsed date components.
            unique_consumer_id (str): Unique identifier for the consumer.
        Returns:
            str: Full file path including filename.
        """
        file_name = f"{unique_consumer_id}_{msg_hash}.json"
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
