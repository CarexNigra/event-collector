import uuid
from api.producer import ConfigParser
CONFIG_FILE_PATH = 'config/dev.toml' 


def assert_producer_mock(topic: str, value: str, key: str, on_delivery: callable):
    config_parser = ConfigParser(CONFIG_FILE_PATH)
    general_config_dict = config_parser.get_general_config()
    
    assert topic == general_config_dict['kafka_topic']
    print(value)
    assert len(value) > 0
    assert len(key) > 0


def test_post(kafka_producer_mock, client):
    
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"},
        json={
            "event_name": 'TestEvent',
            "context": {
                "sent_at": 1701530942,
                "received_at": 1701530942,
                "processed_at": 1701530942,
                "message_id": str(uuid.uuid4()),
                "user_agent": "some_user_agent",
            },
            "data": {
                "user_id": "example_user_id",
                "account_id": "example_account_id",
                "user_role": "OWNER"
            },
        }
    )

    assert response.status_code == 204
    kafka_producer_mock.produce.assert_called_once()  # Check if produce method is called
    assert_producer_mock(**kafka_producer_mock.produce.call_args.kwargs)



# BODY FORMAT / DATE-TIME
def test_post_datetime_in_future(client, kafka_producer_mock):
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"}, 
        json={
            "event_name": 'TestEvent',
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
    kafka_producer_mock.produce.assert_not_called()  # Ensure produce method is not called
    

def test_post_datetime_in_past(client, kafka_producer_mock):
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"}, 
        json={
            "event_name": 'TestEvent',
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
    kafka_producer_mock.produce.assert_not_called()  # Ensure produce method is not called



# BODY FORMAT / MESSAGE ID
def test_post_wrong_message_id_format(client, kafka_producer_mock):
    response = client.post(
        "/store", 
        headers={"Content-type": "application/json"}, 
        json={
            "event_name": 'TestEvent',
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
    kafka_producer_mock.produce.assert_not_called()  # Ensure produce method is not called



# BODY FORMAT / EVENT NAME
def test_post_wrong_event_name(client, kafka_producer_mock):
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
    kafka_producer_mock.produce.assert_not_called()  # Ensure produce method is not called