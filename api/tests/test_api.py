from fastapi.testclient import TestClient

from api.app import app

import uuid

client = TestClient(app)


def test_post():
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
    # print(f"Response Status Code: {response.status_code}")
    # print(f"Response Content: {response.text}")
    assert response.status_code == 204




# BODY FORMAT / DATE-TIME
def test_post_datetime_in_future():
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"}, 
        json={
            "event_name": 'test_event_name',
            "context": {
                "sent_at": 1701530942,
                "received_at": 2701530942,
                "processed_at": 1701530942,
                "message_id": str(uuid.uuid4()),
                "user_agent": "some_user_agent",
            },
            "data": {"user_id": "example_user_id",
                     "account_id": "example_account_id",
                     "user_role": "OWNER"},  
        }
    )
    assert response.status_code == 400
    

def test_post_datetime_in_past():
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"}, 
        json={
            "event_name": 'test_event_name',
            "context": {
                "sent_at": 1701530942,
                "received_at": 2701530942,
                "processed_at": -3,
                "message_id": str(uuid.uuid4()),
                "user_agent": "some_user_agent",
            },
            "data": {"user_id": "example_user_id",
                     "account_id": "example_account_id",
                     "user_role": "OWNER"},  
        }
    )
    assert response.status_code == 400



# BODY FORMAT / MESSAGE ID
def test_post_wrong_message_id_format():
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"}, 
        json={
            "event_name": 'test_event_name',
            "context": {
                "sent_at": 1701530942,
                "received_at": 1701530942,
                "processed_at": 1701530942,
                "message_id": "some_message_id_string",
                "user_agent": "some_user_agent",
            },
            "data": {"user_id": "example_user_id",
                     "account_id": "example_account_id",
                     "user_role": "OWNER"},  
        }
    )
    assert response.status_code == 400



# BODY FORMAT / EVENT NAME
def test_post_wrong_event_name():
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"}, 
        json={
            "event_name": 'another_event_name',
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
    assert response.status_code == 400


