from fastapi.testclient import TestClient
from api.app import app, create_kafka_producer
import uuid

from unittest.mock import MagicMock
import pytest


@pytest.fixture
def kafka_producer_mock():
    mock = MagicMock()
    mock.produce = MagicMock()
    yield mock


@pytest.fixture
def client(kafka_producer_mock):
    app.dependency_overrides[create_kafka_producer] = kafka_producer_mock 
    # NB: Apparently we cannot use dependency_overrides with fixtures outside of functions
    # If out it gives following error: 
    # Fixture "kafka_producer_mock" called directly. Fixtures are not meant to be called directly,
    # but are created automatically when test functions request them as parameters.
    # See https://docs.pytest.org/en/stable/explanation/fixtures.html for more information about fixtures, and
    # https://docs.pytest.org/en/stable/deprecations.html#calling-fixtures-directly about how to update your code.

    # TODO: Should I overwrite dependencies before I instantiate TestClient?
    yield TestClient(app)


def test_post(kafka_producer_mock, client):
    
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
    kafka_producer_mock.produce.assert_called_once()  # Check if produce method is called



# # BODY FORMAT / DATE-TIME
# def test_post_datetime_in_future(kafka_producer_mock_with_overwrite):
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
#     kafka_producer_mock_with_overwrite.produce.assert_not_called()  # Ensure produce method is not called
    

# def test_post_datetime_in_past(kafka_producer_mock_with_overwrite):
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
#     kafka_producer_mock_with_overwrite.produce.assert_not_called()  # Ensure produce method is not called



# # BODY FORMAT / MESSAGE ID
# def test_post_wrong_message_id_format(kafka_producer_mock_with_overwrite):
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
#     kafka_producer_mock_with_overwrite.produce.assert_not_called()  # Ensure produce method is not called



# # BODY FORMAT / EVENT NAME
# def test_post_wrong_event_name(kafka_producer_mock_with_overwrite):
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
#     kafka_producer_mock_with_overwrite.produce.assert_not_called()  # Ensure produce method is not called




