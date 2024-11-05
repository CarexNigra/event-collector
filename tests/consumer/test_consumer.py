import os
import threading
import time
from unittest.mock import MagicMock
import uuid
import glob 

from consumer.event_consumer import EventConsumer
from consumer.file_writers import LocalFileWriter 


def test_consumption(kafka_consumer_mock: MagicMock): #, clean_up_temp): 
    # (1) Mock config and define temp folder
    general_config_dict = {
        "kafka_topic": "event-messages",
        "root_path": "/tmp",
        "max_output_file_size": 3000,
        "flush_interval": 10,
        "consumption_period": 16, 
        "consumer_group_id": "cons_gr_id",
    }
    # 16 seconds is sufficient to generate 2 batches of messages to be written in 2 separate files
    # Each message is of size 266 B, batch contains up to 11 messages. File contains up to 3000 B
    temp_folder_uuid = "consumer_test_" + str(uuid.uuid4())

    # (2) Instantiate local file writer
    file_writer = LocalFileWriter(
        root_path=general_config_dict["root_path"] + f"/{temp_folder_uuid}",
    )

    # (3) Instantiate event consumer
    event_consumer = EventConsumer(
        file_writer=file_writer,
        consumer=kafka_consumer_mock,
        consumer_group_id=general_config_dict["consumer_group_id"],
        topics=[general_config_dict["kafka_topic"]],
        max_output_file_size = general_config_dict["max_output_file_size"], 
        flush_interval=general_config_dict["flush_interval"],
    )

    # (4) Run consume loop
    # test_consumer.py runs in a main thread.
    # We make basic_consume_loop to run in a separate thread to be able to end it
    # when main testing thread ends (we define it as a daemon, so it is possible)
    # Otherwise we enter into an infinite loop and test will never pass
    consumer_thread = threading.Thread(
        target=event_consumer.run_consume_loop, # NOTE: we pass function here, not calling it!
    )
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # (5) Let the consumer run for a while to simulate message processing
    # Simulate time for messages to be batched and flushed. 
    time.sleep(general_config_dict["consumption_period"])  

    # (6) Stop the consumer after test
    event_consumer.stop()
    consumer_thread.join(timeout=5)

    # (7) Verify that the file(s) have been written correctly
    # Check that at least one file was created in the temporary directory
    temp_output_path = file_writer._root_path
    files_in_directory = glob.glob(os.path.join(temp_output_path, '**/*.json'), recursive=True)

    assert len(files_in_directory) >= 2, "There should be at least 2 files created in the directory"

    # Check the size of the files or the content
    for file_path in files_in_directory:
        with open(file_path, 'r') as json_file:
            data = json_file.read()
            assert len(data) > 0, "File is empty when it shouldn't be"
            file_data_size = len(data.encode('utf-8'))
            assert file_data_size <= general_config_dict["max_output_file_size"], "File size exceeds limit"



