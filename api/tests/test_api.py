from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import pytest

from api.app import app, create_kafka_producer, KafkaProducerWrapper 

import uuid

client = TestClient(app)



# @pytest.fixture
# def kafka_producer_mock():
#     # Mock the Kafka producer
#     with patch("api.app.create_kafka_producer") as create_kafka_producer_mock: # TODO: Do we need to import create_kafka_producer to use it here?
#         producer_mock = Mock(spec=KafkaProducerWrapper)
#         create_kafka_producer_mock.return_value = producer_mock
#         yield producer_mock


@pytest.fixture
def kafka_producer_mock():
    # Mock the Kafka producer
    with patch("api.app.create_kafka_producer") as create_kafka_producer_mock:
        producer_mock = MagicMock(spec=KafkaProducerWrapper)
        create_kafka_producer_mock.return_value = producer_mock
        yield producer_mock


def test_post(kafka_producer_mock):
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"},
        json={
            "event_name": 'test_event_name',
            "context": {
                "sent_at": 1701530942,
                "received_at": 1701530942,
                "processed_at": 1701530942,
                "message_id": str(uuid.uuid4()),
                "user_agent": "some_user_agent",
            },
            "data": {"user_id": "example_user_id",
                     "account_id": "example_account_id",
                     "user_role": "OWNER"},  
        }
    )

    print("Rsp jsn", response.json())  # Print the entire response


    assert response.status_code == 204
    # kafka_producer_mock.produce.assert_called_once()  # Check if produce method is called
    kafka_producer_mock.assert_called_once_with(topic='event_messages', event=MagicMock())



# # BODY FORMAT / DATE-TIME
# def test_post_datetime_in_future(kafka_producer_mock):
#     response = client.post(
#         "/store", 
#         headers={"Content-type": "application/json"}, 
#         json={
#             "event_name": 'test_event_name',
#             "context": {
#                 "sent_at": 1701530942,
#                 "received_at": 2701530942,
#                 "processed_at": 1701530942,
#                 "message_id": str(uuid.uuid4()),
#                 "user_agent": "some_user_agent",
#             },
#             "data": {"user_id": "example_user_id",
#                      "account_id": "example_account_id",
#                      "user_role": "OWNER"},  
#         }
#     )
#     assert response.status_code == 400
#     kafka_producer_mock.produce.assert_not_called()  # Ensure produce method is not called
    

# def test_post_datetime_in_past(kafka_producer_mock):
#     response = client.post(
#         "/store", 
#         headers={"Content-type": "application/json"}, 
#         json={
#             "event_name": 'test_event_name',
#             "context": {
#                 "sent_at": 1701530942,
#                 "received_at": 2701530942,
#                 "processed_at": -3,
#                 "message_id": str(uuid.uuid4()),
#                 "user_agent": "some_user_agent",
#             },
#             "data": {"user_id": "example_user_id",
#                      "account_id": "example_account_id",
#                      "user_role": "OWNER"},  
#         }
#     )
#     assert response.status_code == 400
#     kafka_producer_mock.produce.assert_not_called()  # Ensure produce method is not called



# # BODY FORMAT / MESSAGE ID
# def test_post_wrong_message_id_format(kafka_producer_mock):
#     response = client.post(
#         "/store", 
#         headers={"Content-type": "application/json"}, 
#         json={
#             "event_name": 'test_event_name',
#             "context": {
#                 "sent_at": 1701530942,
#                 "received_at": 1701530942,
#                 "processed_at": 1701530942,
#                 "message_id": "some_message_id_string",
#                 "user_agent": "some_user_agent",
#             },
#             "data": {"user_id": "example_user_id",
#                      "account_id": "example_account_id",
#                      "user_role": "OWNER"},  
#         }
#     )
#     assert response.status_code == 400
#     kafka_producer_mock.produce.assert_not_called()  # Ensure produce method is not called



# # BODY FORMAT / EVENT NAME
# def test_post_wrong_event_name(kafka_producer_mock):
#     response = client.post(
#         "/store", 
#         headers={"Content-type": "application/json"}, 
#         json={
#             "event_name": 'another_event_name',
#             "context": {
#                 "sent_at": 1701530942,
#                 "received_at": 1701530942,
#                 "processed_at": 1701530942,
#                 "message_id": str(uuid.uuid4()),
#                 "user_agent": "some_user_agent",
#             },
#             "data": {"user_id": "example_user_id",
#                      "account_id": "example_account_id",
#                      "user_role": "OWNER"},  
#         }
#     )
#     assert response.status_code == 400
#     kafka_producer_mock.produce.assert_not_called()  # Ensure produce method is not called




