import json
import os
import time
import uuid
from typing import Any, Callable, Generator
from unittest.mock import MagicMock

import pytest
from google.protobuf.json_format import MessageToJson

from common.logger import get_logger
from events.context_pb2 import EventContext
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

logger = get_logger()


# (1) Create event instance and populate it with data
@pytest.fixture(scope="session")
def event_mock() -> Callable[[], dict[str, Any]]:
    # Initial Unix timestamp
    base_timestamp = [1701530942]  # Using a list to make the timestamp mutable for each test event

    def create_event() -> dict[str, Any]:
        # Increment the base timestamp by 1 second on each call
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


# (2) Create consumer mock
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


# (3) Clean temp folder from consumer output folder created during testing
@pytest.fixture(scope="function")
def clean_up_temp() -> Generator:
    yield
    # NB: if yield is before command, it means that test function that receives
    # clean_up_temp as argument, first runs, than launches clean_up_temp running
    # in our case it is "test_consumption" function
    os.system("rm -rf /tmp/consumer_test_*")
