import json
import os
import time
import uuid
from typing import Any, Callable, Generator
from unittest.mock import MagicMock

import pytest
from google.protobuf.json_format import MessageToJson

from common.logger import get_logger
from consumer.file_writers import FileWriterBase
from events.context_pb2 import EventContext
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

logger = get_logger()


# (1) Create event instance and populate it with data
@pytest.fixture(scope="session")
def event_mock() -> Callable[[], dict[str, Any]]:
    # (1) Set initial Unix timestamp
    base_timestamp = [1701530942]  # Using a list to make the timestamp mutable for each test event

    def create_event() -> dict[str, Any]:
        # (2) Increment the base timestamp by 1 second on each call
        base_timestamp[0] += 1

        event_class = events_mapping.get("TestEvent")
        event_context = EventContext(
            sent_at=base_timestamp[0],
            received_at=base_timestamp[0],  # Incremented timestamp
            processed_at=base_timestamp[0],
            message_id=str(uuid.uuid4()),
            user_agent="some_user_agent",
        )
        if event_class is None:
            raise Exception("Unknown event name: 'TestEvent'")
        else:
            event_instance = event_class(
                context=event_context,
                user_id="example_user_id",
                account_id="example_account_id",
                user_role="OWNER",
            )
            key_manager = ProducerKeyManager(event_type="TestEvent")
            event_json_string = MessageToJson(event_instance)
            event_json_data = json.loads(event_json_string)
            return {"event_instance": event_instance, "key_manager": key_manager, "event_json_data": event_json_data}

    return create_event


# (2) Create batch of events
@pytest.fixture(scope="session")
def batch_of_events_mock(event_mock: Callable[[], dict[str, Any]], number_of_messages_in_batch: int = 25) -> list[str]:
    batch = []
    for i in range(number_of_messages_in_batch):
        message_dict = event_mock()["event_json_data"]
        #  Modify message for it to have different receivedAt timestamp
        message_dict["context"]["receivedAt"] = str(int(message_dict["context"]["receivedAt"]) + i)
        message_str = json.dumps(message_dict)
        batch.append(message_str)

    logger.debug(f"A batch of {len(batch)} messages has been created")

    return batch


# (3) Create consumer mock
@pytest.fixture(scope="session")
def kafka_consumer_mock(event_mock: Callable[[], dict[str, Any]]) -> Generator[MagicMock, None, None]:
    def poll(timeout: float = 1.0):
        msg = MagicMock()
        msg.value.return_value = event_mock()["event_instance"].SerializeToString()
        msg.error.return_value = False
        msg.key.return_value = event_mock()["key_manager"].generate_key().encode("utf-8")
        time.sleep(timeout)
        return msg

    mock = MagicMock()
    mock.subscribe = MagicMock()
    mock.commit = MagicMock()
    mock.poll = poll

    mock.memberid.return_value = str(uuid.uuid4())

    yield mock


# (4) Create file writer mock
@pytest.fixture(scope="session")
def local_file_writer():
    """
    A fixture that provides an instance of LocalFileWriter for saving messages to local storage in dev environment.

    Returns:
        LocalFileWriter: An instance of LocalFileWriter configured with the specified root path.
    """

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
            logger.debug(f"JSON file saved to: {file_path}")

    return LocalFileWriter


# (5) Clean temp folder from consumer output folder created during testing
@pytest.fixture(scope="function")
def clean_up_temp() -> Generator:
    """
    NOTE: if yield is before command, it means that test function that receives
    clean_up_temp as argument, first runs, than launches clean_up_temp running
    in our case it is "test_consumption" function
    """
    yield
    os.system("rm -rf /tmp/consumer_test_*")
