import json
import os
import time
import uuid
from unittest.mock import MagicMock

import pytest
from google.protobuf.json_format import MessageToJson

from events.context_pb2 import EventContext
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager


# (1) Create event instance and populate it with data
@pytest.fixture(scope="session")
def event_mock():
    event_class = events_mapping.get("TestEvent")
    event_context = EventContext(
        sent_at=1701530942,
        received_at=1701530942,
        processed_at=1701530942,
        message_id=str(uuid.uuid4()),
        user_agent="some_user_agent",
    )
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


# (2) Create consumer mock
@pytest.fixture(scope="session")
def kafka_consumer_mock(event_mock):
    def poll(timeout: float = 1.0):
        msg = MagicMock()
        msg.value.return_value = event_mock["event_instance"].SerializeToString()
        msg.error.return_value = False
        msg.key.return_value = event_mock["key_manager"].generate_key().encode("utf-8")
        time.sleep(timeout)
        return msg

    mock = MagicMock()
    mock.subscribe = MagicMock()
    mock.commit = MagicMock()
    mock.poll = poll
    yield mock


# (3) Clean temp folder from consumer output folder created during testing
@pytest.fixture(scope="function")
def clean_up_temp():
    yield
    # NB: if yield is before command, it means that test function that receives
    # clean_up_temp as argument, first runs, than launches clean_up_temp running
    # in our case it is "test_consumption" function
    os.system("rm -rf /tmp/consumer_test_*")
