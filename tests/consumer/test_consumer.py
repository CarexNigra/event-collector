import threading
import time
import os
import uuid

from consumer.consumer import basic_consume_loop, parse_message, LocalFileWriter


CONFIG_FILE_PATH = 'config/dev.toml' 


def test_consumption(event_mock, kafka_consumer_mock, clean_up_temp): 
    # (1) Mock config and define temp folder
    general_config_dict = {
        'kafka_topic': 'event-messages', 
        'min_commit_count': 10,
        'save_to_path': '/tmp',
    }
    temp_folder_uuid = "consumer_test_" + str(uuid.uuid4())

    # (2) Run consume loop
    # test_consumer.py runs in a main thread. 
    # We make basic_consume_loop to run in a separate thread to be able to end it 
    # when main testing thread ends (we define it as a daemon, so it is possible)
    # Otherwise we enter into an infinite loop and test will never pass
    consumer_thread = threading.Thread(
        target=basic_consume_loop, 
        args=(
            kafka_consumer_mock, 
            [general_config_dict['kafka_topic']], 
            general_config_dict['min_commit_count'], 
            general_config_dict['save_to_path'] + f"/{temp_folder_uuid}",
        ),
    )
    consumer_thread.daemon = True
    consumer_thread.start()
    time.sleep(1)

    # (3) Check that file has been created 
    message_dict = event_mock['event_json_data']
    file_writer = LocalFileWriter(
        event_json_data = message_dict, 
        environment = 'dev', 
        root_path = general_config_dict['save_to_path'] + f"/{temp_folder_uuid}"
    )
    full_file_path = file_writer.get_full_path()
    print("full_file_path:", full_file_path)

    assert os.path.exists(full_file_path) == True
