import abc
import json
import os
from datetime import datetime

import xxhash

from common.logger import get_logger

logger = get_logger("file-writer-base")


def get_list_hash(objs: list[str]) -> str:
    """
    This function computes a hash for a list of Kafka messages, which are provided as JSON-decoded strings.
    The purpose of this hash is to create a unique identifier for the entire list, which can be
    added to the file name to avoid duplication.

    Args:
        objs (list[str]): A list of json strings, representing decoded Kafka messages.
    Returns:
        str: A hexadecimal hash value representing the concatenated contents of the list.
    """
    objs_str = "\n".join(objs)
    hash = xxhash.xxh64(objs_str).hexdigest()
    logger.debug(f"(5) Saving. Hash of consumed message queue: {hash}")
    return hash


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
        Generates a file path using the folder path, message queue hash, and a unique identifier.

        Args:
            folder_path (str): Base folder path (folder for local storage in dev, minio bucket for stg)
            msg_hash (str): Hash of the message queue
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
