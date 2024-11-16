import os
from io import BytesIO
from typing import Any, Optional

from minio import Minio
from minio.error import S3Error

from common.logger import get_logger
from config.config import MinioProperties, get_consumer_config
from consumer.file_writers.base import FileWriterBase, get_list_hash

logger = get_logger("minio-file-writer")


def create_minio_client(minio_config: MinioProperties | None = None) -> Minio:
    """
    Creates and returns a Minio client using the provided configuration or
    default configuration if none is provided.

    Returns:
        Minio: An initialized Minio client.
    """
    if not minio_config:
        config = get_consumer_config()
        minio_config = config.minio
    minio_config_dict = minio_config.model_dump(by_alias=True)
    logger.debug(f"Minio config raw type: {type(minio_config_dict)}, data: {minio_config_dict}")
    minio_client = Minio(**minio_config_dict)
    return minio_client


class MinioFileWriter(FileWriterBase):
    """
    A file writer that saves messages to MinIO storage.

    Args:
        root_path (str): MinIO bucket name.
        minio_client (Minio): Minio client instance.
        NOTE: password and login should be stored as environment vars (see Readme)
    """

    def __init__(self, root_path: str, minio_client: Minio) -> None:
        self._root_path = root_path  # This is minio bucket_name
        self._minio_client = minio_client

    def create_bucket(self, bucket_name: str | None = None) -> None:
        """
        Creates a bucket in Minio if it does not already exist.

        Args:
            bucket_name (str): The name of the bucket to create.
            minio_client (Minio): The Minio client used to create the bucket.
        Logs:
            Loggs success or error messages based on the creation status.
        """
        if not bucket_name:
            bucket_name = self._root_path
        try:
            if not self._minio_client.bucket_exists(bucket_name):
                self._minio_client.make_bucket(bucket_name)
                logger.info(f"Bucket '{bucket_name}' created successfully")
            else:
                logger.info(f"Bucket '{bucket_name}' already exists")
        except S3Error as exc:
            logger.error(f"Error occurred: {exc}")

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
        if not messages:
            return ""
        first_message = messages[0]
        date_dict = self.parse_received_at_date(first_message)

        # (1) Define folder path
        folder_path = os.path.join(date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"])

        # (2) Create file path
        msg_hash = get_list_hash(messages)
        file_path = self.create_file_path(folder_path, msg_hash, unique_consumer_id)

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
        if not file_path:
            logger.debug("Can't write empty file, ommiting")
            return

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
