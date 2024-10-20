import json
import os
import time
import uuid
from unittest.mock import MagicMock

import pytest
from pytest_minio_mock.plugin import MockMinioServers, MockMinioClient
from google.protobuf.json_format import MessageToJson

from events.context_pb2 import EventContext
from events_registry.events_registry import events_mapping
from events_registry.key_manager import ProducerKeyManager

from common.logger import get_logger

logger = get_logger()


# (1) Create event instance and populate it with data
@pytest.fixture(scope="session")
def event_mock():
    # Initial Unix timestamp
    base_timestamp = [1701530942]  # Using a list to make the timestamp mutable for each test event

    def create_event():
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
def batch_of_events_mock(event_mock):
   # Create message batches of message out of one sample message
    test_configs = {
        "number_of_test_messages": 25,
        "consumer_batch_size": 10,
    }
    dict_of_batches = {}
    for i in range(test_configs['number_of_test_messages']):
        message_dict = event_mock()["event_json_data"]
        #  Modify message for it to be potentially written into the next file
        message_dict["context"]["receivedAt"] = str(int(message_dict["context"]["receivedAt"]) + i)

        # Assign message to the random batch
        batch_id = i//test_configs['consumer_batch_size'] # At most ten messages in a batch
        if batch_id in dict_of_batches:
            dict_of_batches[batch_id].append(message_dict)
        else:
            dict_of_batches[batch_id] = [message_dict]

    logger.debug(f"{len(dict_of_batches.keys())} batches of messages have been created")

    return dict_of_batches


# (2) Create consumer mock
@pytest.fixture(scope="session")
def kafka_consumer_mock(event_mock):
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
def clean_up_temp():
    yield
    # NB: if yield is before command, it means that test function that receives
    # clean_up_temp as argument, first runs, than launches clean_up_temp running
    # in our case it is "test_consumption" function
    os.system("rm -rf /tmp/consumer_test_*")




