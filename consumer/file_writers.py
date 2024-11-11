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
    if not config:
        config = get_config()["minio"]
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
# (2) Set up FileWriters
# ==================================== #


class FileWriterBase(abc.ABC):
    # NOTE: This is an abstract class to make file writing env agnostic

    def parse_received_at_date(self, message: str) -> dict[str, str]:
        # NOTE: The date is taken from the first message
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
        file_name = f"{unique_consumer_id}_{date_dict['int_timestamp']}.json"
        file_path = os.path.join(folder_path, file_name)
        return file_path

    @abc.abstractmethod
    def get_full_path(self, messages: list[str], unique_consumer_id: str) -> str:
        pass

    @abc.abstractmethod
    def write_file(self, messages: list[str], unique_consumer_id: str):
        pass


class LocalFileWriter(FileWriterBase):
    def __init__(self, root_path) -> None:
        self._root_path = root_path

    def get_full_path(self, messages: list[str], unique_consumer_id: str) -> str:
        first_message = messages[0]
        date_dict = self.parse_received_at_date(first_message)

        # (1) Check if the subfolder exists in the consumer_output folder
        folder_path = os.path.join(
            self._root_path, date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"]
        )

        # (2) Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

        # (3) Create file path
        file_path = self.create_file_path(folder_path, date_dict, unique_consumer_id)

        return file_path

    def write_file(self, messages: list[str], unique_consumer_id: str) -> None:
        if not messages:
            return

        file_path = self.get_full_path(messages, unique_consumer_id)
        if file_path is None:
            return

        with open(file_path, "w") as json_file:
            for m in messages:
                json_file.write(m + "\n")
        logger.info(f"(4) Saving. JSON file saved to: {file_path}")


class MinioFileWriter(FileWriterBase):
    def __init__(self, root_path, minio_client) -> None:
        self._root_path = root_path  # = minio bucket_name TODO: should we rename it for comprehensibility?
        self._minio_client = minio_client

    def get_full_path(self, messages: list[str], unique_consumer_id: str) -> str:
        first_message = messages[0]
        date_dict = self.parse_received_at_date(first_message)

        # (1) Define folder path
        folder_path = os.path.join(date_dict["year"], date_dict["month"], date_dict["day"], date_dict["hour"])

        # (2) Create file path
        file_path = self.create_file_path(folder_path, date_dict, unique_consumer_id)

        return file_path

    def write_file(self, messages: list[str], unique_consumer_id: str) -> None:
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
        logger.info(f"(4) Saving. JSON file saved to MinIO at: {file_path}")
